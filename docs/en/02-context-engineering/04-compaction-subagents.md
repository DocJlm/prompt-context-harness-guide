---
title: §2.4 Compaction and Sub-agents
description: Compaction · Sub-agent · the two heavy hammers when the context window isn't enough
---

# §2.4 Compaction and Sub-agents

> "Sub-agents handle focused tasks with **clean context windows**, returning condensed summaries (typically **1,000–2,000 tokens**) to a coordinating main agent."  
> — Anthropic, *Effective Context Engineering for AI Agents*

When you've already pulled out every tool from §2.1–§2.3 and you're still blowing the window, the last two hammers come out: **compaction** and **sub-agents**.

## 1. Compaction: Compress History in Place

### When to trigger

```
if total_tokens > 0.7 * window_size:
    compact()
```

The empirical threshold is 60–80% of the window. Claude Code's official setting is around 70%.

### Step-by-step

```
1. Split history into two segments:
   - "Stable" segment: very old dialogue (to be compressed)
   - "Recent" segment: the most recent N turns (kept verbatim)

2. Use an LLM to generate a summary (with a special prompt that preserves key decisions and open issues)

3. Replace history with:
   [System] + [Tools] + [Examples] + [Summary] + [Recent N turns]
```

### Summary Prompt Template

```text
You are assisting an Agent system with context compaction.

Read the following conversation history and produce a "project state summary".
**Be sure to retain**:

1. **Goal / task**: what does the user want?
2. **Key decisions**: chosen approaches, parameters, design picks already locked in.
3. **What's done**: which sub-tasks are complete; which files / data were produced.
4. **Open questions**: pending inputs, unresolved choices.
5. **Style / constraints**: preferences the user has expressed (wording, formatting, things not to do).

**Do not** keep:
- Pleasantries or procedural acknowledgments ("ok", "got it").
- Intermediate proposals that were overridden.
- Outdated code / data.

Format: Markdown, each subsection starts with `##`, each bullet ≤ 30 characters.
```

::: note
Different Agent systems compact differently. One of Claude Code's tricks: **keep the names + full content of the most recently read 5 files**, because subsequent turns are likely to need them. This is **structure-aware** compaction.
:::

### The cost of compaction

- ⚠️ **Irreversible**: most of the detail you compress out doesn't come back (unless you saved a backup).
- ⚠️ **One LLM call**: the summarization itself costs money and latency.
- ⚠️ **Quality risk**: the summary may **omit** or **distort** key facts.

Ways to reduce the risk in practice:
- **Back up the raw history** to disk (not in context, but reachable via a tool call).
- **Many small compactions beat one big compaction**: 50K → 20K loses less info than 150K → 20K.
- **Don't compress critical checkpoints**: e.g., right after running an expensive tool result, refine the essential bits before compressing.

## 2. Sub-agents: Outsource "Token-Hungry Sub-tasks"

### Motivation

While the main Agent is on a long-running task, it hits a sub-task that's **dense but independent** (e.g., search 50 files, analyze a chunk of large data, generate a 100-page report).

If the main Agent does it itself, it **burns through its own context budget like crazy**.

**Outsource**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Agent                                │
│        (main context: 90K used / 200K)                       │
│                                                              │
│              ┌──────────────────────────────┐                │
│              │  Spawn Sub-Agent              │                │
│              │  Task: "search and summarize  │                │
│              │  all code in the repo about   │                │
│              │  'refund process'"            │                │
│              └────────────┬─────────────────┘                │
│                           │                                   │
└───────────────────────────┼───────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │ Sub-Agent (clean context)    │
              │   - 50 search calls          │
              │   - reads 20 files           │
              │   - burns 80K tokens         │
              │   - output: 1500-token summary│
              └─────────────┬───────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────┐
│  Main Agent receives the 1500-token summary, continues task    │
│        (main context grows: 90K → 92K, not 90K → 170K)        │
└───────────────────────────────────────────────────────────────┘
```

The main Agent's window only grew by **a 1500-token summary**, not by the 80K of search activity. That's the leverage sub-agents give you.

