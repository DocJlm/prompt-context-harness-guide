---
title: Chapter 2 · Context Engineering
description: Managing the attention budget — the second muscle of LLM application development
---

# Chapter 2 · Context Engineering: Managing the Attention Budget

> "Context engineering is the natural progression of prompt engineering. As we build agents that operate over longer time horizons and across more turns of interaction, we need strategies for **curating the optimal set of tokens** that will land in the model's limited attention budget."  
> — Anthropic Engineering, *Effective Context Engineering for AI Agents*, 2025-09

## Chapter Overview

⏱️ **Reading time**: about 120 minutes  
🎯 **After this chapter, you can**: **design a context flow** for a long-running task — know when to compress, when to retrieve, and when to take notes.  
🧪 **Companion lab**: [Lab 2 · mini_rag](../../../code/lab2-context-rag/)

## Section Structure

| Section | Topic | Focus |
| :---: | :--- | :--- |
| [§2.1](./01-context-anatomy.md) | **Anatomy of Context** | The System / Tools / Examples / History quartet, attention budget |
| [§2.2](./02-retrieval.md) | **Retrieval: Get the right info into the window** | RAG pipeline, just-in-time retrieval |
| [§2.3](./03-memory.md) | **Memory: Help your Agent remember across turns and sessions** | Short-term / long-term memory, structured notes |
| [§2.4](./04-compaction-subagents.md) | **Compaction and Sub-agents** | Compaction, sub-agent summaries |
| [§2.5](./05-lab.md) | **Hands-on Lab** | Build a mini RAG from scratch |
| [§2.6](./references.md) | **References** | Links to primary sources |

## One-paragraph Recap of What This Chapter Solves

**Context engineering is the craft of "putting exactly the right information into the window at every step."**  
When a task spans 50 turns, the context fills 200K tokens, and information flows in from 10 different sources, **the model will not make those tradeoffs on its own** — you have to prepare them for it.

The cost of not preparing:
- **Context rot**: the longer the window, the more the model loses focus.
- **Budget eaten by noise**: the 5 key sentences drown in 50K of fluff.
- **Cross-turn hallucinations**: the model forgets earlier constraints and repeats mistakes.

## Mental Model: Think of Context as the Model's "Working Memory"

```
┌──────────────────────────────────────────────────────────────┐
│  Context Window (200K tokens)                                │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ [System Prompt]  ← who, goal, constraints, style — always││
│  ├──────────────────────────────────────────────────────────┤│
│  │ [Tool Definitions]  ← schemas of available tools — always││
│  ├──────────────────────────────────────────────────────────┤│
│  │ [Few-shot Examples]  ← key demonstrations — cacheable    ││
│  ├──────────────────────────────────────────────────────────┤│
│  │ [Retrieved Knowledge]  ← Just-in-time RAG snippets       ││
│  ├──────────────────────────────────────────────────────────┤│
│  │ [Long-term Memory Snippet]  ← pulled from external store ││
│  ├──────────────────────────────────────────────────────────┤│
│  │ [Conversation History]  ← compressible, truncatable      ││
│  ├──────────────────────────────────────────────────────────┤│
│  │ [Current User Turn / Tool Result]  ← this turn's input   ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

Every token is part of the budget. You decide:
- Should this chunk go into the window at all?
- Where does it sit (front / middle / back)?
- **How long until** it should be compressed or evicted?

::: key insight
**A 1M context window doesn't mean you can stuff in 1M.**  
Transformer attention is *O(n²)* across pairs of *n* tokens; the larger the window, the more diluted each token's "share of attention" becomes. That's **context rot**.
:::

## How This Chapter Builds on the Last

Every technique from Chapter 1 — Role, Few-shot, CoT, Structured Output — is still in play.  
But now they're **one piece of the context puzzle**, not the whole thing.

- The System Prompt still needs to be well written, but it's now only ~5% of the context.
- Few-shot examples are still useful, but you have to **choose which ones** go into the window (not all of them).
- CoT still matters, but reasoning models do it for you — the saved budget can go to more retrieval results.

**The perspective upgrade**: from "how do I write a good paragraph?" to "how do I manage the evolution of this entire window?"

---

Next: [§2.1 Anatomy of Context →](./01-context-anatomy.md)
