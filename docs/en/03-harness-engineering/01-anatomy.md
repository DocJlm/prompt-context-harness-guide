---
title: §3.1 Anatomy of a Harness
description: Tool loop, permissions, sandbox, hooks, sessions
---

# §3.1 Anatomy of a Harness

> "An agent harness is everything between the language model and the real world. **The model generates text. The harness decides what that text can touch.**"

## 1. The Minimal Harness: the Tool Loop

```python
def run(user_input):
    messages = [system_prompt, {"role": "user", "content": user_input}]
    while True:
        resp = model.chat(messages, tools=TOOLS)
        if not resp.tool_calls:
            return resp.content            # Model gives a final answer, exit the loop
        for tc in resp.tool_calls:
            result = TOOLS[tc.name](**tc.args)
            messages.append(tool_result(tc.id, result))
        messages.append(resp)              # Also append the assistant's tool_call
```

These 7 lines are **the soul of a Harness**:

1. The model decides what to "think" and "do" next.
2. The Harness intercepts the `tool_call` and invokes real code.
3. Real results are written back to messages.
4. The model continues based on the new results.

Every Agent is a variant of this loop. The complex differences are: **how many tools, who can call them, what to do when a call fails, whether to split the loop into sub-agents, how to resume across sessions...**

## 2. Tools: the World the Agent Can "Reach Out and Touch"

**A model without tools can only write text.**

| Category | Examples | Risk |
| :--- | :--- | :--- |
| **Read** | `read_file`, `list_files`, `search`, `web_fetch` | Near zero |
| **Write** | `write_file`, `edit_file`, `mkdir` | May overwrite |
| **Execute** | `bash`, `python_eval`, `npm_install` | High |
| **Communication** | `send_email`, `post_slack`, `call_api` | Irreversible |
| **Meta-tools** | `task` (sub-Agent), `memory_write`, `thinking` | — |

Anthropic explicitly notes in the *Harness Engineering* article:

> "Claude Code exposes roughly 19 permission-gated tools."

These 19 tools are the whole "universe" of Claude Code. Understanding them = understanding the capability boundary of a Coding Agent.

### Criteria for a "Good" Tool

A well-designed tool satisfies:

```
1. Self-contained         One call returns a complete result, without needing another tool to prepare it
2. Robust to error        Wrong args / missing resource → returns a **meaningful** error, never crashes the loop
3. Token-efficient        Returns compact structured data, not a 50K-char dump
4. Idempotent or marked   Can be repeated safely, or clearly labeled "irreversible"
5. Clear naming & desc    The name + description tell the model exactly when to use it
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
# Is it bash or Python? No error contract; permissions can blow up
```

## 3. Permissions and Sandboxes

How much a tool can actually do **depends on what permissions the Harness grants it**.

### Permission Tiers (borrowed from Claude Code)

```
permission_mode:
  - read_only        Agent can only read; writes/exec must ask each time
  - acceptEdits      Allow file writes, but bash still asks
  - autoApprove      All tools auto-allowed (only in controlled environments)
  - plan             Plan-only, no real actions ("think before you speak" mode)
```

Before every tool call, the Harness checks:

```python
def execute_tool_call(tc):
    if not is_permitted(tc.name, tc.args, current_mode):
        if has_user():
            user_response = ask_user(f"Allow call {tc.name}({tc.args})?")
            if not user_response.approve:
                return tool_result(tc.id, "user denied")
        else:
            return tool_result(tc.id, "denied: no permission and no user")
    return tool_result(tc.id, TOOLS[tc.name](**tc.args))
```

### Sandbox

Writing files / running bash always happens **inside a sandbox**:

| Sandbox form | Isolation strength | Example |
| :--- | :--- | :--- |
| **Same process** | None | Direct `subprocess.run` |
| **Same host, separate directory** | Low | `cd /tmp/agent-workdir && bash` |
| **Same host, separate user** | Medium | `sudo -u agent_user bash` |
| **Container** | High | Docker / Firecracker |
| **Remote VM** | Very high | Modal / E2B / Daytona |

deer-flow provides two implementations: `AioSandboxProvider` (Docker containers) and `LocalSandboxProvider` (local directory isolation), so developers can pick per risk profile.

::: Production advice
**If the Agent runs user-written or downloaded code → container-level sandbox or stronger is required.**  
**If the Agent only runs on your own codebase → at least same-host separate directory + no `sudo` / `rm -rf /`.**
:::

## 4. Hooks (Middleware): the Agent's AOP

This is standard in helixent / Claude Code. **Insert user code at the Agent's key event points**:

```
The 8 hooks Helixent provides:

beforeAgentRun     ─ Agent task starts
  beforeAgentStep  ─ Each step starts
    beforeModel    ─ Before model call  (mutate prompt, add logging)
    afterModel     ─ After model call   (evaluate output)
    beforeToolUse  ─ Before tool call   (approval, arg filtering)
    afterToolUse   ─ After tool call    (record results)
  afterAgentStep   ─ Each step ends
afterAgentRun      ─ Agent task ends    (persist state)
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

Hooks are the key to taking a Harness from a "toy demo" to an "operable product". **No hooks → no logging, no auditing, no dynamic interception.**

## 5. Session Switching: the Key to Long-Running Tasks

**When the task is bigger than one context window**, you must support "shift handover."

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

Each session start ≈ a new engineer reporting for duty. What lets them get up to speed quickly is **the progress file + git log + project structure conventions**.

In *Effective Harnesses for Long-Running Agents*, Anthropic gives a canonical session-start flow (pseudocode):

```
[Session Start]
→ Run pwd                    (establish working directory)
→ Read claude-progress.txt   (review previous work)
→ Read feature_list.json     (identify todos)
→ Review git log             (understand recent changes)
→ Execute init.sh            (launch dev environment)
→ Run basic end-to-end tests (verify current state)
→ Select highest-priority incomplete feature
→ Implement with continuous testing
→ Commit to git with descriptive message
→ Update progress file
[Session End - Clean state maintained]
```

Write this flow **into the system prompt** and the Agent inherits "engineer-like working habits." We'll go deeper on this in the next section.

## 6. Memory: the "Long-Term Disk" Across Sessions

Harness-level memory ≠ the in-context memory we discussed in §2.3.

| Context Memory (§2.3) | Harness Memory (here) |
| :--- | :--- |
| Lifetime: one session | Cross-session, permanent |
| Where: inside the context window | Files, SQLite, vector store |
| Read/written by: the model itself | Hooks + tools + scheduler |
| Example: a `<summary>` block | `~/.deer-flow/memory/profile.json` |

deer-flow's memory is a textbook example of the latter:

> "DeerFlow remembers across sessions, building a persistent memory of your profile, preferences, and accumulated knowledge."

## 7. Above Hooks: Scheduler & Human-in-the-Loop

The outermost layer is the **scheduler**:

- Who triggers the task? (user, cron, webhook, IM message)
- How long until timeout?
- Does each step need a human approval pause?
- How does it restart after a crash?

Industrial-grade Harnesses (Codex / Claude Code / deer-flow) all have:

- **TaskQueue**: long tasks run asynchronously off a queue.
- **Heartbeat**: regularly reports progress to the user.
- **Cancel/Resume**: user can stop mid-way or resume later.
- **Notification**: notify task completion via Slack / Lark, etc.

## 8. A Complete Inventory of Harness Components

Pulling it all together into one diagram:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Complete Harness Components                                          │
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

It looks like a lot. **But every component maps to a real problem.** For toy projects you can skip most of them; for production, sooner or later you'll need each one.

---

Next section: [§3.2 Engineering Long-Running Harnesses →](./02-long-running.md)
