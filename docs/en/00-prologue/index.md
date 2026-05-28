---
title: Prologue · Why Prompt → Context → Harness
description: The three paradigm shifts of LLM application development
---

# Prologue: Why Prompt → Context → Harness?

> "Building with language models is becoming less about finding the right words and phrases for your prompts, and more about answering the broader question of *'what configuration of context is most likely to generate our model's desired behavior?'*"  
> — Anthropic Engineering, *Effective Context Engineering for AI Agents*, 2025-09

## 1. The Dynamics of Paradigm Shifts

Every paradigm shift is driven by the simultaneous rise of **model capability** and **application complexity**.

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  Capability                                        Harness Engineering │
│   ▲                                       ╱───────────────             │
│   │                          Context     ╱                             │
│   │                          Engineering╱                              │
│   │                  ┌──────────────────┘                              │
│   │       Prompt    ╱                                                  │
│   │       Engineering                                                  │
│   │  ┌───┘                                                             │
│   │ ╱                                                                  │
│   └─────────────────────────────────────────────────────────────► Time │
│     2022          2023-2024         2024-2025         2025-2026        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

- **2022–2023: The Prompt Engineering era.** GPT-3.5 / GPT-4 with 4K–8K context. The application shape was "input a passage → output a passage." The deciding factor was **how to phrase one sentence so the model listens**: Role, Few-shot, CoT, Delimiters, Output Format.
- **2024: Context Engineering sprouts.** Context windows expanded to 128K–1M, but with the rise of RAG, long-document Q&A, and multi-turn Agents, engineers discovered that **writing good instructions alone was no longer enough**—they also had to manage "what information enters the window, when it enters, and how it enters."
- **2025-09: Anthropic formally names Context Engineering.** In an Engineering Blog post coinciding with the Claude Sonnet 4.5 release, they wrote: "**Context engineering is the natural progression of prompt engineering**."
- **2025–2026: Harness Engineering emerges.** Coding Agents like Claude Code, Codex, Cursor, and Devin let a single Agent run for hours, call hundreds of tools, and span multiple Sessions. At this point the model is just a CPU in the middle, and **everything outside the model**—tools, loops, memory, sandboxes, sub-agents, human-in-the-loop—becomes decisive. Anthropic gave a systematic definition in *Effective Harnesses for Long-Running Agents* in early 2026.

## 2. The Boundaries and Continuity Across the Three Layers

A common question: **aren't these three just different names for the same thing?**

No. They solve problems at **different scales**:

| Dimension | Prompt Engineering | Context Engineering | Harness Engineering |
| :--- | :--- | :--- | :--- |
| **Object of concern** | A single prompt text | The state of the entire context window | All the code outside the model |
| **Time scale** | One inference (seconds) | Multi-turn / one Task (minutes) | Multi-Session / long-running task (hours) |
| **Typical question** | "How do I get it to output JSON?" | "How do I keep it from forgetting after 100 turns?" | "How do I keep it running for 4 hours without blowing up?" |
| **Failure mode** | Off-topic / wrong format | Hallucination / repeated work / forgetting mid-task | Crashing mid-run / never finishing / wrecking the environment |
| **Typical tools** | Prompt templates | RAG, Compaction, Memory | Tool Loop, Sandbox, Sub-agent, Hook |

Note: **they are nested, not substitutes for each other.**

```
┌──────────────────────────────────────────────────────────────────┐
│   Harness Engineering                                            │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │   Context Engineering                                    │  │
│   │   ┌──────────────────────────────────────────────────┐  │  │
│   │   │   Prompt Engineering                             │  │  │
│   │   │   • System / User / Few-shot / CoT               │  │  │
│   │   │   • Output format, role, delimiters              │  │  │
│   │   └──────────────────────────────────────────────────┘  │  │
│   │   • Tool descriptions / compaction / retrieval / sub-agent summaries │  │
│   └──────────────────────────────────────────────────────────┘  │
│   • Tool loops / permissions / sandbox / hooks / session switching / persistent state │
└──────────────────────────────────────────────────────────────────┘
```

A good prompt is the foundation for a good context; a good context is the foundation for a Harness that can run a long task. **You can't skip levels.**

## 3. Why "Prompt Engineering" Is No Longer Enough as a Term

Anthropic's 2025-09 article had a particularly incisive line:

> "Despite their speed and ability to manage larger and larger volumes of data, we've observed that LLMs, like humans, **lose focus or experience confusion at a certain point**. Studies on needle-in-a-haystack style benchmarking have uncovered the concept of **context rot**: as the number of tokens in the context window increases, the model's ability to accurately recall information from that context decreases."

**Context Rot** is the root of all this. The attention mechanism in a Transformer produces *n²* pairwise relationships over *n* tokens—the larger the window, the more the model's "attention budget" gets diluted. A 1M window doesn't mean you can stuff in 1M tokens of garbage.

So the question shifts from "**how do I write the best prompt**" to "**how do I manage this finite attention budget**." The latter is Context Engineering.

And when Agents start working **across multiple context windows** (a Session fills up at 200K tokens, but the task needs 2M tokens to complete), new problems appear:

- How does an Agent **quickly recover** prior state when starting a new Session?
- How do multiple Agents **coordinate** rather than step on each other?
- How can an Agent call tools without **wrecking the environment**?

These problems can no longer be solved by context-layer tactics alone—they are **software engineering problems** requiring state machines, file systems, version control, sandboxes, permission models, and human-machine protocols. That's Harness Engineering.

## 4. Putting It Together with an Example

Suppose you want to build an app that "automatically writes weekly reports for my GitHub repo."

- **Prompt Engineering stage (V1)**: You write a prompt: "Please summarize the following commit list as a weekly report. Each bullet point should be under 20 characters, grouped by 'feature/fix/refactor', output in Markdown." You paste in the `git log` and the model produces a report. **Good enough, until you exceed 200 commits.**
- **Context Engineering stage (V2)**: You discover that long commit lists cause the model to miss the point. You introduce:
  - **Retrieval**: only pull commits linked to PRs with reviewer comments.
  - **Compaction**: use a smaller model to generate a one-sentence summary of each commit first.
  - **Structure**: inject JSON rather than a wall of text.
  - **Examples**: stuff 2–3 high-quality report examples into the system prompt.
- **Harness Engineering stage (V3)**: You want it to **run automatically every Monday morning**, **alert** when commits contain security risks, call the GitHub API to fetch PR diffs, and **insert charts** into the generated report. You give it:
  - A **Cron / scheduler** to trigger the loop.
  - A set of **tools**: `get_commits` / `get_pr_diff` / `render_chart` / `send_slack`.
  - A **Planner**: first list the key events of the week, then dispatch sub-agents to write each category.
  - A **sandbox**: chart-rendering code executes in a container.
  - A **progress.md**: read at the start of each Session to learn the prior summary style and recipient preferences.

See it? From V1 to V3, **the model itself didn't change**, but your engineering effort grew 10x and so did the output quality. That's the engineering leverage P→C→H gives us.

## 5. What This Tutorial Promises

- **Chapter 1**: You'll be able to write a prompt that "any model can understand," and you'll be able to dial its "responsiveness."
- **Chapter 2**: You'll be able to **design the context flow** for a long task, knowing when to compact, when to retrieve, and when to take notes.
- **Chapter 3**: You'll be able to **build your own** Agent Harness that runs for hours, and read the source of industrial-grade open-source projects (helixent / deer-flow).

---

Continue reading: [Chapter 1 · Prompt Engineering →](../01-prompt-engineering/index.md)
