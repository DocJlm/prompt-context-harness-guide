"""Demo 5 · Compaction（上下文压缩）

模拟一个长对话，每次 LLM 调用前检查 token 估算。
超过阈值时把老的 history 压成 summary，保留最近 N 轮。

观察：
- 第几轮触发压缩？
- 压缩前后 token 数变化
- summary 是否保留了关键事实
"""
import json
from _common import get_client, MODEL, banner

client = get_client()


def estimate_tokens(messages) -> int:
    """粗估：中文 1 字 ≈ 1.5 token，英文 4 字符 ≈ 1 token。"""
    total = 0
    for m in messages:
        content = m.get("content", "") or ""
        if isinstance(content, list):
            content = json.dumps(content)
        total += len(content) // 2
    return total


THRESHOLD = 1500
KEEP_RECENT = 4  # 保留最近 N 轮（user + assistant 各算 1 条 = 2N）


def compact(messages):
    """[system] + [...old to compact] + [last KEEP_RECENT pairs] → [system] + [summary] + [last]"""
    system_msg = messages[0]
    keep = messages[-KEEP_RECENT * 2 :]
    to_compress = messages[1 : -KEEP_RECENT * 2]
    if not to_compress:
        return messages

    summary_resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": (
                "你是上下文压缩助手。请把下面的多轮对话压成简洁摘要。"
                "**重点保留**：目标 / 已决定的方案 / 未决问题 / 用户偏好。"
                "**不要保留**：寒暄、已被覆盖的方案。"
                "不超过 300 字。"
            )},
            {"role": "user", "content": "对话：\n" + json.dumps(
                [{"role": m["role"], "content": m.get("content", "")} for m in to_compress],
                ensure_ascii=False
            )},
        ],
        temperature=0,
    )
    summary = summary_resp.choices[0].message.content
    return [
        system_msg,
        {"role": "system", "content": f"[Conversation Summary]\n{summary}"},
        *keep,
    ]


SIMULATED_TURNS = [
    "你好，我想了解一下你们的退款政策。",
    "好的，那如果我买的是化妆品，能 7 天无理由退吗？",
    "明白了。再问一下，订单 48 小时没发货能取消吗？",
    "我用了优惠券买的，退款时优惠券会还吗？",
    "OK。我是 vip 金卡用户，听说有专属客服？怎么联系？",
    "钻石会员的权益和金卡相比多了什么？",
    "明白。我想申请发票，是电子的还是纸质的？",
    "纸质发票要加钱吗？专票怎么申请？",
    "好的。我想注销账户，怎么操作？",
    "注销后多久能恢复？",
    "我对刚才客服的处理不满意，怎么投诉？",
    "投诉升级会很久吗？",
]


def main():
    banner("Demo 5 · Compaction (threshold=1500 ~tokens)")
    messages = [
        {"role": "system", "content": "你是 X 公司客服助手。简洁回答用户问题。"},
    ]
    for i, turn in enumerate(SIMULATED_TURNS, 1):
        messages.append({"role": "user", "content": turn})

        # 压缩判断
        used = estimate_tokens(messages)
        print(f"\n--- Turn {i}  est_tokens={used} ---")
        if used > THRESHOLD:
            print(f"  ⚙ 触发 Compaction (over threshold {THRESHOLD})...")
            messages = compact(messages)
            print(f"  ⚙ Compacted: now ~{estimate_tokens(messages)} tokens")
            # 打印 summary 节选
            for m in messages:
                if isinstance(m.get("content"), str) and m["content"].startswith("[Conversation Summary]"):
                    print("  ⚙ Summary preview:", m["content"][:200].replace("\n", " ") + "…")
                    break

        resp = client.chat.completions.create(model=MODEL, messages=messages, temperature=0)
        answer = resp.choices[0].message.content
        messages.append({"role": "assistant", "content": answer})
        print(f"  User: {turn}")
        print(f"  Bot:  {answer[:100]}…" if len(answer) > 100 else f"  Bot:  {answer}")


if __name__ == "__main__":
    main()
