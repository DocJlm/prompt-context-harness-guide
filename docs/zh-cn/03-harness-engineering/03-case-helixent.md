---
title: §3.3 案例 · helixent
description: TypeScript + Bun，最简优雅的 Harness 骨架
---

# §3.3 案例 · helixent

> "Helixent is a small library for building ReAct-style AI agent loops based on the Bun stack."  
> — [github.com/MagicCube/helixent](https://github.com/MagicCube/helixent)

helixent 由开发者 **Henry Li / MagicCube** 维护，是一个**极简但完整**的 Agent Harness 框架。**因为它简单，所以特别适合学习**——你能在一两个晚上把它整个吃透。

## 一、项目自画像

| 维度 | helixent |
| :--- | :--- |
| **语言** | TypeScript 99.3% |
| **运行时** | **Bun**（不是 Node） |
| **核心抽象** | Model、Message、Tool、Agent Loop、Middleware、Skill |
| **形态** | npm 库 + CLI |
| **依赖** | React + Ink（终端 UI）、OpenAI SDK |
| **代码规模** | 几千行（可一周读完） |

## 二、三层架构

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3 · Coding Agent (src/coding/)                            │
│   一个面向"写代码"场景的具体 Agent，                              │
│   带 file tools、bash tool、project memory（AGENTS.md）           │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ uses
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2 · Agent Loop (src/agent/)                               │
│   通用 ReAct 循环 + Middleware + Skills loader                   │
│   人在回路 approval、并行 tool execution                          │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ uses
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1 · Foundation (src/foundation/)                          │
│   Model、Message、Tool 三个核心抽象                              │
│   ModelProvider 抽象（OpenAI / Anthropic / 自定义）              │
└─────────────────────────────────────────────────────────────────┘
```

这个三层分得**特别干净**：

- **Foundation** 抽象了"什么是模型、什么是工具、什么是消息"——它**不知道**有循环。
- **Agent Loop** 负责 think → act → observe，但**不知道**具体在做什么。
- **Coding Agent** 是一个具体应用，**继承**了 Agent Loop 并塞进 coding 工具。

你想做"客服 Agent" / "数据分析 Agent" / "邮件助理 Agent"？**复制 Coding Agent 那一层换工具就行**。

## 三、最小可工作示例

```ts
import { OpenAIModelProvider, Model } from "helixent";
import { createCodingAgent } from "helixent/coding";

const provider = new OpenAIModelProvider({
    baseURL: "https://api.openai.com/v1",
    apiKey: process.env.OPENAI_API_KEY,
});
const model = new Model("gpt-4o", provider, { max_tokens: 16384 });
const agent = await createCodingAgent({ model });

const stream = await agent.stream({
    role: "user",
    content: [{ type: "text", text: "请把当前目录下所有 .ts 文件统计 LOC，然后输出 markdown 表格。" }]
});

for await (const event of stream) {
    console.log(event);  // events 是 ReAct 循环的中间产物：thinking / tool_call / observation / answer
}
```

**16 行代码**就跑起了一个能调 bash / read file 的 Coding Agent。**这就是好的抽象**。

## 四、Agent Loop 内部（伪代码）

把 helixent 的 agent loop 剖出来，大致长这样（基于源码简化）：

```ts
async function* agentLoop(agent, userMessage) {
    yield* hooks.beforeAgentRun(ctx);
    
    let messages = [...agent.systemMessages, userMessage];
    
    for (let step = 0; step < MAX_STEPS; step++) {
        yield* hooks.beforeAgentStep(ctx, step);
        
        yield* hooks.beforeModel(ctx, messages);
        const response = await agent.model.chat(messages, agent.tools);
        yield* hooks.afterModel(ctx, response);
        
        messages.push(response);
        
        if (!response.tool_calls) {
            yield { type: "final", content: response.content };
            break;  // 模型不再调工具 → 退出循环
        }
        
        // 并行执行所有 tool_calls
        const results = await Promise.all(
            response.tool_calls.map(async (tc) => {
                yield* hooks.beforeToolUse(ctx, tc);
                
                if (agent.requiresApproval && !await ui.approve(tc)) {
                    return { tool_call_id: tc.id, content: "user denied" };
                }
                
                const result = await agent.toolRegistry[tc.name].execute(tc.args);
                yield* hooks.afterToolUse(ctx, tc, result);
                
                return { tool_call_id: tc.id, content: result };
            })
        );
        
        messages.push(...results);
        yield* hooks.afterAgentStep(ctx, step);
    }
    
    yield* hooks.afterAgentRun(ctx);
}
```

注意三个关键设计：

1. **流式 yield**：每一步都产 event，方便 UI / 日志 / 测试。
2. **8 个 hook 点**：完全 AOP。
3. **并行 tool execution**：模型一次 yield 多个 tool_call → 一起跑。

## 五、Tool 的声明方式

```ts
import { tool } from "helixent";
import { z } from "zod";

export const readFile = tool({
    name: "read_file",
    description: "Read a UTF-8 text file. Returns up to 2000 lines.",
    parameters: z.object({
        file_path: z.string().describe("Absolute path to the file."),
        offset: z.number().default(0),
        limit: z.number().default(2000),
    }),
    async execute({ file_path, offset, limit }) {
        const text = await Bun.file(file_path).text();
        const lines = text.split("\n").slice(offset, offset + limit);
        return { content: lines.join("\n"), total_lines: text.split("\n").length };
    },
});
```

特点：

- ✅ 用 **Zod** 描述 schema → 自动转 JSON Schema → 自动校验参数。
- ✅ 异步 execute → 用 Bun 的原生 IO。
- ✅ 返回结构化 JSON → 不是大段字符串。

这种 tool 声明方式可以说是**业界标准**（OpenAI Agent SDK、Vercel AI SDK、LangChain.js 都长得类似）。

## 六、Middleware（Hook）的实战例子

```ts
import { defineMiddleware } from "helixent";

export const auditLogger = defineMiddleware({
    async beforeToolUse(ctx, toolCall) {
        await db.insert("audit", {
            session_id: ctx.sessionId,
            tool: toolCall.name,
            args: toolCall.args,
            timestamp: Date.now(),
        });
    },
});

export const dangerousCmdGuard = defineMiddleware({
    async beforeToolUse(ctx, toolCall) {
        if (toolCall.name === "bash") {
            const cmd = toolCall.args.command;
            if (/rm\s+-rf\s+\//.test(cmd)) {
                return { reject: true, reason: "rm -rf / 被禁止" };
            }
        }
    },
});

agent.use(auditLogger).use(dangerousCmdGuard);
```

加 hook 不动 core code，**所有约束都是可插拔的**。这就是 helixent 给到的优雅。

## 七、Skills：第三方能力的动态加载

helixent 实现了 Agent Skills 标准格式。一个 skill 长这样：

```
~/.agents/skills/
└── code-review/
    ├── SKILL.md       ← 描述这个 skill 是什么、何时用
    ├── prompt.txt     ← 注入的 system 片段
    └── tools/
        ├── lint.ts
        └── coverage.ts
```

helixent 启动时**自动发现**这些路径：

- `~/.agents/skills/` （全局）
- `~/.helixent/skills/` （helixent 私有）
- `<project>/.agents/skills/` （项目级）
- `<project>/.helixent/skills/`

然后根据 user query 动态决定**激活哪些 skill**。

这种"插件化"设计让 helixent 可以被**社区扩展**而不需要 fork。Anthropic 的 Skills、Claude Code 的 skill 系统都是同一思路。

## 八、Project Memory：AGENTS.md

helixent 约定项目根目录有一个 `AGENTS.md`（Anthropic 的 Claude Code 是 `CLAUDE.md`，OpenAI Codex 是 `AGENTS.md` 也兼容）：

```markdown
# Project Agents Guide

## Tech Stack
- Bun 1.1+
- TypeScript strict mode
- React 19 + Ink for terminal UI

## Coding Conventions
- 4-space indent
- Use ZodSchema for all tool params
- Errors return { error: { code, message } }, never throw

## Testing
- Run `bun test` before any commit
- E2E tests live in tests/e2e/

## Things NOT to do
- Don't add Node.js shims (Bun-only)
- Don't introduce ESLint (use Biome)
```

**这一份文件**会被自动加到 Coding Agent 的 system prompt 里。它是 §3.2 讲的 "structured artifacts for context handoff" 的具体落地。

## 九、helixent 没做的事（与 deer-flow 对比）

helixent **故意保持精简**，没有：

- ❌ Sub-agents（在 roadmap 里，还未实现）
- ❌ 沙箱（直接跑 Bun 进程，依赖 host）
- ❌ 持久化向量记忆（依赖外部库）
- ❌ Web UI（只有终端 Ink UI）
- ❌ 多模态视觉处理

这恰恰是它适合做教学样本的原因——**简单到能读懂，但完整到能用**。

## 十、源码阅读路线（推荐顺序）

如果你 git clone 这个 repo 想读源码，建议这样：

```
1. README.md                     概览
2. src/foundation/types.ts       Model/Message/Tool 基本类型
3. src/foundation/model.ts       Model 类
4. src/foundation/tool.ts        Tool 的定义和注册
5. src/agent/loop.ts            ReAct 主循环（黄金的 100 行）
6. src/agent/middleware.ts      Hook 注册和触发机制
7. src/coding/tools/*.ts        各个工具的具体实现
8. src/coding/agent.ts          具体的 CodingAgent 怎么组装出来
9. examples/*.ts                看 demo 是怎么用的
```

一个晚上能读完。**强烈推荐**作为入门第一个要读的 Harness 项目。

## 十一、helixent 教会我们什么

```
✅ Harness 的核心是 ~100 行的 loop + 工具调度
✅ Foundation / Loop / Specific Agent 三层分离是好品味
✅ Middleware/Hook 是把 toy 变 product 的关键
✅ Tool 用 Zod schema 是当今最佳实践
✅ Skills 让框架自身保持小，把扩展性外包
✅ 项目 README + AGENTS.md 是工程师的"接班手册"
```

接下来我们看一个**几乎完全相反**的 Harness 项目——deer-flow。它把 Sub-agents、Sandbox、Long-term memory、Multi-channel UI 全做了。

---

下一节：[§3.4 案例 · deer-flow →](./04-case-deer-flow.md)
