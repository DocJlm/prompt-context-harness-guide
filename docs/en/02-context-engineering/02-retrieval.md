---
title: §2.2 Retrieval · Get the Right Info Into the Window
description: RAG pipeline, just-in-time retrieval, hybrid search
---

# §2.2 Retrieval: Get the Right Info Into the Window

> "Rather than pre-processing all relevant data upfront, agents can maintain **lightweight identifiers** (file paths, queries, links) and dynamically load data at runtime using tools."  
> — Anthropic, *Effective Context Engineering for AI Agents*

## 1. Why Retrieval?

You have 10,000 internal documents. A single user question may need at most 5 of them. **The other 9,995 must not enter the context window.**

That is the motivation for RAG (Retrieval-Augmented Generation): **before the model answers, a search system finds the most relevant k pieces of material and injects them into context, then the model generates.**

## 2. Classic RAG Pipeline

```
                       Offline indexing
                       ┌───────────────────────┐
  Docs ─→ Chunker ─→ Embed ─→ Vector DB  ─────│─→ Index
                       └───────────────────────┘

                       Online retrieval
  User Query ─→ Embed ─→ Vector DB ─→ Top-k ─→ Rerank ─→ Inject ─→ LLM ─→ Answer
                                                  ↑
                                            (optional Cross-encoder)
```

### Offline indexing

1. **Chunk**: cut documents into 200–500 token blocks.
2. **Embed**: use an embedding model (`text-embedding-3-small`, `BAAI/bge-m3`, `Qwen3-Embedding`, `OpenAI text-embedding-3`) to turn each block into a vector.
3. **Store in a vector DB**: Chroma / FAISS / Milvus / Qdrant / Postgres+pgvector / Elasticsearch.

### Online retrieval

1. User query → embed → get vector.
2. Vector DB returns top-k (typically k=20–50) similar chunks.
3. (Optional) **Rerank**: a stronger cross-encoder model reorders them, picking top-5.
4. Inject the top-5 into the prompt:
   ```
   Below is relevant material:
   <doc1 source="...">{chunk1}</doc1>
   <doc2 source="...">{chunk2}</doc2>
   ...
   Please answer the user's question based on the material above: {query}
   If the material does not contain an answer, reply "I don't know."
   ```

## 3. Chunking: An Underrated Decision

Chunks are not "the smaller the better" nor "the larger the better."

| Chunk size | Pros | Cons |
| :--- | :--- | :--- |
| Short (128t) | High recall precision | Fragmented context, incomplete answers |
| Medium (512t) | Balanced (**recommended starting point**) | — |
| Long (1500t) | Complete context | Noisier recall |

**Advanced strategies**:
- **Recursive chunk**: split by sections → paragraphs → sentences, preserving structure.
- **Overlap**: 50t overlap between adjacent chunks reduces boundary loss.
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
| `text-embedding-3-small` (OpenAI) | 1536 | Good | Cloud | Cost-effective |
| `text-embedding-3-large` (OpenAI) | 3072 | Excellent | Cloud | Expensive |
| `BAAI/bge-m3` | 1024 | Excellent | Local / Cloud | Top pick for Chinese+English |
| `BAAI/bge-large-zh-v1.5` | 1024 | Excellent | Local | Veteran Chinese |
| `Qwen3-Embedding-8B` | 4096 | Excellent | Cloud (DashScope) | Very high Chinese quality |
| `gte-Qwen2-7B-instruct` | 3584 | Excellent | Local | Open-source flagship |

**For Chinese scenarios**: start with `bge-m3` or `Qwen3-Embedding` — cheap and stable.

## 5. Hybrid Search

Vector retrieval excels at **semantic similarity** but is weak at **exact keyword matching** (names, product codes, numbers).

**Hybrid = vector retrieval + BM25 keyword retrieval**:

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

RRF needs no score normalization and is **rock-solid in practice**.

## 6. Rerank: Second-Stage Refinement

Among the top-50 of vector retrieval, the top-5 are often not actually the best. Reorder with a **Cross-encoder Reranker**:

```python
from sentence_transformers import CrossEncoder
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

def rerank(query, candidates, top_n=5):
    pairs = [(query, c.text) for c in candidates]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda x: -x[1])
    return [c for c, _ in ranked[:top_n]]
```

Empirical numbers: BGE-reranker / Cohere Rerank typically pushes top-5 accuracy from ~70% to ~88%. **Rerank is more cost-effective than upgrading to a larger embedding.**

## 7. Just-in-Time Retrieval (Anthropic's Recommended Paradigm)

Classic RAG is **all-at-once retrieval → one-shot injection**. In *Context Engineering*, Anthropic emphasizes a paradigm better suited to agents:

> "Agents can maintain **lightweight identifiers** (file paths, queries, links) and **dynamically load data at runtime** using tools, rather than pre-processing all relevant data upfront."

In other words:

```
Classic RAG:
[User Query]
   ↓
[Embed + Search] ─→ top-5 chunks (5K tokens) ─→ Inject ─→ LLM

Just-in-time (Anthropic-recommended):
[User Query]
   ↓
LLM ─tool call→ search_docs("X refund process")  → snippet 1
   ↓
LLM ─tool call→ read_file("policy/refund.md") → snippet 2
   ↓
LLM decides → Answer
```

