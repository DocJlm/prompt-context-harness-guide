---
title: §2.1 上下文的解剖学
description: System / Tools / Examples / History 四件套；注意力预算
---

# §2.1 上下文的解剖学

> "Anthropic's overall guidance across different components of context (system prompts, tools, examples, message history, etc.) is to be **thoughtful and keep your context informative, yet tight**."  
> — Anthropic, *Effective Context Engineering for AI Agents*

## 一、四件套：System / Tools / Examples / History

按 Anthropic 的官方分类，一个 Agent 的上下文由四类组件组成：

| 组件 | 角色 | 典型 token 占比 | 何时变化 |
| :--- | :--- | :--- | :--- |
| **System Prompt** | 谁、做什么、约束、风格 | 1–5K | 几乎不变（每个 Session） |
| **Tool Definitions** | 工具列表 + schema | 1–10K | 几乎不变（启动时确定） |
| **Examples (Few-shot)** | 关键示范 | 0–5K | 偶尔切换 |
| **Message History** | 历史对话 / 工具结果 | 0–180K | **每一轮都在涨** |

注意 **Message History 是动态的大头**——前三项加起来通常 < 20K，剩下 180K 都给 History。**Context Engineering 的核心战场就在这里。**

## 二、System Prompt 的"恰当高度"

Anthropic 给了一个非常有意思的判据：System Prompt 要写在 **"the right altitude"**。

> "Specific enough to guide behavior effectively, yet flexible enough to provide strong heuristics, avoiding both brittle hardcoded logic and vague high-level guidance."

太低（hardcoded）：

```text
当用户提到 "退款" 时，回复：
"好的，您的订单号是？我帮您查询。"
当用户提到 "投诉" 时，回复：
"非常抱歉，我转您给主管。"
...
```

→ 这种写法相当于把规则引擎写进 prompt——一旦用户的说法跟规则不完全匹配，模型就乱。

太高（vague）：

```text
你是一个客服助手。请帮助用户。
```

→ 模型自由发挥，输出风格随机。

**恰当**：

```text
你是 X 公司的客服助手。

【职责】
- 解答订单查询、退款、物流相关问题。
- 涉及投诉时，先共情再引导提供订单号。
- 不能承诺：补偿金额、责任归属、退款时间。

【风格】
- 中文，专业但友好。
- 单条回复不超过 80 字。
- 涉及个人信息时主动遮蔽（手机中间 4 位、地址只保留城市）。

【边界】
- 涉及主管 / 经理 / 法务的请求 → 输出 `{"escalate": true}`。
- 涉及自杀 / 自伤 / 暴力威胁 → 输出 `{"crisis": true, "hotline": "..."}`。
```

→ 给了**职责的范围**、**风格的边界**、**升级的硬规则**，但没把每一句话都写死。

## 三、Tool Definitions：你的"API 文档" 也是 Prompt

工具描述本质上是 prompt——模型靠它的描述决定**什么时候调、怎么调、调谁**。

### 反面 vs 正面：一个工具的 schema

❌ 反面：

```python
{
    "name": "search",
    "description": "Search.",
    "parameters": {"type": "object", "properties": {"q": {"type": "string"}}}
}
```

✅ 正面：

```python
{
    "name": "search_internal_docs",
    "description": (
        "搜索 X 公司内部知识库。**仅用于** 内部产品 / 流程 / 政策类问题。"
        "**不要** 用它搜公开互联网内容（用 `web_search` 工具）。"
        "返回 top-5 段落 + 来源链接。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "查询关键词，中文或英文均可。短语优于句子。"
            },
            "category": {
                "type": "string",
                "enum": ["product", "process", "policy", "any"],
                "description": "限定搜索范围。如不确定填 any。"
            }
        },
        "required": ["query"]
    }
}
```

Anthropic 的原文是："Tools should promote efficiency by returning token-efficient information... must be **self-contained, robust to error, and clear regarding intended use**."

写好 tool description 的几条：

- **名字明确**：`search_internal_docs` 比 `search` 好。
- **范围明确**：什么时候用、什么时候不用。
- **参数说明**：每个 parameter 给一句话描述 + enum。
- **返回的格式描述**：让模型知道接下来怎么用。
- **token-efficient**：工具返回的内容**要简洁**，比如返回结构化 JSON 而不是大段 HTML。

