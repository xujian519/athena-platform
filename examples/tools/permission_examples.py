#!/usr/bin/env python3
"""
工具权限系统使用示例

演示如何使用工具权限系统进行权限控制。

作者: Athena平台团队
创建时间: 2026-04-19
版本: v1.0.0
"""

import asyncio
from core.tools.permissions import (
    ToolPermissionContext,
    PermissionMode,
    PermissionRule,
    DEFAULT_ALLOW_RULES,
    DEFAULT_DENY_RULES,
    get_global_permission_context,
)


async def example_1_basic_usage():
    """
    示例1: 基础使用

    演示如何创建权限上下文并进行基本的权限检查。
    """
    print("\n" + "=" * 60)
    print("示例1: 基础使用")
    print("=" * 60)

    # 创建权限上下文（AUTO模式）
    ctx = ToolPermissionContext(mode=PermissionMode.AUTO)

    # 添加允许规则
    ctx.add_rule(
        "allow",
        PermissionRule(
            rule_id="safe-read", pattern="*:read", description="允许所有读操作", priority=10
        ),
    )

    # 添加拒绝规则
    ctx.add_rule(
        "deny",
        PermissionRule(
            rule_id="dangerous-rm",
            pattern="bash:*rm*",
            description="拒绝包含rm的bash命令",
            priority=100,
        ),
    )

    # 测试权限检查
    test_cases = [
        ("file:read", {"path": "/tmp/file.txt"}),
        ("file:write", {"path": "/tmp/file.txt"}),
        ("bash:ls", {"command": "ls -la"}),
        ("bash:rm -rf /", {"command": "rm -rf /"}),
    ]

    print("\n权限检查结果:")
    print("-" * 60)
    for tool_name, params in test_cases:
        decision = ctx.check_permission(tool_name, params)
        status = "✅ 允许" if decision.allowed else "❌ 拒绝"
        print(f"{status} | {tool_name:20s} | {decision.reason}")


async def example_2_pattern_matching():
    """
    示例2: 通配符模式匹配

    演示如何使用通配符进行灵活的模式匹配。
    """
    print("\n" + "=" * 60)
    print("示例2: 通配符模式匹配")
    print("=" * 60)

    ctx = ToolPermissionContext(mode=PermissionMode.AUTO)

    # 添加各种模式的规则
    rules = [
        (
            "allow",
            PermissionRule(
                rule_id="all-read", pattern="*:read", description="允许所有读操作", priority=10
            ),
        ),
        (
            "allow",
            PermissionRule(
                rule_id="patent-tools",
                pattern="patent_*",
                description="允许专利工具",
                priority=10,
            ),
        ),
        (
            "allow",
            PermissionRule(
                rule_id="analysis-tools",
                pattern="*analysis*",
                description="允许分析工具",
                priority=5,
            ),
        ),
        (
            "deny",
            PermissionRule(
                rule_id="dangerous-bash",
                pattern="bash:*",
                description="拒绝所有bash命令",
                priority=100,
            ),
        ),
    ]

    for rule_type, rule in rules:
        ctx.add_rule(rule_type, rule)

    # 测试各种模式
    test_cases = [
        "file:read",  # 匹配 *:read
        "db:read",  # 匹配 *:read
        "patent_search",  # 匹配 patent_*
        "patent_analyzer",  # 匹配 patent_*
        "code_analysis",  # 匹配 *analysis*
        "semantic_analysis",  # 匹配 *analysis*
        "bash:ls",  # 匹配 bash:* (拒绝)
        "bash:cat",  # 匹配 bash:* (拒绝)
    ]

    print("\n模式匹配结果:")
    print("-" * 60)
    for tool_name in test_cases:
        decision = ctx.check_permission(tool_name)
        status = "✅ 允许" if decision.allowed else "❌ 拒绝"
        matched_rule = decision.matched_rule or "无"
        print(f"{status} | {tool_name:25s} | 匹配规则: {matched_rule}")


