# 🏛️ Athena法律世界模型 - 三库联动持久化完整方案

## ✅ 当前状态总结

所有数据库已成功启动并使用持久化数据：

```
┌─────────────────────────────────────────────────────────────────┐
│  三库联动系统 - 运行状态 ✅                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📊 PostgreSQL (8GB+)                                            │
│     ├─ 状态: ✅ 运行中 (postgresql@17)                          │
│     ├─ 连接: localhost:5432/postgres                            │
│     ├─ 数据: 8GB+ 持久化数据                                    │
│     └─ 位置: /opt/homebrew/var/postgresql@17                     │
│                                                                   │
│  🔗 Neo4j (295,753节点)                                          │
│     ├─ 状态: ✅ 运行中 (PID: 20114)                              │
│     ├─ 连接: bolt://localhost:7687                              │
│     ├─ 数据: 941MB 持久化数据                                   │
│     └─ 位置: /opt/homebrew/var/neo4j/data                       │
│                                                                   │
│  🔍 Qdrant (130,353向量)                                         │
│     ├─ 状态: ✅ 运行中 (athena-qdrant-new)                      │
│     ├─ 连接: http://localhost:6333                              │
│     ├─ 数据: 711MB 持久化存储                                   │
│     └─ 位置: /Users/xujian/Athena工作平台/data/qdrant/storage   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 持久化方案设计

### 当前持久化架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    生产环境持久化架构                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  本地持久化（Homebrew）                                         │
│  ├─ PostgreSQL: /opt/homebrew/var/postgresql@17                 │
│  └─ Neo4j: /opt/homebrew/var/neo4j/data                         │
│                                                                   │
│  容器持久化（Docker Volume）                                     │
│  └─ Qdrant: 绑定到项目目录                                      │
│      └─ /Users/xujian/Athena工作平台/data/qdrant/storage         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 为什么这样设计？

1. **PostgreSQL & Neo4j使用Homebrew安装**
   - ✅ 直接与系统集成
   - ✅ 数据更稳定可靠
   - ✅ 不需要容器网络
   - ✅ 便于本地开发调试

2. **Qdrant使用Docker容器**
   - ✅ 版本管理简单
   - ✅ 部署灵活
   - ✅ 资源隔离
   - ✅ 易于备份迁移

## 📋 完整启动流程

### 方式一：一键启动（推荐）

```bash
# 进入项目目录
cd /Users/xujian/Athena工作平台

# 运行启动脚本
./scripts/start_legal_world_model.sh
```

### 方式二：分步启动

```bash
# 1. 启动PostgreSQL
brew services start postgresql@17

# 2. 启动Neo4j
neo4j start

# 3. 启动Qdrant（使用持久化存储）
docker run -d --name athena-qdrant-new \
  -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/data/qdrant/storage:/qdrant/storage:z \
  -e QDRANT__SERVICE__HTTP_PORT=6333 \
  -e QDRANT__SERVICE__GRPC_PORT=6334 \
  --restart unless-stopped \
  qdrant/qdrant:latest
```

## 💾 数据持久化机制

### 1. PostgreSQL持久化

```bash
# 数据位置
/opt/homebrew/var/postgresql@17/

# 自动备份
# Homebrew会自动管理数据，不需要手动干预

# 手动备份
pg_dump -h localhost -U postgres postgres > backup.sql

# 恢复
psql -h localhost -U postgres postgres < backup.sql
```

### 2. Neo4j持久化

```bash
# 数据位置
/opt/homebrew/var/neo4j/data/

# 自动备份
# Neo4j会自动持久化所有数据修改

# 手动备份
neo4j-admin dump --database=neo4j --to=/path/to/backup

# 恢复
neo4j-admin load --from=/path/to/backup --database=neo4j
```

### 3. Qdrant持久化

```bash
# 数据位置
/Users/xujian/Athena工作平台/data/qdrant/storage/

# 自动备份
# 容器重启时自动加载持久化数据

# 手动备份
cp -r data/qdrant/storage data/qdrant/storage_backup

