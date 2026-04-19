# vector_search工具详细分析报告

> 工具名称: vector_search
> 向量维度: **1024**（项目标准）
> 分析日期: 2026-04-19

---

## 一、工具概述

### 1.1 功能描述

**向量语义搜索工具**基于BGE-M3嵌入模型，提供高质量的语义检索功能，支持法律和专利知识图谱的向量存储、检索和优化。

### 1.2 核心特性

1. **1024维向量**: 项目统一使用1024维度（非标准的768维）
2. **多语言支持**: 支持中文、英文等100+种语言
3. **长文档处理**: 最大序列长度8192 tokens
4. **多集合管理**: 支持多个向量集合
5. **查询缓存**: 1000条缓存限制
6. **混合检索**: 结合关键词和向量检索

### 1.3 技术架构

**模型**: BGE-M3（定制版）
- 标准维度: 768维
- **项目维度: 1024维** ⚠️
- 扩展方式: Zero-padding或投影层

**向量数据库**: Qdrant
- 端点: http://localhost:6333
- 距离度量: Cosine
- 集合命名: `{name}_1024`

**设备支持**: MPS（Apple Silicon）> CUDA > CPU

---

## 二、项目配置分析

### 2.1 向量维度配置

**文件**: `config/vector_config.py`

```python
# 项目向量维度配置
VECTOR_DIMENSION = 1024  # 项目统一使用1024维向量

# 向量集合配置
COLLECTION_CONFIGS = {
    'patents_invalid': {
        'name': 'patents_invalid_1024',
        'dimension': 1024,
        'distance': 'Cosine',
    },
    'legal_clauses': {
        'name': 'legal_clauses_1024',
        'dimension': 1024,
        'distance': 'Cosine',
    },
    'technical_terms': {
        'name': 'technical_terms_1024',
        'dimension': 1024,
        'distance': 'Cosine',
    }
}
```

### 2.2 维度标准化策略

**文件**: `config/dimension_standardization.json`

```json
{
  "target_dimension": 1024,
  "transformations": {
    "384_to_1024": "zero_padding",
    "768_to_1024": "zero_padding",
    "1024+": "truncation"
  }
}
```

**策略**:
- **384维 → 1024维**: Zero-padding（补零）
- **768维 → 1024维**: Zero-padding（补零）
- **>1024维**: Truncation（截断）

### 2.3 BGE-M3嵌入器配置

**文件**: `core/embedding/bge_m3_embedder.py`

```python
class BGE_M3_Embedder:
    """
    BGE-M3模型嵌入器(MPS优化版)
    
    模型信息:
    - 模型名称: BAAI/bge-m3
    - 向量维度: 1024  # ⚠️ 非标准维度
    - 支持语言: 多语言(中文、英文等100+种语言)
    - 最大序列长度: 8192 tokens
    - 设备支持: MPS(Apple Silicon)、CUDA、CPU
    """
    
    def __init__(self):
        self.dimension = 1024  # BGE-M3的标准维度（项目定制）
```

---

## 三、向量集合分析

### 3.1 现有集合

| 集合名称 | 维度 | 用途 | 状态 |
|---------|------|------|------|
| patents_invalid_1024 | 1024 | 专利无效宣告向量库 | ✅ 已配置 |
| legal_clauses_1024 | 1024 | 法律条款向量库 | ✅ 已配置 |
| technical_terms_1024 | 1024 | 技术术语向量库 | ✅ 已配置 |
| patent_rules_1024 | 1024 | 专利规则向量库 | ✅ 已配置 |

### 3.2 集合命名规范

**规范**: `{collection_name}_1024`

**示例**:
- `legal_main_1024`
- `patent_applications_1024`
- `legal_contracts_1024`
- `legal_ip_1024`

---

## 四、维度处理机制

### 4.1 维度扩展

**标准BGE-M3**: 768维
**项目BGE-M3**: 1024维
**扩展方式**: Zero-padding（补256个零）

```python
def expand_vector_to_1024(vector_768: np.ndarray) -> np.ndarray:
    """将768维向量扩展到1024维"""
    if len(vector_768) == 768:
        # 补256个零
        padding = np.zeros(1024 - 768, dtype=vector_768.dtype)
        return np.concatenate([vector_768, padding])
    elif len(vector_768) == 1024:
        return vector_768
    else:
        raise ValueError(f"不支持的向量维度: {len(vector_768)}")
```

