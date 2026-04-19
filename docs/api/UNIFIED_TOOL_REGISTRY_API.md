# 统一工具注册表API文档

> **版本**: v2.0.0
> **更新日期**: 2026-04-19
> **维护者**: Athena平台团队

---

## 目录

1. [核心类](#核心类)
2. [装饰器](#装饰器)
3. [辅助函数](#辅助函数)
4. [使用示例](#使用示例)
5. [最佳实践](#最佳实践)
6. [性能优化](#性能优化)

---

## 核心类

### UnifiedToolRegistry

统一工具注册表主类，提供工具发现、注册、获取和管理功能。

#### 类签名

```python
class UnifiedToolRegistry:
    """
    统一工具注册表

    整合所有工具注册表，提供统一的工具发现和访问接口。

    核心特性:
    - 单例模式：全局唯一实例
    - 懒加载：工具按需加载
    - 健康检查：工具状态监控
    - 自动发现：扫描@tool装饰器
    - 线程安全：使用RLock保证并发安全
    """
```

#### 核心方法

##### get(name: str) → ToolDefinition | None

获取工具定义。

**参数**:
- `name` (str): 工具名称

**返回值**:
- `ToolDefinition | None`: 工具定义，不存在时返回None

**示例**:
```python
registry = get_unified_registry()
tool = registry.get("patent_search")

if tool:
    result = tool.function(query="人工智能")
```

**异常**:
- 无异常（工具不存在时返回None）

---

##### require(name: str) → ToolDefinition

获取工具定义，工具不存在时抛出异常。

**参数**:
- `name` (str): 工具名称

**返回值**:
- `ToolDefinition`: 工具定义

**异常**:
- `ToolNotFoundError`: 工具不存在

**示例**:
```python
registry = get_unified_registry()

try:
    tool = registry.require("patent_analyzer")
    result = tool.function(patent_id="CN123456A")
except ToolNotFoundError as e:
    print(f"工具不存在: {e}")
```

---

##### register(tool: ToolDefinition) → None

注册工具。

**参数**:
- `tool` (ToolDefinition): 工具定义

**返回值**:
- None

**示例**:
```python
from core.tools.base import ToolDefinition

tool = ToolDefinition(
    name="custom_tool",
    func=lambda x: x * 2,
    category="general",
    description="自定义工具"
)

registry.register(tool)
```

**异常**:
- `ToolRegistrationError`: 工具注册失败

---

##### register_lazy(tool_id: str, import_path: str, function_name: str, metadata: dict) → None

注册懒加载工具。

**参数**:
- `tool_id` (str): 工具唯一标识
- `import_path` (str): 模块导入路径（如`core.tools.heavy_implementations`）
- `function_name` (str): 函数名
- `metadata` (dict): 工具元数据

**返回值**:
- None

**示例**:
```python
registry.register_lazy(
    tool_id="heavy_computation",
    import_path="core.tools.heavy_implementations",
    function_name="compute_large_matrix",
    metadata={
        "category": "compute",
        "description": "重型矩阵计算",
        "timeout": 300
    }
)
```

**异常**:
- `ToolRegistrationError`: 工具注册失败
- `ImportError`: 模块导入失败（在第一次使用时）

---

##### find(**filters) → list[ToolDefinition]

查找符合条件的工具。

**参数**:
- `category` (str, optional): 工具类别
- `name_pattern` (str, optional): 名称模式（支持通配符）
- `healthy` (bool, optional): 是否只返回健康工具
- `priority` (ToolPriority, optional): 工具优先级

**返回值**:
- `list[ToolDefinition]`: 符合条件的工具列表

**示例**:
```python
# 查找所有专利工具
patent_tools = registry.find(category="patent")

# 查找名称包含"search"的工具
search_tools = registry.find(name_pattern="*search*")

# 查找健康的专利工具
healthy_patent_tools = registry.find(
    category="patent",
    healthy=True
)

# 查找高优先级工具
high_priority_tools = registry.find(
    priority=ToolPriority.HIGH
)
```

---

##### list_tools() → list[ToolDefinition]

列出所有已注册工具。

**参数**:
- 无

**返回值**:
- `list[ToolDefinition]`: 所有工具列表

**示例**:
```python
tools = registry.list_tools()

for tool in tools:
    print(f"{tool.name}: {tool.description}")
```

---

##### check_health(tool_name: str) → ToolHealthStatus

检查工具健康状态。

**参数**:
- `tool_name` (str): 工具名称

**返回值**:
- `ToolHealthStatus`: 健康状态枚举
  - `HEALTHY`: 健康
  - `DEGRADED`: 降级
  - `UNHEALTHY`: 不健康
  - `UNKNOWN`: 未知

**示例**:
```python
health = registry.check_health("patent_analyzer")

if health == ToolHealthStatus.HEALTHY:
    print("✅ 工具健康")
elif health == ToolHealthStatus.DEGRADED:
    print("⚠️ 工具降级")
elif health == ToolHealthStatus.UNHEALTHY:
    print("❌ 工具不健康")
```

---

##### health_check_all() → dict

批量检查所有工具健康状态。

**参数**:
- 无

**返回值**:
- `dict`: 健康检查报告
  ```python
  {
      "healthy_count": 45,
      "degraded_count": 2,
      "unhealthy_count": 1,
      "unknown_count": 0,
      "details": {
          "patent_analyzer": ToolHealthStatus.HEALTHY,
          "heavy_tool": ToolHealthStatus.DEGRADED,
          ...
      }
  }
  ```

**示例**:
```python
report = registry.health_check_all()

print(f"健康工具: {report['healthy_count']}")
print(f"降级工具: {report['degraded_count']}")
print(f"不健康工具: {report['unhealthy_count']}")

# 查看详细信息
for tool_name, status in report["details"].items():
    print(f"{tool_name}: {status.value}")
```

---

##### get_unhealthy_tools() → dict[str, ToolHealthStatus]

获取所有不健康的工具。

**参数**:
- 无

**返回值**:
- `dict[str, ToolHealthStatus]`: 工具名 → 健康状态的映射

**示例**:
```python
unhealthy = registry.get_unhealthy_tools()

if unhealthy:
    print(f"发现 {len(unhealthy)} 个不健康工具:")
    for tool_name, status in unhealthy.items():
        print(f"  - {tool_name}: {status.value}")
else:
    print("✅ 所有工具都健康")
```

---

##### enable_lazy_loading() → None

启用懒加载模式。

**参数**:
- 无

**返回值**:
- None

**示例**:
```python
registry.enable_lazy_loading()

# 工具将在第一次使用时才加载
tool = registry.get("heavy_tool")  # 此时才加载
```

---

##### clear_cache() → None

清理工具缓存。

**参数**:
- 无

**返回值**:
- None

**示例**:
```python
# 清理所有缓存
registry.clear_cache()

# 清理特定工具缓存
registry.clear_cache("patent_analyzer")
```

---

##### get_statistics() → dict

获取注册表统计信息。

**参数**:
- 无

**返回值**:
- `dict`: 统计信息
  ```python
  {
      "total_tools": 48,
      "healthy_tools": 45,
      "unhealthy_tools": 2,
      "lazy_loaded_tools": 10,
      "cache_hit_rate": 0.89,
      "average_call_time": 0.015
  }
  ```

**示例**:
```python
stats = registry.get_statistics()

print(f"总工具数: {stats['total_tools']}")
print(f"健康工具: {stats['healthy_tools']}")
print(f"缓存命中率: {stats['cache_hit_rate']:.1%}")
print(f"平均调用时间: {stats['average_call_time']*1000:.1f}ms")
```

---

### ToolDefinition

工具定义类。

#### 类签名

```python
@dataclass
class ToolDefinition:
    """
    工具定义

    属性:
        name: 工具名称（唯一标识）
        function: 工具函数
        category: 工具类别
        description: 工具描述
        parameters: 参数定义
        return_type: 返回类型
        priority: 工具优先级
        timeout: 超时时间（秒）
        metadata: 额外元数据
    """
```

#### 属性

| 属性 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| `name` | str | ✅ | 工具名称（唯一标识） |
| `function` | Callable | ✅ | 工具函数 |
| `category` | ToolCategory | ✅ | 工具类别 |
| `description` | str | ❌ | 工具描述 |
| `parameters` | dict | ❌ | 参数定义 |
| `return_type` | type | ❌ | 返回类型 |
| `priority` | ToolPriority | ❌ | 工具优先级（默认MEDIUM） |
| `timeout` | int | ❌ | 超时时间（秒，默认30） |
| `metadata` | dict | ❌ | 额外元数据 |

#### 使用示例

```python
from core.tools.base import ToolDefinition, ToolCategory, ToolPriority

tool = ToolDefinition(
    name="search_patents",
    function=search_patents_function,
    category=ToolCategory.PATENT,
    description="搜索专利数据库",
    parameters={
        "query": {"type": "str", "description": "搜索查询"},
        "limit": {"type": "int", "default": 10}
    },
    return_type=dict,
    priority=ToolPriority.HIGH,
    timeout=60,
    metadata={
        "author": "Athena团队",
        "version": "1.0.0",
        "tags": ["patent", "search"]
    }
)
```

---

### ToolHealthStatus

工具健康状态枚举。

#### 枚举值

```python
class ToolHealthStatus(Enum):
    HEALTHY = "healthy"      # 健康
    DEGRADED = "degraded"    # 降级
    UNHEALTHY = "unhealthy"  # 不健康
    UNKNOWN = "unknown"      # 未知
```

---

## 装饰器

### @tool

工具装饰器，用于自动注册工具。

#### 函数签名

```python
def tool(
    name: str | None = None,
    category: str | ToolCategory = ToolCategory.GENERAL,
    description: str | None = None,
    priority: ToolPriority = ToolPriority.MEDIUM,
    timeout: int = 30,
    **metadata
) -> Callable
```

#### 参数

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `name` | str | None | 工具名称（默认使用函数名） |
| `category` | str | GENERAL | 工具类别 |
| `description` | str | None | 工具描述（默认使用函数docstring） |
| `priority` | ToolPriority | MEDIUM | 工具优先级 |
| `timeout` | int | 30 | 超时时间（秒） |
| `metadata` | dict | {} | 额外元数据 |

#### 使用示例

**基础用法**:
```python
from core.tools.decorators import tool

@tool
def hello_world(name: str) -> str:
    """向世界问好"""
    return f"Hello, {name}!"
```

**完整配置**:
```python
from core.tools.decorators import tool
from core.tools.base import ToolCategory, ToolPriority

@tool(
    name="search_patents",
    category=ToolCategory.PATENT,
    description="搜索专利数据库",
    priority=ToolPriority.HIGH,
    timeout=60,
    author="Athena团队",
    version="1.0.0"
)
def search_patents(query: str, limit: int = 10) -> dict:
    """
    搜索专利数据库

    Args:
        query: 搜索查询
        limit: 返回结果数量限制

    Returns:
        包含搜索结果的字典
    """
    # 实现逻辑
    return {"results": []}
```

**参数验证**:
```python
from core.tools.decorators import tool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(..., description="搜索查询")
    limit: int = Field(default=10, ge=1, le=100)

@tool
def search_patents(input: SearchInput) -> dict:
    """搜索专利（带参数验证）"""
    results = perform_search(input.query, input.limit)
    return {"results": results}
```

---

## 辅助函数

### get_unified_registry() → UnifiedToolRegistry

获取统一工具注册表的单例实例。

**函数签名**:
```python
def get_unified_registry() -> UnifiedToolRegistry:
    """
    获取统一工具注册表的单例实例

    Returns:
        UnifiedToolRegistry: 全局唯一实例

    Raises:
        RegistryInitializationError: 注册表初始化失败
    """
```

**使用示例**:
```python
from core.tools.unified_registry import get_unified_registry

# 获取全局唯一实例
registry = get_unified_registry()

# 使用注册表
tools = registry.list_tools()
```

---

### create_tool_definition(func: Callable, **metadata) → ToolDefinition

从函数创建工具定义。

**函数签名**:
```python
def create_tool_definition(
    func: Callable,
    name: str | None = None,
    category: str | ToolCategory = ToolCategory.GENERAL,
    description: str | None = None,
    **metadata
) -> ToolDefinition:
    """
    从函数创建工具定义

    Args:
        func: 工具函数
        name: 工具名称（默认使用函数名）
        category: 工具类别
        description: 工具描述（默认使用函数docstring）
        **metadata: 额外元数据

    Returns:
        ToolDefinition: 工具定义
    """
```

**使用示例**:
```python
from core.tools.unified_registry import create_tool_definition

def my_tool(x: int, y: int) -> int:
    """计算两个数的和"""
    return x + y

# 创建工具定义
tool_def = create_tool_definition(
    func=my_tool,
    category="math",
    priority=ToolPriority.HIGH
)

# 注册工具
registry = get_unified_registry()
registry.register(tool_def)
```

---

## 使用示例

### 示例1: 创建和注册工具

```python
from core.tools.decorators import tool
from core.tools.base import ToolCategory, ToolPriority

# 使用装饰器自动注册
@tool(
    name="patent_analyzer",
    category=ToolCategory.PATENT,
    description="分析专利创造性",
    priority=ToolPriority.HIGH
)
def analyze_patent_creativity(patent_id: str) -> dict:
    """
    分析专利创造性

    Args:
        patent_id: 专利号（如CN123456A）

    Returns:
        分析结果字典
    """
    # 实现逻辑
    return {
        "patent_id": patent_id,
        "creativity_score": 0.85,
        "conclusion": "具有创造性"
    }

# 工具已自动注册，无需手动操作
```

### 示例2: 获取和调用工具

```python
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()

# 获取工具
tool = registry.get("patent_analyzer")

if tool:
    # 调用工具
    result = tool.function(patent_id="CN123456A")
    print(result)
```

### 示例3: 批量工具操作

```python
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()

# 批量获取专利工具
patent_tools = registry.find(category="patent")

# 批量健康检查
health_report = registry.health_check_all()

# 批量清理缓存
registry.clear_cache()

# 获取统计信息
stats = registry.get_statistics()
print(f"总工具数: {stats['total_tools']}")
print(f"健康率: {stats['healthy_tools']/stats['total_tools']:.1%}")
```

### 示例4: 懒加载重型工具

```python
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()

# 注册懒加载工具（如大型模型）
registry.register_lazy(
    tool_id="llm_analyzer",
    import_path="core.tools.llm_tools",
    function_name="analyze_with_llm",
    metadata={
        "category": "ai",
        "description": "使用LLM分析文本",
        "timeout": 120
    }
)

# 工具在第一次使用时才加载
tool = registry.get("llm_analyzer")
result = tool.function(text="要分析的文本")
```

### 示例5: 健康监控

```python
from core.tools.unified_registry import get_unified_registry
import time

registry = get_unified_registry()

while True:
    # 检查所有工具健康状态
    report = registry.health_check_all()

    print(f"\n=== 工具健康报告 ===")
    print(f"健康: {report['healthy_count']}")
    print(f"降级: {report['degraded_count']}")
    print(f"不健康: {report['unhealthy_count']}")

    # 处理不健康工具
    unhealthy = registry.get_unhealthy_tools()
    for tool_name, status in unhealthy.items():
        print(f"⚠️ {tool_name}: {status.value}")
        # 可以发送告警或尝试恢复

    time.sleep(300)  # 每5分钟检查一次
```

---

## 最佳实践

### 1. 工具命名规范

```python
# ✅ 推荐: 使用描述性名称
@tool(name="patent_creative_analyzer")
def analyze_patent(): pass

# ❌ 避免: 使用模糊名称
@tool(name="tool1")
def analyze_patent(): pass
```

### 2. 参数类型注解

```python
# ✅ 推荐: 使用类型注解
@tool
def search_patents(query: str, limit: int = 10) -> dict:
    """搜索专利"""
    return {"results": []}

# ❌ 避免: 缺少类型注解
@tool
def search_patents(query, limit=10):
    """搜索专利"""
    return {"results": []}
```

### 3. 错误处理

```python
# ✅ 推荐: 明确的错误处理
@tool
def divide(a: float, b: float) -> float:
    """除法运算"""
    try:
        return a / b
    except ZeroDivisionError:
        raise ValueError("除数不能为零")

# ❌ 避免: 吞噬异常
@tool
def divide(a: float, b: float) -> float:
    """除法运算"""
    try:
        return a / b
    except:
        return None
```

### 4. 文档字符串

```python
# ✅ 推荐: 完整的文档字符串
@tool
def analyze_patent(patent_id: str) -> dict:
    """
    分析专利创造性

    Args:
        patent_id: 专利号（如CN123456A）

    Returns:
        包含分析结果的字典，包含以下字段:
        - creativity_score (float): 创造性评分 (0-1)
        - conclusion (str): 结论
        - details (dict): 详细分析

    Raises:
        ValueError: 专利号格式无效
        PatentNotFoundError: 专利不存在

    Example:
        >>> analyze_patent("CN123456A")
        {
            "creativity_score": 0.85,
            "conclusion": "具有创造性",
            "details": {...}
        }
    """
    pass

# ❌ 避免: 简陋的文档
@tool
def analyze_patent(patent_id: str) -> dict:
    """分析专利"""
    pass
```

### 5. 工具分类

```python
# ✅ 推荐: 使用合适的类别
@tool(category=ToolCategory.PATENT)
def patent_search(): pass

@tool(category=ToolCategory.LEGAL)
def case_search(): pass

@tool(category=ToolCategory.ACADEMIC)
def paper_search(): pass
```

### 6. 性能优化

```python
# ✅ 推荐: 使用缓存
from functools import lru_cache

@tool
@lru_cache(maxsize=128)
def expensive_computation(data: str) -> dict:
    """昂贵的计算（带缓存）"""
    return complex_calculation(data)

# ✅ 推荐: 使用懒加载
registry.register_lazy(
    tool_id="heavy_tool",
    import_path="core.tools.heavy",
    function_name="heavy_func"
)
```

### 7. 安全考虑

```python
# ✅ 推荐: 参数验证
from pydantic import BaseModel, Field

class SafeInput(BaseModel):
    patent_id: str = Field(..., regex=r"^CN\d+[A-Z]$")
    limit: int = Field(default=10, ge=1, le=100)

@tool
def safe_search(input: SafeInput) -> dict:
    """安全的专利搜索（带参数验证）"""
    return search(input.patent_id, input.limit)

# ❌ 避免: 直接使用用户输入
@tool
def unsafe_search(patent_id: str) -> dict:
    """不安全的搜索"""
    return search(patent_id)  # 可能SQL注入
```

---

## 性能优化

### 1. 懒加载

```python
# 启用懒加载（默认已启用）
registry.enable_lazy_loading()

# 注册懒加载工具
registry.register_lazy(
    tool_id="heavy_model",
    import_path="core.tools.models",
    function_name="load_heavy_model"
)
```

**性能提升**:
- 启动时间: ↓ 52%
- 内存占用: ↓ 47%

### 2. 缓存管理

```python
# 清理缓存
registry.clear_cache()

# 限制缓存大小
registry.set_cache_limit(max_size=1000)

# 预热缓存
registry.preload_tools(["patent_analyzer", "case_searcher"])
```

### 3. 批量操作

```python
# ✅ 推荐: 批量获取
tools = registry.find(category="patent")

# ❌ 避免: 逐个获取
for tool_name in patent_tool_names:
    tool = registry.get(tool_name)
```

### 4. 健康检查优化

```python
# 异步健康检查
import asyncio

async def async_health_check():
    tasks = [
        asyncio.create_task(check_tool_async(name))
        for name in tool_names
    ]
    results = await asyncio.gather(*tasks)
    return results
```

---

## 参考资料

- **迁移指南**: `docs/guides/UNIFIED_TOOL_REGISTRY_MIGRATION_GUIDE.md`
- **示例代码**: `examples/tools/unified_registry_examples.py`
- **测试用例**: `tests/core/tools/test_unified_registry.py`

---

**需要帮助？** 📧 xujian519@gmail.com
