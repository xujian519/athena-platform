# 小娜智能画像系统使用文档

## 📚 系统概述

小娜智能画像系统是基于规则驱动和数据增强的专利业务智能分析系统，通过深度学习专利法核心条款的本质特征，为专利申请、审查、撰写、复审、无效和诉讼六大业务场景提供智能画像支持。

### 核心能力

- 📖 **条款本质画像**: 8条专利法核心条款的深度本质分析
- 🎭 **业务场景画像**: 6大专利业务场景的策略画像
- 🔍 **智能情境分析**: 自动识别法律问题、评估风险、生成策略
- 📊 **向量检索集成**: 从256,690个向量中检索相似案例
- 🕸️ **知识图谱推理**: 基于知识图谱的关联分析

---

## 🚀 快速开始

### 安装依赖

```bash
# 基础依赖（必需）
pip install dataclasses

# 可选依赖（增强功能）
pip install qdrant-client nebula3
```

### 基础使用

```python
import asyncio
from core.cognition.xiaona_portrait_api import (
    analyze_article,
    analyze_patent_situation,
    quick_ask,
    get_system_info
)

async def main():
    # 1. 查询系统状态
    status = get_system_info()
    print(f"系统状态: {status['status']}")

    # 2. 分析条款本质
    article = await analyze_article("第22条")
    print(f"条款本质: {article['core_value']}")

    # 3. 分析专利情境
    analysis = await analyze_patent_situation(
        scenario="专利无效",
        description="挑战某专利的创造性",
        key_facts={"prior_art": ["D1", "D2"]}
    )
    print(f"成功概率: {analysis['success_probability']}")

    # 4. 快速查询
    result = await quick_ask("我的专利申请有什么风险？")
    print(f"建议: {result['strategy_recommendations']}")

asyncio.run(main())
```

---

## 📖 API 参考

### 1. 分析条款本质

**函数**: `analyze_article(article_number: str)`

**参数**:
- `article_number`: 条款号，如"第22条"

**返回**: 条款本质画像数据

**示例**:
```python
result = await analyze_article("第22条")
# {
#     "article_number": "第22条",
#     "title": "新颖性、创造性、实用性",
#     "core_value": "专利质量门槛",
#     "legislative_purpose": "防止低质量专利垄断技术",
#     "essence_type": "实质性审查标准",
#     "essence_features": [...],
#     "application_scenarios": [...],
#     "controversy_points": [...]
# }
```

---

### 2. 分析专利情境

**函数**: `analyze_patent_situation(scenario, description, key_facts)`

**参数**:
- `scenario`: 业务场景（"专利申请"、"专利审查"、"专利撰写"、"专利复审"、"专利无效"、"专利诉讼"）
- `description`: 情境描述
- `key_facts`: 关键事实字典

**返回**: 完整的情境分析结果

**示例**:
```python
result = await analyze_patent_situation(
    scenario="专利无效",
    description="基于现有技术挑战专利创造性",
    key_facts={
        "target_patent": "CN1234567A",
        "prior_art": ["D1", "D2", "D3"],
        "challenge_basis": "缺乏创造性"
    }
)
# {
#     "situation_id": "专利无效_20251223...",
#     "xiaona_portrait": "社会公益捍卫者 - 专利无效",
#     "applicable_articles": ["第22条", "第25条", "第26条", "第47条"],
#     "legal_issues": ["新颖性/创造性问题"],
#     "success_probability": 0.7,
#     "risk_assessment": {...},
#     "strategy_recommendations": [...],
#     "critical_factors": [...]
# }
```

---

### 3. 快速查询

**函数**: `quick_ask(question: str)`

**参数**:
- `question`: 自然语言问题描述

**返回**: 分析结果

**示例**:
```python
result = await quick_ask("我的AI算法专利申请有什么风险？")
```

---

### 4. 获取系统状态

**函数**: `get_system_info()`

**返回**: 系统状态信息

**示例**:
```python
status = get_system_info()
# {
#     "status": "running",
#     "system_name": "小娜专利法本质学习画像系统",
#     "version": "v2.0.0 Complete",
#     "article_essences": 8,
#     "business_portraits": 6,
#     "supported_scenarios": [...]
# }
```

---

## 🎯 业务场景使用指南

### 场景1: 专利申请

