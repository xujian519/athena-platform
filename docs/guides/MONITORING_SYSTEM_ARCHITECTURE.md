# 监控系统架构设计

> **Phase 3 Week 3**
> **主题**: 监控系统设计
> **设计时间**: 2026-04-22

---

## 📋 设计目标

### 核心功能
1. **指标采集**: 自动采集系统和应用指标
2. **指标存储**: 使用Prometheus时序数据库
3. **数据展示**: Grafana可视化仪表板
4. **告警系统**: 基于指标的智能告警

### 非功能性需求
- **低开销**: 指标采集不影响应用性能（<5% CPU）
- **高可用**: 监控系统本身高可用
- **可扩展**: 易于添加新的指标和仪表板
- **易用性**: 简单的配置和查询界面

---

## 🏗️ 监控架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │ Xiaona   │  │ Xiaonuo  │  │ Gateway  │  │ 其他服务 ││
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘│
│       │             │             │             │       │
└───────┼─────────────┼─────────────┼─────────────┼───────┘
        │             │             │             │
        │             │             │             │
        ▼             ▼             ▼             ▼
   ┌──────────────────────────────────────────────────┐
   │         Prometheus Metrics Exporter             │
   │  ┌──────────────┐  ┌──────────────┐              │
   │  │ HTTP Endpoint│  │ Metrics      │              │
   │  │ /metrics     │  │ Collector    │              │
   │  └──────────────┘  └──────────────┘              │
   └──────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Prometheus Server                          │
│  • 指标抓取 (scrape)                                   │
│  • 时序存储                                           │
│  • PromQL查询                                         │
│  • 告警规则                                           │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Grafana                                │
│  • 数据源配置                                          │
│  • 仪表板                                              │
│  • 可视化                                              │
│  • 告警                                                │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 指标体系设计

### 1. 系统指标 (System Metrics)

由Prometheus Node Exporter自动采集。

| 指标名称 | 类型 | 说明 |
|---------|------|------|
| `cpu_usage_percent` | Gauge | CPU使用率 |
| `memory_usage_bytes` | Gauge | 内存使用量 |
| `memory_available_bytes` | Gauge | 可用内存 |
| `disk_usage_bytes` | Gauge | 磁盘使用量 |
| `disk_io_time_seconds` | Counter | 磁盘IO时间 |
| `network_receive_bytes` | Counter | 网络接收字节数 |
| `network_transmit_bytes` | Counter | 网络发送字节数 |
| `system_load1` | Gauge | 1分钟平均负载 |

### 2. 应用指标 (Application Metrics)

自定义应用层指标。

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `http_requests_total` | Counter | method, endpoint, status | HTTP请求总数 |
| `http_request_duration_seconds` | Histogram | method, endpoint | HTTP请求耗时 |
| `http_requests_in_flight` | Gauge | method, endpoint | 正在处理的HTTP请求数 |
| `service_tasks_total` | Counter | service, status | 任务总数 |
| `service_task_duration_seconds` | Histogram | service, task_type | 任务耗时 |
| `service_errors_total` | Counter | service, error_type | 错误总数 |
| `cache_hits_total` | Counter | cache_type | 缓存命中数 |
| `cache_misses_total` | Counter | cache_type | 缓存未命中数 |
| `llm_requests_total` | Counter | provider, model | LLM请求总数 |
| `llm_response_time_seconds` | Histogram | provider, model | LLM响应时间 |
| `llm_tokens_total` | Counter | provider, model, type | LLM token使用量 |

### 3. 业务指标 (Business Metrics)

业务相关指标。

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `patent_analysis_total` | Counter | status | 专利分析总数 |
| `patent_analysis_duration_seconds` | Histogram | - | 专利分析耗时 |
| `legal_search_total` | Counter | search_type | 法律检索总数 |
| `document_generation_total` | Counter | doc_type | 文档生成总数 |
| `agent_tasks_completed` | Counter | agent_name, task_type | Agent完成任务数 |

---

## 🔧 核心组件设计

