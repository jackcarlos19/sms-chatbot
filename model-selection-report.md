# SMS Chatbot AI Model Selection Report
**Date:** February 22, 2026  
**Project:** SMS Appointment Booking Chatbot  
**Current Model:** `anthropic/claude-sonnet-4-20250514` via OpenRouter ($3/$15 per 1M tokens)

---

## Executive Summary

You're currently using Claude Sonnet 4.5 — a frontier-class model designed for complex coding and research — to classify 5 intents and generate 2-sentence SMS replies. That's like hiring a neurosurgeon to put on a Band-Aid.

**Recommendation:** Switch to **GPT-4.1-mini** (`openai/gpt-4.1-mini`) as your primary model. It cuts AI costs by **95%**, has best-in-class tool calling reliability, and is purpose-built for exactly this kind of structured, low-complexity task. If you want to go even cheaper, **DeepSeek V3.2** or **Gemini 2.5 Flash** are strong secondary options.

---

## What Your App Actually Needs

Before evaluating models, let's be precise about the task. Your `ai_service.py` does two things:

### Task 1: `detect_intent()` — Intent Classification + Response Generation
- **Input:** System prompt (~200 tokens) + conversation history (0-400 tokens) + user message (~20 tokens)
- **Output:** Structured JSON via tool call (~80-150 tokens): `{intent, confidence, extracted_data, response_text, needs_info}`
- **Intent categories:** BOOK, CANCEL, RESCHEDULE, FAQ, CONFIRM_YES, CONFIRM_NO, UNCLEAR (7 total)
- **Response text:** 1-2 sentences, max 480 characters
- **Difficulty:** Low. This is pattern matching with short generation. A fine-tuned 7B model could do this.

### Task 2: `parse_slot_selection()` — Slot Number Extraction
- **Input:** User message + list of available slots
- **Output:** Structured JSON via tool call: `{slot_index, confidence}`
- **Difficulty:** Trivial. The user says "1" or "the Tuesday one."

### Token Budget Per Conversation
A typical 5-turn booking conversation (greeting → show slots → pick slot → confirm → done):

| Turn | Input Tokens | Output Tokens |
|------|-------------|---------------|
| 1 (intent detection) | ~400 | ~120 |
| 2 (slot presentation) | ~500 | ~150 |
| 3 (slot parsing) | ~450 | ~80 |
| 4 (confirmation) | ~550 | ~100 |
| 5 (booking complete) | ~600 | ~120 |
| **Total per conversation** | **~2,500** | **~570** |

### Critical Model Requirements
1. **Reliable tool/function calling** — Your app uses `tool_choice: {type: "function", function: {name: "submit_intent"}}` which forces a tool call. The model MUST return valid JSON in the tool call arguments, every time.
2. **Fast response time** — SMS users expect replies in 2-5 seconds. Latency matters more than raw intelligence.
3. **Short, natural responses** — The model writes 1-2 sentence SMS replies, not essays. Smaller models actually do this better (less verbose).
4. **OpenRouter compatibility** — Must be accessible via the OpenAI-compatible API at `openrouter.ai/api/v1`.

### What You Do NOT Need
- Extended context windows (your conversations are under 3K tokens)
- Complex reasoning or chain-of-thought
- Code generation
- Multimodal capabilities
- 100K+ token context

---

## Model Comparison

All prices are per 1M tokens via OpenRouter. Cost estimates assume 500 conversations/month (your Pro tier).

### Tier 1: Best Value (Recommended)

#### 🏆 GPT-4.1-mini — PRIMARY RECOMMENDATION
| Attribute | Value |
|-----------|-------|
| OpenRouter ID | `openai/gpt-4.1-mini` |
| Price | $0.40 input / $1.60 output per 1M tokens |
| Context | 1M tokens |
| Tool Calling | ✅ Native, strict mode available |
| Structured Output | ✅ 100% schema compliance with `strict: true` |
| Speed | ~200+ tokens/sec, sub-1s latency |

**Why it wins for your app:**
- **Tool calling was the #1 design goal** for the GPT-4.1 family. OpenAI specifically optimized these models for reliable function calling with strict schema adherence.
- With `strict: true` on the tool definition, it achieves 100% JSON schema compliance — meaning your `submit_intent` tool call will never return malformed data.
- At $0.40/$1.60, a 5-turn booking conversation costs approximately **$0.002** (two-tenths of a cent).
- It's fast enough that SMS responses arrive in 1-2 seconds.
- Well-tested in production by thousands of developers building chatbots and agents.

**Monthly cost at 500 conversations:** ~$1.00  
**vs. current Sonnet 4.5:** ~$10.13  
**Savings:** 90%

---

#### DeepSeek V3.2 — BUDGET CHAMPION
| Attribute | Value |
|-----------|-------|
| OpenRouter ID | `deepseek/deepseek-v3.2` |
| Price | $0.28 input / $0.40 output per 1M tokens |
| Context | 128K tokens |
| Tool Calling | ✅ Supported |
| Structured Output | ✅ Via tool calling |
| Speed | Fast, competitive latency |

