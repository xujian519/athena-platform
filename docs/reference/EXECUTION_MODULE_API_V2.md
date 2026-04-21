# 执行模块 API 文档 (v2.0.0)

**版本**: 2.0.0
**更新日期**: 2026-01-27
**作者**: Athena AI系统

---

## 📋 概述

执行模块 (`core.execution`) 提供**统一的任务执行框架**，支持多种执行模式：

- ✅ **任务调度**: 基于优先级的智能任务调度
- ✅ **并行执行**: 多任务并行处理能力
- ✅ **资源管理**: 动态资源分配和监控
- ✅ **工作流支持**: 复杂任务依赖关系管理
- ✅ **容错机制**: 自动重试和错误处理

---

## 🎯 核心改进 (v2.0.0)

### 1. 统一类型定义

所有类型定义现在位于 `core/execution/shared_types.py`，确保整个模块的类型一致性。

#### 问题修复

| 问题 | 修复前 | 修复后 |
|------|--------|--------|
| TaskPriority 冲突 | 三个文件定义不同，值相反 | 统一定义，值越小优先级越高 |
| Task 类不兼容 | 字段冲突，无法跨模块传递 | 统一 Task 类支持多种模式 |
| 类型重复 | 多处重复定义 | 单一来源 `shared_types.py` |

### 2. TaskPriority 枚举

```python
class TaskPriority(Enum):
    CRITICAL = 1     # 关键任务，最高优先级
    HIGH = 2         # 高优先级
    NORMAL = 3       # 普通优先级（默认）
    LOW = 4          # 低优先级
    BACKGROUND = 5   # 后台任务，最低优先级
```

**关键特性**：
- ✅ 数值越小，优先级越高
- ✅ 与优先队列排序兼容
- ✅ 所有模块使用相同定义

### 3. 统一的 Task 类

`Task` 类支持两种使用方式：

#### 方式 1: 基于动作的任务

适用于 `ExecutionEngine` 和 `EnhancedExecutionEngine`：

```python
from core.execution.shared_types import Task, ActionType

task = Task(
    task_id="api_call_001",
    name="调用外部API",
    action_type=ActionType.API_CALL,
    action_data={
        "url": "https://api.example.com/data",
        "method": "GET",
    },
    priority=TaskPriority.HIGH,
)
```

#### 方式 2: 基于函数的任务

适用于 `OptimizedExecutionModule` 和 `TaskManager`：

```python
from core.execution.shared_types import Task

async def my_function(x, y):
    return x + y

task = Task(
    task_id="func_001",
    name="计算任务",
    function=my_function,
    args=(1, 2),
    kwargs={},
    priority=TaskPriority.NORMAL,
)
```

---

## 📚 核心 API

### 1. Task 类

#### 创建任务

```python
from core.execution.shared_types import Task, TaskPriority, TaskStatus, ActionType

# 最小任务
task = Task(
    task_id="unique_id",
    name="任务名称",
)

# 带优先级和超时
task = Task(
    task_id="unique_id",
    name="任务名称",
    priority=TaskPriority.HIGH,
    timeout=300.0,  # 5分钟超时
    max_retries=3,
)

# 基于动作的任务
task = Task(
    task_id="unique_id",
    name="API调用",
    action_type=ActionType.API_CALL,
    action_data={"url": "https://api.example.com"},
)

# 基于函数的任务
async def my_handler():
    return {"status": "ok"}

task = Task(
    task_id="unique_id",
    name="异步任务",
    function=my_handler,
    args=(),
    kwargs={},
)

# 带依赖的任务
task = Task(
    task_id="unique_id",
    name="有依赖的任务",
    dependencies=["task_001", "task_002"],
)
```

#### Task 方法

```python
# 检查是否可以开始
can_start = task.can_start(completed_tasks)

# 开始任务
task.start()
# → status = TaskStatus.RUNNING
# → started_at = 当前时间

# 完成任务
task.complete(success=True, data="result")
# → status = TaskStatus.COMPLETED
# → completed_at = 当前时间

task.complete(success=False, error="错误信息")
# → status = TaskStatus.FAILED

# 重试任务
if task.retry():
    # → retry_count += 1
    # → status = TaskStatus.PENDING
```

#### Task 属性

