# 上下文插件系统使用指南

> **Phase 2.3 动态加载机制**
>
> 灵活的插件机制，支持动态加载和热插拔上下文处理器

---

## 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [内置插件](#内置插件)
4. [自定义插件](#自定义插件)
5. [配置管理](#配置管理)
6. [API参考](#api参考)
7. [最佳实践](#最佳实践)

---

## 快速开始

### 基本使用

```python
import asyncio
from core.context_management.plugins import PluginLoader
from core.context_management.base_context import BaseContext

async def main():
    # 创建加载器
    loader = PluginLoader()

    # 从配置文件加载插件
    await loader.load_from_yaml("config/context_plugins.yaml")

    # 获取插件
    compression = loader.registry.get("compression")

    # 执行插件
    context = BaseContext("test_ctx", "test_type")
    result = await compression.execute(context)

    print(f"压缩比例: {result['compression_ratio']}")

asyncio.run(main())
```

### 热加载

```python
# 配置文件更新后重新加载
await loader.hot_reload("config/context_plugins.yaml")
```

---

## 核心概念

### 插件生命周期

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ initialize  │ -> │   execute   │ -> │  shutdown   │
│  (初始化)   │    │   (执行)    │    │   (关闭)    │
└─────────────┘    └─────────────┘    └─────────────┘
```

### 组件关系

```
┌─────────────────────────────────────────────┐
│              PluginLoader                   │
│  (从配置文件加载插件)                        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│         ContextPluginRegistry               │
│  (管理插件注册、依赖检查)                    │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐
   │Compression│Validation│Metrics│
   │ Plugin  │ │ Plugin  │ │ Plugin │
   └────────┘ └────────┘ └────────┘
```

---

## 内置插件

### 1. CompressionPlugin（压缩插件）

压缩上下文内容，减少Token使用量。

**配置参数**:
| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| `ratio` | float | 0.5 | 压缩比例 (0.1-1.0) |
| `preserve_keywords` | list[str] | [] | 保留的关键词 |
| `min_length` | int | 100 | 最小保留长度 |

**使用示例**:
```python
from core.context_management.plugins import CompressionPlugin

plugin = CompressionPlugin()
await plugin.initialize({
    "ratio": 0.3,
    "preserve_keywords": ["IMPORTANT", "关键"]
})

result = await plugin.execute(context)
print(f"压缩率: {result['compression_ratio']:.1%}")
```

### 2. ValidationPlugin（验证插件）

验证上下文数据的完整性和安全性。

**配置参数**:
| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| `required_fields` | list[str] | [] | 必需字段列表 |
| `max_length` | int | 100000 | 字段最大长度 |
| `patterns` | dict | {} | 字段格式验证模式 |
| `check_injection` | bool | True | 是否检查注入攻击 |

**使用示例**:
```python
from core.context_management.plugins import ValidationPlugin

plugin = ValidationPlugin()
await plugin.initialize({
    "required_fields": ["context_id", "content"],
    "patterns": {
        "context_id": "^[a-zA-Z0-9_-]+$"
    }
})

result = await plugin.execute(context)
if not result["valid"]:
    print("验证失败:", result["errors"])
```

### 3. MetricsPlugin（指标插件）

收集和上报性能指标。

**配置参数**:
| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| `enabled_metrics` | list[str] | ["execution_time", ...] | 启用的指标类型 |
| `sample_rate` | float | 1.0 | 采样率 |
| `export_interval` | int | 60 | 导出间隔（秒） |

**使用示例**:
```python
from core.context_management.plugins import MetricsPlugin
import time

plugin = MetricsPlugin()
await plugin.initialize({})

# 计时
timing_id = await plugin.start_timing("operation")
# ... 执行操作 ...
elapsed = await plugin.end_timing(timing_id)

# 收集指标
await plugin.execute(
    context,
    operation="operation",
    start_time=start_time,
    token_count=1000,
    success=True
)

# 获取统计
stats = plugin.get_statistics()
print(stats)
```

---

## 自定义插件

### 插件模板

```python
from core.context_management.base_context import BaseContextPlugin
from core.context_management.interfaces import IContext
from typing import Any, Dict

class MyCustomPlugin(BaseContextPlugin):
    """自定义插件"""

    def __init__(self):
        super().__init__(
            plugin_name="my_custom",
            plugin_version="1.0.0",
            dependencies=[],  # 依赖的其他插件
        )
        self._config: Dict[str, Any] = {}

    async def initialize(self, config: Dict[str, Any]) -> None:
        """初始化插件"""
        await super().initialize(config)
        self._config = config
        # 初始化逻辑

    async def execute(self, context: IContext, **kwargs) -> Any:
        """执行插件逻辑"""
        # 处理上下文
        result = process_context(context)
        return result

    async def shutdown(self) -> None:
        """关闭插件"""
        await super().shutdown()
        # 清理资源
```

### 注册自定义插件

```python
from core.context_management.plugins import ContextPluginRegistry

registry = ContextPluginRegistry()
plugin = MyCustomPlugin()

await registry.register(plugin, config={"key": "value"})
```

---

## 配置管理

### YAML配置格式

```yaml
plugins:
  - name: my_plugin
    module_path: my_module.my_plugin
    class_name: MyCustomPlugin
    enabled: true
    priority: 100
    config:
      setting1: value1
      setting2: value2
```

### 配置参数说明

| 参数 | 必填 | 说明 |
|-----|------|------|
| `name` | 是 | 插件唯一标识符 |
| `module_path` | 是 | Python模块路径 |
| `class_name` | 否 | 插件类名（默认为名称+Plugin） |
| `enabled` | 否 | 是否启用（默认true） |
| `priority` | 否 | 加载优先级（越小越优先，默认100） |
| `config` | 否 | 插件配置参数 |

---

## API参考

### PluginLoader

```python
class PluginLoader:
    """插件加载器"""

    def __init__(self, registry: ContextPluginRegistry | None = None): ...

    async def load_from_yaml(
        self,
        config_path: str | Path,
        auto_start: bool = True
    ) -> list[str]: ...

    async def load_plugin(self, config: PluginConfig) -> bool: ...

    async def unload_plugin(self, plugin_name: str) -> bool: ...

    async def reload_plugin(self, plugin_name: str) -> bool: ...

    async def hot_reload(self, config_path: str | Path) -> list[str]: ...

    async def execute_plugin(
        self,
        plugin_name: str,
        context: Any,
        **kwargs
    ) -> Any: ...
```

### ContextPluginRegistry

```python
class ContextPluginRegistry:
    """插件注册表"""

    async def register(
        self,
        plugin: IContextPlugin,
        config: dict | None = None,
        auto_initialize: bool = True
    ) -> bool: ...

    async def load(self, plugin_name: str) -> IContextPlugin: ...

    async def unload(self, plugin_name: str) -> bool: ...

    async def reload(
        self,
        plugin_name: str,
        new_config: dict | None = None
    ) -> bool: ...

    def get(self, plugin_name: str) -> IContextPlugin | None: ...

    def is_active(self, plugin_name: str) -> bool: ...

    async def check_dependencies(
        self,
        plugin_name: str
    ) -> dict[str, bool]: ...
```

---

## 最佳实践

### 1. 插件设计原则

- **单一职责**: 每个插件只做一件事
- **无状态优先**: 尽量设计为无状态插件
- **幂等性**: 多次执行应产生相同结果
- **错误处理**: 优雅处理异常，不影响其他插件

### 2. 依赖管理

```python
# 声明依赖
class MyPlugin(BaseContextPlugin):
    def __init__(self):
        super().__init__(
            plugin_name="my_plugin",
            dependencies=["compression", "validation"]  # 依赖的插件
        )
```

### 3. 性能优化

```python
# 使用采样率减少开销
await plugin.initialize({
    "sample_rate": 0.1  # 只处理10%的请求
})
```

### 4. 热加载策略

```python
# 生产环境谨慎使用热加载
# 建议在低峰期进行，并做好回滚准备

try:
    await loader.hot_reload("config/context_plugins.yaml")
except Exception as e:
    logger.error(f"热加载失败: {e}")
    # 回滚到旧配置
    await loader.load_from_yaml("config/context_plugins_backup.yaml")
```

---

## 常见问题

### Q: 如何调试插件？

```python
import logging
logging.getLogger("core.context_management.plugins").setLevel(logging.DEBUG)
```

### Q: 插件执行顺序如何控制？

通过 `priority` 参数控制，数值越小越优先执行。

### Q: 如何处理插件间的通信？

```python
# 通过上下文元数据传递数据
context.metadata["plugin_a_result"] = result_a
# 插件B可以读取
result_b = await plugin_b.execute(context)
```

---

**维护者**: Athena平台团队
**最后更新**: 2026-04-24