Difference:

| Dimension | Classic RAG | Just-in-Time |
| :--- | :--- | :--- |
| Retrieval timing | Once, before the LLM | LLM decides, multiple calls |
| Context cost | Fixed ~5K | On-demand, could be cheaper or more |
| Suited to | Single-turn Q&A | Multi-turn agents, coding |
| Control granularity | Coarse | Fine |
| Implementation complexity | Low | Medium (requires tool loop) |

**Conclusion**: Use classic RAG for single-turn Q&A; use just-in-time for agents / coding (Claude Code, Cursor, Codex all do this).

## ⚡ Side note · "Million-token Context" in Chinese Big-Tech Production

In 2025 several Chinese tech companies hit engineering breakthroughs on the **long-context + RAG synergy** worth capturing:

### Alibaba Tongyi Qwen-Agent — Use RAG to Stretch 8K to 1M
Alibaba's Tongyi Lab released Qwen-Agent (github.com/QwenLM/Qwen-Agent), which demonstrates an engineering trick:

> "**Qwen-Agent has the ability to remember context** and maintain state across a conversation."  
> By **chunking documents and keeping only the most relevant parts** via RAG, it stretches the base model's 8K context to handle documents at the **million-token scale**.  
> — [Alibaba Cloud developer community, first posted 2024-10](https://developer.aliyun.com/article/1647468)

**The implication**: the size of the base window is not the endpoint. **A good RAG + chunking strategy can "virtually" enlarge your window by 100×.** This is also why §2.2 is the core of §2 — retrieval determines the "effective size" of your window.

### DeepSeek MLA — Shrink KV Cache 4–7×
DeepSeek V3/R1's **MLA (Multi-head Latent Attention)** squeezes the KV cache to roughly 70KB per token:

> "**DeepSeek-V3's KV cache per token is only 70KB, 1/7 to 1/4 of traditional methods.**"  
> — [Chen Wei: An analysis of DeepSeek V3/R1 architecture and training, Zhihu](https://zhuanlan.zhihu.com/p/21208287743)

What this means: **model-architecture optimization and application-layer context engineering multiply**. No matter how well your harness is written, a base model with a large KV cache is expensive; MLA shrinks per-token KV by 4–7×, effectively expanding your context by 4–7× for free.

### Moonshot Kimi MoBA + DeepSeek NSA — "Long Context That Actually Runs"
In the same period of 2025, two labs published **sparse attention** papers: DeepSeek's NSA (with Liang Wenfeng as co-author) and Moonshot's MoBA (Mixture of Block Attention). Each pushes long context into the **128K – 1M** range.

### Meituan LongCat-Flash — Zero-Compute Experts + PID Control
A more radical approach comes from Meituan:

> "LongCat-Flash achieves **100 tokens/s** generation speed on H800s, and while maintaining peak generation speed it brings output cost as low as **5 RMB per million tokens**."  
> — [Meituan Tech Team, 2025-09-01](https://tech.meituan.com/2025/09/01/longcat-flash-chat.html)

A 560B-total / ~27B-active MoE, with "zero-compute experts + a PID controller" dynamically adjusting activation. **This is the hallmark of base models optimized for agents**: pre-2025 models were optimized for chat; 2025 onward we see base models natively designed for agents (long context + high QPS + tool-call density).

::: warning Engineer's view
These numbers tell you: **when you design an Agent's context flow, the choice of model is itself part of context engineering.** The same RAG/Compaction strategy can have 5× cost-and-latency differences across Qwen / DeepSeek / Kimi / LongCat. Pick the wrong base model and no amount of clever prompting will save you.
:::

## 8. Common Causes of Retrieval Failure

Sorted by frequency. **This is where 80% of your RAG bugs come from**:

1. **Chunk size wrong** — especially when the user's question expects a one-sentence answer but chunks are 1500t: it gets recalled but answers imprecisely.
2. **Embedding model doesn't match your domain** — generic embeddings often underperform in medical / legal domains; **fine-tune or swap to a domain model**.
3. **Query too short / vague** — "that one," "the earlier thing" → add a **query rewriting** step: have a small LLM rewrite the vague query into a clear one.
4. **No rerank** — the answer is in top-20 but ranked 12th.
5. **No keyword search** — names, order numbers, error codes need **exact match** that vectors can't hit.
6. **Prompt lets the model "freestyle"** — material injected but model ignores it; add a "**use only the provided material**" constraint.

## 9. The "Three-Layer Defense" of Production RAG

A production-grade RAG typically looks like this:

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
        │    - Multi-index (sharded by category)                    │
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

Each layer wrings a bit more precision. The essence of RAG engineering is **precision compounded over multiple stages**.

## 10. Takeaways

- ✅ **Small task**: upload doc + one-shot Q&A → classic RAG is fine.
- ✅ **Multi-turn agent**: let the LLM actively `search_docs` / `read_file` → just-in-time.
- ✅ **Across multiple knowledge sources**: multi-index + query routing.
- ✅ **High precision required**: always add rerank.
- ✅ **Mixed Chinese-English / many proper nouns**: always add BM25 hybrid retrieval.
- ⚠️ **Don't forget** to tune chunk size — it's often the largest lever.

---

Next: [§2.3 Memory →](./03-memory.md)
