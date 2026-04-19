# AutoSpec专利说明书撰写框架 API文档

> 基于论文 "AutoSpec: Multi-Agent Patent Specification Drafting" (2025)
>
> **版本**: v1.0
> **创建日期**: 2026-03-23
> **使用模型**: deepseek-reasoner (核心生成), qwen3.5 (快速分析)

---

## 概述

`AutoSpecDrafter` 是基于多Agent协作的专利说明书自动撰写框架，整合了权利要求生成、范围测量和附图分析功能。

### 核心功能

1. **发明理解**: 解析技术交底书，提取核心创新点
2. **权利要求生成**: 自动生成独立和从属权利要求
3. **说明书撰写**: 生成技术领域、背景技术、发明内容、具体实施方式
4. **附图说明**: 整合附图分析结果
5. **质量审核**: 多维度质量评估和迭代优化

---

## 快速开始

### 1. 基本使用

```python
from core.patent.ai_services.autospec_drafter import (
    AutoSpecDrafter,
    draft_patent_specification,
    format_specification
)

# 方式1: 便捷函数
draft = await draft_patent_specification(
    disclosure="""
    光伏充电系统

    技术领域：新能源技术

    核心创新：采用智能充电控制算法，根据光照强度自动调节充电电流

    技术效果：
    1. 提高充电效率30%
    2. 延长电池寿命

    主要组件：
    - 光伏板：将光能转换为电能
    - 充电控制器：控制充电过程
    - 储能电池：存储电能
    """,
    llm_manager=llm_manager,  # 可选
    drawing_paths=["/path/to/fig1.png"]  # 可选
)

# 查看结果
print(f"发明名称: {draft.invention_title}")
print(f"质量评分: {draft.overall_quality_score:.1f}/10")
print(f"迭代次数: {draft.iteration_count}")

# 获取完整说明书
print(format_specification(draft))
```

### 2. 使用撰写框架

```python
# 创建撰写框架
drafter = AutoSpecDrafter(llm_manager=llm_manager)

# 完整撰写
draft = await drafter.draft_specification(
    disclosure="发明披露材料...",
    invention_type=InventionType.DEVICE,  # 可选
    drawing_paths=["fig1.png", "fig2.png"],  # 可选
    enable_quality_check=True,
    max_iterations=3
)

# 快速撰写（简化版）
draft = await drafter.quick_draft(
    disclosure="发明披露材料...",
    skip_quality_check=False
)
```

---

## API参考

### `AutoSpecDrafter`

#### 初始化

```python
drafter = AutoSpecDrafter(
    llm_manager: UnifiedLLMManager = None  # LLM管理器(可选)
)
```

#### 主要方法

##### `draft_specification()`

撰写专利说明书

```python
async def draft_specification(
    self,
    disclosure: str,
    invention_type: Optional[InventionType] = None,
    drawing_paths: Optional[List[str]] = None,
    enable_quality_check: bool = True,
    max_iterations: int = 3
) -> SpecificationDraft
```

**参数说明**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `disclosure` | str | 必需 | 发明披露材料 |
| `invention_type` | InventionType | None | 发明类型（自动检测） |
| `drawing_paths` | List[str] | None | 附图路径列表 |
| `enable_quality_check` | bool | True | 是否启用质量检查 |
| `max_iterations` | int | 3 | 最大迭代次数 |

##### `quick_draft()`

快速撰写（简化版）

```python
async def quick_draft(
    self,
    disclosure: str,
    skip_quality_check: bool = False
) -> SpecificationDraft
```

---

## 数据结构

### `SpecificationDraft`

```python
@dataclass
class SpecificationDraft:
    draft_id: str                           # 草稿ID
    version: int = 1                        # 版本号
    invention_title: str = ""               # 发明名称

    # 各章节内容
    sections: Dict[SectionType, SectionContent]

    # 权利要求
    claims: List[str]

    # 附图信息
    figure_descriptions: List[str]

    # 质量评估
    overall_quality_score: float            # 整体质量分
    quality_dimensions: Dict[str, float]    # 各维度得分

    # 迭代信息
    iteration_count: int                    # 迭代次数
    improvement_history: List[Dict]         # 改进历史

    # 元数据
    processing_time_ms: float               # 处理时间
```

