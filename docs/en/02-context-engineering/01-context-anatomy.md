---
title: §2.1 Anatomy of Context
description: The System / Tools / Examples / History quartet; the attention budget
---

# §2.1 Anatomy of Context

> "Anthropic's overall guidance across different components of context (system prompts, tools, examples, message history, etc.) is to be **thoughtful and keep your context informative, yet tight**."  
> — Anthropic, *Effective Context Engineering for AI Agents*

## Origin of the Idea · Karpathy Names "Context Engineering"

Although Anthropic was the first company to put "Context Engineering" into an official blog post, **the term's real popularizer was Andrej Karpathy**. On 2025-06-25 he posted:

> "**+1 for 'context engineering' over 'prompt engineering'**. People associate prompts with short task descriptions you'd give an LLM in your day-to-day use. When in every industrial-strength LLM app, **context engineering is the delicate art and science of filling the context window with just the right information for the next step**."  
> — [@karpathy, 2025-06-25](https://x.com/karpathy/status/1937902205765607626)

And in the same thread he added a key footnote:

> "Context engineering is just one small piece of an emerging **thick layer of non-trivial software** that coordinates individual LLM calls (and a lot more) into full LLM apps."

That second clause — "a thick layer of non-trivial software" — **is the subject of Chapter 3, Harness Engineering**. The two form a continuous spectrum:

- **Context Engineering** = the strategy for **deciding what goes into the window for each step**
- **Harness Engineering** = the **surrounding engineering** that implements those strategies (loops, tools, scheduling, state machines)

## 1. The Quartet: System / Tools / Examples / History

In Anthropic's official taxonomy, an Agent's context is made of four kinds of components:

| Component | Role | Typical token share | When does it change |
| :--- | :--- | :--- | :--- |
| **System Prompt** | Who, what, constraints, style | 1–5K | Essentially never (per session) |
| **Tool Definitions** | Tool list + schema | 1–10K | Essentially never (fixed at startup) |
| **Examples (Few-shot)** | Key demonstrations | 0–5K | Occasionally swapped |
| **Message History** | Past dialogue / tool results | 0–180K | **Grows every turn** |

Note that **Message History is the dynamic majority** — the other three typically sum to < 20K, leaving 180K for History. **The core battlefield of context engineering is here.**

## 2. The "Right Altitude" of a System Prompt

Anthropic gives a wonderfully evocative criterion: a system prompt should be written at **"the right altitude"**.

> "Specific enough to guide behavior effectively, yet flexible enough to provide strong heuristics, avoiding both brittle hardcoded logic and vague high-level guidance."

Too low (hardcoded):

```text
When the user mentions "refund", reply:
"Sure, what's your order number? Let me check."
When the user mentions "complaint", reply:
"I'm very sorry, let me transfer you to a supervisor."
...
```

→ This is essentially baking a rules engine into the prompt — the moment a user's phrasing doesn't match the rule exactly, the model breaks.

Too high (vague):

```text
You are a customer-service assistant. Please help the user.
```

→ The model freestyles; the output style is random.

**Just right**:

```text
You are X Company's customer-service assistant.

[Responsibilities]
- Answer questions about orders, refunds, and shipping.
- For complaints, empathize first, then guide the user to provide an order number.
- You must never commit to: compensation amounts, attributions of fault, refund timing.

[Style]
- Chinese, professional but friendly.
- Each reply must be at most 80 characters.
- When personal info comes up, redact proactively (middle 4 digits of phone numbers,
  keep only the city of an address).

[Escalation]
- Requests involving managers / supervisors / legal → output `{"escalate": true}`.
- Suicide / self-harm / violence threats → output `{"crisis": true, "hotline": "..."}`.
```

→ This gives **the scope of responsibility**, **the bounds of style**, and **hard escalation rules**, without scripting every line.

## 3. Tool Definitions: Your "API Docs" Are Also Prompts

A tool description is essentially a prompt — the model relies on it to decide **when to call, how to call, and which tool to call**.

### Bad vs. Good: a tool schema

❌ Bad:

```python
{
    "name": "search",
    "description": "Search.",
    "parameters": {"type": "object", "properties": {"q": {"type": "string"}}}
}
```

✅ Good:

```python
{
    "name": "search_internal_docs",
    "description": (
        "Search X Company's internal knowledge base. **Use only** for questions about "
        "internal products / processes / policies. **Do not** use it to search the public "
        "internet (use the `web_search` tool for that). Returns the top-5 paragraphs + source links."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Query keywords, Chinese or English. Phrases beat sentences."
            },
            "category": {
                "type": "string",
                "enum": ["product", "process", "policy", "any"],
                "description": "Scope the search. If unsure, set to any."
            }
        },
        "required": ["query"]
    }
}
```

Anthropic puts it: "Tools should promote efficiency by returning token-efficient information... must be **self-contained, robust to error, and clear regarding intended use**."

A few rules for writing good tool descriptions:

- **Clear name**: `search_internal_docs` beats `search`.
- **Clear scope**: when to use it, when not to.
- **Parameter docs**: one-line description + enum for each parameter.
- **Describe the return format**: so the model knows how to use it next.
- **Token-efficient**: the tool's returned content should be **concise**, e.g. structured JSON instead of a wall of HTML.

## 4. Choosing Examples: Quality > Quantity

Anthropic emphasizes in *Context Engineering*:

> "Examples should comprise a curated set of **diverse, canonical** examples portraying expected agent behavior rather than exhaustive edge cases."

**Three examples covering normal / edge / counter cases beat 20 similar examples.** Reasons:

- Context budget is finite.
- The model "induces patterns" from examples; pattern coverage matters more than sample count.
- The **contrast** between examples gives the model a decision boundary.

A practical trick: **dynamic few-shot**. Based on the current query, **retrieve top-k similar examples from a pool and inject them**. This trick has lifted accuracy in many customer-service / doc-Q&A systems.

## 5. Message History: the Largest "Consumable"

History grows every turn. Ignore it, and you'll blow the window sooner or later. Three basic management strategies:

### Strategy A · Truncation

The simplest: keep only the last N turns.

```python
def truncate(messages, max_turns=20):
    return messages[0:1] + messages[-max_turns*2:]  # Keep system + last N turns
```

Suited for: customer-service-style "short-term memory only" scenarios. **Issue**: cross-turn key info is lost.

### Strategy B · Compaction

Compress old turns into a single summary message:

```
Original messages:
  [system], [user:U1], [assistant:A1], [user:U2], [assistant:A2], ... ×50

After compaction:
  [system]
  [summary]: "User and assistant discussed X, Y, Z. Key conclusions: abc. Open questions: def."
  [user:U50], [assistant:A50], [user:U51]
```

This is the **standard practice in coding agents (Claude Code, Cursor, Codex)** — we'll devote the next section to it.

### Strategy C · "Slim Down" Tool Results

Large content returned by tools (full file contents, long JSON) should be **summarized by a small model first** before going into history:

```python
def fold_tool_result(name, raw_result):
    if len(raw_result) > 2000:
        summary = small_model_summarize(raw_result, max_tokens=300)
        return f"<tool_result name={name}>(folded) {summary}</tool_result>"
    return raw_result
```

In practice this can cut context usage by 50%+.

## 6. Context Rot: You Can't Pretend It Doesn't Exist

This is a hard engineering constraint. Anthropic has cited the famous *Lost in the Middle* / *Needle in a Haystack* experiments: when context fills close to the window limit, the model's recall on **middle** content drops sharply.

Practical impact:

- ⚠️ **Put key constraints at the very front + very end**: the model's attention is highest at start and finish.
- ⚠️ **Don't put important data past 100K tokens**: unless you "remind" the model.
- ⚠️ **Once past 70% of the window, compact**: don't bet on "the remaining 30%."

Rules of thumb:

| Window size | Safe use range | Compact-by threshold |
| :--- | :--- | :--- |
| 32K | < 16K | > 22K |
| 128K | < 60K | > 90K |
| 200K | < 100K | > 140K |
| 1M | < 300K | > 600K |

> "Larger windows don't mean you can stuff more, they mean you have more **headroom to recover from mistakes**." — a rule of thumb I've come to on my own.

## 7. Putting This Section in Your Head: The Evolution of a Context Stream

```
Turn 1 (10K used):
[System 3K] [Tools 5K] [User: "check my order status" 200t] [Tool result 1K]

Turn 5 (28K used):
[System 3K] [Tools 5K] [Few-shot 2K] [History 15K] [Tool result 3K]

Turn 20 (98K used, near threshold):
↓ Trigger Compaction
[System 3K] [Tools 5K] [Few-shot 2K] [Summary of turns 1-15: 4K] [Recent turns 16-20: 18K] [Current: 2K]

Turn 50 (105K used):
↓ Recompact + inject Long-term Memory
[System 3K] [Tools 5K] [Memory note: user preferences / history of complaints 2K] [Summary 1-45: 5K] [Recent: 15K]
```

Note that this evolution involves **truncation + compaction + memory injection** — we'll cover each in the next three sections.

---

Next: [§2.2 Retrieval: Get the Right Info Into the Window →](./02-retrieval.md)
