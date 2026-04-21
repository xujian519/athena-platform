# 知识图谱架构文档

> **版本**: 1.0
> **最后更新**: 2026-04-21
> **状态**: 已定稿

---

## 📋 概述

`core/knowledge_graph/` 模块为Athena平台提供知识图谱集成、检索、推理等功能。与 `core/llm/` 模块不同，知识图谱模块采用**扁平架构**，原因是业务特性（多种图数据库支持、法律领域特定推理）不适合过度抽象。

---

## 🏗️ 架构设计

### 为什么采用扁平架构？

**与 `core/llm/` 的对比**：

| 特性 | `core/llm/` | `core/knowledge_graph/` |
|------|-------------|--------------------------|
| **抽象层** | engines → models → services → adapters | 扁平结构 |
| **原因** | 多个LLM提供商接口相似 | Neo4j/ArangoDB接口差异大 |
| **业务特性** | 通用文本生成 | 法律领域特定推理 |
| **数据模型** | 统一（prompt → response） | 多样（三元组、图遍历） |

**扁平架构的优势**：
- ✅ 灵活支持多种图数据库（Neo4j、ArangoDB）
- ✅ 业务逻辑与数据模型紧密耦合（法律推理）
- ✅ 减少过度抽象带来的复杂度
- ✅ 便于快速迭代和实验

---

## 📁 目录结构

```
core/knowledge_graph/
├── __init__.py                       # 模块导出
├── kg_integration.py                 # 集成层（核心API）
├── kg_real_client.py                 # 真实客户端实现
├── legal_kg_reasoning_enhancer.py    # 法律知识图谱推理增强器
├── neo4j_graph_engine.py             # Neo4j引擎
├── arango_engine.py                  # ArangoDB引擎
├── patent_guideline_importer.py      # 专利指南导入器
├── quick_deploy_arangodb.py          # ArangoDB快速部署脚本
├── deploy_arangodb.sh                # ArangoDB部署脚本
└── install_arangodb_*.sh             # ArangoDB安装脚本
```

---

## 🧩 核心模块

### 1. kg_integration.py - 集成层

**职责**：提供统一的知识图谱API

**核心类**：
- `EntityType`: 实体类型枚举（PATENT、CONCEPT、COMPANY等）
- `RelationType`: 关系类型枚举（CONTAINS、BELONGS_TO、CITES等）
- `Entity`: 实体数据类
- `Relation`: 关系数据类
- `KnowledgeGraphClient`: 抽象客户端基类
- `MockKnowledgeGraphClient`: 模拟客户端（测试用）

**核心函数**：
```python
def get_kg_client() -> KnowledgeGraphClient:
    """获取知识图谱客户端（自动选择Mock/Real）"""

def search_concepts(query: str, limit: int = 10) -> list[Entity]:
    """搜索概念节点"""

def expand_query(query: str, graph_type: str) -> str:
    """基于知识图谱扩展查询"""
```

**导入示例**：
```python
from core.knowledge_graph import (
    Entity,
    EntityType,
    KnowledgeGraphClient,
    get_kg_client,
    search_concepts,
)

# 获取客户端
client = get_kg_client()

# 搜索概念
results = search_concepts("深度学习", limit=10)
```

---

### 2. kg_real_client.py - 真实客户端

**职责**：连接真实图数据库的客户端实现

**核心类**：
- `RealKnowledgeGraphClient`: 真实知识图谱客户端

**核心函数**：
```python
def create_knowledge_graph_client(
    backend: str = "neo4j",  # 或 "arango"
    config: dict | None = None
) -> RealKnowledgeGraphClient:
    """创建真实知识图谱客户端"""
```

**使用示例**：
```python
from core.knowledge_graph.kg_real_client import create_knowledge_graph_client

# 创建Neo4j客户端
client = create_knowledge_graph_client(backend="neo4j")

# 创建ArangoDB客户端
client = create_knowledge_graph_client(
    backend="arango",
    config={
        "url": "http://localhost:8529",
        "username": "root",
        "password": "password",
        "database": "athena_patent_db"
    }
)
```

