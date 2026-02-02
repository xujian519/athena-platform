# 方案B: 微服务架构重构规划

## 📋 方案概述

**目标**: 将单体执行器重构为微服务架构
**时间**: 3个月 (12周)
**投资**: ¥150,000
**预期回报**: 233% ROI
**团队规模**: 4-5人

---

## 🏗️ 目标架构

### 当前架构 (单体)

```
┌─────────────────────────────────────────┐
│        单体执行器应用                     │
├─────────────────────────────────────────┤
│  PatentAnalysisExecutor                 │
│  PatentFilingExecutor                   │
│  PatentMonitoringExecutor               │
│  PatentValidationExecutor               │
├─────────────────────────────────────────┤
│  直接调用:                              │
│  ├─ LLM服务                            │
│  ├─ 数据库                             │
│  └─ 缓存                               │
└─────────────────────────────────────────┘
```

**问题**:
- 所有功能耦合在一个进程中
- 无法独立扩展特定功能
- 一个服务的Bug可能影响整个系统
- 技术栈无法多样化

### 目标架构 (微服务)

```
┌─────────────────────────────────────────────────────────────────┐
│                      API网关 (Kong / Nginx)                   │
└────────────────────────────┬────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ 分析服务       │  │ 申请服务       │  │ 监控服务       │
│ (Python/FastAPI)│  │ (Python/FastAPI)│  │ (Python/FastAPI)│
├────────────────┤  ├────────────────┤  ├────────────────┤
│ • 新颖性分析    │  │ • 文档生成      │  │ • 状态监控     │
│ • 创造性分析    │  │ • 费用计算      │  │ • 告警通知     │
│ • 综合分析      │  │ • 申请提交      │  │ • 趋势分析     │
└────────┬───────┘  └────────┬───────┘  └────────┬───────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ LLM网关服务     │  │ 缓存服务        │  │ 消息队列       │
│ (Python)        │  │ (Go)            │  │ (RabbitMQ)     │
├────────────────┤  ├────────────────┤  ├────────────────┤
│ • 统一LLM调用   │  │ • Redis集群     │  │ • 任务队列     │
│ • 模型选择      │  │ • 分布式锁     │  │ • 死信队列     │
│ • 限流熔断      │  │ • 会话存储     │  │ • 延迟队列     │
└────────┬───────┘  └────────┬───────┘  └────────┬───────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ 数据库服务      │  │ 文档服务        │  │ 通知服务       │
│ (PostgreSQL)    │  │ (MinIO/S3)      │  │ (SMTP/Slack)   │
├────────────────┤  ├────────────────┤  ├────────────────┤
│ • 任务记录      │  │ • 文档存储      │  │ • 邮件通知     │
│ • 分析结果      │  │ • 版本管理      │  │ • Webhook      │
│ • 用户数据      │  │ • 文档检索      │  │ • 即时消息     │
└────────────────┘  └────────────────┘  └────────────────┘
```

---

## 📦 服务拆分设计

### 服务1: 分析服务 (analysis-service)

**职责**: 专利分析相关功能
**端口**: 8001
**技术栈**: Python 3.12 + FastAPI + uvicorn

**API端点**:
```python
# 分析服务API
POST /api/v1/analysis/novelty
POST /api/v1/analysis/inventiveness
POST /api/v1/analysis/comprehensive
POST /api/v1/analysis/batch
GET  /api/v1/analysis/{task_id}
```

**代码结构**:
```
analysis-service/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── novelty.py
│   │   │   ├── inventiveness.py
│   │   │   └── comprehensive.py
│   ├── services/
│   │   ├── analysis_service.py
│   │   └── report_generator.py
│   ├── models/
│   │   └── schemas.py
│   └── main.py
├── tests/
├── Dockerfile
└── requirements.txt
```

**Docker配置**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 服务2: LLM网关服务 (llm-gateway-service)

**职责**: 统一的LLM调用入口
**端口**: 8002
**技术栈**: Python 3.12 + FastAPI

**核心功能**:
- 模型选择和路由
- 请求限流和熔断
- 响应缓存
- 成本追踪

**API端点**:
```python
# LLM网关API
POST /api/v1/llm/generate
POST /api/v1/llm/chat
POST /api/v1/llm/embed
GET  /api/v1/llm/models
GET  /api/v1/llm/usage
```

**代码结构**:
```
llm-gateway-service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── generate.py
│   │       └── models.py
│   ├── services/
│   │   ├── model_selector.py
│   │   ├── rate_limiter.py
│   │   └── cost_tracker.py
│   ├── middleware/
│   │   └── auth.py
│   └── main.py
├── Dockerfile
└── requirements.txt
```