### 1. MetricsCollector

指标收集器。

```python
class MetricsCollector:
    """Prometheus指标收集器"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.registry = CollectorRegistry()
        
        # 默认指标
        self._setup_default_metrics()
    
    def _setup_default_metrics(self):
        """设置默认指标"""
        # HTTP请求计数
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        # HTTP请求耗时
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request latency',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # 服务任务计数
        self.service_tasks_total = Counter(
            'service_tasks_total',
            'Total service tasks',
            ['service', 'status'],
            registry=self.registry
        )
        
        # LLM请求计数
        self.llm_requests_total = Counter(
            'llm_requests_total',
            'Total LLM requests',
            ['provider', 'model'],
            registry=self.registry
        )
        
        # LLM响应时间
        self.llm_response_time = Histogram(
            'llm_response_time_seconds',
            'LLM response latency',
            ['provider', 'model'],
            registry=self.registry
        )
```

### 2. HTTPMetricsExporter

HTTP指标导出器。

```python
class HTTPMetricsExporter:
    """HTTP指标导出器"""
    
    def __init__(self, collector: MetricsCollector, port: int = 9090):
        self.collector = collector
        self.port = port
        self.app = make_asgi_app()
    
    def start(self):
        """启动指标导出服务"""
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="warning"
        )
    
    async def metrics_endpoint(self):
        """Prometheus /metrics 端点"""
        from prometheus_client import generate_latest
        
        metrics = generate_latest(self.collector.registry)
        return Response(
            content=metrics,
            media_type=CONTENT_TYPE_LATEST
        )
```

### 3. InstrumentationDecorator

性能监控装饰器。

```python
def monitor_performance(
    collector: MetricsCollector,
    metric_name: str
):
    """性能监控装饰器"""
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                
                # 记录成功
                duration = time.time() - start_time
                collector.service_tasks_total.labels(
                    service=collector.service_name,
                    status="success"
                ).inc()
                
                # 记录耗时
                if hasattr(collector, f"{metric_name}_duration"):
                    histogram = getattr(collector, f"{metric_name}_duration")
                    histogram.observe(duration)
                
                return result
                
            except Exception as e:
                # 记录失败
                duration = time.time() - start_time
                collector.service_tasks_total.labels(
                    service=collector.service_name,
                    status="error"
                ).inc()
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                # 记录成功
                duration = time.time() - start_time
                collector.service_tasks_total.labels(
                    service=collector.service_name,
                    status="success"
                ).inc()
                
                return result
                
            except Exception as e:
                # 记录失败
                duration = time.time() - start_time
                collector.service_tasks_total.labels(
                    service=collector.service_name,
                    status="error"
                ).inc()
                
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
```

---

## 📈 Prometheus配置

### prometheus.yml

```yaml
# Prometheus配置文件
global:
  scrape_interval: 15s  # 抓取间隔
  evaluation_interval: 15s  # 规则评估间隔
  external_labels:
    cluster: 'athena'
    environment: 'development'

# 告警规则配置
rule_files:
  - '/etc/prometheus/rules/*.yml'

# 抓取配置
scrape_configs:
  # 服务自身指标
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # 小娜服务
  - job_name: 'xiaona'
    static_configs:
      - targets: ['xiaona:9090']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'xiaona'

  # 小诺服务
  - job_name: 'xiaonuo'
    static_configs:
      - targets: ['xiaonuo:9091']

  # Gateway服务
  - job_name: 'gateway'
    static_configs:
      - targets: ['gateway:9092']

  # Node Exporter (系统指标)
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
```

### 告警规则

```yaml
groups:
  - name: service_alerts
    rules:
      # 服务错误率告警
      - alert: HighErrorRate
        expr: |
          (
            rate(http_requests_total{status=~"5.."}[5m])
            /
            rate(http_requests_total[5m])
          ) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "服务错误率过高"
          description: "{{ $labels.service }} 错误率超过5%"

      # 服务响应时间告警
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, 
            rate(http_request_duration_seconds_bucket[5m])
          ) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "服务响应时间过长"
          description: "{{ $labels.service }} P95响应时间超过1秒"

      # 服务不可用告警
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "服务不可用"
          description: "{{ $labels.job }} 服务已停止"
```

