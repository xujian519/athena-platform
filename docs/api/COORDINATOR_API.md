# Coordinator模式API文档

**版本**: 1.0.0
**最后更新**: 2026-04-20

---

## 目录

- [核心类](#核心类)
- [数据类](#数据类)
- [枚举类](#枚举类)
- [调度策略](#调度策略)
- [高级功能](#高级功能)

---

## 核心类

### Coordinator

多Agent系统的核心协调器。

#### 初始化

```python
from core.coordinator import Coordinator, CoordinatorConfig

config = CoordinatorConfig(
    max_concurrent_tasks=10,
    task_timeout=300,
    enable_load_balancing=True,
)

coordinator = Coordinator(config=config)
```

#### Agent管理方法

##### register_agent()

注册Agent到协调器。

```python
register_agent(agent: AgentInfo) -> bool
```

**参数**:
- `agent`: Agent信息对象

**返回**:
- `bool`: 是否成功注册

**示例**:
```python
agent = AgentInfo(
    agent_id="agent-001",
    name="检索Agent",
    capabilities=["search"],
)
coordinator.register_agent(agent)
```

##### unregister_agent()

注销Agent。

```python
unregister_agent(agent_id: str) -> bool
```

**参数**:
- `agent_id`: Agent ID

**返回**:
- `bool`: 是否成功注销

##### get_agent()

获取Agent信息。

```python
get_agent(agent_id: str) -> AgentInfo | None
```

##### list_agents()

列出所有Agent。

```python
list_agents() -> list[AgentInfo]
```

##### get_agents_by_capability()

按能力获取Agent。

```python
get_agents_by_capability(capability: str) -> list[AgentInfo]
```

#### 任务管理方法

##### submit_task()

提交任务。

```python
submit_task(
    task_id: str,
    task_type: str,
    payload: dict[str, Any],
    priority: int = 1,
) -> TaskAssignment | None
```

**参数**:
- `task_id`: 任务ID
- `task_type`: 任务类型
- `payload`: 任务数据
- `priority`: 任务优先级（1-10，越高越优先）

**返回**:
- `TaskAssignment | None`: 任务分配对象

##### complete_task()

完成任务。

```python
complete_task(
    task_id: str,
    agent_id: str,
    result: dict[str, Any],
) -> bool
```

##### fail_task()

标记任务失败。

```python
fail_task(
    task_id: str,
    agent_id: str,
    error: str,
) -> bool
```

##### get_task_assignment()

获取任务分配。

```python
get_task_assignment(task_id: str) -> TaskAssignment | None
```

##### get_pending_tasks()

获取待处理任务。

```python
get_pending_tasks() -> list[TaskAssignment]
```

#### 通信方法

##### send_message()

发送点对点消息。

```python
send_message(
    sender: str,
    receiver: str,
    content: Any,
    priority: MessagePriority = MessagePriority.NORMAL,
) -> bool
```

##### broadcast_message()

广播消息。

```python
broadcast_message(
    sender: str,
    content: Any,
    priority: MessagePriority = MessagePriority.NORMAL,
) -> int
```

**返回**:
- `int`: 接收者数量

##### get_pending_messages()

获取待处理消息。

```python
get_pending_messages(agent_id: str) -> list[Message]
```

#### 冲突解决方法

##### detect_conflict()

检测冲突。

```python
detect_conflict(
    conflict_type: ConflictType,
    agents: list[str],
    resource_id: str | None = None,
    description: str = "",
) -> ConflictInfo | None
```

##### resolve_conflict()

解决冲突。

```python
resolve_conflict(
    conflict_id: str,
    strategy: ConflictResolutionStrategy,
) -> bool
```

##### get_active_conflicts()

获取活跃冲突。

```python
get_active_conflicts() -> list[ConflictInfo]
```

#### 状态方法

##### get_state()

获取协调器状态。

```python
get_state() -> dict[str, Any]
```

**返回**:
```python
{
    "total_agents": int,        # 总Agent数
    "active_agents": int,       # 活跃Agent数
    "total_tasks": int,         # 总任务数
    "pending_tasks": int,       # 待处理任务数
    "active_conflicts": int,    # 活跃冲突数
}
```

##### get_metrics()

获取指标统计。

```python
get_metrics() -> dict[str, int]
```

---

### AdvancedCoordinator

高级Coordinator，提供依赖管理、重试、超时等功能。

#### 初始化

```python
from core.coordinator import AdvancedCoordinator

advanced = AdvancedCoordinator(coordinator)
```

#### 依赖管理方法

##### add_dependency()

添加任务依赖。

```python
add_dependency(dependency: TaskDependency) -> bool
```

##### check_dependencies()

检查依赖是否满足。

```python
check_dependencies(task_id: str) -> bool
```

##### mark_task_completed()

标记任务完成。

```python
mark_task_completed(task_id: str) -> None
```

#### 重试方法

##### set_retry_config()

设置重试配置。

```python
set_retry_config(task_id: str, config: TaskRetryConfig) -> None
```

##### schedule_retry()

安排任务重试。

```python
schedule_retry(assignment: TaskAssignment) -> bool
```

##### get_ready_retries()

获取可重试任务。

```python
get_ready_retries() -> list[TaskAssignment]
```

#### 超时方法

##### set_timeout()

设置任务超时。

```python
set_timeout(task_id: str, timeout_seconds: int) -> None
```

##### check_timeouts()

检查超时任务。

```python
check_timeouts() -> list[str]
```

##### start_timeout_monitor()

启动超时监控。

```python
start_timeout_monitor() -> None
```

##### stop_timeout_monitor()

停止超时监控。

```python
stop_timeout_monitor() -> None
```

#### 任务链方法

##### create_task_chain()

创建任务链。

```python
create_task_chain(tasks: list[dict[str, Any]]) -> list[str]
```

**参数**:
- `tasks`: 任务列表，每个任务是一个字典

**返回**:
- `list[str]`: 任务ID列表

---

## 数据类

### AgentInfo

Agent信息数据类。

```python
@dataclass
class AgentInfo:
    agent_id: str
    name: str
    capabilities: list[str]
    max_concurrent_tasks: int = 5
    status: AgentStatus = AgentStatus.IDLE
    current_tasks: int = 0
    completed_tasks: int = 0
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    last_heartbeat: datetime = field(default_factory=datetime.now)
```

**方法**:

##### can_handle_task()

检查是否能处理指定类型的任务。

```python
can_handle_task(task_type: str) -> bool
```

##### increment_tasks()

增加当前任务数。

```python
increment_tasks() -> None
```

##### decrement_tasks()

减少当前任务数。

```python
decrement_tasks() -> None
```

### TaskAssignment

任务分配数据类。

```python
@dataclass
class TaskAssignment:
    task_id: str
    agent_id: str
    task_type: str
    priority: int = 1
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

### Message

消息数据类。

```python
@dataclass
class Message:
    message_id: str
    sender: str
    receiver: str
    content: Any
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)
```

### ConflictInfo

冲突信息数据类。

```python
@dataclass
class ConflictInfo:
    conflict_id: str
    conflict_type: ConflictType
    agents: list[str]
    resource_id: str | None = None
    description: str = ""
    status: str = "detected"
    resolution_strategy: ConflictResolutionStrategy | None = None
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: datetime | None = None
```

### TaskDependency

任务依赖数据类。

```python
@dataclass
class TaskDependency:
    task_id: str
    depends_on: list[str]
    wait_mode: str = "all"  # "all" 或 "any"
```

### TaskRetryConfig

任务重试配置。

```python
@dataclass
class TaskRetryConfig:
    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0
```

---

## 枚举类

### AgentStatus

Agent状态枚举。

```python
class AgentStatus(Enum):
    IDLE = "idle"          # 空闲
    BUSY = "busy"          # 忙碌
    OFFLINE = "offline"    # 离线
    ERROR = "error"        # 错误
```

### MessagePriority

消息优先级枚举。

```python
class MessagePriority(IntEnum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
```

### ConflictType

冲突类型枚举。

```python
class ConflictType(Enum):
    RESOURCE = "resource"  # 资源冲突
    DATA = "data"          # 数据冲突
    TIMING = "timing"      # 时序冲突
    ACCESS = "access"      # 访问冲突
```

### ConflictResolutionStrategy

冲突解决策略枚举。

```python
class ConflictResolutionStrategy(Enum):
    PRIORITY = "priority"      # 按优先级
    NEGOTIATE = "negotiate"    # 协商解决
    DEFER = "defer"            # 延迟处理
    ESCALATE = "escalate"      # 上报处理
```

---

## 调度策略

### StrategyFactory

调度策略工厂。

```python
from core.coordinator import StrategyFactory

# 创建策略
strategy = StrategyFactory.create_strategy("round_robin")

# 获取可用策略
strategies = StrategyFactory.get_available_strategies()
```

### 可用策略

| 策略名称 | 说明 | 参数 |
|---------|------|------|
| round_robin | 轮询调度 | 无 |
| least_loaded | 最少负载 | 无 |
| priority | 优先级 | 无 |
| weighted | 加权调度 | weight_key: str = "weight" |

### 自定义策略

```python
from core.coordinator.scheduler import SchedulingStrategy

class CustomStrategy(SchedulingStrategy):
    def select_agent(self, agents, task):
        # 实现选择逻辑
        return selected_agent

    def get_name(self):
        return "custom"

# 注册
StrategyFactory.register_strategy("custom", CustomStrategy)
```

---

## 全局函数

### get_coordinator()

获取全局Coordinator实例。

```python
from core.coordinator import get_coordinator

coordinator = get_coordinator()
```

---

## 异常

所有方法在失败时返回`False`或`None`，不抛出异常。错误信息会记录到日志中。