```python
result = await analyze_patent_situation(
    scenario="专利申请",
    description="基于深度学习的图像识别方法专利申请",
    key_facts={
        "technology_field": "人工智能/计算机视觉",
        "innovation_type": "算法优化",
        "technical_features": [
            "改进的CNN结构",
            "新的损失函数",
            "多模态数据融合"
        ]
    }
)

print(f"小娜角色: {result['xiaona_portrait']}")
print(f"成功概率: {result['success_probability']:.1%}")
print(f"策略建议: {result['strategy_recommendations']}")
```

### 场景2: 专利审查

```python
result = await analyze_patent_situation(
    scenario="专利审查",
    description="审查某AI专利申请的可专利性",
    key_facts={
        "application_number": "CN202310000001",
        "claims": ["权利要求1", "权利要求2"],
        "prior_art_found": ["D1", "D2"]
    }
)
```

### 场景3: 专利撰写

```python
result = await analyze_patent_situation(
    scenario="专利撰写",
    description="优化权利要求保护范围",
    key_facts={
        "invention_summary": "一种智能推荐算法",
        "key_features": ["用户行为分析", "协同过滤", "深度学习"],
        "protection_scope": "需要覆盖多种实现方式"
    }
)
```

### 场景4: 专利复审

```python
result = await analyze_patent_situation(
    scenario="专利复审",
    description="申请被驳回，提起复审",
    key_facts={
        "rejection_reason": "不具备创造性",
        "examiner_findings": "与D1结合D2显而易见",
        "our_arguments": ["D1未公开特征X", "D2教导相反", "技术效果意想不到"]
    }
)
```

### 场景5: 专利无效

```python
result = await analyze_patent_situation(
    scenario="专利无效",
    description="挑战竞争对手专利的创造性",
    key_facts={
        "target_patent": "CN1234567A",
        "prior_art": ["D1", "D2", "D3"],
        "challenge_basis": "D1+D2+D3组合显而易见",
        "differences": "仅参数优化"
    }
)
```

### 场景6: 专利诉讼

```python
result = await analyze_patent_situation(
    scenario="专利诉讼",
    description="被诉专利侵权，分析抗辩策略",
    key_facts={
        "plaintiff_patent": "CN109876543A",
        "accused_product": "我们的推荐系统",
        "claim_elements": ["数据采集", "协同过滤", "相似度计算"],
        "our_differences": ["使用深度学习", "实时更新", "不同特征工程"]
    }
)
```

---

## 📊 条款本质画像参考

### 第22条 - 新颖性、创造性、实用性

| 属性 | 内容 |
|-----|------|
| 核心价值 | 专利质量门槛 |
| 立法目的 | 防止低质量专利垄断技术 |
| 本质类型 | 实质性审查标准 |
| 适用场景 | 专利申请、实质审查、无效宣告、侵权判定 |
| 争议焦点 | 现有技术认定、技术对比、改进程度判断 |

### 第25条 - 不授予专利权的客体

| 属性 | 内容 |
|-----|------|
| 核心价值 | 专利保护边界 |
| 立法目的 | 平衡私权与公共利益 |
| 本质类型 | 保护客体界定 |
| 适用场景 | 专利申请、客体审查、无效宣告 |
| 争议焦点 | 技术性判断、产业应用性、自然产物 |

### 第26条 - 申请文件要求

| 属性 | 内容 |
|-----|------|
| 核心价值 | 专利公开对价 |
| 立法目的 | 充分公开换取保护 |
| 本质类型 | 程序性要求 |
| 适用场景 | 专利申请、审查、侵权判定 |
| 争议焦点 | 公开充分性、支持范围、清楚性 |

### 第47条 - 专利权的无效宣告

| 属性 | 内容 |
|-----|------|
| 核心价值 | 社会公共利益保护 |
| 立法目的 | 纠正不当授权 |
| 本质类型 | 事后监督 |
| 适用场景 | 不当授权、垄断争议、FTO障碍 |
| 争议焦点 | 无效理由、证据充分性、时效问题 |

---

## 🔧 高级配置

### 禁用向量检索

```python
from core.cognition.xiaona_patent_portrait_system import create_xiaona_essence_learner

learner = await create_xiaona_essence_learner(
    enable_vector_search=False,
    enable_kg_query=True
)
```

### 自定义配置

