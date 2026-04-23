# Qdrant向量数据导入方案

**更新时间**: 2026-01-30
**说明**: Qdrant现有2,000点为测试数据，需要完整导入生产数据

---

## 📊 生产数据统计

### PostgreSQL向量数据

| 数据源 | 总记录数 | 有向量 | 待导入 |
|--------|----------|--------|--------|
| **patent_rules_unified** | 9,956 | 2,416 (24%) | 2,416 |
| **patent_rules_unified_embeddings** | 384 | 384 (100%) | 384 |
| **legal_concepts** | - | - | 已有索引 |

**PostgreSQL小计**: 2,800条向量

### Neo4j向量数据

| 节点类型 | 总节点数 | 有embedding | 待导入 |
|----------|----------|-------------|--------|
| **PatentLawDocument** | 32,820 | 32,818 (99.9%) | 32,818 |
| **JudgmentDocument** | 11,812 | 11,812 (100%) | 11,812 |
| **LawDocument** | 1,365 | 1,365 (100%) | 1,365 |
| **PatentConcept** | 191 | 191 (100%) | 191 |

**Neo4j小计**: 46,186条向量

### 总计

**待导入Qdrant**: 48,986条向量
- PostgreSQL: 2,800条
- Neo4j: 46,186条

---

## 🎯 导入策略

### 方案A: 分层导入（推荐）⭐⭐⭐⭐⭐

#### 集合设计

| Qdrant集合 | 来源 | 预期点数 | 向量维度 | 用途 |
|------------|------|----------|----------|------|
| **patent_law_documents** | Neo4j PatentLawDocument | 32,818 | 1024 | 专利法律文档检索 |
| **patent_judgments** | Neo4j JudgmentDocument | 11,812 | 1024 | 判决文档检索 |
| **patent_laws** | Neo4j LawDocument | 1,365 | 1024 | 核心法律检索 |
| **patent_concepts** | Neo4j PatentConcept | 191 | 1024 | 专利概念检索 |
| **patent_rules** | PostgreSQL patent_rules_unified | 2,416 | ? | 专利规则检索 |
| **patent_rules_chunks** | PostgreSQL embeddings表 | 384 | ? | 专利规则分块 |

#### 导入顺序

```python
# 1. 清理测试数据
# 2. 创建集合
# 3. 从Neo4j导入（优先，数据量大）
# 4. 从PostgreSQL导入
# 5. 验证一致性
```

### 方案B: 统一导入

#### 单一集合设计

| Qdrant集合 | 来源 | 预期点数 | 说明 |
|------------|------|----------|------|
| **patent_legal_unified** | 所有来源 | 48,986 | 统一存储，用payload区分类型 |

**优点**: 管理简单
**缺点**: 查询需要过滤，性能略低

---

## 🚀 实施步骤

### 步骤1: 清理测试数据

```bash
# 删除测试集合
curl -X DELETE http://localhost:6333/collections/patent_rules_db
```

### 步骤2: 创建生产集合

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, CreateCollection

client = QdrantClient(host="localhost", port=6333)

# 创建集合
collections_config = [
    {"name": "patent_law_documents", "size": 1024},
    {"name": "patent_judgments", "size": 1024},
    {"name": "patent_laws", "size": 1024},
    {"name": "patent_concepts", "size": 1024},
]

for config in collections_config:
    client.create_collection(
        collection_name=config["name"],
        vectors_config=VectorParams(size=config["size"], distance=Distance.COSINE)
    )
    print(f"✅ 创建集合: {config['name']}")
```

### 步骤3: 从Neo4j导入向量

```python
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
import numpy as np

# 连接Neo4j
neo4j_driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "athena_neo4j_2024")
)

# 连接Qdrant
qdrant_client = QdrantClient(host="localhost", port=6333)

