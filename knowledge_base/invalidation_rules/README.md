# 无效宣告规则知识库 - Athena 集成

> **版本**: v1.0.0
> **生成时间**: 2026-04-05
> **维护者**: 小诺
> **数据来源**: 17,036 条无效复审决定

---

## 一、系统概览

本知识库基于 **17,036 条无效复审决定** 提取而成，提供：

- **42 个核心规则模板**（覆盖 14 个主要法条）
- **80 个增强规则模板**（支持同义词匹配）
- **智能检索**（法条、关键词、语义匹配）
- **答复模板**（云熙可直接使用）

---

## 二、快速开始

### 2.1 基础检索

```python
from knowledge_base.invalidation_rules import InvalidationRuleRetriever

# 初始化检索器
retriever = InvalidationRuleRetriever()

# 1. 按法条检索
rules = retriever.search_by_article("A22.3", limit=5)

# 2. 按关键词检索
rules = retriever.search_by_keyword("创造性", limit=5)

# 3. 按文本检索（智能匹配）
rules = retriever.search_by_text("权利要求创造性判断的三步法", limit=5)

# 4. 组合检索
rules = retriever.search(article="A22.3", keyword="公知常识", limit=5)
```

### 2.2 云熙专用接口

```python
from knowledge_base.invalidation_rules import YunxiRuleHelper

# 初始化助手
helper = YunxiRuleHelper()

# 1. 查找创造性规则
rules = helper.find_rules_for_creativity()

# 2. 根据案情推荐规则
rules = helper.recommend_rules("权利要求与D1存在区别，但D2给出了技术启示")

# 3. 获取答复要点
points = helper.get_response_points("A22.3")
# 返回：["1. 确定最接近现有技术", "2. 识别区别特征", ...]

# 4. 获取答复模板
template = helper.generate_response_template("A22.3", "defense")
```

---

## 三、核心功能

### 3.1 规则检索

**支持三种检索方式**：

1. **法条检索** - 精确匹配法条编号
2. **关键词检索** - 支持同义词扩展
3. **语义检索** - 智能匹配案情描述

**检索准确率**: 80%（优化后，从 60% 提升）

### 3.2 规则模板

每个规则模板包含：

```json
{
  "模板ID": "T003",
  "适用法条": ["A22.3", "A46.2"],
  "规则模板": "如果权利要求请求保护的技术方案...",
  "关键词": ["创造性", "公知常识", "技术启示"],
  "同义词": ["非显而易见", "实质性特点"],
  "案例数量": 2434,
  "典型案例": [...]
}
```

### 3.3 答复支持

- **答复要点** - 针对每个法条的标准化答复流程
- **答复模板** - 可直接使用的答复文本框架
- **法条解释** - 核心法条的简要说明

---

## 四、数据结构

### 4.1 文件目录

```
~/Athena工作平台/knowledge_base/invalidation_rules/
├── __init__.py                    # 集成入口
├── README.md                      # 本文档
└── data/                          # 数据目录（符号链接）
    ├── all_decision_points.json   # 原始数据（17,036 条）
    ├── rule_templates.json        # 原始模板（42 个）
    ├── rule_templates_enhanced.json # 增强模板（80 个）
    ├── yunxi_knowledge_base.json  # 云熙知识库
    └── article_network.json       # 法条关联网络
```

### 4.2 数据统计

| 指标 | 数值 |
|------|------|
| **决定书总数** | 17,036 条 |
| **提取率** | 54% |
| **法条数量** | 103 个 |
| **核心法条** | 6 个（A22.3, A26.3, A26.4, A22.2, A23.2, A23.1） |
| **规则模板** | 80 个 |
| **检索准确率** | 80% |

---

## 五、核心法条

### 5.1 法条频次 TOP 5

| 法条 | 名称 | 出现次数 | 占比 |
|------|------|----------|------|
| A46.2 | 无效宣告请求范围 | 16,865 | 25.0% |
| A46.1 | 无效宣告请求理由 | 16,786 | 24.9% |
| A22.3 | 创造性 | 10,553 | 15.7% |
| A23.2 | 明显区别（外观） | 5,086 | 7.5% |
| A26.4 | 权利要求清楚 | 4,216 | 6.3% |

### 5.2 法条关联

**最强关联 TOP 3**：

1. **A46.1 ↔ A46.2**: 16,641 次（Jaccard: 0.978）
2. **A22.3 ↔ A46.2**: 10,406 次（Jaccard: 0.612）
3. **A22.3 ↔ A46.1**: 10,342 次（Jaccard: 0.609）

---

## 六、使用场景

### 6.1 云熙答复撰写

```python
# 场景：云熙接到无效宣告任务

# Step 1: 识别核心法条
article = "A22.3"  # 创造性

# Step 2: 检索相关规则
rules = helper.find_rules_for_creativity(limit=3)

# Step 3: 获取答复要点
points = helper.get_response_points(article)

# Step 4: 生成答复模板
template = helper.generate_response_template(article, "defense")

# Step 5: 基于规则和模板撰写答复
# ...（云熙的主模型完成）
```

### 6.2 Athena法律推理

```python
# 场景：Athena进行法律推理

# Step 1: 案情分析
case_desc = "权利要求1与D1相比存在区别特征X，D2给出了应用X的技术启示"

# Step 2: 检索相关规则
rules = retriever.search_by_text(case_desc, limit=5)

# Step 3: 提取判断标准
for rule in rules:
    print(f"法条: {rule['适用法条']}")
    print(f"规则: {rule['规则模板'][:100]}...")
    print(f"案例数: {rule['案例数量']}")
    
# Step 4: 应用到具体案件
# ...（Athena的法律推理引擎）
```

---

## 七、API 参考

### 7.1 InvalidationRuleRetriever

**方法列表**：

- `search_by_article(article, limit)` - 按法条检索
- `search_by_keyword(keyword, limit)` - 按关键词检索
- `search_by_text(text, limit)` - 按文本检索
- `search(article, keyword, limit)` - 组合检索
- `get_template_by_id(template_id)` - 根据ID获取模板
- `list_articles()` - 列出所有法条
- `get_stats()` - 获取统计信息

### 7.2 YunxiRuleHelper

**方法列表**：

- `find_rules_for_creativity(limit)` - 创造性规则
- `find_rules_for_disclosure(limit)` - 说明书公开规则
- `find_rules_for_clarity(limit)` - 权利要求清楚规则
- `find_rules_for_design(limit)` - 外观设计规则
- `recommend_rules(case_desc, limit)` - 案情推荐
- `get_response_points(article)` - 答复要点
- `get_article_explanation(article)` - 法条解释
- `generate_response_template(article, case_type)` - 答复模板

---

## 八、性能指标

| 指标 | 数值 |
|------|------|
| **检索准确率** | 80%（5个测试案例） |
| **模板覆盖率** | 100%（核心法条） |
| **平均检索时间** | <100ms |
| **数据大小** | ~50MB |

---

## 九、更新日志

### v1.0.0 (2026-04-05)
- ✅ 完成 Phase 1-4 全部任务
- ✅ 构建规则模板库（42 → 80 个）
- ✅ 优化检索准确率（60% → 80%）
- ✅ 集成到 Athena 工作平台
- ✅ 为云熙创建专用接口

---

## 十、维护者

- **开发**: 小诺 🐟
- **维护**: 徐健
- **邮箱**: xujian519@gmail.com

---

_本知识库基于 17,036 条无效复审决定构建，持续更新中..._
