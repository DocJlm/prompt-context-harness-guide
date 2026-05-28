---
title: Glossary
description: Quick reference for the key terms in Prompt × Context × Harness Engineering
---

# Glossary

## A

- **Agent**: An LLM application that autonomously decides its sequence of actions (think / call tool / observe) based on a goal.
- **Agentic Eagerness**: How aggressively an Agent explores or calls tools during multi-step tasks. A controllable knob in the GPT-5 era.
- **Agent Harness**: All the code outside the model — session management, tool implementations, permissions, sandboxing, error recovery, HITL. The topic of Chapter 3.
- **Agentic Memory**: The Agent's ability to proactively write notes to external storage on its own. See §2.3.
- **AGENTS.md / CLAUDE.md**: An "engineer's handbook" placed at the project root by convention. Automatically injected into the system prompt by the Agent.
- **Attention Budget**: The finite "concentration" resource a model can spend within one context window. The larger the window, the more diluted each token's share of attention becomes.

## B

- **BM25**: A classic keyword retrieval algorithm. In RAG it's often combined with vector search as a Hybrid setup.

## C

- **Chain-of-Thought (CoT)**: A prompt pattern that gets the model to "reason step by step". Built into reasoning models; needs explicit triggering on legacy models.
- **Chunking**: Splitting long documents into smaller pieces for embedding/indexing. Chunk size is the first tuning lever in RAG.
- **Compaction**: Compressing older multi-turn dialogue into a summary to make room in the context. A core Context Engineering strategy.
- **Context Engineering**: The topic of Chapter 2. "Put exactly the information needed into the window at every step."
- **Context Reset**: A harness strategy that proactively kills the current Session and starts a new one, to deal with context anxiety.
- **Context Rot**: The phenomenon where the model's ability to recall middle-section information degrades as the window fills up. A key concept introduced by Anthropic.
- **Context Window**: The maximum number of tokens the model can process in one shot (32K / 128K / 200K / 1M...).
- **Confidence Drift**: A failure mode where an Agent becomes blindly confident in its own output and won't re-examine it.

## E

- **Embedding**: Turning text into fixed-length vectors for vector retrieval.
- **Evaluator Agent**: In the Planner-Generator-Evaluator architecture, the Agent that evaluates code/output. Context is isolated from the Generator.

## F

- **Few-shot Prompting**: Including 2–5 examples in the prompt. Quality > quantity; cover normal cases, edge cases, and counter-examples.

## G

- **Generator Agent**: In the P-G-E architecture, the Agent responsible for writing code or producing output.
- **Golden Set**: A hand-curated eval dataset. The "unit tests" of iterative Prompt Engineering.

## H

- **Hallucination**: The phenomenon of the model fabricating facts. RAG, strict prompting, and external verification are common countermeasures.
- **Harness Engineering**: The topic of Chapter 3. All the engineering outside the model.
- **Hook / Middleware**: A mechanism for plugging user code into key event points of the Agent loop. helixent exposes 8 hook points.
- **HITL (Human-in-the-Loop)**: Requesting human approval before important tool calls.
- **Hybrid Search**: A combination of vector retrieval and BM25 keyword retrieval, commonly fused with RRF.

## J

- **Just-in-time Retrieval**: A paradigm where the LLM autonomously decides when to call the search tool (in contrast to classic RAG's "one-shot pre-retrieval"). Anthropic's recommended pattern.

## L

- **LangGraph**: A multi-Agent state-machine framework from LangChain. The foundation of deer-flow.
- **LLM-as-Judge**: Using a model to evaluate model output. Watch out for judge bias.
- **Lost in the Middle**: A 2023 paper showing that models pay less attention to information in the middle of the context than to the ends.

## M

- **MCP (Model Context Protocol)**: An open protocol initiated by Anthropic that lets tools be reused across multiple Agent Harnesses.
- **Memory (Long-term)**: Harness-layer cross-session persistent memory (profile / episodes / knowledge).
- **Meta-prompting**: A method that uses the model to improve its own prompt. GPT-5 is a meta-prompting expert.
- **Middleware**: See Hook.

## P

- **Persistence**: A prompt design pattern that keeps the Agent from stopping easily. "Don't end your turn until the user's query is completely resolved."
- **Planner Agent**: In the P-G-E architecture, the Agent responsible for decomposing the task.
- **Planner-Generator-Evaluator (P-G-E)**: Anthropic's recommended three-Agent architecture for long-running tasks.
- **Prompt Engineering**: The topic of Chapter 1. Instruction optimization for a single inference call.
- **progress.txt / progress.md**: A cross-session state file. The first thing a new Session does on startup is read it.

## R

- **RAG (Retrieval-Augmented Generation)**: Inject external knowledge retrieved on demand into the prompt before generation.
- **ReAct**: A prompt pattern that alternates Reason and Act. The foundational paradigm for all Agent systems.
- **Reranking**: Re-ranking the top-k from vector retrieval using a cross-encoder model. Usually more cost-effective than upgrading to a larger embedding model.
- **Reasoning Effort**: A knob for the depth of the model's reasoning. GPT-5 uses `minimal / low / medium / high`; Claude uses the `thinking` block.
- **RRF (Reciprocal Rank Fusion)**: A simple algorithm for fusing rankings from multiple retrieval methods. `score = sum(1 / (k + rank))`.

## S

- **Sandbox**: The isolated environment in which Agent tools run. Forms range from same-host directories to Docker to cloud sandboxes (E2B / Modal).
- **Self-Consistency**: A method of voting across N CoT runs to improve reliability on reasoning tasks.
- **Skill**: A capability module that can be independently enabled/disabled. A directory + SKILL.md + tools + prompts. Supported by helixent, deer-flow, and Claude Code.
- **Structured Output**: Making the model output results that strictly conform to a JSON Schema. Three implementation tiers: soft prompt constraints / function calling / strict mode.
- **Sub-agent**: A child Agent spawned by the main Agent. Independent context, focused on a sub-task, returns a ~1500-token summary.
- **System Prompt**: The model's "global instructions". Write them at the right altitude — neither hardcoded nor too vague.

## T

- **Temperature**: The decoding-randomness parameter. 0 = deterministic, 1 = default, > 1 more divergent.
- **Tool Loop**: The Agent's core loop: model decides on a tool call → harness executes → result is returned → model continues.
- **Tool Preamble**: A one-sentence note the Agent gives the user before calling a tool, saying "here's what I'm about to do". Standard practice in the GPT-5 era.
- **Tree-of-Thought (ToT)**: A tree-shaped extension of CoT. Elegant academically, rarely used in industry.

## Z

- **Zero-shot Prompting**: Asking directly with no examples. The first choice for simple, common tasks.

---

Back to [appendix home ←](./index.md)