| 属性 | 类型 | 描述 |
|------|------|------|
| `task_id` | `str` | 任务唯一标识 |
| `name` | `str` | 任务名称 |
| `priority` | `TaskPriority` | 任务优先级 |
| `status` | `TaskStatus` | 任务状态 |
| `function` | `Callable \| None` | 要执行的函数 |
| `action_type` | `str \| ActionType` | 动作类型 |
| `action_data` | `dict` | 动作数据 |
| `args` | `tuple` | 函数位置参数 |
| `kwargs` | `dict` | 函数关键字参数 |
| `dependencies` | `list[str]` | 依赖任务ID列表 |
| `timeout` | `float \| None` | 超时时间（秒） |
| `max_retries` | `int` | 最大重试次数 |
| `retry_count` | `int` | 当前重试次数 |
| `created_at` | `datetime` | 创建时间 |
| `started_at` | `datetime \| None` | 开始时间 |
| `completed_at` | `datetime \| None` | 完成时间 |
| `result` | `Any` | 执行结果 |
| `error` | `str \| None` | 错误信息 |
| `progress` | `float` | 进度 (0.0-1.0) |
| `metadata` | `dict` | 元数据 |

---

### 2. TaskQueue 类

#### 创建队列

```python
from core.execution.shared_types import TaskQueue

queue = TaskQueue(max_size=10000)
```

#### 队列操作

```python
# 入队
task = Task(task_id="001", name="任务1", priority=TaskPriority.HIGH)
success = queue.enqueue(task)

# 出队（按优先级）
task = queue.dequeue()

# 获取特定任务
task = queue.get_task("task_id")

# 清空队列
queue.clear()

# 获取队列大小
size = queue.size()

# 获取队列摘要
summary = queue.get_summary()
# {
#     "size": 10,
#     "max_size": 10000,
#     "priority_distribution": {
#         "CRITICAL": 1,
#         "HIGH": 3,
#         "NORMAL": 5,
#         "LOW": 1,
#         "BACKGROUND": 0
#     }
# }
```

---

### 3. TaskResult 类

```python
from core.execution.shared_types import TaskResult, TaskStatus

result = TaskResult(
    task_id="task_001",
    status=TaskStatus.COMPLETED,
    result="成功结果",
    duration=1.5,
    metrics={"cpu_time": 0.8, "memory_mb": 128},
)
```

---

### 4. Workflow 类

```python
from core.execution.shared_types import Workflow, Task, TaskPriority

workflow = Workflow(
    id="workflow_001",
    name="数据处理工作流",
    parallel=True,
    max_concurrent=5,
    timeout=600.0,
)

# 添加任务
workflow.tasks.append(
    Task(task_id="task_001", name="步骤1", priority=TaskPriority.HIGH)
)
```

---

### 5. 异常类

```python
from core.execution.shared_types import (
    ExecutionError,
    TaskExecutionError,
    TaskTimeoutError,
    DeadlockDetectedError,
    DependencyCycleError,
    TaskValidationError,
)

# 使用异常
try:
    # 执行任务
    pass
except TaskTimeoutError:
    # 处理超时
    pass
except TaskExecutionError as e:
    # 处理执行错误
    pass
except ExecutionError:
    # 处理一般执行错误
    pass
```

---

## 🔧 执行引擎

### EnhancedExecutionEngine

```python
from core.execution.enhanced_execution_engine import EnhancedExecutionEngine

# 创建引擎
engine = EnhancedExecutionEngine(
    agent_id="my_agent",
    config={
        "max_workers": 10,
        "max_concurrent": 20,
        "task_timeout": 300.0,
    }
)

# 初始化
await engine.initialize()

# 启动
await engine.start()

# 执行任务
result = await engine.execute_task(task)

# 获取统计信息
stats = engine.get_statistics()

# 关闭
await engine.shutdown()
```

### ParallelExecutor

```python
from core.execution.parallel_executor import ParallelExecutor, TaskPriority

# 创建执行器
executor = ParallelExecutor(
    max_workers=10,
    max_concurrent_tasks=20,
)

# 提交任务
await executor.submit_task(
    task_id="task_001",
    task_name="并行任务",
    coroutine=my_async_function,
    priority=TaskPriority.HIGH,
)

# 执行所有任务
results = await executor.execute_all()

# 获取执行报告
report = executor.get_execution_report()
```

### TaskManager

