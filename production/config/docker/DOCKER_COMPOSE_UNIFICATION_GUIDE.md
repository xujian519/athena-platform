# Athena工作平台 - Docker Compose配置统一化指南

## 📊 现状分析

### 配置文件分布统计

| 目录 | 文件数量 | 状态 | 说明 |
|------|----------|------|------|
| `config/docker/` | 16 | ✅ **已整合** | 核心配置目录，使用分层模块化设计 |
| `config/configs-legacy/` | 8 | ⚠️ 遗留配置 | 待清理或迁移 |
| `infrastructure/docker/` | 7 | ⚠️ 独立配置 | 可能需要整合 |
| `services/*/docker-compose.*` | 48 | ⚠️ 分散配置 | 各服务独立配置 |
| `apps/*/docker-compose.*` | 5 | ⚠️ 分散配置 | 应用独立配置 |
| 其他目录 | 若干 | ⚠️ 零散配置 | 各种临时/测试配置 |

**总计**: 79个Docker Compose文件

---

## ✅ 已完成整合的核心配置

### 推荐使用的统一配置

```
config/docker/docker-compose.yml
```

**特点**：
- 使用Docker Compose v2.0+的`include`功能
- 5层模块化架构
- 统一的网络和卷管理
- 完整的依赖关系和健康检查

### 配置分层结构

```
docker-compose.yml (主配置)
├── docker-compose.infrastructure.yml   # 基础设施层
├── docker-compose.core-services.yml    # 核心服务层
├── docker-compose.mcp-servers.yml      # MCP服务器层
├── docker-compose.applications.yml     # 应用层
└── docker-compose.monitoring.yml       # 监控层
```

#### 1️⃣ 基础设施层 (`docker-compose.infrastructure.yml`)

**包含服务**：
- PostgreSQL (使用本地17.7版本，非容器)
- Redis 7 (缓存)
- Qdrant (向量数据库)
- NebulaGraph集群 (Meta、Storage、Graph)

**网络**: `athena-infrastructure` (172.20.0.0/16)

#### 2️⃣ 核心服务层 (`docker-compose.core-services.yml`)

**包含服务**：
- API网关 (8080)
- 统一身份认证 (8010)
- YunPat专利代理 (8020)
- 浏览器自动化 (8030)
- 自主控制 (8040)
- 专利分析 (8050)
- 专利搜索 (8060)
- 知识图谱服务 (8070)
- JoyAgent优化 (8035)

**网络**: `athena-core-services` (172.21.0.0/16)

#### 3️⃣ MCP服务器层 (`docker-compose.mcp-servers.yml`)

**包含服务**：
- 学术搜索MCP (8200)
- 专利搜索MCP (8201)
- 专利下载MCP (8202)
- Jina AI MCP (8203)
- Chrome MCP (8205)
- 高德地图MCP (8206)
- GitHub MCP (8207)
- 谷歌专利元数据MCP (8208)

**网络**: `athena-mcp-servers` (172.22.0.0/16)

#### 4️⃣ 应用层 (`docker-compose.applications.yml`)

**包含服务**：
- XiaoNuo统一网关 (8100)
- 意图识别服务 (8002)
- 可视化工具 (8091)

**网络**: `athena-applications` (172.23.0.0/16)

#### 5️⃣ 监控层 (`docker-compose.monitoring.yml`)

**包含服务**：
- Prometheus (9090)
- Grafana (3001)
- AlertManager (9093)
- cAdvisor (8081)
- Node Exporter (9100)

**网络**: `athena-monitoring` (172.24.0.0/16)

---

## 🚀 快速启动指南

### 启动所有服务

```bash
cd /Users/xujian/Athena工作平台/config/docker
docker-compose up -d
```

### 按层启动

```bash
# 仅基础设施层
docker-compose -f docker-compose.infrastructure.yml up -d

# 基础设施 + 核心服务
docker-compose -f docker-compose.infrastructure.yml \
               -f docker-compose.core-services.yml up -d

# 基础设施 + 核心服务 + 应用层
docker-compose -f docker-compose.infrastructure.yml \
               -f docker-compose.core-services.yml \
               -f docker-compose.applications.yml up -d
```

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 所有服务日志
docker-compose logs -f

