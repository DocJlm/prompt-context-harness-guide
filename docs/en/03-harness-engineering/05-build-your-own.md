---
title: §3.5 Hands-on Lab · Lab 3
description: Build a mini Harness in ~200 lines of Python
---

# §3.5 Hands-on Lab: Lab 3 · Build a Mini Harness

## Lab Goals

After finishing Lab 3, you will have **personally implemented** the core components from Chapter 3:

| Demo | What you'll do | What you'll learn |
| :---: | :--- | :--- |
| 1 | Implement a ReAct Tool Loop in 100 lines | The "skeleton" of a Harness |
| 2 | Add hooks (logging + dangerous command blocking) | The middleware pattern |
| 3 | Add a sub-agent (outsourcing a search task) | Sub-agent interface |
| 4 | Add Progress persistence + Session recovery | Engineering for cross-session work |
| 5 | Run a real small task | Have the mini harness write a README for you |

> Lab 3's code lives in [`code/lab3-mini-harness/`](../../../code/lab3-mini-harness/). It has **no dependency** on LangGraph / LangChain / any Agent framework — pure Python + the `openai` SDK.

## Setup

```bash
cd code/lab3-mini-harness
pip install -r requirements.txt

export OPENAI_API_KEY=sk-xxxxx
export OPENAI_BASE_URL=https://api.openai.com/v1   # or any OpenAI-Compatible endpoint
export MODEL=gpt-4o-mini
```

## Demo 1 · 100-Line Tool Loop

```bash
python 01_tool_loop.py
```

The core ~100 lines (excerpt — full file in the lab3 directory):

```python
import json, os
from openai import OpenAI

client = OpenAI()
MODEL = os.getenv("MODEL", "gpt-4o-mini")

# ─── Tool implementations ─────────────────────────────
def list_files(path="."):
    return [str(p) for p in __import__("pathlib").Path(path).iterdir()]

def read_file(file_path, max_chars=4000):
    text = open(file_path).read()
    return text[:max_chars] + ("\n... [TRUNCATED]" if len(text) > max_chars else "")

def write_file(file_path, content):
    open(file_path, "w").write(content)
    return f"Wrote {len(content)} chars to {file_path}"

TOOLS_IMPL = {"list_files": list_files, "read_file": read_file, "write_file": write_file}

TOOLS_SCHEMA = [
    {"type": "function", "function": {
        "name": "list_files", "description": "List files in a directory.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string", "default": "."}}},
    }},
    {"type": "function", "function": {
        "name": "read_file", "description": "Read a UTF-8 text file.",
        "parameters": {"type": "object",
                       "properties": {"file_path": {"type": "string"}, "max_chars": {"type": "integer", "default": 4000}},
                       "required": ["file_path"]},
    }},
    {"type": "function", "function": {
        "name": "write_file", "description": "Write text to a file (overwrite).",
        "parameters": {"type": "object",
                       "properties": {"file_path": {"type": "string"}, "content": {"type": "string"}},
                       "required": ["file_path", "content"]},
    }},
]

# ─── Harness Tool Loop ────────────────────────────────
def run(user_message, max_steps=10):
    messages = [
        {"role": "system", "content": "You are a file assistant Agent. Complete tasks using the provided tools."},
        {"role": "user", "content": user_message},
    ]
    for step in range(max_steps):
        resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS_SCHEMA)
        msg = resp.choices[0].message
        messages.append(msg)
        if not msg.tool_calls:
            return msg.content
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            try: result = TOOLS_IMPL[tc.function.name](**args)
            except Exception as e: result = f"Error: {e}"
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(result, ensure_ascii=False)[:4000]})
    return "[max steps exceeded]"

if __name__ == "__main__":
    print(run("List all files in the current directory, then tell me which is the largest .py file and show its first 30 lines."))
```

**80 lines** gives you a working small Agent. Run it:

```
$ python 01_tool_loop.py
[Agent] → list_files(path=".")
[Agent] → read_file(file_path="01_tool_loop.py", max_chars=4000)
[Agent] The largest .py file is 01_tool_loop.py. Its first 30 lines are: ...
```

## Demo 2 · Add Hooks: Logging + Dangerous Command Blocking

```bash
python 02_hooks.py
```

Add a minimal Hook system:

```python
class Hook:
    def before_tool(self, tc): pass
    def after_tool(self, tc, result): pass

class AuditLog(Hook):
    def before_tool(self, tc):
        print(f"📝 [audit] {tc.function.name}({tc.function.arguments[:200]})")

class DangerGuard(Hook):
    def before_tool(self, tc):
        if tc.function.name == "write_file":
            args = json.loads(tc.function.arguments)
            if args["file_path"].startswith("/etc") or args["file_path"].startswith("/"):
                return {"reject": True, "reason": "writing to system directories is forbidden"}

def run_with_hooks(user_message, hooks: list[Hook], max_steps=10):
    # ... same as demo1, but run hooks before/after every tool_call ...
    for tc in msg.tool_calls:
        rejection = None
        for h in hooks:
            r = h.before_tool(tc)
            if r and r.get("reject"):
                rejection = r["reason"]; break
        if rejection:
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": f"[rejected by hook] {rejection}"})
            continue
        ...
```

