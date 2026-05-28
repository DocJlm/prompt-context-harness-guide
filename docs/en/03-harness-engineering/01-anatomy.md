---
title: §3.1 Anatomy of a Harness
description: Tool loop, permissions, sandbox, hooks, sessions
---

# §3.1 Anatomy of a Harness

> "An agent harness is everything between the language model and the real world. **The model generates text. The harness decides what that text can touch.**"

## Origin of the Idea · Karpathy's LLM OS

Before discussing "what is a Harness," let's return to the intellectual origin of the paradigm. In September 2023, Andrej Karpathy posted the now-famous "LLM OS" tweet on X:

> "With many 🧩 dropping recently, a more complete picture is emerging of LLMs not as a chatbot, but the **kernel process of a new Operating System**. E.g. today it orchestrates: Input & Output across modalities (text, audio, vision); Code interpreter, ability to write & run programs; Browser / internet access; Embeddings database for files and internal memory storage & retrieval. … TLDR looking at LLMs as chatbots is the same as looking at early computers as calculators. We're seeing an emergence of a whole new computing paradigm, and it is very early."  
> — [@karpathy, 2023-09-28](https://x.com/karpathy/status/1707437820045062561)

Two months later he gave the "spec sheet":

> "LLM OS. Bear with me I'm still cooking. Specs:  
> **LLM**: OpenAI GPT-4 Turbo 256 core (batch size) processor @ 20Hz (tok/s);  
> **RAM**: 128Ktok;  
> **Filesystem**: Ada002"  
> — [@karpathy, 2023-11-11](https://x.com/karpathy/status/1723140519554105733)

At YC AI Startup School 2025 he formalized the analogy:

> "LLMs have very strong analogies to operating systems. … **LLM is a new kind of computer. It's kind of like a CPU equivalent.** The context windows are kind of like the memory. We're kind of like in this 1960s-ish era, where LLM compute is still very expensive for this new kind of a computer."  
> — Karpathy, *Software Is Changing (Again)*, [YC AI Startup School 2025-06-17](https://www.youtube.com/watch?v=LCEmiRjPEtQ)

**This is the intellectual origin of Harness Engineering.** Karpathy didn't use the word "harness," but he gave us the equivalent picture:

- **LLM = CPU** — accepts input, produces output
- **Context Window = RAM** — bounded "working memory"
- **Embeddings DB = Filesystem** — long-term persistent storage
- **Code interpreter / browser = Peripherals** — system calls
- **Harness = OS kernel** — scheduling, memory management, I/O, permissions

Hold this picture in mind as you read about the "tool loop" below — each block of code corresponds to a classic OS subsystem.

## 1. The Minimal Harness: A Tool Loop

```python
def run(user_input):
    messages = [system_prompt, {"role": "user", "content": user_input}]
    while True:
        resp = model.chat(messages, tools=TOOLS)
        if not resp.tool_calls:
            return resp.content            # Model gave a final answer; exit loop
        for tc in resp.tool_calls:
            result = TOOLS[tc.name](**tc.args)
            messages.append(tool_result(tc.id, result))
        messages.append(resp)              # Also write assistant's tool_call back
```

These 7 lines are the **soul of the Harness**:

1. The model decides "what to think" and "what to do" next.
2. The harness intercepts `tool_call` and runs the real code.
3. Real results are written back to messages.
4. The model continues based on the new results.

In his late-2025 *Year in Review* blog, Karpathy called this loop "the first convincing demonstration of an LLM agent":

> "**Claude Code (CC) emerged as the first convincing demonstration of what an LLM Agent looks like** — something that in a loopy way strings together tool use and reasoning. … it's not just a website you go to like Google, it's a little spirit/ghost that 'lives' on your computer."  
> — [Karpathy, 2025 LLM Year in Review (bearblog)](https://karpathy.bearblog.dev/year-in-review-2025/)

Note "a little spirit/ghost that 'lives' on your computer" — this is the same intuition as the §3.0 analogy of the harness as an "agent OS." **The agent isn't a web-page conversation; it's a program that lives in your machine.**

All agents are variants of this loop. The complex differences are: **how many tools, who can call what, what to do when things break, whether to split into sub-agents, how to continue across sessions, etc.**

## 2. Tools: The World the Agent Can "Reach"

**A model without tools can only write words.**

| Category | Examples | Risk |
| :--- | :--- | :--- |
| **Read** | `read_file`, `list_files`, `search`, `web_fetch` | Almost none |
| **Write** | `write_file`, `edit_file`, `mkdir` | Possible misedits |
| **Execute** | `bash`, `python_eval`, `npm_install` | High |
| **Communicate** | `send_email`, `post_slack`, `call_api` | Irreversible |
| **Meta-tools** | `task`(sub-agent), `memory_write`, `thinking` | — |

Anthropic explicitly notes in their *Harness Engineering* article:

> "Claude Code exposes roughly 19 permission-gated tools."

Those 19 tools are Claude Code's entire "universe." Understand them = you understand the capability boundaries of a coding agent.

### Standards for a "Good" Tool

A well-built tool should satisfy:

```
1. Self-contained         One call returns full result, no need to call another tool first
2. Robust to error        Bad args / missing resource → return a meaningful error, not crash the loop
3. Token-efficient        Return concise structured data, not a 50K-char dump
4. Idempotent or marked   Repeatedly callable / clearly marked "irreversible"
5. Clear naming & desc    Name + description make it obvious when to use
```

Example:

✅ Good tool:

```python
{
  "name": "read_file",
  "description": "Read a UTF-8 text file. Returns up to 2000 lines from given offset. Errors as JSON.",
  "parameters": {
    "file_path": "absolute path",
    "offset": "default 0",
    "limit": "default 2000, max 5000"
  }
}
# returns: {"content": "...", "total_lines": 1234, "truncated": false}
# on error: {"error": "FileNotFound", "path": "..."}
```

❌ Bad tool:

```python
{
  "name": "execute",
  "description": "Execute something",
  "parameters": {"cmd": "string"}
}
# bash or python? no error contract; may blow permissions
```

## 3. Permissions and Sandbox

The size of action a tool can take **depends on what permissions the harness grants it**.

### Permission tiers (inspired by Claude Code)

```
permission_mode:
  - read_only        Agent can only read; writes / executes ask every time
  - acceptEdits      Allow file writes; bash still asks
  - autoApprove      All tools auto-allowed (only for controlled environments)
  - plan             Only planning allowed, no real action ("think before acting" mode)
```

Before each tool call, the harness checks:

```python
def execute_tool_call(tc):
    if not is_permitted(tc.name, tc.args, current_mode):
        if has_user():
            user_response = ask_user(f"Allow call to {tc.name}({tc.args})?")
            if not user_response.approve:
                return tool_result(tc.id, "user denied")
        else:
            return tool_result(tc.id, "denied: no permission and no user")
    return tool_result(tc.id, TOOLS[tc.name](**tc.args))
```

### Sandboxing

Writes / bash always run in a **sandbox**:

| Sandbox form | Isolation strength | Examples |
| :--- | :--- | :--- |
| **Same process** | None | direct `subprocess.run` |
| **Same host, different dir** | Low | `cd /tmp/agent-workdir && bash` |
| **Same host, different user** | Medium | `sudo -u agent_user bash` |
| **Container** | High | Docker / Firecracker |
| **Remote VM** | Very high | Modal / E2B / Daytona |

deer-flow provides both `AioSandboxProvider` (Docker container) and `LocalSandboxProvider` (local directory isolation), letting developers choose by risk.

::: tip Production advice
**Agent runs user-written code / code downloaded from the internet → must have container-level sandboxing or higher.**  
**Agent runs your own codebase → at least different-dir-on-same-host + no `sudo` / `rm -rf /`.**
:::

## 4. Hooks (Middleware): AOP for Agents

This is standard in helixent / Claude Code. **Inject user code at key event points in the agent**:

```
The 8 hooks Helixent provides:

beforeAgentRun     ─ Agent task starts
  beforeAgentStep  ─ Each step starts
    beforeModel    ─ Before model call (modify prompt, add log)
    afterModel     ─ After model call (evaluate output)
    beforeToolUse  ─ Before tool call (approval, parameter filter)
    afterToolUse   ─ After tool call (log result)
  afterAgentStep   ─ Each step ends
afterAgentRun      ─ Agent task ends (persist)
```

Typical usage:

```python
@hook("beforeToolUse")
def log_tool(ctx, tool_call):
    print(f"[{ctx.session_id}] → {tool_call.name}({tool_call.args})")

@hook("beforeToolUse")
def guard_dangerous(ctx, tool_call):
    if tool_call.name == "bash" and "rm" in tool_call.args.get("cmd", ""):
        return {"reject": True, "reason": "rm is forbidden"}

@hook("afterModel")
def truncate_huge_response(ctx, response):
    if len(response.content) > 50000:
        response.content = response.content[:50000] + "... [TRUNCATED]"
```

Hooks are the key to moving a harness from "toy demo" to "operable product." **No hooks → no logging, no audit, no dynamic interception.**

## 5. Session Switching: The Key to Long Runs

**When the task is bigger than one context window**, you must be able to "hand off."

```
Session 1                Session 2                Session 3
[start fresh]            [resume from S1]         [resume from S2]
  • read goal              • read progress.md       • read progress.md
  • plan                   • read recent files      • test current state
  • implement feat 1       • implement feat 2       • implement feat 3
  • commit                 • commit                 • commit
  • write progress.md      • update progress.md     • update progress.md
[context: 95K / 100K]    [context: 92K / 100K]    [context: 88K / 100K]
```

Each session start ≈ a new engineer reporting for duty. What helps them get up to speed is **the progress file + git log + project conventions**.

In *Effective Harnesses for Long-Running Agents* Anthropic gives a typical session-start pseudocode:

```
[Session Start]
→ Run pwd                    (establish working directory)
→ Read claude-progress.txt   (review prior work)
→ Read feature_list.json     (identify outstanding items)
→ Review git log             (understand recent changes)
→ Execute init.sh            (start the dev environment)
→ Run basic end-to-end tests (verify current state)
→ Select highest-priority incomplete feature
→ Implement with continuous testing
→ Commit to git with descriptive message
→ Update progress file
[Session End - Clean state maintained]
```

Write this flow into the system prompt and the agent gains **an engineer's working habits**. We'll dig into this in the next section.

## 6. Memory: The "Long-Term Disk" Across Sessions

Harness-level memory ≠ in-context memory from §2.3.

| Context Memory (§2.3) | Harness Memory (here) |
| :--- | :--- |
| Lifetime: one session | Across sessions, permanent |
| Lives in: context window | Files, SQLite, vector store |
| Read/written by: the model | Hooks + tools + scheduler |
| Example: `<summary>` block | `~/.deer-flow/memory/profile.json` |

deer-flow's memory is the canonical implementation of this kind:

> "DeerFlow remembers across sessions, building a persistent memory of your profile, preferences, and accumulated knowledge."

## 7. Above Hooks: Scheduler & Human-in-the-Loop

The outermost layer is the **scheduler**:

- Who triggers tasks? (user, cron, webhook, IM message)
- After how long do tasks timeout?
- Does each step need to pause for human approval?
- What if it crashes — how to restart?

Industrial-grade harnesses (Codex / Claude Code / deer-flow) include:

- **TaskQueue**: long tasks run async via a queue.
- **Heartbeat**: regular progress reports to users.
- **Cancel/Resume**: user can stop / resume mid-flight.
- **Notification**: notify task completion via Slack / Feishu.

## 8. A Complete Component Inventory of a Harness

Pulled together in one diagram:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Complete Harness components                                          │
│                                                                      │
│  ┌────────────────┐  Tool Loop                                       │
│  │ Loop Controller│ ←──→ Model API (OpenAI/Anthropic/...)            │
│  └───────┬────────┘                                                  │
│          │                                                           │
│          ↓                                                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ Tool Registry  │  │ Permission Mgr │  │ Sandbox        │         │
│  │ - read_file    │  │ - mode         │  │ - container    │         │
│  │ - bash         │  │ - approve()    │  │ - rate limit   │         │
│  │ - search       │  │ - audit log    │  │ - fs scope     │         │
│  │ - ...          │  └────────────────┘  └────────────────┘         │
│  └────────────────┘                                                  │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ Hook System    │  │ Sub-agent Mgr  │  │ Memory Backend │         │
│  │ - beforeModel  │  │ - spawn        │  │ - profile      │         │
│  │ - afterToolUse │  │ - collect_sum  │  │ - episodes     │         │
│  │ - ...          │  └────────────────┘  │ - knowledge    │         │
│  └────────────────┘                      └────────────────┘         │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ Session Mgr    │  │ Scheduler      │  │ HITL UI        │         │
│  │ - resume       │  │ - cron         │  │ - chat         │         │
│  │ - persist      │  │ - timeout      │  │ - approve UI   │         │
│  │ - progress.md  │  │ - retry        │  │ - cancel       │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
└──────────────────────────────────────────────────────────────────────┘
```

It looks like a lot. **But each component answers a real problem.** A toy project can skip most; a production system will eventually need them all.

---

Next: [§3.2 Engineering Long-Running Harnesses →](./02-long-running.md)
