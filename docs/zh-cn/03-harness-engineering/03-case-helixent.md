---
title: §3.3 案例 · helixent
description: TypeScript + Bun，最简优雅的 Harness 骨架 — 逐文件源码剖析
---

# §3.3 案例 · helixent — 把 ReAct 装进一个函数里

> "Helixent is a small library for building ReAct-style AI agent loops based on the Bun stack."  
> — [github.com/MagicCube/helixent](https://github.com/MagicCube/helixent)

helixent 由 **Henry Li / MagicCube** 维护，是一个**极简但完整**的 Agent Harness 框架。整个仓库约 85 个源文件、~1 万行 TypeScript —— 一个晚上能从头到尾读完。它的价值不在于"功能多"，而在于**用最少的代码把工业级 Harness 的所有关键设计模式演示了一遍**。

::: tip 为什么用 helixent 当教学样本？
**它小到能读懂，但完整到能用**。Claude Code、Codex、Cursor 都是闭源或庞大无比。helixent 的核心 `Agent.stream()` 方法只有 ~25 行，但里面已经包含了**think → act → observe**、并行工具执行、中间件、可中断、流式输出 —— 真实生产 Harness 的所有核心结构。
:::

## 一、项目自画像

| 维度 | helixent v1.3.1 |
| :--- | :--- |
| **语言** | TypeScript 99.3% |
| **运行时** | **Bun**（不是 Node） |
| **核心抽象** | `Model` · `Message` · `Tool` · `Agent` · `Middleware` · `Skill` |
| **形态** | npm 库 + Bun 编译的单文件 CLI 二进制 |
| **依赖** | OpenAI SDK · Anthropic SDK · React + Ink（终端 TUI）· Zod · Commander |
| **代码规模** | ~85 源文件，约 1 万行 |
| **License** | MIT |

`package.json` 几行配置就把整个项目的工程化哲学讲清楚：

```json
{
  "name": "helixent", "version": "1.3.1",
  "bin": { "helixent": "dist/bin/helixent" },
  "scripts": {
    "build:bin": "rm -rf dist/bin && bun build index.ts --compile --outfile dist/bin/helixent",
    "check": "tsc --noEmit && eslint . --ext .ts && bun test",
    "dev": "bun run index.ts"
  }
}
```

**教学点 #0**：开发路径上**零构建工具**。Bun 原生跑 TypeScript，`bun build --compile` 直接产物是静态二进制。没有 webpack、没有 ts-node、没有 nodemon。这种"少即是多"的取舍贯穿全仓库。

## 二、四层架构

```
┌──────────────────────────────────────────────────────────────┐
│ src/cli/             基于 React + Ink 的终端 TUI、配置向导     │
└────────────────────────┬─────────────────────────────────────┘
                         │ 依赖
┌────────────────────────▼─────────────────────────────────────┐
│ src/coding/          面向"写代码"场景的具体 Agent              │
│   - 11 个文件工具 + bash + todo + permissions                 │
│   - createCodingAgent() 工厂                                  │
│   - AGENTS.md 自动加载                                        │
└────────────────────────┬─────────────────────────────────────┘
                         │ 依赖
┌────────────────────────▼─────────────────────────────────────┐
│ src/agent/           通用 ReAct 循环 + Middleware + Skills    │
│   - Agent 类（核心 ~25 行的 stream() 方法在这里）             │
│   - 8-hook middleware 协议                                    │
│   - skills 加载 / tool-result 标准化                          │
└────────────────────────┬─────────────────────────────────────┘
                         │ 依赖
┌────────────────────────▼─────────────────────────────────────┐
│ src/foundation/      Model · Message · Tool 三个核心抽象      │
│ src/community/       Anthropic / OpenAI 适配 ModelProvider    │
└──────────────────────────────────────────────────────────────┘
```

**关键品味**：`foundation/` 不知道有 `agent/`；`agent/` 不知道有 `coding/`；`coding/` 不知道有 `cli/`。**零循环依赖**。这意味着你想做"客服 Agent"或"数据分析 Agent"，**复制 `coding/` 那一层换工具就行**，不用动 `agent/` 一行代码。

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
    content: [{ type: "text", text: "请把当前目录所有 .ts 文件统计 LOC，输出 markdown 表格。" }]
});

