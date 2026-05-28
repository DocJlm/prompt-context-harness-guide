---
title: 序章 · 为什么是 Prompt → Context → Harness
description: LLM 应用开发的三次范式跃迁
---

# 序章：为什么是 Prompt → Context → Harness？

> "Building with language models is becoming less about finding the right words and phrases for your prompts, and more about answering the broader question of *'what configuration of context is most likely to generate our model's desired behavior?'*"  
> — Anthropic Engineering, *Effective Context Engineering for AI Agents*, 2025-09

## 一、范式跃迁的动力学

每一次范式的更换，背后都是**模型能力**与**应用复杂度**的同步抬高。

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  能力                                              Harness Engineering │
│   ▲                                       ╱───────────────             │
│   │                          Context     ╱                             │
│   │                          Engineering╱                              │
│   │                  ┌──────────────────┘                              │
│   │       Prompt    ╱                                                  │
│   │       Engineering                                                  │
│   │  ┌───┘                                                             │
│   │ ╱                                                                  │
│   └─────────────────────────────────────────────────────────────►时间  │
│     2022          2023-2024         2024-2025         2025-2026        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

- **2022–2023：Prompt Engineering 时代**。GPT-3.5 / GPT-4 上下文 4K–8K，应用形态是「输入一段话 → 输出一段话」。胜负手在于**怎么把一句话写得让模型听话**：Role、Few-shot、CoT、Delimiters、Output Format。
- **2024：Context Engineering 萌芽**。模型上下文扩到 128K–1M，但 RAG、长文档问答、多轮 Agent 兴起后，工程师发现**只把指令写好已经不够**——还需要把"哪些信息进入窗口、什么时候进入、怎么进入"管起来。
- **2025-09：Anthropic 正式命名 Context Engineering**。他们在 Claude Sonnet 4.5 发布同期的 Engineering Blog 上写道："**Context engineering is the natural progression of prompt engineering**"。
- **2025-2026：Harness Engineering 浮出水面**。Claude Code、Codex、Cursor、Devin 等 Coding Agent 让一个 Agent 能跑数小时、调上百次工具、跨多个 Session。这时模型只是中间的一颗 CPU，**模型之外的一切**——工具、循环、记忆、沙箱、子 Agent、人在回路——成为决定成败的关键。Anthropic 在 2026 年初的 *Effective Harnesses for Long-Running Agents* 里给出了系统化定义。

## 二、三层的边界与连续性

很多人会问：**这三个不就是同一件事的不同说法吗？**

不是。它们解决**不同尺度**的问题：

| 维度 | Prompt Engineering | Context Engineering | Harness Engineering |
| :--- | :--- | :--- | :--- |
| **关心的对象** | 一段 prompt 文本 | 整个上下文窗口的状态 | 模型之外的所有代码 |
| **时间尺度** | 一次推理（seconds） | 多轮 / 一个 Task（minutes） | 多 Session / 长任务（hours） |
| **典型问题** | "怎么让它输出 JSON？" | "怎么让它在 100 轮后还不忘事？" | "怎么让它跑 4 小时还不爆？" |
| **失败表现** | 答非所问 / 格式错 | 幻觉 / 重复劳动 / 中途忘 | 中途崩 / 永远跑不完 / 把环境搞坏 |
| **典型工具** | 提示词模板 | RAG、Compaction、Memory | Tool Loop、Sandbox、Sub-agent、Hook |

注意：**它们是包含关系，不是替代关系**。

```
┌──────────────────────────────────────────────────────────────────┐
│   Harness Engineering                                            │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │   Context Engineering                                    │  │
│   │   ┌──────────────────────────────────────────────────┐  │  │
│   │   │   Prompt Engineering                             │  │  │
│   │   │   • System / User / Few-shot / CoT               │  │  │
│   │   │   • Output format, role, delimiters              │  │  │
│   │   └──────────────────────────────────────────────────┘  │  │
│   │   • 工具描述 / 历史压缩 / 检索注入 / 子 Agent 摘要         │  │
│   └──────────────────────────────────────────────────────────┘  │
│   • 工具循环 / 权限 / 沙箱 / 钩子 / Session 切换 / 持久化状态     │
└──────────────────────────────────────────────────────────────────┘
```

