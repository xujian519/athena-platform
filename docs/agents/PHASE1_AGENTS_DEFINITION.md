# Athena团队成员定义文档

> **版本**: 1.0
> **日期**: 2026-04-21
> **状态**: 已定稿

---

## 📋 文档概述

本文档详细定义Athena团队所有专业智能体的定位、能力边界、知识来源和实施阶段。

---

## 🎯 团队组成总览

| Phase | 智能体 | 定位 | 知识来源 |
|-------|--------|------|---------|
| **Phase 1** | 分析者 | 技术本身分析 | 技术理解能力 |
| **Phase 1** | 创造性分析智能体 | 创造性判断（技术+法律） | 专利实务/创造性、复审无效/创造性 |
| **Phase 1** | 新颖性分析智能体 | 新颖性判断（技术+法律） | 专利实务/新颖性、复审无效/新颖性 |
| **Phase 1** | 侵权分析智能体 | 侵权判定（技术+法律） | 专利侵权/ |
| **Phase 2** | 申请文件审查智能体 | 权利要求+说明书分析 | 专利实务/权利要求、说明书、撰写/审查-权利要求 |
| **Phase 2** | 撰写审查智能体 | 撰写质量审查 | 撰写/（完整的撰写指南） |
| **Phase 3** | 无效宣告分析智能体 | 无效宣告请求/答辩 | 复审无效/ |

---

## Phase 1：基础智能体

### 1. 分析者（AnalyzerAgent）

#### 定位
技术本身的分析专家，专注于技术方案的深度理解，不涉及法律判断。

#### 职责

**✅ 负责什么**：
- 技术特征提取
- 特征-问题-效果三原则提取
- 技术交底书深度分析
- 对比文件技术分析
- 技术总结（核心步骤、部件组合、工作原理）

**❌ 不负责什么**：
- 创造性分析 → 创造性分析智能体
- 新颖性分析 → 新颖性分析智能体
- 侵权分析 → 侵权分析智能体
- 专利检索 → 检索者
- 法律规则校验 → 规则官（Phase 2）

#### 能力

```python
class AnalyzerAgent(BaseXiaonaComponent):
    """分析者能力定义"""
    
    capabilities = [
        AgentCapability(
            name="feature_extraction",
            description="技术特征提取",
            input_types=["专利文本", "技术交底书"],
            output_types=["技术特征列表"],
            estimated_time=10.0,
        ),
        AgentCapability(
            name="problem_effect_extraction",
            description="特征-问题-效果三原则提取",
            input_types=["技术方案"],
            output_types=["三原则列表"],
            estimated_time=15.0,
        ),
        AgentCapability(
            name="technical_summary",
            description="技术总结（步骤、部件、原理）",
            input_types=["技术文档"],
            output_types=["技术总结报告"],
            estimated_time=20.0,
        ),
    ]
```

#### 输出格式

**JSON格式**：
```json
{
  "structured_data": {
    "target_features": [
      {
        "feature_id": "F001",
        "feature_name": "自动驾驶掉头系统",
        "description": "包括传感器、控制器、执行器",
        "feature_type": "结构",
        "category": "必要"
      }
    ],
    "problem_effect": [
      {
        "technical_feature": "自动驾驶掉头系统",
        "technical_problem": "解决狭窄空间掉头困难",
        "technical_effect": "提高掉头安全性和效率"
      }
    ],
    "technical_summary": {
      "core_steps": ["步骤1：...", "步骤2：..."],
      "component_structure": ["传感器", "控制器", "执行器"],
      "working_principle": "工作原理说明..."
    }
  },
  "markdown_text": "# 技术分析报告\n\n## 技术特征\n\n## 特征-问题-效果\n\n## 技术总结\n"
}
```

---

### 2. 创造性分析智能体（CreativityAnalyzerAgent）

#### 定位
专利创造性判断专家，基于专利实务和复审无效案例，进行三步法判断。

#### 职责

**✅ 负责什么**：
- 创造性三步法判断
- 技术启示判断
- 辅助判断因素分析
- 不同类型发明的创造性判断
- 创造性分析推理与有限试验

**❌ 不负责什么**：
- 技术特征提取 → 分析者
- 专利检索 → 检索者
- 新颖性分析 → 新颖性分析智能体
- 侵权分析 → 侵权分析智能体

#### 能力

