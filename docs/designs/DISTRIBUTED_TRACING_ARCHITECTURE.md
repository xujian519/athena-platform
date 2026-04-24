# Gateway分布式追踪架构设计

> **文档编号**: BEAD-201
> **创建日期**: 2026-04-24
> **状态**: 设计阶段
> **作者**: 架构团队

---

## 1. 概述

### 1.1 背景

Athena工作平台采用多智能体协作架构，随着系统复杂度增加，传统日志监控已无法满足以下需求：

- **跨服务调用链追踪**: 小娜→小诺→9个专业代理的调用路径
- **性能瓶颈定位**: P95延迟从目标100ms恶化到150ms的根本原因
- **错误传播分析**: 0.15%错误率的具体来源和传播路径
- **资源占用分析**: 缓存命中率89.7%为何仍未达到性能目标

### 1.2 设计目标

| 维度 | 当前状态 | 目标状态 | 改善幅度 |
|-----|---------|---------|---------|
| API响应时间(P95) | ~150ms | <100ms | -33% |
| 向量检索延迟 | ~80ms | <50ms | -37.5% |
| 查询吞吐量 | ~85 QPS | >100 QPS | +17.6% |
| 错误率 | ~0.15% | <0.1% | -33% |
| 追踪开销 | N/A | <5% | 新增 |

### 1.3 追踪范围

```
┌─────────────────────────────────────────────────────────────────┐
│                      Athena Platform                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐│
│  │   用户请求       │───→│  Gateway(8005)  │───→│   Xiaonuo       ││
│  │   REST/WebSocket│    │  Go网关          │    │   协调代理       ││
│  └─────────────────┘    └─────────────────┘    └────────┬────────┘│
│                                                       │         │
│                              ┌────────────────────────┼─────────┤│
│                              ↓                        ↓         ↓│
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Xiaona模块     │  │  专业代理矩阵    │  │  外部服务        │ │
│  │  (9个代理)      │  │  (检索/分析/...) │  │  LLM/DB/缓存     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 技术选型

### 2.1 方案对比

| 特性 | OpenTelemetry | Jaeger | Zipkin | SkyWalking |
|-----|--------------|--------|--------|------------|
| **标准化程度** | ⭐⭐⭐⭐⭐ CNCF标准 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Python支持** | ⭐⭐⭐⭐⭐ 原生SDK | ⭐⭐⭐⭐ 通过OTel | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Go支持** | ⭐⭐⭐⭐⭐ 原生SDK | ⭐⭐⭐⭐⭐ 原生 | ⭐⭐⭐ | ⭐⭐⭐ |
| **集成难度** | ⭐⭐⭐⭐⭐ 装饰器模式 | ⭐⭐⭐⭐ 需要Agent | ⭐⭐⭐ 需要Agent | ⭐⭐⭐⭐⭐ Agentless |
| **性能开销** | ⭐⭐⭐⭐⭐ <3% | ⭐⭐⭐⭐ 3-5% | ⭐⭐⭐ 5-8% | ⭐⭐⭐⭐ <5% |
| **可视化能力** | ⭐⭐⭐ 需要后端 | ⭐⭐⭐⭐⭐ 优秀UI | ⭐⭐⭐⭐ 良好UI | ⭐⭐⭐⭐⭐ 优秀UI |
| **社区活跃度** | ⭐⭐⭐⭐⭐ 最活跃 | ⭐⭐⭐⭐ 稳定 | ⭐⭐⭐ 维护模式 | ⭐⭐⭐⭐ 活跃 |
| **云原生** | ⭐⭐⭐⭐⭐ 完全兼容 | ⭐⭐⭐⭐⭐ 完全兼容 | ⭐⭐⭐⭐ 兼容 | ⭐⭐⭐⭐ 兼容 |

### 2.2 选型决策

**最终方案: OpenTelemetry + Jaeger**

```
┌─────────────────────────────────────────────────────────────────┐
│                    OpenTelemetry + Jaeger                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐│
│  │  Python应用     │    │  Go应用         │    │  其他服务        ││
│  │  (Agents/LLM)   │    │  (Gateway)      │    │  (DB/缓存)       ││
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘│
│           │                      │                      │         │
│           ↓                      ↓                      ↓         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              OpenTelemetry SDK/Instrumentation             ││
│  │  • Python: opentelemetry-api/sdk                           ││
│  │  • Go: go.opentelemetry.io/otel                             ││
│  └──────────────────────────┬──────────────────────────────────┘│
│                             │ OTLP Protocol                    │
│                             ↓                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              OpenTelemetry Collector                        ││
│  │  • Span处理与聚合                                           ││
│  │  • 批量导出优化                                             ││
│  │  • 数据转换与过滤                                           ││
│  └──────────────────────────┬──────────────────────────────────┘│
│                             │                                   │
│                             ↓                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Jaeger Backend                          ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ ││
│  │  │ Collector   │→ │  Storage    │  │  Query Service      │ ││
│  │  │ (gRPC/HTTP) │  │ (Elasticsearch)│ │  (API)              │ ││
│  │  └─────────────┘  └─────────────┘  └──────────┬──────────┘ ││
│  │                                              ↓              ││
│  │                                    ┌─────────────────┐     ││
│  │                                    │  Jaeger UI      │     ││
│  │                                    │  (Web Dashboard)│     ││
│  │                                    └─────────────────┘     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**选择理由**:

