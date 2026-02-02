
# 混合搜索引擎使用指南

## 概述
混合搜索引擎结合了JanusGraph知识图谱和Qdrant向量数据库的优势，提供：
- 语义相似度搜索（基于向量）
- 知识关系挖掘（基于图数据库）
- 多维度相关性排序
- 高性能检索能力

## 使用方式

### 1. 纯向量搜索
```python
results = await hybrid_search.vector_search(
    collection_name="knowledge_graph_entities",
    query_text="深度学习专利分析",
    limit=5
)
```

### 2. 纯图搜索
```python
results = hybrid_search.simulate_graph_search(
    entity_type="Patent",
    property_filter={"priority": "高"}
)
```

### 3. 混合搜索
```python
results = await hybrid_search.hybrid_search(
    collection_name="knowledge_graph_entities",
    query_text="AI专利分析方法",
    entity_type="Patent",
    limit=5
)
```

## 搜索类型

### 语义搜索
- 使用自然语言描述进行搜索
- 基于向量相似度匹配
- 适合内容检索和概念搜索

### 混合搜索
- 结合语义和关系信息
- 提供更丰富的上下文
- 支持精确的实体查询

### 关系挖掘
- 发现实体间的隐藏关系
- 支持多跳关系查询
- 提供网络分析能力

## 应用场景

1. **专利检索**: 通过技术描述查找相关专利
2. **竞争分析**: 分析竞争对手的专利布局
3. **技术趋势**: 发现技术演进路径和关联
4. **法律研究**: 查找相关案例和法律条文
5. **专家发现**: 找到特定领域的发明人和专家

## 性能优化
- 使用索引加速查询
- 缓存热门搜索结果
- 分页处理大数据集
- 并行处理多个查询
