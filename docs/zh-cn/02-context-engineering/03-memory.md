---
title: §2.3 记忆 · 让 Agent 跨轮 / 跨 Session 不忘事
description: 短期 vs 长期记忆；结构化笔记；Agentic Memory
---

# §2.3 记忆：让 Agent 不忘事

> "Agents that maintain notes outside the context window—and pull them back in when needed—can demonstrate persistent memory across **thousands of steps** with minimal context overhead."  
> — Anthropic, paraphrasing the Claude-plays-Pokémon experiment

## 一、记忆的两个层次

| 层次 | 时间尺度 | 存在哪 | 例子 |
| :--- | :--- | :--- | :--- |
| **短期记忆** | 一个 Session 内（minutes） | Context Window 里 | 当前对话 history、刚检索的资料 |
| **长期记忆** | 跨 Session（days/months） | **窗口之外**：文件、数据库、向量库 | 用户偏好、累积知识、历史决策 |

短期记忆的工程已经在 §2.1（History 管理）讲过。**这一节聚焦长期记忆**。

## 二、为什么需要长期记忆？

考虑一个个人助理 Agent：

- 用户上周说："我不喝咖啡。"
- 今天用户说："给我推荐一家公司附近的早餐店。"

如果没有长期记忆，Agent 推一家咖啡馆。**已经知道偏好却忘了**——用户体验崩。

长期记忆 = **跨 Session 持久存储 + 按需 pull 回 context**。

## 三、长期记忆的三种实现

### 方式 A · 全量塞回（最朴素）

每次 Session 启动，把用户所有历史对话喂进去。

```python
SYSTEM_PROMPT_TEMPLATE = """你是 X 助理。
以下是用户的历史对话记录（按时间倒序）：
{all_history}
"""
```

🚫 几轮就爆窗口。**不可用**。

### 方式 B · 摘要式（Summary Memory）

每个 Session 结束时，用 LLM 把这轮对话摘要成 1–2 段，存起来。下一个 Session 开始时把所有历史摘要拼起来塞进去。

```python
def end_of_session(messages, user_id):
    summary = llm_summarize(messages, max_tokens=200)
    db.insert({"user_id": user_id, "summary": summary, "timestamp": now()})

def start_of_session(user_id):
    summaries = db.query({"user_id": user_id}, limit=20, order="recent")
    return "\n".join([s.summary for s in summaries])
```

✅ 简单有效，**适合个人助理类应用**。但问题是：摘要不可避免地丢细节，几十次 Session 后**关键事实可能被稀释**。

### 方式 C · 结构化记忆（Structured Memory）

把记忆**结构化**存储，按需检索。

```python
# 用户画像
profile = {
    "name": "张三",
    "preferences": {"diet": "不喝咖啡", "exercise": "跑步、瑜伽"},
    "dislikes": ["香菜"],
    "important_dates": {"anniversary": "2020-05-20"},
}

# 事件流（episodic memory）
episodes = [
    {"date": "2026-05-20", "event": "用户庆祝结婚 6 周年，订了西餐"},
    {"date": "2026-05-15", "event": "用户抱怨上周的早餐店服务态度差"},
    ...
]

# 知识 / 偏好（semantic memory）
knowledge = vector_index_of([
    "用户喜欢轻断食",
    "用户对乳糖不耐受",
    ...
])
```

每次 Session 启动：
1. 注入 profile（小，几百 token）。
2. 检索最近 / 最相关的 5–10 条 episodes。
3. 检索最相关的 3–5 条 knowledge。

```python
def build_memory_block(user_id, current_query):
    profile = db.get_profile(user_id)
    recent_episodes = db.get_episodes(user_id, limit=5)
    relevant_knowledge = knowledge_index.search(current_query, top_k=5)
    return f"""
[用户画像] {json.dumps(profile, ensure_ascii=False)}

[最近事件]
{format_episodes(recent_episodes)}

[相关知识 / 偏好]
{format_knowledge(relevant_knowledge)}
"""
```

✅ **生产级方案**。OpenAI 的 ChatGPT Memory、Anthropic 的 Claude Memory（2025+），底层都是这一类。

## 四、Agentic Memory：让 Agent 自己记笔记

Anthropic 在 *Context Engineering* 里浓墨重彩地讲了一个例子——**Claude plays Pokémon**：

> Claude playing Pokémon demonstrated memory capabilities tracking "for the last 1,234 steps" and maintaining multi-hour task sequences.

它怎么做到的？**让 Agent 自己往一个文件里写笔记**。

```
工具集:
- write_note(text)    ← Agent 主动调用，把当前关键信息写入 notes.md
- read_note()         ← 启动新 step / 新 session 时读取
- update_note(line, new_text)
```

一个简化的 progress note 看起来像这样：

