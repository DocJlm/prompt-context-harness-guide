---
title: §2.1 Anatomy of Context
description: The System / Tools / Examples / History quartet; the attention budget
---

# §2.1 Anatomy of Context

> "Anthropic's overall guidance across different components of context (system prompts, tools, examples, message history, etc.) is to be **thoughtful and keep your context informative, yet tight**."  
> — Anthropic, *Effective Context Engineering for AI Agents*

## 1. The Quartet: System / Tools / Examples / History

By Anthropic's official taxonomy, an Agent's context is made of four kinds of components:

| Component | Role | Typical token share | When it changes |
| :--- | :--- | :--- | :--- |
| **System Prompt** | who, what to do, constraints, style | 1–5K | rarely (per session) |
| **Tool Definitions** | tool list + schemas | 1–10K | rarely (fixed at startup) |
| **Examples (Few-shot)** | key demonstrations | 0–5K | occasionally swapped |
| **Message History** | past dialogue / tool results | 0–180K | **grows every turn** |

Notice that **Message History is the dynamic heavyweight** — the first three usually add up to < 20K, leaving 180K for History. **This is where the real battle of context engineering is fought.**

## 2. The "Right Altitude" of a System Prompt

Anthropic offers a wonderful rule: a system prompt should sit at **"the right altitude"**.

> "Specific enough to guide behavior effectively, yet flexible enough to provide strong heuristics, avoiding both brittle hardcoded logic and vague high-level guidance."

Too low (hardcoded):

```text
When the user mentions "refund", reply:
"Sure, what's your order number? I'll look it up."
When the user mentions "complaint", reply:
"I'm really sorry, let me transfer you to a supervisor."
...
```

→ This is basically encoding a rules engine into the prompt — the moment the user phrases something slightly differently, the model derails.

Too high (vague):

```text
You are a customer support assistant. Please help the user.
```

→ The model freelances and the output style is all over the place.

**Just right**:

```text
You are the customer support assistant for Company X.

【Responsibilities】
- Answer questions about orders, refunds, and logistics.
- For complaints, empathize first, then ask for the order number.
- Do not commit to: compensation amounts, liability, or refund timing.

【Style】
- Chinese, professional but friendly.
- Each reply ≤ 80 characters.
- Mask personal info proactively (mid 4 digits of phone, city only for address).

【Boundaries】
- Requests involving supervisor / manager / legal → output `{"escalate": true}`.
- Suicide / self-harm / threats of violence → output `{"crisis": true, "hotline": "..."}`.
```

→ Gives a **scope of responsibility**, a **style boundary**, and **hard escalation rules** — without nailing down every single sentence.

## 3. Tool Definitions: Your "API Docs" Are Also Prompts

Tool descriptions are essentially prompts — the model relies on them to decide **when to call, how to call, and which tool to call**.

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
        "Search Company X's internal knowledge base. **Only use** for questions "
        "about internal products / processes / policies. **Do not** use it to "
        "search the public internet (use `web_search` for that). "
        "Returns top-5 passages + source links."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search keywords, Chinese or English. Phrases beat sentences."
            },
            "category": {
                "type": "string",
                "enum": ["product", "process", "policy", "any"],
                "description": "Scope the search. Use 'any' if uncertain."
            }
        },
        "required": ["query"]
    }
}
```

Anthropic puts it this way: "Tools should promote efficiency by returning token-efficient information... must be **self-contained, robust to error, and clear regarding intended use**."

Rules of thumb for tool descriptions:

- **Be explicit in the name**: `search_internal_docs` beats `search`.
- **Be explicit in scope**: when to use, when not to.
- **Document parameters**: a one-line description for each parameter + an enum where applicable.
- **Document the return format**: so the model knows how to use it next.
- **Be token-efficient**: the tool's return should be concise — prefer structured JSON over a wall of HTML.

## 4. Choosing Examples: Quality > Quantity

In *Context Engineering*, Anthropic emphasizes:

> "Examples should comprise a curated set of **diverse, canonical** examples portraying expected agent behavior rather than exhaustive edge cases."

**Three examples that cover normal / edge / counter cases beat 20 similar ones.** Why:

- The context budget is limited.
- The model "induces patterns" from examples — pattern coverage matters more than sample count.
- The **contrast** between examples gives the model a decision boundary.

Practical trick: dynamic few-shot. **Based on the current query, retrieve the top-k most similar examples from an example pool and inject them.** This move has lifted accuracy noticeably in many customer-support and document-QA systems.

## 5. Message History: the biggest "consumable"

History grows every turn. Ignore it and you'll eventually blow the window. There are three basic management strategies.

### Strategy A · Truncation

The simplest: keep only the most recent N turns.

```python
def truncate(messages, max_turns=20):
    return messages[0:1] + messages[-max_turns*2:]  # keep system + last N turns