### 4.2 维度验证

```python
def validate_vector_dimension(vector) -> bool:
    """验证向量维度是否为1024"""
    if isinstance(vector, list):
        return len(vector) == 1024
    elif hasattr(vector, 'shape'):
        return vector.shape[-1] == 1024
    return False
```

---

## 五、验证检查清单

### 5.1 依赖项检查

```bash
# 检查依赖安装
python3 -c "
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import numpy as np
print('✅ 所有依赖已安装')
"
```

### 5.2 维度配置检查

```python
# 验证向量维度配置
from config.vector_config import VECTOR_DIMENSION
assert VECTOR_DIMENSION == 1024, f"维度配置错误: {VECTOR_DIMENSION}"
print(f"✅ 向量维度配置正确: {VECTOR_DIMENSION}")
```

### 5.3 BGE-M3模型检查

```python
# 验证BGE-M3模型输出维度
from core.embedding.bge_m3_embedder import BGE_M3_Embedder

embedder = BGE_M3_Embedder()
await embedder.initialize()

# 测试编码
test_text = "测试文本"
embedding = await embedder.encode([test_text])

assert embedding.shape[1] == 1024, f"维度错误: {embedding.shape[1]}"
print(f"✅ BGE-M3输出维度正确: {embedding.shape[1]}")
```

### 5.4 Qdrant集合检查

```python
# 验证Qdrant集合维度
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
collections = client.get_collections().result.collections

for coll in collections:
    vector_size = coll.config.params.vectors.size
    assert vector_size == 1024, f"集合 {coll.name} 维度错误: {vector_size}"
    print(f"✅ 集合 {coll.name} 维度正确: {vector_size}")
```

---

## 六、迁移实施

### 6.1 Handler包装器

```python
@tool(
    name="vector_search",
    category="vector_search",
    description="向量语义搜索（基于BGE-M3模型，1024维）",
    priority="high",
    tags=["search", "vector", "semantic", "bge-m3", "1024dim"]
)
async def vector_search_handler(
    query: str,
    collection: str = "legal_main_1024",
    top_k: int = 10,
    threshold: float = 0.7
) -> dict:
    """
    向量语义搜索Handler（1024维版本）
    
    参数:
        query: 查询文本
        collection: 集合名称（必须以_1024结尾）
        top_k: 返回结果数（默认: 10）
        threshold: 相似度阈值（默认: 0.7）
    
    返回:
        {
            "success": true,
            "query": "...",
            "collection": "...",
            "dimension": 1024,
            "total_results": 10,
            "results": [...]
        }
    """
    try:
        from core.vector.intelligent_vector_manager import IntelligentVectorManager
        from config.vector_config import validate_vector_dimension

        # 参数验证
        if not query:
            return {
                "success": False,
                "error": "缺少必需参数: query"
            }

        # 验证集合名称
        if not collection.endswith("_1024"):
            return {
                "success": False,
                "error": f"集合名称必须以_1024结尾，当前: {collection}"
            }

        if top_k <= 0:
            return {
                "success": False,
                "error": "top_k必须大于0"
            }

        if not (0.0 <= threshold <= 1.0):
            return {
                "success": False,
                "error": "threshold必须在0.0到1.0之间"
            }

        # 创建向量管理器
        manager = IntelligentVectorManager()

        # 执行搜索
        results = await manager.search_vector(
            query=query,
            collection_name=collection,
            limit=top_k,
            score_threshold=threshold
        )

        # 验证结果维度
        for result in results:
            if "vector" in result:
                assert validate_vector_dimension(result["vector"]), \
                    f"结果向量维度错误: {len(result['vector'])}"

        return {
            "success": True,
            "query": query,
            "collection": collection,
            "dimension": 1024,
            "total_results": len(results),
            "results": results
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "collection": collection
        }
```

### 6.2 维度兼容性处理

```python
def ensure_vector_dimension(vector: np.ndarray, target_dim: int = 1024) -> np.ndarray:
    """确保向量维度为目标维度"""
    current_dim = len(vector) if isinstance(vector, (list, np.ndarray)) else vector.shape[-1]
    
    if current_dim == target_dim:
        return vector
    elif current_dim < target_dim:
        # 补零
        padding = np.zeros(target_dim - current_dim, dtype=vector.dtype)
        if isinstance(vector, np.ndarray):
            return np.concatenate([vector, padding])
        else:
            return list(vector) + list(padding)
    else:
        # 截断
        if isinstance(vector, np.ndarray):
            return vector[:target_dim]
        else:
            return vector[:target_dim]
```

