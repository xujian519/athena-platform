# Athena知识图谱API文档（NebulaGraph版）

## 📋 API概述

**服务名称**: Athena知识图谱API
**技术栈**: NebulaGraph
**版本**: v1.0.0
**基础URL**: `http://localhost:8001`
**替代说明**: 本API替代原Neo4j知识图谱API

---

## 🔗 替代关系

| 废弃模块 | 新模块 | 状态 |
|----------|--------|------|
| `utils/knowledge-graph/optimized_kg_api.py` | `domains/patent-ai/services/nebula_knowledge_api.py` | ✅ 已替代 |
| `services/dev/scripts/knowledge_graph_query_api.py` | `domains/patent-ai/services/nebula_knowledge_api.py` | ✅ 已替代 |

---

## 📡 API端点

### 1. 服务信息

#### GET `/`

获取API服务基本信息。

**响应示例**:
```json
{
  "service": "Athena知识图谱API (NebulaGraph)",
  "version": "1.0.0",
  "status": "running",
  "backend": "NebulaGraph",
  "docs_url": "/docs"
}
```

---

### 2. 健康检查

#### GET `/health`

检查服务健康状态。

**响应示例**:
```json
{
  "status": "healthy",
  "message": "连接正常"
}
```

---

### 3. 创建节点

#### POST `/nodes`

创建图节点。

**请求体**:
```json
{
  "label": "Patent",
  "vid": "patent_cn12345",
  "properties": {
    "title": "一种人工智能算法",
    "abstract": "本发明涉及...",
    "applicant": "某某公司",
    "application_date": "2023-01-01"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "vid": "patent_cn12345",
  "label": "Patent",
  "message": "节点创建成功"
}
```

---

### 4. 创建边

#### POST `/edges`

创建图边。

**请求体**:
```json
{
  "edge_type": "CITES",
  "src_vid": "patent_cn12345",
  "dst_vid": "patent_cn67890",
  "properties": {
    "strength": "0.8",
    "date": "2023-06-01"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "edge_type": "CITES",
  "src": "patent_cn12345",
  "dst": "patent_cn67890",
  "message": "边创建成功"
}
```

---

### 5. 执行nGQL查询

#### POST `/query`

执行自定义nGQL查询。

**请求体**:
```json
{
  "query": "MATCH (n:Patent) RETURN n LIMIT 10",
  "parameters": {}
}
```

**响应示例**:
```json
{
  "success": true,
  "count": 10,
  "reports/reports/results": [
    {
      "n": {
        "title": "一种人工智能算法",
        "applicant": "某某公司"
      }
    }
  ]
}
```

---

### 6. 查找路径

#### POST `/path`

查找两个节点之间的路径。

**请求体**:
```json
{
  "src_vid": "patent_cn12345",
  "dst_vid": "patent_cn67890",
  "edge_type": "CITES",
  "direction": "BOTH",
  "max_steps": 3
}
```

**响应示例**:
```json
{
  "success": true,
  "count": 1,
  "paths": [...]
}
```

---

### 7. 查询邻居

#### POST `/neighbors`

查询节点的邻居节点。

**请求体**:
```json
{
  "vid": "patent_cn12345",
  "edge_type": "CITES",
  "direction": "OUTGOING",
  "depth": 1
}
```

**响应示例**:
```json
{
  "success": true,
  "count": 5,
  "neighbors": [...]
}
```

---

### 8. 获取统计信息

#### GET `/statistics`

获取图谱统计信息。

**响应示例**:
```json
{
  "success": true,
  "statistics": {
    "Patent_count": 1000,
    "Company_count": 500,
    "CITES_count": 2000,
    "total_tags": 6,
    "total_edge_types": 5
  }
}
```

---

### 9. 获取图Schema

#### GET `/schema`

获取图模式定义。

**响应示例**:
```json
{
  "success": true,
  "schema": {
    "tags": {
      "Patent": ["title", "abstract", "applicant"],
      "Company": ["name", "type", "country"]
    },
    "edges": {
      "CITES": ["strength", "date"],
      "BELONGS_TO": ["since", "role"]
    }
  }
}
```

