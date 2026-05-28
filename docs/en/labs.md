---
title: Hands-on Labs Overview
description: Entry point for the three Python labs
---

# 🧪 Hands-on Labs

Each chapter ships with a **self-contained Python lab**. Five demos per lab, minimal deps, well-commented.

> All code lives under [`code/`](https://github.com/your-name/prompt-context-harness-guide/tree/main/code).

## Setup

```bash
git clone https://github.com/your-name/prompt-context-harness-guide
cd prompt-context-harness-guide

# Each lab has its own requirements
cd code/lab1-prompting
pip install -r requirements.txt

# API keys — works with any OpenAI-compatible provider
export OPENAI_API_KEY=sk-xxxxx
export OPENAI_BASE_URL=https://api.openai.com/v1   # optional
export MODEL=gpt-4o-mini                            # optional
```

::: tip Using a Chinese model
```bash
# DeepSeek
export OPENAI_BASE_URL=https://api.deepseek.com/v1
export OPENAI_API_KEY=<deepseek-key>
export MODEL=deepseek-chat
```
:::

---

## Lab 1 · Prompt Patterns

For [Chapter 1](./01-prompt-engineering/).

| # | File | Topic |
| :---: | :--- | :--- |
| 1 | `01_zero_shot.py` | Zero-shot baseline + temperature effects |
| 2 | `02_few_shot.py` | Diverse few-shot examples (incl. sarcasm edge) |
| 3 | `03_cot.py` | Chain-of-Thought accuracy lift |
| 4 | `04_structured_output.py` | JSON Schema strict mode |
| 5 | `05_eval_loop.py` | Golden set + accuracy evaluation |

```bash
cd code/lab1-prompting
python 01_zero_shot.py
python 02_few_shot.py
python 03_cot.py
python 04_structured_output.py
python 05_eval_loop.py
```

Walkthrough: [§1.5 Lab 1](./01-prompt-engineering/05-lab)

---

## Lab 2 · Mini RAG + Context Engineering

For [Chapter 2](./02-context-engineering/).

| # | File | Topic |
| :---: | :--- | :--- |
| 1 | `01_index.py` | Chunk + embed + persist to Chroma |
| 2 | `02_classic_rag.py` | Classic RAG QA |
| 3 | `03_hybrid_rerank.py` | Hybrid (BM25 + Vector) with RRF |
| 4 | `04_jit_agent.py` | Just-in-time retrieval agent |
| 5 | `05_compaction.py` | Long-conversation auto-compaction |

```bash
cd code/lab2-context-rag
pip install -r requirements.txt
python 01_index.py
python 02_classic_rag.py "How do I request a refund?"
python 03_hybrid_rerank.py "How long does a refund take"
python 04_jit_agent.py
python 05_compaction.py
```

Walkthrough: [§2.5 Lab 2](./02-context-engineering/05-lab)

---

## Lab 3 · Mini Harness

For [Chapter 3](./03-harness-engineering/).

| # | File | Topic |
| :---: | :--- | :--- |
| 1 | `01_tool_loop.py` | ReAct tool loop in ~100 lines |
| 2 | `02_hooks.py` | Hooks: audit log + danger guard |
| 3 | `03_subagent.py` | Sub-agent: offload heavy search |
| 4 | `04_progress.py` | Progress persistence + session resume |
| 5 | `05_real_task.py` | Real task: write a README for a fake project |

```bash
cd code/lab3-mini-harness
pip install -r requirements.txt
python 01_tool_loop.py
python 02_hooks.py
python 03_subagent.py
python 04_progress.py
python 04_progress.py --resume    # resume previous session
python 05_real_task.py
```

Walkthrough: [§3.5 Build Your Own](./03-harness-engineering/05-build-your-own)

---

## Design principles

- **Minimal deps**: stdlib first; each lab's `requirements.txt` has ≤3 packages.
- **OpenAI-compatible**: all calls go through `OPENAI_API_KEY` + `OPENAI_BASE_URL`; works for any compliant provider.
- **<1 minute to run**: each demo produces meaningful output in ~30 seconds.
- **Teaching > performance**: readability first; production-grade tricks live in the docs, not the lab code.
