# 专利全文处理系统 Schema 定义文档

## 版本信息

- **版本**: v3.0.0
- **创建时间**: 2025-12-25
- **作者**: Athena平台团队

---

## 一、Qdrant向量数据库Schema

### 1.1 集合配置

```yaml
集合名称: patent_full_text_v2
向量维度: 768 (BGE-base-zh-v1.5)
距离度量: Cosine
分片数: 4
副本数: 1
```

### 1.2 向量类型（分层架构）

#### Layer 1: 全局检索层（粗筛）

| 向量类型 | 说明 | 数量/专利 | 用途 |
|---------|------|----------|------|
| `title` | 标题向量 | 1 | 快速匹配 |
| `abstract` | 摘要向量 | 1 | 技术概述 |
| `ipc_classification` | IPC分类向量 | 1 | 领域筛选 |

#### Layer 2: 核心内容层（精排）

| 向量类型 | 说明 | 数量/专利 | 用途 |
|---------|------|----------|------|
| `independent_claim` | 独立权利要求向量 | 1-3 | 核心保护范围 |
| `dependent_claim` | 从属权利要求向量 | 5-20 | 细化特征 |

#### Layer 3: 发明内容层（深度分析）

| 向量类型 | 说明 | 数量/专利 | 用途 |
|---------|------|----------|------|
| `technical_problem` | 技术问题向量 | 1 | 问题定位 |
| `technical_solution` | 技术方案向量 | 1-3 | 方案理解 |
| `beneficial_effect` | 有益效果向量 | 1 | 效果对比 |
| `embodiment` | 具体实施方式向量 | 2-10 | 实施细节 |

### 1.3 Payload结构

```python
{
    # ========== 基础信息 ============
    "patent_number": "CN112233445A",
    "publication_date": 20210815,  # YYYYMMDD
    "application_date": 20201201,

    # ========== IPC分类 ============
    "ipc_main_class": "G06F",
    "ipc_subclass": "G06F40/00",
    "ipc_full_path": "G→G06→G06F→G06F40",

    # ========== 专利类型 ============
    "patent_type": "invention",  # invention/utility_model/design
    "legal_status": "active",

    # ========== 向量类型标识 ============
    "vector_type": "independent_claim",
    "section": "权利要求书",

    # ========== 权利要求专用 ============
    "claim_number": 1,
    "claim_type": "independent",

    # ========== 发明内容专用 ============
    "content_section": "技术方案",
    "chunk_index": 0,
    "total_chunks": 3,

    # ========== 内容标识 ============
    "text": "实际文本内容（前500字符）",
    "text_hash": "md5值",
    "token_count": 234,
    "language": "zh"
}
```

### 1.4 Payload索引

```python
payload_schema = {
    # 基础信息索引
    "patent_number": "keyword",
    "publication_date": "integer",
    "application_date": "integer",

    # IPC分类索引
    "ipc_main_class": "keyword",
    "ipc_subclass": "keyword",

    # 专利类型索引
    "patent_type": "keyword",
    "legal_status": "keyword",

    # 向量类型索引
    "vector_type": "keyword",
    "claim_type": "keyword",
    "content_section": "keyword",

    # 权利要求索引
    "claim_number": "integer",

    # 分块索引
    "chunk_index": "integer",
    "total_chunks": "integer",

    # Token数量索引
    "token_count": "integer"
}
```

---

## 二、NebulaGraph知识图谱Schema

### 2.1 图空间配置

```yaml
空间名称: patent_full_text_v2
分区数: 10
副本数: 1
VID类型: FIXED_STRING(32)
```

### 2.2 TAG（顶点类型）

#### 基础顶点

| TAG名称 | 属性数量 | 说明 |
|---------|---------|------|
| `patent` | 12 | 专利基本信息 |
| `claim` | 7 | 权利要求 |
| `applicant` | 5 | 申请人 |
| `ipc_class` | 6 | IPC分类 |

