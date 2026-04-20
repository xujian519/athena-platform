# 多级权限系统使用指南

> **版本**: v2.0.0
> **作者**: Athena平台团队
> **更新日期**: 2026-04-20

---

## 🎯 快速开始

### 安装和初始化

```python
from core.tools.permissions_v2.manager import get_global_permission_manager
from core.tools.permissions_v2.modes import PermissionMode

# 获取全局权限管理器（单例）
manager = get_global_permission_manager()

# 初始化（使用默认配置）
manager.initialize(mode=PermissionMode.DEFAULT)

# 或者从配置文件加载
manager.initialize(
    mode=PermissionMode.PLAN,
    config_path="config/permissions.yaml"
)
```

### 基础使用

```python
# 检查权限
allowed, reason = manager.check_permission(
    "file:write",
    {"path": "/tmp/test.txt"}
)

if not allowed:
    print(f"权限拒绝: {reason}")
else:
    # 执行工具调用
    result = await tool_manager.call_tool("file:write", {...})
```

---

## 🔐 权限模式详解

### DEFAULT 模式（默认）

**行为**: 未匹配规则时需要用户确认

**适用场景**: 日常开发

**示例**:
```python
manager.set_mode(PermissionMode.DEFAULT)

# 匹配到允许规则 → 允许
allowed, _ = manager.check_permission("file:read", {"path": "/tmp/test.txt"})
# allowed=True

# 未匹配规则 → 拒绝（需要确认）
allowed, reason = manager.check_permission("bash:execute", {"command": "ls"})
# allowed=False, reason="默认模式: 无匹配规则，需要用户确认"
```

### AUTO 模式（自动）

**行为**: 未匹配规则时自动拒绝

**适用场景**: 自动化脚本、CI/CD

**示例**:
```python
manager.set_mode(PermissionMode.AUTO)

# 未匹配规则 → 自动拒绝
allowed, reason = manager.check_permission("bash:execute", {"command": "ls"})
# allowed=False, reason="自动模式: 无匹配允许规则，默认拒绝"
```

### PLAN 模式（计划）

**行为**: 阻止所有写入操作

**适用场景**: 大重构、代码审查

**示例**:
```python
manager.set_mode(PermissionMode.PLAN)

# 写入操作 → 被阻止
allowed, reason = manager.check_permission("file:write", {"path": "/tmp/test.txt"})
# allowed=False, reason="计划模式: 阻止写入操作 (file:write)"

# 读取操作 → 允许
allowed, _ = manager.check_permission("file:read", {"path": "/tmp/test.txt"})
# allowed=True
```

### BYPASS 模式（绕过）

**行为**: 允许所有调用

**适用场景**: 紧急修复、本地调试（⚠️ 谨慎使用）

**示例**:
```python
manager.set_mode(PermissionMode.BYPASS)

# 所有操作 → 允许
allowed, _ = manager.check_permission("bash:execute", {"command": "rm -rf /"})
# allowed=True（危险！）
```

---

## 🛣️ 路径规则配置

### 递归匹配（`**`）

匹配所有子目录：

```python
from core.tools.permissions_v2.path_rules import PathRule

manager.add_path_rule(PathRule(
    rule_id="project-dir",
    pattern="/Users/xujian/Athena工作平台/**",
    allow=True,
    priority=50,
    reason="项目目录允许访问"
))

# 匹配
# ✅ /Users/xujian/Athena工作平台/core/test.py
# ✅ /Users/xujian/Athena工作平台/docs/api/test.md
# ✅ /Users/xujian/Athena工作平台/a/b/c/d/e/test.txt
```

### 单层匹配（`*`）

只匹配直接文件和目录：

```python
manager.add_path_rule(PathRule(
    rule_id="tmp-deny",
    pattern="/tmp/*",
    allow=False,
    priority=100,
    reason="临时目录根级别禁止写入"
))

# 匹配
# ✅ /tmp/test.txt（被拒绝）
# ❌ /tmp/subdir/test.txt（不被匹配）
```

### 优先级排序

高优先级规则优先生效：

```python
# 低优先级允许规则
manager.add_path_rule(PathRule(
    rule_id="allow-all",
    pattern="/tmp/**",
    allow=True,
    priority=10
))

# 高优先级拒绝规则
manager.add_path_rule(PathRule(
    rule_id="deny-secret",
    pattern="/tmp/secret/**",
    allow=False,
    priority=100
))

# 结果: /tmp/secret/data.txt 被拒绝（高优先级）
allowed, reason = manager.check_permission("file:read", {"path": "/tmp/secret/data.txt"})
# allowed=False, reason="匹配拒绝规则: deny-secret"
```

---

## 🚫 命令黑名单

### 预定义黑名单

系统预定义了 21 条危险命令：

