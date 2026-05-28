"""Demo 4 · Progress 持久化 + Session 恢复

把 §3.2 Anthropic 推荐的"长跑型 Harness"思路落地：
  - progress.md 是 Agent 的"接班手册"
  - Session 启动时第一件事：read_progress()
  - Session 结束前：update_progress()
"""
import json
import pathlib
import sys
from _common import get_client, MODEL, banner, C
from importlib import import_module

m1 = import_module("01_tool_loop")
client = get_client()

PROGRESS_PATH = pathlib.Path(__file__).parent / "progress.md"

INITIAL_PROGRESS = """# Project Progress

Last updated: (just initialized)

## Goal
为 lab3-mini-harness 目录写一份完整 README.md，覆盖：项目简介、依赖、demo 列表、跑法、学习路径。

## Completed
- (none)

## In Progress
- 需要先扫描目录、读每个 demo 的 docstring

## Open Questions
- (none)
"""


def read_progress() -> str:
    if PROGRESS_PATH.exists():
        return PROGRESS_PATH.read_text(encoding="utf-8")
    return "(no previous progress; this is a fresh start)"


def update_progress(content: str) -> str:
    PROGRESS_PATH.write_text(content, encoding="utf-8")
    return f"progress saved ({len(content)} chars)"


# 扩展工具集
PROGRESS_TOOLS_IMPL = {
    **m1.TOOLS_IMPL,
    "read_progress": read_progress,
    "update_progress": update_progress,
}
PROGRESS_TOOLS_SCHEMA = m1.TOOLS_SCHEMA + [
    {"type": "function", "function": {
        "name": "read_progress",
        "description": "读取 progress.md，了解上一次 session 留下的状态。**Session 启动时第一件事**。",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "update_progress",
        "description": "把当前进度写到 progress.md（覆盖）。**Session 结束前必做**。",
        "parameters": {
            "type": "object",
            "properties": {"content": {"type": "string", "description": "Markdown 格式的进度报告"}},
            "required": ["content"],
        },
    }},
]

SYSTEM = """你是一个长跑型项目 Agent。

# Session 启动协议（必须按顺序）
1. 调用 read_progress() 看上次进度
2. 决定本 session 要做的下一步
3. 用最多 6-8 步工具调用完成

# Session 结束协议
在准备结束 session 时（输出最终回答前），**必须**调用 update_progress(...)
把以下信息写进 progress.md：
  # Project Progress
  Last updated: ...
  ## Goal ...
  ## Completed ...
  ## In Progress ...
  ## Open Questions ...

# 工程师习惯
- 小步快跑：每次只做一个 feature
- 写代码 → 测一下 → 下一步
"""


def run_session(user_message: str, max_steps: int = 12) -> str:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_message},
    ]
    for step in range(max_steps):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=PROGRESS_TOOLS_SCHEMA, temperature=0
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if msg.content:
            print(f"{C.DIM}[step {step+1}] {msg.content[:200]}{C.END}")
        if not msg.tool_calls:
            return msg.content or "(no content)"
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            print(f"{C.CYAN}  → {tc.function.name}({json.dumps(args, ensure_ascii=False)[:100]}){C.END}")
            try:
                result = PROGRESS_TOOLS_IMPL[tc.function.name](**args)
            except Exception as e:
                result = f"Error: {e}"
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False)[:4000],
            })
    return "[max steps]"


def main():
    banner("Demo 4 · Progress-aware long-running Agent")

    if "--resume" in sys.argv:
        if not PROGRESS_PATH.exists():
            print(f"{C.YELLOW}No progress.md found; behaving like fresh session.{C.END}")
        msg = "请基于 progress.md 继续未完成的任务。完成一步后更新 progress.md 退出。"
    else:
        if not PROGRESS_PATH.exists():
            PROGRESS_PATH.write_text(INITIAL_PROGRESS, encoding="utf-8")
            print(f"{C.YELLOW}Initialized progress.md{C.END}")
        msg = "请基于 progress.md 完成下一步任务（小步快跑），完成后更新 progress.md。"

    result = run_session(msg)
    print(f"\n{C.GREEN}{C.BOLD}=== Final ==={C.END}\n{result}")
    if PROGRESS_PATH.exists():
        print(f"\n{C.BOLD}--- progress.md (after session) ---{C.END}")
        print(PROGRESS_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
