#!/usr/bin/env python3
"""
服务自动释放集成示例
Service Auto-Release Integration Example

演示如何在现有服务中集成60分钟不使用自动释放功能

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

from core.session.service_session_manager import (
    ServiceType,
    auto_register_current_process,
    get_service_session_manager,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# === 示例1: 最简单的集成方式（推荐）===
# =============================================================================

async def example_simple_integration():
    """
    示例1: 最简单的集成方式

    只需一行代码即可为你的服务添加自动释放功能！
    """
    logger.info("📖 示例1: 最简单的集成方式")
    logger.info("=" * 60)

    # 注册当前服务，60分钟不使用后自动释放
    session = await auto_register_current_process(
        service_type=ServiceType.AGENT,
        service_name="我的AI服务",
        auto_stop=True
    )

    logger.info(f"✅ 服务已注册: {session.service_name}")
    logger.info(f"📍 进程ID: {session.process_id}")
    logger.info("⏰ 空闲超时: 60分钟")
    logger.info(f"💾 初始内存: {session.memory_mb:.1f}MB")

    # 你的服务正常逻辑
    logger.info("🚀 服务正在运行...")

    # 模拟服务运行
    try:
        while True:
            await asyncio.sleep(60)

            # 每次处理请求时，更新活动时间（重要！）
            manager = get_service_session_manager()
            manager.update_activity(session.process_id)

            logger.info("🔄 活动时间已更新，服务继续保持运行")

    except asyncio.CancelledError:
        logger.info("🛑 服务收到停止信号")
    except KeyboardInterrupt:
        logger.info("🛑 用户中断服务")


# =============================================================================
# === 示例2: 自定义超时时间===
# =============================================================================

async def example_custom_timeout():
    """
    示例2: 自定义超时时间

    你可以为不同的服务设置不同的超时时间
    """
    logger.info("📖 示例2: 自定义超时时间")
    logger.info("=" * 60)

    # 注册服务，设置30分钟超时
    session = await auto_register_current_process(
        service_type=ServiceType.CACHE,
        service_name="缓存服务",
        auto_stop=True,
        custom_timeout=30 * 60  # 30分钟
    )

    logger.info(f"✅ 服务已注册: {session.service_name}")
    logger.info("⏰ 自定义超时: 30分钟")

    # 服务运行逻辑
    try:
        while True:
            await asyncio.sleep(60)
            # 更新活动时间
            get_service_session_manager().update_activity(session.process_id)
    except KeyboardInterrupt:
        logger.info("🛑 服务已停止")


# =============================================================================
# === 示例3: 永不停止的核心服务===
# =============================================================================

async def example_never_stop_service():
    """
    示例3: 永不停止的核心服务

    对于核心服务（如Gateway），可以设置为永不停止
    """
    logger.info("📖 示例3: 永不停止的核心服务")
    logger.info("=" * 60)

    # 注册核心服务，设置为永不停止
    session = await auto_register_current_process(
        service_type=ServiceType.GATEWAY,
        service_name="Gateway网关服务",
        auto_stop=False  # 设置为False，永不自动停止
    )

    logger.info(f"✅ 核心服务已注册: {session.service_name}")
    logger.info("🛡️ 自动停止: 关闭（永不停止）")

    # 服务运行逻辑
    try:
        while True:
            await asyncio.sleep(60)
            logger.info("🏰 Gateway服务稳定运行中...")
    except KeyboardInterrupt:
        logger.info("🛑 Gateway服务已停止")


# =============================================================================
# === 示例4: 带活动监控的服务===
# =============================================================================

async def example_with_activity_monitoring():
    """
    示例4: 带活动监控的服务

    演示如何在处理请求时更新活动时间
    """
    logger.info("📖 示例4: 带活动监控的服务")
    logger.info("=" * 60)

    # 注册服务
    session = await auto_register_current_process(
        service_type=ServiceType.API,
        service_name="API主服务",
        auto_stop=True
    )

    manager = get_service_session_manager()

    logger.info(f"✅ 服务已注册: {session.service_name}")

    # 模拟API请求处理
    request_count = 0

    try:
        while True:
            await asyncio.sleep(10)

            # 模拟处理请求
            request_count += 1
            logger.info(f"📨 处理请求 #{request_count}")

            # 每次处理请求后，更新活动时间
            manager.update_activity(session.process_id)

            # 每5次请求显示一次状态
            if request_count % 5 == 0:
                stats = manager.get_stats()
                logger.info(
                    f"📊 服务状态: "
                    f"空闲时间={stats['sessions'][0]['idle_time_seconds']:.1f}秒, "
                    f"内存={stats['sessions'][0]['memory_mb']:.1f}MB"
                )

    except KeyboardInterrupt:
        logger.info("🛑 API服务已停止")


# =============================================================================
# === 示例5: 手动管理会话===
# =============================================================================

async def example_manual_session_management():
    """
    示例5: 手动管理会话

    演示如何手动创建和管理多个服务的会话
    """
    logger.info("📖 示例5: 手动管理会话")
    logger.info("=" * 60)

    # 获取管理器实例
    manager = get_service_session_manager(
        idle_timeout=3600,      # 60分钟超时
        cleanup_interval=300    # 5分钟检查一次
    )

    # 启动监控
    await manager.start_monitoring()

    logger.info("👁️ 会话管理器已启动")

    # 注册多个服务（模拟）
    services = [
        (ServiceType.XIAONUO, "小诺调度中心", False),
        (ServiceType.XIAONA, "小娜法律专家", True),
        (ServiceType.YUNXI, "云熙IP管理", True),
        (ServiceType.CACHE, "缓存服务", True),
        (ServiceType.NLP, "NLP服务", True),
    ]

    import os
    sessions = []

    for service_type, service_name, auto_stop in services:
        # 使用当前PID模拟（实际应该是不同服务的PID）
        session = manager.register_session(
            process_id=os.getpid() + len(sessions),  # 模拟不同PID
            service_type=service_type,
            service_name=service_name,
            auto_stop=auto_stop
        )
        sessions.append(session)
        logger.info(
            f"✅ 已注册: {service_name} "
            f"(自动停止: {'是' if auto_stop else '否'})"
        )

    # 显示统计信息
    stats = manager.get_stats()
    logger.info(f"📊 活动会话数: {stats['active_sessions']}")
    logger.info(f"💾 内存使用: {stats['current_memory_usage_mb']:.1f}MB")

    # 模拟运行一段时间
    logger.info("⏳ 服务运行中...")
    await asyncio.sleep(5)

    # 停止管理器
    await manager.stop_monitoring()
    logger.info("🛑 会话管理器已停止")


# =============================================================================
# === 示例6: 集成到FastAPI服务===
# =============================================================================

from fastapi import FastAPI, Request


async def example_fastapi_integration():
    """
    示例6: 集成到FastAPI服务

    演示如何在FastAPI应用中集成自动释放功能
    """
    logger.info("📖 示例6: 集成到FastAPI服务")
    logger.info("=" * 60)

    # 创建FastAPI应用
    app = FastAPI(title="Athena API with Auto-Release")

    # 注册当前服务
    session = await auto_register_current_process(
        service_type=ServiceType.API,
        service_name="FastAPI主服务",
        auto_stop=True
    )

    manager = get_service_session_manager()

    # 中间件：每个请求都更新活动时间
    @app.middleware("http")
    async def update_activity_middleware(request: Request, call_next):
        """中间件：每个请求都更新活动时间"""
        manager.update_activity(session.process_id)
        response = await call_next(request)
        return response

    @app.get("/")
    async def root():
        """根路径"""
        return {"message": "Athena API服务运行中"}

    @app.get("/health")
    async def health():
        """健康检查"""
        return {"status": "healthy", "service": session.service_name}

    @app.get("/stats")
    async def stats():
        """获取服务统计"""
        return manager.get_stats()

    logger.info("✅ FastAPI应用已配置自动释放功能")
    logger.info("💡 每个请求都会自动更新活动时间")
    logger.info("⏰ 60分钟无请求后服务将自动释放")

    # 注意：实际使用时，需要用 uvicorn 运行
    # uvicorn main:app --host 0.0.0.0 --port 8000


# =============================================================================
# === 使用指南 ===
# =============================================================================

async def show_usage_guide():
    """显示使用指南"""
    guide = """
