---
title: 教程总览
description: Prompt × Context × Harness Engineering 教程的总入口
---

# 📖 教程总览

欢迎来到 **Prompt × Context × Harness Engineering** 教程。

这里是一份**完整、动手、面向中文读者**的实战指南，目标是带你看清并亲手走过 LLM 应用开发的三次范式演进。

## 三句话讲清楚我们要做什么

1. **2022–2023**：大家在卷"怎么把一句话写得让模型听话" —— **Prompt Engineering**。
2. **2024–2025**：模型越来越强、上下文越来越长，但**只把指令写好已经不够**。我们要在每一步往窗口里塞**恰好需要的信息**，并在多轮里维护它的演化 —— **Context Engineering**。
3. **2025–2026**：Agent 跑数小时、调几十个工具、跨多个会话。模型只是中间的一颗 CPU，**模型之外的一切**（工具、循环、记忆、沙箱、子 Agent、人在回路）才是决定成败的关键 —— **Harness Engineering**。

## 章节导航

- 🟢 [**序章 · 为什么是这三层？**](./00-prologue/index.md)  
  范式演进的动力学，以及为什么"提示词工程"这个词逐渐不够用。

- 🔵 [**第 1 章 · Prompt Engineering**](./01-prompt-engineering/index.md)  
  从最基础的指令格式，到 Chain-of-Thought、Structured Output、Self-Consistency、Meta-Prompting 与 GPT-5 时代的 Reasoning Effort / Eagerness 控制。

- 🟣 [**第 2 章 · Context Engineering**](./02-context-engineering/index.md)  
  系统提示 / 工具 / 示例 / 历史四件套；上下文腐烂（Context Rot）与注意力预算；Just-in-time 检索、压缩（Compaction）、结构化笔记、子 Agent。

- 🟠 [**第 3 章 · Harness Engineering**](./03-harness-engineering/index.md)  
  Harness 的解剖学；长跑型应用的 Planner-Generator-Evaluator 架构；**helixent** 与 **deer-flow** 两个工业级开源项目源码导读；亲手实现一个最小 Harness。

- ⚪ [**附录**](./04-appendix/index.md)  
  术语表、路线图、参考文献、贡献指南。

## 阅读建议

- **章节顺序很重要**：第 2 章建立在第 1 章的肌肉之上，第 3 章是前两章的工程化。
- **每章末有 Lab**：建议读完概念立刻动手跑一遍，对应 [`code/`](../../code/) 目录。
- **遇到陌生名词就查附录术语表**：[glossary.md](./04-appendix/glossary.md)。

## 我们想让你在读完之后能做到什么

✅ 看到一个新模型 / 新框架，能立刻判断它在 P-C-H 这三层里改的是哪一层。  
✅ 写出生产级的 System Prompt、Tool Schema、Few-shot 例子。  
✅ 设计能跑长任务、不"忘"事、不爆窗口的智能体上下文流。  
✅ 读懂 Claude Code、Codex、Cursor 这类 Coding Agent 的工作原理，并能造一个简化版。

> 准备好了吗？翻到 [序章](./00-prologue/index.md)。
