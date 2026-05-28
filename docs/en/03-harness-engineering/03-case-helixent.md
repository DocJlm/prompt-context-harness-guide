---
title: §3.3 Case · helixent
description: TypeScript + Bun, the most minimal yet elegant Harness skeleton — a file-by-file source walkthrough
---

# §3.3 Case · helixent — Fitting ReAct into a Single Function

> "Helixent is a small library for building ReAct-style AI agent loops based on the Bun stack."  
> — [github.com/MagicCube/helixent](https://github.com/MagicCube/helixent)

helixent is maintained by **Henry Li / MagicCube** and is a **minimal but complete** Agent Harness framework. The whole repo is ~85 source files and ~10K lines of TypeScript — you can read it cover-to-cover in an evening. Its value isn't "many features"; it's that **with the least code it demonstrates every key design pattern of an industrial-grade harness**.

::: tip Why use helixent as the teaching example?
**It's small enough to read but complete enough to use.** Claude Code, Codex, Cursor are either closed-source or enormous. Helixent's core `Agent.stream()` method is ~25 lines, but it already contains **think → act → observe**, parallel tool execution, middleware, cancellability, streaming output — every core structure of a real production harness.
:::

## 1. Self-portrait of the Project

| Dimension | helixent v1.3.1 |
| :--- | :--- |
| **Language** | TypeScript 99.3% |
| **Runtime** | **Bun** (not Node) |
| **Core abstractions** | `Model` · `Message` · `Tool` · `Agent` · `Middleware` · `Skill` |
| **Distribution** | npm library + Bun-compiled single-file CLI binary |
| **Dependencies** | OpenAI SDK · Anthropic SDK · React + Ink (terminal TUI) · Zod · Commander |
| **Code size** | ~85 source files, ~10K lines |
| **License** | MIT |

A few lines of `package.json` capture the project's whole engineering philosophy:

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

**Lesson #0**: **zero build tools** on the development path. Bun runs TypeScript natively; `bun build --compile` produces a static binary directly. No webpack, no ts-node, no nodemon. This "less is more" stance runs through the whole repo.

## 2. The Four-Layer Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ src/cli/             React + Ink terminal TUI, config wizard   │
└────────────────────────┬─────────────────────────────────────┘
                         │ depends on
┌────────────────────────▼─────────────────────────────────────┐
│ src/coding/          Concrete Agent for "writing code"          │
│   - 11 file tools + bash + todo + permissions                  │
│   - createCodingAgent() factory                                 │
│   - AGENTS.md auto-load                                         │
└────────────────────────┬─────────────────────────────────────┘
                         │ depends on
┌────────────────────────▼─────────────────────────────────────┐
│ src/agent/           Generic ReAct loop + Middleware + Skills │
│   - Agent class (the core ~25-line stream() lives here)       │
│   - 8-hook middleware protocol                                 │
│   - skills loading / tool-result normalization                 │
└────────────────────────┬─────────────────────────────────────┘
                         │ depends on
┌────────────────────────▼─────────────────────────────────────┐
│ src/foundation/      Model · Message · Tool — the 3 core abs. │
│ src/community/       Anthropic / OpenAI ModelProvider adapters │
└──────────────────────────────────────────────────────────────┘
```

**Key taste**: `foundation/` doesn't know about `agent/`; `agent/` doesn't know about `coding/`; `coding/` doesn't know about `cli/`. **Zero circular dependencies.** This means if you want a "customer-service agent" or a "data-analysis agent", **you copy the `coding/` layer and swap tools**, without touching a single line in `agent/`.

## 3. Minimal Working Example

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
    content: [{ type: "text", text: "Count LOC for all .ts files in the current directory and output a markdown table." }]
});

for await (const event of stream) {
    console.log(event);  // ReAct loop intermediates: thinking / tool_call / observation / answer
}
```

**16 lines** of code launch a Coding Agent that can call bash / read files. That's helixent's "developer experience."

## 4. Foundation Layer — Contracts Every Agent Must Agree On

### 4.1 `src/foundation/messages/types/message.ts` — Message Types

helixent uses a **discriminated union** to define four message kinds:

```typescript
export interface AssistantMessage {
  role: "assistant";
  content: AssistantMessageContent;     // (TextContent | ThinkingContent | ToolUseContent)[]
  usage?: TokenUsage;
  streaming?: boolean;                  // present and true mid-stream; deleted when the stream ends
}

export interface ToolMessage {
  role: "tool";
  content: ToolMessageContent;          // ToolResultContent[]
}

export interface ToolUseContent<T extends Record<string, unknown> = Record<string, unknown>> {
  type: "tool_use";
  id: string;        // stable id to match the ToolResultContent
  name: string;
  input: T;
}

export interface ToolResultContent {
  type: "tool_result";
  tool_use_id: string;
  content: string;   // always a string (JSON or plain text)
}
```

**Lesson #1**: helixent's wire-format is **essentially the Anthropic API content schema**, but re-expressed in a "provider-neutral" way. The OpenAI adapter does conversion at both ends. The `streaming` flag is a clever optimization — the same object is **repeatedly yielded** during streaming, accumulating each time; at the end the flag is `delete`d (see §4.2).

### 4.2 `src/foundation/tools/function-tool.ts` — Tool Contract

The entire tool system boils down to **one interface + one factory function**:

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

**Lesson #2**: A tool is just **a plain data record** + a function pointer. **No BaseTool class, no `@tool` decorator, no DI container, no registry.** A Zod schema here plays **three roles**:
1. **Runtime parameter validation**
2. **JSON Schema** (via `zod-to-json-schema`, sent to the model)
3. **TypeScript type inference** (`z.infer<P>` makes `invoke`'s input fully typed)

`AbortSignal` is **enforced at the type level** — every tool must be cancellable. This closes off the common production failure mode "agent wants to cancel but the tool is hung."

### 4.3 `src/foundation/models/model.ts` — Model Is a Thin Wrapper

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

**Lesson #3**: `Model`'s only job is to **merge the system prompt into the message list** and forward to the provider. **The system prompt stays outside the message list** (`context.prompt`) until the very last moment. This lets middleware **dynamically modify the system prompt each turn** without rewriting the entire history — the skills loading mechanism exploits exactly this (§6).

## 5. The Agent Class — the Whole ReAct Control Flow Fits in One Function

`src/agent/agent.ts` is the **heart** of the entire repo. The whole ReAct loop is in one `async function*`.

### 5.1 The `stream()` Method — the Full ReAct Loop

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

**This is helixent's soul.** **~25 lines** to deliver:
- Reentrancy guard (`_streaming` flag)
- AbortController injection
- Step counter (default 100)
- 6 lifecycle hooks
- think / act branches
- Natural termination: **exit when the model stops producing `tool_use`**

::: details Can you see the relationship to the "7-line simplified loop" in §3.1?
```python
# §3.1 simplified
while True:
    resp = model.chat(messages, tools=TOOLS)
    if not resp.tool_calls:
        return resp.content
    for tc in resp.tool_calls:
        result = TOOLS[tc.name](**tc.args)
        messages.append(tool_result(tc.id, result))
    messages.append(resp)
```

All the additional code in helixent is for: **reentrancy guard / abort signal / step cap / 8 middleware hooks / streaming events**. **The core structure is identical.**
:::

### 5.2 The `_think()` Phase — Stream-Accumulate the Model Output

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

Three details to note:
- **`_beforeModel` is called after `modelContext` is built** — middleware can **modify** prompt / messages / tools (the skills middleware uses exactly this to inject skill descriptions).
- **Snapshot semantics**: what the provider yields each time is not a delta but **the accumulated current message in full**. helixent uses the `streaming` flag to decide whether to emit a progress event.
- **`delete latest.streaming`** at the end as a defensive cleanup, even though the provider should remove it.

`_deriveProgress` is an 8-line helper that decides whether to emit a "thinking" or "tool" progress event:

```typescript
private _deriveProgress(snapshot: AssistantMessage): AgentEvent {
  const toolUses = snapshot.content.filter((c): c is ToolUseContent => c.type === "tool_use");
  if (toolUses.length === 0) return { type: "progress", subtype: "thinking" };
  const last = toolUses[toolUses.length - 1]!;
  return { type: "progress", subtype: "tool", name: last.name, input: last.input };
}
```

### 5.3 The `_act()` Phase — Parallel Tool Execution, Yield in Completion Order

This is the **most clever** part of `agent.ts`. The same assistant message can contain multiple `tool_use`s. helixent uses `Promise.race` to **execute them concurrently**, and yields to the UI in **completion order** (not declaration order):

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

**Three designs worth memorizing**:

1. **Errors become tool_results, not throws** — a failed tool sends `"Error: ..."` strings back to the model and lets it decide what to do. **This is the most important resilience pattern in industrial-grade agents.**
2. **`__skip` is a first-class citizen** — middleware can short-circuit a specific tool call (the approval middleware uses this to inject "user denied" instead of actually executing). The shape `{ __skip: true, result: ... }` is detected in `_beforeToolUse`.
3. **Yield in completion order** — a tool_message is yielded as soon as each tool completes, while the `tool_use` order within the assistant message is preserved. The UI sees fast tools' results first; the model's transcript stays consistent.

## 6. The Middleware Protocol — Eight Hooks Are All There Is

`src/agent/agent-middleware.ts` describes the entire hook system in one interface:

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

**Note what isn't there**:
- ❌ **No `next()` callback** (Koa/Express style)
- ❌ **No priority ordering**
- ❌ **No try/catch error boundary**
- ❌ **No registration API** (middlewares are passed in directly via the Agent constructor)

The invocation mechanism is just 8 lines:

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

**Lesson #4**: The middleware protocol reduces to "**return a partial, the framework Object.assigns it**." This sacrifices some flexibility (middleware can't stop later middleware from running unless via `__skip`) but **is so simple it's hard to misuse**. Shared state lives in one object — `AgentContext`.

### 6.1 A Real Middleware — Skill Auto-loading

`src/agent/skills/skills-middleware.ts` shows how **two hooks deliver a complex capability**:

```typescript
export function createSkillsMiddleware(skillsDirs: string[] = ["./skills"]): AgentMiddleware {
  return {
    // hook 1: At task start, scan disk and fill in all skill metadata to agentContext
    beforeAgentRun: async () => {
      const skills: SkillFrontmatter[] = [];
      const seenSkillFiles = new Set<string>();
      for (let skillsDir of skillsDirs) {
        if (skillsDir.startsWith("~")) skillsDir = join(os.homedir(), skillsDir.slice(1));
        if (!(await exists(skillsDir))) continue;
        // Walk dir, find SKILL.md, read frontmatter (gray-matter)
        // Dedupe by absolute path
      }
      return { skills };
    },

    // hook 2: Before each model call, inject the skill list into the system prompt
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

**Lesson #5**: `beforeAgentRun` is called once per user turn and **populates** `agentContext.skills`. `beforeModel` is called before each model call and **injects** them into the prompt. **The two hooks communicate via the single shared `AgentContext` object — no closures needed.** That's why the "merge a partial" protocol is sufficient.

### 6.2 Approval Middleware — the `__skip` Rejection Mechanism

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
      // ... when allow_always_project, persist to allow-list
    },
  };
}
```

**Lesson #6**: Rejection is communicated to the model as a **tool_result message**, not as a thrown exception. The model reads "User denied execution of tool: write_file..." and **changes course** or asks for clarification. Contrast this with the clumsy alternative — throwing an exception that crashes the loop — which leaks permission-related UX outside the model's training distribution.

## 7. A Real Tool — `bash.ts` In Full

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

**Three designs worth copying**:

1. **The `description` parameter is required and first** — and the Zod `.describe()` **tells the model** "always fill this parameter first." This is a way of **actively steering the model**: forcing it to **state its intent** before generating the command. Anthropic uses the same trick in Claude Code (each tool call begins with "what I'm about to do" — the Tool Preamble idea from §1.3).
2. **AbortSignal piped directly to `proc.kill()`** — cleanup uses `{ once: true }` + removal inside `proc.exited.then(...)` — **zero memory leaks**.
3. **Non-zero exit codes return an `"Error: ..."` string** — the normalizer in `tool-result-runtime.ts` recognizes the prefix and converts it to a structured error (§8).

## 8. Tool Result Normalization — an Underrated Subsystem

`src/agent/tool-result-runtime.ts` (~5.3 KB) defines the three-way taxonomy of **what tools may return and how the harness understands them**:

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
  // ... otherwise treat as success, summary is the stringified content
}
```

**`inferToolErrorKind`** maps error-code naming conventions (`INVALID_*`, `*_NOT_FOUND`, `*_FAILED`, `RG_NOT_FOUND`) to six `ToolErrorKind` enum values that can drive UI badges and policy decisions.

**Lesson #7**: helixent enforces a tool-result **protocol**, but **does not require every tool to implement it**. Tools can return raw strings; if they want richer behavior (truncation policy, "summary-only" mode for noisy tools) they return the `{ ok, summary, data, code, details }` structure. **The runtime hides this asymmetry from the model.**

## 9. Assembling a Real Agent — `createCodingAgent`

`src/coding/agents/lead-agent.ts` shows how helixent puts the blocks together to make a real agent:

```typescript
export async function createCodingAgent(options): Promise<Agent> {
  const cwd = options.cwd ?? process.cwd();
  const skillsDirs = options.skillsDirs ?? [
    join(homedir(), ".agents/skills"),
    join(homedir(), ".helixent/skills"),
    join(cwd, ".agents/skills"),
    join(cwd, ".helixent/skills"),
  ];

  // 1. Auto-load AGENTS.md (helixent's CLAUDE.md)
  const messages: Message[] = [];
  const agentsMd = await loadAgentsMd(cwd);
  if (agentsMd) messages.push({ role: "user", content: [{ type: "text", text: agentsMd }] });

  // 2. Todo system (one tool + one middleware bound together)
  const { tool: todoTool, middleware: todoMiddleware } = createTodoSystem();

  // 3. Assemble middlewares
  const middlewares: AgentMiddleware[] = [
    createSkillsMiddleware(skillsDirs),
    todoMiddleware,
  ];
  if (askUser) {
    middlewares.push(createCodingApprovalMiddleware({
      cwd, requiresApproval: CODING_TOOLS_REQUIRING_APPROVAL, askUser, approvalPersistence,
    }));
  }

  // 4. Assemble tool set
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

**Lesson #8**: **No "Agent base class to extend."** A Coding Agent is just **a factory function that returns a configured Agent**. Optional capabilities are **opted-in via construction parameters** with patterns like `askUserQuestionTool ? [askUserQuestionTool] : []`, no inheritance hierarchy required.

## 10. What helixent **Doesn't Do** — Tension with deer-flow

helixent deliberately stays lean. **It has no**:

| Missing capability | Consequence |
| :--- | :--- |
| ❌ Sub-agents | On the roadmap but not implemented |
| ❌ Sandbox | Runs Bun directly, relies on host |
| ❌ Persistent vector memory | Depends on external libraries |
| ❌ Web UI | Terminal Ink TUI only |
| ❌ Multimodal vision | — |
| ❌ MCP tool protocol | — |
| ❌ Multi-user / auth | — |
| ❌ Remote sandbox / container orchestration | — |

**That's precisely why it makes a good teaching example**: simple enough to read, complete enough to use. **After you read §3.4 on deer-flow**, you'll see the real complexity an industrial-grade harness gains by adding these missing capabilities.

## 11. A Source-Reading Path (recommended order)

After git cloning, reading ~7 core files in this order is enough:

```
1. README.md                                  Overview
2. src/foundation/messages/types/message.ts   Four message types
3. src/foundation/tools/function-tool.ts      Tool contract
4. src/foundation/models/model.ts             Model thin wrapper
5. src/agent/agent.ts                         ★ The core ReAct loop (25-line stream())
6. src/agent/agent-middleware.ts              8-hook protocol
7. src/agent/skills/skills-middleware.ts      A real middleware
8. src/coding/tools/bash.ts                   A real tool
9. src/coding/agents/lead-agent.ts            Assembly example
```

**Readable in an evening.** After you finish, look back at the ~200-line Python harness you wrote yourself in Lab 3 and you'll find **the core structure is remarkably identical** — you weren't learning helixent, you were learning **the common skeleton of every coding agent**.

## 12. What helixent Teaches Us (Eight Takeaways)

> This section is the gist of the case study. **Each item is the concrete embodiment of a principle from §3.1 / §3.2.**

**1. One generator function = the entire control flow**  
`stream()` is 25 lines, readable **without scrolling**. Many frameworks bury this in event emitters, state machines, or LangGraph-style DAGs. helixent proves **a clean `async function*` + a for-loop is enough**.

**2. Tools are data, not classes**  
`defineTool({ ... })` returns a plain object. No BaseTool, no decorators, no registry. **Adding a tool is 20 lines of code.** A Zod schema simultaneously is runtime validator, JSON Schema for the model, and TypeScript type inference for `invoke` — **one piece of code, three uses**.

**3. Middleware is `Object.assign`, not Express-style `next()`**  
All 8 hooks use the same protocol: **return a partial, framework merges into AgentContext**. No `next()` calls, no priority queue, no error boundaries. Extreme simplicity, good composability — because shared `AgentContext` is the only state.

**4. Errors are tool_results, not exceptions**  
Both the tool layer (bash returns `"Error: ..."` string) and the middleware layer (`__skip` returns a rejection message) **turn errors into model-readable tool_results**. This is the **single most important resilience pattern** that turns a toy demo into a production agent.

**5. Parallel tool execution + yield in completion order**  
`_act` runs all tool_uses via `Promise.race`, **yielding each tool_result as it completes**. The TUI sees fast tools' results first; the model's transcript still preserves the original tool_use order.

**6. The system prompt isn't "finalized" until the last moment**  
`Model._buildModelProviderParams` injects the system prompt into the message list at forward-time; `beforeModel` middleware can append to it (that's how skills middleware does it). **This avoids the common anti-pattern of "rebuilding the entire message history every turn just to update the system prompt."**

**7. Streaming relies on snapshots, not deltas**  
Each yielded `AssistantMessage` is **the cumulative state** + a `streaming: true` flag. The loop derives progress events by inspecting snapshot content (text vs. tool_use). At stream end, the flag is deleted **in-place**. **This eliminates an entire class of "did I miss a delta?" bugs** — no consumer needs to maintain an accumulator.

**8. Strict layering, zero circular dependencies**  
`foundation/` doesn't know `agent/`, `agent/` doesn't know `coding/`, `coding/` doesn't know `cli/`. **You can lift `foundation` + `agent` out and build a totally different agent (say, a research agent) without touching a single existing file.** The README's roadmap mentions sub-agents and multi-agent teams — **and only because of this layering does extension look feasible**.

---

Next: [§3.4 Case · deer-flow →](./04-case-deer-flow.md)
