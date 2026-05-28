# Lab 2 · Mini RAG + Context Engineering

第 2 章配套实验。5 个 demo 带你从零搭出一个 mini RAG，并演示 Just-in-time 检索与上下文压缩。

## 准备

```bash
pip install -r requirements.txt

export OPENAI_API_KEY=sk-xxxxx
export OPENAI_BASE_URL=https://api.openai.com/v1   # 可选
export MODEL=gpt-4o-mini                            # 主对话模型
export EMBED_MODEL=text-embedding-3-small           # embedding 模型
```

> 想全本地跑？把 `EMBED_MODEL=local` 并 `pip install sentence-transformers`，代码会自动改用 `BAAI/bge-m3`。

## Demo 列表

| # | 文件 | 主题 |
| :---: | :--- | :--- |
| 1 | `01_index.py` | 切块 + 向量化 + 落 Chroma |
| 2 | `02_classic_rag.py` | 经典 RAG QA |
| 3 | `03_hybrid_rerank.py` | Hybrid 检索（BM25 + Vector）+ RRF |
| 4 | `04_jit_agent.py` | Just-in-time 检索 Agent |
| 5 | `05_compaction.py` | 长对话自动压缩 |

## 跑

```bash
python 01_index.py            # 先建索引
python 02_classic_rag.py "怎么申请退款？"
python 03_hybrid_rerank.py "退款多久到账"
python 04_jit_agent.py
python 05_compaction.py
```