## 四、Examples 的选择：质 > 量

Anthropic 在 *Context Engineering* 里强调：

> "Examples should comprise a curated set of **diverse, canonical** examples portraying expected agent behavior rather than exhaustive edge cases."

**3 个覆盖正常 / 边界 / 反例的 example，比 20 个相似 example 更有用**。理由：

- 上下文预算有限。
- 模型从 examples 里"归纳模式"，模式覆盖度比样本数量更重要。
- 例子之间的**对比**给模型提供决策边界。

实战技巧：动态 few-shot。**根据当前 query，从一个 example pool 里检索 top-k 相似 examples 注入**。这一招在很多客服 / 文档问答系统里把准确率拉了一截。

## 五、Message History：最大的"消耗品"

History 每一轮都在涨。不管它，迟早爆窗口。基本管理策略有三种：

### 策略 A · 截断（Truncation）

最简单：只保留最近 N 轮。

```python
def truncate(messages, max_turns=20):
    return messages[0:1] + messages[-max_turns*2:]  # 保留 system + 最近 N 轮
```

适用：客服等"短期记忆为主"的场景。**问题**：跨轮的关键信息会丢。

### 策略 B · 压缩（Compaction）

把老的多轮对话压成一段摘要：

```
原 messages:
  [系统]、[用户:U1]、[助手:A1]、[用户:U2]、[助手:A2]、... ×50

压缩后:
  [系统]
  [摘要消息]: "用户和助手讨论了 X、Y、Z 三个话题。重要结论：abc。未决问题：def。"
  [用户:U50]、[助手:A50]、[用户:U51]
```

这一招是 **Claude Code、Cursor、Codex 等 Coding Agent 的标配**，下一节我们专门讲。

### 策略 C · 工具结果"瘦身"

工具返回的大段内容（文件全文、长 JSON）**先用一个小模型摘要**，再放进 history：

```python
def fold_tool_result(name, raw_result):
    if len(raw_result) > 2000:
        summary = small_model_summarize(raw_result, max_tokens=300)
        return f"<tool_result name={name}>(folded) {summary}</tool_result>"
    return raw_result
```

实测能把上下文消耗降 50% 以上。

## 六、Context Rot：你不能假装它不存在

这是一个工程上的硬约束。Anthropic 引用过著名的 *Lost in the Middle* / *Needle in a Haystack* 实验：当上下文塞到接近窗口上限时，模型对**中段**信息的回忆率显著下降。

实战影响：

- ⚠️ **关键约束放最前 + 最后**：模型对开头和结尾的注意力最高。
- ⚠️ **不要把 important 数据放在 100K 之后**：除非你做了"提醒"。
- ⚠️ **超过 70% 窗口就要压缩**：不要赌"还有 30% 空间"。

经验阈值：

| 窗口大小 | 安全使用区间 | 必须压缩阈值 |
| :--- | :--- | :--- |
| 32K | < 16K | > 22K |
| 128K | < 60K | > 90K |
| 200K | < 100K | > 140K |
| 1M | < 300K | > 600K |

> "Larger windows don't mean you can stuff more, they mean you have more **headroom to recover from mistakes**." — 一个我自己总结的经验定律。

## 七、把这一节装进脑子：一个上下文流的演化

```
Turn 1 (10K used):
[System 3K] [Tools 5K] [User: "帮我查订单状态" 200t] [Tool result 1K]

Turn 5 (28K used):
[System 3K] [Tools 5K] [Few-shot 2K] [History 15K] [Tool result 3K]

Turn 20 (98K used, 接近阈值):
↓ 触发 Compaction
[System 3K] [Tools 5K] [Few-shot 2K] [Summary of turns 1-15: 4K] [Recent turns 16-20: 18K] [Current: 2K]

Turn 50 (105K used):
↓ 重新 Compaction + 引入 Long-term Memory
[System 3K] [Tools 5K] [Memory note: 用户偏好 / 历史投诉 2K] [Summary 1-45: 5K] [Recent: 15K]
```

注意上面的演化里包含了**截断 + 压缩 + 记忆注入** 三招，下面三节我们逐个讲。

---

下一节：[§2.2 检索：把对的信息塞进窗口 →](./02-retrieval.md)