# 特定服务日志
docker-compose logs -f [service_name]
```

### 停止服务

```bash
docker-compose down
```

---

## ⚠️ 待清理的遗留配置

### `config/configs-legacy/` 目录

这些配置文件已过时，需要清理或迁移：

| 文件 | 状态 | 建议 |
|------|------|------|
| `docker-compose.arangodb.yml` | ❌ 已废弃 | 删除 (已迁移到Neo4j) |
| `docker-compose.databases.yml` | ⚠️ 重复 | 删除 (已被infrastructure替代) |
| `docker-compose.production.yml` | ⚠️ 过时 | 删除 (已被主配置替代) |
| `docker-compose.qdrant.yml` | ⚠️ 重复 | 删除 (已被infrastructure替代) |
| `docker-compose.quick.yml` | ⚠️ 临时 | 删除 (仅用于测试) |
| `docker-compose.xiaonuo-optimized.yml` | ❌ 已废弃 | 删除 (8006端口已废弃) |
| `docker-compose.yml` | ⚠️ 过时 | 删除 (已被主配置替代) |

### 各服务目录中的独立配置

以下配置保留用于独立开发和测试，生产环境应使用统一配置：

```
services/athena-unified/docker-compose.production.yml
services/yunpat_agent/docker-compose.prod.yml
services/whiteboard-service/docker-compose.*.yml
apps/xiaonuo/docker-compose.v*.yml
apps/xiaonuo/orchestrator/docker-compose.*.yml
```

**建议**: 这些文件保留用于独立测试，但应在文档中标注"仅用于开发/测试"。

---

## 🔧 配置迁移计划

### 阶段1: 遗留配置清理

```bash
# 删除确认废弃的配置
cd /Users/xujian/Athena工作平台
rm -rf config/configs-legacy/
```

### 阶段2: 独立配置标记

在各服务目录的独立配置文件中添加注释：

```yaml
# ⚠️ 注意: 此配置仅用于独立开发和测试
# 生产环境请使用: config/docker/docker-compose.yml
```

### 阶段3: 文档更新

- 更新README.md，推荐使用统一配置
- 在各服务文档中添加配置使用说明
- 创建配置迁移指南

---

## 📋 配置使用决策树

```
是否需要启动所有服务？
├── 是 → 使用 config/docker/docker-compose.yml
└── 否 → 需要哪些服务？
    ├── 仅数据库 → docker-compose.infrastructure.yml
    ├── 核心服务 → infrastructure + core-services
    ├── MCP服务 → infrastructure + core-services + mcp-servers
    ├── 应用服务 → infrastructure + core-services + applications
    └── 监控服务 → docker-compose.monitoring.yml (独立)
```

---

## 🔍 故障排查

### 端口冲突

```bash
# 检查端口占用
lsof -i :<port>

# 修改端口 (在.env文件中配置)
SERVICE_PORT=<new_port>
```

### 网络问题

```bash
# 查看网络列表
docker network ls

# 清理未使用的网络
docker network prune
```

### 服务启动失败

```bash
# 查看详细日志
docker-compose logs [service_name]

# 检查服务健康状态
docker-compose ps
```

---

## 📚 相关文档

- [主README](../../../README.md)
- [部署指南](../../../DEPLOYMENT_GUIDE.md)
- [监控指南](../../../MONITORING_GUIDE.md)
- [端口配置](../ports.yaml)

---

## 🎯 最佳实践

1. **生产环境**: 始终使用 `config/docker/docker-compose.yml`
2. **开发环境**: 可使用各服务独立配置进行快速迭代
3. **测试环境**: 使用 `docker-compose.unified-databases.yml` 仅启动必要服务
4. **监控告警**: 始终启动监控层以获得完整可观测性

---

**文档版本**: v1.0
**最后更新**: 2026-01-24
**维护者**: Athena工作平台团队
