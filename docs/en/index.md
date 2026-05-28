---
layout: home
title: English · Prompt × Context × Harness
description: A complete tutorial on the three paradigm shifts of LLM application development

hero:
  name: "Prompt × Context × Harness"
  text: "Engineering Tutorial"
  tagline: "<strong>Open · Complete · Hands-on.</strong> Walk through the three paradigm shifts of LLM application development —<br/>from a single prompt, to a curated context, to a multi-hour Agent harness."
  image:
    src: /logo.svg
    alt: PCH
  actions:
    - theme: brand
      text: 📖 Start with the Prologue
      link: /en/00-prologue/
    - theme: alt
      text: 🧪 Jump to the Labs
      link: /en/labs
    - theme: alt
      text: 📚 Read the Glossary
      link: /en/04-appendix/glossary

features:
  - icon: 🔵
    title: Chapter 1 · Prompt Engineering
    details: Get your instructions across — Role / Few-shot / CoT / Structured Output / Meta-prompting / Reasoning Effort & Agentic Eagerness in the GPT-5 era.
    link: /en/01-prompt-engineering/
    linkText: Open Chapter 1 →
  - icon: 🟣
    title: Chapter 2 · Context Engineering
    details: Manage the attention budget — system/tools/examples/history anatomy; context rot; just-in-time retrieval; compaction; agentic memory; sub-agents.
    link: /en/02-context-engineering/
    linkText: Open Chapter 2 →
  - icon: 🟠
    title: Chapter 3 · Harness Engineering
    details: Build agents that run for hours — tool loop, sandbox, hooks, session handoff, progress.txt, Planner-Generator-Evaluator; deep-dive on helixent / deer-flow.
    link: /en/03-harness-engineering/
    linkText: Open Chapter 3 →
  - icon: 🧪
    title: Three Hands-on Labs
    details: Each chapter ships with five runnable Python demos. Lab 1 prompt patterns, Lab 2 mini RAG, Lab 3 a ~200-line mini Harness.
    link: /en/labs
    linkText: Run the labs →
  - icon: 📖
    title: Sourced from primary material
    details: Content cross-referenced with Anthropic Engineering, OpenAI Cookbook, Aliyun Bailian, ByteDance deer-flow, MagicCube helixent, and more.
    link: /en/04-appendix/references
    linkText: Full reference list →
  - icon: 🌐
    title: Bilingual
    details: Complete English tutorial plus a Chinese version. Switch via the top-right language toggle. Code samples are OpenAI-compatible.
    link: /zh-cn/
    linkText: 中文版 →
---

<div style="max-width: 960px; margin: 4rem auto 0; padding: 0 1.5rem;">

## 🗺️ Learning Map

<div style="font-family: var(--vp-font-family-mono); white-space: pre; font-size: 0.85em; line-height: 1.5; background: var(--vp-c-bg-soft); padding: 1.5rem; border-radius: 12px; overflow-x: auto;">
    Prompt Engineering         Context Engineering         Harness Engineering
    ──────────────────         ───────────────────         ───────────────────
    A polished instruction  →  A whole context recipe   →  Everything outside the model
        (words)                    (chapters / state)         (loop / tools / sandbox)

    📍 Chapter 1              📍 Chapter 2                 📍 Chapter 3
</div>

## 📋 Chapters at a glance

| Chapter | Theme | Time | Lab |
| :---: | :--- | :---: | :---: |
| [Prologue](/en/00-prologue/) | Why Prompt → Context → Harness | 15 min | — |
| [Chapter 1](/en/01-prompt-engineering/) | Prompt Engineering: getting instructions across | 90 min | [Lab 1](/en/labs) |
| [Chapter 2](/en/02-context-engineering/) | Context Engineering: managing the attention budget | 120 min | [Lab 2](/en/labs) |
| [Chapter 3](/en/03-harness-engineering/) | Harness Engineering: building agents that run for hours | 150 min | [Lab 3](/en/labs) |
| [Appendix](/en/04-appendix/) | Glossary · Roadmap · References · Contributing | — | — |

## 🎯 What you'll be able to do after reading

- ✅ When a new model or framework lands, instantly tell which of the P-C-H layers it changes.
- ✅ Write production-grade system prompts, tool schemas, and few-shot examples.
- ✅ Design context flows that survive long tasks without forgetting or overflowing the window.
- ✅ Understand how Claude Code / Codex / Cursor-style coding agents work — and build a simplified one.

## 🚀 Three recommended learning tempos

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin: 1rem 0;">
  <div style="border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 1.2rem;">
    <strong>🚶 Newcomer (0 background)</strong><br/>
    Read in order; run every lab as you go.<br/><br/>
    <em>~1 week</em>
  </div>
  <div style="border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 1.2rem;">
    <strong>🚴 Some LLM app experience</strong><br/>
    Jump straight to chapters 2 & 3; labs are mandatory.<br/><br/>
    <em>~2-3 days</em>
  </div>
  <div style="border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 1.2rem;">
    <strong>🏎️ Toolbuilder</strong><br/>
    Focus on chapter 3 + helixent / deer-flow + Lab 3.<br/><br/>
    <em>~1 day</em>
  </div>
</div>

## 🙏 Acknowledgements

The site's presentation borrows from the excellent [datawhalechina / easy-vibe](https://github.com/datawhalechina/easy-vibe).  
Methodology is built on public material from Anthropic, OpenAI, Aliyun, ByteDance, MagicCube and the broader open-source community.

</div>
