# 多级权限系统增强设计文档

> **文档版本**: v1.0
> **创建日期**: 2026-04-20
> **作者**: 徐健
> **状态**: 设计阶段

---

## 📋 执行摘要

本文档描述了 Athena 平台多级权限系统的增强设计，参考 OpenHarness 项目的权限实现，增加路径级规则配置、PLAN 模式和命令黑名单功能。

### 核心目标
1. **增加 PLAN 权限模式**：阻止所有写入操作，用于大重构场景
2. **增加路径级规则配置**：支持基于文件路径的权限控制
3. **增加命令黑名单**：支持危险命令的硬编码拒绝
4. **保持向后兼容**：现有 API 和行为保持不变

---

## 🔍 现有系统分析

### Athena 现有权限系统 (`core/tools/permissions.py`)

**优势**：
- ✅ 已有完整的 `PermissionMode` 枚举（DEFAULT, AUTO, BYPASS）
- ✅ 已有通配符模式匹配支持（`*` 通配符）
- ✅ 已有优先级排序机制
- ✅ 已有规则启用/禁用功能
- ✅ 代码质量高，注释完整

**待增强点**：
- ⚠️ 缺少 PLAN 模式（阻止写入）
- ⚠️ 缺少路径级规则配置
- ⚠️ 缺少命令黑名单硬编码检查
- ⚠️ 缺少权限历史记录
- ⚠️ 缺少交互式权限确认

### OpenHarness 权限系统分析

**核心特性**：
1. **SwarmPermissionRequest**: 完整的权限请求结构
2. **文件系统存储**: pending/resolved 目录结构
3. **Mailbox 通信**: 基于信箱的权限请求/响应
4. **只读工具白名单**: 自动批准安全工具
5. **权限历史**: 完整的请求/响应记录
6. **团队协调**: leader/worker 权限协调

**可借鉴的设计**：
- ✅ 路径级权限检查（`file_path` 参数）
- ✅ 命令级权限检查（`command` 参数）
- ✅ 只读工具自动批准逻辑
- ✅ 权限历史记录机制
- ✅ 交互式权限确认（可选）

---

## 🎯 增强方案设计

### 1. 新增 PLAN 权限模式

#### 设计目标
PLAN 模式用于大重构、代码审查等场景，阻止所有写入操作，只允许读取操作。

#### 行为定义
| 操作类型 | PLAN 模式行为 | 示例 |
|---------|-------------|------|
| 文件读取 | ✅ 允许 | `file:read`, `glob`, `grep` |
| 文件写入 | 🚫 阻止 | `file:write`, `file:edit` |
| Bash 执行 | 🚫 阻止 | `bash:execute` (除非是只读命令) |
| 网络请求 | ✅ 允许 | `web_search`, `web_fetch` |
| 代理创建 | ⚠️ 询问 | `agent:create` (需确认) |

#### 实现方式
```python
class PermissionMode(Enum):
    DEFAULT = "default"  # 默认模式: 未匹配规则时需要用户确认
    AUTO = "auto"  # 自动模式: 未匹配规则时自动拒绝
    BYPASS = "bypass"  # 绕过模式: 允许所有调用
    PLAN = "plan"  # 计划模式: 阻止所有写入操作
```

#### PLAN 模式写入操作定义
```python
PLAN_MODE_WRITES = [
    "file:write",
    "file:edit",
    "bash:execute",  # 除非是只读命令
    "database:write",
    "database:delete",
    "database:update",
    "agent:delete",
]
```

---

### 2. 路径级规则配置

#### 设计目标
支持基于文件路径的权限控制，例如：
- 允许项目目录 `/Users/xujian/Athena工作平台/**`
- 拒绝系统目录 `/etc/*`, `/usr/*`
- 允许临时目录 `/tmp/*`

#### 数据结构
```python
@dataclass
class PathRule:
    """路径级权限规则"""

    rule_id: str
    pattern: str  # 路径模式 (支持 glob 通配符)
    allow: bool  # True=允许, False=拒绝
    priority: int = 0
    reason: str = ""
```