```python
class CreativityAnalyzerAgent(BaseXiaonaComponent):
    """创造性分析智能体能力定义"""
    
    capabilities = [
        AgentCapability(
            name="three_step_analysis",
            description="创造性三步法判断",
            input_types=["目标专利", "对比文件"],
            output_types=["三步法分析报告"],
            estimated_time=25.0,
        ),
        AgentCapability(
            name="technical_teaching_judgment",
            description="技术启示判断",
            input_types=["区别特征", "对比文件"],
            output_types=["技术启示结论"],
            estimated_time=15.0,
        ),
        AgentCapability(
            name="secondary_considerations",
            description="辅助判断因素分析",
            input_types=["分析结果"],
            output_types=["辅助因素评估"],
            estimated_time=20.0,
        ),
    ]
```

#### 输出格式

```json
{
  "three_step_analysis": {
    "step1_closest_prior_art": "D1：名称为...",
    "step2_distinctive_features": ["特征1", "特征2"],
    "step2_technical_problem": "实际解决...",
    "step3_obviousness": false,
    "step3_technical_teaching": "无明确启示"
  },
  "secondary_considerations": {
    "unexpected_effect": "预料不到的技术效果",
    "technical_prejudice": "克服技术偏见",
    "commercial_success": "商业成功（佐证）"
  },
  "creativity_conclusion": "具备创造性",
  "creativity_level": "高",
  "reasoning": "基于三步法..."
}
```

#### 知识来源

**核心知识库**：
- `专利实务/创造性/` (17个文件)
  - 创造性-概述与三步法框架.md
  - 创造性-技术启示的判断.md
  - 创造性-辅助判断因素.md
  - 创造性-预料不到的技术效果与实验数据.md
  - 等等...

- `复审无效/创造性/`
  - 创造性-无效决定裁判规则分析.md

---

### 3. 新颖性分析智能体（NoveltyAnalyzerAgent）

#### 定位
用户新颖性判断专家，基于单独对比原则。

#### 职责

**✅ 负责什么**：
- 新颖性判断（单独对比原则）
- 抵触申请判断
- 出版物/使用公开判断
- 不丧失新颖性的公开

**❌ 不负责什么**：
- 技术特征提取 → 分析者
- 创造性分析 → 创造性分析智能体
- 专利检索 → 检索者

---

### 4. 侵权分析智能体（InfringementAnalyzerAgent）

#### 定位
专利侵权判定专家，基于专利侵权相关案例和法规。

#### 职责

**✅ 负责什么**：
- 直接侵权判定（全面覆盖原则、等同原则）
- 间接侵权判定（帮助侵权、共同侵权）
- 侵权抗辩分析
- 侵权救济分析

---

## Phase 2：审查智能体

### 5. 申请文件审查智能体（ApplicationDocumentReviewerAgent）

#### 定位
权利要求和说明书的分析专家，确保形式和实质要求。

#### 职责

**✅ 负责什么**：
- 权利要求书分析（类型、范围、必要技术特征、功能性限定）
- 说明书分析（充分公开、清楚完整、能够实现）
- 说明书支持权利要求分析

---

### 6. 撰写审查智能体（WritingReviewerAgent）

#### 定位
专利申请文件撰写质量审查专家，基于完整的撰写指南。

#### 职责

**✅ 负责什么**：
- 权利要求书撰写审查（类型、范围、必要技术特征、从属权利要求）
- 说明书撰写审查（五部分完整性、清楚完整、能够实现）
- 撰写常见错误识别

#### 知识来源

**核心知识库**：
- `撰写/` (完整的撰写指南)
  - 撰写-权利要求书撰写要求.md
  - 撰写-说明书撰写要求.md
  - 撰写-常见错误-XXX.md (10个案例分析)

---

## Phase 3：高级智能体

### 7. 无效宣告分析智能体（InvalidationAnalyzerAgent）

#### 定位
无效宣告请求和答辩专家。

#### 职责

**✅ 负责什么**：
- 无效宣告理由分析
- 无效宣告证据组织
- 无效宣告请求书撰写审查
- 无效宣告答辩策略

#### 知识来源

**核心知识库**：
- `复审无效/`

---

## 📊 智能体对比表

| 维度 | 技术分析 | 法律分析 |
|------|---------|---------|
| **纯技术** | 分析者 | - |
| **技术+法律** | - | 创造性分析、新颖性分析、侵权分析 |
| **形式+实质** | - | 申请文件审查、撰写审查 |
| **高级法律** | - | 无效宣告分析 |

---

## 🔗 关联文档

- [数据契约规范](../api/DATA_CONTRACT_SPECIFICATION.md)
- [工作流程设计](../workflows/SCENARIO_BASED_WORKFLOWS.md)

---

**End of Document**
