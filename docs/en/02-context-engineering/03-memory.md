---
title: §2.3 Memory · Help your Agent Remember Across Turns and Sessions
description: Short-term vs. long-term memory; structured notes; agentic memory
---

# §2.3 Memory: Help Your Agent Not Forget

> "Agents that maintain notes outside the context window—and pull them back in when needed—can demonstrate persistent memory across **thousands of steps** with minimal context overhead."  
> — Anthropic, paraphrasing the Claude-plays-Pokémon experiment

## 1. Two Layers of Memory

| Layer | Timescale | Where it lives | Examples |
| :--- | :--- | :--- | :--- |
| **Short-term memory** | Within one session (minutes) | Inside the context window | Current dialogue history, recently retrieved material |
| **Long-term memory** | Across sessions (days/months) | **Outside the window**: files, databases, vector stores | User preferences, accumulated knowledge, historical decisions |

The engineering of short-term memory was covered in §2.1 (History management). **This section focuses on long-term memory.**

## 2. Why Long-Term Memory?

Consider a personal assistant agent:

- Last week the user said: "I don't drink coffee."
- Today the user says: "Recommend a breakfast place near my office."

Without long-term memory, the agent recommends a café. **The preference was known but forgotten** — UX collapse.

Long-term memory = **persistent cross-session storage + on-demand pull back into context**.

## 3. Three Implementations of Long-Term Memory

### Approach A · Stuff Everything Back (the Naive)

At the start of each session, feed the user's entire conversation history.

```python
SYSTEM_PROMPT_TEMPLATE = """You are X Assistant.
Below is the user's full conversation history (in reverse chronological order):
{all_history}
"""
```

🚫 Window blown in a few turns. **Unusable.**

### Approach B · Summary Memory

At the end of each session, use an LLM to summarize the conversation into 1–2 paragraphs and store it. At the start of the next session, concatenate all stored summaries.

```python
def end_of_session(messages, user_id):
    summary = llm_summarize(messages, max_tokens=200)
    db.insert({"user_id": user_id, "summary": summary, "timestamp": now()})

def start_of_session(user_id):
    summaries = db.query({"user_id": user_id}, limit=20, order="recent")
    return "\n".join([s.summary for s in summaries])
```

✅ Simple and effective — **suits personal-assistant-class apps**. But: summarization inevitably loses detail, and after dozens of sessions **key facts may be diluted**.

### Approach C · Structured Memory

Store memory **structurally** and retrieve on demand.

```python
# User profile
profile = {
    "name": "Zhang San",
    "preferences": {"diet": "no coffee", "exercise": "running, yoga"},
    "dislikes": ["cilantro"],
    "important_dates": {"anniversary": "2020-05-20"},
}

# Event stream (episodic memory)
episodes = [
    {"date": "2026-05-20", "event": "User celebrated their 6th anniversary; booked a Western restaurant"},
    {"date": "2026-05-15", "event": "User complained about poor service at last week's breakfast place"},
    ...
]

# Knowledge / preferences (semantic memory)
knowledge = vector_index_of([
    "User likes intermittent fasting",
    "User is lactose intolerant",
    ...
])
```

At session start:
1. Inject profile (small, a few hundred tokens).
2. Retrieve the most recent / most relevant 5–10 episodes.
3. Retrieve the most relevant 3–5 pieces of knowledge.

```python
def build_memory_block(user_id, current_query):
    profile = db.get_profile(user_id)
    recent_episodes = db.get_episodes(user_id, limit=5)
    relevant_knowledge = knowledge_index.search(current_query, top_k=5)
    return f"""
[User profile] {json.dumps(profile, ensure_ascii=False)}

[Recent events]
{format_episodes(recent_episodes)}

[Relevant knowledge / preferences]
{format_knowledge(relevant_knowledge)}
"""
```

✅ **Production-grade.** OpenAI's ChatGPT Memory and Anthropic's Claude Memory (2025+) are all variants of this.

### Case · deer-flow's Three-Layer Memory Schema