1. **标准化**: OpenTelemetry是CNCF标准，避免厂商锁定
2. **生态兼容**: 可导出到Jaeger、Zipkin、Prometheus等多种后端
3. **语言覆盖**: Python和Go都有原生SDK支持
4. **性能优异**: 异步批量处理，开销<3%
5. **渐进迁移**: 可先导出到Jaeger，后续切换到其他后端

---

## 3. 四层架构设计

### 3.1 架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        分布式追踪四层架构                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Layer 1: 应用层 (Application Layer)                          │ │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │ │
│  │  │   Agents   │ │     LLM    │ │  Database  │ │   Cache    │  │ │
│  │  │  (Python)  │ │  (Claude)  │ │ (Postgres) │ │  (Redis)   │  │ │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │ │
│  └───────────────────────────────┬───────────────────────────────┘ │
│                                  │ Trace Context                   │
│                                  ↓ (propagation)                  │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Layer 2: 埋点层 (Instrumentation Layer)                     │ │
│  │  ┌─────────────────────────────────────────────────────────┐  │ │
│  │  │  OpenTelemetry SDK                                      │  │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐    │  │ │
│  │  │  │    Tracer   │ │    Meter    │ │    Logger       │    │  │ │
│  │  │  │  (Spans)    │ │  (Metrics)  │ │   (Logs)        │    │  │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────────┘    │  │ │
│  │  │  ┌─────────────────────────────────────────────────┐     │  │ │
│  │  │  │  Auto-Instrumentation                          │     │  │ │
│  │  │  │  • HTTP/HTTPS                                  │     │  │ │
│  │  │  │  • asyncio                                     │     │  │ │
│  │  │  │  • requests/aiohttp                            │     │  │ │
│  │  │  │  • psycopg2/asyncpg (DB)                       │     │  │ │
│  │  │  └─────────────────────────────────────────────────┘     │  │ │
│  │  └─────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────┬───────────────────────────────┘ │
│                                  │ OTLP (Protocol Buffers)        │
│                                  ↓                                 │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Layer 3: 采集层 (Collection Layer)                          │ │
│  │  ┌─────────────────────────────────────────────────────────┐  │ │
│  │  │  OpenTelemetry Collector                                │  │ │
│  │  │                                                         │  │ │
│  │  │  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐ │  │ │
│  │  │  │   Receiver    │→ │  Processor    │→ │   Exporter  │ │  │ │
│  │  │  │  (OTLP/gRPC)  │  │  (Batch/Filter)│ │  (Jaeger)   │ │  │ │
│  │  │  └───────────────┘  └───────────────┘  └─────────────┘ │  │ │
│  │  │                                                         │  │ │
│  │  │  • 端点: otel-collector:4317 (gRPC)                   │  │ │
│  │  │  • 端点: otel-collector:4318 (HTTP)                   │  │ │
│  │  │  • 批处理: 100 spans 或 10s                           │  │ │
│  │  └─────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────┬───────────────────────────────┘ │
│                                  │ jaeger.thrift                   │
│                                  ↓                                 │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Layer 4: 存储层 (Storage Layer)                             │ │
│  │  ┌─────────────────────────────────────────────────────────┐  │ │
│  │  │  Jaeger Storage                                         │  │ │
│  │  │                                                         │  │ │
│  │  │  ┌─────────────────┐  ┌─────────────────────────────┐   │  │ │
│  │  │  │    Spans        │  │       Dependencies           │   │  │ │
│  │  │  │  (Elasticsearch)│  │       (Elasticsearch)        │   │  │ │
│  │  │  │  • 索引: jaeger-*│  │       索引: jaeger-*        │   │  │ │
│  │  │  │  • TTL: 7天     │  │       • TTL: 30天            │   │  │ │
│  │  │  └─────────────────┘  └─────────────────────────────┘   │  │ │
│  │  └─────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────┬───────────────────────────────┘ │
│                                  │ HTTP Query                      │
│                                  ↓                                 │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  可视化层 (Visualization Layer)                               │ │
│  │  ┌─────────────────────────────────────────────────────────┐  │ │
│  │  │  Jaeger UI                                              │  │ │
│  │  │  • 端点: http://localhost:16686                         │  │ │
│  │  │  • 功能: Trace搜索、Waterfall、Service Map、Metrics      │  │ │
│  │  └─────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 各层详细设计

