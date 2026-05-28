import { defineConfig } from 'vitepress'

// ---------------------------------------------------------------
// Site-wide constants
// ---------------------------------------------------------------
const SITE_TITLE = 'Prompt × Context × Harness'
const REPO = 'https://github.com/your-name/prompt-context-harness-guide'

// ---------------------------------------------------------------
// Sidebar definitions
// ---------------------------------------------------------------
function zhSidebar() {
  return [
    {
      text: '📘 教程总览',
      collapsed: false,
      items: [
        { text: '总览', link: '/zh-cn/' },
        { text: '序章 · 为什么是 P→C→H', link: '/zh-cn/00-prologue/' },
      ],
    },
    {
      text: '🔵 第 1 章 · Prompt Engineering',
      collapsed: false,
      items: [
        { text: '本章导读', link: '/zh-cn/01-prompt-engineering/' },
        { text: '§1.1 Prompt 的解剖学', link: '/zh-cn/01-prompt-engineering/01-fundamentals' },
        { text: '§1.2 七大模式', link: '/zh-cn/01-prompt-engineering/02-patterns' },
        { text: '§1.3 进阶与 GPT-5 时代', link: '/zh-cn/01-prompt-engineering/03-advanced' },
        { text: '§1.4 评估与迭代', link: '/zh-cn/01-prompt-engineering/04-evaluation' },
        { text: '§1.5 动手实验 Lab 1', link: '/zh-cn/01-prompt-engineering/05-lab' },
        { text: '§1.6 参考文献', link: '/zh-cn/01-prompt-engineering/references' },
      ],
    },
    {
      text: '🟣 第 2 章 · Context Engineering',
      collapsed: false,
      items: [
        { text: '本章导读', link: '/zh-cn/02-context-engineering/' },
        { text: '§2.1 上下文的解剖学', link: '/zh-cn/02-context-engineering/01-context-anatomy' },
        { text: '§2.2 检索', link: '/zh-cn/02-context-engineering/02-retrieval' },
        { text: '§2.3 记忆', link: '/zh-cn/02-context-engineering/03-memory' },
        { text: '§2.4 压缩与子 Agent', link: '/zh-cn/02-context-engineering/04-compaction-subagents' },
        { text: '§2.5 动手实验 Lab 2', link: '/zh-cn/02-context-engineering/05-lab' },
        { text: '§2.6 参考文献', link: '/zh-cn/02-context-engineering/references' },
      ],
    },
    {
      text: '🟠 第 3 章 · Harness Engineering',
      collapsed: false,
      items: [
        { text: '本章导读', link: '/zh-cn/03-harness-engineering/' },
        { text: '§3.1 Harness 的解剖学', link: '/zh-cn/03-harness-engineering/01-anatomy' },
        { text: '§3.2 长跑型 Harness', link: '/zh-cn/03-harness-engineering/02-long-running' },
        { text: '§3.3 案例 · helixent', link: '/zh-cn/03-harness-engineering/03-case-helixent' },
        { text: '§3.4 案例 · deer-flow', link: '/zh-cn/03-harness-engineering/04-case-deer-flow' },
        { text: '§3.5 动手实验 Lab 3', link: '/zh-cn/03-harness-engineering/05-build-your-own' },
        { text: '§3.6 参考文献', link: '/zh-cn/03-harness-engineering/references' },
      ],
    },
    {
      text: '📚 附录',
      collapsed: false,
      items: [
        { text: '附录总览', link: '/zh-cn/04-appendix/' },
        { text: '术语表', link: '/zh-cn/04-appendix/glossary' },
        { text: '路线图', link: '/zh-cn/04-appendix/roadmap' },
        { text: '完整参考文献', link: '/zh-cn/04-appendix/references' },
        { text: '贡献指南', link: '/zh-cn/04-appendix/contributing' },
      ],
    },
  ]
}

function enSidebar() {
  return [
    {
      text: '📘 Overview',
      collapsed: false,
      items: [
        { text: 'Introduction', link: '/en/' },
        { text: 'Prologue · Why P→C→H', link: '/en/00-prologue/' },
      ],
    },
    {
      text: '🔵 Chapter 1 · Prompt Engineering',
      collapsed: false,
      items: [
        { text: 'Chapter Intro', link: '/en/01-prompt-engineering/' },
        { text: '§1.1 Anatomy of a Prompt', link: '/en/01-prompt-engineering/01-fundamentals' },
        { text: '§1.2 Seven Patterns', link: '/en/01-prompt-engineering/02-patterns' },
        { text: '§1.3 Advanced · GPT-5 Era', link: '/en/01-prompt-engineering/03-advanced' },
        { text: '§1.4 Eval & Iteration', link: '/en/01-prompt-engineering/04-evaluation' },
        { text: '§1.5 Hands-on Lab 1', link: '/en/01-prompt-engineering/05-lab' },
        { text: '§1.6 References', link: '/en/01-prompt-engineering/references' },
      ],
    },
    {
      text: '🟣 Chapter 2 · Context Engineering',
      collapsed: false,
      items: [
        { text: 'Chapter Intro', link: '/en/02-context-engineering/' },
        { text: '§2.1 Anatomy of Context', link: '/en/02-context-engineering/01-context-anatomy' },
        { text: '§2.2 Retrieval', link: '/en/02-context-engineering/02-retrieval' },
        { text: '§2.3 Memory', link: '/en/02-context-engineering/03-memory' },
        { text: '§2.4 Compaction & Sub-agents', link: '/en/02-context-engineering/04-compaction-subagents' },
        { text: '§2.5 Hands-on Lab 2', link: '/en/02-context-engineering/05-lab' },
        { text: '§2.6 References', link: '/en/02-context-engineering/references' },
      ],
    },
    {
      text: '🟠 Chapter 3 · Harness Engineering',
      collapsed: false,
      items: [
        { text: 'Chapter Intro', link: '/en/03-harness-engineering/' },
        { text: '§3.1 Anatomy of a Harness', link: '/en/03-harness-engineering/01-anatomy' },
        { text: '§3.2 Long-running Harnesses', link: '/en/03-harness-engineering/02-long-running' },
        { text: '§3.3 Case · helixent', link: '/en/03-harness-engineering/03-case-helixent' },
        { text: '§3.4 Case · deer-flow', link: '/en/03-harness-engineering/04-case-deer-flow' },
        { text: '§3.5 Build Your Own', link: '/en/03-harness-engineering/05-build-your-own' },
        { text: '§3.6 References', link: '/en/03-harness-engineering/references' },
      ],
    },
    {
      text: '📚 Appendix',
      collapsed: false,
      items: [
        { text: 'Appendix Index', link: '/en/04-appendix/' },
        { text: 'Glossary', link: '/en/04-appendix/glossary' },
        { text: 'Roadmap', link: '/en/04-appendix/roadmap' },
        { text: 'Full References', link: '/en/04-appendix/references' },
        { text: 'Contributing', link: '/en/04-appendix/contributing' },
      ],
    },
  ]
}

