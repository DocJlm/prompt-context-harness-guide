---
title: §1.2 七大模式
description: Zero-shot · Few-shot · CoT · Self-Consistency · ToT · ReAct · Structured Output
---

# §1.2 七大模式

> 模式不是教条。每一种模式都对应一个具体的失败场景——**你先要会诊断问题，再选模式**。

## 模式速查表

| # | 模式 | 一句话 | 典型适用 | 主要代价 |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **Zero-shot** | 不给例子，直接问 | 简单、有先验的任务 | — |
| 2 | **Few-shot** | 给 2–5 个示例 | 风格 / 格式有特异要求 | 上下文消耗 |
| 3 | **Chain-of-Thought** | "Let's think step by step" | 多步推理、数学、逻辑 | 输出变长 |
| 4 | **Self-Consistency** | 跑 N 次取多数 | 推理任务、希望抗噪 | N× 调用成本 |
| 5 | **Tree-of-Thought** | 树形枚举分支 + 评估 | 搜索 / 规划类难题 | 复杂、慢 |
| 6 | **ReAct** | Reason + Act 交错 | 需要工具调用 | 跨多轮 |
| 7 | **Structured Output** | 强制 JSON / Schema | 要被下游程序消费 | 偶尔会过约束 |

## 模式 1 · Zero-shot

最朴素的形式：**给指令，不给例子**。

```text
将下面的句子翻译为日语：
"今天天气真不错。"
```

什么时候用？
- 任务**广泛常见**（模型见过几千万次）。
- 你不在乎风格细节，只要语义对。

什么时候**不要**用？
- 输出需要符合**你团队特定的格式 / 风格**。
- 任务有**反直觉**的边界条件（如"翻译时保留所有英文专有名词"）。这类要求 Zero-shot 经常被忽略。

## 模式 2 · Few-shot

给 2–5 个**精挑的**示例。

```text
任务：把用户反馈分类为 [bug / feature / praise / other]。

示例 1:
用户: "登录页一直转圈进不去。"
标签: bug

示例 2:
用户: "如果能加个夜间模式就完美了。"
标签: feature

示例 3:
用户: "客服 5 分钟响应，太赞了！"
标签: praise

请分类：
用户: "{{input}}"
标签:
```

::: 关键
**示例的多样性 > 示例的数量**。Anthropic 的指南原话："examples should be a curated set of diverse, **canonical** examples"。给 3 个相似的例子，不如给 3 个**覆盖不同边界**的例子。
:::

实战 trick：
- 把 few-shot 写成 `assistant` 角色的多轮历史，**比写在 `user` 里更有效**（被模型当成"我自己说过的话"）。
- 示例顺序有影响——把**最重要**或**最易错**的放最后。
- 示例里要包含**正常 + 边界 + 反例**。

## 模式 3 · Chain-of-Thought (CoT)

**让模型在给出答案前，先写出推理过程**。

```text
请逐步推理后再给最终答案。

问题：一个商品原价 200 元，先涨价 20%，再打 8 折，最终多少钱？
推理：
最终答案：
```

实现方式有两种：

1. **显式触发**（Zero-shot CoT）：在 prompt 里加 "Let's think step by step." / "请逐步推理。"
2. **隐式触发**（结合 Few-shot）：在示例里**写出**推理过程，模型会照搬。

> ⚠️ **GPT-5 / Claude 4.x / DeepSeek-R1 这类推理模型自带 CoT**，开发者**不需要再**显式触发，反而**会干扰**。OpenAI 的官方指南明确说："don't ask reasoning models to think step by step"。所以使用 CoT 时**要看模型**：传统模型用，推理模型别用。

## 模式 4 · Self-Consistency

CoT 有个问题：**单次推理可能走错路**。

Self-Consistency 的思路：**跑 N 次 CoT（高 temperature），对最终答案投票**。

```python
answers = []
for _ in range(5):
    r = chat(prompt, temperature=0.8)
    answers.append(extract_final_answer(r))
final = majority_vote(answers)
```

适用：
- 数学题、逻辑题、SQL 生成等**有唯一正解**的任务。
- 单次正确率 > 50%，但有波动。

