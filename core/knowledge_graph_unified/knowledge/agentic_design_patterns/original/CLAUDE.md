# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **bilingual Chinese-English translation project** of "Agentic Design Patterns: A Hands-On Guide to Building Intelligent Systems" by Antonio Gulli. The project provides a comprehensive technical guide covering 21 core agentic design patterns for building intelligent AI systems.

**Key Characteristics:**
- Pure documentation/translation project (no code to build, test, or run)
- All content is in Markdown format
- Uses HTML `<mark>` tags for Chinese text highlighting
- Follows strict bilingual format with English and Chinese side-by-side
- Original book has 424 pages across 21 chapters plus appendices

## File Structure

```
00-Table-of-Contents.md     # Main table of contents
01-Dedication.md            # Dedication section
02-Acknowledgment.md        # Acknowledgment section
03-Foreword.md             # Foreword by Google VP
04-Thought-Leader.md       # Thought leader perspective (in progress)
05-Introduction.md         # Introduction (not yet translated)
06-What-Makes-Agent.md     # What makes an AI system an agent (not yet translated)
07-Chapter-01.md           # Chapter 1: Prompt Chaining (not yet translated)
...                        # Subsequent chapters follow same naming pattern
rules.md                   # Translation rules and guidelines
README.md                  # Project README with bilingual content
```

## Translation Format and Rules

### Mandatory Highlighting System

**All Chinese translations MUST use HTML `<mark>` tags:**
```markdown
English text here.

<mark>中文翻译在这里。</mark>
```

This creates yellow highlighting for Chinese content on GitHub, making it easy to distinguish between languages.

### Two Layout Formats

**1. Short Content (Dedication, Acknowledgment, Foreword):**
```markdown
## English | 英文
[Complete English content]

---

## Chinese | 中文
[Complete Chinese translation]
```

**2. Long Content (Chapters):**
```markdown
[English paragraph 1]

<mark>[中文翻译段落 1]</mark>

[English paragraph 2]

<mark>[中文翻译段落 2]</mark>
```

### Technical Term Conventions

Keep important terms in English with Chinese in parentheses on first use:
- Agent → 智能体 (Agent)
- Prompt Chaining → 提示链 (Prompt Chaining)
- RAG → 检索增强生成 (RAG)
- Human-in-the-Loop → 人在回路中 (Human-in-the-Loop)

Reference the technical term dictionary in rules.md:1-179 for consistent translations.

### Spacing Rules

- Add space between Chinese and English: `AI 系统`
- Add space between Chinese and numbers: `21 个章节`
- Use Chinese punctuation in Chinese context
- Use English punctuation in English context

### Format Requirements

- Use horizontal rules (`---`) to separate major sections
- Add horizontal rules between level-2 headings for readability
- Preserve all original code example links (Google Colab/Drive)
- Maintain exact Markdown formatting from original
- Use proper Chinese quotation marks: 「」 or ""

## Translation Quality Standards

1. **Accuracy**: 100% faithful to original meaning
2. **Fluency**: Natural Chinese expression that follows local conventions
3. **Technical Precision**: Maintain technical document rigor
4. **Consistency**: Uniform terminology throughout
5. **Format Compliance**: 100% correct Markdown syntax

See rules.md:1-179 for complete translation guidelines.

## Project Status

The project is being translated chapter by chapter:
- ✅ Completed: Dedication, Acknowledgment, Foreword
- 🚧 In Progress: Thought Leader's Perspective
- ⏳ Pending: Introduction and all chapters

Check README.md:33-87 for detailed progress tracking.

## Common Tasks

### Adding a New Translation

1. Follow the file naming convention (e.g., `07-Chapter-01.md`)
2. Use appropriate layout format (short vs. long content)
3. Apply `<mark>` tags to ALL Chinese text
4. Preserve original structure and links
5. Follow technical term dictionary for consistency
6. Update README.md checklist when complete

### Reviewing Translations

Check for:
- `<mark>` tags around all Chinese content
- Consistent technical term usage (check rules.md dictionary)
- Proper spacing between Chinese/English and numbers
- Horizontal rules between major sections
- All code links preserved and functional
- Correct Markdown syntax rendering

### Git Commit Messages

Use English commit messages with clear descriptions:
```
Add: [chapter name] translation
Update: [chapter name] formatting
Fix: [specific issue] in [chapter name]
```

## Important Notes

- **No build/test/run commands**: This is a pure documentation project
- **All files are Markdown**: No code compilation or execution needed
- **GitHub is the primary viewing platform**: Format optimized for GitHub rendering
- **Yellow highlighting is essential**: `<mark>` tags are mandatory for all Chinese text
- **Original book charity**: All royalties donated to Save the Children
- **License**: Translation released under CC BY 4.0

## The 21 Core Agentic Design Patterns

For context, the book covers these patterns across four parts:

**Part One (Core Patterns):**
1. Prompt Chaining
2. Routing
3. Parallelization
4. Reflection
5. Tool Use
6. Planning
7. Multi-Agent

**Part Two (Advanced Patterns):**
8. Memory Management
9. Learning and Adaptation
10. Model Context Protocol (MCP)
11. Goal Setting and Monitoring

**Part Three (Integration Patterns):**
12. Exception Handling and Recovery
13. Human-in-the-Loop
14. Knowledge Retrieval (RAG)

**Part Four (Production Patterns):**
15. Inter-Agent Communication (A2A)
16. Resource-Aware Optimization
17. Reasoning Techniques
18. Guardrails/Safety Patterns
19. Evaluation and Monitoring
20. Prioritization
21. Exploration and Discovery

## Resources

- **Original Book**: [Amazon Link](https://www.amazon.com/Agentic-Design-Patterns-Hands-Intelligent/dp/3032014018/)
- **Translation Rules**: rules.md
- **Progress Tracking**: README.md Table of Contents
- **Code Examples**: Linked in each chapter (Google Colab/Drive)
