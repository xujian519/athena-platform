#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一MCP管理器测试脚本
Test Unified MCP Manager

测试MCP服务的统一管理功能

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import asyncio
import sys
import os

# 添加核心路径
sys.path.append('/Users/xujian/Athena工作平台/core/orchestration')
sys.path.append('/Users/xujian/Athena工作平台')

from unified_mcp_manager import UnifiedMCPManager

async def test_mcp_manager():
    """测试MCP管理器"""

    print("\\n" + "="*80)
    print("🧪 统一MCP管理器测试")
    print("="*80)

    # 1. 初始化管理器
    print("\\n1️⃣ 初始化MCP管理器...")
    manager = UnifiedMCPManager()

    # 2. 显示服务汇总
    print("\\n2️⃣ 显示服务汇总...")
    manager.print_services_summary()

    # 3. 测试单个服务启动
    print("\\n3️⃣ 测试启动高德地图MCP服务...")
    success = await manager.start_service("gaode-mcp-server")
    print(f"启动结果: {'成功' if success else '失败'}")

    # 4. 获取服务状态
    print("\\n4️⃣ 获取服务状态...")
    status = manager.get_service_status()
    if "gaode-mcp-server" in status:
        service_info = status["gaode-mcp-server"]
        print(f"高德地图服务状态: {service_info['status']}")
        print(f"服务描述: {service_info['description']}")
        print(f"服务能力: {', '.join(service_info['capabilities'])}")

    # 5. 测试服务重启
    print("\\n5️⃣ 测试重启服务...")
    restart_success = await manager.restart_service("gaode-mcp-server")
    print(f"重启结果: {'成功' if restart_success else '失败'}")

    # 6. 停止服务
    print("\\n6️⃣ 停止服务...")
    stop_success = await manager.stop_service("gaode-mcp-server")
    print(f"停止结果: {'成功' if stop_success else '失败'}")

    # 7. 测试批量启动
    print("\\n7️⃣ 测试批量启动Node.js服务...")
    nodejs_services = [name for name, service in manager.services.items() if service.type == "nodejs"]

    results = {}
    for service_name in nodejs_services[:2]:  # 只测试前两个
        results[service_name] = await manager.start_service(service_name)
        await asyncio.sleep(1)

    success_count = sum(1 for success in results.values() if success)
    print(f"Node.js服务启动结果: {success_count}/{len(results)} 成功")

    # 8. 最终状态
    print("\\n8️⃣ 最终服务状态...")
    final_summary = manager.get_services_summary()
    print(f"运行中服务: {final_summary['running_services']}")
    print(f"已停止服务: {final_summary['stopped_services']}")

    # 9. 清理
    print("\\n9️⃣ 清理测试环境...")
    await manager.stop_all_services()

    print("\\n" + "="*80)
    print("✅ MCP管理器测试完成")
    print("="*80)

    # 评分
    print("\\n📊 测试评分:")
    test_items = [
        ("初始化管理器", 10, 10),
        ("服务汇总显示", 10, 10),
        ("单个服务启动", 10, 10 if success else 0),
        ("服务状态获取", 10, 10),
        ("服务重启", 10, 10 if restart_success else 0),
        ("服务停止", 10, 10 if stop_success else 0),
        ("批量启动", 10, 10 if success_count > 0 else 0),
        ("状态管理", 10, 10),
        ("环境清理", 10, 10)
    ]

    total_score = sum(score for _, max_score, score in test_items)
    max_score = sum(max_score for _, max_score, _ in test_items)

    for item, max_score, score in test_items:
        status = "✅" if score == max_score else "❌" if score == 0 else "⚠️"
        print(f"{status} {item}: {score}/{max_score}")

    print(f"\\n🏆 总分: {total_score}/{max_score} ({total_score/max_score*100:.1f}%)")

    if total_score >= max_score * 0.9:
        print("🌟 优秀！MCP管理器功能完善")
    elif total_score >= max_score * 0.7:
        print("👍 良好！MCP管理器基本功能正常")
    else:
        print("⚠️ 需要改进！部分功能存在问题")

if __name__ == "__main__":
    asyncio.run(test_mcp_manager())