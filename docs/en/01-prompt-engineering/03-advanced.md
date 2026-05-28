---
title: §1.3 Advanced · Meta-prompting & the GPT-5 Era
description: Using the model to improve the model; Reasoning Effort, Eagerness, Persistence, Tool Preambles
---

# §1.3 Advanced: Meta-prompting & the GPT-5 Era

> "Most folks know prompt engineering. But to get the most out of AI agents, you need context engineering."  
> — Anthropic

By 2025–2026, models themselves can write better prompts than you can. So **the center of gravity of advanced prompt engineering has shifted from "how to write" to "how to tune"**—tuning reasoning depth, tuning proactivity, tuning tool-use style.

## 1. Meta-prompting: Letting the Model Improve Its Own Prompt

OpenAI's GPT-5 Prompting Guide states it plainly: **GPT-5 is a metaprompting expert**.

The simplest metaprompt template:

```text
I want you to help me **evaluate and improve** a prompt.

Original prompt:
"""
{{original_prompt}}
"""

It performs poorly on the following cases:
Case 1: input X → expected Y → actual Z
Case 2: ...

Please output in the following structure:
1. Diagnosis of failure causes (one per case)
2. Suggestions for improvement
3. The full rewritten prompt
```

This metaprompt is itself a prompt—you can also ask the model how to improve it. **It's a recursive process.**

### Three Practical Uses of Meta-prompting

1. **Cold start**: when you don't know how to start a new prompt, have the model generate a first draft from a one-sentence requirement.
2. **Diagnose**: when a current prompt is inaccurate, feed the bad cases to the model and have it diagnose.
3. **Refactor**: have the model rewrite a long prompt to be more compact (**note**: tell it which parts must not be changed).

### Pitfalls of Meta-prompting

- ❌ Letting the model "improvise"—it'll add too much boilerplate. Instructions must be tight.
- ❌ Changing too much at once—iterate on one dimension at a time (first fix accuracy, then length, then format).
- ❌ Putting metaprompt output **straight into production**—it must be **Eval-gated** (see §1.4).

## 2. Reasoning Effort: How Much Brainpower?

Models like GPT-5, Claude 4.x, DeepSeek-R1, and Qwen3-Thinking all introduce a **reasoning budget** knob. OpenAI uses the `reasoning_effort` parameter; Anthropic uses a `thinking` block.

```python
# OpenAI GPT-5 style
response = client.chat.completions.create(
    model="gpt-5",
    messages=messages,
    reasoning_effort="medium",  # "minimal" | "low" | "medium" | "high"
)
```

| Effort | Use case | Cost |
| :--- | :--- | :--- |
| `minimal` | Single-step classification, extraction, translation | Near-instant |
| `low` | Simple code, rule-based reasoning | Slightly slow |
| `medium` | **Default.** Multi-step tasks | Moderate |
| `high` | Complex math, long-document reasoning | Slow, expensive |

::: OpenAI official guidance
> "Scale `reasoning_effort` up for complex tasks, down for efficiency; default is medium."

**Best practice**: run Eval at medium first, then decide whether to tune. **Don't default to high**—it makes simple tasks slow and expensive too.
:::

## 3. Agentic Eagerness: Tuning "Proactivity"

This is a new dimension introduced by GPT-5. In multi-step tasks, **how eagerly should the model explore / call tools**?

### Prompt that reduces eagerness

```
"Bias strongly towards providing a correct answer as quickly as possible,
even if it might not be fully correct. Usually, this means an absolute
maximum of 2 tool calls."
```

### Prompt that increases eagerness

```
"Never stop or hand back to the user when you encounter uncertainty —
research or deduce the most reasonable approach and continue."
```

::: key judgment
- **Customer service / coding**: lean **eager**—don't keep saying "please provide more information."
- **Finance / medical / delete operations**: lean **not eager**—better to ask than to act recklessly.
:::

## 4. Tool Preambles: "Say Something" Before Calling a Tool

Another habit introduced by GPT-5: **before calling a tool, have the model tell the user "what I'm about to do" in one sentence**.

```text
Before each tool call, tell the user in one sentence what you're about to do.
For example:
"Let me first look at the file structure..."
Then issue the ListFiles call.
```

Why it matters:
- **Users can follow along**: reduces "black box" anxiety.
- **Interpretability**: the model's intent is visible in logs.
- **Reduces hallucination**: making the model "speak before acting" forces it to plan first.

This is standard practice for Coding Agents (such as Claude Code, Cursor, Codex).

## 5. Persistence: Make the Model Stick With the Task

From OpenAI's official guidance, **almost all agentic scenarios should add this**:

```text
You are an agent — please keep going until the user's query is completely
resolved, before ending your turn and yielding back to the user. Only
terminate your turn when you are sure the problem is solved.
```

It fixes a classic bug: **the model timidly stops midway**, leaving a half-finished job for you.

## 6. Advanced Output Format: Make the Model "Self-Check"

Force the model to **self-check** at the end of its output:

```text
# Output format
{
  "answer": "...",
  "self_check": {
    "constraint_1_met": true,
    "constraint_2_met": true,
    "uncertainty_level": "<low|medium|high>"
  }
}
```

This trick is astonishingly effective in production—**to fill in that self_check field, the model automatically goes back and reviews whether its answer meets the constraints**. You get a free layer of self-reflection.

## 7. Adapting to Chinese Models: Differences

Chinese-domestic models (Tongyi Qwen, Zhipu GLM, DeepSeek, Moonshot Kimi, Baichuan, Wenxin) mostly support OpenAI-compatible APIs, so the prompt templates above **can be reused almost verbatim**. But there are a few empirical differences:

| Model family | Tendencies / notes |
| :--- | :--- |
| **Qwen** | More stable on Chinese prompts; XML tags + JSON Schema compatibility is good |
| **GLM** | Prefers Markdown structure; trigger CoT with "请逐步思考" (please reason step by step) |
| **DeepSeek-V/R series** | The R series has strong built-in CoT—**don't** add step-by-step on top |
| **Kimi** | Excellent long-context, especially suited to very long RAG scenarios |
| **Baichuan / Wenxin** | More "polite" Chinese word choice; prefers "expert" role framings |

::: general advice
**Write and tune all prompts first on GPT-4o-mini or Claude Haiku, then** run an Eval on the Chinese models. Cross-model robustness is a core production value metric.
:::

## 8. Combining Everything: One "GPT-5 Era Prompt"

```text
# Role and goal
You are a senior SRE Agent, responsible for diagnosing production incidents.

# Persistence
Do not stop until the incident is localized + a fix plan is given.

# Eagerness
Be eager about tool calls: better to inspect one more log than to miss something. Max 8 tool-call budget.

# Tool Preamble
Before each tool call, tell the on-call engineer in one sentence what you're about to do.

# Reasoning
Use thinking for complex correlation analysis. Don't use thinking for trivial command concatenation.

# Output
Final output in the following JSON:
{
  "root_cause": "...",
  "evidence": ["...", "..."],
  "fix_plan": "...",
  "confidence": "<low|medium|high>",
  "self_check": {
    "evidence_traceable": true,
    "fix_actionable": true
  }
}
```

This snippet simultaneously contains Role, Persistence, Eagerness, Preamble, Reasoning, Structured Output, and Self-check — **every move from earlier in this chapter is in here**.

---

Next: [§1.4 Evaluation & Iteration →](./04-evaluation.md)
