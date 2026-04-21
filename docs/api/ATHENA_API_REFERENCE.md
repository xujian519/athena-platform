# Athena平台API文档

> **版本**: v1.0
> **更新时间**: 2026-04-21

---

## 📚 核心API文档索引

### 1. 统一配置管理 API

**模块**: `core/config/unified_settings.py`

**主要类**:
- `Settings` - 统一配置管理类

**核心方法**:
```python
# 加载配置
settings = Settings.load(environment="development")

# 访问配置
db_url = settings.database_url
llm_provider = settings.llm_provider

# 获取单例
settings = get_settings()
```

**配置字段**:
- `environment`: 运行环境
- `database_url`: Athena主库连接
- `patent_db_url`: Patent专利库连接
- `neo4j_bolt_url`: Neo4j Bolt连接
- `llm_provider`: LLM提供商
- `redis_host`: Redis主机

---

### 2. 服务注册中心 API

**模块**: `core/service_registry/`

**主要类**:
- `ServiceRegistry` - 服务注册表
- `HealthChecker` - 健康检查器
- `DiscoveryAPI` - 服务发现API

**核心方法**:
```python
# 服务注册
from core.service_registry import ServiceInfo, get_service_registry

registry = get_service_registry()
service = ServiceInfo(
    id="service-001",
    name="my-service",
    type="api",
    host="localhost",
    port=8000,
    health_check_url="http://localhost:8000/health"
)
registry.register(service)

# 服务发现
from core.service_registry import get_discovery_api

api = get_discovery_api()
service = await api.discover("my-service")

# 健康检查
from core.service_registry import get_health_checker

checker = get_health_checker()
health = await checker.check_service(service)
```

---

### 3. 统一LLM服务 API

**模块**: `core/llm/unified_llm_manager.py`

**主要类**:
- `UnifiedLLMManager` - 统一LLM管理器

**核心方法**:
```python
# 获取管理器
from core.llm.unified_llm_manager import get_unified_llm_manager

manager = get_unified_llm_manager()

# 生成文本
response = await manager.generate(
    prompt="分析专利的创造性",
    task_type="creativity_analysis"
)

# 流式生成
async for chunk in manager.generate_stream(
    prompt="写一段专利摘要",
    task_type="general_chat"
):
    print(chunk, end="")
```

**支持的模型**:
- Claude (Anthropic)
- GPT-4 (OpenAI)
- DeepSeek
- GLM-4.7 (智谱AI)
- Qwen (阿里)
- Ollama (本地)

---

### 4. 性能监控 API

**模块**: `core/monitoring/performance_metrics_enhanced.py`

**主要类**:
- `PerformanceMetrics` - 性能指标收集器

**核心指标**:
- 系统指标: CPU、内存、磁盘
- 应用指标: HTTP请求、Agent执行
- LLM指标: 请求、Token、缓存
- 业务指标: 专利分析、检索

**使用示例**:
```python
from core.monitoring.performance_metrics_enhanced import get_performance_metrics

metrics = get_performance_metrics()

# 记录配置加载耗时
metrics.record_config_load(duration=0.01)

# 记录模型选择耗时
metrics.record_model_selection(duration=0.005)
```

**Prometheus端点**: `http://localhost:8000/metrics`

---

### 5. MCP服务集成 API

**模块**: `core/mcp/`

**主要类**:
- `MCPServiceRegistryBridge` - MCP服务注册中心桥接器
- `MCPHealthChecker` - MCP健康检查器

**核心方法**:
```python
# 注册所有MCP服务
from core.mcp import register_all_mcp_services

results = await register_all_mcp_services()

# 同步服务状态
from core.mcp import sync_mcp_service_status

statuses = await sync_mcp_service_status()

# 获取健康状态
from core.mcp import get_mcp_health_checker

checker = get_mcp_health_checker()
health = await checker.check_all_mcp_services(mcp_manager)
```

---

## 🔧 使用示例

### 示例1: 快速启动

```python
from core.config.unified_settings import get_settings
from core.llm.unified_llm_manager import get_unified_llm_manager

# 获取配置
settings = get_settings()

# 获取LLM管理器
llm_manager = get_unified_llm_manager()

# 生成文本
response = await llm_manager.generate(
    prompt="分析专利的创造性",
    task_type="creativity_analysis"
)
```

### 示例2: 服务注册和发现

```python
from core.service_registry import ServiceInfo, get_service_registry
from core.service_registry import get_discovery_api
import asyncio

async def main():
    # 注册服务
    registry = get_service_registry()
    service = ServiceInfo(
        id="patent-service",
        name="专利服务",
        type="api",
        host="localhost",
        port=8080,
        health_check_url="http://localhost:8080/health"
    )
    registry.register(service)

    # 发现服务
    api = get_discovery_api()
    discovered = await api.discover("patent-service")
    print(f"发现服务: {discovered.name}")

asyncio.run(main())
```

### 示例3: 性能监控

```python
from core.monitoring.performance_metrics_enhanced import get_performance_metrics

metrics = get_performance_metrics()

# 模拟指标记录
metrics.http_requests_total.labels(
    method="GET",
    endpoint="/api/patents",
    status="200"
).inc()

metrics.http_request_duration.labels(
    endpoint="/api/patents"
).observe(0.123)

# 访问Prometheus端点
# http://localhost:8000/metrics
```

---

## 📊 性能基准

### API响应时间目标

| API | 目标P95 | 目标P99 |
|-----|---------|---------|
| **配置加载** | <50ms | <100ms |
| **模型选择** | <10ms | <20ms |
| **服务注册** | <100ms | <200ms |
| **服务发现** | <20ms | <50ms |
| **LLM请求** | <5s | <10s |
| **Agent执行** | <30s | <60s |

### 吞吐量目标

| 服务 | 目标QPS |
|------|---------|
| **HTTP API** | >100 QPS |
| **Agent执行** | >10 QPS |
| **服务注册** | >1000 QPS |
| **服务发现** | >500 QPS |

---

## 🔗 相关文档

- [配置架构文档](../architecture/CONFIG_ARCHITECTURE_DESIGN.md)
- [服务注册架构](../architecture/SERVICE_REGISTRY_ARCHITECTURE.md)
- [日志监控架构](../architecture/LOGGING_MONITORING_ARCHITECTURE.md)
- [统一LLM服务指南](../guides/UNIFIED_LLM_SERVICE_GUIDE.md)
- [数据库资产说明](../guides/DATABASE_ASSETS_GUIDE.md)

---

**文档维护**: Athena平台团队
**最后更新**: 2026-04-21