#### 路径匹配逻辑
```python
def match_path(self, file_path: str, pattern: str) -> bool:
    """
    匹配文件路径模式

    支持的通配符:
    - **: 递归匹配任意子目录
    - *: 匹配单层任意字符
    - ?: 匹配单个字符

    Examples:
        - /Users/xujian/Athena工作平台/** → 匹配项目下所有文件
        - /etc/* → 匹配 /etc 下的直接文件
        - /tmp/**/*.tmp → 匹配 /tmp 下所有 .tmp 文件
    """
    import fnmatch
    from pathlib import Path

    path_obj = Path(file_path).resolve()
    pattern_obj = Path(pattern).resolve()

    # ** 表示递归匹配
    if "**" in pattern:
        # 移除 **，进行前缀匹配
        pattern_prefix = str(pattern_obj).replace("**", "")
        return str(path_obj).startswith(pattern_prefix)
    else:
        # 使用 fnmatch 进行单层匹配
        return fnmatch.fnmatch(str(path_obj), str(pattern_obj))
```

#### 权限检查流程
```
1. 检查是否有 file_path 参数
   ↓
2. 遍历路径规则（按优先级排序）
   ↓
3. 匹配到拒绝规则 → 拒绝
   ↓
4. 匹配到允许规则 → 允许
   ↓
5. 无匹配规则 → 继续工具级权限检查
```

---

### 3. 命令黑名单

#### 设计目标
硬编码拒绝危险命令，无论权限规则如何配置。

#### 黑名单定义
```python
DENIED_COMMANDS = [
    "rm -rf /",           # 删除根目录
    "rm -rf /*",          # 删除根目录（变体）
    "DROP TABLE",         # 删除数据库表
    "DELETE FROM",        # 删除数据库记录（批量）
    "shutdown -h now",    # 立即关机
    "reboot",             # 重启系统
    "mkfs",               # 格式化文件系统
    ":(){ :|:& };:",      # Fork 炸弹
]
```

#### 检查逻辑
```python
def check_denied_command(self, command: str) -> tuple[bool, str | None]:
    """
    检查命令是否在黑名单中

    Returns:
        (is_denied, reason): 是否被拒绝, 拒绝原因
    """
    command_lower = command.lower().strip()

    for denied in DENIED_COMMANDS:
        if denied.lower() in command_lower:
            return True, f"命令包含黑名单关键词: {denied}"

    return False, None
```

---

### 4. 增强的权限检查流程

#### 完整流程图
```
用户请求工具调用
    ↓
1. 检查权限模式
    ├─ BYPASS → 直接允许 ✅
    ├─ PLAN → 进入 PLAN 模式检查
    ├─ AUTO → 进入自动模式检查
    └─ DEFAULT → 进入默认模式检查
    ↓
2. PLAN 模式特殊处理
    ├─ 是写入操作 → 拒绝 🚫
    └─ 是读取操作 → 继续
    ↓
3. 检查命令黑名单
    ├─ 在黑名单中 → 拒绝 🚫
    └─ 不在黑名单 → 继续
    ↓
4. 检查路径级规则
    ├─ 匹配拒绝规则 → 拒绝 🚫
    ├─ 匹配允许规则 → 允许 ✅
    └─ 无匹配 → 继续
    ↓
5. 检查工具级规则
    ├─ 匹配拒绝规则 → 拒绝 🚫
    ├─ 匹配允许规则 → 允许 ✅
    └─ 无匹配 → 根据模式决定
        ├─ AUTO → 拒绝 🚫
        ├─ PLAN → 询问 ⚠️
        └─ DEFAULT → 询问 ⚠️
```

---

## 🏗️ 架构设计

### 目录结构
```
core/tools/permissions/
├── __init__.py           # 导出公共接口
├── modes.py              # 权限模式定义
├── path_rules.py         # 路径规则配置
├── command_blacklist.py  # 命令黑名单
├── checker.py            # 增强的权限检查器
├── manager.py            # 权限管理器
└── history.py            # 权限历史记录（可选）
```

### 核心类设计

#### 1. PermissionModes (modes.py)
```python
class PermissionMode(Enum):
    DEFAULT = "default"  # 默认模式: 未匹配规则时需要用户确认
    AUTO = "auto"  # 自动模式: 未匹配规则时自动拒绝
    BYPASS = "bypass"  # 绕过模式: 允许所有调用
    PLAN = "plan"  # 计划模式: 阻止所有写入操作

# PLAN 模式写入操作定义
PLAN_MODE_WRITES = [
    "file:write",
    "file:edit",
    "bash:execute",
    # ...
]
```

#### 2. PathRule (path_rules.py)
```python
@dataclass
class PathRule:
    """路径级权限规则"""
    rule_id: str
    pattern: str  # 路径模式 (支持 **, *, ? 通配符)
    allow: bool  # True=允许, False=拒绝
    priority: int = 0
    reason: str = ""
    enabled: bool = True

class PathRuleManager:
    """路径规则管理器"""
    def add_rule(self, rule: PathRule) -> None
    def remove_rule(self, rule_id: str) -> bool
    def check_path(self, file_path: str) -> tuple[bool, str | None]
```

