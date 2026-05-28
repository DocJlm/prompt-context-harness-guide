---
title: §2.4 压缩与子 Agent
description: Compaction · Sub-agent · Context Window 不够用时的两板斧
---

# §2.4 压缩与子 Agent

> "Sub-agents handle focused tasks with **clean context windows**, returning condensed summaries (typically **1,000–2,000 tokens**) to a coordinating main agent."  
> — Anthropic, *Effective Context Engineering for AI Agents*

当 §2.1–§2.3 的工具都用上，仍然爆窗口时，最后两板斧来了：**压缩** 与 **子 Agent**。

::: tip 在开始之前 · Manus 的两条铁律
Manus 团队在 2025 年 7 月公开了 Agent 框架做了**四次重写**之后的核心教训：

> "如果只能选择一个指标，我会认为 **KV-缓存命中率是生产阶段 AI 智能体最重要的单一指标**。"  
> "**任何更改都将使后续所有动作和观察结果的 KV-缓存失效。**"  
> — [《AI 智能体"上下文工程"实践：来自 Manus 项目的经验总结》, 腾讯云开发者社区, 2025-07-23](https://cloud.tencent.com/developer/article/2545989)

带来两条直接约束（**在你考虑 compaction / sub-agent 之前先确认这两条**）：

1. **System prompt 前缀必须绝对稳定**。一切动态内容（时间戳、用户名、当前文件名）放消息列表里，**不要放进 system prompt**。
2. **工具列表不要在 session 中动态增删**。需要"屏蔽"某个工具？用 **logits mask** 在解码阶段过滤，**而不是从工具数组里删掉它** —— 后者会让 KV-cache 全部失效。

Manus 还披露了个反直觉的成本结构：**input:output ≈ 100:1**。意味着 99% 成本在输入端，**缓存与未缓存通常差 10×**。所以"KV-cache 命中率"是单一最重要指标，这一点不夸张。
:::

## 一、Compaction：原地压缩 history

### 触发时机

```
if total_tokens > 0.7 * window_size:
    compact()
```

经验阈值是窗口的 60–80%。Claude Code 的官方做法是 ~70%。

### Compaction 的具体步骤

```
1. 把 history 切成两段：
   - "Stable" 段：很老的对话（要被压缩的）
   - "Recent" 段：最近 N 轮（保持原样）

2. 用 LLM 生成 Summary（带特殊 prompt 让它保留关键决策、未决问题）

3. 替换 history：
   [System] + [Tools] + [Examples] + [Summary] + [Recent N turns]
```

### Summary 的 Prompt 模板

```text
你正在协助一个 Agent 系统进行上下文压缩。

请阅读以下对话历史，输出一份「项目状态摘要」，**重点保留**：

1. **目标 / 任务**：用户想要什么？
2. **关键决定**：已经决定了的方案、参数、选型。
3. **已完成**：迄今完成了哪些子任务，产出了什么文件 / 数据。
4. **未决问题**：还在等待的输入、未确定的选择。
5. **风格 / 约束**：用户表达过的偏好（用词、格式、不许做的事）。

**不要**保留：
- 寒暄、过程性确认（"好的"、"明白"）。
- 已被覆盖的中间方案。
- 已经过时的代码 / 数据。

输出格式：Markdown，每个小节用 `##` 开头，每条要点不超过 30 字。
```

::: 注意
不同的 Agent 系统有不同的压缩策略。Claude Code 的一个 trick 是：**保留最近 5 个被读取的文件名 + 完整内容**，因为后续轮次大概率还会用到。这是一种**结构感知**的压缩。
:::

### Compaction 的代价

- ⚠️ **不可逆**：被压掉的细节大多回不来（除非你存了备份）。
- ⚠️ **一次 LLM 调用**：摘要本身有成本和延时。
- ⚠️ **质量风险**：摘要可能**漏掉**或**扭曲**关键事实。

减小风险的实战：
- **备份原始 history** 到磁盘（不在 context 里，但可以被工具调用拉回）。
- **多次小压缩 > 一次大压缩**：50K → 20K 比 150K → 20K 信息损失少。
- **关键节点不要压**：例如刚跑完一个昂贵的 tool result，先把它的精华提炼后再压。

## 二、Sub-agents：把"耗 token 的子任务"外包出去

### 动机

主 Agent 在做一个长任务时，遇到一个**密集但可独立**的子任务（如：搜索 50 个文件、分析一段大数据、生成一份 100 页报告）。

如果主 Agent 自己干，会**疯狂消耗主上下文的预算**。

**外包**：

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Agent                                │
│        (主上下文：90K used / 200K)                            │
│                                                              │
│              ┌──────────────────────────────┐                │
│              │  Spawn Sub-Agent              │                │
│              │  Task: "搜索并总结仓库里所有  │                │
│              │  关于'退款流程'的代码"         │                │
│              └────────────┬─────────────────┘                │
│                           │                                   │
└───────────────────────────┼───────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │ Sub-Agent (清白上下文)         │
              │   - 调用 50 次 search        │
              │   - 读 20 个文件              │
              │   - 消耗 80K tokens          │
              │   - 输出: 一份 1500 token 摘要 │
              └─────────────┬───────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────┐
│  Main Agent 收到 1500 token 摘要，继续主任务                  │
│        (主上下文增长: 90K → 92K，而非 90K → 170K)             │
└───────────────────────────────────────────────────────────────┘
```

主 Agent 的窗口只增加了 **1500 token 的摘要**，而不是 80K 的搜索过程。这就是 sub-agent 给到的杠杆。

### 子 Agent 的核心约定

按 Anthropic 的官方表述：

> "Sub-agent summaries generally return **1,000–2,000 tokens** of condensed information."

也就是说：**主 Agent 与子 Agent 之间的接口是"输入任务描述 + 输出摘要"**。子 Agent 的 trace 完全不进入主上下文。

Claude Agent SDK / Claude Code 把这个能力封装成了 `Task` 工具：

```python
task_result = call_tool("Task", {
    "subagent_type": "researcher",
    "prompt": "搜索本仓库里所有关于退款流程的代码，输出一份不超过 1500 字的摘要..."
})
# task_result.summary 进入主 Agent 的 history
```

### 什么时候用子 Agent

| 适合外包的子任务 | 不适合的子任务 |
| :--- | :--- |
| 大量搜索 / 读取 | 需要与主上下文紧密耦合 |
| 长报告生成 | 多步追问、需要主 Agent 即时反馈 |
| 独立的批处理任务 | 高速对话的客服场景 |
| 评估 / 测试一个候选方案 | 需要工具状态共享的场景 |

> 经验法则：**子任务的工具调用 > 5 次** 且 **输出 < 2K token**，就值得外包。

### 子 Agent 与多 Agent 协作的区别

```
Sub-agent（单向外包）:                Multi-agent collaboration（双向通信）:
  Main  ──spawn──►  Sub                Agent A ◄──messages──► Agent B
        ◄─summary──                          ▲
                                             │
                                          Coordinator
```

- Sub-agent：**单向**，主等子返回。简单、可控、token-efficient。
- Multi-agent：**双向**，复杂协议。更强大，但**容易陷入消息地狱**（无限互相确认）。

Anthropic 的官方推荐：**先用 sub-agent**，只有当任务真的需要多个角色长时间协作时再升级到 multi-agent。

## 三、子 Agent 在 Coding Agent 中的实战

Claude Code、Cursor、Codex 都大量用 sub-agent。常见的 sub-agent 角色：

```
┌──────────────────────────────────────────────────────────────────┐
│  Main Agent (规划 + 高层决策)                                     │
│   │                                                              │
│   ├── Explore sub-agent      搜索代码 / 文件结构                  │
│   ├── Plan sub-agent         设计实现方案                         │
│   ├── Code reviewer          审查 diff                            │
│   ├── Test runner            运行测试 + 总结结果                  │
│   └── Bash sub-agent         执行长命令 / 流式日志                │
└──────────────────────────────────────────────────────────────────┘
```

每一个子 Agent 都有自己的 system prompt 和工具子集——**专才胜过通才**。

## 四、Compaction × Sub-agent 的组合：长跑型 Agent 的完整图景

```
Time ─►
─────────────────────────────────────────────────────────────────────►

  Main Agent context usage
  
  100K ┤
       │           ┌──── compaction ────┐                              
   80K ┤          ╱                      ╲                             
       │         ╱                        ╲      ┌─ sub-agent          
   60K ┤        ╱           ┌──sub-agent───┐╲    │  来回不进入主上下文  
       │       ╱            │ (并行任务)    │ ╲  │                     
   40K ┤      ╱             │              │  ╲ │                     
       │     ╱              └──summary─────┘   ╲│                     
   20K ┤    ╱                       ↓           ╲                      
       │   ╱                                                           
    0K └──────────────────────────────────────────────────────────►
       0min   1m   2m   3m   4m   5m   6m   7m   8m   9m   10m
       
  ▲ Compaction：原地切上去
  ▲ Sub-agent：外包不增长
```

主 Agent 想"持续跑下去"的两大法器，就这两个。

## 五、把这一节装进脑子

- ✅ **接近窗口 60–80%**：触发 compaction。
- ✅ **遇到大量搜索 / 报告 / 评估子任务**：spawn sub-agent。
- ⚠️ **不要轻易触发 multi-agent**：先看 sub-agent 能不能解决。
- ⚠️ **重要原始信息备份到磁盘**：让模型可以"回放"。

到这里，**Context Engineering 的核心装备已经讲完**。下面是 Lab 2，亲手把上面的概念落地。

---

下一节：[§2.5 动手实验 →](./05-lab.md)