### `InventionUnderstanding`

```python
@dataclass
class InventionUnderstanding:
    invention_title: str                    # 发明名称
    invention_type: InventionType           # 发明类型
    technical_field: str                    # 技术领域

    # 技术分析
    core_innovation: str                    # 核心创新点
    technical_problem: str                  # 技术问题
    technical_solution: str                 # 技术方案
    technical_effects: List[str]            # 技术效果

    # 特征提取
    essential_features: List[TechnicalFeature]    # 必要特征
    optional_features: List[TechnicalFeature]     # 可选特征
```

### `QualityReport`

```python
@dataclass
class QualityReport:
    overall_score: float                     # 总分 (0-10)
    dimensions: Dict[str, float]             # 各维度得分

    # 具体问题
    critical_issues: List[str]               # 严重问题
    warnings: List[str]                      # 警告
    suggestions: List[str]                   # 优化建议

    # 是否通过
    is_acceptable: bool
```

---

## 枚举类型

### `SectionType` - 章节类型

| 值 | 说明 |
|----|------|
| `TECHNICAL_FIELD` | 技术领域 |
| `BACKGROUND` | 背景技术 |
| `INVENTION_CONTENT` | 发明内容 |
| `DRAWING_DESCRIPTION` | 附图说明 |
| `EMBODIMENTS` | 具体实施方式 |

### `InventionType` - 发明类型

| 值 | 说明 |
|----|------|
| `PRODUCT` | 产品发明 |
| `METHOD` | 方法发明 |
| `DEVICE` | 装置发明 |
| `SYSTEM` | 系统发明 |
| `COMPOSITION` | 组合物发明 |

---

## 质量评估维度

| 维度 | 说明 | 评分标准 |
|------|------|----------|
| completeness | 完整性 | 各部分是否齐全 |
| clarity | 清晰性 | 表述是否清楚 |
| accuracy | 准确性 | 技术描述是否准确 |
| sufficiency | 充分性 | 是否充分公开 |
| consistency | 一致性 | 各部分是否一致 |
| compliance | 规范性 | 是否符合格式规范 |
| support | 支持性 | 是否支持权利要求 |

**可接受阈值**: 7.5/10

---

## 输出示例

### 完整说明书结构

```markdown
# 光伏充电系统

## 技术领域
本发明涉及新能源技术领域，具体涉及一种光伏充电系统。

## 背景技术
随着新能源技术的发展，光伏充电系统越来越普及...

## 发明内容
本发明的目的是提供一种光伏充电系统，以解决现有技术充电效率低的问题...

## 附图说明
图1是本发明实施例提供的光伏充电系统的结构示意图；
图中：1-光伏板；2-充电控制器；3-储能电池...

## 具体实施方式
下面结合附图和具体实施方式对本发明作进一步详细描述...

## 权利要求书
1. 一种光伏充电系统，其特征在于，包括光伏板、充电控制器和储能电池...
2. 根据权利要求1所述的光伏充电系统，其特征在于...
```

---

## 使用建议

### 1. 发明披露材料准备

建议包含以下信息：
- 发明名称
- 技术领域
- 核心创新点
- 解决的技术问题
- 技术方案
- 技术效果
- 主要技术特征

### 2. 质量控制

- 启用质量检查以获得更好的输出
- 设置适当的迭代次数（通常2-3次）
- 检查critical_issues并手动修复

### 3. 模块集成

AutoSpec整合了以下模块：
- P1-1: 权利要求范围测量
- P1-2: 多模态附图分析
- P1-4: 高质量权利要求生成

---

## 性能指标

| 指标 | 值 |
|------|-----|
| 撰写时间 (无LLM) | <1秒 |
| 撰写时间 (有LLM) | 30-60秒 |
| 质量评分 (有LLM) | 7.5-9.0 |
| 质量评分 (无LLM) | 5.0-7.0 |

---

## 相关文档

- [专利AI技术引入实施计划](../papers/2026_ai_agent/专利AI技术引入实施计划_v1.0.md)
- [权利要求生成器 v2 API](./claim_generator_v2.md)
- [附图分析器 API](./drawing_analyzer.md)
- [范围测量 API](./claim_scope_analyzer.md)
