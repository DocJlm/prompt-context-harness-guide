---
title: 第 3 章 · Harness Engineering
description: 模型之外的一切 —— LLM 应用开发的第三层肌肉
---

# 第 3 章 · Harness Engineering：构建可长跑的智能体

> "A raw model is not an agent. **It becomes one once a harness gives it state, tool execution, feedback loops, and enforceable constraints.**"  
> — 改写自 Anthropic, *Effective Harnesses for Long-Running Agents*

## 本章导读

⏱️ **阅读时长**：约 150 分钟  
🎯 **学完之后你能**：自己造一个能跑数小时的 Agent Harness，并能读懂工业级开源项目源码。  
🧪 **配套实验**：[Lab 3 · mini_harness](../../../code/lab3-mini-harness/)

## 章节结构

| 小节 | 主题 | 重点 |
| :---: | :--- | :--- |
| [§3.1](./01-anatomy.md) | **Harness 的解剖学** | 工具循环、权限、沙箱、钩子、Session 切换 |
| [§3.2](./02-long-running.md) | **长跑型 Harness 的工程** | Planner-Generator-Evaluator、progress.txt、Context Reset |
| [§3.3](./03-case-helixent.md) | **案例 · helixent** | TypeScript + Bun，最简 Harness 骨架 |
| [§3.4](./04-case-deer-flow.md) | **案例 · deer-flow** | 字节跳动的 SuperAgent Harness |
| [§3.5](./05-build-your-own.md) | **动手实验** | 用 ~200 行 Python 造一个 mini Harness |
| [§3.6](./references.md) | **参考文献** | 一手资料链接 |

## 一段话回顾这一章要解决的问题

**Harness Engineering 是一门"造工具循环 + 状态机 + 权限模型"的工程学科**。  
当你的 Agent 要跑 4 小时、调 200 次工具、跨 5 个 Session、操作真实文件系统的时候，**模型是中间一颗 CPU**，外面的所有代码——session 管理、tool 实现、权限、沙箱、错误恢复、人在回路——才是决定项目能不能落地的关键。

Anthropic 在 2026 年初的 *Effective Harnesses for Long-Running Agents* 里的核心洞察：

> "The core challenge of long-running agents is that they must work in discrete sessions, and each new session begins with no memory of what came before. Imagine a software project staffed by engineers working in shifts, where each new engineer arrives with no memory of what happened on the previous shift."

**Harness Engineering 的使命就是：让"接班工程师"能在 30 秒内进入状态。**

## 心智模型：Harness = Agent 的「操作系统」

```
┌────────────────────────────────────────────────────────────────────┐
│                         Harness（操作系统）                          │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Loop  (think → act → observe)                    │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │                  Model (CPU)                            │ │  │
│  │  │       接受 messages → 输出 messages / tool calls         │ │  │
│  │  └─────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│        ↑↓                                ↑↓                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │  Tools   │  │  Memory  │  │ Sandbox  │  │  Hooks   │          │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │
│        ↑                                                            │
│   File System / Network / Database / Other agents (sub-agents)     │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  Session Manager                              │  │
│  │     启动 / 恢复 / 持久化进度 / 切换 context window             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                          ↑↓
                      用户 / 调度器
```

模型是中间这颗 CPU。它什么都能做，但**离开 OS 它什么都做不了**。  
你写代码会用到「文件系统」「进程」「权限」「调度」——Agent Harness 给模型同样的一套。

## 这一章和前两章的接续

```
Stage 1 · Prompt Engineering
   ↓ 解决：单次推理的输出质量
Stage 2 · Context Engineering
   ↓ 解决：跨多轮的上下文管理
Stage 3 · Harness Engineering  ← 你在这里
   解决：跨多 Session、长任务、真实操作的工程化
```

Harness 内部用到的每一份 prompt（system / tool description / sub-agent prompt）都是 Stage 1 的成果。  
Harness 调度上下文流（compaction / sub-agent / memory）都是 Stage 2 的成果。  
Harness 还多了一层 Stage 3 独有的：**真实环境交互、跨 Session 状态、安全沙箱**。

## 这一章读完，你会看懂这些项目

| 项目 | 语言 | 类型 |
| :--- | :--- | :--- |
| **Claude Code** | TS（闭源 + 公开 SDK） | 编码 Agent |
| **OpenAI Codex CLI** | TS | 编码 Agent |
| **Cursor / Windsurf / Trae** | TS | IDE 内的 Agent |
| **Claude Agent SDK** | Python / TS | 通用 Agent Harness |
| **[helixent](https://github.com/MagicCube/helixent)** | TS + Bun | **本章重点 · §3.3** |
| **[deer-flow (bytedance)](https://github.com/bytedance/deer-flow)** | Python + LangGraph | **本章重点 · §3.4** |
| **AutoGen / Smol-developer / SWE-agent** | Python | 各种学术 / 早期产品 |

它们的内部架构 ~70% 是同一套模式。

---

下一节：[§3.1 Harness 的解剖学 →](./01-anatomy.md)
