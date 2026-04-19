# Athena工具系统性能优化 - 使用指南

**版本**: v1.0.0
**更新日期**: 2026-04-19
**作者**: Agent-Gamma (性能专家)

---

## 🚀 快速开始

### 1. 功能门控系统

#### 启用/禁用功能

**方式1: 环境变量** (推荐)
```bash
# 启用并行工具执行
export ATHENA_FLAG_PARALLEL_TOOL_EXECUTION=TRUE

# 禁用详细日志
export ATHENA_FLAG_VERBOSE_LOGGING=FALSE

# 启用实验性功能
export ATHENA_FLAG_EXPERIMENTAL_FEATURES=TRUE
```

**方式2: 运行时切换**
```python
from core.tools.feature_gates import get_feature_gates, FeatureState

gates = get_feature_gates()

# 启用功能
gates.set_state("verbose_logging", FeatureState.ENABLED)

# 禁用功能
gates.set_state("experimental_features", FeatureState.DISABLED)
```

#### 使用示例
```python
from core.tools.feature_gates import feature

# 检查功能是否启用
if feature("parallel_tool_execution"):
    # 执行并行逻辑
    results = await manager.call_tools_parallel(tool_calls)
else:
    # 回退到串行逻辑
    results = await manager._call_tools_serial(tool_calls, context)
```

#### 查看功能状态
```python
from core.tools.feature_gates import get_feature_gates

gates = get_feature_gates()

# 获取统计信息
stats = gates.get_statistics()
print(f"总功能数: {stats['total_features']}")
print(f"已启用: {stats['enabled_count']}")
print(f"已禁用: {stats['disabled_count']}")
print(f"测试中: {stats['testing_count']}")

# 列出所有功能
features = gates.list_features()
for f in features:
    print(f"{f['name']}: {f['state']}")
```

---

### 2. 统一异步接口

#### 创建异步工具

**方式1: 继承BaseTool**
```python
from core.tools.async_interface import BaseTool, ToolContext

class MyAsyncTool(BaseTool):
    def __init__(self):
        super().__init__("my_tool", "我的异步工具")

    async def call(self, parameters: dict, context: ToolContext | None = None) -> dict:
        # 异步处理逻辑
        result = await some_async_operation(parameters)
        return {"result": result}

# 使用
tool = MyAsyncTool()
result = await tool.call({"arg1": "value1"})
```

**方式2: 装饰器 (推荐)**
```python
from core.tools.async_interface import to_async_tool

@to_async_tool("my_tool", "我的工具")
async def my_handler(params: dict) -> dict:
    # 异步处理
    result = await some_async_operation(params)
    return {"result": result}

# 使用
result = await my_handler.call({"arg1": "value1"})
```

**方式3: 同步函数自动包装**
```python
@to_async_tool("sync_tool", "同步工具")
def sync_handler(params: dict) -> dict:
    # 同步处理
    result = do_sync_operation(params)
    return {"result": result}

# 自动在线程池中执行
result = await sync_tool.call({"arg1": "value1"})
```

#### 使用ToolExecutor
```python
from core.tools.async_interface import ToolExecutor

executor = ToolExecutor(
    max_retries=3,
    retry_delay=1.0,
    timeout=30.0,
)

# 自动重试和超时控制
result = await executor.execute(tool, parameters, context)
```

---

### 3. 工具发现缓存 (自动启用)

缓存是透明的，无需修改代码。`find_by_category()` 和 `find_by_domain()` 自动使用LRU缓存。

#### 查看缓存统计
```python
from core.tools.base import get_global_registry

registry = get_global_registry()

# 获取统计信息（包含缓存性能）
stats = registry.get_statistics()

cache_stats = stats["cache_performance"]
print(f"分类查找缓存命中率: {cache_stats['find_by_category']['hit_rate']:.2%}")
print(f"领域查找缓存命中率: {cache_stats['find_by_domain']['hit_rate']:.2%}")
```

#### 手动清除缓存
```python
registry.clear_cache()
```

---

### 4. 并行工具执行

#### 基础用法 (无依赖)
```python
from core.tools.tool_call_manager import get_tool_manager

manager = get_tool_manager()

# 准备工具调用
tool_calls = [
    {"tool_name": "tool1", "parameters": {"arg1": "value1"}},
    {"tool_name": "tool2", "parameters": {"arg2": "value2"}},
    {"tool_name": "tool3", "parameters": {"arg3": "value3"}},
]

# 并行执行
results = await manager.call_tools_parallel(
    tool_calls=tool_calls,
    max_concurrency=10,
)
```

#### 高级用法 (带依赖)
```python
# tool2依赖tool1, tool3依赖tool2
tool_calls = [
    {"tool_name": "tool1", "parameters": {}},
    {"tool_name": "tool2", "parameters": {}, "depends_on": ["tool1"]},
    {"tool_name": "tool3", "parameters": {}, "depends_on": ["tool2"]},
]

# 自动分析依赖，按批次执行
results = await manager.call_tools_parallel(tool_calls)
```

