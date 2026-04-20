# Coordinator模式设计文档

**作者**: Athena平台团队
**创建时间**: 2026-04-20
**版本**: 1.0.0

---

## 概述

Coordinator模式是多Agent系统的核心协调组件，负责Agent注册、任务分配、负载均衡、通信协调、冲突解决和状态同步。

---

## 架构设计

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Coordinator                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Agent Management                         │  │
│  │  - Register/Unregister                               │  │
│  │  - Capability Discovery                              │  │
│  │  - Health Monitoring                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Task Management                         │  │
│  │  - Task Queue (Priority-based)                       │  │
│  │  - Assignment Strategies                             │  │
│  │  - Load Balancing                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Communication                           │  │
│  │  - Point-to-point Messaging                          │  │
│  │  - Broadcast                                         │  │
│  │  - Message Queues                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Conflict Resolution                      │  │
│  │  - Resource Conflicts                                │  │
│  │  - Data Conflicts                                    │  │
│  │  - Resolution Strategies                             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
    ┌────┴────┐    ┌───┴────┐    ┌───┴────┐    ┌───┴────┐
    │ Agent 1 │    │ Agent 2 │    │ Agent 3 │    │ Agent N │
    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

### 核心组件

1. **Coordinator**: 主协调器类
2. **AgentInfo**: Agent信息数据类
3. **TaskAssignment**: 任务分配数据类
4. **Message**: Agent间消息数据类
5. **ConflictInfo**: 冲突信息数据类
6. **AdvancedCoordinator**: 高级功能扩展
7. **SchedulingStrategy**: 调度策略接口

---

## 核心功能

### 1. Agent管理

```python
from core.coordinator import Coordinator, AgentInfo, AgentStatus

# 创建Coordinator
coordinator = Coordinator()

# 注册Agent
agent = AgentInfo(
    agent_id="agent-001",
    name="专利检索Agent",
    capabilities=["patent_search", "patent_analyze"],
    max_concurrent_tasks=5,
)
coordinator.register_agent(agent)

# 查询Agent
agent = coordinator.get_agent("agent-001")
agents = coordinator.list_agents()
capable_agents = coordinator.get_agents_by_capability("patent_search")
```

### 2. 任务分配

```python
# 提交任务
assignment = coordinator.submit_task(
    task_id="task-001",
    task_type="patent_search",
    payload={"query": "人工智能", "limit": 10},
    priority=3,  # 高优先级
)

# 完成任务
coordinator.complete_task(
    task_id="task-001",
    agent_id="agent-001",
    result={"count": 10, "patents": [...]},
)

# 任务失败处理
coordinator.fail_task(
    task_id="task-001",
    agent_id="agent-001",
    error="检索服务不可用",
)
```

### 3. 负载均衡

```python
from core.coordinator import CoordinatorConfig

# 启用负载均衡
config = CoordinatorConfig(enable_load_balancing=True)
coordinator = Coordinator(config)

# 任务会自动分配到负载最少的Agent
for i in range(10):
    coordinator.submit_task(
        task_id=f"task-{i}",
        task_type="patent_search",
        payload={},
    )
```

### 4. 通信协调

```python
from core.coordinator import MessagePriority

# 点对点消息
coordinator.send_message(
    sender="agent-001",
    receiver="agent-002",
    content={"patent_id": "CN123456"},
    priority=MessagePriority.HIGH,
)

# 广播消息
count = coordinator.broadcast_message(
    sender="coordinator",
    content="系统维护通知",
    priority=MessagePriority.URGENT,
)

# 获取待处理消息
messages = coordinator.get_pending_messages("agent-002")
```

### 5. 冲突解决

```python
from core.coordinator import (
    ConflictType,
    ConflictResolutionStrategy,
)

# 检测冲突
conflict = coordinator.detect_conflict(
    conflict_type=ConflictType.RESOURCE,
    agents=["agent-001", "agent-002"],
    resource_id="database-001",
    description="同时访问同一数据库",
)

# 解决冲突
coordinator.resolve_conflict(
    conflict.conflict_id,
    ConflictResolutionStrategy.PRIORITY,
)
```

### 6. 任务依赖