写好一个 prompt，是写好整个上下文的基石；写好整个上下文，是构建一个能跑长任务的 Harness 的基石。**学不能跳级**。

## 三、为什么"提示词工程"这个词逐渐不够用

Anthropic 在 2025-09 那篇文章里有一句话特别犀利：

> "Despite their speed and ability to manage larger and larger volumes of data, we've observed that LLMs, like humans, **lose focus or experience confusion at a certain point**. Studies on needle-in-a-haystack style benchmarking have uncovered the concept of **context rot**: as the number of tokens in the context window increases, the model's ability to accurately recall information from that context decreases."

**Context Rot（上下文腐烂）** 是这一切的根。Transformer 的注意力机制对 *n* 个 token 会产生 *n²* 的两两关系——窗口越大，模型能"集中注意力"的预算越被稀释。1M 的窗口不意味着你可以塞 1M 的垃圾。

于是问题从「**怎么把一段提示词写得最好**」变成了「**怎么管理这个有限的注意力预算**」。后者就是 Context Engineering。

而当 Agent 开始**跨多个上下文窗口**工作时（一个 Session 200K tokens 就满了，但任务需要 200 万 tokens 才能完成），又出现新问题：

- 怎么在新 Session 启动时，让 Agent **快速恢复**之前的状态？
- 怎么让多个 Agent **协同**而不是相互踩踏？
- 怎么让 Agent 调工具时不会**把环境搞坏**？

这些问题，单凭"上下文"层面的策略已经解决不了——它们是**软件工程问题**，需要状态机、文件系统、版本控制、沙箱、权限模型、人机协议。这就是 Harness Engineering。

## 四、用一个例子串起来

假设你想做一个"自动给我的 GitHub 仓库写周报"的应用。

- **Prompt Engineering 阶段（V1）**：你写一个 prompt：「请总结以下 commit 列表为周报，每个要点不超过 20 字，按"功能/修复/重构"分类输出 Markdown」。你把 `git log` 粘进去，模型生成周报。**够用，直到 commit 超过 200 条**。
- **Context Engineering 阶段（V2）**：你发现长 commit 列表会让模型抓不住重点。你引入：
  - **检索**：只把跟 PR 关联、有 reviewer 评论的 commit 拉进来。
  - **压缩**：先用一个小模型对每个 commit 生成 1 句话摘要。
  - **结构化**：用 JSON 而不是大段文本注入。
  - **示例**：在 system prompt 里塞 2–3 个高质量周报例子。
- **Harness Engineering 阶段（V3）**：你想让它**每周一早自动跑**，并且能在 commit 含安全风险时**告警**、能调用 GitHub API 拉 PR diff、能在生成的周报里**插入图表**。你给它：
  - 一个 **Cron / 调度器** 触发循环。
  - 一组**工具**：`get_commits` / `get_pr_diff` / `render_chart` / `send_slack`。
  - 一个 **Planner**：先列出本周关键事件，再分发给子 Agent 写各分类。
  - 一个 **沙箱**：渲染图表的代码在容器里执行。
  - 一份 **progress.md**：每次 Session 启动先读，知道上周的总结风格、收件人偏好。

看出来了吗：从 V1 到 V3，**模型本身没换**，但你的工程量翻了 10 倍，输出质量也翻了 10 倍。这就是 P→C→H 演进给到我们的工程杠杆。

## 五、本教程的承诺

- **第 1 章**：让你写得出一个"任何模型都听得懂"的提示词，并能调它的"反应程度"。
- **第 2 章**：让你能为一个长任务**设计上下文流**，知道什么时候压缩、什么时候检索、什么时候记笔记。
- **第 3 章**：让你能**自己造**一个能跑数小时的 Agent Harness，并能读懂工业级开源项目（helixent / deer-flow）的源码。

---

继续阅读：[第 1 章 · Prompt Engineering →](../01-prompt-engineering/index.md)