Run a case that should be blocked:

```python
run_with_hooks("Rename /etc/passwd to /etc/hello", hooks=[AuditLog(), DangerGuard()])
# → The file write request is blocked by DangerGuard
```

## Demo 3 · Sub-Agent: Outsourcing a Search Task

```bash
python 03_subagent.py
```

The main Agent gets an extra `task` tool that spawns sub-Agents:

```python
def task(prompt, role="researcher"):
    """Spawn a sub-agent with a fresh context. Return a condensed summary."""
    sub_system = SUB_AGENT_SYSTEMS[role]
    sub_messages = [
        {"role": "system", "content": sub_system},
        {"role": "user", "content": prompt + "\n\nPlease output a summary of no more than 1500 chars as the final result."},
    ]
    # The sub-agent's own tool loop (simplified here, allows only read/list)
    for _ in range(8):
        r = client.chat.completions.create(model=MODEL, messages=sub_messages, tools=SUB_TOOLS_SCHEMA)
        m = r.choices[0].message
        sub_messages.append(m)
        if not m.tool_calls:
            return m.content
        # ... handle sub tool calls ...
    return "[sub-agent: max steps]"

SUB_AGENT_SYSTEMS = {
    "researcher": "You are a researcher. Thoroughly browse the given code / files and output a high-density summary.",
    "reviewer": "You are a code reviewer. Point out bugs and improvements."
}
```

The main Agent calls it like:

```
User: "I'd like to understand the overall architecture of the lab3 directory."

[Main Agent] → task(role="researcher", prompt="Scan all .py files in lab3-mini-harness and output an architecture summary")
   [Sub-Agent thinking...]
   [Sub-Agent] → list_files
   [Sub-Agent] → read_file(01_tool_loop.py)
   [Sub-Agent] → read_file(02_hooks.py)
   [Sub-Agent] → read_file(03_subagent.py)
   [Sub-Agent] returns: "Lab 3 consists of 5 demos... primarily showcasing the minimum viable implementation of a Harness..."

[Main Agent] gives a final answer based on the sub-Agent's summary.
```

Note: **The main agent's context only gains a ~1500-char sub-Agent summary**, instead of 30K of raw source code.

## Demo 4 · Progress Persistence + Session Recovery

```bash
python 04_progress.py
python 04_progress.py --resume
```

Add two tools:

```python
def update_progress(content):
    open("progress.md", "w").write(content)
    return "progress saved"

def read_progress():
    try: return open("progress.md").read()
    except FileNotFoundError: return "(no previous progress)"
```

Add this to the system prompt:

```
You are a project Agent.

**At session start**, you must always:
1. read_progress() → review previous progress
2. Decide the next step for this session
3. Before session exit, call update_progress(...) to record the new progress

**Structure of progress.md**:
# Goal
...
# Completed
- ...
# In Progress
- ...
# Open Questions
- ...
```

Run with `--resume`: the Agent **reads progress.md on its own** instead of starting from zero.

```
$ python 04_progress.py
[Session 1] Goal: Help me organize the lab3 code and write a README
   ... (ctrl-C halfway through)

$ python 04_progress.py --resume
[Session 2] 
[Agent] → read_progress()
[Agent] Last time I finished the outline + file list. This session I'll continue: filling in demo3's description...
```

**This is the key capability of a long-running Agent.**

## Demo 5 · Run a Real Small Task

```bash
python 05_real_task.py
```

Have the mini-harness write a README for you. `05_real_task.py` ships with a fake project (a simple todo app). The Agent will:

1. Read the project structure
2. Read key files
3. Spawn a sub-agent to analyze the architecture
4. Write README.md
5. Record "first draft README written" in progress.md

After it finishes, check `fake_project/README.md` — you'll see it contains:

- Project introduction ✓
- Dependencies ✓
- Usage instructions ✓
- File structure ✓
- A paragraph of "my opinion" feedback for the developer ✓ ← that's the Agent's "self-evaluation"

## Lab Exercises

After running the 5 demos:

1. **Add a new tool**: give Demo 1 a `web_search(query)` tool (using the DuckDuckGo HTML endpoint / a search API) and watch how the Agent uses it to answer current-events questions.
2. **Add a permission mode**: implement `permission_mode = "plan"` — the Agent can only produce a plan (a list of steps) and cannot call any write tool.
3. **Add an evaluator**: emulate Anthropic's P-G-E architecture by adding an evaluator sub-agent. Let it read the code the generator wrote, run pytest, and write the results into `eval_contracts.json`.
4. **Swap to the Anthropic API**: replace the OpenAI client with the Anthropic client and run the mini-harness on Claude. Look for any compatibility quirks.
5. **Stretch challenge**: turn the mini-harness into a "Coding Agent" — let it run for 30 minutes on a real small project. Can it complete a full feature? Compare it to Claude Code: where's the gap?

After finishing these, **you'll have the ability to independently design, implement, and debug a production Harness.**

---

Next section: [§3.6 References →](./references.md)
