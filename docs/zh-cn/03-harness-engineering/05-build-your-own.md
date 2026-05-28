---
title: §3.5 动手实验 · Lab 3
description: 用 ~200 行 Python 造一个 mini Harness
---

# §3.5 动手实验：Lab 3 · 造一个 mini Harness

## 实验目标

跑完 Lab 3，你会**亲手实现**第 3 章的核心组件：

| Demo | 你会做什么 | 学到什么 |
| :---: | :--- | :--- |
| 1 | 100 行实现 ReAct Tool Loop | Harness 的"骨架" |
| 2 | 加 Hook（日志 + 危险命令拦截） | Middleware 模式 |
| 3 | 加 Sub-agent（外包搜索任务） | Sub-agent 接口 |
| 4 | 加 Progress 持久化 + Session 恢复 | 跨 Session 的工程化 |
| 5 | 跑一个真实小任务 | 让 mini harness 帮你写一篇 README |

> Lab 3 的代码位于 [`code/lab3-mini-harness/`](../../../code/lab3-mini-harness/)。它**不依赖** LangGraph / LangChain / 任何 Agent 框架——纯 Python + `openai` SDK。

## 准备

```bash
cd code/lab3-mini-harness
pip install -r requirements.txt

export OPENAI_API_KEY=sk-xxxxx
export OPENAI_BASE_URL=https://api.openai.com/v1   # 或任意 OpenAI-Compatible
export MODEL=gpt-4o-mini
```

## Demo 1 · 100 行实现 Tool Loop

```bash
python 01_tool_loop.py
```

核心 100 行（节选 - 完整文件见 lab3 目录）：

```python
import json, os
from openai import OpenAI

client = OpenAI()
MODEL = os.getenv("MODEL", "gpt-4o-mini")

# ─── 工具实现 ──────────────────────────────────────────
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
        {"role": "system", "content": "你是一个文件助手 Agent。用提供的工具完成任务。"},
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
    print(run("列出当前目录的所有文件，然后告诉我其中最大的 .py 文件是哪个，给出它的前 30 行。"))
```

**80 行**给你一个能跑的小 Agent。运行它：

```
$ python 01_tool_loop.py
[Agent] → list_files(path=".")
[Agent] → read_file(file_path="01_tool_loop.py", max_chars=4000)
[Agent] 最大的 .py 文件是 01_tool_loop.py，前 30 行如下: ...
```

## Demo 2 · 加 Hook：日志 + 危险命令拦截

```bash
python 02_hooks.py
```

加一个简单的 Hook 系统：

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
                return {"reject": True, "reason": "禁止写系统目录"}

def run_with_hooks(user_message, hooks: list[Hook], max_steps=10):
    # ... 同 demo1，但每次 tool_call 调用前后跑 hooks ...
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

跑一个会被拦截的 case：

```python
run_with_hooks("把 /etc/passwd 改名成 /etc/hello", hooks=[AuditLog(), DangerGuard()])
# → 写文件请求会被 DangerGuard 拦截
```

## Demo 3 · Sub-agent：外包搜索任务

```bash
python 03_subagent.py
```

主 Agent 多一个 `task` 工具，可以 spawn 子 Agent：

```python
def task(prompt, role="researcher"):
    """Spawn a sub-agent with a fresh context. Return a condensed summary."""
    sub_system = SUB_AGENT_SYSTEMS[role]
    sub_messages = [
        {"role": "system", "content": sub_system},
        {"role": "user", "content": prompt + "\n\n请输出不超过 1500 字的摘要作为最终结果。"},
    ]
    # 子 Agent 自己的 tool loop（这里简化，只允许 read/list）
    for _ in range(8):
        r = client.chat.completions.create(model=MODEL, messages=sub_messages, tools=SUB_TOOLS_SCHEMA)
        m = r.choices[0].message
        sub_messages.append(m)
        if not m.tool_calls:
            return m.content
        # ... handle sub tool calls ...
    return "[sub-agent: max steps]"

SUB_AGENT_SYSTEMS = {
    "researcher": "你是一个搜索员。彻底浏览给定的代码 / 文件，输出一份高密度摘要。",
    "reviewer": "你是一个代码审查员。指出 bug 和改进建议。"
}
```