async def example_3_priority_resolution():
    """
    示例3: 优先级冲突解决

    演示如何使用优先级解决规则冲突。
    """
    print("\n" + "=" * 60)
    print("示例3: 优先级冲突解决")
    print("=" * 60)

    ctx = ToolPermissionContext(mode=PermissionMode.AUTO)

    # 添加冲突的规则（使用优先级解决）
    rules = [
        (
            "allow",
            PermissionRule(
                rule_id="low-priority-deny",
                pattern="file:write",
                description="低优先级拒绝",
                priority=10,
            ),
        ),
        (
            "deny",
            PermissionRule(
                rule_id="high-priority-deny",
                pattern="file:*",
                description="高优先级拒绝",
                priority=100,
            ),
        ),
        (
            "allow",
            PermissionRule(
                rule_id="very-high-priority-allow",
                pattern="file:write",
                description="非常高优先级允许",
                priority=200,
            ),
        ),
    ]

    for rule_type, rule in rules:
        ctx.add_rule(rule_type, rule)

    # 测试优先级
    decision = ctx.check_permission("file:write")
    print(f"\n工具: file:write")
    print(f"结果: {'✅ 允许' if decision.allowed else '❌ 拒绝'}")
    print(f"原因: {decision.reason}")
    print(f"匹配规则: {decision.matched_rule}")
    print(f"\n说明: 优先级最高的规则生效 (priority=200)")


async def example_4_default_rules():
    """
    示例4: 使用预定义规则

    演示如何使用系统预定义的默认规则。
    """
    print("\n" + "=" * 60)
    print("示例4: 使用预定义规则")
    print("=" * 60)

    # 使用预定义规则创建上下文
    ctx = ToolPermissionContext(
        mode=PermissionMode.DEFAULT, always_allow=DEFAULT_ALLOW_RULES, always_deny=DEFAULT_DENY_RULES
    )

    # 查看所有规则
    rules = ctx.get_rules()
    print(f"\n默认规则:")
    print(f"  允许规则: {len(rules['allow'])} 条")
    for rule in rules["allow"]:
        print(f"    - {rule['id']}: {rule['pattern']} ({rule['description']})")

    print(f"\n  拒绝规则: {len(rules['deny'])} 条")
    for rule in rules["deny"]:
        print(f"    - {rule['id']}: {rule['pattern']} ({rule['description']})")

    # 测试默认规则
    test_cases = ["file:read", "web_search", "patent_search", "bash:rm -rf /", "system:shutdown"]

    print("\n默认规则测试:")
    print("-" * 60)
    for tool_name in test_cases:
        decision = ctx.check_permission(tool_name)
        status = "✅ 允许" if decision.allowed else "❌ 拒绝"
        print(f"{status} | {tool_name:20s} | {decision.reason}")


async def example_5_dynamic_rule_management():
    """
    示例5: 动态规则管理

    演示如何在运行时动态添加、移除和修改规则。
    """
    print("\n" + "=" * 60)
    print("示例5: 动态规则管理")
    print("=" * 60)

    ctx = ToolPermissionContext(mode=PermissionMode.AUTO)

    print("\n1. 初始状态:")
    rules = ctx.get_rules()
    print(f"   允许规则: {len(rules['allow'])} 条")
    print(f"   拒绝规则: {len(rules['deny'])} 条")

    print("\n2. 添加临时规则:")
    ctx.add_rule(
        "allow",
        PermissionRule(
            rule_id="temp-allow", pattern="temp:*", description="临时允许测试工具", priority=50
        ),
    )

    decision = ctx.check_permission("temp:test_tool")
    print(f"   temp:test_tool: {'✅ 允许' if decision.allowed else '❌ 拒绝'}")

    print("\n3. 移除临时规则:")
    removed = ctx.remove_rule("temp-allow")
    print(f"   移除成功: {removed}")

    decision = ctx.check_permission("temp:test_tool")
    print(f"   temp:test_tool: {'✅ 允许' if decision.allowed else '❌ 拒绝'}")

    print("\n4. 切换权限模式:")
    print(f"   当前模式: {ctx.mode.value}")
    ctx.set_mode(PermissionMode.BYPASS)
    print(f"   新模式: {ctx.mode.value}")

    decision = ctx.check_permission("any:tool")
    print(f"   any:tool: {'✅ 允许' if decision.allowed else '❌ 拒绝'}")
    print(f"   原因: {decision.reason}")


