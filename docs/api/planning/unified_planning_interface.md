# 统一规划接口 API 文档

## 概述

`UnifiedPlannerRegistry` 是小诺系统的核心规划组件，提供统一的规划器注册、请求处理和协调功能。

## 核心组件

### 1. UnifiedPlannerRegistry - 统一规划器注册中心

#### 功能
- 管理多个规划器的注册和检索
- 处理规划请求并缓存结果
- 提供注册中心状态查询

#### 使用示例

```python
from core.planning.unified_planning_interface import (
    UnifiedPlannerRegistry,
    PlannerType,
    PlanningRequest,
    Priority,
)

# 创建注册中心
registry = UnifiedPlannerRegistry()

# 注册规划器
planner = MyCustomPlanner("我的规划器", PlannerType.TASK_PLANNER)
registry.register_planner(planner)

# 创建规划请求
request = PlanningRequest(
    title="专利分析任务",
    description="分析技术方案的可专利性",
    priority=Priority.HIGH,
    deadline=datetime.now() + timedelta(hours=2),
    requirements=["完成现有技术调研", "分析创造性", "评估实用性"],
)

# 提交请求
result = await registry.submit_request(request)

if result.success:
    print(f"规划成功: {result.plan_id}")
    print(f"预估时间: {result.estimated_duration}")
    print(f"置信度: {result.confidence_score}")
else:
    print(f"规划失败: {result.feedback}")
```

#### API 方法

##### `register_planner(planner: BasePlanner) -> None`
注册规划器到注册中心。

**参数:**
- `planner`: 继承自 BasePlanner 的规划器实例

**返回:** None

**示例:**
```python
registry.register_planner(my_planner)
```

##### `get_planner(planner_type: PlannerType) -> BasePlanner | None`
获取指定类型的规划器。

**参数:**
- `planner_type`: 规划器类型枚举值

**返回:** 规划器实例，如果不存在返回 None

**示例:**
```python
planner = registry.get_planner(PlannerType.TASK_PLANNER)
if planner:
    print(f"找到规划器: {planner.name}")
```

##### `async submit_request(request: PlanningRequest) -> PlanningResult`
提交规划请求并获取结果。

**参数:**
- `request`: 规划请求对象

**返回:** 规划结果对象

**示例:**
```python
result = await registry.submit_request(request)
if result.success:
    for step in result.steps:
        print(f"步骤 {step['step_number']}: {step['name']}")
```

##### `async get_result(request_id: str) -> PlanningResult | None`
从缓存获取请求结果。

**参数:**
- `request_id`: 请求ID

**返回:** 规划结果对象，如果不存在返回 None

##### `get_status() -> dict[str, Any]`
获取注册中心状态信息。

**返回:** 包含状态信息的字典

**示例:**
```python
status = registry.get_status()
print(f"已注册规划器: {status['registered_planners']}")
print(f"待处理请求: {status['pending_requests']}")
print(f"缓存结果数: {status['cached_results']}")
```

---

### 2. PlannerIntegrationBridge - 规划器集成桥接

#### 功能
- 连接外部系统和内部规划器
- 提供数据格式转换适配器
- 统一的集成接口

#### 使用示例

```python
from core.planning.unified_planning_interface import PlannerIntegrationBridge

# 创建桥接器
bridge = PlannerIntegrationBridge(registry)

# 定义适配器函数
def external_adapter(source_data: dict) -> PlanningRequest:
    """将外部数据转换为规划请求"""
    return PlanningRequest(
        title=source_data["task_name"],
        description=source_data.get("description", ""),
        priority=Priority(source_data.get("priority", 2)),
        context={"source": "external_system"},
    )

# 注册适配器
bridge.register_integration_adapter(
    source_type="external_system",
    target_planner=PlannerType.TASK_PLANNER,
    adapter_func=external_adapter,
)

# 处理外部请求
external_request = {
    "task_name": "分析专利",
    "description": "分析技术方案的专利性",
    "priority": 3,
}

result = await bridge.integrate_request(
    source_data=external_request,
    source_type="external_system",
    target_planner=PlannerType.TASK_PLANNER,
)
```

#### API 方法

##### `register_integration_adapter(source_type: str, target_planner: PlannerType, adapter_func) -> None`
注册集成适配器。

**参数:**
- `source_type`: 源系统类型标识
- `target_planner`: 目标规划器类型
- `adapter_func`: 适配器函数，接收源数据返回 PlanningRequest

##### `async integrate_request(source_data: dict, source_type: str, target_planner: PlannerType) -> PlanningResult`
处理集成请求。

**参数:**
- `source_data`: 源数据字典
- `source_type`: 源系统类型
- `target_planner`: 目标规划器类型

**返回:** 规划结果对象

---

### 3. PlannerCoordinator - 规划器协调器

#### 功能
- 协调多个规划器并行工作
- 管理任务依赖关系
- 优先级调度

#### 使用示例

```python
from core.planning.unified_planning_interface import PlannerCoordinator

# 创建协调器
coordinator = PlannerCoordinator(registry)

# 创建多个请求
requests = [
    PlanningRequest(title="任务1", priority=Priority.URGENT),
    PlanningRequest(title="任务2", priority=Priority.HIGH),
    PlanningRequest(title="任务3", priority=Priority.MEDIUM),
]

# 并行协调执行
results = await coordinator.coordinate_multi_planner_request(requests)

for i, result in enumerate(results):
    if result.success:
        print(f"任务{i+1}完成: {result.plan_id}")
    else:
        print(f"任务{i+1}失败: {result.feedback}")
```

