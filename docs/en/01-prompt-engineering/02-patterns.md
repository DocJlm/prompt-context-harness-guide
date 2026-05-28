---
title: §1.2 The Seven Patterns
description: Zero-shot · Few-shot · CoT · Self-Consistency · ToT · ReAct · Structured Output
---

# §1.2 The Seven Patterns

> Patterns are not dogma. Each pattern corresponds to a specific failure scenario—**you have to diagnose the problem first, then pick the pattern**.

## Pattern Cheat Sheet

| # | Pattern | One Sentence | Typical Use | Main Cost |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **Zero-shot** | Ask directly, no examples | Simple tasks with strong priors | — |
| 2 | **Few-shot** | Provide 2–5 examples | Style / format has specific requirements | Context consumption |
| 3 | **Chain-of-Thought** | "Let's think step by step" | Multi-step reasoning, math, logic | Longer outputs |
| 4 | **Self-Consistency** | Run N times and majority-vote | Reasoning tasks, noise resistance | N× call cost |
| 5 | **Tree-of-Thought** | Enumerate tree branches + evaluate | Search / planning problems | Complex, slow |
| 6 | **ReAct** | Interleave Reason + Act | Need tool calls | Multi-turn |
| 7 | **Structured Output** | Force JSON / Schema | Consumed by downstream programs | Occasionally over-constrains |

## Pattern 1 · Zero-shot

The most basic form: **give an instruction, no examples**.

```text
Translate the following sentence into Japanese:
"今天天气真不错。"
```

When to use:
- The task is **broadly common** (the model has seen it tens of millions of times).
- You don't care about stylistic details, only that the semantics are right.

When **not** to use:
- The output must conform to **your team's specific format / style**.
- The task has **counterintuitive** edge constraints (like "preserve all English proper nouns when translating"). Zero-shot frequently ignores such requirements.

## Pattern 2 · Few-shot

Give 2–5 **carefully selected** examples.

```text
Task: Classify user feedback as [bug / feature / praise / other].

Example 1:
User: "The login page just keeps spinning, can't get in."
Label: bug

Example 2:
User: "It would be perfect if you added a night mode."
Label: feature

Example 3:
User: "Customer service responded in 5 minutes, amazing!"
Label: praise

Please classify:
User: "{{input}}"
Label:
```

::: key
**Example diversity > example count**. Anthropic's guide says verbatim: "examples should be a curated set of diverse, **canonical** examples." Three similar examples are worse than three examples that **cover different edges**.
:::

Field tricks:
- Writing few-shot as multi-turn history under the `assistant` role is **more effective than placing it under `user`** (the model treats it as "things I have said myself").
- Example order matters—place the **most important** or **most error-prone** at the end.
- Examples should include **normal + edge + counter-examples**.

## Pattern 3 · Chain-of-Thought (CoT)

**Have the model write out its reasoning before giving an answer.**

```text
Reason step by step, then give the final answer.

Question: An item originally costs 200 yuan. First the price increases by 20%, then it gets a 20% discount. What's the final price?
Reasoning:
Final answer:
```

There are two ways to invoke it:

1. **Explicit trigger** (Zero-shot CoT): add "Let's think step by step." / "Please reason step by step." in the prompt.
2. **Implicit trigger** (combined with Few-shot): **write out** the reasoning in the examples, and the model will copy the style.

> ⚠️ **Reasoning models like GPT-5 / Claude 4.x / DeepSeek-R1 already do CoT internally**, so developers **should not** trigger it explicitly—doing so **interferes**. OpenAI's official guide says explicitly: "don't ask reasoning models to think step by step." So when using CoT, **check the model**: use it on traditional models, don't use it on reasoning models.

## Pattern 4 · Self-Consistency

CoT has a problem: **a single inference may go down the wrong path**.

Self-Consistency's idea: **run N CoT inferences (with high temperature) and vote on the final answer**.

```python
answers = []
for _ in range(5):
    r = chat(prompt, temperature=0.8)
    answers.append(extract_final_answer(r))
final = majority_vote(answers)
```

Applicable to:
- Math problems, logic problems, SQL generation, and other tasks with a **unique correct answer**.
- Single-shot accuracy > 50% but with variance.

Cost: 5× call cost. Very useful at evaluation time; use only on critical paths in production.

