---
title: §1.5 Hands-on Lab · Lab 1
description: Run 5 demos to put all the Chapter 1 muscle into action
---

# §1.5 Hands-on Lab: Lab 1

## Lab Goals

After finishing Lab 1, you will **land every Chapter 1 concept with your own hands**:

| Demo | What you'll do | What you'll learn |
| :---: | :--- | :--- |
| 1 | Zero-shot sentiment classification | API call basics, effect of temperature |
| 2 | Few-shot + edge examples | The power of example diversity |
| 3 | CoT vs direct answer | +20% accuracy on reasoning problems |
| 4 | Structured Output (JSON Schema) | Direct consumption by downstream programs |
| 5 | Build your own Eval Loop | Golden set + acc report |

## Setup

```bash
cd code/lab1-prompting
pip install -r requirements.txt

export OPENAI_API_KEY=sk-xxxxx           # required
export OPENAI_BASE_URL=https://...       # optional: any OpenAI-Compatible endpoint (DeepSeek/Tongyi/Zhipu/...)
export MODEL=gpt-4o-mini                 # optional: defaults to gpt-4o-mini
```

> 💡 Using a Chinese model? Example with DeepSeek:  
> `export OPENAI_BASE_URL=https://api.deepseek.com/v1`  
> `export OPENAI_API_KEY=<deepseek-key>`  
> `export MODEL=deepseek-chat`

## Demo 1 · Zero-shot

```bash
python 01_zero_shot.py
```

Code walkthrough:

```python
from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "你是一个情感分类器。"},
        {"role": "user", "content": "请将这条评论分类为 positive / negative / neutral：\n\n这家店服务真差，菜也凉了。"},
    ],
    temperature=0,
)
print(response.choices[0].message.content)
```

**What to observe**:
- Is the output a single word? Usually **not**—the model adds an extra sentence of explanation.
- Set temperature to 1.5 and run 5 times—watch it become random.

## Demo 2 · Few-shot

```bash
python 02_few_shot.py
```

Key change: 3 example pairs are stuffed into messages:

```python
messages = [
    {"role": "system", "content": "你是一个情感分类器，只输出一个词。"},
    {"role": "user", "content": "服务员态度恶劣。"},
    {"role": "assistant", "content": "negative"},
    {"role": "user", "content": "我超级喜欢这本书！"},
    {"role": "assistant", "content": "positive"},
    {"role": "user", "content": "包装一般般，没什么特别。"},
    {"role": "assistant", "content": "neutral"},
    {"role": "user", "content": "这家店服务真差，菜也凉了。"},
]
```

**What to observe**:
- Does the output become just one word?
- Add a sarcasm test: "这服务真'好'啊，让我等了一小时" — zero-shot will misclassify it, but adding one sarcasm example to few-shot fixes it.

## Demo 3 · Chain-of-Thought

```bash
python 03_cot.py
```

Math baseline:

```python
PROMPT_NAIVE = "一辆车以 60km/h 行驶 2.5 小时，再以 80km/h 行驶 1.5 小时，平均速度是多少？"

PROMPT_COT = PROMPT_NAIVE + "\n\n请逐步推理后再给出答案。"
```

Averaging 20 runs, CoT typically jumps accuracy from ~50% to ~90%.

> ⚠️ If you use DeepSeek-R1 / GPT-5 / Claude 4.x, **don't add "please reason step by step"**—they reason internally. Switch to GPT-4o-mini / Qwen-Plus or other regular models to see the effect.

## Demo 4 · Structured Output

```bash
python 04_structured_output.py
```

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "抽取用户消息里的关键字段。"},
        {"role": "user", "content": "我叫张三，电话 13800138000，住在北京市朝阳区。"},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "extract",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "phone": {"type": "string"},
                    "city": {"type": "string"},
                    "district": {"type": "string"},
                },
                "required": ["name", "phone", "city", "district"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
)
import json
data = json.loads(response.choices[0].message.content)
print(data)
```

**What to observe**:
- Output is 100% valid JSON with all fields present.
- Deliberately drop input that has no phone: "我叫张三，住北京。"—see how the model fills the `phone` field (it should be an empty string, not invented).

## Demo 5 · Run an Eval Loop

```bash
python 05_eval_loop.py
```

This demo runs two prompts (v1 zero-shot vs v2 few-shot + structured output) and computes accuracy on a 20-case golden set.

```
[v1] Accuracy: 75.0%  (15/20)
[v2] Accuracy: 95.0%  (19/20)
[v1 → v2] +20% absolute, with no extra cost.
```

**You should see v2 clearly beating v1**. If not:
- Check whether the golden set covers v1's weak spots.
- Set temperature to 0 for reproducibility.

## Lab Exercises

After running the 5 demos, give yourself these exercises:

1. Cut Demo 2's few-shot examples from 3 to 1. Run Eval. How much does acc drop?
2. Replace Demo 3's question with a real GRE problem you got wrong—does CoT still solve it?
3. Add a `gender` field (required) to Demo 4's schema, but feed input that **contains no** gender info—how does the model respond? Write up the trade-offs vs OpenAI's *strict mode* in your notes.
4. Expand Demo 5's golden set to 40 cases, adding: (a) sarcasm, (b) multilingual mixing, (c) extremely short inputs. Re-run both prompt versions and record the acc changes.

After completing these 4 exercises, you've **truly mastered Chapter 1**.

---

Next: [§1.6 References →](./references.md)
