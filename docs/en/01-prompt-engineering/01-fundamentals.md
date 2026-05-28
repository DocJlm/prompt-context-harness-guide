---
title: §1.1 The Anatomy of a Prompt
description: The three-layer structure of System / User / Assistant and the controllable variables
---

# §1.1 The Anatomy of a Prompt

> Before learning a foreign language, you have to know its grammar.

## 1. The Three-Part Form: System / User / Assistant

Almost every modern chat-model API splits messages into three roles:

```python
messages = [
    {"role": "system",    "content": "你是一个简洁的中文助手。"},
    {"role": "user",      "content": "把这段英文翻译为中文：Hello world."},
    {"role": "assistant", "content": "你好，世界。"},
    {"role": "user",      "content": "再翻一遍，要更口语。"},
]
```

| Role | Who writes it | What it typically holds |
| :--- | :--- | :--- |
| `system` | Developer | Role setup, global instructions, output format, hard constraints that shouldn't be jailbroken |
| `user` | The user | The problem to solve right now / input data |
| `assistant` | The model | Past replies; can also be **manually injected** for few-shot |

::: note
- `system` is not a "super instruction." Models generally weight it **more highly**, but **not infinitely**. Jailbreak attacks and long-context dilution both erode its effect. So important constraints should be **concise, placed early, and repeated**.
- Some models (such as Claude) allow very long "role + task + tools" descriptions in `system`—this is the main battleground of Context Engineering.
:::

## 2. The Minimum Components of a "Runnable" Prompt

Synthesizing the guides from Anthropic, OpenAI, and Aliyun Bailian, a production-grade prompt needs at least these 6 pieces:

```
┌─────────────────────────────────────────────────────────────┐
│  1. Role           — Who are you?                            │
│  2. Task           — What do you need to do?                 │
│  3. Context        — What background information is needed?  │
│  4. Constraints    — What must / must not be done?           │
│  5. Examples       — (Optional) 1–3 demonstrations           │
│  6. Output Format  — What should it look like?               │
└─────────────────────────────────────────────────────────────┘
```

> **Aliyun Bailian's Prompt Engineering Guide** summarizes it even more briefly: **Task, Context, Examples, Output Format**—remember these four and you've got it.

### A "Bad → Good" Side-by-Side

**❌ Bad example** (works, but very risky):

```
Take a look at this code and tell me if there are any problems.
def divide(a, b): return a/b
```

The model will likely improvise: it might say "looks fine," or list 5 improvements. You don't get stable output.

**✅ Good example**:

```text
# Role
You are a senior Python code reviewer.

# Task
Review the following Python function and list potential defects.

# Constraints
- Focus only on three categories: boundary values, exception handling, type safety.
- Each issue must be under 30 characters.
- If there are no issues, output "No issues found."

# Example
Input:
def add(a, b): return a+b
Output:
- Boundary values: a or b being None is unhandled
- Type safety: a, b are not constrained to be numeric

# Output format
Output a Markdown list, each item starting with "- <category>: ".

# Code to review
```python
def divide(a, b): return a/b
```
```

The differences:
- Gave a **Role** → triggers the "code review" prior in the model.
- Gave an **explicit scope of 3 issue categories** → won't drift into unrelated topics.
- Gave a **length constraint** → predictable output.
- Gave an **example** → anchors style.
- Gave an **output format** → can be `parse`-d directly.

## 3. Controllable Variables: Delimiters, Variabilization, Markdown

### 1. Delimiters

Separating "instructions" from "data" is habit #1. Common patterns:

```text
Please summarize the following meeting transcript:

---BEGIN MEETING---
{{transcript}}
---END MEETING---
```

Or use XML (Claude models **especially prefer** XML tags):

```xml
<task>Summarize the meeting transcript</task>
<transcript>
{{transcript}}
</transcript>
<output_format>
<summary>...</summary>
<action_items><item>...</item></action_items>
</output_format>
```

> In practice on Claude, XML tag stability > Markdown > plain text. On GPT-series the three are roughly equivalent, but **Markdown reads the best**.

### 2. Variabilization

Don't hardcode data into the prompt. **Write the prompt as a template** and inject via `{{var}}` or f-string:

```python
SYSTEM_PROMPT = """You are a {role}.
Your task is to {task}.
Constraints: {constraints}
"""
messages = [
    {"role": "system", "content": SYSTEM_PROMPT.format(
        role="senior SQL optimizer",
        task="optimize the user's SQL query",
        constraints="rewrite only, do not modify schema",
    )},
    ...
]
```

This is **the first step toward Context Engineering**—your prompt is no longer a string but a **composable, testable template**.

### 3. Markdown Makes Structure Pop

```markdown
## Role
...
## Task
...
## Constraints
- ...
- ...
## Examples
...
## Output Format
```

Models follow instructions noticeably better with structured prompts. Even using just `##` headers gives a significant boost.

## 4. Temperature, Top-p, Seed: Parameters on the Decoding Side

After writing a good prompt, **generation parameters** still determine output randomness:

| Parameter | Range | High = ? | Low = ? | Recommended |
| :--- | :--- | :--- | :--- | :--- |
| `temperature` | 0–2 | More divergent, more creative | More deterministic, more reproducible | 0–0.3 for deterministic tasks, 0.7–1.0 for creative |
| `top_p` | 0–1 | More candidate tokens | Fewer candidate tokens | Generally pick this OR temperature, not both |
| `seed` | int | — | — | Fix seed during debugging for reproducibility |
| `max_tokens` | int | Longer | Shorter | Set a cap **with some headroom** |
| `stop` | list | — | — | Use hard stop sequences when the model might "over-extend" |

> **Golden rule**: **Fix the seed before evaluating; care about p99 in production.**

## 5. When Is a Prompt Enough?

Not every problem needs to escalate to Context / Harness. **Ask yourself first**:

- ❓ Can the task be completed in a **single inference**? (Writing copy, translating, classifying, extracting JSON fields...)
- ❓ Is the input **suitable for direct placement in the window**? (Input < 50K tokens)
- ❓ Is the output **structured** or **short text**?

**Three yeses** → Prompt Engineering is enough.  
**Any no** → Flip to Chapter 2 and start thinking about Context Engineering.

---

Next: [§1.2 The Seven Patterns →](./02-patterns.md)