## Pattern 5 · Tree-of-Thought (ToT)

More aggressive: extend CoT from "one line" to "a tree"—each step generates multiple candidate branches, and the model itself **scores** and **prunes**.

```
       Problem
       ├─ Idea A → sub-step A1 → ...
       ├─ Idea B → sub-step B1 → ...
       └─ Idea C → sub-step C1 → ...
                 ↓
            Score + pick best
```

Complex to implement, rarely used in industry. **Understand the concept**; in real production, such problems are more often solved with ReAct + tool search.

## Pattern 6 · ReAct (Reason + Act)

> "Reasoning **and** Acting" — Yao et al., 2022

Have the model **alternate** at each step:

```
Thought: I need to check today's weather.
Action: search("today's weather in Beijing")
Observation: Beijing today: cloudy, 22–30°C.
Thought: Now I can answer the user.
Final Answer: Beijing today: cloudy, 22–30°C. Recommend a light jacket.
```

This is **the foundational pattern for all Agent systems**. We'll implement it hands-on in Chapter 3.

ReAct prompt template (simplified):

```text
You can use the following tools:
- search(query): search the web
- calc(expression): compute

Output in the following format until a Final Answer is produced:
Thought: <your thought>
Action: <tool_name>(<args>)
Observation: <tool result, filled in by the system>
... (can repeat multiple turns)
Final Answer: <final answer>

Question: {{question}}
```

::: note
ReAct is only a pattern at the prompt level. **It becomes truly usable only when the Harness intercepts the `Action:` line, calls the tool, and writes the result back into `Observation:`**—which is the subject of Chapter 3.
:::

## Pattern 7 · Structured Output

**Force the model to output JSON / YAML / XML that conforms strictly to a schema.**

Three implementations, weakest to strongest:

### a) Prompt-level soft constraints

```text
Please output as the following JSON (no other content):
{"sentiment": "<positive|negative|neutral>", "score": <0-1>}
```

The model usually obeys, but occasionally adds markdown code fences or extra comments. **Not recommended alone in production.**

### b) Function Calling / Tool Use

OpenAI, Claude, and DeepSeek all support this. The developer defines a schema, and the model's output is **guaranteed by the API layer** to be valid JSON:

```python
tools = [{
    "type": "function",
    "function": {
        "name": "classify_sentiment",
        "parameters": {
            "type": "object",
            "properties": {
                "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                "score": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["sentiment", "score"]
        }
    }
}]
```

When the model "calls" this function, the arguments are your structured output.

### c) Structured Outputs mode (OpenAI / some models)

Provide a `response_format` or JSON Schema directly, and **the API guarantees 100% validity**:

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    response_format={
        "type": "json_schema",
        "json_schema": {"name": "result", "schema": {...}, "strict": True}
    }
)
```

> **Production advice**: use (c) when you can; (b) when (c) isn't available; if only (a) is on the table, **always wrap with `json.loads` exception retry**.

## How to Compose Patterns? A Combined Example

Combine the moves above into a **production-grade customer-service intent classifier prompt**:

```text
# Role
You are the intent classifier for X Company's customer service system.

# Task
Classify the user's message as one of: [refund / logistics / repair / complaint / other].

# Reasoning (CoT)
Before giving the classification, write your judgment basis in 1–2 sentences.

# Examples (Few-shot, covering normal + edges)
User: "The shoes I bought last week have come unglued, can I exchange them?"
Basis: Involves a product quality issue and mentions "exchange"—this is repair.
Class: repair

User: "I want to file a complaint about your logistics, my package is lost!"
Basis: The user used the word "complaint", but the core issue is a lost package—by business priority, file it under "logistics".
Class: logistics

User: "Can you tell me about your company?"
Basis: No clear after-sales / logistics intent.
Class: other

# Output format (Structured Output via JSON)
Output only the following JSON, no extra text:
{"reason": "<basis>", "intent": "<class>"}

# Message to classify
User: "{{message}}"
```

This snippet **uses 5 patterns**: Role / Task / CoT / Few-shot (with edges) / Structured Output. This is the best-practice skeleton for most production scenarios.

---

Next: [§1.3 Advanced: Meta-prompting & the GPT-5 era →](./03-advanced.md)
