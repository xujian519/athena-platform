# Athena Tools 模块 API 参考文档

> **版本**: v1.0.0
> **最后更新**: 2026-01-25
> **作者**: Athena平台团队

## 概述

Athena Tools 模块是智能体工具系统的核心组件，提供统一的工具定义、注册、选择和调用管理功能。

### 核心特性

- 🔧 **统一工具定义** - 标准化的工具元数据和能力描述
- 📇 **智能工具注册** - 线程安全的工具注册中心
- 🎯 **智能工具选择** - 基于多种策略的工具推荐
- 🚦 **速率限制** - 可选的调用频率控制
- 📊 **性能监控** - 实时统计和性能跟踪
- 🛡️ **安全防护** - 参数验证和错误处理

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     应用层 (Agents)                          │
│                    使用工具执行任务                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                   ToolCallManager                           │
│  - 统一调用接口  - 调用历史  - 速率限制  - 性能统计          │
└─────┬───────────────────────────────────────────┬───────────┘
      │                                           │
┌─────┴───────────┐                   ┌──────────┴─────────┐
│  ToolSelector   │                   │   ToolRegistry    │
│  - 工具选择      │                   │   - 工具注册       │
│  - 策略管理      │◄──────────────────►   - 工具发现       │
│  - 性能评估      │                   │   - 统计信息       │
└─────────────────┘                   └────────────────────┘
      │
┌─────┴──────────────────────────────────────────────────────┐
│                   ToolDefinition (base.py)                  │
│  - 工具元数据  - 能力声明  - 优先级  - 参数定义             │
└─────────────────────────────────────────────────────────────┘
```

---

## 模块索引

| 模块 | 文件 | 功能描述 |
|------|------|---------|
| 基础定义 | `base.py` | ToolDefinition、ToolCategory、ToolCapability 等核心数据类 |
| 工具注册 | `base.py` (ToolRegistry) | 工具注册、发现和统计 |
| 工具选择 | `selector.py` | 智能工具选择和策略管理 |
| 调用管理 | `tool_call_manager.py` | 统一工具调用接口和生命周期管理 |
| 速率限制 | `rate_limiter.py` | 令牌桶、滑动窗口、固定窗口算法 |
| 生产实现 | `production_tool_implementations.py` | 实际可用的工具实现 |

---

## 核心 API

### 1. ToolDefinition

工具定义类，描述工具的元数据和能力。

#### 类定义

```python
@dataclass
class ToolDefinition:
    """工具定义类"""

    # 基础信息
    tool_id: str                          # 工具唯一标识符
    name: str                             # 工具名称
    category: ToolCategory                # 工具分类
    description: str                      # 工具描述

    # 能力声明
    capability: ToolCapability            # 工具能力描述

    # 参数定义
    required_params: List[str]            # 必需参数列表
    optional_params: List[str]            # 可选参数列表

    # 执行配置
    handler: Optional[Callable]           # 异步处理函数
    timeout: float = 30.0                 # 超时时间（秒）
    max_retries: int = 3                  # 最大重试次数

    # 优先级
    priority: ToolPriority = ToolPriority.MEDIUM  # 工具优先级
```

#### 使用示例

```python
from core.tools.base import ToolDefinition, ToolCategory, ToolCapability, ToolPriority