代价：5× 调用成本。在评估阶段非常有用，生产环境只在关键路径用。

## 模式 5 · Tree-of-Thought (ToT)

更激进：把 CoT 从"一条线"扩成"一棵树"——每一步生成多个候选分支，用模型自己**评估** + **剪枝**。

```
       问题
       ├─ 思路A → 子步骤A1 → ...
       ├─ 思路B → 子步骤B1 → ...
       └─ 思路C → 子步骤C1 → ...
                 ↓
            评分 + 选最优
```

实现复杂，工业界用得不多。**了解概念即可**，真正生产里这类问题更多是用 ReAct + 工具搜索来解决。

## 模式 6 · ReAct（Reason + Act）

> "Reasoning **and** Acting" — Yao et al., 2022

让模型在每一步**交替**进行：

```
Thought: 我需要查一下今天的天气。
Action: search("today's weather in Beijing")
Observation: 北京今日多云，22-30°C。
Thought: 现在我可以回答用户了。
Final Answer: 北京今日多云，22-30°C，建议穿薄外套。
```

这是**所有 Agent 系统的基础模式**。第 3 章我们会亲手实现它。

ReAct 的 Prompt 模板（简化）：

```text
你可以用以下工具：
- search(query): 搜索网页
- calc(expression): 计算

按下面格式输出，直到产出 Final Answer：
Thought: <你的思考>
Action: <工具名>(<参数>)
Observation: <工具返回结果，由系统填入>
... (可重复多轮)
Final Answer: <最终答案>

问题：{{question}}
```

::: 注意
ReAct 在 prompt 层只是模式，**真正可用还要靠 Harness 拦截 `Action:` 行、调用工具、把结果回填到 `Observation:`**——这就是第 3 章的内容。
:::

## 模式 7 · Structured Output

**让模型输出严格符合 schema 的 JSON / YAML / XML**。

三种实现方式，从弱到强：

### a) Prompt 软约束

```text
请以如下 JSON 输出（不要包含其他内容）：
{"sentiment": "<positive|negative|neutral>", "score": <0-1>}
```

模型大多数时候会听话，但偶尔会输出 markdown code fence 或多余注释。**生产不推荐单用**。

### b) Function Calling / Tool Use

OpenAI、Claude、DeepSeek 都支持。开发者定义一个 schema，模型生成的内容会被**API 层**保证为合法 JSON：

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

模型"调用"这个函数时，参数就是你要的结构化输出。

### c) Structured Outputs 模式（OpenAI / 部分模型）

直接提供 `response_format` 或 JSON Schema，**API 保证 100% 合法**：

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

> **生产建议**：能用 (c) 就用 (c)；不支持的话用 (b)；只有 (a) 可用时**一定要加 `json.loads` 异常重试**。

## 模式怎么搭？一个组合范例

把上面几招组合起来——一个**生产级的客服意图分类 Prompt**：

```text
# 角色
你是 X 公司客服系统的意图分类器。

# 任务
将用户消息分类为以下意图之一：[退款 / 物流 / 售后维修 / 投诉 / 其他]。

# 推理（CoT）
在给出分类前，先用 1-2 句话写出你的判断依据。

# 示例（Few-shot, 涵盖正常 + 边界）
用户: "我上周买的鞋子开胶了，能换吗？"
判断依据: 涉及商品质量问题，且提到"换"，属于售后维修。
分类: 售后维修

用户: "我要投诉你们物流，包裹丢了！"
判断依据: 用户使用了"投诉"一词，但核心问题是物流丢件——按业务优先级归到"物流"。
分类: 物流

用户: "可以介绍下你们公司吗？"
判断依据: 无明确售后/物流相关意图。
分类: 其他

# 输出格式（Structured Output via JSON）
仅输出以下 JSON，不要任何额外文字：
{"reason": "<判断依据>", "intent": "<分类>"}

# 待分类消息
用户: "{{message}}"
```

这一段里**用了 5 个模式**：Role / Task / CoT / Few-shot（含边界）/ Structured Output。这是大多数生产场景的最佳实践骨架。

---

下一节：[§1.3 进阶：Meta-prompting & GPT-5 时代 →](./03-advanced.md)
