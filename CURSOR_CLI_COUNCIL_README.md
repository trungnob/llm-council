# Cursor CLI Council - Improved Version

A command-line tool that queries multiple AI models in parallel using cursor-agent, has them review each other's responses, and synthesizes a final answer.

## What's Different in This Version

This is an improved fork with the following fixes:

1. **Fixed Context Pollution** - Models no longer see your project files and get confused
2. **Visible Peer Reviews** - See what models actually think about each other's answers
3. **Parallel Execution Tracking** - Clear progress indicators and timing
4. **Updated Models** - Sonnet 4.5, Gemini 3 Pro, GPT-5.1

### Performance Improvements
- **8.7x faster** on simple questions (11s vs 95.7s)
- **2x faster** on complex questions (59s vs 117s)
- Clean, focused answers without project debugging talk

## Quick Start

```bash
# Simple question
python cursor_council.py "What is 2+2?"

# Complex question
python cursor_council.py "Explain quantum entanglement"

# Code generation
python cursor_council.py "Write Python code to find the Nth prime number"
```

## How It Works

**Stage 1:** All models answer your question in parallel
```
🚀 Starting 3 queries in parallel...
✅ [1/3] sonnet-4.5 completed
✅ [2/3] gpt-5.1 completed
✅ [3/3] gemini-3-pro completed
⏱️  All queries completed in 11.0s
```

**Stage 2:** Models review each other's answers (anonymized)
```
🔍 gpt-5.1's Review:
Response A provides the clearest explanation...
Response B is more concise but lacks detail...

FINAL RANKING:
1. Response A
2. Response B
3. Response C
```

**Stage 3:** Chairman synthesizes the best final answer
```
👑 Chairman (sonnet-4.5) Synthesizing
🎯 FINAL SYNTHESIZED ANSWER
[Comprehensive answer incorporating best insights from all models]
```

## Configuration

Edit the top of `cursor_council.py`:

```python
# Council members - change these to your preferred models
COUNCIL_MODELS = [
    "sonnet-4.5",           # Claude Sonnet 4.5
    "gemini-3-pro",         # Gemini 3 Pro
    "gpt-5.1",              # GPT-5.1
]

# Chairman synthesizes final answer
CHAIRMAN_MODEL = "sonnet-4.5"
```

### Available Models

According to cursor-agent documentation:
- `sonnet-4.5` - Claude Sonnet 4.5
- `opus-4.5` - Claude Opus 4.5 (slower, more thorough)
- `gemini-3-pro` - Google Gemini 3 Pro
- `gpt-5` - GPT-5
- `gpt-5.1` - GPT-5.1
- `gpt-5.1-high` - GPT-5.1 High Quality
- `grok` - xAI Grok
- `sonnet-4.5-thinking` - Claude with extended reasoning
- `opus-4.5-thinking` - Opus with extended reasoning

## Requirements

- **Cursor subscription** (uses cursor-agent CLI)
- **No API keys needed** (unlike the OpenRouter version)
- Python 3.10+

## Key Technical Changes

### 1. Fixed Context Pollution
**Problem:** Models saw project files and tried to help debug instead of answering.

**Solution:** Use empty temp workspace
```python
with tempfile.TemporaryDirectory() as tmpdir:
    result = subprocess.run([
        "cursor-agent",
        "--workspace", tmpdir,  # Isolated context
        "--model", model,
        prompt
    ])
```

### 2. Show Peer Reviews
**Problem:** Stage 2 only showed "evaluation received" without content.

**Solution:** Print review previews
```python
print(f"🔍 {model}'s Review:")
preview = response[:800] + ("..." if len(response) > 800 else "")
print(preview)
```

### 3. Parallel Execution Feedback
**Problem:** No visibility into what's happening.

**Solution:** Progress counters and timing
```python
print(f"🚀 Starting {len(models)} queries in parallel...")
start_time = time.time()
# ... execute queries ...
print(f"✅ [{completed}/{total}] {model} completed")
print(f"⏱️  All queries completed in {elapsed:.1f}s")
```

## Example Output

```
🏛️  CURSOR LLM COUNCIL
📝 Query: What is 2+2?
👥 Council: sonnet-4.5, gemini-3-pro, gpt-5.1
👑 Chairman: sonnet-4.5

============================================================
📋 STAGE 1: Collecting Individual Responses
============================================================
🚀 Starting 3 queries in parallel...
✅ [1/3] sonnet-4.5 completed
✅ [2/3] gpt-5.1 completed
✅ [3/3] gemini-3-pro completed
⏱️  All queries completed in 11.0s

📄 RESPONSES RECEIVED:
✅ sonnet-4.5: 2 + 2 = 4
✅ gpt-5.1: **2 + 2 = 4.**
✅ gemini-3-pro: 2 + 2 is 4.

============================================================
🏆 STAGE 2: Peer Review & Ranking
============================================================
🚀 Starting 3 queries in parallel...
✅ [1/3] gpt-5.1 completed
✅ [2/3] gemini-3-pro completed
✅ [3/3] sonnet-4.5 completed
⏱️  All queries completed in 17.0s

📊 PEER REVIEWS:
🔍 gpt-5.1's Review:
All responses are correct. Response A uses cleanest mathematical
notation without unnecessary formatting...

FINAL RANKING: 1. Response A, 2. Response B, 3. Response C

============================================================
👑 STAGE 3: Chairman (sonnet-4.5) Synthesizing
============================================================
🎯 FINAL SYNTHESIZED ANSWER

Based on unanimous consensus: **2 + 2 = 4**

The peer evaluations revealed that simple mathematical notation
without embellishment is most appropriate for arithmetic questions.
============================================================
```

## Comparison with OpenRouter Version

| Feature | cursor_council.py (This) | council_cli.py (OpenRouter) |
|:--------|:------------------------|:---------------------------|
| **Cost** | Free (Cursor subscription) | Pay per API call |
| **API Key** | Not needed | Required (OPENROUTER_API_KEY) |
| **Speed** | Fast | Fast |
| **Model Selection** | cursor-agent models | All OpenRouter models |
| **Setup** | Just run | Need .env file + credits |

## License

Same as original llm-council project.

## Credits

Improvements by community. Original project by @karpathy.
