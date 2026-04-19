---
# === 基本信息 ===
name: docx
version: 2.0.0
description: |
  专业的Word文档创建、编辑和分析技能。支持追踪修改、批注、
  格式保留和文本提取。适用于创建新文档、修改现有文档、
  处理追踪修改、应用模板等场景。

# === 触发器定义（借鉴MiniMax） ===
triggers:
  keywords:
    high_confidence:
      - "创建Word文档"
      - "编辑docx"
      - "Word文档"
      - "追踪修改"
      - "文档批注"
    medium_confidence:
      - "合同"
      - "报告"
      - "提案"
      - "文档"
  patterns:
    - pattern: "(创建|生成|新建|制作).*(文档|合同|报告|提案)"
      confidence: 0.9
      pipeline: create
    - pattern: "(修改|编辑|更新|修订).*.docx"
      confidence: 0.95
      pipeline: edit
    - pattern: "(应用|使用).*模板"
      confidence: 0.85
      pipeline: apply_template
  file_extensions:
    - ".docx"
    - ".docm"
    - ".dotx"
  context:
    - condition: "用户提到'合同'且需要文档"
      suggest_pipeline: apply_template
      suggest_template: legal-contract
    - condition: "用户提到'专利分析报告'"
      suggest_pipeline: apply_template
      suggest_template: patent-analysis-report

# === 元数据 ===
metadata:
  author: "Claude Code Team"
  license: "Proprietary"
  min_claude_version: "1.0.0"
  dependencies:
    - name: pandoc
      version: ">=2.0"
      purpose: "文档格式转换"
    - name: python-docx
      version: ">=0.8.11"
      purpose: "Python DOCX操作"
    - name: ooxml-tools
      purpose: "OOXML底层操作"
  capabilities:
    - document_creation
    - tracked_changes
    - comments
    - formatting_preservation
    - template_application
    - batch_processing
  limitations:
    - "复杂表格布局可能需要手动调整"
    - "宏代码(VBA)不支持"
    - "嵌入式OLE对象有限支持"

# === 管道定义（借鉴MiniMax） ===
pipelines:
  create:
    description: "创建新的Word文档"
    priority: 1
    steps:
      - name: validate_input
        description: "验证输入参数"
        required: true
      - name: generate_content
        description: "生成文档内容"
        required: true
      - name: apply_formatting
        description: "应用格式"
        required: false
      - name: validate_output
        description: "验证输出质量"
        required: true
    output_format: ".docx"

  edit:
    description: "编辑现有文档（支持追踪修改）"
    priority: 2
    steps:
      - name: read_document
        description: "读取现有文档"
        required: true
      - name: identify_changes
        description: "识别需要修改的内容"
        required: true
      - name: apply_tracked_changes
        description: "应用追踪修改"
        required: true
      - name: validate_output
        description: "验证修改结果"
        required: true
    output_format: ".docx"

  apply_template:
    description: "应用模板创建文档"
    priority: 3
    steps:
      - name: select_template
        description: "选择合适的模板"
        required: true
      - name: populate_content
        description: "填充内容到模板"
        required: true
      - name: customize_formatting
        description: "自定义格式"
        required: false
      - name: validate_output
        description: "验证输出质量"
        required: true
    output_format: ".docx"

# === 模板配置 ===
templates:
  built_in:
    - name: legal-contract
      description: "法律合同模板"
      variables: ["party_a", "party_b", "contract_date", "terms"]
    - name: technical-report
      description: "技术报告模板"
      variables: ["title", "author", "date", "sections"]
    - name: patent-analysis-report
      description: "专利分析报告模板"
      variables: ["patent_number", "client_name", "analysis_date", "findings"]
    - name: business-proposal
      description: "商业提案模板"
      variables: ["company", "proposal_title", "date", "budget"]
---

# DOCX 创建、编辑和分析技能 v2.0

## 快速参考

### 三管道工作流

| 管道 | 用途 | 典型命令示例 |
|-----|------|------------|
| **CREATE** | 创建新文档 | "创建一份合同文档" |
| **EDIT** | 编辑现有文档 | "修改report.docx中的日期" |
| **APPLY-TEMPLATE** | 应用模板 | "用法律合同模板创建NDA" |

### 快速命令

```
创建文档:    /docx create [类型] [内容描述]
编辑文档:    /docx edit [文件路径] [修改描述]
应用模板:    /docx template [模板名] [变量值]
验证文档:    /docx validate [文件路径]
```

---

## 工作流决策树

### 场景1：创建新文档

```
用户请求创建文档
        │
        ▼
    需要模板？──是──► 选择APPLY-TEMPLATE管道
        │                    │
        否                   ▼
        │              1. 匹配内置模板
        ▼              2. 填充变量
    选择CREATE管道      3. 生成文档
        │
        ▼
    1. 确定文档类型
    2. 生成内容结构
    3. 应用格式
    4. 输出文档
```

### 场景2：编辑现有文档

```
用户提供文档文件
        │
        ▼
    文档来源？──自己创建──► 简单编辑模式
        │
    他人创建
        │
        ▼
    文档类型？──法律/学术/商业──► 追踪修改模式（必须）
        │
        其他
        │
        ▼
    选择EDIT管道
        │
        ▼
    1. 转换为Markdown预览
    2. 识别修改点
    3. 应用追踪修改
    4. 验证输出
```

---

## 详细操作指南

### 管道1：CREATE（创建新文档）

#### 基本文档创建

```bash
# 使用pandoc从Markdown创建
pandoc input.md -o output.docx

# 带格式选项
pandoc input.md -o output.docx \
  --reference-doc=reference.docx \
  --toc \
  --toc-depth=3
```

#### 使用Python创建

