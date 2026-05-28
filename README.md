<div align="center">

# Prompt × Context × Harness Engineering 教程

**从提示词工程到上下文工程，再到 Agent Harness 工程 —— 一份完整的中文实战指南**

*Stage 1 → Stage 2 → Stage 3：陪你走完 LLM 应用开发范式的三次跃迁*

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg?style=for-the-badge)](./LICENSE)
[![Made with ❤ in Chinese](https://img.shields.io/badge/made%20with-%E2%9D%A4%20in%20Chinese-red?style=for-the-badge)](#)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-success?style=for-the-badge)](./docs/zh-cn/04-appendix/contributing.md)

📖 [开始阅读](./docs/zh-cn/index.md) · 🗺️ [学习地图](#-学习地图) · 🧪 [动手实验](#-动手实验) · 📚 [参考文献](./docs/zh-cn/04-appendix/references.md)

</div>

---

## 🎯 这是什么？

这是一份**开源、完整、可动手**的中文教程，带你系统理解 LLM 应用开发的三次范式跃迁：

| 阶段 | 关键词 | 核心问题 | 代表性产出 |
| :---: | :--- | :--- | :--- |
| **Stage 1** | Prompt Engineering（提示词工程） | "怎么把指令说清楚？" | 一段会工作的提示词 |
| **Stage 2** | Context Engineering（上下文工程） | "在每一步把恰好需要的信息放进窗口" | 能跨多轮、长任务稳定工作的智能体 |
| **Stage 3** | Harness Engineering（Agent Harness 工程） | "模型之外的一切：状态、工具、循环、约束" | 能跑数小时、复杂可控的智能体系统 |

> Anthropic 在 2025 年 9 月把范式正式命名为 **Context Engineering**，并在 2026 年初进一步提出 **Harness Engineering**。这份教程把这三层串成一条**可学、可练、可复制**的路径。

---

## 🗺️ 学习地图

```
┌──────────────────────────────────────────────────────────────────┐
│                         开发范式演进路径                          │
└──────────────────────────────────────────────────────────────────┘

  Prompt Engineering        Context Engineering        Harness Engineering
  ─────────────────         ───────────────────         ───────────────────
  一段精心打磨的指令    →   一整套上下文配置策略   →   模型之外的所有工程
       (字)                     (篇章 / 状态)               (循环 / 工具 / 沙箱)

  📍 第 1 章                 📍 第 2 章                 📍 第 3 章
```

| 章节 | 主题 | 阅读时长 | 实验 |
| :---: | :--- | :---: | :---: |
| [序章](./docs/zh-cn/00-prologue/index.md) | 为什么是 Prompt → Context → Harness | 15 min | — |
| [第 1 章](./docs/zh-cn/01-prompt-engineering/index.md) | Prompt Engineering：把指令说清楚 | 90 min | [Lab 1](./code/lab1-prompting/) |
| [第 2 章](./docs/zh-cn/02-context-engineering/index.md) | Context Engineering：管理注意力预算 | 120 min | [Lab 2](./code/lab2-context-rag/) |
| [第 3 章](./docs/zh-cn/03-harness-engineering/index.md) | Harness Engineering：构建可长跑的智能体 | 150 min | [Lab 3](./code/lab3-mini-harness/) |
| [附录](./docs/zh-cn/04-appendix/index.md) | 术语表 · 路线图 · 参考文献 · 贡献指南 | — | — |

---

## 🧪 动手实验

每一章都配有一个**可运行的 Python 实验**，依赖最小、注释充分：

- **[Lab 1 · prompt_patterns](./code/lab1-prompting/)** — Zero/Few-shot、Chain-of-Thought、Structured Output、Self-Consistency
- **[Lab 2 · mini_rag](./code/lab2-context-rag/)** — 从零搭建一个 RAG，演示 Just-in-time 检索 + 上下文压缩
- **[Lab 3 · mini_harness](./code/lab3-mini-harness/)** — 实现一个最小可工作的 ReAct Harness（工具循环 + 子 Agent + 持久化进度）

> 实验代码兼容 **任何 OpenAI-Compatible API**（OpenAI / DeepSeek / 通义千问 / 月之暗面 / 智谱 …）。默认走 `OPENAI_API_KEY` + `OPENAI_BASE_URL` 环境变量。

---

## 🔬 开源项目深度解读

第 3 章会带你**逐行**读两个工业级 Harness 项目：

- **[MagicCube / helixent](https://github.com/MagicCube/helixent)** — TypeScript + Bun，简洁优雅的 ReAct 循环 + 中间件 + Skills，是理解"Harness 最小骨架"的最佳样本。
- **[bytedance / deer-flow](https://github.com/bytedance/deer-flow)** — 字节开源的 SuperAgent Harness：LangGraph + 子 Agent + 沙箱 + 长期记忆 + 可插拔技能。

读完之后，你不仅能用 Claude Code / Codex，还能**自己造一个**。

---

## 📚 我们站在谁的肩膀上

本教程内容大量参考并交叉验证以下来源：

- **Anthropic Engineering**：[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) · [Harness design for long-running app development](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- **OpenAI**：[GPT-5 Prompting Guide](https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide) · [Prompt engineering guide](https://platform.openai.com/docs/guides/prompt-engineering)
- **阿里云百炼**：[Prompt Engineering 提示工程指南](https://help.aliyun.com/zh/model-studio/prompt-engineering-guide)
- **字节跳动 / 腾讯 / 阿里**：相关技术博客与开源实践（见 [references.md](./docs/zh-cn/04-appendix/references.md)）
- **开源项目**：helixent、deer-flow、Claude Agent SDK、LangGraph 等

完整文献清单见 [参考文献](./docs/zh-cn/04-appendix/references.md)。

---

## 🤝 如何使用本教程

```bash
# 1. 克隆仓库
git clone https://github.com/<your>/prompt-context-harness-guide.git
cd prompt-context-harness-guide

# 2. 进入对应章节阅读
open docs/zh-cn/01-prompt-engineering/index.md

# 3. 跑实验
cd code/lab1-prompting
pip install -r requirements.txt
export OPENAI_API_KEY=...      # 或任意 OpenAI-Compatible Key
export OPENAI_BASE_URL=...     # 可选，默认走官方
python 01_zero_shot.py
```

**建议学习节奏**：

- 🚶 **新手**（0 经验）：按章顺序读，每章配套跑一次 Lab。预计 1 周。
- 🚴 **有 LLM 应用经验**：可以直接跳到第 2、3 章；Lab 必跑。预计 2–3 天。
- 🏎️ **想造工具的工程师**：精读第 3 章 + helixent / deer-flow 源码导读 + Lab 3。预计 1 天。

---

## 🛣️ 路线图

- ✅ Stage 1：Prompt Engineering 基础与进阶（已完成）
- ✅ Stage 2：Context Engineering 系统化方法（已完成）
- ✅ Stage 3：Harness Engineering 与案例研究（已完成）
- 🔜 Stage 4：评估（Eval）与可观测性（规划中）
- 🔜 Stage 5：多 Agent 协作架构进阶（规划中）

详情见 [路线图](./docs/zh-cn/04-appendix/roadmap.md)。

---

## 🙏 贡献 & 鸣谢

欢迎一切形式的贡献：内容补全、错别字、新案例、新语言翻译。请先阅读 [贡献指南](./docs/zh-cn/04-appendix/contributing.md)。

灵感来自 [datawhalechina/easy-vibe](https://github.com/datawhalechina/easy-vibe) 的优秀工作。

---

## 📄 协议

本教程采用 [CC BY-NC-SA 4.0](./LICENSE) 协议。代码部分采用 MIT 协议。
