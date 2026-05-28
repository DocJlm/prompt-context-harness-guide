"""Demo 5 · 真实小任务：为 fake_project 写一份 README

集合前 4 个 demo 的所有能力：
  - tool loop
  - hooks（DangerGuard）
  - sub-agent（researcher）
  - progress tracking

跑完看 fake_project/README.md：是不是像一份真实工程师写的 README。
"""
import json
import pathlib
from _common import get_client, MODEL, banner, C
from importlib import import_module

m1 = import_module("01_tool_loop")
m2 = import_module("02_hooks")
m3 = import_module("03_subagent")

client = get_client()

FAKE_PROJECT_DIR = pathlib.Path(__file__).parent / "fake_project"


def ensure_fake_project():
    """生成一个简单的待办应用作为'真实小项目'。"""
    FAKE_PROJECT_DIR.mkdir(exist_ok=True)
    (FAKE_PROJECT_DIR / "main.py").write_text(
        '"""Simple TODO CLI."""\nimport json, sys, pathlib\n\n'
        'DATA = pathlib.Path(__file__).parent / "todos.json"\n\n'
        'def load(): return json.loads(DATA.read_text()) if DATA.exists() else []\n'
        'def save(todos): DATA.write_text(json.dumps(todos, ensure_ascii=False, indent=2))\n\n'
        'def add(text): t = load(); t.append({"text": text, "done": False}); save(t); print("added")\n'
        'def list_all(): [print(f"[{\\"x\\" if t[\\"done\\"] else \\" \\"}] {i}. {t[\\"text\\"]}") for i, t in enumerate(load())]\n'
        'def done(i): t = load(); t[int(i)]["done"] = True; save(t); print("done")\n\n'
        'if __name__ == "__main__":\n'
        '    cmd, *args = sys.argv[1:] if len(sys.argv) > 1 else ["list"]\n'
        '    {"add": add, "list": list_all, "done": done}[cmd](*args)\n',
        encoding="utf-8",
    )
    (FAKE_PROJECT_DIR / "requirements.txt").write_text("# pure stdlib\n", encoding="utf-8")
    (FAKE_PROJECT_DIR / "tests.py").write_text(
        '"""Smoke tests for the TODO CLI."""\n'
        'import subprocess, sys, pathlib\n'
        'HERE = pathlib.Path(__file__).parent\n\n'
        'def run(*args): return subprocess.check_output([sys.executable, str(HERE / "main.py"), *args]).decode()\n\n'
        'def test_add_list():\n'
        '    (HERE / "todos.json").unlink(missing_ok=True)\n'
        '    run("add", "buy milk")\n'
        '    assert "buy milk" in run("list")\n'
        '    print("test_add_list OK")\n\n'
        'if __name__ == "__main__":\n'
        '    test_add_list()\n',
        encoding="utf-8",
    )


# ─── 主 Agent 全工具集合 ────────────────────────────────
ALL_TOOLS_IMPL = {**m3.MAIN_TOOLS_IMPL}
ALL_TOOLS_SCHEMA = m3.MAIN_TOOLS_SCHEMA  # 含 task + 文件工具


SYSTEM = """你是一个 Documentation Agent，要为一个小项目写 README.md。

# 流程
1. 用 `task(role="researcher")` spawn 一个子 Agent 扫描整个项目，
   返回项目结构、文件作用、用法摘要。
2. 基于摘要写一份 README.md，包含：
   - 项目简介（1-2 句）
   - 文件结构（用 tree 展示）
   - 安装 / 依赖
   - 使用方法（命令示例）
   - 测试方法
   - 一段"我作为 Agent 的开发反馈"
3. 用 write_file 写入 fake_project/README.md
4. 退出前简要说明你做了什么
"""


def run(user_message: str, max_steps: int = 12) -> str:
    hooks = [m2.AuditLog(), m2.DangerGuard()]
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_message},
    ]
    for step in range(max_steps):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=ALL_TOOLS_SCHEMA, temperature=0
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if msg.content:
            print(f"{C.BLUE}[main · step {step+1}] {msg.content[:200]}{C.END}")
        if not msg.tool_calls:
            return msg.content or "(no content)"
        for tc in msg.tool_calls:
            rejected = None
            for h in hooks:
                r = h.before_tool(tc)
                if r and r.get("reject"):
                    rejected = r["reason"]; break
            if rejected:
                print(f"{C.RED}  ✗ {rejected}{C.END}")
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": f"[rejected] {rejected}"})
                continue
            args = json.loads(tc.function.arguments or "{}")
            print(f"{C.CYAN}  → {tc.function.name}({json.dumps(args, ensure_ascii=False)[:100]}){C.END}")
            try:
                result = ALL_TOOLS_IMPL[tc.function.name](**args)
            except Exception as e:
                result = f"Error: {e}"
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False)[:4000],
            })
    return "[max steps]"


def main():
    banner("Demo 5 · Real task — write README for fake_project")
    ensure_fake_project()
    print(f"{C.YELLOW}fake_project 已经生成在: {FAKE_PROJECT_DIR}{C.END}")
    result = run(f"请为 {FAKE_PROJECT_DIR} 项目写一份完整的 README.md。")
    print(f"\n{C.GREEN}{C.BOLD}=== Final ==={C.END}\n{result}")
    readme = FAKE_PROJECT_DIR / "README.md"
    if readme.exists():
        print(f"\n{C.BOLD}--- {readme} ---{C.END}\n{readme.read_text(encoding='utf-8')}")


if __name__ == "__main__":
    main()