```markdown
# Game Progress

## Current State
- Location: Cerulean City, Pokémon Center
- Party: Charmeleon (L24), Pikachu (L18), Pidgey (L15)
- Goal: Get HM01 Cut to access Vermilion City gym

## Recent Events
- L24 Charmeleon evolved from Charmander after defeating Misty
- Picked up Squirtle's Bubble TM (TM11)

## Open Questions
- Where is Bill's PC? Need to ask the NPC near the bridge.
- Need 200 yen for next Pokéball purchase.
```

每个 step Agent 都可能 `read_note()`，必要时 `write_note(...)`。**这就是用文件系统当作工作记忆**。

这个范式深刻：

- **记忆容量无上限**（受文件系统限制，不是 context window）。
- **记忆结构化**（Markdown / JSON）。
- **完全在 Agent 的控制下**——不是开发者写死。

## 五、Memory 的 Read–Write 操作

把记忆当数据库来设计：

```
Read 操作（pull into context）:
  - search(query)             向量 / 关键词检索
  - get_recent(n)              最近 N 条
  - get_by_type(type)          按类别拿（profile / episode / fact）

Write 操作（push out of context）:
  - add(text, type=...)        新增一条
  - update(id, text)           修改一条
  - delete(id)                 删除一条
  - upsert_profile(field, val) 更新用户画像
```

Anthropic 的 Claude Agent SDK / OpenAI 的 Assistants API 都把这套能力封进了平台。

## 六、Memory 的难题

### 1. 何时写？

太频繁 → 噪声多 + token 浪费。太稀疏 → 关键事实漏。

**经验规则**：让 LLM 在以下时机主动写：
- 用户陈述了一个偏好 / 事实（"我不喝咖啡"）。
- 任务完成时（写"已完成 X"）。
- 出现新的可记忆人 / 物 / 地点。

可以用一个系统级指令：

```
你有一个长期记忆系统。当用户表达明确偏好、关键事实、或重大决定时，
调用 `remember(...)` 工具记录。不要为日常对话内容写入。
```

### 2. 何时读？

太多 → 干扰当前任务。太少 → 漏关键。

**经验规则**：
- 每个 Session 启动**默认读 profile + 最近 5 条 episode**。
- 用户提到代词（"那家店" "前面提的"）→ 触发额外检索。
- 任务跨 domain → 检索 domain 相关 knowledge。

### 3. 何时清理 / 更新？

记忆会**过时**："用户上个月在学 Python" → 现在该说什么？

**经验规则**：
- 每条记忆**带时间戳**。
- 检索时按 recency × relevance 排序。
- 定期（如每月）用 LLM 做 memory consolidation：合并、去重、过时标记。

### 4. 如何防止"被污染"？

用户随口一说不代表是事实。  
"我妈妈是女王"——不该写进 profile。

**经验规则**：
- 在 `remember` 工具的 description 里写明："仅写入可被独立验证或长期相关的事实"。
- 用 confidence 字段：每条记忆带 0–1 的置信度，时间越久没复现的置信度衰减。

## 七、案例：一个最小的 Memory 系统

```python
# memory.py
import json, time
from pathlib import Path

class Memory:
    def __init__(self, path):
        self.path = Path(path)
        self.path.touch(exist_ok=True)
        self._cache = self._load()

    def _load(self):
        try: return json.loads(self.path.read_text() or "[]")
        except: return []

    def remember(self, text, kind="fact", confidence=0.9):
        entry = {
            "id": len(self._cache),
            "text": text, "kind": kind,
            "confidence": confidence,
            "ts": time.time(),
        }
        self._cache.append(entry)
        self.path.write_text(json.dumps(self._cache, ensure_ascii=False, indent=2))
        return entry["id"]

    def recall(self, kind=None, limit=10):
        items = self._cache if kind is None else [e for e in self._cache if e["kind"] == kind]
        return sorted(items, key=lambda e: -e["ts"])[:limit]

    def search(self, query, limit=5):
        # 真实场景里用 embedding；demo 用字符串包含
        items = [e for e in self._cache if query in e["text"]]
        return items[:limit]
```

Lab 2 会扩展这个 demo 加入 embedding 检索。

## 八、把这一节装进脑子

```
What to store:                What NOT to store:
  ✓ 用户偏好 / 画像             ✗ 闲聊
  ✓ 关键决策 / 事件             ✗ 易过时事实（"今天的天气"）
  ✓ 累积知识 / 教训             ✗ 高度个人隐私（未授权）
  ✓ 任务进度 / 待办              ✗ 可重新计算的中间结果

When to read:                 When to write:
  ✓ Session 启动                 ✓ 用户明确表达偏好
  ✓ 涉及代词 / 历史指代          ✓ 任务完成
  ✓ 跨 domain 任务跳转           ✓ 出现新的关键实体
  ✗ 每一轮都读（太贵）            ✗ 每条 message 都写（太吵）
```

---

下一节：[§2.4 压缩与子 Agent →](./04-compaction-subagents.md)
