# Translation Rules and Guidelines | 翻译规则和指南

## Project Overview | 项目概述

本项目旨在将《Agentic Design Patterns: A Hands-On Guide to Building Intelligent Systems》完整翻译为中英文对照版本，为中文读者提供优质的智能体设计模式学习资源。

## Core Principles | 核心原则

### 1. Accuracy and Faithfulness | 准确性和忠实性

- 翻译内容必须与原文含义完全一致
- 不得随意添加、删除或修改原文内容
- 保持原文的逻辑结构和论述顺序

### 2. Readability and Localization | 可读性和本土化

#### 翻译质量标准（信雅达原则）

- **信（Faithfulness）**：准确传达原文含义
  - 不得曲解、漏译或随意增译
  - 保持原文的逻辑结构和论述层次
  - 技术概念必须精确对应
  
- **达（Expressiveness）**：清晰易懂，符合中文表达习惯
  - 减少不必要的长句，适当断句
  - 避免生硬直译，采用地道的中文表达
  - 优先考虑读者理解，而非逐字对应
  
- **雅（Elegance）**：优美流畅，有文采但不过度
  - 保持技术文档的专业性和严谨性
  - 避免过度文学化或诗意化
  - 在准确性基础上追求表达的优雅

#### 具体实践

- **长句处理**：英文复杂句可拆分为多个中文短句
  - 单个中文段落避免超过 3-4 行
  - 代码说明等技术性段落适当拆分，提高可读性
  - 使用空行分隔不同层次的说明

- **意译许可**：为提升流畅度，允许必要的意译和句式调整
- **段落对应**：保持段落级别的对应，但句子可灵活处理
- **语体统一**：全书语体保持一致，避免风格断层

- **冗余词汇处理**：删除不必要的冗余词汇，使表达更简洁
  - ❌ "一个系统" → ✅ "系统"
  - ❌ "您可以" → ✅ "可以"
  - ❌ "Google 的 Gemini" → ✅ "Google Gemini"
  - ❌ "它可以先对传入查询进行分类以判断" → ✅ "它可以先对传入查询进行分类，判断"

- **避免口语化**：减少不必要的过渡词和口语表达
  - ❌ "那么"、"好的"、"其实" 等过渡词
  - ✅ 直接表达主要内容

- **强调适度**：加粗文本仅在非常必要时使用

#### 常见问题避免

- ❌ 过度诗化（如："一束全新而灿烂的光"）
- ❌ 生硬直译（如："在岗精进"）
- ❌ 术语不当（如：用 HR 语境的词汇描述 AI）
- ❌ 风格不一（如：同一文档中混用文言与白话）

## Format Requirements | 格式要求

### 1. Document Structure | 文档结构

- 使用相同的格式（包含标题、内容概要、目录和正文）
- 各部分之间使用横线分隔（`---`）
- 在二级标题之间增加横线分隔，提升阅读体验

#### 章节标题格式

所有章节标题采用双语对照格式：

```markdown
# Chapter N: Title | <mark>第 N 章：标题</mark>

## Section Title | <mark>章节标题</mark>

## At a Glance | <mark>要点速览</mark>
```

#### 章节固定术语翻译

| English | 中文 | 说明 |
|---------|------|------|
| At a Glance | 要点速览 | 章节速览部分 |
| What | 问题所在 | 问题描述 |
| Why | 解决之道 | 解决方案 |
| Rule of Thumb | 经验法则 | 使用建议 |
| Visual summary | 可视化总结 | 图示总结 |
| Conclusion | 结语 | 章节结尾 |
| Key Takeaways | 核心要点 | 要点总结 |
| Hands-On Code Example | 使用 XX 的实战代码 | 代码示例标题 |

### 2. Markdown Syntax | Markdown 语法

- 使用正确的 Markdown 语法
- 避免因前后空格导致无法渲染的问题
- 所有代码块必须使用正确的格式标记

### 3. Bilingual Layout | 双语布局

#### For Short Content (致谢等短章节)

使用完整英文 + 完整中文的分隔格式：

```markdown
## English | 英文
[完整英文内容]

---

## Chinese | 中文
[完整中文翻译]
```

