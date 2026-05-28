---
title: §2.5 动手实验 · Lab 2
description: 从零搭一个 mini RAG，演示 Just-in-time 检索 + 上下文压缩
---

# §2.5 动手实验：Lab 2

## 实验目标

Lab 2 让你**亲手实现** Context Engineering 的关键能力：

| Demo | 你会做什么 | 学到什么 |
| :---: | :--- | :--- |
| 1 | 索引一批中文文档 | 文档加载、chunking、embedding |
| 2 | 经典 RAG QA | 向量检索 + 注入 + 生成 |
| 3 | Hybrid 检索 + Rerank | 检索精度的杠杆 |
| 4 | Just-in-time 检索 Agent | 让 LLM 主动调 search 工具 |
| 5 | History Compaction | 长对话自动摘要 |

## 准备

```bash
cd code/lab2-context-rag
pip install -r requirements.txt

export OPENAI_API_KEY=sk-xxxxx
export OPENAI_BASE_URL=https://...     # 可选
export MODEL=gpt-4o-mini
export EMBED_MODEL=text-embedding-3-small  # 或 BAAI/bge-m3 等
```

> 💡 想全本地跑？设：  
> `pip install sentence-transformers`  
> 代码里改用 `from sentence_transformers import SentenceTransformer` 跑 `bge-m3`。

`data/docs.md` 自带一份关于 "X 公司退款政策 / 物流流程 / 售后规范" 的虚构知识库，约 5K 字。

## Demo 1 · 索引

```bash
python 01_index.py
```

代码核心：

```python
from openai import OpenAI
import json, chromadb

client = OpenAI()
chroma = chromadb.PersistentClient(path=".chroma")
coll = chroma.get_or_create_collection("docs")

def chunk(text, size=500, overlap=50):
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i:i+size])
        i += size - overlap
    return chunks

text = open("data/docs.md").read()
for j, c in enumerate(chunk(text)):
    emb = client.embeddings.create(model="text-embedding-3-small", input=c).data[0].embedding
    coll.add(ids=[f"doc-{j}"], documents=[c], embeddings=[emb])

print(f"Indexed {coll.count()} chunks.")
```

跑完后 `.chroma/` 里会有持久化的向量索引。

## Demo 2 · 经典 RAG QA

```bash
python 02_classic_rag.py "怎么申请退款？"
```

```python
def rag_answer(query, top_k=5):
    q_emb = client.embeddings.create(model="text-embedding-3-small", input=query).data[0].embedding
    hits = coll.query(query_embeddings=[q_emb], n_results=top_k)
    context = "\n\n---\n\n".join(hits["documents"][0])
    
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "仅基于提供的资料回答问题。不知道就说不知道。"},
                  {"role": "user", "content": f"资料:\n{context}\n\n问题: {query}"}],
        temperature=0,
    )
    return resp.choices[0].message.content
```

**观察**：把上面的 system 改成 "你是客服，可以自由发挥"——会出现幻觉。这就是为什么 RAG 一定要写 "**仅基于提供的资料**"。

## Demo 3 · Hybrid + Rerank

```bash
pip install rank_bm25
python 03_hybrid_rerank.py "退款多久到账"
```

```python
from rank_bm25 import BM25Okapi
# ...

# BM25
texts = coll.get()["documents"]
bm25 = BM25Okapi([t.split() for t in texts])

# Hybrid via RRF
def hybrid_search(query, k=20):
    # 向量
    q_emb = embed(query)
    vec = coll.query(query_embeddings=[q_emb], n_results=k)
    # BM25
    scores = bm25.get_scores(query.split())
    bm25_top = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
    # RRF
    rrf = {}
    for r, doc_id in enumerate(vec["ids"][0]): rrf[doc_id] = rrf.get(doc_id, 0) + 1 / (60 + r)
    for r, idx in enumerate(bm25_top):         rrf[f"doc-{idx}"] = rrf.get(f"doc-{idx}", 0) + 1 / (60 + r)
    return sorted(rrf.items(), key=lambda x: -x[1])[:k]
```

把同一个 query 用纯向量、纯 BM25、Hybrid 各跑一次，**比较 top-3 命中率**。对中文里包含具体名词的 query（如"7 天无理由"），Hybrid 通常显著好。

## Demo 4 · Just-in-time 检索 Agent

让 LLM **自己**决定什么时候调 search：

```bash
python 04_jit_agent.py
```

```python
TOOLS = [{
    "type": "function",
    "function": {
        "name": "search_docs",
        "description": "搜索 X 公司内部知识库。仅用于退款/物流/售后政策类问题。",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    }
}]

def search_docs(query):
    q_emb = embed(query)
    hits = coll.query(query_embeddings=[q_emb], n_results=3)
    return "\n---\n".join(hits["documents"][0])

def run(user_msg):
    messages = [
        {"role": "system", "content": "你是 X 公司客服。涉及政策类问题请用 search_docs 工具查询。"},
        {"role": "user", "content": user_msg},
    ]
    for _ in range(5):
        resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        msg = resp.choices[0].message
        messages.append(msg)
        if not msg.tool_calls:
            return msg.content
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = search_docs(args["query"])
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
```

跑一个交互 session：

```
用户: 你们退款多久到账？
[Agent thinking...] → 调用 search_docs(query="退款到账时间")
[Agent] → 根据资料，退款一般 3 个工作日内原路返回...

用户: 那要是我用了优惠券呢？
[Agent thinking...] → 调用 search_docs(query="优惠券退款")
[Agent] → ...
```

注意它**自己决定**调几次、调什么 query。这就是 Just-in-time。

## Demo 5 · Compaction

```bash
python 05_compaction.py
```

模拟一个长对话，token 超过阈值就压缩：

```python
def estimate_tokens(messages):
    # 粗估：中文 1 字 ≈ 1.5 token，英文 4 字符 ≈ 1 token
    return sum(len(m.get("content", "") or "") for m in messages) // 2

THRESHOLD = 3000  # 测试用小阈值

def compact_if_needed(messages):
    if estimate_tokens(messages) <= THRESHOLD:
        return messages
    
    system, history, recent = messages[0], messages[1:-6], messages[-6:]
    summary_prompt = [
        {"role": "system", "content": "你是上下文压缩助手。生成 summary，重点保留：目标、决定、未决问题、风格约束。不超过 300 字。"},
        {"role": "user", "content": "请压缩以下对话：\n" + json.dumps(history, ensure_ascii=False)},
    ]
    summary = client.chat.completions.create(model=MODEL, messages=summary_prompt, temperature=0).choices[0].message.content
    return [system, {"role": "system", "content": f"[Conversation Summary]\n{summary}"}] + recent

# 在每轮 LLM 调用前
messages = compact_if_needed(messages)
```

跑 20 轮长对话，观察：
- 第几轮触发压缩？
- 压缩前后的 token 数 / 关键事实保留情况。

## 实验作业

1. 改变 `chunk size`（200 / 500 / 1500）跑 Demo 2，看 top-5 命中率怎么变。
2. 在 Demo 4 的 system prompt 里加："**不要超过 3 次 tool call**"——观察行为变化（Eagerness 控制）。
3. 把 Demo 5 的 summary prompt 改成英文，对比中文 summary 和英文 summary 在 recall 上的差异。
4. 用 Demo 4 + Demo 5 组合，搭一个能跑 30 轮长对话的 mini 客服 agent。

完成之后，你**真正掌握了第 2 章**。

---

下一节：[§2.6 参考文献 →](./references.md)