#### Layer 1: 应用层

**Python组件**:
```python
# 核心追踪点
1. Agent调用: BaseAgent.execute()
2. LLM请求: UnifiedLLMManager.call()
3. DB查询: PostgreSQL执行
4. 缓存操作: Redis读写
5. 向量检索: Qdrant搜索
6. 文件操作: 读写交底书/专利
```

**Go组件**:
```go
// 核心追踪点
1. HTTP请求: Gateway路由处理
2. WebSocket连接: 会话管理
3. 服务发现: 注册中心查询
4. 负载均衡: 后端服务调用
```

#### Layer 2: 埋点层

**自动埋点**:
- HTTP/HTTPS客户端和服务端
- asyncio事件循环
- 数据库驱动 (psycopg2, asyncpg, redis-py)
- 消息队列 (如适用)

**手动埋点装饰器**:
```python
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor

@trace.get_tracer(__name__).start_as_current_span("agent_execution")
def execute(self, task: str) -> str:
    # 自动创建Span
    with trace.get_tracer(__name__).start_as_current_span("llm_call"):
        result = self.llm.generate(task)
    return result
```

#### Layer 3: 采集层

**Collector配置**:
```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    batch_size: 100

exporters:
  jaeger:
    endpoint: jaeger-collector:14250
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
```

#### Layer 4: 存储层

**存储策略**:
| 数据类型 | 存储 | TTL | 索引策略 |
|---------|------|-----|---------|
| Spans | Elasticsearch | 7天 | TraceID, SpanID, Timestamp |
| Dependencies | Elasticsearch | 30天 | Service, Operation |
| Metrics | Prometheus | 15天 | Label-based |

---

## 4. 关键组件设计

### 4.1 TracerProvider

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# 配置TracerProvider
provider = TracerProvider()
provider.configure(
    sampler=trace.sampler.ParentBased(
        root=trace.sampler.TraceIdRatioBased(0.1)  # 10%采样
    )
)

# 配置导出器
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger-agent",
    agent_port=6831,
)

# 批量处理Span
span_processor = BatchSpanProcessor(
    jaeger_exporter,
    max_queue_size=2048,
    schedule_delay_millis=5000,
    max_export_batch_size=512,
)

