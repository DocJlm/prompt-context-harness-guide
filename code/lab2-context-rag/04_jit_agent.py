"""Demo 4 · Just-in-time 检索 Agent

让 LLM **自己**决定什么时候调 search_docs 工具，而不是开发者强行注入。
观察：
- Agent 一轮可能调 0-3 次 search
- 加约束 "最多 2 次 search" 后行为变化（Agentic Eagerness 控制）
"""
import json
from _common import get_client, embed, get_chroma, MODEL, banner

client = get_client()

TOOLS = [{
    "type": "function",
    "function": {
        "name": "search_docs",
        "description": (
            "搜索 X 公司内部知识库。"
            "**仅用于** 退款 / 物流 / 售后 / 投诉 / 会员 / 优惠券 / 发票 / 隐私 类问题。"
            "返回 top-3 相关段落。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "查询关键词，建议是短语。"},
            },
            "required": ["query"],
        },
    },
}]


def search_docs(query: str) -> str:
    coll = get_chroma().get_collection("docs")
    q_emb = embed([query])[0]
    hits = coll.query(query_embeddings=[q_emb], n_results=3)
    return "\n---\n".join(hits["documents"][0])


def run(user_msg: str, max_steps: int = 6) -> str:
    messages = [
        {"role": "system", "content": (
            "你是 X 公司的客服 Agent。"
            "涉及公司政策的问题，请用 search_docs 工具查询。"
            "每次调工具前，先用一句中文告诉用户你即将查什么（Tool Preamble）。"
            "**回答只基于检索到的资料，不要编造。**"
        )},
        {"role": "user", "content": user_msg},
    ]
    for step in range(max_steps):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, temperature=0
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            return msg.content

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            print(f"  [step {step+1}] → search_docs({args['query']})")
            result = search_docs(args["query"])
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })
    return "[max steps exceeded]"


def main():
    banner("Demo 4 · Just-in-time Retrieval Agent")
    queries = [
        "你们退款多久到账？",
        "我下了单 30 小时还没发货，怎么办？另外我买的化妆品能不能退？",
        "今天天气怎么样？",  # 不应触发 search
    ]
    for q in queries:
        print(f"\n问: {q}")
        ans = run(q)
        print(f"答: {ans}")


if __name__ == "__main__":
    main()
