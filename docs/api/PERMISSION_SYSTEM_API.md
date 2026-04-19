# 工具权限系统 API 文档

> **版本**: v1.0.0
> **作者**: Athena平台团队
> **创建时间**: 2026-04-19
> **模块**: `core/tools/permissions.py`

---

## 目录

- [概述](#概述)
- [核心类](#核心类)
  - [PermissionMode](#permissionmode)
  - [PermissionRule](#permissionrule)
  - [PermissionDecision](#permissiondecision)
  - [ToolPermissionContext](#toolpermissioncontext)
- [预定义规则](#预定义规则)
- [使用示例](#使用示例)
- [最佳实践](#最佳实践)
- [异常处理](#异常处理)

---

## 概述

工具权限系统实现Claude Code风格的工具权限控制，支持三种权限模式和基于规则的访问控制。

### 核心特性

1. **三种权限模式**
   - `DEFAULT`: 默认模式，需要用户确认
   - `AUTO`: 自动模式，根据规则自动决策
   - `BYPASS`: 绕过模式，允许所有调用

2. **基于规则的权限控制**
   - 支持允许/拒绝规则
   - 通配符模式匹配
   - 优先级冲突解决

3. **运行时权限检查**
   - 实时权限验证
   - 详细的决策原因记录
   - 与ToolCallManager无缝集成

---

## 核心类

### PermissionMode

**权限模式枚举**

```python
class PermissionMode(Enum):
    DEFAULT = "default"  # 默认模式: 未匹配规则时需要用户确认
    AUTO = "auto"        # 自动模式: 未匹配规则时自动拒绝
    BYPASS = "bypass"    # 绕过模式: 允许所有调用
```

| 模式 | 说明 | 使用场景 |
|-----|------|---------|
| `DEFAULT` | 保守模式，未匹配规则时需要用户确认 | 生产环境，敏感操作 |
| `AUTO` | 自动模式，未匹配规则时自动拒绝 | 自动化任务，批处理 |
| `BYPASS` | 绕过模式，允许所有调用 | 测试环境，调试模式 |

---

### PermissionRule

**权限规则数据类**

定义工具调用的允许或拒绝规则。

#### 参数说明

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `rule_id` | `str` | ✅ | 规则唯一标识 |
| `pattern` | `str` | ✅ | 工具名称模式（支持通配符`*`） |
| `description` | `str` | ✅ | 规则描述 |
| `enabled` | `bool` | ❌ | 是否启用该规则（默认: `True`） |
| `priority` | `int` | ❌ | 优先级（默认: `0`，数值越大优先级越高） |
| `metadata` | `dict[str, Any]` | ❌ | 额外元数据（默认: `{}`） |

#### 通配符模式

支持在`pattern`中使用`*`通配符：

- `bash:*` - 匹配所有bash工具
- `*_search` - 匹配所有搜索工具
- `file_*` - 匹配所有文件操作工具
- `*:read` - 匹配所有读操作

#### 使用示例

```python
from core.tools.permissions import PermissionRule

# 允许规则
allow_rule = PermissionRule(
    rule_id="safe-read",
    pattern="*:read",
    description="允许所有读操作",
    priority=10
)

# 拒绝规则
deny_rule = PermissionRule(
    rule_id="dangerous-rm",
    pattern="bash:*rm*",
    description="拒绝包含rm的bash命令",
    priority=100
)

# 禁用规则
disabled_rule = PermissionRule(
    rule_id="temp-rule",
    pattern="temp:*",
    description="临时规则（已禁用）",
    enabled=False
)
```

---

### PermissionDecision

**权限决策结果**

记录权限检查的结果和原因。

#### 属性说明

| 属性 | 类型 | 说明 |
|-----|------|------|
| `allowed` | `bool` | 是否允许调用 |
| `reason` | `str` | 决策原因 |
| `mode` | `PermissionMode` | 决策时使用的权限模式 |
| `matched_rule` | `str \| None` | 匹配的规则ID（如果有） |

#### 使用示例

```python
decision = ctx.check_permission("file:read")

print(f"允许: {decision.allowed}")
print(f"原因: {decision.reason}")
print(f"模式: {decision.mode.value}")
print(f"匹配规则: {decision.matched_rule}")
```

---

### ToolPermissionContext

**工具权限上下文**

管理工具调用的权限规则和决策逻辑。

#### 构造函数

```python
def __init__(
    self,
    mode: PermissionMode = PermissionMode.DEFAULT,
    always_allow: list[PermissionRule] | None = None,
    always_deny: list[PermissionRule] | None = None
)
```

**参数说明**：

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `mode` | `PermissionMode` | ❌ | 权限模式（默认: `DEFAULT`） |
| `always_allow` | `list[PermissionRule]` | ❌ | 总是允许的规则列表 |
| `always_deny` | `list[PermissionRule]` | ❌ | 总是拒绝的规则列表 |

#### 权限检查流程

```
1. 检查是否为BYPASS模式 → 直接允许
2. 检查拒绝规则（按优先级排序）→ 匹配则拒绝
3. 检查允许规则（按优先级排序）→ 匹配则允许
4. 无匹配规则 → 根据mode决定（AUTO:拒绝, DEFAULT:需要确认）
```

#### 主要方法

##### check_permission()

检查工具调用权限。

```python
def check_permission(
    self,
    tool_name: str,
    parameters: dict[str, Any] | None = None
) -> PermissionDecision
```

**参数说明**：

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `tool_name` | `str` | ✅ | 工具名称 |
| `parameters` | `dict[str, Any]` | ❌ | 工具参数（可选，未来可用于高级规则） |

**返回值**：`PermissionDecision` - 权限决策结果

**使用示例**：

```python
decision = ctx.check_permission(
    tool_name="file:read",
    parameters={"path": "/tmp/file.txt"}
)

if decision.allowed:
    print("允许调用")
else:
    print(f"拒绝调用: {decision.reason}")
```

---

##### add_rule()

添加权限规则。

```python
def add_rule(
    self,
    rule_type: str,
    rule: PermissionRule
) -> None
```

**参数说明**：

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `rule_type` | `str` | ✅ | 规则类型（`"allow"` 或 `"deny"`） |
| `rule` | `PermissionRule` | ✅ | 权限规则 |

**异常**：

- `ValueError`: 如果规则类型无效

**使用示例**：

```python
ctx.add_rule("allow", PermissionRule(
    rule_id="safe-read",
    pattern="*:read",
    description="允许所有读操作"
))

ctx.add_rule("deny", PermissionRule(
    rule_id="dangerous-rm",
    pattern="bash:*rm*",
    description="拒绝危险命令"
))
```

---

##### remove_rule()

移除权限规则。

```python
def remove_rule(self, rule_id: str) -> bool
```

**参数说明**：

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `rule_id` | `str` | ✅ | 规则ID |

**返回值**：`bool` - 是否成功移除

**使用示例**：

```python
success = ctx.remove_rule("temp-rule")
if success:
    print("规则已移除")
else:
    print("规则不存在")
```

---

##### set_mode()

设置权限模式。

```python
def set_mode(self, mode: PermissionMode) -> None
```

**参数说明**：

| 参数 | 类型 | 必需 | 说明 |
|-----|------|-----|------|
| `mode` | `PermissionMode` | ✅ | 新的权限模式 |

**使用示例**：

```python
# 切换到自动模式
ctx.set_mode(PermissionMode.AUTO)

# 切换到绕过模式（谨慎使用）
ctx.set_mode(PermissionMode.BYPASS)
```

---

##### get_rules()

获取所有规则。

```python
def get_rules(self) -> dict[str, Any]
```

**返回值**：`dict` - 包含allow和deny规则的字典

**结构示例**：

```python
{
    "allow": [
        {
            "id": "safe-read",
            "pattern": "*:read",
            "description": "允许所有读操作",
            "enabled": True,
            "priority": 10
        }
    ],
    "deny": [
        {
            "id": "dangerous-rm",
            "pattern": "bash:*rm*",
            "description": "拒绝包含rm的bash命令",
            "enabled": True,
            "priority": 100
        }
    ]
}
```

---

## 预定义规则

### DEFAULT_ALLOW_RULES

默认允许规则列表：

| 规则ID | 模式 | 描述 | 优先级 |
|-------|------|------|--------|
| `read-operations` | `*:read` | 允许所有读操作 | 10 |
| `safe-tools` | `web_search` | 允许网络搜索工具 | 10 |
| `patent-tools` | `patent_*` | 允许专利相关工具 | 10 |
| `analysis-tools` | `*analysis*` | 允许分析类工具 | 5 |

### DEFAULT_DENY_RULES

默认拒绝规则列表：

| 规则ID | 模式 | 描述 | 优先级 |
|-------|------|------|--------|
| `dangerous-rm` | `bash:*rm*` | 拒绝包含rm的bash命令 | 100 |
| `dangerous-format` | `bash:*format*` | 拒绝格式化磁盘命令 | 100 |
| `system-critical` | `*:shutdown` | 拒绝系统关机命令 | 100 |

---

## 使用示例

### 示例1: 基础使用

```python
from core.tools.permissions import (
    ToolPermissionContext,
    PermissionMode,
    PermissionRule
)

# 创建权限上下文
ctx = ToolPermissionContext(mode=PermissionMode.AUTO)

# 添加规则
ctx.add_rule("allow", PermissionRule(
    rule_id="safe-read",
    pattern="*:read",
    description="允许所有读操作",
    priority=10
))

# 检查权限
decision = ctx.check_permission("file:read")
print(f"允许: {decision.allowed}, 原因: {decision.reason}")
```

### 示例2: 复杂规则配置

```python
from core.tools.permissions import (
    ToolPermissionContext,
    PermissionMode,
    PermissionRule,
    DEFAULT_ALLOW_RULES,
    DEFAULT_DENY_RULES
)

# 创建带默认规则的上下文
ctx = ToolPermissionContext(
    mode=PermissionMode.DEFAULT,
    always_allow=DEFAULT_ALLOW_RULES,
    always_deny=DEFAULT_DENY_RULES
)

# 添加自定义规则
ctx.add_rule("deny", PermissionRule(
    rule_id="no-production-write",
    pattern="production:*write",
    description="拒绝生产环境写操作",
    priority=200  # 高优先级
))

# 检查权限
decision = ctx.check_permission("production:db:write")
if not decision.allowed:
    print(f"操作被拒绝: {decision.reason}")
```

### 示例3: 动态规则管理

```python
from core.tools.permissions import get_global_permission_context

# 获取全局权限上下文
ctx = get_global_permission_context()

# 临时添加规则
ctx.add_rule("allow", PermissionRule(
    rule_id="temp-allow",
    pattern="temp:*",
    description="临时允许测试工具"
))

# 执行操作
decision = ctx.check_permission("temp:test_tool")

# 操作完成后移除规则
ctx.remove_rule("temp-allow")
```

---

## 最佳实践

### 1. 权限模式选择

| 场景 | 推荐模式 | 理由 |
|-----|---------|------|
| 生产环境 | `DEFAULT` | 保守策略，需要用户确认 |
| 自动化任务 | `AUTO` | 明确规则，自动决策 |
| 开发测试 | `BYPASS` | 方便调试（谨慎使用） |

### 2. 规则优先级设置

```python
# 高优先级：安全相关规则
security_rule = PermissionRule(
    rule_id="security-block",
    pattern="*",
    description="安全阻止规则",
    priority=1000
)

# 中优先级：业务逻辑规则
business_rule = PermissionRule(
    rule_id="business-allow",
    pattern="business:*",
    description="业务允许规则",
    priority=100
)

# 低优先级：辅助规则
helper_rule = PermissionRule(
    rule_id="helper-allow",
    pattern="helper:*",
    description="辅助规则",
    priority=10
)
```

### 3. 通配符使用技巧

```python
# 精确匹配
pattern = "file:read"  # 只匹配 file:read

# 前缀匹配
pattern = "file:*"  # 匹配 file:read, file:write, etc.

# 后缀匹配
pattern = "*:read"  # 匹配 file:read, db:read, etc.

# 包含匹配
pattern = "*analysis*"  # 匹配 code_analysis, semantic_analysis, etc.

# 全匹配
pattern = "*"  # 匹配所有工具
```

### 4. 规则组合策略

```python
# 策略1: 白名单模式（默认拒绝，明确允许）
ctx = ToolPermissionContext(mode=PermissionMode.AUTO)
ctx.add_rule("allow", PermissionRule(
    rule_id="whitelist",
    pattern="safe:*",
    description="只允许安全工具"
))

# 策略2: 黑名单模式（默认允许，明确拒绝）
ctx = ToolPermissionContext(mode=PermissionMode.DEFAULT)
ctx.add_rule("deny", PermissionRule(
    rule_id="blacklist",
    pattern="dangerous:*",
    description="拒绝危险工具"
))

# 策略3: 分层控制
ctx = ToolPermissionContext(mode=PermissionMode.DEFAULT)
# 基础层：安全规则
ctx.add_rule("deny", PermissionRule(
    rule_id="security-layer",
    pattern="*",
    description="默认拒绝所有",
    priority=100
))
# 业务层：业务规则
ctx.add_rule("allow", PermissionRule(
    rule_id="business-layer",
    pattern="business:*",
    description="允许业务工具",
    priority=50
))
```

---

## 异常处理

### ValueError

**场景**: 无效的规则类型

```python
try:
    ctx.add_rule("invalid_type", PermissionRule(...))
except ValueError as e:
    print(f"规则类型错误: {e}")
    # 正确的类型是 "allow" 或 "deny"
```

### 权限检查失败处理

```python
decision = ctx.check_permission("dangerous:operation")

if not decision.allowed:
    # 记录日志
    logger.warning(f"权限检查失败: {decision.reason}")

    # 根据模式处理
    if decision.mode == PermissionMode.AUTO:
        # 自动模式：直接拒绝
        raise PermissionDenied(f"操作被拒绝: {decision.reason}")
    elif decision.mode == PermissionMode.DEFAULT:
        # 默认模式：请求用户确认
        user_input = request_user_confirmation(decision.reason)
        if not user_input:
            raise PermissionDenied("用户拒绝操作")
```

---

## 全局函数

### get_global_permission_context()

获取全局权限上下文（单例模式）。

```python
def get_global_permission_context() -> ToolPermissionContext
```

**返回值**：`ToolPermissionContext` - 全局权限上下文

**使用示例**：

```python
from core.tools.permissions import get_global_permission_context

# 获取全局上下文
ctx = get_global_permission_context()

# 检查权限
decision = ctx.check_permission("tool:name")
```

---

## 相关文档

- [工具管理器 API](./TOOL_MANAGER_API.md)
- [工具调用管理器](./TOOL_CALL_MANAGER_API.md)
- [工具系统使用指南](../guides/TOOL_SYSTEM_GUIDE.md)
- [权限系统示例代码](../../examples/tools/permission_examples.py)

---

**最后更新**: 2026-04-19
**维护者**: Athena平台团队
