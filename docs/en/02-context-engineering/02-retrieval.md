---
title: §2.2 Retrieval · Get the Right Info into the Window
description: RAG pipeline, just-in-time retrieval, hybrid search
---

# §2.2 Retrieval: Get the Right Info into the Window

> "Rather than pre-processing all relevant data upfront, agents can maintain **lightweight identifiers** (file paths, queries, links) and dynamically load data at runtime using tools."  
> — Anthropic, *Effective Context Engineering for AI Agents*

## 1. Why Do We Need Retrieval?

You have 10,000 internal documents. A given user question might need at most 5 of them. **The other 9995 should not enter the window.**

That's the motivation for RAG (Retrieval-Augmented Generation): **before answering, a search system finds the most relevant k pieces of material**, injects them into the context, and then the model generates.

## 2. The Classic RAG Pipeline

```
                       Offline indexing
                       ┌───────────────────────┐
  Docs ─→ Chunker ─→ Embed ─→ Vector DB  ─────│─→ Index
                       └───────────────────────┘

                       Online retrieval
  User Query ─→ Embed ─→ Vector DB ─→ Top-k ─→ Rerank ─→ Inject ─→ LLM ─→ Answer
                                                  ↑
                                            (optional cross-encoder)
```

### Offline indexing

1. **Chunk**: split documents into 200–500 token blocks.
2. **Embed**: turn each block into a vector with an embedding model (`text-embedding-3-small`, `BAAI/bge-m3`, `Qwen3-Embedding`, `OpenAI text-embedding-3`).
3. **Store in a vector DB**: Chroma / FAISS / Milvus / Qdrant / Postgres+pgvector / Elasticsearch.

### Online retrieval

1. User query → embed → get vector.
2. Vector DB returns top-k (typically k=20–50) similar chunks.
3. (Optional) **Rerank**: re-order with a stronger cross-encoder model, pick top-5.
4. Inject top-5 into the prompt:
   ```
   Below are the relevant materials:
   <doc1 source="...">{chunk1}</doc1>
   <doc2 source="...">{chunk2}</doc2>
   ...
   Based on the above, answer the user's question: {query}
   If the answer isn't in the materials, reply "I don't know".
   ```

## 3. Chunking: the Underrated Lever

Chunks are neither best-when-small nor best-when-large.

| Chunk size | Pros | Cons |
| :--- | :--- | :--- |
| Short (128t) | High recall precision | Fragmented context, incomplete answers |
| Medium (512t) | Balanced (**recommended starting point**) | — |
| Long (1500t) | Complete context | More noisy retrievals |

**Advanced strategies**:
- **Recursive chunking**: split by section → paragraph → sentence, preserving structure.
- **Overlap**: 50t of overlap between adjacent chunks to avoid losing info at the boundary.
- **Parent–Child**: retrieve small chunks (precise recall), inject large chunks (complete context).

```python
# Parent–Child example
parent_chunks = split_by_section(doc)       # ~1500 tokens
for parent in parent_chunks:
    child_chunks = split_by_sentence(parent, size=200)
    for child in child_chunks:
        index.add(embed(child), {"text": child, "parent_id": parent.id})

def retrieve(query):
    hits = index.search(embed(query), top_k=5)
    parent_ids = {h.parent_id for h in hits}
    return [parents[pid] for pid in parent_ids]  # return parents
```

## 4. Choosing an Embedding Model

| Model | Dim | Chinese quality | Deployment | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `text-embedding-3-small` (OpenAI) | 1536 | good | cloud | great value |
| `text-embedding-3-large` (OpenAI) | 3072 | excellent | cloud | pricey |
| `BAAI/bge-m3` | 1024 | excellent | local / cloud | top pick for zh-en bilingual |
| `BAAI/bge-large-zh-v1.5` | 1024 | excellent | local | veteran for Chinese |
| `Qwen3-Embedding-8B` | 4096 | excellent | cloud (DashScope) | great Chinese quality |
| `gte-Qwen2-7B-instruct` | 3584 | excellent | local | open-source flagship |

**For Chinese**: start with `bge-m3` or `Qwen3-Embedding` — cheap and stable.

## 5. Hybrid Search

Vector search excels at **semantic similarity** but is weak at **exact keyword matching** (names, product codes, numbers).

**Hybrid = vector search + BM25 keyword search**:

```python
def hybrid_search(query, k=20):
    vec_hits = vector_index.search(embed(query), k=k)        # semantic
    bm25_hits = bm25_index.search(query, k=k)                # keyword
    return rrf_fusion(vec_hits, bm25_hits, k=k)              # Reciprocal Rank Fusion

def rrf_fusion(*ranked_lists, k=20, k_rrf=60):
    scores = {}
    for lst in ranked_lists:
        for rank, item in enumerate(lst):
            scores[item.id] = scores.get(item.id, 0) + 1 / (k_rrf + rank)
    return sorted(scores.items(), key=lambda x: -x[1])[:k]
```