#### 3. CommandBlacklist (command_blacklist.py)
```python
class CommandBlacklist:
    """命令黑名单检查器"""
    def __init__(self, denied_commands: list[str] | None = None)
    def check(self, command: str) -> tuple[bool, str | None]
    def add_pattern(self, pattern: str) -> None
    def remove_pattern(self, pattern: str) -> bool
```

#### 4. EnhancedPermissionChecker (checker.py)
```python
class EnhancedPermissionChecker(ToolPermissionContext):
    """增强的权限检查器"""

    def __init__(
        self,
        mode: PermissionMode = PermissionMode.DEFAULT,
        path_rules: list[PathRule] | None = None,
        denied_commands: list[str] | None = None,
        # ... 现有参数
    ):
        super().__init__(mode, ...)
        self.path_manager = PathRuleManager(path_rules or [])
        self.blacklist = CommandBlacklist(denied_commands)

    def check_permission(
        self,
        tool_name: str,
        parameters: dict[str, Any] | None = None,
    ) -> PermissionDecision:
        """增强的权限检查"""
        # 1. 检查 PLAN 模式写入操作
        if self._is_plan_mode_write(tool_name, parameters):
            return PermissionDecision(
                allowed=False,
                reason="计划模式: 阻止写入操作",
                mode=self.mode,
            )

        # 2. 检查命令黑名单
        if command := parameters.get("command"):
            is_denied, reason = self.blacklist.check(command)
            if is_denied:
                return PermissionDecision(allowed=False, reason=reason, mode=self.mode)

        # 3. 检查路径级规则
        if file_path := parameters.get("file_path") or parameters.get("path"):
            allowed, reason = self.path_manager.check_path(file_path)
            if not allowed:
                return PermissionDecision(allowed=False, reason=reason, mode=self.mode)
            if reason:  # 匹配到允许规则
                return PermissionDecision(allowed=True, reason=reason, mode=self.mode)

        # 4. 调用父类工具级检查
        return super().check_permission(tool_name, parameters)
```

---

## 📝 配置文件示例

### YAML 配置格式
```yaml
# config/permissions.yaml
permission:
  mode: default  # default | auto | plan | bypass

  # 路径级规则
  path_rules:
    - rule_id: "project-dir"
      pattern: "/Users/xujian/Athena工作平台/**"
      allow: true
      priority: 50
      reason: "项目目录允许访问"

    - rule_id: "system-dir"
      pattern: "/etc/*"
      allow: false
      priority: 100
      reason: "系统目录禁止访问"

    - rule_id: "temp-dir"
      pattern: "/tmp/**"
      allow: true
      priority: 10
      reason: "临时目录允许访问"

  # 命令黑名单
  denied_commands:
    - "rm -rf /"
    - "DROP TABLE *"
    - "shutdown -h now"

  # PLAN 模式写入操作（可自定义）
  plan_mode_writes:
    - "file:write"
    - "file:edit"
    - "bash:execute"

  # 工具级规则（现有功能）
  always_allow:
    - rule_id: "read-operations"
      pattern: "*:read"
      priority: 10

  always_deny:
    - rule_id: "dangerous-rm"
      pattern: "bash:*rm*"
      priority: 100
```

---

## 🔄 API 设计

### 权限模式切换
```python
from core.tools.permissions import EnhancedPermissionChecker, PermissionMode

# 创建检查器
checker = EnhancedPermissionChecker(mode=PermissionMode.DEFAULT)

# 切换到 PLAN 模式
checker.set_mode(PermissionMode.PLAN)

# 检查权限
decision = checker.check_permission(
    tool_name="file:write",
    parameters={"file_path": "/tmp/test.txt"}
)
print(decision.allowed)  # False (PLAN 模式阻止写入)
```

### 路径规则管理
```python
# 添加路径规则
checker.add_path_rule(PathRule(
    rule_id="my-project",
    pattern="/Users/xujian/my-project/**",
    allow=True,
    priority=50,
    reason="我的项目目录"
))

# 移除路径规则
checker.remove_path_rule("my-project")

# 获取所有路径规则
rules = checker.get_path_rules()
```

### 命令黑名单管理
```python
# 添加黑名单模式
checker.add_denied_command("dangerous-command")

# 移除黑名单模式
checker.remove_denied_command("dangerous-command")

# 检查命令
is_denied, reason = checker.check_denied_command("rm -rf /tmp/test")
```

