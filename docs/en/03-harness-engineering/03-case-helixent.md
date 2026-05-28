---
title: §3.3 Case · helixent
description: TypeScript + Bun, the most minimal yet elegant Harness skeleton
---

# §3.3 Case · helixent

> "Helixent is a small library for building ReAct-style AI agent loops based on the Bun stack."  
> — [github.com/MagicCube/helixent](https://github.com/MagicCube/helixent)

helixent is maintained by developer **Henry Li / MagicCube**. It's an **extremely minimal yet complete** Agent Harness framework. **Because it's simple, it's especially good for learning** — you can read the whole thing front-to-back in a couple of evenings.

## 1. Project Self-Portrait

| Dimension | helixent |
| :--- | :--- |
| **Language** | TypeScript 99.3% |
| **Runtime** | **Bun** (not Node) |
| **Core abstractions** | Model, Message, Tool, Agent Loop, Middleware, Skill |
| **Form** | npm library + CLI |
| **Dependencies** | React + Ink (terminal UI), OpenAI SDK |
| **Code size** | A few thousand lines (readable in a week) |

## 2. Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3 · Coding Agent (src/coding/)                            │
│   A concrete Agent tailored for "writing code" scenarios,       │
│   with file tools, bash tool, project memory (AGENTS.md)        │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ uses
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2 · Agent Loop (src/agent/)                               │
│   General ReAct loop + Middleware + Skills loader               │
│   Human-in-the-loop approval, parallel tool execution           │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ uses
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1 · Foundation (src/foundation/)                          │
│   Three core abstractions: Model, Message, Tool                 │
│   ModelProvider abstraction (OpenAI / Anthropic / custom)       │
└─────────────────────────────────────────────────────────────────┘
```

These three layers are **exceptionally clean**:

- **Foundation** abstracts "what a model is, what a tool is, what a message is" — it **doesn't know** there's a loop.
- **Agent Loop** handles think → act → observe but **doesn't know** what concrete task is being done.
- **Coding Agent** is a concrete application that **extends** the Agent Loop and plugs in coding tools.

Want to build a "customer service Agent" / "data analysis Agent" / "email assistant"? **Just copy the Coding Agent layer and swap out the tools.**

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
    content: [{ type: "text", text: "Count LOC for every .ts file in the current directory, then output a markdown table." }]
});

for await (const event of stream) {
    console.log(event);  // events are intermediate ReAct outputs: thinking / tool_call / observation / answer
}
```

**16 lines of code** spin up a Coding Agent that can call bash / read files. **This is what a good abstraction looks like.**

## 4. Inside the Agent Loop (pseudocode)

Drilling into helixent's agent loop, simplified from the source it looks roughly like this:

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
            break;  // Model stops calling tools → exit loop
        }
        
        // Execute all tool_calls in parallel
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

Three key design choices to note:

1. **Streaming yield**: every step emits an event, making UI / logging / testing easy.
2. **8 hook points**: fully AOP.
3. **Parallel tool execution**: when the model yields multiple tool_calls at once → run them concurrently.

## 5. How Tools Are Declared

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

Highlights:

- ✅ Uses **Zod** for schema → auto-converted to JSON Schema → automatic arg validation.
- ✅ Async execute → uses Bun's native IO.
- ✅ Returns structured JSON → not a giant string blob.

This style of tool declaration is essentially **industry standard** (OpenAI Agent SDK, Vercel AI SDK, LangChain.js all look similar).

## 6. Practical Middleware (Hook) Examples

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
                return { reject: true, reason: "rm -rf / is forbidden" };
            }
        }
    },
});

agent.use(auditLogger).use(dangerousCmdGuard);
```

You add hooks without touching the core code — **all constraints are pluggable**. That's helixent's elegance in action.

## 7. Skills: Dynamically Loading Third-Party Capabilities

helixent implements the Agent Skills standard format. A skill looks like:

```
~/.agents/skills/
└── code-review/
    ├── SKILL.md       ← What this skill is, when to use it
    ├── prompt.txt     ← The system fragment to inject
    └── tools/
        ├── lint.ts
        └── coverage.ts
```

helixent **auto-discovers** these paths at startup:

- `~/.agents/skills/` (global)
- `~/.helixent/skills/` (helixent-private)
- `<project>/.agents/skills/` (project-level)
- `<project>/.helixent/skills/`

It then dynamically decides **which skills to activate** based on the user query.

This "plugin" design lets helixent be **extended by the community** without forking. Anthropic's Skills and Claude Code's skill system follow the same approach.

## 8. Project Memory: AGENTS.md

helixent conventions place an `AGENTS.md` in the project root (Anthropic's Claude Code uses `CLAUDE.md`; OpenAI Codex also accepts `AGENTS.md`):

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

**This file** is automatically inserted into the Coding Agent's system prompt. It is the concrete realization of the "structured artifacts for context handoff" idea from §3.2.

## 9. What helixent Deliberately Doesn't Do (vs deer-flow)

helixent **intentionally stays lean**, without:

- ❌ Sub-agents (on the roadmap, not yet implemented)
- ❌ Sandbox (runs Bun process directly, depends on host)
- ❌ Persistent vector memory (relies on external libs)
- ❌ Web UI (only terminal Ink UI)
- ❌ Multimodal vision processing

That's precisely what makes it a great teaching sample — **small enough to read, complete enough to use**.

## 10. Recommended Source-Reading Path

If you git clone the repo and want to read the source, this is the recommended order:

```
1. README.md                     Overview
2. src/foundation/types.ts       Model/Message/Tool basic types
3. src/foundation/model.ts       The Model class
4. src/foundation/tool.ts        Tool definition and registration
5. src/agent/loop.ts             The ReAct main loop (the golden ~100 lines)
6. src/agent/middleware.ts       Hook registration and triggering
7. src/coding/tools/*.ts         Concrete implementations of each tool
8. src/coding/agent.ts           How the concrete CodingAgent is assembled
9. examples/*.ts                 See how the demos use it
```

Read it in one evening. **Strongly recommended** as the first Harness project to study for newcomers.

## 11. What helixent Teaches Us

```
✅ The core of a Harness is a ~100-line loop + tool dispatch
✅ Foundation / Loop / Specific Agent — three-layer separation is good taste
✅ Middleware/Hook is the key to turning a toy into a product
✅ Tool with Zod schema is today's best practice
✅ Skills keep the framework small by outsourcing extensibility
✅ Project README + AGENTS.md is the engineer's "shift handover manual"
```

Next we'll look at a Harness project that's **almost the exact opposite** — deer-flow. It does Sub-agents, Sandbox, Long-term memory, and Multi-channel UI, all of it.

---

Next section: [§3.4 Case · deer-flow →](./04-case-deer-flow.md)
