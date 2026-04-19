# 统一工具注册表培训指南

> **版本**: v2.0.0
> **培训对象**: Athena平台开发者
> **预计时长**: 60分钟
> **更新日期**: 2026-04-19

---

## 培训大纲

1. [新架构讲解](#新架构讲解) (15分钟)
2. [核心概念](#核心概念) (10分钟)
3. [实战练习](#实战练习) (25分钟)
4. [最佳实践](#最佳实践) (5分钟)
5. [常见陷阱](#常见陷阱) (5分钟)

---

## 新架构讲解

### 为什么要统一注册表？

**问题**: 历史上存在4个独立的工具注册表

```
之前:
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  ToolRegistry   │  │EnhancedToolSystem│  │ToolSetRegistry  │
│  (基础注册表)    │  │  (增强系统)      │  │  (工具集管理)    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                     │                     │
         └─────────────────────┴─────────────────────┘
                              │
                    功能重叠、维护困难、性能问题
```

**解决**: 统一注册表整合所有功能

```
现在:
┌─────────────────────────────────────────┐
│        UnifiedToolRegistry              │
│                                         │
│  ✅ 单例模式  ✅ 懒加载  ✅ 健康检查     │
│  ✅ 自动发现  ✅ 线程安全  ✅ 向后兼容   │
└─────────────────────────────────────────┘
         │         │         │
    ┌────┴────┐ ┌──┴────┐ ┌┴──────┐
    │ 专利工具 │ │ 法律工具 │ │ 通用工具 │
    └─────────┘ └───────┘ └───────┘
```

### 核心优势

| 维度 | 旧系统 | 统一注册表 | 改善 |
|-----|--------|-----------|------|
| **代码复杂度** | 4个注册表 | 1个注册表 | ↓ 75% |
| **启动时间** | ~2.5s | ~1.2s | ↓ 52% |
| **内存占用** | ~180MB | ~95MB | ↓ 47% |
| **工具查找** | ~35ms | ~8ms | ↓ 77% |
| **并发性能** | 850 QPS | 2100 QPS | ↑ 147% |

---

## 核心概念

### 1. 单例模式

**概念**: 全局唯一实例，所有代码共享同一个注册表。

**为什么**:
- ✅ 避免重复初始化
- ✅ 保证数据一致性
- ✅ 减少内存占用

**代码示例**:
```python
from core.tools.unified_registry import get_unified_registry

# 无论调用多少次，返回同一个实例
registry1 = get_unified_registry()
registry2 = get_unified_registry()

assert registry1 is registry2  # True
```

**错误示例**:
```python
# ❌ 不要这样做
from core.tools.unified_registry import UnifiedToolRegistry

registry1 = UnifiedToolRegistry()  # 创建多个实例
registry2 = UnifiedToolRegistry()  # 浪费内存，数据不一致
```

---

### 2. 懒加载机制

**概念**: 工具在第一次使用时才加载，而不是启动时全部加载。

**为什么**:
- ✅ 减少启动时间
- ✅ 降低内存占用
- ✅ 按需加载，提升性能

**代码示例**:
```python
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()

# 注册懒加载工具
registry.register_lazy(
    tool_id="heavy_model",
    import_path="core.tools.models",
    function_name="load_llm_model",
    metadata={"description": "大型语言模型"}
)

# 此时工具未加载，只是记录配置
print("工具已注册但未加载")

# 第一次使用时才真正加载
tool = registry.get("heavy_model")
result = tool.function(text="分析")  # 此时才加载模型

# 后续调用直接使用缓存的实例
result2 = tool.function(text="分析2")  # 快速，无需重新加载
```

**性能对比**:
```
预加载方式:
启动时间: 2.5秒
内存占用: 180MB

懒加载方式:
启动时间: 1.2秒 (↓ 52%)
内存占用: 95MB (↓ 47%)
首次调用: +10ms (可接受)
```

---

### 3. 健康状态管理

**概念**: 自动监控工具健康状态，及时发现和处理问题。

**健康状态**:
- `HEALTHY`: 工具正常运行
- `DEGRADED`: 工具可用但性能下降
- `UNHEALTHY`: 工具不可用
- `UNKNOWN`: 状态未知

**代码示例**:
```python
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()

# 检查单个工具健康状态
health = registry.check_health("patent_analyzer")

if health == ToolHealthStatus.HEALTHY:
    print("✅ 工具健康，可以正常使用")
elif health == ToolHealthStatus.DEGRADED:
    print("⚠️ 工具降级，建议检查")
elif health == ToolHealthStatus.UNHEALTHY:
    print("❌ 工具不健康，避免使用")

# 批量检查所有工具
report = registry.health_check_all()
print(f"健康工具: {report['healthy_count']}")
print(f"不健康工具: {report['unhealthy_count']}")

# 获取所有不健康工具
unhealthy = registry.get_unhealthy_tools()
for tool_name, status in unhealthy.items():
    print(f"⚠️ {tool_name}: {status.value}")
```

**实际应用**:
```python
# 定期健康检查（生产环境）
import time

def monitor_tool_health():
    registry = get_unified_registry()

    while True:
        report = registry.health_check_all()

        # 发送告警
        if report['unhealthy_count'] > 0:
            send_alert(f"发现{report['unhealthy_count']}个不健康工具")

        # 记录指标
        metrics.gauge('tools.healthy', report['healthy_count'])
        metrics.gauge('tools.unhealthy', report['unhealthy_count'])

        time.sleep(300)  # 每5分钟
```

---

### 4. 自动发现机制

**概念**: 使用`@tool`装饰器自动注册工具，无需手动调用注册方法。

**代码示例**:
```python
from core.tools.decorators import tool
from core.tools.base import ToolCategory, ToolPriority

# 使用装饰器自动注册
@tool(
    name="patent_search",
    category=ToolCategory.PATENT,
    description="搜索专利数据库",
    priority=ToolPriority.HIGH
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

# 工具已自动注册，可以直接使用
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()
tool = registry.get("patent_search")
print(tool)  # <ToolDefinition: patent_search>
```

**工作原理**:
```python
# @tool装饰器内部实现（简化版）
def tool(**kwargs):
    def decorator(func):
        # 创建工具定义
        tool_def = ToolDefinition(
            name=kwargs.get('name', func.__name__),
            function=func,
            category=kwargs.get('category', ToolCategory.GENERAL),
            description=kwargs.get('description', func.__doc__),
            **kwargs
        )

        # 自动注册到统一注册表
        registry = get_unified_registry()
        registry.register(tool_def)

        return func
    return decorator
```

---

### 5. 线程安全

**概念**: 使用锁机制保证多线程环境下数据一致性。

**为什么需要**:
```python
# 场景: 多线程同时注册工具
# 线程1
registry.register(tool1)

# 线程2
registry.register(tool2)

# 如果没有锁，可能导致:
# - 工具列表损坏
# - 注册失败
# - 数据不一致
```

**实现方式**:
```python
import threading

class UnifiedToolRegistry:
    def __init__(self):
        self._lock = threading.RLock()  # 可重入锁
        self._tools = {}

    def register(self, tool):
        with self._lock:  # 加锁
            # 安全地修改工具列表
            self._tools[tool.name] = tool

    def get(self, name):
        with self._lock:  # 加锁
            # 安全地读取工具列表
            return self._tools.get(name)
```

**用户无需关心**:
- 统一注册表已内置线程安全机制
- 用户正常使用即可，无需额外操作
- 在多线程环境下自动保证数据一致性

---

## 实战练习

### 练习1: 创建和注册工具 (10分钟)

**任务**: 创建一个专利检索工具

**步骤**:

1. 创建文件`core/tools/patent_tools.py`:
```python
from core.tools.decorators import tool
from core.tools.base import ToolCategory, ToolPriority

@tool(
    name="patent_retrieval",
    category=ToolCategory.PATENT,
    description="从专利数据库检索专利",
    priority=ToolPriority.HIGH
)
def retrieve_patent(patent_id: str) -> dict:
    """
    检索专利详细信息

    Args:
        patent_id: 专利号（如CN123456A）

    Returns:
        专利信息字典，包含:
        - title: 标题
        - abstract: 摘要
        - claims: 权利要求
    """
    # 模拟实现
    return {
        "patent_id": patent_id,
        "title": "一种人工智能方法",
        "abstract": "本发明公开了...",
        "claims": ["1. 一种方法..."]
    }
```

2. 测试工具:
```python
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()

# 检查工具是否注册
tool = registry.get("patent_retrieval")
print(f"工具名称: {tool.name}")
print(f"工具描述: {tool.description}")

# 调用工具
result = tool.function(patent_id="CN123456A")
print(f"检索结果: {result}")
```

3. 验证健康状态:
```python
health = registry.check_health("patent_retrieval")
print(f"健康状态: {health.value}")
```

**预期输出**:
```
工具名称: patent_retrieval
工具描述: 从专利数据库检索专利
检索结果: {'patent_id': 'CN123456A', 'title': '一种人工智能方法', ...}
健康状态: healthy
```

---

### 练习2: 使用懒加载 (5分钟)

**任务**: 创建一个懒加载的重型工具

**步骤**:

1. 创建重型工具模块`core/tools/heavy_tools.py`:
```python
import time

def heavy_computation(data: str) -> dict:
    """
    重型计算工具（模拟加载时间）

    Args:
        data: 输入数据

    Returns:
        计算结果
    """
    print("⏳ 正在加载重型工具...")
    time.sleep(2)  # 模拟加载时间
    print("✅ 重型工具加载完成")

    return {"result": f"处理了: {data}"}
```

2. 注册懒加载工具:
```python
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()

registry.register_lazy(
    tool_id="heavy_computation",
    import_path="core.tools.heavy_tools",
    function_name="heavy_computation",
    metadata={
        "category": "compute",
        "description": "重型计算工具"
    }
)

print("✅ 工具已注册（懒加载模式）")
```

3. 测试懒加载:
```python
print("\n第一次调用（触发加载）:")
tool = registry.get("heavy_computation")
result1 = tool.function(data="test1")

print("\n第二次调用（使用缓存）:")
result2 = tool.function(data="test2")

print(f"\n结果1: {result1}")
print(f"结果2: {result2}")
```

**预期输出**:
```
✅ 工具已注册（懒加载模式）

第一次调用（触发加载）:
⏳ 正在加载重型工具...
✅ 重型工具加载完成

第二次调用（使用缓存）:
(无加载时间，直接使用缓存)

结果1: {'result': '处理了: test1'}
结果2: {'result': '处理了: test2'}
```

---

### 练习3: 工具发现和过滤 (5分钟)

**任务**: 查找和过滤工具

**步骤**:

1. 查找所有专利工具:
```python
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()

# 查找专利类工具
patent_tools = registry.find(category="patent")

print(f"找到 {len(patent_tools)} 个专利工具:")
for tool in patent_tools:
    print(f"  - {tool.name}: {tool.description}")
```

2. 按名称模式查找:
```python
# 查找名称包含"search"的工具
search_tools = registry.find(name_pattern="*search*")

print(f"\n找到 {len(search_tools)} 个搜索工具:")
for tool in search_tools:
    print(f"  - {tool.name}")
```

3. 组合查询:
```python
# 查找健康的专利工具
healthy_patent_tools = registry.find(
    category="patent",
    healthy=True
)

print(f"\n找到 {len(healthy_patent_tools)} 个健康的专利工具")
```

**预期输出**:
```
找到 3 个专利工具:
  - patent_retrieval: 从专利数据库检索专利
  - patent_analyzer: 分析专利创造性
  - patent_search: 搜索专利数据库

找到 2 个搜索工具:
  - patent_search
  - case_search

找到 3 个健康的专利工具
```

---

### 练习4: 健康监控 (5分钟)

**任务**: 实现工具健康监控

**步骤**:

1. 批量健康检查:
```python
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()

# 批量检查所有工具
report = registry.health_check_all()

print("=== 工具健康报告 ===")
print(f"总工具数: {report['healthy_count'] + report['degraded_count'] + report['unhealthy_count']}")
print(f"✅ 健康: {report['healthy_count']}")
print(f"⚠️ 降级: {report['degraded_count']}")
print(f"❌ 不健康: {report['unhealthy_count']}")
```

2. 获取不健康工具:
```python
unhealthy = registry.get_unhealthy_tools()

if unhealthy:
    print("\n⚠️ 不健康工具列表:")
    for tool_name, status in unhealthy.items():
        print(f"  - {tool_name}: {status.value}")
else:
    print("\n✅ 所有工具都健康")
```

3. 获取统计信息:
```python
stats = registry.get_statistics()

print("\n=== 注册表统计 ===")
print(f"总工具数: {stats['total_tools']}")
print(f"懒加载工具: {stats['lazy_loaded_tools']}")
print(f"缓存命中率: {stats['cache_hit_rate']:.1%}")
print(f"平均调用时间: {stats['average_call_time']*1000:.1f}ms")
```

**预期输出**:
```
=== 工具健康报告 ===
总工具数: 48
✅ 健康: 45
⚠️ 降级: 2
❌ 不健康: 1

⚠️ 不健康工具列表:
  - old_tool: unhealthy

=== 注册表统计 ===
总工具数: 48
懒加载工具: 10
缓存命中率: 89.7%
平均调用时间: 15.2ms
```

---

## 最佳实践

### 1. 工具命名

✅ **推荐**:
```python
@tool(name="patent_creative_analyzer")
def analyze(): pass
```

❌ **避免**:
```python
@tool(name="tool1")
def analyze(): pass
```

**规则**:
- 使用描述性名称
- 使用小写字母和下划线
- 名称应反映工具功能

---

### 2. 参数类型注解

✅ **推荐**:
```python
@tool
def search_patents(query: str, limit: int = 10) -> dict:
    """搜索专利"""
    return {"results": []}
```

❌ **避免**:
```python
@tool
def search_patents(query, limit=10):
    """搜索专利"""
    return {"results": []}
```

**好处**:
- IDE自动补全
- 类型检查
- 文档自动生成

---

### 3. 错误处理

✅ **推荐**:
```python
@tool
def divide(a: float, b: float) -> float:
    """除法运算"""
    try:
        return a / b
    except ZeroDivisionError:
        raise ValueError("除数不能为零")
```

❌ **避免**:
```python
@tool
def divide(a: float, b: float) -> float:
    """除法运算"""
    try:
        return a / b
    except:
        return None  # 吞噬异常
```

**原则**:
- 明确异常类型
- 提供有用的错误信息
- 不要吞噬异常

---

### 4. 文档字符串

✅ **推荐**:
```python
@tool
def analyze_patent(patent_id: str) -> dict:
    """
    分析专利创造性

    Args:
        patent_id: 专利号（如CN123456A）

    Returns:
        分析结果字典，包含:
        - creativity_score (float): 创造性评分 (0-1)
        - conclusion (str): 结论

    Raises:
        ValueError: 专利号格式无效
        PatentNotFoundError: 专利不存在

    Example:
        >>> analyze_patent("CN123456A")
        {"creativity_score": 0.85, "conclusion": "具有创造性"}
    """
    pass
```

❌ **避免**:
```python
@tool
def analyze_patent(patent_id: str) -> dict:
    """分析专利"""
    pass
```

**标准**:
- 使用Google风格docstring
- 包含参数说明
- 包含返回值说明
- 包含异常说明
- 包含使用示例

---

### 5. 性能优化

✅ **推荐**:
```python
from functools import lru_cache

@tool
@lru_cache(maxsize=128)
def expensive_computation(data: str) -> dict:
    """昂贵的计算（带缓存）"""
    return complex_calculation(data)
```

❌ **避免**:
```python
@tool
def expensive_computation(data: str) -> dict:
    """昂贵的计算（无缓存）"""
    return complex_calculation(data)
```

**技巧**:
- 使用缓存减少重复计算
- 使用懒加载减少启动时间
- 使用异步处理提升并发性能

---

### 6. 安全考虑

✅ **推荐**:
```python
from pydantic import BaseModel, Field

class SafeInput(BaseModel):
    patent_id: str = Field(..., regex=r"^CN\d+[A-Z]$")
    limit: int = Field(default=10, ge=1, le=100)

@tool
def safe_search(input: SafeInput) -> dict:
    """安全的专利搜索（带参数验证）"""
    return search(input.patent_id, input.limit)
```

❌ **避免**:
```python
@tool
def unsafe_search(patent_id: str) -> dict:
    """不安全的搜索"""
    return search(patent_id)  # 可能SQL注入
```

**原则**:
- 验证所有输入
- 使用参数化查询
- 限制资源使用

---

## 常见陷阱

### 陷阱1: 忘记使用单例

❌ **错误代码**:
```python
from core.tools.unified_registry import UnifiedToolRegistry

# 创建多个实例
registry1 = UnifiedToolRegistry()
registry2 = UnifiedToolRegistry()

# 问题: 数据不一致
registry1.register(tool1)
# registry2中没有tool1
```

✅ **正确做法**:
```python
from core.tools.unified_registry import get_unified_registry

# 使用单例
registry = get_unified_registry()
```

---

### 陷阱2: 懒加载工具导入路径错误

❌ **错误代码**:
```python
registry.register_lazy(
    tool_id="my_tool",
    import_path="core.tools.my_tool",  # 错误: 模块路径
    function_name="my_function"
)

# ImportError: No module named 'core.tools.my_tool'
```

✅ **正确做法**:
```python
registry.register_lazy(
    tool_id="my_tool",
    import_path="core.tools.my_tools",  # 正确: 文件名
    function_name="my_function"
)
```

**规则**: `import_path`应该是模块路径（文件名），不含`.py`后缀

---

### 陷阱3: 忽略健康检查

❌ **错误代码**:
```python
# 直接使用工具，不检查健康状态
tool = registry.get("patent_analyzer")
result = tool.function(data=input_data)  # 可能失败
```

✅ **正确做法**:
```python
# 先检查健康状态
health = registry.check_health("patent_analyzer")

if health == ToolHealthStatus.HEALTHY:
    tool = registry.get("patent_analyzer")
    result = tool.function(data=input_data)
else:
    print(f"工具不健康: {health.value}")
    # 使用备用方案或降级处理
```

---

### 陷阱4: 缓存未清理

❌ **错误代码**:
```python
# 长时间运行不清理缓存
# 导致内存占用持续增长
```

✅ **正确做法**:
```python
# 定期清理缓存
import time

while True:
    time.sleep(3600)  # 每小时
    registry.clear_cache()
    print("✅ 缓存已清理")
```

---

### 陷阱5: 并发安全问题

❌ **错误代码**:
```python
# 多线程环境下直接访问内部数据
tools = registry._tools  # 不应该访问私有属性
```

✅ **正确做法**:
```python
# 使用公共API
tools = registry.list_tools()  # 线程安全
```

**原则**: 不要访问私有属性（`_`开头），使用公共API

---

## 参考资料

- **API文档**: `docs/api/UNIFIED_TOOL_REGISTRY_API.md`
- **迁移指南**: `docs/guides/UNIFIED_TOOL_REGISTRY_MIGRATION_GUIDE.md`
- **示例代码**: `examples/tools/unified_registry_examples.py`
- **测试用例**: `tests/core/tools/test_unified_registry.py`

---

## 培训完成检查清单

完成培训后，你应该能够：

- [ ] 理解统一注册表的核心概念
- [ ] 正确使用`@tool`装饰器注册工具
- [ ] 使用懒加载优化性能
- [ ] 实现工具健康监控
- [ ] 避免常见陷阱
- [ ] 应用最佳实践

---

**培训完成！** 🎉

如有疑问，请联系: xujian519@gmail.com
