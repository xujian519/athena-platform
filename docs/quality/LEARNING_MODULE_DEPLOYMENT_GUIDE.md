# 学习与适应模块部署指南
# Learning & Adaptation Module Deployment Guide

**版本**: 1.0.0
**更新时间**: 2026-01-24
**作者**: Athena平台团队

---

## 📋 目录

1. [概述](#概述)
2. [部署前检查](#部署前检查)
3. [环境配置](#环境配置)
4. [部署步骤](#部署步骤)
5. [验证和测试](#验证和测试)
6. [监控和告警](#监控和告警)
7. [故障排查](#故障排查)
8. [维护操作](#维护操作)

---

## 📖 概述

学习与适应模块是Athena工作平台的核心智能组件，提供以下功能：

- **监督学习**: 从标注数据中学习模式
- **在线学习**: 持续学习和灾难遗忘防护
- **强化学习**: 基于用户反馈优化决策
- **元学习**: 快速适应新任务
- **知识蒸馏**: 模型压缩和知识转移

### 架构特点

- **类型安全**: 100% pyright类型检查通过
- **异步架构**: 高并发处理能力
- **RESTful API**: 标准化的API接口
- **可观测性**: 完善的日志和监控
- **容错性**: 优雅的错误处理

---

## ✅ 部署前检查

### 系统要求

| 资源 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 4核 | 8核+ |
| 内存 | 8GB | 16GB+ |
| 存储 | 50GB | 100GB+ |
| Python | 3.14+ | 3.14+ |

### 依赖服务

- ✅ PostgreSQL 15+ (主数据库)
- ✅ Redis 7.0+ (缓存)
- ✅ Qdrant (向量数据库)
- ✅ Prometheus + Grafana (监控)

### 配置文件检查

```bash
# 检查配置文件
config/learning_config.yaml

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件填写实际配置
```

---

## 🔧 环境配置

### 1. 环境变量设置

创建 `.env` 文件：

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=athena
DB_USER=athena
DB_PASSWORD=your_secure_password

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Qdrant配置
QDRANT_HOST=localhost
QDRANT_PORT=6333

# API配置
API_HOST=0.0.0.0
API_PORT=8000
JWT_SECRET=your-jwt-secret-key

# 监控配置
PROMETHEUS_PORT=9090
ALERT_WEBHOOK_URL=https://your-webhook-url

# 备份配置
BACKUP_PATH=s3://athena-backups/learning
MLFLOW_TRACKING_URI=http://localhost:5000
```

### 2. 配置文件调整

根据部署环境调整 `config/learning_config.yaml`：

```yaml
module:
  environment: "production"  # development | staging | production
  debug: false
  log_level: "INFO"

api:
  workers: 8  # 根据CPU核心数调整
  cors_origins: ["https://your-domain.com"]  # 限制CORS源
```

---

## 🚀 部署步骤

### 方式一：Docker Compose部署（推荐）

```bash
# 1. 启动依赖服务
docker-compose -f config/docker/docker-compose.unified-databases.yml up -d

# 2. 构建并启动学习模块
docker-compose -f config/docker/docker-compose.learning-module.yml up -d

# 3. 查看日志
docker-compose -f config/docker/docker-compose.learning-module.yml logs -f

# 4. 健康检查
curl http://localhost:8000/api/v1/learning/health
```

### 方式二：直接部署

```bash
# 1. 安装依赖
poetry install

# 2. 初始化数据库
python scripts/init_db.py

# 3. 启动API服务
uvicorn core.learning.api:app --host 0.0.0.0 --port 8000 --workers 4

# 4. 启动监控服务
python core/learning/rl_monitoring.py &
```

### 方式三：Kubernetes部署

```bash
# 1. 创建ConfigMap
kubectl create configmap learning-config \
  --from-file=config/learning_config.yaml

# 2. 创建Secret
kubectl create secret generic learning-secrets \
  --from-env-file=.env

# 3. 部署
kubectl apply -f infrastructure/k8s/learning-module/

# 4. 验证
kubectl get pods -l app=learning-module
kubectl port-forward svc/learning-module 8000:8000
```

---

## 🧪 验证和测试

### 1. 健康检查

```bash
# 基本健康检查
curl http://localhost:8000/api/v1/learning/health

# 预期响应
{
  "status": "healthy",
  "timestamp": "2026-01-24T10:00:00",
  "module": "learning"
}
```

### 2. API测试

```bash
# 测试学习端点
curl -X POST http://localhost:8000/api/v1/learning/learn \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "supervised",
    "data": [{"input": "test", "output": "result"}]
  }'

# 测试统计端点
curl http://localhost:8000/api/v1/learning/statistics

# 测试RL交互端点
curl -X POST http://localhost:8000/api/v1/learning/rl/interaction \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "测试查询",
    "agent_response": "测试响应",
    "capability_used": "search"
  }'
```

### 3. 集成测试

```bash
# 运行集成测试套件
pytest tests/integration/learning/ -v

# 预期输出：所有测试通过
# tests/integration/learning/test_learning_api.py::TestLearningAPI::test_root_endpoint PASSED
# tests/integration/learning/test_learning_api.py::TestLearningAPI::test_health_check PASSED
# ...
```

### 4. 性能测试

```bash
# 运行负载测试
locust -f tests/performance/learning_load_test.py --host=http://localhost:8000

# 检查结果：
# - 请求成功率 > 99%
# - P95响应时间 < 200ms
# - 无内存泄漏
```

---

## 📊 监控和告警

### Prometheus指标

访问 `http://localhost:9090/metrics` 查看以下指标：

```promql
# 学习任务总数
learning_tasks_total

# 学习任务成功率
learning_tasks_success_rate

# 平均学习时间
learning_task_duration_seconds

# RL交互统计
rl_interactions_total
rl_rewards_mean

# 资源使用
learning_memory_usage_bytes
learning_cpu_usage_percent
```

### Grafana仪表板

导入仪表板：`infrastructure/monitoring/grafana/dashboards/learning-module.json`

关键监控面板：
1. **学习任务**: 任务数、成功率、平均时长
2. **强化学习**: 交互数、奖励分布、探索率
3. **系统资源**: CPU、内存、磁盘使用
4. **API性能**: 请求速率、响应时间、错误率

### 告警规则

配置告警规则：`infrastructure/monitoring/prometheus/alerts/learning-alerts.yml`

```yaml
groups:
  - name: learning_module_alerts
    rules:
      - alert: HighErrorRate
        expr: learning_error_rate > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "学习模块错误率过高"

      - alert: HighMemoryUsage
        expr: learning_memory_usage_percent > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
```

---

## 🔍 故障排查

### 常见问题

#### 问题1：API无法启动

**症状**：`uvicorn` 启动失败

**排查步骤**：
```bash
# 检查端口占用
lsof -i :8000

# 检查配置文件
python -c "import yaml; yaml.safe_load(open('config/learning_config.yaml'))"

# 查看详细日志
uvicorn core.learning.api:app --log-level debug
```

**解决方案**：
- 释放占用端口或更换端口
- 修复配置文件语法错误
- 检查依赖是否完整安装

#### 问题2：数据库连接失败

**症状**：`psycopg2.OperationalError`

**排查步骤**：
```bash
# 测试数据库连接
psql -h localhost -U athena -d athena

# 检查连接池状态
curl http://localhost:8000/api/v1/learning/health
```

**解决方案**：
- 确认PostgreSQL服务运行
- 检查连接字符串配置
- 验证用户权限

#### 问题3：内存持续增长

**症状**：内存使用率持续上升

**排查步骤**：
```bash
# 监控内存使用
watch -n 5 'ps aux | grep python | grep learning'

# 检查对象引用
import gc
print(gc.get_count())
print(gc.get_stats())
```

**解决方案**：
- 调整experience_replay缓冲区大小
- 启用定期模型清理
- 重启服务

#### 问题4：学习任务超时

**症状**：学习任务执行时间过长

**排查步骤**：
```bash
# 查看任务日志
tail -f logs/learning.log | grep "task_id"

# 检查数据大小
du -sh data/learning/*
```

**解决方案**：
- 减小batch_size
- 增加timeout配置
- 优化数据加载

---

## 🔧 维护操作

### 日常维护

#### 每日检查清单

- [ ] 检查服务健康状态
- [ ] 查看错误日志
- [ ] 验证备份完成
- [ ] 检查资源使用

#### 每周维护

- [ ] 分析性能指标
- [ ] 清理过期日志
- [ ] 检查模型版本
- [ ] 审查安全日志

#### 每月维护

- [ ] 更新依赖版本
- [ ] 审查和优化配置
- [ ] 进行容量规划
- [ ] 执行灾难恢复演练

### 模型管理

#### 保存模型

```bash
curl -X POST http://localhost:8000/api/v1/learning/models/save \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "production_model_v1",
    "description": "Production model version 1"
  }'
```

#### 加载模型

```bash
curl -X POST http://localhost:8000/api/v1/learning/models/load \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "production_model_v1"
  }'
```

#### 模型版本管理

```bash
# 列出所有模型
curl http://localhost:8000/api/v1/learning/models

# 删除旧模型
curl -X DELETE http://localhost:8000/api/v1/learning/models/old_model_id
```

### 数据备份

#### 手动备份

```bash
# 备份模型
python scripts/backup_learning_data.py --type models

# 备份经验缓冲区
python scripts/backup_learning_data.py --type experience_buffers

# 完整备份
python scripts/backup_learning_data.py --type all
```

#### 恢复数据

```bash
# 恢复模型
python scripts/restore_learning_data.py --type models \
  --backup_path backups/learning/models_20260124.tar.gz

# 恢复经验缓冲区
python scripts/restore_learning_data.py --type experience_buffers \
  --backup_path backups/learning/buffers_20260124.tar.gz
```

### 性能调优

#### 缓存优化

```yaml
# config/learning_config.yaml
database:
  redis:
    max_connections: 100  # 增加连接池
    socket_timeout: 2     # 减少超时时间
```

#### 学习参数调优

```yaml
learning_engine:
  parameters:
    batch_size: 64        # 增大批次
    learning_rate: 0.01   # 调整学习率
```

---

## 📈 扩容指南

### 水平扩展

```bash
# 启动多个实例
docker-compose up -d --scale learning-module=4

# 配置负载均衡
# 在nginx或HAProxy中配置：
upstream learning_backend {
    server learning-module-1:8000;
    server learning-module-2:8000;
    server learning-module-3:8000;
    server learning-module-4:8000;
}
```

### 垂直扩展

```yaml
# 增加资源限制
resources:
  memory:
    max_allocation: 4294967296  # 4GB
  cpu:
    max_workers: 8
```

---

## 🔐 安全加固

### 安全检查清单

- [ ] 启用HTTPS/TLS
- [ ] 配置防火墙规则
- [ ] 启用请求认证
- [ ] 设置CORS策略
- [ ] 启用输入验证
- [ ] 配置速率限制
- [ ] 启用审计日志
- [ ] 定期安全扫描

### SSL/TLS配置

```nginx
# nginx配置示例
server {
    listen 443 ssl http2;
    server_name learning.yourdomain.com;

    ssl_certificate /etc/ssl/certs/learning.crt;
    ssl_certificate_key /etc/ssl/private/learning.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://learning_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📞 支持和联系

### 获取帮助

- **文档**: https://docs.athena.ai/learning
- **Issues**: https://github.com/athena/learning-module/issues
- **Email**: support@athena.ai
- **Slack**: #learning-module-help

### 报告问题

报告问题时请提供：

1. 环境信息（OS、Python版本）
2. 错误日志
3. 配置文件（敏感信息已遮蔽）
4. 复现步骤
5. 预期行为 vs 实际行为

---

## 📚 附录

### A. 端口列表

| 服务 | 端口 | 用途 |
|------|------|------|
| API | 8000 | REST API服务 |
| Prometheus | 9090 | 指标收集 |
| Grafana | 3000 | 可视化面板 |
| PostgreSQL | 5432 | 主数据库 |
| Redis | 6379 | 缓存 |
| Qdrant | 6333 | 向量数据库 |

### B. 文件结构

```
learning-module/
├── config/
│   └── learning_config.yaml      # 主配置文件
├── core/learning/
│   ├── api.py                     # API路由
│   ├── learning_engine.py         # 学习引擎
│   ├── online_learning.py         # 在线学习
│   └── ...
├── data/learning/
│   ├── models/                    # 模型存储
│   ├── buffers/                   # 经验缓冲区
│   └── statistics/                # 统计数据
├── logs/
│   └── learning.log               # 学习日志
├── tests/
│   └── integration/learning/      # 集成测试
└── scripts/
    ├── init_db.py                 # 数据库初始化
    ├── backup_learning_data.py    # 备份脚本
    └── restore_learning_data.py   # 恢复脚本
```

### C. 性能基准

| 指标 | 目标值 |
|------|--------|
| API响应时间 (P95) | < 200ms |
| 学习任务成功率 | > 99% |
| 内存使用 | < 2GB |
| CPU使用 | < 80% |
| 错误率 | < 1% |

---

**文档版本**: 1.0.0
**最后更新**: 2026-01-24
