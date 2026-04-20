# Docker Compose统一配置 - 快速参考

> **配置文件**: `docker-compose.unified.yml`
> **迁移日期**: 2026-04-20

---

## 🚀 快速开始

### 开发环境

```bash
# 启动
docker-compose -f docker-compose.unified.yml --profile dev up -d

# 查看日志
docker-compose -f docker-compose.unified.yml --profile dev logs -f

# 停止
docker-compose -f docker-compose.unified.yml --profile dev down
```

**端口**: Redis 6379, Qdrant 6333/6334, Neo4j 7474/7687

---

### 测试环境

```bash
# 启动
docker-compose -f docker-compose.unified.yml --profile test up -d

# 启动特定服务
docker-compose -f docker-compose.unified.yml --profile test up -d postgres-test redis-test

# 清理数据
docker-compose -f docker-compose.unified.yml --profile test down -v
```

**端口**: PostgreSQL 5433, Redis 6380, Qdrant 6334/6335, Neo4j 7475/7688, MinIO 9001/9002

---

### 生产环境

```bash
# 启动
docker-compose -f docker-compose.unified.yml --profile prod up -d
```

**端口**: Qdrant 6335, NebulaGraph 9670/19670

---

### 监控服务

```bash
# 启动
docker-compose -f docker-compose.unified.yml --profile monitoring up -d

# 访问
open http://localhost:3005  # Grafana
open http://localhost:9090  # Prometheus
open http://localhost:9093  # Alertmanager
```

**端口**: Prometheus 9090, Grafana 3005, Alertmanager 9093

---

## 🔄 组合使用

```bash
# 开发 + 监控
docker-compose -f docker-compose.unified.yml --profile dev --profile monitoring up -d

# 测试 + 监控
docker-compose -f docker-compose.unified.yml --profile test --profile monitoring up -d
```

---

## 📖 环境变量

```bash
# 开发环境
source .env.dev

# 测试环境
source .env.test

# 生产环境（修改密码！）
source .env.prod
```

---

## 🆘 常用命令

```bash
# 查看容器状态
docker-compose -f docker-compose.unified.yml --profile dev ps

# 查看服务日志
docker-compose -f docker-compose.unified.yml --profile dev logs redis

# 重启服务
docker-compose -f docker-compose.unified.yml --profile dev restart

# 强制重新创建
docker-compose -f docker-compose.unified.yml --profile dev up -d --force-recreate
```

---

## 🔄 迁移

```bash
# 自动迁移
./scripts/migrate_docker_compose.sh

# 手动迁移详见
cat DOCKER_COMPOSE_MIGRATION_GUIDE.md
```

---

## 📊 端口对照表

| 服务 | 开发 | 测试 | 生产 |
|-----|------|------|------|
| PostgreSQL | - | 5433 | - |
| Redis | 6379 | 6380 | - |
| Qdrant HTTP | 6333 | 6334 | 6335 |
| Qdrant gRPC | 6334 | 6335 | - |
| Neo4j HTTP | 7474 | 7475 | - |
| Neo4j Bolt | 7687 | 7688 | - |
| MinIO API | - | 9001 | - |
| MinIO Console | - | 9002 | - |
| Prometheus | 9090 | - | - |
| Grafana | 3005 | - | - |
| Alertmanager | 9093 | - | - |

---

**详细文档**: `DOCKER_COMPOSE_MIGRATION_GUIDE.md`
