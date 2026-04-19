#!/usr/bin/env python3
"""
Google Scholar 搜索服务
Google Scholar Search Production Service

生产环境服务 - 提供Google Scholar学术搜索能力

作者: 小诺·双鱼公主 (Xiaonuo Pisces Princess)
版本: v1.0.0
创建: 2025-12-31
"""

from __future__ import annotations
import asyncio
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 设置路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScholarSearchService:
    """
    Google Scholar 搜索生产服务

    功能:
    • 持续运行的学术搜索服务
    • 健康检查和监控
    • 优雅关闭
    • 统计信息报告
    """

    def __init__(self):
        self.running = False
        self.start_time = datetime.now()
        self.serper_manager = None
        self.search_count = 0
        self.cache_hits = 0

        # 加载配置
        self.api_key = os.getenv('SERPER_API_KEY')

        if not self.api_key:
            raise ValueError(
                "未设置 SERPER_API_KEY 环境变量！\n"
                "请设置: export SERPER_API_KEY='your_api_key'"
            )

        logger.info("🔧 Scholar搜索服务初始化中...")
        logger.info(f"   API密钥: {self.api_key[:10]}...{self.api_key[-6:]}")

    async def initialize(self):
        """初始化服务"""
        try:
            from core.search.external.serper_api_manager import SerperAPIManager, SerperConfig

            # 创建Serper管理器
            config = SerperConfig(
                api_key=self.api_key,
                enable_cache=True,
                cache_ttl_seconds=86400
            )

            self.serper_manager = SerperAPIManager(config)
            await self.serper_manager.initialize()

            logger.info("✅ Serper API管理器初始化完成")

            # 测试连接
            from core.search.external.serper_api_manager import (
                SerperSearchRequest,
                SerperSearchType,
            )

            test_request = SerperSearchRequest(
                query="artificial intelligence",
                search_type=SerperSearchType.SCHOLAR,
                num_results=1
            )

            result = await self.serper_manager.search(test_request)

            if result.success:
                logger.info("✅ API连接测试成功")
            else:
                logger.warning(f"⚠️  API测试: {result.error_message}")

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            raise

    async def start(self):
        """启动服务"""
        self.running = True
        self.start_time = datetime.now()

        print()
        print("=" * 70)
        print("🎓 Google Scholar 搜索服务")
        print("=" * 70)
        print(f"📅 启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔑 API密钥: {self.api_key[:10]}...{self.api_key[-6:]}")
        print("💾 剩余信用点: ~2490")
        print("=" * 70)
        print()

        logger.info("🚀 Scholar搜索服务已启动")

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            # 初始化
            await self.initialize()

            # 服务主循环
            while self.running:
                try:
                    await self.service_loop()
                    await asyncio.sleep(30)  # 30秒健康检查间隔
                except Exception as e:
                    logger.error(f"服务循环错误: {e}")
                    await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"服务启动失败: {e}")
            raise

        finally:
            await self.shutdown()

    async def service_loop(self):
        """服务主循环 - 定期健康检查"""
        # 定期报告统计信息
        if self.serper_manager:
            stats = self.serper_manager.get_statistics()

            logger.info("📊 服务统计:")
            logger.info(f"   总请求: {stats['total_requests']}")
            logger.info(f"   成功: {stats['successful_requests']}")
            logger.info(f"   缓存: {stats['cache_size']}")
            logger.info(f"   剩余信用点: ~{stats['remaining_budget']}")
            logger.info(f"   运行时间: {self._get_uptime()}")

    async def search(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "scholar"
    ) -> dict[str, Any]:
        """
        执行搜索

        Args:
            query: 搜索关键词
            max_results: 最大结果数
            search_type: 搜索类型 (scholar/patents/search)

        Returns:
            搜索结果
        """
        if not self.serper_manager:
            return {
                "success": False,
                "error": "服务未初始化"
            }

        self.search_count += 1

        from core.search.external.serper_api_manager import SerperSearchRequest, SerperSearchType

        # 映射搜索类型
        type_map = {
            "scholar": SerperSearchType.SCHOLAR,
            "patents": SerperSearchType.PATENTS,
            "search": SerperSearchType.SEARCH
        }

        serper_type = type_map.get(search_type, SerperSearchType.SCHOLAR)

        request = SerperSearchRequest(
            query=query,
            search_type=serper_type,
            num_results=max_results
        )

        result = await self.serper_manager.search(request)

        if hasattr(self.serper_manager, '_get_from_cache'):
            cached = self.serper_manager._get_from_cache(request)
            if cached:
                self.cache_hits += 1

        return {
            "success": result.success,
            "query": result.query,
            "total_results": result.total_results,
            "results": result.results,
            "search_time": result.search_time,
            "api_credits": result.api_credits_used
        }

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        try:
            if not self.serper_manager:
                return {
                    "status": "unhealthy",
                    "reason": "Serper管理器未初始化"
                }

            stats = self.serper_manager.get_statistics()

            return {
                "status": "healthy",
                "uptime": self._get_uptime(),
                "total_searches": self.search_count,
                "cache_hits": self.cache_hits,
                "cache_hit_rate": f"{(self.cache_hits/max(self.search_count,1)*100):.1f}%",
                "serper_stats": stats,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def shutdown(self):
        """关闭服务"""
        logger.info("🛑 正在关闭服务...")

        if self.serper_manager:
            await self.serper_manager.close()

        # 最终统计
        print()
        print("=" * 70)
        print("📊 服务关闭统计")
        print("=" * 70)
        print(f"⏱️  运行时长: {self._get_uptime()}")
        print(f"🔍 总搜索次数: {self.search_count}")
        print(f"💾 缓存命中: {self.cache_hits}")

        if self.serper_manager:
            stats = self.serper_manager.get_statistics()
            print("📊 API统计:")
            print(f"   总请求: {stats['total_requests']}")
            print(f"   成功: {stats['successful_requests']}")
            print(f"   失败: {stats['failed_requests']}")
            print(f"   信用点使用: {stats['total_credits_used']}")
            print(f"   剩余信用点: ~{stats['remaining_budget']}")

        print("=" * 70)
        print()
        print("👋 Scholar搜索服务已关闭")
        print()

    def _get_uptime(self) -> str:
        """获取运行时间"""
        delta = datetime.now() - self.start_time
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        return f"{hours}小时{minutes}分钟"

    def _signal_handler(self, signum, frame) -> None:
        """信号处理器"""
        logger.info(f"收到信号 {signum}，准备关闭...")
        self.running = False


# === 快速启动函数 ===

async def quick_start():
    """快速启动 - 用于测试"""
    service = ScholarSearchService()

    try:
        # 初始化并执行一次搜索
        await service.initialize()

        print("🔍 执行测试搜索...")
        result = await service.search(
            query="machine learning",
            max_results=3
        )

        print(f"✅ 搜索完成: 找到 {result['total_results']} 个结果")
        print(f"   耗时: {result['search_time']:.2f}秒")

        # 显示前3个结果
        if result['results']:
            print("\n前3个结果:")
            for i, r in enumerate(result['results'][:3], 1):
                print(f"{i}. {r.get('title', 'N/A')[:60]}...")

        # 健康检查
        health = await service.health_check()
        print(f"\n健康状态: {health['status']}")

    except Exception as e:
        print(f"❌ 错误: {e}")

    finally:
        if service.serper_manager:
            await service.serper_manager.close()


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║        🎓 Google Scholar 搜索服务 - Athena工作平台               ║
║                                                                   ║
║        作者: 小诺·双鱼公主 (Xiaonuo Pisces Princess)            ║
║        版本: v1.0.0                                               ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    import argparse

    parser = argparse.ArgumentParser(description='Google Scholar搜索服务')
    parser.add_argument(
        '--mode',
        choices=['service', 'test'],
        default='service',
        help='运行模式: service(持续服务) 或 test(快速测试)'
    )

    args = parser.parse_args()

    if args.mode == 'test':
        print("🧪 运行测试模式...\n")
        asyncio.run(quick_start())
    else:
        print("🚀 启动生产服务...\n")
        service = ScholarSearchService()
        asyncio.run(service.start())
