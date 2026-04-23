# Athena法律世界模型 - 三库联动持久化使用指南

## 📋 概述

Athena法律世界模型采用**三库联动架构**，通过PostgreSQL、Neo4j、Qdrant三个数据库协同工作，为法律AI应用提供完整的数据支撑。

```
┌─────────────────────────────────────────────────────────────────┐
│  🏛️ 法律世界模型 - 三库联动架构                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📊 PostgreSQL (关系数据库)                                       │
│     ├─ 法律文章、专利决定、判决书等结构化数据                      │
│     ├─ 数据量: ~8GB                                              │
│     ├─ 连接: localhost:5432/postgres                            │
│     └─ 持久化: /opt/homebrew/var/postgresql@17                   │
│                                                                   │
│  🔗 Neo4j (图数据库)                                               │
│     ├─ 法律实体关系、知识图谱                                    │
│     ├─ 数据量: 295,753节点                                       │
│     ├─ 连接: bolt://localhost:7687                              │
│     └─ 持久化: /opt/homebrew/var/neo4j/data                      │
│                                                                   │
│  🔍 Qdrant (向量数据库)                                           │
│     ├─ 法律条款、专利规则等向量嵌入                               │
│     ├─ 数据量: 130,353向量                                       │
│     ├─ 连接: http://localhost:6333                              │
│     └─ 持久化: /Users/xujian/Athena工作平台/data/qdrant/storage   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 快速启动

### 方法一：使用统一启动脚本（推荐）

```bash
# 启动所有数据库
./scripts/start_legal_world_model.sh
```

这个脚本会自动：
1. ✅ 检查Docker环境
2. ✅ 启动PostgreSQL（使用本地Homebrew安装）
3. ✅ 启动Neo4j（使用本地Homebrew安装）
4. ✅ 启动Qdrant（使用Docker，挂载持久化存储）
5. ✅ 验证三库连接
6. ✅ 显示数据统计

### 方法二：手动启动

#### 1. PostgreSQL (Homebrew安装)

```bash
# 启动PostgreSQL服务
brew services start postgresql@17

# 或使用系统命令
neo4j start

# 验证连接
psql -h localhost -U postgres -d postgres -c "SELECT version();"
```

#### 2. Neo4j (Homebrew安装)

```bash
# 启动Neo4j服务
neo4j start

# 验证连接
curl http://localhost:7474
```

#### 3. Qdrant (Docker)

```bash
# 启动Qdrant容器（使用持久化存储）
docker run -d --name athena-qdrant-new \
  -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/data/qdrant/storage:/qdrant/storage:z \
  -e QDRANT__SERVICE__HTTP_PORT=6333 \
  -e QDRANT__SERVICE__GRPC_PORT=6334 \
  --restart unless-stopped \
  qdrant/qdrant:latest

# 验证连接
curl http://localhost:6333
```

## 💾 数据备份与恢复

### 备份数据

```bash
# 完整备份（三库）
python3 scripts/backup_restore_legal_world.py backup --name "backup_$(date +%Y%m%d)"

# 备份位置
# backups/legal_world_model/backup_YYYYMMDD_HHMMSS/
#   ├── postgres_backup.sql
#   ├── neo4j/
#   ├── qdrant/
#   └── backup_metadata.json
```

### 恢复数据

```bash
# 列出所有备份
python3 scripts/backup_restore_legal_world.py list

# 恢复指定备份
python3 scripts/backup_restore_legal_world.py restore backups/legal_world_model/backup_YYYYMMDD_HHMMSS
```

### 导出数据快照

```bash
# PostgreSQL导出
pg_dump -h localhost -U postgres postgres > backup_postgres_$(date +%Y%m%d).sql

# Neo4j导出
neo4j-admin dump --database=neo4j --to=/path/to/backup

# Qdrant导出
curl -X POST http://localhost:6333/collections/{collection_name}/snapshots
```

## 📊 数据验证

### 验证PostgreSQL数据

```bash
python3 << 'EOF'
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='athena_dev_password_2024_secure',
    database='postgres'
)
cur = conn.cursor()

# 检查数据库大小
cur.execute("""
    SELECT
        datname,
        pg_size_pretty(pg_database_size(datname)) as size
    FROM pg_database
    WHERE datistemplate = false
""")
for row in cur.fetchall():
    print(f"{row[0]}: {row[1]}")

