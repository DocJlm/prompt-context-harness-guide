"""Demo 1 · 切块 + 向量化 + 落 Chroma"""
import os
from _common import embed, chunk, get_chroma, banner


def main():
    banner("Demo 1 · Index docs.md into Chroma")

    docs_path = os.path.join(os.path.dirname(__file__), "data", "docs.md")
    text = open(docs_path, encoding="utf-8").read()
    chunks = chunk(text, size=400, overlap=60)
    print(f"切了 {len(chunks)} 个 chunk")

    chroma = get_chroma()
    # 重建 collection
    try:
        chroma.delete_collection("docs")
    except Exception:
        pass
    coll = chroma.create_collection("docs")

    # 批量向量化
    embeddings = embed(chunks)
    coll.add(
        ids=[f"doc-{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=embeddings,
    )
    print(f"已索引 {coll.count()} 个 chunk 到 .chroma/")


if __name__ == "__main__":
    main()
