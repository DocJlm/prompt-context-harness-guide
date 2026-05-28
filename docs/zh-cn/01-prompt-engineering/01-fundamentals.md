---
title: §1.1 Prompt 的解剖学
description: System、User、Assistant 三层结构与可控变量
---

# §1.1 Prompt 的解剖学

> 学一门外语之前，得先认识它的语法。

## 一、三段式：System / User / Assistant

现代 Chat 模型的 API 几乎都把消息切成三种角色：

```python
messages = [
    {"role": "system",    "content": "你是一个简洁的中文助手。"},
    {"role": "user",      "content": "把这段英文翻译为中文：Hello world."},
    {"role": "assistant", "content": "你好，世界。"},
    {"role": "user",      "content": "再翻一遍，要更口语。"},
]
```

| Role | 谁在写 | 通常用来放什么 |
| :--- | :--- | :--- |
| `system` | 开发者 | 角色设定、全局指令、输出格式、不可越狱的硬约束 |
| `user` | 用户 | 当下要解决的问题 / 输入数据 |
| `assistant` | 模型 | 历史回答；也可以**人工注入**做 few-shot |

::: 注意
- `system` 不是"超级指令"。模型对它的权重通常**更高**，但**不是无限**。越狱攻击、长上下文稀释，都会削弱它的效力。所以重要约束要**精炼、靠前、可重复**。
- 一些模型（如 Claude）允许在 `system` 里放很长的"角色 + 任务 + 工具"描述，是 Context Engineering 的主战场。
:::

## 二、一段「能跑」的 Prompt 的最小构件

按 Anthropic、OpenAI、阿里云百炼三家的指南综合，一段生产级 Prompt 至少包括下面 6 件：

```
┌─────────────────────────────────────────────────────────────┐
│  1. Role           — 你是谁？                                │
│  2. Task           — 你要做什么？                            │
│  3. Context        — 你需要哪些背景信息？                    │
│  4. Constraints    — 有什么不能做 / 必须做的？               │
│  5. Examples       — （可选）这是 1–3 个示范                 │
│  6. Output Format  — 我希望长什么样？                        │
└─────────────────────────────────────────────────────────────┘
```

> **阿里云百炼 Prompt 工程指南**总结的更短：**任务、上下文、示例、输出格式**——记住这八个字即可。

### 一个反面教材 → 正面教材的对比

**❌ 反面教材**（凑合能跑，但风险很高）：

```
帮我看看这段代码有没有问题。
def divide(a, b): return a/b
```

模型大概率会自由发挥：可能告诉你"看起来还行"，也可能列出 5 条改进。你拿不到稳定输出。

**✅ 正面教材**：

```text
# 角色
你是一名资深 Python 代码审查官。

# 任务
审查以下 Python 函数，列出潜在缺陷。

# 约束
- 只关注：边界值、异常处理、类型安全 这三类问题。
- 每条问题不超过 30 字。
- 如果没有问题，输出 "No issues found."。

# 示例
输入:
def add(a, b): return a+b
输出:
- 边界值: 未处理 a / b 为 None
- 类型安全: 未约束 a, b 必须为数值

# 输出格式
按 Markdown 列表输出，每条以 "- <类别>: " 开头。

# 待审查代码
```python
def divide(a, b): return a/b
```
```

差异：
- 给了 **Role** → 调用模型的"代码审查"先验。
- 给了 **明确的 3 类问题范围** → 不会扯到无关方面。
- 给了 **长度约束** → 输出可预测。
- 给了 **示例** → 风格定锚。
- 给了 **输出格式** → 可直接 `parse`。

## 三、可控变量：分隔符、变量化、Markdown

### 1. 分隔符（Delimiters）

把"指令"和"数据"分开是头号习惯。常见做法：

```text
请总结下面这段会议纪要：

---BEGIN MEETING---
{{transcript}}
---END MEETING---
```

或者用 XML（Claude 模型**特别偏好** XML 标签）：

```xml
<task>总结会议纪要</task>
<transcript>
{{transcript}}
</transcript>
<output_format>
<summary>...</summary>
<action_items><item>...</item></action_items>
</output_format>
```

> 实测在 Claude 上，XML 标签的稳定性 > Markdown > 纯文本。在 GPT 系列上，三者差异不大，但 **Markdown 的可读性最好**。

### 2. 变量化

不要把数据 hardcode 进 prompt。**把 prompt 写成模板**，用 `{{var}}` 或 f-string 注入：

```python
SYSTEM_PROMPT = """你是一名 {role}。
你的任务是 {task}。
约束：{constraints}
"""
messages = [
    {"role": "system", "content": SYSTEM_PROMPT.format(
        role="资深 SQL 优化师",
        task="优化用户给出的 SQL 查询",
        constraints="只改写，不修改 schema",
    )},
    ...
]
```

这是**走向 Context Engineering 的第一步**——你的 prompt 不再是字符串，而是一个**可组合、可测试的模板**。

### 3. Markdown 让结构跳出来

```markdown
## 角色
...
## 任务
...
## 约束
- ...
- ...
## 示例
...
## 输出格式
```

模型对结构化的 prompt 有显著更好的指令遵循率。即便你只用最简单的 `##` 标题，效果就会显著提升。

## 四、温度、Top-p、Seed：解码端的参数

写好了 prompt，还有**生成参数**决定输出的随机性：

| 参数 | 范围 | 高=？ | 低=？ | 推荐 |
| :--- | :--- | :--- | :--- | :--- |
| `temperature` | 0–2 | 更发散、更有创意 | 更确定、更可重复 | 任务确定型用 0–0.3，创作型用 0.7–1.0 |
| `top_p` | 0–1 | 候选词多 | 候选词少 | 一般和 temperature 二选一调 |
| `seed` | int | — | — | 调试时固定 seed，让输出可复现 |
| `max_tokens` | int | 更长 | 更短 | 给一个**带余量**的上限 |
| `stop` | list | — | — | 当模型可能"过度延伸"时设硬停止符 |

> **黄金法则**：**评估前固定 seed，生产环境关心 p99**。

## 五、什么时候 prompt 就够了？

不是所有问题都需要走到 Context / Harness。**先问自己**：

- ❓ 任务是不是**单次推理**就能完成？（写一段文案、翻译、分类、抽取 JSON 字段……）
- ❓ 输入是不是**适合直接放进窗口**？（输入 < 50K tokens）
- ❓ 输出是不是**结构化**或**短文本**？

**三个 Yes** → Prompt Engineering 就够了。  
**有 No** → 翻到第 2 章，开始考虑 Context Engineering。

---

下一节：[§1.2 七大模式 →](./02-patterns.md)