```python
from core.coordinator import AdvancedCoordinator, TaskDependency

advanced = AdvancedCoordinator(coordinator)

# 添加依赖
dependency = TaskDependency(
    task_id="task-analyze",
    depends_on=["task-search"],
    wait_mode="all",
)
advanced.add_dependency(dependency)

# 检查依赖
if advanced.check_dependencies("task-analyze"):
    # 依赖满足，可以执行
    pass

# 标记任务完成
advanced.mark_task_completed("task-search")
```

### 7. 任务重试

```python
from core.coordinator import TaskRetryConfig

# 配置重试
retry_config = TaskRetryConfig(
    max_retries=3,
    retry_delay=1.0,
    backoff_factor=2.0,
)
advanced.set_retry_config("task-001", retry_config)

# 安排重试
advanced.schedule_retry(assignment)

# 获取可重试任务
ready_retries = advanced.get_ready_retries()
```

### 8. 调度策略

```python
from core.coordinator import StrategyFactory

# 使用轮询策略
strategy = StrategyFactory.create_strategy("round_robin")

# 使用最少负载策略
strategy = StrategyFactory.create_strategy("least_loaded")

# 使用优先级策略
strategy = StrategyFactory.create_strategy("priority")

# 使用加权策略
strategy = StrategyFactory.create_strategy(
    "weighted",
    weight_key="performance_score",
)
```

---

## 数据结构

### AgentInfo

```python
@dataclass
class AgentInfo:
    agent_id: str                    # Agent唯一标识
    name: str                        # Agent名称
    capabilities: list[str]          # 能力列表
    max_concurrent_tasks: int        # 最大并发任务数
    status: AgentStatus              # 当前状态
    current_tasks: int               # 当前任务数
    completed_tasks: int             # 已完成任务数
    priority: int                    # 优先级
    metadata: dict                   # 扩展元数据
    last_heartbeat: datetime         # 最后心跳时间
```

### TaskAssignment

```python
@dataclass
class TaskAssignment:
    task_id: str                     # 任务ID
    agent_id: str                    # 分配的Agent ID
    task_type: str                   # 任务类型
    priority: int                    # 任务优先级
    payload: dict                    # 任务数据
    status: str                      # 任务状态
    created_at: datetime             # 创建时间
    started_at: datetime             # 开始时间
    completed_at: datetime           # 完成时间
    result: dict                     # 任务结果
    error: str                       # 错误信息
    metadata: dict                   # 扩展元数据
```

---

## 配置选项

### CoordinatorConfig

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| max_concurrent_tasks | int | 10 | 最大并发任务数 |
| task_timeout | int | 300 | 任务超时时间（秒） |
| heartbeat_interval | int | 30 | 心跳间隔（秒） |
| enable_load_balancing | bool | True | 是否启用负载均衡 |
| enable_conflict_detection | bool | True | 是否启用冲突检测 |
| enable_state_sync | bool | True | 是否启用状态同步 |

---

## 扩展性

### 自定义调度策略

```python
from core.coordinator.scheduler import SchedulingStrategy

class CustomStrategy(SchedulingStrategy):
    def select_agent(self, agents, task):
        # 自定义选择逻辑
        return selected_agent

    def get_name(self):
        return "custom"

# 注册策略
StrategyFactory.register_strategy("custom", CustomStrategy)
```

### 自定义冲突解决策略

```python
def custom_conflict_resolver(conflict: ConflictInfo) -> bool:
    # 自定义解决逻辑
    return True

coordinator.register_conflict_resolver(custom_conflict_resolver)
```

---

## 性能考虑

1. **线程安全**: 所有操作使用RLock保护
2. **优先级队列**: 任务使用堆实现高效优先级排序
3. **惰性计算**: 状态按需计算，避免不必要开销
4. **批量操作**: 支持批量任务提交和消息发送

---

## 使用场景

1. **专利检索流程**: 检索Agent → 分析Agent → 报告Agent
2. **并行数据处理**: 多个Agent并行处理不同数据源
3. **任务编排**: 复杂任务的依赖管理和执行
4. **资源调度**: 计算资源的动态分配和管理

---

## 相关文档

- [API文档](../api/COORDINATOR_API.md)
- [使用指南](../guides/COORDINATOR_GUIDE.md)
- [示例代码](../../examples/coordinator/)