### 服务3: 缓存服务 (cache-service)

**职责**: 分布式缓存和会话管理
**端口**: 8003
**技术栈**: Go + Redis + gRPC

**选择Go的原因**:
- 高并发性能优异
- 内存占用小
- gRPC支持好

**核心功能**:
```go
// 缓存服务接口
service CacheService {
    rpc Get(GetRequest) returns (GetResponse);
    rpc Set(SetRequest) returns (SetResponse);
    rpc Delete(DeleteRequest) returns (DeleteResponse);
    rpc GetBatch(GetBatchRequest) returns (GetBatchResponse);
}
```

### 服务4: 任务队列服务 (queue-service)

**职责**: 异步任务处理和调度
**技术栈**: Python + Celery + RabbitMQ

**任务类型**:
```python
# 任务定义
from celery import Celery

app = Celery('patent-tasks')

@app.task(bind=True)
def analyze_patent_task(self, task_data):
    """异步专利分析任务"""
    pass

@app.task
def generate_report_task(self, analysis_result):
    """异步报告生成任务"""
    pass
```

### 服务5: 文档服务 (document-service)

**职责**: 专利文档生成和管理
**端口**: 8004
**技术栈**: Python + FastAPI + MinIO/S3

**核心功能**:
- 文档模板管理
- PDF生成
- 文档版本控制
- 文档检索

---

## 🔄 服务间通信

### 同步通信 (REST/gRPC)

**场景**: 需要即时响应的操作

```python
# 分析服务调用LLM网关
import httpx

async def call_llm_gateway(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://llm-gateway:8002/api/v1/llm/generate',
            json={'prompt': prompt},
            timeout=30.0
        )
        return response.json()
```

### 异步通信 (消息队列)

**场景**: 不需要即时响应的后台任务

```python
# 提交异步任务
from celery import Celery

celery = Celery(
    'patent-tasks',
    broker='amqp://rabbitmq:5672'
)

@celery.task
def async_analysis_task(patent_id: str):
    """异步分析任务"""
    result = analyze_patent(patent_id)
    send_notification(patent_id, result)
    return result
```

---

## 🗄️ 数据持久化方案

### 数据库设计

**表结构**:

```sql
-- 任务表
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    priority INTEGER DEFAULT 5,
    parameters JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    INDEX idx_status (status),
    INDEX idx_priority (priority)
);

-- 分析结果表
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES tasks(id),
    patent_id VARCHAR(100),
    analysis_type VARCHAR(50),
    result JSONB NOT NULL,
    llm_provider VARCHAR(50),
    model_used VARCHAR(50),
    tokens_used INTEGER,
    cost DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_task_id (task_id),
    INDEX idx_patent_id (patent_id)
);

-- 文档表
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES tasks(id),
    doc_type VARCHAR(50),
    file_path VARCHAR(500),
    file_size BIGINT,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_task_id (task_id)
);
```

### 数据库迁移

使用Alembic进行版本管理：

```bash
# 安装alembic
pip install alembic

# 初始化
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "Initial schema"

# 执行迁移
alembic upgrade head
```

---

## 🚀 部署方案

### Kubernetes部署配置

```yaml
# deployment.yaml - 分析服务
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analysis-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: analysis-service
  template:
    metadata:
      labels:
        app: analysis-service
    spec:
      containers:
      - name: analysis-service
        image: patent-analysis-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: db-config
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: redis-config
              key: url
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: analysis-service
spec:
  selector:
    app: analysis-service
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: analysis-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: analysis-service
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 服务网格 (Istio)

启用服务网格实现流量管理和安全：

```yaml
# virtual-service.yaml - 流量管理
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: analysis-service
spec:
  hosts:
  - analysis-service
  http:
  - match:
    - uri:
        prefix: /api/v1/analysis
    route:
    - destination:
        host: analysis-service
        subset: v2  # 金丝雀发布
      weight: 20  # 20%流量到v2
    - destination:
        host: analysis-service
        subset: v1  # 80%流量到v1
      weight: 80
```

---

## 📊 监控和可观测性

### Prometheus指标

每个服务暴露指标端点：

```python
from prometheus_client import Counter, Histogram, Gauge

# 业务指标
analysis_requests_total = Counter(
    'analysis_requests_total',
    'Total analysis requests',
    ['analysis_type', 'status']
)

