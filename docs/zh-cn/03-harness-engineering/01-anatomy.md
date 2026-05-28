---
title: §3.1 Harness 的解剖学
description: 工具循环、权限、沙箱、钩子、Session
---

# §3.1 Harness 的解剖学

> "An agent harness is everything between the language model and the real world. **The model generates text. The harness decides what that text can touch.**"

## 思想源头 · Karpathy 的 LLM OS

讨论"Harness 是什么"之前，先回到这个范式的思想原点。2023 年 9 月，Andrej Karpathy 在 X 上发了那条被反复引用的"LLM OS"推文：

> "With many 🧩 dropping recently, a more complete picture is emerging of LLMs not as a chatbot, but the **kernel process of a new Operating System**. E.g. today it orchestrates: Input & Output across modalities (text, audio, vision); Code interpreter, ability to write & run programs; Browser / internet access; Embeddings database for files and internal memory storage & retrieval. … TLDR looking at LLMs as chatbots is the same as looking at early computers as calculators. We're seeing an emergence of a whole new computing paradigm, and it is very early."  
> — [@karpathy, 2023-09-28](https://x.com/karpathy/status/1707437820045062561)

两个月后他给了"规格表"：

> "LLM OS. Bear with me I'm still cooking. Specs:  
> **LLM**: OpenAI GPT-4 Turbo 256 core (batch size) processor @ 20Hz (tok/s);  
> **RAM**: 128Ktok;  
> **Filesystem**: Ada002"  
> — [@karpathy, 2023-11-11](https://x.com/karpathy/status/1723140519554105733)

2025 年 6 月在 YC AI Startup School 演讲里他把这个类比正式化：

> "LLMs have very strong analogies to operating systems. … **LLM is a new kind of computer. It's kind of like a CPU equivalent.** The context windows are kind of like the memory. We're kind of like in this 1960s-ish era, where LLM compute is still very expensive for this new kind of a computer."  
> — Karpathy, *Software Is Changing (Again)*, [YC AI Startup School 2025-06-17](https://www.youtube.com/watch?v=LCEmiRjPEtQ)

**这就是 Harness Engineering 的思想原点**。Karpathy 没有用"harness"这个词，但他给出了等价的图：

- **LLM = CPU** —— 接受输入、产出输出
- **Context Window = RAM** —— 有限的"工作记忆"
- **嵌入数据库 = 文件系统** —— 长期持久存储
- **代码解释器 / 浏览器 = 外设** —— 系统调用
- **Harness = OS 内核** —— 调度、内存管理、I/O、权限

带着这张图回看下面的"工具循环",会发现每一块代码都对应 OS 里的一个经典子系统。

## 一、最小 Harness：工具循环（Tool Loop）

```python
def run(user_input):
    messages = [system_prompt, {"role": "user", "content": user_input}]
    while True:
        resp = model.chat(messages, tools=TOOLS)
        if not resp.tool_calls:
            return resp.content            # 模型给出最终答案，结束循环
        for tc in resp.tool_calls:
            result = TOOLS[tc.name](**tc.args)
            messages.append(tool_result(tc.id, result))
        messages.append(resp)              # 把 assistant 的 tool_call 也写回
```

这 7 行就是 **Harness 的灵魂**：

1. 模型决定下一步「想什么」「做什么」。
2. Harness 拦下 `tool_call`，调用真实代码。
3. 真实结果回填到 messages。
4. 模型基于新结果继续。

Karpathy 在 2025 年底的 *Year in Review* 博文里把这个循环称作"第一次令人信服的 LLM Agent 演示"：

> "**Claude Code (CC) emerged as the first convincing demonstration of what an LLM Agent looks like** — something that in a loopy way strings together tool use and reasoning. … it's not just a website you go to like Google, it's a little spirit/ghost that 'lives' on your computer."  
> — [Karpathy, 2025 LLM Year in Review (bearblog)](https://karpathy.bearblog.dev/year-in-review-2025/)

注意"a little spirit/ghost that 'lives' on your computer" —— 这和 §3.0 章我们把 Harness 类比成"Agent 的 OS"是同一直觉。**Agent 不是网页里的对话，是住在你电脑里的程序**。

所有 Agent 都是这个循环的变种。复杂的差异是：**多少工具、谁能调、调坏了怎么办、循环要不要拆 sub-agent、多 Session 怎么续……**

## 二、Tools：Agent 能"伸手够到"的世界

**没有工具的模型，只能写字。**

| 类别 | 例子 | 风险 |
| :--- | :--- | :--- |
| **读类** | `read_file`, `list_files`, `search`, `web_fetch` | 几乎无 |
| **写类** | `write_file`, `edit_file`, `mkdir` | 可能误改 |
| **执行类** | `bash`, `python_eval`, `npm_install` | 高 |
| **通信类** | `send_email`, `post_slack`, `call_api` | 不可逆 |
| **元工具** | `task`(子 Agent)、`memory_write`、`thinking` | — |

Anthropic 在 *Harness Engineering* 文章里点名：

> "Claude Code exposes roughly 19 permission-gated tools."

这 19 个工具是 Claude Code 的全部"宇宙"。理解了它们 = 你理解了 Coding Agent 的能力边界。

### 工具的"好坏"标准

写好一个工具，要满足：

```
1. Self-contained         一次调用能拿到完整结果，不需要先调另一个工具准备
2. Robust to error        参数错 / 资源不存在 → 返回**有意义**的错误，不抛异常崩 loop
3. Token-efficient        返回简洁结构化数据，不要 dump 50K 字符串
4. Idempotent or marked   可重复调 / 标明"不可逆"
5. Clear naming & desc    名字 + description 让模型一看就知道何时用
```

举例：

✅ 好工具：

```python
{
  "name": "read_file",
  "description": "Read a UTF-8 text file. Returns up to 2000 lines from given offset. Errors as JSON.",
  "parameters": {
    "file_path": "absolute path",
    "offset": "default 0",
    "limit": "default 2000, max 5000"
  }
}
# returns: {"content": "...", "total_lines": 1234, "truncated": false}
# on error: {"error": "FileNotFound", "path": "..."}
```

❌ 坏工具：

```python
{
  "name": "execute",
  "description": "Execute something",
  "parameters": {"cmd": "string"}
}
# 不知道是 bash 还是 python；无错误约定；可能炸权限
```

## 三、权限与沙箱

工具能动多大动作，**取决于 Harness 给它什么权限**。

### 权限层级（从 Claude Code 借鉴）

```
permission_mode:
  - read_only        Agent 只能读，写 / 执行需要每次问
  - acceptEdits      允许写文件，但 bash 仍需问
  - autoApprove      所有工具自动放行（仅在受控环境）
  - plan             只允许 plan，不允许真动手（"想清楚再说"模式）
```

每个工具调用前，Harness 检查：

```python
def execute_tool_call(tc):
    if not is_permitted(tc.name, tc.args, current_mode):
        if has_user():
            user_response = ask_user(f"允许调用 {tc.name}({tc.args})？")
            if not user_response.approve:
                return tool_result(tc.id, "user denied")
        else:
            return tool_result(tc.id, "denied: no permission and no user")
    return tool_result(tc.id, TOOLS[tc.name](**tc.args))
```

### 沙箱

写文件 / 执行 bash 永远在**沙箱**里：

| 沙箱形态 | 隔离强度 | 例子 |
| :--- | :--- | :--- |
| **同进程** | 无 | 直接 `subprocess.run` |
| **同主机不同目录** | 低 | `cd /tmp/agent-workdir && bash` |
| **同主机不同用户** | 中 | `sudo -u agent_user bash` |
| **容器** | 高 | Docker / Firecracker |
| **远程 VM** | 极高 | Modal / E2B / Daytona |

deer-flow 提供了 `AioSandboxProvider`（Docker 容器）和 `LocalSandboxProvider`（本机目录隔离）两种实现，开发者可按风险选。

::: 生产建议
**Agent 跑用户写的代码 / 网上下载的代码 → 必须容器级以上沙箱**。  
**Agent 跑你自己 codebase → 至少同主机不同目录 + 不允许 `sudo` / `rm -rf /`**。
:::

## 四、Hooks（中间件）：Agent 的 AOP

这是 helixent / Claude Code 的标配。**在 Agent 的关键事件点插入用户代码**：

```
Helixent 提供的 8 个 hook：

beforeAgentRun     ─ Agent 任务开始
  beforeAgentStep  ─ 每一步开始
    beforeModel    ─ 调模型前  (改 prompt、加日志)
    afterModel     ─ 调模型后  (评估输出)
    beforeToolUse  ─ 调工具前  (审批、参数过滤)
    afterToolUse   ─ 调工具后  (结果记录)
  afterAgentStep   ─ 每一步结束
afterAgentRun      ─ Agent 任务结束 (持久化)
```

典型用法：

```python
@hook("beforeToolUse")
def log_tool(ctx, tool_call):
    print(f"[{ctx.session_id}] → {tool_call.name}({tool_call.args})")

@hook("beforeToolUse")
def guard_dangerous(ctx, tool_call):
    if tool_call.name == "bash" and "rm" in tool_call.args.get("cmd", ""):
        return {"reject": True, "reason": "rm 被禁止"}

@hook("afterModel")
def truncate_huge_response(ctx, response):
    if len(response.content) > 50000:
        response.content = response.content[:50000] + "... [TRUNCATED]"
```

Hook 是 Harness 从"toy demo"走向"可运营产品"的关键。**没有 hook → 不能加日志、不能审计、不能动态拦截**。

## 五、Session 切换：长跑的关键

**当任务比一个 context window 还大**时，必须能"接班"。

```
Session 1                Session 2                Session 3
[start fresh]            [resume from S1]         [resume from S2]
  • read goal              • read progress.md       • read progress.md
  • plan                   • read recent files      • test current state
  • implement feat 1       • implement feat 2       • implement feat 3
  • commit                 • commit                 • commit
  • write progress.md      • update progress.md     • update progress.md
[context: 95K / 100K]    [context: 92K / 100K]    [context: 88K / 100K]
```

每个 Session 启动 ≈ 一个新工程师上岗。能让他迅速进状态的是 **progress 文件 + git log + 项目结构约定**。

Anthropic 在 *Effective Harnesses for Long-Running Agents* 里给了一份典型的 Session 启动流程（pseudocode）：

```
[Session Start]
→ Run pwd                    (建立工作目录)
→ Read claude-progress.txt   (回顾之前的工作)
→ Read feature_list.json     (识别待办)
→ Review git log             (理解最近变更)
→ Execute init.sh            (启动开发环境)
→ Run basic end-to-end tests (验证当前状态)
→ Select highest-priority incomplete feature
→ Implement with continuous testing
→ Commit to git with descriptive message
→ Update progress file
[Session End - Clean state maintained]
```

把这套流程**写进 system prompt**，Agent 就有了"工程师的工作习惯"。下一节我们会深入这块。

## 六、Memory：跨 Session 的"长期硬盘"

Harness 层的 memory ≠ §2.3 讲的 context 内 memory。

| Context Memory（§2.3） | Harness Memory（这里） |
| :--- | :--- |
| 寿命：一个 Session | 跨 Session、永久 |
| 存哪：context window 内 | 文件、SQLite、向量库 |
| 由谁读写：模型自身 | Hooks + 工具 + 调度器 |
| 例子：`<summary>` 区段 | `~/.deer-flow/memory/profile.json` |

deer-flow 的 memory 是这一类的典型实现：

> "DeerFlow remembers across sessions, building a persistent memory of your profile, preferences, and accumulated knowledge."

## 七、Hooks 之上：调度器 & 人在回路

最外层是**调度器**：

- 谁触发任务？（用户、cron、webhook、IM 消息）
- 任务跑多久后 timeout？
- 是否需要每个 step 暂停等人审批？
- 跑挂了怎么 restart？

工业级 Harness（Codex / Claude Code / deer-flow）都有：

- **TaskQueue**：长任务进队列异步跑。
- **Heartbeat**：定期向用户报进度。
- **Cancel/Resume**：用户中途叫停 / 续跑。
- **Notification**：通过 Slack / 飞书通知任务完成。

## 八、一个 Harness 完整组件清单

把上面所有抽出来一张图：

```
┌──────────────────────────────────────────────────────────────────────┐
│ Harness 完整组件                                                      │
│                                                                      │
│  ┌────────────────┐  Tool Loop                                       │
│  │ Loop Controller│ ←──→ Model API (OpenAI/Anthropic/...)            │
│  └───────┬────────┘                                                  │
│          │                                                           │
│          ↓                                                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ Tool Registry  │  │ Permission Mgr │  │ Sandbox        │         │
│  │ - read_file    │  │ - mode         │  │ - container    │         │
│  │ - bash         │  │ - approve()    │  │ - rate limit   │         │
│  │ - search       │  │ - audit log    │  │ - fs scope     │         │
│  │ - ...          │  └────────────────┘  └────────────────┘         │
│  └────────────────┘                                                  │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ Hook System    │  │ Sub-agent Mgr  │  │ Memory Backend │         │
│  │ - beforeModel  │  │ - spawn        │  │ - profile      │         │
│  │ - afterToolUse │  │ - collect_sum  │  │ - episodes     │         │
│  │ - ...          │  └────────────────┘  │ - knowledge    │         │
│  └────────────────┘                      └────────────────┘         │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ Session Mgr    │  │ Scheduler      │  │ HITL UI        │         │
│  │ - resume       │  │ - cron         │  │ - chat         │         │
│  │ - persist      │  │ - timeout      │  │ - approve UI   │         │
│  │ - progress.md  │  │ - retry        │  │ - cancel       │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
└──────────────────────────────────────────────────────────────────────┘
```

这看起来很多。**但每个组件都对应一个真实问题**。你做 toy 项目时可以省略大部分；做生产时迟早每个都得有。

---

下一节：[§3.2 长跑型 Harness 的工程 →](./02-long-running.md)
