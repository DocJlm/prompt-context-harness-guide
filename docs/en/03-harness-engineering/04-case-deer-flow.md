---
title: §3.4 Case · deer-flow
description: ByteDance's open-source SuperAgent Harness — a full-stack walkthrough of an industrial-grade Harness
---

# §3.4 Case · deer-flow — What an Industrial-Grade Harness Looks Like

> "DeerFlow is an open-source long-horizon **super agent harness** that orchestrates **sub-agents**, **memory**, and **sandboxes** to do almost anything — powered by **extensible skills**."  
> — [github.com/bytedance/deer-flow](https://github.com/bytedance/deer-flow) · README L14–17

**deer-flow** (Deep Exploration and Efficient Research Flow) is open-sourced by ByteDance. **Within 48 hours of its v2.0 release in February 2026, GitHub stars surged past 47k+**, briefly hitting Trending #1. v2.0 is a **full rewrite** — sharing almost no code with v1.0 (the earlier LangManus deep-research framework). Everything in this section refers to v2.0.

If helixent is "Lego Technic basic bricks," **deer-flow is a finished car off the factory line**. It provides industrial-grade answers to everything helixent deliberately leaves out: **sub-agent scheduling, Docker sandbox, long-term memory, observability, multi-IM channels, MCP, safe termination**. **The two solve different problems, and both are worth reading.**

## 1. Self-portrait of the Project

| Dimension | deer-flow v2.0 |
| :--- | :--- |
| **Main language** | Python 73% + TypeScript 15% |
| **Core framework** | **LangGraph + LangChain**, but the key innovation is **replacing LangGraph nodes with 18 Middlewares** |
| **Distribution** | Monorepo: backend / frontend / skills / docker |
| **Features** | Sub-agent · Sandbox · Memory · 7 IM channels · MCP (with OAuth) · Loop Detection · Tracing |
| **Typical deployment** | Nginx (2026) + Gateway (8001) + Frontend (3000) + Provisioner (K8s sandbox) |

## 2. Repository Topology

The **load-bearing paths** extracted via `gh api repos/bytedance/deer-flow/git/trees/main?recursive=1`:

```
backend/
├── app/                                     # FastAPI Gateway (unified entry for Web/IM/CLI)
│   ├── gateway/app.py                       # Gateway entry
│   ├── gateway/routers/{runs,threads,...}.py
│   └── channels/                            # IM channel adapters
│       ├── manager.py  service.py  message_bus.py  store.py
│       ├── feishu.py  slack.py  telegram.py  wechat.py
│       ├── wecom.py   dingtalk.py  discord.py
│       └── base.py    commands.py
├── langgraph.json                           # LangGraph Server graph registry
└── packages/harness/deerflow/               # Core harness library
    ├── agents/
    │   ├── lead_agent/{agent.py,prompt.py}  # Lead Agent factory + system prompt
    │   ├── memory/{storage,updater,queue,...}.py
    │   ├── middlewares/                     # ★ 18 middlewares
    │   └── thread_state.py
    ├── subagents/{executor,registry,config,token_collector}.py
    │             /builtins/{general_purpose,bash_agent}.py
    ├── sandbox/                             # Abstract Sandbox + LocalSandbox
    │   ├── sandbox.py  sandbox_provider.py
    │   └── local/local_sandbox_provider.py
    ├── community/aio_sandbox/               # Docker / K8s sandbox providers
    │   ├── aio_sandbox_provider.py
    │   ├── local_backend.py  remote_backend.py
    ├── skills/{installer,parser,storage,tool_policy,security_scanner,types}.py
    ├── mcp/{client,session_pool,cache,oauth,tools}.py
    ├── models/{factory,claude_provider,patched_openai,vllm_provider,...}.py
    ├── runtime/{checkpointer,events,runs,stream_bridge,store}.py
    ├── tools/builtins/{task_tool,setup_agent_tool,update_agent_tool,
    │                   clarification_tool,view_image_tool,tool_search.py}
    └── tracing/{factory,metadata}.py
skills/public/                               # 20+ built-in skills (filesystem layout)
├── github-deep-research/  skill-creator/  deep-research/
├── chart-visualization/   ppt-generation/  podcast-generation/
├── data-analysis/         image-generation/ video-generation/
├── frontend-design/  ...  claude-to-deerflow/
```

`langgraph.json` reveals a key design choice — deer-flow **only keeps LangGraph Studio compatibility**; the real runtime is embedded in its own FastAPI:

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "python_version": "3.12",
  "graphs": {
    "lead_agent": "deerflow.agents:make_lead_agent"
  },
  "auth": {"path": "./app/gateway/langgraph_auth.py:auth"},
  "checkpointer": {"path": "./packages/harness/deerflow/runtime/checkpointer/async_provider.py:make_checkpointer"}
}
```

**Lesson #0**: **A real Harness preserves the LangGraph-compatible surface but embeds the runtime inside its own FastAPI**, so it can wrap auth, CSRF, channel adaptation, and event logging around graph invocations.

## 3. Comparing with helixent — Same ReAct, Two Engineering Paths

| Dimension | helixent | deer-flow |
| :--- | :--- | :--- |
| Code size | ~10K lines of TS | ~100K lines Python + TS |
| Control flow | Hand-rolled `async function*`, 25 lines | LangGraph `create_agent` + 18 middlewares |
| Sub-agent | ❌ (roadmap) | ✅ first-class, with **concurrency cap + persistent event loop** |
| Sandbox | ❌ (bare Bun) | ✅ abstract SPI + local Docker + remote K8s |
| Memory | ❌ | ✅ **three-tier** (profile + history + facts) + mtime cache |
| IM channels | ❌ | ✅ Feishu/Slack/WeChat/WeCom/DingTalk/Telegram/Discord |
| MCP | ❌ | ✅ stdio/SSE/HTTP + **OAuth flow** |
| Observability | Basic logs | ✅ Langfuse + LangSmith + RunJournal |
| Safety | Simple approval | ✅ Loop Detection / Safety Finish / Dangling Tool |
| Learning curve | An evening | A week+ |

Reading deer-flow lets you see **what a production harness actually looks like**. We'll dissect it component by component.

## 4. Lead Agent — One LangGraph, Eighteen Middlewares

**Path**: `backend/packages/harness/deerflow/agents/lead_agent/agent.py`

deer-flow's LangGraph state machine is **not** a hand-drawn multi-node graph (that was v1). In **v2**, **there's only one graph**, built by `langchain.agents.create_agent(...)`, and what would traditionally be "nodes" are expressed as **`AgentMiddleware` subclasses wrapped around the model+tools loop**.

The module's top-of-file docstring spells out the key invariant:

```python
"""Lead agent factory.

INVARIANT — tracing callback placement
======================================

Tracing callbacks (Langfuse, LangSmith) are attached at the **graph
invocation root** in :func:`_make_lead_agent` (see the
``build_tracing_callbacks()`` block that appends to ``config["callbacks"]``).
Every ``create_chat_model(...)`` call inside this module — and inside any
middleware reachable from this graph (e.g. ``TitleMiddleware``) — MUST pass
``attach_tracing=False``.

Forgetting that flag emits duplicate spans (one rooted at the graph, one at
the model) AND prevents the Langfuse handler's ``propagate_attributes``
path from firing, so ``session_id`` / ``user_id`` never reach the trace.
"""
```

**Lesson #1**: This habit of **locking team-level invariants in docstrings** is a hallmark of industrial-grade codebases — burned once, written into the code, never burned again.

`_build_middlewares` is the recipe for the entire graph; each `middlewares.append(...)` call is effectively a LangGraph node:

```python
def _build_middlewares(config, model_name, agent_name=None, ...):
    resolved_app_config = app_config or get_app_config()
    middlewares = build_lead_runtime_middlewares(app_config=resolved_app_config, lazy_init=True)

    # Inject dynamic context (project structure, recent files, user prefs, etc.)
    middlewares.append(DynamicContextMiddleware(agent_name=agent_name, app_config=resolved_app_config))

    # Summarization middleware — engages early to reduce context for downstream processing
    summarization_middleware = _create_summarization_middleware(app_config=resolved_app_config)
    if summarization_middleware is not None:
        middlewares.append(summarization_middleware)

    # TODO list for plan mode
    cfg = _get_runtime_config(config)
    is_plan_mode = cfg.get("is_plan_mode", False)
    todo_list_middleware = _create_todo_list_middleware(is_plan_mode)
    if todo_list_middleware is not None:
        middlewares.append(todo_list_middleware)

    # Token usage tracking
    if resolved_app_config.token_usage.enabled:
        middlewares.append(TokenUsageMiddleware())

    # Auto-generate title (after first exchange)
    middlewares.append(TitleMiddleware(app_config=resolved_app_config))

    # Long-term memory queue (queue after the first turn)
    middlewares.append(MemoryMiddleware(agent_name=agent_name, memory_config=resolved_app_config.memory))

    # Vision model — inject image details into LLM input
    model_config = resolved_app_config.get_model_config(model_name) if model_name else None
    if model_config is not None and model_config.supports_vision:
        middlewares.append(ViewImageMiddleware())

    # Tool search (dynamically filter visible tools)
    if resolved_app_config.tool_search.enabled:
        middlewares.append(DeferredToolFilterMiddleware())

    # Sub-agent concurrency cap (matches the hard cap in the prompt)
    subagent_enabled = cfg.get("subagent_enabled", False)
    if subagent_enabled:
        max_concurrent_subagents = cfg.get("max_concurrent_subagents", 3)
        middlewares.append(SubagentLimitMiddleware(max_concurrent=max_concurrent_subagents))

    # Loop detection (core safety)
    loop_detection_config = resolved_app_config.loop_detection
    if loop_detection_config.enabled:
        middlewares.append(LoopDetectionMiddleware.from_config(loop_detection_config))

    # Slot for custom middleware
    if custom_middlewares:
        middlewares.extend(custom_middlewares)

    # Safety finish detection
    safety_config = resolved_app_config.safety_finish_reason
    if safety_config.enabled:
        middlewares.append(SafetyFinishReasonMiddleware.from_config(safety_config))

    # Clarification interception — must be last
    middlewares.append(ClarificationMiddleware())
    return middlewares
