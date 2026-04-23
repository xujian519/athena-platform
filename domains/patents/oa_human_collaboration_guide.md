# 审查意见答复人机协作系统使用指南

## 📋 系统概述

智能审查意见答复系统现已增强人机协作功能，提供从文档解析到答复生成的完整工作流程。

### 核心特性

1. **智能文档解析** - 支持PDF、Word、图片OCR等多种格式
2. **结构化信息提取** - 自动提取目标专利信息、对比文件详细信息等
3. **人机交互确认** - 用户可审查和修正解析结果
4. **智能策略推荐** - 基于历史案例和专家知识推荐答复策略
5. **完整工作流程** - 从输入到输出的端到端处理

### 新增功能

#### ✅ 目标专利信息提取
- 目标专利申请号
- 专利标题
- 申请人信息

#### ✅ 对比文件详细信息提取
- 对比文件标识 (D1, D2等)
- 公开号
- 公开日
- 标题
- 申请人
- 相关权利要求
- 审查员引用描述

---

## 🚀 快速开始

### 1. 基本使用

```python
from core.patent.oa_integration_service import get_oa_integration_service

# 获取集成服务
service = get_oa_integration_service()

# 处理审查意见文档
result = await service.process_with_interaction(
    document_path="path/to/office_action.pdf",
    enable_interaction=True  # 启用人机交互
)

# 查看结果
print(service.export_result(result, format="markdown"))
```

### 2. 自动处理模式（无人机交互）

```python
# 自动处理，直接生成答复方案
result = await service.process_auto("path/to/office_action.pdf")
```

---

## 📊 工作流程详解

### 步骤1: 文档上传与解析

```
用户上传审查意见文档
    ↓
系统自动检测文档类型
    ↓
调用相应解析器:
  - PDF → pdfplumber
  - Word → python-docx
  - 图片 → ChineseOCROptimizer (OCR)
    ↓
结构化信息提取
```

**提取的关键信息**:
- 目标专利申请号
- 驳回类型（新颖性/创造性等）
- 对比文件详细信息
- 审查员论点
- 时间信息

### 步骤2: 解析结果确认

系统生成Markdown格式的确认模板：

```markdown
# 📋 审查意见解析结果

## 🎯 目标专利信息
- **申请号**: `202310000001.X`
- **专利标题**: 基于深度学习的图像识别方法
- **申请人**: XX科技有限公司

## 📄 对比文件

### D1: `CN112345678A`
- **标题**: 图像识别方法及装置
- **公开日**: 2023-01-15
- **申请人**: YY科技股份公司
- **相关权利要求**: 权利要求1, 2, 3
- **引用描述**: D1公开了基于卷积神经网络的图像识别方法...

### ✅ 请确认以上信息是否准确
- **重点检查**:
  - 目标专利申请号是否正确
  - 对比文件信息是否完整
```

### 步骤3: 信息修正（可选）

用户可以修改任何提取的信息：

```python
# 应用用户修改
workflow = get_oa_interaction()

# 修改申请号
workflow.apply_user_modification("target_application_number", "202310000002.X")

# 修改对比文件
workflow.apply_user_modification("prior_art_references", ["CN112345678A", "US2023001234A1"])
```

### 步骤4: 策略审查

系统生成答复策略方案：

```json
{
  "recommended_strategy": "argue_differences",
  "strategy_rationale": "针对新颖性驳回，建议争辩区别特征",
  "success_probability": 0.78,
  "confidence": 0.85,
  "arguments": [
    "本申请与对比文件D1存在以下区别技术特征:",
    "对比文件未公开: 特殊的损失函数"
  ],
  "claim_modifications": [
    "权利要求1: 建议增加[具体技术特征]进行进一步限定"
  ]
}
```

### 步骤5: 最终确认

### 步骤6: 生成答复

---

## 🛠️ 高级用法

### 自定义解析器配置

```python
from core.patent.oa_document_parser import OfficeActionParser

parser = OfficeActionParser()

# 检查解析器能力
print(parser.capabilities)
# {'pdf': True, 'docx': True, 'ocr': True}
```

### 直接使用解析器

```python
from core.patent.oa_document_parser import get_oa_parser

parser = get_oa_parser()

# 解析文档
parsed_oa = parser.parse_document("office_action.pdf")

# 获取JSON格式
print(parsed_oa.to_json())

# 获取Markdown确认模板
print(parsed_oa.to_markdown())
```