provider.add_span_processor(span_processor)
trace.set_tracer_provider(provider)
```

### 4.2 ContextPropagator

```python
from opentelemetry import propagators
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMap

# HTTP请求头传播
carrier = {}
propagator = propagators.get_global_textmap()
propagator.inject(carrier)

# 在请求中携带
headers = {
    "traceparent": carrier.get("traceparent"),
    "Content-Type": "application/json",
}
response = requests.post(url, json=data, headers=headers)
```

### 4.3 SpanProcessor

```python
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

# 实时Span处理器（开发环境）
simple_processor = SimpleSpanProcessor(jaeger_exporter)

# 批量Span处理器（生产环境）
batch_processor = BatchSpanProcessor(
    jaeger_exporter,
    max_queue_size=2048,
    schedule_delay_millis=10000,
    max_export_batch_size=512,
)

# 根据环境选择
if os.getenv("ENVIRONMENT") == "production":
    provider.add_span_processor(batch_processor)
else:
    provider.add_span_processor(simple_processor)
```

---

## 5. 部署架构

### 5.1 Docker Compose配置

```yaml
# docker-compose.unified.yml 新增服务
services:
  # OpenTelemetry Collector
  otel-collector:
    image: otel/opentelemetry-collector:0.91.0
    command: --config=/etc/otel-collector-config.yaml
    volumes:
      - ./config/otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
    depends_on:
      - jaeger-collector
    networks:
      - athena-network

  # Jaeger Collector
  jaeger-collector:
    image: jaegertracing/jaeger-collector:1.50
    command:
      - "--es.server-urls=http://elasticsearch:9200"
      - "--es.num-shards=1"
      - "--es.num-replicas=0"
      - "--collector.grpc-server.host-port=:14250"
      - "--collector.http-server.host-port=:14268"
    ports:
      - "14250:14250" # gRPC
      - "14268:14268" # HTTP
      - "14269:14269" # Admin
    depends_on:
      - elasticsearch
    networks:
      - athena-network

  # Jaeger Query
  jaeger-query:
    image: jaegertracing/jaeger-query:1.50
    command:
      - "--es.server-urls=http://elasticsearch:9200"
      - "--span-storage.type=elasticsearch"
    environment:
      - JAEGER_AGENT_HOST=jaeger-agent
    ports:
      - "16686:16686" # Web UI
      - "16687:16687" # Admin
    depends_on:
      - elasticsearch
    networks:
      - athena-network

  # Jaeger Agent
  jaeger-agent:
    image: jaegertracing/jaeger-agent:1.50
    command:
      - "--reporter.grpc.server-addr=jaeger-collector:14250"
      - "--metrics-backend=prometheus"
    ports:
      - "5775:5775"   # Compact Thrift
      - "5778:5778"   # Admin
      - "6831:6831"   # Thrift binary
      - "6832:6832"   # Thrift compact
      - "5778:5778"   # Config
    networks:
      - athena-network
```

### 5.2 端口规划

| 服务 | 端口 | 协议 | 用途 |
|-----|------|------|------|
| OTEL Collector | 4317 | gRPC | OTLP接收（推荐） |
| OTEL Collector | 4318 | HTTP | OTLP接收 |
| Jaeger Agent | 6831 | UDP | Thrift binary |
| Jaeger Agent | 6832 | UDP | Thrift compact |
| Jaeger Collector | 14250 | gRPC | Collector接收 |
| Jaeger Collector | 14268 | HTTP | Collector接收 |
| Jaeger Query | 16686 | HTTP | Web UI |
| Jaeger Query | 16687 | HTTP | Admin API |

---

## 6. 采样策略

### 6.1 分层采样

```python
# 生产环境采样策略
PRODUCTION_SAMPLING = {
    "default": 0.01,              # 默认1%
    "agent_call": 0.1,            # Agent调用10%
    "llm_request": 0.5,           # LLM请求50%
    "database_query": 0.05,       # DB查询5%
    "cache_miss": 0.2,            # 缓存未命中20%
    "error": 1.0,                 # 错误100%
    "slow_request": 1.0,          # 慢请求100%
}

