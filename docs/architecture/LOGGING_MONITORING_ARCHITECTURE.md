# Athena统一日志和监控系统架构设计

> **版本**: v1.0
> **日期**: 2026-04-21
> **状态**: 设计阶段

---

## 📋 现状分析

### 当前日志系统

**问题**:
1. 🔴 **日志格式不统一** - 混合使用print、logging、自定义日志
2. 🔴 **缺少结构化** - 难以解析和分析
3. 🔴 **缺少日志分级** - 无法过滤日志级别
4. 🔴 **缺少聚合** - 日志分散在各处

### 当前监控系统

**已有**:
- Prometheus（指标收集）
- Grafana（可视化）
- Alertmanager（告警）

**问题**:
- 🔴 指标不完整
- 🔴 仪表板不统一
- 🔴 告警规则不完善

---

## 🎯 设计目标

### 目标1: 统一日志格式 🎯
- JSON格式日志
- 结构化字段
- 时间戳标准化
- 请求ID追踪

### 目标2: 日志分级机制 🎯
- DEBUG: 详细调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

### 目标3: 日志聚合 🎯
- 集中收集日志
- 日志轮转和归档
- 日志搜索和分析

### 目标4: 监控指标完善 🎯
- 系统指标（CPU、内存、磁盘）
- 应用指标（请求量、响应时间）
- 业务指标（Agent调用、专利分析）

---

## 🏗️ 日志架构设计

### 日志格式

```json
{
  "timestamp": "2026-04-21T12:00:00.000Z",
  "level": "INFO",
  "logger": "core.agents.xiaona",
  "message": "Agent执行完成",
  "context": {
    "agent_id": "xiaona-001",
    "task_id": "task-123",
    "session_id": "session-456",
    "user_id": "user-789"
  },
  "extra": {
    "execution_time": 1.23,
    "tokens_used": 1500,
    "model": "claude-sonnet-4-6"
  }
}
```

### 日志分级

| 级别 | 用途 | 示例 |
|------|------|------|
| **DEBUG** | 详细调试信息 | 函数入参、中间变量 |
| **INFO** | 一般信息 | 服务启动、请求处理 |
| **WARNING** | 警告信息 | 重试、降级、配置缺失 |
| **ERROR** | 错误信息 | 异常、失败、错误码 |
| **CRITICAL** | 严重错误 | 服务崩溃、数据丢失 |

### 日志字段

**标准字段**:
- `timestamp`: ISO 8601格式时间戳
- `level`: 日志级别
- `logger`: 日志记录器名称
- `message`: 日志消息

**上下文字段**:
- `agent_id`: Agent ID
- `task_id`: 任务ID
- `session_id`: 会话ID
- `user_id`: 用户ID
- `request_id`: 请求ID

**扩展字段**:
- `execution_time`: 执行时间
- `tokens_used`: Token使用量
- `model`: 模型名称

---

## 🔧 核心组件设计

### 1. 统一日志记录器 (UnifiedLogger)

**职责**:
- 格式化日志为JSON
- 添加标准字段
- 支持日志分级
- 支持上下文追踪

**API**:
```python
class UnifiedLogger:
    """统一日志记录器"""
    
    def debug(self, message: str, **context):
        """记录DEBUG级别日志"""
        
    def info(self, message: str, **context):
        """记录INFO级别日志"""
        
    def warning(self, message: str, **context):
        """记录WARNING级别日志"""
        
    def error(self, message: str, **context):
        """记录ERROR级别日志"""
        
    def critical(self, message: str, **context):
        """记录CRITICAL级别日志"""
```

### 2. 结构化日志格式化器 (StructuredFormatter)

**职责**:
- 将日志格式化为JSON
- 添加时间戳
- 添加标准字段
- 序列化复杂对象

### 3. 日志上下文管理器 (LogContext)

**职责**:
- 管理日志上下文
- 自动添加追踪字段
- 支持上下文传递

---

