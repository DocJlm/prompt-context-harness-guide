"""Demo 3 · Hybrid 检索（BM25 + Vector）+ RRF 融合

观察：
- 纯向量 vs 纯 BM25 vs Hybrid 三种召回 top-3 的差异
- 对包含"7 天" "3-5 个工作日"这类数字 / 短语 query，BM25 通常更稳
"""
import sys
import re
from typing import List
from rank_bm25 import BM25Okapi
from _common import embed, get_chroma, banner


def tokenize_cn(text: str) -> List[str]:
    """简单中英 token：单字 + 英文单词。"""
    text = re.sub(r"\s+", " ", text).strip()
    tokens = []
    for tok in re.findall(r"[a-zA-Z0-9]+|[一-鿿]", text):
        tokens.append(tok.lower())
    return tokens


def load_corpus():
    coll = get_chroma().get_collection("docs")
    data = coll.get(include=["documents"])
    return data["ids"], data["documents"]


def search_vec(query: str, k: int = 10):
    coll = get_chroma().get_collection("docs")
    q_emb = embed([query])[0]
    res = coll.query(query_embeddings=[q_emb], n_results=k)
    return list(zip(res["ids"][0], res["documents"][0]))


def search_bm25(query: str, ids: List[str], docs: List[str], k: int = 10):
    bm25 = BM25Okapi([tokenize_cn(d) for d in docs])
    scores = bm25.get_scores(tokenize_cn(query))
    ranked = sorted(zip(ids, docs, scores), key=lambda x: -x[2])[:k]
    return [(i, d) for i, d, _ in ranked]


def rrf(rank_lists, k: int = 10, k_rrf: int = 60):
    scores = {}
    docs_by_id = {}
    for lst in rank_lists:
        for r, (doc_id, doc) in enumerate(lst):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k_rrf + r)
            docs_by_id[doc_id] = doc
    top = sorted(scores.items(), key=lambda x: -x[1])[:k]
    return [(doc_id, docs_by_id[doc_id], s) for doc_id, s in top]


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "退款多久到账"
    banner(f"Demo 3 · Hybrid Search — query='{query}'")

    ids, docs = load_corpus()
    vec_hits = search_vec(query, k=5)
    bm25_hits = search_bm25(query, ids, docs, k=5)
    hybrid_hits = rrf([vec_hits, bm25_hits], k=5)

    def show(name, hits):
        print(f"\n--- {name} top-3 ---")
        for i, h in enumerate(hits[:3]):
            doc = h[1]
            print(f"  [{i+1}] {doc[:80].strip()}…")

    show("Vector", vec_hits)
    show("BM25", bm25_hits)
    show("Hybrid (RRF)", hybrid_hits)


if __name__ == "__main__":
    main()
