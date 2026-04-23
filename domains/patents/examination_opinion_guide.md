# 专利审查意见解析器使用指南

## 📋 概述

专门用于解析专利申请审查过程中的审查意见（**非驳回类**），精准提取：
- 具体法律条款引用
- 权利要求编号与条款的关联
- 审查员信息（姓名、电话、部门等）
- 问题描述和修改建议

---

## 🎯 核心功能

### 1. 审查员信息提取

```python
from core.patent.examination_opinion_parser import get_examination_opinion_parser

parser = get_examination_opinion_parser()
examiner_info = parser.extract_examiner_info(text)

# 输出:
# ExaminerInfo(
#     name="张三",
#     phone="010-12345678",
#     department="机械发明审查部",
#     examiner_id="A123456"
# )
```

### 2. 法律条款精准识别

支持的法律条款：

#### 说明书相关
- 专利法第26条第3款 - 说明书清楚、完整要求
- 专利法实施细则第20条 - 说明书内容要求
- 专利法第33条 - 修改权限

#### 权利要求相关
- 专利法第22条第2款 - 新颖性
- 专利法第22条第3款 - 创造性
- 专利法第22条第4款 - 实用性
- 专利法第26条第4款 - 权利要求以说明书为依据
- 专利法第31条第1款 - 单一性
- 专利法第33条 - 权利要求修改
- 专利法实施细则第22-25条 - 权利要求撰写规定

### 3. 权利要求-条款关联

```python
# 输出示例:
ExaminationOpinion(
    opinion_type="权利要求不支持问题",
    target_claims=["2", "4-8"],  # 权利要求2、4-8
    legal_articles=[
        LegalArticle(
            law_name="专利法",
            article_number="第26条第4款",
            full_reference="专利法第26条第4款",
            description="权利要求应当以说明书为依据"
        )
    ],
    issue_description="权利要求2、4-8不符合专利法第26条第4款规定..."
)
```

---

## 📊 Markdown确认模板示例

```markdown
# 📋 专利审查意见解析结果

---

## 👤 审查员信息
- **姓名**: 张三
- **电话**: `010-12345678`
- **部门**: 机械发明审查部
- **编号**: A123456

## 📝 共解析到 3 条审查意见

### 审查意见 1

**类型**: 权利要求不支持问题

**涉及权利要求**: 权利要求2-4、权利要求8

**违反条款**:
  - `专利法第26条第4款` - 权利要求应当以说明书为依据

**问题描述**: 权利要求2、4-8不符合专利法第26条第4款规定，
权利要求所限定的技术方案中，"所述的特征"在说明书中没有明确记载。

**审查员意见**: 本领域技术人员根据说明书公开的内容无法确定该特征的具体含义。

---

### 审查意见 2

**类型**: 说明书内容问题

**涉及权利要求**: (无)

**违反条款**:
  - `专利法第26条第3款` - 说明书应当清楚、完整地写明发明所要解决的技术问题

**问题描述**: 说明书不符合专利法第26条第3款的规定，
说明书对发明技术方案的描述不够清楚、完整。

---

### 审查意见 3

**类型**: 新颖性/创造性问题

**涉及权利要求**: 权利要求1

**违反条款**:
  - `专利法第22条第2款` - 新颖性
  - `专利法第22条第3款` - 创造性

**问题描述**: 权利要求1不符合专利法第22条第2款、第3款规定，
不具备新颖性和创造性。

**修改建议**: 建议增加区别技术特征或修改权利要求保护范围。

---

### ✅ 请确认以上审查意见是否准确

**重点检查**:
- 权利要求编号是否准确
- 法律条款引用是否正确
- 问题描述是否完整

- 如有错误，请指出需要修改的部分
- 确认无误后，回复 `确认` 或 `confirm` 继续
```

---

## 💻 使用示例

### 完整流程

```python
from core.patent.examination_opinion_parser import get_examination_opinion_parser

# 获取解析器
parser = get_examination_opinion_parser()

# 审查意见文本
text = """
审查意见通知书

申请号: 202310000001.X
审查员: 张三
电话: 010-12345678

1. 权利要求2、4-8不符合专利法第26条第4款规定...
2. 说明书不符合专利法第26条第3款的规定...
3. 权利要求1不符合专利法第22条第2款、第3款规定...
"""

# 提取审查员信息
examiner_info = parser.extract_examiner_info(text)

# 解析审查意见
opinions = parser.parse_examination_opinions(text)

# 生成确认模板
markdown = parser.opinions_to_markdown(opinions, examiner_info)

# 输出
print(markdown)
```

---

## 📝 支持的权利要求编号格式

| 输入格式 | 解析结果 |
|---------|---------|
| 权利要求1、2-8 | ["1", "2-8"] |
| 权利要求1-3 | ["1-3"] |
| 权利要求1,2,3 | ["1", "2", "3"] |
| 权利要求2、4、6-8 | ["2", "4", "6-8"] |

---

## 🔧 高级用法

### 自定义条款映射

```python
parser = get_examination_opinion_parser()

# 查看所有支持的条款
for key, pattern in parser.legal_patterns.items():
    print(f"{key}: {pattern.pattern}")
```

### 提取单个意见

```python
opinion = parser._parse_section(section_text)

if opinion:
    print(f"类型: {opinion.opinion_type}")
    print(f"权利要求: {opinion.target_claims}")
    print(f"法律条款: {[str(a) for a in opinion.legal_articles]}")
```

---

## ⚙️ 与驳回类审查意见的区别

| 特性 | 驳回类 (oa_document_parser.py) | 审查类 (examination_opinion_parser.py) |
|-----|-------------------------------|-----------------------------------|
| 主要用途 | 驳回决定答复 | 申请审查意见 |
| 输出结构 | OfficeAction | ExaminationOpinion |
| 侧重 | 驳回类型、对比文件 | 法律条款、权利要求关联 |
| 审查员信息 | 无 | 有（姓名、电话等） |
| 法律条款 | 一般识别 | 精准到具体条款 |

---

## 📦 文件位置

- 解析器: `core/patent/examination_opinion_parser.py`
- 数据结构: `ExaminerInfo`, `ExaminationOpinion`, `LegalArticle`
- 使用文档: 当前文档

---

## 💡 最佳实践

1. **确认优先级**:
   - ✅ 重点检查权利要求编号
   - ✅ 重点检查法律条款引用
   - ✅ 重点检查问题描述完整性

2. **使用场景**:
   - 专利申请审查阶段
   - 一通、二通答复准备
   - 审查意见答复策略制定

3. **数据质量**:
   - 原始文档质量越高，解析越准确
   - 建议使用清晰的PDF/Word格式
   - OCR识别准确率取决于图片质量

---

**作者**: 小诺·双鱼公主
**版本**: v0.1.2 "晨星初现"
**更新时间**: 2025-12-24
