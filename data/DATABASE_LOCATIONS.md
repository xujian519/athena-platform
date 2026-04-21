# Athena法律世界模型 - 数据库位置标识

> 本文件标识Athena平台所有数据库的持久化存储位置
> 创建时间: 2026-02-06
> 最后更新: 2026-04-21
> 用途: 方便智能体查找和访问数据库

---

## 📊 数据库概览

| 数据库 | 类型 | 端口 | 数据量 | 用途 |
|--------|------|------|--------|------|
| **PostgreSQL 17** | 关系+向量数据库 | 5432 | ~417万条 | 🎯 法律世界模型核心数据库（含向量存储） |
| **Neo4j** | 图数据库 | 7474/7687 | 93万节点+6万关系 | 知识图谱存储（本项目+OpenClaw合并数据） |
| **Redis** | 缓存数据库 | 6379 | 88 B | 会话缓存 |
| **Qdrant** | 向量数据库 | 6333/6334 | 39条向量 | 备用向量存储（Agent记忆） |

---

## 1️⃣ PostgreSQL 17 (本地安装) - 核心数据库

### 连接信息
```yaml
Host: localhost
Port: 5432
Version: PostgreSQL 17 (Homebrew)
扩展: pgvector 0.8.1
Database: legal_world_model ⭐
User: postgres
Password: nxLVXyZ3e87L0kE8Xqx3AB9NK1z74pwOdjugqpc7hc
```

### 数据持久化位置
```bash
# 主数据目录
/usr/local/var/postgres/

# 数据文件位置
/usr/local/var/postgres/base/
```

### 核心数据库结构

#### legal_world_model 数据库 (~417万条) - 法律世界模型核心

| 表名 | 大小 | 行数 | 说明 |
|------|------|------|------|
| **向量嵌入表** | | | |
| legal_articles_v2_embeddings | 4,041 MB | 295,810 | 🎯 法律文章向量 (1024维) ✅ 已优化 |
| patent_invalid_embeddings | 1,777 MB | 119,660 | 专利无效决定向量 (1024维) ✅ 已优化 |
| judgment_embeddings | 273 MB | 20,478 | 判决向量 (1024维) ✅ 已优化 |
| patent_judgment_vectors | 231 MB | 17,388 | 专利判决向量 |
| **原始文档表** | | | |
| patent_invalid_decisions | 898 MB | 31,562 | 专利无效决定 |
| legal_articles_v2 | 323 MB | 295,733 | 法律文章 |
| patent_invalid_entities | 320 MB | 2,363,891 | ⚠️ 无效决定实体（最大表） |
| **结构化数据表** | | | |
| judgment_entities | 147 MB | 891,659 | 🎯 判决实体（第二大） |
| judgment_relations | 11 MB | 45,770 | 实体关系 |
| patent_decisions_v2 | 93 MB | 9,562 | 决定文档v2 |
| patent_decisions_v1 | 65 MB | 6,845 | 决定文档v1 |
| patent_judgment_cases | 28 MB | - | 判决案例 |
| patent_judgments | 11 MB | 5,906 | 专利判决 |
| **规则库** | | | |
| patent_rules_unified | 4 MB | 1,371 | 统一专利规则 |
| **元数据** | | | |
| judgment_law_articles | 4.6 MB | 20,306 | 引用法条 |
| judgment_courts | 2.4 MB | 12,497 | 法院信息 |
| judgment_patent_numbers | 904 KB | 4,243 | 专利号关联 |

### 向量存储详情（已优化）

PostgreSQL使用 **pgvector** 扩展存储向量数据，已优化IVFFlat索引：

