# Athena工作平台可观测性基础设施

**版本**: v1.0.0
**创建时间**: 2025-12-14
**状态**: ✅ 生产就绪

---

## 📖 概述

Athena工作平台统一可观测性基础设施，为所有服务提供：
- **分布式追踪** (OpenTelemetry)
- **指标收集** (Prometheus)
- **可视化仪表板** (Grafana)
- **结构化日志** (JSON格式)

---

## 🎯 设计原则

### 1. 统一性
- 所有服务使用相同的追踪标准
- 统一的指标命名规范
- 一致的日志格式

### 2. 非侵入性
- 装饰器模式，最小化代码修改
- 自动上下文传播
- 零配置快速启动

### 3. 可扩展性
- 支持自定义指标
- 支持自定义Span属性
- 插件化架构

### 4. 性能优先
- 异步数据导出
- 批量处理
- 低开销（<5%性能影响）

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install opentelemetry-api opentelemetry-sdk prometheus-client aiohttp
```

### 2. 启用追踪（3行代码）

```python
from shared.observability.tracing import get_tracer
from shared.observability.metrics import get_metrics_registry

# 获取追踪器
tracer = get_tracer("your-service-name")

# 使用装饰器自动追踪
@tracer.trace("operation_name")
async def your_function():
    # 业务逻辑
    pass
```

### 3. 添加指标（2行代码）

```python
from shared.observability.metrics import Counter, Histogram

# 定义指标
request_counter = Counter("http_requests_total", "Total HTTP requests")
response_time = Histogram("http_response_time_seconds", "HTTP response time")

# 使用指标
request_counter.inc()
response_time.observe(0.5)
```

### 4. 启动监控栈

```bash
cd deploy
docker-compose up -d prometheus grafana
```

---

## 📚 使用指南

### 分布式追踪

#### 基础用法

```python
from shared.observability.tracing import get_tracer

tracer = get_tracer("patent-service")

@tracer.trace("analyze_patent")
async def analyze_patent(patent_id: str):
    # 自动创建Span，包含：
    # - span_name: "patent-service.analyze_patent"
    # - attributes: {"patent_id": patent_id}
    result = await process_patent(patent_id)
    return result
```

#### 嵌套追踪

```python
@tracer.trace("parent_operation")
async def parent_operation():
    # 父Span
    await child_operation_1()
    await child_operation_2()

@tracer.trace("child_operation_1")
async def child_operation_1():
    # 子Span（自动关联到父Span）
    pass
```

#### 自定义属性

```python
@tracer.trace("analyze_patent")
async def analyze_patent(patent_id: str):
    # 获取当前Span
    current_span = tracer.get_current_span()

    # 添加自定义属性
    current_span.set_attribute("patent.id", patent_id)
    current_span.set_attribute("patent.type", "invention")

    # 记录事件
    current_span.add_event("analysis_started", {"timestamp": time.time()})

    result = await process(patent_id)

    # 记录结果
    current_span.set_attribute("analysis.success", True)
    return result
```

#### 错误处理

```python
@tracer.trace("risky_operation")
async def risky_operation():
    try:
        return await risky_call()
    except Exception as e:
        # 自动记录异常到Span
        current_span = tracer.get_current_span()
        current_span.record_exception(e)
        raise
```

### Prometheus指标

#### Counter（计数器）

```python
from shared.observability.metrics import Counter

# 创建计数器
total_requests = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labels={"method": "GET", "endpoint": "/api/patents"}
)

# 增加计数
total_requests.inc()
total_requests.inc(5)  # 增加5
```

#### Histogram（直方图）

```python
from shared.observability.metrics import Histogram

