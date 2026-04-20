# Coordinator模式使用指南

**版本**: 1.0.0
**最后更新**: 2026-04-20

---

## 快速开始

### 安装

Coordinator模式是Athena平台的核心组件，无需额外安装。

### 基本使用

```python
from core.coordinator import Coordinator, AgentInfo

# 创建Coordinator
coordinator = Coordinator()

# 注册Agent
agent = AgentInfo(
    agent_id="my-agent",
    name="My Agent",
    capabilities=["task_type"],
)
coordinator.register_agent(agent)

# 提交任务
assignment = coordinator.submit_task(
    task_id="task-001",
    task_type="task_type",
    payload={"data": "value"},
)
```

---

## 核心概念

### Agent

Agent是执行任务的基本单元，每个Agent具有：

- **唯一标识**: agent_id
- **能力列表**: capabilities - 可以处理的任务类型
- **并发限制**: max_concurrent_tasks - 同时处理的最大任务数
- **状态**: status - 当前状态（空闲/忙碌/离线/错误）

### 任务

任务是分配给Agent的工作单元，包含：

- **任务ID**: 唯一标识
- **任务类型**: 决定由哪个Agent处理
- **优先级**: 决定执行顺序
- **负载**: 实际的工作数据

### 消息

消息是Agent间通信的方式，支持：

- **点对点**: 一个Agent发送给另一个Agent
- **广播**: 一个Agent发送给所有其他Agent
- **优先级**: 消息的紧急程度

---

## 常见场景

### 场景1: 专利检索流程

创建一个检索→分析→报告的任务链：

```python
from core.coordinator import AdvancedCoordinator, TaskDependency

advanced = AdvancedCoordinator(coordinator)

# 定义任务
tasks = [
    {"task_id": "search", "task_type": "patent_search"},
    {"task_id": "analyze", "task_type": "patent_analyze"},
    {"task_id": "report", "task_type": "report_generate"},
]

# 创建任务链
task_ids = advanced.create_task_chain(tasks)

# 依次执行任务
for task_id in task_ids:
    assignment = coordinator.submit_task(
        task_id=task_id,
        task_type=tasks[task_ids.index(task_id)]["task_type"],
        payload={},
    )
    # ... 执行任务
    advanced.mark_task_completed(task_id)
```

### 场景2: 并行数据处理

多个Agent并行处理不同数据源：

```python
# 注册多个处理Agent
for i in range(5):
    agent = AgentInfo(
        agent_id=f"processor-{i}",
        name=f"Processor {i}",
        capabilities=["process_data"],
    )
    coordinator.register_agent(agent)

# 并行提交任务
data_sources = ["source1", "source2", "source3", "source4", "source5"]
for i, source in enumerate(data_sources):
    coordinator.submit_task(
        task_id=f"process-{i}",
        task_type="process_data",
        payload={"source": source},
    )

# Coordinator会自动负载均衡
```

### 场景3: 任务重试

配置任务失败后的自动重试：

```python
from core.coordinator import TaskRetryConfig

# 配置重试策略
retry_config = TaskRetryConfig(
    max_retries=3,
    retry_delay=1.0,
    backoff_factor=2.0,
)
advanced.set_retry_config("task-001", retry_config)

# 任务失败时安排重试
if task_failed:
    advanced.schedule_retry(assignment)

# 定期检查可重试任务
ready_retries = advanced.get_ready_retries()
for assignment in ready_retries:
    # 重新执行任务
    pass
```

### 场景4: 冲突解决

处理多个Agent竞争同一资源的情况：

```python
from core.coordinator import ConflictType, ConflictResolutionStrategy

# 检测冲突
conflict = coordinator.detect_conflict(
    conflict_type=ConflictType.RESOURCE,
    agents=["agent-001", "agent-002"],
    resource_id="shared-resource",
    description="同时访问共享资源",
)

# 使用优先级策略解决
coordinator.resolve_conflict(
    conflict.conflict_id,
    ConflictResolutionStrategy.PRIORITY,
)
```