---

## 📊 Grafana仪表板设计

### 1. 系统概览仪表板

** panels**:
- CPU使用率 (所有服务)
- 内存使用率 (所有服务)
- 磁盘使用率 (所有服务)
- 网络流量 (所有服务)
- 系统负载 (所有服务)

### 2. 服务监控仪表板

** panels**:
- HTTP请求率 (QPS)
- HTTP响应时间 (P50, P95, P99)
- 错误率
- 任务完成率
- LLM调用次数和响应时间

### 3. 性能分析仪表板

** panels**:
- 慢查询Top10
- 错误分布
- 缓存命中率
- 服务依赖关系图
- 资源消耗排行

---

## 🔌 服务集成示例

### 小娜服务集成

```python
from core.monitoring import MetricsCollector, monitor_performance

class XiaonaAgent:
    """小娜Agent（带监控）"""
    
    def __init__(self):
        self.service_name = "xiaona"
        
        # 创建指标收集器
        self.metrics = MetricsCollector(self.service_name)
        
        # 启动指标导出
        self.exporter = HTTPMetricsExporter(self.metrics, port=9090)
    
    @monitor_performance(self.metrics, "patent_analysis")
    async def analyze_patent(self, patent_id: str):
        """分析专利（带性能监控）"""
        # 业务逻辑
        result = await self._do_analysis(patent_id)
        
        # 记录专利分析计数
        self.metrics.patent_analysis_total.labels(
            status="success"
        ).inc()
        
        return result
```

### Gateway服务集成

```python
from prometheus_client import Counter, Histogram

# HTTP请求中间件
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Prometheus监控中间件"""
    
    start_time = time.time()
    
    # 处理请求
    response = await call_next(request)
    
    # 记录请求计数
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    # 记录请求耗时
    duration = time.time() - start_time
    http_request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

---

## 📁 文件结构

```
core/monitoring/
├── __init__.py                 # 模块入口
├── collector.py                # 指标收集器
├── exporter.py                 # HTTP指标导出器
├── decorators.py               # 监控装饰器
└── middleware.py               # 监控中间件

prometheus/
├── prometheus.yml              # Prometheus配置
└── rules/                      # 告警规则
    ├── service_alerts.yml
    └── system_alerts.yml

grafana/
├── dashboards/                 # 仪表板配置
│   ├── system_overview.json
│   ├── service_monitoring.json
│   └── performance_analysis.json
└── provisioning/               # 预配置
    └── datasources/
```

---

## ✅ 实施计划

### Phase 1: 核心实现 (Day 2)
- [ ] 实现MetricsCollector
- [ ] 实现HTTPMetricsExporter
- [ ] 实现InstrumentationDecorator
- [ ] 集成到现有服务

### Phase 2: Prometheus配置 (Day 3)
- [ ] 配置prometheus.yml
- [ ] 配置告警规则
- [ ] 启动Prometheus服务

### Phase 3: Grafana仪表板 (Day 4)
- [ ] 配置数据源
- [ ] 创建系统概览仪表板
- [ ] 创建服务监控仪表板
- [ ] 创建性能分析仪表板

---

## 📈 成功标准

### 功能完整性
- [ ] 指标自动采集 ✅
- [ ] Prometheus集成 ✅
- [ ] Grafana仪表板 ✅
- [ ] 告警规则配置 ✅

### 性能要求
- [ ] 指标采集开销 < 5% CPU
- [ ] 指标存储支持30天+
- [ ] 查询响应时间 < 1秒

### 可用性要求
- [ ] 配置简单
- [ ] 仪表板直观
- [ ] 告警及时准确

---

**监控系统架构设计完成！**

**设计时间**: 2026-04-22
**设计人**: Claude Code (OMC模式)
**下一步**: 实施监控系统
