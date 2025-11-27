#!/usr/bin/env python3
"""
LLM Council using cursor-agent CLI

Uses your Cursor subscription to query multiple models and synthesize responses.
No external API keys needed!

Usage:
    python cursor_council.py "Your question here"
    
Or interactive:
    python cursor_council.py
"""

import subprocess
import sys
import json
import concurrent.futures
from typing import List, Dict, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

# Council members - models available in cursor-agent
# Confirmed available: sonnet-4.5, opus-4.5, opus-4.1, gemini-3-pro, 
#                      gpt-5, gpt-5.1, gpt-5.1-high, grok
#                      sonnet-4.5-thinking, opus-4.5-thinking (reasoning)
COUNCIL_MODELS = [
    "sonnet-4.5",           # Anthropic Claude Sonnet 4.5 (latest)
    "gemini-3-pro",         # Google Gemini 3 Pro (latest)
    "gpt-5.1",              # OpenAI GPT-5.1 (latest)
]

# Chairman model for final synthesis
CHAIRMAN_MODEL = "sonnet-4.5"

# Timeout for each model query (seconds)
TIMEOUT = 120

# ============================================================================
# CURSOR-AGENT INTERFACE
# ============================================================================

def query_model(model: str, prompt: str, timeout: int = TIMEOUT) -> Optional[str]:
    """Query a single model using cursor-agent CLI."""
    import tempfile
    import os
    
    try:
        # Run from empty temp directory to avoid workspace context
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    "cursor-agent",
                    "--print",
                    "--output-format", "text",
                    "--model", model,
                    "--workspace", tmpdir,  # Use empty temp directory
                    prompt
                ],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"❌ {model} error: {result.stderr[:200]}")
                return None
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ {model} timed out after {timeout}s")
        return None
    except FileNotFoundError:
        print("❌ cursor-agent not found! Make sure it's installed and in PATH")
        return None
    except Exception as e:
        print(f"❌ {model} exception: {e}")
        return None


def query_models_parallel(models: List[str], prompt: str) -> Dict[str, Optional[str]]:
    """Query multiple models in parallel."""
    import time
    
    print(f"🚀 Starting {len(models)} queries in parallel...")
    start_time = time.time()
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(models)) as executor:
        # Submit all tasks at once
        future_to_model = {
            executor.submit(query_model, model, prompt): model 
            for model in models
        }
        
        # Collect results as they complete
        completed = 0
        for future in concurrent.futures.as_completed(future_to_model):
            model = future_to_model[future]
            completed += 1
            try:
                result = future.result()
                results[model] = result
                if result:
                    print(f"✅ [{completed}/{len(models)}] {model} completed")
                else:
                    print(f"❌ [{completed}/{len(models)}] {model} failed")
            except Exception as e:
                print(f"❌ [{completed}/{len(models)}] {model} exception: {e}")
                results[model] = None
    
    elapsed = time.time() - start_time
    print(f"⏱️  All queries completed in {elapsed:.1f}s")
    
    return results


# ============================================================================
# COUNCIL STAGES
# ============================================================================

def stage1_collect_responses(user_query: str) -> List[Dict[str, str]]:
    """Stage 1: Get individual responses from all council members."""
    print("\n" + "="*60)
    print("📋 STAGE 1: Collecting Individual Responses")
    print("="*60)
    print(f"Council: {', '.join(COUNCIL_MODELS)}\n")
    
    responses = query_models_parallel(COUNCIL_MODELS, user_query)
    
    print("\n" + "-"*60)
    print("📄 RESPONSES RECEIVED:")
    print("-"*60)
    
    results = []
    for model, response in responses.items():
        if response:
            print(f"\n✅ {model}")
            print("-" * 40)
            # Show preview
            preview = response[:500] + ("..." if len(response) > 500 else "")
            print(preview)
            print()
            results.append({"model": model, "response": response})
        else:
            print(f"\n❌ {model} - No response")
    
    return results


