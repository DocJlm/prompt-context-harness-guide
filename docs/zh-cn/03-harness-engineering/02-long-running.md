---
title: §3.2 长跑型 Harness 的工程
description: Planner-Generator-Evaluator · progress.txt · Context Reset
---

# §3.2 长跑型 Harness 的工程

> "By 'clean state' we mean the kind of code that would be appropriate for merging to a main branch: there are no major bugs, the code is orderly and well-documented, and in general, a developer could easily begin work on a new feature **without first having to clean up an unrelated mess**."  
> — Anthropic, *Effective Harnesses for Long-Running Agents*

## 一、长跑任务的核心难题

一个 Agent 任务要跑 4 小时、写 30 个文件、调 200 次工具，**它会遇到的失败模式**：

1. **Context anxiety**：上下文越用越满，模型开始"心虚地"提前收尾。
2. **Confidence drift**：模型对自己生成的代码盲目自信，不肯重新审视。
3. **Environment damage**：把开发环境搞坏（依赖装错、文件覆盖、git 状态乱）。
4. **Lost progress**：跑到一半挂掉，没存进度，下次完全从零开始。
5. **One-shot illusion**：试图一次性把整个产品做完，结果做了一半发现整体方向错。

Karpathy 在 Dwarkesh 播客上把这个问题刻画为 **"March of Nines"（9 的长征）**：