```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# 创建文档
doc = Document()

# 设置标题
title = doc.add_heading('文档标题', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# 添加段落
para = doc.add_paragraph('这是正文内容...')
para.add_run('粗体文字').bold = True
para.add_run('普通文字')

# 添加列表
doc.add_paragraph('列表项1', style='List Bullet')
doc.add_paragraph('列表项2', style='List Bullet')

# 添加表格
table = doc.add_table(rows=3, cols=2)
table.style = 'Table Grid'

# 保存
doc.save('output.docx')
```

### 管道2：EDIT（编辑现有文档）

#### 追踪修改工作流（推荐）

**步骤1：获取Markdown预览**

```bash
pandoc --track-changes=all document.docx -o preview.md
```

**步骤2：识别修改点**

阅读preview.md，确定需要修改的具体内容。

**步骤3：解包文档**

```bash
python ooxml/scripts/unpack.py document.docx unpacked/
```

**步骤4：应用追踪修改**

编辑`unpacked/word/document.xml`，使用追踪修改标记：

```xml
<!-- 删除内容 -->
<w:del w:id="1" w:author="Claude" w:date="2026-03-31T00:00:00Z">
  <w:r>
    <w:delText>原始文字</w:delText>
  </w:r>
</w:del>

<!-- 插入内容 -->
<w:ins w:id="2" w:author="Claude" w:date="2026-03-31T00:00:00Z">
  <w:r>
    <w:t>新文字</w:t>
  </w:r>
</w:ins>
```

**步骤5：打包文档**

```bash
python ooxml/scripts/pack.py unpacked/ modified.docx
```

**步骤6：验证修改**

```bash
pandoc --track-changes=all modified.docx -o verification.md
```

#### 精细化修改原则

```xml
<!-- ❌ 错误：替换整个句子 -->
<w:del>
  <w:r><w:delText>The term is 30 days.</w:delText></w:r>
</w:del>
<w:ins>
  <w:r><w:t>The term is 60 days.</w:t></w:r>
</w:ins>

<!-- ✅ 正确：只修改变化的部分 -->
<w:r w:rsidR="00AB12CD"><w:t>The term is </w:t></w:r>
<w:del>
  <w:r><w:delText>30</w:delText></w:r>
</w:del>
<w:ins>
  <w:r><w:t>60</w:t></w:r>
</w:ins>
<w:r w:rsidR="00AB12CD"><w:t> days.</w:t></w:r>
```

### 管道3：APPLY-TEMPLATE（应用模板）

#### 内置模板列表

| 模板名 | 描述 | 必需变量 |
|-------|------|---------|
| `legal-contract` | 法律合同 | party_a, party_b, contract_date, terms |
| `technical-report` | 技术报告 | title, author, date, sections |
| `patent-analysis-report` | 专利分析报告 | patent_number, client_name, analysis_date |
| `business-proposal` | 商业提案 | company, proposal_title, date, budget |

#### 使用模板

```python
# 模板变量示例
variables = {
    "patent_number": "CN109459075A",
    "client_name": "济南东盛热电有限公司",
    "analysis_date": "2026-03-31",
    "technology_field": "有限空间检测工具",
    "novelty_assessment": "具备新颖性",
    "creativity_assessment": "存在风险"
}

# 应用模板
# 系统会自动：
# 1. 加载templates/patent-analysis-report/template.docx
# 2. 替换占位符
# 3. 填充表格数据
# 4. 生成最终文档
```

---

## 格式规范

### 标题层级

```markdown
# 一级标题（文档标题）
## 二级标题（章节）
### 三级标题（小节）
#### 四级标题（段落标题）
```

### 列表样式

- **无序列表**: 使用 `List Bullet` 样式
- **有序列表**: 使用 `List Number` 样式
- **多级列表**: 使用缩进控制

### 表格格式

```python
# 标准表格样式
table.style = 'Table Grid'

# 表头加粗
for cell in table.rows[0].cells:
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
```

### 页面设置

```python
from docx.shared import Cm

# A4纸张，标准边距
section = doc.sections[0]
section.page_width = Cm(21)
section.page_height = Cm(29.7)
section.left_margin = Cm(2.5)
section.right_margin = Cm(2.5)
section.top_margin = Cm(2.5)
section.bottom_margin = Cm(2.5)
```

---

## 验证机制

### 输入验证

创建或编辑文档前，系统会自动验证：

1. **内容完整性**: 检查必需的变量和内容
2. **格式合规性**: 检查格式提示是否有效
3. **模板存在性**: 检查指定的模板是否存在

### 输出验证

文档生成后，系统会验证：

1. **文件有效性**: 确保是有效的DOCX格式
2. **结构完整性**: 检查必需的XML部件
3. **内容完整性**: 检查必需的内容是否存在
4. **格式正确性**: 检查格式是否符合要求

---

## 常见问题

### Q: 如何处理复杂的表格布局？

A: 对于复杂的表格，建议：
1. 先创建基础结构
2. 使用`pandas`处理数据
3. 手动调整合并单元格

### Q: 如何保留原文档的格式？

A: 使用追踪修改模式：
```bash
pandoc --track-changes=all document.docx -o preview.md
```

### Q: 如何批量处理多个文档？

A: 使用批处理脚本：
```python
import os
from pathlib import Path

for docx_file in Path('.').glob('*.docx'):
    # 处理每个文档
    process_document(docx_file)
```

---

## 相关资源

- [OOXML参考文档](references/ooxml.md)
- [DOCX JavaScript操作](references/docx-js.md)
- [格式化指南](references/formatting.md)
- [模板开发指南](references/template-development.md)

---

**维护者**: Claude Code Team
**最后更新**: 2026-03-31