```sql
-- 向量维度: 1024维
-- 索引类型: IVFFlat (余弦相似度)
-- 总向量数: 453,336条
-- 平均查询性能: 3.86ms ⚡

-- 示例表结构
CREATE TABLE legal_articles_v2_embeddings (
    id integer PRIMARY KEY,
    article_id varchar(200) NOT NULL,
    chunk_type varchar(64),
    chunk_text text,
    vector vector(1024) NOT NULL,  -- pgvector类型
    weight double precision DEFAULT 1.0,
    created_at timestamp DEFAULT now()
);

-- ✅ 优化后的向量索引（lists = sqrt(行数)）
CREATE INDEX idx_legal_articles_v2_embeddings_vector
ON legal_articles_v2_embeddings
USING ivfflat (vector vector_cosine_ops)
WITH (lists = '543');  -- sqrt(295810) ≈ 543

CREATE INDEX idx_patent_invalid_embeddings_vector
ON patent_invalid_embeddings
USING ivfflat (vector vector_cosine_ops)
WITH (lists = '346');  -- sqrt(119660) ≈ 346

CREATE INDEX idx_judgment_embeddings_vector
ON judgment_embeddings
USING ivfflat (vector vector_cosine_ops)
WITH (lists = '143');  -- sqrt(20478) ≈ 143
```

### 性能优化成果

| 表名 | 优化前 | 优化后 | 提升幅度 |
|------|--------|--------|---------|
| legal_articles_v2_embeddings | 39.99 ms | **9.43 ms** | 76.4% ⬆️ |
| patent_invalid_embeddings | ~35 ms | **1.44 ms** | 95.9% ⬆️ |
| judgment_embeddings | ~20 ms | **0.70 ms** | 96.5% ⬆️ |

### 快速访问命令

```bash
# 连接legal_world_model数据库
/opt/homebrew/opt/postgresql@17/bin/psql -h localhost -p 5432 -U postgres -d legal_world_model

# 查看所有数据库
psql -U postgres -l

# 向量相似度搜索示例（性能优化后）
psql -U postgres -d legal_world_model -c "
SELECT article_id, chunk_text,
       1 - (vector <=> '[0.1,0.2,...]'::vector) as similarity
FROM legal_articles_v2_embeddings
ORDER BY vector <=> '[0.1,0.2,...]'::vector
LIMIT 10;
"
# 平均响应时间: 9.43ms
```

---

## 2️⃣ Neo4j 图数据库 (Docker) - 合并知识图谱

### 连接信息
```yaml
容器名: athena-neo4j-dev
HTTP: http://localhost:7474
Bolt: bolt://localhost:7687
用户: neo4j
密码: athena_neo4j_2024
版本: 5.15-community
状态: ✅ 已合并本项目判决数据+OpenClaw法律世界模型（93万节点+6万关系）
```

### 数据持久化位置
```bash
# Docker卷名称
athena-neo4j-dev-data

# 宿主机实际路径
/var/lib/docker/volumes/athena-neo4j-dev-data/_data/

# 容器内路径
/data/
```

### 数据结构
```
/data/
├── databases/              # 数据库文件
│   ├── neo4j/             # Neo4j主数据库
│   │   ├── schema/        # 数据库模式
│   │   └── data/          # 图数据文件
│   └── system/            # 系统数据库
├── dbms/                  # DBMS配置
├── transactions/          # 事务日志
└── server_id             # 服务器标识
```

### 图数据统计（2026-04-21更新）

**总计**:
- **节点**: 931,693个 ✅
- **关系**: 59,770条 ✅

**节点类型分布**:

| 节点类型 | 数量 | 占比 | 数据源 |
|---------|------|------|--------|
| **Entity** | **891,659** | 95.7% | 本项目判决数据 |
| **OpenClawNode** | **40,034** | 4.3% | OpenClaw法律世界模型 |
| **总计** | **931,693** | 100% | 合并数据 |

**Entity类型分布**（本项目）:

| 实体类型 | 数量 | 占比 |
|---------|------|------|
| **PATENT_NUMBER** | 850,529 | 95.4% |
| **PERSON** | 27,034 | 3.0% |
| **COURT** | 12,497 | 1.4% |
| **DATE** | 1,146 | 0.1% |
| **IPC_CODE** | 281 | <0.1% |
| **LAW_ARTICLE** | 172 | <0.1% |