# 导入PatentLawDocument
with neo4j_driver.session() as session:
    result = session.run("""
        MATCH (doc:PatentLawDocument)
        WHERE doc.embedding IS NOT NULL
        RETURN doc.node_id as id, doc.embedding as vector,
               doc.title as title, doc.content as content
        LIMIT 1000
    """)

    points = []
    for record in result:
        points.append({
            "id": record["id"],
            "vector": record["vector"],
            "payload": {
                "title": record["title"],
                "content": record.get("content", "")[:1000]  # 限制长度
            }
        })

    # 批量插入
    qdrant_client.upsert(
        collection_name="patent_law_documents",
        points=points
    )
    print(f"✅ 导入 {len(points)} 条PatentLawDocument")

# 类似地导入其他节点类型...
```

### 步骤4: 从PostgreSQL导入向量

```python
import psycopg2
from qdrant_client import QdrantClient

# 连接PostgreSQL
conn = psycopg2.connect(host="localhost", port=5432,
                        database="athena", user="postgres")
cursor = conn.cursor()

# 查询向量数据
cursor.execute("""
    SELECT id, article_id, chunk_type, chunk_text, vector
    FROM patent_rules_unified_embeddings
    LIMIT 1000
""")

points = []
for row in cursor.fetchall():
    id, article_id, chunk_type, chunk_text, vector = row
    points.append({
        "id": str(id),
        "vector": vector,
        "payload": {
            "article_id": article_id,
            "chunk_type": chunk_type,
            "text": chunk_text[:500]
        }
    })

# 插入Qdrant
qdrant_client.upsert(
    collection_name="patent_rules_chunks",
    points=points
)
print(f"✅ 导入 {len(points)} 条patent_rules_chunks")

conn.close()
```

### 步骤5: 验证导入

```python
# 验证各集合点数
collections = [
    "patent_law_documents",
    "patent_judgments",
    "patent_laws",
    "patent_concepts"
]

for collection_name in collections:
    collection_info = qdrant_client.get_collection(collection_name)
    print(f"{collection_name}: {collection_info.points_count} 点")
```

---

## 📋 完整导入脚本

创建文件: `/Users/xujian/Athena工作平台/scripts/import_vectors_to_qdrant.py`

```python
#!/usr/bin/env python3
"""
向量数据完整导入到Qdrant
Import All Vectors to Qdrant

从Neo4j和PostgreSQL导入所有向量数据到Qdrant

作者: Athena平台团队
版本: v1.0.0
日期: 2026-01-30
"""

import logging
from datetime import datetime
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, CreateCollection
import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "athena_neo4j_2024"

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

PG_HOST = "localhost"
PG_PORT = 5432
PG_DATABASE = "athena"
PG_USER = "postgres"


def create_qdrant_collections():
    """创建Qdrant集合"""
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # 删除测试集合
    try:
        client.delete_collection("patent_rules_db")
        logger.info("🗑️  删除测试集合: patent_rules_db")
    except:
        pass

    # 创建生产集合
    collections = [
        ("patent_law_documents", 1024),
        ("patent_judgments", 1024),
        ("patent_laws", 1024),
        ("patent_concepts", 1024),
        ("patent_rules", 1024),
    ]

    for name, size in collections:
        try:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=size, distance=Distance.COSINE)
            )
            logger.info(f"✅ 创建集合: {name} ({size}维)")
        except Exception as e:
            logger.warning(f"⚠️  集合 {name} 可能已存在: {e}")


