"""Demo 2 · 经典 RAG QA

观察：
- 改 system prompt 的"仅基于资料"约束 → 容易出幻觉
- 调 top_k → 召回数量与质量的 trade-off
"""
import sys
from _common import get_client, embed, get_chroma, MODEL, banner

client = get_client()


def rag_answer(query: str, top_k: int = 5) -> str:
    coll = get_chroma().get_collection("docs")
    q_emb = embed([query])[0]
    hits = coll.query(query_embeddings=[q_emb], n_results=top_k)
    context_chunks = hits["documents"][0]

    context_block = "\n\n---\n\n".join(
        f"[doc {i+1}]\n{c}" for i, c in enumerate(context_chunks)
    )

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": (
                "你是 X 公司的客服助手。**仅基于下面提供的资料**回答用户问题。"
                "若资料里没有答案，请直接回复\"抱歉，资料里没有相关信息\"。"
                "回答时引用资料编号 [doc N]。"
            )},
            {"role": "user", "content": f"资料:\n{context_block}\n\n问题: {query}"},
        ],
        temperature=0,
    )
    return resp.choices[0].message.content


def main():
    banner("Demo 2 · Classic RAG QA")
    query = sys.argv[1] if len(sys.argv) > 1 else "怎么申请退款？多久能到账？"
    print(f"\n问: {query}\n")
    print(f"答:\n{rag_answer(query)}")


if __name__ == "__main__":
    main()
