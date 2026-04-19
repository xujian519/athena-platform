# Athena工作平台 - Docker Compose统一配置

## 概述

本目录包含Athena工作平台的统一Docker Compose配置，将原有的81个分散配置文件整合为统一文件体系。

**版本**: v3.0.0
**技术决策**: TD-001 - 统一图数据库选择为Neo4j
**更新时间**: 2026-01-26

## 配置文件结构

```
config/docker/
├── docker-compose.unified-databases.yml    # ⭐ 统一数据库服务（推荐使用）
│   ├── Neo4j 5-community (图数据库 - TD-001)
│   ├── Qdrant (向量数据库)
│   └── Redis (缓存)
│
├── docker-compose.local-db.yml            # 本地开发数据库配置
│   ├── Neo4j (使用7475/7688端口避免冲突)
│   └── Qdrant本地版
│
├── docker-compose.production-tools.yml    # 生产环境工具
│   ├── 数据库服务 (Neo4j + PostgreSQL + Qdrant)
│   └── 监控服务 (Prometheus + Grafana)
│
├── docker-compose.infrastructure.yml     # 基础设施层（已废弃）
├── docker-compose.core-services.yml      # 核心服务层（已废弃）
├── docker-compose.mcp-servers.yml        # MCP服务器层（已废弃）
├── docker-compose.applications.yml       # 应用层（已废弃）
├── docker-compose.monitoring.yml         # 监控层（已废弃）
│
├── .env.example                          # 环境变量模板
├── archive/                              # 旧配置文件归档目录
│   └── nebulagraph_configs/              # NebulaGraph旧配置（TD-001已废弃）
└── README.md                             # 本文件
```

> ⚠️ **TD-001迁移说明**: 已从NebulaGraph迁移到Neo4j。旧版NebulaGraph配置已归档到`archive/nebulagraph_configs/`。

## 服务层级架构 (TD-001: Neo4j版本)

```
┌─────────────────────────────────────────────────────────────┐
│                     应用层 (Applications)                    │
│   XiaoNuo网关 (8100) | 意图识别 (8002) | 可视化工具 (8091)    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                    MCP服务器层 (MCP Servers)                 │
│   8个专业MCP服务器 (8200-8208)                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                   核心服务层 (Core Services)                 │
│   API网关 (8080) | YunPat代理 (8020) | 专利分析 (8050)       │
│   浏览器自动化 (8030) | 自主控制 (8040) | 专利搜索 (8060)      │
│   知识图谱 (8070) | JoyAgent优化 (8035)                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                 基础设施层 (Infrastructure)                  │
│   Redis (6379) | Qdrant (6333/6334) | Neo4j (7474/7687) ⭐   │
│   PostgreSQL - 使用本地17.7版本 (host.docker.internal:5432)  │
└─────────────────────────────────────────────────────────────┘
```

> ⭐ **TD-001重大变更**: NebulaGraph已替换为Neo4j 5-community

## 快速开始 (TD-001: Neo4j版本)

### 1. 配置环境变量

```bash
cd config/docker
cp .env.example .env
# 编辑 .env 文件，填写必要的配置
```

### 2. 启动服务

#### ⭐ 推荐：启动统一数据库服务（包含Neo4j）
```bash
# 启动Neo4j + Qdrant + Redis（推荐用于开发和测试）
docker-compose -f docker-compose.unified-databases.yml up -d
```

#### 本地开发环境
```bash
# 启动本地开发数据库（使用7475/7688端口避免冲突）
docker-compose -f docker-compose.local-db.yml up -d
```

#### 生产环境工具
```bash
# 启动生产环境工具（包含监控）
docker-compose -f docker-compose.production-tools.yml up -d
```

#### 按层启动（旧方式，已废弃）
```bash
# ⚠️ 以下配置文件已废弃，建议使用上述统一配置
# 第1步：启动基础设施层
docker-compose -f docker-compose.infrastructure.yml up -d

# 第2步：等待基础设施健康后，启动核心服务层
docker-compose -f docker-compose.core-services.yml up -d

# 第3步：启动MCP服务器层
docker-compose -f docker-compose.mcp-servers.yml up -d

# 第4步：启动应用层
docker-compose -f docker-compose.applications.yml up -d

# 第5步：启动监控层（可选）
docker-compose -f docker-compose.monitoring.yml up -d
```

### 3. 检查服务状态

```bash
docker-compose ps
```

### 4. 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f xiaonuo-gateway
docker-compose logs -f api-gateway
```

### 5. 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（谨慎使用）
docker-compose down -v
```

## 服务端口分配

### 基础设施层
| 服务 | 端口 | 说明 |
|------|------|------|
| Redis | 6379 | 缓存服务 |
| Qdrant HTTP | 6333 | 向量数据库API |
| Qdrant gRPC | 6334 | 向量数据库gRPC |
| **Neo4j HTTP** | **7474** | **图数据库Web界面** ⭐ |
| **Neo4j Bolt** | **7687** | **图数据库连接协议** ⭐ |
| Neo4j HTTP (本地) | 7475 | 本地开发环境Web界面 |
| Neo4j Bolt (本地) | 7688 | 本地开发环境连接协议 |

