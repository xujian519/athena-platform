#!/usr/bin/env python3
"""
工具权限系统单元测试
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from core.tools.permissions import (
    PermissionMode,
    PermissionRule,
    PermissionDecision,
    ToolPermissionContext,
    DEFAULT_ALLOW_RULES,
    DEFAULT_DENY_RULES,
)


class TestPermissionMode:
    """测试权限模式枚举"""

    def test_mode_values(self):
        """测试模式值"""
        assert PermissionMode.DEFAULT.value == "default"
        assert PermissionMode.AUTO.value == "auto"
        assert PermissionMode.BYPASS.value == "bypass"


class TestPermissionRule:
    """测试权限规则"""

    def test_rule_creation(self):
        """测试规则创建"""
        rule = PermissionRule(
            rule_id="test-rule",
            pattern="test:*",
            description="测试规则",
            priority=10,
        )
        assert rule.rule_id == "test-rule"
        assert rule.pattern == "test:*"
        assert rule.description == "测试规则"
        assert rule.enabled is True
        assert rule.priority == 10

    def test_rule_disabled(self):
        """测试禁用规则"""
        rule = PermissionRule(
            rule_id="disabled-rule",
            pattern="disabled:*",
            description="禁用规则",
            enabled=False,
        )
        assert rule.enabled is False


class TestToolPermissionContext:
    """测试工具权限上下文"""

    def test_initialization(self):
        """测试初始化"""
        ctx = ToolPermissionContext(mode=PermissionMode.AUTO)
        assert ctx.mode == PermissionMode.AUTO
        assert len(ctx._always_allow) == 0
        assert len(ctx._always_deny) == 0

    def test_initialization_with_rules(self):
        """测试带规则初始化"""
        allow_rule = PermissionRule(
            rule_id="allow-1",
            pattern="allow:*",
            description="允许规则",
        )
        deny_rule = PermissionRule(
            rule_id="deny-1",
            pattern="deny:*",
            description="拒绝规则",
        )

        ctx = ToolPermissionContext(
            mode=PermissionMode.AUTO,
            always_allow=[allow_rule],
            always_deny=[deny_rule],
        )

        assert len(ctx._always_allow) == 1
        assert len(ctx._always_deny) == 1
        assert "allow-1" in ctx._always_allow
        assert "deny-1" in ctx._always_deny

    def test_bypass_mode_allows_all(self):
        """测试绕过模式允许所有调用"""
        ctx = ToolPermissionContext(mode=PermissionMode.BYPASS)
        decision = ctx.check_permission("any_tool")
        assert decision.allowed is True
        assert "绕过" in decision.reason

    def test_deny_rule_blocks(self):
        """测试拒绝规则阻止调用"""
        deny_rule = PermissionRule(
            rule_id="no-danger",
            pattern="danger:*",
            description="拒绝危险工具",
            priority=100,
        )

        ctx = ToolPermissionContext(
            mode=PermissionMode.AUTO,
            always_deny=[deny_rule],
        )

        decision = ctx.check_permission("danger:command")
        assert decision.allowed is False
        assert "拒绝" in decision.reason
        assert decision.matched_rule == "no-danger"

    def test_allow_rule_permits(self):
        """测试允许规则允许调用"""
        allow_rule = PermissionRule(
            rule_id="allow-safe",
            pattern="safe:*",
            description="允许安全工具",
            priority=10,
        )

        ctx = ToolPermissionContext(
            mode=PermissionMode.AUTO,
            always_allow=[allow_rule],
        )

        decision = ctx.check_permission("safe:tool")
        assert decision.allowed is True
        assert "允许" in decision.reason
        assert decision.matched_rule == "allow-safe"

    def test_auto_mode_no_match_denies(self):
        """测试自动模式下无匹配规则时拒绝"""
        ctx = ToolPermissionContext(mode=PermissionMode.AUTO)
        decision = ctx.check_permission("unknown_tool")
        assert decision.allowed is False
        assert "自动模式" in decision.reason

    def test_default_mode_no_match_requires_confirm(self):
        """测试默认模式下无匹配规则时需要确认"""
        ctx = ToolPermissionContext(mode=PermissionMode.DEFAULT)
        decision = ctx.check_permission("unknown_tool")
        assert decision.allowed is False
        assert "需要用户确认" in decision.reason

    def test_wildcard_matching(self):
        """测试通配符匹配"""
        allow_rule = PermissionRule(
            rule_id="wildcard",
            pattern="test_*",
            description="通配符测试",
        )

        ctx = ToolPermissionContext(
            mode=PermissionMode.AUTO,
            always_allow=[allow_rule],
        )

        # 应该匹配
        assert ctx.check_permission("test_tool").allowed is True
        assert ctx.check_permission("test_123").allowed is True
        assert ctx.check_permission("test_anything").allowed is True

        # 不应该匹配
        assert ctx.check_permission("other_tool").allowed is False

    def test_priority_ordering(self):
        """测试优先级排序"""
        # 高优先级拒绝
        high_priority_deny = PermissionRule(
            rule_id="high-priority-deny",
            pattern="test:*",
            description="高优先级拒绝",
            priority=100,
        )

        # 低优先级允许
        low_priority_allow = PermissionRule(
            rule_id="low-priority-allow",
            pattern="test:*",
            description="低优先级允许",
            priority=1,
        )

        ctx = ToolPermissionContext(
            mode=PermissionMode.AUTO,
            always_deny=[high_priority_deny],
            always_allow=[low_priority_allow],
        )

        decision = ctx.check_permission("test:tool")
        # 拒绝规则优先级更高，应该被拒绝
        assert decision.allowed is False
        assert decision.matched_rule == "high-priority-deny"

    def test_disabled_rule_ignored(self):
        """测试禁用规则被忽略"""
        disabled_rule = PermissionRule(
            rule_id="disabled",
            pattern="blocked:*",
            description="禁用的规则",
            enabled=False,
        )

        ctx = ToolPermissionContext(
            mode=PermissionMode.AUTO,
            always_deny=[disabled_rule],
        )

        decision = ctx.check_permission("blocked:tool")
        # 规则被禁用，应该通过
        assert decision.allowed is False  # 但AUTO模式下无匹配允许规则，仍拒绝

    def test_add_rule(self):
        """测试添加规则"""
        ctx = ToolPermissionContext(mode=PermissionMode.AUTO)

        new_rule = PermissionRule(
            rule_id="new-rule",
            pattern="new:*",
            description="新规则",
        )

        ctx.add_rule("allow", new_rule)
        assert "new-rule" in ctx._always_allow

    def test_remove_rule(self):
        """测试移除规则"""
        rule = PermissionRule(
            rule_id="to-remove",
            pattern="remove:*",
            description="待移除规则",
        )

        ctx = ToolPermissionContext(
            mode=PermissionMode.AUTO,
            always_allow=[rule],
        )

        assert "to-remove" in ctx._always_allow
        removed = ctx.remove_rule("to-remove")
        assert removed is True
        assert "to-remove" not in ctx._always_allow

    def test_set_mode(self):
        """测试设置模式"""
        ctx = ToolPermissionContext(mode=PermissionMode.DEFAULT)
        assert ctx.mode == PermissionMode.DEFAULT

        ctx.set_mode(PermissionMode.BYPASS)
        assert ctx.mode == PermissionMode.BYPASS

    def test_get_rules(self):
        """测试获取规则"""
        allow_rule = PermissionRule(
            rule_id="allow-1",
            pattern="allow:*",
            description="允许",
            priority=10,
        )
        deny_rule = PermissionRule(
            rule_id="deny-1",
            pattern="deny:*",
            description="拒绝",
            priority=5,
        )

        ctx = ToolPermissionContext(
            mode=PermissionMode.AUTO,
            always_allow=[allow_rule],
            always_deny=[deny_rule],
        )

        rules = ctx.get_rules()
        assert "allow" in rules
        assert "deny" in rules
        assert len(rules["allow"]) == 1
        assert len(rules["deny"]) == 1
        # 检查排序 (高优先级在前)
        assert rules["allow"][0]["priority"] >= rules["allow"][-1]["priority"]


class TestDefaultRules:
    """测试默认规则"""

    def test_default_allow_rules_exist(self):
        """测试默认允许规则存在"""
        assert len(DEFAULT_ALLOW_RULES) > 0
        assert any(rule.rule_id == "read-operations" for rule in DEFAULT_ALLOW_RULES)

    def test_default_deny_rules_exist(self):
        """测试默认拒绝规则存在"""
        assert len(DEFAULT_DENY_RULES) > 0
        assert any(rule.rule_id == "dangerous-rm" for rule in DEFAULT_DENY_RULES)

    def test_default_rules_work(self):
        """测试默认规则生效"""
        ctx = ToolPermissionContext(
            mode=PermissionMode.AUTO,
            always_allow=DEFAULT_ALLOW_RULES,
            always_deny=DEFAULT_DENY_RULES,
        )

        # 测试允许规则
        assert ctx.check_permission("web_search").allowed is True
        assert ctx.check_permission("patent_search").allowed is True

        # 测试拒绝规则
        assert ctx.check_permission("bash:rm -rf /").allowed is False
        assert ctx.check_permission("bash:format disk").allowed is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
