# Athena 感知模块部署指南

## 使用现有基础设施：本地PostgreSQL 17.7 + Docker服务

**版本**: 1.0.0
**最后更新**: 2026-01-26
**作者**: Athena Platform Team

---

## 📋 目录

- [概述](#概述)
- [架构设计](#架构设计)
- [前置条件](#前置条件)
- [部署步骤](#部署步骤)
- [多智能体接入](#多智能体接入)
- [监控配置](#监控配置)
- [运维指南](#运维指南)
- [故障排查](#故障排查)

---

## 📖 概述

### 什么是感知模块？

Athena感知模块是**平台级多模态处理服务**，为所有智能体提供统一的感知能力：

- **图像处理**: OCR识别、场景识别、目标检测
- **音频处理**: 语音转文字、情感分析、说话人识别
- **视频处理**: 帧提取、内容分析、动作识别
- **多模态融合**: 跨模态语义理解和关联

### 模块定位

```
┌─────────────────────────────────────────────────────┐
│              智能体层 (Agents)                        │
├──────────┬──────────┬──────────┬────────────────────┤
│  Athena  │  小诺    │   小娜   │    其他智能体       │
│ 专利分析 │ 生活助理 │ 法律顾问 │    (自定义)         │
└────┬─────┴────┬─────┴────┬─────┴────────┬───────────┘
     │          │          │             │
     └──────────┴──────────┴─────────────┘
                        │
     ┌──────────────────┴──────────────────┐
     │      感知模块 (8070)                  │  ← 平台共用
     │  - 统一API接口                        │
     │  - 多模态处理能力                     │
     │  - 智能体隔离和权限控制               │
     └──────────────────┬──────────────────┘
                        │
     ┌──────────────────┴──────────────────┐
     │  PostgreSQL | Redis | Qdrant | Neo4j │
     └──────────────────────────────────────┘
```

### 核心特性

- ✅ **平台级服务**: 所有智能体共享使用
- ✅ **智能体隔离**: 按智能体ID隔离数据和权限
- ✅ **高性能**: 异步处理、三级缓存、批量处理
- ✅ **可观测**: 完善的监控、日志、追踪
- ✅ **高可用**: 健康检查、自动重启、降级策略

---

## 🏗️ 架构设计

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     感知模块 (8070)                      │
├─────────────────────────────────────────────────────────┤
│  API层 (FastAPI)                                        │
│  - /api/v1/perception/image                             │
│  - /api/v1/perception/ocr                               │
│  - /api/v1/perception/audio                             │
│  - /api/v1/perception/video                             │
├─────────────────────────────────────────────────────────┤
│  业务逻辑层                                              │
│  - 智能体认证和授权                                      │
│  - 请求路由和调度                                        │
│  - 结果聚合和缓存                                        │
├─────────────────────────────────────────────────────────┤
│  处理器层                                                │
│  - ImageProcessor (图像处理)                            │
│  - OCRProcessor (OCR识别)                               │
│  - AudioProcessor (音频处理)                            │
│  - VideoProcessor (视频处理)                            │
│  - MultimodalProcessor (多模态融合)                     │
├─────────────────────────────────────────────────────────┤
│  存储层                                                  │
│  - PostgreSQL 17.7 (本地) - 主数据库                   │
│  - Redis (Docker) - L1/L2缓存                           │
│  - Qdrant (Docker) - 向量搜索                           │
│  - Neo4j (Docker) - 知识图谱                            │
└─────────────────────────────────────────────────────────┘
```

### 数据流

```
智能体请求
    │
    ├─> API网关 (认证: X-Agent-ID)
    │       │
    │       ├─> 请求验证
    │       ├─> 智能体识别
    │       └─> 权限检查
    │
    ├─> 缓存层 (Redis)
    │       │
    │       ├─> L1: 内存缓存
    │       ├─> L2: Redis缓存
    │       └─> L3: 数据库缓存
    │
    ├─> 处理器层
    │       │
    │       ├─> 图像处理 (OpenCV, PIL)
    │       ├─> OCR识别 (Tesseract, PaddleOCR)
    │       ├─> 音频处理 (Whisper)
    │       └─> 视频处理 (FFmpeg)
    │
    ├─> 存储层
    │       │
    │       ├─> PostgreSQL (任务记录)
    │       ├─> Qdrant (向量搜索)
    │       └─> Neo4j (知识关联)
    │
    └─> 响应返回
```

---

## ✅ 前置条件

### 1. 系统要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Ubuntu 20.04+, macOS 11+ | Ubuntu 22.04 LTS |
| CPU | 2核心 | 4核心+ |
| 内存 | 4GB RAM | 8GB+ RAM |
| 磁盘 | 10GB 可用空间 | 50GB SSD |
| Python | 3.14+ | 3.14+ |

### 2. 必需软件

**本地PostgreSQL 17.7**:
```bash
# 检查版本
psql --version
# 输出: psql (PostgreSQL) 17.7

# 检查运行状态
pg_isready -h localhost -p 5432
# 输出: localhost:5432 - accepting connections
```

**Docker & Docker Compose**:
```bash
docker --version
docker-compose --version
```

### 3. Docker服务

确保以下Docker服务正在运行：

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

必需服务：
- ✅ athena-redis (Redis 7)
- ✅ athena_neo4j (Neo4j 5)
- ✅ athena-qdrant (Qdrant Latest)
- ✅ athena-prometheus (监控)
- ✅ athena-grafana (可视化)

启动服务（如果未运行）：
```bash
cd /Users/xujian/Athena工作平台
docker-compose -f config/docker/docker-compose.unified-databases.yml up -d
docker-compose -f config/docker/docker-compose.monitoring.yml up -d
```

### 4. 网络配置

确保以下Docker网络存在：
```bash
docker network ls | grep -E "unified-db-network|athena-network"
```

如果不存在，创建网络：
```bash
docker network create unified-db-network
docker network create athena-network
```

---

## 🚀 部署步骤

### 方式一：自动部署（推荐）

使用提供的自动化部署脚本：

```bash
cd /Users/xujian/Athena工作平台
./scripts/deployment/deploy_perception.sh
```

脚本将自动完成：
1. ✅ 环境检查（PostgreSQL、Docker、网络）
2. ✅ 数据库初始化
3. ✅ 环境变量配置
4. ✅ Docker镜像构建
5. ✅ 服务启动
6. ✅ 健康检查

### 方式二：手动部署

#### 步骤1：初始化数据库

```bash
# 连接到PostgreSQL
psql -h localhost -p 5432 -U $(whoami) -d postgres

# 执行初始化脚本
\i /Users/xujian/Athena工作平台/scripts/deployment/init_perception_db.sql
```

或使用命令行：
```bash
psql -h localhost -p 5432 -U $(whoami) -d postgres \
  -f /Users/xujian/Athena工作平台/scripts/deployment/init_perception_db.sql
```

#### 步骤2：配置环境变量

```bash
# 创建环境变量文件
cat > /Users/xujian/Athena工作平台/.env.perception << 'EOF'
# 数据库配置
DATABASE_URL=postgresql://athena_perception:athena_perception_secure_2024@host.docker.internal:5432/athena_perception

# Redis配置
REDIS_URL=redis://athena-redis:6379/1

# Qdrant配置
QDRANT_URL=http://athena-qdrant:6333

# Neo4j配置
NEO4J_URI=bolt://athena_neo4j:7687
NEO4J_PASSWORD=athena_neo4j_2024

# API配置
PERCEPTION_API_KEY=athena_perception_api_key_2024
EOF
```

#### 步骤3：构建Docker镜像

```bash
cd /Users/xujian/Athena工作平台
docker-compose -f config/docker/docker-compose.perception-module.yml build --no-cache
```

#### 步骤4：启动服务

```bash
docker-compose -f config/docker/docker-compose.perception-module.yml up -d
```

#### 步骤5：验证部署

```bash
# 健康检查
curl http://localhost:8070/health

# 预期输出：
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "timestamp": "2026-01-26T..."
# }
```

---

## 🤖 多智能体接入

### 支持的智能体

| 智能体 | ID | 用途 | 示例场景 |
|--------|-----|------|---------|
| Athena | `athena` | 专利分析 | 专利附图OCR、技术图像识别 |
| 小诺 | `xiaonuo` | 生活助理 | 食物识别、场景分类、证件识别 |
| 小娜 | `xiaona` | 法律顾问 | 法律文书OCR、合同条款提取 |
| 自定义 | 自定义ID | 自定义用途 | 按需扩展 |

### 接入方式

#### 1. HTTP API调用

```bash
# Athena智能体调用示例
curl -X POST http://localhost:8070/api/v1/perception/ocr \
  -H "X-Agent-ID: athena" \
  -H "Authorization: Bearer athena_perception_api_key_2024" \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "/data/patents/fig1.png",
    "language": "chinese"
  }'
```

#### 2. Python客户端

```python
import asyncio
from docs.perception_module_examples import PerceptionClient

async def main():
    # Athena智能体
    async with PerceptionClient(agent_id="athena") as client:
        result = await client.ocr_recognize(
            image_path="/data/patents/fig1.png",
            language="chinese"
        )
        print(result)

asyncio.run(main())
```

#### 3. 智能体配置

在智能体的配置文件中添加感知模块地址：

```yaml
# Athena配置
perception:
  base_url: http://localhost:8070
  agent_id: athena
  api_key: athena_perception_api_key_2024
  timeout: 30.0
  retry: 3

# 小诺配置
perception:
  base_url: http://localhost:8070
  agent_id: xiaonuo
  api_key: athena_perception_api_key_2024
  timeout: 30.0
  retry: 3
```

### 数据隔离

每个智能体的数据在数据库中完全隔离：

```sql
-- 查看Athena的任务
SELECT * FROM perception_tasks WHERE agent_id = 'athena';

-- 查看小诺的任务
SELECT * FROM perception_tasks WHERE agent_id = 'xiaonuo';

-- 智能体统计
SELECT agent_id, COUNT(*) as task_count
FROM perception_tasks
GROUP BY agent_id;
```

### 权限控制

```sql
-- 授予智能体访问权限
GRANT SELECT, INSERT, UPDATE, DELETE ON perception_tasks TO athena;
GRANT SELECT, INSERT, UPDATE, DELETE ON perception_tasks TO xiaonuo;
GRANT SELECT, INSERT, UPDATE, DELETE ON perception_tasks TO xiaona;
```

---

## 📊 监控配置

### Prometheus监控

#### 1. 配置Prometheus

将监控配置添加到Prometheus：

```bash
# 复制配置文件
cp /Users/xujian/Athena工作平台/config/monitoring/prometheus-perception.yml \
   /etc/prometheus/

# 添加告警规则
cp /Users/xujian/Athena工作平台/config/monitoring/perception-alerts.yml \
   /etc/prometheus/
```

#### 2. 更新Prometheus主配置

编辑 `/etc/prometheus/prometheus.yml`：

```yaml
# 在scrape_configs中添加
scrape_configs:
  - job_name: 'perception-service'
    static_configs:
      - targets: ['host.docker.internal:9070']
        labels:
          service: 'perception'

  - job_name: 'perception-exporter'
    static_configs:
      - targets: ['athena_perception_exporter:9121']
        labels:
          service: 'perception-exporter'

# 添加告警规则
rule_files:
  - 'perception-alerts.yml'
```

#### 3. 重新加载Prometheus

```bash
# 验证配置
promtool check config /etc/prometheus/prometheus.yml
promtool check rules /etc/prometheus/perception-alerts.yml

# 重新加载
kill -HUP $(pidof prometheus)
```

### Grafana仪表盘

#### 导入预配置仪表盘

1. 访问 Grafana: http://localhost:3000
2. 登录（默认: admin/admin）
3. 导入仪表盘：
   - 点击 "+" → "Import"
   - 上传仪表盘JSON文件
   - 选择Prometheus数据源

#### 关键指标

| 指标 | 描述 | 告警阈值 |
|------|------|---------|
| `perception_requests_total` | 总请求数 | - |
| `perception_request_duration_seconds` | 请求延迟 | P95 > 5秒 |
| `perception_cache_hit_rate` | 缓存命中率 | < 70% |
| `perception_cpu_usage` | CPU使用率 | > 80% |
| `perception_memory_usage` | 内存使用率 | > 80% |

### 告警配置

#### 告警级别

- **Critical**: 服务不可用，立即处理
- **Warning**: 性能下降，尽快处理
- **Info**: 信息性告警，建议关注

#### 告警规则示例

```yaml
# 服务不可用
- alert: PerceptionServiceDown
  expr: up{job="perception-service"} == 0
  for: 1m
  labels:
    severity: critical

# 高错误率
- alert: PerceptionHighErrorRate
  expr: rate(perception_errors_total[5m]) > 0.05
  for: 5m
  labels:
    severity: warning
```

---

## 🔧 运维指南

### 日常操作

#### 查看服务状态

```bash
# 查看容器状态
docker-compose -f config/docker/docker-compose.perception-module.yml ps

# 查看日志
docker-compose -f config/docker/docker-compose.perception-module.yml logs -f perception-service

# 查看实时日志（最近100行）
docker logs --tail 100 -f athena_perception_service
```

#### 服务管理

```bash
# 启动服务
docker-compose -f config/docker/docker-compose.perception-module.yml up -d

# 停止服务
docker-compose -f config/docker/docker-compose.perception-module.yml down

# 重启服务
docker-compose -f config/docker/docker-compose.perception-module.yml restart

# 重新构建并启动
docker-compose -f config/docker/docker-compose.perception-module.yml up -d --build
```

#### 性能调优

```bash
# 查看资源使用
docker stats athena_perception_service

# 进入容器
docker exec -it athena_perception_service bash

# 查看进程
docker exec athena_perception_service ps aux
```

### 数据库维护

#### 清理过期缓存

```sql
-- 查看过期缓存数量
SELECT COUNT(*) FROM perception_cache WHERE expires_at < NOW();

-- 清理过期缓存
SELECT cleanup_expired_cache();

-- 或使用SQL直接删除
DELETE FROM perception_cache WHERE expires_at < NOW();
```

#### 性能分析

```sql
-- 查看慢查询
SELECT
    agent_id,
    task_type,
    AVG(processing_time) as avg_time,
    MAX(processing_time) as max_time,
    COUNT(*) as count
FROM perception_metrics
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY agent_id, task_type
ORDER BY avg_time DESC;
```

#### 数据备份

```bash
# 备份感知模块数据库
pg_dump -h localhost -p 5432 -U athena_perception athena_perception \
  > backup_perception_$(date +%Y%m%d).sql

# 恢复数据库
psql -h localhost -p 5432 -U athena_perception athena_perception \
  < backup_perception_20260126.sql
```

### 日志管理

#### 日志位置

```bash
# 容器内日志
/app/logs/perception/

# 宿主机映射日志
/Users/xujian/Athena工作平台/logs/perception/
```

#### 日志轮转

```python
# 在日志配置中启用轮转
LOG_ROTATION=true
LOG_MAX_BYTES=104857600  # 100MB
LOG_BACKUP_COUNT=10
```

#### 查看日志

```bash
# 查看所有日志
tail -f /Users/xujian/Athena工作平台/logs/perception/*.log

# 搜索错误日志
grep -i "error" /Users/xujian/Athena工作平台/logs/perception/*.log

# 统计错误数量
grep -c "ERROR" /Users/xujian/Athena工作平台/logs/perception/*.log
```

---

## 🔍 故障排查

### 常见问题

#### 1. 服务无法启动

**现象**:
```bash
docker-compose -f config/docker/docker-compose.perception-module.yml up -d
# 容器启动后立即退出
```

**排查步骤**:

```bash
# 查看容器日志
docker logs athena_perception_service

# 常见原因：
# 1. PostgreSQL未启动
pg_isready -h localhost -p 5432

# 2. 数据库未初始化
psql -h localhost -p 5432 -U athena_perception -d athena_perception

# 3. 端口被占用
lsof -i :8070
```

**解决方案**:
```bash
# 确保PostgreSQL运行
brew services start postgresql

# 初始化数据库
psql -f scripts/deployment/init_perception_db.sql

# 释放端口
kill -9 $(lsof -ti :8070)
```

#### 2. 健康检查失败

**现象**:
```bash
curl http://localhost:8070/health
# curl: (7) Failed to connect
```

**排查步骤**:

```bash
# 检查容器状态
docker ps | grep perception

# 检查端口映射
docker port athena_perception_service

# 检查网络连接
docker exec athena_perception_service curl http://localhost:8000/health
```

**解决方案**:
```bash
# 重启服务
docker-compose -f config/docker/docker-compose.perception-module.yml restart

# 检查防火墙
sudo ufw status
sudo ufw allow 8070/tcp
```

#### 3. 数据库连接失败

**现象**:
```
DatabaseError: connection to host.docker.internal:5432 failed
```

**排查步骤**:

```bash
# 测试PostgreSQL连接
psql -h localhost -p 5432 -U athena_perception -d athena_perception

# 检查extra_hosts配置
docker exec athena_perception_service ping host.docker.internal
```

**解决方案**:
```bash
# 确保extra_hosts配置正确
# 在docker-compose.yml中：
extra_hosts:
  - "host.docker.internal:host-gateway"

# 测试容器内连接
docker exec athena_perception_service \
  psql -h host.docker.internal -U athena_perception -d athena_perception
```

#### 4. OCR识别失败

**现象**:
```json
{
  "status": "error",
  "message": "Tesseract not found"
}
```

**排查步骤**:

```bash
# 检查Tesseract安装
docker exec athena_perception_service tesseract --version

# 检查语言包
docker exec athena_perception_service tesseract --list-langs
```

**解决方案**:
```bash
# 重新构建镜像，确保包含Tesseract
docker-compose -f config/docker/docker-compose.perception-module.yml build --no-cache

# 或在Dockerfile中添加：
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    tesseract-ocr-eng
```

#### 5. 性能问题

**现象**:
- 请求响应慢
- CPU/内存使用率高

**排查步骤**:

```bash
# 查看资源使用
docker stats athena_perception_service

# 查看慢查询
psql -c "
SELECT agent_id, AVG(processing_time) as avg_time
FROM perception_metrics
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY agent_id
ORDER BY avg_time DESC
LIMIT 10;
"
```

**解决方案**:

```yaml
# 调整资源配置
deploy:
  resources:
    limits:
      cpus: '8.0'
      memory: 16G
    reservations:
      cpus: '4.0'
      memory: 8G

# 调整并发配置
environment:
  - MAX_CONCURRENT_REQUESTS=500
  - WORKER_PROCESSES=8
```

### 诊断工具

#### 健康检查脚本

```bash
#!/bin/bash
# health_check.sh

echo "=== 感知模块健康检查 ==="

# 1. 服务状态
echo -n "1. 服务状态: "
curl -s http://localhost:8070/health | jq -r '.status'

# 2. 数据库连接
echo -n "2. 数据库连接: "
pg_isready -h localhost -p 5432 && echo "✓" || echo "✗"

# 3. Redis连接
echo -n "3. Redis连接: "
docker exec athena_perception_service redis-cli -h athena-redis ping

# 4. 容器状态
echo "4. 容器状态:"
docker ps | grep perception

# 5. 资源使用
echo "5. 资源使用:"
docker stats --no-stream athena_perception_service
```

#### 性能测试脚本

```bash
#!/bin/bash
# performance_test.sh

echo "=== 感知模块性能测试 ==="

# 并发测试
for i in {1..10}; do
  curl -X POST http://localhost:8070/api/v1/perception/ocr \
    -H "X-Agent-ID: test" \
    -H "Content-Type: application/json" \
    -d '{"image_path": "/test/image.png"}' &
done

wait
echo "测试完成"
```

---

## 📚 附录

### A. 端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| 感知模块API | 8070 | HTTP API |
| Prometheus指标 | 9070 | 监控指标 |
| Exporter | 9122 | Redis Exporter |

### B. 环境变量参考

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DATABASE_URL` | - | PostgreSQL连接字符串 |
| `REDIS_URL` | redis://athena-redis:6379/1 | Redis连接字符串 |
| `QDRANT_URL` | http://athena-qdrant:6333 | Qdrant地址 |
| `NEO4J_URI` | bolt://athena_neo4j:7687 | Neo4j地址 |
| `MAX_CONCURRENT_REQUESTS` | 200 | 最大并发请求数 |
| `BATCH_SIZE` | 100 | 批处理大小 |
| `CACHE_TTL` | 7200 | 缓存过期时间（秒） |
| `LOG_LEVEL` | INFO | 日志级别 |

### C. 相关文档

- [Athena平台架构文档](../README.md)
- [Docker配置指南](../../config/docker/README.md)
- [监控配置指南](../../config/monitoring/README.md)
- [智能体开发指南](../AGENT_DEVELOPMENT.md)

### D. 支持和反馈

- **问题反馈**: [GitHub Issues](https://github.com/athena-platform/perception-module/issues)
- **技术支持**: athena-support@example.com
- **文档更新**: 2026-01-26

---

**文档版本**: 1.0.0
**最后更新**: 2026-01-26
**维护者**: Athena Platform Team
