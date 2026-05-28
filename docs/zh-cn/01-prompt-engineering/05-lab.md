---
title: §1.5 动手实验 · Lab 1
description: 跑通 5 个 demo，把第 1 章学到的全部肌肉打开
---

# §1.5 动手实验：Lab 1

## 实验目标

跑完 Lab 1，你会**亲手把第 1 章所有概念落地一遍**：

| Demo | 你会做什么 | 学到什么 |
| :---: | :--- | :--- |
| 1 | Zero-shot 情感分类 | API 调用基础、温度参数影响 |
| 2 | Few-shot + 边界示例 | 示例多样性的威力 |
| 3 | CoT vs 直接回答 | 推理题上 +20% 准确率 |
| 4 | Structured Output（JSON Schema） | 让下游程序直接消费 |
| 5 | 自建一个 Eval Loop | Golden set + acc 报告 |

## 准备

```bash
cd code/lab1-prompting
pip install -r requirements.txt

export OPENAI_API_KEY=sk-xxxxx           # 必填
export OPENAI_BASE_URL=https://...       # 可选：DeepSeek/通义/智谱等任意 OpenAI-Compatible
export MODEL=gpt-4o-mini                 # 可选：默认 gpt-4o-mini
```

> 💡 用国内模型？以 DeepSeek 为例：  
> `export OPENAI_BASE_URL=https://api.deepseek.com/v1`  
> `export OPENAI_API_KEY=<deepseek-key>`  
> `export MODEL=deepseek-chat`

## Demo 1 · Zero-shot

```bash
python 01_zero_shot.py
```

代码导读：

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

**观察什么**：
- 输出是不是只有一个词？通常**不是**——模型会多说一句解释。
- 把 temperature 改成 1.5 跑 5 次——开始随机。

## Demo 2 · Few-shot

```bash
python 02_few_shot.py
```

关键改动：在 messages 里塞了 3 个示例对：

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

**观察什么**：
- 输出是否变得只有一个词？
- 加一句反讽测试："这服务真'好'啊，让我等了一小时"——会被 zero-shot 错判，few-shot 加一个反讽例就能搞定。

## Demo 3 · Chain-of-Thought

```bash
python 03_cot.py
```

数学题 baseline：

```python
PROMPT_NAIVE = "一辆车以 60km/h 行驶 2.5 小时，再以 80km/h 行驶 1.5 小时，平均速度是多少？"

PROMPT_COT = PROMPT_NAIVE + "\n\n请逐步推理后再给出答案。"
```

跑 20 次平均，CoT 通常正确率从 ~50% 跳到 ~90%。

> ⚠️ 如果你用 DeepSeek-R1 / GPT-5 / Claude 4.x，**不要加 "请逐步推理"**——它们自带推理。换成 GPT-4o-mini / Qwen-Plus 等普通模型看效果。

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

**观察什么**：
- 输出 100% 是合法 JSON 且字段齐。
- 故意丢一段不含电话的输入："我叫张三，住北京。"——看看模型怎么填 `phone` 字段（应该是空串而不是编一个）。

## Demo 5 · 跑一个 Eval Loop

```bash
python 05_eval_loop.py
```

这个 demo 跑两个 prompt（v1 zero-shot vs v2 few-shot + structured output），在一个 20-case 的 golden set 上算 accuracy。

```
[v1] Accuracy: 75.0%  (15/20)
[v2] Accuracy: 95.0%  (19/20)
[v1 → v2] +20% absolute, with no extra cost.
```

**你应该看到 v2 显著优于 v1**。如果没有：
- 检查 golden set 是不是覆盖了 v1 的弱项？
- 把 temperature 设 0 让结果可复现。

## 实验作业

跑完 5 个 demo 之后，给自己留这几道作业：

1. 把 Demo 2 的 few-shot 例子从 3 个删到 1 个，跑 Eval，acc 跌多少？
2. 把 Demo 3 的题目换成你 GRE 错过的真题，看 CoT 还能不能解。
3. 把 Demo 4 的 schema 加一个 `gender` 字段（required），但输入里**不包含**性别信息——模型怎么应对？把它和 OpenAI 的 *strict mode* 的 trade-off 写进笔记。
4. 把 Demo 5 的 golden set 扩到 40 个 case，加入：(a) 反讽 (b) 多语种混合 (c) 极短输入。重新跑两版 prompt，记录 acc 变化。

完成这 4 道作业之后，你**真正掌握了第 1 章**。

---

下一节：[§1.6 参考文献 →](./references.md)
