"""Demo 4 · Structured Output（JSON Schema 强制）

要点：
- 用 response_format={"type": "json_schema", ...} 强制输出严格 JSON
- 如果模型 / 服务端不支持 strict mode，退化到 prompt 软约束 + json.loads
- 故意丢一段不含某字段的输入，看模型怎么处理
"""
import json
from _common import get_client, MODEL, banner

client = get_client()

SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "phone": {"type": "string"},
        "city": {"type": "string"},
        "district": {"type": "string"},
    },
    "required": ["name", "phone", "city", "district"],
    "additionalProperties": False,
}


def extract_strict(text: str) -> dict:
    """走 OpenAI strict mode（最稳）。"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "从用户消息里抽取关键字段。未提及的字段填空字符串。"},
            {"role": "user", "content": text},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "extract", "schema": SCHEMA, "strict": True},
        },
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)


def extract_soft(text: str) -> dict:
    """退化方案：靠 prompt 软约束。"""
    prompt = (
        "从下面的消息里抽取 name / phone / city / district 四个字段，"
        "用 JSON 返回。未提及的字段填空字符串。**只返回 JSON 一行，不要任何 Markdown / 解释**。\n\n"
        f"消息: {text}"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip()
    # 兜底剥掉 markdown code fence
    if raw.startswith("```"):
        raw = raw.strip("`").strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()
    return json.loads(raw)


SAMPLES = [
    "我叫张三，电话 13800138000，住在北京市朝阳区。",
    "联系人：王五，住上海浦东。",  # 缺 phone
    "Hi, this is Alice. Phone: 555-1234. SF / Mission.",  # 英文
]


def main():
    banner("Demo 4 · Structured Output")
    for s in SAMPLES:
        print(f"\n输入: {s}")
        try:
            data = extract_strict(s)
            print(f"strict 模式: {json.dumps(data, ensure_ascii=False)}")
        except Exception as e:
            print(f"strict 模式失败（{e}），退化到 soft 模式...")
            try:
                data = extract_soft(s)
                print(f"soft 模式:   {json.dumps(data, ensure_ascii=False)}")
            except Exception as e2:
                print(f"soft 模式也失败: {e2}")


if __name__ == "__main__":
    main()
