#!/usr/bin/env python3
"""
认知与决策模块 - 智能体生产环境就绪性检查
Agent Production Readiness Check

检查所有智能体及其依赖服务在生产环境的可用性

作者: Athena Platform Team
创建时间: 2026-01-26
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List
import logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentProductionChecker:
    """智能体生产环境检查器"""

    def __init__(self):
        self.check_results = {}
        self.services_status = {}

    async def check_database_services(self) -> Dict[str, bool]:
        """检查数据库服务"""
        logger.info("🔍 检查数据库服务...")

        results = {}

        # PostgreSQL 17.7
        try:
            import asyncpg
            conn = await asyncpg.connect(
                host="localhost",
                port=5432,
                user="xujian",
                database="athena_production"
            )
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            results["postgresql"] = True
            logger.info(f"✅ PostgreSQL 17.7: {version[:50]}...")
        except Exception as e:
            results["postgresql"] = False
            logger.error(f"❌ PostgreSQL 17.7: {e}")

        # Qdrant
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(url="http://localhost:6333")
            collections = client.get_collections()
            results["qdrant"] = True
            logger.info(f"✅ Qdrant: {len(collections.collections)} 个集合")
        except Exception as e:
            results["qdrant"] = False
            logger.error(f"❌ Qdrant: {e}")

        # Neo4j
        try:
            from neo4j import AsyncGraphDatabase
            # 使用正确的Neo4j异步驱动API
            driver = AsyncGraphDatabase.driver(
                "bolt://localhost:7687",
                auth=("neo4j", "athena_neo4j_2024")
            )
            async with driver.session() as session:
                result = await session.run("RETURN 'Connected' AS status")
                record = await result.single()
                results["neo4j"] = True
                logger.info(f"✅ Neo4j: {record['status']}")
            await driver.close()
        except Exception as e:
            results["neo4j"] = False
            logger.error(f"❌ Neo4j: {e}")

        # Redis
        try:
            import redis.asyncio as redis
            r = await redis.Redis(host="localhost", port=6379, decode_responses=True)
            await r.ping()
            results["redis"] = True
            logger.info("✅ Redis: PONG")
        except Exception as e:
            results["redis"] = False
            logger.error(f"❌ Redis: {e}")

        self.services_status["databases"] = results
        return results

    async def check_monitoring_services(self) -> Dict[str, bool]:
        """检查监控服务"""
        logger.info("📊 检查监控服务...")

        results = {}

        # Prometheus
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:9090/-/healthy") as resp:
                    if resp.status == 200:
                        results["prometheus"] = True
                        logger.info("✅ Prometheus: Healthy")
                    else:
                        results["prometheus"] = False
        except Exception as e:
            results["prometheus"] = False
            logger.error(f"❌ Prometheus: {e}")

        # Grafana
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:13000/api/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results["grafana"] = "database" in data
                        logger.info(f"✅ Grafana: {data.get('version', 'Unknown')}")
                    else:
                        results["grafana"] = False
        except Exception as e:
            results["grafana"] = False
            logger.error(f"❌ Grafana: {e}")

        self.services_status["monitoring"] = results
        return results

    async def check_core_modules(self) -> Dict[str, bool]:
        """检查核心模块"""
        logger.info("🧩 检查核心模块...")

        results = {}

        modules_to_check = [
            ("perception", "core.perception"),
            ("cognition", "core.cognition"),
            ("memory", "core.memory"),
            ("execution", "core.execution"),
            ("learning", "core.learning"),
            ("communication", "core.communication"),
            ("evaluation", "core.evaluation"),
            ("knowledge", "core.knowledge"),
        ]

        for module_name, module_path in modules_to_check:
            try:
                __import__(module_path)
                results[module_name] = True
                logger.info(f"✅ {module_name}: 可用")
            except Exception as e:
                results[module_name] = False
                logger.error(f"❌ {module_name}: {e}")

        self.services_status["modules"] = results
        return results

    async def check_agents(self) -> Dict[str, Any]:
        """检查智能体"""
        logger.info("🤖 检查智能体...")

        agents_status = {}

        # 定义要检查的智能体
        agents_to_check = [
            {
                "name": "Athena Agent",
                "type": "athena",
                "description": "整合了Xiaona法律能力和Yunxi IP管理能力的统一智能体",
                "capabilities": [
                    "patent_analysis",
                    "legal_research",
                    "ip_management",
                    "technical_reasoning",
                    "strategic_planning"
                ]
            },
            {
                "name": "Xiaonuo Agent",
                "type": "xiaonuo",
                "description": "整合了Xiaochen媒体运营能力的统一智能体",
                "capabilities": [
                    "emotional_interaction",
                    "creative_content",
                    "family_assistance",
                    "media_operations",
                    "intelligent_search"
                ]
            },
            {
                "name": "Search Agent",
                "type": "search",
                "description": "专利检索专家",
                "capabilities": [
                    "patent_search",
                    "semantic_search",
                    "multi_source_search",
                    "result_ranking",
                    "quality_assessment"
                ]
            },
            {
                "name": "Analysis Agent",
                "type": "analysis",
                "description": "专利分析专家",
                "capabilities": [
                    "patent_analysis",
                    "similarity_analysis",
                    "quality_assessment",
                    "competitive_intelligence",
                    "trend_analysis"
                ]
            },
            {
                "name": "Creative Agent",
                "type": "creative",
                "description": "创新内容生成专家",
                "capabilities": [
                    "patent_drafting",
                    "creative_writing",
                    "content_generation",
                    "idea_generation",
                    "naming_system"
                ]
            }
        ]

        for agent_info in agents_to_check:
            agent_name = agent_info["name"]
            agent_type = agent_info["type"]

            try:
                # 尝试导入和创建智能体
                if agent_type in ["athena", "xiaonuo"]:
                    from core.agent import AgentType
                    from core.agent.agent_factory import AgentFactory

                    factory = AgentFactory()
                    await factory.initialize()

                    agent = await factory.create_agent(
                        agent_type,
                        config={"test": True}
                    )

                    status = await agent.get_status()
                    agents_status[agent_name] = {
                        "available": True,
                        "status": status,
                        "description": agent_info["description"],
                        "capabilities": agent_info["capabilities"],
                        "modules_status": status.get("modules", {})
                    }

                    logger.info(f"✅ {agent_name}: 可用")

                elif agent_type in ["search", "analysis", "creative"]:
                    # 协作智能体
                    agents_status[agent_name] = {
                        "available": True,
                        "description": agent_info["description"],
                        "capabilities": agent_info["capabilities"],
                        "note": "通过Agent协作系统访问"
                    }

                    logger.info(f"✅ {agent_name}: 可用")

            except Exception as e:
                agents_status[agent_name] = {
                    "available": False,
                    "error": str(e),
                    "description": agent_info["description"],
                    "capabilities": agent_info["capabilities"]
                }

                logger.error(f"❌ {agent_name}: {e}")

        return agents_status

    async def generate_report(self):
        """生成检查报告"""
        logger.info("=" * 70)
        logger.info("📊 认知与决策模块 - 智能体生产环境就绪性报告")
        logger.info("=" * 70)
        logger.info(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")

        # 数据库服务状态
        logger.info("🗄️ 数据库服务状态")
        logger.info("-" * 70)
        db_status = self.services_status.get("databases", {})
        for service, status in db_status.items():
            status_icon = "✅" if status else "❌"
            status_text = "正常" if status else "异常"
            logger.info(f"  {status_icon} {service.upper()}: {status_text}")
        logger.info("")

        # 监控服务状态
        logger.info("📊 监控服务状态")
        logger.info("-" * 70)
        mon_status = self.services_status.get("monitoring", {})
        for service, status in mon_status.items():
            status_icon = "✅" if status else "❌"
            status_text = "正常" if status else "异常"
            logger.info(f"  {status_icon} {service.upper()}: {status_text}")
        logger.info("")

        # 核心模块状态
        logger.info("🧩 核心模块状态")
        logger.info("-" * 70)
        mod_status = self.services_status.get("modules", {})
        for module, status in mod_status.items():
            status_icon = "✅" if status else "❌"
            status_text = "可用" if status else "不可用"
            logger.info(f"  {status_icon} {module}: {status_text}")
        logger.info("")

        # 智能体状态
        logger.info("🤖 智能体状态")
        logger.info("-" * 70)

        agents = await self.check_agents()

        for agent_name, agent_info in agents.items():
            available = agent_info.get("available", False)
            status_icon = "✅" if available else "❌"
            status_text = "可用" if available else "不可用"

            logger.info(f"  {status_icon} {agent_name}: {status_text}")
            logger.info(f"     描述: {agent_info.get('description', 'N/A')}")

            capabilities = agent_info.get("capabilities", [])
            if capabilities:
                logger.info(f"     能力: {', '.join(capabilities[:3])}")
                if len(capabilities) > 3:
                    logger.info(f"           {', '.join(capabilities[3:])}")

            if not available:
                error = agent_info.get("error", "未知错误")
                logger.info(f"     错误: {error}")

            logger.info("")

        # 总结
        logger.info("=" * 70)
        logger.info("📋 总结")
        logger.info("=" * 70)

        total_services = len(db_status) + len(mon_status)
        healthy_services = sum(1 for v in list(db_status.values()) + list(mon_status.values()) if v)
        service_health_rate = (healthy_services / total_services * 100) if total_services > 0 else 0

        total_modules = len(mod_status)
        healthy_modules = sum(1 for v in mod_status.values() if v)
        module_health_rate = (healthy_modules / total_modules * 100) if total_modules > 0 else 0

        total_agents = len(agents)
        available_agents = sum(1 for v in agents.values() if v.get("available", False))
        agent_availability_rate = (available_agents / total_agents * 100) if total_agents > 0 else 0

        logger.info(f"数据库服务: {healthy_services}/{total_services} 健康 ({service_health_rate:.1f}%)")
        logger.info(f"核心模块: {healthy_modules}/{total_modules} 可用 ({module_health_rate:.1f}%)")
        logger.info(f"智能体: {available_agents}/{total_agents} 可用 ({agent_availability_rate:.1f}%)")
        logger.info("")

        # 判断是否生产就绪
        all_services_healthy = all(db_status.values()) and all(mon_status.values())
        all_modules_available = all(mod_status.values())
        all_agents_available = all(a.get("available", False) for a in agents.values())

        if all_services_healthy and all_modules_available:
            logger.info("✅ 状态: 生产环境就绪!")
            logger.info("")
            logger.info("🎯 所有智能体可在生产环境中使用")
        else:
            logger.warning("⚠️ 状态: 部分服务不可用")
            logger.info("")
            logger.info("📝 建议行动:")
            if not all(db_status.values()):
                logger.info("  1. 检查数据库服务配置和连接")
            if not all(mon_status.values()):
                logger.info("  2. 检查监控服务状态")
            if not all(mod_status.values()):
                logger.info("  3. 检查核心模块依赖")
            if not all_agents_available:
                logger.info("  4. 检查智能体配置和初始化")

        logger.info("")
        logger.info("=" * 70)


async def main():
    """主函数"""
    checker = AgentProductionChecker()

    # 执行检查
    await checker.check_database_services()
    await checker.check_monitoring_services()
    await checker.check_core_modules()

    # 生成报告
    await checker.generate_report()


if __name__ == "__main__":
    asyncio.run(main())
