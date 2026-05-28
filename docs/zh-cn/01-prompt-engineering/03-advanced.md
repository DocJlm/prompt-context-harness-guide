---
title: §1.3 进阶 · Meta-prompting & GPT-5 时代
description: 用模型改进模型；Reasoning Effort、Eagerness、Persistence、Tool Preambles
---

# §1.3 进阶：Meta-prompting & GPT-5 时代

> "Most folks know prompt engineering. But to get the most out of AI agents, you need context engineering."  
> — Anthropic

> "**Your prompts are code, your .md/.json files are state on disk.**"  
> — [Peter Steinberger（OpenClaw 作者）, *Essential Reading for Agentic Engineers*, 2025-06-30](https://steipete.me/posts/2025/essential-reading)

到 2025–2026 年，模型本身已经能写出比你好的 Prompt。所以**进阶提示工程的重心从"怎么写"转到了"怎么调"**——调推理深度、调主动性、调工具使用风格。

## 〇、范式跃迁 · Karpathy 的 "Software 3.0"

Karpathy 2025 年在 YC AI Startup School 演讲里给这个变化命了名：

> "Imo fair to say that software is changing quite fundamentally again. **LLMs are a new kind of computer, and you program them *in English*. Hence I think they are well deserving of a major version upgrade in terms of … Software 3.0.**"  
> — [Karpathy, *Software Is Changing (Again)*, YC AI 2025-06-17](https://www.youtube.com/watch?v=LCEmiRjPEtQ)

并且：

> "**The hottest new programming language is English.**"

含义对本章工程：**写 Prompt = 写代码**。你应该用版本管理它、用 eval 测试它、用 PR review 它、用 changelog 追踪它。Peter Steinberger 那句"prompts 是代码、md/json 是磁盘上的状态"是同一意思的工程化版本。

这也是为什么本章 §1.4 评估那么重要 —— 没有 eval 的 prompt，就是没有单元测试的代码。

## 一、Meta-prompting：让模型改进自己的 prompt

OpenAI 在 GPT-5 Prompting Guide 里明说：**GPT-5 是 metaprompting 高手**。

最简单的 metaprompt 模板：

```text
我想让你帮我**评估并改进**一段 prompt。

原 prompt：
"""
{{original_prompt}}
"""

它在以下 case 上表现不佳：
案例 1：输入 X → 期望 Y → 实际 Z
案例 2：...

请按以下结构输出：
1. 失败原因诊断（每个 case 一条）
2. 改进建议
3. 改写后的完整 prompt
```

这个 metaprompt 本身就是一个 prompt——你也可以拿它去问模型怎么改进它自己。**这是一个递归过程**。

### Meta-prompting 的三个实战用法

1. **Cold start**：写新 prompt 不知道怎么开头时，让模型基于一句话需求生成第一版。
2. **Diagnose**：手里有一版 prompt 跑不准，把 bad cases 喂给模型让它诊断。
3. **Refactor**：把一段长 prompt 让模型重写得更紧凑（**注意**：让它说明哪些部分不能动）。

### Meta-prompting 的陷阱

- ❌ 让模型"自由发挥"——它会过度增加 boilerplate。指令要紧。
- ❌ 一次改太多——分维度迭代（先 fix 准确率，再 fix 长度，再 fix 格式）。
- ❌ 把 metaprompt 的输出**直接上线**——必须**Eval-gate**（见 §1.4）。

## 二、Reasoning Effort：花多少脑力？

GPT-5、Claude 4.x、DeepSeek-R1、Qwen3-Thinking 等模型，都引入了**推理预算**这个旋钮。OpenAI 用 `reasoning_effort` 参数，Anthropic 用 `thinking` block。

```python
# OpenAI GPT-5 风格
response = client.chat.completions.create(
    model="gpt-5",
    messages=messages,
    reasoning_effort="medium",  # "minimal" | "low" | "medium" | "high"
)
```

| Effort | 适用 | 代价 |
| :--- | :--- | :--- |
| `minimal` | 单步分类、抽取、翻译 | 几乎瞬时 |
| `low` | 简单代码、规则推理 | 略慢 |
| `medium` | **默认。**多步任务 | 中等 |
| `high` | 复杂数学、长文档推理 | 慢、贵 |

::: OpenAI 官方建议
> "Scale `reasoning_effort` up for complex tasks, down for efficiency; default is medium."

**最佳实践**：先 medium 跑一遍 Eval，再决定要不要调。**不要默认 high**——会把简单任务也跑得又慢又贵。
:::

## 三、Agentic Eagerness：调"主动性"

这是 GPT-5 引入的全新维度。模型在多步任务中，**应该多积极去探索 / 调工具**？

### 减少 eagerness 的 prompt

```
"Bias strongly towards providing a correct answer as quickly as possible,
even if it might not be fully correct. Usually, this means an absolute
maximum of 2 tool calls."
```

中文版：

```
请尽快给出最有可能正确的答案，哪怕不完全准确。
通常意味着**最多 2 次**工具调用。
```

### 增加 eagerness 的 prompt

```
"Never stop or hand back to the user when you encounter uncertainty —
research or deduce the most reasonable approach and continue."
```

中文版：

```
遇到不确定的情况时**绝不**停下来问用户或终止任务。
请自己研究或推断出最合理的方案后继续。
```

::: 关键判断
- **客服 / 写代码**：偏 **eager**——别动不动就说"请提供更多信息"。
- **金融 / 医疗 / 删除操作**：偏 **不 eager**——宁可问，不要乱动。
:::

## 四、Tool Preambles：工具调用前先"说一句"

GPT-5 引入的另一个习惯：**调工具前，让模型先用一句话告诉用户「我接下来要做什么」**。

```text
在每次调用工具前，先用一句中文告诉用户你即将做什么。
例如：
"我先看一下文件结构……"
然后再发起 ListFiles 调用。
```

为什么重要？
- **用户能跟得上**：减少"黑盒"焦虑。
- **可解释性**：日志里能看到模型的意图。
- **降低幻觉**：让模型"先说后做"，强迫它先 plan。

这是 Coding Agent（如 Claude Code、Cursor、Codex）的标配做法。

::: tip 旁注 · Karpathy 命名 "Vibe Coding"
2025 年 2 月 Karpathy 发了一条把 "vibe coding" 推进英文互联网词典的推文：

> "There's a new kind of coding I call '**vibe coding**', where **you fully give in to the vibes**, embrace exponentials, and forget that the code even exists. It's possible because the LLMs (e.g. Cursor Composer w Sonnet) are getting too good. Also I just talk to Composer with SuperWhisper and I **barely even touch the keyboard**. …  
> I 'Accept All' always, **I don't read the diffs anymore**. When I get error messages I just copy paste them in with no comment, usually that fixes it. …  
> I'm building a project or webapp, but it's not really coding — **I just see stuff, say stuff, run stuff, and copy paste stuff, and it mostly works**."  
> — [@karpathy, 2025-02-02](https://x.com/karpathy/status/1886192184808149383)

注意：**这不是"提示词"，这是"全自然语言对模型说话 + 不读 diff"**。它需要的"prompt 工程"反而最少 —— Karpathy 强调"talk to Composer with SuperWhisper"，连键盘都不碰。

**vibe coding 的边界**：Karpathy 也说这适合"周末项目 / 一次性原型"。生产代码仍然需要 §1.4 的 eval、§1.3 的 Persistence/Eagerness 控制。Peter Steinberger 把这套实践推向极致 —— 详见 §3.2 §8.2。
:::

## 五、Persistence：让模型坚持完成任务

这条来自 OpenAI 官方建议，**几乎所有 agentic 场景都要加**：

```text
You are an agent — please keep going until the user's query is completely
resolved, before ending your turn and yielding back to the user. Only
terminate your turn when you are sure the problem is solved.
```

中文版：

```
你是一个 agent。在用户问题被**完全解决**之前不要交还控制权。
只有当你确信任务完成时，才结束这一轮。
```

它解决一个经典 bug：**模型在中途"心虚"地停下来**，留一个半截活给你。

## 六、Output Format 进阶：让模型"自检"

强制让模型在输出末尾**自检一下**：

```text
# 输出格式
{
  "answer": "...",
  "self_check": {
    "constraint_1_met": true,
    "constraint_2_met": true,
    "uncertainty_level": "<low|medium|high>"
  }
}
```

这个 trick 在生产里效果惊人——**模型为了填那个 self_check 字段，会自动回头审视自己的答案是否符合约束**。等于免费加了一层 self-reflection。

## 七、与中文模型的适配差异

国产模型（通义 Qwen、智谱 GLM、DeepSeek、月之暗面 Kimi、百川、文心）大多支持 OpenAI-Compatible API，所以上面的 prompt 模板**几乎可以直接复用**。但有几点经验差异：

| 模型家族 | 倾向 / 注意点 |
| :--- | :--- |
| **Qwen** | 中文 prompt 更稳；XML 标签 + JSON Schema 兼容好 |
| **GLM** | 偏好 Markdown 结构；CoT 触发用"请逐步思考" |
| **DeepSeek-V/R 系列** | R 系列自带强 CoT，**不要**再加 step-by-step |
| **Kimi** | 长上下文优秀，特别适合超长 RAG 场景 |
| **Baichuan / 文心** | 中文遣词更"客气"，Role 设定时偏好"专家"角色 |

::: 通用建议
**所有 prompt 都先在 GPT-4o-mini 或 Claude Haiku 上写、调通；然后**在国产模型上跑一次 Eval。 cross-model robustness 是生产价值的核心指标。
:::

## 八、把上面的全部组合：一段"GPT-5 时代的 prompt"

```text
# 角色与目标
你是一个资深 SRE Agent，负责定位线上事故。

# Persistence
在事故被定位 + 修复方案给出之前，不要停。

# Eagerness
对工具调用要 eager：宁可多看一份日志，不要漏。最多 8 次工具调用预算。

# Tool Preamble
每次调工具前，用一句中文告诉运维同学你要做什么。

# Reasoning
对复杂的相关性判断使用 thinking。简单的命令拼接不需要 thinking。

# 输出
最终用以下 JSON：
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

这一段同时包含了 Role、Persistence、Eagerness、Preamble、Reasoning、Structured Output、Self-check —— **本章前面所有的招都在里面**。

---

下一节：[§1.4 评估与迭代 →](./04-evaluation.md)