# 动态采样配置
class AdaptiveSampler:
    def __init__(self):
        self.base_rate = 0.01
        self.error_rate = 0.0
        self.p95_latency = 0.0

    def should_sample(self, span_name: str, attributes: dict) -> bool:
        # 错误始终采样
        if attributes.get("error"):
            return True

        # 慢请求始终采样
        if attributes.get("duration_ms", 0) > 100:
            return True

        # 根据类型采样
        span_type = attributes.get("span_type", "default")
        return random.random() < PRODUCTION_SAMPLING.get(span_type, self.base_rate)
```

### 6.2 采样开销分析

| 采样率 | 每日Spans | 存储需求 | CPU开销 | 推荐场景 |
|-------|----------|---------|--------|---------|
| 100% | ~8.6M | ~50GB/天 | ~5% | 开发/测试 |
| 10% | ~860K | ~5GB/天 | ~2% | 预发布 |
| 1% | ~86K | ~500MB/天 | <1% | 生产默认 |
| 动态 | ~100K | ~600MB/天 | ~1.5% | 生产推荐 |

---

## 7. 性能优化

### 7.1 批量导出优化

```python
# 优化前：每个Span立即导出
SimpleSpanProcessor(exporter)  # 高延迟，高CPU

# 优化后：批量导出
BatchSpanProcessor(
    exporter,
    max_queue_size=2048,        # 队列大小
    schedule_delay_millis=10000, # 10秒定时导出
    max_export_batch_size=512,   # 每批512个Span
)
```

### 7.2 异步导出

```python
from concurrent.futures import ThreadPoolExecutor

# 使用线程池异步导出
executor = ThreadPoolExecutor(max_workers=4)
exporter = JaegerExporter(
    agent_host_name="jaeger-agent",
    agent_port=6831,
)

processor = BatchSpanProcessor(
    exporter,
    executor=executor,
)
```

### 7.3 内存优化

```python
# Span属性限制
MAX_ATTRIBUTE_COUNT = 32
MAX_ATTRIBUTE_VALUE_LENGTH = 128

def sanitize_span(attributes: dict) -> dict:
    """清理Span属性，防止内存溢出"""
    result = {}
    for k, v in list(attributes.items())[:MAX_ATTRIBUTE_COUNT]:
        key = str(k)[:MAX_ATTRIBUTE_VALUE_LENGTH]
        value = str(v)[:MAX_ATTRIBUTE_VALUE_LENGTH]
        result[key] = value
    return result
```

---

## 8. 安全性考虑

### 8.1 敏感数据过滤

```python
# 敏感字段过滤
SENSITIVE_PATTERNS = [
    r"password",
    r"token",
    r"api[_-]?key",
    r"secret",
    r"auth",
    r"session[_-]?id",
]

def sanitize_attributes(attributes: dict) -> dict:
    """过滤敏感数据"""
    result = {}
    for k, v in attributes.items():
        if any(re.search(pattern, k.lower()) for pattern in SENSITIVE_PATTERNS):
            result[k] = "***REDACTED***"
        else:
            result[k] = v
    return result
```

### 8.2 访问控制

```yaml
# Jaeger UI访问控制
jaeger-query:
  environment:
    - QUERY_BASE_PATH=/jaeger
    - JAEGER_AUTH_ENABLED=true
    - JAEGER_ADMIN_HTTP_TOKEN=${ADMIN_TOKEN}
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.jaeger.rule=PathPrefix(`/jaeger`)"
    - "traefik.http.routers.jaeger.middlewares=auth"