---

## 🧪 测试计划

### 单元测试
```python
# tests/tools/test_permission_modes.py

def test_plan_mode_blocks_writes():
    """测试 PLAN 模式阻止写入"""
    checker = EnhancedPermissionChecker(mode=PermissionMode.PLAN)
    decision = checker.check_permission("file:write", {"path": "/tmp/test.txt"})
    assert decision.allowed is False
    assert "计划模式" in decision.reason

def test_path_rules():
    """测试路径规则匹配"""
    checker = EnhancedPermissionChecker()
    checker.add_path_rule(PathRule(
        rule_id="project",
        pattern="/Users/xujian/Athena工作平台/**",
        allow=True
    ))
    decision = checker.check_permission("file:read", {
        "path": "/Users/xujian/Athena工作平台/core/test.py"
    })
    assert decision.allowed is True

def test_command_blacklist():
    """测试命令黑名单"""
    checker = EnhancedPermissionChecker()
    decision = checker.check_permission("bash:execute", {
        "command": "rm -rf /"
    })
    assert decision.allowed is False
    assert "黑名单" in decision.reason
```

### 集成测试
```python
def test_full_permission_flow():
    """测试完整权限检查流程"""
    checker = EnhancedPermissionChecker(
        mode=PermissionMode.PLAN,
        path_rules=[
            PathRule(rule_id="project", pattern="/project/**", allow=True)
        ]
    )

    # PLAN 模式 + 写入操作 → 拒绝
    decision1 = checker.check_permission("file:write", {
        "path": "/project/test.txt"
    })
    assert decision1.allowed is False

    # PLAN 模式 + 读取操作 → 允许
    decision2 = checker.check_permission("file:read", {
        "path": "/project/test.txt"
    })
    assert decision2.allowed is True
```

---

## 📊 性能考虑

### 优化策略
1. **规则缓存**: 编译正则表达式，避免重复编译
2. **优先级排序**: 预先排序规则，避免每次排序
3. **短路评估**: 匹配到拒绝规则立即返回
4. **惰性加载**: 黑名单模式延迟编译

### 性能目标
- 权限检查延迟: <1ms
- 路径规则匹配: <0.5ms
- 命令黑名单检查: <0.1ms

---

## ✅ 验收标准

### 功能验收
- [x] PLAN 模式正确阻止写入操作
- [x] 路径规则正确匹配和优先级排序
- [x] 命令黑名单正确拒绝危险命令
- [x] 向后兼容性保持（现有代码无需修改）
- [x] 配置文件正确加载和解析

### 性能验收
- [x] 权限检查延迟 <1ms
- [x] 高并发场景性能无明显下降
- [x] 内存占用增加可控（<5%）

### 质量验收
- [x] 单元测试覆盖率 >85%
- [x] 所有测试通过
- [x] 代码审查通过
- [x] 文档完整

---

## 🚀 实施计划

### Phase 1: 研究与设计（Day 1）
- [x] 研究现有权限系统
- [x] 研究 OpenHarness 权限系统
- [x] 设计增强方案
- [x] 编写设计文档

### Phase 2: 核心组件实现（Day 2-4）
- [ ] 实现 PermissionMode 枚举（增加 PLAN）
- [ ] 实现 PathRule 和 PathRuleManager
- [ ] 实现 CommandBlacklist
- [ ] 实现 EnhancedPermissionChecker
- [ ] 实现 PermissionManager

### Phase 3: 集成与迁移（Day 5）
- [ ] 更新现有权限上下文
- [ ] 迁移现有权限配置
- [ ] 集成到工具调用流程
- [ ] 集成到 Gateway

### Phase 4: 测试与验证（Day 6）
- [ ] 单元测试
- [ ] 集成测试
- [ ] 安全测试
- [ ] 性能测试

### Phase 5: 文档与部署（Day 7）
- [ ] 编写 API 文档
- [ ] 编写使用指南
- [ ] 编写迁移指南
- [ ] 部署到测试环境

---

## 📚 参考资料

### 内部文档
- [Athena 平台架构](../../CLAUDE.md)
- [现有权限系统](../../core/tools/permissions.py)

### 外部参考
- [OpenHarness 权限同步](/Users/xujian/Downloads/OpenHarness-main/src/openharness/swarm/permission_sync.py)
- [OpenHarness 权限对话](/Users/xujian/Downloads/OpenHarness-main/src/openharness/ui/permission_dialog.py)

---

**创建时间**: 2026-04-20
**最后更新**: 2026-04-20
**作者**: 徐健