for await (const event of stream) {
    console.log(event);  // ReAct 循环的中间产物：thinking / tool_call / observation / answer
}
```

**16 行代码**就跑起了一个能调 bash / read file 的 Coding Agent。这就是 helixent 的"开发者体验"。

## 四、Foundation 层 — 所有 Agent 必须同意的契约

### 4.1 `src/foundation/messages/types/message.ts` — 消息类型

helixent 用**鉴别联合**（discriminated union）定义四种消息：

```typescript
export interface AssistantMessage {
  role: "assistant";
  content: AssistantMessageContent;     // (TextContent | ThinkingContent | ToolUseContent)[]
  usage?: TokenUsage;
  streaming?: boolean;                  // 流式中存在并为 true；流结束后该字段被删除
}

export interface ToolMessage {
  role: "tool";
  content: ToolMessageContent;          // ToolResultContent[]
}

export interface ToolUseContent<T extends Record<string, unknown> = Record<string, unknown>> {
  type: "tool_use";
  id: string;        // 稳定 id，用来匹配 ToolResultContent
  name: string;
  input: T;
}

export interface ToolResultContent {
  type: "tool_result";
  tool_use_id: string;
  content: string;   // 始终是字符串（JSON 或纯文本）
}
```

**教学点 #1**：helixent 的线上消息格式**几乎就是 Anthropic API 的 content schema**，但被重新表达为"provider 无关"的形式。OpenAI 适配器在两端做转换。`streaming` 标志是个聪明的优化 —— 同一个对象在流式过程中**反复 yield 出去**，每次累积，结束时把标志 `delete` 掉（详见 §4.2）。

### 4.2 `src/foundation/tools/function-tool.ts` — 工具契约

整个工具系统就是**一个接口 + 一个工厂函数**：

```typescript
export interface FunctionTool<
  P extends z.ZodSchema<Record<string, unknown>> = z.ZodSchema<Record<string, unknown>>,
  R = unknown,
> {
  name: string;
  description: string;
  parameters: P;                                       // Zod schema
  invoke: (input: z.infer<P>, signal?: AbortSignal) => Promise<R>;
}

export function defineTool<P, R>(
  { name, description, parameters, invoke }: { ... }
): FunctionTool<P, R> {
  return { name, description, parameters, invoke };
}
```

**教学点 #2**：一个工具就是一条**普通数据记录** + 一个函数指针。**没有 BaseTool 基类、没有 @tool 装饰器、没有 DI 容器、没有注册中心**。Zod schema 在这里**身兼三职**：
1. **运行时参数校验**
2. **JSON Schema**（通过 `zod-to-json-schema` 发给模型）
3. **TypeScript 类型推断**（`z.infer<P>` 让 `invoke` 的入参完全类型安全）

`AbortSignal` 是**类型层强制**的 —— 每个工具都必须可被中断。这就堵住了"Agent 想取消但工具卡死"的常见生产事故。

### 4.3 `src/foundation/models/model.ts` — Model 是个薄外壳

```typescript
export class Model {
  constructor(
    readonly name: string,
    readonly provider: ModelProvider,
    readonly options?: Record<string, unknown>,
  ) {}

  invoke(context: ModelContext) {
    return this.provider.invoke(this._buildModelProviderParams(context));
  }
  stream(context: ModelContext) {
    return this.provider.stream(this._buildModelProviderParams(context));
  }

