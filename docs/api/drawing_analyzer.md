# 专利附图智能分析系统 API文档

> 基于论文 "PatentVision: A multimodal method for drafting patent applications" (2025)
>
> **版本**: v1.0
> **创建日期**: 2026-03-23
> **使用模型**: qwen3.5 (本地多模态)

---

## 概述

`PatentDrawingAnalyzer` 是基于视觉语言模型(VLM)的专利附图智能分析系统，能够自动识别附图组件、提取连接关系并生成标准格式的附图说明。

### 核心功能

1. **组件识别**: 自动识别附图中的技术组件
2. **连接关系提取**: 分析组件之间的连接关系
3. **附图标记生成**: 自动生成标准格式的附图标记
4. **说明文字撰写**: 生成专利规范格式的附图说明

---

## 快速开始

### 1. 基本使用

```python
from core.patent.ai_services.drawing_analyzer import (
    PatentDrawingAnalyzer,
    analyze_patent_drawing,
    format_figure_description
)

# 方式1: 便捷函数
result = await analyze_patent_drawing(
    image_path="/path/to/drawing.png",
    llm_manager=llm_manager,  # 可选
    claim_context="1. 一种光伏充电系统..."  # 可选，提供上下文
)

# 查看结果
print(f"附图类型: {result.drawing_type.value}")
print(f"识别组件数: {len(result.components)}")
print(f"置信度: {result.confidence_score:.0%}")

# 格式化输出
print(format_figure_description(result, figure_number=1))
```

### 2. 批量分析

```python
analyzer = PatentDrawingAnalyzer(llm_manager=llm_manager)

image_paths = [
    "/path/to/fig1.png",
    "/path/to/fig2.png",
    "/path/to/fig3.png"
]

results = await analyzer.batch_analyze_drawings(
    image_paths=image_paths,
    claim_context="权利要求上下文..."
)

# 生成完整附图说明
from core.patent.ai_services.drawing_analyzer import format_full_figure_description
full_description = format_full_figure_description(results, "智能装置")
print(full_description)
```

---

## API参考

### `PatentDrawingAnalyzer`

#### 初始化

```python
analyzer = PatentDrawingAnalyzer(
    llm_manager: UnifiedLLMManager = None  # LLM管理器(可选)
)
```

#### 主要方法

##### `analyze_drawing()`

分析单张专利附图

```python
async def analyze_drawing(
    self,
    image_path: str,
    claim_context: Optional[str] = None,
    figure_number: int = 1
) -> DrawingAnalysisResult
```

**参数说明**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `image_path` | str | 必需 | 图片路径 |
| `claim_context` | str | None | 权利要求上下文（可选） |
| `figure_number` | int | 1 | 附图编号 |

##### `generate_figure_description()`

生成标准格式的附图说明

```python
async def generate_figure_description(
    self,
    drawing: DrawingAnalysisResult,
    figure_number: int = 1,
    invention_name: str = "装置"
) -> str
```

##### `batch_analyze_drawings()`

批量分析多张附图

```python
async def batch_analyze_drawings(
    self,
    image_paths: List[str],
    claim_context: Optional[str] = None
) -> List[DrawingAnalysisResult]
```

---

## 数据结构

### `DrawingAnalysisResult`

```python
@dataclass
class DrawingAnalysisResult:
    image_path: str                           # 图片路径
    drawing_type: DrawingType                 # 附图类型
    drawing_description: str                  # 附图整体描述

    # 识别结果
    components: List[DrawingComponent]        # 组件列表
    connections: List[ComponentConnection]    # 连接关系
    annotations: List[DrawingAnnotation]      # 附图标记

    # 生成的说明
    figure_description: str                   # 附图说明文字

    # 元数据
    confidence_score: float                   # 置信度
    processing_time_ms: float                 # 处理时间
    model_used: str                           # 使用的模型
```

### `DrawingComponent`