RRF doesn't require score normalization and is **rock-solid in practice**.

## 6. Rerank: the Second-Stage Refinement

Within the top-50 from vector search, the top-5 are often not the truly best. Use a **cross-encoder reranker** to re-order:

```python
from sentence_transformers import CrossEncoder
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

def rerank(query, candidates, top_n=5):
    pairs = [(query, c.text) for c in candidates]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda x: -x[1])
    return [c for c, _ in ranked[:top_n]]
```

Empirical numbers: BGE-reranker / Cohere Rerank typically lift top-5 accuracy from ~70% to ~88%. **Reranking is more cost-effective than upgrading to a bigger embedding model.**

## 7. Just-in-Time Retrieval (Anthropic's preferred pattern)

Classic RAG is **retrieve everything up front → inject once**. In *Context Engineering*, Anthropic emphasizes a pattern that fits Agents better:

> "Agents can maintain **lightweight identifiers** (file paths, queries, links) and **dynamically load data at runtime** using tools, rather than pre-processing all relevant data upfront."

In other words:

```
Classic RAG:
[User Query]
   ↓
[Embed + Search] ─→ top-5 chunks (5K tokens) ─→ Inject ─→ LLM

Just-in-time (Anthropic's recommendation):
[User Query]
   ↓
LLM ─tool call→ search_docs("X refund process")  → snippet 1
   ↓
LLM ─tool call→ read_file("policy/refund.md") → snippet 2
   ↓
LLM decides → Answer
```

Differences:

| Dimension | Classic RAG | Just-in-Time |
| :--- | :--- | :--- |
| Retrieval timing | one-shot, before the LLM | LLM decides, multiple calls |
| Context cost | fixed ~5K | on-demand, can be lower or higher |
| Best for | single-turn QA | multi-turn agents, coding |
| Granularity of control | coarse | fine |
| Implementation complexity | low | medium (needs a tool loop) |

**Conclusion**: for single-turn QA, use classic RAG; for agent / coding scenarios, use just-in-time (Claude Code, Cursor, and Codex all work this way).

## 8. Common Reasons Retrieval Fails

In rough order of frequency — **this accounts for 80% of your RAG bugs**:

1. **Chunk size too big or too small**: especially when the user wants a one-sentence answer but the chunk is 1500 tokens — the chunk is recalled but the answer is fuzzy.
2. **Embedding model doesn't match your domain**: general-purpose embeddings often crash in medical/legal domains — **fine-tune or pick a domain-specific model**.
3. **Queries too short / too vague**: "that one", "the one before" → add a **query rewriting** step that uses a small LLM to rewrite vague queries into explicit ones.
4. **Missing rerank**: the answer is in the top-20 but ranked 12th.
5. **No keyword search**: names, order numbers, error codes — these **exact matches** are missed by vector search.
6. **Prompt lets the model "freelance"**: materials are injected but the model ignores them — remember to add "**based only on the provided materials**".

## 9. Production RAG's "Three Layers of Defense"

A production RAG generally looks like this:

```
        ┌─────────────────────────────────────────────────────────┐
        │ 1. Pre-retrieval                                         │
        │    - Query rewriting / expansion                         │
        │    - Query classification (route to which index)         │
        └──────────────────┬───────────────────────────────────────┘
                           │
        ┌──────────────────▼───────────────────────────────────────┐
        │ 2. Retrieval                                              │
        │    - Hybrid (vector + BM25)                              │
        │    - Multi-index (split DBs by category)                 │
        └──────────────────┬───────────────────────────────────────┘
                           │
        ┌──────────────────▼───────────────────────────────────────┐
        │ 3. Post-retrieval                                         │
        │    - Rerank (cross-encoder)                              │
        │    - Diversity filter (MMR)                              │
        │    - Citation extraction                                  │
        └──────────────────┬───────────────────────────────────────┘
                           │
                           ▼
                       LLM Generate
```

Each layer squeezes a bit more accuracy out. The essence of RAG engineering is **multi-stage multiplicative precision**.

## 10. Putting This Section in Your Head

- ✅ **Small task**: upload docs + single-shot QA → classic RAG is enough.
- ✅ **Multi-turn agent**: let the LLM proactively call `search_docs` / `read_file` → just-in-time.
- ✅ **Multiple knowledge sources**: multi-index + query routing.
- ✅ **High precision required**: always add a reranker.
- ✅ **Mixed Chinese-English / many proper nouns**: always add BM25 hybrid search.
- ⚠️ **Never forget** to tune chunk size — it's often the single biggest lever.

---

Next: [§2.3 Memory →](./03-memory.md)