def import_from_neo4j():
    """从Neo4j导入向量"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # 导入配置
    imports = [
        ("patent_law_documents", "PatentLawDocument", 1000),
        ("patent_judgments", "JudgmentDocument", 1000),
        ("patent_laws", "LawDocument", 1000),
        ("patent_concepts", "PatentConcept", 200),
    ]

    for collection_name, node_label, batch_size in imports:
        logger.info(f"📥 开始导入: {node_label} → {collection_name}")

        with driver.session() as session:
            # 统计总数
            count_result = session.run(f"""
                MATCH (n:{node_label})
                WHERE n.embedding IS NOT NULL
                RETURN count(n) as total
            """)
            total = count_result.single()["total"]
            logger.info(f"   总数: {total:,}")

            # 批量导入
            skip = 0
            imported = 0

            while skip < total:
                result = session.run(f"""
                    MATCH (n:{node_label})
                    WHERE n.embedding IS NOT NULL
                    RETURN n.node_id as id, n.embedding as vector, n.title as title
                    ORDER BY n.title
                    SKIP {skip}
                    LIMIT {batch_size}
                """)

                points = []
                for record in result:
                    points.append({
                        "id": record["id"],
                        "vector": record["vector"],
                        "payload": {"title": record.get("title", "")}
                    })

                if points:
                    client.upsert(collection_name=collection_name, points=points)
                    imported += len(points)
                    logger.info(f"   已导入: {imported:,}/{total:,}")

                skip += batch_size

            logger.info(f"✅ {collection_name}: {imported:,} 条")

    driver.close()


def import_from_postgres():
    """从PostgreSQL导入向量"""
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER
    )
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # 导入patent_rules_unified
    logger.info("📥 开始导入: PostgreSQL patent_rules_unified")

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            section_id,
            embedding,
            title
        FROM patent_rules_unified
        WHERE embedding IS NOT NULL
        ORDER BY title
    """)

    points = []
    for row in cursor.fetchall():
        section_id, embedding, title = row
        points.append({
            "id": section_id,
            "vector": embedding,
            "payload": {"title": title or ""}
        })

    if points:
        client.upsert(collection_name="patent_rules", points=points)
        logger.info(f"✅ patent_rules: {len(points):,} 条")

    cursor.close()
    conn.close()


def verify_import():
    """验证导入结果"""
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    collections = [
        "patent_law_documents",
        "patent_judgments",
        "patent_laws",
        "patent_concepts",
        "patent_rules"
    ]

    logger.info("\n" + "="*60)
    logger.info("📊 导入结果验证")
    logger.info("="*60)

    total = 0
    for collection_name in collections:
        try:
            info = client.get_collection(collection_name)
            count = info.points_count
            total += count
            logger.info(f"  {collection_name}: {count:,} 点")
        except Exception as e:
            logger.warning(f"  {collection_name}: 查询失败")

    logger.info(f"\n  📊 总计: {total:,} 点")
    logger.info("="*60)


def main():
    """主函数"""
    logger.info("""
╔═══════════════════════════════════════════════════════════╗
║           向量数据完整导入到Qdrant                              ║
╚═══════════════════════════════════════════════════════════╝
    """)

    try:
        # 1. 创建集合
        create_qdrant_collections()

        # 2. 从Neo4j导入
        import_from_neo4j()

        # 3. 从PostgreSQL导入
        import_from_postgres()

        # 4. 验证
        verify_import()

        logger.info("\n🎉 导入完成！")

    except Exception as e:
        logger.error(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
```

---

## 📝 总结

### 更新后的建议

| 问题 | 答案 | 优先级 |
|------|------|--------|
| Qdrant是否需要完整导入？ | **是**，删除测试数据，导入48,986条生产向量 | ⭐⭐⭐⭐⭐ |
| 是否应该建立向量索引？ | **是**，PostgreSQL仍需HNSW索引 | ⭐⭐⭐⭐ |
| 最佳架构？ | **三库架构**: PostgreSQL(结构化) + Neo4j(图谱) + Qdrant(向量) | ⭐⭐⭐⭐⭐ |

### 导入后的数据分布

| 数据库 | 角色 | 数据量 |
|--------|------|--------|
| **PostgreSQL** | 结构化数据存储 | 32,720条记录 |
| **Neo4j** | 知识图谱 + 向量 | 46,186个节点 |
| **Qdrant** | 向量相似度搜索 | 48,986个向量 |

### 三库一致性目标

- PostgreSQL ↔ Neo4j: 99.70%
- PostgreSQL ↔ Qdrant: 100%
- Neo4j ↔ Qdrant: 100%

---

**文档位置**: `/Users/xujian/Athena工作平台/docs/VECTOR_STORAGE_ANALYSIS_AND_RECOMMENDATIONS.md`
