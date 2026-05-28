---
title: §3.4 案例 · deer-flow
description: 字节跳动开源的 SuperAgent Harness
---

# §3.4 案例 · deer-flow

> "DeerFlow is an open-source long-horizon **SuperAgent harness** that researches, codes, and creates. With the help of **sandboxes, memories, tools, skills, sub-agents and message gateway**, it handles different levels of tasks that could take minutes to hours."  
> — [github.com/bytedance/deer-flow](https://github.com/bytedance/deer-flow)

deer-flow（**Deep Exploration and Efficient Research Flow**）由字节跳动开源，**2026 年 2 月 v2.0 发布后短暂登顶 GitHub Trending #1**。它代表了"全功能 Harness"的当代形态。

## 一、项目自画像

| 维度 | deer-flow |
| :--- | :--- |
| **主语言** | Python 73% + TypeScript 15% |
| **核心框架** | LangGraph + LangChain |
| **形态** | Backend + Frontend + Skills 完整套件 |
| **特性** | Sub-agent、Sandbox、Long-term Memory、IM 集成、MCP 支持、可观测性 |
| **目录** | backend / frontend / skills / docker |

> 注意：deer-flow v2.0 是一次**完全重写**——和 v1.0（早期 deep research framework）几乎不共享代码。本节讨论的都是 v2.0。

## 二、和 helixent 的对比

```
                    helixent              deer-flow
                    ────────              ─────────
代码规模             几千行                几万行
范围               单机库 + CLI          后端 + 前端 + 部署
语言               TypeScript            Python + TypeScript
sub-agent           ❌（roadmap）           ✅
持久记忆            ❌                     ✅
沙箱                ❌                     ✅（Docker / local）
多模态              ❌                     ✅（图片、视频、PPT）
观测性             基础日志              ✅（LangSmith / Langfuse）
IM 集成             ❌                     ✅（飞书 / Slack / Telegram）
学习曲线            一晚                  一周+
适合做的事          学原理、做工具         做产品
```

如果说 helixent 是"乐高 Technic 基础件"，deer-flow 就是"出厂即能跑的成品车"。**两者解决不同问题，都值得读**。

## 三、架构图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              User                                         │
│  ┌────────────┬──────────────┬──────────────┬──────────────┬──────────┐  │
│  │  Web UI    │   飞书        │  Telegram    │   Slack       │  CLI    │  │
│  └────────────┴──────────────┴──────────────┴──────────────┴──────────┘  │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────────┐
│                        Message Gateway (port 2026)                       │
│                  统一接入层 · 路由 · 鉴权 · 速率                          │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────────┐
│                           Agent Runtime (LangGraph)                      │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  Lead Agent  ──spawn──►  Sub-Agent (research)                       │ │
│  │              ──spawn──►  Sub-Agent (code generation)                │ │
│  │              ──spawn──►  Sub-Agent (slide deck)                     │ │
│  │              ──spawn──►  Sub-Agent (image)                          │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
┌───────▼────────┐         ┌────────▼────────┐         ┌────────▼────────┐
│ Skills Registry│         │ Sandbox Provider│         │ Long-term Memory│
│   (public/     │         │   • Aio (Docker)│         │   • Profile     │
│    custom/)    │         │   • Local       │         │   • Episodes    │
└────────────────┘         └─────────────────┘         │   • Knowledge   │
                                                       └─────────────────┘
```

## 四、Skills：deer-flow 的核心扩展点

skill = 一个**目录**，里面有 `SKILL.md` 和一组工具 / prompt 资源。

deer-flow 出厂自带的 public skills：

```
skills/public/
├── research/                    深度研究：搜索 + 综合 + 引用
├── report-generation/           长文报告生成
├── slide-creation/              生成 PPT
├── web-page/                    生成静态网页
├── image-generation/            文生图、图生图
├── github-deep-research/        ★ GitHub 项目深度分析
└── claude-to-deerflow/          从 Claude Code 一键提交任务到 deer-flow
```

每个 skill 都是一个完整子能力，**可独立 enable / disable**。

### Skill 内部长什么样

```
github-deep-research/
├── SKILL.md           ← 主描述：何时用 / 怎么用 / 输出格式
├── tools/
│   ├── gh_search.py
│   ├── gh_metrics.py
│   └── gh_timeline.py
├── prompts/
│   ├── planner.txt
│   ├── synthesizer.txt
│   └── citation.txt
└── templates/
    └── report.md
```

主 Agent 看见 `SKILL.md` 的 description 之后，**决定要不要激活它**。激活后这个 skill 的 tools 和 prompts 都进 context。

## 五、Sub-Agent：deer-flow 的并行武器

deer-flow 的核心 advantage 是**强 sub-agent 能力**。Lead Agent 可以**并行 spawn** 多个 sub-agent：

```python
# 简化的伪代码
async def lead_agent(user_query):
    plan = await llm_plan(user_query)
    # plan = [{"role": "research", "topic": "X"}, {"role": "research", "topic": "Y"}, ...]
    
    sub_results = await asyncio.gather(*[
        spawn_sub_agent(role=t["role"], task=t)
        for t in plan["subtasks"]
    ])
    
    final = await llm_synthesize(user_query, sub_results)
    return final
```

每个 sub-agent **独立 context**，最后只返回 ~1500 token 的 condensed summary（和 Anthropic 的官方建议完全一致）。

LangGraph 把这一切的状态机做成了**显式图**——你能可视化看到执行流。

## 六、Sandbox 实现细节

deer-flow 提供两种沙箱：

### `LocalSandboxProvider`

- 在 host 上**新建一个隔离目录**（`~/.deer-flow/sandboxes/<session_id>/`）。
- 限制工具只能读 / 写这个目录。
- bash 执行被限制在该 cwd。
- **快、依赖少，但隔离强度低**。

### `AioSandboxProvider`

- 每个 session 起一个 **Docker 容器**。
- 容器内有 Python / Node / 常用 CLI。
- 文件系统 / 网络都按需开放。
- **慢、依赖 Docker，但隔离强**。

工程上的好习惯：**`Provider` 抽象使得 deer-flow 可以接入 E2B / Modal / Daytona 这类云沙箱供应商**——只需实现同一份接口。

## 七、Long-term Memory 的实现

deer-flow 的 memory 模型分三层（和 §2.3 一致）：

```python
class Memory:
    profile: UserProfile       # 用户画像
    episodes: List[Episode]    # 事件流
    knowledge: VectorStore     # 累积知识 (向量索引)
    
    def remember(self, fact: str, kind: str, confidence: float): ...
    def recall(self, query: str, limit: int = 5): ...
    def consolidate(self): ...  # 定期合并 / 去重 / 衰减
```

数据落地：

- profile / episodes：SQLite + JSON
- knowledge：向量库（默认 Chroma，可换 Milvus）
- 全部**留在用户本机**（README 强调 "memory is stored locally and stays under your control"）

## 八、可观测性

deer-flow **直接集成** LangSmith 和 Langfuse：

```bash
# 一行环境变量打开
export LANGFUSE_PUBLIC_KEY=...
export LANGFUSE_SECRET_KEY=...
```

打开后你能在 Langfuse Web 上看到：

- 每次 Agent 调用的完整 trace
- 子 Agent 的调用树
- 每个 tool call 的 input / output / latency
- 每个 step 的 token / cost

**生产 Harness 的标配。不可观测的 Agent 是不可运营的**。

## 九、几个值得品读的设计

### A) 文件系统作为"通用接口"

无论是 sub-agent 输出、skill 产物、还是用户上传文件，**统一通过沙箱内的文件系统流转**：

```
/sandbox/<session>/
├── inbox/           ← 用户上传
├── work/            ← agent 工作目录
├── outputs/         ← 最终产物
└── reports/         ← 调试 / trace
```

这让前后端 / sub-agent 之间的通信变得**简单且语义清晰**——直接传文件名而不是塞 JSON Blob。

### B) Message Gateway 的解耦

不管你从飞书还是 Slack 还是 Web 进来，**进了 Gateway 之后是同一份 message format**。Agent runtime 完全不关心来源。

这是个**好工程**——业务进来再多渠道，Agent 内部不动。

### C) MCP 兼容

deer-flow 支持 **Model Context Protocol** —— Anthropic 提的开放协议。意味着你写一个 MCP server，就可以同时接进 Claude Code、Cursor、deer-flow，**工具一份代码到处跑**。

## 十、deer-flow 教会我们什么

```
✅ 当你做"产品级"Harness，需要 sub-agent / sandbox / memory / 观测性
✅ LangGraph 是实现复杂多 Agent 状态机的好选择
✅ Skill 是可扩展性的最佳抽象——把复杂度推到外面
✅ Message Gateway 让多渠道接入不污染 core
✅ 文件系统是最朴素也最强的 Agent 间通信介质
✅ MCP 让你的工具可被复用到任何 Harness
```

## 十一、helixent + deer-flow 互补地学

```
学 helixent，理解 Harness 的「骨架」：
   什么是 ReAct loop、什么是 tool / middleware / skill 的「基础形」

学 deer-flow，理解 Harness 的「全身肌肉」：
   sub-agent 怎么调度、sandbox 怎么设计、memory 怎么落地、UI 怎么接

读完两个项目，你会发现它们的核心模式高度一致——
只是 deer-flow 在每一个轴上都做得更深。这就是 Harness Engineering 的「普遍性」。
```

下一节我们**亲手实现**一个 mini Harness——你不需要任何花哨依赖，~200 行 Python 跑起来。

---

下一节：[§3.5 动手实验 →](./05-build-your-own.md)