> ⭐ **TD-001变更**: 已将NebulaGraph端口(9669/9559/9779)替换为Neo4j端口(7474/7687)

#### NebulaGraph旧端口（已废弃，仅供参考）
| 服务 | 旧端口 | 说明 |
|------|--------|------|
| NebulaGraph | 9669 | 已废弃 |
| NebulaGraph Meta | 9559 | 已废弃 |
| NebulaGraph Storage | 9779 | 已废弃 |

### 核心服务层
| 服务 | 端口 | 说明 |
|------|------|------|
| API网关 | 8080 | 统一API网关 |
| 统一身份认证 | 8010 | 身份认证服务 |
| YunPat代理 | 8020 | 专利代理服务 |
| 浏览器自动化 | 8030 | 浏览器自动化 |
| JoyAgent优化 | 8035 | 优化服务 |
| 自主控制 | 8040 | 自主控制服务 |
| 专利分析 | 8050 | 专利分析服务 |
| 专利搜索 | 8060 | 专利搜索服务 |
| 知识图谱服务 | 8070 | 知识图谱服务 |

### MCP服务器层
| 服务 | 端口 | 说明 |
|------|------|------|
| 学术搜索MCP | 8200 | 学术论文搜索 |
| 专利搜索MCP | 8201 | 专利搜索服务 |
| 专利下载MCP | 8202 | 专利文档下载 |
| Chrome MCP | 8205 | Chrome浏览器控制 |
| Jina AI MCP | 8203 | Jina AI集成 |
| 高德地图MCP | 8206 | 高德地图集成 |
| GitHub MCP | 8207 | GitHub集成 |
| 谷歌专利元数据MCP | 8208 | 谷歌专利元数据 |

### 应用层
| 服务 | 端口 | 说明 |
|------|------|------|
| 意图识别 | 8002 | 意图识别服务 |
| XiaoNuo网关 | 8100 | XiaoNuo统一网关 |
| 可视化工具 | 8091 | 可视化工具 |

### 监控层
| 服务 | 端口 | 说明 |
|------|------|------|
| Prometheus | 9090 | 监控数据采集 |
| Grafana | 3000 | 监控可视化 |
| AlertManager | 9093 | 告警管理 |
| cAdvisor | 8081 | 容器监控 |
| Node Exporter | 9100 | 节点监控 |

## 重要说明 (TD-001迁移)

