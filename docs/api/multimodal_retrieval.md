# 多模态检索增强系统 API文档

> 基于多模态专利检索论文的检索系统
>
> **版本**: v1.0
> **创建日期**: 2026-03-23
> **使用模型**: qwen3.5 (本地向量化), deepseek-reasoner (复杂查询)

---

## 概述

`MultimodalRetrievalSystem` 是多模态专利检索系统，支持：
1. **图像向量化**: 将专利附图转换为向量表示
2. **跨模态检索**: 文本-图像相互检索
3. **混合检索融合**: 多种融合策略整合结果

### 核心功能

1. **多模态检索**: 同时使用文本和图像进行检索
2. **图像相似度搜索**: 查找相似的专利附图
3. **混合融合**: 线性、RRF、归一化等融合策略
4. **批量索引**: 高效索引大量图像数据

---

## 快速开始

### 1. 基本检索

```python
from core.patent.ai_services.multimodal_retrieval import (
    MultimodalRetrievalSystem,
    RetrievalConfig,
    SearchMode,
    format_search_result
)

# 创建系统实例
config = RetrievalConfig(
    mode=SearchMode.HYBRID,
    top_k=20
)
system = MultimodalRetrievalSystem(config=config)

# 执行检索
result = await system.search("光伏充电控制器")

# 格式化输出
print(format_search_result(result))
```

### 2. 多模态检索

```python
from core.patent.ai_services.multimodal_retrieval import (
    multimodal_search
)

# 使用图像和文本同时检索
query_image = open("patent_figure.png", "rb").read()
result = await multimodal_search(
    query="电路结构",
    query_image=query_image,
    top_k=10
)

# 查看结果
for r in result.fused_results[:5]:
    print(f"{r.patent_number}: {r.relevance_score:.2%}")
```

### 3. 图像相似度搜索

```python
# 批量索引图像
images = [
    {
        "image_id": "img_001",
        "image_data": open("figure1.png", "rb").read(),
        "patent_number": "CN1234567A",
        "figure_number": "图1",
        "caption": "主结构示意图"
    }
]
await system.index_images(images)

# 查找相似图像
query_image = open("query_figure.png", "rb").read()
similar = await system.find_similar_images(
    query_image,
    top_k=5,
    min_similarity=0.6
)

for image_vec, similarity in similar:
    print(f"{image_vec.patent_number} - {image_vec.figure_number}: {similarity:.2%}")
```

---

## API参考

### `MultimodalRetrievalSystem`

#### 初始化

```python
system = MultimodalRetrievalSystem(
    llm_manager=None,           # LLM管理器(可选)
    embedding_service=None,     # 嵌入服务(可选)
    vector_store=None,          # 向量存储(可选)
    config=RetrievalConfig()    # 检索配置
)
```

#### 主要方法

##### `search()`

执行多模态检索

```python
async def search(
    self,
    query: str,                                    # 文本查询
    query_image: Optional[bytes] = None,          # 查询图像(可选)
    config: Optional[RetrievalConfig] = None,     # 检索配置
    filters: Optional[Dict[str, Any]] = None      # 过滤条件
) -> HybridSearchResult
```

##### `index_images()`

批量索引图像

```python
async def index_images(
    self,
    images: List[Dict[str, Any]]   # 图像列表
) -> int                           # 成功索引数量
```

##### `find_similar_images()`

查找相似图像

```python
async def find_similar_images(
    self,
    query_image: bytes,            # 查询图像
    top_k: int = 10,               # 返回数量
    min_similarity: float = 0.5    # 最低相似度
) -> List[Tuple[ImageVector, float]]
```

##### `get_stats()`

获取系统统计

```python
def get_stats(self) -> Dict[str, Any]
```

---

## 数据结构

### `RetrievalConfig`

检索配置

```python
@dataclass
class RetrievalConfig:
    mode: SearchMode = SearchMode.HYBRID       # 检索模式
    fusion_strategy: FusionStrategy = FusionStrategy.RRF  # 融合策略
    text_weight: float = 0.6                   # 文本权重
    image_weight: float = 0.4                  # 图像权重
    top_k: int = 20                            # 返回数量
    min_score: float = 0.3                     # 最低分数
    enable_rerank: bool = True                 # 启用重排序
    cache_results: bool = True                 # 缓存结果
```

### `HybridSearchResult`

混合检索结果

```python
@dataclass
class HybridSearchResult:
    query_id: str                     # 查询ID
    query: str                        # 原始查询
    mode: SearchMode                  # 检索模式
    text_results: List[SearchResult]  # 文本结果
    image_results: List[SearchResult] # 图像结果
    fused_results: List[SearchResult] # 融合结果
    fusion_strategy: FusionStrategy   # 融合策略
    text_weight: float                # 文本权重
    image_weight: float               # 图像权重
    total_time: float                 # 总耗时
    retrieval_stats: Dict[str, Any]   # 检索统计
```

### `SearchResult`

单个检索结果

```python
@dataclass
class SearchResult:
    result_id: str                    # 结果ID
    patent_number: str                # 专利号
    relevance_score: float            # 相关度(0-1)
    relevance_level: RelevanceLevel   # 相关度级别
    matched_content: str              # 匹配内容
    matched_images: List[str]         # 匹配图像
    source_type: str                  # 来源类型
```

### `ImageVector`

图像向量

```python
@dataclass
class ImageVector:
    image_id: str                     # 图像ID
    patent_number: str                # 专利号
    figure_number: str                # 图号
    image_type: ImageType             # 图像类型
    vector: np.ndarray                # 768维向量
    caption: str                      # 图像说明
    components: List[str]             # 组件列表
```

