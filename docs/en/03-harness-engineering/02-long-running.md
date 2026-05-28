---
title: §3.2 Engineering Long-Running Harnesses
description: Planner-Generator-Evaluator · progress.txt · Context Reset
---

# §3.2 Engineering Long-Running Harnesses

> "By 'clean state' we mean the kind of code that would be appropriate for merging to a main branch: there are no major bugs, the code is orderly and well-documented, and in general, a developer could easily begin work on a new feature **without first having to clean up an unrelated mess**."  
> — Anthropic, *Effective Harnesses for Long-Running Agents*

## 1. The Core Difficulty of Long-Running Tasks

When an Agent task runs for 4 hours, writes 30 files, and makes 200 tool calls, **the failure modes it will hit** are:

1. **Context anxiety**: as context fills up, the model gets "nervous" and starts wrapping up prematurely.
2. **Confidence drift**: the model is blindly confident in its own generated code, refusing to re-examine it.
3. **Environment damage**: it breaks the dev environment (wrong dependencies, overwritten files, dirty git state).
4. **Lost progress**: it crashes halfway, no progress saved, and starts from scratch next time.
5. **One-shot illusion**: tries to build the whole product in one go, only to realize the direction was wrong halfway through.

Anthropic's solution is the three principles from *Harness Design for Long-Running Applications*.

## 2. The Three Principles

### Principle 1 · Decompose into tractable chunks

Don't let the Agent do the whole project in one shot. **Plan first, decompose the project into small features where "one session = one feature."**

```json
// feature_list.json
[
  {"id": "F1", "desc": "Login page UI",       "deps": [],     "status": "done"},
  {"id": "F2", "desc": "Login API route",     "deps": ["F1"], "status": "done"},
  {"id": "F3", "desc": "JWT auth middleware", "deps": ["F2"], "status": "in_progress"},
  {"id": "F4", "desc": "Logout endpoint",     "deps": ["F3"], "status": "pending"},
  ...
]
```

Each session:
- Reads `feature_list.json`, picks one that's `pending` with all deps `done`.
- Implements + tests + commits.
- Marks status as `done`, then writes a hint for the next session.
- Exits.

### Principle 2 · Use structured artifacts for context handoff

Don't rely on message history to carry state between sessions. **Write files**:

```
project/
├── claude-progress.txt    ← Current progress + key decisions + known issues
├── feature_list.json      ← Full feature checklist
├── ARCHITECTURE.md        ← High-level architecture description
├── init.sh                ← Script to launch the dev environment
└── .git/                  ← Full version history
```

Anthropic's own words:

> "The key insight here was finding a way for agents to quickly understand the state of work when starting with a fresh context window, which is accomplished with the **claude-progress.txt** file alongside the git history. Inspiration for these practices came from knowing what effective software engineers do every day."

**An Agent's project = a real engineer's project.** However you'd write a README and NOTES.md, that's how the Agent should write them.

### Principle 3 · Separate generation from evaluation

Anthropic's finding: **the Agent can't be trusted to evaluate itself.**

> "Agents tend to respond by confidently praising the work—even when, to a human observer, the quality is obviously mediocre."

Solution: **a dedicated Evaluator agent**, with its own independent context window, whose sole job is to run tests and inspect. It communicates with the Generator agent through files + test cases.

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Planner    │ ─spec─►│  Generator  │ ─diff─► │  Evaluator  │
│             │        │ (writes code)│         │ (runs tests) │
└─────────────┘        └─────────────┘         └─────────────┘
                              ▲                        │
                              │ <─ fail report─────────┘
                              │
                       (fix → re-eval)
```

This is the **Planner-Generator-Evaluator** three-agent architecture. Anthropic describes it in detail in the *Harness Design* article.

## 3. A Canonical Session-Start Flow

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
  │     • if fails → prioritize fixing env, don't start a new feature
  │
  ├── 3. Pick next feature
  │     • Find one from feature_list.json that's pending with deps done
  │     • Append to progress.txt: "Working on F3"
  │
  ├── 4. Implement
  │     • Write code (small steps, fast iterations)
  │     • Run unit tests as you go
  │     • If needed, spawn an evaluator sub-agent for end-to-end acceptance
  │
  ├── 5. Commit
  │     • git commit -m "F3: ..."
  │     • Update feature_list.json: F3.status = done
  │     • Write in progress.txt: today's completion + key decisions + known issues
  │
  └── 6. Exit cleanly
        • Verify git working tree is clean
        • Verify init.sh still runs
        • Leave a line "next session should work on F4" in progress.txt
```

