# Docker Compose配置合并迁移指南

> **版本**: v1.0
> **日期**: 2026-04-20
> **状态**: ✅ 已完成

---

## 📋 概述

Athena工作平台原有的6个Docker Compose配置文件已合并为**1个统一配置文件**，使用**Docker Profiles**区分不同环境。

### 🎯 迁移目标

- ✅ 简化配置管理（6个文件 → 1个文件）
- ✅ 统一环境管理（dev/test/prod/monitoring）
- ✅ 避免端口冲突
- ✅ 降低维护成本

---

## 🗂️ 配置文件对照表

### 旧配置文件（已废弃）

| 文件路径 | 用途 | 新配置 |
|---------|------|--------|
| `docker-compose.yml` | 开发环境 | `--profile dev` |
| `docker-compose.test.yml` | 测试环境 | `--profile test` |
| `config/docker/docker-compose.production.yml` | 生产环境 | `--profile prod` |
| `core/observability/monitoring/docker-compose.yml` | 监控服务 | `--profile monitoring` |
| `shared/observability/monitoring/docker-compose.yml` | 监控服务 | `--profile monitoring` |
| `tests/integration/docker-compose.test.yml` | 集成测试 | `--profile test` |

### 新配置文件

**唯一配置文件**: `docker-compose.unified.yml`

**环境Profile**:
- `dev` - 开发环境（默认）
- `test` - 测试环境
- `prod` - 生产环境
- `monitoring` - 监控服务

---

## 🚀 快速迁移步骤

### 步骤1: 备份现有配置

```bash
# 创建备份目录
mkdir -p .docker_backup_$(date +%Y%m%d)

# 备份所有docker-compose文件
cp docker-compose.yml .docker_backup_$(date +%Y%m%d)/
cp docker-compose.test.yml .docker_backup_$(date +%Y%m%d)/ 2>/dev/null || true
cp -r config/docker/ .docker_backup_$(date +%Y%m%d)/
cp -r core/observability/monitoring/docker-compose.yml .docker_backup_$(date +%Y%m%d)/ 2>/dev/null || true
cp -r shared/observability/monitoring/docker-compose.yml .docker_backup_$(date +%Y%m%d)/ 2>/dev/null || true
cp tests/integration/docker-compose.test.yml .docker_backup_$(date +%Y%m%d)/ 2>/dev/null || true

echo "✅ 配置文件已备份到: .docker_backup_$(date +%Y%m%d)/"
```

---

### 步骤2: 停止所有运行中的容器

```bash
# 停止开发环境容器
docker-compose down 2>/dev/null || true

# 停止测试环境容器
docker-compose -f docker-compose.test.yml down 2>/dev/null || true

# 停止生产环境容器
docker-compose -f config/docker/docker-compose.production.yml down 2>/dev/null || true

# 停止监控服务
docker-compose -f core/observability/monitoring/docker-compose.yml down 2>/dev/null || true

# 停止集成测试容器
docker-compose -f tests/integration/docker-compose.test.yml down 2>/dev/null || true

echo "✅ 所有容器已停止"
```

---

### 步骤3: 创建环境变量文件

```bash
# 创建开发环境变量
cat > .env.dev << 'EOF'
# Redis配置
REDIS_PASSWORD=redis123

# Grafana配置
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin123
GRAFANA_ROOT_URL=http://localhost:3005
EOF

# 创建测试环境变量
cat > .env.test << 'EOF'
# 测试数据库配置
TEST_DATABASE_URL=postgresql://athena_test:athena_test_password_2024@localhost:5433/athena_test_db
TEST_REDIS_URL=redis://localhost:6380/0
TEST_QDRANT_URL=http://localhost:6334
TEST_NEO4J_URI=bolt://localhost:7688
TEST_NEO4J_USER=neo4j
TEST_NEO4J_PASSWORD=athena_test_2024
TEST_MINIO_ENDPOINT=http://localhost:9001
TEST_MINIO_ACCESS_KEY=minioadmin
TEST_MINIO_SECRET_KEY=minioadmin123
EOF

# 创建生产环境变量
cat > .env.prod << 'EOF'
# 生产环境配置
REDIS_PASSWORD=CHANGE_ME_PRODUCTION
GRAFANA_ADMIN_PASSWORD=CHANGE_ME_SECURE_PASSWORD
EOF

echo "✅ 环境变量文件已创建"
```