#### For Long Content (正文章节等)

使用段落对照格式：

```markdown
[English paragraph 1]

[对应的中文翻译段落 1]

[English paragraph 2]

[对应的中文翻译段落 2]
```

### 4. Highlighting System | 高亮系统

#### 主要方案（推荐）

- **HTML `<mark>` 标签**：`<mark>中文内容</mark>`
  - ✅ GitHub 完美支持
  - ✅ 黄色高亮背景，视觉效果佳
  - ✅ 所有现代浏览器兼容
  - 📝 使用场景：所有中文翻译内容

#### 特殊场景格式

- **表格对照**：适用于术语表、短句对比
- **引用块 + 粗体**：`> **中文内容**` 适用于重要强调
- **当前分隔格式**：长章节可保持 English/中文 分区结构

### 5. Mark + Markdown Rendering | 高亮与 Markdown 渲染

- `<mark>` 内不要依赖 Markdown 语法渲染加粗/斜体；请使用 HTML 标签：
  - 加粗：`<mark><strong>文本</strong></mark>`
  - 斜体：`<mark><em>文本</em></mark>`
- 列表标记必须在 `<mark>` 外，保证语义与渲染正确：
  - 无序：`- <mark>条目内容</mark>`（而非 `<mark>- 条目内容</mark>`）
  - 有序：`1. <mark>条目内容</mark>`（而非 `<mark>1. 条目内容</mark>`）
- 图注统一格式：`<mark>图 N：说明文字</mark>`。
- 在中文段内引用英文缩写或术语时，使用中文全角括号：`大语言模型（LLM）`、`检索增强生成（RAG）`、`小语言模型（SLM）`。
- 中文引号统一为「」；避免在中文段中使用英文直引号（""）。
- 若需在高亮内显示强调性小标题（如「什么/为什么/经验法则/可视化总结」），使用：`<mark><strong>小标题：</strong>后续说明</mark>`。
- 不在正文中加入进度或编辑性标注（如「已完成/代码正常」），此类信息仅出现在 PR 描述或 Issue 中。

#### 参考文献格式

参考文献采用独立行格式：

```markdown
1. Source Title: [URL](URL)

   <mark>来源标题：[URL](URL)</mark>

2. Another Source: [URL](URL)

   <mark>另一来源：[URL](URL)</mark>
```

### 6. Lists & Emphasis Patterns | 列表与强调规范

- 列表内的关键短语可加粗，但仍放在 `<mark>` 中：`- <mark><strong>用例：</strong>说明……</mark>`。
- 需要中英文并列的行内强调时，中文放 `<mark>` 内，英文保持原样；不要在 `<mark>` 内再嵌套 Markdown 语法。
- 斜体文本在 `<mark>` 内请使用 `<em>`；避免使用 `*斜体*`。

### 7. Names, Titles & Captions | 姓名、头衔与标题

- 中文段中的人名/头衔如需加粗：`<mark><strong>姓名 / 头衔</strong></mark>`。
- 段内术语的第一次出现可使用「中文（EN）」形式；后续保持一致，不要在同一章节中变更写法。

### 8. Tone & Pronouns | 语气与人称

- 中文段优先使用「你/你的」保持一致；避免同段混用「您/你」。
- 技术用语直译不通顺时，优先保证中文可读性与专业性。

### 9. Quick QA Checks | 快速自检

#### 格式检查

- 搜索加粗在高亮内是否使用了 `<strong>`：`rg -n "<mark><strong>"`
- 搜索列表是否把标记放在 `<mark>` 外：
  - 有序：`rg -n "^<mark>\s*\d+\."` 应为 0
  - 无序：`rg -n "^<mark>\s*[-*+]"` 应为 0
- 搜索图注是否使用统一格式：`rg -n "<mark>图\s*\d+："`

#### 标点检查

- 搜索中文段中的英文直引号：`grep -r "\"" --include="*.md"` 并替换为「」
- 搜索英文半角括号：`grep -r " (" --include="*.md"` 检查是否应为全角
- 术语括注是否为中文全角括号：`（LLM）`、`（RAG）`、`（MCP）`

#### 术语检查