## 📊 监控指标设计

### 系统指标

| 指标 | 类型 | 说明 |
|------|------|------|
| `cpu_usage_percent` | Gauge | CPU使用率 |
| `memory_usage_bytes` | Gauge | 内存使用量 |
| `disk_usage_percent` | Gauge | 磁盘使用率 |
| `network_io_bytes` | Counter | 网络IO字节数 |

### 应用指标

| 指标 | 类型 | 说明 |
|------|------|------|
| `http_requests_total` | Counter | HTTP请求总数 |
| `http_request_duration_seconds` | Histogram | 请求耗时分布 |
| `http_requests_in_flight` | Gauge | 处理中的请求数 |
| `http_requests_failed_total` | Counter | 失败的请求总数 |

### 业务指标

| 指标 | 类型 | 说明 |
|------|------|------|
| `agent_executions_total` | Counter | Agent执行总数 |
| `agent_execution_duration_seconds` | Histogram | Agent执行耗时 |
| `patent_analysis_total` | Counter | 专利分析总数 |
| `llm_tokens_used_total` | Counter | LLM Token使用量 |

---

## 🎨 Grafana仪表板设计

### 系统概览仪表板

**面板**:
1. CPU使用率（折线图）
2. 内存使用量（折线图）
3. 磁盘使用率（折线图）
4. 网络IO（折线图）

### 应用性能仪表板

**面板**:
1. 请求速率（折线图）
2. 请求延迟（热力图）
3. 错误率（折线图）
4. 活跃连接（折线图）

### Agent监控仪表板

**面板**:
1. Agent执行次数（条形图）
2. Agent平均执行时间（折线图）
3. Agent成功率（折线图）
4. Token使用量（折线图）

---

## 🚀 使用示例

### 基础日志

```python
from core.monitoring.logger import get_logger

logger = get_logger(__name__)

logger.info("服务启动", port=8005)
logger.warning("配置缺失", key="api_key", default="使用默认值")
logger.error("请求失败", url="/api/test", status_code=500)
```

### 带上下文的日志

```python
from core.monitoring.logger import get_logger, bind_context

logger = get_logger(__name__)

# 绑定上下文
with bind_context(agent_id="xiaona-001", task_id="task-123"):
    logger.info("开始执行任务")
    # ... 执行任务
    logger.info("任务完成", execution_time=1.23)
```

### 监控指标

```python
from prometheus_client import Counter, Histogram

# 定义指标
agent_executions = Counter(
    'agent_executions_total',
    'Agent执行总数',
    ['agent_name', 'status']
)

agent_duration = Histogram(
    'agent_execution_duration_seconds',
    'Agent执行耗时',
    ['agent_name']
)

# 使用指标
agent_executions.labels(agent_name='xiaona', status='success').inc()
agent_duration.labels(agent_name='xiaona').observe(1.23)
```

---

## ✅ 实施计划

### Day 15-17: 设计日志架构
- 设计日志格式
- 设计日志分级
- 设计日志聚合方案
- 编写日志架构文档

### Day 18-19: 实现日志工具
- 创建UnifiedLogger
- 实现StructuredFormatter
- 实现LogContext
- 编写单元测试

### Day 20-21: 集成监控系统
- 集成Prometheus指标
- 配置Grafana仪表板
- 建立告警规则
- 清理旧的监控代码

---

## 📊 预期成果

### 日志系统

| 指标 | 目标 |
|------|------|
| 日志格式统一率 | 100% |
| 日志结构化率 | >90% |
| 日志可解析率 | 100% |

### 监控系统

| 指标 | 目标 |
|------|------|
| Prometheus指标覆盖率 | >80% |
| Grafana仪表板数量 | ≥3个 |
| 告警规则数量 | ≥10条 |

---

**文档版本**: v1.0
**最后更新**: 2026-04-21
**状态**: ✅ 日志架构设计完成

**下一步**: 实现日志工具（Day 18-19）