---

### 3. legal_kg_reasoning_enhancer.py - 法律推理增强器

**职责**：基于知识图谱的法律知识推理

**核心类**：
- `LegalEntityType`: 法律实体类型（LEGAL_CONCEPT、CASE、STATUTE等）
- `LegalRelationType`: 法律关系类型（APPLIES_TO、OVERRULED_BY等）
- `GraphReasoningContext`: 推理上下文
- `LegalKGReasoningEnhancer`: 法律推理增强器
- `GraphEnhancedReasoningEngine`: 图增强推理引擎

**使用示例**：
```python
from core.knowledge_graph.legal_kg_reasoning_enhancer import (
    LegalKGReasoningEnhancer,
    GraphReasoningContext,
)

# 创建增强器
enhancer = LegalKGReasoningEnhancer(kg_client=client)

# 创建推理上下文
context = GraphReasoningContext(
    query="专利创造性判断",
    domain="patent_law",
    depth=2
)

# 执行推理
result = enhancer.reason_with_graph(context)
```

---

### 4. neo4j_graph_engine.py - Neo4j引擎

**职责**：Neo4j图数据库引擎

**核心功能**：
- Cypher查询执行
- 图遍历
- 三元组提取
- 专利知识图谱支持

**使用示例**：
```python
from core.knowledge_graph.neo4j_graph_engine import Neo4jGraphEngine

# 创建引擎
engine = Neo4jGraphEngine(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password"
)

# 执行查询
result = engine.execute_cypher(
    "MATCH (p:Patent {id: $id})-[:HAS_FEATURE]->(f) RETURN f",
    {"id": "CN123456789A"}
)
```

---

### 5. arango_engine.py - ArangoDB引擎

**职责**：ArangoDB多模型数据库引擎

**核心功能**：
- AQL查询执行
- 图遍历
- 多数据库支持（专利、商标、法律等）

**使用示例**：
```python
from core.knowledge_graph.arango_engine import ArangoEngine

# 创建引擎
engine = ArangoEngine(
    url="http://localhost:8529",
    username="root",
    password="password",
    database="athena_patent_db"
)

# 执行查询
result = engine.execute_aql(
    "FOR p IN patents FILTER p._key == @key RETURN p",
    bind_vars={"key": "patent_001"}
)
```

---

### 6. patent_guideline_importer.py - 专利指南导入器

**职责**：导入专利审查指南到知识图谱

**核心功能**：
- 解析专利审查指南文档
- 提取法律概念和关系
- 构建专利法律知识图谱

---

## 🚀 快速开始

### 基础使用

```python
from core.knowledge_graph import (
    get_kg_client,
    search_concepts,
    EntityType,
)

# 1. 获取客户端
client = get_kg_client()

# 2. 搜索概念
concepts = search_concepts("深度学习", limit=10)

# 3. 查询实体关系
from core.knowledge_graph import find_entity_relations

relations = find_entity_relations(
    entity_id="patent_001",
    relation_type=EntityType.CITES
)

# 4. 获取图增强器
from core.knowledge_graph import get_graph_enhancer

enhancer = get_graph_enhancer()
enhanced_query = enhancer.expand_query("人工智能专利检索")
```

### 法律推理

```python
from core.knowledge_graph.legal_kg_reasoning_enhancer import (
    LegalKGReasoningEnhancer,
    GraphReasoningContext,
)
from core.knowledge_graph import get_kg_client

# 1. 创建增强器
client = get_kg_client()
enhancer = LegalKGReasoningEnhancer(kg_client=client)

# 2. 创建推理上下文
context = GraphReasoningContext(
    query="本专利是否具备创造性？",
    domain="patent_law",
    patent_id="CN123456789A",
    depth=3
)

# 3. 执行推理
result = enhancer.reason_with_graph(context)

# 4. 获取推理路径
paths = enhancer.get_reasoning_paths(context)
```

