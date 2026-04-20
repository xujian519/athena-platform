# knowledge_graph_search工具使用指南

> **工具名称**: knowledge_graph_search（知识图谱搜索）
> **工具ID**: `knowledge_graph_search`
> **版本**: 1.0.0
> **作者**: Athena Team

---

## 快速开始

### 1. 获取工具

```python
from core.tools.unified_registry import get_unified_registry

# 获取统一工具注册表
registry = get_unified_registry()

# 获取知识图谱搜索工具
kg_tool = registry.get("knowledge_graph_search")
```

### 2. 基础使用

```python
# 执行Cypher查询
result = await kg_tool.function(
    query="MATCH (n) RETURN n LIMIT 10",
    query_type="cypher"
)

# 检查结果
if result['success']:
    print(f"找到 {result['count']} 个节点")
    for node in result['results']:
        print(node)
else:
    print(f"查询失败: {result['error']}")
```

---

## 核心功能

### 功能1: Cypher查询

```python
# 查询所有Patent节点
result = await kg_tool.function(
    query="MATCH (n:Patent) RETURN n ORDER BY n.id LIMIT 20",
    query_type="cypher",
    top_k=20
)

# 查询特定节点
result = await kg_tool.function(
    query="MATCH (n:Patent {id: 'CN123456789A'}) RETURN n",
    query_type="cypher"
)

# 复杂查询 - 查找引用关系
result = await kg_tool.function(
    query="""
    MATCH (p1:Patent)-[r:CITES]->(p2:Patent)
    RETURN p1.id, p2.id, r.citation_date
    LIMIT 50
    """,
    query_type="cypher"
)
```

### 功能2: 获取统计信息

```python
# 获取图谱统计
result = await kg_tool.function(
    query="",
    query_type="stats"
)

stats = result['results'][0]
print(f"后端类型: {stats['backend']}")
print(f"节点总数: {stats['node_count']}")
print(f"边总数: {stats['edge_count']}")
print(f"标签类型: {stats['tag_types']}")
print(f"关系类型: {stats['edge_types']}")
```

### 功能3: 路径查找

```python
# 查找两个节点之间的最短路径
result = await kg_tool.function(
    query="""
    MATCH path = shortestPath(
        (start:Patent {id: 'CN123456789A'})-[*..5]-(end:Patent {id: 'CN987654321A'})
    )
    RETURN path, length(path) as path_length
    """,
    query_type="path"
)

# 查找所有路径（不超过3跳）
result = await kg_tool.function(
    query="""
    MATCH path = (start:Patent {id: 'CN123456789A'})-[*..3]-(end:Patent)
    RETURN path, length(path) as path_length
    ORDER BY path_length
    LIMIT 10
    """,
    query_type="cypher"
)
```

### 功能4: 邻居查询

```python
# 查找节点的所有邻居
result = await kg_tool.function(
    query="(n:Patent {id: 'CN123456789A'})",
    query_type="neighbors",
    top_k=20
)

# 查找特定类型的邻居
result = await kg_tool.function(
    query="""
    MATCH (n:Patent {id: 'CN123456789A'})-[r:CITES]->(neighbor)
    RETURN neighbor, r
    LIMIT 20
    """,
    query_type="cypher"
)
```

---

## 便捷函数

### 1. 获取统计信息

```python
from core.tools.knowledge_graph_handler import get_graph_statistics

stats = await get_graph_statistics()
print(f"节点数: {stats['results'][0]['node_count']}")
```

### 2. 按关键词搜索专利

```python
from core.tools.knowledge_graph_handler import search_patents_by_keyword

# 搜索包含"人工智能"的专利
result = await search_patents_by_keyword(
    keyword="人工智能",
    limit=10
)

for item in result['results']:
    patent = item['n']
    print(f"专利ID: {patent['id']}")
    print(f"标题: {patent['title']}")
```

### 3. 查找相关专利

```python
from core.tools.knowledge_graph_handler import find_related_patents

# 查找引用了指定专利的专利
result = await find_related_patents(
    patent_id="CN123456789A",
    relationship_type="CITES",
    limit=10
)

for item in result['results']:
    related_patent = item['p2']
    rel_type = item['relationship_type']
    print(f"相关专利: {related_patent['id']}")
    print(f"关系类型: {rel_type}")
```

### 4. 查找最短路径

```python
from core.tools.knowledge_graph_handler import find_shortest_path

# 查找两个专利之间的最短路径
result = await find_shortest_path(
    start_id="CN123456789A",
    end_id="CN987654321A",
    max_depth=5
)

if result['success'] and result['count'] > 0:
    path_info = result['results'][0]
    print(f"路径长度: {path_info['path_length']}")
    print(f"路径: {path_info['path']}")
```

