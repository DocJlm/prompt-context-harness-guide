---
title: §3.2 Engineering Long-Running Harnesses
description: Planner-Generator-Evaluator · progress.txt · Context Reset
---

# §3.2 Engineering Long-Running Harnesses

> "By 'clean state' we mean the kind of code that would be appropriate for merging to a main branch: there are no major bugs, the code is orderly and well-documented, and in general, a developer could easily begin work on a new feature **without first having to clean up an unrelated mess**."  
> — Anthropic, *Effective Harnesses for Long-Running Agents*

## 1. The Core Difficulty of Long-Running Tasks

An agent task that has to run for 4 hours, write 30 files, and make 200 tool calls **will encounter these failure modes**:

1. **Context anxiety**: as the context fills, the model starts to "lose its nerve" and wrap up early.
2. **Confidence drift**: the model is blindly confident in the code it generated and refuses to revisit it.
3. **Environment damage**: it breaks the dev environment (wrong deps installed, files overwritten, git in a mess).
4. **Lost progress**: it crashes halfway; no progress was saved; next run starts from zero.
5. **One-shot illusion**: it tries to do the entire product in one shot, only to realize halfway that the overall direction is wrong.

Karpathy on the Dwarkesh podcast called this problem the **"March of Nines"**:

> "What takes the long amount of time and the way to think about it is that it's a **march of nines**. Every single nine is a constant amount of work. … When you get a demo and something works **90%** of the time, that's just the first nine. Then you need the second nine, a third nine, a fourth nine, a fifth nine."  
> — [Karpathy, Dwarkesh Podcast 2025-10-17](https://www.dwarkesh.com/p/andrej-karpathy)

In other words: **a demo working 90% is just the first nine.** From there to production-grade 99.999%, every additional nine is the same amount of work. The whole value of long-running harness engineering is to make "adding one more nine" repeatable.

Anthropic's solution lies in the three principles from their *Harness Design for Long-Running Applications*.

## 2. The Three Principles

### Principle 1 · Decompose into tractable chunks

Don't let the agent do the whole project in one go. **Plan first, break the project into "one-session-each" small features.**

```json
// feature_list.json
[
  {"id": "F1", "desc": "User login page UI", "deps": [],     "status": "done"},
  {"id": "F2", "desc": "Login API route",     "deps": ["F1"], "status": "done"},
  {"id": "F3", "desc": "JWT auth middleware", "deps": ["F2"], "status": "in_progress"},
  {"id": "F4", "desc": "Logout endpoint",      "deps": ["F3"], "status": "pending"},
  ...
]
```

Each session:
- Read `feature_list.json`, pick a `pending` whose deps are `done`.
- Implement + test + commit.
- Mark it `done`, write the next session's hint.
- Exit.

### Principle 2 · Use structured artifacts for context handoff

Don't rely on message history to pass state between sessions. **Write files**:

```
project/
├── claude-progress.txt    ← Current progress + key decisions + known issues
├── feature_list.json      ← Full feature list
├── ARCHITECTURE.md        ← High-level architecture
├── init.sh                ← Script to bootstrap the dev environment
└── .git/                  ← Full version history
```

Anthropic's own words:

> "The key insight here was finding a way for agents to quickly understand the state of work when starting with a fresh context window, which is accomplished with the **claude-progress.txt** file alongside the git history. Inspiration for these practices came from knowing what effective software engineers do every day."

**An agent's project = a real engineer's project.** However you write your README and NOTES.md, the agent should too.

### Principle 3 · Separate generation from evaluation

Anthropic's finding: **Agent self-evaluation is unreliable.**

> "Agents tend to respond by confidently praising the work—even when, to a human observer, the quality is obviously mediocre."

Solution: **a dedicated Evaluator agent**, with its own context window, that runs tests and checks. It and the Generator agent communicate via files + test cases.

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Planner    │ ─spec─►│  Generator  │ ─diff─► │  Evaluator  │
│             │        │ (writes code)│         │ (runs tests)│
└─────────────┘        └─────────────┘         └─────────────┘
                              ▲                        │
                              │ <─ fail report─────────┘
                              │
                       (fix → re-eval)
```

This is the **Planner-Generator-Evaluator** three-agent architecture, described in detail in Anthropic's *Harness Design*.

## 3. A Typical Session-Start Flow

```
[Session Start]
  │
  ├── 1. Orient
  │     • pwd
  │     • ls -la
  │     • cat claude-progress.txt
  │     • cat feature_list.json
  │     • git log -10 --oneline
  │
  ├── 2. Verify environment
  │     • ./init.sh
  │     • npm test  / pytest  (smoke test)
  │     • If fails → prioritize fixing env, don't start new feature
  │
  ├── 3. Pick next feature
  │     • From feature_list.json find a pending whose deps are done
  │     • Append to progress.txt: "Working on F3"
  │
  ├── 4. Implement
  │     • Write code (small steps, fast iterations)
  │     • Run unit tests as you go
  │     • Spawn an evaluator sub-agent for end-to-end validation if needed
  │
  ├── 5. Commit
  │     • git commit -m "F3: ..."
  │     • Update feature_list.json: F3.status = done
  │     • In progress.txt write: today's completions + key decisions + known issues
  │
  └── 6. Exit cleanly
        • Confirm git working tree is clean
        • Confirm init.sh still runs
        • Leave a line "Next session should do F4" in progress.txt
```

Write this all into the system prompt + tool descriptions and the agent will naturally have **the work habits of an engineer**.

## 4. The Content Pattern of claude-progress.txt

```markdown
# Project Progress

Last updated: 2026-05-28 by Session #7

## Goal
Build a Notion-like online note app with SSO support.

## Architecture (decided)
- Backend: FastAPI + PostgreSQL + Redis
- Frontend: Next.js + TipTap editor
- Auth: GitHub OAuth + JWT

## Completed
- F1 ✅ User login page UI
- F2 ✅ Login API route
- F3 ✅ JWT middleware (this session)

## In Progress
- F4 🚧 Logout endpoint (next session start here)

## Known Issues
- Redis connection times out occasionally in Docker compose → tracked in issue #7
- Frontend TipTap shows a BOM-related rendering bug on Safari 18 → workaround in commit a1b2c3

## Key Decisions
- Chose JWT over sessions: because of front/back split + mobile support
- Did not introduce Prisma: FastAPI with native SQLAlchemy is sufficient

## Open Questions
- Is multi-tenant support required for V1? Awaiting user confirmation.
```

**This file itself is an extension of the System Prompt** — at the start of every session, the first thing the agent does is read it.

## 5. Context Reset: Proactively "Shuffling"

> "Context resets were a key unlock: the harness used Sonnet 4.5, which exhibited the 'context anxiety' tendency... Creating a harness that worked well across context resets was key to keeping the model on task."  
> — Anthropic, *Harness Design*

What is a context reset?

**When the agent shows "context anxiety" or has been circling for a while, the harness proactively kills the current session and starts a fresh one to continue.**

```
Session N (60min in):
  context 168K / 200K
  Agent: "I think we're almost done, let me wrap up..."  ← anxiety signal
  Agent: oscillating between two patches over and over   ← stuck signal
  
  ┌────────────────────────────────────────┐
  │  Harness intervenes:                    │
  │  1. Force save progress.txt             │
  │  2. Force git commit (WIP)              │
  │  3. Kill session                        │
  │  4. Start Session N+1 fresh             │
  └────────────────────────────────────────┘

Session N+1 (fresh):
  context 0K / 200K
  Agent reads progress.txt → orient → continue
  
  ↓ no anxiety, fresh attention budget
```

**Context reset sounds blunt, but it's extremely effective** — it mimics a real engineer's "sleep on it" wisdom.

How to implement:

- **Token-based**: context > 70% → prepare to reset.
- **Behavior-based**: detect repeated edits to the same block → force reset.
- **Time-based**: running continuously > X hours → force reset to refresh attention.

## 6. Generator vs. Evaluator: Communicate via File Contracts

```python
# Files the Evaluator sees
# /workspace/eval_contracts/F3_jwt_middleware.json
{
  "feature_id": "F3",
  "description": "JWT authentication middleware",
  "test_steps": [
    "POST /api/login with valid credentials → expect 200 + token",
    "GET /api/me without token → expect 401",
    "GET /api/me with valid token → expect 200 + user info",
    "GET /api/me with expired token → expect 401 + 'token expired'"
  ],
  "test_via": "playwright",   // or "pytest", "curl"
  "passes": false,
  "evaluator_notes": []
}
```

The Evaluator runs tests and updates this file. The Generator reads it at the start of a new step:

```python
def pick_next_action():
    failed = [c for c in load_contracts() if not c["passes"]]
    if failed:
        return f"Fix and re-test: {failed[0].feature_id}"
    return "All pass. Pick next feature from feature_list.json"
```

This trick replaces **"model self-evaluation"** with **"a separate agent evaluates + communicates via file"**, sidestepping confidence drift.

## 7. Case: Anthropic's Own Two-Phase + Three-Agent Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          PLANNING PHASE                              │
│                                                                      │
│  User Brief ────► Planner Agent (1 session)                          │
│                      │                                               │
│                      ↓ produces:                                     │
│                   • feature_list.json (16+ features over sprints)    │
│                   • ARCHITECTURE.md                                  │
│                   • acceptance_criteria.md                           │
│                   • init.sh                                          │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ↓
┌──────────────────────────────────────────────────────────────────────┐
│                        IMPLEMENTATION PHASE                          │
│                                                                      │
│  Loop until all features done:                                       │
│                                                                      │
│   Generator Agent ◄──────────────┐                                   │
│      (fresh context per session) │                                   │
│      • read progress.txt          │                                   │
│      • pick next feature         │                                   │
│      • implement + commit        │                                   │
│      • update progress.txt       │                                   │
│         │                        │                                   │
│         ↓ commit                 │                                   │
│   Evaluator Agent                │                                   │
│      • run Playwright tests      │                                   │
│      • update eval_contracts     │                                   │
│      • if fail → write report ───┘                                   │
└──────────────────────────────────────────────────────────────────────┘
```

This architecture, which Anthropic tested with Sonnet 4.5, can **automatically produce web apps that pass end-to-end tests**.

## 8. Voices from the Trenches

Theory's done. Below is **what people who've run thousands of production hours** will tell you.

### 8.1 Manus — "KV-Cache Hit Rate Is the Single Most Important Metric"

In July 2025 the Manus team published a retrospective on building their agent framework (reposted in Chinese on the Tencent Cloud Developer Community), self-mockingly calling their process "stochastic-gradient-descent engineering" — **they rewrote it four times**. The two deepest rules:

> "If I could pick only one metric, I'd say **KV-cache hit rate is the single most important metric for an AI agent in production**."

> "**Any change will invalidate the KV cache for all subsequent actions and observations.**"

— [*"Context Engineering" Lessons from the Manus Project*, Tencent Cloud Developer Community, 2025-07-23](https://cloud.tencent.com/developer/article/2545989)

These two iron rules give Harness design two direct constraints:

1. **The system prompt prefix must be absolutely stable.** Any dynamic content goes at the end.
2. **Do not dynamically add/remove tools.** Use a **logits mask** to block tools that shouldn't be called, rather than removing them from the tool list — removal invalidates all downstream KV cache.

Manus also disclosed a counter-intuitive cost structure: **input:output ≈ 100:1**. That is, 99% of a long-running agent's cost is on the input side. **The price gap between cached and uncached tokens is typically 10×.** That's why KV-cache hit rate is the core metric.

### 8.2 Peter Steinberger — "The Terminal Grid Is My Orchestrator"

Peter Steinberger — author of OpenClaw (previously Clawd / Moltbot), former founder of PSPDFKit — shared in his 2025–2026 blog posts and his Pragmatic Engineer interview a **counter-consensus** long-running agent workflow. This "Austrian vibe coder" doesn't use any high-level orchestrator; he uses **a grid of terminals**:

> "Between 3-8 in parallel **in a 3x3 terminal grid**, most of them in the same folder. … Agents make **git atomic commits themselves**. **Don't be afraid of stopping models mid-way** — file changes are atomic."  
> — [Steinberger, *Just Talk To It*, 2025-10-14](https://steipete.me/posts/just-talk-to-it)

He offers a Peter-style manifesto for "long-running agent engineering" (an interesting contrast to Anthropic's official version):

| Principle | Source |
| :--- | :--- |
| **Prompts are code, your .md/.json files are state on disk.** | [Essential Reading for Agentic Engineers](https://steipete.me/posts/2025/essential-reading) |
| **Atomic git commits by the agent itself, safe to kill mid-stream.** | [Just Talk To It](https://steipete.me/posts/just-talk-to-it) |
| **Skip third-party harnesses; subscribe to the labs directly.** "4 OpenAI subs and 1 Anthropic sub." | [Just Talk To It](https://steipete.me/posts/just-talk-to-it) |
| **Close the loop inside the agent** — let the agent compile / lint / test / validate itself; local tests beat remote CI. | [Pragmatic Engineer interview](https://newsletter.pragmaticengineer.com/p/the-creator-of-clawd-i-ship-code) |
| **YOLO mode + `--dangerously-skip-permissions`** is the only way to unlock real inference speed. | [Pragmatic Engineer interview](https://newsletter.pragmaticengineer.com/p/the-creator-of-clawd-i-ship-code) |
| **"I ship code I don't read."** | [Pragmatic Engineer interview](https://newsletter.pragmaticengineer.com/p/the-creator-of-clawd-i-ship-code) |

Note that the Peter camp and the Anthropic camp **disagree on at least two fundamentals**:

| Dimension | Anthropic camp | Peter camp |
| :--- | :--- | :--- |
| Sub-agent scheduling | Explicit `task` tool to spawn | **No orchestrator**, just a grid of terminals |
| Eval loop | Independent Evaluator agent | Let the Generator run its own tests |
| Risk control | Strict permission gates | YOLO + `--dangerously-skip-permissions` |

Which is right? **Both are right, depending on your project** —
- **Enterprise, multi-user, many irreversible operations**: the Anthropic camp is steadier.
- **Solo project, atomic commits, iteration speed first**: the Peter camp is faster.

Karpathy, at Sequoia, gave the middle-of-the-road advice: **"Keep AI on a tight leash"** and **"Autonomy slider"**:

> "There's what I call the **autonomous slider** … you can either just do a quick search, or you can do research, or you can do deep research."  
> — Karpathy, Software Is Changing (Again), YC 2025-06

**A good harness doesn't fix one autonomy level — it gives users an adjustable slider.**

### 8.3 Alibaba Cloud — "Should the Agent Be Flexible and Autonomous, or Stable and Controlled?"

Jiang Jian (Feixue), an algorithm expert at Alibaba Cloud, writes in InfoQ about the same tension from an enterprise-deployment perspective:

> "Should the agent be flexible and autonomous, or stable and controlled? It's not an either/or — **it depends on your scenario**."  
> — [*Practice: Improving Customer-Service Agents at Alibaba Cloud*, InfoQ, 2025-07-04](https://www.infoq.cn/article/vxqmohtlz9oasln733rg)

Alibaba splits agents into two classes:
- **"LLM-driven autonomous planning"** (e.g., RDS anomaly diagnosis) — leans Peter camp
- **"Workflow pre-orchestration"** (e.g., order/finance lookup) — leans Anthropic camp

With a matching **eval corpus** (tool selection / action execution / parameter extraction accuracy) + **AI-assisted prompt tuning** workflow, to lower the bar for business teams to write prompts.

### 8.4 Alibaba Cloud's Wang Chen — "Frameworks Take Over Context Engineering"

In *On the Evolution of Agent Development Tooling*, Alibaba Cloud's Wang Chen offers this judgment:

> "**The context engineering that was once the developer's job is being moved into the framework**, including construction, execution, and runtime."  
> — [Alibaba Cloud Native, 2025-10-27](https://www.cnblogs.com/alisystemsoftware/p/19169571)

He divides the tooling evolution into four phases: foundation frameworks (LangChain/LlamaIndex) → collaboration & tools (Dify, MCP) → reinforcement learning → **model-centric** (AgentKit, Claude Skills).

Note the fourth phase: **Skills, AGENTS.md, and other conventions make the framework itself thinner while the model takes on more.** Helixent's auto-discovery of `~/.agents/skills/`, deer-flow's `claude-to-deerflow` interop skill — these are concrete instances of that trend.

## 9. Takeaways

The non-negotiables for writing long-running harnesses:

✅ **Decompose**: feature_list.json, one feature per session.  
✅ **Write**: progress.txt + ARCHITECTURE.md + every key decision goes into a file.  
✅ **Separate**: Planner / Generator / Evaluator — at least three roles, independent contexts.  
✅ **Shuffle**: Context > 70% → proactively reset, don't wait to blow up.  
✅ **Test**: every session ends with a smoke test; environment must be clean.  
✅ **Commit**: every small step `git commit -m "..."` — git log is the agent's brain trace.

In the next two sections we'll look at two **industrial-grade open-source harness projects** — helixent and deer-flow — and how they put these principles into practice.

---

Next: [§3.3 Case · helixent →](./03-case-helixent.md)
