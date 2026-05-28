---
title: 第 1 章 · Prompt Engineering
description: 把指令说清楚 —— LLM 应用开发的第一层肌肉
---

# 第 1 章 · Prompt Engineering：把指令说清楚

> "GPT-5 是出色的 metaprompting 选手——用模型来改进自己的提示词，并且通常需要更少的 scaffolding，更短、更清晰的指令往往效果更好。"  
> — OpenAI, *GPT-5 Prompting Guide*

## 本章导读

⏱️ **阅读时长**：约 90 分钟  
🎯 **学完之后你能**：写出一段「换任何模型都能听话」的生产级 Prompt，并能用 Eval 驱动地迭代它。  
🧪 **配套实验**：[Lab 1 · prompt_patterns](../../../code/lab1-prompting/)

## 章节结构

| 小节 | 主题 | 重点 |
| :---: | :--- | :--- |
| [§1.1](./01-fundamentals.md) | **Prompt 的解剖学** | System / User / Assistant，Role、Delimiter、Output Format |
| [§1.2](./02-patterns.md) | **七大模式** | Zero-shot · Few-shot · CoT · Self-Consistency · Tree-of-Thought · ReAct · Structured Output |
| [§1.3](./03-advanced.md) | **进阶：Meta-prompting & GPT-5 时代** | Reasoning Effort · Agentic Eagerness · Tool Preambles · Persistence |
| [§1.4](./04-evaluation.md) | **评估与迭代** | 怎么知道你的 prompt 是好的？ |
| [§1.5](./05-lab.md) | **动手实验** | 跑完 Lab 1 五个 demo |
| [§1.6](./references.md) | **参考文献** | 一手资料链接 |

## 一段话回顾这一章要解决的问题

**Prompt Engineering 是一门"用自然语言写程序"的手艺**。  
它的产出是一段（或几段）模型指令，目标是让模型在**单次推理**里，给出**符合预期格式、内容准确、可重复**的输出。

它的边界也很清楚：当问题变成「多轮里怎么不忘事」「怎么从 1000 份文档里挑出对的内容」「怎么让模型用工具」——那已经是第 2、第 3 章的事了。

但**没有写好 prompt 的肌肉**，后两章的工程根本搭不起来：System Prompt 是 Context Engineering 的第一块砖，Tool Description 是 Harness Engineering 的第一块砖，而它们的本质都是 prompt。

## 心智模型：一段 Prompt = 一道菜的菜谱

| Prompt 元素 | 菜谱类比 |
| :--- | :--- |
| **Role** | "你是一个米其林三星主厨" |
| **Task** | "为 4 人份做一道意式番茄牛肉酱面" |
| **Constraints** | "总用时 < 30 分钟，用家庭厨房可得的食材" |
| **Examples / Few-shot** | "可以参考下面这两份样例菜谱..." |
| **Output Format** | "请按【食材清单 / 步骤 / 注意事项】三段输出" |
| **Reasoning hint** | "在写下步骤前，先想清楚关键时序" |

写一段菜谱时，缺哪样都会出问题：
- 不写"米其林主厨"——可能给你一份能下口但平庸的菜。
- 不写"4 人份"——量没法控。
- 不写"30 分钟"——可能给你一份要熬汤 8 小时的硬菜。
- 不给样例——风格随机。
- 不要输出格式——你拿到的是一段散文，无法导入到点菜系统里。

接下来的几节，我们会**把每一项做到工程级**。

---

下一节：[§1.1 Prompt 的解剖学 →](./01-fundamentals.md)
