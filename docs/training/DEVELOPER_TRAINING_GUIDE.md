# Athena平台开发者培训指南

**版本**: v5.0.0  
**更新时间**: 2025-12-14  
**培训时长**: 3小时  
**目标读者**: 平台开发者

---

## 📚 培训大纲

1. [平台可观测性基础](#平台可观测性基础) (60分钟)
2. [分布式追踪实战](#分布式追踪实战) (60分钟)
3. [业务指标开发](#业务指标开发) (45分钟)
4. [最佳实践与代码示例](#最佳实践与代码示例) (15分钟)

---

## 🏗️ 平台可观测性基础

### 1.1 可观测性三大支柱

```
┌─────────────────────────────────────────────────────┐
│              Athena可观测性架构                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  🔍 TRACE（追踪）     📊 METRICS（指标）    📝 LOGS（日志）  │
│  │                   │                   │            │
│  │ OpenTelemetry      │ Prometheus        │ 结构化日志   │
│  │ Jaeger             │ Grafana           │ 集中式收集   │
│  │                   │                   │            │
│  └───────────────────┴───────────────────┘            │
│                      │                                │
│              上下文关联与统一视图                      │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 1.2 为什么需要可观测性？

**开发阶段**：
- 🔍 快速定位bug
- 📊 性能分析
- 🎯 代码质量验证

**测试阶段**：
- ✅ 自动化测试监控
- 📈 性能基准验证
- 🐛 缺陷追踪

**生产环境**：
- 🚨 实时告警
- 📊 业务指标监控
- 🔧 快速故障排查

### 1.3 平台可观测性基础设施

**目录结构**：
```
shared/observability/
├── README.md                           # 使用文档
├── tracing/                            # 分布式追踪
│   ├── tracer.py                       # OpenTelemetry追踪器
│   └── __init__.py
├── metrics/                            # Prometheus指标
│   ├── prometheus_exporter.py          # 指标导出器
│   ├── business_metrics.py             # 业务指标定义
│   └── __init__.py
└── monitoring/                         # 监控配置
    ├── prometheus/prometheus.yml       # Prometheus配置
    ├── grafana/dashboards/             # Grafana仪表板
    └── docker-compose.yml              # 监控栈部署
```

**快速启用**：
```python
# 1. 导入追踪器
from shared.observability.tracing import get_tracer

# 2. 获取指标注册表
from shared.observability.metrics import get_metrics_registry

# 3. 使用追踪器
tracer = get_tracer("your-service-name")

@tracer.trace("operation_name")
async def your_function():
    pass
```

---

## 🔍 分布式追踪实战

### 2.1 OpenTelemetry追踪器使用

#### 2.1.1 装饰器追踪（推荐）

**适用场景**：大多数业务函数

```python
from shared.observability.tracing import get_tracer

tracer = get_tracer("patent-service")

@tracer.trace("analyze_patent")
async def analyze_patent(patent_id: str, analysis_type: str):
    """
    分析专利
    
    自动记录：
    - Span名称: patent-service.analyze_patent
    - 参数: patent_id, analysis_type
    - 异常: 自动捕获
    - 耗时: 自动统计
    """
    # 业务逻辑
    result = await process_analysis(patent_id, analysis_type)
    return result
```

#### 2.1.2 上下文管理器追踪

**适用场景**：代码块、复杂逻辑

```python
from shared.observability.tracing import get_tracer

tracer = get_tracer("patent-service")

async def complex_workflow():
    async with tracer.start_async_span("workflow_step1") as span:
        # 步骤1
        span.set_attribute("step", 1)
        await step1()
    
    async with tracer.start_async_span("workflow_step2") as span:
        # 步骤2
        span.set_attribute("step", 2)
        await step2()
```

### 2.2 跨服务追踪

**场景**：服务间调用需要传递追踪上下文

```python
# 服务A：发起请求
from shared.observability.tracing import get_tracer
import httpx

tracer = get_tracer("service-a")

async def call_service_b():
    async with tracer.start_async_span("call_service_b") as span:
        # 获取当前追踪上下文
        headers = {}
        tracer.inject_context(headers)
        
        # 发送HTTP请求（自动携带追踪信息）
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://service-b/api/data",
                headers=headers
            )
        return response.json()
```

### 2.3 追踪最佳实践

✅ **应该做的**：
1. **所有公开API都要追踪**
2. **使用描述性的操作名称**
3. **记录关键业务参数**
4. **添加业务事件**

❌ **不应该做的**：
1. **不要追踪过于细粒度的操作**
2. **不要在高基数标签上使用**
3. **不要在Span中存储大对象**

---

## 📊 业务指标开发

### 3.1 Prometheus指标类型

#### 3.1.1 Counter（计数器）

**用途**：只增不减的值

```python
from shared.observability.metrics import PrometheusCounter

# 创建计数器
request_counter = PrometheusCounter(
    name="api_requests_total",
    description="Total API requests",
    labelnames=("method", "endpoint", "status")
)

# 使用计数器
request_counter.labels(
    method="GET",
    endpoint="/api/patents",
    status="success"
).inc()
```

#### 3.1.2 Histogram（直方图）

**用途**：记录数值分布（延迟、大小等）

```python
from shared.observability.metrics import PrometheusHistogram

response_time = PrometheusHistogram(
    name="api_response_time_seconds",
    description="API response time",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
)

import time
start = time.time()
# ... 执行操作 ...
duration = time.time() - start
response_time.labels(endpoint="/api/patents").observe(duration)
```

### 3.2 使用平台预定义业务指标

**36个预定义指标**位于：`shared/observability/metrics/business_metrics.py`

#### 3.2.1 专利执行指标

```python
from shared.observability.metrics.business_metrics import get_business_metrics

metrics = get_business_metrics()

# 1. 专利分析总数
metrics.patent_analysis_total.labels(
    type="novelty",
    status="completed"
).inc()

# 2. 专利分析延迟
metrics.patent_analysis_duration_seconds.labels(
    type="novelty"
).observe(5.2)

# 3. 专利分析成本
metrics.patent_analysis_cost_yuan.labels(
    type="novelty"
).observe(10.50)
```

#### 3.2.2 LLM调用指标

```python
# LLM请求总数
metrics.llm_requests_total.labels(
    model="glm-4-plus",
    status="success"
).inc()

# LLM响应时间
metrics.llm_response_time_seconds.labels(
    model="glm-4-plus"
).observe(2.3)

# LLM Token使用量
metrics.llm_tokens_total.labels(
    model="glm-4-plus",
    token_type="input"
).inc(1500)
```

---

## 🎯 最佳实践与代码示例

### 4.1 完整的API端点示例

```python
from fastapi import FastAPI, HTTPException
from shared.observability.tracing import get_tracer
from shared.observability.metrics.business_metrics import get_business_metrics

app = FastAPI()
tracer = get_tracer("patent-api")
metrics = get_business_metrics()

@app.post("/api/patents/analyze")
@tracer.trace("api_analyze_patent")
async def analyze_patent_api(request: AnalyzeRequest):
    """
    专利分析API端点
    
    自动追踪：
    - Span: patent-api.api_analyze_patent
    - 参数: patent_id, analysis_type
    - 指标: patent_analysis_total, duration_seconds, cost_yuan
    """
    patent_id = request.patent_id
    analysis_type = request.analysis_type
    
    start = time.time()
    success = False
    cost = 0.0
    
    try:
        # 执行分析
        async with tracer.start_async_span("execute_analysis") as span:
            span.set_attribute("analysis.type", analysis_type)
            result = await analysis_service.analyze(patent_id, analysis_type)
        
        success = True
        cost = calculate_analysis_cost(analysis_type)
        return result
        
    except Exception as e:
        metrics.patent_analysis_total.labels(
            type=analysis_type,
            status="failed"
        ).inc()
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # 更新业务指标
        duration = time.time() - start
        metrics.patent_analysis_duration_seconds.labels(
            type=analysis_type
        ).observe(duration)
        metrics.patent_analysis_cost_yuan.labels(
            type=analysis_type
        ).observe(cost)
```

---

## 📚 延伸阅读

- [OpenTelemetry官方文档](https://opentelemetry.io/docs/)
- [Prometheus最佳实践](https://prometheus.io/docs/practices/)
- [平台可观测性架构文档](../../shared/observability/README.md)

---

**培训版本**: v5.0.0  
**最后更新**: 2025-12-14  
**维护团队**: Athena AI系统