```

Suitable for: scenarios dominated by short-term memory like customer support. **Downside**: cross-turn key information gets lost.

### Strategy B · Compaction

Squash the older turns into a summary:

```
Original messages:
  [system], [user:U1], [assistant:A1], [user:U2], [assistant:A2], ... ×50

After compaction:
  [system]
  [summary message]: "User and assistant discussed topics X, Y, Z. Key conclusions: abc. Open issues: def."
  [user:U50], [assistant:A50], [user:U51]
```

This move is **standard equipment in Claude Code, Cursor, Codex, and other coding agents** — we dedicate the next section to it.

### Strategy C · Slimming tool results

Large tool outputs (full files, long JSON) should **first be summarized by a small model**, then placed in history:

```python
def fold_tool_result(name, raw_result):
    if len(raw_result) > 2000:
        summary = small_model_summarize(raw_result, max_tokens=300)
        return f"<tool_result name={name}>(folded) {summary}</tool_result>"
    return raw_result
```

In practice this can cut context consumption by more than 50%.

## 6. Context Rot: You Cannot Pretend It Isn't There

This is a hard engineering constraint. Anthropic cites the well-known *Lost in the Middle* / *Needle in a Haystack* experiments: as the context approaches the window limit, the model's recall on **middle-segment** information drops noticeably.

Practical implications:

- ⚠️ **Put key constraints at the start AND the end**: the model attends most strongly to the beginning and the end.
- ⚠️ **Don't put important data past the 100K mark**: unless you've added a "reminder".
- ⚠️ **Past 70% of the window, compress**: don't gamble on "there's still 30% left."

Empirical thresholds:

| Window size | Safe usage zone | Must-compress threshold |
| :--- | :--- | :--- |
| 32K | < 16K | > 22K |
| 128K | < 60K | > 90K |
| 200K | < 100K | > 140K |
| 1M | < 300K | > 600K |

> "Larger windows don't mean you can stuff more, they mean you have more **headroom to recover from mistakes**." — an empirical law I'd state myself.

## 7. Putting This Section in Your Head: the Evolution of a Context Flow

```
Turn 1 (10K used):
[System 3K] [Tools 5K] [User: "Help me check order status" 200t] [Tool result 1K]

Turn 5 (28K used):
[System 3K] [Tools 5K] [Few-shot 2K] [History 15K] [Tool result 3K]

Turn 20 (98K used, near threshold):
↓ trigger compaction
[System 3K] [Tools 5K] [Few-shot 2K] [Summary of turns 1-15: 4K] [Recent turns 16-20: 18K] [Current: 2K]

Turn 50 (105K used):
↓ re-compact + bring in long-term memory
[System 3K] [Tools 5K] [Memory note: user prefs / past complaints 2K] [Summary 1-45: 5K] [Recent: 15K]
```

Notice this evolution combines **truncation + compaction + memory injection** — we cover each in the next three sections.

---

Next: [§2.2 Retrieval: Get the Right Info into the Window →](./02-retrieval.md)
