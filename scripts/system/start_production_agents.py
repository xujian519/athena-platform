#!/usr/bin/env python3
"""
Athena生产环境统一启动脚本
Production Unified Startup Script

启动核心服务：小诺(调度官) + 小娜(法律专家)
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'production_agents.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProductionAgentManager:
    """生产环境智能体管理器"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.agents = {}
        self.running = True

    async def check_infrastructure(self) -> dict:
        """检查基础设施状态"""
        logger.info("=" * 60)
        logger.info("🔍 检查基础设施状态...")
        logger.info("=" * 60)

        checks = {
            "gateway": self._check_gateway(),
            "redis": self._check_redis(),
            "qdrant": self._check_qdrant(),
            "neo4j": self._check_neo4j(),
        }

        results = {}
        for name, check in checks.items():
            try:
                results[name] = await check
                status = "✅" if results[name] else "❌"
                logger.info(f"  {status} {name}")
            except Exception as e:
                results[name] = False
                logger.error(f"  ❌ {name}: {e}")

        healthy = sum(1 for v in results.values() if v)
        total = len(results)
        logger.info(f"📊 基础设施状态: {healthy}/{total} 健康")

        return results

    async def _check_gateway(self) -> bool:
        """检查Gateway"""
        import requests
        try:
            response = requests.get("http://localhost:8005/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    async def _check_redis(self) -> bool:
        """检查Redis"""
        try:
            import os

            import redis
            # 从环境变量获取密码，默认使用docker-compose中的配置
            redis_password = os.getenv('REDIS_PASSWORD', 'redis123')
            client = redis.Redis(
                host='localhost',
                port=6379,
                password=redis_password,
                decode_responses=True
            )
            return client.ping()
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}")
            return False

    async def _check_qdrant(self) -> bool:
        """检查Qdrant"""
        import requests
        try:
            response = requests.get("http://localhost:6333", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    async def _check_neo4j(self) -> bool:
        """检查Neo4j"""
        import requests
        try:
            response = requests.get("http://localhost:7474", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    async def start_xiaonuo(self):
        """启动小诺协调器"""
        logger.info("=" * 60)
        logger.info("💠 启动小诺·双鱼公主...")
        logger.info("=" * 60)

        try:
            from core.framework.agents.xiaonuo_coordinator import XiaonuoAgent

            config = {
                'agent_id': 'xiaonuo-pisces-production',
                'name': '小诺·双鱼公主',
                'role': '平台协调官',
                'enable_planning': True,
                'enable_memory': True,
                'llm_provider': 'anthropic',
                'llm_model': 'claude-3-5-sonnet-20241022'
            }

            agent = XiaonuoAgent(config)
            await agent.initialize()

            self.agents['xiaonuo'] = agent
            logger.info(f"✅ 小诺已启动 (ID: {config['agent_id']})")
            logger.info(f"📋 角色: {config['role']}")

            return True
        except Exception as e:
            logger.error(f"❌ 小诺启动失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def start_xiaona(self):
        """启动小娜法律专家"""
        logger.info("=" * 60)
        logger.info("⚖️ 启动小娜·天秤女神...")
        logger.info("=" * 60)

        try:
            from core.framework.agents.xiaona_professional import XiaonaProfessionalAgent

            config = {
                "llm_provider": "anthropic",
                "llm_model": "claude-3-5-sonnet-20241022",
            }

            agent = XiaonaProfessionalAgent(config=config)
            await agent.initialize()

            self.agents['xiaona'] = agent
            logger.info("✅ 小娜已启动")
            logger.info("📋 角色: 法律专家")

            return True
        except Exception as e:
            logger.error(f"❌ 小娜启动失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def run(self):
        """运行智能体"""
        logger.info("=" * 60)
        logger.info("🚀 Athena生产环境启动")
        logger.info(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        # 1. 检查基础设施
        infra_status = await self.check_infrastructure()
        if not all(infra_status.values()):
            logger.warning("⚠️ 部分基础设施不健康，但继续启动智能体...")

        # 2. 启动小诺
        xiaonuo_ok = await self.start_xiaonuo()

        # 3. 启动小娜
        xiaona_ok = await self.start_xiaona()

        # 4. 启动汇总
        logger.info("=" * 60)
        logger.info("📊 启动汇总")
        logger.info("=" * 60)
        logger.info(f"  小诺·双鱼公主: {'✅ 运行中' if xiaonuo_ok else '❌ 失败'}")
        logger.info(f"  小娜·天秤女神: {'✅ 运行中' if xiaona_ok else '❌ 失败'}")
        logger.info("=" * 60)

        if xiaonuo_ok and xiaona_ok:
            logger.info("🎉 所有智能体启动成功！")
        else:
            logger.warning("⚠️ 部分智能体启动失败")

        # 5. 保持运行
        logger.info("🔄 智能体运行中，按 Ctrl+C 退出...")
        try:
            while self.running:
                await asyncio.sleep(60)
                logger.info("💓 智能体心跳正常")
        except KeyboardInterrupt:
            logger.info("\n👋 正在关闭智能体...")
            await self.shutdown()

    async def shutdown(self):
        """关闭智能体"""
        self.running = False

        for name, agent in self.agents.items():
            try:
                if hasattr(agent, 'shutdown'):
                    await agent.shutdown()
                logger.info(f"✅ {name} 已关闭")
            except Exception as e:
                logger.error(f"❌ {name} 关闭失败: {e}")

        logger.info("👋 所有智能体已关闭")


async def main():
    """主函数"""
    manager = ProductionAgentManager()
    await manager.run()


if __name__ == "__main__":
    asyncio.run(main())