---

## 枚举类型

### `SearchMode` - 检索模式

| 值 | 说明 |
|----|------|
| `TEXT_ONLY` | 纯文本检索 |
| `VECTOR_ONLY` | 纯向量检索 |
| `HYBRID` | 文本+向量混合 |
| `IMAGE_ONLY` | 纯图像检索 |
| `MULTIMODAL` | 多模态(文本+图像) |

### `ImageType` - 图像类型

| 值 | 说明 |
|----|------|
| `STRUCTURE` | 结构图 |
| `FLOWCHART` | 流程图 |
| `CIRCUIT` | 电路图 |
| `CHEMICAL` | 化学结构式 |
| `PERSPECTIVE` | 立体图 |
| `EXPLODED` | 爆炸图 |
| `SECTION` | 剖面图 |
| `UNKNOWN` | 未知类型 |

### `FusionStrategy` - 融合策略

| 值 | 说明 |
|----|------|
| `LINEAR` | 线性加权融合 |
| `RRF` | Reciprocal Rank Fusion |
| `RR_FUSION` | RRF别名 |
| `SCORE_NORM` | 分数归一化融合 |
| `LEARNED` | 学习式融合 |

### `RelevanceLevel` - 相关度级别

| 值 | 分数范围 |
|----|---------|
| `HIGHLY_RELEVANT` | >0.8 |
| `RELEVANT` | 0.6-0.8 |
| `PARTIALLY_RELEVANT` | 0.4-0.6 |
| `MARGINAL` | 0.2-0.4 |
| `IRRELEVANT` | <0.2 |

---

## 融合策略详解

### 1. 线性融合 (Linear)

```
Score = w_text × (S_text / max_text) + w_image × (S_image / max_image)
```

- 适用场景: 文本和图像权重明确
- 参数: text_weight, image_weight

### 2. Reciprocal Rank Fusion (RRF)

```
RRF(d) = Σ 1/(k + rank(d))
```

- k: 常数(默认60)
- 适用场景: 排名比分数更重要

### 3. 分数归一化融合 (Score Norm)

```
Score = w_text × (S - min) / (max - min) + w_image × (S - min) / (max - min)
```

- 适用场景: 分数范围差异大

---

## 使用示例

### 示例1: 基本混合检索

```python
from core.patent.ai_services.multimodal_retrieval import (
    hybrid_search,
    SearchMode
)

result = await hybrid_search(
    query="太阳能充电控制器",
    mode=SearchMode.HYBRID,
    top_k=10
)

print(f"找到 {len(result.fused_results)} 个结果")
print(f"耗时: {result.total_time:.3f}秒")
```

### 示例2: 多模态检索

```python
from core.patent.ai_services.multimodal_retrieval import (
    multimodal_search
)

# 使用产品图片和描述检索相关专利
product_image = open("product.jpg", "rb").read()
result = await multimodal_search(
    query="控制电路板",
    query_image=product_image,
    top_k=5
)

for r in result.fused_results:
    print(f"专利: {r.patent_number}")
    print(f"相关度: {r.relevance_score:.2%}")
    print(f"匹配图像: {len(r.matched_images)}")
```

### 示例3: 批量索引和搜索

```python
# 索引专利附图
patent_images = []
for fig in ["图1", "图2", "图3"]:
    patent_images.append({
        "image_id": f"CN1234567A_{fig}",
        "image_data": open(f"figures/{fig}.png", "rb").read(),
        "patent_number": "CN1234567A",
        "figure_number": fig,
        "caption": f"{fig}结构示意图"
    })

indexed = await system.index_images(patent_images)
print(f"索引了 {indexed} 张图像")

# 使用新图像搜索相似专利
new_image = open("new_product.png", "rb").read()
similar = await system.find_similar_images(new_image, top_k=3)

for img, score in similar:
    print(f"相似: {img.patent_number} {img.figure_number} ({score:.1%})")
```

---

## 输出示例

### 检索报告

```
============================================================
多模态检索结果
============================================================

【查询ID】 query_1711234567890
【查询内容】 光伏充电控制器
【检索模式】 hybrid
【融合策略】 rrf

【文本结果】 15 条
【图像结果】 8 条
【融合结果】 20 条

【Top 5 结果】
------------------------------------------------------------

1. CN1234567A
   相关度: 92.35% (highly_relevant)
   匹配内容: 光伏充电控制器包括主控模块、充电管理模块...
   匹配图像: 2 张

2. CN2345678A
   相关度: 85.12% (relevant)
   匹配内容: 充电控制方法包括检测电压、调节电流...
   匹配图像: 1 张

3. CN3456789A
   相关度: 78.45% (relevant)
   匹配内容: 太阳能充电系统包括光伏板、蓄电池...
   匹配图像: 3 张

------------------------------------------------------------
【总耗时】 0.234 秒
============================================================
```

---

## 性能指标

| 指标 | 目标 | 说明 |
|------|------|------|
| 检索延迟 | <500ms | 端到端检索时间 |
| 融合时间 | <100ms | 结果融合时间 |
| 索引速度 | >100图/秒 | 批量索引速度 |
| 缓存命中率 | >80% | 结果缓存效果 |

---

## 相关文档

- [专利AI技术引入实施计划](../papers/2026_ai_agent/专利AI技术引入实施计划_v1.0.md)
- [附图分析 API](./drawing_analyzer.md)
- [任务分类 API](./task_classifier.md)
