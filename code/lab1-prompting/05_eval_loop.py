"""Demo 5 · 跑一个最小 Eval Loop

对比 v1 (zero-shot) vs v2 (few-shot + structured output) 在一个 golden set 上的准确率。
"""
import json
import re
from _common import get_client, MODEL, banner

client = get_client()

GOLDEN_SET = [
    {"input": "登录页一直转圈进不去。", "expected": "bug"},
    {"input": "如果能加个夜间模式就完美了。", "expected": "feature"},
    {"input": "客服 5 分钟响应，太赞了！", "expected": "praise"},
    {"input": "页面加载贼慢", "expected": "bug"},
    {"input": "希望能支持导入 CSV", "expected": "feature"},
    {"input": "今天的天气真不错", "expected": "other"},
    {"input": "我的订单状态查不到", "expected": "bug"},
    {"input": "强烈建议增加多人协作", "expected": "feature"},
    {"input": "你们的客服真敬业，半夜都回我", "expected": "praise"},
    {"input": "怎么注销账号？", "expected": "other"},
    {"input": "404 again, fix it!", "expected": "bug"},
    {"input": "Add dark mode plz.", "expected": "feature"},
    {"input": "Love the new UI", "expected": "praise"},
    {"input": "What's your refund policy?", "expected": "other"},
    {"input": "用了三天感觉一般", "expected": "other"},
    {"input": "上传失败显示 500 错误", "expected": "bug"},
    {"input": "支持下导出 PDF 吧", "expected": "feature"},
    {"input": "客服小姐姐巨耐心！", "expected": "praise"},
    {"input": "你们公司在哪？", "expected": "other"},
    {"input": "按钮点了没反应", "expected": "bug"},
]


def classify_v1(text: str) -> str:
    """v1 · Zero-shot."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "把用户反馈分类为 bug / feature / praise / other 之一。"},
            {"role": "user", "content": text},
        ],
        temperature=0,
    )
    out = response.choices[0].message.content.strip().lower()
    # 抓出 bug/feature/praise/other 任一
    m = re.search(r"\b(bug|feature|praise|other)\b", out)
    return m.group(1) if m else "other"


SCHEMA_V2 = {
    "type": "object",
    "properties": {
        "reason": {"type": "string"},
        "intent": {"type": "string", "enum": ["bug", "feature", "praise", "other"]},
    },
    "required": ["reason", "intent"],
    "additionalProperties": False,
}


def classify_v2(text: str) -> str:
    """v2 · Few-shot + Structured Output."""
    messages = [
        {"role": "system", "content": (
            "你是 X 公司的用户反馈意图分类器。"
            "分类标签：bug / feature / praise / other。"
            "**先用一句话写出判断依据**，再给分类。"
        )},
        {"role": "user", "content": "我上周买的鞋子开胶了，能换吗？"},
        {"role": "assistant", "content": '{"reason": "提到商品质量问题，属于 bug 反馈", "intent": "bug"}'},
        {"role": "user", "content": "希望加个一键导出 Excel 的功能。"},
        {"role": "assistant", "content": '{"reason": "明确要求新功能", "intent": "feature"}'},
        {"role": "user", "content": "客服小哥哥真厉害！"},
        {"role": "assistant", "content": '{"reason": "正向表扬", "intent": "praise"}'},
        {"role": "user", "content": "你们星期天上班吗？"},
        {"role": "assistant", "content": '{"reason": "查询信息，与产品反馈无关", "intent": "other"}'},
        {"role": "user", "content": text},
    ]
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "feedback", "schema": SCHEMA_V2, "strict": True},
            },
            temperature=0,
        )
        return json.loads(response.choices[0].message.content)["intent"]
    except Exception:
        # 不支持 strict mode 的服务回退到普通调用
        response = client.chat.completions.create(model=MODEL, messages=messages, temperature=0)
        raw = response.choices[0].message.content.strip().strip("`").lstrip("json").strip()
        try:
            return json.loads(raw)["intent"]
        except Exception:
            m = re.search(r"\b(bug|feature|praise|other)\b", raw.lower())
            return m.group(1) if m else "other"


def evaluate(name: str, classify_fn) -> tuple[float, list]:
    correct = 0
    fails = []
    for case in GOLDEN_SET:
        got = classify_fn(case["input"])
        if got == case["expected"]:
            correct += 1
        else:
            fails.append({"input": case["input"], "expected": case["expected"], "got": got})
    acc = correct / len(GOLDEN_SET)
    print(f"  [{name}] {correct}/{len(GOLDEN_SET)} = {acc:.1%}")
    return acc, fails


def main():
    banner("Demo 5 · Eval Loop (v1 zero-shot vs v2 few-shot + JSON)")
    acc1, fails1 = evaluate("v1", classify_v1)
    acc2, fails2 = evaluate("v2", classify_v2)
    print(f"\n→ Delta: v1={acc1:.1%}, v2={acc2:.1%}, lift={(acc2-acc1)*100:+.1f}pp")

    print("\nFailures in v2:")
    for f in fails2:
        print(f"  ✗ '{f['input']}' → got={f['got']} (want={f['expected']})")


if __name__ == "__main__":
    main()