  private _buildModelProviderParams(context: ModelContext): ModelProviderInvokeParams {
    const messages: Message[] = [];
    if (context.prompt) {
      messages.push({ role: "system", content: [{ type: "text", text: context.prompt }] });
    }
    messages.push(...context.messages);
    return { model: this.name, options: this.options, messages,
             tools: context.tools, signal: context.signal };
  }
}
```

**教学点 #3**：`Model` 唯一职责是**把 system prompt 合并进 message 列表**，再转发给 provider。**系统提示词一直放在消息列表之外**（`context.prompt`），直到最后一刻才注入。这让 middleware 可以**按轮次动态修改 system prompt** 而不需要重写整个历史 —— skill 加载机制就利用了这一点（§六）。

## 五、Agent 类 — 整个 ReAct 控制流装在一个函数里

`src/agent/agent.ts` 是全仓库**心脏**。整个 ReAct 循环就在一个 `async function*` 里。

### 5.1 `stream()` 方法 — ReAct 循环全文

```typescript
async *stream(message: UserMessage): AsyncGenerator<AgentEvent> {
  if (this._streaming) {
    throw new Error("Agent is already streaming");
  }

  this._abortController = new AbortController();
  this._appendMessage(message);
  await this._beforeAgentRun();
  this._streaming = true;
  try {
    for (let step = 1; step <= this.options.maxSteps; step++) {
      this._abortController.signal.throwIfAborted();
      await this._beforeAgentStep(step);
      const assistantMessage = yield* this._think();
      await this._afterModel(assistantMessage);
      yield { type: "message", message: assistantMessage };

      const toolUses = this._extractToolUses(assistantMessage);
      if (toolUses.length === 0) {
        await this._afterAgentRun();
        return;
      }

      yield* this._act(toolUses);
      await this._afterAgentStep(step);
    }
    throw new Error("Maximum number of steps reached");
  } finally {
    this._streaming = false;
    this._abortController = null;
  }
}
```

**这就是 helixent 的灵魂**。**~25 行**完成：
- 重入保护（`_streaming` 守卫）
- AbortController 注入
- 步数计数器（默认 100）
- 6 个生命周期 hook
- think / act 分支
- 自然终止条件：**模型不再产生 `tool_use` 就退出**

::: details 你能看出和 §3.1 那个"7 行简化版"的关系吗？
```python
# §3.1 简化版
while True:
    resp = model.chat(messages, tools=TOOLS)
    if not resp.tool_calls:
        return resp.content
    for tc in resp.tool_calls:
        result = TOOLS[tc.name](**tc.args)
        messages.append(tool_result(tc.id, result))
    messages.append(resp)