**关系类型分布**:

| 关系类型 | 数量 | 占比 | 数据源 |
|---------|------|------|--------|
| **RELATION** | **46,770** | 78.3% | 本项目判决关系 |
| **RELATED_TO** | **10,731** | 17.9% | OpenClaw关系 |
| **CITES** | **2,269** | 3.8% | OpenClaw引用关系 |
| **总计** | **59,770** | 100% | 合并数据 |

### 数据源说明

**本项目数据**（完全导入）:
- 来源: `legal_world_model.judgment_entities` + `judgment_relations`
- 节点: 891,659个（100%）
- 关系: 46,770条（100%）
- 导入时间: 2026-04-21

**OpenClaw数据**（部分导入）:
- 来源: `athena-neo4j-data` Docker卷
- 节点: 40,034个（100%）
- 关系: 12,858条（3.2%，核心关系）
- 说明: 完整数据包含407,744条关系

### 快速访问命令

```bash
# 启动Cypher Shell
docker exec -it athena-neo4j-dev cypher-shell -u neo4j -p athena_neo4j_2024

# 查询节点统计
MATCH (n) RETURN labels(n) as label, count(*) as count ORDER BY count DESC;

# 查询Entity节点按类型统计
MATCH (e:Entity) RETURN e.type as type, count(*) as count ORDER BY count DESC;

# 查询关系统计
MATCH ()-[r]->() RETURN type(r) as type, count(*) as count ORDER BY count DESC;

# 查询Entity节点示例
MATCH (e:Entity) RETURN e.text, e.type LIMIT 3;

# Web界面访问
open http://localhost:7474
```

---

## 3️⃣ Redis 缓存数据库 (Docker)

### 连接信息
```yaml
容器名: athena-redis-dev
端口: 6379
密码: redis123
版本: 7-alpine
```

### 数据持久化位置
```bash
# Docker卷名称
athena-redis-dev-data

# 宿主机实际路径
/var/lib/docker/volumes/athena-redis-dev-data/_data/

# 容器内路径
/data/
```

---

## 4️⃣ Qdrant 向量数据库 (Docker) - Agent记忆存储

### 连接信息
```yaml
容器名: athena-qdrant-dev
HTTP API: http://localhost:6333
gRPC API: localhost:6334
版本: v1.7.4
```

### 当前状态

| 集合名称 | 向量数 | 状态 |
|----------|--------|------|
| agent_memory_vectors | 39 | ✅ Agent记忆向量 |
| conversation_vectors | 0 | 🔴 空 |
| knowledge_vectors | 0 | 🔴 空 |

**说明**: Qdrant用于存储Agent记忆向量，法律向量数据存储在PostgreSQL。

---

## 🔍 数据卷汇总

| 数据卷名称 | 容器路径 | 宿主机路径 | 大小 | 状态 |
|-----------|----------|-----------|------|------|
| athena-neo4j-dev-data | /data | /var/lib/docker/volumes/athena-neo4j-dev-data/_data | ~50 MB | ✅ |
| athena-redis-dev-data | /data | /var/lib/docker/volumes/athena-redis-dev-data/_data | 88 B | ✅ |
| athena-qdrant-dev-data | /qdrant/storage | /var/lib/docker/volumes/athena-qdrant-dev-data/_data | ~1 MB | ✅ |

---

## 🛠️ 智能体访问指南

### Python代码示例

