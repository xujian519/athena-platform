# 感知模块Pyright类型检查报告

**报告日期**: 2026-01-25
**检查范围**: `core/perception/`
**工具**: Pyright 1.1.408

---

## 📊 检查结果摘要

| 指标 | 数量 |
|------|------|
| ❌ 错误 (Errors) | 398 |
| ⚠️ 警告 (Warnings) | 1579 |
| ℹ️ 信息 (Infos) | 0 |

---

## 🔍 主要问题分类

### 1. 类型注解缺失 (Missing Type Annotations)

**问题数量**: ~150

**典型错误**:
```python
# 缺少类型参数
_tasks: list[asyncio.Task] = []  # ❌ 应为 list[asyncio.Task[None]]

# 缺少参数类型
def wrapper(*args, **kwargs):  # ❌ 应为 (*args: Any, **kwargs: Any)
```

**修复建议**:
- 为泛型容器添加类型参数
- 为函数参数添加类型注解
- 使用 `typing.Any` 处理未知类型

### 2. 可选成员访问 (Optional Member Access)

**问题数量**: ~50

**典型错误**:
```python
# _global_limiter 可能为 None
l = _global_limiter
result = await l.acquire()  # ❌ l 可能为 None
```

**修复建议**:
```python
# 添加None检查
if _global_limiter is not None:
    result = await _global_limiter.acquire()
```

### 3. 未使用导入 (Unused Imports)

**问题数量**: ~80

**典型错误**:
```python
from datetime import datetime, timedelta  # ❌ timedelta 未使用
import asyncio  # ❌ 在某些文件中未使用
```

**修复建议**:
- 移除未使用的导入
- 使用 `# noqa: F401` 标记有意导入

### 4. 数据类冲突 (Dataclass Conflict)

**问题数量**: ~20

**典型错误**:
```python
@dataclass(order=True)  # ❌ 与自定义 __lt__ 冲突
class PriorityTask:
    def __lt__(self, other):  # ❌ 冲突
        pass
```

**修复建议**:
- 移除 `order=True` 或自定义比较方法
- 使用 `functools.total_ordering` 装饰器

### 5. 上下文管理器类型问题 (Context Manager Type Issues)

**问题数量**: ~30

**典型错误**:
```python
async with asyncio.to_thread(open, file_path, "rb") as f:  # ❌ 类型不匹配
    data = await f.read()
```

**修复建议**:
```python
f = await asyncio.to_thread(open, file_path, "rb")
async with f:
    data = await f.read()
```

---

## 🛠️ 修复优先级

### P0 - 必须修复 (影响功能)

1. **dataclass order冲突** (`priority_queue.py`)
   - 已在本次优化中修复

2. **asyncio.Task类型参数** (多个文件)
   ```python
   # 修复前
   _tasks: list[asyncio.Task] = []

   # 修复后
   _tasks: list[asyncio.Task[None]] = []
   ```

3. **全局实例None检查**
   ```python
   # 修复前
   def wrapper(*args, **kwargs):
       l = _global_limiter
       return await l.acquire()

   # 修复后
   def wrapper(*args, **kwargs):
       l = _global_limiter
       if l is None:
           raise RuntimeError("Limiter not initialized")
       return await l.acquire()
   ```

### P1 - 应该修复 (提升代码质量)

1. **移除未使用导入**
2. **添加参数类型注解**
3. **修复上下文管理器使用**

### P2 - 可以修复 (最佳实践)

1. **使用更精确的类型**
2. **添加类型守卫**
3. **改进泛型约束**

---

## 📋 详细修复清单

### 已修复问题 ✅

- [x] `priority_queue.py` - dataclass order冲突
- [x] `monitoring_metrics.py` - CPU阻塞问题

### 待修复问题 📝

#### `adaptive_rate_limiter.py` (16个错误)
```python
# 1. 添加类型参数
- _workers: list[asyncio.Task] = []
+ _workers: list[asyncio.Task[None]] = []

# 2. 修复上下文管理器
async def __aexit__(self, exc_type, exc_val, exc_tb):
    await self.release()

# 3. 修复全局实例
def wrapper(func: Callable[[Any], Any]):
    l = limiter or _global_limiter
+   if l is None:
+       raise RuntimeError("Limiter not initialized")
```

#### `intelligent_cache_eviction.py` (5个错误)
```python
# 修复 get_stats 方法
def get_stats(self) -> CacheStats:
    if hasattr(self._impl, 'get_stats'):
        return self._impl.get_stats()
-   return CacheStats()
+   else:
+       return CacheStats()  # 各策略类需要实现 get_stats
```

