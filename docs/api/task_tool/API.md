# Task Tool系统API文档

**版本**: v1.0.0
**创建日期**: 2026-04-05
**作者**: Agent-3 (domain-adapter-tester)

---

## 📋 目录

1. [概述](#概述)
2. [核心API](#核心api)
   - [TaskTool API](#tasktool-api)
   - [ModelMapper API](#modelmapper-api)
   - [BackgroundTaskManager API](#backgroundtaskmanager-api)
3. [数据模型](#数据模型)
4. [工作流API](#工作流api)
5. [使用示例](#使用示例)
6. [最佳实践](#最佳实践)

---

## 概述

Task Tool系统是Athena平台的核心任务执行框架,支持:
- 多种LLM模型的选择和映射
- 同步和异步任务执行
- 后台任务管理
- 专利领域特定代理类型
- 工具权限控制和过滤

### 核心特性

- ✅ 模型映射 (haiku/sonnet/opus → quick/task/main)
- ✅ 同步/异步执行模式
- ✅ 后台任务管理 (支持10+并发任务)
- ✅ 四层记忆系统集成 (HOT/WARM/COLD/ARCHIVE)
- ✅ 专利代理类型 (patent-analyst/patent-searcher/legal-researcher/patent-drafter)

---

## 核心API

### TaskTool API

TaskTool是任务执行的核心类,提供统一的任务执行接口。

#### 初始化

```python
from core.agents.task_tool import TaskTool, TaskStore, ModelMapper

# 创建TaskTool实例
task_tool = TaskTool(
    task_store=None,        # 可选: 任务存储实例
    model_mapper=None,      # 可选: 模型映射器实例
    config=None,           # 可选: 配置字典
)
```

**参数**:
- `task_store` (Optional[TaskStore]): 任务存储实例,如果不提供则自动创建
- `model_mapper` (Optional[ModelMapper]): 模型映射器实例,如果不提供则自动创建
- `config` (Optional[Dict[str, Any]]): 配置字典

#### execute() - 执行任务

同步或异步执行任务。

```python
result = task_tool.execute(
    prompt="分析专利CN202310123456.7的技术方案",
    tools=["patent-search", "patent-analysis", "knowledge-graph-query"],
    model=None,              # 可选: 模型名称
    agent_type="analysis",    # 可选: 代理类型
    background=False,         # 可选: 是否后台执行
)
```

**参数**:
- `prompt` (str): 任务提示词
- `tools` (List[str]): 可用工具列表
- `model` (Optional[str]): 模型名称,如果不提供则根据agent_type自动选择
- `agent_type` (Optional[str]): 代理类型,用于模型选择
- `background` (bool): 是否后台执行,默认为False

**返回值**:
```python
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",  # 任务ID
    "status": "completed",                               # 任务状态
    "agent_id": "analysis-agent-12345678",               # 代理ID
    "model": "task",                                     # 使用的模型
}
```

**示例**:

```python
# 示例1: 同步执行专利分析
result = task_tool.execute(
    prompt="分析专利CN202310123456.7的技术方案",
    tools=["patent-search", "patent-analysis"],
    agent_type="analysis",
)
print(f"任务ID: {result['task_id']}")
print(f"状态: {result['status']}")

# 示例2: 异步执行专利检索
result = task_tool.execute(
    prompt="检索关于量子计算的专利",
    tools=["patent-search", "result-ranker"],
    agent_type="search",
    background=True,
)
print(f"任务ID: {result['task_id']}")
print(f"状态: {result['status']}")  # "submitted"

# 后续可以查询任务状态
task_status = task_tool.task_store.get_task(result['task_id'])
```

---

### ModelMapper API

ModelMapper负责模型名称的映射和配置管理。

#### 初始化

```python
from core.agents.task_tool import ModelMapper

# 创建ModelMapper实例
mapper = ModelMapper()
```

#### map() - 模型映射

将Kode模型名称映射到Athena模型名称。

```python
athena_model = mapper.map("haiku")   # 返回: "quick"
athena_model = mapper.map("sonnet")  # 返回: "task"
athena_model = mapper.map("opus")    # 返回: "main"
```

**参数**:
- `model` (Union[str, ModelChoice]): 模型名称或ModelChoice枚举

**返回值**:
- `str`: Athena模型名称

**异常**:
- `ValueError`: 如果模型名称未知

**示例**:
```python
mapper = ModelMapper()

# 字符串输入
quick_model = mapper.map("haiku")
task_model = mapper.map("sonnet")
main_model = mapper.map("opus")

# 枚举输入
from core.agents.task_tool.models import ModelChoice
task_model = mapper.map(ModelChoice.SONNET)
```

#### get_model_config() - 获取模型配置

获取指定模型的配置信息。

```python
config = mapper.get_model_config("haiku")
# 返回:
# {
#     "name": "quick",
#     "temperature": 0.7,
#     "max_tokens": 4096,
#     "description": "快速模型，适合简单任务"
# }
```

**参数**:
- `model` (Union[str, ModelChoice]): 模型名称或ModelChoice枚举

**返回值**:
- `Dict[str, Any]`: 模型配置字典

**异常**:
- `ValueError`: 如果模型名称未知

#### get_available_models() - 获取可用模型

获取所有可用的模型列表。

```python
models = mapper.get_available_models()
# 返回: ["haiku", "sonnet", "opus"]
```

**返回值**:
- `List[str]`: 可用模型名称列表

#### get_environment_model() - 获取环境变量模型

获取环境变量`ATHENA_SUBAGENT_MODEL`指定的模型。

```python
env_model = mapper.get_environment_model()
# 返回: "sonnet" (如果设置了环境变量)
# 返回: None (如果未设置环境变量)
```

**返回值**:
- `str | None`: 环境变量指定的模型名称,如果未设置则返回None

---

### BackgroundTaskManager API

BackgroundTaskManager负责后台任务的异步执行和管理。

#### 初始化

```python
from core.agents.task_tool import BackgroundTaskManager

# 创建BackgroundTaskManager实例
task_manager = BackgroundTaskManager(max_workers=10)
```

**参数**:
- `max_workers` (int): 最大并发任务数,默认为10

#### submit() - 提交后台任务

提交一个函数到后台异步执行。

```python
def my_task(x, y):
    return x + y

task = task_manager.submit(
    func=my_task,
    args=(1, 2),              # 可选: 位置参数
    kwargs={"timeout": 30},      # 可选: 关键字参数
    agent_id="analysis-agent-1", # 可选: 代理ID
    input_data=None,            # 可选: 任务输入数据
)

# 返回BackgroundTask对象
print(f"任务ID: {task.task_id}")
print(f"状态: {task.status}")
```

**参数**:
- `func` (Callable): 要执行的函数
- `args` (Optional[Tuple[Any, ...]]): 函数位置参数
- `kwargs` (Optional[Dict[str, Any]]): 函数关键字参数
- `agent_id` (Optional[str]): 代理ID
- `input_data` (Optional[TaskInput]): 任务输入数据

**返回值**:
- `BackgroundTask`: 后台任务对象

**异常**:
- `RuntimeError`: 如果管理器已关闭

#### get_task() - 获取任务信息

获取指定任务的当前状态。

```python
task = task_manager.get_task("550e8400-e29b-41d4-a716-446655440000")
if task:
    print(f"任务ID: {task.task_id}")
    print(f"状态: {task.status}")
    print(f"代理ID: {task.agent_id}")
else:
    print("任务不存在")
```

**参数**:
- `task_id` (str): 任务ID

**返回值**:
- `Optional[BackgroundTask]`: BackgroundTask对象,如果任务不存在则返回None

#### wait_get_task() - 等待任务完成

等待任务完成并返回结果。

```python
try:
    task = task_manager.wait_get_task(
        task_id="550e8400-e29b-41d4-a716-446655440000",
        timeout=60,  # 可选: 超时时间(秒)
    )
    print(f"任务完成: {task.status}")
except TimeoutError:
    print("任务超时")
```

**参数**:
- `task_id` (str): 任务ID
- `timeout` (Optional[float]): 超时时间(秒)

**返回值**:
- `Optional[BackgroundTask]`: BackgroundTask对象,如果任务不存在则返回None

**异常**:
- `TimeoutError`: 如果任务超时

#### cancel() - 取消任务

取消一个正在执行或待执行的任务。

```python
success = task_manager.cancel("550e8400-e29b-41d4-a716-446655440000")
if success:
    print("任务已取消")
else:
    print("任务取消失败")
```

**参数**:
- `task_id` (str): 任务ID

**返回值**:
- `bool`: True如果任务被成功取消,False如果任务不存在或无法取消

#### get_all_tasks() - 获取所有任务

获取所有任务的列表。

```python
all_tasks = task_manager.get_all_tasks()
print(f"总任务数: {len(all_tasks)}")
for task in all_tasks:
    print(f"  {task.task_id}: {task.status}")
```

**返回值**:
- `List[BackgroundTask]`: 所有任务列表

#### get_running_tasks() - 获取运行中的任务

获取当前正在运行的任务列表。

```python
running_tasks = task_manager.get_running_tasks()
print(f"运行中的任务数: {len(running_tasks)}")
```

**返回值**:
- `List[BackgroundTask]`: 运行中的任务列表

#### shutdown() - 关闭管理器

优雅地关闭任务管理器。

```python
task_manager.shutdown(wait=True)  # 等待所有任务完成
```

**参数**:
- `wait` (bool): 是否等待所有任务完成,默认为True

#### 上下文管理器

支持`with`语句自动关闭管理器。

```python
with BackgroundTaskManager(max_workers=10) as manager:
    # 提交任务
    task = manager.submit(func=my_task, args=(1, 2))
    # ... 其他操作
# 管理器自动关闭
```

---

## 数据模型

### TaskInput

任务输入数据类。

```python
@dataclass
class TaskInput:
    prompt: str                              # 任务提示词
    tools: List[str] = field(default_factory=list)  # 可用工具列表
    context: Dict[str, Any] = field(default_factory=dict)  # 上下文信息
    agent_type: Optional[str] = None    # 代理类型
```

### TaskOutput

任务输出数据类。

```python
@dataclass
class TaskOutput:
    content: str                             # 输出内容
    tool_uses: int = 0                      # 工具使用次数
    duration: float = 0.0                    # 执行时长(秒)
    success: bool = True                     # 是否成功
    error: Optional[str] = None              # 错误信息
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
```

### TaskRecord

任务记录数据类,用于持久化存储。

```python
@dataclass
class TaskRecord:
    task_id: str                            # 任务ID
    agent_id: str                           # 代理ID
    model: str                              # 使用的模型
    status: TaskStatus                       # 任务状态
    input: TaskInput                         # 任务输入
    output: Optional[TaskOutput] = None       # 任务输出
    created_at: str                          # 创建时间(ISO 8601)
    updated_at: str                          # 更新时间(ISO 8601)
    error_message: Optional[str] = None       # 错误信息
```

### BackgroundTask

后台任务数据类。

```python
@dataclass
class BackgroundTask:
    task_id: str                            # 任务ID
    status: TaskStatus                       # 任务状态
    future: Any                             # 异步Future对象
    agent_id: str                           # 代理ID
    created_at: str                          # 创建时间(ISO 8601)
    updated_at: str                          # 更新时间(ISO 8601)
    input_data: Optional[TaskInput] = None   # 任务输入数据

    def update_status(self, new_status: TaskStatus) -> None:
        """更新任务状态"""
        self.status = new_status
        self.updated_at = datetime.utcnow().isoformat() + "Z"
```

### TaskStatus

任务状态枚举。

```python
class TaskStatus(Enum):
    PENDING = "pending"       # 任务待执行
    RUNNING = "running"       # 任务执行中
    COMPLETED = "completed"   # 任务完成
    FAILED = "failed"         # 任务失败
    CANCELLED = "cancelled"   # 任务已取消
```

### ModelChoice

模型选择枚举。

```python
class ModelChoice(Enum):
    HAIKU = "haiku"    # Claude Haiku (快速模型)
    SONNET = "sonnet"  # Claude Sonnet (任务模型)
    OPUS = "opus"      # Claude Opus (主模型)
```

---

## 工作流API

### AnalysisWorkflow

专利分析工作流,用于分析专利技术方案和创新点。

**配置文件**: `config/patent/patent_agents.yaml`

**步骤**:
1. 专利检索
2. 技术方案分析
3. 创新点识别
4. 对比分析
5. 报告生成

**使用示例**:
```python
from core.patent.workflows import AnalysisWorkflow

workflow = AnalysisWorkflow()
result = workflow.execute(
    patent_number="CN202310123456.7",
    analysis_type="technical",
    include_comparison=True,
)
```

### SearchWorkflow

专利检索工作流,用于执行专利检索和筛选。

**步骤**:
1. 检索策略构建
2. 多源检索执行
3. 结果去重和排序
4. 相关性过滤
5. 结果导出

**使用示例**:
```python
from core.patent.workflows import SearchWorkflow

workflow = SearchWorkflow()
result = workflow.execute(
    query="量子计算",
    data_sources=["local", "online"],
    export_format="csv",
)
```

### LegalWorkflow

法律研究工作流,用于研究专利法律法规和案例。

**步骤**:
1. 法律问题解析
2. 法规检索
3. 案例检索
4. 法理分析
5. 法律意见生成

**使用示例**:
```python
from core.patent.workflows import LegalWorkflow

workflow = LegalWorkflow()
result = workflow.execute(
    legal_query="分析专利侵权判例",
    include_trend_analysis=True,
)
```

---

## 使用示例

### 示例1: 基础任务执行

```python
from core.agents.task_tool import TaskTool

# 创建TaskTool实例
task_tool = TaskTool()

# 执行任务
result = task_tool.execute(
    prompt="分析专利CN202310123456.7的技术方案",
    tools=["patent-search", "patent-analysis"],
    agent_type="analysis",
)

print(f"任务ID: {result['task_id']}")
print(f"状态: {result['status']}")
```

### 示例2: 异步后台任务

```python
from core.agents.task_tool import TaskTool, BackgroundTaskManager

# 创建实例
task_tool = TaskTool()
task_manager = BackgroundTaskManager(max_workers=10)

# 提交后台任务
task = task_manager.submit(
    func=task_tool.execute,
    kwargs={
        "prompt": "检索关于量子计算的专利",
        "tools": ["patent-search", "result-ranker"],
        "agent_type": "search",
        "background": False,
    },
    agent_id="search-agent-1",
)

# 获取任务ID
task_id = task.task_id
print(f"任务ID: {task_id}")

# 查询任务状态
import time
time.sleep(5)
status = task_manager.get_task(task_id)
print(f"任务状态: {status.status}")

# 等待任务完成
result = task_manager.wait_get_task(task_id, timeout=60)
print(f"任务完成: {result.status}")
```

### 示例3: 模型选择和映射

```python
from core.agents.task_tool import ModelMapper

# 创建ModelMapper实例
mapper = ModelMapper()

# 映射模型
quick_model = mapper.map("haiku")
print(f"haiku → {quick_model}")  # 输出: "quick"

# 获取模型配置
config = mapper.get_model_config("haiku")
print(f"温度: {config['temperature']}")
print(f"最大token: {config['max_tokens']}")
print(f"描述: {config['description']}")
```

### 示例4: 专利代理类型使用

```python
from core.agents.task_tool import TaskTool

# 创建TaskTool实例
task_tool = TaskTool()

# 使用专利分析师
result = task_tool.execute(
    prompt="分析专利CN202310123456.7",
    tools=["patent-search", "patent-analysis", "knowledge-graph-query"],
    agent_type="analysis",  # 自动选择sonnet模型
)

# 使用专利检索专家
result = task_tool.execute(
    prompt="检索关于量子计算的专利",
    tools=["patent-search", "result-ranker", "patent-filter"],
    agent_type="search",    # 自动选择haiku模型
    background=True,         # 后台执行
)

# 使用法律研究员
result = task_tool.execute(
    prompt="分析专利侵权判例",
    tools=["legal-knowledge-query", "case-law-search", "legal-reasoning"],
    agent_type="legal",     # 自动选择opus模型
)

# 使用专利撰写专家
result = task_tool.execute(
    prompt="撰写专利申请文件",
    tools=["patent-drafting", "patent-review", "patent-formatting"],
    agent_type="drafter",    # 自动选择opus模型
)
```

### 示例5: 工作流集成

```python
from core.patent.workflows import AnalysisWorkflow, SearchWorkflow, LegalWorkflow

# 专利分析工作流
analysis_workflow = AnalysisWorkflow()
analysis_result = analysis_workflow.execute(
    patent_number="CN202310123456.7",
    analysis_type="comprehensive",
)

# 专利检索工作流
search_workflow = SearchWorkflow()
search_result = search_workflow.execute(
    query="量子计算",
    max_results=50,
    export_format="csv",
    export_path="/path/to/results.csv",
)

# 法律研究工作流
legal_workflow = LegalWorkflow()
legal_result = legal_workflow.execute(
    legal_query="专利侵权判例分析",
    case_types=["infringement", "invalidation"],
    include_trend_analysis=True,
)
```

---

## 最佳实践

### 1. 模型选择原则

- **快速任务**: 使用`haiku`模型,如专利检索
- **标准任务**: 使用`sonnet`模型,如专利分析
- **复杂任务**: 使用`opus`模型,如法律推理、专利撰写

### 2. 异步任务使用

- **长时间运行的任务**: 使用后台执行模式
- **需要并发的任务**: 使用BackgroundTaskManager
- **需要立即返回的场景**: 使用后台任务,后续查询状态

### 3. 错误处理

```python
try:
    result = task_tool.execute(
        prompt="执行任务",
        tools=["tool1", "tool2"],
    )
except ValueError as e:
    print(f"输入验证错误: {e}")
except RuntimeError as e:
    print(f"运行时错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

### 4. 资源管理

- **使用上下文管理器**: 确保资源正确释放
- **及时关闭任务管理器**: 避免资源泄露
- **控制并发数**: 根据系统资源调整max_workers

```python
# 推荐做法
with BackgroundTaskManager(max_workers=10) as manager:
    task = manager.submit(func=my_task, args=(1, 2))
    # ... 其他操作
# 管理器自动关闭,确保资源释放
```

### 5. 任务状态监控

```python
# 定期检查任务状态
import time

task_id = "550e8400-e29b-41d4-a716-446655440000"
while True:
    task = task_manager.get_task(task_id)
    if task.status == TaskStatus.COMPLETED:
        print("任务完成!")
        break
    elif task.status == TaskStatus.FAILED:
        print("任务失败!")
        break
    time.sleep(2)  # 每2秒检查一次
```

---

## 常见问题

### Q1: 如何选择合适的模型?

**A**: 根据任务复杂度选择:
- 简单任务(检索、筛选): `haiku`
- 标准任务(分析、评估): `sonnet`
- 复杂任务(推理、撰写): `opus`

### Q2: 后台任务如何获取结果?

**A**: 使用`wait_get_task()`方法:
```python
result = task_manager.wait_get_task(task_id, timeout=60)
```

### Q3: 如何取消正在运行的任务?

**A**: 使用`cancel()`方法:
```python
success = task_manager.cancel(task_id)
```

### Q4: 任务失败后如何重试?

**A**: 提交新任务,使用相同的参数:
```python
result = task_tool.execute(
    prompt="重试任务",
    tools=tools,
    agent_type=agent_type,
)
```

---

## 附录

### A. 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ATHENA_SUBAGENT_MODEL` | 指定默认LLM模型 | None |
| `ATHENA_MAX_WORKERS` | 后台任务最大并发数 | 10 |

### B. 配置文件

- 专利代理类型配置: `config/patent/patent_agents.yaml`
- 模型映射配置: `core/agents/task_tool/model_mapper.py`
- 全局配置: `config/athena_config.yaml`

### C. 相关文档

- Task Tool系统设计: `docs/reports/task-tool-system-design/`
- 专利领域需求分析: `docs/reports/task-tool-system-implementation/domain-analysis/T3-1-patent-domain-requirements-analysis.md`
- 代理类型配置: `config/patent/patent_agents.yaml`

---

**API文档版本**: v1.0.0
**最后更新**: 2026-04-05
**维护者**: Agent-3 (domain-adapter-tester)
