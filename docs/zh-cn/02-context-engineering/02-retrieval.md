---
title: §2.2 检索 · 把对的信息塞进窗口
description: RAG 流水线，Just-in-time 检索，混合检索
---

# §2.2 检索：把对的信息塞进窗口

> "Rather than pre-processing all relevant data upfront, agents can maintain **lightweight identifiers** (file paths, queries, links) and dynamically load data at runtime using tools."  
> — Anthropic, *Effective Context Engineering for AI Agents*

## 一、为什么需要检索？

你有 10,000 篇内部文档。一个用户问题最多可能用得上其中 5 篇。**剩下 9995 篇不该进窗口**。

这就是 RAG（Retrieval-Augmented Generation）的诞生动机：**让模型在回答前，先用一个搜索系统找到最相关的 k 片资料**，把它们注入 context，再生成。

## 二、经典 RAG 流水线

```
                       离线索引
                       ┌───────────────────────┐
  Docs ─→ Chunker ─→ Embed ─→ Vector DB  ─────│─→ Index
                       └───────────────────────┘

                       在线检索
  User Query ─→ Embed ─→ Vector DB ─→ Top-k ─→ Rerank ─→ Inject ─→ LLM ─→ Answer
                                                  ↑
                                            (可选 Cross-encoder)
```

### 离线索引

1. **Chunk**：把文档切成 200–500 token 的小块。
2. **Embed**：用 embedding 模型（`text-embedding-3-small`, `BAAI/bge-m3`, `Qwen3-Embedding`, `OpenAI text-embedding-3`）把每块变成一个向量。
3. **存进向量库**：Chroma / FAISS / Milvus / Qdrant / Postgres+pgvector / Elasticsearch。

### 在线检索

1. 用户 query → embed → 拿向量。
2. 向量库返回 top-k（通常 k=20–50）相似 chunk。
3. （可选）**Rerank**：用一个更强的 cross-encoder 模型重新排序，挑出 top-5。
4. 把 top-5 注入 prompt：
   ```
   下面是相关资料：
   <doc1 source="...">{chunk1}</doc1>
   <doc2 source="...">{chunk2}</doc2>
   ...
   请基于上述资料回答用户问题：{query}
   如果资料里没有答案，请回复 "我不知道"。
   ```

## 三、Chunking 的选择：被低估的关键

Chunk 不是越小越好，也不是越大越好。

| Chunk 大小 | 利 | 弊 |
| :--- | :--- | :--- |
| 短（128t） | 召回精度高 | 上下文割裂、答案不全 |
| 中（512t） | 平衡（**推荐起步**） | — |
| 长（1500t） | 上下文完整 | 召回 noise 多 |

**进阶策略**：
- **递归 chunk**：先按章节 → 段落 → 句子层级切，保留结构。
- **Overlap**：相邻 chunk 重叠 50t，减少边界丢信息。
- **Parent–Child**：检索小 chunk（精确召回），注入大 chunk（完整上下文）。

```python
# Parent–Child 示例
parent_chunks = split_by_section(doc)       # ~1500 token
for parent in parent_chunks:
    child_chunks = split_by_sentence(parent, size=200)
    for child in child_chunks:
        index.add(embed(child), {"text": child, "parent_id": parent.id})

def retrieve(query):
    hits = index.search(embed(query), top_k=5)
    parent_ids = {h.parent_id for h in hits}
    return [parents[pid] for pid in parent_ids]  # 返回 parent
```

## 四、Embedding 模型选型

| 模型 | 维度 | 中文表现 | 部署 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `text-embedding-3-small` (OpenAI) | 1536 | 良 | 云 | 性价比高 |
| `text-embedding-3-large` (OpenAI) | 3072 | 优 | 云 | 贵 |
| `BAAI/bge-m3` | 1024 | 优 | 本地 / 云 | 中英双语首选 |
| `BAAI/bge-large-zh-v1.5` | 1024 | 优 | 本地 | 中文老牌 |
| `Qwen3-Embedding-8B` | 4096 | 优 | 云（DashScope）| 中文质量很高 |
| `gte-Qwen2-7B-instruct` | 3584 | 优 | 本地 | 开源旗舰 |

**中文场景建议**：先用 `bge-m3` 或 `Qwen3-Embedding`，便宜稳定。

## 五、混合检索（Hybrid Search）

向量检索擅长**语义相似**，但弱在**精确关键词匹配**（人名、产品代码、数字）。

