# 任务管理器API参考文档

**版本**: 1.0.0
**更新日期**: 2026-04-20
**适用对象**: 开发者

---

## 📚 目录

1. [概述](#概述)
2. [核心类](#核心类)
3. [数据模型](#数据模型)
4. [异常处理](#异常处理)
5. [使用示例](#使用示例)
6. [最佳实践](#最佳实践)

---

## 概述

任务管理器是Athena平台P1阶段的核心模块，整合P0系统的Skills、Plugins和会话记忆系统，提供统一的任务管理接口。

### 核心特性

- ✅ **任务生命周期管理**: 创建、分配、执行、完成、取消
- ✅ **优先级队列**: 基于优先级的智能调度
- ✅ **任务依赖**: 支持复杂的任务依赖关系
- ✅ **状态持久化**: 文件存储，支持恢复
- ✅ **任务监控**: 实时指标和报告
- ✅ **自动重试**: 失败任务自动重试机制
- ✅ **观察者模式**: 任务状态变化通知

---

## 核心类

### TaskManager

任务管理器主类，提供统一的任务管理接口。

```python
from core.tasks.manager import TaskManager, get_task_manager
```

#### 初始化

```python
def __init__(
    storage: TaskStorage | None = None,
    enable_auto_cleanup: bool = True,
    cleanup_interval: int = 3600,
):
    """初始化任务管理器

    Args:
        storage: 任务存储实例
        enable_auto_cleanup: 是否启用自动清理
        cleanup_interval: 清理间隔（秒）
    """
```

#### 任务创建

```python
def create_task(
    title: str,
    description: str = "",
    priority: TaskPriority = TaskPriority.NORMAL,
    assigned_to: str | None = None,
    created_by: str | None = None,
    session_id: str | None = None,
    skill_id: str | None = None,
    deadline: datetime | None = None,
    dependencies: list[str] | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Task:
    """创建新任务"""
```

#### 任务查询

```python
def get_task(self, task_id: str) -> Task | None:
    """获取任务"""

def get_tasks_by_status(self, status: TaskStatus) -> list[Task]:
    """按状态获取任务"""

def get_tasks_by_agent(self, agent_id: str) -> list[Task]:
    """按Agent获取任务"""

def get_tasks_by_session(self, session_id: str) -> list[Task]:
    """按会话获取任务"""

def get_ready_tasks(self) -> list[Task]:
    """获取所有准备就绪的任务"""

def get_blocked_tasks(self) -> list[Task]:
    """获取所有被阻塞的任务"""

def get_overdue_tasks(self) -> list[Task]:
    """获取所有过期任务"""
```

#### 任务操作

```python
def assign_task(self, task_id: str, agent_id: str) -> bool:
    """分配任务给Agent"""

def start_task(self, task_id: str) -> bool:
    """开始执行任务"""

def complete_task(self, task_id: str, result: TaskResult) -> bool:
    """完成任务"""

def fail_task(self, task_id: str, error: str) -> bool:
    """标记任务失败"""

def cancel_task(self, task_id: str) -> bool:
    """取消任务"""
```

#### 任务调度

```python
def get_next_task(self, agent_id: str | None = None) -> Task | None:
    """获取下一个可执行的任务"""

def get_pending_count(self) -> int:
    """获取等待中的任务数量"""

def is_empty(self) -> bool:
    """检查队列是否为空"""
```

#### 监控和清理

```python
def get_metrics(self) -> TaskMetrics:
    """获取任务指标"""

def cleanup_completed(self, keep_days: int = 7) -> int:
    """清理已完成的任务"""

def add_observer(self, observer: Callable[[Task, str], None]) -> None:
    """添加任务状态观察者"""

def remove_observer(self, observer: Callable[[Task, str], None]) -> None:
    """移除任务状态观察者"""
```

#### 生命周期管理

```python
def start_auto_cleanup(self) -> None:
    """启动自动清理"""

def stop_auto_cleanup(self) -> None:
    """停止自动清理"""

def shutdown(self) -> None:
    """关闭任务管理器"""
```

---

### TaskScheduler

任务调度器，负责任务的调度和优先级管理。

```python
from core.tasks.manager import TaskScheduler
```

#### 核心方法

```python
def schedule_task(self, task: Task) -> bool:
    """调度任务"""

def get_next_task(self) -> Task | None:
    """获取下一个可执行的任务"""

def start_task(self, task_id: str, agent_id: str | None = None) -> bool:
    """开始执行任务"""

def complete_task(self, task_id: str, result: TaskResult) -> bool:
    """完成任务"""

def fail_task(self, task_id: str, error: str) -> bool:
    """标记任务失败"""

def cancel_task(self, task_id: str) -> bool:
    """取消任务"""
```

---

### TaskStorage

任务存储基类，提供持久化功能。

```python
from core.tasks.manager import TaskStorage, FileTaskStorage
```

#### FileTaskStorage

文件存储实现。

```python
def __init__(self, storage_dir: str | Path | None = None):
    """初始化文件存储

    Args:
        storage_dir: 存储目录路径
    """
```

#### 存储方法

```python
def save(self, task: Task) -> bool:
    """保存任务"""

def load(self, task_id: str) -> Task | None:
    """加载任务"""

def delete(self, task_id: str) -> bool:
    """删除任务"""

def exists(self, task_id: str) -> bool:
    """检查任务是否存在"""

def load_all(self) -> dict[str, Task]:
    """加载所有任务"""

def load_by_status(self, status: TaskStatus) -> list[Task]:
    """按状态加载任务"""

def load_by_agent(self, agent_id: str) -> list[Task]:
    """按Agent ID加载任务"""

def load_by_session(self, session_id: str) -> list[Task]:
    """按会话ID加载任务"""

def clear(self) -> bool:
    """清空所有任务"""

def get_stats(self) -> dict[str, Any]:
    """获取存储统计信息"""
```

---

## 数据模型

### Task

任务对象，包含任务的所有信息。

```python
@dataclass
class Task:
    """任务对象"""

    id: str                                          # 任务唯一标识
    title: str                                      # 任务标题
    description: str = ""                           # 任务描述
    status: TaskStatus = TaskStatus.PENDING         # 任务状态
    priority: TaskPriority = TaskPriority.NORMAL    # 任务优先级
    created_at: datetime                            # 创建时间
    updated_at: datetime                            # 更新时间
    started_at: datetime | None = None              # 开始时间
    completed_at: datetime | None = None            # 完成时间
    deadline: datetime | None = None                # 截止时间
    assigned_to: str | None = None                  # 分配给的Agent ID
    created_by: str | None = None                   # 创建者ID
    session_id: str | None = None                   # 关联的会话ID
    skill_id: str | None = None                     # 关联的技能ID
    dependencies: list[TaskDependency]              # 任务依赖
    dependents: list[str]                           # 依赖此任务的其他任务ID
    result: TaskResult | None = None                # 执行结果
    progress: float = 0.0                           # 进度 (0.0 - 1.0)
    tags: list[str]                                 # 标签
    metadata: dict[str, Any]                        # 元数据
    retry_count: int = 0                            # 重试次数
    max_retries: int = 3                            # 最大重试次数
    timeout_seconds: int | None = None              # 超时时间（秒）
```

#### Task方法

```python
def can_start(self, completed_tasks: set[str]) -> bool:
    """检查任务是否可以开始"""

def add_dependency(self, task_id: str, dependency_type: TaskDependencyType = ...) -> None:
    """添加任务依赖"""

def assign_to(self, agent_id: str) -> None:
    """分配任务给Agent"""

def start(self) -> None:
    """开始执行任务"""

def complete(self, result: TaskResult) -> None:
    """完成任务"""

def fail(self, error: str) -> None:
    """标记任务失败"""

def cancel(self) -> None:
    """取消任务"""

def update_progress(self, progress: float) -> None:
    """更新任务进度"""

def is_overdue(self) -> bool:
    """检查任务是否过期"""

def can_retry(self) -> bool:
    """检查任务是否可以重试"""

def increment_retry(self) -> None:
    """增加重试次数"""

def to_dict(self) -> dict[str, Any]:
    """转换为字典"""

@classmethod
def from_dict(cls, data: dict[str, Any]) -> "Task":
    """从字典创建任务"""
```

### TaskStatus

任务状态枚举。

```python
class TaskStatus(Enum):
    PENDING = "pending"        # 等待执行
    READY = "ready"            # 准备就绪
    ASSIGNED = "assigned"      # 已分配
    RUNNING = "running"        # 执行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"    # 已取消
    BLOCKED = "blocked"        # 阻塞
    TIMEOUT = "timeout"        # 超时
```

### TaskPriority

任务优先级枚举。

```python
class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5
```

### TaskDependency

任务依赖关系。

```python
@dataclass
class TaskDependency:
    task_id: str                              # 依赖的任务ID
    dependency_type: TaskDependencyType       # 依赖类型
    required: bool = True                     # 是否必须依赖
```

### TaskDependencyType

任务依赖类型枚举。

```python
class TaskDependencyType(Enum):
    FINISH_TO_START = "fts"    # 前置任务完成后开始
    START_TO_START = "sts"     # 前置任务开始后开始
    FINISH_TO_FINISH = "ftf"   # 前置任务完成后完成
    START_TO_FINISH = "stf"    # 前置任务开始后完成
```

### TaskResult

任务执行结果。

```python
@dataclass
class TaskResult:
    success: bool                      # 是否成功
    data: dict[str, Any] | None        # 结果数据
    error: str | None                  # 错误信息
    execution_time: float = 0.0        # 执行时间（秒）
    token_usage: int = 0               # Token使用量
    metadata: dict[str, Any]           # 元数据
```

### TaskMetrics

任务指标。

```python
@dataclass
class TaskMetrics:
    total_tasks: int = 0               # 总任务数
    pending_tasks: int = 0             # 等待中的任务
    running_tasks: int = 0             # 运行中的任务
    completed_tasks: int = 0           # 已完成的任务
    failed_tasks: int = 0              # 失败的任务
    blocked_tasks: int = 0             # 阻塞的任务
    average_execution_time: float = 0.0 # 平均执行时间
    total_token_usage: int = 0         # 总Token使用量
```

---

## 异常处理

### 异常层次结构

```
TaskManagerError (基础异常)
├── TaskNotFoundError (任务未找到)
├── TaskDependencyError (任务依赖错误)
├── TaskValidationError (任务验证错误)
├── TaskExecutionError (任务执行错误)
├── TaskStorageError (任务存储错误)
└── TaskSchedulingError (任务调度错误)
```

### 异常使用示例

```python
from core.tasks.manager.exceptions import (
    TaskManagerError,
    TaskNotFoundError,
    TaskDependencyError,
)

try:
    task = manager.get_task("task_id")
    if not task:
        raise TaskNotFoundError("task_id")
except TaskDependencyError as e:
    logger.error(f"任务依赖错误: {e.message}")
except TaskManagerError as e:
    logger.error(f"任务管理错误: {e.message}")
```

---

## 使用示例

### 基本使用

```python
from core.tasks.manager import get_task_manager, TaskPriority
from core.tasks.manager.models import TaskResult
from datetime import datetime, timedelta

# 获取任务管理器
manager = get_task_manager()

# 创建任务
task = manager.create_task(
    title="分析专利CN123456789A",
    description="分析专利的创造性和新颖性",
    priority=TaskPriority.HIGH,
    assigned_to="xiaona",
    created_by="user_123",
    session_id="session_456",
    skill_id="patent_analysis",
    deadline=datetime.now() + timedelta(hours=2),
    tags=["专利", "分析"],
)

# 分配并开始任务
manager.assign_task(task.id, "xiaona")
manager.start_task(task.id)

# 完成任务
result = TaskResult(
    success=True,
    data={"analysis": "专利具有创造性"},
    execution_time=120.5,
    token_usage=1500,
)
manager.complete_task(task.id, result)
```

### 任务依赖

```python
# 创建任务链：检索 -> 分析 -> 报告
retrieval_task = manager.create_task(
    title="检索相关专利",
    priority=TaskPriority.HIGH,
)

analysis_task = manager.create_task(
    title="分析专利",
    dependencies=[retrieval_task.id],
)

report_task = manager.create_task(
    title="生成报告",
    dependencies=[analysis_task.id],
)

# 完成第一个任务后，后续任务自动解除阻塞
manager.start_task(retrieval_task.id)
manager.complete_task(retrieval_task.id, TaskResult(success=True))
```

### 观察者模式

```python
def task_observer(task: Task, event: str):
    """任务状态观察者"""
    print(f"任务 {task.id} 事件: {event}")
    if event == "completed":
        print(f"任务完成，结果: {task.result}")

# 添加观察者
manager.add_observer(task_observer)

# 创建任务（观察者会被通知）
task = manager.create_task(title="测试任务")
```

### 查询和过滤

```python
# 获取所有准备就绪的任务
ready_tasks = manager.get_ready_tasks()

# 获取特定Agent的任务
agent_tasks = manager.get_tasks_by_agent("xiaona")

# 获取特定会话的任务
session_tasks = manager.get_tasks_by_session("session_456")

# 获取过期任务
overdue_tasks = manager.get_overdue_tasks()

# 获取任务指标
metrics = manager.get_metrics()
print(f"总任务数: {metrics.total_tasks}")
print(f"已完成: {metrics.completed_tasks}")
print(f"运行中: {metrics.running_tasks}")
```

### 自动清理

```python
# 启动自动清理（每天清理7天前的已完成任务）
manager.start_auto_cleanup()

# 手动清理
cleaned = manager.cleanup_completed(keep_days=7)
print(f"清理了 {cleaned} 个任务")

# 关闭时停止清理
manager.shutdown()
```

---

## 最佳实践

### 1. 任务ID管理

```python
# 使用UUID自动生成唯一ID
import uuid

task_id = str(uuid.uuid4())
```

### 2. 优先级设置

```python
# 根据紧急程度设置优先级
if deadline < datetime.now() + timedelta(hours=1):
    priority = TaskPriority.CRITICAL
elif deadline < datetime.now() + timedelta(hours=6):
    priority = TaskPriority.URGENT
elif deadline < datetime.now() + timedelta(days=1):
    priority = TaskPriority.HIGH
else:
    priority = TaskPriority.NORMAL
```

### 3. 依赖关系设计

```python
# 使用依赖链确保任务按顺序执行
task1 = manager.create_task(title="第一步")
task2 = manager.create_task(title="第二步", dependencies=[task1.id])
task3 = manager.create_task(title="第三步", dependencies=[task2.id])
```

### 4. 错误处理

```python
# 始终处理任务异常
try:
    manager.start_task(task_id)
except TaskDependencyError:
    logger.warning(f"任务依赖未满足: {task_id}")
except TaskNotFoundError:
    logger.error(f"任务不存在: {task_id}")
```

### 5. 资源清理

```python
# 使用完毕后关闭管理器
try:
    manager = get_task_manager()
    # ... 使用管理器
finally:
    manager.shutdown()
```

### 6. 性能优化

```python
# 批量操作时使用事务
with scheduler._lock:
    for task_data in batch_data:
        task = Task(**task_data)
        scheduler.schedule_task(task)
```

---

**作者**: Athena平台团队
**最后更新**: 2026-04-20
**版本**: 1.0.0