```

helixent 多出来的代码全部用于：**重入保护 / 中断信号 / 步数上限 / 8 个 middleware hook / 流式 event**。**核心结构完全一致**。
:::

### 5.2 `_think()` 阶段 — 流式累积模型输出

```typescript
private async *_think(): AsyncGenerator<AgentEvent, AssistantMessage> {
  const modelContext: ModelContext = {
    prompt: this.prompt,
    messages: this.messages,
    tools: this.tools,
    signal: this._abortController?.signal,
  };
  await this._beforeModel(modelContext);

  let latest: AssistantMessage | null = null;
  for await (const snapshot of this.model.stream(modelContext)) {
    latest = snapshot;
    if (snapshot.streaming) {
      yield this._deriveProgress(snapshot);
    }
  }
  if (!latest) throw new Error("Model stream ended without producing a message");
  if (latest.streaming) delete latest.streaming;
  this._appendMessage(latest);
  return latest;
}
```

注意三个细节：
- **`_beforeModel` 在 modelContext 构建之后调用** —— middleware 可以**修改** prompt / messages / tools（skills middleware 就靠这个注入 skill 描述）
- **snapshot 语义**：provider 每次 yield 的不是 delta 而是**累积当前消息全文**。helixent 用 `streaming` 标志判断要不要发 progress event。
- **`delete latest.streaming`** 在结尾防御性删除标志，即便 provider 应该自己删

`_deriveProgress` 是个 8 行的小工具，决定要发 "thinking" 还是 "tool" 进度事件：

```typescript
private _deriveProgress(snapshot: AssistantMessage): AgentEvent {
  const toolUses = snapshot.content.filter((c): c is ToolUseContent => c.type === "tool_use");
  if (toolUses.length === 0) return { type: "progress", subtype: "thinking" };
  const last = toolUses[toolUses.length - 1]!;
  return { type: "progress", subtype: "tool", name: last.name, input: last.input };
}
```

### 5.3 `_act()` 阶段 — 并行工具执行，按完成顺序 yield

这是 `agent.ts` 里**最巧妙**的部分。同一条 assistant 消息里可能有多个 `tool_use`。helixent 用 `Promise.race` 让它们**并发执行**，并按**完成顺序**（而不是声明顺序）yield 给 UI：

```typescript
private async *_act(toolUses: ToolUseContent[]): AsyncGenerator<AgentEvent> {
  const signal = this._abortController?.signal;
  const pending = toolUses.map(async (toolUse, index) => {
    try {
      const tool = this.tools?.find((t) => t.name === toolUse.name);
      if (!tool) throw new Error(`Tool ${toolUse.name} not found`);
      const beforeResult = await this._beforeToolUse(toolUse);
      if (beforeResult.skip) {
        return { index, toolUseId: toolUse.id, toolName: toolUse.name, result: beforeResult.result };
      }
      const result = await tool.invoke(toolUse.input, signal);
      await this._afterToolUse(toolUse, result);
      return { index, toolUseId: toolUse.id, toolName: toolUse.name, result };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return { index, toolUseId: toolUse.id, toolName: toolUse.name, result: `Error: ${message}` };
    }
  });

  const abortPromise = signal
    ? new Promise<never>((_, reject) => {
        if (signal.aborted) { reject(signal.reason); return; }
        signal.addEventListener("abort", () => reject(signal.reason), { once: true });
      })
    : null;

  const remaining = new Set(pending.map((_, i) => i));
  while (remaining.size > 0) {
    const candidates = [...remaining].map((i) => pending[i]);
    const resolved = (await (abortPromise
      ? Promise.race([...candidates, abortPromise])
      : Promise.race(candidates)))!;
    remaining.delete(resolved.index);

    const toolMessage: ToolMessage = {
      role: "tool",
      content: [{
        type: "tool_result",
        tool_use_id: resolved.toolUseId,
        content: formatToolResultForMessage({ toolName: resolved.toolName, result: resolved.result }),
      }],
    };
    this._appendMessage(toolMessage);
    yield { type: "message", message: toolMessage };
  }
}
```

**三个值得记下来的设计**：

1. **错误变 tool_result，而不是 throw** —— 失败的工具把 `"Error: ..."` 字符串送回模型，让模型自行决定怎么处理。**这是工业级 Agent 最重要的韧性模式**。
2. **`__skip` 是一等公民** —— middleware 可以短路某个工具调用（审批 middleware 用它注入"用户拒绝"而不真的执行）。形状 `{ __skip: true, result: ... }` 在 `_beforeToolUse` 里被检测。
3. **完成顺序 yield** —— tool_message 完成一个 yield 一个，但 assistant message 里 `tool_use` 仍保留原始顺序。这让 UI 看到快工具先出结果，模型看到的 transcript 仍然一致。

## 六、Middleware 协议 — 八个 hook 就是全部

`src/agent/agent-middleware.ts` 用一个 interface 描述了 hook 系统全部：

```typescript
export interface AgentMiddleware {
  beforeModel?:    (p: BeforeModelParams)    => Promise<Partial<ModelContext> | null | void>;
  afterModel?:     (p: AfterModelParams)     => Promise<Partial<AssistantMessage> | null | void>;
  beforeAgentRun?: (p: BeforeAgentRunParams) => Promise<Partial<AgentContext> | null | void>;
  afterAgentRun?:  (p: AfterAgentRunParams)  => Promise<Partial<AgentContext> | null | void>;
  beforeAgentStep?:(p: BeforeAgentStepParams)=> Promise<Partial<AgentContext> | null | void>;
  afterAgentStep?: (p: AfterAgentStepParams) => Promise<Partial<AgentContext> | null | void>;
  beforeToolUse?:  (p: { agentContext: AgentContext; toolUse: ToolUseContent })
                                              => Promise<BeforeToolUseResult>;
  afterToolUse?:   (p: AfterToolUseParams)   => Promise<Partial<AgentContext> | null | void>;
}