---

### 步骤4: 测试新配置

```bash
# 测试开发环境
echo "🧪 测试开发环境..."
docker-compose -f docker-compose.unified.yml --profile dev config

# 测试测试环境
echo "🧪 测试测试环境..."
docker-compose -f docker-compose.unified.yml --profile test config

# 测试生产环境
echo "🧪 测试生产环境..."
docker-compose -f docker-compose.unified.yml --profile prod config

# 测试监控服务
echo "🧪 测试监控服务..."
docker-compose -f docker-compose.unified.yml --profile monitoring config

echo "✅ 配置测试完成"
```

---

### 步骤5: 启动新环境

```bash
# 启动开发环境
docker-compose -f docker-compose.unified.yml --profile dev up -d

# 查看容器状态
docker-compose -f docker-compose.unified.yml --profile dev ps

echo "✅ 开发环境已启动"
```

---

### 步骤6: 验证服务

```bash
# 检查Redis
docker exec athena-redis-dev redis-cli -a redis123 ping

# 检查Qdrant
curl http://localhost:6333/

# 检查Neo4j
curl http://localhost:7474/

echo "✅ 服务验证完成"
```

---

### 步骤7: 更新脚本和文档

#### 更新启动脚本

将所有脚本中的Docker Compose命令更新为新格式：

**旧命令**:
```bash
docker-compose up -d
docker-compose -f docker-compose.test.yml up -d
```

**新命令**:
```bash
docker-compose -f docker-compose.unified.yml --profile dev up -d
docker-compose -f docker-compose.unified.yml --profile test up -d
```

#### 更新文档

更新以下文档中的Docker Compose命令：
- `README.md`
- `CLAUDE.md`
- `docs/**/*.md`
- `scripts/**/*.sh`

---

## 📖 新配置使用指南

### 开发环境

```bash
# 启动开发环境
docker-compose -f docker-compose.unified.yml --profile dev up -d

# 查看日志
docker-compose -f docker-compose.unified.yml --profile dev logs -f

# 停止服务
docker-compose -f docker-compose.unified.yml --profile dev down

# 重启服务
docker-compose -f docker-compose.unified.yml --profile dev restart
```

**端口映射**:
- Redis: 6379
- Qdrant: 6333 (HTTP), 6334 (gRPC)
- Neo4j: 7474 (HTTP), 7687 (Bolt)

---

### 测试环境

```bash
# 启动测试环境
docker-compose -f docker-compose.unified.yml --profile test up -d

# 启动特定服务
docker-compose -f docker-compose.unified.yml --profile test up -d postgres-test redis-test

# 查看日志
docker-compose -f docker-compose.unified.yml --profile test logs -f postgres-test

# 停止服务
docker-compose -f docker-compose.unified.yml --profile test down

# 清理测试数据
docker-compose -f docker-compose.unified.yml --profile test down -v
```

**端口映射**:
- PostgreSQL: 5433
- Redis: 6380
- Qdrant: 6334 (HTTP), 6335 (gRPC)
- Neo4j: 7475 (HTTP), 7688 (Bolt)
- MinIO: 9001 (API), 9002 (Console)

---

### 生产环境

```bash
# 启动生产环境
docker-compose -f docker-compose.unified.yml --profile prod up -d

# 查看日志
docker-compose -f docker-compose.unified.yml --profile prod logs -f

# 停止服务
docker-compose -f docker-compose.unified.yml --profile prod down
```

**端口映射**:
- Qdrant: 6335
- NebulaGraph: 9670, 19670

---

### 监控服务

```bash
# 启动监控服务
docker-compose -f docker-compose.unified.yml --profile monitoring up -d

# 访问Grafana
open http://localhost:3005

# 访问Prometheus
open http://localhost:9090

# 访问Alertmanager
open http://localhost:9093
```

**端口映射**:
- Prometheus: 9090
- Grafana: 3005
- Alertmanager: 9093

---

### 组合使用

```bash
# 开发环境 + 监控
docker-compose -f docker-compose.unified.yml --profile dev --profile monitoring up -d

# 测试环境 + 监控
docker-compose -f docker-compose.unified.yml --profile test --profile monitoring up -d
```

---

## 🗑️ 清理旧配置（确认无问题后）

