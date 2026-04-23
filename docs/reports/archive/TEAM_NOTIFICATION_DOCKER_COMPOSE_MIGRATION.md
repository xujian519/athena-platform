# 📢 团队通知 - Docker Compose配置更新

> **发布日期**: 2026-04-20
> **影响范围**: 所有开发人员
> **重要程度**: 🔴 高

---

## 🎯 更新摘要

Athena工作平台的Docker Compose配置已完成重大升级：

- ✅ **6个配置文件合并为1个** - `docker-compose.unified.yml`
- ✅ **使用Docker Profiles区分环境** - dev/test/prod/monitoring
- ✅ **端口冲突已解决** - 不同环境使用不同端口
- ✅ **所有脚本已更新** - 使用新的命令格式

---

## 🚀 新的使用方法

### 开发环境（默认）

```bash
# 启动开发环境
docker-compose -f docker-compose.unified.yml --profile dev up -d

# 查看日志
docker-compose -f docker-compose.unified.yml --profile dev logs -f

# 停止服务
docker-compose -f docker-compose.unified.yml --profile dev down
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
```

**端口映射**:
- Qdrant: 6335
- NebulaGraph: 9670, 19670

---

### 监控服务

```bash
# 启动监控服务
docker-compose -f docker-compose.unified.yml --profile monitoring up -d

# 访问地址
open http://localhost:3005  # Grafana (admin/admin123)
open http://localhost:9090  # Prometheus
open http://localhost:9093  # Alertmanager
```

---

### 组合使用

```bash
# 开发环境 + 监控
docker-compose -f docker-compose.unified.yml --profile dev --profile monitoring up -d

# 测试环境 + 监控
docker-compose -f docker-compose.unified.yml --profile test --profile monitoring up -d
```

---

## 📖 快速参考

### 常用命令对照表

| 操作 | 旧命令 | 新命令 |
|-----|--------|--------|
| 启动开发环境 | `docker-compose up -d` | `docker-compose -f docker-compose.unified.yml --profile dev up -d` |
| 停止开发环境 | `docker-compose down` | `docker-compose -f docker-compose.unified.yml --profile dev down` |
| 查看日志 | `docker-compose logs -f` | `docker-compose -f docker-compose.unified.yml --profile dev logs -f` |
| 启动测试环境 | `docker-compose -f docker-compose.test.yml up -d` | `docker-compose -f docker-compose.unified.yml --profile test up -d` |

### 端口映射总览

| 服务 | 开发 | 测试 | 生产 |
|-----|------|------|------|
| PostgreSQL | - | 5433 | - |
| Redis | 6379 | 6380 | - |
| Qdrant HTTP | 6333 | 6334 | 6335 |
| Qdrant gRPC | 6334 | 6335 | - |
| Neo4j HTTP | 7474 | 7475 | - |
| Neo4j Bolt | 7687 | 7688 | - |
| Grafana | 3005 | - | - |
| Prometheus | 9090 | - | - |

---

## ⚠️ 重要变更

### 1. 配置文件变更

**旧配置文件（已废弃）**:
- ❌ `docker-compose.yml`
- ❌ `docker-compose.test.yml`
- ❌ `config/docker/docker-compose.production.yml`
- ❌ `core/observability/monitoring/docker-compose.yml`
- ❌ `shared/observability/monitoring/docker-compose.yml`
- ❌ `tests/integration/docker-compose.test.yml`

**新配置文件（唯一）**:
- ✅ `docker-compose.unified.yml`

### 2. 命令格式变更

所有docker-compose命令现在需要：
1. 指定配置文件：`-f docker-compose.unified.yml`
2. 指定环境profile：`--profile <dev|test|prod|monitoring>`

### 3. 环境变量

新增环境变量文件：
- `.env.dev` - 开发环境
- `.env.test` - 测试环境
- `.env.prod` - 生产环境（**请修改默认密码！**）

---

## 🔧 迁移检查清单

### 立即行动

- [ ] 阅读本文档
- [ ] 查看快速参考：`DOCKER_COMPOSE_QUICK_REFERENCE.md`
- [ ] 测试新配置：`docker-compose -f docker-compose.unified.yml --profile dev up -d`
- [ ] 验证服务正常运行

### 本周完成

- [ ] 更新个人脚本中的docker-compose命令
- [ ] 更新个人文档中的docker-compose引用
- [ ] 通知团队成员

### 后续工作

- [ ] 确认所有测试通过
- [ ] 删除旧的docker-compose文件（1周后）
- [ ] 反馈遇到的问题

---

## 📚 详细文档

- **快速参考**: `DOCKER_COMPOSE_QUICK_REFERENCE.md`
- **迁移指南**: `DOCKER_COMPOSE_MIGRATION_GUIDE.md`
- **合并报告**: `DOCKER_COMPOSE_MERGE_REPORT.md`
- **配置文件**: `docker-compose.unified.yml`

---

## 🔄 回滚方案

如果遇到问题，可以快速回滚到旧配置：

```bash
# 停止新配置
docker-compose -f docker-compose.unified.yml --profile dev down

# 恢复旧配置
cp .docker_backup_20260420_232115/docker-compose.yml ./

# 重新启动
docker-compose up -d
```

**备份位置**: `.docker_backup_20260420_232115/`

---

## 🆘 获取帮助

### 常见问题

**Q1: 端口冲突怎么办？**
A: 确保旧容器已停止：`docker-compose -f docker-compose.unified.yml --profile dev down`

**Q2: 如何查看所有容器？**
A: `docker-compose -f docker-compose.unified.yml --profile dev ps`

**Q3: 如何清理数据？**
A: `docker-compose -f docker-compose.unified.yml --profile dev down -v`

**Q4: 监控服务无法访问？**
A: 确保同时启动了dev和monitoring profiles

### 联系方式

- **技术支持**: 徐健 (xujian519@gmail.com)
- **问题反馈**: GitHub Issues

---

## 📅 时间线

- **2026-04-20**: 配置合并完成
- **2026-04-20**: 脚本和文档更新完成
- **2026-04-27**: 删除旧配置文件（1周后）

---

## ✅ 确认收到

请所有团队成员确认收到此通知，并在测试后反馈问题。

- [ ] 张三
- [ ] 李四
- [ ] 王五
- [ ] 赵六

---

**感谢大家的配合！🙏**

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-20
