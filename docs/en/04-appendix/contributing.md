---
title: Contributing Guide
description: How to help us improve this tutorial
---

# Contributing Guide

Contributions of every kind are very welcome!

## Which contributions are most welcome

| Priority | Type | Notes |
| :---: | :--- | :--- |
| 🔥🔥🔥 | **Typo / broken-link fixes** | Just send a PR |
| 🔥🔥🔥 | **Real-world case studies** | "What I built with helixent / deer-flow" — share it with readers |
| 🔥🔥 | **Newer open-source project case studies** | Projects newer than helixent / deer-flow |
| 🔥🔥 | **Code-lab enhancements** | Make the demos more complete and more educational |
| 🔥 | **Translations** | English / Traditional Chinese / Japanese / Korean |
| 🔥 | **New chapters / new topics** | See the [roadmap](./roadmap.md) |

## Writing conventions

- **Chinese primarily, English where needed**: Use Chinese for the main exposition; keep the original English form when a term first appears.
- **At most 6 `##` headings per chapter**: More than that loses the rhythm.
- **Use tables / code blocks / blockquotes**: Reduce long prose paragraphs.
- **Every claim has at least one example**: Purely abstract theory will not be accepted.
- **Link to primary sources**: Blogs / papers / GitHub repos.

## Code conventions

- **Python**: `black` + `ruff`, default config.
- **Minimize dependencies**: Use stdlib when you can; use one package instead of five when you can.
- **Demos must be runnable**: Each demo must produce **meaningful output in under one minute**.
- **OpenAI-Compatible first**: API calls must be compatible with `OPENAI_API_KEY` + `OPENAI_BASE_URL` so domestic Chinese models can run too.

## PR workflow

1. Fork the repo
2. Create a branch: `feat/<short-desc>` or `fix/<short-desc>`
3. Commit → PR
4. Merge after CI passes and at least one reviewer approves

## Issue template

When filing an issue, please include:

```
## Type
- [ ] Typo / broken link
- [ ] Content addition
- [ ] New chapter suggestion
- [ ] Code bug
- [ ] Other

## Description
...

## Files / sections involved
docs/zh-cn/02-context-engineering/01-context-anatomy.md
```

## Credits

All contributors are listed at the bottom of the README. You're also welcome to cite this tutorial on your blog / public account (just credit the source).

---

Back to [appendix home ←](./index.md)