- 搜索残留"代理"：`grep -r "代理" --include="*.md"` 应全部改为"智能体"
- 检查术语一致性：确保 Agent/Agentic/Canvas 等翻译统一
- 检查代码术语格式化：在代码说明段落中，类名、函数名、变量名是否使用 `<code>` 标签

#### 质量检查

- 是否有"可可靠"等重复字符（笔误）
- 长句是否适当断句（避免超过 50 字的单句）
- 是否有过度文学化表达

### 10. PR Review Checklist | PR 审阅清单

#### 内容质量

- [ ] 双语对照是否一一对应，中文段均使用 `<mark>` 包裹
- [ ] 翻译符合"信雅达"标准：准确、流畅、优雅
- [ ] 无曲解、漏译或过度增译
- [ ] 长句已适当断句，易于理解
- [ ] 语体风格统一，无文白夹杂

#### 格式规范

- [ ] 高亮内的加粗/斜体使用 `<strong>/<em>`，未混用 Markdown
- [ ] 列表、有序/无序格式正确（标记在 `<mark>` 外）
- [ ] 图注格式统一：`<mark>图 N：说明</mark>`
- [ ] 编号与正文引用一致

#### 术语统一

- [ ] 核心术语统一（智能体、具智能体特性、技术底座）
- [ ] 无残留"代理"等禁用术语
- [ ] 首次出现采用"中文（English）"格式
- [ ] 技术缩写使用全角括号：`（LLM）`、`（RAG）`

#### 标点符号

- [ ] 引号统一使用「」，无英文直引号 ""
- [ ] 括号规范：中文全角（），英文半角 ()
- [ ] 破折号（——）、顿号（、）、逗号（，）使用正确
- [ ] 冒号（：）使用恰当，未过度使用

#### 其他检查

- [ ] 无进度性标注或注释性语句混入正文
- [ ] 链接和引用正确
- [ ] 中英文、中文数字间有空格
- [ ] 无明显笔误或重复字符

## Translation Guidelines | 翻译指南

### 1. Technical Terms | 技术术语

#### 核心术语统一

| English | 中文 | 说明 | 首次出现格式 |
|---------|------|------|------------|
| Agent | 智能体 | 核心概念，禁用"代理" | 智能体（Agent） |
| Agentic | 具智能体特性 / 智能体式 | 形容词，视语境选用 | 具智能体特性 |
| AI Agent | AI 智能体 | 完整表述 | AI 智能体 |
| Multi-Agent | 多智能体 | 复合词 | 多智能体 |
| Canvas | 技术底座 | 隐喻性术语 | 技术底座（canvas） |

#### 翻译原则

- **首次出现**：使用"中文（English）"格式标注
- **后续出现**：直接使用中文，保持一致
- **专有名词**：Google、GitHub、LangChain 等保持英文
- **技术缩写**：LLM、RAG、API 等保持大写，用全角括号注释
  - 例：大语言模型（LLM）

#### 禁用术语

- ❌ **"代理"** → 必须使用 **"智能体"**
- ❌ **"代理人"** → 必须使用 **"智能体"**
- ❌ **"Agent 代理"** → 必须使用 **"智能体"**

#### 术语一致性检查

- 使用 `grep -r "代理" --include="*.md"` 检查残留
- 全书术语必须保持统一，不可混用

#### 代码术语格式化

在中文翻译中引用代码组件、类名、函数名、变量名时，应使用 `<code>` 标签包裹，以提高可读性和专业性。

**何时使用 `<code>` 标签：**

- ✅ **类名**：`<code>ChatOpenAI</code>`、`<code>RunnableParallel</code>`、`<code>LlmAgent</code>`
- ✅ **函数/方法名**：`<code>ainvoke</code>`、`<code>run_parallel_example</code>`、`<code>asyncio.run</code>`
- ✅ **变量名**：`<code>map_chain</code>`、`<code>full_parallel_chain</code>`、`<code>output_key</code>`
- ✅ **模型名称**：`<code>gpt-4o-mini</code>`、`<code>GEMINI_MODEL</code>`
- ✅ **代码符号/运算符**：`<code>|</code>`、`<code>if __name__ == "__main__":</code>`
- ✅ **配置项/参数**：`<code>temperature</code>`、`<code>try-except</code>`

