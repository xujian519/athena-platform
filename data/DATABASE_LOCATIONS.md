# Athena法律世界模型 - 数据库位置标识

> 本文件标识Athena平台所有数据库的持久化存储位置
> 创建时间: 2026-02-06
> 最后更新: 2026-02-06
> 用途: 方便智能体查找和访问数据库

---

## 📊 数据库概览

| 数据库 | 类型 | 端口 | 数据量 | 用途 |
|--------|------|------|--------|------|
| **PostgreSQL 17.7** | 关系+向量数据库 | 5432 | 8 GB+ | 🎯 法律世界模型核心数据库（含向量存储） |
| **Qdrant** | 向量数据库 | 6333/6334 | 空 | 备用向量存储（未使用） |
| **Neo4j** | 图数据库 | 7474/7687 | 517 MB | 知识图谱存储 |
| **Redis** | 缓存数据库 | 6379 | 88 B | 会话缓存 |

---

## 1️⃣ PostgreSQL 17.7 (本地安装) - 核心数据库

### 连接信息
```yaml
Host: localhost
Port: 5432
Version: PostgreSQL 17.7 (Homebrew)
扩展: pgvector (向量存储)
Users: postgres / xujian
```

### 数据持久化位置
```bash
# 主数据目录
/usr/local/var/postgres/

# 数据文件位置
/usr/local/var/postgres/base/
```

### 核心数据库结构

#### postgres 数据库 (8,237 MB) - 法律世界模型核心

| 表名 | 大小 | 行数 | 说明 |
|------|------|------|------|
| **向量嵌入表** | | | |
| legal_articles_v2_embeddings | 4,041 MB | 295,810 | 🎯 法律文章向量 (1024维) |
| patent_invalid_embeddings | 1,777 MB | 119,660 | 专利无效决定向量 (1024维) |
| judgment_embeddings | 273 MB | 20,478 | 判决向量 (1024维) |
| patent_judgment_vectors | 231 MB | 17,388 | 专利判决向量 |
| patent_rules_unified_embeddings | 40 KB | 0 | 规则向量（空） |
| **原始文档表** | | | |
| patent_invalid_decisions | 898 MB | 31,562 | 专利无效决定 |
| legal_articles_v2 | 323 MB | 295,733 | 法律文章 |
| patent_invalid_entities | 320 MB | - | 无效决定实体 |
| **结构化数据表** | | | |
| judgment_entities | 147 MB | 891,659 | 🎯 判决实体（最大表） |
| patent_decisions_v2 | 93 MB | - | 决定文档v2 |
| patent_decisions_v1 | 65 MB | - | 决定文档v1 |
| patent_judgment_cases | 28 MB | - | 判决案例 |
| patent_judgments | 11 MB | 5,906 | 专利判决 |
| judgment_relations | 11 MB | - | 实体关系 |
| **规则库** | | | |
| patent_rules_unified | 4 MB | 1,371 | 统一专利规则 |
| **元数据** | | | |
| judgment_law_articles | 4.6 MB | - | 引用法条 |
| judgment_courts | 2.4 MB | - | 法院信息 |
| judgment_patent_numbers | 904 KB | - | 专利号关联 |

#### 其他数据库

| 数据库名 | 大小 | 说明 |
|----------|------|------|
| athena | 155 MB | Athena智能体数据库 |
| patent_rules | 35 MB | 专利规则库 |
| patent_guidelines | 39 MB | 专利指南库 |
| yunpat | 21 MB | YunPat数据库 |
| patent_db | 228 GB | 专利检索业务数据库（独立） |

### 向量存储详情

PostgreSQL使用 **pgvector** 扩展存储向量数据：

```sql
-- 向量维度: 1024维
-- 索引类型: IVFFlat (余弦相似度)
-- 总向量数: ~45万条

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

-- 向量索引
CREATE INDEX idx_legal_articles_v2_embeddings_vector
ON legal_articles_v2_embeddings
USING ivfflat (vector vector_cosine_ops)
WITH (lists = '100');
```

### 快速访问命令

```bash
# 连接postgres核心数据库
psql -U postgres -d postgres

# 查看所有数据库
psql -U postgres -l

# 向量相似度搜索示例
psql -U postgres -d postgres -c "
SELECT article_id, chunk_text,
       1 - (vector <=> '[0.1,0.2,...]'::vector) as similarity
FROM legal_articles_v2_embeddings
ORDER BY vector <=> '[0.1,0.2,...]'::vector
LIMIT 10;
"
```

---

## 2️⃣ Qdrant 向量数据库 (Docker) - 未使用

### 连接信息
```yaml
容器名: athena-qdrant
HTTP API: http://localhost:6333
gRPC API: localhost:6334
版本: v1.7.4
状态: 集合存在但数据为空
```

### 数据持久化位置
```bash
# Docker卷名称
athena_qdrant_data

# 宿主机实际路径
/var/lib/docker/volumes/athena_qdrant_data/_data/

# 容器内路径
/qdrant/storage/
```

### 当前状态

| 集合名称 | 向量数 | 状态 |
|----------|--------|------|
| law_documents | 0 | 🔴 空 |
| patent_law_documents | 0 | 🔴 空 |
| patent_judgments | 0 | 🔴 空 |
| claims | 0 | 🔴 空 |
| patents | 0 | 🔴 空 |
| workflow_patterns | 0 | 🔴 空 |