---

## 最佳实践

### 1. 合理设置Agent能力

```python
# 好：明确的能力定义
agent = AgentInfo(
    agent_id="patent-agent",
    capabilities=["patent_search", "patent_analyze"],
)

# 避免：过于宽泛的能力
agent = AgentInfo(
    agent_id="generic-agent",
    capabilities=["*"],  # 不推荐
)
```

### 2. 设置合理的并发限制

```python
# 根据Agent的实际处理能力设置
agent = AgentInfo(
    agent_id="cpu-intensive-agent",
    capabilities=["compute"],
    max_concurrent_tasks=2,  # CPU密集型任务限制并发
)
```

### 3. 使用任务优先级

```python
# 高优先级任务优先执行
coordinator.submit_task(
    task_id="urgent-task",
    task_type="process",
    payload={},
    priority=10,  # 最高优先级
)
```

### 4. 监控Coordinator状态

```python
# 定期检查状态
state = coordinator.get_state()
if state["pending_tasks"] > 100:
    # 任务积压，考虑增加Agent
    pass

if state["active_conflicts"] > 10:
    # 冲突过多，检查资源配置
    pass
```

### 5. 使用高级功能处理复杂场景

```python
# 任务依赖：使用AdvancedCoordinator
advanced = AdvancedCoordinator(coordinator)

# 任务重试：配置重试策略
advanced.set_retry_config(task_id, retry_config)

# 超时处理：设置任务超时
advanced.set_timeout(task_id, timeout_seconds=60)
```

---

## 性能优化

### 1. 启用负载均衡

```python
config = CoordinatorConfig(enable_load_balancing=True)
```

### 2. 批量操作

```python
# 批量提交任务比单个提交更高效
tasks = [f"task-{i}" for i in range(100)]
for task_id in tasks:
    coordinator.submit_task(task_id, "process", {})
```

### 3. 合理设置超时

```python
# 避免任务长时间占用资源
advanced.set_timeout(task_id, timeout_seconds=300)
```

---

## 故障排查

### 问题1: 任务无法分配

**原因**: 没有Agent能处理该类型的任务

**解决**:
```python
# 检查是否有能力的Agent
agents = coordinator.get_agents_by_capability("task_type")
if not agents:
    # 注册能处理该任务的Agent
    pass
```

### 问题2: Agent状态始终为BUSY

**原因**: 任务完成后未正确更新状态

**解决**:
```python
# 确保调用complete_task或fail_task
coordinator.complete_task(task_id, agent_id, result)
```

### 问题3: 消息未送达

**原因**: 接收者Agent不存在

**解决**:
```python
# 检查Agent是否存在
agent = coordinator.get_agent(receiver_id)
if not agent:
    # 先注册Agent
    pass
```

---

## 进阶话题

### 自定义调度策略

```python
from core.coordinator.scheduler import SchedulingStrategy
from core.coordinator import StrategyFactory

class CustomStrategy(SchedulingStrategy):
    def select_agent(self, agents, task):
        # 自定义选择逻辑
        # 例如：根据地理位置选择最近的Agent
        return selected_agent

    def get_name(self):
        return "geo_location"

# 注册策略
StrategyFactory.register_strategy("geo_location", CustomStrategy)

# 使用策略
strategy = StrategyFactory.create_strategy("geo_location")
```

### 与任务管理器集成

```python
from core.tasks.manager import get_task_manager

task_manager = get_task_manager()

# 创建任务
task = task_manager.create_task(
    title="专利检索",
    description="检索人工智能相关专利",
)

# 提交到Coordinator
coordinator.submit_task(
    task_id=task.id,
    task_type="patent_search",
    payload={"query": "人工智能"},
)
```

---

## 更多示例

详见 [示例目录](../../examples/coordinator/):

- `basic_usage.py` - 基本使用
- `advanced_features.py` - 高级功能
- `integration_example.py` - 集成示例
