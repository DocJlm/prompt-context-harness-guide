---
title: §2.3 Memory · Help your Agent Remember Across Turns and Sessions
description: Short-term vs. long-term memory; structured notes; agentic memory
---

# §2.3 Memory: Help your Agent Remember

> "Agents that maintain notes outside the context window—and pull them back in when needed—can demonstrate persistent memory across **thousands of steps** with minimal context overhead."  
> — Anthropic, paraphrasing the Claude-plays-Pokémon experiment

## 1. Two Tiers of Memory

| Tier | Time scale | Where it lives | Examples |
| :--- | :--- | :--- | :--- |
| **Short-term memory** | within one session (minutes) | in the context window | current dialogue history, just-retrieved materials |
| **Long-term memory** | across sessions (days/months) | **outside the window**: files, databases, vector stores | user preferences, accumulated knowledge, past decisions |

The engineering of short-term memory was covered in §2.1 (History management). **This section focuses on long-term memory.**

## 2. Why Long-Term Memory?

Consider a personal assistant Agent:

- Last week the user said: "I don't drink coffee."
- Today the user says: "Recommend a breakfast spot near the office."

Without long-term memory, the Agent recommends a coffee shop. **It knew the preference but forgot** — user experience tanks.

Long-term memory = **cross-session persistent storage + on-demand pulling back into context**.

## 3. Three Implementations of Long-Term Memory

### Approach A · Stuff Everything Back (the naive one)

Every session start, feed in every past conversation the user has had.

```python
SYSTEM_PROMPT_TEMPLATE = """You are X's assistant.
Below is the user's complete history (most recent first):
{all_history}
"""
```

🚫 Blows the window after a few turns. **Not viable.**

### Approach B · Summary Memory

At the end of each session, the LLM summarizes the dialogue into 1–2 paragraphs and stores it. At the start of the next session, concatenate all stored summaries and feed them in.

```python
def end_of_session(messages, user_id):
    summary = llm_summarize(messages, max_tokens=200)
    db.insert({"user_id": user_id, "summary": summary, "timestamp": now()})

def start_of_session(user_id):
    summaries = db.query({"user_id": user_id}, limit=20, order="recent")
    return "\n".join([s.summary for s in summaries])
```

✅ Simple and effective — **good for personal-assistant-style apps**. But: summaries inevitably lose detail, and after dozens of sessions **key facts can be diluted away**.

### Approach C · Structured Memory

**Structure** the memory and retrieve as needed.

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
    {"date": "2026-05-20", "event": "User celebrated 6th wedding anniversary, booked Western food"},
    {"date": "2026-05-15", "event": "User complained about last week's breakfast spot service attitude"},
    ...
]

# Knowledge / preferences (semantic memory)
knowledge = vector_index_of([
    "User enjoys intermittent fasting",
    "User is lactose-intolerant",
    ...
])
```

Every session start:
1. Inject profile (small, a few hundred tokens).
2. Retrieve the 5–10 most recent / most relevant episodes.
3. Retrieve the 3–5 most relevant knowledge entries.

```python
def build_memory_block(user_id, current_query):
    profile = db.get_profile(user_id)
    recent_episodes = db.get_episodes(user_id, limit=5)
    relevant_knowledge = knowledge_index.search(current_query, top_k=5)
    return f"""
[User Profile] {json.dumps(profile, ensure_ascii=False)}

[Recent Events]
{format_episodes(recent_episodes)}

[Relevant Knowledge / Preferences]
{format_knowledge(relevant_knowledge)}
"""
```

✅ **Production-grade solution.** OpenAI's ChatGPT Memory and Anthropic's Claude Memory (2025+) are all variations of this underneath.

## 4. Agentic Memory: Let the Agent Take its Own Notes

In *Context Engineering*, Anthropic spends considerable time on one example — **Claude plays Pokémon**:

> Claude playing Pokémon demonstrated memory capabilities tracking "for the last 1,234 steps" and maintaining multi-hour task sequences.

How did it pull that off? **Let the Agent write notes into a file by itself.**

```
Toolset:
- write_note(text)    ← Agent calls proactively to save key info into notes.md
- read_note()         ← read when starting a new step / new session
- update_note(line, new_text)
```

A simplified progress note looks like this:

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

At each step the Agent might `read_note()` and, when needed, `write_note(...)`. **This is using the filesystem as working memory.**

This pattern is profound:

- **Unlimited memory capacity** (bounded by the filesystem, not the context window).
- **Memory is structured** (Markdown / JSON).
- **Fully under the Agent's control** — not hardcoded by the developer.

## 5. Memory's Read–Write Operations

Design memory like a database:

```
Read operations (pull into context):
  - search(query)             vector / keyword retrieval
  - get_recent(n)              most recent N entries
  - get_by_type(type)          fetch by category (profile / episode / fact)

Write operations (push out of context):
  - add(text, type=...)        add a new entry
  - update(id, text)           edit an entry
  - delete(id)                 delete an entry
  - upsert_profile(field, val) update user profile
```

Anthropic's Claude Agent SDK and OpenAI's Assistants API have wrapped these capabilities into their platforms.

## 6. The Hard Problems of Memory

### 1. When to write?

Too often → noise and wasted tokens. Too sparse → key facts missed.

**Rule of thumb**: let the LLM proactively write at moments like:
- The user states a preference / fact ("I don't drink coffee").
- A task is finished (write "X is done").
- A new memorable person / object / place appears.

You can use a system-level instruction like:

```
You have a long-term memory system. When the user expresses a clear preference, a key fact,
or makes a major decision, call the `remember(...)` tool to record it. Do not write down
everyday conversational content.
```

### 2. When to read?

Too much → distracts from the current task. Too little → misses key facts.

**Rule of thumb**:
- Default at session start: **read the profile + the 5 most recent episodes**.
- User uses pronouns ("that place", "the one mentioned earlier") → trigger an extra search.
- Cross-domain task → retrieve domain-relevant knowledge.

### 3. When to clean up / update?

Memory **goes stale**: "user was learning Python last month" → what should we say now?

**Rule of thumb**:
- Every memory entry **carries a timestamp**.
- Sort retrievals by recency × relevance.
- Periodically (e.g., monthly) run an LLM-driven memory consolidation: merge, dedupe, flag as stale.

### 4. How do we prevent "pollution"?

A user's offhand remark isn't necessarily a fact.  
"My mother is the queen" — should not get written into the profile.

**Rule of thumb**:
- In the `remember` tool's description, state: "only write facts that are independently verifiable or persistently relevant."
- Use a confidence field: each memory entry gets a 0–1 confidence; confidence decays over time without reaffirmation.

## 7. Case Study: a Minimal Memory System

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
        # In real scenarios use embeddings; demo uses substring containment
        items = [e for e in self._cache if query in e["text"]]
        return items[:limit]
```

Lab 2 will extend this demo to include embedding-based retrieval.

## 8. Putting This Section in Your Head

```
What to store:                What NOT to store:
  ✓ user prefs / profile        ✗ small talk
  ✓ key decisions / events      ✗ rapidly-stale facts ("today's weather")
  ✓ accumulated knowledge       ✗ highly sensitive personal data (unauthorized)
  ✓ task progress / TODOs        ✗ recomputable intermediates

When to read:                 When to write:
  ✓ session start                ✓ user states a clear preference
  ✓ pronouns / past references   ✓ task complete
  ✓ cross-domain task pivots     ✓ a new key entity appears
  ✗ every turn (too expensive)    ✗ every message (too noisy)
```

---

Next: [§2.4 Compaction and Sub-agents →](./04-compaction-subagents.md)
