#!/usr/bin/env python3
"""
服务自动释放功能测试脚本
Test Script for Service Auto-Release Feature

快速测试60分钟不使用自动释放功能

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-02-09
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.session.service_session_manager import ServiceType, get_service_session_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_basic_functionality():
    """测试基本功能"""
    logger.info("🧪 测试1: 基本功能测试")
    logger.info("=" * 60)

    # 创建管理器（设置较短的超时时间用于测试）
    manager = get_service_session_manager(
        idle_timeout=10,        # 10秒超时（测试用）
        cleanup_interval=5      # 5秒检查一次
    )

    # 启动监控
    await manager.start_monitoring()
    logger.info("✅ 监控已启动")

    # 注册测试服务
    import os
    session = manager.register_session(
        process_id=os.getpid(),
        service_type=ServiceType.AGENT,
        service_name="测试服务",
        auto_stop=True
    )

    logger.info(f"✅ 测试服务已注册 (PID: {session.process_id})")
    logger.info("⏰ 超时时间: 10秒（测试用）")
    logger.info("🔍 检查间隔: 5秒")

    # 显示初始状态
    stats = manager.get_stats()
    logger.info(f"📊 初始状态: {stats['active_sessions']} 个活动会话")

    # 模拟活动
    logger.info("\n🔄 模拟服务活动...")
    for i in range(3):
        await asyncio.sleep(2)
        manager.update_activity(session.process_id)
        logger.info(f"  活动更新 #{i+1} - 空闲时间重置")

    # 等待超时
    logger.info("\n⏳ 等待超时（10秒无活动）...")
    logger.info("💡 注意：服务将在超时后自动停止")

    # 等待15秒，应该会触发超时
    await asyncio.sleep(15)

    # 检查最终状态
    stats = manager.get_stats()
    logger.info(f"\n📊 最终状态: {stats['active_sessions']} 个活动会话")
    logger.info(f"🧹 清理的会话数: {stats['expired_sessions_cleaned']}")

    # 停止监控
    await manager.stop_monitoring()
    logger.info("✅ 测试完成")


async def test_multiple_services():
    """测试多个服务"""
    logger.info("\n🧪 测试2: 多服务测试")
    logger.info("=" * 60)

    # 创建管理器
    manager = get_service_session_manager(
        idle_timeout=15,       # 15秒超时
        cleanup_interval=5
    )

    await manager.start_monitoring()

    # 注册多个服务
    import os
    services = [
        ("Gateway服务", ServiceType.GATEWAY, False),  # 不自动停止
        ("小诺调度", ServiceType.XIAONUO, False),     # 不自动停止
        ("小娜专家", ServiceType.XIAONA, True),       # 自动停止
        ("缓存服务", ServiceType.CACHE, True),        # 自动停止
    ]

    sessions = []
    for name, service_type, auto_stop in services:
        session = manager.register_session(
            process_id=os.getpid() + len(sessions),
            service_type=service_type,
            service_name=name,
            auto_stop=auto_stop
        )
        sessions.append(session)
        logger.info(f"  ✅ {name} (自动停止: {auto_stop})")

    # 显示状态
    stats = manager.get_stats()
    logger.info(f"\n📊 初始会话数: {stats['active_sessions']}")
    logger.info(f"💾 内存使用: {stats['current_memory_usage_mb']:.1f}MB")

    # 只更新可自动停止的服务
    logger.info("\n🔄 更新可自动停止服务的活动时间...")
    for session in sessions:
        if session.auto_stop:
            manager.update_activity(session.process_id)
            logger.info(f"  更新: {session.service_name}")

    # 等待超时
    logger.info("\n⏳ 等待超时...")
    await asyncio.sleep(20)

    # 检查状态
    stats = manager.get_stats()
    logger.info(f"\n📊 最终会话数: {stats['active_sessions']}")
    logger.info(f"💾 内存使用: {stats['current_memory_usage_mb']:.1f}MB")

    # 显示剩余会话
    for session_info in stats['sessions']:
        logger.info(f"  📌 {session_info['service_name']} (PID: {session_info['pid']})")

    await manager.stop_monitoring()
    logger.info("✅ 测试完成")


async def test_custom_timeout():
    """测试自定义超时"""
    logger.info("\n🧪 测试3: 自定义超时测试")
    logger.info("=" * 60)

    manager = get_service_session_manager(
        idle_timeout=20,       # 默认20秒
        cleanup_interval=5
    )

    await manager.start_monitoring()

    import os
    # 注册不同超时的服务
    services = [
        ("短超时服务", 5),     # 5秒超时
        ("中等超时服务", 10),  # 10秒超时
        ("长超时服务", 15),    # 15秒超时
    ]

    sessions = []
    for name, timeout in services:
        session = manager.register_session(
            process_id=os.getpid() + len(sessions),
            service_type=ServiceType.AGENT,
            service_name=name,
            auto_stop=True,
            custom_timeout=timeout
        )
        sessions.append(session)
        logger.info(f"  ✅ {name} (超时: {timeout}秒)")

    logger.info("\n⏳ 观察不同超时时间的清理顺序...")

    # 等待所有服务超时
    await asyncio.sleep(25)

    stats = manager.get_stats()
    logger.info(f"\n📊 最终会话数: {stats['active_sessions']}")
    logger.info(f"🧹 总共清理: {stats['expired_sessions_cleaned']} 个会话")

    await manager.stop_monitoring()
    logger.info("✅ 测试完成")


async def test_real_scenario():
    """测试真实场景"""
    logger.info("\n🧪 测试4: 真实场景模拟")
    logger.info("=" * 60)

    logger.info("💡 模拟真实使用场景：")
    logger.info("   1. Gateway和小诺始终保持运行")
    logger.info("   2. 其他服务按需启动，60分钟无活动后自动释放")
    logger.info("   3. 定期更新活动时间，保持服务活跃")

    manager = get_service_session_manager(
        idle_timeout=3600,     # 60分钟（真实设置）
        cleanup_interval=300   # 5分钟检查一次
    )

    await manager.start_monitoring()

    import os
    # 注册真实服务
    services = [
        ("Gateway网关", ServiceType.GATEWAY, False, None),
        ("小诺调度中心", ServiceType.XIAONUO, False, None),
        ("小娜法律专家", ServiceType.XIAONA, True, None),
        ("云熙IP管理", ServiceType.YUNXI, True, None),
        ("缓存服务", ServiceType.CACHE, True, None),
        ("NLP服务", ServiceType.NLP, True, None),
    ]

    sessions = []
    for name, service_type, auto_stop, timeout in services:
        session = manager.register_session(
            process_id=os.getpid() + len(sessions),
            service_type=service_type,
            service_name=name,
            auto_stop=auto_stop,
            custom_timeout=timeout
        )
        sessions.append(session)

    # 显示初始状态
    stats = manager.get_stats()
    logger.info("\n📊 初始状态:")
    logger.info(f"   活动会话: {stats['active_sessions']}")
    logger.info(f"   总内存: {stats['current_memory_usage_mb']:.1f}MB")

    logger.info("\n✅ 配置完成！")
    logger.info("💡 在实际使用中：")
    logger.info("   - 核心服务（Gateway、小诺）永不停止")
    logger.info("   - 业务服务60分钟无活动后自动释放")
    logger.info("   - 每次处理请求时更新活动时间")

    # 显示会话详情
    logger.info("\n📋 会话详情:")
    for session_info in stats['sessions']:
        auto_stop_str = "是" if session_info['auto_stop'] else "否"
        logger.info(f"   - {session_info['service_name']}")
        logger.info(f"     PID: {session_info['pid']}, 自动停止: {auto_stop_str}")

    await manager.stop_monitoring()
    logger.info("\n✅ 测试完成")


async def main():
    """主测试函数"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║          Athena服务自动释放功能 - 测试套件                          ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    print("请选择测试:")
    print("1. 基本功能测试（10秒超时）")
    print("2. 多服务测试（区分核心/业务服务）")
    print("3. 自定义超时测试")
    print("4. 真实场景模拟（60分钟超时）")
    print("0. 退出")

    choice = input("\n请输入选项 (0-4): ").strip()

    tests = {
        "1": test_basic_functionality,
        "2": test_multiple_services,
        "3": test_custom_timeout,
        "4": test_real_scenario,
    }

    test_func = tests.get(choice)
    if test_func:
        try:
            await test_func()
        except KeyboardInterrupt:
            logger.info("\n⚠️ 测试被中断")
    else:
        logger.info("👋 退出测试")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 测试已退出")