ByteDance's deer-flow takes this paradigm all the way to **enforced schema** — rather than handing developers an empty dict to fill arbitrarily:

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
— [bytedance/deer-flow `agents/memory/storage.py`](https://github.com/bytedance/deer-flow/blob/main/backend/packages/harness/deerflow/agents/memory/storage.py)

Three engineering decisions to notice:

1. **`workContext` and `personalContext` are separated** — reflecting real ToB customer needs: work memory must not pollute personal preferences.
2. **`history.{recentMonths, earlierContext, longTermBackground}` is a three-tier time bucketing** — not a simple "sort by time, take last N" but bucketing into "recent months / earlier / long-term background."
3. **Writes use atomic rename + mtime caching** —
   ```python
   temp_path = file_path.with_suffix(f".{uuid.uuid4().hex}.tmp")
   ...
   temp_path.replace(file_path)  # ← atomic rename
   ```
   Even if the process crashes mid-write, the file on disk is either the old version or the new version — **never half-written**.

§3.4 in Chapter 3 walks through how deer-flow wires this memory system into LangGraph state and sub-agents.

## 4. Agentic Memory: Let the Agent Take Its Own Notes

In *Context Engineering*, Anthropic devotes significant ink to one example — **Claude plays Pokémon**:

> Claude playing Pokémon demonstrated memory capabilities tracking "for the last 1,234 steps" and maintaining multi-hour task sequences.

How does it work? **The agent writes notes to a file itself.**

```
Tools:
- write_note(text)    ← Agent calls this to record key info into notes.md
- read_note()         ← Read at the start of a new step / new session
- update_note(line, new_text)
```

A simplified progress note looks like:

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

Every step the agent may `read_note()`, and when needed `write_note(...)`. **This is using the filesystem as working memory.**

The paradigm is deep:

- **Memory capacity has no upper limit** (bounded by the filesystem, not the context window).
- **Memory is structured** (Markdown / JSON).
- **Memory is entirely under the agent's control** — not hardcoded by the developer.

## 5. Memory Read–Write Operations

Treat memory like a database:

```
Read operations (pull into context):
  - search(query)             vector / keyword search
  - get_recent(n)              last N entries
  - get_by_type(type)          by category (profile / episode / fact)

Write operations (push out of context):
  - add(text, type=...)        add an entry
  - update(id, text)           modify an entry
  - delete(id)                 delete an entry
  - upsert_profile(field, val) update user profile
```

Both Anthropic's Claude Agent SDK and OpenAI's Assistants API package this capability into their platforms.

## 6. Memory's Hard Problems

### 1. When to write?

Too frequent → noise + token waste. Too sparse → key facts lost.

**Rule of thumb**: have the LLM actively write at these moments:
- The user states a preference / fact ("I don't drink coffee").
- A task completes (write "completed X").
- A new memorable person / object / location appears.

You can use a system-level instruction:

```
You have a long-term memory system. When the user expresses an explicit preference,
a key fact, or a major decision, call the `remember(...)` tool to log it. Do not
write down everyday conversational content.
```

### 2. When to read?

Too much → distracts from the current task. Too little → key info missed.

**Rule of thumb**:
- At the start of each session, **default to reading profile + last 5 episodes**.
- When the user uses a pronoun ("that place," "the one you mentioned earlier") → trigger extra retrieval.
- When a task crosses domains → retrieve domain-relevant knowledge.

### 3. When to clean / update?

Memory goes **stale**: "the user was learning Python last month" → what to say now?

**Rule of thumb**:
- Every memory entry has a **timestamp**.
- Retrieval sorts by recency × relevance.
- Run periodic (e.g., monthly) memory consolidation with an LLM: merge, dedupe, flag stale items.

### 4. How to prevent "pollution"?

A user's offhand remark is not necessarily fact.  
"My mother is the queen" — that shouldn't go into the profile.

**Rule of thumb**:
- In the `remember` tool's description, write: "Only store facts that can be independently verified or that are long-term relevant."
- Use a confidence field: each memory carries a 0–1 confidence, decaying over time without reinforcement.

## 7. Case: A Minimal Memory System

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
        # In production, use embeddings; demo uses substring match
        items = [e for e in self._cache if query in e["text"]]
        return items[:limit]
```

Lab 2 will extend this demo with embedding search.

## 8. Takeaways

```
What to store:                What NOT to store:
  ✓ user preferences / profile  ✗ small talk
  ✓ key decisions / events       ✗ easily stale facts ("today's weather")
  ✓ accumulated knowledge        ✗ highly private info (without consent)
  ✓ task progress / TODOs        ✗ recomputable intermediate results

When to read:                 When to write:
  ✓ session start               ✓ user explicitly states a preference
  ✓ pronouns / back-references  ✓ task completes
  ✓ cross-domain task jumps     ✓ new key entity appears
  ✗ every turn (too expensive)  ✗ every message (too noisy)
```

---

Next: [§2.4 Compaction and Sub-agents →](./04-compaction-subagents.md)