**说明**: Qdrant容器运行但数据未同步，向量数据存储在PostgreSQL的pgvector表中。

---

## 3️⃣ Neo4j 图数据库 (Docker)

### 连接信息
```yaml
容器名: athena-neo4j
HTTP: http://localhost:7474
Bolt: bolt://localhost:7687
用户: neo4j
密码: athena_neo4j_2024
版本: 5.15-community
```

### 数据持久化位置
```bash
# Docker卷名称
athena-neo4j-data

# 宿主机实际路径
/var/lib/docker/volumes/athena-neo4j-data/_data/

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

### 图数据统计

| 类型 | 数量 | 说明 |
|------|------|------|
| 节点总数 | 20 | ScenarioRule类型 |
| 关系总数 | 0 | 待扩展 |

### 快速访问命令

```bash
# 启动Cypher Shell
docker exec -it athena-neo4j cypher-shell -u neo4j -p athena_neo4j_2024

# 查询节点统计
MATCH (n) RETURN labels(n) as label, count(*) as count ORDER BY count DESC;

# 查询关系统计
MATCH ()-[r]->() RETURN type(r) as type, count(*) as count ORDER BY count DESC;

# Web界面访问
open http://localhost:7474
```

---

## 4️⃣ Redis 缓存数据库 (Docker)

### 连接信息
```yaml
容器名: athena-redis
端口: 6379
密码: redis123
版本: 7-alpine
```

### 数据持久化位置
```bash
# Docker卷名称
athena-redis-data

# 宿主机实际路径
/var/lib/docker/volumes/athena-redis-data/_data/

# 容器内路径
/data/
```

### 快速访问命令

```bash
# 连接Redis CLI
docker exec -it athena-redis redis-cli -a redis123

# 查看所有键
KEYS *

# 查看数据库信息
INFO
```

---

## 🔍 数据卷汇总

| 数据卷名称 | 容器路径 | 宿主机路径 | 大小 | 状态 |
|-----------|----------|-----------|------|------|
| athena_qdrant_data | /qdrant/storage | /var/lib/docker/volumes/athena_qdrant_data/_data | ~1 MB | 🔴 空 |
| athena-neo4j-data | /data | /var/lib/docker/volumes/athena-neo4j-data/_data | 517 MB | ✅ |
| athena-redis-data | /data | /var/lib/docker/volumes/athena-redis-data/_data | 88 B | ✅ |

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
    database="postgres",
    user="postgres",
    password="your_password"
)
register_vector(conn)

# 向量相似度搜索
cur = conn.cursor()
cur.execute("""
    SELECT article_id, chunk_text,
           1 - (vector <=> %s::vector) as similarity
    FROM legal_articles_v2_embeddings
    ORDER BY vector <=> %s::vector
    LIMIT 10
""", (query_vector, query_vector))

# Neo4j连接
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "athena_neo4j_2024")
)
```

---

## 📊 数据统计汇总

### 按存储位置分类

| 存储位置 | 数据类型 | 数据量 |
|----------|----------|--------|
| **PostgreSQL (pgvector)** | 向量嵌入 | ~45万条 (6GB+) |
| **PostgreSQL (结构化)** | 原始文档 | ~120万条 (2GB) |
| **PostgreSQL (结构化)** | 实体数据 | ~90万条 (150MB) |
| **Neo4j** | 知识图谱 | 20节点 |
| **Qdrant** | 向量嵌入 | 0（未使用） |

### 按法律世界模型三层分类

| 层级 | 数据库表 | 记录数 | 向量数 |
|------|----------|--------|--------|
| **第一层：基础法律层** | legal_articles_v2 | 295,733 | 295,810 |
| **第二层：专利专业层** | patent_invalid_decisions | 31,562 | 119,660 |
| | patent_rules_unified | 1,371 | 0 |
| **第三层：司法案例层** | patent_judgments | 5,906 | 17,388 |
| | judgment_entities | 891,659 | 20,478 |

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
pg_dump -U postgres -d postgres > backups/postgres_full_backup_$(date +%Y%m%d).sql

# 只备份向量嵌入表
pg_dump -U postgres -d postgres -t legal_articles_v2_embeddings \
  -t patent_invalid_embeddings -t judgment_embeddings \
  > backups/vector_embeddings_$(date +%Y%m%d).sql

# Neo4j备份
docker run --rm -v athena-neo4j-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/neo4j_$(date +%Y%m%d).tar.gz /data
```

---

## 📖 相关文档

- [Athena平台架构文档](../docs/architecture/README.md)
- [法律世界模型运维手册](../docs/LEGAL_WORLD_MODEL_OPS_MANUAL.md)
- [Docker配置说明](../docker-compose.yml)
- [pgvector使用指南](https://github.com/pgvector/pgvector)

---

## ⚠️ 重要提示

1. **向量数据存储在PostgreSQL**: 使用pgvector扩展，不是Qdrant
2. **Qdrant未使用**: 容器运行但数据为空，可能是计划中的备用存储
3. **主要向量表**: legal_articles_v2_embeddings (29万+)、patent_invalid_embeddings (11万+)
4. **向量维度**: 1024维，使用IVFFlat索引（余弦相似度）

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-02-06