**混合 = 向量检索 + BM25 关键词检索**：

```python
def hybrid_search(query, k=20):
    vec_hits = vector_index.search(embed(query), k=k)        # 语义
    bm25_hits = bm25_index.search(query, k=k)                # 关键词
    return rrf_fusion(vec_hits, bm25_hits, k=k)              # Reciprocal Rank Fusion

def rrf_fusion(*ranked_lists, k=20, k_rrf=60):
    scores = {}
    for lst in ranked_lists:
        for rank, item in enumerate(lst):
            scores[item.id] = scores.get(item.id, 0) + 1 / (k_rrf + rank)
    return sorted(scores.items(), key=lambda x: -x[1])[:k]
```

RRF 不需要分数归一化，**实战稳定**。

## 六、Rerank：第二阶段精排

向量检索 top-50 中，前 5 名经常不是真正最好的。用 **Cross-encoder Reranker** 重排：

```python
from sentence_transformers import CrossEncoder
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

def rerank(query, candidates, top_n=5):
    pairs = [(query, c.text) for c in candidates]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda x: -x[1])
    return [c for c, _ in ranked[:top_n]]
```

经验数字：BGE-reranker / Cohere Rerank 通常能把 top-5 准确率从 ~70% 提到 ~88%。**Rerank 比换更大 embedding 更划算**。

## 七、Just-in-Time 检索（Anthropic 力推的范式）

经典 RAG 是**预先全量检索 → 一次注入**。Anthropic 在 *Context Engineering* 里强调了一个更适合 Agent 的范式：

> "Agents can maintain **lightweight identifiers** (file paths, queries, links) and **dynamically load data at runtime** using tools, rather than pre-processing all relevant data upfront."

也就是说：

```
传统 RAG:
[User Query]
   ↓
[Embed + Search] ─→ top-5 chunks (5K tokens) ─→ Inject ─→ LLM

Just-in-time（Anthropic 推荐）:
[User Query]
   ↓
LLM ─tool call→ search_docs("X 退款流程")  → snippet 1
   ↓
LLM ─tool call→ read_file("policy/refund.md") → snippet 2
   ↓
LLM 决策 → Answer
```

差异：

| 维度 | 传统 RAG | Just-in-Time |
| :--- | :--- | :--- |
| 检索时机 | 一次性，在 LLM 之前 | LLM 自主决定，多次调用 |
| Context 消耗 | 固定 ~5K | 按需，可能更省也可能更多 |
| 适用场景 | 单轮问答 | 多轮 Agent、Coding |
| 控制粒度 | 粗 | 细 |
| 实现复杂度 | 低 | 中（需要 tool loop） |

**结论**：单轮 QA 用传统 RAG；Agent / Coding 场景用 Just-in-Time（Claude Code、Cursor、Codex 都是这种）。

## 八、检索失败的常见原因

按出现频率排序，**这是你 80% 的 RAG bug 出处**：

1. **chunking 太大或太小**：尤其是用户问的是一句话答案，chunk 却是 1500t，召回但答不准。
2. **embedding 模型和你的领域不匹配**：通用 embedding 在医疗 / 法律领域常常拉胯，**fine-tune 或换领域模型**。
3. **query 太短 / 太模糊**："那个" "前面那个" → 加一步 **query rewriting**：用一个小 LLM 把模糊 query 改写为明确 query。
4. **缺 rerank**：top-20 里答案存在，但被排在 12 名。
5. **没做关键词检索**：人名、订单号、错误码这类**精确匹配**用向量打不到。
6. **prompt 让模型"自由发挥"**：注入了资料但模型不用——记得加 "**仅基于提供的资料**" 的约束。

## 九、生产 RAG 的"三层防御"

一个上生产的 RAG 通常长这样：

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
        │    - Multi-index (按 category 分库)                       │
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

每一层都让准确率多挤出一点。RAG 工程的本质是**精度的多级累乘**。

## 十、把这一节装进脑子

- ✅ **小任务**：上传文档 + 一次问答 → 经典 RAG 够了。
- ✅ **多轮 Agent**：让 LLM 主动 `search_docs` / `read_file` → Just-in-time。
- ✅ **跨多个知识源**：multi-index + query routing。
- ✅ **精度要求高**：必加 rerank。
- ✅ **中英混合 / 名词多**：必加 BM25 混合检索。
- ⚠️ **千万别忘** chunk size 调优——它常常是最大的杠杆。

---

下一节：[§2.3 记忆 →](./03-memory.md)
