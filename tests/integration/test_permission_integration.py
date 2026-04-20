#!/usr/bin/env python3
"""
测试权限系统端到端功能

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_permission_integration():
    """测试权限系统集成"""
    from core.tools.permissions_v2.manager import get_global_permission_manager
    from core.tools.permissions_v2.modes import PermissionMode
    from core.tools.permissions_v2.path_rules import PathRule

    # 获取全局权限管理器
    manager = get_global_permission_manager()

    # 初始化
    manager.initialize(mode=PermissionMode.PLAN)

    # 测试 PLAN 模式
    print("\n=== 测试 PLAN 模式 ===")
    allowed, reason = manager.check_permission("file:write", {"path": "/tmp/test.txt"})
    print(f"file:write → allowed={allowed}, reason={reason}")
    assert not allowed, "PLAN 模式应该阻止写入"
    assert "计划模式" in reason

    allowed, reason = manager.check_permission("file:read", {"path": "/tmp/test.txt"})
    print(f"file:read → allowed={allowed}, reason={reason}")
    assert allowed, "PLAN 模式应该允许读取"

    # 测试路径规则
    print("\n=== 测试路径规则 ===")
    manager.add_path_rule(
        PathRule(
            rule_id="test-deny",
            pattern="/tmp/secret/**",
            allow=False,
            priority=100,
        )
    )

    allowed, reason = manager.check_permission("file:read", {"path": "/tmp/secret/data.txt"})
    print(f"file:read /tmp/secret/data.txt → allowed={allowed}, reason={reason}")
    assert not allowed, "应该被路径规则拒绝"

    # 测试命令黑名单
    print("\n=== 测试命令黑名单 ===")
    allowed, reason = manager.check_permission("bash:execute", {"command": "rm -rf /"})
    print(f"bash:execute 'rm -rf /' → allowed={allowed}, reason={reason}")
    assert not allowed, "应该被命令黑名单拒绝"
    assert "黑名单" in reason

    # 测试模式切换
    print("\n=== 测试模式切换 ===")
    manager.set_mode(PermissionMode.BYPASS)
    allowed, reason = manager.check_permission("file:write", {"path": "/etc/test.txt"})
    print(f"BYPASS 模式 file:write → allowed={allowed}, reason={reason}")
    assert allowed, "BYPASS 模式应该允许所有操作"

    print("\n✅ 所有测试通过！")


async def test_tool_call_integration():
    """测试工具调用集成"""
    print("\n=== 测试工具调用集成 ===")

    from core.tools.permissions_v2.tool_call_integration import (
        create_tool_manager_with_permissions,
    )
    from core.tools.permissions_v2.modes import PermissionMode

    # 创建带权限检查的工具管理器
    tool_manager = create_tool_manager_with_permissions(
        log_dir="logs/tool_calls",
        enable_rate_limit=False,
        enable_hooks=False,
    )

    # 设置为 PLAN 模式
    tool_manager.set_permission_mode(PermissionMode.PLAN)

    # 测试写入操作被阻止
    print("\n测试 PLAN 模式阻止写入...")
    result = await tool_manager.call_tool(
        "file:write",
        {"path": "/tmp/test.txt", "content": "test"},
    )
    print(f"file:write → status={result.status}, error={result.error}")
    assert result.status.value == "failed", "写入操作应该被阻止"
    assert "权限拒绝" in result.error or "计划模式" in result.error

    print("\n✅ 工具调用集成测试通过！")


async def main():
    """主函数"""
    print("🧪 开始端到端测试...")

    await test_permission_integration()
    await test_tool_call_integration()

    print("\n🎉 所有端到端测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
