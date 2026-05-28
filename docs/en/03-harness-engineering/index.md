---
title: Chapter 3 · Harness Engineering
description: Everything beyond the model — the third layer of muscle in LLM application development
---

# Chapter 3 · Harness Engineering: Building Agents That Can Run Long

> "A raw model is not an agent. **It becomes one once a harness gives it state, tool execution, feedback loops, and enforceable constraints.**"  
> — Adapted from Anthropic, *Effective Harnesses for Long-Running Agents*

## Chapter Guide

⏱️ **Reading time**: ~150 minutes  
🎯 **After this chapter you will be able to**: build an Agent Harness that can run for hours on its own, and read the source code of industrial-grade open source projects.  
🧪 **Companion lab**: [Lab 3 · mini_harness](../../../code/lab3-mini-harness/)

## Chapter Structure

| Section | Topic | Focus |
| :---: | :--- | :--- |
| [§3.1](./01-anatomy.md) | **Anatomy of a Harness** | Tool loop, permissions, sandbox, hooks, session switching |
| [§3.2](./02-long-running.md) | **Engineering Long-Running Harnesses** | Planner-Generator-Evaluator, progress.txt, Context Reset |
| [§3.3](./03-case-helixent.md) | **Case · helixent** | TypeScript + Bun, the minimal Harness skeleton |
| [§3.4](./04-case-deer-flow.md) | **Case · deer-flow** | ByteDance's SuperAgent Harness |
| [§3.5](./05-build-your-own.md) | **Hands-on Lab** | Build a mini Harness in ~200 lines of Python |
| [§3.6](./references.md) | **References** | First-hand source links |

## A One-Paragraph Recap of What This Chapter Solves

**Harness Engineering is a discipline of "tool loops + state machines + permission models."**  
When your Agent has to run for 4 hours, call 200 tools, span 5 sessions, and operate a real file system, **the model is just a CPU in the middle**. Everything around it — session management, tool implementations, permissions, sandboxes, error recovery, human-in-the-loop — is what decides whether the project ships.

The core insight from Anthropic's early-2026 *Effective Harnesses for Long-Running Agents*:

> "The core challenge of long-running agents is that they must work in discrete sessions, and each new session begins with no memory of what came before. Imagine a software project staffed by engineers working in shifts, where each new engineer arrives with no memory of what happened on the previous shift."

**The mission of Harness Engineering is to make the "incoming shift engineer" productive within 30 seconds.**

## Mental Model: Harness = the Agent's "Operating System"

```
┌────────────────────────────────────────────────────────────────────┐
│                       Harness (Operating System)                    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Loop  (think → act → observe)                    │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │                  Model (CPU)                            │ │  │
│  │  │   accepts messages → outputs messages / tool calls       │ │  │
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
│  │     start / resume / persist progress / switch context window │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                          ↑↓
                     User / Scheduler
```

The model is the CPU in the middle. It can do anything, but **without the OS it can't do anything**.  
When you write code, you use file systems, processes, permissions, scheduling — the Agent Harness gives the model the same toolkit.

## How This Chapter Continues from the Previous Two

```
Stage 1 · Prompt Engineering
   ↓ Solves: output quality of a single inference
Stage 2 · Context Engineering
   ↓ Solves: context management across multiple turns
Stage 3 · Harness Engineering  ← You are here
   Solves: engineering for multiple sessions, long tasks, real-world operations
```

Every prompt used inside the Harness (system / tool description / sub-agent prompt) is a Stage 1 product.  
Every context flow scheduled by the Harness (compaction / sub-agent / memory) is a Stage 2 product.  
The Harness adds one more Stage 3 layer of its own: **real-environment interaction, cross-session state, and security sandboxes**.

## After This Chapter, You'll Understand These Projects

| Project | Language | Type |
| :--- | :--- | :--- |
| **Claude Code** | TS (closed-source + public SDK) | Coding Agent |
| **OpenAI Codex CLI** | TS | Coding Agent |
| **Cursor / Windsurf / Trae** | TS | In-IDE Agent |
| **Claude Agent SDK** | Python / TS | General Agent Harness |
| **[helixent](https://github.com/MagicCube/helixent)** | TS + Bun | **Chapter highlight · §3.3** |
| **[deer-flow (bytedance)](https://github.com/bytedance/deer-flow)** | Python + LangGraph | **Chapter highlight · §3.4** |
| **AutoGen / Smol-developer / SWE-agent** | Python | Various academic / early products |

Their internal architectures share ~70% of the same patterns.

---

Next section: [§3.1 Anatomy of a Harness →](./01-anatomy.md)