主 Agent 调用：

```
User: "我想了解 lab3 这个目录的整体架构。"

[Main Agent] → task(role="researcher", prompt="扫描 lab3-mini-harness 目录的所有 .py 文件，输出架构摘要")
   [Sub-Agent thinking...]
   [Sub-Agent] → list_files
   [Sub-Agent] → read_file(01_tool_loop.py)
   [Sub-Agent] → read_file(02_hooks.py)
   [Sub-Agent] → read_file(03_subagent.py)
   [Sub-Agent] returns: "Lab 3 由 5 个 demo 组成... 主要展示 Harness 的最小可行实现..."

[Main Agent] 根据子 Agent 摘要给出最终回答。
```

注意：**Main agent 的 context 只多了 1500 字的子 Agent 摘要**，而不是 30K 字的源码内容。

## Demo 4 · Progress 持久化 + Session 恢复

```bash
python 04_progress.py
python 04_progress.py --resume
```

加两个工具：

```python
def update_progress(content):
    open("progress.md", "w").write(content)
    return "progress saved"

def read_progress():
    try: return open("progress.md").read()
    except FileNotFoundError: return "(no previous progress)"
```

加到 system prompt：

```
你是一个项目 Agent。

**Session 启动时**必须先做：
1. read_progress() → 看上次进度
2. 决定本 session 要做的下一步
3. 在 session 退出前，update_progress(...) 记录新进度

**progress.md 的结构**：
# Goal
...
# Completed
- ...
# In Progress
- ...
# Open Questions
- ...
```

用 `--resume` 跑：Agent **会自己读 progress.md** 而不是从零开始。

```
$ python 04_progress.py
[Session 1] Goal: 帮我整理 lab3 的代码并写 README
   ... (跑到一半 ctrl-C)

$ python 04_progress.py --resume
[Session 2] 
[Agent] → read_progress()
[Agent] 上次完成了概要 + 文件清单，本 session 继续：补全 demo3 的说明...
```

**这就是长跑型 Agent 的关键能力**。

## Demo 5 · 跑一个真实小任务

```bash
python 05_real_task.py
```

让 mini-harness 帮你写一个 README。`05_real_task.py` 自带一个 fake project（一个简单的待办应用）。Agent 会：

1. 读 project 结构
2. 读关键文件
3. 起一个 sub-agent 分析架构
4. 写 README.md
5. 在 progress.md 里记录"已写第一版 README"

跑完看 `fake_project/README.md`，会发现它有：

- 项目简介 ✓
- 依赖 ✓
- 使用方法 ✓
- 文件结构 ✓
- 一段反馈给开发者的"我的看法" ✓ ← 这就是 Agent 的"自评"

## 实验作业

跑完 5 个 demo 之后：

1. **加新工具**：给 Demo 1 加一个 `web_search(query)` 工具（用 DuckDuckGo HTML 接口 / 搜索 API），看 Agent 怎么用它回答时事问题。
2. **加权限模式**：实现 `permission_mode = "plan"`——Agent 只能产出 plan（list of steps），不能真调写类工具。
3. **加 evaluator**：仿 Anthropic 的 P-G-E 架构，加一个 evaluator sub-agent，让它读 generator 写的代码并跑 pytest，把结果写进 `eval_contracts.json`。
4. **改用 Anthropic API**：把 OpenAI client 换成 Anthropic client，让 mini-harness 跑 Claude。看会不会有任何奇怪的兼容性问题。
5. **挑战题**：把 mini-harness 改成"Coding Agent"——让它在一个真实的小项目里跑 30 分钟，能不能完成一个完整 feature？把它和 Claude Code 对比一下，差距在哪？

完成之后，你**已经具备了独立设计、实现、调试一个生产 Harness 的能力**。

---

下一节：[§3.6 参考文献 →](./references.md)
