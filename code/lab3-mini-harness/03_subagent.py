"""Demo 3 · Sub-agent

主 Agent 多一个 `task` 元工具：可以 spawn 一个子 Agent 跑独立 context，
子 Agent 完成后返回 ≤1500 字摘要。

主 Agent 的 context 只多了摘要，子 Agent 内部工具调用过程不进入主 context。
"""
import json
from _common import get_client, MODEL, banner, C
from importlib import import_module

m1 = import_module("01_tool_loop")
client = get_client()


# ─── Sub-agent 实现 ───────────────────────────────────
SUB_AGENT_SYSTEMS = {
    "researcher": (
        "你是一个研究员。会被分派一个研究任务，需要使用提供的工具自主完成。"
        "**最终结果**：用不超过 1500 字的中文摘要描述发现，结构化输出。"
        "不要返回 'I have completed' 这种空话，直接给摘要。"
    ),
    "reviewer": (
        "你是一个代码 / 文本审查员。指出 bug、不一致、改进建议。"
        "**最终结果**：用结构化清单输出（每条不超过 30 字），不超过 1500 字。"
    ),
}

# 子 Agent 只用只读工具，更安全
SUB_TOOLS = [s for s in m1.TOOLS_SCHEMA if s["function"]["name"] != "write_file"]


def run_sub_agent(role: str, prompt: str, max_steps: int = 8) -> str:
    """独立 context、独立 loop，最终返回 final text。"""
    sub_messages = [
        {"role": "system", "content": SUB_AGENT_SYSTEMS[role]},
        {"role": "user", "content": prompt},
    ]
    print(f"{C.MAGENTA}  ⤷ [sub-agent · {role}] start{C.END}")
    for step in range(max_steps):
        resp = client.chat.completions.create(
            model=MODEL, messages=sub_messages, tools=SUB_TOOLS, temperature=0
        )
        msg = resp.choices[0].message
        sub_messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            print(f"{C.MAGENTA}  ⤷ [sub-agent · {role}] done in {step+1} steps{C.END}")
            return msg.content or "(empty)"
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            print(f"{C.MAGENTA}     ⤷ {tc.function.name}({json.dumps(args, ensure_ascii=False)[:80]}){C.END}")
            try:
                result = m1.TOOLS_IMPL[tc.function.name](**args)
            except Exception as e:
                result = f"Error: {e}"
            sub_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False)[:4000],
            })
    return "[sub-agent: max steps exceeded]"


# ─── 主 Agent 多一个 `task` 工具 ──────────────────────
def call_task(role: str, prompt: str) -> str:
    return run_sub_agent(role, prompt)


TASK_TOOL = {
    "type": "function",
    "function": {
        "name": "task",
        "description": (
            "Spawn a sub-agent in a **fresh context window** to handle a heavy sub-task."
            " The sub-agent has its own read/list tools. Returns a condensed summary (≤1500 chars)."
            " 用于：需要大量文件扫描 / 长内容综合 / 评估等任务，避免污染主 context。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "role": {"type": "string", "enum": ["researcher", "reviewer"]},
                "prompt": {"type": "string", "description": "给子 Agent 的具体任务描述。"},
            },
            "required": ["role", "prompt"],
        },
    },
}

MAIN_TOOLS_SCHEMA = m1.TOOLS_SCHEMA + [TASK_TOOL]
MAIN_TOOLS_IMPL = {**m1.TOOLS_IMPL, "task": call_task}


def run_main(user_message: str, max_steps: int = 8) -> str:
    messages = [
        {"role": "system", "content": (
            "你是 Coordinator Agent。"
            "对于需要大量文件搜索 / 综合 / 审查的子任务，**优先 spawn sub-agent**（task 工具）。"
            "保持主对话简洁。"
        )},
        {"role": "user", "content": user_message},
    ]
    for step in range(max_steps):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=MAIN_TOOLS_SCHEMA, temperature=0
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if msg.content:
            print(f"{C.BLUE}[main · step {step+1}] {msg.content[:200]}{C.END}")
        if not msg.tool_calls:
            return msg.content or "(no content)"
        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments or "{}")
            print(f"{C.CYAN}  → {name}({json.dumps(args, ensure_ascii=False)[:100]}){C.END}")
            try:
                result = MAIN_TOOLS_IMPL[name](**args)
            except Exception as e:
                result = f"Error: {e}"
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False)[:4000],
            })
    return "[max steps]"


def main():
    banner("Demo 3 · Sub-agent")
    task = (
        "我想了解 lab3-mini-harness 这个目录的整体架构。"
        "请 spawn 一个 researcher 子 Agent 扫描所有 .py 文件给我一份架构摘要，"
        "然后基于摘要告诉我：哪个文件最适合作为入门第一个读的？"
    )
    print(f"{C.BOLD}Task: {task}{C.END}")
    result = run_main(task)
    print(f"\n{C.GREEN}{C.BOLD}=== Final ==={C.END}\n{result}")


if __name__ == "__main__":
    main()
