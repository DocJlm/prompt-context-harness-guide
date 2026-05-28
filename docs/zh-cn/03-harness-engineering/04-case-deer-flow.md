---
title: §3.4 案例 · deer-flow
description: 字节跳动开源的 SuperAgent Harness — 一份工业级 Harness 全栈剖析
---

# §3.4 案例 · deer-flow — 工业级 Harness 长什么样

> "DeerFlow is an open-source long-horizon **super agent harness** that orchestrates **sub-agents**, **memory**, and **sandboxes** to do almost anything — powered by **extensible skills**."  
> — [github.com/bytedance/deer-flow](https://github.com/bytedance/deer-flow) · README L14–17

**deer-flow**（Deep Exploration and Efficient Research Flow）由字节跳动开源，**2026 年 2 月 v2.0 发布后 48 小时内 GitHub Star 暴涨到 47k+**，短暂登顶 Trending #1。v2.0 是一次**完全重写** —— 和 v1.0（早期 LangManus deep research framework）几乎不共享代码。本节讨论的都是 v2.0。

如果 helixent 是"乐高 Technic 基础件"，**deer-flow 就是"出厂即跑的成品车"**。它给出了 helixent 故意没做的所有东西的工业级答案：**子 Agent 调度、Docker 沙箱、长期记忆、可观测性、多 IM 渠道、MCP、安全终止**。**两者解决不同问题，都值得读**。

## 一、项目自画像

| 维度 | deer-flow v2.0 |
| :--- | :--- |
| **主语言** | Python 73% + TypeScript 15% |
| **核心框架** | **LangGraph + LangChain**，但是关键创新是**用 18 个 Middleware 替代 LangGraph 节点** |
| **形态** | Monorepo: backend / frontend / skills / docker |
| **特性** | Sub-agent · Sandbox · Memory · 7 IM 渠道 · MCP（含 OAuth）· Loop Detection · Tracing |
| **典型部署** | Nginx (2026) + Gateway (8001) + Frontend (3000) + Provisioner (K8s 沙箱) |

## 二、仓库地形

通过 `gh api repos/bytedance/deer-flow/git/trees/main?recursive=1` 抽出的**最承重路径**：

```
backend/
├── app/                                     # FastAPI Gateway（Web/IM/CLI 统一入口）
│   ├── gateway/app.py                       # Gateway 入口
│   ├── gateway/routers/{runs,threads,...}.py
│   └── channels/                            # IM 渠道适配
│       ├── manager.py  service.py  message_bus.py  store.py
│       ├── feishu.py  slack.py  telegram.py  wechat.py
│       ├── wecom.py   dingtalk.py  discord.py
│       └── base.py    commands.py
├── langgraph.json                           # LangGraph Server 图注册
└── packages/harness/deerflow/               # 核心 harness 库
    ├── agents/
    │   ├── lead_agent/{agent.py,prompt.py}  # Lead Agent 工厂 + 系统提示词
    │   ├── memory/{storage,updater,queue,...}.py
    │   ├── middlewares/                     # ★ 18 个中间件
    │   └── thread_state.py
    ├── subagents/{executor,registry,config,token_collector}.py
    │             /builtins/{general_purpose,bash_agent}.py
    ├── sandbox/                             # 抽象 Sandbox + LocalSandbox
    │   ├── sandbox.py  sandbox_provider.py
    │   └── local/local_sandbox_provider.py
    ├── community/aio_sandbox/               # Docker / K8s 沙箱提供者
    │   ├── aio_sandbox_provider.py
    │   ├── local_backend.py  remote_backend.py
    ├── skills/{installer,parser,storage,tool_policy,security_scanner,types}.py
    ├── mcp/{client,session_pool,cache,oauth,tools}.py
    ├── models/{factory,claude_provider,patched_openai,vllm_provider,...}.py
    ├── runtime/{checkpointer,events,runs,stream_bridge,store}.py
    ├── tools/builtins/{task_tool,setup_agent_tool,update_agent_tool,
    │                   clarification_tool,view_image_tool,tool_search.py}
    └── tracing/{factory,metadata}.py
skills/public/                               # 20+ 内置技能（文件系统布局）
├── github-deep-research/  skill-creator/  deep-research/
├── chart-visualization/   ppt-generation/  podcast-generation/
├── data-analysis/         image-generation/ video-generation/
├── frontend-design/  ...  claude-to-deerflow/
```

`langgraph.json` 暴露了一个关键设计选择 —— deer-flow **仅保留 LangGraph Studio 兼容性**，真正的 runtime 嵌入在自己的 FastAPI 里：

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

**教学点 #0**：**一个真正的 Harness 保留 LangGraph 兼容表面，但把 runtime 嵌进自家 FastAPI**，以便在图调用周围加 auth、CSRF、渠道适配、事件日志。

## 三、与 helixent 的对比 —— 同一个 ReAct，两条工程路径

| 维度 | helixent | deer-flow |
| :--- | :--- | :--- |
| 代码规模 | ~1 万行 TS | ~10 万行 Python + TS |
| 控制流 | 手写 `async function*` 25 行 | LangGraph `create_agent` + 18 个 middleware |
| Sub-agent | ❌（roadmap）| ✅ 一等公民，含**并发限制 + 持久事件循环** |
| 沙箱 | ❌（裸跑 Bun）| ✅ 抽象 SPI + 本地 Docker + 远程 K8s |
| 记忆 | ❌ | ✅ **三层**（profile + history + facts）+ mtime 缓存 |
| IM 渠道 | ❌ | ✅ 飞书/Slack/微信/企微/钉钉/Telegram/Discord |
| MCP | ❌ | ✅ stdio/SSE/HTTP + **OAuth 流** |
| 观测性 | 基础日志 | ✅ Langfuse + LangSmith + RunJournal |
| 安全 | 简单 approval | ✅ Loop Detection / Safety Finish / Dangling Tool |
| 学习曲线 | 一晚 | 一周+ |

读 deer-flow，你能看到**生产 Harness 真实长什么样**。下面我们逐组件拆。

## 四、Lead Agent — 一张 LangGraph，十八条 Middleware

**Path**: `backend/packages/harness/deerflow/agents/lead_agent/agent.py`

deer-flow 的 LangGraph 状态机**不是**手工绘制的多节点图（那是 v1）。在 **v2** 里，**只有一张图**，由 `langchain.agents.create_agent(...)` 构建，传统意义上的"节点"被表达为**包在 model+tools 循环外的 `AgentMiddleware` 子类**。

模块开头的 docstring 道出关键不变量：

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

**教学点 #1**：这种**用 docstring 锁住团队级别不变量**的做法是工业级代码库的标志 —— 一次踩坑、写进代码、未来不再踩。

`_build_middlewares` 是整张图的"配方"，每个 `middlewares.append(...)` 调用都相当于一个 LangGraph 节点：

```python
def _build_middlewares(config, model_name, agent_name=None, ...):
    resolved_app_config = app_config or get_app_config()
    middlewares = build_lead_runtime_middlewares(app_config=resolved_app_config, lazy_init=True)

    # 注入动态上下文（项目结构、最近文件、用户偏好等）
    middlewares.append(DynamicContextMiddleware(agent_name=agent_name, app_config=resolved_app_config))

    # 摘要中间件 —— 早期介入以减少后续处理的上下文
    summarization_middleware = _create_summarization_middleware(app_config=resolved_app_config)
    if summarization_middleware is not None:
        middlewares.append(summarization_middleware)

    # Plan 模式下的 TODO 列表
    cfg = _get_runtime_config(config)
    is_plan_mode = cfg.get("is_plan_mode", False)
    todo_list_middleware = _create_todo_list_middleware(is_plan_mode)
    if todo_list_middleware is not None:
        middlewares.append(todo_list_middleware)

    # Token 统计
    if resolved_app_config.token_usage.enabled:
        middlewares.append(TokenUsageMiddleware())

    # 自动起标题（首轮对话后）
    middlewares.append(TitleMiddleware(app_config=resolved_app_config))

    # 长期记忆队列（首轮之后才进队列）
    middlewares.append(MemoryMiddleware(agent_name=agent_name, memory_config=resolved_app_config.memory))

    # 视觉模型 — 把图片细节注入 LLM 输入
    model_config = resolved_app_config.get_model_config(model_name) if model_name else None
    if model_config is not None and model_config.supports_vision:
        middlewares.append(ViewImageMiddleware())

    # 工具搜索（动态过滤可见工具）
    if resolved_app_config.tool_search.enabled:
        middlewares.append(DeferredToolFilterMiddleware())

    # Sub-agent 并发上限（与 prompt 中的硬限对应）
    subagent_enabled = cfg.get("subagent_enabled", False)
    if subagent_enabled:
        max_concurrent_subagents = cfg.get("max_concurrent_subagents", 3)
        middlewares.append(SubagentLimitMiddleware(max_concurrent=max_concurrent_subagents))

    # 循环检测（核心安全）
    loop_detection_config = resolved_app_config.loop_detection
    if loop_detection_config.enabled:
        middlewares.append(LoopDetectionMiddleware.from_config(loop_detection_config))

    # 自定义 middleware 插槽
    if custom_middlewares:
        middlewares.extend(custom_middlewares)

    # 安全终止检测
    safety_config = resolved_app_config.safety_finish_reason
    if safety_config.enabled:
        middlewares.append(SafetyFinishReasonMiddleware.from_config(safety_config))

    # 澄清请求拦截 —— 必须最后
    middlewares.append(ClarificationMiddleware())
    return middlewares
```

**插入顺序很重要**。`_build_middlewares` 函数上方的注释逐条解释为什么是这个顺序：

> - `ThreadDataMiddleware must be before SandboxMiddleware` —— 沙箱要 thread_id
> - `UploadsMiddleware should be after ThreadDataMiddleware` —— 上传需要 thread_id 才能解析路径
> - `DanglingToolCallMiddleware patches missing ToolMessages before model sees the history`
> - `SummarizationMiddleware should be early to reduce context before other processing`
> - `TodoListMiddleware should be before ClarificationMiddleware to allow todo management`
> - `TitleMiddleware generates title after first exchange`
> - `MemoryMiddleware queues conversation for memory update (after TitleMiddleware)`
> - `ViewImageMiddleware should be before ClarificationMiddleware to inject image details before LLM`
> - `ToolErrorHandlingMiddleware should be before ClarificationMiddleware to convert tool exceptions to ToolMessages`
> - `ClarificationMiddleware should be last to intercept clarification requests after model calls`

**最终的 graph 创建**：

```python
return create_agent(
    model=create_chat_model(
        name=model_name, thinking_enabled=thinking_enabled,
        reasoning_effort=reasoning_effort,
        app_config=resolved_app_config,
        attach_tracing=False  # ← 不变量
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

`ThreadState` 是 deer-flow 自定义的 LangGraph state schema：

```python
class ThreadState(AgentState):
    messages: list[BaseMessage]
    sandbox: dict             # 沙箱环境信息
    artifacts: list[str]      # 生成的文件路径
    thread_data: dict         # {workspace, uploads, outputs} 路径
    title: str | None         # 自动生成的对话标题
    todos: list[dict]         # 任务追踪（Plan 模式）
    viewed_images: dict       # 视觉模型已读图片数据
```

**教学点 #2 (核心)**：deer-flow 用 **"中间件即节点"** 替代了传统的"节点+边"图。**每个 middleware 拥有一个横切关注点**（线程状态、摘要、视觉、澄清、循环检测、安全终止、子 Agent 预算、Token 统计、Tracing……）。这是 v2 最重要的架构跃迁，**让 Harness 在保留 LangGraph 兼容性的同时变得可组合**。

## 五、Lead Agent 的系统提示词 — 在 prompt 里硬编码协议

**Path**: `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`

系统提示词不是一个静态文件，而是**按请求动态构建**。最有意思的部分是 `_build_subagent_section` —— 它把**硬并发限制 + 批次执行协议**直接写进 prompt：

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

这不是装饰 —— 同样的 `max_concurrent` 值在 `SubagentLimitMiddleware` 里**用代码强制执行**。

**教学点 #3 (核心)**：**提示词和中间件相互加强** —— 提示词教 LLM 契约，中间件**确定性地执行**契约。**文档活在代码里，不是 wiki 里**。这就是工业级 Agent 工程的标志。

## 六、Sub-Agent 调度 —— task_tool + SubagentExecutor

Lead Agent 自己不创建子 Agent，它通过 **`task` 工具**间接调度：

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

注意三个参数描述里的"FIRST/SECOND/THIRD"**序数提示** —— 这是一种**防御 LLM 调换位置参数的实战技巧**。

### 6.1 SubagentRegistry —— 三层覆盖

```python
def get_subagent_config(name: str, *, app_config=None) -> SubagentConfig | None:
    """
    Resolution order (mirrors Codex's config layering):
    1. Built-in subagents (general-purpose, bash)
    2. Custom subagents from config.yaml custom_agents section
    3. Per-agent overrides from config.yaml agents section (timeout, max_turns, model, skills)
    """
```

内置 `bash` 子 Agent 的配置：

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

**`disallowed_tools=["task", ...]`** 是个关键设计 —— 子 Agent 被**明令禁止**孵化孙 Agent。**在配置层**杀死失控递归。

### 6.2 SubagentExecutor —— 重型并发原语

`subagents/executor.py` 是 deer-flow 最复杂、最值得抄的文件之一。亮点：

**(A) 持久化的隔离事件循环** —— 当 executor 在已经跑着 loop 的 sync API 里被调用时使用：

```python
# Persistent event loop for isolated subagent executions triggered from an
# already-running parent loop. Reusing one long-lived loop avoids creating a
# fresh loop per execution and then closing async resources bound to it.
_isolated_subagent_loop: asyncio.AbstractEventLoop | None = None
_isolated_subagent_loop_thread: threading.Thread | None = None
_isolated_subagent_loop_started: threading.Event | None = None
_isolated_subagent_loop_lock = threading.Lock()
```

这个注释**就是一份生产事故复盘** —— 任何调试过"RuntimeError: this event loop is closed"或者"loop already running"的开发者都会立刻明白。

**(B) 竞态安全的终态转换** —— 任务可以被取消、超时、或并发完成：

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
        # ... 写入 status / result / error
```

**教学点 #4**：`try_set_terminal` + `_state_lock` 给出了**单调、幂等的状态机**。无竞态的状态机 = 可靠的取消语义。

**(C) 流式 + 协作取消**：

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

子 Agent 一边流，父 Agent 一边按 message id 去重收集。

## 七、Sandbox —— 两个 Provider，一套抽象

### 7.1 抽象 Sandbox

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

### 7.2 SandboxProvider —— 反射加载

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
        cls = resolve_class(config.sandbox.use, SandboxProvider)  # ← 字符串反射
        _default_sandbox_provider = cls(**kwargs)
    return _default_sandbox_provider
```

所以 `config.yaml` 写：

```yaml
sandbox:
  use: "deerflow.community.aio_sandbox:AioSandboxProvider"
```

就**字符串反射加载**一个完全不同的实现。这是 SPI（Service Provider Interface）模式的教科书演示。

### 7.3 AioSandboxProvider — 生产级组合

它**组合一个可替换的 backend**（`LocalContainerBackend` vs `RemoteSandboxBackend`）：

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

        # ★ 温池：已释放但容器还活着的 sandbox，可快速重新申领
        self._warm_pool: dict[str, tuple[SandboxInfo, float]] = {}

        self._shutdown_called = False
        self._backend: SandboxBackend = self._create_backend()
        atexit.register(self.shutdown)
        self._register_signal_handlers()

        # ★ 启动时收养上次进程留下的孤儿容器
        self._reconcile_orphans()

        # ★ 后台线程：超过 idle_timeout 自动驱逐
        if self._config.get("idle_timeout", DEFAULT_IDLE_TIMEOUT) > 0:
            self._start_idle_checker()
```

**三个生产特性**：
1. **Warm pool**（温池）—— 释放后容器保留一段时间，重申领时秒级冷启动
2. **`_reconcile_orphans()`** —— 启动时找上次进程残留的容器，收养或杀死
3. **Idle checker 线程** —— `idle_timeout`（默认 600s）后自动驱逐

### 7.4 虚拟路径映射

两个 Provider 都遵守**虚拟路径**约定：

| 虚拟路径 | 物理路径 |
| :--- | :--- |
| `/mnt/user-data/workspace` | `backend/.deer-flow/threads/{thread_id}/user-data/workspace` |
| `/mnt/user-data/uploads`   | `backend/.deer-flow/threads/{thread_id}/user-data/uploads` |
| `/mnt/user-data/outputs`   | `backend/.deer-flow/threads/{thread_id}/user-data/outputs` |
| `/mnt/skills`              | `deer-flow/skills/` |

**教学点 #5**：经典 SPI 设计 —— Agent 代码只看虚拟路径 + 抽象 `Sandbox` API。**开发跑 LocalSandboxProvider**（本地目录），**生产跑 AioSandboxProvider**（K8s）。Agent 一行不动。

## 八、Memory —— 三层、缓存、按用户隔离

不像很多 framework 直接抛一个空字典让你随便存，deer-flow 的 memory **强制三层 schema**（profile / history / facts）：

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

这比 Anthropic 在 *Context Engineering* 里讲的"profile + episodes + knowledge"**还要更细分**。`workContext` vs `personalContext` 反映了字节内部 ToB 客户的真实需求：工作记忆要严格不污染私人偏好。

**存储**实现 `MemoryStorage` ABC，默认的文件后端**按 mtime 缓存**，并**按 (user_id, agent_name) 元组隔离**：

```python
class FileMemoryStorage(MemoryStorage):
    def __init__(self):
        # 缓存键: (user_id, agent_name)；值: (memory_data, file_mtime)
        self._memory_cache: dict[tuple[str | None, str | None],
                                 tuple[dict[str, Any], float | None]] = {}
        self._cache_lock = threading.Lock()

    def save(self, memory_data, agent_name=None, *, user_id=None) -> bool:
        memory_data = {**memory_data, "lastUpdated": utc_now_iso_z()}
        temp_path = file_path.with_suffix(f".{uuid.uuid4().hex}.tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(memory_data, f, indent=2, ensure_ascii=False)
        temp_path.replace(file_path)  # ← 原子重命名
```

**教学点 #6**：`temp_path.replace(file_path)` 是**原子重命名** —— 经典的崩溃安全写模式。即便进程在写入中途崩了，文件要么是旧版本要么是新版本，**不会半残**。

**更新器**用专门的同步线程池避开事件循环交叉污染：

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

这个注释又是一份**调试史诗** —— 凡是被 "RuntimeError: this event loop is closed" 折磨过的工程师都会立刻共鸣。

## 九、Skills —— 文件系统原生的插件格式

`skills/public/github-deep-research/` 的目录结构：

```
github-deep-research/
├── SKILL.md
├── assets/report_template.md
└── scripts/github_api.py
```

`SKILL.md` 是 **YAML frontmatter + Markdown**，被 harness 解析：

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

`scripts/github_api.py` 是**可执行脚本**，Agent 在沙箱里直接运行：

```python
#!/usr/bin/env python3
"""GitHub API client for deep research."""
try:
    import requests
except ImportError:
    # ★ 沙箱可能没装 requests，提供 urllib fallback
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

注意 `RequestsFallback` —— **skill 作者不能假设沙箱有 `requests`**，所以打包一个 `urllib` fallback。**这是分发型 skill 的标准设计模式**。

20+ 内置 skill 包括：`chart-visualization`（Antv 全套图表 + 25+ 引用模板）、`skill-creator`（**生成新 skill 的元 skill**，自带 HTML 评估查看器）、`frontend-design`、`ppt-generation`、`podcast-generation`、`image-generation`、`video-generation`、`systematic-literature-review`、`claude-to-deerflow`（**把 Claude Code 的 skill 自动转过来**）等。

**Skill 通过工具门控暴露给 LLM**：

```python
skills_for_tool_policy = _load_enabled_skills_for_tool_policy(available_skills, app_config=resolved_app_config)
tools = filter_tools_by_skill_allowed_tools(tools + extra_tools, skills_for_tool_policy)
```

每个 skill 可以声明 `allowed_tools`，`filter_tools_by_skill_allowed_tools` 把不在白名单里的工具从该 skill 视野里移除。**和 Claude Code 用同一套模式**。

## 十、Message Gateway —— 七个 IM、一个统一入口

`backend/app/channels/` 是 deer-flow 多渠道接入的核心。一个简短的注册表：

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

每个渠道实现 `Channel` ABC，把入站事件推到 `MessageBus`，由 `ChannelManager` 转发到与 Web UI 相同的 Gateway 端点：

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

    # ★ 每个渠道是否支持流式
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

两个值得抄的常量：

```python
STREAM_UPDATE_MIN_INTERVAL_SECONDS = 0.35
THREAD_BUSY_MESSAGE = "This conversation is already processing another request. " \
                      "Please wait for it to finish and try again."
```

—— **350ms 的流式节流**和**线程并发繁忙提示**。生产 Agent 必须有的两个 UX 护栏。

**教学点 #7**：**所有 IM 折叠到同一个 Gateway 端点**。每个渠道只翻译协议特定的 webhook 到 `InboundMessage`。这就是全渠道 Bot 的教科书模式 —— **Slack/飞书/微信/Telegram 共存而 Agent runtime 一行代码不动**。

## 十一、MCP 集成 —— 含 OAuth 流的实战实现

deer-flow 用 `langchain-mcp-adapters` 作为协议库，**叠加自己的 session pool、cache、OAuth handler**。传输无关的配置构建：

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

伴随文件：
- `mcp/session_pool.py` —— **跨 run 保持 MCP session 热**
- `mcp/oauth.py` —— **`client_credentials` + `refresh_token` 流**叠在 MCP HTTP/SSE 之上
- `mcp/cache.py` —— 工具元数据缓存

**教学点 #8**：标准化协议（MCP）上层做**鉴权流 + 连接池** —— 这是把社区协议升级到企业级的标准手法。

## 十二、Loop Detection —— 一个值得复制的生产安全模式

`agents/middlewares/loop_detection_middleware.py` 的 docstring 单独就是一节工程课：

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

**这是一份完整的生产事故复盘**。

默认阈值：

```python
_DEFAULT_WARN_THRESHOLD = 3   # 3 次相同调用后注入警告
_DEFAULT_HARD_LIMIT     = 5   # 5 次相同调用后强制结束
_DEFAULT_WINDOW_SIZE    = 20  # 跟踪最近 N 次 tool call
_DEFAULT_MAX_TRACKED_THREADS = 100
_DEFAULT_TOOL_FREQ_WARN       = 30
_DEFAULT_TOOL_FREQ_HARD_LIMIT = 50
```

最妙的地方在 `_stable_tool_key` —— 对 `read_file` 工具的**行号范围做分桶**：

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

这意味着 Agent 反复读同一文件的"相近行号"（典型死循环模式：往同一区域跳着读 7 次）会**被识别为同一个调用**，不会因为行号略有不同就逃过检测。

**教学点 #9**：你**只有跑过几千小时生产 Agent 才能想到这种细节**。把这种经验沉淀进默认配置 = 把团队知识固化到代码里。

## 十三、其它值得抓拍的生产模式

非穷举清单：

- **`SafetyFinishReasonMiddleware`** —— provider 因安全原因终止时，抑制后续工具执行
- **`DanglingToolCallMiddleware`** —— 历史里有缺失 `ToolMessage` 时自动补上（多轮对话不会因此崩溃）
- **`TokenUsageMiddleware` + `SubagentTokenCollector`** —— 跨 lead + subagents 聚合 token，通过 SSE 发布
- **`RunJournal`** —— 追加日志，三种可插拔存储：`db.py` / `jsonl.py` / `memory.py`
- **Checkpointer SPI** —— 注册给 LangGraph 实现崩溃恢复
- **`tracing/factory.py:build_tracing_callbacks`** —— Langfuse + LangSmith 单一接入点
- **`patched_openai.py`, `patched_deepseek.py`, `patched_minimax.py`** —— provider 特定 shim 修 LangChain bug，**不 fork**
- **`security_scanner.py`** —— 安装前扫描 Skill 里的不安全 shell 模式（**LLM 供应链防御**）
- **`subagents/executor.py` `_THREAD_LOCK_EXECUTOR`** —— 有界线程池让阻塞的锁获取异步化

## 十四、三条最值得抄走的设计

> **如果你这一节只记三条**，记下面这三条：

### 设计 1 · 中间件即节点（Middleware-as-Node）
不是手画一张五角星状态机，而是**用 18 个中间件包裹一个 tool loop**。每个 middleware 负责一个横切关注点。这让 Harness **可组合** —— 想加新能力？写一个新 middleware，加到 `_build_middlewares` 的 `append` 列表里，**核心一行不改**。

### 设计 2 · 沙箱-Provider-Backend 三层 SPI
**抽象 `Sandbox` → `SandboxProvider` 生命周期 → 可替换 `SandboxBackend`**（本地容器 vs 远程 K8s）。一个 yaml 字符串 `deerflow.community.aio_sandbox:AioSandboxProvider` 就**反射加载完全不同的实现**。开源 Agent 代码里**最干净的可插拔示例**之一。

### 设计 3 · 提示词 + 中间件双重护栏
Lead Agent 提示词**教 LLM 契约**（"最多 N 个并发 `task` 调用"），`SubagentLimitMiddleware` **确定性地强制执行**。文档活在代码里。**等到团队 onboard 第 7 个人时**你会感激当初这么做。

---

## 十五、deer-flow vs helixent 对比表（终极版）

| 维度 | bytedance/deer-flow 2.0 | helixent |
| :--- | :--- | :--- |
| **起源 & lineage** | 字节跳动开源；v2 是地基重写（2026-02）；v1 是带命名节点的研究流水线 | 原创，无前作 |
| **核心图模型** | 单 LangGraph (`create_agent`) + 18 个 `AgentMiddleware`。"节点"即 middleware | 手写节点-边状态机；易可视化，扩展正交性较弱 |
| **Sub-agent 模型** | 一等公民 `task` 工具 + `SubagentExecutor`，含**持久隔离事件循环、竞态安全终态、协作取消、token 回滚**。硬并发上限**双重护栏**（prompt + middleware） | 通常建模为图节点；取消 / token 回滚需自定义 |
| **Sandbox 抽象** | `Sandbox` + `SandboxProvider` SPI；两个生产 Provider；后者本地 Docker / 远程 K8s 切换；**温池、孤儿收养、空闲驱逐** | 通常单一执行后端（本地 Python / subprocess）；无温池 |
| **Skills 格式** | 文件系统原生：`SKILL.md`（YAML frontmatter）+ `scripts/` + `references/` + `templates/` + 可选 `evals/`。挂载在 `/mnt/skills`。**与 Claude Code 格式兼容**（见 `claude-to-deerflow` skill） | Skill 通常是进程内 Python 模块；可移植性较弱 |
| **Memory** | 固定 3 层 schema（`user.{workContext, personalContext, topOfMind}` + `history.{recentMonths, earlierContext, longTermBackground}` + `facts[]`）；文件后端，**mtime 缓存**，按 `(user_id, agent_name)` 隔离，**原子重命名写** | 通常向量库或无结构 KV；缺"profile + episodes + knowledge"治理 |
| **Channels / Gateway** | 7 个 IM 渠道（飞书/Slack/微信/企微/钉钉/Telegram/Discord）全部折到一个 Gateway `/api/threads/{id}/runs` 端点。每渠道流式能力矩阵，350ms 流式节流 | 通常 CLI / Web only |
| **MCP** | 原生 `langchain-mcp-adapters` + DeerFlow `session_pool`、`cache`、**OAuth（client_credentials + refresh_token）**。stdio/SSE/HTTP 全支持 | 通常 stdio-only；OAuth 流罕见 |
| **生产安全** | 专门 middleware：循环检测（含 `read_file` 行号分桶）、安全终止原因、悬挂 tool call、token 使用、子 Agent 预算、摘要、安全终止检测器。**每条都有可测试的配置旋钮** | 通常依赖 `recursion_limit` 和临时重试；无类似 `LoopDetectionMiddleware` |
| **可观测性** | **单一回调注入点**（不变量见 §四）；Langfuse + LangSmith 单工厂；`RunJournal` 事件存储三后端（db / jsonl / memory） | 默认只有日志；tracing 一次性接入 |
| **多用户 / 鉴权** | Gateway with JWT + SQLite auth、CSRF middleware、**按用户路径**、按用户隔离的 memory 和 skills、渠道与 gateway 间内部鉴权 header | 通常单用户开发工具 |

## 十六、给中文章节读者的三个 takeaways

读完 helixent + deer-flow，你应该明白三件事：

**1. ReAct 的核心 ~25 行不变**。无论是 helixent 的 `async function*` 还是 deer-flow 用 LangGraph 包出来的 tool loop，本质都是 "think → act → observe" 循环。区别在外围。

**2. "中间件即节点"是 v2 时代的关键架构**。这让 Harness 在保留可调度图的同时变得**横切关注点可组合**。每加一个生产能力（记忆、循环检测、安全终止）= 加一个 middleware = 一行 append。

**3. SPI 是工业级 Harness 的标志**。沙箱、Memory 存储、Sub-agent registry、Skill 来源 —— deer-flow 把每个可能换实现的点都做成"配置加载类"。这是开源代码里**少见的、能直接抄进自家系统的纯设计模式**。

---

下一节：[§3.5 动手实验 →](./05-build-your-own.md)