```python
# 系统破坏
- rm -rf /
- DROP TABLE *
- shutdown -h now

# Fork 炸弹
- :(){ :|:& };:

# ... 更多
```

### 自定义黑名单

```python
# 添加黑名单
manager.add_denied_command("my-dangerous-command")

# 移除黑名单
manager.remove_denied_command("my-dangerous-command")

# 查看所有黑名单
denied = manager.get_denied_commands()
print(f"黑名单数量: {len(denied)}")
```

---

## 🔧 实用场景

### 场景1: 大重构安全保护

```python
# 切换到 PLAN 模式
manager.set_mode(PermissionMode.PLAN)

# 允许读取代码
allowed, _ = manager.check_permission("file:read", {"path": "src/main.py"})
# allowed=True

# 阻止修改代码
allowed, reason = manager.check_permission("file:edit", {"path": "src/main.py"})
# allowed=False, reason="计划模式: 阻止写入操作 (file:edit)"

# 重构完成后切换回 DEFAULT
manager.set_mode(PermissionMode.DEFAULT)
```

### 场景2: CI/CD 自动化

```python
# 切换到 AUTO 模式
manager.set_mode(PermissionMode.AUTO)

# 添加允许规则
from core.tools.permissions_v2.path_rules import PathRule

manager.add_path_rule(PathRule(
    rule_id="ci-build",
    pattern="/home/ci/build/**",
    allow=True,
    priority=50
))

# CI 任务中的操作
allowed, reason = manager.check_permission("file:write", {"path": "/home/ci/build/output.jar"})
# allowed=True（匹配到允许规则）

# 其他操作被自动拒绝
allowed, reason = manager.check_permission("bash:execute", {"command": "rm -rf /"})
# allowed=False（黑名单）
```

### 场景3: 多项目隔离

```python
# 项目A：允许访问
manager.add_path_rule(PathRule(
    rule_id="project-a",
    pattern="/projects/project-a/**",
    allow=True,
    priority=50
))

# 项目B：允许访问
manager.add_path_rule(PathRule(
    rule_id="project-b",
    pattern="/projects/project-b/**",
    allow=True,
    priority=50
))

# 其他项目：拒绝访问
manager.add_path_rule(PathRule(
    rule_id="other-projects",
    pattern="/projects/**",
    allow=False,
    priority=100
))

# 测试
allowed, _ = manager.check_permission("file:read", {"path": "/projects/project-a/src/main.py"})
# allowed=True

allowed, _ = manager.check_permission("file:read", {"path": "/projects/project-c/src/main.py"})
# allowed=False（被拒绝规则匹配）
```

---

## 📊 监控和调试

### 查看当前配置

```python
from core.tools.permissions_v2.checker import PermissionConfig

# 获取当前配置
config = manager.get_config()

print(f"权限模式: {config.mode.value}")
print(f"路径规则数量: {len(config.path_rules)}")
print(f"黑名单模式数量: {len(config.denied_commands)}")
```

### 权限检查日志

```python
import logging

# 启用调试日志
logging.getLogger("core.tools.permissions_v2").setLevel(logging.DEBUG)

# 查看详细日志
allowed, reason = manager.check_permission("file:write", {"path": "/tmp/test.txt"})
# DEBUG:core.tools.permissions_v2.checker:检查权限: file:write
# DEBUG:core.tools.permissions_v2.checker:PLAN 模式检查...
```

### 性能监控

```python
import time

start = time.perf_counter()
allowed, reason = manager.check_permission("file:read", {"path": "/tmp/test.txt"})
end = time.perf_counter()

print(f"权限检查耗时: {(end-start)*1000:.3f}ms")
```

---

## 🎓 最佳实践

### 1. 权限模式选择

| 场景 | 推荐模式 |
|------|---------|
| 日常开发 | `DEFAULT` |
| 自动化脚本 | `AUTO` |
| 大重构 | `PLAN` |
| 紧急修复 | `BYPASS`（谨慎） |

### 2. 路径规则配置

- ✅ 使用 `**` 匹配整个目录树
- ✅ 使用 `*` 匹配单层目录
- ✅ 设置合理的优先级（0-100）
- ✅ 添加清晰的规则说明

### 3. 命令黑名单

- ✅ 定期审查黑名单
- ✅ 添加项目特定的危险命令
- ✅ 记录黑名单原因

### 4. 性能优化

- ✅ 限制规则数量（<1000）
- ✅ 禁用不需要的规则
- ✅ 使用高优先级规则快速拒绝

---

## 🔗 相关文档

- [API 文档](PERMISSION_MODES_API.md)
- [设计文档](PERMISSION_MODES_DESIGN.md)
- [迁移指南](PERMISSION_MIGRATION.md)

---

**版本**: v2.0.0
**最后更新**: 2026-04-20
**维护者**: Athena平台团队