async def example_6_global_context():
    """
    示例6: 使用全局权限上下文

    演示如何使用全局权限上下文进行统一的权限管理。
    """
    print("\n" + "=" * 60)
    print("示例6: 使用全局权限上下文")
    print("=" * 60)

    # 获取全局权限上下文
    ctx = get_global_permission_context()

    print("\n全局上下文信息:")
    print(f"  模式: {ctx.mode.value}")
    rules = ctx.get_rules()
    print(f"  允许规则: {len(rules['allow'])} 条")
    print(f"  拒绝规则: {len(rules['deny'])} 条")

    # 添加自定义规则
    print("\n添加自定义规则:")
    ctx.add_rule(
        "deny",
        PermissionRule(
            rule_id="custom-deny",
            pattern="custom:*",
            description="自定义拒绝规则",
            priority=150,
        ),
    )

    # 测试
    decision = ctx.check_permission("custom:test")
    print(f"  custom:test: {'✅ 允许' if decision.allowed else '❌ 拒绝'}")
    print(f"  原因: {decision.reason}")


async def example_7_real_world_scenario():
    """
    示例7: 真实场景 - 生产环境权限控制

    演示如何在生产环境中配置权限控制。
    """
    print("\n" + "=" * 60)
    print("示例7: 真实场景 - 生产环境权限控制")
    print("=" * 60)

    # 生产环境配置
    ctx = ToolPermissionContext(
        mode=PermissionMode.DEFAULT,  # 保守模式
        always_allow=DEFAULT_ALLOW_RULES,
        always_deny=DEFAULT_DENY_RULES,
    )

    # 添加生产环境特定规则
    production_rules = [
        (
            "deny",
            PermissionRule(
                rule_id="no-production-write",
                pattern="production:*write",
                description="拒绝生产环境写操作",
                priority=200,
            ),
        ),
        (
            "deny",
            PermissionRule(
                rule_id="no-direct-db-access",
                pattern="db:direct_*",
                description="拒绝直接数据库访问",
                priority=200,
            ),
        ),
        (
            "allow",
            PermissionRule(
                rule_id="allow-read-only-queries",
                pattern="db:query",
                description="允许只读查询",
                priority=100,
            ),
        ),
    ]

    for rule_type, rule in production_rules:
        ctx.add_rule(rule_type, rule)

    # 模拟生产环境操作
    operations = [
        ("production:db:write", "生产环境数据库写入"),
        ("db:direct_access", "直接数据库访问"),
        ("db:query", "只读数据库查询"),
        ("file:read", "文件读取"),
        ("patent_search", "专利检索"),
    ]

    print("\n生产环境权限检查:")
    print("-" * 60)
    for tool_name, desc in operations:
        decision = ctx.check_permission(tool_name)
        status = "✅ 允许" if decision.allowed else "❌ 拒绝"
        print(f"{status} | {desc:20s} | {decision.reason}")

    print("\n说明:")
    print("  - 生产环境使用DEFAULT模式，需要用户确认未匹配的操作")
    print("  - 危险操作（写操作、直接访问）被明确拒绝")
    print("  - 安全操作（读操作、查询）被允许")


async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("工具权限系统使用示例")
    print("=" * 60)

    await example_1_basic_usage()
    await example_2_pattern_matching()
    await example_3_priority_resolution()
    await example_4_default_rules()
    await example_5_dynamic_rule_management()
    await example_6_global_context()
    await example_7_real_world_scenario()

    print("\n" + "=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