### Neo4j数据库

```python
from core.knowledge_graph.neo4j_graph_engine import Neo4jGraphEngine

# 创建引擎
engine = Neo4jGraphEngine(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password"
)

# 执行Cypher查询
result = engine.execute_cypher(
    "MATCH (p:Patent)-[:HAS_FEATURE]->(f) RETURN p, f LIMIT 10"
)

# 提取三元组
triples = engine.extract_patent_triples("CN123456789A")
```

### ArangoDB数据库

```python
from core.knowledge_graph.arango_engine import ArangoEngine

# 创建引擎
engine = ArangoEngine(
    url="http://localhost:8529",
    username="root",
    password="password",
    database="athena_patent_db"
)

# 执行AQL查询
result = engine.execute_aql(
    "FOR p IN patents LIMIT 10 RETURN p"
)

# 图遍历
path = engine.traverse_graph(
    start_vertex="patents/001",
    direction="outbound",
    max_depth=2
)
```

---

## 📊 数据模型

### 实体类型 (EntityType)

| 类型 | 说明 | 示例 |
|------|------|------|
| `PATENT` | 专利 | CN123456789A |
| `CONCEPT` | 技术概念 | 深度学习 |
| `COMPANY` | 公司/申请人 | 某科技公司 |
| `INVENTOR` | 发明人 | 张三 |
| `CATEGORY` | 分类号 | G06N |
| `KEYWORD` | 关键词 | 神经网络 |
| `LEGAL` | 法律概念 | 创造性 |
| `TECH_FIELD` | 技术领域 | 人工智能 |

### 关系类型 (RelationType)

| 类型 | 说明 | 示例 |
|------|------|------|
| `CONTAINS` | 包含 | 专利包含特征 |
| `BELONGS_TO` | 属于 | 特征属于技术领域 |
| `CITES` | 引用 | 专利A引用专利B |
| `SIMILAR_TO` | 相似 | 概念A相似于概念B |
| `RELATED_TO` | 相关 | 概念A相关于概念B |
| `INVENTED_BY` | 发明者 | 专利由发明人创造 |
| `ASSIGNED_TO` | 受让人 | 专利转让给公司 |
| `SUB_CLASS_OF` | 子类 | 概念A是概念B的子类 |
| `PART_OF` | 部分 | 特征是方案的一部分 |
| `APPLIES_TO` | 应用于 | 法律概念应用于案例 |
| `DERIVED_FROM` | 源于 | 技术方案源于现有技术 |

---

## 🔧 配置

### Neo4j配置

```yaml
# config/base/knowledge_graph.yml
neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "${NEO4J_PASSWORD}"
  database: "neo4j"
```

### ArangoDB配置

```yaml
# config/base/knowledge_graph.yml
arango:
  url: "http://localhost:8529"
  username: "root"
  password: "${ARANGO_PASSWORD}"
  databases:
    patent: "athena_patent_db"
    legal: "athena_legal_db"
    trademark: "athena_trademark_db"
```

---

## 🧪 测试

```bash
# 单元测试
pytest tests/unit/core/knowledge_graph/ -v

# 集成测试（需要Neo4j/ArangoDB）
pytest tests/integration/core/knowledge_graph/ -v -m integration
```

---

## 📚 相关文档

- [知识图谱技术栈选型](../../KNOWLEDGE_GRAPH_TECH_STACK_SELECTION.md)
- [多知识图谱架构设计](../../MULTI_KNOWLEDGE_GRAPH_ARCHITECTURE.md)
- [知识图谱项目总结](../../knowledge_graph_project_summary.md)

---

## 🚧 未来优化方向

虽然当前扁平架构满足需求，但未来可考虑：

1. **统一图查询接口**：抽象Neo4j Cypher和ArangoDB AQL
2. **图缓存层**：缓存频繁访问的子图
3. **异步查询支持**：支持async/await模式
4. **多图谱事务**：跨图谱事务支持

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-21