### The core contract for sub-agents

In Anthropic's words:

> "Sub-agent summaries generally return **1,000–2,000 tokens** of condensed information."

In other words: **the interface between main Agent and sub-agent is "input task description → output summary"**. The sub-agent's trace never enters the main context.

The Claude Agent SDK / Claude Code wrap this capability as the `Task` tool:

```python
task_result = call_tool("Task", {
    "subagent_type": "researcher",
    "prompt": "Search this repo for all code related to the refund process, output a summary of ≤ 1500 chars..."
})
# task_result.summary goes into the main Agent's history
```

### When to use sub-agents

| Good fits for outsourcing | Poor fits |
| :--- | :--- |
| Heavy search / reading | Tightly coupled with the main context |
| Long report generation | Multi-step Q&A needing real-time main-agent feedback |
| Independent batch jobs | High-frequency conversational customer service |
| Evaluating / testing a candidate approach | Scenarios where tool state must be shared |

> Rule of thumb: **sub-task has > 5 tool calls** AND **outputs < 2K tokens** → worth outsourcing.

### Sub-agents vs. multi-agent collaboration

```
Sub-agent (one-way outsourcing):           Multi-agent collaboration (two-way comms):
  Main  ──spawn──►  Sub                       Agent A ◄──messages──► Agent B
        ◄─summary──                                  ▲
                                                     │
                                                  Coordinator
```

- Sub-agent: **one-way**, main waits for sub to return. Simple, controllable, token-efficient.
- Multi-agent: **two-way**, complex protocols. More powerful, but **easy to fall into message hell** (endless mutual confirmations).

Anthropic's official advice: **start with sub-agents**, only escalate to multi-agent when the task genuinely needs multiple roles collaborating for an extended time.

## 3. Sub-agents in Coding Agents

Claude Code, Cursor, and Codex all lean heavily on sub-agents. Common sub-agent roles:

```
┌──────────────────────────────────────────────────────────────────┐
│  Main Agent (planning + high-level decisions)                     │
│   │                                                              │
│   ├── Explore sub-agent      search code / file structure        │
│   ├── Plan sub-agent         design the implementation           │
│   ├── Code reviewer          review the diff                     │
│   ├── Test runner            run tests + summarize results       │
│   └── Bash sub-agent         run long commands / stream logs     │
└──────────────────────────────────────────────────────────────────┘
```

Each sub-agent has its own system prompt and tool subset — **specialists beat generalists**.

## 4. Compaction × Sub-agent: the Full Picture for Long-Running Agents

```
Time ─►
─────────────────────────────────────────────────────────────────────►

  Main Agent context usage
  
  100K ┤
       │           ┌──── compaction ────┐                              
   80K ┤          ╱                      ╲                             
       │         ╱                        ╲      ┌─ sub-agent          
   60K ┤        ╱           ┌──sub-agent───┐╲    │  back-and-forth     
       │       ╱            │ (parallel)    │ ╲  │  doesn't enter main 
   40K ┤      ╱             │              │  ╲ │                     
       │     ╱              └──summary─────┘   ╲│                     
   20K ┤    ╱                       ↓           ╲                      
       │   ╱                                                           
    0K └──────────────────────────────────────────────────────────►
       0min   1m   2m   3m   4m   5m   6m   7m   8m   9m   10m
       
  ▲ Compaction: chops it back down in place
  ▲ Sub-agent: outsourced, doesn't grow the main window
```

The main Agent's two weapons for "keeping it running" — these are the two.

## 5. Putting This Section in Your Head

- ✅ **Near 60–80% of the window**: trigger compaction.
- ✅ **Big search / report / evaluation sub-tasks**: spawn a sub-agent.
- ⚠️ **Don't reach for multi-agent too easily**: try whether a sub-agent solves it first.
- ⚠️ **Back up critical raw info to disk**: so the model can "replay" it.

That wraps up **the core arsenal of context engineering**. Next is Lab 2, where you put the above concepts into your own hands.

---

Next: [§2.5 Hands-on Lab →](./05-lab.md)