export type BeforeToolUseResult =
  | Partial<AgentContext>
  | { readonly __skip: true; readonly result: unknown }
  | null | undefined | void;
```

**注意有什么没有**：
- ❌ **没有 `next()` 回调**（Koa/Express 风格）
- ❌ **没有优先级排序**
- ❌ **没有 try/catch 错误边界**
- ❌ **没有注册 API**（middleware 数组直接通过 Agent 构造器传入）

调用机制简单到只有 8 行：

```typescript
private async _beforeModel(modelContext: ModelContext) {
  for (const middleware of this.middlewares) {
    if (!middleware.beforeModel) continue;
    const result = await middleware.beforeModel({ modelContext, agentContext: this._context });
    if (result) {
      Object.assign(modelContext, result);
    }
  }
}
```

**教学点 #4**：整个 middleware 协议归结为"**返回一个 partial，框架帮你 Object.assign**"。这丢掉了一些灵活性（middleware 不能阻止后续 middleware 运行，除非用 `__skip`），但**简单到让人无法误用**。共享状态都装在 `AgentContext` 这一个对象里。

### 6.1 一个真实 middleware — skill 自动加载

`src/agent/skills/skills-middleware.ts` 演示了**用两个 hook 实现复杂能力**：

```typescript
export function createSkillsMiddleware(skillsDirs: string[] = ["./skills"]): AgentMiddleware {
  return {
    // hook 1: 任务开始时扫描磁盘，把所有 skill 元数据填入 agentContext
    beforeAgentRun: async () => {
      const skills: SkillFrontmatter[] = [];
      const seenSkillFiles = new Set<string>();
      for (let skillsDir of skillsDirs) {
        if (skillsDir.startsWith("~")) skillsDir = join(os.homedir(), skillsDir.slice(1));
        if (!(await exists(skillsDir))) continue;
        // 遍历目录，找 SKILL.md，读 frontmatter（gray-matter）
        // 去重 by 绝对路径
      }
      return { skills };
    },

    // hook 2: 每次调模型前，把 skill 列表注入 system prompt
    beforeModel: async ({ modelContext, agentContext }) => {
      if (agentContext.skills && agentContext.skills.length > 0) {
        const skillsXML = agentContext.skills
          .map((s) => `<skill name="${s.name}" path="${s.path}">\n${s.description}\n</skill>`)
          .join("\n");
        return {
          prompt: modelContext.prompt + `\n<skill_system>...<skills>\n${skillsXML}\n</skills>...</skill_system>`,
        };
      }
    },
  };
}
```

**教学点 #5**：`beforeAgentRun` 每个用户回合调用一次，**填充** `agentContext.skills`。`beforeModel` 每次调模型时调用，**注入**到 prompt。**两个 hook 通过 AgentContext 这一个共享对象通信**，根本不需要闭包。这就是为什么"merge a partial"协议足够用。

### 6.2 审批 middleware — `__skip` 拒绝机制

```typescript
export function createCodingApprovalMiddleware(options: { ... }): AgentMiddleware {
  return {
    beforeToolUse: async ({ toolUse }) => {
      if (!options.requiresApproval.includes(toolUse.name)) return;
      const allowed = await options.approvalPersistence?.loadAllowList(options.cwd) ?? new Set();
      if (allowed.has(toolUse.name)) return;

      const decision = await options.askUser(toolUse);
      if (decision === "deny") {
        return {
          __skip: true,
          result: `User denied execution of tool: ${toolUse.name}. You must either find an alternative approach or ask the user for clarification.`,
        };
      }
      // ... allow_always_project 时持久化白名单
    },
  };
}
```

**教学点 #6**：拒绝以 **tool_result message** 的形式告诉模型，而不是 throw 异常。模型读到"User denied execution of tool: write_file..."后会**改变路线**或主动澄清。这与那种"抛异常然后崩 loop"的拙劣实现形成鲜明对比 —— 后者会把权限相关的 UX 泄露到模型训练分布之外。

## 七、一个真实工具 —— `bash.ts` 全文

```typescript
import z from "zod";
import { defineTool } from "@/foundation";