---

## 常见查询模式

### 模式1: 按属性筛选

```python
# 查找特定申请人的专利
result = await kg_tool.function(
    query="""
    MATCH (n:Patent {applicant: '某某公司'})
    RETURN n
    ORDER BY n.filing_date DESC
    LIMIT 20
    """,
    query_type="cypher"
)

# 查找特定时间范围的专利
result = await kg_tool.function(
    query="""
    MATCH (n:Patent)
    WHERE n.filing_date >= '2020-01-01' AND n.filing_date < '2021-01-01'
    RETURN n
    LIMIT 20
    """,
    query_type="cypher"
)
```

### 模式2: 聚合统计

```python
# 统计每个申请人的专利数量
result = await kg_tool.function(
    query="""
    MATCH (n:Patent)
    RETURN n.applicant as applicant, count(n) as patent_count
    ORDER BY patent_count DESC
    LIMIT 10
    """,
    query_type="cypher"
)

# 统计每年的专利数量
result = await kg_tool.function(
    query="""
    MATCH (n:Patent)
    RETURN substring(n.filing_date, 0, 4) as year, count(n) as patent_count
    ORDER BY year
    """,
    query_type="cypher"
)
```

### 模式3: 关系分析

```python
# 查找高被引专利
result = await kg_tool.function(
    query="""
    MATCH (p:Patent)<-[r:CITES]-(other:Patent)
    RETURN p.id as patent_id, p.title as title, count(r) as citation_count
    ORDER BY citation_count DESC
    LIMIT 10
    """,
    query_type="cypher"
)

# 查找专利网络中的关键节点（中介中心性）
result = await kg_tool.function(
    query="""
    MATCH (p:Patent)
    WHERE size((p)-[]-()) > 10
    RETURN p.id, p.title, size((p)-[]-()) as connection_count
    ORDER BY connection_count DESC
    LIMIT 10
    """,
    query_type="cypher"
)
```

### 模式4: 社区发现

```python
# 查找紧密连接的专利集群
result = await kg_tool.function(
    query="""
    MATCH (p:Patent)-[r:CITES]-(other:Patent)
    WITH p, count(r) as connection_count
    WHERE connection_count >= 5
    RETURN p.id, p.title, connection_count
    ORDER BY connection_count DESC
    LIMIT 20
    """,
    query_type="cypher"
)
```

---

## 错误处理

### 1. 检查查询是否成功

```python
result = await kg_tool.function(
    query="MATCH (n) RETURN n",
    query_type="cypher"
)

if result['success']:
    print(f"查询成功，找到 {result['count']} 个结果")
else:
    print(f"查询失败: {result['error']}")
```

### 2. 处理空结果

```python
result = await kg_tool.function(
    query="MATCH (n:Patent {id: 'NONEXISTENT'}) RETURN n",
    query_type="cypher"
)

if result['success'] and result['count'] > 0:
    print(f"找到 {result['count']} 个结果")
else:
    print("没有找到匹配的结果")
```

### 3. 超时处理

```python
# 复杂查询设置合理的top_k限制
result = await kg_tool.function(
    query="""
    MATCH (p1:Patent)-[r*1..5]-(p2:Patent)
    RETURN p1, p2
    """,
    query_type="cypher",
    top_k=100  # 限制结果数量
)
```

---

## 性能优化建议

### 1. 使用LIMIT

```python
# ✅ 好的做法 - 使用LIMIT
result = await kg_tool.function(
    query="MATCH (n:Patent) RETURN n LIMIT 100",
    query_type="cypher"
)

# ❌ 不好的做法 - 可能返回数百万条记录
result = await kg_tool.function(
    query="MATCH (n:Patent) RETURN n",
    query_type="cypher"
)
```

### 2. 使用索引

```python
# 如果经常按ID查询，确保有索引
# CREATE INDEX ON :Patent(id)

result = await kg_tool.function(
    query="MATCH (n:Patent {id: 'CN123456789A'}) RETURN n",
    query_type="cypher"
)
```

### 3. 避免笛卡尔积

```python
# ✅ 好的做法 - 明确关系
result = await kg_tool.function(
    query="""
    MATCH (p1:Patent)-[r:CITES]->(p2:Patent)
    RETURN p1, p2
    LIMIT 100
    """,
    query_type="cypher"
)

# ❌ 不好的做法 - 可能产生笛卡尔积
result = await kg_tool.function(
    query="""
    MATCH (p1:Patent), (p2:Patent)
    RETURN p1, p2
    LIMIT 100
    """,
    query_type="cypher"
)
```

### 4. 使用参数化查询（未来功能）