Embed this entire flow into the system prompt + tool descriptions, and the Agent naturally inherits **engineer-like working habits**.

## 4. The Content Template for claude-progress.txt

```markdown
# Project Progress

Last updated: 2026-05-28 by Session #7

## Goal
Build a Notion-like online note-taking app with SSO support.

## Architecture (decided)
- Backend: FastAPI + PostgreSQL + Redis
- Frontend: Next.js + TipTap editor
- Auth: GitHub OAuth + JWT

## Completed
- F1 ✅ Login page UI
- F2 ✅ Login API route
- F3 ✅ JWT middleware (this session)

## In Progress
- F4 🚧 Logout endpoint (next session start here)

## Known Issues
- Redis connection occasionally times out on Docker compose → tracked in issue #7
- TipTap on Safari 18 shows a BOM rendering glitch → workaround in commit a1b2c3

## Key Decisions
- Chose JWT over session: front/back separation + mobile support
- No Prisma: native SQLAlchemy in FastAPI is enough

## Open Questions
- Is multi-tenancy a V1 must-have? Awaiting user confirmation.
```

This **file itself is an extension of the system prompt** — the first thing the next session's Agent does is read it.

## 5. Context Reset: Actively "Shuffling the Deck"

> "Context resets were a key unlock: the harness used Sonnet 4.5, which exhibited the 'context anxiety' tendency... Creating a harness that worked well across context resets was key to keeping the model on task."  
> — Anthropic, *Harness Design*

What is a Context Reset?

**When the Agent is in "context anxiety" or stuck in circles for too long, the Harness actively kills the current session and opens a brand-new one to continue.**

```
Session N (60min in):
  context 168K / 200K
  Agent: "I think we're almost done, let me wrap up..."  ← anxiety signal
  Agent: keeps oscillating between two fix options        ← stuck signal
  
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

**Context Reset sounds brutal but is extremely effective** — it replicates the real-engineer wisdom of "sleep on it and look again tomorrow."

How to trigger it:

- **Token-based**: context > 70% → prepare to reset.
- **Behavior-based**: detect repeated edits to the same chunk → force reset.
- **Time-based**: running continuously > X hours → force a mental refresh reset.

## 6. Generator vs Evaluator: Communicating via File Contracts

```python
# What the Evaluator sees on disk
# /workspace/eval_contracts/F3_jwt_middleware.json
{
  "feature_id": "F3",
  "description": "JWT auth middleware",
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

The Evaluator runs the tests and updates this file. The Generator reads it at the start of each new step:

```python
def pick_next_action():
    failed = [c for c in load_contracts() if not c["passes"]]
    if failed:
        return f"Fix and re-test: {failed[0].feature_id}"
    return "All pass. Pick next feature from feature_list.json"
```

This trick replaces **"the model evaluating itself"** with **"another independent agent evaluating, communicated via files"**, sidestepping confidence drift.

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

Anthropic measured this architecture with Sonnet 4.5 and found that it can **autonomously produce web applications that pass end-to-end tests**.

## 8. Burning This Section into Your Brain

The non-negotiable rules for writing long-running harnesses:

✅ **Decompose**: feature_list.json, one feature per session.  
✅ **Write**: progress.txt + ARCHITECTURE.md + every key decision goes into a file.  
✅ **Split**: Planner / Generator / Evaluator — at least three roles, independent contexts.  
✅ **Reset**: when context > 70%, reset proactively; don't wait for it to overflow.  
✅ **Test**: every session must run a smoke test before exiting; the environment must stay clean.  
✅ **Commit**: every small step ends with `git commit -m "..."` — the git log is the Agent's neural pathway.

In the next two sections, we'll look at two **industrial-grade open source Harness projects** — helixent and deer-flow — and see how they put these principles into practice.

---

Next section: [§3.3 Case · helixent →](./03-case-helixent.md)
