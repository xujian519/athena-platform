# Hook系统增强 API文档

**版本**: 2.0.0
**作者**: Athena平台团队
**最后更新**: 2026-04-20

---

## 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [生命周期管理](#生命周期管理)
4. [Hook链和中间件](#hook链和中间件)
5. [性能监控](#性能监控)
6. [调试工具](#调试工具)
7. [Skills系统集成](#skills系统集成)
8. [Plugins系统集成](#plugins系统集成)
9. [迁移指南](#迁移指南)
10. [最佳实践](#最佳实践)

---

## 快速开始

### 安装

Hook系统增强是Athena平台的核心组件，无需额外安装。

### 基本使用

```python
from core.hooks.enhanced import HookLifecycleManager
from core.hooks.base import HookFunction, HookType

# 创建生命周期管理器
lifecycle = HookLifecycleManager()

# 定义Hook函数
async def my_hook(context):
    print(f"Hook triggered: {context.hook_type}")
    return "result"

# 注册Hook
hook = HookFunction(
    name="my_hook",
    hook_type=HookType.POST_TASK_COMPLETE,
    func=my_hook,
    priority=10,
)

await lifecycle.register(hook)
```

---

## 核心概念

### Hook类型

```python
from core.hooks.base import HookType

# 任务生命周期
HookType.PRE_TASK_START      # 任务开始前
HookType.POST_TASK_COMPLETE  # 任务完成后

# 工具调用
HookType.PRE_TOOL_USE        # 工具使用前
HookType.POST_TOOL_USE       # 工具使用后

# 错误处理
HookType.ON_ERROR            # 发生错误时

# 其他
HookType.ON_CHECKPOINT        # 检查点
HookType.ON_STATE_CHANGE      # 状态变化
```

### Hook上下文

```python
from core.hooks.base import HookContext

context = HookContext(
    hook_type=HookType.POST_TASK_COMPLETE,
    data={"key": "value"},
)

# 设置和获取数据
context.set("result", 42)
value = context.get("result")  # 42
```

### Hook结果

```python
from core.hooks.enhanced import HookResult, HookStatus

result = HookResult(
    success=True,
    data="result data",
    execution_time=0.123,
    status=HookStatus.COMPLETED,
)

# 转换为字典
data = result.to_dict()
```

---

## 生命周期管理

### HookLifecycleManager

管理Hook的完整生命周期：注册、激活、停用、卸载。

#### 初始化

```python
from core.hooks.enhanced import HookLifecycleManager
from core.hooks.base import HookRegistry

# 使用默认注册表
lifecycle = HookLifecycleManager()

# 或使用自定义注册表
registry = HookRegistry()
lifecycle = HookLifecycleManager(registry)
```

#### 注册Hook

```python
from core.hooks.base import HookFunction, HookType

async def my_hook(context):
    return "result"

hook = HookFunction(
    name="my_hook",
    hook_type=HookType.POST_TASK_COMPLETE,
    func=my_hook,
)

# 注册并自动激活
await lifecycle.register(hook)

# 注册但不自动激活
await lifecycle.register(hook, auto_activate=False)

# 注册带依赖的Hook
await lifecycle.register(
    hook,
    dependencies=["other_hook"],
    auto_activate=True,
)
```

#### 激活/停用Hook

```python
# 激活Hook
await lifecycle.activate("my_hook")

# 停用Hook
await lifecycle.deactivate("my_hook")
```

#### 卸载Hook

```python
# 卸载Hook（会自动停用）
await lifecycle.unregister("my_hook")
```

#### 查询状态

```python
from core.hooks.enhanced import HookState

# 获取单个Hook状态
state = lifecycle.get_state("my_hook")
print(state)  # HookState.ACTIVE

# 获取所有Hook状态
states = lifecycle.get_all_states()

# 解析依赖顺序
order = await lifecycle.resolve_dependencies()
print(order)  # ['hook1', 'hook2', 'hook3']
```

---

## Hook链和中间件

### HookChain

管理一组Hook的链式执行。

#### 创建Hook链

```python
from core.hooks.enhanced import HookChain
from core.hooks.base import HookType

chain = HookChain(
    hook_type=HookType.POST_TASK_COMPLETE,
    stop_on_error=False,  # 遇到错误时是否停止
    stop_on_failure=False,  # 遇到失败时是否停止
)
```

#### 添加Hook

```python
from core.hooks.base import HookFunction

async def hook1(ctx):
    return "hook1"

async def hook2(ctx):
    return "hook2"

chain.add_hook(
    HookFunction("hook1", HookType.POST_TASK_COMPLETE, hook1, priority=1)
)
chain.add_hook(
    HookFunction("hook2", HookType.POST_TASK_COMPLETE, hook2, priority=2)
)
```

#### 执行链

```python
from core.hooks.base import HookContext

context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
result = await chain.execute(context)

print(result.success)  # True
print(result.data)  # ['hook2', 'hook1'] (按优先级排序)
```

### HookMiddleware

中间件可以在Hook执行前后添加自定义逻辑。

#### 定义中间件

```python
from core.hooks.enhanced import HookMiddleware
from core.hooks.base import HookContext
from core.hooks.enhanced import HookResult

class LoggingMiddleware(HookMiddleware):
    """日志中间件"""

    async def before_hook(self, context: HookContext) -> HookContext:
        print(f"Before hook: {context.hook_type}")
        return context

    async def after_hook(
        self, context: HookContext, result: HookResult
    ) -> HookResult:
        print(f"After hook: {result.execution_time:.3f}s")
        return result
```

#### 使用中间件

```python
chain = HookChain(hook_type=HookType.POST_TASK_COMPLETE)
chain.add_middleware(LoggingMiddleware())
```

### HookChainProcessor

管理所有Hook链的创建和执行。

#### 创建处理器

```python
from core.hooks.enhanced import HookChainProcessor

processor = HookChainProcessor()
```

#### 添加全局中间件

```python
processor.add_middleware(LoggingMiddleware())
```

#### 处理Hook

```python
from core.hooks.base import HookContext

context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)

# 串行处理
result = await processor.process(HookType.POST_TASK_COMPLETE, context)

# 并行处理
result = await processor.process(
    HookType.POST_TASK_COMPLETE,
    context,
    parallel=True,
)
```

---

## 性能监控

### HookPerformanceMonitor

跟踪Hook的执行时间和性能指标。

#### 初始化

```python
from core.hooks.enhanced import HookPerformanceMonitor

monitor = HookPerformanceMonitor()
```

#### 跟踪执行

```python
# 开始跟踪
await monitor.start_tracking("my_hook")

# 执行Hook
result = await my_hook(context)

# 结束跟踪
metrics = await monitor.end_tracking("my_hook", success=True)

print(metrics.call_count)  # 1
print(metrics.avg_time)  # 0.123
print(metrics.success_rate)  # 1.0
```

#### 获取报告

```python
report = await monitor.get_report()

print(report.total_hooks)  # 5
print(report.total_calls)  # 100
print(report.avg_time_per_call)  # 0.05
print(report.throughput)  # 20.0 (calls/s)
```

#### 基准测试

```python
async def my_hook():
    await asyncio.sleep(0.001)

result = await monitor.benchmark(
    "my_hook",
    my_hook,
    iterations=1000,
    warmup=100,
)

print(result.avg_time)  # 平均执行时间
print(result.p95_time)  # P95延迟
print(result.throughput)  # 吞吐量
```

---

## 调试工具

### HookDebugger

提供断点、追踪和可视化等调试功能。

#### 初始化

```python
from core.hooks.enhanced import HookDebugger

debugger = HookDebugger()
```

#### 启用调试

```python
debugger.enable_debugging()
```

#### 设置断点

```python
debugger.set_breakpoint("my_hook")
```

#### 追踪执行

```python
from core.hooks.base import HookContext

context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)

await debugger.trace_execution(
    hook_id="my_hook",
    hook_type="post_task_complete",
    context=context,
    execution_time=0.123,
    success=True,
)
```

#### 获取追踪日志

```python
log = await debugger.get_trace_log()

for entry in log:
    print(f"{entry.hook_id}: {entry.execution_time:.3f}s")
```

#### 可视化执行

```python
mermaid = debugger.visualize_execution()
print(mermaid)
# 输出Mermaid图表代码
```

#### 获取统计信息

```python
stats = debugger.get_statistics()

print(stats["total_calls"])  # 100
print(stats["success_rate"])  # 0.95
```

---

## Skills系统集成

### SkillHookIntegration

为Skills系统提供Hook支持。

#### 创建集成

```python
from core.hooks.integrations import create_skill_hook_integration

integration = create_skill_hook_integration(
    enable_lifecycle=True,
)
```

#### 技能执行前后Hook

```python
from core.skills.base import Skill

skill = MySkill()

# 执行前
await integration.before_skill_execute(skill, {"param": "value"})

# 执行技能
result = await skill.execute(param="value")

# 执行后
await integration.after_skill_execute(skill, result, 0.123)
```

### SkillExecutorWithHooks

自动包装技能执行，触发Hook。

```python
from core.hooks.integrations import wrap_skill_with_hooks

executor = wrap_skill_with_hooks(skill, integration)

# 执行时会自动触发Hook
result = await executor.execute(param="value")
```

---

## Plugins系统集成

### PluginHookIntegration

为Plugins系统提供Hook支持。

#### 创建集成

```python
from core.hooks.integrations import create_plugin_hook_integration

integration = create_plugin_hook_integration(
    enable_lifecycle=True,
)
```

#### 插件加载前后Hook

```python
# 加载前
await integration.before_plugin_load("/path/to/plugin.yaml")

# 加载插件
plugin = loader.load_from_file("/path/to/plugin.yaml")

# 加载后
await integration.after_plugin_load(plugin, success=True)
```

### PluginLoaderWithHooks

自动包装插件加载器，触发Hook。

```python
from core.hooks.integrations import wrap_plugin_loader_with_hooks

wrapped_loader = wrap_plugin_loader_with_hooks(loader, integration)

# 加载时会自动触发Hook
plugin = await wrapped_loader.load_from_file("/path/to/plugin.yaml")
```

---

## 迁移指南

### 从旧Hook API迁移到新API

旧API仍然完全兼容，可以逐步迁移。

#### 基本Hook注册

**旧API**:
```python
from core.hooks import HookRegistry, HookType

registry = HookRegistry()

@registry.register_function(
    name="my_hook",
    hook_type=HookType.POST_TASK_COMPLETE,
    priority=10,
)
async def my_hook(context):
    return "result"
```

**新API**:
```python
from core.hooks.enhanced import HookLifecycleManager
from core.hooks.base import HookFunction, HookType

lifecycle = HookLifecycleManager()

hook = HookFunction(
    name="my_hook",
    hook_type=HookType.POST_TASK_COMPLETE,
    func=my_hook,
    priority=10,
)

await lifecycle.register(hook)
```

#### 添加生命周期管理

```python
# 旧代码
registry.register_function("my_hook", hook_type, func)

# 新代码 - 添加生命周期控制
await lifecycle.register(hook, auto_activate=False)
await lifecycle.activate("my_hook")
await lifecycle.deactivate("my_hook")
await lifecycle.unregister("my_hook")
```

#### 添加性能监控

```python
# 旧代码 - 无性能监控
await registry.trigger(hook_type, context)

# 新代码 - 带性能监控
await monitor.start_tracking("my_hook")
await registry.trigger(hook_type, context)
await monitor.end_tracking("my_hook")
```

### 混合使用

新旧API可以混合使用：

```python
from core.hooks import HookRegistry
from core.hooks.enhanced import HookLifecycleManager

# 使用旧API的现有代码
old_registry = HookRegistry()
old_registry.register_function("old_hook", hook_type, func)

# 使用新API的新代码
lifecycle = HookLifecycleManager(old_registry)  # 共享注册表
await lifecycle.register(new_hook)
```

---

## 最佳实践

### 1. Hook命名

使用描述性的名称，按前缀组织：

```python
# 好的命名
"skill.patent_analysis.validate"
"plugin.citiation.load"
"system.metrics.collect"

# 避免模糊命名
"hook1"
"my_hook"
"process"
```

### 2. 优先级设置

```python
# 系统级Hook：高优先级 (100-999)
priority=100

# 业务级Hook：中优先级 (10-99)
priority=50

# 日志级Hook：低优先级 (1-9)
priority=5
```

### 3. 错误处理

```python
async def robust_hook(context):
    try:
        # Hook逻辑
        return result
    except Exception as e:
        # 记录错误但不抛出
        logger.error(f"Hook failed: {e}")
        return None  # 返回默认值
```

### 4. 性能考虑

```python
# 快速Hook（<1ms）
async def fast_hook(context):
    return context.get("cached_value")

# 慢速Hook（考虑异步）
async def slow_hook(context):
    # 使用异步I/O
    result = await async_operation()
    return result
```

### 5. 中间件使用

```python
# 使用中间件避免重复代码
class TimingMiddleware(HookMiddleware):
    async def before_hook(self, context):
        context.set("_start", time.time())
        return context

    async def after_hook(self, context, result):
        start = context.get("_start")
        result.execution_time = time.time() - start
        return result
```

---

## 附录

### API参考

完整的API参考请查看源代码文档字符串。

### 示例代码

更多示例代码位于：
- `tests/hooks/` - 测试用例
- `examples/hooks/` - 使用示例

### 支持

如有问题，请联系Athena平台团队。

---

**文档版本**: 2.0.0
**最后更新**: 2026-04-20
