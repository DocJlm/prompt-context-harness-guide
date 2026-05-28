<div align="center">

<img src="docs/public/logo.svg" alt="PCH Logo" width="120" />

# Prompt × Context × Harness Engineering

**走完 LLM 应用开发的三次范式跃迁 · The three paradigm shifts of LLM app dev**

<p>
<a href="https://docjlm.github.io/prompt-context-harness-guide/">
  <img src="https://img.shields.io/badge/🌐_在线阅读_·_Read_Online-5b6cff?style=for-the-badge" alt="Read Online" height="34" />
</a>
<a href="https://docjlm.github.io/prompt-context-harness-guide/zh-cn/">
  <img src="https://img.shields.io/badge/🇨🇳_中文版-中文_推荐-success?style=for-the-badge" alt="Chinese" height="34" />
</a>
<a href="https://docjlm.github.io/prompt-context-harness-guide/en/">
  <img src="https://img.shields.io/badge/🇬🇧_English-Full_Translation-blue?style=for-the-badge" alt="English" height="34" />
</a>
</p>

[![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](./LICENSE)
[![Stars](https://img.shields.io/github/stars/DocJlm/prompt-context-harness-guide?style=social)](https://github.com/DocJlm/prompt-context-harness-guide)

**🚀 [立即开始阅读 →](https://docjlm.github.io/prompt-context-harness-guide/)**

</div>

---

## ✨ 这是什么 · What is this?

> 一份**开源、完整、可动手**的中文+英文双语教程。  
> 系统拆解 LLM 应用开发从 **Prompt Engineering** → **Context Engineering** → **Harness Engineering** 的三次范式跃迁。

### 三章地图

| 章节 | 主题 | 实验 |
| :---: | :--- | :---: |
| [🔵 第 1 章](https://docjlm.github.io/prompt-context-harness-guide/zh-cn/01-prompt-engineering/) | Prompt Engineering · 把指令说清楚 | [Lab 1](https://docjlm.github.io/prompt-context-harness-guide/zh-cn/labs) |
| [🟣 第 2 章](https://docjlm.github.io/prompt-context-harness-guide/zh-cn/02-context-engineering/) | Context Engineering · 管理注意力预算 | [Lab 2](https://docjlm.github.io/prompt-context-harness-guide/zh-cn/labs) |
| [🟠 第 3 章](https://docjlm.github.io/prompt-context-harness-guide/zh-cn/03-harness-engineering/) | Harness Engineering · 构建可长跑的智能体 | [Lab 3](https://docjlm.github.io/prompt-context-harness-guide/zh-cn/labs) |

### 亮点

- 📖 **完整的双语网站**（VitePress 驱动，含搜索 / 暗色模式 / 侧边栏 / 锚点导航）
- 🌐 **中英文 1:1 同步**（29 + 29 篇 markdown，结构对称）
- 🧪 **3 个可运行 Python 实验**（兼容 OpenAI / DeepSeek / 通义 / 智谱 / Kimi 任意 OpenAI-Compatible API）
- 🔬 **工业级开源项目源码导读**：[helixent](https://github.com/MagicCube/helixent) + [deer-flow](https://github.com/bytedance/deer-flow)
- 📚 **一手资料对齐**：Anthropic Engineering · OpenAI Cookbook · 阿里云百炼 · ByteDance ...

---

## 🌐 在线阅读 · Live Site

**主入口（GitHub Pages）**：

| 语言 | 链接 |
| :--- | :--- |
| 🇨🇳 简体中文 | <https://docjlm.github.io/prompt-context-harness-guide/zh-cn/> |
| 🇬🇧 English | <https://docjlm.github.io/prompt-context-harness-guide/en/> |

> ⚠️ **第一次访问 404？** 仓库需要先启用 GitHub Pages：  
> 1. 推送代码到 `main` 分支 → 触发自动构建  
> 2. 在 GitHub 仓库页 **Settings → Pages → Source** 选 **GitHub Actions**  
> 3. 等待 ~1 分钟，Actions 会自动部署到上面的 URL  
> 之后每次 push 到 `main`，站点自动重新发布。

---

## 💻 本地运行 · Run Locally

```bash
git clone https://github.com/DocJlm/prompt-context-harness-guide
cd prompt-context-harness-guide
npm install
npm run dev         # → http://localhost:5173/
```

构建静态站：

```bash
npm run build       # 输出到 docs/.vitepress/dist
npm run preview     # 本地预览构建产物
```

---

## ⚡ 一键部署到别处 · One-click Deploy Elsewhere

不想用 GitHub Pages？直接部署到 Vercel / Netlify：

<p>
<a href="https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FDocJlm%2Fprompt-context-harness-guide">
  <img src="https://vercel.com/button" alt="Deploy to Vercel" height="32" />
</a>
&nbsp;
<a href="https://app.netlify.com/start/deploy?repository=https://github.com/DocJlm/prompt-context-harness-guide">
  <img src="https://www.netlify.com/img/deploy/button.svg" alt="Deploy to Netlify" height="32" />
</a>
</p>

部署到根域名（如 Vercel）时，无需任何环境变量；  
部署到子路径（如 GitHub Pages `user.github.io/repo/`）时，已配好 `VITEPRESS_BASE` 环境变量。

---

## 🗂️ 仓库结构 · Repo layout

```
prompt-context-harness-guide/
├── docs/                                  VitePress 站点（教程本体）
│   ├── .vitepress/config.mjs              多语言配置 (zh-cn + en)
│   ├── index.md                           落地页（选语言）
│   ├── zh-cn/                             🇨🇳 中文完整版
│   └── en/                                🇬🇧 English 完整版
├── code/                                  可运行 Python 实验
│   ├── lab1-prompting/                    5 demos · 第 1 章配套
│   ├── lab2-context-rag/                  5 demos · 第 2 章配套
│   └── lab3-mini-harness/                 5 demos · 第 3 章配套
├── package.json                           VitePress 依赖
├── vercel.json                            Vercel 部署配置
├── netlify.toml                           Netlify 部署配置
└── .github/workflows/deploy.yml           GitHub Pages 自动部署
```

---

## 🧪 跑实验 · Run the Labs

每个 lab 独立。进入对应目录：

```bash
cd code/lab1-prompting
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...                  # 兼容 DeepSeek / 通义 / 智谱
export OPENAI_BASE_URL=https://api.openai.com/v1   # 可选
python 01_zero_shot.py
```

详细说明：网站 [`/zh-cn/labs`](https://docjlm.github.io/prompt-context-harness-guide/zh-cn/labs) 或 [`/en/labs`](https://docjlm.github.io/prompt-context-harness-guide/en/labs)。

---

## 🙏 致谢 · Credits

- 站点形式参考 [datawhalechina/easy-vibe](https://github.com/datawhalechina/easy-vibe)
- 方法论来自 Anthropic、OpenAI、阿里云、字节跳动、MagicCube 等团队公开材料
- 开源项目案例：[helixent](https://github.com/MagicCube/helixent) · [deer-flow](https://github.com/bytedance/deer-flow)

## 📄 协议 · License

- 文档（`docs/`）：[CC BY-NC-SA 4.0](./LICENSE)
- 代码（`code/`, theme）：MIT