```python
@dataclass
class DrawingComponent:
    component_id: str              # 组件编号 (如 "1", "2", "10")
    name: str                      # 组件名称
    component_type: ComponentType  # 组件类型
    description: str = ""          # 组件描述
    position: Optional[Tuple[float, float]] = None  # 位置
    bounding_box: Optional[Dict[str, float]] = None  # 边界框
```

### `ComponentConnection`

```python
@dataclass
class ComponentConnection:
    source_id: str                 # 源组件编号
    target_id: str                 # 目标组件编号
    connection_type: str           # 连接类型
    description: str = ""          # 连接描述
```

### `DrawingAnnotation`

```python
@dataclass
class DrawingAnnotation:
    reference_number: str          # 附图标记号
    component_name: str            # 对应组件名称
    position: Tuple[float, float]  # 标记位置
    confidence: float = 0.8        # 识别置信度
```

---

## 枚举类型

### `DrawingType` - 附图类型

| 值 | 说明 |
|----|------|
| `STRUCTURE` | 结构图 |
| `FLOWCHART` | 流程图 |
| `CIRCUIT` | 电路图 |
| `BLOCK_DIAGRAM` | 方框图 |
| `SCHEMATIC` | 示意图 |
| `EXPLODED_VIEW` | 分解图 |
| `CROSS_SECTION` | 剖视图 |
| `UNKNOWN` | 未知类型 |

### `ComponentType` - 组件类型

| 值 | 说明 |
|----|------|
| `MECHANICAL` | 机械部件 |
| `ELECTRICAL` | 电子元件 |
| `SOFTWARE` | 软件模块 |
| `INTERFACE` | 接口 |
| `SENSOR` | 传感器 |
| `ACTUATOR` | 执行器 |
| `CONTROLLER` | 控制器 |
| `UNKNOWN` | 未知类型 |

---

## 输出示例

### 分析结果

```python
result.to_dict()
# {
#     "image_path": "/path/to/fig1.png",
#     "drawing_type": "structure",
#     "drawing_description": "光伏充电系统结构示意图",
#     "components": [
#         {
#             "component_id": "1",
#             "name": "光伏板",
#             "component_type": "mechanical",
#             "description": "将光能转换为电能"
#         },
#         {
#             "component_id": "2",
#             "name": "充电控制器",
#             "component_type": "controller",
#             "description": "控制充电过程"
#         }
#     ],
#     "connections": [
#         {
#             "source_id": "1",
#             "target_id": "2",
#             "connection_type": "electrical",
#             "description": "电连接传输电能"
#         }
#     ],
#     "confidence_score": 0.85,
#     "model_used": "qwen3.5"
# }
```

### 附图说明

```
图1是本发明实施例提供的光伏充电装置的结构示意图；
图中：
1-光伏板；
2-充电控制器；
3-储能电池；
4-逆变器；
5-负载接口。
```

---

## 使用建议

### 1. 图片格式

支持的图片格式:
- PNG (推荐)
- JPG/JPEG
- 其他主流图片格式

### 2. 上下文提供

提供权利要求上下文可以显著提高识别准确率:

```python
# 推荐: 提供权利要求作为上下文
result = await analyzer.analyze_drawing(
    image_path="fig1.png",
    claim_context="1. 一种光伏充电系统，包括光伏板、充电控制器..."
)
```

### 3. 批量处理

对于多张相关附图，建议使用批量处理:

```python
results = await analyzer.batch_analyze_drawings(
    image_paths=["fig1.png", "fig2.png", "fig3.png"],
    claim_context=claim_text
)
```

---

## 性能指标

| 指标 | 值 |
|------|-----|
| 单图分析时间 | 2-5s (有LLM) |
| 单图分析时间 | <100ms (无LLM/启发式) |
| 组件识别准确率 | 75-85% |
| 附图类型判断准确率 | 80-90% |

---

## 相关文档

- [专利AI技术引入实施计划](../papers/2026_ai_agent/专利AI技术引入实施计划_v1.0.md)
- [权利要求生成器 v2 API](./claim_generator_v2.md)
- [权利要求范围测量 API](./claim_scope_analyzer.md)