```

**Insertion order matters.** The comments above `_build_middlewares` explain why this ordering, one line at a time:

> - `ThreadDataMiddleware must be before SandboxMiddleware` — sandbox needs thread_id
> - `UploadsMiddleware should be after ThreadDataMiddleware` — uploads need thread_id to resolve paths
> - `DanglingToolCallMiddleware patches missing ToolMessages before model sees the history`
> - `SummarizationMiddleware should be early to reduce context before other processing`
> - `TodoListMiddleware should be before ClarificationMiddleware to allow todo management`
> - `TitleMiddleware generates title after first exchange`
> - `MemoryMiddleware queues conversation for memory update (after TitleMiddleware)`
> - `ViewImageMiddleware should be before ClarificationMiddleware to inject image details before LLM`
> - `ToolErrorHandlingMiddleware should be before ClarificationMiddleware to convert tool exceptions to ToolMessages`
> - `ClarificationMiddleware should be last to intercept clarification requests after model calls`

**Final graph creation**:

```python
return create_agent(
    model=create_chat_model(
        name=model_name, thinking_enabled=thinking_enabled,
        reasoning_effort=reasoning_effort,
        app_config=resolved_app_config,
        attach_tracing=False  # ← the invariant
    ),
    tools=filter_tools_by_skill_allowed_tools(tools + extra_tools, skills_for_tool_policy),
    middleware=_build_middlewares(config, ...),
    system_prompt=apply_prompt_template(
        subagent_enabled=subagent_enabled,
        max_concurrent_subagents=max_concurrent_subagents,
        agent_name=agent_name,
        available_skills=set(agent_config.skills) if agent_config else None,
        app_config=resolved_app_config,
    ),
    state_schema=ThreadState,
)
```

`ThreadState` is deer-flow's custom LangGraph state schema:

```python
class ThreadState(AgentState):
    messages: list[BaseMessage]
    sandbox: dict             # sandbox environment info
    artifacts: list[str]      # generated file paths
    thread_data: dict         # {workspace, uploads, outputs} paths
    title: str | None         # auto-generated conversation title
    todos: list[dict]         # task tracking (Plan mode)
    viewed_images: dict       # image data the vision model has read