#### 检查功能状态
```python
from core.tools.feature_gates import feature

if feature("parallel_tool_execution"):
    # 使用并行执行
    results = await manager.call_tools_parallel(tool_calls)
else:
    # 回退到串行执行
    results = [await manager.call_tool(**call) for call in tool_calls]
```

---

## 📊 性能监控

### 关键指标

1. **缓存命中率**
   - 目标: >90%
   - 查看: `registry.get_statistics()["cache_performance"]`

2. **并行加速比**
   - 目标: >3x
   - 计算: `串行耗时 / 并行耗时`

3. **工具调用延迟**
   - 目标: P95 <100ms
   - 查看: `manager.get_stats()`

### Grafana集成

建议将以下指标接入Grafana:
```python
from prometheus_client import Counter, Histogram

# 缓存命中率
cache_hits = Counter('tool_cache_hits_total', 'Total cache hits')
cache_misses = Counter('tool_cache_misses_total', 'Total cache misses')

# 并行执行
parallel_executions = Counter('tool_parallel_executions_total', 'Total parallel executions')
parallel_speedup = Histogram('tool_parallel_speedup', 'Parallel execution speedup')

# 工具调用
tool_calls = Histogram('tool_call_duration_seconds', 'Tool call duration', ['tool_name'])
```

---

## 🧪 测试

### 运行单元测试
```bash
# 功能门控测试
pytest tests/tools/test_feature_gates.py -v

# 异步接口测试
pytest tests/tools/test_async_interface.py -v

# 性能优化测试
pytest tests/tools/test_performance_optimization.py -v
```

### 性能基准测试
```bash
# 运行性能测试并查看输出
pytest tests/tools/test_performance_optimization.py -v -s
```

---

## 🔧 配置调优

### 缓存大小调整

如果工具数量很大，可以调整LRU缓存大小:
```python
import functools

@functools.lru_cache(maxsize=512)  # 增加到512
def find_by_category(self, category, enabled_only=True):
    # ...
```

### 并发数调整

根据系统资源调整最大并发数:
```python
results = await manager.call_tools_parallel(
    tool_calls=tool_calls,
    max_concurrency=20,  # 增加到20
)
```

### 功能开关配置

在生产环境建议使用环境变量配置:
```bash
# /etc/athena/flags.conf
export ATHENA_FLAG_PARALLEL_TOOL_EXECUTION=TRUE
export ATHENA_FLAG_TOOL_CACHE=TRUE
export ATHENA_FLAG_RATE_LIMIT=TRUE
export ATHENA_FLAG_PERFORMANCE_MONITORING=TRUE
export ATHENA_FLAG_PERMISSION_SYSTEM=FALSE
export ATHENA_FLAG_HOOK_SYSTEM=FALSE
export ATHENA_FLAG_VERBOSE_LOGGING=FALSE
```

---

## 🐛 故障排查

### 问题1: 功能开关未生效
**症状**: 设置环境变量后功能未启用
**解决**:
```python
# 检查环境变量
import os
print(os.getenv("ATHENA_FLAG_PARALLEL_TOOL_EXECUTION"))

# 检查功能状态
from core.tools.feature_gates import get_feature_gates
gates = get_feature_gates()
print(gates.get_state("parallel_tool_execution"))
```

### 问题2: 缓存命中率低
**症状**: 缓存命中率 <80%
**原因**: 工具频繁注册/更新
**解决**:
- 减少工具注册频率
- 批量注册工具后统一清除缓存
- 增加缓存大小

### 问题3: 并行执行未加速
**症状**: 并行执行时间与串行相同
**原因**: 工具之间有依赖关系
**解决**:
- 检查 `depends_on` 配置
- 分析依赖图是否合理
- 考虑减少依赖关系

---

## 📚 相关文档

- **详细报告**: `docs/reports/TOOL_SYSTEM_PERFORMANCE_OPTIMIZATION_REPORT_20260419.md`
- **完成总结**: `docs/reports/AGENT_GAMMA_COMPLETION_SUMMARY_20260419.md`
- **API文档**: `docs/api/tool_system_api.md` (待创建)

---

## 💡 最佳实践

### 1. 功能门控
- ✅ 使用环境变量控制生产环境功能
- ✅ 新功能先设为TESTING，验证后设为ENABLED
- ✅ 实验性功能默认DISABLED
- ❌ 避免在代码中硬编码功能状态

### 2. 异步接口
- ✅ 新工具优先使用 `async def`
- ✅ 使用装饰器简化工具注册
- ✅ 同步工具使用 `SyncToolWrapper` 包装
- ❌ 避免混用同步/异步调用

### 3. 缓存使用
- ✅ 缓存透明，无需修改代码
- ✅ 定期监控缓存命中率
- ✅ 工具批量注册后清除缓存
- ❌ 避免频繁注册单个工具

### 4. 并行执行
- ✅ 无依赖工具尽量并行
- ✅ 合理设置 `max_concurrency`
- ✅ 使用 `depends_on` 定义依赖
- ❌ 避免循环依赖

---

**版本历史**:
- v1.0.0 (2026-04-19) - 初始版本，包含P1和P2优化

**维护者**: Agent-Gamma (性能专家)
