<div align="center">

<img src="docs/public/logo.svg" alt="PCH Logo" width="120" />

# Prompt × Context × Harness Engineering

**走完 LLM 应用开发的三次范式跃迁 · The three paradigm shifts of LLM app dev**

[![VitePress Site](https://img.shields.io/badge/📖_Read_Online-VitePress-5b6cff?style=for-the-badge)](#-read-the-tutorial-online)
[![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg?style=for-the-badge)](./LICENSE)
[![Made bilingual](https://img.shields.io/badge/🌐_中文_·_English-Bilingual-success?style=for-the-badge)](#)

</div>

---

## 📖 Read the tutorial online

This repository **is a VitePress site**. The README is just an entry point — please read the tutorial through the site UI for a much better experience (sidebar nav, search, dark mode, language switcher).

### Option A · Run locally

```bash
git clone https://github.com/DocJlm/prompt-context-harness-guide
cd prompt-context-harness-guide
npm install
npm run dev     # opens http://localhost:5173/
```

Then choose:
- 🇨🇳 [简体中文](http://localhost:5173/zh-cn/) — 完整中文教程（推荐）
- 🇬🇧 [English](http://localhost:5173/en/) — Full English version

### Option B · Build for static hosting

```bash
npm run build       # outputs docs/.vitepress/dist
npm run preview     # local preview of the built site
```

Deploy `docs/.vitepress/dist` to GitHub Pages, Vercel, Netlify, or any static host.

---

## 🗺️ What's inside

```
prompt-context-harness-guide/
├── docs/                                  VitePress site (the tutorial itself)
│   ├── .vitepress/
│   │   ├── config.mjs                     Multilingual config (zh-cn + en)
│   │   └── theme/                         Light custom styling
│   ├── index.md                           Landing → choose language
│   ├── zh-cn/                             🇨🇳 Chinese version (full)
│   │   ├── 00-prologue/  ~  04-appendix/  4 chapters + appendix
│   │   └── labs.md
│   └── en/                                🇬🇧 English version (full)
│       ├── 00-prologue/  ~  04-appendix/
│       └── labs.md
└── code/                                  Runnable Python labs
    ├── lab1-prompting/                    5 demos · 第 1 章配套
    ├── lab2-context-rag/                  5 demos · 第 2 章配套
    └── lab3-mini-harness/                 5 demos · 第 3 章配套
```

## 🧪 Run the labs

Each lab is independent. Inside any `code/labN-*/` directory:

```bash
cd code/lab1-prompting
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...    # works with DeepSeek/Qwen/GLM via OPENAI_BASE_URL
python 01_zero_shot.py
```

Full lab walkthroughs live in the site (`/zh-cn/labs` or `/en/labs`).

## 🙏 Credits

Site presentation borrows from the wonderful [datawhalechina/easy-vibe](https://github.com/datawhalechina/easy-vibe).  
Methodology built on public material from Anthropic, OpenAI, Aliyun, ByteDance, and the open-source community.

## 📄 License

- Tutorial content (`docs/`): [CC BY-NC-SA 4.0](./LICENSE)
- Code (`code/`, theme): MIT
