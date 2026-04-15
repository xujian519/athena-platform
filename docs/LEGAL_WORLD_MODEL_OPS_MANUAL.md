# 法律世界模型运维手册
# Legal World Model Operations Manual

> **最后更新**: 2026-02-03
> **版本**: v1.0.0
> **维护团队**: Athena平台团队

---

## 📋 目录

1. [系统概述](#系统概述)
2. [部署指南](#部署指南)
3. [监控告警](#监控告警)
4. [备份恢复](#备份恢复)
5. [故障排查](#故障排查)
6. [性能优化](#性能优化)
7. [安全最佳实践](#安全最佳实践)

---

## 系统概述

### 架构组件

```
┌─────────────────────────────────────────────────────────┐
│                  法律世界模型架构                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │   宪法模块   │  │  场景识别    │  │  规则检索    │                │
│  │ Constitution│  │  Identifier │  │  Retriever   │                │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │
│         │                │                │                        │
│         └────────────────┴────────────────┘                        │
│                           │                                       │
│  ┌─────────────────────────────────────────────────┐           │
│  │            数据存储层                             │           │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │           │
│  │  │  Neo4j   │  │PostgreSQL│  │  Qdrant  │            │           │
│  │  │ 知识图谱 │  │ 专利数据  │  │ 向量检索 │            │           │
│  │  └──────────┘  └──────────┘  └──────────┘            │           │
│  └─────────────────────────────────────────────────┘           │
│                                                           │
│  ┌─────────────────────────────────────────────────┐           │
│  │            API和服务层                             │           │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │           │
│  │  │健康检查  │  │  学习引擎 │  │  监控告警 │            │           │
│  │  │ /health  │  │ Learning  │  │Monitoring│            │           │
│  │  └──────────┘  └──────────┘  └──────────┘            │           │
│  └─────────────────────────────────────────────────┘           │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 关键数据

| 数据存储 | 大小 | 说明 |
|---------|------|------|
| Neo4j知识图谱 | 2.4 GB | 125万+ 节点，328万+ 关系 |
| Qdrant向量库 | 3.4 GB | 2126条专利规则向量 |
| PostgreSQL | - | 专利文档、元数据 |
| Redis缓存 | - | 会话缓存、临时数据 |

---

## 部署指南

### 前置要求

#### 硬件要求
- CPU: 4核心以上
- 内存: 8GB以上
- 磁盘: 20GB以上可用空间

#### 软件依赖
```bash
# 核心依赖
Python 3.11+
PostgreSQL 15+
Neo4j 5.x
Qdrant 1.7+
Redis 7.x+

# Python包
fastapi
uvicorn
psycopg2-binary
neo4j
qdrant-client
redis
```

### 部署步骤

#### 1. 环境准备

```bash
# 克隆代码
git clone <repository_url> Athena工作平台
cd Athena工作平台

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库密码等
```

#### 2. 数据库初始化

```bash
# 启动服务
docker-compose up -d postgres neo4j qdrant redis

# 导入数据（如果需要）
python scripts/migration/import_legal_data.py
```

#### 3. 启动应用

```bash
# 开发环境
uvicorn core.main:app --reload

# 生产环境
pm2 start ecosystem.config.js
```

#### 4. 验证部署

```bash
# 运行健康检查
python scripts/verify_database_connections.py

# 运行测试
pytest tests/legal_world_model/ -v
```

---

## 监控告警

### 监控指标

#### 核心指标

| 类别 | 指标 | 阈值 | 告警级别 |
|------|------|------|----------|
| 可用性 | 组件健康状态 | up/down | P0 |
| 性能 | P50响应时间 | <100ms | P1 |
| 性能 | P95响应时间 | <500ms | P1 |
| 性能 | P99响应时间 | <1000ms | P2 |
| 业务 | 规则检索成功率 | >95% | P1 |
| 业务 | 检索准确率 | >0.85 | P2 |

#### 监控端点

```
GET /health/              # 简单健康检查
GET /health/detailed     # 详细健康状态
GET /health/components   # 组件状态
POST /health/test/{name}  # 测试特定组件
```

### 告警规则

#### P0 告警（立即处理）

| 条件 | 触发条件 | 通知渠道 |
|------|----------|----------|
| 系统不可用 | 任何组件down | 钉钉、邮件、短信 |
| 数据丢失 | 数据损坏或丢失 | 钉钉、邮件、短信 |
| 安全漏洞 | 检测到入侵 | 钉钉、邮件、短信 |

#### P1 告警（24小时内处理）

| 条件 | 触发条件 | 通知渠道 |
|------|----------|----------|
| 性能下降 | P95 > 1秒 | 钉钉、邮件 |
| 错误率增加 | 错误率 >5% | 钉钉、邮件 |
| 磁盘空间不足 | <10% | 邮件 |

### 监控工具集成

#### Prometheus集成

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'athena_health'
    scrape_interval: 30s
    static_configs:
      - targets: ['localhost:8000/health/metrics']
```

#### Grafana仪表板

提供预配置的仪表板：
- 系统健康仪表板
- 性能指标仪表板
- 业务指标仪表板

---

## 备份恢复

### 备份策略

#### 自动化备份

```bash
# 运行备份
python scripts/backup/run_backup.py

# 设置定时任务（每天凌晨2点）
0 2 * * * cd /Users/xujian/Athena工作平台 && \
  python3 scripts/backup/run_backup.py >> \
  /var/log/athena_backup.log 2>&1
```

#### 备份内容

- PostgreSQL数据库（SQL格式 + 压缩）
- Neo4j图数据库（数据目录）
- Qdrant向量索引（数据目录）
- Redis持久化数据
- 配置文件（.env, docker-compose.yml等）

#### 备份保留策略

- 每日完整备份保留30天
- 每周备份保留3个月
- 每月备份保留1年

### 恢复流程

#### PostgreSQL恢复

```bash
# 1. 停止应用服务
docker-compose down

# 2. 恢复数据库
gunzip < /backup/path/athena_dump.sql.gz | \
  psql -h localhost -U postgres athena

# 3. 重启服务
docker-compose up -d
```

#### Neo4j恢复

```bash
# 1. 停止Neo4j服务
docker-compose stop neo4j

# 2. 恢复数据目录
rm -rf /data/neo4j/*
cp -r /backup/path/neo4j/* /data/neo4j/

# 3. 重启服务
docker-compose start neo4j
```

#### Qdrant恢复

```bash
# 1. 停止Qdrant服务
docker-compose stop qdrant

# 2. 恢复数据目录
rm -rf /data/qdrant/*
cp -r /backup/path/qdrant/* /data/qdrant/

# 3. 重启服务
docker-compose start qdrant
```

### 备份验证

```bash
# 验证备份完整性
python scripts/backup/verify_backups.sh

# 测试恢复流程（在测试环境）
# 定期进行恢复演练
```

---

## 故障排查

### 常见问题

#### 1. 数据库连接失败

**症状**: 健康检查显示数据库down

**诊断**:
```bash
# 检查服务状态
docker-compose ps

# 检查日志
docker-compose logs postgres
docker-compose logs neo4j

# 测试连接
python scripts/verify_database_connections.py
```

**解决方案**:
- 检查服务是否运行
- 验证.env中的密码配置
- 检查网络连接

#### 2. 检索性能下降

**症状**: 响应时间变慢

**诊断**:
```bash
# 检查Qdrant集合状态
curl http://localhost:6333/collections

# 检查Neo4j查询性能
# 在Neo4j浏览器中运行 PROFILE查询

# 检查缓存命中率
```

**解决方案**:
- 重建Qdrant索引
- 优化Neo4j查询
- 增加缓存预热

#### 3. 内存不足

**症状**: OOM错误，系统变慢

**诊断**:
```bash
# 检查内存使用
free -h

# 检查Python进程内存
ps aux | grep python

# 检查Docker容器内存
docker stats
```

**解决方案**:
- 增加系统内存
- 优化缓存策略
- 限制并发连接数

#### 4. 数据不一致

**症状**: 检索结果与实际不符

**诊断**:
```bash
# 运行数据校验
python scripts/verify_data_persistence.sh

# 检查日志中的错误
grep ERROR /var/log/athena/*.log
```

**解决方案**:
- 从备份恢复数据
- 同步数据源
- 修复数据不一致

### 紧急联系

| 级别 | 响应时间 | 联系方式 |
|------|----------|----------|
| P0 | 15分钟 | 电话 + 钉钉 |
| P1 | 1小时 | 邮件 + 钉钉 |
| P2 | 4小时 | 邮件 |

---

## 性能优化

### 优化策略

#### 1. Neo4j优化

```cypher
// 创建索引
CREATE INDEX ON :Patent(id)
CREATE INDEX ON :Case(date)

// 查询优化
PROFILE MATCH (p:Patent)-[:RELATED]->()
RETURN p
LIMIT 100
```

#### 2. Qdrant优化

```python
# 批量查询
def search_optimized(queries):
    # 使用批量查询减少网络往返
    results = client.search_batch(
        collection_name="patents",
        requests=queries
    )
    return results
```

#### 3. 缓存优化

```python
# 多级缓存
L1: 内存缓存 (热数据, 5分钟TTL)
L2: Redis缓存 (温数据, 1小时TTL)
L3: 数据库 (冷数据)
```

#### 4. 并发优化

```python
# 使用连接池
from psycopg2 import pool

connection_pool = pool.SimplePool(
    minconn=5,
    maxconn=20,
    idle_connection_ttl=300
)

# 异步处理
async def process_batch(items):
    tasks = [process_item(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results
```

### 性能基准

| 操作 | 目标值 | 当前值 |
|------|--------|--------|
| 健康检查 | <5秒 | 待测 |
| 规则检索 | <100ms | 待测 |
| 批量查询 | <500ms | 待测 |
| 数据导入 | 1000条/秒 | 待测 |

---

## 安全最佳实践

### 访问控制

```yaml
# 网络访问
防火墙规则:
  - 仅允许80, 443, 8000端口
  - 限制数据库端口访问

# 应用访问
  - 所有API需要认证
  - 敏感操作需要二次确认
```

### 数据保护

```yaml
加密:
  - 传输加密: HTTPS/TLS
  - 存储加密: 数据库加密

备份:
  - 备份文件加密
  - 备份存储隔离
  - 定期验证备份

审计:
  - 操作日志记录
  - 访问日志记录
  - 定期审计日志
```

### 更新维护

```yaml
更新策略:
  - 滚动更新 (无停机)
  - 蓝绿部署
  - 自动回滚

维护窗口:
  - 每周凌晨 2:00-4:00
  - 提前通知用户
```

---

## 附录

### A. 环境变量参考

```bash
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=athena
DB_USER=postgres
DB_PASSWORD=<your_password>

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your_password>

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=<optional>

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=<optional>
```

### B. 端口参考

```bash
# 健康检查
GET /health/
GET /health/detailed
GET /health/components

# 法律世界模型
GET /api/v1/legal-world-model/health
GET /api/v1/legal-world-model/retrieve
POST /api/v1/legal-world-model/validate
```

### C. 联系方式

- 技术支持: support@athena.local
- 紧急热线: +86-xxx-xxxx-xxxx
- 文档: https://docs.athena.local

---

> **文档维护**: 本文档需要随系统更新持续维护
> **版本控制**: 使用Git追踪所有修改
> **变更记录**: 记录重要更新和变更原因
