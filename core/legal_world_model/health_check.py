#!/usr/bin/env python3
"""
法律世界模型健康检查
Legal World Model Health Check

提供法律世界模型组件的健康状态检查功能。

作者: Athena平台团队
创建时间: 2026-02-03
版本: v1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """健康状态"""

    HEALTHY = "healthy"  # 健康
    DEGRADED = "degraded"  # 降级运行
    UNHEALTHY = "unhealthy"  # 不健康
    UNKNOWN = "unknown"  # 未知


@dataclass
class ComponentHealth:
    """组件健康状态"""

    name: str
    status: HealthStatus
    message: str = ""
    response_time_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SystemHealthReport:
    """系统健康报告"""

    overall_status: HealthStatus
    components: dict[str, ComponentHealth]
    timestamp: datetime = field(default_factory=datetime.now)
    total_components: int = 0
    healthy_components: int = 0
    degraded_components: int = 0
    unhealthy_components: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "overall_status": self.overall_status.value,
            "timestamp": self.timestamp.isoformat(),
            "summary": {
                "total": self.total_components,
                "healthy": self.healthy_components,
                "degraded": self.degraded_components,
                "unhealthy": self.unhealthy_components,
            },
            "components": {
                name: {
                    "status": comp.status.value,
                    "message": comp.message,
                    "response_time_ms": comp.response_time_ms,
                    "details": comp.details,
                    "timestamp": comp.timestamp.isoformat(),
                }
                for name, comp in self.components.items()
            },
        }


class LegalWorldModelHealthChecker:
    """法律世界模型健康检查器"""

    def __init__(self):
        """初始化健康检查器"""
        self.components: dict[str, ComponentHealth] = {}

    async def check_all_components(self) -> SystemHealthReport:
        """
        检查所有组件的健康状态

        Returns:
            系统健康报告
        """
        logger.info("开始健康检查...")

        # 并发检查所有组件
        checks = [
            self._check_neo4j(),
            self._check_postgres(),
            self._check_qdrant(),
            self._check_cache(),
            self._check_scenario_retriever(),
            self._check_constitution_validator(),
        ]

        results = await asyncio.gather(*checks, return_exceptions=True)

        # 整理结果
        self.components = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"健康检查异常: {result}")
            elif isinstance(result, ComponentHealth):
                self.components[result.name] = result

        # 计算总体状态
        return self._generate_report()

    async def _check_neo4j(self) -> ComponentHealth:
        """检查Neo4j连接"""
        start_time = datetime.now()
        try:
            import subprocess
            from dotenv import load_dotenv
            import os

            load_dotenv()

            username = os.getenv("NEO4J_USERNAME", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "")

            # 使用cypher-shell命令行工具（避免Python驱动兼容性问题）
            cmd = ["cypher-shell", "-u", username, "-p", password,
                    "MATCH (n) RETURN count(n) as count"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # 解析输出获取节点数
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    try:
                        count = int(lines[1].strip().replace(',', ''))
                    except ValueError:
                        count = 0
                else:
                    count = 0

                response_time = (datetime.now() - start_time).total_seconds() * 1000

                return ComponentHealth(
                    name="neo4j",
                    status=HealthStatus.HEALTHY,
                    message=f"Neo4j正常运行，节点数: {count:,}",
                    response_time_ms=response_time,
                    details={"node_count": count},
                )
            else:
                # cypher-shell失败，尝试Python驱动
                try:
                    from neo4j import GraphDatabase
                    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                    driver = GraphDatabase.driver(uri, auth=(username, password))
                    with driver.session() as session:
                        result = session.run("MATCH (n) RETURN count(n) as count")
                        count = result.single()["count"]
                    driver.close()

                    response_time = (datetime.now() - start_time).total_seconds() * 1000

                    return ComponentHealth(
                        name="neo4j",
                        status=HealthStatus.HEALTHY,
                        message=f"Neo4j正常运行，节点数: {count:,}",
                        response_time_ms=response_time,
                        details={"node_count": count},
                    )
                except Exception as e2:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    logger.error(f"Neo4j健康检查失败: {e2}")
                    return ComponentHealth(
                        name="neo4j",
                        status=HealthStatus.UNHEALTHY,
                        message=f"Neo4j连接失败: {e2}",
                        response_time_ms=response_time,
                    )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Neo4j健康检查失败: {e}")
            return ComponentHealth(
                name="neo4j",
                status=HealthStatus.UNHEALTHY,
                message=f"Neo4j连接失败: {str(e)[:100]}",
                response_time_ms=response_time,
            )

    async def _check_postgres(self) -> ComponentHealth:
        """检查PostgreSQL连接"""
        start_time = datetime.now()
        try:
            import psycopg2
            from dotenv import load_dotenv
            import os

            load_dotenv()

            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 5432)),
                database=os.getenv("DB_NAME", "athena"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
            )

            cur = conn.cursor()

            # 检查专利法律文档表（实际存在的表）
            cur.execute("SELECT COUNT(*) FROM patent_law_documents")
            doc_count = cur.fetchone()[0]

            cur.close()
            conn.close()

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            return ComponentHealth(
                name="postgres",
                status=HealthStatus.HEALTHY,
                message=f"PostgreSQL正常运行，文档数: {doc_count:,}",
                response_time_ms=response_time,
                details={"document_count": doc_count},
            )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"PostgreSQL健康检查失败: {e}")
            return ComponentHealth(
                name="postgres",
                status=HealthStatus.UNHEALTHY,
                message=f"PostgreSQL连接失败: {str(e)[:100]}",
                response_time_ms=response_time,
            )

    async def _check_qdrant(self) -> ComponentHealth:
        """检查Qdrant连接"""
        start_time = datetime.now()
        try:
            from qdrant_client import QdrantClient
            from dotenv import load_dotenv
            import os

            load_dotenv()

            url = os.getenv("QDRANT_URL", "http://localhost:6333")
            api_key = os.getenv("QDRANT_API_KEY")

            client = QdrantClient(url=url, api_key=api_key)

            # 获取集合列表
            collections = client.get_collections()

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            collection_names = [c.name for c in collections.collections]

            return ComponentHealth(
                name="qdrant",
                status=HealthStatus.HEALTHY,
                message=f"Qdrant正常运行，集合数: {len(collection_names)}",
                response_time_ms=response_time,
                details={"collections": collection_names},
            )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Qdrant健康检查失败: {e}")
            return ComponentHealth(
                name="qdrant",
                status=HealthStatus.UNHEALTHY,
                message=f"Qdrant连接失败: {str(e)[:100]}",
                response_time_ms=response_time,
            )

    async def _check_cache(self) -> ComponentHealth:
        """检查缓存状态"""
        start_time = datetime.now()
        try:
            import redis
            from dotenv import load_dotenv
            import os

            load_dotenv()

            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", 6379))
            password = os.getenv("REDIS_PASSWORD", "")

            r = redis.Redis(host=host, port=port, password=password, decode_responses=True)

            # 测试连接
            r.ping()

            # 获取信息
            info = r.info("stats")

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            return ComponentHealth(
                name="cache",
                status=HealthStatus.HEALTHY,
                message=f"Redis正常运行",
                response_time_ms=response_time,
                details={"total_connections": info.get("total_connections_received", 0)},
            )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.warning(f"Redis健康检查失败: {e}")
            # 缓存不可用不算严重问题
            return ComponentHealth(
                name="cache",
                status=HealthStatus.DEGRADED,
                message=f"Redis不可用: {str(e)[:100]}",
                response_time_ms=response_time,
            )

    async def _check_scenario_retriever(self) -> ComponentHealth:
        """检查场景规则检索器"""
        start_time = datetime.now()
        try:
            # 只检查模块是否可导入（不实例化，避免依赖db_manager）
            from core.legal_world_model.scenario_rule_retriever_optimized import (
                ScenarioRuleRetrieverOptimized,
            )

            # 检查类是否可访问
            status = "available"
            if hasattr(ScenarioRuleRetrieverOptimized, "ALLOWED_DOMAINS"):
                domains = len(ScenarioRuleRetrieverOptimized.ALLOWED_DOMAINS)
            else:
                domains = 0

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            return ComponentHealth(
                name="scenario_retriever",
                status=HealthStatus.HEALTHY,
                message=f"场景规则检索器可用，支持{domains}个领域",
                response_time_ms=response_time,
                details={"status": status, "domains": domains},
            )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"场景规则检索器检查失败: {e}")
            return ComponentHealth(
                name="scenario_retriever",
                status=HealthStatus.UNHEALTHY,
                message=f"场景规则检索器异常: {str(e)[:100]}",
                response_time_ms=response_time,
            )

    async def _check_constitution_validator(self) -> ComponentHealth:
        """检查宪法验证器"""
        start_time = datetime.now()
        try:
            from core.legal_world_model.constitution import ConstitutionalValidator

            validator = ConstitutionalValidator()

            # 检查验证器是否可用
            is_available = validator is not None

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            if is_available:
                return ComponentHealth(
                    name="constitution_validator",
                    status=HealthStatus.HEALTHY,
                    message="宪法验证器可用",
                    response_time_ms=response_time,
                )
            else:
                return ComponentHealth(
                    name="constitution_validator",
                    status=HealthStatus.UNHEALTHY,
                    message="宪法验证器初始化失败",
                    response_time_ms=response_time,
                )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"宪法验证器检查失败: {e}")
            return ComponentHealth(
                name="constitution_validator",
                status=HealthStatus.UNHEALTHY,
                message=f"宪法验证器异常: {str(e)[:100]}",
                response_time_ms=response_time,
            )

    def _generate_report(self) -> SystemHealthReport:
        """生成健康报告"""
        total = len(self.components)
        healthy = sum(1 for c in self.components.values() if c.status == HealthStatus.HEALTHY)
        degraded = sum(1 for c in self.components.values() if c.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for c in self.components.values() if c.status == HealthStatus.UNHEALTHY)

        # 确定总体状态
        if unhealthy > 0:
            overall = HealthStatus.UNHEALTHY
        elif degraded > 0:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        return SystemHealthReport(
            overall_status=overall,
            components=self.components,
            total_components=total,
            healthy_components=healthy,
            degraded_components=degraded,
            unhealthy_components=unhealthy,
        )


# 全局单例
_health_checker: LegalWorldModelHealthChecker | None = None


def get_health_checker() -> LegalWorldModelHealthChecker:
    """获取健康检查器单例"""
    global _health_checker
    if _health_checker is None:
        _health_checker = LegalWorldModelHealthChecker()
    return _health_checker


async def check_health() -> SystemHealthReport:
    """
    检查法律世界模型健康状态（便捷函数）

    Returns:
        系统健康报告
    """
    checker = get_health_checker()
    return await checker.check_all_components()


__all__ = [
    "HealthStatus",
    "ComponentHealth",
    "SystemHealthReport",
    "LegalWorldModelHealthChecker",
    "get_health_checker",
    "check_health",
]
