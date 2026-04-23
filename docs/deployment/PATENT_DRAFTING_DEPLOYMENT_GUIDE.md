# PatentDraftingProxy部署指南

> **版本**: 1.0.0  
> **更新日期**: 2026-04-23  
> **维护者**: Athena Team

---

## 📋 目录

1. [概述](#概述)
2. [前置要求](#前置要求)
3. [快速开始](#快速开始)
4. [详细配置](#详细配置)
5. [部署流程](#部署流程)
6. [监控与告警](#监控与告警)
7. [故障排查](#故障排查)
8. [维护操作](#维护操作)
9. [安全最佳实践](#安全最佳实践)

---

## 概述

PatentDraftingProxy是Athena平台的专利撰写智能体服务，基于FastAPI和Docker构建，提供企业级的专利申请文件撰写能力。

### 核心特性

- ✅ **AI驱动的专利撰写**: 集成DeepSeek和本地LLM
- ✅ **多数据库支持**: PostgreSQL + Redis + Neo4j + Qdrant
- ✅ **知识库集成**: Obsidian知识库自动加载
- ✅ **完善的监控**: Prometheus + Grafana + Alertmanager
- ✅ **健康检查**: 多层次健康检查和自动恢复
- ✅ **容器化部署**: Docker Compose一键部署

---

## 前置要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 cores | 4+ cores |
| 内存 | 4 GB | 8+ GB |
| 磁盘 | 20 GB | 50+ GB SSD |
| 网络 | 10 Mbps | 100+ Mbps |

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 7+) / macOS 10.15+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.11+ (开发环境)

### API密钥要求

- **DeepSeek API**: 用于主要LLM调用
- **本地LLM**: 可选，用于降级

---

## 快速开始

### 1. 克隆代码仓库

```bash
git clone https://github.com/your-org/athena-platform.git
cd athena-platform
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.production.template .env.production

# 编辑环境变量文件
nano .env.production
```

**必须配置的变量**:

```bash
# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 数据库密码
POSTGRES_PASSWORD=your_secure_password_here
REDIS_PASSWORD=your_secure_password_here
NEO4J_PASSWORD=your_secure_password_here

# 知识库路径
KNOWLEDGE_BASE_PATH=/path/to/your/knowledge/base
```

### 3. 启动服务

```bash
# 方式1: 使用部署脚本(推荐)
bash scripts/deploy_patent_drafting.sh prod

# 方式2: 手动启动
docker-compose -f docker-compose.patent-drafting.yml --profile prod up -d
```

### 4. 验证部署

```bash
# 检查服务状态
bash scripts/status_patent_drafting.sh prod

# 健康检查
curl http://localhost:8010/health

# 查看日志
docker logs -f patent-drafting-api
```

### 5. 访问服务

- **主应用**: http://localhost:8010
- **API文档**: http://localhost:8010/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)

---

## 详细配置

### Docker Compose配置

`docker-compose.patent-drafting.yml` 包含以下服务:

| 服务名称 | 端口 | 描述 |
|---------|------|------|
| patent-drafting-api | 8010 | 主应用服务 |
| postgres | 5432 | PostgreSQL数据库 |
| redis | 6379 | Redis缓存 |
| neo4j | 7474, 7687 | Neo4j知识图谱 |
| qdrant | 6333, 6334 | Qdrant向量数据库 |
| prometheus | 9091 | Prometheus监控 |
| grafana | 3000 | Grafana可视化 |
| alertmanager | 9093 | Alertmanager告警 |

### 环境变量配置

详见 `config/patent_drafting_config.yaml` 和 `.env.production.template`。

主要配置项:

#### LLM配置
```yaml
llm:
  primary_model: "deepseek-chat"
  fallback_model: "local_8009"
  temperature: 0.7
  max_tokens: 4096
```

#### 数据库配置
```yaml
database:
  postgres:
    host: "localhost"
    port: 5432
    database: "athena"
    pool_size: 20
```

#### 监控配置
```yaml
monitoring:
  prometheus:
    enabled: true
    port: 9090
  health_check:
    enabled: true
    interval: 30
```

---

## 部署流程

### 完整部署流程

```bash
# 1. 检查系统环境
bash scripts/xiaonuo_system_checker.py

# 2. 备份现有部署(如适用)
bash scripts/backup_database.sh

# 3. 部署服务
bash scripts/deploy_patent_drafting.sh prod

# 4. 验证部署
bash scripts/status_patent_drafting.sh prod --verbose

# 5. 运行测试(可选)
pytest tests/agents/xiaona/test_patent_drafting_proxy.py -v
```

### CI/CD部署

使用GitHub Actions自动部署:

1. 配置GitHub Secrets:
   - `DEEPSEEK_API_KEY`
   - `SSH_PRIVATE_KEY`
   - `SERVER_HOST`
   - `SERVER_USER`

2. 推送代码触发部署:
```bash
git add .
git commit -m "feat: 新功能发布"
git push origin main
```

3. 查看部署状态:
```bash
gh run list
gh run view
```

---

## 监控与告警

### Prometheus监控

访问 http://localhost:9090 查看Prometheus指标。

**关键指标**:

- `http_requests_total`: HTTP请求总数
- `http_request_duration_seconds`: HTTP请求延迟
- `llm_calls_total`: LLM调用总数
- `llm_response_time_seconds`: LLM响应时间
- `task_queue_size`: 任务队列大小
- `cache_hits_total`: 缓存命中数

### Grafana仪表板

访问 http://localhost:3000 查看可视化仪表板。

**预配置仪表板**:

1. **服务概览**: 服务健康状态、请求量、错误率
2. **LLM性能**: LLM调用次数、响应时间、成本统计
3. **数据库性能**: 连接池使用、查询性能
4. **系统资源**: CPU、内存、磁盘使用率

### Alertmanager告警

告警规则定义在 `config/monitoring/rules/patent-drafting-alerts.yml`。

**主要告警**:

| 告警名称 | 严重级别 | 触发条件 |
|---------|---------|---------|
| ServiceDown | critical | 服务宕机超过1分钟 |
| HighErrorRate | critical | 5xx错误率超过5% |
| HighLLMFailureRate | warning | LLM失败率超过20% |
| HighResponseTime | warning | P95响应时间超过1秒 |
| HighMemoryUsage | warning | 内存使用率超过85% |

---

## 故障排查

### 常见问题

#### 1. 服务启动失败

**症状**: `docker-compose up` 失败

**解决方案**:
```bash
# 检查端口占用
lsof -i :8010
lsof -i :5432

# 检查Docker日志
docker-compose logs patent-drafting-api

# 检查环境变量
docker-compose config
```

#### 2. 数据库连接失败

**症状**: 日志显示"Database connection failed"

**解决方案**:
```bash
# 检查PostgreSQL容器状态
docker ps | grep postgres

# 进入PostgreSQL容器
docker exec -it patent-drafting-postgres psql -U athena -d athena

# 检查连接配置
docker exec patent-drafting-api env | grep POSTGRES
```

#### 3. LLM调用失败

**症状**: 日志显示"LLM call failed"

**解决方案**:
```bash
# 检查API密钥配置
docker exec patent-drafting-api env | grep DEEPSEEK

# 测试LLM连接
docker exec patent-drafting-api curl https://api.deepseek.com/v1/models

# 检查降级配置
docker logs patent-drafting-api | grep fallback
```

#### 4. 内存不足

**症状**: OOM (Out of Memory) 错误

**解决方案**:
```bash
# 增加Docker内存限制
# 编辑 docker-compose.patent-drafting.yml
deploy:
  resources:
    limits:
      memory: 8G

# 重启服务
docker-compose -f docker-compose.patent-drafting.yml restart
```

### 日志查看

```bash
# 实时查看主应用日志
docker logs -f patent-drafting-api

# 查看所有服务日志
docker-compose -f docker-compose.patent-drafting.yml logs -f

# 查看特定时间段日志
docker logs --since 1h patent-drafting-api

# 查看最近100行日志
docker logs --tail 100 patent-drafting-api
```

### 性能调优

#### 1. 数据库性能优化

```sql
-- PostgreSQL配置优化
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
-- 重启PostgreSQL
SELECT pg_reload_conf();
```

#### 2. Redis性能优化

```bash
# 修改Redis最大内存
# 编辑 docker-compose.patent-drafting.yml
command: >
  redis-server
  --maxmemory 1gb
  --maxmemory-policy allkeys-lru
```

#### 3. LLM调用优化

```yaml
# 启用缓存
llm:
  cache_enabled: true
  cache_ttl: 3600

# 调整并发
api:
  rate_limit:
    requests_per_minute: 120
```

---

## 维护操作

### 日常维护

#### 1. 备份数据库

```bash
# 备份PostgreSQL
docker exec patent-drafting-postgres pg_dump \
  -U athena -d athena > backup/postgres_$(date +%Y%m%d).sql

# 备份Redis
docker exec patent-drafting-redis redis-cli --rdb /data/backup_$(date +%Y%m%d).rdb

# 备份Neo4j
docker exec patent-drafting-neo4j neo4j-admin backup \
  --from=/data --backup-dir=/backups
```

#### 2. 清理日志

```bash
# 清理Docker日志
docker system prune -a

# 清理应用日志
find logs/ -name "*.log" -mtime +30 -delete
```

#### 3. 更新服务

```bash
# 拉取最新镜像
docker pull patent-drafting-proxy:latest

# 重新部署
bash scripts/deploy_patent_drafting.sh prod
```

### 回滚操作

```bash
# 回滚到上一个版本
bash scripts/rollback_patent_drafting.sh prod

# 恢复数据库备份
docker exec -i patent-drafting-postgres psql \
  -U athena -d athena < backup/postgres_20260422.sql
```

### 扩容操作

#### 1. 增加API实例

```bash
# 编辑 docker-compose.patent-drafting.yml
patent-drafting-api:
  deploy:
    replicas: 3

# 重新部署
docker-compose -f docker-compose.patent-drafting.yml up -d --scale patent-drafting-api=3
```

#### 2. 增加数据库资源

```yaml
# 编辑 docker-compose.patent-drafting.yml
postgres:
  deploy:
    resources:
      limits:
        memory: 4G
```

---

## 安全最佳实践

### 1. 网络安全

```yaml
# 限制暴露端口
ports:
  - "127.0.0.1:8010:8010"  # 仅本地访问

# 使用TLS
environment:
  - TLS_ENABLED=true
  - TLS_CERT_PATH=/certs/server.crt
  - TLS_KEY_PATH=/certs/server.key
```

### 2. 认证授权

```yaml
# 启用API认证
api:
  auth:
    enabled: true
    type: "bearer"
    secret_key: "${JWT_SECRET}"
```

### 3. 数据加密

```bash
# 加密敏感数据
docker secret create postgres_password .secrets/postgres_password.txt

# 使用加密卷
volumes:
  postgres-data:
    driver: local
    driver_opts:
      type: "crypt"
```

### 4. 访问控制

```bash
# 限制Docker访问
# 编辑 /etc/docker/daemon.json
{
  "iptables": false,
  "userland-proxy": false
}

# 使用非root用户运行容器
# 已在Dockerfile中配置
USER athena
```

### 5. 安全扫描

```bash
# 扫描镜像漏洞
docker scan patent-drafting-proxy:latest

# 运行安全测试
pytest tests/security/ -v
```

---

## 附录

### A. 端口映射表

| 内部端口 | 外部端口 | 协议 | 服务 |
|---------|---------|------|------|
| 8010 | 8010 | HTTP | 主应用 |
| 9090 | 9090 | HTTP | Prometheus指标 |
| 5432 | 5432 | TCP | PostgreSQL |
| 6379 | 6379 | TCP | Redis |
| 7474 | 7474 | HTTP | Neo4j Web |
| 7687 | 7687 | TCP | Neo4j Bolt |
| 6333 | 6333 | HTTP | Qdrant |
| 6334 | 6334 | gRPC | Qdrant |
| 3000 | 3000 | HTTP | Grafana |
| 9091 | 9091 | HTTP | Prometheus |
| 9093 | 9093 | HTTP | Alertmanager |

### B. 目录结构

```
.
├── config/
│   ├── patent_drafting_config.yaml    # 主配置文件
│   └── monitoring/                    # 监控配置
│       ├── prometheus.yml
│       ├── alertmanager.yml
│       └── rules/
├── scripts/
│   ├── deploy_patent_drafting.sh      # 部署脚本
│   ├── rollback_patent_drafting.sh    # 回滚脚本
│   └── status_patent_drafting.sh      # 状态脚本
├── docker-compose.patent-drafting.yml # Docker Compose配置
├── Dockerfile.patent-drafting         # Dockerfile
├── .env.production                    # 环境变量
├── logs/                              # 日志目录
└── backup/                            # 备份目录
```

### C. 常用命令速查

```bash
# 部署
bash scripts/deploy_patent_drafting.sh prod

# 查看状态
bash scripts/status_patent_drafting.sh prod

# 查看日志
docker logs -f patent-drafting-api

# 重启服务
docker-compose -f docker-compose.patent-drafting.yml restart

# 停止服务
docker-compose -f docker-compose.patent-drafting.yml down

# 备份数据
docker exec patent-drafting-postgres pg_dump -U athena athena > backup.sql

# 恢复数据
docker exec -i patent-drafting-postgres psql -U athena athena < backup.sql

# 进入容器
docker exec -it patent-drafting-api bash

# 查看资源使用
docker stats patent-drafting-api
```

---

## 获取帮助

如有问题，请联系:

- **Email**: support@athena.example.com
- **文档**: https://docs.athena.example.com
- **GitHub Issues**: https://github.com/your-org/athena-platform/issues

---

**最后更新**: 2026-04-23  
**文档版本**: 1.0.0