╔══════════════════════════════════════════════════════════════════════╗
║                   服务自动释放功能使用指南                          ║
╚══════════════════════════════════════════════════════════════════════╝

📖 功能说明
─────────────────────────────────────────────────────────────────────
为你的后台服务添加"60分钟不使用自动释放"功能，节省系统资源。

🚀 快速开始（3步集成）
─────────────────────────────────────────────────────────────────────
1️⃣  在你的服务启动代码中添加：

    from core.session.service_session_manager import auto_register_current_process, ServiceType

    session = await auto_register_current_process(
        service_type=ServiceType.AGENT,
        service_name="你的服务名称",
        auto_stop=True
    )

2️⃣  在处理请求的地方添加活动更新：

    manager = get_service_session_manager()
    manager.update_activity(session.process_id)

3️⃣  完成！你的服务现在具有自动释放功能了。

⚙️  配置选项
─────────────────────────────────────────────────────────────────────
• auto_stop=True        → 启用自动停止（默认）
• auto_stop=False       → 禁用自动停止（核心服务使用）
• custom_timeout=1800   → 自定义超时时间（秒）

📊 服务类型
─────────────────────────────────────────────────────────────────────
• ServiceType.GATEWAY     → Gateway网关服务
• ServiceType.API         → API主服务
• ServiceType.AGENT       → 智能体服务
• ServiceType.XIAONUO     → 小诺调度官
• ServiceType.XIAONA      → 小娜法律专家
• ServiceType.YUNXI       → 云熙IP管理
• ServiceType.XIAOCHEN    → 小宸自媒体
• ServiceType.CACHE       → 缓存服务
• ServiceType.NLP         → NLP服务
• ServiceType.MONITOR     → 监控系统