analysis_duration_seconds = Histogram(
    'analysis_duration_seconds',
    'Analysis duration',
    ['analysis_type'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

analysis_queue_size = Gauge(
    'analysis_queue_size',
    'Current analysis queue size'
)

# 使用示例
@analysis_duration_seconds.time('novelty')
async def analyze_novelty(patent_data):
    analysis_requests_total.labels(
        analysis_type='novelty',
        status='processing'
    ).inc()

    result = await perform_analysis(patent_data)

    analysis_requests_total.labels(
        analysis_type='novelty',
        status='success' if result else 'failed'
    ).inc()

    return result
```

### Grafana仪表板

创建统一的监控仪表板：

```json
{
  "dashboard": {
    "title": "专利执行器监控",
    "panels": [
      {
        "title": "分析请求QPS",
        "targets": [
          {
            "expr": "rate(analysis_requests_total[5m])"
          }
        ]
      },
      {
        "title": "分析延迟P99",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, analysis_duration_seconds)"
          }
        ]
      },
      {
        "title": "错误率",
        "targets": [
          {
            "expr": "rate(analysis_requests_total{status=\"failed\"}[5m]) / rate(analysis_requests_total[5m])"
          }
        ]
      }
    ]
  }
}
```

### 分布式追踪

使用OpenTelemetry和Jaeger：

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.jaeger import JaegerExporter

# 配置追踪
trace.set_tracer_provider(provider)
FastAPIInstrumentor.instrument_app(app)

# 在代码中使用
tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("analyze_patent")
async def analyze_patent(patent_data):
    with tracer.start_as_current_span("llm_call"):
        result = await llm_service.analyze(patent_data)
    return result
```

---

## 🧪 测试策略

### 单元测试

```python
# tests/test_analysis_service.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_novelty_analysis():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/analysis/novelty",
            json={
                "patent_data": {...}
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"
```

### 集成测试

```python
# tests/integration/test_service_communication.py
@pytest.mark.asyncio
async def test_analysis_to_llm_gateway():
    # 测试分析服务调用LLM网关
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/analysis/novelty",
            json={"patent_data": {...}}
        )

        # 验证LLM网关被调用
        assert mock_llm_gateway.called
        assert response.status_code == 200
```

### 性能测试

使用Locust进行负载测试：

```python
# locustfile.py
from locust import HttpUser, task, between

class PatentAnalysisUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.client.post("/api/v1/auth/login")

    @task
    def analyze_novelty(self):
        self.client.post("/api/v1/analysis/novelty", json={
            "patent_data": {...}
        })
```

---

## 📅 实施时间表

### 第1-2周：架构设计和准备

- [ ] 完成服务拆分设计
- [ ] 定义服务接口契约
- [ ] 搭建开发环境
- [ ] 创建代码仓库

### 第3-4周：核心服务开发

- [ ] 开发LLM网关服务
- [ ] 开发缓存服务
- [ ] 开发分析服务
- [ ] 编写单元测试

### 第5-6周：基础设施搭建

- [ ] 配置Kubernetes集群
- [ ] 搭建CI/CD流水线
- [ ] 配置监控系统
- [ ] 配置日志系统

### 第7-8周：数据层实现

- [ ] 设计数据库schema
- [ ] 实现数据访问层
- [ ] 编写数据迁移脚本
- [ ] 数据备份策略

### 第9-10周：服务集成和测试

- [ ] 服务间联调测试
- [ ] 集成测试
- [ ] 性能测试
- [ ] 安全测试

### 第11-12周：灰度发布和优化

- [ ] 灰度发布（10%流量）
- [ ] 监控指标
- [ ] 性能优化
- [ ] 全量发布

---

## 🎯 成功指标

### 技术指标

| 指标 | 当前 | 目标 | 测量方法 |
|------|------|------|----------|
| 服务可用性 | 95% | 99.9% | Prometheus uptime |
| P99延迟 | 5.2s | 2.0s | Histogram quantile |
| 吞吐量 | 0.35 QPS | 100 QPS | Request rate |
| 错误率 | 5% | <0.1% | Error rate |
| 部署时间 | N/A | <5分钟 | CI/CD duration |

### 业务指标

| 指标 | 当前 | 目标 | 测量方法 |
|------|------|------|----------|
| 日处理量 | 3万 | 30万 | Task count |
| 客户满意度 | 未知 | >90% | Survey |
| 成本/次 | ¥15.09 | ¥5 | Cost tracking |

---

## 🚨 风险和缓解

### 风险1: 服务间通信延迟

**缓解措施**:
- 使用gRPC代替REST
- 实现服务本地缓存
- 优化网络拓扑

### 风险2: 分布式事务复杂

**缓解措施**:
- 使用Saga模式处理长事务
- 实现幂等性
- 最终一致性设计

### 风险3: 运维复杂度增加

**缓解措施**:
- 完善监控和告警
- 自动化运维工具
- 知识文档化

---

**创建时间**: 2025-12-14
**规划版本**: v1.0
**状态**: ✅ 已完成