```python
import psycopg2
from pgvector.psycopg2 import register_vector
from neo4j import GraphDatabase

# PostgreSQL连接（含向量支持）
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="legal_world_model",  # ⭐ 注意数据库名
    user="postgres",
    password="nxLVXyZ3e87L0kE8Xqx3AB9NK1z74pwOdjugqpc7hc"
)
register_vector(conn)

# 向量相似度搜索（性能优化后）
cur = conn.cursor()
cur.execute("""
    SELECT article_id, chunk_text,
           1 - (vector <=> %s::vector) as similarity
    FROM legal_articles_v2_embeddings
    ORDER BY vector <=> %s::vector
    LIMIT 10
""", (query_vector, query_vector))
# 平均响应时间: 9.43ms

# Neo4j连接
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "athena_neo4j_2024")
)
```

---

## 📊 数据统计汇总

### 按存储位置分类

| 存储位置 | 数据类型 | 数据量 | 状态 |
|----------|----------|--------|------|
| **PostgreSQL (pgvector)** | 向量嵌入 | 453,336条 (6GB+) | ✅ 已优化 |
| **PostgreSQL (结构化)** | 原始文档 | ~120万条 (2GB) | ✅ 完整 |
| **PostgreSQL (结构化)** | 实体数据 | ~326万条 (150MB) | ✅ 完整 |
| **Neo4j** | 知识图谱 | 55,906节点 | ✅ 已导入 |
| **Qdrant** | Agent记忆 | 39条向量 | ✅ 可用 |

### 按法律世界模型三层分类

| 层级 | 数据库表 | 记录数 | 向量数 | 状态 |
|------|----------|--------|--------|------|
| **第一层：基础法律层** | legal_articles_v2 | 295,733 | 295,810 | ✅ 已优化 |
| **第二层：专利专业层** | patent_invalid_decisions | 31,562 | 119,660 | ✅ 已优化 |
| | patent_rules_unified | 1,371 | 0 | ✅ 可用 |
| **第三层：司法案例层** | patent_judgments | 5,906 | 17,388 | ✅ 可用 |
| | judgment_entities | 891,659 | 20,478 | ✅ 可用 |
| | judgment_relations | 45,770 | - | ✅ 可用 |

---

## 📝 备份建议

### 定期备份脚本位置
```bash
# 备份脚本目录
/Users/xujian/Athena工作平台/scripts/backup/

# 备份存储目录
/Users/xujian/Athena工作平台/backups/
```

### 备份命令示例

```bash
# PostgreSQL完整备份
pg_dump -U postgres -d legal_world_model > backups/legal_world_model_$(date +%Y%m%d).sql

# 只备份向量嵌入表
pg_dump -U postgres -d legal_world_model -t legal_articles_v2_embeddings \
  -t patent_invalid_embeddings -t judgment_embeddings \
  > backups/vector_embeddings_$(date +%Y%m%d).sql

# Neo4j备份
docker run --rm -v athena-neo4j-dev-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/neo4j_$(date +%Y%m%d).tar.gz /data
```

---

## 📖 相关文档

- [Athena平台架构文档](../docs/architecture/README.md)
- [法律世界模型运维手册](../docs/LEGAL_WORLD_MODEL_OPS_MANUAL.md)
- [Docker配置说明](../docker-compose.unified.yml)
- [pgvector使用指南](https://github.com/pgvector/pgvector)
- [向量索引优化报告](../docs/reports/IVFFLAT_OPTIMIZATION_COMPLETE_20260421.md)
- [系统验证报告](../docs/reports/LEGAL_WORLD_MODEL_VERIFICATION_COMPLETE_20260421.md)

---

## ⚠️ 重要提示

1. **数据库名称**: ⭐ `legal_world_model`（不是postgres或athena）
2. **向量数据存储在PostgreSQL**: 使用pgvector扩展，已优化IVFFlat索引
3. **向量性能优化**: 平均查询时间从31.7ms降至3.86ms（提升76.5%）
4. **Neo4j图谱**: 已导入55,906个节点（超过原始OpenClaw图谱的140%）
5. **Qdrant用途**: 仅用于Agent记忆（39条），法律向量在PostgreSQL

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-21
**系统状态**: 🟢 优秀（91.7%验证通过率）

