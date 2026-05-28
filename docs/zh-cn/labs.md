---
title: 动手实验总览
description: 三个 Python 实验的入口
---

# 🧪 动手实验总览

教程的三章各配套一个**可独立运行的 Python 实验**。每个实验 5 个 demo，依赖最小、注释充分。

> 全部代码在仓库 [`code/`](https://github.com/DocJlm/prompt-context-harness-guide/tree/main/code) 目录下。

## 通用准备

```bash
git clone https://github.com/DocJlm/prompt-context-harness-guide
cd prompt-context-harness-guide

# 每个 lab 独立 requirements，进各自目录安装
cd code/lab1-prompting
pip install -r requirements.txt

# 环境变量（兼容 OpenAI / DeepSeek / 通义 / 智谱 / Kimi）
export OPENAI_API_KEY=sk-xxxxx
export OPENAI_BASE_URL=https://api.openai.com/v1   # 可选
export MODEL=gpt-4o-mini                            # 可选
```

::: tip 国内模型示例
```bash
# DeepSeek
export OPENAI_BASE_URL=https://api.deepseek.com/v1
export OPENAI_API_KEY=<deepseek-key>
export MODEL=deepseek-chat

# 通义 (DashScope)
export OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export OPENAI_API_KEY=<dashscope-key>
export MODEL=qwen-plus
```
:::

---

## Lab 1 · Prompt Patterns

对应 [第 1 章](./01-prompt-engineering/)。

| # | 文件 | 主题 |
| :---: | :--- | :--- |
| 1 | `01_zero_shot.py` | Zero-shot baseline + 温度参数效应 |
| 2 | `02_few_shot.py` | Few-shot 多样性示例（含反讽边界） |
| 3 | `03_cot.py` | Chain-of-Thought 准确率提升对比 |
| 4 | `04_structured_output.py` | JSON Schema 强制输出 |
| 5 | `05_eval_loop.py` | Golden set + accuracy 评估 |

```bash
cd code/lab1-prompting
python 01_zero_shot.py
python 02_few_shot.py
python 03_cot.py
python 04_structured_output.py
python 05_eval_loop.py
```

详细说明：[§1.5 动手实验](./01-prompt-engineering/05-lab)

---

## Lab 2 · Mini RAG + Context Engineering

对应 [第 2 章](./02-context-engineering/)。

| # | 文件 | 主题 |
| :---: | :--- | :--- |
| 1 | `01_index.py` | 切块 + 向量化 + 落 Chroma |
| 2 | `02_classic_rag.py` | 经典 RAG QA |
| 3 | `03_hybrid_rerank.py` | Hybrid 检索（BM25 + Vector）+ RRF |
| 4 | `04_jit_agent.py` | Just-in-time 检索 Agent |
| 5 | `05_compaction.py` | 长对话自动压缩 |

```bash
cd code/lab2-context-rag
pip install -r requirements.txt
python 01_index.py
python 02_classic_rag.py "怎么申请退款？"
python 03_hybrid_rerank.py "退款多久到账"
python 04_jit_agent.py
python 05_compaction.py
```

详细说明：[§2.5 动手实验](./02-context-engineering/05-lab)

---

## Lab 3 · Mini Harness

对应 [第 3 章](./03-harness-engineering/)。

| # | 文件 | 主题 |
| :---: | :--- | :--- |
| 1 | `01_tool_loop.py` | 100 行实现 ReAct Tool Loop |
| 2 | `02_hooks.py` | Hook：日志 + 危险命令拦截 |
| 3 | `03_subagent.py` | Sub-agent：外包搜索任务 |
| 4 | `04_progress.py` | Progress 持久化 + Session 恢复 |
| 5 | `05_real_task.py` | 真实任务：为 fake_project 写 README |

```bash
cd code/lab3-mini-harness
pip install -r requirements.txt
python 01_tool_loop.py
python 02_hooks.py
python 03_subagent.py
python 04_progress.py
python 04_progress.py --resume    # 恢复上一个 session
python 05_real_task.py
```

详细说明：[§3.5 动手实验](./03-harness-engineering/05-build-your-own)

---

## 实验设计原则

- **依赖最小**：能用 stdlib 不用第三方；每个 lab 的 `requirements.txt` 都≤ 3 个包。
- **OpenAI-Compatible**：所有 API 调用通过 `OPENAI_API_KEY` + `OPENAI_BASE_URL` 环境变量切换，国内国外模型都能跑。
- **跑完不超 1 分钟**：每个 demo 设计为 30 秒内产出有意义结果，方便迭代实验。
- **教学 > 性能**：代码可读性优先，生产化优化都在文档里讲，不放在 lab 里。