async def my_handler(params: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Any:
    """工具处理函数"""
    return {"result": "success"}

tool = ToolDefinition(
    tool_id="my_tool",
    name="My Tool",
    category=ToolCategory.CODE_ANALYSIS,
    description="我的工具描述",
    capability=ToolCapability(
        input_types=["text"],
        output_types=["result"],
        domains=["all"],
        task_types=["analysis"]
    ),
    required_params=["input"],
    optional_params=["option"],
    handler=my_handler,
    timeout=30.0,
    priority=ToolPriority.HIGH
)
```

---

### 2. ToolCategory

工具分类枚举。

#### 枚举值

```python
class ToolCategory(Enum):
    """工具类别"""
    CODE_ANALYSIS = "code_analysis"           # 代码分析
    KNOWLEDGE_GRAPH = "knowledge_graph"       # 知识图谱
    DECISION_ENGINE = "decision_engine"       # 决策引擎
    MICROSERVICE = "microservice"             # 微服务
    EMBEDDING = "embedding"                   # 向量嵌入
    CHAT_COMPLETION = "chat_completion"       # 聊天补全
    DOCUMENT_PROCESSING = "document_processing" # 文档处理
    WEB_SEARCH = "web_search"                 # 网络搜索
    COORDINATION = "coordination"             # 协调管理
    MONITORING = "monitoring"                 # 监控告警
    DATA_TRANSFORMATION = "data_transformation" # 数据转换
```

---

### 3. ToolCapability

工具能力描述类。

#### 类定义

```python
@dataclass
class ToolCapability:
    """工具能力描述"""
    input_types: List[str]      # 支持的输入类型
    output_types: List[str]     # 输出的数据类型
    domains: List[str]          # 适用领域 (如: patent, legal, academic)
    task_types: List[str]       # 支持的任务类型
```

#### 使用示例

```python
capability = ToolCapability(
    input_types=["text", "code"],
    output_types=["analysis", "suggestions"],
    domains=["patent", "legal"],
    task_types=["analysis", "review"]
)

# 检查能力匹配
capability.matches_input_type("text")         # True
capability.matches_domain("patent")            # True
capability.matches_task_type("analysis")       # True
```

---

### 4. ToolPriority

工具优先级枚举。

```python
class ToolPriority(Enum):
    """工具优先级"""
    CRITICAL = "critical"    # 关键工具,优先使用
    HIGH = "high"           # 高优先级
    MEDIUM = "medium"       # 中等优先级
    LOW = "low"             # 低优先级
```

---

### 5. ToolRegistry

工具注册中心，线程安全的工具管理。

#### 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `register(tool)` | `ToolDefinition` | `None` | 注册工具 |
| `unregister(tool_id)` | `str` | `bool` | 注销工具 |
| `get_tool(tool_id)` | `str` | `Optional[ToolDefinition]` | 获取工具定义 |
| `list_tools(category=None)` | `Optional[ToolCategory]` | `List[str]` | 列出工具名称 |
| `get_statistics()` | - | `Dict[str, Any]` | 获取统计信息 |
| `find_by_category(category)` | `ToolCategory` | `List[ToolDefinition]` | 按分类查找 |
| `find_by_priority(priority)` | `ToolPriority` | `List[ToolDefinition]` | 按优先级查找 |

#### 使用示例

```python
from core.tools.base import ToolRegistry

# 创建注册中心
registry = ToolRegistry()

# 注册工具
registry.register(tool)

# 获取工具
tool = registry.get_tool("my_tool")

# 列出所有工具
all_tools = registry.list_tools()

# 按分类查找
code_tools = registry.find_by_category(ToolCategory.CODE_ANALYSIS)

# 获取统计信息
stats = registry.get_statistics()
print(f"总工具数: {stats['total_tools']}")
```

---

### 6. ToolSelector

智能工具选择器，支持多种选择策略。

#### 选择策略

```python
class SelectionStrategy(Enum):
    """工具选择策略"""
    BALANCED = "balanced"       # 平衡模式（性能 + 质量）
    PERFORMANCE = "performance" # 性能优先
    QUALITY = "quality"        # 质量优先
    PRIORITY = "priority"      # 优先级驱动
```

#### 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `select_tool(task_type, domain, ...)` | `str, str, ...` | `Optional[ToolDefinition]` | 选择单个工具 |
| `select_tools(task_type, domain, ...)` | `str, str, ...` | `List[ToolDefinition]` | 选择多个工具 |

#### 使用示例

```python
from core.tools.selector import ToolSelector, SelectionStrategy

# 创建选择器
selector = ToolSelector(
    registry=registry,
    strategy=SelectionStrategy.BALANCED,
    min_success_rate=0.7
)

# 选择工具
tool = await selector.select_tool(
    task_type="analysis",
    domain="patent"
)

if tool:
    print(f"选择工具: {tool.name}")
```

---

### 7. ToolCallManager

工具调用管理器，统一管理工具调用、日志、错误处理和性能监控。

#### 初始化参数

```python
ToolCallManager(
    log_dir: str = "logs/tool_calls",      # 日志目录
    max_history: int = 1000,                # 最大历史记录数
    enable_rate_limit: bool = True,         # 是否启用速率限制
    max_calls_per_minute: int = 100         # 每分钟最大调用次数
)
```

#### 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `register_tool(tool)` | `ToolDefinition` | `None` | 注册工具 |
| `call_tool(tool_name, parameters, ...)` | `str, Dict, ...` | `ToolCallResult` | 调用工具 |
| `get_tool(tool_name)` | `str` | `Optional[ToolDefinition]` | 获取工具 |
| `list_tools(category=None)` | `Optional[ToolCategory]` | `List[str]` | 列出工具 |
| `get_stats()` | - | `Dict[str, Any]` | 获取统计信息 |
| `get_recent_calls(limit)` | `int` | `List[ToolCallResult]` | 获取最近调用 |

#### 使用示例

```python
from core.tools.tool_call_manager import ToolCallManager

# 创建管理器
manager = ToolCallManager(
    max_history=1000,
    enable_rate_limit=True,
    max_calls_per_minute=100
)

# 注册工具
manager.register_tool(tool)

# 调用工具
result = await manager.call_tool(
    tool_name="my_tool",
    parameters={"input": "test_data"},
    context={"user": "test_user"}
)

# 检查结果
if result.status == CallStatus.SUCCESS:
    print(f"结果: {result.result}")
    print(f"执行时间: {result.execution_time:.2f}秒")
else:
    print(f"错误: {result.error}")
```

---

### 8. CallStatus

调用状态枚举。

```python
class CallStatus(Enum):
    """调用状态"""
    PENDING = "pending"           # 等待执行
    RUNNING = "running"           # 执行中
    SUCCESS = "success"           # 成功
    FAILED = "failed"             # 失败
    TIMEOUT = "timeout"           # 超时
    CANCELLED = "cancelled"       # 已取消
```

---

### 9. ToolCallResult

工具调用结果类。

#### 类定义

```python
@dataclass
class ToolCallResult:
    """工具调用结果"""
    request_id: str                    # 请求ID
    tool_name: str                     # 工具名称
    status: CallStatus                 # 调用状态
    result: Optional[Any] = None       # 调用结果
    error: Optional[str] = None        # 错误信息
    execution_time: float = 0.0        # 执行时间（秒）
    timestamp: datetime = ...          # 时间戳
    metadata: Dict[str, Any] = ...     # 元数据
```

---

## 速率限制 API

### RateLimiter

速率限制器，支持多种限流算法。

#### 初始化

```python
from core.tools.rate_limiter import RateLimiter, RateLimitStrategy

rate_limiter = RateLimiter(
    max_calls=100,                         # 最大调用次数
    period=60.0,                            # 时间窗口（秒）
    strategy=RateLimitStrategy.SLIDING_WINDOW  # 限流策略
)
```

#### 限流策略

```python
class RateLimitStrategy(Enum):
    """速率限制策略"""
    FIXED_WINDOW = "fixed_window"       # 固定窗口
    SLIDING_WINDOW = "sliding_window"   # 滑动窗口
    TOKEN_BUCKET = "token_bucket"       # 令牌桶
```

#### 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `acquire(timeout=None)` | `Optional[float]` | `bool` | 获取调用许可 |
| `get_stats()` | - | `Dict[str, Any]` | 获取统计信息 |
| `reset()` | - | `None` | 重置计数器 |

#### 使用示例

```python
# 检查是否允许调用
if await rate_limiter.acquire(timeout=5.0):
    # 执行调用
    result = await tool_call()
else:
    # 被限流
    print("调用过于频繁，请稍后重试")

# 获取统计
stats = rate_limiter.get_stats()
print(f"总调用数: {stats['total_calls']}")
print(f"被限流次数: {stats['rejected_calls']}")
```

---

## 工具处理器规范

### 处理器签名

```python
async def tool_handler(
    params: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """
    工具处理函数

    Args:
        params: 工具参数字典
        context: 可选的上下文信息

    Returns:
        工具执行结果，可以是任意类型

    Raises:
        ValueError: 参数验证失败
        RuntimeError: 执行错误
    """
    # 1. 参数验证
    # 2. 执行逻辑
    # 3. 返回结果
    pass
```

### 最佳实践

1. **参数验证**
   ```python
   required = ["input"]
   for param in required:
       if param not in params:
           raise ValueError(f"缺少必需参数: {param}")
   ```

2. **错误处理**
   ```python
   try:
       result = await process(params)
   except Exception as e:
       logger.error(f"工具执行失败: {e}")
       raise RuntimeError(f"处理失败: {e}")
   ```

3. **超时控制**
   ```python
   import asyncio

   try:
       result = await asyncio.wait_for(
           long_running_task(),
           timeout=30.0
       )
   except asyncio.TimeoutError:
       raise TimeoutError("操作超时")
   ```

---

## 性能监控

### 统计指标

ToolCallManager 提供以下统计指标：

| 指标 | 说明 | 计算方式 |
|------|------|---------|
| `total_calls` | 总调用次数 | 累计所有调用 |
| `successful_calls` | 成功调用次数 | status == SUCCESS |
| `failed_calls` | 失败调用次数 | status == FAILED |
| `timeout_calls` | 超时调用次数 | status == TIMEOUT |
| `rate_limited_calls` | 被限流次数 | 因速率限制拒绝 |
| `success_rate` | 成功率 | successful / total |
| `avg_execution_time` | 平均执行时间 | 总时间 / 总次数 |

### 获取统计

```python
stats = manager.get_stats()

print(f"""
工具调用统计:
├─ 总调用数: {stats['total_calls']}
├─ 成功数: {stats['successful_calls']}
├─ 失败数: {stats['failed_calls']}
├─ 超时数: {stats['timeout_calls']}
├─ 成功率: {stats['success_rate']:.2%}
├─ 平均执行时间: {stats['avg_execution_time']:.3f}秒
└─ 工具数量: {stats['tool_count']}
""")
```

---

## 错误处理

### 常见错误

| 错误类型 | 原因 | 解决方法 |
|---------|------|---------|
| `ValueError: 缺少必需参数` | 未提供必需参数 | 检查 required_params |
| `RuntimeError: 工具不存在` | 工具未注册 | 先调用 register_tool() |
| `TimeoutError` | 执行超时 | 增加 timeout 参数 |
| `RuntimeError: 速率限制` | 调用过于频繁 | 等待或调整速率限制 |

### 错误处理示例

```python
try:
    result = await manager.call_tool(
        tool_name="my_tool",
        parameters={"input": "data"}
    )
except ValueError as e:
    logger.error(f"参数错误: {e}")
except RuntimeError as e:
    logger.error(f"执行错误: {e}")
except TimeoutError as e:
    logger.error(f"超时: {e}")
```

---

## 完整使用示例

### 示例 1: 简单工具调用

```python
import asyncio
from core.tools.base import (
    ToolDefinition, ToolCategory, ToolCapability, ToolRegistry
)
from core.tools.tool_call_manager import ToolCallManager

# 1. 定义工具处理器
async def hello_handler(params, context):
    name = params.get("name", "World")
    return {"message": f"Hello, {name}!"}

# 2. 创建工具定义
tool = ToolDefinition(
    tool_id="hello_tool",
    name="Hello Tool",
    category=ToolCategory.CHAT_COMPLETION,
    description="问候工具",
    capability=ToolCapability(
        input_types=["text"],
        output_types=["message"],
        domains=["all"],
        task_types=["greeting"]
    ),
    required_params=[],
    optional_params=["name"],
    handler=hello_handler
)

# 3. 创建管理器并注册工具
manager = ToolCallManager()
manager.register_tool(tool)

# 4. 调用工具
async def main():
    result = await manager.call_tool(
        tool_name="hello_tool",
        parameters={"name": "Athena"}
    )

    if result.status == "success":
        print(result.result["message"])  # Hello, Athena!

    # 查看统计
    stats = manager.get_stats()
    print(f"成功率: {stats['success_rate']:.2%}")

asyncio.run(main())
```

### 示例 2: 智能工具选择

```python
import asyncio
from core.tools.base import ToolRegistry, ToolCategory, ToolCapability
from core.tools.selector import ToolSelector, SelectionStrategy

# 创建注册中心并注册多个工具
registry = ToolRegistry()

# 注册代码分析工具
code_analyzer = ToolDefinition(
    tool_id="code_analyzer",
    name="Code Analyzer",
    category=ToolCategory.CODE_ANALYSIS,
    description="代码分析工具",
    capability=ToolCapability(
        input_types=["code"],
        output_types=["analysis"],
        domains=["software"],
        task_types=["analysis"]
    )
)

# 注册文档处理工具
doc_processor = ToolDefinition(
    tool_id="doc_processor",
    name="Doc Processor",
    category=ToolCategory.DOCUMENT_PROCESSING,
    description="文档处理工具",
    capability=ToolCapability(
        input_types=["document"],
        output_types=["processed"],
        domains=["all"],
        task_types=["processing"]
    )
)

registry.register(code_analyzer)
registry.register(doc_processor)

# 创建选择器
selector = ToolSelector(
    registry=registry,
    strategy=SelectionStrategy.BALANCED
)

# 根据任务选择工具
async def main():
    # 选择代码分析工具
    tool = await selector.select_tool(
        task_type="analysis",
        domain="software"
    )

    if tool:
        print(f"选择工具: {tool.name}")  # Code Analyzer

asyncio.run(main())
```

---

## API 版本历史

### v1.0.0 (2026-01-25)
- ✨ 初始版本
- ✨ 统一 ToolDefinition 定义
- ✨ 线程安全的 ToolRegistry
- ✨ 智能工具选择器
- ✨ 速率限制支持
- ✨ 完整的性能监控

---

## 相关文档

- [工具系统测试文档](../../tests/unit/tools/README.md)
- [Pytest 测试配置](../../tests/pytest.ini)
- [项目主文档](../../README.md)

---

## 许可证

Copyright © 2026 Athena平台团队. All rights reserved.