💡 使用建议
─────────────────────────────────────────────────────────────────────
1. 核心服务（Gateway、小诺）设置 auto_stop=False
2. 业务服务设置 auto_stop=True
3. 在每次处理请求后更新活动时间
4. 定期检查服务状态

🔍 监控命令
─────────────────────────────────────────────────────────────────────
查看所有会话状态：
    manager = get_service_session_manager()
    stats = manager.get_stats()
    print(stats)

查看特定服务：
    sessions = manager.get_sessions_by_service("服务名称")
    for session in sessions:
        print(f"空闲时间: {session.idle_time_seconds}秒")

⚠️  注意事项
─────────────────────────────────────────────────────────────────────
• 确保在处理请求时更新活动时间
• 核心服务建议设置 auto_stop=False
• 测试时可以设置较短的 custom_timeout
• 进程会被 SIGTERM 优雅关闭

📚 更多示例
─────────────────────────────────────────────────────────────────────
运行本文件查看不同场景的集成示例。
"""
    print(guide)


# =============================================================================
# === 主程序 ===
# =============================================================================

async def main():
    """主程序"""
    import sys

    if len(sys.argv) > 1:
        sys.argv[1]
    else:
        # 显示使用指南
        await show_usage_guide()

        print("\n" + "=" * 60)
        print("请选择要运行的示例：")
        print("=" * 60)
        print("1. 最简单的集成方式（推荐）")
        print("2. 自定义超时时间")
        print("3. 永不停止的核心服务")
        print("4. 带活动监控的服务")
        print("5. 手动管理会话")
        print("6. 集成到FastAPI服务")
        print("0. 显示使用指南")
        print("=" * 60)

        choice = input("\n请输入选项 (0-6): ").strip()

        examples = {
            "1": example_simple_integration,
            "2": example_custom_timeout,
            "3": example_never_stop_service,
            "4": example_with_activity_monitoring,
            "5": example_manual_session_management,
            "6": example_fastapi_integration,
            "0": show_usage_guide,
        }

        example_func = examples.get(choice, show_usage_guide)

    # 运行示例
    try:
        if asyncio.iscoroutinefunction(example_func):
            await example_func()
        else:
            await example_func()
    except KeyboardInterrupt:
        logger.info("\n👋 程序已退出")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 程序已退出")
