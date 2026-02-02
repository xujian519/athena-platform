# 学习模块 API 文档

> Athena智能工作平台 - 自主学习系统API参考文档

版本: 1.0.0
最后更新: 2026-01-28

---

## 目录

- [概述](#概述)
- [并发控制 API](#并发控制-api)
  - [ConcurrencyConfig](#concurrencyconfig)
  - [RateLimiter](#ratelimiter)
  - [AsyncSemaphore](#asyncsemaphore)
  - [ConcurrencyController](#concurrencycontroller)
- [错误处理 API](#错误处理-api)
  - [错误类型](#错误类型)
  - [RetryHandler](#retryhandler)
  - [CircuitBreaker](#circuitbreaker)
  - [FallbackHandler](#fallbackhandler)
- [持久化 API](#持久化-api)
  - [StorageBackend](#storagebackend)
  - [LearningPersistenceManager](#learningpersistencemanager)
- [输入验证 API](#输入验证-api)
- [自主学习 API](#自主学习-api)

---

## 概述

学习模块提供以下核心能力：

1. **并发控制** - 控制学习任务的并发执行，防止资源竞争
2. **错误处理** - 智能重试、断路器、降级策略
3. **持久化** - 多后端学习数据存储
4. **输入验证** - 统一的输入验证机制
5. **自主学习** - 在线学习、性能分析、A/B测试

---

## 并发控制 API

### ConcurrencyConfig

并发控制配置类。

```python
from core.learning.concurrency_control import ConcurrencyConfig

config = ConcurrencyConfig(
    max_concurrent_tasks=10,        # 最大并发任务数
    max_operations_per_second=100,  # 每秒最大操作数
    max_queue_size=1000,             # 最大队列大小
    task_timeout=30.0                # 任务超时时间（秒）
)
```

**属性**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_concurrent_tasks` | `int` | 10 | 最大并发任务数 |
| `max_operations_per_second` | `int` | 100 | 每秒最大操作数 |
| `max_queue_size` | `int` | 1000 | 最大队列大小 |
| `task_timeout` | `float` | 30.0 | 任务超时时间（秒） |

---

### RateLimiter

基于令牌桶算法的速率限制器。

```python
from core.learning.concurrency_control import RateLimiter

# 创建限制器：10操作/秒，时间窗口1秒
limiter = RateLimiter(max_rate=10, window=1.0)

# 尝试获取令牌
if await limiter.acquire():
    # 执行操作
    pass
else:
    # 超过速率限制
    pass

# 等待获取令牌
await limiter.wait_for_token()
```

**方法**

#### `async acquire() -> bool`
尝试获取一个令牌。

- **返回**: `bool` - 是否成功获取

#### `async wait_for_token() -> None`
阻塞等待直到获取到令牌。

---

### AsyncSemaphore

带超时和统计功能的异步信号量。

```python
from core.learning.concurrency_control import AsyncSemaphore

semaphore = AsyncSemaphore(max_concurrent=5)

# 获取信号量
if await semaphore.acquire(timeout=10.0):
    try:
        # 执行操作
        pass
    finally:
        semaphore.release()

# 使用上下文管理器
async with semaphore:
    # 自动释放
    pass

# 获取统计信息
stats = semaphore.get_stats()
print(stats)
# {
#     "max_concurrent": 5,
#     "current_count": 0,
#     "total_acquired": 10,
#     "utilization": 0.0
# }
```

**方法**

#### `async acquire(timeout: float | None = None) -> bool`
获取信号量。

- **参数**:
  - `timeout`: 超时时间（秒），`None`表示无限等待
- **返回**: `bool` - 是否获取成功

#### `release() -> None`
释放信号量。

#### `get_stats() -> dict[str, Any]`
获取统计信息。

---

### ConcurrencyController

综合的并发控制器，结合信号量、速率限制和任务队列。

```python
from core.learning.concurrency_control import ConcurrencyController, ConcurrencyConfig

config = ConcurrencyConfig(max_concurrent_tasks=10)
controller = ConcurrencyController(config)

# 提交单个任务
async def my_task():
    await asyncio.sleep(0.1)
    return "result"

result = await controller.submit_task(my_task, timeout=5.0)

# 批量提交任务
async def task_factory(n):
    return await my_task()

task_factories = [lambda i=i: task_factory(i) for i in range(10)]
results = await controller.submit_batch(task_factories, timeout=5.0)

# 获取统计信息
stats = controller.get_statistics()

# 优雅关闭
await controller.shutdown()
```

**方法**

#### `async submit_task(coro: Callable[[], Any], priority: int = 0, timeout: float | None = None) -> Any`
提交任务到并发控制器。

- **参数**:
  - `coro`: 协程函数（无参数）
  - `priority`: 优先级（预留，当前未使用）
  - `timeout`: 任务超时时间
- **返回**: 任务结果
- **异常**:
  - `asyncio.TimeoutError`: 任务超时
  - `RuntimeError`: 队列已满或无法获取信号量

#### `async submit_batch(coros: list[Callable[[], Any]], timeout: float | None = None) -> list[Any]`
批量提交任务。

- **参数**:
  - `coros`: 协程函数列表
  - `timeout`: 每个任务的超时时间
- **返回**: 结果列表

#### `get_statistics() -> dict[str, Any]`
获取统计信息。

#### `async shutdown() -> None`
关闭并发控制器，等待所有活动任务完成。

---

## 错误处理 API

### 错误类型

#### LearningEngineError

基础学习引擎异常类。

```python
from core.learning.error_handling import LearningEngineError, ErrorSeverity, ErrorCategory

error = LearningEngineError(
    message="操作失败",
    severity=ErrorSeverity.HIGH,
    category=ErrorCategory.TRANSIENT,
    metadata={"context": "..."}
)
```

**参数**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `message` | `str` | - | 错误消息 |
| `severity` | `ErrorSeverity` | `MEDIUM` | 错误严重程度 |
| `category` | `ErrorCategory` | `TRANSIENT` | 错误类别 |
| `metadata` | `dict` | `{}` | 元数据 |

#### 专用异常类

| 类名 | 用途 | 默认严重度 | 默认类别 |
|------|------|-----------|-----------|
| `TransientError` | 临时错误 | MEDIUM | TRANSIENT |
| `PermanentError` | 永久错误 | HIGH | PERMANENT |
| `ValidationError` | 验证错误 | LOW | VALIDATION |
| `ResourceError` | 资源错误 | HIGH | RESOURCE |

---

### RetryHandler

智能重试处理器，支持指数退避和抖动。

```python
from core.learning.error_handling import RetryHandler, RetryConfig, TransientError

config = RetryConfig(
    max_attempts=5,           # 最大尝试次数
    base_delay=1.0,           # 基础延迟（秒）
    max_delay=60.0,           # 最大延迟（秒）
    exponential_base=2.0,     # 指数退避基数
    jitter=True               # 启用抖动
)

handler = RetryHandler(config)

async def unstable_task():
    if random.random() < 0.3:
        raise TransientError("临时失败")
    return "success"

result = await handler.execute_with_retry(unstable_task)

# 获取统计信息
stats = handler.get_statistics()
print(stats)
# {
#     "total_retries": 2,
#     "successful_retries": 1,
#     "recent_errors": [...]
# }
```

**RetryConfig 参数**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_attempts` | `int` | 3 | 最大尝试次数 |
| `base_delay` | `float` | 1.0 | 基础延迟（秒） |
| `max_delay` | `float` | 60.0 | 最大延迟（秒） |
| `exponential_base` | `float` | 2.0 | 指数退避基数 |
| `jitter` | `bool` | True | 是否启用抖动 |

**方法**

#### `async execute_with_retry(func: Callable, *args, **kwargs) -> Any`
执行函数并在失败时重试。

- **返回**: 函数返回值
- **异常**:
  - `LearningEngineError`: 重试耗尽后仍然失败

#### `get_statistics() -> dict[str, Any]`
获取重试统计信息。

---

### CircuitBreaker

断路器模式实现，防止连续失败导致的雪崩效应。

```python
from core.learning.error_handling import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,      # 失败阈值
    timeout=60.0,             # 超时时间（秒）
    half_open_attempts=1      # 半开状态尝试次数
)

async def protected_operation():
    return await some_remote_call()

# 通过断路器调用
try:
    result = await breaker.call(protected_operation)
except Exception as e:
    print(f"操作失败: {e}")

# 检查断路器状态
state = breaker.get_state()
print(state)
# {
#     "state": "closed",  # closed, open, half_open
#     "failures": 0,
#     "failure_threshold": 5
# }
```

**状态**

| 状态 | 说明 |
|------|------|
| `closed` | 关闭状态，正常允许调用 |
| `open` | 打开状态，拒绝调用 |
| `half_open` | 半开状态，允许部分调用尝试恢复 |

**方法**

#### `async call(func: Callable, *args, **kwargs) -> Any`
通过断路器调用函数。

#### `get_state() -> dict[str, Any]`
获取断路器状态。

---

### FallbackHandler

降级处理器，在主函数失败时使用备选方案。

```python
from core.learning.error_handling import FallbackHandler

handler = FallbackHandler()

# 注册降级函数
async def fallback_function():
    return "fallback_result"

handler.register_fallback("my_service", fallback_function)

# 使用主函数和降级
async def main_function():
    # 可能失败的操作
    return await risky_operation()

result = await handler.execute_with_fallback(
    name="my_service",
    primary_func=main_function
)

# 获取统计信息
stats = handler.get_statistics()
```

**方法**

#### `async execute_with_fallback(name: str, primary_func: Callable) -> Any`
执行主函数，失败时使用降级函数。

- **参数**:
  - `name`: 操作名称（用于查找降级函数）
  - `primary_func`: 主函数
- **返回**: 操作结果

#### `register_fallback(name: str, fallback_func: Callable) -> None`
注册降级函数。

#### `get_statistics() -> dict[str, Any]`
获取统计信息。

---

## 持久化 API

### StorageBackend

存储后端类型枚举。

```python
from core.learning.persistence_manager import StorageBackend

backend = StorageBackend.FILE     # JSON文件存储
# backend = StorageBackend.REDIS  # Redis缓存
# backend = StorageBackend.POSTGRESQL  # PostgreSQL
# backend = StorageBackend.NEO4J  # Neo4j图数据库
```

---

### LearningPersistenceManager

学习数据持久化管理器，支持多种存储后端。

```python
from core.learning.persistence_manager import LearningPersistenceManager, StorageBackend

# 创建管理器
manager = LearningPersistenceManager(backend=StorageBackend.FILE)

# 初始化
await manager.initialize(base_path="data/learning")

# 保存学习经验
record_id = await manager.save_experience(
    agent_id="agent_123",
    experience={
        "task": "patent_analysis",
        "action": "use_advanced_model",
        "result": {"accuracy": 0.95}
    },
    metadata={"timestamp": "..."},
    ttl=3600  # 1小时过期
)

# 保存学习模式
pattern_id = await manager.save_pattern(
    agent_id="agent_123",
    pattern={
        "type": "optimization_pattern",
        "description": "在高负载时使用简化模型"
    }
)

# 保存知识
knowledge_id = await manager.save_knowledge(
    agent_id="agent_123",
    knowledge={
        "fact": "模型X在场景Y下表现更好"
    }
)

# 加载数据
experiences = await manager.load_experiences("agent_123", limit=100)
patterns = await manager.load_patterns("agent_123", limit=50)
knowledge = await manager.load_knowledge("agent_123", limit=1000)

# 获取统计信息
stats = await manager.get_statistics("agent_123")
print(stats)
# {
#     "agent_id": "agent_123",
#     "total_experiences": 150,
#     "total_patterns": 10,
#     "total_knowledge": 25,
#     "backend_type": "file"
# }

# 清空智能体数据
await manager.clear_agent_data("agent_123")
```

**方法**

#### `async initialize(**kwargs) -> bool`
初始化持久化后端。

- **FILE后端参数**:
  - `base_path`: 基础路径（默认: "data/learning"）
- **REDIS后端参数**:
  - `redis_client`: Redis客户端实例

#### `async save_experience(agent_id, experience, metadata=None, ttl=None) -> str`
保存学习经验。

#### `async save_pattern(agent_id, pattern, metadata=None) -> str`
保存学习模式。

#### `async save_knowledge(agent_id, knowledge, metadata=None) -> str`
保存知识。

#### `async load_experiences(agent_id, limit=1000) -> list[dict]`
加载学习经验。

#### `async load_patterns(agent_id, limit=100) -> list[dict]`
加载学习模式。

#### `async load_knowledge(agent_id, limit=1000) -> list[dict]`
加载知识。

#### `async clear_agent_data(agent_id) -> bool`
清空智能体所有数据。

#### `async get_statistics(agent_id) -> dict`
获取统计信息。

---

## 输入验证 API

### InputValidator

统一的输入验证器。

```python
from core.learning.input_validator import get_input_validator

validator = get_input_validator()

# 验证学习输入
result = await validator.validate_learning_input(
    context={"task": "patent_search", "data": "..."},
    action="search_patents",
    result={"found": 100},
    reward=0.8
)

if result.is_valid:
    print("验证通过")
else:
    print(f"验证失败: {result.errors}")
```

**验证规则**

| 字段 | 规则 |
|------|------|
| `context` | 最大10MB，最大深度10层 |
| `action` | 最大长度100字符 |
| `result` | 自动序列化和大小检查 |
| `reward` | -1.0到1.0范围 |

**ValidationResult 属性**

| 属性 | 类型 | 说明 |
|------|------|------|
| `is_valid` | `bool` | 是否验证通过 |
| `errors` | `list[str]` | 错误列表 |
| `warnings` | `list[str]` | 警告列表 |

---

## 自主学习 API

### AutonomousLearningSystem

自主学习系统核心类。

```python
from core.learning.autonomous_learning_system import AutonomousLearningSystem

system = AutonomousLearningSystem(agent_id="my_agent")

# 从经验中学习
experience = await system.learn_from_experience(
    context={"task": "document_analysis", "complexity": "high"},
    action="use_advanced_model",
    result={"accuracy": 0.95, "execution_time": 1.5},
    reward=0.9
)

# 分析性能
analysis = await system.analyze_performance()
print(analysis)
# {
#     "trends": {...},
#     "anomalies": [...],
#     "recommendations": [...]
# }

# 创建A/B测试
experiment_id = await system.create_ab_test(
    name="model_comparison",
    description="比较模型性能",
    control_config={"model": "baseline"},
    treatment_configs=[{"model": "experimental"}],
    success_metric="accuracy"
)

# 获取学习指标
metrics = await system.get_learning_metrics()
print(metrics)
# {
#     "learning": {
#         "total_cycles": 100,
#         "total_experiences": 1000,
#         "optimizations_applied": 5
#     },
#     "performance": {
#         "current_avg_reward": 0.85,
#         "current_success_rate": 0.92
#     }
# }
```

**核心方法**

#### `async learn_from_experience(context, action, result, reward=None) -> LearningExperience`
从经验中学习。

- **参数**:
  - `context`: 上下文信息
  - `action`: 执行的动作
  - `result`: 执行结果
  - `reward`: 奖励值（可选，自动计算）
- **返回**: `LearningExperience` 对象

#### `async analyze_performance() -> dict`
分析性能趋势。

#### `async create_ab_test(name, description, control_config, treatment_configs, success_metric) -> str`
创建A/B测试。

#### `async get_learning_metrics() -> dict`
获取学习指标。

---

## 使用示例

### 完整的自主学习流程

```python
import asyncio
from core.learning.autonomous_learning_system import AutonomousLearningSystem
from core.learning.concurrency_control import ConcurrencyController
from core.learning.error_handling import RetryHandler
from core.learning.persistence_manager import LearningPersistenceManager, StorageBackend

async def autonomous_learning_example():
    # 初始化组件
    system = AutonomousLearningSystem(agent_id="smart_agent")
    controller = ConcurrencyController()
    retry_handler = RetryHandler()
    persistence = LearningPersistenceManager(StorageBackend.FILE)
    await persistence.initialize()

    # 定义学习任务
    async def learning_task(task_data):
        context = {"task": task_data["type"], "data": task_data}

        # 带重试执行
        async def execute():
            # 模拟任务执行
            await asyncio.sleep(0.1)
            return {"status": "success", "accuracy": 0.9}

        result = await retry_handler.execute_with_retry(execute)

        # 从经验中学习
        experience = await system.learn_from_experience(
            context=context,
            action="process_task",
            result=result,
            reward=0.9 if result["status"] == "success" else -0.5
        )

        # 持久化经验
        await persistence.save_experience(
            agent_id="smart_agent",
            experience=experience.to_dict()
        )

        return result

    # 并发执行多个学习任务
    tasks = [
        controller.submit_task(lambda td=td: learning_task(td))
        for td in [{"type": "task1"}, {"type": "task2"}, {"type": "task3"}]
    ]

    results = await asyncio.gather(*tasks)

    # 分析性能
    metrics = await system.get_learning_metrics()
    print(f"学习完成: {metrics['learning']['total_experiences']}条经验")

    # 关闭控制器
    await controller.shutdown()

asyncio.run(autonomous_learning_example())
```

---

## 性能指标

基于压测结果（2026-01-28）：

| 模块 | 操作 | 吞吐量 |
|------|------|--------|
| 并发控制 | 任务处理 | ~70,000 任务/秒 |
| 错误处理 | 重试操作 | ~500,000 次/秒 |
| 持久化 | 写入 | ~6,000 记录/秒 |
| 持久化 | 读取 | ~170,000 记录/秒 |
| 输入验证 | 验证操作 | ~150,000 次/秒 |

---

## 最佳实践

### 1. 并发控制

```python
# 根据实际资源调整配置
config = ConcurrencyConfig(
    max_concurrent_tasks=min(32, (os.cpu_count() or 4) * 4),
    max_operations_per_second=1000,
    task_timeout=30.0
)
```

### 2. 错误处理

```python
# 区分临时和永久错误
async def operation():
    try:
        return await risky_call()
    except ConnectionError as e:
        raise TransientError("连接失败") from e
    except ValueError as e:
        raise PermanentError("数据无效") from e
```

### 3. 持久化

```python
# 使用适当的TTL
await manager.save_experience(
    agent_id="agent",
    experience=exp,
    ttl=86400  # 1天，长期保存的知识不设置TTL
)
```

---

## 相关文档

- [测试指南](../../tests/core/learning/TEST_GUIDE.md)
- [测试报告](../../tests/core/learning/TEST_REPORT.md)
- [配置管理](../../config/athena_development.yaml)