# 恢复
# 将备份文件复制回原位置即可
```

## 🔄 完整生命周期管理

### 日常启动

```bash
# 一键启动所有服务
./scripts/start_legal_world_model.sh
```

### 定期备份

```bash
# 完整备份
python3 scripts/backup_restore_legal_world.py backup --name "daily_backup_$(date +%Y%m%d)"

# 查看备份列表
python3 scripts/backup_restore_legal_world.py list
```

### 环境迁移

```bash
# 1. 在原环境备份
python3 scripts/backup_restore_legal_world.py backup --name "migration_$(date +%Y%m%d)"

# 2. 打包数据
cd /Users/xujian/Athena工作平台
tar -czf athena_legal_world_backup.tar.gz \
    /opt/homebrew/var/postgresql@17 \
    /opt/homebrew/var/neo4j/data \
    data/qdrant/storage \
    .env \
    scripts/

# 3. 在新环境恢复
tar -xzf athena_legal_world_backup.tar.gz -C /path/to/new/environment
cd /path/to/new/environment
./scripts/start_legal_world_model.sh
```

### 数据更新

```bash
# 1. 添加新数据到PostgreSQL
psql -h localhost -U postgres -d postgres -f new_data.sql

# 2. 添加新数据到Neo4j
# 通过API或Cypher查询添加

# 3. 添加新数据到Qdrant
# 通过API添加向量

# 4. 验证数据完整性
python3 << 'EOF'
# 验证PostgreSQL
import psycopg2
conn = psycopg2.connect(host='localhost', user='postgres', password='athena_dev_password_2024_secure', database='postgres')
print("PostgreSQL: 连接成功")

# 验证Neo4j
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'athena_neo4j_2024'))
print("Neo4j: 连接成功")

# 验证Qdrant
import requests
r = requests.get('http://localhost:6333')
print(f"Qdrant: {r.status_code == 200}")
EOF
```

## 🎛️ 配置文件

### 环境变量 (.env)

```bash
# PostgreSQL配置
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_NAME=postgres
DB_PASSWORD=athena_dev_password_2024_secure

# Neo4j配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=athena_neo4j_2024

# Qdrant配置
QDRANT_URL=http://localhost:6333
```

### 法律世界模型服务配置

服务会自动读取环境变量并连接到三库：

```python
# PostgreSQL连接
import psycopg2
conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 5432)),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "postgres")
)

# Neo4j连接
from neo4j import GraphDatabase
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD", ""))
)

# Qdrant连接
import requests
response = requests.get(os.getenv("QDRANT_URL", "http://localhost:6333"))
```

## 📊 性能监控

### 查看数据使用情况

```bash
# PostgreSQL数据量
psql -h localhost -U postgres -d postgres -c "
SELECT
    datname,
    pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database
WHERE datistemplate = false;"

# Neo4j节点数量
curl -X POST http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -d '{"statements":[{"statement":"MATCH (n) RETURN count(n)"}]}'

# Qdrant向量数量
curl -s http://localhost:6333/collections | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = sum(c.get('points_count', 0) for c in data['result']['collections'])
print(f'总向量数: {total:,}')
"
```

## 🚀 总结

通过这套完整的三库联动持久化方案，您可以：

1. ✅ **一键启动**所有数据库
2. ✅ **自动加载**持久化数据
3. ✅ **定期备份**防止数据丢失
4. ✅ **快速迁移**到新环境
5. ✅ **监控数据**使用情况

### 关键文件

| 文件 | 说明 |
|------|------|
| `scripts/start_legal_world_model.sh` | 一键启动脚本 |
| `scripts/backup_restore_legal_world.py` | 备份恢复工具 |
| `docs/LEGAL_WORLD_MODEL_PERSISTENCE_GUIDE.md` | 详细使用指南 |

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| PostgreSQL | localhost:5432 | 包含8GB+法律数据 |
| Neo4j Browser | http://localhost:7474 | 图数据库管理界面 |
| Qdrant Dashboard | http://localhost:6333/dashboard | 向量数据库管理界面 |
| 法律世界模型API | http://localhost:8020 | 法律AI服务API |

---

**版本**: v1.0.0
**更新时间**: 2026-02-28
**维护者**: Athena平台团队
