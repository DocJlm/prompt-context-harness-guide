---
title: §1.4 Evaluation & Iteration
description: How do you know your prompt is good? And how do you change it scientifically?
---

# §1.4 Evaluation & Iteration

> Prompt Engineering without Eval is like code without unit tests.

## 1. Why Eval Is Mandatory

**A prompt is a kind of code, but it is "probabilistic code."**

- Regular code: fix one bug at a time.
- Prompts: changing one line may fix one case and break three.

You can refactor untested code once without disaster; refactor five times and disaster is guaranteed. Prompts are the same.

## 2. Minimum Viable Eval: A Hand-Rolled Golden Set

For v1, no need for LangSmith or Promptfoo. **Start with 20 lines of Python**:

```python
# eval_golden_set.py
import json
from openai import OpenAI

client = OpenAI()

GOLDEN_SET = [
    {"input": "登录页一直转圈进不去。", "expected": "bug"},
    {"input": "如果能加个夜间模式就完美了。", "expected": "feature"},
    {"input": "客服 5 分钟响应，太赞了！", "expected": "praise"},
    # ... 20-50 cases
]

def run(prompt_template, case):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt_template.format(input=case["input"])}],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()

def evaluate(prompt_template, name):
    correct = 0
    failures = []
    for case in GOLDEN_SET:
        out = run(prompt_template, case)
        if case["expected"].lower() in out.lower():
            correct += 1
        else:
            failures.append({"input": case["input"], "expected": case["expected"], "got": out})
    acc = correct / len(GOLDEN_SET)
    print(f"[{name}] Accuracy: {acc:.1%}  ({correct}/{len(GOLDEN_SET)})")
    return acc, failures
```

**This is the minimum Eval loop**. A run costs pennies, but tells you:

- Did the prompt change make things better or worse?
- Which cases keep failing?

## 3. The "Four Dimensions" of Eval

| Dimension | What it measures | Examples |
| :--- | :--- | :--- |
| **Correctness** | Is the answer right? | Is the class correct? Are extracted field values correct? |
| **Format** | Is the format valid? | Does the JSON parse? Are all fields present? |
| **Style** | Does the style match? | Length, tone, Chinese-English mixing? |
| **Cost** | Tokens / dollars? | Input / output tokens, p99 latency |

**Production Eval must look at all four dimensions.** Looking only at Correctness easily produces "accurate but expensive but slow" prompts.

## 4. LLM-as-Judge: Use a Model to Evaluate a Model

When the task is open-ended generation (summarization, rewriting, customer replies), there's no ground truth—how do you eval?

**Use a stronger / equally strong model as the judge**:

```python
JUDGE_PROMPT = """You are a strict output evaluator.

Task description:
{task_description}

Model output:
{output}

Please score on the following dimensions (1-5 integers):
- relevance (does it address the task?)
- factuality (factual correctness)
- format (format compliance)
- safety (no sensitive content)

Output only JSON:
{{"relevance": <int>, "factuality": <int>, "format": <int>, "safety": <int>, "comment": "<one-sentence reason>"}}
"""
```

::: note
- LLM-as-Judge **has biases**: it usually prefers long outputs and the style of models from the same family as the judge.
- Solutions: **use multiple different models as judges and vote**; **sample 10–20% for human spot-check** to prevent judge drift.
- Anthropic emphasizes in *Harness Design*: "agents tend to respond by confidently praising the work—even when, to a human observer, the quality is obviously mediocre."
:::

## 5. Debugging: How to Localize Failure Causes

When a case fails, **don't rush to change the prompt**. Investigate in this order:

```
1. Is the model itself capable enough?
   → Try a stronger model. Still wrong → change prompt; correct → consider if a smaller model + better prompt can do it.

2. Is the input data faulty?
   → Show the same input to a human—can they answer correctly?
   → If the data is noisy → clean data first, not the prompt.

3. Which line of the prompt is responsible?
   → Bisect: delete half and see if it still fails.

4. Is it temperature-induced flakiness?
   → Set temperature=0, fix the seed, run 3 times.
   → All consistent → systematic problem; inconsistent → decoding-randomness problem.

5. Token truncation?
   → Check whether max_tokens is fully used.
```

## 6. Prompt Version Management

**Manage prompts like code.** Even just putting a prompt into a `.py` file and `git commit`-ing it is better than leaving it in a notebook cell.

Minimum convention:

```python
# prompts/classify_v3.py
"""
Version: v3 (2026-05-28)
Author: zhang-san
Eval: 95.2% on golden_v2 (40 cases)
Notes:
  - v3 vs v2: added "return other directly for short inputs" constraint
  - v3 vs v1: added self_check field
"""

PROMPT = """..."""
```

Or use dedicated tools:

- **Promptfoo**: open source, local, `jest`-like experience.
- **LangSmith**: LangChain ecosystem, cloud trace + eval.
- **Weights & Biases Prompts**: extension of the traditional ML toolstack.
- **PromptLayer / Helicone**: lightweight prompt logging.

::: practical advice
**Put prompts in git first, think about tooling later.** I've seen too many teams adopt LangSmith while their prompts still live in chat groups—putting the cart before the horse.
:::

## 7. Iteration Rhythm: Change One Thing at a Time

```
v1: baseline
  ├─ eval: 76% correctness
  
v2: add few-shot examples
  ├─ eval: 84% correctness  ← one change
  
v3: add self_check field
  ├─ eval: 89% correctness, format 100%  ← one change
  
v4: tune temperature AND change system prompt at once
  ├─ eval: 87% correctness  ← two changes, regression—you don't know which caused it
  
✗ Counter-example: v4 is the bad example
```

**Each commit changes one variable**, repeatable, reversible.

## 8. Case Study: Optimizing a Prompt from 70% to 95%

Below is a real (simplified) case (sentiment classification task):

| Version | Change | Acc | Notes |
| :---: | :--- | :---: | :--- |
| v1 | Zero-shot "judge sentiment" | 71% | baseline |
| v2 | + Role: "You are a financial sentiment analyst" | 74% | Role tightens the prior |
| v3 | + Few-shot (3 examples) | 82% | Includes 1 sarcasm edge case |
| v4 | + CoT "list keywords before judging" | 87% | Explicit reasoning |
| v5 | + Structured Output + self_check | 91% | 100% format compliance |
| v6 | + Subdivide "neutral" into "neutral-positive / neutral-negative leaning" | 95% | Business-understanding win |

Note v6 isn't a victory of prompt technique—it's a **victory of business understanding**. But you need the engineering muscle of v1–v5 to stabilize the baseline before you can see that "business refinement" can lift things further.

## 9. When to Stop?

- ✅ Acc / metrics show **no significant gain for two rounds in a row**.
- ✅ Failure cases are **clustered in edge-business**, not the main flow.
- ✅ Call cost / latency are **within budget**.
- ❌ Don't write a 3000-character prompt to chase +1%—**diminishing returns, more brittle**.

**At this point**: you've mastered the core muscle of Prompt Engineering. The next step is Context Engineering—but before that, **run Lab 1 with your own hands first**.

---

Next: [§1.5 Hands-on Lab →](./05-lab.md)
