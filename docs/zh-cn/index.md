---
layout: home
title: 中文版 · Prompt × Context × Harness
description: 一份完整的中文实战教程，带你走完 LLM 应用开发的三次范式跃迁

hero:
  name: "Prompt × Context × Harness"
  text: "Engineering 中文教程"
  tagline: "<strong>开源 · 完整 · 可动手</strong>　走完 LLM 应用开发的三次范式跃迁。<br/>从一段提示词，到一整套上下文配置，到一个能跑数小时的 Agent Harness。"
  image:
    src: /logo.svg
    alt: PCH
  actions:
    - theme: brand
      text: 📖 开始阅读 · 序章
      link: /zh-cn/00-prologue/
    - theme: alt
      text: 🧪 直接看实验
      link: /zh-cn/labs
    - theme: alt
      text: 📚 看附录术语表
      link: /zh-cn/04-appendix/glossary

features:
  - icon: 🔵
    title: 第 1 章 · Prompt Engineering
    details: 把指令说清楚 —— Role / Few-shot / CoT / Structured Output / Meta-prompting / GPT-5 时代的 Reasoning Effort & Agentic Eagerness。
    link: /zh-cn/01-prompt-engineering/
    linkText: 进入第 1 章 →
  - icon: 🟣
    title: 第 2 章 · Context Engineering
    details: 管理注意力预算 —— System / Tools / Examples / History 四件套；Context Rot；Just-in-time 检索；Compaction；Agentic Memory；子 Agent。
    link: /zh-cn/02-context-engineering/
    linkText: 进入第 2 章 →
  - icon: 🟠
    title: 第 3 章 · Harness Engineering
    details: 构建可长跑的智能体 —— 工具循环、沙箱、Hook、Session 切换、progress.txt、Planner-Generator-Evaluator；helixent / deer-flow 案例剖析。
    link: /zh-cn/03-harness-engineering/
    linkText: 进入第 3 章 →
  - icon: 🧪
    title: 三个动手实验
    details: 每章配套 5 个可运行 Python demo。Lab1 prompt 模式、Lab2 mini RAG、Lab3 用 200 行 Python 造一个 mini Harness。
    link: /zh-cn/labs
    linkText: 跑实验 →
  - icon: 📖
    title: 一手资料对齐
    details: 内容引自 Anthropic Engineering、OpenAI Cookbook、阿里云百炼、字节 deer-flow、MagicCube helixent 等官方与社区资料。
    link: /zh-cn/04-appendix/references
    linkText: 看完整参考 →
  - icon: 🌐
    title: 中英双语
    details: 完整中文教程 + English version。点击右上角语言切换。代码示例兼容任意 OpenAI-Compatible API。
    link: /en/
    linkText: English →
---

<div style="max-width: 960px; margin: 4rem auto 0; padding: 0 1.5rem;">

## 🗺️ 学习地图

<div style="font-family: var(--vp-font-family-mono); white-space: pre; font-size: 0.85em; line-height: 1.5; background: var(--vp-c-bg-soft); padding: 1.5rem; border-radius: 12px; overflow-x: auto;">
    Prompt Engineering        Context Engineering        Harness Engineering
    ─────────────────         ───────────────────        ───────────────────
    一段精心打磨的指令     →   一整套上下文配置策略    →   模型之外的所有工程
        (字)                      (篇章 / 状态)              (循环 / 工具 / 沙箱)

    📍 第 1 章                 📍 第 2 章                 📍 第 3 章
</div>

## 📋 章节速览

| 章节 | 主题 | 阅读时长 | 实验 |
| :---: | :--- | :---: | :---: |
| [序章](/zh-cn/00-prologue/) | 为什么是 Prompt → Context → Harness | 15 min | — |
| [第 1 章](/zh-cn/01-prompt-engineering/) | Prompt Engineering：把指令说清楚 | 90 min | [Lab 1](/zh-cn/labs) |
| [第 2 章](/zh-cn/02-context-engineering/) | Context Engineering：管理注意力预算 | 120 min | [Lab 2](/zh-cn/labs) |
| [第 3 章](/zh-cn/03-harness-engineering/) | Harness Engineering：构建可长跑的智能体 | 150 min | [Lab 3](/zh-cn/labs) |
| [附录](/zh-cn/04-appendix/) | 术语表 · 路线图 · 参考文献 · 贡献指南 | — | — |

## 🎯 我们想让你在读完之后能做到什么

- ✅ 看到一个新模型 / 新框架，能立刻判断它在 P-C-H 这三层里改的是哪一层。
- ✅ 写出生产级的 System Prompt、Tool Schema、Few-shot 例子。
- ✅ 设计能跑长任务、不"忘"事、不爆窗口的智能体上下文流。
- ✅ 读懂 Claude Code、Codex、Cursor 这类 Coding Agent 的工作原理，并能造一个简化版。

## 🚀 三种推荐学习节奏

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin: 1rem 0;">
  <div style="border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 1.2rem;">
    <strong>🚶 新手（0 经验）</strong><br/>
    按章顺序读，每章配套跑一次 Lab。<br/><br/>
    <em>预计 1 周</em>
  </div>
  <div style="border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 1.2rem;">
    <strong>🚴 有 LLM 应用经验</strong><br/>
    直接跳到第 2、3 章；Lab 必跑。<br/><br/>
    <em>预计 2-3 天</em>
  </div>
  <div style="border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 1.2rem;">
    <strong>🏎️ 想造工具的工程师</strong><br/>
    精读第 3 章 + helixent / deer-flow + Lab 3。<br/><br/>
    <em>预计 1 天</em>
  </div>
</div>

## 🙏 致谢

灵感与展示形式参考 [datawhalechina / easy-vibe](https://github.com/datawhalechina/easy-vibe) 的优秀工作。  
内容方法论来自 Anthropic、OpenAI、阿里云、字节、MagicCube 等团队的公开材料。

</div>