def stage2_collect_rankings(
    user_query: str,
    stage1_results: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """Stage 2: Each model ranks the anonymized responses."""
    print("\n" + "="*60)
    print("🏆 STAGE 2: Peer Review & Ranking")
    print("="*60)
    
    # Anonymize responses
    labels = [chr(65 + i) for i in range(len(stage1_results))]
    responses_text = "\n\n---\n\n".join([
        f"**Response {label}:**\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])
    
    ranking_prompt = f"""You are evaluating different AI responses to this question:

QUESTION: {user_query}

Here are the anonymized responses:

{responses_text}

---

Please:
1. Briefly evaluate each response's strengths and weaknesses
2. End with a FINAL RANKING from best to worst:

FINAL RANKING:
1. Response X
2. Response Y
(etc.)"""

    print()
    responses = query_models_parallel(COUNCIL_MODELS, ranking_prompt)
    
    print("\n" + "-"*60)
    print("📊 PEER REVIEWS:")
    print("-"*60)
    
    results = []
    for model, response in responses.items():
        if response:
            print(f"\n🔍 {model}'s Review:")
            print("-" * 40)
            # Show first 800 chars of review
            preview = response[:800] + ("..." if len(response) > 800 else "")
            print(preview)
            print()
            results.append({"model": model, "ranking": response})
    
    # Show mapping
    print("\n📊 Response mapping (revealed):")
    for label, result in zip(labels, stage1_results):
        print(f"   Response {label} = {result['model']}")
    
    return results


def stage3_synthesize(
    user_query: str,
    stage1_results: List[Dict[str, str]],
    stage2_results: List[Dict[str, str]]
) -> str:
    """Stage 3: Chairman synthesizes the final answer."""
    print("\n" + "="*60)
    print(f"👑 STAGE 3: Chairman ({CHAIRMAN_MODEL}) Synthesizing")
    print("="*60)
    
    stage1_text = "\n\n---\n\n".join([
        f"### {result['model']}:\n{result['response']}"
        for result in stage1_results
    ])
    
    stage2_text = "\n\n---\n\n".join([
        f"### {result['model']}'s evaluation:\n{result['ranking']}"
        for result in stage2_results
    ])
    
    chairman_prompt = f"""You are the Chairman of an LLM Council. Your job is to synthesize multiple AI responses into ONE comprehensive, accurate final answer.

ORIGINAL QUESTION: {user_query}

---

STAGE 1 - Individual Model Responses:

{stage1_text}

---

STAGE 2 - Peer Evaluations & Rankings:

{stage2_text}

---

YOUR TASK:
Synthesize all of this into a single, high-quality answer that:
- Incorporates the best insights from all responses
- Addresses any disagreements or gaps
- Provides clear, accurate information

Provide the final synthesized answer:"""

    print("(Synthesizing final answer...)\n")
    
    response = query_model(CHAIRMAN_MODEL, chairman_prompt, timeout=180)
    
    if response:
        return response
    return "Error: Chairman failed to synthesize response."


# ============================================================================
# MAIN
# ============================================================================

def run_council(query: str):
    """Run the full 3-stage council process."""
    print("\n" + "🏛️ "*15)
    print("       CURSOR LLM COUNCIL")
    print("🏛️ "*15)
    print(f"\n📝 Query: {query}")
    print(f"👥 Council: {', '.join(COUNCIL_MODELS)}")
    print(f"👑 Chairman: {CHAIRMAN_MODEL}")
    
    # Stage 1: Collect responses
    stage1 = stage1_collect_responses(query)
    if not stage1:
        print("\n❌ No models responded. Check cursor-agent authentication.")
        return
    
    # Stage 2: Peer review (skip if only 1 response)
    if len(stage1) > 1:
        stage2 = stage2_collect_rankings(query, stage1)
    else:
        print("\n⚠️ Only 1 response received, skipping peer review")
        stage2 = []
    
    # Stage 3: Synthesize
    final = stage3_synthesize(query, stage1, stage2)
    
    # Final output
    print("\n" + "="*60)
    print("🎯 FINAL SYNTHESIZED ANSWER")
    print("="*60)
    print(f"\n{final}")
    print("\n" + "="*60)


def check_cursor_agent():
    """Verify cursor-agent is available and authenticated."""
    try:
        result = subprocess.run(
            ["cursor-agent", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if "not logged in" in result.stdout.lower() or "not authenticated" in result.stdout.lower():
            print("❌ cursor-agent not authenticated!")
            print("Run: cursor-agent login")
            return False
        return True
    except FileNotFoundError:
        print("❌ cursor-agent not found in PATH!")
        print("Make sure Cursor CLI is installed.")
        return False
    except Exception as e:
        print(f"⚠️ Could not verify cursor-agent status: {e}")
        return True  # Try anyway


def main():
    # Check cursor-agent
    if not check_cursor_agent():
        sys.exit(1)
    
    # Get query
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        print("\n🏛️  Cursor LLM Council - Interactive Mode")
        print("-" * 40)
        query = input("Enter your question: ").strip()
        if not query:
            print("No question provided. Exiting.")
            sys.exit(0)
    
    run_council(query)


if __name__ == "__main__":
    main()