#### 技术分析顶点（核心）

| TAG名称 | 属性数量 | 说明 |
|---------|---------|------|
| `technical_problem` | 6 | 技术问题 |
| `technical_feature` | 7 | 技术特征 |
| `technical_effect` | 6 | 技术效果 |
| `solution` | 5 | 技术方案 |

#### 对比分析顶点

| TAG名称 | 属性数量 | 说明 |
|---------|---------|------|
| `contrast_document` | 5 | 对比文件（D1/D2/D3） |
| `discriminating_feature` | 6 | 区别技术特征 |

### 2.3 EDGE（边类型）

#### 基础关系

| EDGE名称 | 属性 | 说明 |
|---------|------|------|
| `HAS_CLAIM` | sequence: int | patent → claim |
| `HAS_APPLICANT` | role: string | patent → applicant |
| `BELONGS_TO_IPC` | - | patent → ipc_class |
| `DEPENDS_ON` | sequence: int | claim → claim |

#### 技术逻辑关系（三元组）

| EDGE名称 | 属性 | 说明 |
|---------|------|------|
| `SOLVES` | support_score: float | feature → problem |
| `ACHIEVES` | contribution_score: float | feature → effect |
| `RELATES_TO` | relation_type, strength, description | feature → feature |

#### 方案构成关系

| EDGE名称 | 属性 | 说明 |
|---------|------|------|
| `CONSISTS_OF` | role: string | solution → feature |

#### 对比分析关系

| EDGE名称 | 属性 | 说明 |
|---------|------|------|
| `CITES` | citation_type: string | patent → patent |
| `SIMILAR_TO` | similarity_score, similar_aspects | patent → patent |
| `HAS_D1` | - | patent → contrast_document |
| `NOT_IN_D1` | - | discriminating_feature → contrast_document |
| `REVEALED_BY` | revelation_type: string | discriminating_feature → contrast_document |

### 2.4 核心三元组

```cypher
// 问题-特征-效果三元组
(technical_feature) -[:SOLVES]-> (technical_problem)
(technical_feature) -[:ACHIEVES]-> (technical_effect)

// 特征间关系
(technical_feature) -[:RELATES_TO]-> (technical_feature)
  ├─ relation_type: COMBINATIONAL  # 组合
  ├─ relation_type: DEPENDENT      # 依赖
  ├─ relation_type: ALTERNATIVE    # 替代
  ├─ relation_type: SEQUENTIAL     # 顺序
  ├─ relation_type: HIERARCHICAL   # 层次
  └─ relation_type: CAUSAL         # 因果
```

### 2.5 图谱示例

```
        ┌─────────────────┐
        │   Patent P1     │
        │ CN112233445A    │
        └────────┬────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  Feature F1  │  │  Feature F2  │
│  CNN模块     │  │  注意力机制  │
└──────┬───────┘  └──────┬───────┘
       │                 │
       │      SOLVES      │
       ▼                 ▔─────┐
┌──────────────┐            │
│  Problem P1  │            │
│  精度低       │<───────────┘
└──────────────┘      RELATES_TO
                            │
       ┌────────────────────┘
       │
       ▼
┌──────────────┐
│  Effect E1   │
│  提高准确率  │
└──────────────┘
```

---

## 三、数据模型

### 3.1 技术问题

```python
TechnicalProblem:
    id: str
    description: str              # 问题描述
    problem_type: str            # technical/cost/efficiency/safety
    source_section: str          # background/invention_content
    severity: float              # 严重程度 0-1
```

### 3.2 技术特征

```python
TechnicalFeature:
    id: str
    description: str              # 特征描述
    feature_category: str         # structural/functional/performance
    feature_type: str            # component/parameter/process/structure
    source_claim: int             # 来源权利要求号
    importance: float             # 重要性 0-1
```

### 3.3 技术效果

