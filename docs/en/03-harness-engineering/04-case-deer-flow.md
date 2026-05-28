---
title: §3.4 Case · deer-flow
description: ByteDance's open-source SuperAgent Harness
---

# §3.4 Case · deer-flow

> "DeerFlow is an open-source long-horizon **SuperAgent harness** that researches, codes, and creates. With the help of **sandboxes, memories, tools, skills, sub-agents and message gateway**, it handles different levels of tasks that could take minutes to hours."  
> — [github.com/bytedance/deer-flow](https://github.com/bytedance/deer-flow)

deer-flow (**Deep Exploration and Efficient Research Flow**) is open-sourced by ByteDance. **In February 2026, the v2.0 release briefly reached GitHub Trending #1**. It represents the modern shape of a "full-featured Harness."

## 1. Project Self-Portrait

| Dimension | deer-flow |
| :--- | :--- |
| **Main language** | Python 73% + TypeScript 15% |
| **Core framework** | LangGraph + LangChain |
| **Form** | Complete Backend + Frontend + Skills suite |
| **Features** | Sub-agents, Sandbox, Long-term Memory, IM integrations, MCP support, observability |
| **Directories** | backend / frontend / skills / docker |

> Note: deer-flow v2.0 is a **complete rewrite** — it shares almost no code with v1.0 (the early deep-research framework). Everything in this section is about v2.0.

## 2. Comparison with helixent

```
                    helixent              deer-flow
                    ────────              ─────────
Code size           A few thousand lines  Tens of thousands of lines
Scope               Single library + CLI  Backend + frontend + deployment
Language            TypeScript            Python + TypeScript
Sub-agents          ❌ (roadmap)            ✅
Persistent memory   ❌                     ✅
Sandbox             ❌                     ✅ (Docker / local)
Multimodal          ❌                     ✅ (images, video, PPT)
Observability       Basic logging         ✅ (LangSmith / Langfuse)
IM integrations     ❌                     ✅ (Lark / Slack / Telegram)
Learning curve      One evening           One week+
Good for            Learning, building    Building products
                    tools
```

If helixent is "the Lego Technic foundation set," deer-flow is "an out-of-the-box production car." **They solve different problems, both are worth reading.**

## 3. Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              User                                         │
│  ┌────────────┬──────────────┬──────────────┬──────────────┬──────────┐  │
│  │  Web UI    │    Lark      │  Telegram    │   Slack       │  CLI    │  │
│  └────────────┴──────────────┴──────────────┴──────────────┴──────────┘  │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────────┐
│                        Message Gateway (port 2026)                       │
│                 Unified ingress · routing · auth · rate limit            │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────────┐
│                           Agent Runtime (LangGraph)                      │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  Lead Agent  ──spawn──►  Sub-Agent (research)                       │ │
│  │              ──spawn──►  Sub-Agent (code generation)                │ │
│  │              ──spawn──►  Sub-Agent (slide deck)                     │ │
│  │              ──spawn──►  Sub-Agent (image)                          │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
┌───────▼────────┐         ┌────────▼────────┐         ┌────────▼────────┐
│ Skills Registry│         │ Sandbox Provider│         │ Long-term Memory│
│   (public/     │         │   • Aio (Docker)│         │   • Profile     │
│    custom/)    │         │   • Local       │         │   • Episodes    │
└────────────────┘         └─────────────────┘         │   • Knowledge   │
                                                       └─────────────────┘
```

## 4. Skills: deer-flow's Core Extension Point

A skill = a **directory** containing a `SKILL.md` and a set of tools / prompt resources.

The public skills deer-flow ships out of the box:

```
skills/public/
├── research/                    Deep research: search + synthesis + citations
├── report-generation/           Long-form report generation
├── slide-creation/              Generate PPT decks
├── web-page/                    Generate static web pages
├── image-generation/            Text-to-image, image-to-image
├── github-deep-research/        ★ In-depth GitHub project analysis
└── claude-to-deerflow/          One-click submit tasks from Claude Code to deer-flow
```

Each skill is a complete sub-capability and **can be enabled / disabled independently**.

### What a Skill Looks Like Inside

```
github-deep-research/
├── SKILL.md           ← Main description: when to use / how to use / output format
├── tools/
│   ├── gh_search.py
│   ├── gh_metrics.py
│   └── gh_timeline.py
├── prompts/
│   ├── planner.txt
│   ├── synthesizer.txt
│   └── citation.txt
└── templates/
    └── report.md
```

After the lead Agent sees the `SKILL.md` description, it **decides whether to activate it**. Once activated, the skill's tools and prompts are loaded into context.

## 5. Sub-Agents: deer-flow's Parallel Weapon

deer-flow's core advantage is its **strong sub-agent capability**. The Lead Agent can **spawn multiple sub-agents in parallel**:

```python
# Simplified pseudocode
async def lead_agent(user_query):
    plan = await llm_plan(user_query)
    # plan = [{"role": "research", "topic": "X"}, {"role": "research", "topic": "Y"}, ...]
    
    sub_results = await asyncio.gather(*[
        spawn_sub_agent(role=t["role"], task=t)
        for t in plan["subtasks"]
    ])
    
    final = await llm_synthesize(user_query, sub_results)
    return final
```

Each sub-agent has its own **independent context**, and only returns a condensed ~1500-token summary at the end (exactly matching Anthropic's official recommendation).

LangGraph turns this entire state machine into an **explicit graph** — you can visualize the execution flow.

## 6. Sandbox Implementation Details

deer-flow provides two sandboxes:

### `LocalSandboxProvider`

- Creates an **isolated directory** on the host (`~/.deer-flow/sandboxes/<session_id>/`).
- Restricts tools to only read / write inside that directory.
- bash execution is confined to that cwd.
- **Fast, few dependencies, but weak isolation.**

### `AioSandboxProvider`

- Spins up a **Docker container** per session.
- The container has Python / Node / common CLIs preinstalled.
- File system / network access are opened up on demand.
- **Slower, requires Docker, but strong isolation.**

A nice engineering habit: **the `Provider` abstraction means deer-flow can plug into cloud sandbox vendors like E2B / Modal / Daytona** — just implement the same interface.

## 7. Long-term Memory Implementation

deer-flow's memory model has three layers (consistent with §2.3):

```python
class Memory:
    profile: UserProfile       # User profile
    episodes: List[Episode]    # Event stream
    knowledge: VectorStore     # Accumulated knowledge (vector index)
    
    def remember(self, fact: str, kind: str, confidence: float): ...
    def recall(self, query: str, limit: int = 5): ...
    def consolidate(self): ...  # Periodic merge / dedupe / decay
```

Storage:

- profile / episodes: SQLite + JSON
- knowledge: vector store (Chroma by default, swappable to Milvus)
- All **stays on the user's local machine** (the README emphasizes "memory is stored locally and stays under your control")

## 8. Observability

deer-flow **directly integrates** with LangSmith and Langfuse:

```bash
# One line of env vars to enable
export LANGFUSE_PUBLIC_KEY=...
export LANGFUSE_SECRET_KEY=...
```

Once enabled, in the Langfuse Web UI you can see:

- The full trace of every Agent call
- The sub-agent call tree
- input / output / latency for every tool call
- token / cost for every step

**Standard equipment for production Harnesses. An Agent you can't observe is one you can't operate.**

## 9. Design Choices Worth Savoring

### A) File System as the "Universal Interface"

Whether it's sub-agent output, skill products, or user-uploaded files, **everything flows through the file system inside the sandbox**:

```
/sandbox/<session>/
├── inbox/           ← User uploads
├── work/            ← Agent working directory
├── outputs/         ← Final products
└── reports/         ← Debug / trace
```

This makes communication between front/back-end and sub-agents **simple and semantically clear** — just pass filenames, not stuffed JSON blobs.

### B) Decoupling via the Message Gateway

Whether you come in via Lark, Slack, or the Web, **once you're past the Gateway it's the same message format**. The Agent runtime doesn't care about the source at all.

This is **good engineering** — no matter how many channels are added on the business side, the Agent internals don't change.

### C) MCP Compatibility

deer-flow supports the **Model Context Protocol** — the open protocol proposed by Anthropic. That means if you write an MCP server, it can simultaneously plug into Claude Code, Cursor, and deer-flow — **one tool implementation runs everywhere**.

## 10. What deer-flow Teaches Us

```
✅ For "product-grade" Harnesses, you need sub-agents / sandbox / memory / observability
✅ LangGraph is a great choice for complex multi-agent state machines
✅ Skills are the best abstraction for extensibility — push complexity outward
✅ The Message Gateway lets multi-channel ingress not pollute the core
✅ The file system is the simplest yet strongest inter-Agent communication medium
✅ MCP lets your tools be reused in any Harness
```

## 11. Learning helixent + deer-flow Complementarily

```
Learn helixent to understand the "skeleton" of a Harness:
   what a ReAct loop is, the "basic shape" of tool / middleware / skill

Learn deer-flow to understand the "full musculature" of a Harness:
   how sub-agents are scheduled, how sandboxes are designed,
   how memory is persisted, how UI is integrated

After reading both projects, you'll find their core patterns are highly aligned —
deer-flow simply goes deeper on every axis. That's the "universality"
of Harness Engineering.
```

In the next section we'll **hand-build** a mini Harness ourselves — no fancy dependencies, ~200 lines of Python and it runs.

---

Next section: [§3.5 Hands-on Lab →](./05-build-your-own.md)
