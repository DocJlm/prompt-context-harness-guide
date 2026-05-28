---
title: 术语表
description: Prompt × Context × Harness Engineering 关键术语速查
---

# 术语表

## A

- **Agent**：能根据目标自主决定行为序列（思考 / 调工具 / 观察）的 LLM 应用。
- **Agentic Eagerness**（主动性）：Agent 在多步任务中"多积极去探索 / 调工具"的程度。GPT-5 时代的可控变量。
- **Agent Harness**：模型之外的所有代码——session 管理、tool 实现、权限、沙箱、错误恢复、HITL。本教程第 3 章主题。
- **Agentic Memory**：Agent 自己主动写笔记到外部存储的能力。详见 §2.3。
- **AGENTS.md / CLAUDE.md**：项目根目录约定的"工程师手册"，会被 Agent 自动注入到 system prompt。
- **Attention Budget**（注意力预算）：模型在一个 context window 内能"集中注意力"的有限资源。窗口越大、单 token 的份额越被稀释。

## B

- **BM25**：经典关键词检索算法。在 RAG 里常和向量检索做 Hybrid。

## C

- **Chain-of-Thought (CoT)**：让模型"分步推理"的 prompt 模式。推理模型自带，传统模型需显式触发。
- **Chunking**：把长文档切成小块供 embedding/索引的过程。chunk size 是 RAG 第一调优杠杆。
- **Compaction**（压缩）：把老的多轮对话压成一段摘要，给 context 腾位置。Context Engineering 的核心策略。
- **Context Engineering**：本教程第 2 章主题。"在每一步把恰好需要的信息放进窗口"。
- **Context Reset**：Harness 主动 kill 当前 Session 开新 Session 的策略，应对 context anxiety。
- **Context Rot**（上下文腐烂）：随着窗口被填满，模型回忆中段信息的能力下降的现象。Anthropic 给出的关键概念。
- **Context Window**：模型一次能处理的最大 token 数（32K / 128K / 200K / 1M...）。
- **Confidence Drift**：Agent 对自己生成内容盲目自信、不愿重新审视的失败模式。

## E

- **Embedding**：把文本变成定长向量的过程，用于向量检索。
- **Evaluator Agent**：在 Planner-Generator-Evaluator 架构里专门评估代码 / 输出的 Agent。和 Generator 隔离 context。

## F

- **Few-shot Prompting**：在 prompt 里给 2–5 个示例。质 > 量；覆盖正常 + 边界 + 反例。

## G

- **Generator Agent**：在 P-G-E 架构里负责写代码 / 产出内容的 Agent。
- **Golden Set**：人工精挑的 eval 数据集。Prompt Engineering 迭代的"单元测试"。

## H

- **Hallucination**（幻觉）：模型编造事实的现象。RAG / strict prompt / 外部验证是常见对策。
- **Harness Engineering**：本教程第 3 章主题。模型之外的全部工程。
- **Hook / Middleware**：Agent loop 的关键事件点插入用户代码的机制。helixent 有 8 个 hook 点。
- **HITL (Human-in-the-Loop)**：人在回路。重要工具调用前请求人工审批。
- **Hybrid Search**：向量检索 + BM25 关键词检索的组合，常用 RRF 融合。

## J

- **Just-in-time Retrieval**：让 LLM 自主决定何时调 search 工具的范式（区别于经典 RAG 的"一次性预检索"）。Anthropic 的推荐模式。

## L

- **LangGraph**：LangChain 推出的多 Agent 状态机框架，deer-flow 的底层。
- **LLM-as-Judge**：用模型评估模型输出的方法。注意 judge 偏差。
- **Lost in the Middle**：2023 论文，证明模型对 context 中段信息的注意力低于头尾。

## M

- **MCP (Model Context Protocol)**：Anthropic 发起的开放协议，让工具可被多个 Agent Harness 复用。
- **Memory (Long-term)**：Harness 层跨 Session 持久存储的记忆（profile / episodes / knowledge）。
- **Meta-prompting**：用模型改进自己的 prompt 的方法。GPT-5 是 meta-prompting 高手。
- **Middleware**：见 Hook。

## P

- **Persistence**（坚持性）：让 Agent 不轻易停下来的 prompt 设计模式。"Don't end your turn until the user's query is completely resolved."
- **Planner Agent**：在 P-G-E 架构里负责拆解 task 的 Agent。
- **Planner-Generator-Evaluator (P-G-E)**：Anthropic 推荐的三 Agent 长跑架构。
- **Prompt Engineering**：本教程第 1 章主题。单次推理的指令优化。
- **progress.txt / progress.md**：跨 Session 的状态文件，新 Session 启动第一件事就是读它。

## R

- **RAG (Retrieval-Augmented Generation)**：检索增强生成。把外部知识检索后注入 prompt 再生成。
- **ReAct**：Reason + Act 交替的 prompt 模式。所有 Agent 系统的基础范式。
- **Reranking**：用 cross-encoder 模型对向量检索的 top-k 重新排序。比换更大 embedding 通常更划算。
- **Reasoning Effort**：模型推理深度的旋钮。GPT-5 用 `minimal / low / medium / high`；Claude 用 `thinking` block。
- **RRF (Reciprocal Rank Fusion)**：把多种检索方式的排名融合的简单算法。`score = sum(1 / (k + rank))`。

## S

- **Sandbox**（沙箱）：Agent 工具执行的隔离环境。形态从同主机目录到 Docker 到云沙箱（E2B / Modal）。
- **Self-Consistency**：跑 N 次 CoT 投票的方法，提高推理任务可靠性。
- **Skill**：可独立 enable / disable 的能力模块。一个目录 + SKILL.md + tools + prompts。helixent / deer-flow / Claude Code 都支持。
- **Structured Output**：让模型输出严格符合 JSON Schema 的结果。三档实现：prompt 软约束 / function calling / strict mode。
- **Sub-agent**：主 Agent spawn 出来的子 Agent。独立 context、专注子任务、返回 ~1500 token 摘要。
- **System Prompt**：模型的"全局指令"。要写在"恰当高度"——不要 hardcode、也不要太模糊。

## T

- **Temperature**：解码随机性参数。0 = 确定，1 = 默认，> 1 更发散。
- **Tool Loop**：Agent 的核心循环：模型决定 tool call → harness 执行 → 结果回填 → 模型继续。
- **Tool Preamble**：调工具前 Agent 用一句话告诉用户"接下来要做什么"。GPT-5 时代的标配。
- **Tree-of-Thought (ToT)**：CoT 的树形扩展。学术上漂亮，工业上少用。

## Z

- **Zero-shot Prompting**：不给例子直接问。简单常见任务首选。

---

回到 [附录首页 ←](./index.md)
