# Task Tool API 参考文档

**版本**: v1.0.0
**最后更新**: 2026-04-06

---

## 📋 概述

Task Tool API提供了一套完整的接口，用于在Athena平台中执行AI任务、管理工作流和集成专利领域功能。

---

## 🎯 核心 API

### 1. TaskTool API

**类**: `core.agents.task_tool.task_tool.TaskTool`

#### 初始化

```python
from core.agents.task_tool.task_tool import TaskTool

task_tool = TaskTool(
    task_store=None,        # 可选: TaskStore实例
    model_mapper=None,      # 可选: ModelMapper实例
    config={}               # 可选: 配置字典
)
```

#### execute()

执行任务（同步或异步）

**参数**:
- `prompt` (str, 必需): 任务提示词
- `tools` (List[str], 必需): 可用工具列表
- `model` (Optional[str]): 模型名称 ("haiku"|"sonnet"|"opus")
- `agent_type` (Optional[str]): 代理类型 ("patent-analyst"|"patent-searcher"|"legal-researcher"|"patent-drafter")
- `background` (bool): 是否后台执行（默认False）
- `fork_context` (Optional[Dict]): Fork上下文信息

**返回**:
```python
{
    "task_id": str,          # 任务ID
    "status": str,           # 任务状态
    "agent_id": str,         # 代理ID
    "model": str,            # 使用的模型
    "filtered_tools": list,  # 过滤后的工具列表
}
```

**示例**:
```python
# 同步执行
result = task_tool.execute(
    prompt="分析这个专利的技术方案",
    tools=["patent_search", "knowledge_graph"],
    agent_type="patent-analyst",
    background=False
)

# 异步执行
result = task_tool.execute(
    prompt="检索人工智能领域的相关专利",
    tools=["patent_search"],
    agent_type="patent-searcher",
    background=True
)
```

#### to_tool_definition()

将TaskTool转换为ToolDefinition，用于ToolManager注册

**返回**: `ToolDefinition`

---

### 2. SubagentRegistry API

**类**: `core.agents.subagent_registry.SubagentRegistry`

#### 初始化

```python
from core.agents.subagent_registry import SubagentRegistry

registry = SubagentRegistry()
```

#### register_agent()

注册代理类型

**参数**:
- `config` (SubagentConfig): 代理配置

**示例**:
```python
from core.agents.subagent_registry import SubagentConfig
from core.agents.task_tool.models import ModelChoice

config = SubagentConfig(
    agent_type="custom-agent",
    display_name="自定义代理",
    description="自定义代理类型",
    default_model=ModelChoice.SONNET,
    capabilities=["能力1", "能力2"],
    system_prompt="系统提示词",
    allowed_tools=["tool1", "tool2"],
    max_concurrent_tasks=5,
    priority=1
)

registry.register_agent(config)
```

#### get_agent()

获取代理配置

**参数**:
- `agent_type` (str): 代理类型

**返回**: `Optional[SubagentConfig]`

**示例**:
```python
agent_config = registry.get_agent("patent-analyst")
if agent_config:
    print(agent_config.display_name)
    print(agent_config.default_model)
```

#### get_available_agents()

获取所有可用代理类型

**返回**: `List[str]`

---

### 3. ForkContextBuilder API

**类**: `core.agents.fork_context_builder.ForkContextBuilder`

#### 初始化

```python
from core.agents.fork_context_builder import ForkContextBuilder

builder = ForkContextBuilder(base_system_prompt="基础系统提示词")
```

#### build()

构建Fork上下文

**参数**:
- `prompt` (str): 任务提示词
- `context` (Optional[Dict]): 上下文信息
- `tool_use_id` (Optional[str]): 工具使用ID

**返回**: `ForkContext`

**示例**:
```python
fork_context = builder.build(
    prompt="分析任务",
    context={
        "parent_messages": [],
        "system_prompt": "代理系统提示词"
    }
)

# 序列化
context_dict = fork_context.to_dict()
context_json = fork_context.to_json()

# 反序列化
from core.agents.fork_context_builder import ForkContext
restored_context = ForkContext.from_dict(context_dict)
```

---

### 4. ToolFilter API

**类**: `core.agents.task_tool.tool_filter.ToolFilter`

#### 初始化

```python
from core.agents.task_tool.tool_filter import ToolFilter
from core.agents.subagent_registry import SubagentRegistry

registry = SubagentRegistry()
tool_filter = ToolFilter(registry)
```

#### filter_tools()

过滤工具列表

**参数**:
- `available_tools` (List[str]): 可用工具列表
- `agent_config` (SubagentConfig): 代理配置

**返回**: `List[str]`

**示例**:
```python
agent_config = registry.get_agent("patent-analyst")
filtered_tools = tool_filter.filter_tools(
    available_tools=["tool1", "tool2", "tool3"],
    agent_config=agent_config
)
```