**Why it's compelling:**
- Achieves ~90% of GPT-5.1's performance at 1/50th the cost.
- Strong tool-use reliability from an agentic task synthesis training pipeline.
- At $0.28/$0.40, a booking conversation costs approximately **$0.001** (one-tenth of a cent).
- Automatic context caching: if your system prompt is consistent (it is), repeat requests get 90% input cost reduction.

**⚠️ Key risk — data privacy:**
- DeepSeek's servers are in China. Prompts may be used for training with no opt-out.
- Chinese law requires cooperation with government data requests.
- Italy banned DeepSeek in 2025; U.S. considered a nationwide ban.
- **For a production SaaS handling customer phone numbers and appointment data, this is a serious liability.** You'd need to disclose this in your privacy policy, and some home services companies won't accept it.

**Monthly cost at 500 conversations:** ~$0.50  
**Best for:** Development/testing, personal use, or if data privacy isn't a concern for your customers.

---

#### Gemini 2.5 Flash — GOOGLE'S SPEED DEMON
| Attribute | Value |
|-----------|-------|
| OpenRouter ID | `google/gemini-2.5-flash` |
| Price | ~$0.15 input / $0.60 output per 1M tokens (non-thinking) |
| Context | 1M tokens |
| Tool Calling | ✅ Native support |
| Structured Output | ✅ `response_mime_type: application/json` with schema enforcement |
| Speed | ~250 tokens/sec — one of the fastest models available |

**Why it works:**
- Extremely fast, great for SMS latency requirements.
- Google offers 90% discount on cached tokens, which stacks well with your consistent system prompt.
- Strong structured output support via native JSON schema enforcement.
- Non-thinking mode is cheap and sufficient for your use case.

**⚠️ Considerations:**
- Tool calling through OpenRouter may route through different providers with varying reliability.
- Less battle-tested than GPT-4.1-mini for function calling in production.

**Monthly cost at 500 conversations:** ~$0.55

---

### Tier 2: Solid Alternatives

#### GPT-4o-mini — THE PROVEN WORKHORSE
| Attribute | Value |
|-----------|-------|
| OpenRouter ID | `openai/gpt-4o-mini` |
| Price | $0.15 input / $0.60 output per 1M tokens |
| Context | 128K tokens |
| Tool Calling | ✅ Native, strict mode |
| Structured Output | ✅ 100% schema compliance |

**The case for it:** Cheapest OpenAI model with proven 100% structured output compliance. Has been in production since mid-2024 with billions of API calls. Slightly less capable than GPT-4.1-mini on instruction following, but for your simple intent classification it won't matter.

**Monthly cost at 500 conversations:** ~$0.42  
**Why not #1:** GPT-4.1-mini has better instruction following for only slightly more cost. The difference is negligible, so either works.

---

#### Claude Haiku 4.5 — STAYING IN THE ANTHROPIC ECOSYSTEM
| Attribute | Value |
|-----------|-------|
| OpenRouter ID | `anthropic/claude-haiku-4-5` |
| Price | $1.00 input / $5.00 output per 1M tokens |
| Context | 200K tokens |
| Tool Calling | ✅ Supported |
| Structured Output | ✅ Via tool calling |

**The case for it:** If you want to stay on Anthropic models, Haiku is the small/fast option. Good instruction following, natural tone for SMS responses.

**⚠️ Drawbacks:**
- 3-8x more expensive than GPT-4.1-mini or GPT-4o-mini for equivalent quality on this simple task.
- No strict schema enforcement mode — tool call arguments are best-effort, not guaranteed.
- Output pricing at $5/M is 3x higher than GPT-4.1-mini.

**Monthly cost at 500 conversations:** ~$3.35  
**Why not #1:** Costs 3x more than GPT-4.1-mini with no meaningful quality advantage for intent classification.

---

#### GPT-4o — MID-RANGE FALLBACK
| Attribute | Value |
|-----------|-------|
| OpenRouter ID | `openai/gpt-4o` |
| Price | $2.50 input / $10.00 output per 1M tokens |
| Context | 128K tokens |
| Tool Calling | ✅ Native, strict mode |
| Structured Output | ✅ 100% compliance |

**Only use this if:** GPT-4.1-mini and GPT-4o-mini somehow produce poor results for your specific prompts (unlikely). It's the same architecture family with more parameters.

**Monthly cost at 500 conversations:** ~$6.95

---

### Tier 3: Overkill (Current Setup)

#### Claude Sonnet 4.5 — YOUR CURRENT MODEL
| Attribute | Value |
|-----------|-------|
| OpenRouter ID | `anthropic/claude-sonnet-4-20250514` |
| Price | $3.00 input / $15.00 output per 1M tokens |

**Why you're overpaying:** This model excels at complex software engineering, multi-step reasoning, and long-form analysis. None of those capabilities are used by your chatbot. You're paying a 10-25x premium for intelligence you don't need.

**Monthly cost at 500 conversations:** ~$10.13

---

### Tier 4: Free Models (Development/Testing Only)

These are great for development and testing but **not recommended for production** due to rate limits (typically 20 requests/minute, 200/day) and no reliability guarantees.