### Neo4j配置 (新标准 - TD-001)
- **图数据库**: Neo4j 5-community
- **Web界面**: http://localhost:7474
- **Bolt协议**: bolt://localhost:7687
- **默认认证**: neo4j/athena_neo4j_2024 (⚠️ 生产环境请修改)
- **数据库管理**: 使用Cypher查询语言
- **数据迁移**: 从NebulaGraph迁移到Neo4j，详见[迁移指南](#td-001迁移指南)

### PostgreSQL配置 (不变)
- **使用本地PostgreSQL 17.7版本**，不使用Docker容器
- 容器通过 `host.docker.internal:5432` 连接本地PostgreSQL
- 确保本地PostgreSQL服务已启动：`brew services start postgresql@17`
- 确保数据库用户和密码配置正确（在.env文件中）

### 网络配置
- 每层使用独立的Docker网络，网络间可以互通
- 网络名称：athena-infrastructure、athena-core-services、athena-mcp-servers、athena-applications、athena-monitoring

### 数据持久化
- 数据存储在：`/Users/xujian/Athena工作平台/data/`
- 日志存储在：`/Users/xujian/Athena工作平台/logs/`
- 请确保这些目录有足够的磁盘空间

### 资源限制
- 每个服务都配置了CPU和内存限制
- 根据实际硬件资源调整各docker-compose文件中的 `deploy.resources`

## 故障排查

### 服务启动失败
1. 检查端口是否被占用：`lsof -i :<port>`
2. 检查日志：`docker-compose logs <service_name>`
3. 检查环境变量：确保.env文件配置正确

### PostgreSQL连接失败
1. 确认本地PostgreSQL已启动：`psql -h localhost -U athena`
2. 检查防火墙设置
3. 确认数据库用户权限

### 健康检查失败
1. 查看服务日志
2. 检查依赖服务是否已启动
3. 使用 `docker-compose ps` 查看服务状态

## 迁移指南

### TD-001: NebulaGraph → Neo4j 迁移指南

从NebulaGraph迁移到Neo4j的技术决策和实施步骤：

#### 1. 代码变更映射

| NebulaGraph | Neo4j | 说明 |
|-------------|-------|------|
| `ConnectionPool` | `GraphDatabase.driver` | 连接管理 |
| `CREATE SPACE` | `CREATE DATABASE` | 数据库创建 |
| `CREATE TAG` | `CREATE CONSTRAINT` | 节点类型 |
| `CREATE EDGE` | `CREATE CONSTRAINT` | 关系类型 |
| `INSERT VERTEX` | `MERGE (n:Label)` | 节点插入 |
| `INSERT EDGE` | `MERGE (a)-[r:REL]->(b)` | 关系插入 |
| `nGQL` | `Cypher` | 查询语言 |
| `space` | `database` | 数据库名称 |
| `vid_type` | `node id` | 节点ID类型 |
| `host+port` | `uri` (bolt://host:port) | 连接地址 |

#### 2. 配置文件迁移

**旧配置 (NebulaGraph)**:
```yaml
nebula:
  image: vesoft/nebula-graph:v3.5.0
  ports:
    - "9669:9669"  # Graph
    - "9559:9559"  # Meta
    - "9779:9779"  # Storage
  environment:
    - NEBULA_ROOT_USER=root
    - NEBULA_ROOT_PASSWORD=nebula
```

**新配置 (Neo4j - TD-001)**:
```yaml
neo4j:
  image: neo4j:5-community
  ports:
    - "7474:7474"  # HTTP
    - "7687:7687"  # Bolt
  environment:
    - NEO4J_AUTH=neo4j/neo4j_password
    - NEO4J_dbms_memory_heap_max__size=512M
    - NEO4J_dbms_memory_pagecache_size=512M
```

#### 3. Python代码迁移示例

**旧代码 (NebulaGraph)**:
```python
from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config

config = Config()
pool = ConnectionPool()
pool.init([("127.0.0.1", 9669)], config)
session = pool.get_session("root", "nebula")

# 创建空间
session.execute("CREATE SPACE IF NOT EXISTS legal_kg (...)")
session.execute("USE legal_kg")

# 插入节点
session.execute('INSERT VERTEX law(name) VALUES "law1": "民法典"')
```

**新代码 (Neo4j - TD-001)**:
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://127.0.0.1:7687",
    auth=("neo4j", "neo4j_password")
)

# 创建数据库
with driver.session(database="system") as session:
    session.run("CREATE DATABASE legal_kg")

# 插入节点
with driver.session(database="legal_kg") as session:
    session.run("MERGE (l:Law {id: 'law1'}) SET l.name = '民法典'")
```

#### 4. 数据迁移步骤

1. **备份NebulaGraph数据**:
   ```bash
   # 使用NebulaGraph导出工具
   nebula-console -addr 127.0.0.1 -port 9669 -u root -p nebula
   > EXPORT GRAPH TO '/backup/nebula';
   ```

2. **转换数据格式**:
   - 将NebulaGraph的VID映射到Neo4j的节点ID
   - 将TAG转换为Label
   - 将EDGE转换为Relationship

3. **导入到Neo4j**:
   ```bash
   # 使用neo4j-admin导入工具
   neo4j-admin database import full \
     --nodes=Law=/data/law.csv \
     --relationships=/data/relations.csv \
     --overwrite-destination=true
   ```

4. **验证迁移**:
   ```python
   # 验证节点数量
   result = session.run("MATCH (n) RETURN count(n) as count")
   print(f"节点总数: {result.single()['count']}")

   # 验证关系数量
   result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
   print(f"关系总数: {result.single()['count']}")
   ```

### 从旧的配置文件迁移

从旧的81个配置文件迁移：

1. **旧配置文件已归档到 `archive/` 目录**
2. **确认所有服务在新配置中正常运行**
3. **更新CI/CD脚本使用新的docker-compose命令**
4. **更新部署文档**

## 维护

### 更新镜像
```bash
docker-compose pull
docker-compose up -d
```

### 清理未使用的资源
```bash
docker system prune -a
```

### 备份数据
```bash
# 备份数据卷
docker run --rm -v athena-redis-data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz /data

# 备份PostgreSQL数据（使用pg_dump）
pg_dump -U athena -h localhost athena > athena-backup.sql
```

## 监控和日志

### Prometheus
- 访问地址：http://localhost:9090
- 默认用户名/密码：无

### Grafana
- 访问地址：http://localhost:3000
- 默认用户名：admin
- 默认密码：admin123（首次登录后需修改）

### 日志聚合
- 所有服务的日志都输出到标准输出/标准错误
- 使用 `docker-compose logs -f` 查看实时日志
- 可以配置日志驱动（如ELK、Loki等）进行日志聚合

## 支持

如有问题，请联系：
- 邮件：xujian519@gmail.com
- 项目文档：/Users/xujian/Athena工作平台/docs/

## 参考文档

### TD-001相关文档
- **技术决策文档**: `/docs/TD-001-neo4j-migration.md`
- **迁移实施报告**: `/docs/TD-001-migration-report.md`
- **Neo4j使用指南**: `/docs/neo4j-user-guide.md`
- **NebulaGraph归档**: `/config/docker/archive/nebulagraph_configs/`

### 相关技术文档
- Neo4j官方文档: https://neo4j.com/docs/
- Docker Compose文档: https://docs.docker.com/compose/
- Qdrant文档: https://qdrant.tech/documentation/
- Redis文档: https://redis.io/documentation

---

**最后更新**: 2026-01-26
**版本**: v3.0.0 (TD-001 - Neo4j统一图数据库)
**维护者**: Athena平台团队