---

## 七、测试用例

### 7.1 维度测试

```python
async def test_vector_dimension():
    """测试向量维度"""
    from core.embedding.bge_m3_embedder import BGE_M3_Embedder
    
    embedder = BGE_M3_Embedder()
    await embedder.initialize()
    
    # 测试单条文本
    text = "专利检索测试"
    embedding = await embedder.encode([text])
    
    assert embedding.shape == (1, 1024), f"维度错误: {embedding.shape}"
    print(f"✅ 单条文本编码维度正确: {embedding.shape}")
    
    # 测试批量文本
    texts = ["测试1", "测试2", "测试3"]
    embeddings = await embedder.encode(texts)
    
    assert embeddings.shape == (3, 1024), f"维度错误: {embeddings.shape}"
    print(f"✅ 批量文本编码维度正确: {embeddings.shape}")
```

### 7.2 集合维度测试

```python
async def test_collection_dimension():
    """测试Qdrant集合维度"""
    from qdrant_client import QdrantClient, models
    
    client = QdrantClient(host="localhost", port=6333)
    
    # 创建测试集合
    collection_name = "test_collection_1024"
    
    try:
        # 删除旧集合（如果存在）
        client.delete_collection(collection_name)
    except:
        pass
    
    # 创建新集合
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=1024,  # ⚠️ 1024维
            distance=models.Distance.COSINE
        )
    )
    
    # 验证集合
    collection_info = client.get_collection(collection_name)
    vector_size = collection_info.result.config.params.vectors.size
    
    assert vector_size == 1024, f"集合维度错误: {vector_size}"
    print(f"✅ 集合维度正确: {vector_size}")
    
    # 清理
    client.delete_collection(collection_name)
```

---

## 八、风险和注意事项

### 8.1 风险

| 风险 | 级别 | 影响 | 缓解措施 |
|-----|-----|------|---------|
| **维度不匹配** | 🔴 高 | 搜索失败或结果错误 | 严格验证所有向量维度 |
| **集合命名错误** | 🟡 中 | 无法找到集合 | 强制使用_1024后缀 |
| **模型输出错误** | 🟡 中 | 生成错误维度向量 | 测试模型输出维度 |
| **数据迁移** | 🟡 中 | 旧数据维度不兼容 | 提供维度转换工具 |

### 8.2 注意事项

1. **所有向量必须是1024维**
   - BGE-M3模型输出需要扩展
   - 查询向量需要扩展
   - 结果向量需要验证

2. **集合命名必须遵循规范**
   - 格式: `{name}_1024`
   - 示例: `legal_main_1024`, `patent_applications_1024`

3. **维度验证必须严格**
   - 输入向量: 1024维
   - 存储向量: 1024维
   - 查询向量: 1024维

---

## 九、迁移时间估算

| 任务 | 预计时间 |
|-----|---------|
| 维度配置检查 | 30分钟 |
| BGE-M3模型测试 | 30分钟 |
| Qdrant集合验证 | 30分钟 |
| Handler包装器创建 | 30分钟 |
| 维度兼容性处理 | 30分钟 |
| 测试验证 | 30分钟 |
| 文档更新 | 30分钟 |

**总计**: 约3.5小时（原估计2小时，增加1.5小时用于维度处理）

---

## 十、下一步

### 10.1 立即行动

1. ✅ 更新维度配置文档
2. ⏳ 运行维度验证测试
3. ⏳ 测试BGE-M3模型输出维度
4. ⏳ 验证Qdrant集合维度
5. ⏳ 创建Handler包装器（含维度处理）

### 10.2 验证通过后

1. 创建Handler包装器
2. 添加维度验证
3. 测试所有功能
4. 更新文档
5. 提交代码

---

**维护者**: 徐健 (xujian519@gmail.com)
**创建者**: Claude Code (Sonnet 4.6)
**最后更新**: 2026-04-19 22:15

---

**重要提醒**: ⚠️ **本项目使用1024维向量，而非标准的768维！**