### 人机交互流程控制

```python
from core.patent.oa_human_interaction import get_oa_interaction

workflow = get_oa_interaction()

# 分步执行
await workflow._step_document_upload("office_action.pdf")
await workflow._step_parse_confirm()
await workflow._step_info_correct()
await workflow._step_strategy_review()
await workflow._step_final_confirm()
await workflow._step_generation()
```

---

## 📝 数据格式说明

### ParsedOfficeAction 数据结构

```python
{
  "oa_id": "OA_20240115123456",
  "document_source": "office_action.pdf",

  # 目标专利信息
  "target_application_number": "202310000001.X",
  "target_patent_title": "基于深度学习的图像识别方法",
  "target_applicant": "XX科技有限公司",

  # 驳回信息
  "rejection_type": "novelty",
  "rejection_reason": "对比文件D1公开了权利要求1的全部技术特征",

  # 对比文件
  "prior_art_references": ["CN112345678A", "US2023001234A1"],
  "prior_art_details": [
    {
      "reference_id": "D1",
      "publication_number": "CN112345678A",
      "publication_date": "2023-01-15",
      "title": "图像识别方法及装置",
      "applicant": "YY科技公司",
      "relevant_claims": ["权利要求1", "权利要求2"],
      "description": "D1公开了..."
    }
  ],

  # 其他信息
  "cited_claims": [1, 2, 3],
  "examiner_arguments": ["D1公开了..."],
  "missing_features": ["特殊的损失函数"],
  "received_date": "2024-01-15",
  "response_deadline": "2024-04-15",
  "confidence": 0.85
}
```

---

## 🔧 工具调用链路

```
用户输入
    ↓
OAIntegrationService (集成服务)
    ├─► OfficeActionParser (文档解析)
    │   ├─► pdfplumber (PDF解析)
    │   ├─► python-docx (Word解析)
    │   └─► ChineseOCROptimizer (OCR识别)
    ├─► HumanInteractionWorkflow (人机交互)
    └─► SmartOfficeActionResponder (智能答复)
        ├─► PatentCaseDatabase (案例检索)
        ├─► QualitativeRuleEngine (规则引擎)
        └─► HebbianOptimizer (赫布学习)
```

---

## 💡 最佳实践

### 1. 文档准备
- 确保文档清晰可读
- PDF/Word格式优先
- 图片建议300dpi以上

### 2. 信息确认
- **重点检查**:
  - 目标专利申请号
  - 对比文件公开号
  - 驳回类型

### 3. 策略选择
- 参考系统推荐的策略
- 根据实际情况调整
- 记录答复结果用于学习

### 4. 持续优化
- 记录答复结果
- 反馈到系统
- 提升未来准确性

---

## 📦 文件说明

| 文件 | 功能 |
|-----|------|
| `oa_document_parser.py` | 文档解析器，支持PDF/Word/OCR |
| `oa_human_interaction.py` | 人机交互流程 |
| `oa_integration_service.py` | 集成服务，统一入口 |
| `smart_oa_responder.py` | 智能答复系统 |

---

## 🤝 人机协作点设计

### 步骤1: 审查意见输入 ✅
- **用户操作**: 上传审查意见文档
- **系统响应**: 解析文档，生成结构化数据
- **确认点**: 显示解析结果供用户确认

### 步骤2: 信息确认 ✅
- **用户操作**: 审查解析结果，指出错误
- **系统响应**: 接收用户修改，更新数据
- **确认点**: 显示修正后的最终版本

### 步骤3: 策略审查 ✅
- **用户操作**: 审查推荐的答复策略
- **系统响应**: 提供策略说明和成功概率
- **确认点**: 确认或调整策略

### 步骤4: 最终确认 ✅
- **用户操作**: 确认所有信息无误
- **系统响应**: 生成完整答复方案

---

## 📈 下一步计划

- [ ] 增加更多文档格式支持
- [ ] 优化OCR识别准确率
- [ ] 增加对比文件自动检索
- [ ] 集成专利数据库API
- [ ] 支持批量处理

---

**作者**: 小诺·双鱼公主
**版本**: v0.1.2 "晨星初现"
**更新时间**: 2025-12-24