# 创建直方图
response_time = Histogram(
    "http_response_time_seconds",
    "HTTP response time",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

# 观察值
response_time.observe(0.3)
response_time.observe(1.2)
```

#### Gauge（仪表）

```python
from shared.observability.metrics import Gauge

# 创建仪表
active_connections = Gauge(
    "active_connections",
    "Active database connections"
)

# 设置值
active_connections.set(10)

# 增加/减少
active_connections.inc()
active_connections.dec()
```

#### Summary（摘要）

```python
from shared.observability.metrics import Summary

# 创建摘要
request_size = Summary(
    "request_size_bytes",
    "Request size in bytes"
)

# 观察值
request_size.observe(1024)
request_size.observe(2048)
```

### 业务指标

```python
from shared.observability.metrics import BusinessMetrics

# 获取业务指标注册表
metrics = BusinessMetrics()

# 专利分析指标
metrics.patent_analysis_started(labels={"type": "novelty"})
metrics.patent_analysis_completed(labels={"type": "novelty", "success": "true"})
metrics.patent_analysis_duration(labels={"type": "novelty"}).observe(5.2)

# LLM调用指标
metrics.llm_request_total(labels={"model": "glm-4-plus", "operation": "analysis"})
metrics.llm_response_time(labels={"model": "glm-4-plus"}).observe(2.3)
metrics.llm_token_usage(labels={"model": "glm-4-plus", "type": "input"}).inc(1500)

# 缓存指标
metrics.cache_hits_total(labels={"cache": "redis", "operation": "get"})
metrics.cache_misses_total(labels={"cache": "redis", "operation": "get"})
metrics.cache_hit_rate(labels={"cache": "redis"}).set(0.85)
```

---

## 🔧 配置

### OpenTelemetry配置

```python
# shared/observability/tracing/config.py
OPENTELEMETRY_CONFIG = {
    "service_name": "athena-platform",
    "environment": "production",  # development | staging | production
    "sample_rate": 1.0,  # 1.0 = 100%采样
    "exporter": "jaeger",  # jaeger | otlp | console
    "jaeger_endpoint": "http://localhost:14250/api/traces",
    "enable_batch_export": True,
    "batch_export_schedule_delay": 5000,  # 毫秒
    "batch_export_max_queue_size": 2048,
}
```

### Prometheus配置

```python
# shared/observability/metrics/config.py
PROMETHEUS_CONFIG = {
    "port": 9090,  # Prometheus服务端口
    "metrics_path": "/metrics",  # 指标暴露路径
    "aggregation_window": 60,  # 聚合窗口（秒）
}
```

---

## 📊 Grafana仪表板

### 内置仪表板

1. **平台总览** (`platform_overview.json`)
   - 所有服务的健康状态
   - 总体请求量、错误率、延迟
   - 资源使用情况

2. **服务指标** (`service_metrics.json`)
   - 单个服务的详细指标
   - QPS、延迟分布、错误率
   - 依赖关系图

3. **专利执行专项** (`patent_execution.json`)
   - 专利分析成功率
   - LLM调用统计
   - 缓存命中率
   - 成本分析

### 导入仪表板

1. 打开Grafana: http://localhost:3000
2. 导航到 Dashboards → Import
3. 上传JSON文件或粘贴内容
4. 选择数据源（Prometheus）
5. 点击导入

---

## 🔍 追踪查询

### Jaeger UI

1. 打开Jaeger UI: http://localhost:16686
2. 选择服务（如：patent-service）
3. 查看Trace列表
4. 点击Trace查看详细调用链

### Prometheus查询

```promql
# 专利分析QPS
rate(patent_analysis_total[5m])

# 专利分析P95延迟
histogram_quantile(0.95, patent_analysis_duration_seconds_bucket)

# LLM调用成功率
rate(llm_requests_total{status="success"}[5m]) / rate(llm_requests_total[5m])

# Redis缓存命中率
rate(cache_hits_total{cache="redis"}[5m]) / (rate(cache_hits_total{cache="redis"}[5m]) + rate(cache_misses_total{cache="redis"}[5m]))
```

---

## 🎯 最佳实践

### 1. 命名规范

- **指标名称**: 使用下划线分隔，包含单位
  - ✅ `patent_analysis_duration_seconds`
  - ❌ `patentAnalysisDuration`

- **Span名称**: 使用点号分隔，包含服务名
  - ✅ `patent-service.analyze_patent`
  - ❌ `analyzePatent`

- **标签名**: 使用下划线分隔，小写
  - ✅ `{"patent_type": "invention"}`
  - ❌ `{"PatentType": "INVENTION"}`

### 2. 指标设计

- **使用Counter**：单调递增的值（请求总数、错误总数）
- **使用Histogram**：需要分布的值（延迟、请求大小）
- **使用Gauge**：可增可减的值（连接数、队列大小）
- **标签基数**：避免高基数标签（如user_id）

### 3. Span设计

- **Span层级**：不超过5层
- **Span大小**：单个Span不超过100个属性
- **Span名称**：具有业务含义
- **事件记录**：关键时刻记录事件

### 4. 性能考虑

- **采样率**：生产环境建议0.1-1.0
- **批量导出**：启用batch export
- **异步导出**：不阻塞业务逻辑
- **本地聚合**：使用Prometheus客户端的聚合功能

---

## 🛠️ 集成到现有服务

### FastAPI集成

```python
from fastapi import FastAPI
from shared.observability.tracing import get_tracer
from shared.observability.metrics import Counter

app = FastAPI()
tracer = get_tracer("patent-api")
request_counter = Counter("http_requests_total", "Total HTTP requests")

@app.middleware("http")
async def tracing_middleware(request, call_next):
    # 自动追踪所有HTTP请求
    with tracer.start_as_current_span(f"http.{request.method} {request.url.path}"):
        response = await call_next(request)
        request_counter.labels(
            method=request.method,
            path=request.url.path,
            status=response.status_code
        ).inc()
        return response
```

### Celery集成

```python
from celery import Celery
from shared.observability.tracing import get_tracer

tracer = get_tracer("celery-worker")
app = Celery('tasks')

@app.task
@tracer.trace("process_patent")
def process_patent(patent_id):
    # 任务逻辑
    pass
```

---

## 📈 扩展性

### 自定义指标收集器

```python
from shared.observability.metrics import MetricsCollector

class CustomMetricsCollector(MetricsCollector):
    def collect(self):
        # 返回自定义指标
        from prometheus_client import Metric
        metric = Metric("custom_metric", "Custom metric", "gauge")
        metric.add_sample("custom_metric", {}, 42)
        return [metric]
```

### 自定义Span处理器

```python
from opentelemetry.trace import SpanProcessor

class CustomSpanProcessor(SpanProcessor):
    def on_start(self, span, parent_context):
        # Span开始时的处理
        pass

    def on_end(self, span):
        # Span结束时的处理
        pass
```

---

## 🔗 相关文档

- [OpenTelemetry Python文档](https://opentelemetry.io/docs/instrumentation/python/)
- [Prometheus Python客户端文档](https://prometheus.github.io/client_python/)
- [Grafana文档](https://grafana.com/docs/)
- [Jaeger文档](https://www.jaegertracing.io/docs/)

---

## 📞 支持和维护

**维护团队**: Athena AI系统
**问题反馈**: GitHub Issues
**更新频率**: 每月更新一次

---

**文档版本**: v1.0.0
**最后更新**: 2025-12-14
**审核状态**: ✅ 已审核
