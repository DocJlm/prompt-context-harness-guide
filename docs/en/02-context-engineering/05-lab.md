---
title: §2.5 Hands-on Lab · Lab 2
description: Build a mini RAG from scratch, demo just-in-time retrieval + context compaction
---

# §2.5 Hands-on Lab: Lab 2

## Lab Goals

Lab 2 has you **implement by hand** the key capabilities of context engineering:

| Demo | What you build | What you learn |
| :---: | :--- | :--- |
| 1 | Index a batch of Chinese documents | Document loading, chunking, embedding |
| 2 | Classic RAG QA | Vector retrieval + injection + generation |
| 3 | Hybrid retrieval + Rerank | The lever of retrieval precision |
| 4 | Just-in-time retrieval Agent | Letting the LLM proactively call a search tool |
| 5 | History compaction | Auto-summarize long conversations |

## Setup

```bash
cd code/lab2-context-rag
pip install -r requirements.txt

export OPENAI_API_KEY=sk-xxxxx
export OPENAI_BASE_URL=https://...     # optional
export MODEL=gpt-4o-mini
export EMBED_MODEL=text-embedding-3-small  # or BAAI/bge-m3, etc.
```

> 💡 Want to run fully local? Do:  
> `pip install sentence-transformers`  
> In the code, switch to `from sentence_transformers import SentenceTransformer` and use `bge-m3`.

`data/docs.md` ships with a fictional knowledge base about "Company X's refund policy / logistics / after-sales rules", about 5K characters.

## Demo 1 · Indexing

```bash
python 01_index.py
```

Core code:

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

After running, `.chroma/` holds the persisted vector index.

## Demo 2 · Classic RAG QA

```bash
python 02_classic_rag.py "How do I apply for a refund?"
```

```python
def rag_answer(query, top_k=5):
    q_emb = client.embeddings.create(model="text-embedding-3-small", input=query).data[0].embedding
    hits = coll.query(query_embeddings=[q_emb], n_results=top_k)
    context = "\n\n---\n\n".join(hits["documents"][0])
    
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Answer based only on the provided materials. If you don't know, say you don't know."},
                  {"role": "user", "content": f"Materials:\n{context}\n\nQuestion: {query}"}],
        temperature=0,
    )
    return resp.choices[0].message.content
```

**Observe**: change the system above to "You are customer support, feel free to improvise" — hallucinations will appear. This is exactly why RAG must include "**based only on the provided materials**".

## Demo 3 · Hybrid + Rerank

```bash
pip install rank_bm25
python 03_hybrid_rerank.py "how long until refund arrives"
```

```python
from rank_bm25 import BM25Okapi
# ...

# BM25
texts = coll.get()["documents"]
bm25 = BM25Okapi([t.split() for t in texts])

# Hybrid via RRF
def hybrid_search(query, k=20):
    # vector
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

Run the same query through pure vector, pure BM25, and Hybrid, and **compare top-3 hit rate**. For Chinese queries containing specific proper nouns (e.g., "7-day no-reason"), Hybrid is usually noticeably better.

## Demo 4 · Just-in-time Retrieval Agent

Let the LLM **decide for itself** when to call search:

```bash
python 04_jit_agent.py
```

```python
TOOLS = [{
    "type": "function",
    "function": {
        "name": "search_docs",
        "description": "Search Company X's internal knowledge base. Use only for refund / logistics / after-sales policy questions.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    }
}]

def search_docs(query):
    q_emb = embed(query)
    hits = coll.query(query_embeddings=[q_emb], n_results=3)
    return "\n---\n".join(hits["documents"][0])

def run(user_msg):
    messages = [
        {"role": "system", "content": "You are Company X's customer support. For policy questions, use the search_docs tool."},
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

Run an interactive session:

```
User: How long does it take for a refund to arrive?
[Agent thinking...] → calls search_docs(query="refund arrival time")
[Agent] → According to the materials, refunds are returned to the original method within 3 business days...

User: What if I used a coupon?
[Agent thinking...] → calls search_docs(query="coupon refund")
[Agent] → ...
```

Note how it **decides for itself** how many times to call and with what query. That's just-in-time.

## Demo 5 · Compaction

```bash
python 05_compaction.py
```

Simulate a long conversation that triggers compaction when tokens exceed a threshold:

```python
def estimate_tokens(messages):
    # Rough estimate: Chinese 1 char ≈ 1.5 tokens, English 4 chars ≈ 1 token
    return sum(len(m.get("content", "") or "") for m in messages) // 2

THRESHOLD = 3000  # small threshold for testing

def compact_if_needed(messages):
    if estimate_tokens(messages) <= THRESHOLD:
        return messages
    
    system, history, recent = messages[0], messages[1:-6], messages[-6:]
    summary_prompt = [
        {"role": "system", "content": "You are a context-compaction assistant. Generate a summary that preserves: goals, decisions, open issues, style constraints. ≤ 300 characters."},
        {"role": "user", "content": "Please compress the following conversation:\n" + json.dumps(history, ensure_ascii=False)},
    ]
    summary = client.chat.completions.create(model=MODEL, messages=summary_prompt, temperature=0).choices[0].message.content
    return [system, {"role": "system", "content": f"[Conversation Summary]\n{summary}"}] + recent

# Before each LLM call
messages = compact_if_needed(messages)
```

Run a 20-turn long conversation and observe:
- At which turn is compaction triggered?
- How does the token count change before/after, and which key facts are preserved?

## Lab Assignments

1. Vary `chunk size` (200 / 500 / 1500) and run Demo 2 — see how the top-5 hit rate changes.
2. In Demo 4's system prompt, add: "**Do not exceed 3 tool calls**" — observe the behavior change (eagerness control).
3. Translate Demo 5's summary prompt into English; compare Chinese-summary vs. English-summary on recall.
4. Combine Demo 4 + Demo 5 to build a mini customer-support agent that can run 30-turn long conversations.

Once you've done that, you **truly own Chapter 2**.

---

Next: [§2.6 References →](./references.md)