---

### 10. 清除缓存

#### POST `/cache/clear`

清除查询缓存。

**响应示例**:
```json
{
  "success": true,
  "message": "缓存已清除"
}
```

---

## 🔧 nGQL快速参考

### 创建节点

```ngql
INSERT VERTEX Patent(title, abstract) VALUES "patent001":("专利标题", "专利摘要");
```

### 创建边

```ngql
INSERT EDGE CITES(strength) VALUES "patent001"->"patent002":("0.8");
```

### 查询节点

```ngql
MATCH (n:Patent) WHERE n.title CONTAINS "人工智能" RETURN n;
```

### 查询路径

```ngql
FIND SHORTEST PATH FROM "patent001" TO "patent003" OVER * BIDIRECT UPTO 3 STEPS;
```

### 查询邻居

```ngql
GO FROM "patent001" OVER CITES YIELD vertices(edge) AS neighbor;
```

---

## 📊 数据模型

### 节点类型（Tags）

| 标签 | 说明 | 主要属性 |
|------|------|----------|
| Patent | 专利节点 | title, abstract, applicant, ipc |
| Company | 公司节点 | name, type, country, industry |
| Inventor | 发明人节点 | name, country, organization |
| TechnologyField | 技术领域节点 | name, description, ipc_code |
| LegalCase | 法律案件节点 | title, case_number, date, outcome |
| PriorArt | 现有技术节点 | title, publication_number, date |

### 边类型（Edges）

| 边类型 | 说明 | 属性 |
|--------|------|------|
| CITES | 引用关系 | strength, date |
| BELONGS_TO | 归属关系 | since, role |
| INVENTED_BY | 发明关系 | contribution |
| RELATES_TO | 关联关系 | type, strength |
| OPPOSED_BY | 被反对关系 | case_number, outcome |

---

## 🚀 快速开始

### 安装依赖

```bash
pip install nebula3-python fastapi uvicorn
```

### 启动服务

```bash
python domains/patent-ai/services/nebula_knowledge_api.py
```

### 使用Python客户端

```python
from domains.patent_ai.services.nebula_knowledge_api import NebulaGraphService

# 创建服务
service = NebulaGraphService({
    "hosts": ["127.0.0.1"],
    "port": 9669,
    "username": "root",
    "password": "nebula",
    "space_name": "patent_knowledge"
})

# 连接
service.connect()

# 执行查询
results = service.execute_query("MATCH (n:Patent) RETURN n LIMIT 10")
print(results)

# 关闭连接
service.disconnect()
```

---

## 📈 性能优化建议

### 1. 使用索引

```ngql
CREATE TAG INDEX patent_title_index ON Patent(title(20));
```

### 2. 批量操作

```ngql
INSERT VERTEX Patent(title) VALUES
  "p1":("专利1"),
  "p2":("专利2"),
  "p3":("专利3");
```

### 3. 利用缓存

默认启用5分钟查询缓存，可通过以下方式控制：

```python
from domains.patent_ai.services.nebula_knowledge_api import QueryCache, CacheConfig

# 自定义缓存配置
cache = QueryCache(CacheConfig(
    enabled=True,
    ttl=600,  # 10分钟
    max_size=2000
))
```

---

## ⚠️ 注意事项

### 与Neo4j的主要差异

1. **节点ID**: NebulaGraph需要手动指定VID（固定长度字符串）
2. **数据类型**: 属性类型需预先定义在Schema中
3. **查询语法**: nGQL与Cypher语法不同，需要适应
4. **事务支持**: NebulaGraph事务机制与Neo4j不同

### VID生成建议

```python
import hashlib

def generate_vid(original_id: str) -> str:
    """生成固定长度32字符的VID"""
    return hashlib.md5(original_id.encode()).hexdigest()
```

---

## 📞 技术支持

- **迁移指南**: `docs/migration/NEO4J_TO_NEBULA_MIGRATION.md`
- **NebulaGraph文档**: https://docs.nebula-graph.io/
- **问题反馈**: 提交Issue到项目仓库

---

*文档版本: 1.0.0*
*最后更新: 2025-12-25*