cur.close()
conn.close()
EOF
```

### 验证Neo4j数据

```bash
python3 << 'EOF'
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'athena_neo4j_2024'))
with driver.session() as session:
    result = session.run('MATCH (n) RETURN count(n) as count')
    print(f"节点总数: {result.single()[\"count\"]}")
driver.close()
EOF
```

### 验证Qdrant数据

```bash
python3 << 'EOF'
import requests
response = requests.get('http://localhost:6333/collections')
data = response.json()
for col in data['result']['collections']:
    name = col['name']
    points = col.get('points_count', 0)
    print(f"{name}: {points} points")
EOF
```

## 🔧 配置法律世界模型服务

法律世界模型服务会自动连接到这三个数据库，配置位于：
- 服务代码：`/Users/xujian/Athena工作平台/services/legal-world-model-service/api.py`
- 环境变量：`/Users/xujian/Athena工作平台/.env`

```bash
# 启动法律世界模型服务
nohup python3 services/legal-world-model-service/api.py > logs/legal_world_model.log 2>&1 &

# 检查服务状态
curl http://localhost:8020/health | python3 -m json.tool
```

## 📁 持久化数据位置

### 当前数据位置

| 数据库 | 数据位置 | 备份命令 |
|--------|----------|----------|
| PostgreSQL | `/opt/homebrew/var/postgresql@17` | `pg_dump` |
| Neo4j | `/opt/homebrew/var/neo4j/data` | `neo4j-admin dump` |
| Qdrant | `/Users/xujian/Athena工作平台/data/qdrant/storage` | 文件复制 |

### 数据迁移到新环境

1. **打包数据**：
```bash
cd /Users/xujian/Athena工作平台
tar -czf legal_world_data_backup.tar.gz \
    /opt/homebrew/var/postgresql@17 \
    /opt/homebrew/var/neo4j/data \
    data/qdrant/storage
```

2. **在新环境解压**：
```bash
tar -xzf legal_world_data_backup.tar.gz -C /
```

3. **启动服务**：
```bash
./scripts/start_legal_world_model.sh
```

## 🎯 使用场景

### 场景1：首次部署

```bash
# 1. 克隆项目
git clone <repository-url>

# 2. 启动三库
./scripts/start_legal_world_model.sh

# 3. 验证数据
curl http://localhost:8020/health
```

### 场景2：日常使用

```bash
# 启动所有服务
./scripts/start_legal_world_model.sh

# 启动法律世界模型API
nohup python3 services/legal-world-model-service/api.py > logs/legal_world_model.log 2>&1 &
```

### 场景3：数据迁移

```bash
# 1. 备份原环境数据
python3 scripts/backup_restore_legal_world.py backup --name "migration_backup"

# 2. 复制备份到新环境
scp -r backups/legal_world_model/migration_backup user@new-server:/path/to/athena/

# 3. 在新环境恢复
cd /path/to/athena
python3 scripts/backup_restore_legal_world.py restore backups/legal_world_model/migration_backup
```

## 🔍 故障排查

### PostgreSQL无法启动

```bash
# 检查PostgreSQL状态
brew services list | grep postgres

# 查看日志
tail -f /opt/homebrew/var/postgresql@17/log/server.log

# 重启PostgreSQL
brew services restart postgresql@17
```

### Neo4j无法启动

```bash
# 检查Neo4j状态
neo4j status

# 查看日志
tail -f /opt/homebrew/var/neo4j/logs/neo4j.log

# 重启Neo4j
neo4j restart
```

### Qdrant无法启动

```bash
# 检查容器状态
docker ps -a | grep qdrant

# 查看日志
docker logs athena-qdrant-new

# 重启容器
docker restart athena-qdrant-new
```

## 📈 性能优化建议

### PostgreSQL优化

```ini
# postgresql.conf
shared_buffers = 2GB
effective_cache_size = 4GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
```

### Neo4j优化

```properties
# neo4j.conf
dbms.memory.heap.initial_size=512m
dbms.memory.heap.max_size=2G
dbms.memory.pagecache.size=1G
dbms.query_cache_size=128m
```

### Qdrant优化

```bash
# 增加搜索线程
-e QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=4

# 使用SSD存储
# 确保数据目录在SSD上
```

## 🎉 总结

通过本指南，您应该能够：

1. ✅ 正确启动三库联动系统
2. ✅ 理解数据持久化机制
3. ✅ 执行数据备份和恢复
4. ✅ 在新环境中快速部署

如有问题，请查看日志文件或运行健康检查命令。

---

**文档版本**: v1.0.0
**最后更新**: 2026-02-28
**维护者**: Athena平台团队