---

## 🔧 工具管理 API

### 5. TaskToolAdapter API

**类**: `core.agents.task_tool.tool_manager_adapter.TaskToolAdapter`

#### 初始化

```python
from core.agents.task_tool.tool_manager_adapter import TaskToolAdapter

adapter = TaskToolAdapter(
    task_tool=None,       # 可选: TaskTool实例
    tool_manager=None,     # 可选: ToolManager实例
    registry=None          # 可选: ToolRegistry实例
)
```

#### register()

将TaskTool注册到ToolManager系统

**返回**: `bool`

**示例**:
```python
success = adapter.register()
if success:
    print("TaskTool注册成功")
```

#### execute_task()

执行任务（简化接口）

**参数**:
- `prompt` (str): 任务提示词
- `tools` (List[str]): 可用工具列表
- `model` (Optional[str]): 模型名称
- `agent_type` (Optional[str]): 代理类型
- `background` (bool): 是否后台执行

**返回**: `Dict[str, Any]`

---

## 📊 数据模型

### TaskInput

```python
@dataclass
class TaskInput:
    prompt: str
    tools: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    agent_type: Optional[str] = None
    fork_context: Optional[ForkContext] = None
```

### TaskOutput

```python
@dataclass
class TaskOutput:
    content: str
    tool_uses: int = 0
    duration: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### TaskRecord

```python
@dataclass
class TaskRecord:
    task_id: str
    agent_id: str
    model: str
    status: TaskStatus
    input: TaskInput
    output: Optional[TaskOutput] = None
    created_at: str
    updated_at: str
```

### SubagentConfig

```python
@dataclass
class SubagentConfig:
    agent_type: str
    display_name: str
    description: str
    default_model: ModelChoice
    capabilities: List[str]
    system_prompt: str
    allowed_tools: List[str]
    max_concurrent_tasks: int = 5
    priority: int = 1
```

---

## 🎭 代理类型

### patent-analyst (专利分析师)

**用途**: 专利技术分析、创新点识别、技术对比

**默认模型**: sonnet

**可用工具**: code_analyzer, knowledge_graph, patent_search, web_search

### patent-searcher (专利检索员)

**用途**: 专利检索、对比文件筛选、检索策略制定

**默认模型**: sonnet

**可用工具**: patent_search, web_search, knowledge_graph

### legal-researcher (法律研究员)

**用途**: 法律研究、法规解读、案例分析

**默认模型**: opus

**可用工具**: knowledge_graph, web_search, patent_search

### patent-drafter (专利撰写员)

**用途**: 专利申请文件撰写、答复撰写

**默认模型**: sonnet

**可用工具**: document_processor, code_analyzer, knowledge_graph

---

## 🚀 快速开始

### 基础使用

```python
from core.agents.task_tool.task_tool import TaskTool

# 1. 初始化
task_tool = TaskTool()

# 2. 执行任务
result = task_tool.execute(
    prompt="分析这个专利的技术方案",
    tools=["patent_search", "knowledge_graph"],
    agent_type="patent-analyst"
)

# 3. 查看结果
print(f"任务ID: {result['task_id']}")
print(f"状态: {result['status']}")
print(f"使用模型: {result['model']}")
```

### 高级使用

```python
# 自定义代理类型
from core.agents.subagent_registry import SubagentRegistry, SubagentConfig
from core.agents.task_tool.models import ModelChoice

registry = SubagentRegistry()

# 注册自定义代理
custom_config = SubagentConfig(
    agent_type="my-custom-agent",
    display_name="我的自定义代理",
    description="用于特定任务的代理",
    default_model=ModelChoice.SONNET,
    capabilities=["能力1", "能力2"],
    system_prompt="你的系统提示词",
    allowed_tools=["tool1", "tool2"],
    max_concurrent_tasks=3,
    priority=2
)

registry.register_agent(custom_config)

# 使用自定义代理
result = task_tool.execute(
    prompt="执行自定义任务",
    tools=["tool1", "tool2"],
    agent_type="my-custom-agent"
)
```

---

## 📝 错误处理

### 常见错误

**ValueError**: Prompt不能为空
```python
try:
    result = task_tool.execute(prompt="", tools=[])
except ValueError as e:
    print(f"错误: {e}")
```

**ValueError**: Tools必须是列表
```python
try:
    result = task_tool.execute(prompt="test", tools="invalid")
except ValueError as e:
    print(f"错误: {e}")
```

---

## 🔗 相关资源

- [使用示例](./examples.md)
- [集成指南](./integration-guide.md)
- [性能优化](./performance.md)
- [故障排除](./troubleshooting.md)

---

**API文档版本**: v1.0.0
**维护者**: Athena Platform Team