**何时不使用 `<code>` 标签：**

- ❌ **框架名称**：LangChain、Google ADK、Python（这些作为产品/语言名称，不需要标记）
- ❌ **概念性术语**：智能体、提示链、并行化（这些是翻译后的中文概念术语）
- ❌ **技术缩写**：LLM、RAG、API（这些使用全角括号注释即可）

**示例对比：**

```markdown
❌ 错误：代码从 langchain_openai 和 langchain_core 导入了关键模块，包含 ChatOpenAI、RunnableParallel 等组件。

✅ 正确：代码从 <code>langchain_openai</code> 和 <code>langchain_core</code> 导入了关键模块，包含 <code>ChatOpenAI</code>、<code>RunnableParallel</code> 等组件。
```

### 2. Spacing Rules | 空格规则

- 中文和英文之间增加一个空格
- 中文和数字之间增加一个空格
- 例：AI 系统，GPT 4 模型，21 个章节

### 3. Punctuation | 标点符号

#### 基本规则

- 中文语境下使用中文标点符号
- 保持原文的标点逻辑和节奏

#### 引号规范

- **强制使用**：中文直角引号「」（U+300C/U+300D）
  - ✅ 正确：「智能体」「引擎」「造车」
  - ❌ 错误：避免使用英文直引号 "" 或弯引号 ""
- **特殊场景**：英文术语或专有名词在中文段落中可不加引号
  - 例：LLM、RAG、Google、GitHub

#### 括号规范

- **中文全角括号**：用于注释、补充说明
  - ✅ 正确：大语言模型（LLM）、检索增强生成（RAG）
  - ❌ 错误：大语言模型 (LLM)、检索增强生成 (RAG)
- **英文半角括号**：仅用于纯英文内容或数学公式

#### 破折号与连接号

- **破折号（——）**：用于解释说明、语气转折
  - 例：这一次确实变了——话题的重心明显转移
- **连字符（-）**：用于复合词
  - 例：多智能体系统、端到端流程

#### 顿号与逗号

- **顿号（、）**：用于简单并列（3 项以内）
  - 例：感知、规划、行动
- **逗号（，）**：用于复杂并列或分句
  - 例：感谢 A 的贡献，感谢 B 的指导，也感谢 C 的支持

#### 冒号使用

- **中文冒号（：）**：用于引出说明、列举
  - 例：我们必须做到：保持透明，对结果负责
- 避免在列表项中过度使用冒号

### 4. Cultural Adaptation | 文化适配

- 适应中文读者的阅读习惯
- 保持专业性和准确性
- 避免过度本土化影响原意

## Quality Control | 质量控制

### 1. Review Process | 审校流程

- 每章完成后进行自我审校
- 检查术语一致性
- 验证格式规范性
- 确保链接和引用正确

### 2. Consistency Checks | 一致性检查

- 术语翻译保持统一
- 格式标准保持一致
- 文档结构保持规范

## File Naming Convention | 文件命名规范

```text
00-Table-of-Contents.md                    # 目录
01-Dedication.md                          # 致谢
02-Acknowledgment.md                      # 鸣谢
03-Foreword.md                           # 前言
04-Thought-Leader.md                     # 思想领袖观点
05-Introduction.md                       # 介绍
06-What-Makes-Agent.md                   # 什么是智能体
07-Chapter-01-Prompt-Chaining.md        # 第一章：提示链
08-Chapter-02-Routing.md                 # 第二章：路由
09-Chapter-03-Parallelization.md        # 第三章：并行化
10-Chapter-04-Reflection.md              # 第四章：反思
11-Chapter-05-Tool-Use.md                # 第五章：工具使用
12-Chapter-06-Planning.md                # 第六章：规划
13-Chapter-07-Multi-Agent-Collaboration.md # 第七章：多智能体协作
...
rules/rules.md                                 # 本规则文档
```

## Git Workflow | Git 工作流程

### 1. Commit Messages | 提交信息

使用清晰的英文提交信息：

```text
Add: [chapter name] translation
Update: [chapter name] formatting
Fix: [specific issue] in [chapter name]
```