#### API 方法

##### `async coordinate_multi_planner_request(requests: list[PlanningRequest]) -> list[PlanningResult]`
协调多个规划器请求。

**参数:**
- `requests`: 规划请求列表

**返回:** 规划结果列表

**特性:**
- 自动按优先级排序
- 并行执行独立任务
- 异常处理和错误报告

##### `async create_dependency_chain(requests: list[PlanningRequest], dependencies: dict[str, list[str]]) -> dict[str, PlanningResult]`
创建具有依赖关系的任务链。

**参数:**
- `requests`: 规划请求列表
- `dependencies`: 依赖关系字典，格式为 `{task_id: [dependent_task_ids]}`

**返回:** 任务ID到规划结果的字典

**示例:**
```python
requests = [
    PlanningRequest(title="需求分析"),
    PlanningRequest(title="方案设计"),
    PlanningRequest(title="实现开发"),
]

dependencies = {
    requests[1].id: [requests[0].id],  # 设计依赖分析
    requests[2].id: [requests[1].id],  # 实现依赖设计
}

results = await coordinator.create_dependency_chain(requests, dependencies)
```

---

## 数据模型

### PlanningRequest - 规划请求

```python
@dataclass
class PlanningRequest:
    id: str                              # 请求ID（自动生成）
    type: PlannerType                    # 规划器类型
    title: str                           # 标题
    description: str                     # 描述
    context: dict[str, Any]              # 上下文信息
    requirements: list[str]              # 需求列表
    constraints: list[str]               # 约束条件
    priority: Priority                   # 优先级
    deadline: datetime | None            # 截止时间
    assigned_agent: str | None           # 指定的代理
    metadata: dict[str, Any]             # 元数据
```

### PlanningResult - 规划结果

```python
@dataclass
class PlanningResult:
    request_id: str                      # 请求ID
    planner_type: PlannerType            # 规划器类型
    success: bool                        # 是否成功
    plan_id: str | None                  # 规划ID
    steps: list[dict[str, Any]]         # 执行步骤
    timeline: dict[str, Any] | None      # 时间线
    resources: list[str]                 # 所需资源
    dependencies: list[str]              # 依赖项
    estimated_duration: timedelta | None # 预估时长
    confidence_score: float              # 置信度分数
    created_at: datetime                 # 创建时间
    status: TaskStatus                   # 任务状态
    feedback: str                        # 反馈信息
```

---

## 枚举类型

### PlannerType - 规划器类型

```python
class PlannerType(Enum):
    TASK_PLANNER = "task_planner"        # 任务规划器
    GOAL_MANAGER = "goal_manager"        # 目标管理器
    SCHEDULER = "scheduler"              # 调度器
    ORCHESTRATOR = "orchestrator"        # 编排器
```

### Priority - 优先级

```python
class Priority(Enum):
    LOW = 1                              # 低优先级
    MEDIUM = 2                           # 中优先级
    HIGH = 3                             # 高优先级
    CRITICAL = 4                         # 关键优先级
    URGENT = 5                           # 紧急优先级
```

### TaskStatus - 任务状态

```python
class TaskStatus(Enum):
    PENDING = "pending"                  # 待处理
    IN_PROGRESS = "in_progress"          # 进行中
    COMPLETED = "completed"              # 已完成
    FAILED = "failed"                    # 失败
    CANCELLED = "cancelled"              # 已取消
```

---

## 全局函数

### `get_planner_registry() -> UnifiedPlannerRegistry`
获取全局规划器注册中心实例。

```python
from core.planning.unified_planning_interface import get_planner_registry

registry = get_planner_registry()
```

### `get_planner_coordinator() -> PlannerCoordinator`
获取全局规划器协调器实例。

```python
from core.planning.unified_planning_interface import get_planner_coordinator

coordinator = get_planner_coordinator()
```

---

## 最佳实践

### 1. 规划器实现

```python
from core.planning.unified_planning_interface import BasePlanner

class MyCustomPlanner(BasePlanner):
    def __init__(self, name: str):
        super().__init__(name, PlannerType.TASK_PLANNER)
        # 自定义初始化

    async def create_plan(self, request: PlanningRequest) -> PlanningResult:
        # 实现规划逻辑
        return PlanningResult(
            request_id=request.id,
            planner_type=self.planner_type,
            success=True,
            plan_id=f"plan_{uuid.uuid4()}",
            steps=[],
            confidence_score=0.9,
        )

    async def execute_plan(self, plan_id: str) -> bool:
        # 实现执行逻辑
        return True

    async def get_plan_status(self, plan_id: str) -> dict:
        # 获取状态逻辑
        return {"status": "completed"}

    async def update_plan(self, plan_id: str, updates: dict) -> bool:
        # 更新规划逻辑
        return True
```

### 2. 错误处理

```python
result = await registry.submit_request(request)

if not result.success:
    if "未找到类型" in result.feedback:
        # 注册规划器
        registry.register_planner(my_planner)
    elif "规划执行失败" in result.feedback:
        # 处理执行错误
        logger.error(f"规划失败: {result.feedback}")
```

### 3. 性能优化

```python
# 使用缓存避免重复规划
cached_result = await registry.get_result(request_id)
if cached_result:
    return cached_result

# 新请求才提交规划
result = await registry.submit_request(request)
```

---

## 相关文档

- [规划器开发指南](../development/planner_development.md)
- [任务管理API](./task_management.md)
- [Agent协调API](./agent_coordination.md)
