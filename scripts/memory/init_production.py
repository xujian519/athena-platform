#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena记忆模块 - 生产环境初始化脚本
Production Environment Initialization Script

此脚本用于初始化记忆系统的生产环境，包括：
1. 验证配置
2. 连接真实数据库
3. 初始化表结构
4. 验证服务可用性

使用方法:
    # 从默认环境变量初始化
    python scripts/memory/init_production.py

    # 从指定配置文件初始化
    python scripts/memory/init_production.py --config /path/to/config.env

    # 仅验证配置，不初始化
    python scripts/memory/init_production.py --validate-only

作者: Athena平台团队
创建时间: 2026-01-24
版本: 1.0.0
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.memory.config import load_production_config, MemorySystemConfig
from core.memory.unified_agent_memory_system import UnifiedAgentMemorySystem

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('init_production.log')
    ]
)
logger = logging.getLogger(__name__)


class ProductionInitializer:
    """生产环境初始化器"""

    def __init__(self, config: MemorySystemConfig):
        """
        初始化生产环境初始化器

        Args:
            config: 记忆系统配置
        """
        self.config = config
        self.system = None

    async def validate_services(self) -> bool:
        """
        验证所有服务是否可用

        Returns:
            所有服务是否都可用
        """
        logger.info("\n" + "=" * 50)
        logger.info("🔍 开始验证服务可用性...")
        logger.info("=" * 50)

        all_available = True

        # 验证PostgreSQL
        logger.info("\n📊 验证PostgreSQL...")
        try:
            import asyncpg
            conn = await asyncio.wait_for(
                asyncpg.connect(
                    host=self.config.postgresql.host,
                    port=self.config.postgresql.port,
                    database=self.config.postgresql.database,
                    user=self.config.postgresql.user,
                    password=self.config.postgresql.password
                ),
                timeout=10
            )
            version = await conn.fetchval('SELECT version()')
            logger.info(f"✅ PostgreSQL连接成功")
            logger.info(f"   版本: {version.split()[1]}")

            # 检查pgvector扩展
            has_pgvector = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'pgvector')"
            )
            if has_pgvector:
                logger.info("✅ pgvector扩展已安装")
            else:
                logger.warning("⚠️ pgvector扩展未安装，向量搜索功能将不可用")
                logger.warning("   请运行: CREATE EXTENSION pgvector;")

            await conn.close()

        except Exception as e:
            logger.error(f"❌ PostgreSQL连接失败: {e}")
            all_available = False

        # 验证Redis
        logger.info("\n🔴 验证Redis...")
        try:
            import aioredis
            redis_url = self.config.redis.get_url()
            redis_client = await aioredis.from_url(
                redis_url,
                socket_connect_timeout=5,
                socket_timeout=5
            )

            # 检查ping是否为async
            import asyncio
            if asyncio.iscoroutinefunction(redis_client.ping):
                await redis_client.ping()
            else:
                redis_client.ping()

            logger.info(f"✅ Redis连接成功")
            logger.info(f"   主机: {self.config.redis.host}:{self.config.redis.port}")

            await redis_client.close()

        except Exception as e:
            logger.warning(f"⚠️ Redis连接失败: {e}")
            logger.warning("   系统将降级运行，不使用缓存功能")

        # 验证Qdrant
        logger.info("\n🔷 验证Qdrant...")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.qdrant.get_url()}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"✅ Qdrant连接成功")
                        logger.info(f"   主机: {self.config.qdrant.host}:{self.config.qdrant.port}")
                    else:
                        logger.warning(f"⚠️ Qdrant状态异常: {resp.status}")

        except Exception as e:
            logger.warning(f"⚠️ Qdrant连接失败: {e}")
            logger.warning("   向量搜索功能将不可用")

        return all_available

    async def initialize_system(self) -> bool:
        """
        初始化记忆系统

        Returns:
            是否成功初始化
        """
        logger.info("\n" + "=" * 50)
        logger.info("🚀 开始初始化Athena记忆系统...")
        logger.info("=" * 50)

        try:
            # 创建记忆系统实例
            self.system = UnifiedAgentMemorySystem()

            # 使用生产配置
            self.system.db_config = self.config.to_db_config()

            # 初始化系统
            await self.system.initialize()

            logger.info("\n✅ 记忆系统初始化成功！")
            logger.info(f"   系统名称: {self.system.system_name}")
            logger.info(f"   版本: {self.system.version}")
            logger.info(f"   注册智能体数: {len(self.system.__class__.__dict__)}")

            return True

        except Exception as e:
            logger.error(f"\n❌ 记忆系统初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_basic_operations(self) -> bool:
        """
        测试基本操作

        Returns:
            测试是否通过
        """
        if not self.system:
            logger.error("❌ 系统未初始化，无法测试")
            return False

        logger.info("\n" + "=" * 50)
        logger.info("🧪 开始测试基本操作...")
        logger.info("=" * 50)

        try:
            from core.memory.unified_agent_memory_system import AgentType, MemoryType, MemoryTier

            # 测试1: 存储记忆
            logger.info("\n📝 测试1: 存储记忆...")
            memory_id = await self.system.store_memory(
                agent_id="test_agent",
                agent_type=AgentType.ATHENA,
                content="这是一条测试记忆，用于验证生产环境配置是否正确。",
                memory_type=MemoryType.CONVERSATION,
                importance=0.8,
                tier=MemoryTier.HOT
            )
            logger.info(f"✅ 记忆存储成功，ID: {memory_id}")

            # 测试2: 回忆记忆
            logger.info("\n🔍 测试2: 回忆记忆...")
            memories = await self.system.recall_memory(
                agent_id="test_agent",
                query="测试",
                limit=5
            )
            logger.info(f"✅ 找到 {len(memories)} 条相关记忆")

            # 测试3: 获取统计信息
            logger.info("\n📊 测试3: 获取统计信息...")
            stats = await self.system.get_agent_stats("test_agent")
            logger.info(f"✅ 统计信息: {stats}")

            logger.info("\n✅ 所有基本操作测试通过！")
            return True

        except Exception as e:
            logger.error(f"\n❌ 基本操作测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def cleanup(self):
        """清理资源"""
        if self.system:
            logger.info("\n🔄 清理资源...")
            try:
                await self.system.close()
                logger.info("✅ 资源清理完成")
            except Exception as e:
                logger.warning(f"⚠️ 资源清理时出现错误: {e}")

    async def run(self, validate_only: bool = False) -> bool:
        """
        运行完整的初始化流程

        Args:
            validate_only: 是否仅验证配置

        Returns:
            是否成功
        """
        try:
            # 验证配置
            if not self.config.validate():
                logger.error("❌ 配置验证失败")
                return False

            # 验证服务可用性
            services_ok = await self.validate_services()
            if not services_ok:
                logger.warning("⚠️ 部分服务不可用，但系统可能仍能运行")

            # 如果仅验证，到此为止
            if validate_only:
                logger.info("\n✅ 配置验证完成")
                return True

            # 初始化系统
            if not await self.initialize_system():
                return False

            # 测试基本操作
            if not await self.test_basic_operations():
                return False

            logger.info("\n" + "=" * 50)
            logger.info("🎉 生产环境初始化完成！")
            logger.info("=" * 50)
            logger.info("\n下一步:")
            logger.info("1. 记忆系统已准备就绪，可以开始使用")
            logger.info("2. 如果需要创建定期备份，请设置备份脚本")
            logger.info("3. 如果需要监控，请配置Prometheus/Grafana")
            logger.info("4. 查看日志: tail -f init_production.log")

            return True

        except Exception as e:
            logger.error(f"\n❌ 初始化过程失败: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            await self.cleanup()


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Athena记忆模块 - 生产环境初始化脚本'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径 (.env文件)'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='仅验证配置，不初始化系统'
    )

    args = parser.parse_args()

    # 加载配置
    logger.info("📋 加载生产环境配置...")
    config = load_production_config(args.config)

    # 创建初始化器并运行
    initializer = ProductionInitializer(config)
    success = await initializer.run(validate_only=args.validate_only)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