```

---

## 9. 监控指标

### 9.1 追踪系统健康指标

| 指标 | 描述 | 告警阈值 |
|-----|------|---------|
| otel_collector_spans_received | 接收的Span数量 | < 0（流异常） |
| otel_collector_spans_filtered | 过滤的Span数量 | > 50% |
| otel_collector_exporter_send_success | 导出成功率 | < 95% |
| jaeger_agent_packets_dropped | Agent丢弃包数 | > 0 |
| jaeger_collector_latency | Collector延迟 | > 1s |

### 9.2 Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Athena Distributed Tracing",
    "panels": [
      {
        "title": "Request Rate (QPS)",
        "targets": [
          {
            "expr": "sum(rate(http_server_duration_seconds_count[5m]))"
          }
        ]
      },
      {
        "title": "P95 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_server_duration_seconds_bucket[5m])) by (le))"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "sum(rate(http_server_duration_seconds_count{status=\"error\"}[5m])) / sum(rate(http_server_duration_seconds_count[5m]))"
          }
        ]
      },
      {
        "title": "Service Dependencies",
        "type": "graph",
        "targets": [
          {
            "expr": "jaeger_dependencies"
          }
        ]
      }
    ]
  }
}
```

---

## 10. 故障排查

### 10.1 常见问题

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| Spans未显示 | 端点配置错误 | 检查OTEL_EXPORTER_OTLP_ENDPOINT |
| Trace断链 | Context未传播 | 确保使用trace.context propagators |
| 性能下降 | 采样率过高 | 降低采样率至1-5% |
| 存储溢出 | TTL未配置 | 设置Elasticsearch索引TTL |

### 10.2 调试命令

```bash
# 检查Collector连接
curl -X POST http://localhost:4318/v1/traces -d '{}'

# 检查Jaeger Agent
nc -zv localhost 6831

# 查看Collector日志
docker-compose logs -f otel-collector

# 查看Jaeger状态
curl http://localhost:16686/api/services
```

---

## 11. 版本兼容性

| 组件 | 版本 | Python兼容 | Go兼容 |
|-----|------|-----------|--------|
| opentelemetry-api | 1.21+ | 3.8+ | - |
| opentelemetry-sdk | 1.21+ | 3.8+ | - |
| opentelemetry-instrumentation | 0.42b+ | 3.8+ | - |
| go.opentelemetry.io | v1.21.0 | - | 1.20+ |
| Jaeger | 1.50+ | - | - |
| Elasticsearch | 7.x/8.x | - | - |

---

## 附录A: 完整追踪点清单

### A.1 Agent系统

| 组件 | 追踪点 | Span名称 | 属性 |
|-----|-------|---------|------|
| BaseAgent | execute | agent.execute | agent_name, task_type |
| XiaonaAgent | process_legal_task | xiaona.legal.process | case_id, legal_scenario |
| XiaonuoAgent | coordinate | xiaonuo.coordinate | session_id, agents_count |
| RetrieverAgent | search_patents | retriever.search | query, database |
| AnalyzerAgent | analyze_patent | analyzer.analyze | patent_id, analysis_type |
| UnifiedPatentWriter | draft_claims | writer.claims.draft | disclosure_id, claims_count |

### A.2 LLM系统

| 组件 | 追踪点 | Span名称 | 属性 |
|-----|-------|---------|------|
| UnifiedLLMManager | call | llm.request | provider, model, tokens |
| ClaudeAdapter | generate | llm.claude.generate | api_version, max_tokens |
| GPTAdapter | chat_completion | llm.gpt.complete | model_name, stream |
| DeepSeekAdapter | inference | llm.deepseek.infer | endpoint, temperature |

### A.3 数据层

| 组件 | 追踪点 | Span名称 | 属性 |
|-----|-------|---------|------|
| PostgreSQL | execute_query | db.postgres.query | table, operation, rows |
| Redis | get/set | redis.operation | key, operation, hit |
| Qdrant | search | qdrant.search | collection, top_k, latency |

---

## 附录B: 参考资料

- [OpenTelemetry Python SDK](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenTelemetry Go SDK](https://opentelemetry.io/docs/instrumentation/go/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/reference/specification/trace/semantic_conventions/)