// ---------------------------------------------------------------
// Main config
// ---------------------------------------------------------------
export default defineConfig({
  title: SITE_TITLE,
  description:
    'A complete tutorial on the evolution from Prompt → Context → Harness Engineering, with hands-on labs and case studies of MagicCube/helixent and bytedance/deer-flow.',
  lang: 'zh-CN',
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: true,

  head: [
    ['link', { rel: 'icon', href: '/favicon.svg' }],
    ['meta', { name: 'theme-color', content: '#5b6cff' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: SITE_TITLE }],
    ['meta', {
      property: 'og:description',
      content: 'Prompt × Context × Harness Engineering — complete bilingual tutorial.',
    }],
  ],

  themeConfig: {
    logo: '/logo.svg',

    search: {
      provider: 'local',
      options: {
        locales: {
          'zh-cn': {
            translations: {
              button: { buttonText: '搜索文档', buttonAriaLabel: '搜索文档' },
              modal: {
                noResultsText: '无法找到相关结果',
                resetButtonTitle: '清除查询条件',
                footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' },
              },
            },
          },
        },
      },
    },

    socialLinks: [{ icon: 'github', link: REPO }],

    footer: {
      message:
        'Released under CC BY-NC-SA 4.0 (docs) and MIT (code). Inspired by <a href="https://github.com/datawhalechina/easy-vibe">datawhalechina/easy-vibe</a>.',
      copyright: `© ${new Date().getFullYear()} Prompt × Context × Harness Engineering Tutorial`,
    },
  },

  // ---------------- Locales ----------------
  locales: {
    root: {
      label: '简体中文',
      lang: 'zh-CN',
      link: '/zh-cn/',
      themeConfig: {
        nav: [
          { text: '🏠 总览', link: '/zh-cn/' },
          { text: '📚 章节', items: [
            { text: '序章', link: '/zh-cn/00-prologue/' },
            { text: '第 1 章 · Prompt', link: '/zh-cn/01-prompt-engineering/' },
            { text: '第 2 章 · Context', link: '/zh-cn/02-context-engineering/' },
            { text: '第 3 章 · Harness', link: '/zh-cn/03-harness-engineering/' },
          ] },
          { text: '🧪 动手实验', link: '/zh-cn/labs' },
          { text: '📖 附录', link: '/zh-cn/04-appendix/' },
          { text: 'GitHub', link: REPO },
        ],
        sidebar: {
          '/zh-cn/': zhSidebar(),
        },
        outline: { label: '本页内容', level: [2, 3] },
        docFooter: { prev: '上一节', next: '下一节' },
        lastUpdatedText: '最近更新',
        darkModeSwitchLabel: '主题',
        lightModeSwitchTitle: '切换至浅色模式',
        darkModeSwitchTitle: '切换至深色模式',
        sidebarMenuLabel: '菜单',
        returnToTopLabel: '回到顶部',
        editLink: {
          pattern: `${REPO}/edit/main/docs/:path`,
          text: '在 GitHub 上编辑此页',
        },
      },
    },

    en: {
      label: 'English',
      lang: 'en-US',
      link: '/en/',
      themeConfig: {
        nav: [
          { text: '🏠 Home', link: '/en/' },
          { text: '📚 Chapters', items: [
            { text: 'Prologue', link: '/en/00-prologue/' },
            { text: 'Ch 1 · Prompt', link: '/en/01-prompt-engineering/' },
            { text: 'Ch 2 · Context', link: '/en/02-context-engineering/' },
            { text: 'Ch 3 · Harness', link: '/en/03-harness-engineering/' },
          ] },
          { text: '🧪 Labs', link: '/en/labs' },
          { text: '📖 Appendix', link: '/en/04-appendix/' },
          { text: 'GitHub', link: REPO },
        ],
        sidebar: {
          '/en/': enSidebar(),
        },
        outline: { label: 'On this page', level: [2, 3] },
        docFooter: { prev: 'Previous', next: 'Next' },
        editLink: {
          pattern: `${REPO}/edit/main/docs/:path`,
          text: 'Edit this page on GitHub',
        },
      },
    },
  },
})
