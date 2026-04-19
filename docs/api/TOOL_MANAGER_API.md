# 工具管理器 API 文档

> **版本**: v1.0.0
> **作者**: Athena平台团队
> **创建时间**: 2026-04-19
> **模块**: `core/tools/tool_manager.py`

---

## 目录

- [概述](#概述)
- [核心类](#核心类)
  - [ToolGroupDef](#toolgroupdef)
  - [GroupActivationRule](#groupactivationrule)
  - [ToolSelectionResult](#toolselectionresult)
  - [ToolManager](#toolmanager)
- [使用示例](#使用示例)
- [最佳实践](#最佳实践)

---

## 概述

工具管理器提供工具分组管理、动态激活和智能选择功能。

### 核心特性

1. **工具分组管理**
   - 按领域和功能分组
   - 支持动态激活/停用
   - 单组/多组激活模式

2. **智能工具选择**
   - 基于任务类型自动激活工具组
   - 匹配度评分机制
   - 最佳工具推荐

3. **性能监控**
   - 工具调用统计
   - 成功率跟踪
   - 执行时间分析

---

## 核心类

### ToolGroupDef

**工具组定义数据类**

定义工具组的元数据和激活规则。

#### 参数说明

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `name` | `str` | ✅ | 工具组唯一标识 |
| `display_name` | `str` | ✅ | 工具组显示名称 |
| `description` | `str` | ✅ | 工具组描述 |
| `category` | `str` | ❌ | 工具组分类 |
| `activation_rules` | `list[GroupActivationRule]` | ❌ | 激活规则列表 |
| `tool_ids` | `list[str]` | ❌ | 包含的工具ID列表 |

#### 使用示例

```python
from core.tools.tool_group import ToolGroupDef, GroupActivationRule

group_def = ToolGroupDef(
    name="patent",
    display_name="专利工具组",
    description="专利检索、分析和翻译工具",
    category="patent",
    activation_rules=[
        GroupActivationRule(
            rule_type=GroupActivationRule.KEYWORD,
            keywords=["专利", "patent", "检索", "分析"],
            priority=10
        )
    ],
    tool_ids=["patent_search", "patent_analyzer", "patent_translator"]
)
```

---

### GroupActivationRule

**工具组激活规则**

定义工具组应该被激活的条件。

#### 规则类型

| 类型 | 说明 | 使用场景 |
|-----|------|---------|
| `KEYWORD` | 关键词匹配 | 基于任务描述中的关键词 |
| `TASK_TYPE` | 任务类型匹配 | 基于明确的任务类型 |
| `DOMAIN` | 领域匹配 | 基于业务领域 |

#### 参数说明

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `rule_type` | `str` | ✅ | 规则类型（`KEYWORD`/`TASK_TYPE`/`DOMAIN`） |
| `keywords` | `list[str]` | ❌ | 关键词列表（KEYWORD类型必需） |
| `task_types` | `list[str]` | ❌ | 任务类型列表（TASK_TYPE类型必需） |
| `domains` | `list[str]` | ❌ | 领域列表（DOMAIN类型必需） |
| `priority` | `int` | ❌ | 优先级（默认: `10`） |

#### 使用示例

```python
from core.tools.tool_group import GroupActivationRule

# 关键词规则
keyword_rule = GroupActivationRule(
    rule_type=GroupActivationRule.KEYWORD,
    keywords=["专利", "patent", "检索"],
    priority=10
)

# 任务类型规则
task_type_rule = GroupActivationRule(
    rule_type=GroupActivationRule.TASK_TYPE,
    task_types=["patent_search", "patent_analysis"],
    priority=20
)

# 领域规则
domain_rule = GroupActivationRule(
    rule_type=GroupActivationRule.DOMAIN,
    domains=["patent", "legal"],
    priority=15
)
```

---

### ToolSelectionResult

**工具选择结果**

记录工具选择的结果和置信度。

#### 属性说明

| 属性 | 类型 | 说明 |
|-----|------|------|
| `tool` | `ToolDefinition` | 选中的工具定义 |
| `group_name` | `str` | 工具所属的组名称 |
| `confidence` | `float` | 选择置信度（0-1） |
| `reason` | `str` | 选择原因 |

#### 使用示例

```python
result = await manager.select_best_tool("检索相关专利")

print(f"选中工具: {result.tool.name}")
print(f"所属组: {result.group_name}")
print(f"置信度: {result.confidence:.2%}")
print(f"原因: {result.reason}")
```

---

### ToolManager

**增强版工具管理器**

提供工具分组管理、动态激活和智能选择功能。

#### 构造函数

```python
def __init__(self, registry: ToolRegistry | None = None)
```

**参数说明**：

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `registry` | `ToolRegistry` | ❌ | 工具注册中心（默认使用全局注册中心） |

#### 主要方法

##### register_group()

注册工具组。

```python
def register_group(self, definition: ToolGroupDef) -> ToolGroup
```

**参数说明**：

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `definition` | `ToolGroupDef` | ✅ | 工具组定义 |

**返回值**：`ToolGroup` - 工具组实例

**使用示例**：

```python
from core.tools.tool_manager import ToolManager
from core.tools.tool_group import ToolGroupDef

manager = ToolManager()

group_def = ToolGroupDef(
    name="patent",
    display_name="专利工具组",
    description="专利相关工具"
)

group = manager.register_group(group_def)
```

---

##### activate_group()

激活工具组。

```python
def activate_group(
    self,
    group_name: str,
    deactivate_others: bool | None = None
) -> bool
```

**参数说明**：

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `group_name` | `str` | ✅ | 工具组名称 |
| `deactivate_others` | `bool` | ❌ | 是否停用其他组（默认使用单组模式设置） |

**返回值**：`bool` - 是否成功激活

**使用示例**：

```python
# 激活工具组（单组模式）
success = manager.activate_group("patent")

# 激活工具组（多组模式）
success = manager.activate_group("patent", deactivate_others=False)
```

---

##### deactivate_group()

停用工具组。

```python
def deactivate_group(self, group_name: str) -> bool
```

**参数说明**：

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `group_name` | `str` | ✅ | 工具组名称 |

**返回值**：`bool` - 是否成功停用

**使用示例**：

```python
success = manager.deactivate_group("patent")
```

---

##### auto_activate_group_for_task()

为任务自动激活最合适的工具组。

```python
async def auto_activate_group_for_task(
    self,
    task_description: str,
    task_type: str | None = None,
    domain: str | None = None
) -> str | None
```

**参数说明**：

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `task_description` | `str` | ✅ | 任务描述 |
| `task_type` | `str` | ❌ | 任务类型 |
| `domain` | `str` | ❌ | 领域 |

**返回值**：`str | None` - 激活的工具组名称，如果没有合适的返回`None`

**使用示例**：

```python
# 自动选择工具组
group_name = await manager.auto_activate_group_for_task(
    task_description="分析专利CN123456789A的创造性",
    task_type="patent_analysis",
    domain="patent"
)

print(f"激活的工具组: {group_name}")
```

---

##### select_best_tool()

为任务选择最佳工具。

```python
async def select_best_tool(
    self,
    task_description: str,
    task_type: str | None = None,
    domain: str | None = None
) -> ToolSelectionResult
```

**参数说明**：

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `task_description` | `str` | ✅ | 任务描述 |
| `task_type` | `str` | ❌ | 任务类型 |
| `domain` | `str` | ❌ | 领域 |

**返回值**：`ToolSelectionResult` - 工具选择结果

**使用示例**：

```python
result = await manager.select_best_tool(
    task_description="检索相关专利",
    task_type="patent_search",
    domain="patent"
)

print(f"最佳工具: {result.tool.name}")
print(f"置信度: {result.confidence:.2%}")
```

---

##### get_all_active_tools()

获取所有激活的工具。

```python
def get_all_active_tools(self) -> list[ToolDefinition]
```

**返回值**：`list[ToolDefinition]` - 工具定义列表

**使用示例**：

```python
tools = manager.get_all_active_tools()

print(f"激活的工具数: {len(tools)}")
for tool in tools:
    print(f"  - {tool.name}: {tool.description}")
```

---

##### get_statistics()

获取工具管理器统计信息。

```python
def get_statistics(self) -> dict[str, Any]
```

**返回值**：`dict` - 统计信息字典

**结构示例**：

```python
{
    "total_groups": 5,
    "active_groups": 2,
    "active_group": "patent",
    "total_active_tools": 15,
    "groups": [...]
}
```

---

##### set_single_group_mode()

设置单组激活模式。

```python
def set_single_group_mode(self, enabled: bool) -> None
```

**参数说明**：

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `enabled` | `bool` | ✅ | 是否启用单组模式 |

**使用示例**：

```python
# 启用单组模式（默认）
manager.set_single_group_mode(True)

# 禁用单组模式（允许多组同时激活）
manager.set_single_group_mode(False)
```

---

## 使用示例

### 示例1: 基础使用

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

### 示例2: 自动工具选择

```python
from core.tools.tool_manager import ToolManager

manager = ToolManager()

# 自动激活工具组
group_name = await manager.auto_activate_group_for_task(
    task_description="分析专利CN123456789A的创造性",
    task_type="patent_analysis",
    domain="patent"
)

print(f"自动激活: {group_name}")

# 选择最佳工具
result = await manager.select_best_tool(
    task_description="检索相关专利",
    task_type="patent_search"
)

print(f"推荐工具: {result.tool.name}")
print(f"置信度: {result.confidence:.2%}")
```

### 示例3: 多组管理

```python
from core.tools.tool_manager import ToolManager

manager = ToolManager()

# 启用多组模式
manager.set_single_group_mode(False)

# 同时激活多个工具组
manager.activate_group("patent", deactivate_others=False)
manager.activate_group("legal", deactivate_others=False)
manager.activate_group("academic", deactivate_others=False)

# 获取所有激活的工具
tools = manager.get_all_active_tools()
print(f"激活工具总数: {len(tools)}")
```

---

## 最佳实践

### 1. 工具组设计原则

```python
# 原则1: 高内聚
# 一个工具组内的工具应该功能相关
patent_group = ToolGroupDef(
    name="patent",
    tool_ids=["patent_search", "patent_analyzer", "patent_translator"]
)

# 原则2: 低耦合
# 工具组之间应该尽量独立，减少依赖

# 原则3: 明确职责
# 每个工具组应该有明确的职责边界
```

### 2. 激活规则配置

```python
# 策略1: 多规则组合
group_def = ToolGroupDef(
    name="patent",
    activation_rules=[
        # 关键词规则（宽泛匹配）
        GroupActivationRule(
            rule_type=GroupActivationRule.KEYWORD,
            keywords=["专利", "patent"],
            priority=10
        ),
        # 任务类型规则（精确匹配）
        GroupActivationRule(
            rule_type=GroupActivationRule.TASK_TYPE,
            task_types=["patent_search", "patent_analysis"],
            priority=20
        ),
        # 领域规则（上下文匹配）
        GroupActivationRule(
            rule_type=GroupActivationRule.DOMAIN,
            domains=["patent"],
            priority=15
        )
    ]
)

# 策略2: 优先级设置
# 高优先级规则应该更精确
high_priority_rule = GroupActivationRule(
    rule_type=GroupActivationRule.TASK_TYPE,
    task_types=["exact_match"],
    priority=100
)

low_priority_rule = GroupActivationRule(
    rule_type=GroupActivationRule.KEYWORD,
    keywords=["broad_match"],
    priority=10
)
```

### 3. 单组 vs 多组模式

```python
# 单组模式（默认）
# 优点: 资源占用少，逻辑清晰
# 缺点: 无法同时使用多个组
manager.set_single_group_mode(True)
manager.activate_group("patent")  # 自动停用其他组

# 多组模式
# 优点: 灵活性高，可以同时使用多个组
# 缺点: 资源占用多，可能有工具冲突
manager.set_single_group_mode(False)
manager.activate_group("patent", deactivate_others=False)
manager.activate_group("legal", deactivate_others=False)
```

### 4. 错误处理

```python
# 检查工具组是否存在
group = manager.get_group("patent")
if not group:
    print("工具组不存在")
    # 创建或注册工具组
    manager.register_group(group_def)

# 检查激活结果
success = manager.activate_group("patent")
if not success:
    print("激活失败")
    # 处理错误情况

# 处理自动选择失败
group_name = await manager.auto_activate_group_for_task(...)
if not group_name:
    print("没有找到合适的工具组")
    # 使用默认工具组或提示用户
```

---

## 相关文档

- [权限系统 API](./PERMISSION_SYSTEM_API.md)
- [工具调用管理器 API](./TOOL_CALL_MANAGER_API.md)
- [工具系统使用指南](../guides/TOOL_SYSTEM_GUIDE.md)
- [工具管理器示例代码](../../examples/tools/tool_manager_examples.py)

---

**最后更新**: 2026-04-19
**维护者**: Athena平台团队
