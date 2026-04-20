"""
多级权限系统单元测试

测试 PLAN 模式、路径规则和命令黑名单功能。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import pytest

from core.tools.permissions_v2.modes import (
    PermissionMode,
    PLAN_MODE_WRITES,
    DENIED_COMMANDS,
    is_plan_mode_write,
    is_read_only_tool,
)
from core.tools.permissions_v2.path_rules import (
    PathRule,
    PathRuleManager,
    DEFAULT_PATH_RULES,
)
from core.tools.permissions_v2.command_blacklist import (
    CommandBlacklist,
    check_denied_command,
)
from core.tools.permissions_v2.checker import (
    EnhancedPermissionChecker,
    PermissionConfig,
)


# ========================================
# PermissionMode 测试
# ========================================


def test_permission_mode_values():
    """测试权限模式枚举值"""
    assert PermissionMode.DEFAULT.value == "default"
    assert PermissionMode.AUTO.value == "auto"
    assert PermissionMode.BYPASS.value == "bypass"
    assert PermissionMode.PLAN.value == "plan"


def test_plan_mode_writes_list():
    """测试 PLAN 模式写入操作列表"""
    assert "file:write" in PLAN_MODE_WRITES
    assert "file:edit" in PLAN_MODE_WRITES
    assert "bash:execute" in PLAN_MODE_WRITES
    assert "file:read" not in PLAN_MODE_WRITES
    assert "web_search" not in PLAN_MODE_WRITES


def test_denied_commands_list():
    """测试危险命令黑名单"""
    assert "rm -rf /" in DENIED_COMMANDS
    assert "DROP TABLE" in DENIED_COMMANDS
    assert "shutdown -h now" in DENIED_COMMANDS


def test_is_plan_mode_write():
    """测试 PLAN 模式写入操作判断"""
    # 写入操作
    assert is_plan_mode_write("file:write") is True
    assert is_plan_mode_write("file:edit") is True
    assert is_plan_mode_write("bash:execute") is True
    assert is_plan_mode_write("database:delete") is True

    # 读取操作
    assert is_plan_mode_write("file:read") is False
    assert is_plan_mode_write("web_search") is False
    assert is_plan_mode_write("glob") is False


def test_is_read_only_tool():
    """测试只读工具判断"""
    assert is_read_only_tool("read_file") is True
    assert is_read_only_tool("glob") is True
    assert is_read_only_tool("grep") is True
    assert is_read_only_tool("web_search") is True

    assert is_read_only_tool("file:write") is False
    assert is_read_only_tool("bash:execute") is False


# ========================================
# PathRule 测试
# ========================================


def test_path_rule_creation():
    """测试路径规则创建"""
    rule = PathRule(
        rule_id="test-rule",
        pattern="/tmp/**",
        allow=True,
        priority=10,
        reason="测试规则",
    )

    assert rule.rule_id == "test-rule"
    assert rule.allow is True
    assert rule.priority == 10
    assert rule.reason == "测试规则"
    assert rule.enabled is True


def test_path_rule_manager_init():
    """测试路径规则管理器初始化"""
    manager = PathRuleManager()
    assert len(manager.get_rules()) == 0

    manager_with_rules = PathRuleManager(rules=DEFAULT_PATH_RULES)
    assert len(manager_with_rules.get_rules()) > 0


def test_path_rule_manager_add_remove():
    """测试路径规则添加和移除"""
    manager = PathRuleManager()

    rule = PathRule(
        rule_id="test",
        pattern="/test/**",
        allow=True,
    )

    manager.add_rule(rule)
    assert len(manager.get_rules()) == 1
    assert manager.get_rule("test") is not None

    manager.remove_rule("test")
    assert len(manager.get_rules()) == 0
    assert manager.get_rule("test") is None


def test_path_match_recursive():
    """测试路径递归匹配 (**)"""
    manager = PathRuleManager()

    manager.add_rule(
        PathRule(
            rule_id="project",
            pattern="/Users/xujian/Athena工作平台/**",
            allow=True,
        )
    )

    # 应该匹配所有子目录
    allowed, _ = manager.check_path("/Users/xujian/Athena工作平台/core/test.py")
    assert allowed is True

    allowed, _ = manager.check_path("/Users/xujian/Athena工作平台/docs/api/test.md")
    assert allowed is True


def test_path_match_single_level():
    """测试路径单层匹配 (*)"""
    # 创建空的管理器（不使用默认规则）
    manager = PathRuleManager(rules=[])

    manager.add_rule(
        PathRule(
            rule_id="tmp-deny",
            pattern="/tmp/*",
            allow=False,
            priority=100,
        )
    )

    # 应该匹配 /tmp 下的直接文件
    allowed, reason = manager.check_path("/tmp/test.txt")
    assert allowed is False
    assert "拒绝规则" in reason

    # 不应该匹配子目录（单层 * 不匹配 /）
    allowed, _ = manager.check_path("/tmp/subdir/test.txt")
    assert allowed is True  # 未匹配到单层 * 规则


def test_path_priority():
    """测试路径规则优先级"""
    manager = PathRuleManager()

    # 添加低优先级允许规则
    manager.add_rule(
        PathRule(
            rule_id="allow-all",
            pattern="/tmp/**",
            allow=True,
            priority=10,
        )
    )

    # 添加高优先级拒绝规则
    manager.add_rule(
        PathRule(
            rule_id="deny-specific",
            pattern="/tmp/secret.txt",
            allow=False,
            priority=100,
        )
    )

    # 高优先级规则应该优先生效
    allowed, _ = manager.check_path("/tmp/secret.txt")
    assert allowed is False

    # 其他文件应该被允许
    allowed, _ = manager.check_path("/tmp/other.txt")
    assert allowed is True


def test_path_rule_enabled():
    """测试路径规则启用/禁用"""
    manager = PathRuleManager()

    rule = PathRule(
        rule_id="test",
        pattern="/test/**",
        allow=False,
    )

    manager.add_rule(rule)

    # 禁用规则
    manager.set_rule_enabled("test", False)

    # 禁用后不应该生效
    allowed, _ = manager.check_path("/test/file.txt")
    assert allowed is True  # 未匹配到任何规则


# ========================================
# CommandBlacklist 测试
# ========================================


def test_command_blacklist_init():
    """测试命令黑名单初始化"""
    blacklist = CommandBlacklist()
    assert len(blacklist.get_patterns()) > 0

    custom_blacklist = CommandBlacklist(denied_patterns=["test"])
    assert len(custom_blacklist.get_patterns()) == 1


def test_command_blacklist_check():
    """测试命令黑名单检查"""
    blacklist = CommandBlacklist()

    # 危险命令应该被拒绝
    is_denied, reason = blacklist.check("rm -rf /")
    assert is_denied is True
    assert "黑名单" in reason

    is_denied, _ = blacklist.check("DROP TABLE users")
    assert is_denied is True

    # 安全命令不应该被拒绝
    is_denied, _ = blacklist.check("ls -la")
    assert is_denied is False

    is_denied, _ = blacklist.check("cat file.txt")
    assert is_denied is False


def test_command_blacklist_add_remove():
    """测试命令黑名单添加和移除"""
    blacklist = CommandBlacklist()

    # 添加自定义模式
    blacklist.add_pattern("custom-danger")
    assert "custom-danger" in blacklist.get_patterns()

    # 移除模式
    assert blacklist.remove_pattern("custom-danger") is True
    assert "custom-danger" not in blacklist.get_patterns()

    # 移除不存在的模式
    assert blacklist.remove_pattern("not-exist") is False


def test_check_denied_command_helper():
    """测试便捷函数"""
    is_denied, reason = check_denied_command("rm -rf /")
    assert is_denied is True
    assert reason is not None


# ========================================
# EnhancedPermissionChecker 测试
# ========================================


def test_enhanced_checker_init():
    """测试增强权限检查器初始化"""
    checker = EnhancedPermissionChecker(mode=PermissionMode.DEFAULT)
    assert checker._enhanced_mode == PermissionMode.DEFAULT


def test_plan_mode_blocks_writes():
    """测试 PLAN 模式阻止写入操作"""
    checker = EnhancedPermissionChecker(mode=PermissionMode.PLAN)

    # 写入操作应该被阻止
    decision = checker.check_permission("file:write", {"path": "/tmp/test.txt"})
    assert decision.allowed is False
    assert "计划模式" in decision.reason

    decision = checker.check_permission("file:edit", {"path": "/tmp/test.txt"})
    assert decision.allowed is False

    # 读取操作应该被允许
    decision = checker.check_permission("file:read", {"path": "/tmp/test.txt"})
    assert decision.allowed is True


def test_readonly_tools_auto_allow():
    """测试只读工具自动允许"""
    checker = EnhancedPermissionChecker(mode=PermissionMode.AUTO)

    # 只读工具应该在所有模式下被允许
    decision = checker.check_permission("read_file", {"path": "/tmp/test.txt"})
    assert decision.allowed is True

    decision = checker.check_permission("glob", {"pattern": "*.py"})
    assert decision.allowed is True


def test_command_blacklist_integration():
    """测试命令黑名单集成"""
    checker = EnhancedPermissionChecker()

    # 危险命令应该被拒绝
    decision = checker.check_permission("bash:execute", {"command": "rm -rf /"})
    assert decision.allowed is False
    assert "黑名单" in decision.reason


def test_path_rules_integration():
    """测试路径规则集成"""
    checker = EnhancedPermissionChecker()

    # 添加路径规则
    checker.add_path_rule(
        PathRule(
            rule_id="deny-system",
            pattern="/etc/*",
            allow=False,
            priority=100,
        )
    )

    # 系统目录应该被拒绝
    decision = checker.check_permission("file:read", {"path": "/etc/hosts"})
    assert decision.allowed is False
    assert "禁止访问" in decision.reason or "拒绝规则" in decision.reason

    # 其他目录应该被允许
    decision = checker.check_permission("file:read", {"path": "/tmp/hosts"})
    assert decision.allowed is True


def test_mode_switching():
    """测试权限模式切换"""
    checker = EnhancedPermissionChecker(mode=PermissionMode.DEFAULT)

    # 切换到 PLAN 模式
    checker.set_mode(PermissionMode.PLAN)
    assert checker._enhanced_mode == PermissionMode.PLAN

    # PLAN 模式下写入操作应该被拒绝
    decision = checker.check_permission("file:write", {"path": "/tmp/test.txt"})
    assert decision.allowed is False

    # 切换回 DEFAULT 模式
    checker.set_mode(PermissionMode.DEFAULT)
    assert checker._enhanced_mode == PermissionMode.DEFAULT


def test_get_config():
    """测试获取配置"""
    checker = EnhancedPermissionChecker(
        mode=PermissionMode.PLAN,
        path_rules=[PathRule(rule_id="test", pattern="/test/**", allow=True)],
    )

    config = checker.get_config()
    assert isinstance(config, PermissionConfig)
    assert config.mode == PermissionMode.PLAN
    assert len(config.path_rules) > 0


# ========================================
# 集成测试
# ========================================


def test_full_permission_flow():
    """测试完整权限检查流程"""
    checker = EnhancedPermissionChecker(
        mode=PermissionMode.PLAN,
        path_rules=[
            PathRule(
                rule_id="project",
                pattern="/Users/xujian/Athena工作平台/**",
                allow=True,
                priority=50,
            ),
            PathRule(
                rule_id="system",
                pattern="/etc/*",
                allow=False,
                priority=100,
            ),
        ],
    )

    # PLAN 模式 + 写入操作 → 拒绝
    decision1 = checker.check_permission("file:write", {
        "path": "/Users/xujian/Athena工作平台/test.txt"
    })
    assert decision1.allowed is False
    assert "计划模式" in decision1.reason

    # PLAN 模式 + 读取操作 + 允许路径 → 允许
    decision2 = checker.check_permission("file:read", {
        "path": "/Users/xujian/Athena工作平台/test.txt"
    })
    assert decision2.allowed is True

    # 读取操作 + 拒绝路径 → 拒绝
    decision3 = checker.check_permission("file:read", {
        "path": "/etc/hosts"
    })
    assert decision3.allowed is False
    assert "拒绝规则" in decision3.reason

    # 危险命令 → 拒绝（黑名单优先于 PLAN 模式）
    decision4 = checker.check_permission("bash:execute", {
        "command": "rm -rf /"
    })
    assert decision4.allowed is False
    # 黑名单检查在 PLAN 模式之前，所以应该是黑名单原因
    assert "黑名单" in decision4.reason or "计划模式" in decision4.reason


def test_bypass_mode_allows_all():
    """测试 BYPASS 模式允许所有操作"""
    checker = EnhancedPermissionChecker(mode=PermissionMode.BYPASS)

    # BYPASS 模式应该允许所有操作
    decision1 = checker.check_permission("file:write", {"path": "/etc/test.txt"})
    assert decision1.allowed is True

    decision2 = checker.check_permission("bash:execute", {"command": "rm -rf /"})
    assert decision2.allowed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