```python
TechnicalEffect:
    id: str
    description: str              # 效果描述
    effect_type: str             # direct/indirect
    quantifiable: bool            # 是否可量化
    metrics: str                 # 量化指标（如"提高10%"）
```

### 3.4 特征关系

```python
FeatureRelation:
    from_feature: str
    to_feature: str
    relation_type: str           # COMBINATIONAL/DEPENDENT/ALTERNATIVE/...
    strength: float              # 关系强度 0-1
    description: str
```

### 3.5 三元组

```python
Triple:
    subject: str                 # 通常是feature
    relation: str                # SOLVES/ACHIEVES
    object: str                  # problem/effect
    confidence: float            # 置信度
```

---

## 四、存储估算

### 4.1 Qdrant存储

**假设**: 100万件专利

| 指标 | 单件专利 | 100万件专利 |
|------|---------|------------|
| 平均向量数 | 20个 | 2000万个 |
| 向量存储 | ~15KB | ~15GB |
| Payload存储 | ~5KB | ~5GB |
| **总计** | **~20KB** | **~20GB** |

### 4.2 NebulaGraph存储

| 指标 | 单件专利 | 100万件专利 |
|------|---------|------------|
| 顶点数 | 30-50个 | 3000-5000万个 |
| 边数 | 50-100个 | 5000万-1亿条 |
| 图存储 | ~10KB | ~10GB |
| **总计** | **~10KB** | **~10GB** |

### 4.3 总存储成本

```
单件专利: ~30KB
100万件专利: ~30GB
1000万件专利: ~300GB
```

---

## 五、API接口

### 5.1 向量化API

```python
# 向量化单个专利
result = await vectorizer.vectorize_patent(patent_data)

# 批量向量化
results = await vectorizer.batch_vectorize(patent_list, max_workers=4)
```

### 5.2 三元组提取API

```python
# 提取三元组
result = await extractor.extract_triples(
    patent_text=text,
    use_cloud_llm=False,
    confidence_threshold=0.7
)

# 获取统计
stats = await extractor.get_extraction_statistics()
```

### 5.3 知识图谱API

```python
# 构建图谱
result = await kg_builder.build_patent_kg(patent_data, triple_result)

# 查询相似专利
similar = await kg_builder.query_similar_patents(
    patent_id="CN112233445A",
    similarity_threshold=0.75
)
```

---

## 六、使用示例

### 6.1 创建Schema

```python
# Qdrant
from phase3.qdrant_schema import get_schema_manager

manager = get_schema_manager()
config = manager.get_create_collection_payload()
qdrant_client.create_collection(**config)

# NebulaGraph
from phase3.nebula_schema import NebulaSchemaManager

manager = NebulaSchemaManager()
sql = manager.get_full_schema_sql()
# 执行SQL创建Schema
```

### 6.2 向量化专利

```python
from phase3 import PatentVectorizerV2

vectorizer = PatentVectorizerV2()
result = await vectorizer.vectorize_patent(patent_data)

print(f"向量化完成: {result.total_vector_count}个向量")
print(f"Layer 1: {len(result.layer1_vectors)}个")
print(f"Layer 2: {len(result.layer2_vectors)}个")
print(f"Layer 3: {len(result.layer3_vectors)}个")
```

### 6.3 提取三元组

```python
from phase3 import HybridTripleExtractor

extractor = HybridTripleExtractor()
result = await extractor.extract_triples(patent_text)

print(f"技术问题: {len(result.problems)}个")
print(f"技术特征: {len(result.features)}个")
print(f"技术效果: {len(result.effects)}个")
print(f"三元组: {len(result.triples)}个")
print(f"特征关系: {len(result.feature_relations)}个")
```

---

## 七、相关文档

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 系统架构文档
- [USER_GUIDE.md](./USER_GUIDE.md) - 用户使用指南
- [API_REFERENCE.md](./API_REFERENCE.md) - API参考手册
