# Athena上下文管理系统 - Prometheus监控指南

> 版本: v1.0.0  
> 创建时间: 2026-04-24  
> 作者: Athena平台团队

## 目录

1. [快速开始](#快速开始)
2. [监控指标说明](#监控指标说明)
3. [Grafana仪表板](#grafana仪表板)
4. [告警规则](#告警规则)
5. [集成示例](#集成示例)
6. [故障排查](#故障排查)

---

## 快速开始

### 1. 安装依赖

```bash
pip3 install prometheus_client
```

### 2. 启动metrics服务器

```python
from core.context_management.monitoring import start_metrics_server

# 启动Prometheus metrics HTTP服务器
start_metrics_server(port=8000, addr="0.0.0.0")
```

访问 `http://localhost:8000/metrics` 查看指标。

### 3. 配置Prometheus

在 `prometheus.yml` 中添加：

```yaml
scrape_configs:
  - job_name: 'athena-context'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 15s
```

### 4. 导入Grafana仪表板

1. 登录Grafana
2. 导航到 Dashboards → Import
3. 上传 `config/monitoring/grafana_dashboard.json`

---

## 监控指标说明

### 1. 操作计数器 (Counter)

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `athena_context_management_operations_total` | Counter | operation, context_type, status | 上下文操作总数 |
| `athena_context_management_cache_operations_total` | Counter | operation, cache_type | 缓存操作总数 |
| `athena_context_management_errors_total` | Counter | error_type, operation | 错误总数 |

**操作类型 (operation)**:
- `create`: 创建上下文
- `read`: 读取上下文
- `update`: 更新上下文
- `delete`: 删除上下文
- `list`: 列出上下文

**状态 (status)**:
- `success`: 操作成功
- `error`: 操作失败
- `not_found`: 未找到

### 2. 延迟直方图 (Histogram)

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `athena_context_management_operation_duration_seconds` | Histogram | operation, context_type | 操作耗时分布 |
| `athena_context_management_pool_duration_seconds` | Histogram | operation | 对象池操作耗时 |

**查询百分位延迟**:
```promql
# P50延迟
histogram_quantile(0.50, rate(athena_context_management_operation_duration_seconds_bucket[5m]))

# P95延迟
histogram_quantile(0.95, rate(athena_context_management_operation_duration_seconds_bucket[5m]))

# P99延迟
histogram_quantile(0.99, rate(athena_context_management_operation_duration_seconds_bucket[5m]))
```

### 3. 仪表指标 (Gauge)

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `athena_context_management_active_contexts` | Gauge | context_type | 当前活跃上下文数量 |
| `athena_context_management_pool_size` | Gauge | pool_type | 对象池大小 |
| `athena_context_management_cache_hit_rate` | Gauge | cache_type | 缓存命中率 (0-1) |

---

## Grafana仪表板

### 仪表板面板

1. **上下文操作速率**: 显示每秒操作数（QPS）
2. **活跃上下文数量**: 实时活跃上下文计数
3. **操作延迟百分位**: P50/P95/P99延迟趋势
4. **错误率**: 操作错误率百分比
5. **对象池大小**: 当前池大小 vs 最大大小
6. **缓存命中率**: 缓存效率监控
7. **对象池操作延迟**: acquire/release平均延迟

### 自动刷新

仪表板默认每10秒自动刷新。

---

## 告警规则

### 告警级别

| 级别 | 说明 | 颜色 |
|------|------|------|
| `info` | 信息性告警 | 蓝色 |
| `warning` | 警告告警 | 黄色 |
| `error` | 错误告警 | 橙色 |
| `critical` | 严重告警 | 红色 |

### 告警规则列表

| 告警名称 | 级别 | 触发条件 | 持续时间 |
|---------|------|---------|---------|
| `HighContextErrorRate` | warning | 错误率 > 5% | 5分钟 |
| `CriticalContextErrorRate` | critical | 错误率 > 10% | 2分钟 |
| `HighContextLatencyP95` | warning | P95延迟 > 100ms | 5分钟 |
| `CriticalContextLatencyP99` | critical | P99延迟 > 500ms | 2分钟 |
| `TooManyActiveContexts` | warning | 活跃上下文 > 500 | 10分钟 |
| `ObjectPoolNearlyFull` | warning | 池使用率 > 90% | 5分钟 |
| `LowCacheHitRate` | info | 缓存命中率 < 70% | 15分钟 |
| `VeryLowCacheHitRate` | warning | 缓存命中率 < 50% | 10分钟 |
| `ContextCreateErrors` | error | 创建错误 > 0 | 2分钟 |
| `ContextReadErrors` | warning | 读取错误 > 0.1 ops/s | 5分钟 |

---

## 集成示例

### 1. 基础使用

```python
from core.context_management.monitoring import (
    get_metrics,
    start_metrics_server,
)

# 启动metrics服务器
start_metrics_server(port=8000)

# 获取metrics实例
metrics = get_metrics()

# 记录操作
metrics.record_operation("create", "task", "success")

# 记录错误
metrics.record_error("timeout", "create")
```

### 2. 上下文管理器监控

```python
from core.context_management.monitoring import monitor_context_manager
from core.context_management.task_context_manager import TaskContextManager

# 创建原始管理器
manager = TaskContextManager()

# 包装为监控管理器
monitored_manager = monitor_context_manager(manager, "task")

# 所有操作自动被监控
await monitored_manager.create_context("task-123", "示例任务")
```

### 3. 使用装饰器

```python
from core.context_management.monitoring import monitor_context_operation

@monitor_context_operation("create", "task")
async def create_task_context(task_id: str, description: str):
    # 函数执行自动被监控
    return await some_operation()
```

### 4. 手动跟踪延迟

```python
from core.context_management.monitoring import track_operation_latency

async with track_operation_latency("custom_operation", "task"):
    # 执行需要监控的操作
    result = await some_expensive_operation()
```

### 5. 对象池监控

```python
from core.context_management.context_object_pool import get_context_pool

# 对象池自动启用监控
pool = get_context_pool(max_size=1000, initial_size=10)

# 所有acquire/release操作自动被监控
context = await pool.acquire("task-123")
await pool.release(context)
```

---

## 故障排查

### 问题1: metrics服务器无法启动

**症状**: `start_metrics_server()` 返回False

**可能原因**:
1. 端口已被占用
2. prometheus_client未安装

**解决方案**:
```bash
# 检查端口占用
lsof -i :8000

# 安装prometheus_client
pip3 install prometheus_client

# 使用其他端口
start_metrics_server(port=8001)
```

### 问题2: Grafana无法显示数据

**症状**: 仪表板面板显示"No data"

**可能原因**:
1. Prometheus未正确抓取metrics
2. 服务地址配置错误

**解决方案**:
```bash
# 检查Prometheus目标
curl http://localhost:9090/api/v1/targets

# 检查metrics端点
curl http://localhost:8000/metrics

# 验证Prometheus配置
curl -X POST http://localhost:9090/-/reload
```

### 问题3: 告警未触发

**症状**: 预期告警未显示

**可能原因**:
1. 告警规则未加载
2. 条件未满足持续时间

**解决方案**:
```bash
# 检查告警规则
curl http://localhost:9090/api/v1/rules

# 查看告警状态
curl http://localhost:9090/api/v1/alerts

# 手动触发测试（在Prometheus UI中执行查询）
rate(athena_context_management_operations_total{status="error"}[5m]) 
/ rate(athena_context_management_operations_total[5m])
```

### 问题4: 监控数据不准确

**症状**: 指标值与预期不符

**可能原因**:
1. 标签基数过高
2. 时间范围选择不当

**解决方案**:
```promql
# 使用sum()聚合标签
sum(rate(athena_context_management_operations_total[5m]))

# 检查标签基数
count by (operation) (athena_context_management_operations_total)

# 使用合理的时间范围
rate(athena_context_management_operations_total[5m])
```

---

## 性能建议

### 1. 减少标签基数

避免使用高基数标签（如task_id、user_id）：

```python
# ❌ 错误：使用高基数标签
metrics.record_operation("create", task_id, status)

# ✅ 正确：使用低基数标签
metrics.record_operation("create", "task", status)
```

### 2. 合理设置抓取间隔

```yaml
# 生产环境建议
scrape_interval: 30s  # 不低于15s

# 测试环境
scrape_interval: 15s
```

### 3. 使用记录规则

对于复杂查询，使用记录规则预计算：

```yaml
groups:
  - name: athena_context_records
    interval: 30s
    rules:
      - record: job:athena_context_error_rate:5m
        expr: |
          rate(athena_context_management_operations_total{status="error"}[5m]) 
          / rate(athena_context_management_operations_total[5m])
```

---

## 相关文档

- [Prometheus查询语法](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana仪表板指南](https://grafana.com/docs/grafana/latest/dashboards/)
- [告警规则最佳实践](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)

---

**维护者**: Athena平台团队  
**最后更新**: 2026-04-24
