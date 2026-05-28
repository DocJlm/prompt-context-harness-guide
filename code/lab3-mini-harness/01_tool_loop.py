"""Demo 1 · 100 行实现 Tool Loop

最小可工作的 ReAct Harness：
  - 3 个 file 工具
  - 自动循环直到模型不再调工具
  - 错误捕获 → 回填给模型（不让循环崩）
"""
import json
import pathlib
from _common import get_client, MODEL, banner, C

client = get_client()


# ─── 工具实现 ────────────────────────────────────────────
def list_files(path: str = ".") -> list:
    p = pathlib.Path(path)
    return [str(x.name) for x in p.iterdir()]


def read_file(file_path: str, max_chars: int = 4000) -> str:
    text = pathlib.Path(file_path).read_text(encoding="utf-8")
    if len(text) > max_chars:
        return text[:max_chars] + "\n... [TRUNCATED]"
    return text


def write_file(file_path: str, content: str) -> str:
    pathlib.Path(file_path).write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} chars to {file_path}"


TOOLS_IMPL = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
}

TOOLS_SCHEMA = [
    {"type": "function", "function": {
        "name": "list_files",
        "description": "列出目录里的文件 / 目录名。",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "default": "."}},
        },
    }},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "读取一个 UTF-8 文本文件。返回内容，超过 max_chars 自动截断。",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "max_chars": {"type": "integer", "default": 4000},
            },
            "required": ["file_path"],
        },
    }},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "把文本写入文件（**覆盖**）。",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["file_path", "content"],
        },
    }},
]


# ─── Harness Tool Loop ───────────────────────────────────
def run(user_message: str, max_steps: int = 10) -> str:
    messages = [
        {"role": "system", "content": (
            "你是一个文件助手 Agent。可以用提供的工具完成任务。"
            "**每次调工具前**先用一句中文告诉用户你即将做什么。"
            "**任务完成前不要停**。"
        )},
        {"role": "user", "content": user_message},
    ]
    for step in range(max_steps):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS_SCHEMA, temperature=0
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if msg.content:
            print(f"{C.DIM}[step {step+1}] {msg.content[:200]}{C.END}")

        if not msg.tool_calls:
            return msg.content or "(no content)"

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            print(f"{C.CYAN}  → {name}({json.dumps(args, ensure_ascii=False)[:120]}){C.END}")
            try:
                result = TOOLS_IMPL[name](**args)
            except Exception as e:
                result = f"Error: {type(e).__name__}: {e}"
                print(f"{C.RED}    ⨯ {result}{C.END}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False)[:4000],
            })
    return "[max steps exceeded]"


def main():
    banner("Demo 1 · Mini Tool Loop")
    task = "请列出当前目录的所有文件，然后找到其中最大的 .py 文件，告诉我它的前 30 行（用代码块）。"
    print(f"{C.BOLD}Task: {task}{C.END}")
    result = run(task)
    print(f"\n{C.GREEN}{C.BOLD}=== Final Answer ==={C.END}\n{result}")


if __name__ == "__main__":
    main()
