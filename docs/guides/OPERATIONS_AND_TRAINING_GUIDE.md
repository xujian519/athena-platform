# Athena专利执行平台运维和培训指南

**版本**: v5.0.0
**更新时间**: 2025-12-14
**目标读者**: 开发者、运维人员、系统管理员

---

## 📚 目录

1. [快速开始](#快速开始)
2. [开发者培训](#开发者培训)
3. [运维培训](#运维培训)
4. [故障排查](#故障排查)
5. [最佳实践](#最佳实践)
6. [FAQ](#faq)

---

## 🚀 快速开始

### 5分钟快速部署

\`\`\`bash
# 1. 克隆代码
git clone https://github.com/athena-platform/patent-platform.git
cd patent-platform

# 2. 启动所有服务（包括监控栈）
docker-compose up -d

# 3. 验证服务
curl http://localhost:8000/health

# 4. 访问监控
# Grafana: http://localhost:3000 (admin/athena123)
# Prometheus: http://localhost:9090
# Jaeger: http://localhost:16686
\`\`\`

---

## 👨‍💻 开发者培训

### 模块1：可观测性使用指南（30分钟）

#### 1.1 如何启用分布式追踪

**目标**: 学会使用OpenTelemetry追踪器

**步骤**:

1. **导入追踪器**
\`\`\`python
from shared.observability.tracing import get_tracer

tracer = get_tracer("your-service-name")
\`\`\`

2. **使用装饰器追踪函数**
\`\`\`python
@tracer.trace("operation_name")
async def your_function(param1, param2):
    # 业务逻辑
    # 自动创建Span、记录参数、记录异常、统计耗时
    return result
\`\`\`

3. **查看追踪结果**
- 打开Jaeger UI: http://localhost:16686
- 选择服务: your-service-name
- 查看Trace列表和详细调用链

#### 1.2 如何添加业务指标

**目标**: 学会定义和使用Prometheus指标

**步骤**:

1. **导入指标类**
\`\`\`python
from shared.observability.metrics import PrometheusCounter, PrometheusHistogram
\`\`\`

2. **创建指标**
\`\`\`python
# 创建计数器
request_counter = PrometheusCounter(
    "my_requests_total",
    "Total requests",
    labelnames=("method", "endpoint")
)

# 创建直方图
response_time = PrometheusHistogram(
    "my_response_time_seconds",
    "Response time",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
)
\`\`\`

3. **使用指标**
\`\`\`python
# 增加计数
request_counter.inc(method="GET", endpoint="/api/patents")

# 记录延迟
response_time.observe(1.2, method="GET", endpoint="/api/patents")
\`\`\`

4. **查看指标**
- 访问Prometheus: http://localhost:9090
- 输入查询: my_requests_total
- 或访问/metrics端点

#### 1.3 使用预定义业务指标

**目标**: 使用平台已定义的36个业务指标

**可用指标列表**:
- 专利执行指标（11个）
- LLM调用指标（5个）
- 缓存指标（4个）
- 数据库指标（3个）
- 可靠性指标（5个）
- 资源使用指标（4个）
- 业务价值指标（4个）

**使用示例**:
\`\`\`python
from shared.observability.metrics.business_metrics import get_business_metrics

# 获取业务指标实例
metrics = get_business_metrics()

# 使用指标
metrics.patent_analysis_total.labels(
    type="novelty",
    status="started"
).inc()

metrics.patent_analysis_duration_seconds.labels(
    type="novelty"
).observe(5.2)
\`\`\`

---

## 🔧 运维培训

### 模块2：监控系统使用（45分钟）

#### 2.1 Prometheus监控

**访问地址**: http://localhost:9090

**常用查询**:

1. **查看专利分析QPS**
\`\`\`promql
rate(patent_analysis_total[5m])
\`\`\`

2. **查看专利分析P95延迟**
\`\`\`promql
histogram_quantile(0.95, patent_analysis_duration_seconds_bucket)
\`\`\`

3. **查看缓存命中率**
\`\`\`promql
sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))
\`\`\`

4. **查看LLM成本趋势**
\`\`\`promql
sum(llm_cost_yuan) by (model)
\`\`\`

#### 2.2 Grafana仪表板

**访问地址**: http://localhost:3000
**登录账号**: admin / athena123

**仪表板说明**:

1. **Athena平台总览**
   - 位置: Home → Athena平台总览
   - 内容: 所有服务的健康状态、总体请求量、错误率、延迟
   - 刷新频率: 30秒

2. **专利执行专项**
   - 位置: Home → 专利执行专项
   - 内容: 专利分析详细指标、LLM监控、缓存性能、可靠性指标
   - 关键面板:
     - 今日处理专利数
     - 分析成功率
     - LLM调用量趋势
     - 缓存命中率对比
     - 重试统计、熔断器状态

#### 2.3 Jaeger分布式追踪

**访问地址**: http://localhost:16686

**使用方法**:

1. **查找Trace**
   - 选择服务: patent-service
   - 选择操作: analyze_patent
   - 点击Find Traces

2. **查看Trace详情**
   - 点击Trace ID
   - 查看调用链: 总耗时、每个Span的耗时
   - 查看Span详情: 标签、日志、错误

3. **分析性能瓶颈**
   - 找到耗时最长的Span
   - 查看该Span的详细信息
   - 分析日志和错误信息

---

## 🛠️ 部署指南

### 模块3：生产环境部署（60分钟）

#### 3.1 环境准备

**系统要求**:
- CPU: 4核+
- 内存: 16GB+
- 磁盘: 100GB+
- 操作系统: Linux (Ubuntu 20.04+ 或 CentOS 7+)

**软件依赖**:
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.12+

#### 3.2 配置环境变量

创建.env文件:
\`\`\`bash
# 应用配置
APP_NAME=athena-patent-platform
APP_VERSION=5.0.0
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql://athena:your_password@db:5432/athena_patents

# Redis配置
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_TTL=3600

# LLM配置
LLM_SERVICE_URL=http://llm-service:8002
LLM_TIMEOUT=30

# 可观测性配置
TELEMETRY_ENABLED=true
TELEMETRY_EXPORTER=jaeger
JAEGER_ENDPOINT=http://jaeger:14250/api/traces
\`\`\`

#### 3.3 启动服务

\`\`\`bash
# 拉取最新镜像
docker-compose pull

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f patent-service
\`\`\`

#### 3.4 验证部署

\`\`\`bash
# 1. 检查健康状态
curl http://localhost:8000/health

# 2. 检查Prometheus指标
curl http://localhost:8000/metrics

# 3. 提交测试任务
curl -X POST http://localhost:8000/api/patents/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "patent_id": "CN123456789A",
    "analysis_type": "novelty"
  }'

# 4. 查看Grafana仪表板
open http://localhost:3000
\`\`\`

---

## 💾 备份和恢复

### 模块5：数据备份和恢复（45分钟）

#### 5.1 备份策略

**数据分类**:

1. **应用数据**（需要每日备份）
   - PostgreSQL数据库
   - Redis缓存数据
   - 专利分析结果

2. **配置数据**（需要版本控制）
   - 环境配置文件（.env）
   - Docker Compose配置
   - 监控配置（Prometheus、Grafana）

3. **监控数据**（短期保留）
   - Prometheus指标数据（保留30天）
   - Jaeger追踪数据（保留7天）

#### 5.2 自动备份脚本

**PostgreSQL备份**:

创建脚本 `scripts/backup_postgres.sh`:

\`\`\`bash
#!/bin/bash
# PostgreSQL备份脚本

BACKUP_DIR="/backup/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="athena_patents_${DATE}.sql.gz"

# 创建备份目录
mkdir -p ${BACKUP_DIR}

# 执行备份
docker exec athena-postgres pg_dump -U athena athena_patents | gzip > ${BACKUP_DIR}/${BACKUP_FILE}

# 删除30天前的备份
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete

# 记录日志
echo "$(date) - PostgreSQL备份完成: ${BACKUP_FILE}" >> /var/log/athena_backup.log
\`\`\`

**Redis备份**:

创建脚本 `scripts/backup_redis.sh`:

\`\`\`bash
#!/bin/bash
# Redis备份脚本

BACKUP_DIR="/backup/redis"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="redis_backup_${DATE}.rdb"

# 创建备份目录
mkdir -p ${BACKUP_DIR}

# 触发Redis保存
docker exec athena-redis redis-cli BGSAVE

# 等待保存完成
sleep 5

# 复制RDB文件
docker cp athena-redis:/data/dump.rdb ${BACKUP_DIR}/${BACKUP_FILE}

# 删除7天前的备份
find ${BACKUP_DIR} -name "*.rdb" -mtime +7 -delete

# 记录日志
echo "$(date) - Redis备份完成: ${BACKUP_FILE}" >> /var/log/athena_backup.log
\`\`\`

#### 5.3 定时备份配置

**配置Cron任务**:

\`\`\`bash
# 编辑crontab
crontab -e

# 添加以下任务
# 每天凌晨2点备份PostgreSQL
0 2 * * * /path/to/scripts/backup_postgres.sh

# 每天凌晨3点备份Redis
0 3 * * * /path/to/scripts/backup_redis.sh

# 每周日凌晨4点备份配置文件
0 4 * * 0 /path/to/scripts/backup_configs.sh
\`\`\`

#### 5.4 数据恢复

**PostgreSQL恢复**:

\`\`\`bash
# 1. 停止应用服务
docker-compose stop patent-service

# 2. 恢复数据库
gunzip < /backup/postgres/athena_patents_20251214_020000.sql.gz | \
  docker exec -i athena-postgres psql -U athena athena_patents

# 3. 重启应用服务
docker-compose start patent-service

# 4. 验证恢复
curl http://localhost:8000/health
\`\`\`

**Redis恢复**:

\`\`\`bash
# 1. 停止Redis
docker-compose stop redis

# 2. 复制备份文件
cp /backup/redis/redis_backup_20251214_030000.rdb /var/lib/redis/

# 3. 启动Redis
docker-compose start redis

# 4. 验证恢复
docker exec athena-redis redis-cli DBSIZE
\`\`\`

#### 5.5 灾难恢复演练

**恢复测试清单**:

- [ ] 每月进行一次恢复演练
- [ ] 记录恢复时间目标（RTO）
- [ ] 记录恢复点目标（RPO）
- [ ] 更新恢复文档

**恢复时间目标**:

| 数据类型 | RTO（恢复时间） | RPO（数据丢失） |
|---------|----------------|----------------|
| PostgreSQL | <1小时 | <1天 |
| Redis | <30分钟 | <1天 |
| 配置文件 | <15分钟 | 0 |

---

## 🔍 监控和告警

### 模块4：监控告警配置（30分钟）

#### 4.1 关键指标监控

**业务指标**:
- 专利分析成功率: >95%
- 专利分析P95延迟: <10s
- 缓存命中率: >40%
- LLM调用成功率: >99%

**系统指标**:
- CPU使用率: <80%
- 内存使用率: <85%
- 磁盘使用率: <80%
- 服务可用性: >99%

#### 4.2 告警规则配置

在Prometheus中配置告警:

1. 创建告警规则文件alert_rules.yml:
\`\`\`yaml
groups:
  - name: patent_platform_alerts
    rules:
      # 专利分析成功率告警
      - alert: LowSuccessRate
        expr: |
          rate(patent_analysis_total{status="completed"}[5m]) 
          / rate(patent_analysis_total[5m]) < 0.95
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "专利分析成功率低于95%"
          description: "成功率: {{ $value | humanizePercentage }}"

      # 专利分析延迟告警
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, patent_analysis_duration_seconds_bucket) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95延迟超过10秒"
          description: "P95延迟: {{ $value }}s"

      # LLM调用失败率告警
      - alert: HighLLMFailureRate
        expr: |
          rate(llm_requests_total{status="failure"}[5m]) 
          / rate(llm_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "LLM调用失败率超过5%"
\`\`\`

2. 在prometheus.yml中引用告警规则:
\`\`\`yaml
rule_files:
  - "alert_rules.yml"
\`\`\`

3. 重新加载Prometheus配置:
\`\`\`bash
docker-compose restart prometheus
\`\`\`

---

## 🆘 故障排查

### 常见问题诊断

#### 问题1: Redis连接失败

**症状**:
\`\`\`
Error: Error connecting to Redis
\`\`\`

**诊断步骤**:
\`\`\`bash
# 1. 检查Redis是否运行
docker ps | grep redis

# 2. 查看Redis日志
docker logs athena-redis

# 3. 测试连接
redis-cli -h localhost -p 6379 ping
# 应该返回: PONG
\`\`\`

**解决方案**:
\`\`\`bash
# 如果Redis未运行，启动它
docker-compose up -d redis

# 如果连接配置错误，检查.env文件
cat .env | grep REDIS_URL
\`\`\`

#### 问题2: Prometheus指标无法访问

**症状**:
\`\`\`
curl http://localhost:8000/metrics
# 返回404或连接被拒绝
\`\`\`

**诊断步骤**:
\`\`\`bash
# 1. 检查Prometheus是否运行
docker ps | grep prometheus

# 2. 检查服务是否暴露/metrics端点
curl http://localhost:8000/docs
# 查看API文档中是否有/metrics端点

# 3. 检查环境变量
docker exec patent-service env | grep TELEMETRY_ENABLED
\`\`\`

**解决方案**:
\`\`\`bash
# 确保TELEMETRY_ENABLED=true
docker-compose up -d patent-service

# 重启服务
docker-compose restart patent-service
\`\`\`

#### 问题3: Jaeger追踪数据为空

**症状**:
Jaeger UI中看不到任何Trace数据

**诊断步骤**:
\`\`\`bash
# 1. 检查环境变量
echo $TELEMETRY_EXPORTER  # 应该是"jaeger"
echo $JAEGER_ENDPOINT    # 应该是Jaeger服务地址

# 2. 检查Jaeger是否运行
docker ps | grep jaeger

# 3. 查看Jaeger日志
docker logs athena-jaeger

# 4. 测试Jaeger连接
curl http://localhost:16686/api/services
\`\`\`

**解决方案**:
\`\`\`bash
# 如果Jaeger未运行，启动它
docker-compose up -d jaeger

# 更新环境变量并重启服务
docker-compose up -d patent-service
\`\`\`

#### 问题4: 内存使用过高

**症状**:
内存使用率持续超过90%

**诊断步骤**:
\`\`\`bash
# 1. 查看内存使用
docker stats patent-service

# 2. 查看对象池状态
# 在代码中添加日志记录对象池大小

# 3. 分析内存泄漏
# 使用memory_profiler进行内存分析
\`\`\`

**解决方案**:
\`\`\`bash
# 1. 降低对象池大小
# 修改配置: OBJECT_POOL_MAX_SIZE=1000

# 2. 重启服务
docker-compose restart patent-service

# 3. 如果持续高内存，考虑扩容
# 增加容器内存限制
\`\`\`

---

## 📋 运维检查清单

### 日常检查（每天）

- [ ] 检查服务健康状态
- [ ] 查看关键指标（成功率、延迟、成本）
- [ ] 检查告警通知
- [ ] 查看日志错误

### 周检查（每周）

- [ ] 分析性能趋势
- [ ] 检查磁盘使用情况
- [ ] 清理旧日志文件
- [ ] 审查安全日志

### 月检查（每月）

- [ ] 性能基线评估
- [ ] 成本分析
- [ ] 容量规划
- [ ] 灾难恢复演练
- [ ] 安全审计

---

## 🎓 最佳实践

### 开发最佳实践

1. **使用追踪器**
   - 所有公开API都应该添加追踪
   - 使用描述性的操作名称
   - 记录关键业务参数

2. **定义指标**
   - 使用标准命名规范（单位后缀）
   - 提供清晰的描述
   - 合理使用标签（避免高基数）

3. **错误处理**
   - 记录所有异常到Span
   - 设置合理的重试策略
   - 使用熔断器保护依赖服务

### 运维最佳实践

1. **监控**
   - 监控关键业务指标
   - 设置合理的告警阈值
   - 定期审查告警规则

2. **部署**
   - 使用Docker Compose一键部署
   - 保持配置版本控制
   - 测试环境验证后再上生产

3. **备份**
   - 定期备份数据库
   - 备份配置文件
   - 测试恢复流程

---

## ❓ FAQ

### Q1: 如何添加新的追踪？

**A**:
\`\`\`python
from shared.observability.tracing import get_tracer

tracer = get_tracer("your-service")

@tracer.trace("new_operation")
async def new_function():
    pass
\`\`\`

### Q2: 如何创建自定义指标？

**A**:
\`\`\`python
from shared.observability.metrics import PrometheusCounter

custom_counter = PrometheusCounter(
    "custom_metric_total",
    "Custom metric description",
    labelnames=("label1", "label2")
)

custom_counter.labels(label1="value1", label2="value2").inc()
\`\`\`

### Q3: 如何查看实时日志？

**A**:
\`\`\`bash
# 查看实时日志
docker-compose logs -f patent-service

# 查看最近100行日志
docker-compose logs --tail=100 patent-service
\`\`\`

### Q4: 如何扩容服务？

**A**:
\`\`\`bash
# 增加服务实例数
docker-compose up -d --scale patent-service=3

# 增加资源限制
# 在docker-compose.yml中修改:
# deploy:
#   resources:
#     limits:
#       cpus: '2'
#       memory: 4G
\`\`\`

---

## 📞 技术支持

**文档**: https://docs.athena-platform.com
**GitHub**: https://github.com/athena-platform/patent-platform
**邮件支持**: athena-support@example.com

---

**指南版本**: v5.0.0
**最后更新**: 2025-12-14
**维护团队**: Athena AI系统