```

**Lesson #2 (core)**: deer-flow replaces the traditional "nodes + edges" graph with **"middleware-as-node."** **Each middleware owns one cross-cutting concern** (thread state, summarization, vision, clarification, loop detection, safety finish, sub-agent budget, token usage, tracing…). This is v2's most important architectural shift, **letting the Harness stay LangGraph-compatible while becoming composable.**

## 5. The Lead Agent's System Prompt — Encode the Protocol in the Prompt

**Path**: `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`

The system prompt isn't a static file — it's **built per request**. The most interesting part is `_build_subagent_section`, which **bakes the hard concurrency limit + batch-execution protocol directly into the prompt**:

```python
return f"""<subagent_system>
**🚀 SUBAGENT MODE ACTIVE - DECOMPOSE, DELEGATE, SYNTHESIZE**

You are running with subagent capabilities enabled. Your role is to be a **task orchestrator**:
1. **DECOMPOSE**: Break complex tasks into parallel sub-tasks
2. **DELEGATE**: Launch multiple subagents simultaneously using parallel `task` calls
3. **SYNTHESIZE**: Collect and integrate results into a coherent answer

**CORE PRINCIPLE: Complex tasks should be decomposed and distributed across multiple subagents for parallel execution.**

**⛔ HARD CONCURRENCY LIMIT: MAXIMUM {n} `task` CALLS PER RESPONSE. THIS IS NOT OPTIONAL.**
- Each response, you may include **at most {n}** `task` tool calls. Any excess calls are
  **silently discarded** by the system — you will lose that work.
- **Before launching subagents, you MUST count your sub-tasks in your thinking:**
  - If count ≤ {n}: Launch all in this response.
  - If count > {n}: **Pick the {n} most important/foundational sub-tasks for this turn.**
    Save the rest for the next turn.
"""
```

This isn't decoration — the same `max_concurrent` value is **deterministically enforced by `SubagentLimitMiddleware`**.

**Lesson #3 (core)**: **Prompt and middleware reinforce each other** — the prompt teaches the LLM the contract; the middleware **deterministically enforces** it. **Documentation lives in code, not in a wiki.** This is a hallmark of industrial-grade agent engineering.

## 6. Sub-Agent Scheduling — task_tool + SubagentExecutor

The Lead Agent doesn't create sub-agents itself — it schedules them indirectly via the **`task` tool**:

```python
@tool("task", parse_docstring=True)
async def task_tool(
    runtime: Runtime,
    description: str,
    prompt: str,
    subagent_type: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> str:
    """Delegate a task to a specialized subagent that runs in its own context.

    Built-in subagent types:
    - **general-purpose**: A capable agent for complex, multi-step tasks ...
    - **bash**: Command execution specialist for running bash commands. ...

    Args:
        description: A short (3-5 word) description of the task ...
                     **ALWAYS PROVIDE THIS PARAMETER FIRST.**
        prompt: The task description for the subagent ...
                **ALWAYS PROVIDE THIS PARAMETER SECOND.**
        subagent_type: The type of subagent to use.
                       **ALWAYS PROVIDE THIS PARAMETER THIRD.**
    """
```

Note the "FIRST/SECOND/THIRD" **ordinal hints** in the parameter descriptions — a practical technique to **defend against LLMs swapping positional arguments**.

### 6.1 SubagentRegistry — Three-Layer Resolution

```python
def get_subagent_config(name: str, *, app_config=None) -> SubagentConfig | None:
    """
    Resolution order (mirrors Codex's config layering):
    1. Built-in subagents (general-purpose, bash)
    2. Custom subagents from config.yaml custom_agents section
    3. Per-agent overrides from config.yaml agents section (timeout, max_turns, model, skills)
    """
```

The built-in `bash` sub-agent's config:

```python
BASH_AGENT_CONFIG = SubagentConfig(
    name="bash",
    description="""Command execution specialist for running bash commands in a separate context. ...""",
    system_prompt="""You are a bash command execution specialist. ...""",
    tools=["bash", "ls", "read_file", "write_file", "str_replace"],
    disallowed_tools=["task", "ask_clarification", "present_files"],
    model="inherit",
    max_turns=60,
)
```

**`disallowed_tools=["task", ...]`** is a key design — sub-agents are **explicitly forbidden** to spawn grand-children. **Runaway recursion is killed at the config layer.**

### 6.2 SubagentExecutor — Heavy-Duty Concurrency Primitives

`subagents/executor.py` is one of deer-flow's most complex and most copy-worthy files. Highlights:

**(A) A persistent isolated event loop** — used when the executor is invoked from a sync API while a parent loop is already running:

```python
# Persistent event loop for isolated subagent executions triggered from an
# already-running parent loop. Reusing one long-lived loop avoids creating a
# fresh loop per execution and then closing async resources bound to it.
_isolated_subagent_loop: asyncio.AbstractEventLoop | None = None
_isolated_subagent_loop_thread: threading.Thread | None = None
_isolated_subagent_loop_started: threading.Event | None = None
_isolated_subagent_loop_lock = threading.Lock()
```

That comment **is itself a production-incident postmortem** — any developer who's debugged "RuntimeError: this event loop is closed" or "loop already running" will recognize it instantly.

**(B) Race-safe terminal-state transitions** — tasks may be cancelled, timed-out, or completed concurrently:

```python
def try_set_terminal(self, status, *, result=None, error=None,
                     completed_at=None, ai_messages=None,
                     token_usage_records=None) -> bool:
    """Set a terminal status exactly once.

    Background timeout/cancellation and the execution worker can race on the
    same result holder. The first terminal transition wins; late terminal
    writes must not change status or payload fields.
    """
    if not status.is_terminal:
        raise ValueError(f"Status {status} is not terminal")
    with self._state_lock:
        if self.status.is_terminal:
            return False
        # ... write status / result / error
```

**Lesson #4**: `try_set_terminal` + `_state_lock` gives you a **monotone, idempotent state machine**. A race-free state machine = reliable cancellation semantics.

**(C) Streaming + cooperative cancellation**:

```python
async for chunk in agent.astream(state, config=run_config, context=context, stream_mode="values"):
    if result.cancel_event.is_set():
        logger.info(f"[trace={self.trace_id}] Subagent {self.config.name} cancelled by parent")
        result.try_set_terminal(
            SubagentStatus.CANCELLED,
            error="Cancelled by user",
            token_usage_records=collector.snapshot_records(),
        )
        return result
    final_state = chunk
    messages = chunk.get("messages", [])
    if messages:
        last_message = messages[-1]
        if isinstance(last_message, AIMessage):
            message_dict = last_message.model_dump()
            message_id = message_dict.get("id")
            is_duplicate = False
            if message_id:
                is_duplicate = any(msg.get("id") == message_id for msg in ai_messages)
            else:
                is_duplicate = message_dict in ai_messages
            if not is_duplicate:
                ai_messages.append(message_dict)
```

The sub-agent streams while the parent dedupes-by-message-id as it collects.

## 7. Sandbox — Two Providers, One Abstraction

### 7.1 Abstract Sandbox

```python
class Sandbox(ABC):
    @abstractmethod
    def execute_command(self, command: str) -> str: ...
    @abstractmethod
    def read_file(self, path: str) -> str: ...
    @abstractmethod
    def download_file(self, path: str) -> bytes: ...
    @abstractmethod
    def list_dir(self, path: str, max_depth=2) -> list[str]: ...
    @abstractmethod
    def write_file(self, path: str, content: str, append: bool = False) -> None: ...
    @abstractmethod
    def glob(self, path: str, pattern: str, *,
             include_dirs: bool = False, max_results: int = 200) -> tuple[list[str], bool]: ...
    @abstractmethod
    def grep(self, path: str, pattern: str, *,
             glob: str | None = None, literal: bool = False,
             case_sensitive: bool = False, max_results: int = 100) -> tuple[list[GrepMatch], bool]: ...
    @abstractmethod
    def update_file(self, path: str, content: bytes) -> None: ...
```

### 7.2 SandboxProvider — Loaded by Reflection

```python
class SandboxProvider(ABC):
    uses_thread_data_mounts: bool = False
    needs_upload_permission_adjustment: bool = True

    @abstractmethod
    def acquire(self, thread_id: str | None = None) -> str: ...

    async def acquire_async(self, thread_id: str | None = None) -> str:
        """Async runtimes should call this so blocking ops run in a worker
        thread instead of stalling the event loop."""
        return await asyncio.to_thread(self.acquire, thread_id)

    @abstractmethod
    def get(self, sandbox_id: str) -> Sandbox | None: ...
    @abstractmethod
    def release(self, sandbox_id: str) -> None: ...
    def reset(self) -> None: ...


def get_sandbox_provider(**kwargs) -> SandboxProvider:
    global _default_sandbox_provider
    if _default_sandbox_provider is None:
        config = get_app_config()
        cls = resolve_class(config.sandbox.use, SandboxProvider)  # ← reflection by string
        _default_sandbox_provider = cls(**kwargs)
    return _default_sandbox_provider
```

So in `config.yaml`:

```yaml
sandbox:
  use: "deerflow.community.aio_sandbox:AioSandboxProvider"
```

**reflection-loads** a completely different implementation. A textbook demonstration of the SPI (Service Provider Interface) pattern.

### 7.3 AioSandboxProvider — Production-Grade Composition

It **composes a swappable backend** (`LocalContainerBackend` vs `RemoteSandboxBackend`):

```python
class AioSandboxProvider(SandboxProvider):
    """Sandbox provider that manages containers running the AIO sandbox.

    Architecture:
        This provider composes a SandboxBackend (how to provision), enabling:
        - Local Docker/Apple Container mode (auto-start containers)
        - Remote/K8s mode (connect to pre-existing sandbox URL)
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._sandboxes: dict[str, AioSandbox] = {}
        self._sandbox_infos: dict[str, SandboxInfo] = {}
        self._thread_sandboxes: dict[str, str] = {}
        self._thread_locks: dict[str, threading.Lock] = {}
        self._last_activity: dict[str, float] = {}

        # ★ Warm pool: released sandboxes whose containers are still alive, for fast re-acquire
        self._warm_pool: dict[str, tuple[SandboxInfo, float]] = {}

        self._shutdown_called = False
        self._backend: SandboxBackend = self._create_backend()
        atexit.register(self.shutdown)
        self._register_signal_handlers()

        # ★ At startup, adopt orphan containers left over from a prior process
        self._reconcile_orphans()

        # ★ Background thread: evict sandboxes idle longer than idle_timeout
        if self._config.get("idle_timeout", DEFAULT_IDLE_TIMEOUT) > 0:
            self._start_idle_checker()
```

**Three production features**:
1. **Warm pool** — containers kept alive for a while after release; re-acquisition is near-instant.
2. **`_reconcile_orphans()`** — at startup, find leftover containers from the previous process; adopt or kill.
3. **Idle checker thread** — auto-evict after `idle_timeout` (default 600s).

### 7.4 Virtual Path Mapping

Both providers obey the **virtual path** convention:

| Virtual path | Physical path |
| :--- | :--- |
| `/mnt/user-data/workspace` | `backend/.deer-flow/threads/{thread_id}/user-data/workspace` |
| `/mnt/user-data/uploads`   | `backend/.deer-flow/threads/{thread_id}/user-data/uploads` |
| `/mnt/user-data/outputs`   | `backend/.deer-flow/threads/{thread_id}/user-data/outputs` |
| `/mnt/skills`              | `deer-flow/skills/` |

**Lesson #5**: Classic SPI design — the agent code only sees virtual paths + the abstract `Sandbox` API. **Dev runs LocalSandboxProvider** (local dirs); **prod runs AioSandboxProvider** (K8s). The agent code doesn't change a line.

## 8. Memory — Three Tiers, Cached, Isolated Per User

Unlike many frameworks that just hand you an empty dict to fill arbitrarily, deer-flow's memory **enforces a three-tier schema** (profile / history / facts):

```python
def create_empty_memory() -> dict[str, Any]:
    return {
        "version": "1.0",
        "lastUpdated": utc_now_iso_z(),
        "user": {
            "workContext":     {"summary": "", "updatedAt": ""},
            "personalContext": {"summary": "", "updatedAt": ""},
            "topOfMind":       {"summary": "", "updatedAt": ""},
        },
        "history": {
            "recentMonths":      {"summary": "", "updatedAt": ""},
            "earlierContext":    {"summary": "", "updatedAt": ""},
            "longTermBackground":{"summary": "", "updatedAt": ""},
        },
        "facts": [],
    }
```

This is **even more granular** than Anthropic's "profile + episodes + knowledge" in *Context Engineering*. `workContext` vs `personalContext` reflects ByteDance's real ToB customer needs: work memory must strictly not pollute personal preferences.

**Storage** implements the `MemoryStorage` ABC. The default file backend uses **mtime-based caching** and is **isolated by `(user_id, agent_name)` tuples**:

```python
class FileMemoryStorage(MemoryStorage):
    def __init__(self):
        # cache key: (user_id, agent_name); value: (memory_data, file_mtime)
        self._memory_cache: dict[tuple[str | None, str | None],
                                 tuple[dict[str, Any], float | None]] = {}
        self._cache_lock = threading.Lock()

    def save(self, memory_data, agent_name=None, *, user_id=None) -> bool:
        memory_data = {**memory_data, "lastUpdated": utc_now_iso_z()}
        temp_path = file_path.with_suffix(f".{uuid.uuid4().hex}.tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(memory_data, f, indent=2, ensure_ascii=False)
        temp_path.replace(file_path)  # ← atomic rename
```

**Lesson #6**: `temp_path.replace(file_path)` is **atomic rename** — the classic crash-safe write pattern. Even if the process crashes mid-write, the file on disk is either old or new — **never half-written**.

The **updater** uses a dedicated synchronous thread pool to avoid cross-event-loop contamination:

```python
# Thread pool for offloading sync memory updates when called from an async
# context. Unlike the previous asyncio.run() approach, this runs *sync*
# model.invoke() calls — no event loop is created, so the langchain async
# httpx client pool (globally cached via @lru_cache) is never touched and
# cross-loop connection reuse is impossible.
_SYNC_MEMORY_UPDATER_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=4, thread_name_prefix="memory-updater-sync",
)
atexit.register(lambda: _SYNC_MEMORY_UPDATER_EXECUTOR.shutdown(wait=False))
```

This comment is **another debugging epic** — anyone tortured by "RuntimeError: this event loop is closed" will resonate immediately.

## 9. Skills — A Filesystem-Native Plugin Format

The directory structure of `skills/public/github-deep-research/`:

```
github-deep-research/
├── SKILL.md
├── assets/report_template.md
└── scripts/github_api.py
```

`SKILL.md` is **YAML frontmatter + Markdown**, parsed by the harness:

```markdown
---
name: github-deep-research
description: Conduct multi-round deep research on any GitHub Repo. Use when users
  request comprehensive analysis, timeline reconstruction, competitive analysis,
  or in-depth investigation of GitHub. Produces structured markdown reports with
  executive summaries, chronological timelines, metrics analysis, and Mermaid
  diagrams. Triggers on Github repository URL or open source projects.
---

# GitHub Deep Research Skill

Multi-round research combining GitHub API, web_search, web_fetch to produce
comprehensive markdown reports.

## Research Workflow
- Round 1: GitHub API
- Round 2: Discovery
- Round 3: Deep Investigation
- Round 4: Deep Dive
```

`scripts/github_api.py` is an **executable script** that the agent runs directly in the sandbox:

```python
#!/usr/bin/env python3
"""GitHub API client for deep research."""
try:
    import requests
except ImportError:
    # ★ The sandbox may not have `requests`; provide a urllib fallback
    import urllib.error
    import urllib.request
    class RequestsFallback: ...
    requests = RequestsFallback()

class GitHubAPI:
    BASE_URL = "https://api.github.com"
    def __init__(self, token: Optional[str] = None):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Deep-Research-Bot/1.0",
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
    ...
```

Notice `RequestsFallback` — **skill authors cannot assume the sandbox has `requests`**, so they package a `urllib` fallback. **This is the standard design pattern for distributable skills.**

The 20+ built-in skills include: `chart-visualization` (full Antv suite of charts + 25+ reference templates), `skill-creator` (a **meta-skill that generates new skills**, with a built-in HTML eval viewer), `frontend-design`, `ppt-generation`, `podcast-generation`, `image-generation`, `video-generation`, `systematic-literature-review`, `claude-to-deerflow` (**auto-converts Claude Code skills**), and more.

**Skills are exposed to the LLM via tool gating**:

```python
skills_for_tool_policy = _load_enabled_skills_for_tool_policy(available_skills, app_config=resolved_app_config)
tools = filter_tools_by_skill_allowed_tools(tools + extra_tools, skills_for_tool_policy)
```

Each skill can declare `allowed_tools`; `filter_tools_by_skill_allowed_tools` removes tools not in the allow-list from the skill's view. **Same pattern as Claude Code.**

## 10. Message Gateway — Seven IMs, One Unified Entry

`backend/app/channels/` is the core of deer-flow's multi-channel integration. A short registry:

```python
_CHANNEL_REGISTRY: dict[str, str] = {
    "dingtalk": "app.channels.dingtalk:DingTalkChannel",
    "discord":  "app.channels.discord:DiscordChannel",
    "feishu":   "app.channels.feishu:FeishuChannel",
    "slack":    "app.channels.slack:SlackChannel",
    "telegram": "app.channels.telegram:TelegramChannel",
    "wechat":   "app.channels.wechat:WechatChannel",
    "wecom":    "app.channels.wecom:WeComChannel",
}

_CHANNEL_CREDENTIAL_KEYS: dict[str, list[str]] = {
    "dingtalk": ["client_id", "client_secret"],
    "discord":  ["bot_token"],
    "feishu":   ["app_id", "app_secret"],
    "slack":    ["bot_token", "app_token"],
    "telegram": ["bot_token"],
    "wecom":    ["bot_id", "bot_secret"],
    "wechat":   ["bot_token"],
}
```

Each channel implements the `Channel` ABC, pushes inbound events to the `MessageBus`, and `ChannelManager` forwards to the same Gateway endpoint as the Web UI:

```python
class ChannelManager:
    """ChannelManager — consumes inbound messages and dispatches them to
    the DeerFlow agent via Gateway."""

    DEFAULT_LANGGRAPH_URL = "http://localhost:8001/api"
    DEFAULT_GATEWAY_URL   = "http://localhost:8001"
    DEFAULT_ASSISTANT_ID  = "lead_agent"
    DEFAULT_RUN_CONFIG: dict[str, Any] = {"recursion_limit": 100}
    DEFAULT_RUN_CONTEXT: dict[str, Any] = {
        "thinking_enabled": True,
        "is_plan_mode":     False,
        "subagent_enabled": False,
    }

    # ★ Whether each channel supports streaming
    CHANNEL_CAPABILITIES = {
        "dingtalk": {"supports_streaming": False},
        "discord":  {"supports_streaming": False},
        "feishu":   {"supports_streaming": True},
        "slack":    {"supports_streaming": False},
        "telegram": {"supports_streaming": False},
        "wechat":   {"supports_streaming": False},
        "wecom":    {"supports_streaming": True},
    }
```

Two constants worth copying:

```python
STREAM_UPDATE_MIN_INTERVAL_SECONDS = 0.35
THREAD_BUSY_MESSAGE = "This conversation is already processing another request. " \
                      "Please wait for it to finish and try again."
```

— **350ms streaming throttle** and a **per-thread busy message**. Two UX guard-rails every production agent must have.

**Lesson #7**: **All IMs fold into one Gateway endpoint.** Each channel just translates protocol-specific webhooks into an `InboundMessage`. This is the textbook pattern for omnichannel bots — **Slack/Feishu/WeChat/Telegram coexist while the agent runtime doesn't change a line.**

## 11. MCP Integration — Production Implementation with OAuth Flow

deer-flow uses `langchain-mcp-adapters` as the protocol library, **layering on its own session pool, cache, and OAuth handler**. Transport-agnostic config building:

```python
def build_server_params(server_name: str, config: McpServerConfig) -> dict[str, Any]:
    transport_type = config.type or "stdio"
    params: dict[str, Any] = {"transport": transport_type}
    if transport_type == "stdio":
        if not config.command:
            raise ValueError(f"MCP server '{server_name}' with stdio transport requires 'command' field")
        params["command"] = config.command
        params["args"] = config.args
        if config.env:
            params["env"] = config.env
    elif transport_type in ("sse", "http"):
        if not config.url:
            raise ValueError(f"MCP server '{server_name}' with {transport_type} transport requires 'url' field")
        params["url"] = config.url
        if config.headers:
            params["headers"] = config.headers
    else:
        raise ValueError(f"unsupported transport type: {transport_type}")
    return params
```

Companion files:
- `mcp/session_pool.py` — **keeps MCP sessions warm across runs**
- `mcp/oauth.py` — **`client_credentials` + `refresh_token` flows** layered on top of MCP HTTP/SSE
- `mcp/cache.py` — tool metadata cache

**Lesson #8**: Layering **auth flows + connection pooling** on top of a standard protocol (MCP) is the standard technique for taking a community protocol to enterprise grade.

## 12. Loop Detection — a Production Safety Pattern Worth Copying

The docstring of `agents/middlewares/loop_detection_middleware.py` is an engineering lesson in itself:

```python
"""Middleware to detect and break repetitive tool call loops.

P0 safety: prevents the agent from calling the same tool with the same
arguments indefinitely until the recursion limit kills the run.

Detection strategy:
  1. After each model response, hash the tool calls (name + args).
  2. Track recent hashes in a sliding window.
  3. If the same hash appears >= warn_threshold times, queue a
     "you are repeating yourself — wrap up" warning ...
  4. If it appears >= hard_limit times, strip all tool_calls from the
     response so the agent is forced to produce a final text answer.

Why the warning is injected at ``wrap_model_call`` instead of
``after_model``:

  ``after_model`` fires immediately after the model emits an
  ``AIMessage`` that may carry ``tool_calls``. The tools node has not
  run yet, so no matching ``ToolMessage`` exists in the history. Any
  message we add here lands *between* the assistant's tool_calls and
  their responses. OpenAI/Moonshot reject the next request with
  ``"tool_call_ids did not have response messages"`` ... Anthropic also
  disallows mid-stream ``SystemMessage``. By deferring the warning to
  ``wrap_model_call``, every prior ToolMessage is already present in
  the request's message list and the warning is appended at the end —
  pairing intact, no ``AIMessage`` semantics are mutated.
"""
```

**This is a full production-incident postmortem.**

Default thresholds:

```python
_DEFAULT_WARN_THRESHOLD = 3   # warn after 3 identical calls
_DEFAULT_HARD_LIMIT     = 5   # force-end after 5 identical calls
_DEFAULT_WINDOW_SIZE    = 20  # track the last N tool calls
_DEFAULT_MAX_TRACKED_THREADS = 100
_DEFAULT_TOOL_FREQ_WARN       = 30
_DEFAULT_TOOL_FREQ_HARD_LIMIT = 50
```

The clever bit is `_stable_tool_key` — it **buckets `read_file`'s line ranges**:

```python
if name == "read_file" and fallback_key is None:
    path = args.get("path") or ""
    start_line = args.get("start_line")
    end_line = args.get("end_line")
    bucket_size = 200
    start_line, end_line = sorted((start_line, end_line))
    bucket_start = max(start_line, 1)
    bucket_end = max(end_line, 1)
    bucket_start = (bucket_start - 1) // bucket_size
    bucket_end = (bucket_end - 1) // bucket_size
```

This means an agent repeatedly reading "nearby line ranges" of the same file (a classic dead-loop pattern: jumping around the same region 7 times in a row) will be **detected as the same call** — it can't escape detection by tweaking the line numbers slightly.

**Lesson #9**: You **only think of details like this after running production agents for thousands of hours**. Bottling such experience into default config = solidifying team knowledge in code.

## 13. Other Production Patterns Worth Capturing

A non-exhaustive list:

- **`SafetyFinishReasonMiddleware`** — when a provider terminates for safety reasons, suppress subsequent tool execution.
- **`DanglingToolCallMiddleware`** — auto-patches missing `ToolMessage` entries in history (multi-turn dialogue won't crash because of this).
- **`TokenUsageMiddleware` + `SubagentTokenCollector`** — aggregate tokens across lead + sub-agents; publish via SSE.
- **`RunJournal`** — append-only log with three pluggable storages: `db.py` / `jsonl.py` / `memory.py`.
- **Checkpointer SPI** — registered with LangGraph for crash recovery.
- **`tracing/factory.py:build_tracing_callbacks`** — single integration point for Langfuse + LangSmith.
- **`patched_openai.py`, `patched_deepseek.py`, `patched_minimax.py`** — provider-specific shims that fix LangChain bugs **without forking**.
- **`security_scanner.py`** — scans skills for unsafe shell patterns before install (**LLM supply-chain defense**).
- **`subagents/executor.py` `_THREAD_LOCK_EXECUTOR`** — a bounded thread pool that makes blocking lock acquisition async-safe.

## 14. The Three Most Copy-Worthy Designs

> **If you only remember three things from this section**, remember these.

### Design 1 · Middleware-as-Node
Don't hand-draw a star-shaped state machine — **wrap a tool loop in 18 middlewares**. Each middleware owns one cross-cutting concern. This makes the Harness **composable** — want to add a new capability? Write a new middleware, append it to the `_build_middlewares` list, **don't touch the core**.

### Design 2 · Three-Layer Sandbox-Provider-Backend SPI
**Abstract `Sandbox` → `SandboxProvider` lifecycle → swappable `SandboxBackend`** (local container vs. remote K8s). A YAML string `deerflow.community.aio_sandbox:AioSandboxProvider` **reflection-loads a completely different implementation**. One of the **cleanest pluggable patterns in open-source agent code**.

### Design 3 · Double Guardrail of Prompt + Middleware
The Lead Agent prompt **teaches the LLM the contract** ("at most N concurrent `task` calls"); `SubagentLimitMiddleware` **deterministically enforces** it. Documentation lives in code. **You'll be grateful you did it this way when the 7th teammate onboards.**

---

## 15. deer-flow vs helixent Comparison Table (Ultimate Edition)

| Dimension | bytedance/deer-flow 2.0 | helixent |
| :--- | :--- | :--- |
| **Origin & lineage** | Open-sourced by ByteDance; v2 is a ground-up rewrite (2026-02); v1 was a research pipeline with named nodes | Original work, no predecessor |
| **Core graph model** | One LangGraph (`create_agent`) + 18 `AgentMiddleware`s. "Nodes" = middlewares | Hand-rolled node-edge state machine; easy to visualize, weaker orthogonality of extension |
| **Sub-agent model** | First-class `task` tool + `SubagentExecutor` with **persistent isolated event loop, race-safe terminal state, cooperative cancellation, token rollup**. Hard concurrency cap **double-enforced** (prompt + middleware) | Usually modeled as a graph node; cancellation / token rollup needs custom code |
| **Sandbox abstraction** | `Sandbox` + `SandboxProvider` SPI; two production providers; the latter switches between local Docker / remote K8s; **warm pool, orphan adoption, idle eviction** | Usually single execution backend (local Python / subprocess); no warm pool |
| **Skills format** | Filesystem-native: `SKILL.md` (YAML frontmatter) + `scripts/` + `references/` + `templates/` + optional `evals/`. Mounted at `/mnt/skills`. **Compatible with Claude Code format** (see `claude-to-deerflow` skill) | Skills usually in-process Python modules; weaker portability |
| **Memory** | Fixed 3-tier schema (`user.{workContext, personalContext, topOfMind}` + `history.{recentMonths, earlierContext, longTermBackground}` + `facts[]`); file backend, **mtime cache**, isolated by `(user_id, agent_name)`, **atomic-rename writes** | Usually vector store or unstructured KV; lacks "profile + episodes + knowledge" governance |
| **Channels / Gateway** | Seven IM channels (Feishu/Slack/WeChat/WeCom/DingTalk/Telegram/Discord) all folded into a single Gateway `/api/threads/{id}/runs` endpoint. Per-channel streaming-capability matrix, 350ms streaming throttle | Usually CLI / Web only |
| **MCP** | Native `langchain-mcp-adapters` + DeerFlow `session_pool`, `cache`, **OAuth (client_credentials + refresh_token)**. stdio/SSE/HTTP all supported | Usually stdio-only; OAuth flow is rare |
| **Production safety** | Dedicated middlewares: loop detection (with `read_file` line-number bucketing), safety finish reason, dangling tool calls, token usage, sub-agent budget, summarization, safety finish detector. **Every one with testable config knobs** | Usually relies on `recursion_limit` and ad-hoc retries; no equivalent of `LoopDetectionMiddleware` |
| **Observability** | **Single callback injection point** (see §4 invariant); single factory for Langfuse + LangSmith; `RunJournal` event store with three backends (db / jsonl / memory) | Logs by default; tracing is a one-off integration |
| **Multi-user / auth** | Gateway with JWT + SQLite auth, CSRF middleware, **per-user paths**, per-user-isolated memory and skills, internal auth header between channels and gateway | Usually a single-user dev tool |

## 16. Three Takeaways for the Reader of This Chapter

After reading helixent + deer-flow, you should understand three things:

**1. The core ~25 lines of ReAct don't change.** Whether it's helixent's `async function*` or the tool loop wrapped by LangGraph in deer-flow, the essence is the "think → act → observe" loop. The differences are around it.

**2. "Middleware-as-Node" is the key architecture of the v2 era.** It lets the Harness keep a schedulable graph **while making cross-cutting concerns composable**. Each added production capability (memory, loop detection, safety finish) = one new middleware = one line appended.

**3. SPI is the hallmark of an industrial-grade Harness.** Sandbox, memory storage, sub-agent registry, skill sources — deer-flow turns every swap-prone point into a "config-loaded class." This is **a rarely-seen, directly-copy-into-your-own-system pure design pattern** in open-source code.

---

Next: [§3.5 Hands-on Lab →](./05-build-your-own.md)
