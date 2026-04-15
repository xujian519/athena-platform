# 混合搜索集成示例

## Python客户端

```python客户端

from qdrant_client import QdrantClient
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

class HybridSearchClient:
    def __init__(self):
        self.qdrant = QdrantClient(host="localhost", port=6333)
        self.janusgraph = traversal().withRemote(
            DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
        )

    async def hybrid_search(self, query: str, entity_type: str = None, limit: int = 10):
        # 1. 向量搜索
        vector_results = await self.vector_search(query, limit)

        # 2. 图搜索
        graph_results = self.graph_search(entity_type) if entity_type else []

        # 3. 融合结果
        return self.merge_results(vector_results, graph_results)

    def merge_results(self, vector_results, graph_results):
        # 实现智能融合算法
        merged = []
        # ... 融合逻辑
        return merged

```

## REST API

```rest api

# 语义搜索
POST /api/v2/hybrid/search
{
    "query": "深度学习专利分析方法",
    "entity_type": "Patent",
    "limit": 5,
    "filters": {
        "category": "人工智能",
        "date_range": "2020-2024"
    }
}

# 响应
{
    "results": [
        {
            "id": "patent_001",
            "type": "Patent",
            "title": "基于深度学习的专利分析系统",
            "relevance_score": 0.95,
            "relationships": [
                {
                    "type": "ASSIGNED_TO",
                    "target": "company_athena",
                    "weight": 0.9
                }
            ]
        }
    ],
    "total": 15,
    "search_time_ms": 45
}

```

## SQL查询

```sql查询

-- 向量相似度查询
SELECT entity_id,
       1 - (vector <=> query_vector) as similarity
FROM knowledge_graph_entities
ORDER BY similarity DESC
LIMIT 10;

-- 关系路径查询
WITH RECURSIVE entity_path AS (
    SELECT id, type, 0 as depth, ARRAY[id] as path
    FROM entities
    WHERE id = 'patent_001'

    UNION ALL

    SELECT e.id, e.type, ep.depth + 1, ep.path || e.id
    FROM entity_path ep
    JOIN relations r ON ep.id = r.source_id
    JOIN entities e ON r.target_id = e.id
    WHERE ep.depth < 3 AND NOT e.id = ANY(ep.path)
)
SELECT * FROM entity_path ORDER BY depth, id;

```

