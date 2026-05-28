---
title: §1.3 Advanced · Meta-prompting & the GPT-5 Era
description: Using the model to improve the model; Reasoning Effort, Eagerness, Persistence, Tool Preambles
---

# §1.3 Advanced: Meta-prompting & the GPT-5 Era

> "Most folks know prompt engineering. But to get the most out of AI agents, you need context engineering."  
> — Anthropic

> "**Your prompts are code, your .md/.json files are state on disk.**"  
> — [Peter Steinberger (author of OpenClaw), *Essential Reading for Agentic Engineers*, 2025-06-30](https://steipete.me/posts/2025/essential-reading)

By 2025–2026, the models themselves can write better prompts than you can. So **the center of advanced prompt engineering has shifted from "how to write" to "how to tune"** — tuning reasoning depth, tuning initiative, tuning tool-use style.

## 0. Paradigm Shift · Karpathy's "Software 3.0"

At YC AI Startup School 2025, Karpathy gave the shift a name:

> "Imo fair to say that software is changing quite fundamentally again. **LLMs are a new kind of computer, and you program them *in English*. Hence I think they are well deserving of a major version upgrade in terms of … Software 3.0.**"  
> — [Karpathy, *Software Is Changing (Again)*, YC AI 2025-06-17](https://www.youtube.com/watch?v=LCEmiRjPEtQ)

And:

> "**The hottest new programming language is English.**"

What this means for the engineering in this chapter: **writing a prompt = writing code**. You should version-control it, test it with evals, review it via PRs, track it with a changelog. Peter Steinberger's line "prompts are code, your .md/.json files are state on disk" is the engineering-flavored version of the same idea.

This is also why §1.4 on evaluation matters so much — **a prompt without an eval is code without unit tests**.

## 1. Meta-prompting: Let the Model Improve Its Own Prompt

OpenAI says it plainly in the GPT-5 Prompting Guide: **GPT-5 is a strong metaprompter**.

The simplest metaprompt template:

```text
I want you to **evaluate and improve** a prompt.

Original prompt:
"""
{{original_prompt}}
"""

It performs poorly on the following cases:
Case 1: input X → expected Y → actual Z
Case 2: ...

Please output, in this structure:
1. Diagnosis of failure (one per case)
2. Suggested improvements
3. The full rewritten prompt
```

This metaprompt is itself a prompt — you can also feed it back to the model and ask how to improve it. **It's recursive.**

### Three real-world uses of meta-prompting

1. **Cold start**: When you don't know how to begin a new prompt, ask the model to generate a first version from a one-line requirement.
2. **Diagnose**: When you have a prompt that misfires, feed the bad cases to the model and let it diagnose.
3. **Refactor**: Ask the model to compress a long prompt (**note**: tell it which parts must not change).

### Pitfalls of meta-prompting

- ❌ Letting the model "freestyle" — it will over-add boilerplate. Keep instructions tight.
- ❌ Changing too much at once — iterate on one dimension at a time (fix accuracy first, then length, then format).
- ❌ Shipping the metaprompt's output **directly** — it must be **eval-gated** (see §1.4).

## 2. Reasoning Effort: How Much Brainpower?

GPT-5, Claude 4.x, DeepSeek-R1, Qwen3-Thinking and others have introduced a **reasoning budget** knob. OpenAI uses the `reasoning_effort` parameter; Anthropic uses a `thinking` block.

```python
# OpenAI GPT-5 style
response = client.chat.completions.create(
    model="gpt-5",
    messages=messages,
    reasoning_effort="medium",  # "minimal" | "low" | "medium" | "high"
)
```

| Effort | Suited for | Cost |
| :--- | :--- | :--- |
| `minimal` | Single-step classification, extraction, translation | Near-instant |
| `low` | Simple code, rule-based reasoning | Slightly slower |
| `medium` | **Default.** Multi-step tasks | Moderate |
| `high` | Complex math, long-document reasoning | Slow, expensive |

::: tip OpenAI's official guidance
> "Scale `reasoning_effort` up for complex tasks, down for efficiency; default is medium."

**Best practice**: Run your Eval at medium first, then decide whether to tune. **Don't default to high** — it will make simple tasks slow and expensive.
:::

## 3. Agentic Eagerness: Tuning "Initiative"

This is a brand-new dimension introduced by GPT-5. In multi-step tasks, **how aggressively should the model explore / call tools**?

### Prompt to decrease eagerness

```
"Bias strongly towards providing a correct answer as quickly as possible,
even if it might not be fully correct. Usually, this means an absolute
maximum of 2 tool calls."
```

### Prompt to increase eagerness

```
"Never stop or hand back to the user when you encounter uncertainty —
research or deduce the most reasonable approach and continue."
```

::: tip Key judgment call
- **Customer support / coding**: lean **eager** — don't keep stopping to ask "please provide more information."
- **Finance / medicine / destructive operations**: lean **not eager** — better to ask than to act recklessly.
:::

## 4. Tool Preambles: Say a Line Before Calling a Tool

Another habit introduced by GPT-5: **before each tool call, have the model say one line telling the user what it's about to do.**

```text
Before each tool call, tell the user in one short sentence what you are about to do.
For example:
"Let me take a look at the file structure first…"
Then make the ListFiles call.
```

Why it matters:
- **The user can follow along** — reduces black-box anxiety.
- **Interpretability** — the model's intent shows up in logs.
- **Reduces hallucination** — by making the model "speak then act," you force it to plan first.

This is standard practice in coding agents (Claude Code, Cursor, Codex).

::: tip Side note · Karpathy names "Vibe Coding"
In February 2025 Karpathy tweeted what put "vibe coding" into the English-internet dictionary:

> "There's a new kind of coding I call '**vibe coding**', where **you fully give in to the vibes**, embrace exponentials, and forget that the code even exists. It's possible because the LLMs (e.g. Cursor Composer w Sonnet) are getting too good. Also I just talk to Composer with SuperWhisper and I **barely even touch the keyboard**. …  
> I 'Accept All' always, **I don't read the diffs anymore**. When I get error messages I just copy paste them in with no comment, usually that fixes it. …  
> I'm building a project or webapp, but it's not really coding — **I just see stuff, say stuff, run stuff, and copy paste stuff, and it mostly works**."  
> — [@karpathy, 2025-02-02](https://x.com/karpathy/status/1886192184808149383)

Notice: **this isn't "prompting" — this is "talk to the model in natural language + don't read the diffs."** The "prompt engineering" it requires is actually the least of all — Karpathy emphasizes "talk to Composer with SuperWhisper" and doesn't even touch the keyboard.

**The boundary of vibe coding**: Karpathy himself notes this suits "weekend projects / throwaway prototypes." Production code still needs the §1.4 evals and the Persistence/Eagerness controls of §1.3. Peter Steinberger pushes this practice to its extreme — see §3.2 §8.2.
:::

## 5. Persistence: Make the Model Finish the Task

This comes from OpenAI's official guidance, and **almost every agentic scenario needs it**:

```text
You are an agent — please keep going until the user's query is completely
resolved, before ending your turn and yielding back to the user. Only
terminate your turn when you are sure the problem is solved.
```

This solves a classic bug: **the model "loses its nerve" partway and stops**, leaving a half-finished job on your hands.

## 6. Output Format, Advanced: Make the Model "Self-Check"

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

The effect of this trick in production is striking — **to fill in the `self_check` field, the model automatically revisits whether its answer meets the constraints**. You get a free layer of self-reflection.

## 7. Adaptation for Chinese Models

Chinese-domestic models (Tongyi Qwen, Zhipu GLM, DeepSeek, Moonshot Kimi, Baichuan, Wenxin) mostly support OpenAI-compatible APIs, so the prompt templates above are **almost directly reusable**. But there are a few notable differences:

| Model family | Tendencies / things to watch |
| :--- | :--- |
| **Qwen** | More stable on Chinese prompts; works well with XML tags + JSON Schema |
| **GLM** | Prefers Markdown structure; CoT is triggered with "please reason step by step" |
| **DeepSeek-V/R series** | The R series has strong built-in CoT — **do not** add step-by-step instructions |
| **Kimi** | Excellent long context, especially suited to very long RAG |
| **Baichuan / Wenxin** | Chinese phrasing is more "polite"; prefer "expert" role framings |

::: tip General advice
**Write and tune all prompts on GPT-4o-mini or Claude Haiku first; then** run an Eval on the Chinese models. Cross-model robustness is the core production metric.
:::

## 8. Putting It All Together: A "GPT-5 Era" Prompt

```text
# Role & Goal
You are a senior SRE Agent responsible for diagnosing production incidents.

# Persistence
Do not stop until the incident is diagnosed AND a fix is proposed.

# Eagerness
Be eager about tool calls: better to read one more log line than to miss something.
Maximum budget: 8 tool calls.

# Tool Preamble
Before each tool call, tell the ops engineer in one sentence what you are about to do.

# Reasoning
Use thinking for complex correlation analysis. Skip thinking for simple command stitching.

# Output
Final answer in this JSON:
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

This single prompt simultaneously contains Role, Persistence, Eagerness, Preamble, Reasoning, Structured Output, and Self-check — **every trick from earlier in the chapter is in there**.

---

Next: [§1.4 Evaluation & Iteration →](./04-evaluation.md)