#### `request_merger.py` (3个错误)
```python
# 修复全局实例
def wrapper(func: Callable) -> Callable:
    m = merger or _global_merger
+   if m is None:
+       raise RuntimeError("Merger not initialized")
```

#### `__init__.py` (12个错误)
```python
# 修复类型不匹配
all_processors = [
    text_processor,
    image_processor,
    # ...
]
- await monitor.start_monitoring(all_processors)
+ await monitor.start_monitoring(cast(list[BaseProcessor], all_processors))

# 需要添加
from typing import cast
```

---

## 🎯 修复建议和最佳实践

### 1. 全局实例处理

**问题**: 全局实例可能为None导致访问错误

**解决方案**:
```python
# 方案A: 使用类型守卫
_global_instance: MyClass | None = None

def get_instance() -> MyClass:
    global _global_instance
    if _global_instance is None:
        _global_instance = MyClass()
    return _global_instance

# 方案B: 延迟初始化
class _InstanceHolder:
    instance: MyClass | None = None

_holder = _InstanceHolder()

def get_instance() -> MyClass:
    if _holder.instance is None:
        _holder.instance = MyClass()
    return _holder.instance
```

### 2. 泛型类型参数

**问题**: 泛型容器缺少类型参数

**解决方案**:
```python
# 正确做法
_tasks: list[asyncio.Task[None]] = []
_cache: dict[str, CacheEntry] = {}
_callbacks: dict[str, list[Callable]] = {}

# 复杂泛型
from typing import TypeVar
T = TypeVar('T')

class Container(Generic[T]):
    items: list[T] = []
```

### 3. 异步上下文管理器

**问题**: asyncio.to_thread与async with不兼容

**解决方案**:
```python
# ❌ 错误
async with asyncio.to_thread(open, path, "r") as f:
    data = await f.read()

# ✅ 正确
f = await asyncio.to_thread(open, path, "r")
try:
    data = await f.read()
finally:
    await asyncio.to_thread(f.close)
```

### 4. 装饰器类型

**问题**: 装饰器函数类型推断

**解决方案**:
```python
from typing import TypeVar, Callable, ParamSpec

P = ParamSpec('P')
R = TypeVar('R')

def decorator(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return await func(*args, **kwargs)
    return wrapper
```

---

## 📈 修复进度

| 文件 | 错误数 | 已修复 | 待修复 |
|------|--------|--------|--------|
| `priority_queue.py` | 1 | 1 | 0 |
| `adaptive_rate_limiter.py` | 16 | 0 | 16 |
| `intelligent_cache_eviction.py` | 5 | 0 | 5 |
| `request_merger.py` | 3 | 0 | 3 |
| `dynamic_load_balancer.py` | 3 | 0 | 3 |
| `resilience.py` | 5 | 0 | 5 |
| `__init__.py` | 12 | 0 | 12 |
| 其他文件 | 353 | 0 | 353 |
| **总计** | **398** | **1** | **397** |

---

## 🔄 下一步行动

1. **立即行动** (P0)
   - 修复已知的全局实例None问题
   - 添加asyncio.Task类型参数
   - 修复dataclass冲突

2. **短期行动** (1周内)
   - 移除未使用导入
   - 添加缺失的类型注解
   - 修复上下文管理器问题

3. **长期行动** (持续)
   - 启用严格类型检查
   - 添加类型测试
   - 定期运行pyright

---

## 💡 建议

### 开发流程改进

1. **在CI/CD中集成pyright**
   ```yaml
   - name: Pyright type check
     run: pyright core/
   ```

2. **配置pyproject.toml**
   ```toml
   [tool.pyright]
   typeCheckingMode = "strict"
   reportMissingTypeStubs = false
   reportUnknownMemberType = "warning"
   ```

3. **使用类型存根**
   - 为没有类型的第三方库创建存根
   - 使用 `typeshed` 标准库存根

### 团队培训

1. **类型注解最佳实践**
   - 使用 `typing` 模块的标准类型
   - 避免使用 `Any`，使用具体类型
   - 为公共API提供完整类型

2. **工具使用**
   - 编辑器集成 (VSCode, PyCharm)
   - 实时类型检查
   - 自动导入管理

---

**报告生成时间**: 2026-01-25
**维护者**: Athena AI团队