```bash
# 删除旧的docker-compose文件
rm docker-compose.yml
rm docker-compose.test.yml
rm -rf config/docker/docker-compose.production.yml
rm core/observability/monitoring/docker-compose.yml
rm shared/observability/monitoring/docker-compose.yml
rm tests/integration/docker-compose.test.yml

echo "✅ 旧配置文件已删除"
```

---

## 🔄 回滚方案

如果迁移后出现问题，可以快速回滚：

```bash
# 停止新配置
docker-compose -f docker-compose.unified.yml --profile dev down

# 恢复旧配置
cp .docker_backup_*/docker-compose.yml ./
cp .docker_backup_*/docker-compose.test.yml ./

# 重新启动旧配置
docker-compose up -d

echo "✅ 已回滚到旧配置"
```

---

## 📊 迁移检查清单

### 迁移前检查

- [ ] 备份所有docker-compose文件
- [ ] 停止所有运行中的容器
- [ ] 记录当前容器配置和端口映射
- [ ] 通知团队成员配置变更

### 迁移中检查

- [ ] 创建环境变量文件
- [ ] 测试新配置语法
- [ ] 验证端口无冲突
- [ ] 启动开发环境并验证服务
- [ ] 启动测试环境并验证服务
- [ ] 启动生产环境并验证服务（可选）

### 迁交后检查

- [ ] 更新所有相关脚本
- [ ] 更新项目文档
- [ ] 通知团队成员迁移完成
- [ ] 保留备份至少1周
- [ ] 监控服务运行状态

---

## ⚠️ 注意事项

### 端口冲突

新配置已调整端口避免冲突：

| 服务 | 开发环境 | 测试环境 | 生产环境 |
|-----|---------|---------|---------|
| PostgreSQL | - | 5433 | - |
| Redis | 6379 | 6380 | - |
| Qdrant HTTP | 6333 | 6334 | 6335 |
| Qdrant gRPC | 6334 | 6335 | - |
| Neo4j HTTP | 7474 | 7475 | - |
| Neo4j Bolt | 7687 | 7688 | - |
| Grafana | 3005 | - | - |

### 数据持久化

不同环境使用独立的数据卷，避免数据混淆：

- 开发环境: `*-dev-data`
- 测试环境: `*-test-data`
- 监控服务: `prometheus-data`, `grafana-data`

### 环境隔离

每个环境使用独立的网络：

- 开发环境: `athena-dev-network` (172.25.0.0/16)
- 测试环境: `athena-test-network` (172.29.0.0/16)
- 生产环境: `athena-prod-network` (172.26.0.0/16)
- 监控服务: `athena-monitoring-network` (172.27.0.0/16)

---

## 🆘 故障排查

### 问题1: 端口已被占用

**错误信息**: `Bind for 0.0.0.0:6379 failed: port is already allocated`

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :6379

# 停止占用端口的容器
docker stop <container_name>

# 或修改端口映射
vim docker-compose.unified.yml
```

---

### 问题2: 容器无法启动

**错误信息**: `Container failed to start`

**解决方案**:
```bash
# 查看容器日志
docker-compose -f docker-compose.unified.yml --profile dev logs <service_name>

# 检查容器状态
docker-compose -f docker-compose.unified.yml --profile dev ps

# 重新创建容器
docker-compose -f docker-compose.unified.yml --profile dev up -d --force-recreate
```

---

### 问题3: 网络连接问题

**错误信息**: `Cannot connect to service`

**解决方案**:
```bash
# 检查网络
docker network ls

# 清理未使用的网络
docker network prune

# 重新创建网络
docker-compose -f docker-compose.unified.yml --profile dev down
docker-compose -f docker-compose.unified.yml --profile dev up -d
```

---

## 📚 参考资源

- **Docker Compose文档**: https://docs.docker.com/compose/
- **Docker Profiles**: https://docs.docker.com/compose/profiles/
- **项目文档**: `CLAUDE.md`, `README.md`

---

## 📝 更新日志

### v1.0 (2026-04-20)

**初始版本**:
- ✅ 合并6个docker-compose文件为1个
- ✅ 使用Docker Profiles区分环境
- ✅ 调整端口映射避免冲突
- ✅ 创建完整迁移指南
- ✅ 提供回滚方案

---

**迁移完成后，请删除本文件或归档保存。**

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-20