export const bashTool = defineTool({
  name: "bash",
  description: "Execute a bash command in a unix-like environment",
  parameters: z.object({
    description: z.string()
      .describe("Explain why you want to execute the command. Always place `description` as the first parameter."),
    command: z.string().describe("The bash command to execute."),
  }),
  invoke: async ({ command }, signal) => {
    const proc = Bun.spawn({
      cmd: ["zsh", "-c", command],
      stdout: "pipe",
      stderr: "pipe",
    });

    if (signal) {
      const onAbort = () => proc.kill();
      signal.addEventListener("abort", onAbort, { once: true });
      void proc.exited.then(() => signal.removeEventListener("abort", onAbort));
    }

    const output = await new Response(proc.stdout).text();
    const exitCode = await proc.exited;
    if (exitCode !== 0) {
      const stderr = await new Response(proc.stderr).text();
      return `Error: Command ${command} failed with exit code ${exitCode}: ${stderr}`;
    }
    return output;
  },
});
```

**三个值得抄走的设计**：

1. **`description` 参数是必填且第一个** —— 而且 schema 的 `.describe()` 里**指令模型**"总是第一个填这个参数"。这是一种**主动 steer 模型的技巧**：强迫它在生成 command 前先**说出意图**。看到 Anthropic 在 Claude Code 设计里也用这一招（每个工具调用前要先说"我接下来要做什么"，§1.3 提到的 Tool Preamble 概念）。
2. **AbortSignal 直通到 `proc.kill()`** —— 清理用 `{ once: true }` + `proc.exited.then(...)` 内移除，**零内存泄漏**。
3. **非零退出码返回 `"Error: ..."` 字符串** —— `tool-result-runtime.ts` 里的规范化器识别这个前缀，转成结构化错误（§八）。

## 八、Tool Result 规范化 — 一个被低估的子系统

`src/agent/tool-result-runtime.ts`（~5.3 KB）定义了**工具能返回什么、harness 如何理解**的三向分类：

```typescript
export function normalizeToolResult(result: unknown): NormalizedToolResult {
  if (isStructuredToolSuccess(result)) {
    return { ok: true, summary: result.summary,
             ...(result.data !== undefined ? { data: result.data } : {}),
             raw: result };
  }
  if (isStructuredToolError(result)) {
    return { ok: false, summary: result.summary, error: result.error,
             ...(result.code ? { code: result.code } : {}),
             errorKind: inferToolErrorKind(result.code), raw: result };
  }
  if (typeof result === "string" && result.startsWith("Error:")) {
    const error = result.slice("Error:".length).trim() || "Tool execution failed.";
    return { ok: false, summary: error, error, errorKind: "unknown", raw: result };
  }
  // ... 否则当 success 包，summary 是字符串化的内容
}
```

**`inferToolErrorKind`** 把错误码命名约定（`INVALID_*`、`*_NOT_FOUND`、`*_FAILED`、`RG_NOT_FOUND`）映射到 6 种 `ToolErrorKind` 枚举，可以驱动 UI 徽章和策略决定。

**教学点 #7**：helixent 强制了一个工具结果**协议**，但**不强迫每个工具实现它**。工具可以返回原始字符串；如果想要更丰富的行为（截断策略、对噪音工具的"仅摘要"模式），就返回 `{ ok, summary, data, code, details }` 结构。**运行时把这种不对称对模型隐藏起来**。

## 九、组装一个真实 Agent —— `createCodingAgent`

`src/coding/agents/lead-agent.ts` 演示了 helixent 如何把所有积木拼成一个真的 Agent：

```typescript
export async function createCodingAgent(options): Promise<Agent> {
  const cwd = options.cwd ?? process.cwd();
  const skillsDirs = options.skillsDirs ?? [
    join(homedir(), ".agents/skills"),
    join(homedir(), ".helixent/skills"),
    join(cwd, ".agents/skills"),
    join(cwd, ".helixent/skills"),
  ];

  // 1. 自动加载 AGENTS.md (helixent 版的 CLAUDE.md)
  const messages: Message[] = [];
  const agentsMd = await loadAgentsMd(cwd);
  if (agentsMd) messages.push({ role: "user", content: [{ type: "text", text: agentsMd }] });

  // 2. Todo 系统（一个工具 + 一个 middleware 绑在一起）
  const { tool: todoTool, middleware: todoMiddleware } = createTodoSystem();

  // 3. 装配 middlewares
  const middlewares: AgentMiddleware[] = [
    createSkillsMiddleware(skillsDirs),
    todoMiddleware,
  ];
  if (askUser) {
    middlewares.push(createCodingApprovalMiddleware({
      cwd, requiresApproval: CODING_TOOLS_REQUIRING_APPROVAL, askUser, approvalPersistence,
    }));
  }

  // 4. 装配工具集
  return new Agent({
    model,
    prompt: `<agent name="Helixent" role="leading_agent" ...>...
<working_directory dir="${cwd}/" />
<tool_usage>
- Inspect directories before assuming file paths.
- Prefer list_files or glob_search to discover files.
- Prefer grep_search to locate relevant content.
- Read a file before editing it.
- Prefer apply_patch for targeted edits.
- ...
</tool_usage>
...`,
    messages,
    tools: [
      bashTool, fileInfoTool, listFilesTool, globSearchTool, grepSearchTool,
      mkdirTool, movePathTool, readFileTool, writeFileTool, strReplaceTool,
      applyPatchTool, todoTool,
      ...(askUserQuestionTool ? [askUserQuestionTool] : []),
    ],
    middlewares,
  });
}
```

**教学点 #8**：**没有 "Agent 基类要继承"**。一个 Coding Agent 就是一个**返回配置好的 Agent 的工厂函数**。可选能力通过 `askUserQuestionTool ? [askUserQuestionTool] : []` **干净地按构造参数 opt-in**，不需要继承层级。

## 十、helixent **没做**的事 — 与 deer-flow 的张力

helixent 故意保持精简。**它没有**：

| 缺席能力 | 后果 |
| :--- | :--- |
| ❌ Sub-agents | roadmap 里有但还没实现 |
| ❌ 沙箱 | 直接跑 Bun 进程，依赖宿主 |
| ❌ 持久化向量记忆 | 依赖外部库 |
| ❌ Web UI | 只有终端 Ink TUI |
| ❌ 多模态视觉处理 | — |
| ❌ MCP 工具协议 | — |
| ❌ 多用户 / 鉴权 | — |
| ❌ 远程沙箱 / 容器编排 | — |

**这恰恰是它适合当教学样本的原因**：简单到能读懂，但完整到能用。**等你看完 §3.4 deer-flow**，就会看到工业级 Harness 加上这些缺失能力之后的真实复杂度。

## 十一、源码阅读路线（推荐顺序）

git clone 之后，按下面顺序读 ~7 个核心文件就够了：

```
1. README.md                                  概览
2. src/foundation/messages/types/message.ts   消息四种类型
3. src/foundation/tools/function-tool.ts      工具契约
4. src/foundation/models/model.ts             Model 薄外壳
5. src/agent/agent.ts                         ★ 核心 ReAct 循环 (25 行 stream())
6. src/agent/agent-middleware.ts              8-hook 协议
7. src/agent/skills/skills-middleware.ts      一个真实 middleware
8. src/coding/tools/bash.ts                   一个真实工具
9. src/coding/agents/lead-agent.ts            装配示例
```

**一个晚上能读完**。读完之后，回过来对照 Lab 3 你自己写的 ~200 行 Python harness，会发现**核心结构高度一致** —— 你不是在学 helixent，你是在学**所有 Coding Agent 的共同骨架**。

## 十二、helixent 教给我们什么（八条 takeaways）

> 这一节是本案例研究的精华。**每一条都对应 §3.1 / §3.2 学到的某个原则的具体落地**。

**1. 一个 generator 函数 = 整个控制流**  
`stream()` 25 行，可以**不用翻页**就看完完整的 ReAct 循环。许多框架把这部分埋在 event emitter、状态机或 LangGraph 风格 DAG 里。helixent 证明**一个干净的 `async function*` + 一个 for 循环就够了**。

**2. 工具是数据，不是类**  
`defineTool({ ... })` 返回一个普通对象。没有 BaseTool、没有装饰器、没有注册中心。**加一个工具就是 20 行代码**。Zod schema 同时担任运行时校验器、给模型的 JSON Schema、给 `invoke` 的 TypeScript 类型推断 —— **一份代码三个用途**。

**3. Middleware 是 `Object.assign`，不是 Express 风格的 `next()`**  
8 个 hook 全部一个协议：**返回 partial，框架 merge 到 AgentContext**。无 `next()` 调用、无优先级队列、无错误边界。简洁度极高，组合性也好 —— 因为共享 `AgentContext` 是唯一状态。

**4. 错误是 tool_result，不是异常**  
工具层（bash 返回 `"Error: ..."` 字符串）和 middleware 层（`__skip` 返回拒绝消息）都把错误**变成模型可读的 tool_result**。这是把 toy demo 变成生产 Agent 的**最重要的韧性模式**。

**5. 并行工具执行 + 按完成顺序 yield**  
`_act` 用 `Promise.race` 跑所有 tool_use，**完成一个 yield 一个 tool_result**。TUI 看到快工具先出结果，模型看到的 transcript 仍然保持 tool_use 原始顺序。

**6. System Prompt 直到最后一刻才"定型"**  
`Model._buildModelProviderParams` 在转发给 provider 时才把 system prompt 注入消息列表，`beforeModel` middleware 可以追加（skills middleware 就是这么干的）。**避免了"每轮重建整个消息历史只为更新 system prompt"** 这种常见反模式。

**7. 流式靠快照而不是 delta**  
每次 yield 的 `AssistantMessage` 是**累积状态** + `streaming: true` 标志。loop 通过查看快照内容（text vs tool_use）来 derive 进度事件。流结束时**原地** delete 掉标志。**消除了一整类"我是不是漏了 delta"的 bug**，所有消费者都不用维护累积器。

**8. 严格分层、零循环依赖**  
`foundation/` 不知道 `agent/`，`agent/` 不知道 `coding/`，`coding/` 不知道 `cli/`。**你可以把 foundation + agent 两层抽出来，造一个完全不同的 Agent（比如研究 Agent），不用动一个现存文件**。README 的 roadmap 里说要做 sub-agents、multi-agent 团队 —— **正是因为这套分层，扩展才看起来可行**。

---

下一节：[§3.4 案例 · deer-flow →](./04-case-deer-flow.md)
