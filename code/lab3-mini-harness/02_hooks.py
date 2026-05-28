"""Demo 2 · Hooks（Middleware）

加两类 Hook：
  - AuditLog：所有工具调用打日志
  - DangerGuard：拦截高危写操作

观察：尝试让 Agent 写 /etc/test.txt，会被拦截，并把"被拒"作为 tool_result 回填，
让 Agent 知道并道歉 / 换条路。
"""
import json
from _common import get_client, MODEL, banner, C

# 复用 demo1 的工具
from importlib import import_module
m1 = import_module("01_tool_loop")
TOOLS_IMPL = m1.TOOLS_IMPL
TOOLS_SCHEMA = m1.TOOLS_SCHEMA

client = get_client()


# ─── Hook 框架 ────────────────────────────────────────
class Hook:
    def before_tool(self, tc) -> dict | None:
        """返回 {'reject': True, 'reason': '...'} 即拒绝。"""
        return None

    def after_tool(self, tc, result) -> None:
        pass


class AuditLog(Hook):
    def before_tool(self, tc) -> None:
        print(f"{C.YELLOW}  📝 [audit] {tc.function.name}({tc.function.arguments[:120]}){C.END}")


class DangerGuard(Hook):
    BLOCKED_PREFIXES = ("/etc/", "/usr/", "/bin/", "/var/", "/boot/", "/root/")

    def before_tool(self, tc) -> dict | None:
        name = tc.function.name
        try:
            args = json.loads(tc.function.arguments)
        except json.JSONDecodeError:
            return None
        if name == "write_file":
            path = args.get("file_path", "")
            if path.startswith(self.BLOCKED_PREFIXES) or path.startswith("/"):
                return {"reject": True, "reason": f"DangerGuard: 禁止写系统路径 {path}"}
        return None


def run_with_hooks(user_message: str, hooks: list, max_steps: int = 10) -> str:
    messages = [
        {"role": "system", "content": (
            "你是一个文件助手 Agent。可以用提供的工具完成任务。"
            "如果某个工具调用被拒绝，请遵守约束、换一条路完成任务，不要重复尝试同样的危险操作。"
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
            rejection = None
            for h in hooks:
                r = h.before_tool(tc)
                if r and r.get("reject"):
                    rejection = r["reason"]
                    break
            if rejection:
                print(f"{C.RED}  ✗ rejected: {rejection}{C.END}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": f"[hook rejected] {rejection}",
                })
                continue

            try:
                args = json.loads(tc.function.arguments)
                result = TOOLS_IMPL[tc.function.name](**args)
            except Exception as e:
                result = f"Error: {type(e).__name__}: {e}"
            for h in hooks:
                h.after_tool(tc, result)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False)[:4000],
            })
    return "[max steps exceeded]"


def main():
    banner("Demo 2 · Hooks (AuditLog + DangerGuard)")
    # 故意诱导：让 Agent 试着写一个系统路径
    task = "请创建一个文件 /etc/notes.txt，里面写 'hello'。然后再创建 ./safe_notes.txt 写 'hello'。最后告诉我哪一步成功了。"
    print(f"{C.BOLD}Task: {task}{C.END}")
    result = run_with_hooks(task, hooks=[AuditLog(), DangerGuard()])
    print(f"\n{C.GREEN}{C.BOLD}=== Final ==={C.END}\n{result}")


if __name__ == "__main__":
    main()