> "What takes the long amount of time and the way to think about it is that it's a **march of nines**. Every single nine is a constant amount of work. … When you get a demo and something works **90%** of the time, that's just the first nine. Then you need the second nine, a third nine, a fourth nine, a fifth nine."  
> — [Karpathy, Dwarkesh Podcast 2025-10-17](https://www.dwarkesh.com/p/andrej-karpathy)

也就是说：**Demo 跑通 90% 只是第一个 9**。从这里到生产级的 99.999% 之间，每一个 9 都是等量的工程量。长跑型 Harness 工程的全部价值，就是把"再加一个 9"变得可重复。

Anthropic 的解决方案，是 *Harness Design for Long-Running Applications* 这篇文章里的三大原则。

## 二、三大原则

### 原则 1 · Decompose into tractable chunks（拆解到可控粒度）

不要让 Agent 一次做完整个项目。**先 plan，把项目拆成"一次 Session 能完成一个"的小 feature**。

```json
// feature_list.json
[
  {"id": "F1", "desc": "用户登录页 UI", "deps": [],     "status": "done"},
  {"id": "F2", "desc": "登录 API 路由",  "deps": ["F1"], "status": "done"},
  {"id": "F3", "desc": "JWT 鉴权中间件", "deps": ["F2"], "status": "in_progress"},
  {"id": "F4", "desc": "登出端点",        "deps": ["F3"], "status": "pending"},
  ...
]
```

每个 Session：
- 读 `feature_list.json`，挑一个 `pending` 且 deps 已 `done` 的。
- 实现 + 测试 + commit。
- 把状态标成 `done`，再写下一个 Session 的提示。
- 退出。

### 原则 2 · Use structured artifacts for context handoff（用结构化文件传递上下文）

不要靠 message history 在 Session 之间传状态。**写文件**：

```
project/
├── claude-progress.txt    ← 当前进度 + 关键决定 + 已知问题
├── feature_list.json      ← 完整 feature 清单
├── ARCHITECTURE.md        ← 高层架构说明
├── init.sh                ← 启动开发环境的脚本
└── .git/                  ← 完整版本历史
```

Anthropic 的原话：

> "The key insight here was finding a way for agents to quickly understand the state of work when starting with a fresh context window, which is accomplished with the **claude-progress.txt** file alongside the git history. Inspiration for these practices came from knowing what effective software engineers do every day."

**Agent 的项目 = 真实工程师的项目**。你怎么写 README 和 NOTES.md，Agent 也怎么写。

### 原则 3 · Separate generation from evaluation（生成与评估分离）

Anthropic 的发现：**Agent 自评不可靠**。

> "Agents tend to respond by confidently praising the work—even when, to a human observer, the quality is obviously mediocre."

解决：**专门有一个 Evaluator agent**，独立 context window，专门跑测试和检查。它和 Generator agent 之间通过文件 + 测试用例通信。

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Planner    │ ─spec─►│  Generator  │ ─diff─► │  Evaluator  │
│             │        │ (写代码)     │         │ (跑测试)     │
└─────────────┘        └─────────────┘         └─────────────┘
                              ▲                        │
                              │ <─ fail report─────────┘
                              │
                       (修复 → re-eval)
```

这就是 **Planner-Generator-Evaluator** 三 Agent 架构。Anthropic 在 *Harness Design* 那篇里详细介绍。

## 三、典型 Session 启动流程

```
[Session Start]
  │
  ├── 1. Orient
  │     • pwd
  │     • ls -la
  │     • cat claude-progress.txt
  │     • cat feature_list.json
  │     • git log -10 --oneline
  │
  ├── 2. Verify environment
  │     • ./init.sh
  │     • npm test  / pytest  (smoke test)
  │     • 如失败 → 优先修复 env，不开新 feature
  │
  ├── 3. Pick next feature
  │     • 从 feature_list.json 找一个 pending 且 deps 已 done 的
  │     • 在 progress.txt 里 append: "Working on F3"
  │
  ├── 4. Implement
  │     • 写代码（小步快跑）
  │     • 边写边跑单元测试
  │     • 必要时 spawn evaluator sub-agent 做端到端验收
  │
  ├── 5. Commit
  │     • git commit -m "F3: ..."
  │     • 更新 feature_list.json: F3.status = done
  │     • 在 progress.txt 写下：今日完成 + 关键决定 + 已知问题
  │
  └── 6. Exit cleanly
        • 确认 git working tree 是干净的
        • 确认 init.sh 还能跑
        • 留一行 "下一次 Session 应该做 F4" 在 progress.txt
```

把这一整段写进 system prompt + tool description，Agent 自然就有了**工程师的工作习惯**。

## 四、claude-progress.txt 的内容范式

```markdown
# Project Progress

Last updated: 2026-05-28 by Session #7

## Goal
构建一个支持 SSO 的 Notion-like 在线笔记应用。

## Architecture (decided)
- Backend: FastAPI + PostgreSQL + Redis
- Frontend: Next.js + TipTap editor
- Auth: GitHub OAuth + JWT

## Completed
- F1 ✅ 用户登录页 UI
- F2 ✅ 登录 API 路由
- F3 ✅ JWT 中间件 (this session)

## In Progress
- F4 🚧 登出端点 (next session start here)

## Known Issues
- Redis 连接在 Docker compose 上偶尔超时 → tracked in issue #7
- 前端 TipTap 在 Safari 18 上的 BOM 显示异常 → workaround in commit a1b2c3

## Key Decisions
- 选 JWT 而不是 session：因为前后端分离 + 移动端支持
- 不引入 Prisma：FastAPI 用原生 SQLAlchemy 已经够用

## Open Questions
- 多租户支持是 V1 必须的吗？等待用户确认。
```

这一份**文件本身就是 System Prompt 的延伸**——下一次 Session 启动时 Agent 第一件事就是读它。

## 五、Context Reset：主动"洗牌"

> "Context resets were a key unlock: the harness used Sonnet 4.5, which exhibited the 'context anxiety' tendency... Creating a harness that worked well across context resets was key to keeping the model on task."  
> — Anthropic, *Harness Design*

什么是 Context Reset？

**当 Agent 处于"context anxiety"或者长时间打圈圈时，Harness 主动 kill 当前 Session，开一个全新 Session 让它继续。**

```
Session N (60min in):
  context 168K / 200K
  Agent: "I think we're almost done, let me wrap up..."  ← 心虚信号
  Agent: 反复在两个修改方案之间摇摆               ← 困境信号
  
  ┌────────────────────────────────────────┐
  │  Harness intervenes:                    │
  │  1. Force save progress.txt             │
  │  2. Force git commit (WIP)              │
  │  3. Kill session                        │
  │  4. Start Session N+1 fresh             │
  └────────────────────────────────────────┘

Session N+1 (fresh):
  context 0K / 200K
  Agent reads progress.txt → orient → continue
  
  ↓ no anxiety, fresh attention budget
```

**Context Reset 听起来粗暴，但极其有效**——它复刻了真实工程师"睡一觉再看"的智慧。

实施方式：

- **基于 token**：context > 70% → 准备 reset。
- **基于行为**：检测到反复改同一段代码 → 强制 reset。
- **基于时间**：连续运行 > X 小时 → 强制 reset 做心智回填。

## 六、Generator vs Evaluator：用文件 contract 通信

```python
# Evaluator 看到的文件
# /workspace/eval_contracts/F3_jwt_middleware.json
{
  "feature_id": "F3",
  "description": "JWT 鉴权中间件",
  "test_steps": [
    "POST /api/login with valid credentials → expect 200 + token",
    "GET /api/me without token → expect 401",
    "GET /api/me with valid token → expect 200 + user info",
    "GET /api/me with expired token → expect 401 + 'token expired'"
  ],
  "test_via": "playwright",   // 或 "pytest", "curl"
  "passes": false,
  "evaluator_notes": []
}
```

Evaluator 跑测试，更新这个文件。Generator 启动新 step 时读它：

```python
def pick_next_action():
    failed = [c for c in load_contracts() if not c["passes"]]
    if failed:
        return f"Fix and re-test: {failed[0].feature_id}"
    return "All pass. Pick next feature from feature_list.json"
```

这一招把 **"模型自评"** 改成 **"另一个独立 Agent 评 + 通过文件传递"**，避开了 confidence drift。

## 七、案例：Anthropic 自己的两阶段 + 三 Agent 架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                          PLANNING PHASE                              │
│                                                                      │
│  User Brief ────► Planner Agent (1 session)                          │
│                      │                                               │
│                      ↓ produces:                                     │
│                   • feature_list.json (16+ features over sprints)    │
│                   • ARCHITECTURE.md                                  │
│                   • acceptance_criteria.md                           │
│                   • init.sh                                          │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ↓
┌──────────────────────────────────────────────────────────────────────┐
│                        IMPLEMENTATION PHASE                          │
│                                                                      │
│  Loop until all features done:                                       │
│                                                                      │
│   Generator Agent ◄──────────────┐                                   │
│      (fresh context per session) │                                   │
│      • read progress.txt          │                                   │
│      • pick next feature         │                                   │
│      • implement + commit        │                                   │
│      • update progress.txt       │                                   │
│         │                        │                                   │
│         ↓ commit                 │                                   │
│   Evaluator Agent                │                                   │
│      • run Playwright tests      │                                   │
│      • update eval_contracts     │                                   │
│      • if fail → write report ───┘                                   │
└──────────────────────────────────────────────────────────────────────┘
```

这套架构 Anthropic 自己用 Sonnet 4.5 实测能**自动跑出能跑通端到端测试的 Web 应用**。

## 八、来自实战的声音

理论讲完了。下面是**在生产里跑了几千小时的人**告诉你的真相。

### 8.1 Manus —— "KV-Cache 命中率是单一最重要的指标"

Manus 团队在 2025 年 7 月公开了他们做 Agent 框架的复盘（被腾讯云开发者社区中文转载），自嘲为 "随机梯度下降式" 工程 —— **重写了四次**。最深刻的两条规则：

> "如果只能选择一个指标，我会认为 **KV-缓存命中率是生产阶段 AI 智能体最重要的单一指标**。"

> "**任何更改都将使后续所有动作和观察结果的 KV-缓存失效。**"

—— [《AI 智能体"上下文工程"实践：来自 Manus 项目的经验总结》, 腾讯云开发者社区, 2025-07-23](https://cloud.tencent.com/developer/article/2545989)

这两条铁律给 Harness 设计带来两条直接约束：

1. **系统 prompt 前缀必须绝对稳定**。任何动态注入都要放在末尾。
2. **工具不要动态增删**。用 **logits mask 屏蔽** 不应被调用的工具，而不是从工具列表里删掉它 —— 删除会让所有后续 KV-cache 失效。

Manus 还披露了一个反直觉的成本结构：**input:output ≈ 100:1**。也就是说一个长跑 Agent 的成本 99% 都在输入端。**缓存与未缓存的 token 价差通常是 10×**。这就解释了为什么 KV cache 命中率是核心指标。

### 8.2 Peter Steinberger —— "终端宫格 = 我的 orchestrator"

OpenClaw（前身 Clawd / Moltbot）的作者、前 PSPDFKit 创始人 Peter Steinberger，2025-2026 年间在博客和 Pragmatic Engineer 专访里分享了他**反共识**的长跑 Agent 工作流。这位"奥地利 vibe coder"不用任何高级 orchestrator，而是直接用**终端宫格**：

> "Between 3-8 in parallel **in a 3x3 terminal grid**, most of them in the same folder. … Agents make **git atomic commits themselves**. **Don't be afraid of stopping models mid-way** — file changes are atomic."  
> — [Steinberger, *Just Talk To It*, 2025-10-14](https://steipete.me/posts/just-talk-to-it)

他给出了"长跑型 Agent 工程"的 Peter 派纲领（与 Anthropic 的官方版形成有意思的对照）：

| 原则 | 出处 |
| :--- | :--- |
| **Prompts are code, your .md/.json files are state on disk.** | [Essential Reading for Agentic Engineers](https://steipete.me/posts/2025/essential-reading) |
| **Atomic git commits by the agent itself, safe to kill mid-stream.** | [Just Talk To It](https://steipete.me/posts/just-talk-to-it) |
| **Skip third-party harnesses; subscribe to the labs directly.** "4 OpenAI subs and 1 Anthropic sub." | [Just Talk To It](https://steipete.me/posts/just-talk-to-it) |
| **Close the loop inside the agent** —— 让 Agent 自己 compile / lint / test / validate，本地测试胜过远程 CI。 | [Pragmatic Engineer interview](https://newsletter.pragmaticengineer.com/p/the-creator-of-clawd-i-ship-code) |
| **YOLO 模式 + `--dangerously-skip-permissions`** 才是 inference 速度的唯一打开方式。 | [Pragmatic Engineer interview](https://newsletter.pragmaticengineer.com/p/the-creator-of-clawd-i-ship-code) |
| **"I ship code I don't read."** | [Pragmatic Engineer interview](https://newsletter.pragmaticengineer.com/p/the-creator-of-clawd-i-ship-code) |

注意 Peter 派与 Anthropic 派**至少有两个根本分歧**：

| 维度 | Anthropic 派 | Peter 派 |
| :--- | :--- | :--- |
| Sub-agent 调度 | 用 `task` 工具显式 spawn | **不用 orchestrator**，纯靠终端宫格 |
| 评估闭环 | 独立 Evaluator agent | 让 Generator 自己跑测试 |
| 风险控制 | 严格 permission gate | YOLO + `--dangerously-skip-permissions` |

哪个对？**两个都对，看你的项目** ——
- **企业级、多用户、不可逆操作多**：Anthropic 派稳。
- **单人项目、原子提交、迭代速度第一**：Peter 派快。

Karpathy 在 Sequoia 演讲里给的中庸建议是 **"Keep AI on tight leash"** 与 **"Autonomy slider"**：

> "There's what I call the **autonomous slider** … you can either just do a quick search, or you can do research, or you can do deep research."  
> — Karpathy, Software Is Changing (Again), YC 2025-06

**好的 Harness 不固定一个自主等级，而是给用户一根可调的滑杆**。

### 8.3 阿里云 —— "Agent 应该灵活自主还是稳定可控？"

阿里云算法专家姜剑（飞樰）在 InfoQ 文章里给出了同一个张力的企业落地版：

> "Agent 到底应该是灵活自主还是稳定可控？其实这并不是非此即彼的状态，**取决于你的场景**。"  
> — [《阿里云客服 Agent 业务提效实践》, InfoQ, 2025-07-04](https://www.infoq.cn/article/vxqmohtlz9oasln733rg)

阿里把 Agent 拆为两类：
- **"大模型自主规划"类**（如 RDS 异常诊断）—— 偏 Peter 派
- **"Workflow 预编排"类**（如订单财务查询）—— 偏 Anthropic 派

并配套**评测语料**（工具选择 / 动作执行 / 参数提取准确率）+ **AI 辅助提示词调优** 流程，降低业务侧 prompt 编写门槛。

### 8.4 阿里云望宸 —— 上下文工程的"框架接管"趋势

阿里云望宸在《浅谈 Agent 开发工具链演进历程》里给出了一个判断：

> "**把原本开发者负责的 Agent 上下文工程，转移到了框架侧**，包括构建、执行和运行。"  
> — [阿里云云原生, 2025-10-27](https://www.cnblogs.com/alisystemsoftware/p/19169571)

他把工具链演进划分为四阶段：基础框架（LangChain/LlamaIndex）→ 协作 & 工具（Dify、MCP）→ 强化学习 → **模型中心化**（AgentKit、Claude Skills）。

注意第四阶段：**Skills、AGENTS.md 这类约定让框架自身越来越薄、模型自己负责越来越多**。helixent 的 `~/.agents/skills/` 自动发现、deer-flow 的 `claude-to-deerflow` 互通 skill —— 都是这个趋势的具体落地。

## 九、把这一节装进脑子

写长跑 Harness 的不二法门：

✅ **拆**：feature_list.json，一次 Session 做一个。  
✅ **写**：progress.txt + ARCHITECTURE.md + 任何关键决定都进文件。  
✅ **分**：Planner / Generator / Evaluator 至少三个角色，独立 context。  
✅ **洗**：Context > 70% 主动 reset，不要等爆。  
✅ **测**：每个 Session 退出前必跑 smoke test，环境必须干净。  
✅ **commit**：每个小步都 `git commit -m "..."` —— git log 是 Agent 的脑回路。

下面两节我们看两个**工业级开源 Harness 项目**——helixent 和 deer-flow——是怎么把这些原则落地的。

---

下一节：[§3.3 案例 · helixent →](./03-case-helixent.md)
