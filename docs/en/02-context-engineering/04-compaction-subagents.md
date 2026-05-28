---
title: §2.4 Compaction and Sub-agents
description: Compaction · Sub-agent · the two heavy hammers when the context window isn't enough
---

# §2.4 Compaction and Sub-agents

> "Sub-agents handle focused tasks with **clean context windows**, returning condensed summaries (typically **1,000–2,000 tokens**) to a coordinating main agent."  
> — Anthropic, *Effective Context Engineering for AI Agents*

When everything in §2.1–§2.3 is in play and you still blow the window, the last two hammers come out: **compaction** and **sub-agents**.

::: tip Before you begin · Manus's two iron rules
In July 2025, the Manus team went public with the core lessons learned after **four rewrites** of their agent framework:

> "If I could pick only one metric, I'd say **KV-cache hit rate is the single most important metric for an AI agent in production**."  
> "**Any change will invalidate the KV cache for all subsequent actions and observations.**"  
> — [*"Context Engineering" Lessons from the Manus Project*, Tencent Cloud Developer Community, 2025-07-23](https://cloud.tencent.com/developer/article/2545989)

This gives you two direct constraints (**check these two before you reach for compaction / sub-agents**):

1. **The system prompt prefix must be absolutely stable.** Anything dynamic (timestamps, usernames, current file names) goes into the message list — **not the system prompt**.
2. **Don't dynamically add or remove tools mid-session.** Need to "mask" a tool? Filter it at the **logits** stage during decoding, **not by removing it from the tool array** — the latter invalidates the entire KV cache.

Manus also disclosed a counter-intuitive cost structure: **input:output ≈ 100:1**. That means 99% of cost is on the input side, and **cached vs. uncached typically differs by 10×**. So "KV-cache hit rate is the single most important metric" is not an exaggeration.
:::

## 1. Compaction: Compress History In Place

### Trigger

```
if total_tokens > 0.7 * window_size:
    compact()
```

Empirical threshold is 60–80% of the window. Claude Code's official choice is ~70%.

### Steps of compaction

```
1. Split history into two segments:
   - "Stable" segment: very old turns (to be compressed)
   - "Recent" segment: last N turns (kept as-is)

2. Use an LLM to produce a Summary (with a special prompt to retain key decisions and open issues)

3. Replace history:
   [System] + [Tools] + [Examples] + [Summary] + [Recent N turns]
```

### Summary Prompt Template

```text
You are assisting an agent system with context compaction.

Read the following conversation history and produce a "project status summary," **emphasizing**:

1. **Goal / task**: what does the user want?
2. **Key decisions**: solutions, parameters, and choices already made.
3. **Completed**: which subtasks have been done so far, and what files / data they produced.
4. **Open issues**: inputs still awaited, choices still pending.
5. **Style / constraints**: preferences the user has stated (wording, format, things not to do).

**Do not** retain:
- Greetings, procedural acknowledgments ("OK," "got it").
- Intermediate proposals that have been superseded.
- Outdated code / data.

Output: Markdown, each section under a `##` heading, each bullet ≤ 30 words.
```

::: tip Note
Different agent systems use different compaction strategies. One Claude Code trick: **keep the last 5 read files (full content)**, because subsequent turns are very likely to reference them again. This is a **structure-aware** form of compaction.
:::

### The cost of compaction

- ⚠️ **Irreversible**: most discarded detail can't be recovered (unless you've kept a backup).
- ⚠️ **One LLM call**: the summary itself has cost and latency.
- ⚠️ **Quality risk**: the summary may **omit** or **distort** key facts.

Mitigations:
- **Back up the raw history to disk** (not in context, but pullable via tool calls).
- **Many small compactions > one big compaction**: 50K → 20K loses less than 150K → 20K.
- **Don't compress at critical junctures**: e.g., right after an expensive tool result, distill its essence before compacting.

## 2. Sub-agents: Outsource "Token-Heavy" Subtasks

### Motivation

While running a long task, the main agent encounters a **dense but independent** subtask (e.g., searching 50 files, analyzing a big chunk of data, generating a 100-page report).

If the main agent does it itself, it **burns through the main context budget**.

**Outsource**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Agent                                │
│        (main context: 90K used / 200K)                       │
│                                                              │
│              ┌──────────────────────────────┐                │
│              │  Spawn Sub-Agent              │                │
│              │  Task: "Search the repo for   │                │
│              │   all refund-flow code and    │                │
│              │   summarize"                  │                │
│              └────────────┬─────────────────┘                │
│                           │                                   │
└───────────────────────────┼───────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │ Sub-Agent (clean context)   │
              │   - 50 search calls         │
              │   - reads 20 files          │
              │   - burns 80K tokens        │
              │   - output: 1500-token sum  │
              └─────────────┬───────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────┐
│  Main Agent receives 1500 tokens of summary, continues task  │
│        (main context grows: 90K → 92K, not 90K → 170K)        │
└───────────────────────────────────────────────────────────────┘
```

The main agent's window grew by **1500 tokens of summary**, not 80K of search trace. That's the leverage sub-agents give you.

### Sub-agent's core contract

In Anthropic's wording:

> "Sub-agent summaries generally return **1,000–2,000 tokens** of condensed information."

In other words: **the interface between main agent and sub-agent is "input a task description, output a summary."** The sub-agent's trace never enters the main context.

Claude Agent SDK / Claude Code package this capability as a `Task` tool:

```python
task_result = call_tool("Task", {
    "subagent_type": "researcher",
    "prompt": "Search this repo for all refund-flow code and produce a summary ≤ 1500 words..."
})
# task_result.summary enters the main agent's history
```

### When to use a sub-agent

| Good for outsourcing | Not good for outsourcing |
| :--- | :--- |
| Bulk search / reading | Tightly coupled to main context |
| Long report generation | Multi-step follow-ups requiring main-agent feedback |
| Independent batch jobs | Fast-paced customer-service dialogues |
| Evaluating / testing a candidate solution | Scenarios requiring shared tool state |

> Rule of thumb: **if a subtask needs > 5 tool calls and outputs < 2K tokens**, it's worth outsourcing.

### Sub-agent vs. multi-agent collaboration

```
Sub-agent (one-way outsourcing):       Multi-agent collaboration (two-way comms):
  Main  ──spawn──►  Sub                Agent A ◄──messages──► Agent B
        ◄─summary──                          ▲
                                             │
                                          Coordinator
```

- Sub-agent: **one-way**, main waits for sub to return. Simple, controllable, token-efficient.
- Multi-agent: **two-way**, complex protocols. More powerful, but **easy to fall into message hell** (endless mutual confirmations).

Anthropic's official recommendation: **use sub-agents first**, and only escalate to multi-agent when the task truly requires multiple roles collaborating over time.

## 3. Sub-agents in Coding Agents

Claude Code, Cursor, and Codex make heavy use of sub-agents. Common sub-agent roles:

```
┌──────────────────────────────────────────────────────────────────┐
│  Main Agent (planning + high-level decisions)                     │
│   │                                                              │
│   ├── Explore sub-agent       Search code / file structure        │
│   ├── Plan sub-agent          Design implementation plan          │
│   ├── Code reviewer           Review diffs                        │
│   ├── Test runner             Run tests + summarize results       │
│   └── Bash sub-agent          Execute long commands / stream logs │
└──────────────────────────────────────────────────────────────────┘
```

Each sub-agent has its own system prompt and tool subset — **specialists beat generalists**.

## 4. Compaction × Sub-agent: The Full Picture of a Long-Running Agent

```
Time ─►
─────────────────────────────────────────────────────────────────────►

  Main Agent context usage
  
  100K ┤
       │           ┌──── compaction ────┐                              
   80K ┤          ╱                      ╲                             
       │         ╱                        ╲      ┌─ sub-agent          
   60K ┤        ╱           ┌──sub-agent───┐╲    │  Round-trips don't  
       │       ╱            │ (parallel)   │ ╲  │  enter main context  
   40K ┤      ╱             │              │  ╲ │                     
       │     ╱              └──summary─────┘   ╲│                     
   20K ┤    ╱                       ↓           ╲                      
       │   ╱                                                           
    0K └──────────────────────────────────────────────────────────►
       0min   1m   2m   3m   4m   5m   6m   7m   8m   9m   10m
       
  ▲ Compaction: chops down vertically
  ▲ Sub-agent: outsources without growth
```

The main agent's two great tools for "keep running" are exactly these two.

## 5. Takeaways

- ✅ **Near 60–80% of the window**: trigger compaction.
- ✅ **Lots of search / report / evaluation subtasks**: spawn a sub-agent.
- ⚠️ **Don't reach for multi-agent lightly**: first see if sub-agent solves it.
- ⚠️ **Back up important raw info to disk**: so the model can "replay" it.

That covers **the core arsenal of context engineering**. Up next, Lab 2 — get your hands on these concepts.

---

Next: [§2.5 Hands-on Lab →](./05-lab.md)