### 2. File Organization | 文件组织

- 保持仓库结构清晰
- 及时提交进度
- 添加适当的说明文档

## Common Translation Patterns | 常用翻译模式

### Technical Terms Dictionary | 技术术语词典

| English | 中文 | 备注 |
|---------|------|------|
| Agent | 智能体 | 核心概念 |
| Sub-agent | 子智能体 | |
| Multi-Agent | 多智能体 | |
| Agentic system | 智能体系统 | |
| Prompt Chaining | 提示链 | |
| Routing | 路由 | |
| Parallelization | 并行化 | |
| Reflection | 反思 | |
| Tool Use | 工具使用 | |
| Planning | 规划 | |
| Memory Management | 记忆管理 | |
| Human-in-the-Loop | 人机协同 | |
| RAG | 检索增强生成 | 保留英文缩写 |
| LLM | 大语言模型 | Large Language Model |
| Concurrency | 并发性 | 与并行性 (Parallelism) 区分 |
| Parallelism | 并行性 | 与并发性 (Concurrency) 区分 |
| Model Context Protocol | 模型上下文协议 | 英文缩写为：MCP |
| Tool Function Calling | 工具函数调用 | |


## Quality Standards | 质量标准

### 1. Translation Quality | 翻译质量

#### 信雅达三重标准

- **准确性（信）**：100% 忠实原文，无曲解漏译
  - 技术概念精确对应
  - 逻辑结构完整保留
  - 关键信息不得遗漏
  
- **流畅性（达）**：符合中文表达习惯
  - 避免生硬直译
  - 长句适当断句
  - 优先考虑读者理解
  
- **优雅性（雅）**：保持技术文档的专业性
  - 表达优美但不过度
  - 避免过度文学化
  - 保持语体一致

#### 常见问题及修正示例

| 问题类型 | ❌ 错误示例 | ✅ 正确示例 |
|---------|-----------|-----------|
| 过度诗化 | "一束全新而灿烂的光" | "全新而灿烂的光" |
| 生硬直译 | "在岗精进的智能助理" | "边做边学的智能助理" |
| 笔误 | "可可靠达成" | "能够可靠达成" |
| 术语错误 | "代理系统" | "智能体系统" |
| 括号错误 | "大语言模型 (LLM)" | "大语言模型（LLM）" |
| 引号错误 | "智能体"系统 | 「智能体」系统 |

### 2. Format Compliance | 格式合规性

- Markdown 语法正确率：100%
- 双语对照格式统一
- 高亮标记使用恰当

### 3. Consistency | 一致性

- 术语翻译前后统一
- 格式标准贯穿全文
- 文档结构保持规范

---

## Version History | 版本历史

- **v1.3 (2025-10-13)**: 新增代码术语格式化规范
  - 新增"代码术语格式化"章节，规范 `<code>` 标签使用
  - 定义何时使用/不使用 `<code>` 标签的明确准则
  - 提供类名、函数名、变量名等代码组件的标记示例
  - 更新快速自检命令，增加代码术语格式化检查
  - 已在第三章应用新规范，作为后续章节参考

- **v1.2 (2025-10-12)**: 基于前三章翻译实践优化规则
  - 新增章节标题格式规范（双语对照格式）
  - 新增章节固定术语翻译表（At a Glance、Conclusion 等）
  - 增强长段落处理规则（单段不超过 3-4 行）
  - 新增冗余词汇处理指南（"一个"、"您"、"的"等）
  - 完善技术术语词典（新增子智能体、并发性等）
  - 新增参考文献格式规范

- **v1.1 (2025-10-10)**: 优化翻译质量规范
  - 新增"信雅达"三重标准详细说明
  - 完善标点符号使用规范（引号、括号、破折号等）
  - 强化术语统一要求（智能体、具智能体特性、技术底座）
  - 新增常见问题及修正示例表
  - 扩充 PR 审阅清单，增加质量和术语检查
  - 更新快速自检命令，包含术语和质量检查

- **v1.0 (2025-10-09)**: 初始版本，建立基础规则和格式标准

---

*本规则文档将随着项目进展持续更新和完善。*
