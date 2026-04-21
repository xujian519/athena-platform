# 统一日志和监控系统使用指南

> **最后更新**: 2026-04-22
> **作者**: Claude Code (OMC模式)

---

## 📋 目录

1. [快速开始](#快速开始)
2. [日志系统使用](#日志系统使用)
3. [监控系统使用](#监控系统使用)
4. [部署指南](#部署指南)
5. [故障排除](#故障排除)
6. [最佳实践](#最佳实践)

---

## 快速开始

### 启动监控服务

```bash
# 启动Prometheus和Grafana
docker-compose -f docker-compose.unified.yml --profile monitoring up -d

# 检查服务状态
docker ps --filter "name=athena-prometheus" --filter "name=athena-grafana"
```

### 访问服务

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3005 (admin/admin123)

### 测试日志系统

```python
from core.logging import get_logger, LogLevel

# 获取logger
logger = get_logger("my_service", level=LogLevel.INFO)

# 记录日志
logger.info("服务启动")
logger.add_context("request_id", "req-001")
logger.info("处理请求")
logger.error("发生错误")
```

---

## 日志系统使用

### 基础用法

#### 1. 获取Logger

```python
from core.logging import get_logger, LogLevel

# 方法1: 使用默认级别
logger = get_logger("my_service")

# 方法2: 指定日志级别
logger = get_logger("my_service", level=LogLevel.DEBUG)
```

#### 2. 记录日志

```python
# 5个日志级别
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

#### 3. 添加上下文

```python
# 添加单个上下文
logger.add_context("request_id", "req-001")
logger.add_context("user_id", "user-123")

# 清除上下文
logger.clear_context()
```

#### 4. 带额外字段的日志

```python
logger.info("任务完成", extra={
    "duration_ms": 1234,
    "task_type": "patent_analysis"
})
```

### 高级用法

#### 1. 文件日志（自动轮转+压缩）

```python
from core.logging import get_logger, RotatingFileHandler

logger = get_logger("file_service")

# 添加文件处理器
file_handler = RotatingFileHandler(
    filename="logs/app.log",
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,
    compress=True  # gzip压缩
)
logger.add_handler(file_handler)
```

#### 2. 异步日志（非阻塞）

```python
from core.logging import get_logger, AsyncLogHandler
import logging

logger = get_logger("async_service")

# 创建底层handler
stream_handler = logging.StreamHandler()

# 包装为异步handler
async_handler = AsyncLogHandler(
    handler=stream_handler,
    capacity=1000,
    batch_size=10
)
logger.add_handler(async_handler)
```

#### 3. 敏感信息过滤

```python
from core.logging import get_logger, SensitiveDataFilter

logger = get_logger("secure_service")

# 添加敏感信息过滤器
sensitive_filter = SensitiveDataFilter(
    mask_char="*",
    mask_ratio=0.5
)
logger.add_filter(sensitive_filter)

# 记录包含敏感信息的日志
logger.info("用户登录", extra={
    "phone": "13800138000",      # 自动脱敏为 138****8000
    "email": "test@example.com",  # 自动脱敏为 t***@example.com
    "token": "sk-12345"           # 自动脱敏为 [REDACTED]
})
```

#### 4. 基于YAML配置

```python
from core.logging.config import LoggingConfigLoader

# 从配置文件创建logger
logger = LoggingConfigLoader.create_logger(
    service_name="xiaona",
    config_path="config/base/logging.yml"
)
```

### 日志格式

#### JSON格式（机器可读）

```json
{
  "timestamp": "2026-04-22T10:00:00Z",
  "level": "INFO",
  "service": "xiaona",
  "module": "patent_analysis",
  "function": "analyze",
  "line": 42,
  "message": "专利分析完成",
  "context": {
    "request_id": "req-001",
    "user_id": "user-123"
  },
  "extra": {
    "duration_ms": 1234
  }
}
```

#### Text格式（人类可读）

```
2026-04-22 10:00:00 - xiaona - INFO - 专利分析完成
```

---

## 监控系统使用

### 指标采集

#### 1. 获取指标收集器

```python
from core.monitoring import get_metrics_collector

collector = get_metrics_collector("my_service")
```

#### 2. 记录HTTP请求

```python
collector.record_http_request(
    method="GET",
    endpoint="/api/patents",
    status=200,
    duration=0.123
)
```

#### 3. 记录服务任务

```python
collector.record_service_task(
    task_type="patent_analysis",
    status="success",
    duration=1.234
)
```

#### 4. 记录错误

```python
try:
    # 业务逻辑
    pass
except Exception as e:
    collector.record_error(f"{type(e).__name__}")
    raise
```

#### 5. 使用装饰器监控性能

```python
from core.monitoring import monitor_performance

collector = get_metrics_collector("my_service")

@monitor_performance(collector, "patent_analysis")
async def analyze_patent(patent_id: str):
    # 业务逻辑
    return result
```

### Prometheus指标

#### 可用指标

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `http_requests_total` | Counter | method, endpoint, status | HTTP请求总数 |
| `http_request_duration_seconds` | Histogram | method, endpoint | HTTP请求耗时 |
| `service_tasks_total` | Counter | service, status | 任务总数 |
| `service_task_duration_seconds` | Histogram | service, task_type | 任务耗时 |
| `service_errors_total` | Counter | service, error_type | 错误总数 |
| `llm_requests_total` | Counter | provider, model | LLM请求总数 |
| `llm_response_time_seconds` | Histogram | provider, model | LLM响应时间 |
| `cache_hits_total` | Counter | cache_type | 缓存命中数 |
| `cache_misses_total` | Counter | cache_type | 缓存未命中数 |

#### 查询示例

```promql
# HTTP请求率（QPS）
rate(http_requests_total[5m])

# HTTP响应时间P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 错误率
(rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])) * 100

# LLM响应时间
rate(llm_response_time_seconds_sum[5m]) / rate(llm_response_time_seconds_count[5m])

# 缓存命中率
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

### Grafana仪表板

#### 导入仪表板

1. 访问 http://localhost:3005
2. 登录（admin/admin123）
3. 导航到 Dashboards → Import
4. 上传 `config/grafana/dashboards/athena-system-overview.json`
5. 或输入仪表板ID: `athena-system-overview`

#### 可用仪表板

- **Athena系统概览**: 系统整体监控
  - HTTP请求率
  - CPU/内存使用率
  - 响应时间
  - 错误率

### 告警规则

#### 查看告警

1. 访问 http://localhost:9090
2. 导航到 Alerts
3. 查看活动告警

#### 配置告警规则

编辑 `config/prometheus/rules/service_alerts.yml`:

```yaml
groups:
  - name: service_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "服务错误率过高"
```

---

## 部署指南

### 环境要求

- Docker: 20.10+
- Docker Compose: 2.0+
- Python: 3.9+

### 部署步骤

#### 1. 启动基础设施

```bash
# 启动开发环境
docker-compose -f docker-compose.unified.yml --profile dev up -d

# 启动监控服务
docker-compose -f docker-compose.unified.yml --profile monitoring up -d
```

#### 2. 验证服务状态

```bash
# 检查容器状态
docker ps

# 检查Prometheus健康
curl http://localhost:9090/-/healthy

# 检查Grafana健康
curl http://localhost:3005/api/health
```

#### 3. 配置Grafana

1. 访问 http://localhost:3005
2. 首次登录时修改密码
3. Prometheus数据源已自动配置
4. 导入仪表板

### 生产环境部署

#### 1. 使用生产配置

```bash
# 启动生产环境
docker-compose -f docker-compose.unified.yml --profile prod up -d
```

#### 2. 配置日志

使用生产环境日志配置：

```python
from core.logging.config import LoggingConfigLoader

logger = LoggingConfigLoader.create_logger(
    service_name="xiaona",
    config_path="config/env/logging.production.yml"
)
```

#### 3. 配置持久化

```yaml
# docker-compose.unified.yml
volumes:
  prometheus-data:
    driver: local
  grafana-data:
    driver: local
```

---

## 故障排除

### 日志系统问题

#### 问题1: 日志没有输出

**原因**: Handler没有正确配置

**解决**:
```python
import logging

logger = get_logger("my_service")

# 添加控制台handler
console_handler = logging.StreamHandler()
logger.add_handler(console_handler)
```

#### 问题2: 日志文件过大

**原因**: 没有配置日志轮转

**解决**:
```python
from core.logging import RotatingFileHandler

file_handler = RotatingFileHandler(
    filename="logs/app.log",
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,
    compress=True
)
logger.add_handler(file_handler)
```

#### 问题3: 敏感信息泄露

**原因**: 没有配置敏感信息过滤器

**解决**:
```python
from core.logging import SensitiveDataFilter

sensitive_filter = SensitiveDataFilter()
logger.add_filter(sensitive_filter)
```

### 监控系统问题

#### 问题1: Prometheus无法抓取指标

**原因**: 服务未启动或端口不可达

**解决**:
```bash
# 检查服务状态
docker ps

# 检查网络连通性
docker network inspect athena-dev-network

# 查看Prometheus日志
docker logs athena-prometheus
```

#### 问题2: Grafana无法连接Prometheus

**原因**: 数据源配置错误

**解决**:
1. 访问 http://localhost:3005
2. 导航到 Configuration → Data Sources
3. 检查Prometheus数据源配置
4. URL应为 `http://prometheus:9090`

#### 问题3: 告警不触发

**原因**: 告警规则配置错误

**解决**:
```bash
# 检查告警规则
curl http://localhost:9090/api/v1/rules | python3 -m json.tool

# 测试告警查询
curl 'http://localhost:9090/api/v1/query?query=ALERTS' | python3 -m json.tool
```

### 性能问题

#### 问题1: 日志写入慢

**原因**: 同步写入阻塞主线程

**解决**: 使用异步日志处理器
```python
from core.logging import AsyncLogHandler

async_handler = AsyncLogHandler(
    handler=file_handler,
    capacity=2000
)
logger.add_handler(async_handler)
```

#### 问题2: 监控数据太多

**原因**: 指标采集频率过高

**解决**: 调整抓取间隔
```yaml
# prometheus.yml
global:
  scrape_interval: 30s  # 从15s增加到30s
```

---

## 最佳实践

### 日志系统

#### 1. 使用结构化日志

```python
# ❌ 不好
logger.info("用户123登录成功")

# ✅ 好
logger.info("用户登录成功", extra={
    "user_id": "123",
    "login_method": "password"
})
```

#### 2. 添加上下文信息

```python
# 在请求处理开始时添加上下文
logger.add_context("request_id", request.id)
logger.add_context("user_id", request.user_id)

# 之后的日志会自动包含这些上下文
logger.info("处理请求")
logger.info("查询数据库")
```

#### 3. 合理使用日志级别

```python
logger.debug("详细调试信息")  # 开发环境
logger.info("正常业务流程")   # 生产环境
logger.warning("警告但不影响运行")  # 需要注意
logger.error("错误但可恢复")      # 需要处理
logger.critical("严重错误，可能无法继续")  # 需要立即处理
```

#### 4. 避免记录敏感信息

```python
# ❌ 不好
logger.info(f"用户登录: {username}, 密码: {password}")

# ✅ 好（自动脱敏）
logger.info("用户登录", extra={
    "username": username,
    "password": password  # 会被自动脱敏为 [REDACTED]
})
```

### 监控系统

#### 1. 监控关键指标

```python
# HTTP请求监控
collector.record_http_request(
    method=request.method,
    endpoint=request.path,
    status=response.status_code,
    duration=duration
)

# 错误监控
try:
    # 业务逻辑
    pass
except Exception as e:
    collector.record_error(f"{type(e).__name__}")
    raise
```

#### 2. 使用性能装饰器

```python
@monitor_performance(collector, "patent_analysis")
async def analyze_patent(patent_id: str):
    # 自动记录任务计数和耗时
    result = await do_analysis(patent_id)
    return result
```

#### 3. 设置合理的告警阈值

```yaml
# ❌ 阈值过低（误报多）
- alert: HighErrorRate
  expr: error_rate > 0.001  # 0.1%

# ✅ 阈值合理
- alert: HighErrorRate
  expr: error_rate > 0.05  # 5%
  for: 5m  # 持续5分钟
```

#### 4. 定期清理历史数据

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

# 保留30天数据
storage.tsdb.retention.time: 30d
```

### 配置管理

#### 1. 环境分离

```bash
# 开发环境
config/env/logging.development.yml

# 测试环境
config/env/logging.test.yml

# 生产环境
config/env/logging.production.yml
```

#### 2. 服务特定配置

```yaml
# config/base/logging.yml
default:
  level: INFO

services:
  xiaona:
    level: DEBUG  # 小娜需要详细日志

  xiaonuo:
    level: INFO

  gateway:
    level: WARNING  # Gateway只需警告和错误
```

---

## 附录

### 相关文档

- `docs/guides/UNIFIED_LOGGING_ARCHITECTURE.md` - 日志架构设计
- `docs/guides/MONITORING_SYSTEM_ARCHITECTURE.md` - 监控架构设计
- `docs/reports/PHASE3_WEEK3_IMPLEMENTATION_COMPLETE_20260422.md` - 实施报告

### 代码示例

- `examples/logging_example.py` - 日志系统示例
- `examples/monitoring_example.py` - 监控系统示例
- `examples/logging_integration_example.py` - 集成示例

### 配置文件

- `config/base/logging.yml` - 基础日志配置
- `config/env/logging.*.yml` - 环境特定配置
- `config/docker/prometheus/prometheus.yml` - Prometheus配置
- `config/docker/prometheus/rules/service_alerts.yml` - 告警规则
- `config/docker/grafana/` - Grafana配置

---

**统一日志和监控系统使用指南完成！**

**最后更新**: 2026-04-22
**维护者**: Claude Code (OMC模式)