```python
learner = XiaonaPatentLawEssenceLearner()
learner.qdrant_host = "localhost"  # Qdrant主机
learner.qdrant_port = 6333          # Qdrant端口
learner.nebula_space = "patent_kg"   # NebulaGraph空间

await learner.initialize()
```

---

## 📁 文件结构

```
core/cognition/
├── xiaona_patent_portrait_system.py    # 核心画像系统
├── xiaona_portrait_api.py               # 统一API接口
├── xiaona_patent_law_essence_learner.py # 旧版本（兼容）
└── xiaona_portrait_practical_demo.py    # 使用演示
```

---

## 🧪 测试运行

```bash
# 运行API演示
python3 core/cognition/xiaona_portrait_api.py

# 运行实用演示
python3 core/cognition/xiaona_portrait_practical_demo.py
```

---

## 💡 最佳实践

1. **快速原型**: 使用`quick_ask()`快速验证想法
2. **精确分析**: 使用`analyze_patent_situation()`获取详细分析
3. **条款学习**: 使用`analyze_article()`深入理解条款本质
4. **状态检查**: 使用`get_system_info()`确认系统可用性

---

## 🔄 版本历史

- **v2.0.0**: 完整版，集成向量检索和知识图谱
- **v1.0.0**: 基础版，规则驱动的画像系统

---

## 🏭 生产环境使用指南

### 触发关键词机制

在生产环境中，需要用户**明确触发**才会启动智能画像分析。这确保了：
- ✅ 用户明确知道正在使用AI分析
- ✅ 控制计算成本
- ✅ 提升响应速度（非必要场景可快速处理）

### 支持的触发关键词

| 类型 | 触发词 | 示例 |
|------|--------|------|
| **主要触发** | 使用小娜画像分析<br>启用小娜画像<br>小娜画像 | "使用小娜画像分析这个专利" |
| **智能分析** | 启用智能画像<br>使用智能画像<br>智能画像分析 | "启用智能画像帮我审查" |
| **深度分析** | 深度分析<br>深度画像<br>全面分析 | "深度分析这个案件" |
| **对话式** | 小娜帮我分析<br>小娜分析<br>请小娜分析 | "小娜帮我分析一下" |
| **通用触发** | 使用AI分析<br>AI分析<br>智能分析 | "使用AI分析这个专利" |
| **英文触发** | portrait<br>xiaona<br>intelligent | "portrait this patent" |

### 生产环境API使用

```python
import asyncio
from core.cognition.xiaona_production_api import (
    analyze_with_trigger_detection,
    is_portrait_triggered,
    get_trigger_keywords
)

async def production_usage():
    # 场景1: 用户明确触发画像
    user_input = "使用小娜画像分析这个实用新型专利申请"

    # 检查是否触发
    if is_portrait_triggered(user_input):
        result = await analyze_with_trigger_detection(
            user_input=user_input,
            patent_data={
                "patent_type": "实用新型",
                "title": "铜铝复合阳极母线",
                "quality_score": 4
            }
        )

        if result['triggered_portrait']:
            analysis = result['analysis']
            print(f"成功概率: {analysis['success_probability']:.1%}")
            print(f"小娜画像: {analysis['xiaona_portrait']}")

    # 场景2: 用户不触发画像（标准处理）
    user_input = "帮我检查权利要求书格式"
    result = await analyze_with_trigger_detection(user_input=user_input)

    if not result['triggered_portrait']:
        print("使用标准处理模式，不启动画像分析")

asyncio.run(production_usage())
```

### 用户界面提示

建议在用户界面添加提示：

```
💡 提示：说 "使用小娜画像分析" 可启用AI智能画像分析
```

或在功能按钮旁添加：

```
[启用智能画像 🤖]
```

### 快捷按钮方案

如果使用图形界面，可以添加快捷触发按钮：

| 按钮文本 | 功能 | 触发词 |
|---------|------|--------|
| 🤖 启用智能画像 | 启动画像分析 | 使用小娜画像分析 |
| 🔍 深度分析 | 全面深度分析 | 深度分析 |
| 📊 专利性评估 | 评估可专利性 | 小娜帮我分析 |

---

## 📞 技术支持

如有问题或建议，请联系：
- 作者: 小娜·天秤女神 (Athena)
- 创建时间: 2025-12-23
