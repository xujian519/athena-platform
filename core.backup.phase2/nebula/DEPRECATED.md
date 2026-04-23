# NebulaGraph 模块已弃用

## 弃用声明

**弃用日期**: 2026-01-27
**替代方案**: Neo4j 5.26.19

## 原因

平台已决定全面使用 Neo4j 作为知识图谱数据库，弃用 NebulaGraph。

## 迁移指南

### 1. 导入路径变更

```python
# ❌ 旧方式 (已弃用)
from core.nebula.nebula_graph_client import NebulaGraphClient

# ✅ 新方式 (使用 Neo4j)
from core.knowledge.neo4j_client import Neo4jClient
from neo4j import GraphDatabase
```

### 2. 查询语言变更

```cypher
# ❌ nGQL (NebulaGraph)
GO FROM "entity" OVER * YIELD vertices($$)

# ✅ Cypher (Neo4j)
MATCH (n {name: "entity"})-[r]->(m) RETURN n, r, m
```

### 3. 连接配置变更

```python
# ❌ 旧方式
nebula_pool = NebulaGraphPool(...)
session = nebula_pool.get_session(username, password)

# ✅ 新方式
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "athena_neo4j_2024")
)
session = driver.session()
```

## 受影响的文件

以下文件已标记为弃用，请使用对应的 Neo4j 版本：

| 旧文件 (弃用) | 新文件 (Neo4j) |
|--------------|---------------|
| `core/nebula/nebula_graph_client.py` | `core/kg/neo4j_kg_expansion.py` |
| `core/nlp/nebula_enhanced_intent_classifier.py` | `core/nlp/neo4j_enhanced_intent_classifier.py` |
| `core/nlp/nebula_graph_enhanced_intent.py` | `core/nlp/neo4j_graph_enhanced_intent.py` |
| `core/judgment_vector_db/storage/nebula_client.py` | `core/judgment_vector_db/storage/neo4j_client.py` |

## 数据迁移

如需从 NebulaGraph 迁移数据到 Neo4j，请参考：

```bash
python scripts/migrate_nebulagraph_to_neo4j.py
```

## 配置更新

在 `config/database_config.yaml` 中：

```yaml
# ❌ 删除 NebulaGraph 配置
# arangodb:  # (旧配置)
#   type: arangodb
#   port: 8529

# ✅ 使用 Neo4j 配置
neo4j:
  uri: "bolt://localhost:7687"
  user: "neo4j"
  password: "athena_neo4j_2024"
  database: "neo4j"
```

## 联系方式

如有疑问，请联系 Athena 平台团队。