```python
# 当前使用字符串拼接
query = f"MATCH (n:Patent {{id: '{patent_id}'}}) RETURN n"

# 未来将支持参数化查询（更安全）
# query = "MATCH (n:Patent {id: $patent_id}) RETURN n"
# params = {"patent_id": patent_id}
```

---

## 实际应用场景

### 场景1: 专利侵权分析

```python
# 查找与目标专利高度相似的专利
target_patent_id = "CN123456789A"

result = await kg_tool.function(
    query="""
    MATCH (target:Patent {id: $target_id})-[r:SIMILAR_TO]-(similar:Patent)
    WHERE r.similarity_score >= 0.8
    RETURN similar.id, similar.title, r.similarity_score
    ORDER BY r.similarity_score DESC
    LIMIT 20
    """.replace("$target_id", f"'{target_patent_id}'"),
    query_type="cypher"
)

print("高风险专利:")
for item in result['results']:
    print(f"  - {item['similar.id']} (相似度: {item['r.similarity_score']})")
```

### 场景2: 技术趋势分析

```python
# 分析专利技术关键词的时间趋势
result = await kg_tool.function(
    query="""
    MATCH (n:Patent)
    WHERE n.filing_date >= '2018-01-01'
    WITH substring(n.filing_date, 0, 4) as year, n.keywords as keywords
    UNWIND keywords as keyword
    RETURN year, keyword, count(*) as patent_count
    ORDER BY year, patent_count DESC
    """,
    query_type="cypher"
)

# 按年份组织数据
trends = {}
for item in result['results']:
    year = item['year']
    keyword = item['keyword']
    count = item['patent_count']

    if year not in trends:
        trends[year] = {}
    trends[year][keyword] = count

print("技术趋势:")
for year, keywords in sorted(trends.items()):
    print(f"\n{year}年:")
    top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:5]
    for keyword, count in top_keywords:
        print(f"  - {keyword}: {count}件专利")
```

### 场景3: 竞争对手分析

```python
# 分析竞争对手的专利布局
competitor = "某某科技公司"

result = await kg_tool.function(
    query=f"""
    MATCH (n:Patent {{applicant: '{competitor}'}})
    WITH substring(n.filing_date, 0, 4) as year, count(n) as patent_count
    RETURN year, patent_count
    ORDER BY year
    """,
    query_type="cypher"
)

print(f"{competitor} 专利申请趋势:")
for item in result['results']:
    print(f"  {item['year']}: {item['patent_count']}件")
```

### 场景4: 专利价值评估

```python
# 基于引用关系评估专利价值
patent_id = "CN123456789A"

result = await kg_tool.function(
    query=f"""
    MATCH (p:Patent {{id: '{patent_id}'}})
    OPTIONAL MATCH (p)<-[r:CITES]-(citing:Patent)
    RETURN
        p.id as patent_id,
        p.title as title,
        count(r) as citation_count,
        size((p)-[:CITES]->()) as forward_citations,
        size((p)-[]-()) as total_connections
    """,
    query_type="cypher"
)

if result['count'] > 0:
    metrics = result['results'][0]
    print(f"专利ID: {metrics['patent_id']}")
    print(f"标题: {metrics['title']}")
    print(f"被引次数: {metrics['citation_count']}")
    print(f"引用他人: {metrics['forward_citations']}")
    print(f"总连接数: {metrics['total_connections']}")
```

---

## 故障排查

### 问题1: 连接失败

```
错误: "Failed to connect to Neo4j"
```

**解决方案**:
1. 检查Neo4j容器是否运行: `docker ps | grep neo4j`
2. 检查连接配置: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`
3. 启动Neo4j: `docker-compose up -d neo4j`

### 问题2: 查询超时

```
错误: "Query execution timeout"
```

**解决方案**:
1. 使用`top_k`参数限制结果数量
2. 简化查询逻辑
3. 添加索引加速查询

### 问题3: 语法错误

```
错误: "Invalid Cypher syntax"
```

**解决方案**:
1. 检查Cypher语法是否正确
2. 使用Neo4j Browser测试查询
3. 查看详细的错误信息

---

## 参考资料

- **Neo4j Cypher手册**: https://neo4j.com/docs/cypher-manual/
- **统一工具注册表API**: `docs/api/UNIFIED_TOOL_REGISTRY_API.md`
- **知识图谱验证报告**: `docs/reports/KNOWLEDGE_GRAPH_SEARCH_TOOL_VERIFICATION_REPORT_20260419.md`
- **测试脚本**: `tests/test_knowledge_graph_tool.py`

---

**最后更新**: 2026-04-19
**版本**: 1.0.0
