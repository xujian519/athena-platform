# 工具系统使用指南

> **版本**: v1.0.0
> **作者**: Athena平台团队
> **创建时间**: 2026-04-19
> **适用人群**: 开发者、系统集成工程师

---

## 目录

- [系统概述](#系统概述)
- [快速开始](#快速开始)
- [权限系统](#权限系统)
- [工具管理](#工具管理)
- [工具开发](#工具开发)
- [最佳实践](#最佳实践)
- [故障排查](#故障排查)
- [进阶话题](#进阶话题)

---

## 系统概述

Athena工具系统是一个增强版的工具管理框架，提供工具分组、权限控制、智能选择和性能监控功能。

### 核心组件

```
┌─────────────────────────────────────────────────────┐
│              工具系统架构                            │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐              │
│  │ 权限系统     │    │ 工具管理器   │              │
│  │ Permissions  │───▶│ ToolManager  │              │
│  └──────────────┘    └──────────────┘              │
│         │                    │                      │
│         ▼                    ▼                      │
│  ┌──────────────┐    ┌──────────────┐              │
│  │ 规则引擎     │    │ 工具注册中心 │              │
│  │ Rule Engine  │    │ Registry     │              │
│  └──────────────┘    └──────────────┘              │
│                              │                      │
│                              ▼                      │
│                    ┌──────────────┐                │
│                    │ 调用管理器   │                │
│                    │ CallManager  │                │
│                    └──────────────┘                │
└─────────────────────────────────────────────────────┘
```

### 主要特性

1. **权限控制**: 三种权限模式（DEFAULT/AUTO/BYPASS）+ 规则匹配
2. **工具分组**: 按领域和功能分组，支持动态激活
3. **智能选择**: 基于任务类型自动选择最佳工具
4. **性能监控**: 实时跟踪工具执行统计和成功率
5. **速率限制**: 防止工具调用过于频繁

---

## 快速开始

### 安装依赖

```bash
# 确保Python版本 >= 3.9
python3 --version

# 安装依赖
poetry install
```

### 基础使用

```python
import asyncio
from core.tools.tool_call_manager import get_tool_manager

async def main():
    # 获取工具管理器
    manager = get_tool_manager()

    # 调用工具
    result = await manager.call_tool(
        "patent_analyzer",
        parameters={
            "patent_id": "CN123456789A",
            "analysis_type": "creativity"
        }
    )

    print(f"状态: {result.status.value}")
    print(f"结果: {result.result}")

asyncio.run(main())
```

---

## 权限系统

### 权限模式

| 模式 | 说明 | 使用场景 |
|-----|------|---------|
| `DEFAULT` | 默认模式，未匹配规则时需要用户确认 | 生产环境，敏感操作 |
| `AUTO` | 自动模式，未匹配规则时自动拒绝 | 自动化任务，批处理 |
| `BYPASS` | 绕过模式，允许所有调用 | 测试环境，调试模式 |

### 创建权限上下文

```python
from core.tools.permissions import (
    ToolPermissionContext,
    PermissionMode,
    PermissionRule
)

# 创建权限上下文
ctx = ToolPermissionContext(mode=PermissionMode.AUTO)

# 添加允许规则
ctx.add_rule("allow", PermissionRule(
    rule_id="safe-read",
    pattern="*:read",
    description="允许所有读操作",
    priority=10
))

# 添加拒绝规则
ctx.add_rule("deny", PermissionRule(
    rule_id="dangerous-rm",
    pattern="bash:*rm*",
    description="拒绝包含rm的bash命令",
    priority=100
))

# 检查权限
decision = ctx.check_permission("file:read")
print(f"允许: {decision.allowed}, 原因: {decision.reason}")
```

### 通配符模式

```python
# 精确匹配
pattern = "file:read"  # 只匹配 file:read

# 前缀匹配
pattern = "file:*"  # 匹配 file:read, file:write, etc.

# 后缀匹配
pattern = "*:read"  # 匹配 file:read, db:read, etc.

# 包含匹配
pattern = "*analysis*"  # 匹配 code_analysis, semantic_analysis, etc.
```

### 预定义规则

```python
from core.tools.permissions import (
    DEFAULT_ALLOW_RULES,
    DEFAULT_DENY_RULES
)

# 使用预定义规则
ctx = ToolPermissionContext(
    mode=PermissionMode.DEFAULT,
    always_allow=DEFAULT_ALLOW_RULES,
    always_deny=DEFAULT_DENY_RULES
)
```

---

## 工具管理

### 工具分组

```python
from core.tools.tool_manager import ToolManager
from core.tools.tool_group import ToolGroupDef, GroupActivationRule

# 创建工具管理器
manager = ToolManager()

# 定义工具组
group_def = ToolGroupDef(
    name="patent",
    display_name="专利工具组",
    description="专利检索、分析和翻译工具",
    activation_rules=[
        GroupActivationRule(
            rule_type=GroupActivationRule.KEYWORD,
            keywords=["专利", "patent", "检索"],
            priority=10
        )
    ]
)

# 注册工具组
group = manager.register_group(group_def)

# 激活工具组
manager.activate_group("patent")
```

### 自动工具选择

```python
# 自动激活工具组
group_name = await manager.auto_activate_group_for_task(
    task_description="分析专利CN123456789A的创造性",
    task_type="patent_analysis",
    domain="patent"
)

print(f"激活的工具组: {group_name}")

# 选择最佳工具
result = await manager.select_best_tool(
    task_description="检索相关专利",
    task_type="patent_search"
)

print(f"推荐工具: {result.tool.name}")
print(f"置信度: {result.confidence:.2%}")
```

### 单组 vs 多组模式

```python
# 单组模式（默认）
manager.set_single_group_mode(True)
manager.activate_group("patent")  # 自动停用其他组

# 多组模式
manager.set_single_group_mode(False)
manager.activate_group("patent", deactivate_others=False)
manager.activate_group("legal", deactivate_others=False)
```

---

## 工具开发

### 创建简单工具

```python
from core.tools.base import ToolDefinition, ToolCategory, ToolPriority
from core.tools.tool_call_manager import get_tool_manager

# 1. 定义工具处理函数
def my_tool_handler(parameters: dict, context: dict | None = None) -> dict:
    """工具处理函数"""
    # 处理逻辑
    result = process(parameters)
    return result

# 2. 创建工具定义
tool = ToolDefinition(
    tool_id="my_tool",
    name="我的工具",
    description="工具描述",
    category=ToolCategory.DATA_PROCESSING,
    priority=ToolPriority.MEDIUM,
    required_params=["input"],
    optional_params=["option"],
    handler=my_tool_handler,
    timeout=30.0
)

# 3. 注册工具
manager = get_tool_manager()
manager.register_tool(tool)

# 4. 调用工具
result = await manager.call_tool("my_tool", parameters={"input": "data"})
```

### 创建异步工具

```python
import asyncio

async def async_tool_handler(parameters: dict, context: dict | None = None) -> dict:
    """异步工具处理函数"""
    # 异步操作
    await asyncio.sleep(1.0)
    return {"result": "success"}

tool = ToolDefinition(
    tool_id="async_tool",
    name="异步工具",
    description="异步操作工具",
    handler=async_tool_handler,
    timeout=30.0
)
```

### 错误处理

```python
def robust_tool_handler(parameters: dict, context: dict | None = None) -> dict:
    """带错误处理的工具"""
    try:
        # 参数验证
        if "required_param" not in parameters:
            return {"error": "缺少必需参数"}

        # 执行逻辑
        result = process(parameters)
        return {"success": True, "data": result}

    except Exception as e:
        # 错误处理
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }
```

### 工具配置

```python
tool = ToolDefinition(
    tool_id="configured_tool",
    name="可配置工具",
    description="支持配置的工具",

    # 基础配置
    category=ToolCategory.DATA_PROCESSING,
    priority=ToolPriority.HIGH,

    # 执行配置
    required_params=["input"],
    optional_params=["option1", "option2"],
    timeout=30.0,
    max_retries=3,

    # 性能配置
    enabled=True,

    # 自定义配置
    config={
        "custom_option": "value",
        "threshold": 0.8
    }
)
```

---

## 最佳实践

### 1. 权限配置

#### 生产环境

```python
# 保守策略
ctx = ToolPermissionContext(
    mode=PermissionMode.DEFAULT,  # 需要用户确认
    always_allow=DEFAULT_ALLOW_RULES,
    always_deny=DEFAULT_DENY_RULES
)

# 添加生产环境特定规则
ctx.add_rule("deny", PermissionRule(
    rule_id="no-production-write",
    pattern="production:*write",
    description="拒绝生产环境写操作",
    priority=200
))
```

#### 开发环境

```python
# 宽松策略
ctx = ToolPermissionContext(
    mode=PermissionMode.BYPASS  # 允许所有操作
)
```

### 2. 工具设计

#### 单一职责

```python
# 好的设计：一个工具只做一件事
class FileReadTool:
    """只负责读取文件"""

class FileWriteTool:
    """只负责写入文件"""

# 不好的设计：一个工具做多件事
class FileTool:
    """负责所有文件操作（不推荐）"""
```

#### 错误处理

```python
async def reliable_tool(parameters: dict, context: dict | None = None) -> dict:
    """可靠工具示例"""
    # 1. 参数验证
    if not validate_parameters(parameters):
        return {"error": "参数验证失败"}

    # 2. 超时控制
    try:
        result = await asyncio.wait_for(
            process_long_operation(parameters),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        return {"error": "操作超时"}

    # 3. 结果验证
    if not validate_result(result):
        return {"error": "结果验证失败"}

    return {"success": True, "data": result}
```

### 3. 性能优化

#### 并发调用

```python
# 串行调用（慢）
for url in urls:
    result = await manager.call_tool("fetch", {"url": url})

# 并发调用（快）
tasks = [manager.call_tool("fetch", {"url": url}) for url in urls]
results = await asyncio.gather(*tasks)
```

#### 缓存结果

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(input_data: str) -> dict:
    """带缓存的操作"""
    return process(input_data)

async def cached_tool(parameters: dict, context: dict | None = None) -> dict:
    """使用缓存的工具"""
    input_key = json.dumps(parameters, sort_keys=True)
    return expensive_operation(input_key)
```

### 4. 日志记录

```python
import logging

logger = logging.getLogger(__name__)

async def logged_tool(parameters: dict, context: dict | None = None) -> dict:
    """带日志的工具"""
    logger.info(f"工具调用开始: {parameters}")

    try:
        result = await process(parameters)
        logger.info(f"工具调用成功: {result}")
        return result
    except Exception as e:
        logger.error(f"工具调用失败: {e}", exc_info=True)
        return {"error": str(e)}
```

---

## 故障排查

### 常见问题

#### 1. 工具调用失败

**问题**: 工具调用返回失败状态

**排查步骤**:

```python
# 1. 检查工具是否注册
tool = manager.get_tool("tool_name")
if not tool:
    print("工具未注册")

# 2. 检查必需参数
missing = [p for p in tool.required_params if p not in parameters]
if missing:
    print(f"缺少参数: {missing}")

# 3. 检查权限
decision = ctx.check_permission("tool_name")
if not decision.allowed:
    print(f"权限被拒绝: {decision.reason}")

# 4. 检查超时
if result.status == CallStatus.TIMEOUT:
    print("工具调用超时，考虑增加timeout值")
```

#### 2. 性能问题

**问题**: 工具调用速度慢

**优化方案**:

```python
# 1. 使用异步工具
async def async_tool(parameters: dict, context: dict | None = None) -> dict:
    # 异步操作
    pass

# 2. 并发调用
results = await asyncio.gather(*[
    manager.call_tool("tool", params) for params in param_list
])

# 3. 调整超时
tool.timeout = 60.0  # 增加超时时间

# 4. 启用缓存
from functools import lru_cache
@lru_cache(maxsize=128)
def cached_operation(input_data):
    pass
```

#### 3. 权限问题

**问题**: 权限检查不符合预期

**调试方法**:

```python
# 1. 查看所有规则
rules = ctx.get_rules()
print("允许规则:", rules["allow"])
print("拒绝规则:", rules["deny"])

# 2. 测试模式匹配
test_patterns = ["file:*", "*read", "bash:*"]
for pattern in test_patterns:
    match = ctx._match_pattern("file:read", pattern)
    print(f"{pattern} -> {match}")

# 3. 检查优先级
for rule in rules["deny"]:
    print(f"{rule['id']}: priority={rule['priority']}")
```

---

## 进阶话题

### 1. 自定义权限规则

```python
class AdvancedPermissionRule(PermissionRule):
    """高级权限规则"""

    def __init__(self, rule_id: str, pattern: str, condition_fn: callable):
        super().__init__(rule_id, pattern, "高级规则")
        self.condition_fn = condition_fn

    def matches(self, tool_name: str, parameters: dict) -> bool:
        """自定义匹配逻辑"""
        if not self._match_pattern(tool_name, self.pattern):
            return False
        return self.condition_fn(tool_name, parameters)

# 使用示例
def time_based_condition(tool_name: str, parameters: dict) -> bool:
    """基于时间的条件"""
    current_hour = datetime.now().hour
    return 9 <= current_hour <= 17  # 只在工作时间允许

rule = AdvancedPermissionRule(
    rule_id="business-hours-only",
    pattern="sensitive:*",
    condition_fn=time_based_condition
)
```

### 2. 工具链编排

```python
async def tool_chain(parameters: dict, context: dict | None = None) -> dict:
    """工具链示例"""
    # 第一步：数据获取
    data_result = await manager.call_tool(
        "data_fetcher",
        {"url": parameters["url"]}
    )

    if not data_result.result:
        return {"error": "数据获取失败"}

    # 第二步：数据分析
    analysis_result = await manager.call_tool(
        "data_analyzer",
        {"data": data_result.result}
    )

    # 第三步：结果格式化
    format_result = await manager.call_tool(
        "result_formatter",
        {"analysis": analysis_result.result}
    )

    return format_result.result
```

### 3. 动态工具注册

```python
class DynamicToolRegistry:
    """动态工具注册器"""

    async def register_tools_from_config(self, config_path: str):
        """从配置文件动态注册工具"""
        config = load_config(config_path)

        for tool_config in config["tools"]:
            tool = self.create_tool_from_config(tool_config)
            manager.register_tool(tool)

    def create_tool_from_config(self, config: dict) -> ToolDefinition:
        """从配置创建工具"""
        return ToolDefinition(
            tool_id=config["id"],
            name=config["name"],
            description=config["description"],
            category=ToolCategory[config["category"]],
            handler=self.load_handler(config["handler"]),
            # ... 其他配置
        )

    def load_handler(self, handler_path: str):
        """动态加载处理函数"""
        module_path, func_name = handler_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, func_name)
```

### 4. 监控和告警

```python
class ToolMonitor:
    """工具监控器"""

    def __init__(self, manager: ToolCallManager):
        self.manager = manager
        self.alert_thresholds = {
            "error_rate": 0.1,  # 10%错误率
            "avg_time": 5.0,    # 5秒平均时间
        }

    async def monitor_loop(self):
        """监控循环"""
        while True:
            stats = self.manager.get_stats()

            # 检查错误率
            if stats["error_rate"] > self.alert_thresholds["error_rate"]:
                await self.send_alert(
                    f"错误率过高: {stats['error_rate']:.2%}"
                )

            # 检查平均时间
            if stats["avg_execution_time"] > self.alert_thresholds["avg_time"]:
                await self.send_alert(
                    f"平均执行时间过长: {stats['avg_execution_time']:.2f}秒"
                )

            await asyncio.sleep(60)  # 每分钟检查一次

    async def send_alert(self, message: str):
        """发送告警"""
        logger.warning(f"工具监控告警: {message}")
        # 发送到监控系统
```

---

## 相关文档

- [权限系统 API](../api/PERMISSION_SYSTEM_API.md)
- [工具管理器 API](../api/TOOL_MANAGER_API.md)
- [工具调用管理器 API](../api/TOOL_CALL_MANAGER_API.md)
- [权限系统示例](../../examples/tools/permission_examples.py)
- [自定义工具示例](../../examples/tools/custom_tool_example.py)

---

**最后更新**: 2026-04-19
**维护者**: Athena平台团队