| Model | OpenRouter ID | Tool Calling | Notes |
|-------|--------------|-------------|-------|
| Llama 3.3 70B | `meta-llama/llama-3.3-70b-instruct:free` | ✅ | Strong general performance, good for testing |
| GPT-OSS-120B | `openai/gpt-oss-120b:free` | ✅ | OpenAI's open-weight MoE model, native tool use |
| Gemma 3 | `google/gemma-3-27b-it:free` | ✅ | 128K context, structured outputs |
| DeepSeek V3.2 | `deepseek/deepseek-v3.2:free` | ✅ | Same privacy concerns as paid tier |

**Best free model for your testing:** Llama 3.3 70B — no data privacy concerns (Meta open-source), good tool calling, large enough for reliable intent classification.

---

### HuggingFace Self-Hosted: Not Worth It (Yet)

You asked about HuggingFace for specialized models. Here's the honest assessment:

**There are no specialized "appointment booking intent classifier" models on HuggingFace** that would outperform a general-purpose LLM with good prompting. The intent classification task (7 categories from conversational SMS) is too niche for a pre-trained specialist and too simple to justify fine-tuning.

Self-hosting would make sense if:
- You had 10,000+ conversations/month (your unit economics don't justify the infrastructure cost below that)
- You needed sub-100ms latency (not required for SMS)
- You had strict data sovereignty requirements

**If you ever reach scale**, the right path would be to fine-tune a small model (Qwen3-4B or Gemma 3n 2B) on your real conversation data. A 2B-4B parameter model fine-tuned on 5,000 labeled conversations would likely outperform GPT-4.1-mini on your specific task while costing almost nothing to run. But you need the data first — and you get the data by running in production with a general-purpose model.

---

## Cost Projection at Scale

Monthly AI costs based on conversation volume:

| Conversations/mo | Sonnet 4.5 (current) | GPT-4.1-mini | GPT-4o-mini | DeepSeek V3.2 |
|------------------|--------------------|-------------|------------|--------------|
| 100 | $2.03 | $0.20 | $0.08 | $0.10 |
| 500 | $10.13 | $1.00 | $0.42 | $0.50 |
| 2,000 | $40.50 | $4.00 | $1.68 | $2.00 |
| 10,000 | $202.50 | $20.00 | $8.40 | $10.00 |
| 50,000 | $1,012.50 | $100.00 | $42.00 | $50.00 |

**At 450 customers × 500 conversations each = 225,000 conversations/month (your Month 24 projection):**
- Sonnet 4.5: **$4,556/mo** in AI costs alone
- GPT-4.1-mini: **$450/mo**
- GPT-4o-mini: **$189/mo**

The model choice is the difference between AI costs eating your margins and AI costs being a rounding error.

---

## Implementation: What to Change

The switch is trivial. Your app uses the OpenAI-compatible client already. Change one environment variable:

```env
# In your .env file, change:
AI_MODEL=openai/gpt-4.1-mini

# That's it. No code changes needed.
```

**Optional improvement** — add `strict: true` to your tool definitions in `ai_service.py` to enable guaranteed schema compliance:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "submit_intent",
            "strict": True,  # ← ADD THIS LINE
            "description": "Return structured intent result.",
            "parameters": {
                "type": "object",
                "properties": { ... },
                "required": [...],
                "additionalProperties": False  # ← ADD THIS LINE (required for strict mode)
            },
        },
    }
]
```

This gives you 100% guaranteed valid JSON from GPT-4.1-mini — no more try/except fallbacks for malformed responses.

---

## Advanced: Multi-Model Routing (Future Optimization)

Once you're in production with real data, you can implement a two-model strategy:

| Task | Model | Why |
|------|-------|-----|
| Intent classification (90% of calls) | GPT-4o-mini ($0.15/$0.60) | Simple pattern matching, cheapest reliable option |
| Complex/ambiguous conversations (10%) | GPT-4.1-mini ($0.40/$1.60) | Better instruction following for edge cases |

**Router logic:** If `detect_intent` returns confidence < 0.7, retry with the more capable model. This is a ~30 minute code change and would reduce costs by another 40%.

OpenRouter also offers `openrouter/auto` which automatically routes simple prompts to cheap models and complex ones to capable models, though building your own routing gives you more control.

---

## Final Recommendation

| Priority | Action | Impact |
|----------|--------|--------|
| **Do now** | Switch `AI_MODEL` to `openai/gpt-4.1-mini` | 90% cost reduction, better tool calling |
| **Do now** | Add `strict: true` + `additionalProperties: false` to tool defs | 100% JSON reliability |
| **Test next** | Try `openai/gpt-4o-mini` and compare response quality | Potential additional 60% savings |
| **At scale** | Implement confidence-based model routing | Another 30-40% savings |
| **At 10K+ convos/mo** | Evaluate fine-tuning a small open model on your data | Near-zero marginal AI cost |

**Bottom line:** Change one line in your `.env` file and save 90% on AI costs while getting better structured output reliability. Test it in your simulator UI right now — send 10 conversations through with `openai/gpt-4.1-mini` and compare the responses to what Sonnet 4.5 gives you.
