---
title: 第 2 章 · Context Engineering
description: 管理注意力预算 —— LLM 应用开发的第二层肌肉
---

# 第 2 章 · Context Engineering：管理注意力预算

> "Context engineering is the natural progression of prompt engineering. As we build agents that operate over longer time horizons and across more turns of interaction, we need strategies for **curating the optimal set of tokens** that will land in the model's limited attention budget."  
> — Anthropic Engineering, *Effective Context Engineering for AI Agents*, 2025-09

## 本章导读

⏱️ **阅读时长**：约 120 分钟  
🎯 **学完之后你能**：为一个长任务**设计上下文流**，知道什么时候压缩、什么时候检索、什么时候记笔记。  
🧪 **配套实验**：[Lab 2 · mini_rag](../../../code/lab2-context-rag/)

## 章节结构

| 小节 | 主题 | 重点 |
| :---: | :--- | :--- |
| [§2.1](./01-context-anatomy.md) | **上下文的解剖学** | System / Tools / Examples / History 四件套，注意力预算 |
| [§2.2](./02-retrieval.md) | **检索：把对的信息塞进窗口** | RAG 流水线，Just-in-time 检索 |
| [§2.3](./03-memory.md) | **记忆：让 Agent 跨轮 / 跨 Session 不忘事** | 短期 / 长期记忆，结构化笔记 |
| [§2.4](./04-compaction-subagents.md) | **压缩与子 Agent** | Compaction、Sub-agent 摘要 |
| [§2.5](./05-lab.md) | **动手实验** | 从零搭一个 mini RAG |
| [§2.6](./references.md) | **参考文献** | 一手资料链接 |

## 一段话回顾这一章要解决的问题

**Context Engineering 是一门"在每一步把恰好需要的信息放进窗口"的手艺**。  
当任务跨 50 轮、上下文塞进 200K tokens、信息来源多达 10 个的时候，**模型不会自动取舍**，你必须给它准备好。

不准备的代价：
- **Context Rot**（上下文腐烂）：窗口越长、模型越走神。
- **预算被噪声占满**：真正关键的 5 句话被 50K 的废话淹没。
- **跨轮幻觉**：模型忘了前面的约束，犯回头错。

## 心智模型：把 Context 想象成模型的"工作记忆"

```
┌──────────────────────────────────────────────────────────────┐
│  Context Window (200K tokens)                                │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ [System Prompt]  ← 谁、目标、约束、风格 — 永驻            ││
│  ├──────────────────────────────────────────────────────────┤│
│  │ [Tool Definitions]  ← 可用工具的 schema — 永驻           ││
│  ├──────────────────────────────────────────────────────────┤│
│  │ [Few-shot Examples]  ← 关键示例 — 可缓存                 ││
│  ├──────────────────────────────────────────────────────────┤│
│  │ [Retrieved Knowledge]  ← Just-in-time 注入的 RAG 片段   ││
│  ├──────────────────────────────────────────────────────────┤│
│  │ [Long-term Memory Snippet]  ← 从外部记忆 pull 进来       ││
│  ├──────────────────────────────────────────────────────────┤│
│  │ [Conversation History]  ← 可压缩、可截断                  ││
│  ├──────────────────────────────────────────────────────────┤│
│  │ [Current User Turn / Tool Result]  ← 本次输入            ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

每个 token 都是预算。你要决定：
- 这一块该不该进窗口？
- 这一块该放在哪儿（前面 / 中间 / 后面）？
- 这一块**多久之后**要被压缩或丢出去？

::: 关键认知
**1M 上下文 ≠ 你可以塞 1M。**  
Transformer 的注意力对 *n* 个 token 是 *O(n²)* 的两两关系；窗口越大，每个 token 能分到的"注意力份额"越被稀释。这就是 **Context Rot**。
:::

## 这一章和上一章的接续

第 1 章里我们学到的所有招数——Role、Few-shot、CoT、Structured Output——都还在用。  
但它们现在是**上下文的一块拼图**，而不是全部。

- System Prompt 仍然要写好，但现在它只是上下文的 ~5%。
- Few-shot Examples 仍然有用，但你要**选哪几个**进窗口（不是全塞）。
- CoT 仍然重要，但 Reasoning 模型自带，省下来的预算可以给更多检索结果。

**视角的升级**：从"我怎么写好一段话"，升级到"我怎么管好这整个窗口的演化"。

---

下一节：[§2.1 上下文的解剖学 →](./01-context-anatomy.md)