```python
from core.execution.task_manager import TaskManager

# 创建管理器
manager = TaskManager(config={"max_concurrent_tasks": 10})

# 初始化
await manager.initialize()

# 创建任务
task_id = await manager.create_task(
    name="我的任务",
    function=my_function,
    priority=TaskPriority.HIGH,
)

# 等待任务完成
result = await manager.wait_for_task(task_id)

# 列出任务
tasks = await manager.list_tasks(status=TaskStatus.COMPLETED)

# 关闭
await manager.shutdown()
```

---

## 📖 迁移指南

### 从 v1.x 迁移到 v2.0

#### 1. 更新导入

**旧方式** (已弃用):
```python
from core.execution.types import Task, TaskPriority, TaskStatus
```

**新方式**:
```python
from core.execution.shared_types import Task, TaskPriority, TaskStatus

# 或者从主模块导入（仍然支持）
from core.execution import Task, TaskPriority, TaskStatus
```

#### 2. TaskPriority 值变更

**重要**: `TaskPriority` 的值现在与优先级**成反比**（值越小优先级越高）。

```python
# 旧代码可能有问题
if priority.value > 3:  # 这可能是低优先级
    pass

# 新代码应该这样
if priority.value >= TaskPriority.NORMAL.value:
    pass  # NORMAL 或更低优先级
```

#### 3. Task 类统一

**旧代码**（使用不同的 Task 类）:
```python
from core.execution.types import Task as OldTask
from core.execution.optimized_execution_module.types import Task as NewTask

# 这两个类不兼容！
```

**新代码**（统一 Task 类）:
```python
from core.execution.shared_types import Task
from core.execution import Task  # 相同的类

# 所有模块使用同一个 Task 类
```

---

## 🧪 测试

### 运行测试

```bash
# 运行所有执行模块测试
pytest tests/core/execution/ -v

# 运行特定测试
pytest tests/core/execution/test_shared_types.py -v

# 查看覆盖率
pytest tests/core/execution/ --cov=core.execution --cov-report=html
```

### 测试覆盖

当前测试覆盖：
- ✅ TaskPriority 枚举
- ✅ TaskStatus 枚举
- ✅ ActionType 枚举
- ✅ Task 类所有方法
- ✅ TaskQueue 所有操作
- ✅ TaskResult 创建
- ✅ Workflow 创建
- ✅ 异常类
- ✅ ExecutionEngine 生命周期
- ✅ 类型一致性检查
- ✅ 集成测试

---

## 🔍 类型参考

### ActionType

```python
class ActionType(Enum):
    COMMAND = "command"           # Shell命令
    FUNCTION = "function"         # 函数调用
    API_CALL = "api_call"         # API请求
    FILE_OPERATION = "file_operation"  # 文件操作
    DATABASE = "database"         # 数据库操作
    HTTP_REQUEST = "http_request" # HTTP请求
    WORKFLOW = "workflow"         # 工作流
    CUSTOM = "custom"             # 自定义
```

### TaskStatus

```python
class TaskStatus(Enum):
    PENDING = "pending"       # 等待执行
    QUEUED = "queued"         # 已排队
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消
    TIMEOUT = "timeout"       # 超时
    PAUSED = "paused"         # 暂停
```

### ResourceType

```python
class ResourceType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK = "network"
    GPU = "gpu"
```

---

## ⚠️ 注意事项

### 1. 优先级排序

`TaskPriority` 的值与优先级**成反比**：
- `CRITICAL = 1` （最高优先级）
- `BACKGROUND = 5` （最低优先级）

在使用优先队列时需要注意：
```python
import heapq

# 错误方式
tasks = [(task.priority.value, task) for task in tasks]
heapq.heapify(tasks)  # 这会按值从小到大排序，符合预期

# 或者使用负值（对于最大堆）
tasks = [(-task.priority.value, task) for task in tasks]
```

### 2. 任务状态转换

任务状态遵循以下转换规则：

```
PENDING → QUEUED → RUNNING → COMPLETED
                        ↘ FAILED → PENDING (重试)
                        ↘ TIMEOUT
                        ↘ CANCELLED
```

### 3. 资源管理

线程池和进程池需要正确关闭：

```python
# 正确方式
async with engine:
    await engine.initialize()
    await engine.start()
    # ... 使用引擎
    # 自动关闭

# 或者手动关闭
try:
    await engine.initialize()
    # ... 使用引擎
finally:
    await engine.shutdown()
```

---

## 📞 支持

如有问题或建议，请联系：

- **作者**: Athena AI系统
- **版本**: 2.0.0
- **更新日期**: 2026-01-27

---

**文档结束**
