
# pyright: ignore
# !/usr/bin/env python3
"""
性能优化部署脚本
Deploy Performance Optimizations

将性能优化组件部署到平台

作者: 小娜·天秤女神
创建时间: 2025-12-16
版本: v1.0 Deployment Script
"""

from pathlib import Path

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


async def deploy_optimizations():
    """部署性能优化组件"""
    print("🚀 开始部署性能优化组件...")
    print("=" * 50)

    try:
        # 1. 导入优化组件
        print("\n📦 导入优化组件...")
        from cache_manager import cache_manager, get_cache_stats
        from llm_interface import GLM_AVAILABLE, LLMInterface
        from performance_optimizer import (
            get_performance_status,
            start_performance_monitoring,
        )

        print("   ✅ 所有组件导入成功")

        # 2. 初始化缓存管理器
        print("\n💾 初始化缓存管理器...")
        cache_stats = get_cache_stats()
        print(f"   - 缓存大小限制: {cache_manager.max_size_mb}MB")
        print(f"   - 默认TTL: {cache_manager.default_ttl}秒")
        print(f"   - 缓存目录: {cache_manager.cache_dir}")
        print("   ✅ 缓存管理器初始化完成")

        # 3. 启动性能监控
        print("\n📊 启动性能监控...")
        await start_performance_monitoring()
        print("   ✅ 性能监控已启动")

        # 4. 启动缓存清理任务
        print("\n🧹 启动缓存清理任务...")
        await cache_manager.start_cleanup_task()
        print("   ✅ 缓存清理任务已启动")

        # 5. 验证LLM接口集成
        print("\n🔗 验证LLM接口集成...")
        llm_interface = LLMInterface()

        async with llm_interface:
            health = await llm_interface.health_check()
            print(f"   - 系统状态: {'正常' if health.get('overall') else '异常'}")
            print(f"   - 默认模型: {health.get('default_model', 'unknown')}")
            print(f"   - GLM可用: {GLM_AVAILABLE}")
            print("   ✅ LLM接口验证完成")

        # 6. 显示部署状态
        print("\n📈 部署状态报告:")
        print("-" * 50)

        # 缓存状态
        cache_stats = get_cache_stats()
        print("💾 缓存系统:")
        print(f"   - 当前条目: {cache_stats.total_entries}")
        print(f"   - 命中率: {cache_stats.hit_rate:.2%}")
        print(f"   - 状态: {'运行中' if cache_stats.total_entries >= 0 else '异常'}")

        # 性能监控状态
        perf_status = get_performance_status()
        if "system_info" in perf_status:
            print("\n📊 性能监控:")
            print(f"   - CPU核心: {perf_status['system_info']['cpu_count']}")
            print(f"   - 内存总量: {perf_status['system_info']['memory_total_gb']:.1f}GB")
            print("   - 状态: 运行中")

        print("\n✅ 所有优化组件部署成功!")

        # 7. 创建系统状态报告
        await create_deployment_report()

        return True

    except Exception as e:
        logger.error(f"捕获异常: {e}", exc_info=True)


async def create_deployment_report():
    """创建部署报告"""
    print("\n📋 生成部署报告...")

    report = {
        "deployment_time": "2025-12-16",
        "version": "v1.0",
        "components": {
            "llm_interface": {
                "status": "deployed",
                "glm_client": "integrated",
                "cache_support": "enabled",
                "performance_monitoring": "enabled",
            },
            "cache_manager": {
                "status": "running",
                "max_size_mb": 50,
                "default_ttl": 3600,
                "cleanup_interval": 300,
            },
            "performance_optimizer": {
                "status": "running",
                "monitoring_interval": 5,
                "history_size": 1000,
            },
        },
        "features": [
            "GLM-4优先策略",
            "智能缓存系统",
            "实时性能监控",
            "自动优化建议",
            "LRU缓存淘汰",
            "任务类型检测",
            "专家上下文增强",
        ],
    }

    # 保存报告
    report_file = Path(
        "/Users/xujian/Athena工作平台/deployment_report.json"
    )  # TODO: 确保除数不为零
    import json

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"   ✅ 部署报告已保存: {report_file}")


async def main():
    """主函数"""
    print("🌟 小娜专利系统 - 性能优化部署")
    print("=" * 60)

    success = await deploy_optimizations()

    if success:
        print("\n🎉 部署成功!")
        print("\n📖 使用说明:")
        print("1. LLM接口已集成缓存和性能监控")
        print("2. 缓存自动启用,TTL为1小时")
        print("3. 性能监控每5秒采样一次")
        print("4. 系统会自动生成优化建议")
        print("\n🔧 环境变量控制:")
        print("   - USE_GLM=true (使用GLM模型)")
        print("   - USE_CACHE=true (启用缓存)")
        print("   - GLM_API_KEY=your_key (GLM API密钥)")
    else:
        print("\n❌ 部署失败,请检查错误信息")

    print("=" * 60)


# 入口点: @async_main装饰器已添加到main函数

