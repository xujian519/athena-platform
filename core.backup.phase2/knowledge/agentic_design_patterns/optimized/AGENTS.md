
# 📚 Agents

> **文件路径**: `AGENTS.md`
> **优化时间**: 2025-12-17 05:10:23
> **阅读模式**: 优化版本

---

## 📋 本页目录

- [Project Structure & Module Organization](#project-structure--module-organization)
- [Build, Test, and Development Commands](#build-test-and-development-commands)
- [Coding Style & Naming Conventions](#coding-style--naming-conventions)
- [Testing Guidelines](#testing-guidelines)
- [Commit & Pull Request Guidelines](#commit--pull-request-guidelines)
- [Agent-Specific Instructions](#agent-specific-instructions)

# Repository Guidelines

## Project Structure & Module Organization

- All content lives at the repository root as numbered Markdown files (e.g., `00-Table-of-Contents.md`, `03-Foreword.md`, `07-Chapter-01.md`).

- Keep bilingual layout per `rules.md` and preserve chapter numbering and order.

- Do not introduce new folders unless discussed; keep images inline links to external sources or propose an `images/` folder in the PR if needed.

## Build, Test, and Development Commands

- Preview Markdown: use your editor’s preview (e.g., VS Code) for quick checks.

- Optional link check: `npx markdown-link-check README.md -q` (run per edited file).

- Optional lint: `npx markdownlint-cli2 .` to catch headings, lists, and spacing issues.

- Quick local server (if embedding images): `python3 -m http.server` and open `http://localhost:8000/`.

## Coding Style & Naming Conventions

- Follow `rules.md` as the single source of truth for translation rules.

- File names: `NN-Title.md` (e.g., `06-What-Makes-Agent.md`, `21-Chapter-15.md`).

- Bilingual format: English paragraph followed by its Chinese translation; short chapters may use separate English/Chinese sections.

- Highlight Chinese with `<mark>…</mark>`; add spaces between Chinese/English and between Chinese/numbers.

- Markdown: GitHub‑flavored Markdown; lists use 2‑space indentation; avoid unnecessary bolding.

## Testing Guidelines

- Before submitting, ensure: no broken links, consistent terminology, matching English/Chinese paragraph pairs, and valid Markdown rendering.

- If using tools: run `markdownlint` and `markdown-link-check` with zero errors for changed files.

- Keep diffs focused—avoid reflowing untouched English source text.

## Commit & Pull Request Guidelines

- Commit messages (English):
  - `Add: [chapter] translation`
  - `Update: [chapter] formatting`
  - `Fix: [issue] in [chapter]`

- Pull Requests must include: clear scope/intent, list of touched files, notes on format decisions, and linked issues. Screenshots are helpful for complex formatting.

## Agent-Specific Instructions

- Only modify targeted chapters; do not renumber files.

- Preserve original English; do not paraphrase. Apply translations and formatting per `rules.md`.

- Keep contributions minimal and reversible; avoid adding tooling/config files without prior discussion.



---

## 🧭 页面导航

- [📖 返回首页](./README.md)
- [📊 查看目录](javascript:showTOC())
- [🔍 搜索内容](javascript:showSearch())
- [⬆️ 返回顶部](javascript:scrollToTop())

## 📚 阅读工具

- 🌙 [深色模式](javascript:toggleDarkMode())
- 📏 [字体大小](javascript:adjustFontSize())
- 🔖 [添加书签](javascript:addBookmark())
- 📤 [导出PDF](javascript:exportPDF())

---

*优化阅读体验 • 专注于中文内容理解*
