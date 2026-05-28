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

## 八、把这一节装进脑子

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
