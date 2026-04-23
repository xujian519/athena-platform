from __future__ import annotations
"""
健康检查模块
Health Check Module

提供系统健康检查和状态报告功能
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import psutil

logger = logging.getLogger(__name__)


# ============================================
# 健康检查结果数据类
# ============================================


@dataclass
class HealthCheckResult:
    """健康检查结果"""

    name: str
    status: str  # healthy, degraded, unhealthy
    message: str
    response_time_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "response_time_ms": self.response_time_ms,
            "details": self.details,
        }


# ============================================
# 健康检查基类
# ============================================


class HealthCheck:
    """健康检查基类"""

    def __init__(self, name: str):
        self.name = name

    async def check(self) -> HealthCheckResult:
        """执行健康检查"""
        raise NotImplementedError


# ============================================
# 数据库健康检查
# ============================================


class DatabaseHealthCheck(HealthCheck):
    """PostgreSQL数据库健康检查"""

    def __init__(self, db_client):
        super().__init__("database")
        self.db_client = db_client

    async def check(self) -> HealthCheckResult:
        """检查数据库连接"""
        start_time = datetime.now()

        try:
            # 执行简单查询
            await self.db_client.execute("SELECT 1")

            elapsed = (datetime.now() - start_time).total_seconds() * 1000

            if elapsed > 1000:
                return HealthCheckResult(
                    name=self.name,
                    status="degraded",
                    message=f"数据库响应慢: {elapsed:.0f}ms",
                    response_time_ms=elapsed,
                    details={"response_time_ms": elapsed},
                )

            return HealthCheckResult(
                name=self.name,
                status="healthy",
                message="数据库连接正常",
                response_time_ms=elapsed,
                details={"response_time_ms": elapsed},
            )

        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                message=f"数据库连接失败: {e!s}",
                response_time_ms=0,
                details={"error": str(e)},
            )


# ============================================
# Redis健康检查
# ============================================


class RedisHealthCheck(HealthCheck):
    """Redis健康检查"""

    def __init__(self, redis_client):
        super().__init__("redis")
        self.redis_client = redis_client

    async def check(self) -> HealthCheckResult:
        """检查Redis连接"""
        start_time = datetime.now()

        try:
            # 执行PING
            result = await self.redis_client.ping()

            elapsed = (datetime.now() - start_time).total_seconds() * 1000

            if not result:
                return HealthCheckResult(
                    name=self.name,
                    status="unhealthy",
                    message="Redis PING失败",
                    response_time_ms=elapsed,
                )

            if elapsed > 500:
                return HealthCheckResult(
                    name=self.name,
                    status="degraded",
                    message=f"Redis响应慢: {elapsed:.0f}ms",
                    response_time_ms=elapsed,
                )

            return HealthCheckResult(
                name=self.name,
                status="healthy",
                message="Redis连接正常",
                response_time_ms=elapsed,
                details={"response_time_ms": elapsed},
            )

        except Exception as e:
            logger.error(f"Redis健康检查失败: {e}")
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                message=f"Redis连接失败: {e!s}",
                response_time_ms=0,
                details={"error": str(e)},
            )


# ============================================
# Qdrant健康检查
# ============================================


class QdrantHealthCheck(HealthCheck):
    """Qdrant向量数据库健康检查"""

    def __init__(self, qdrant_client):
        super().__init__("qdrant")
        self.qdrant_client = qdrant_client

    async def check(self) -> HealthCheckResult:
        """检查Qdrant连接"""
        start_time = datetime.now()

        try:
            # 获取集群信息
            collections = await self.qdrant_client.get_collections()

            elapsed = (datetime.now() - start_time).total_seconds() * 1000

            return HealthCheckResult(
                name=self.name,
                status="healthy",
                message=f"Qdrant连接正常 (集合数: {len(collections)})",
                response_time_ms=elapsed,
                details={"response_time_ms": elapsed, "collections_count": len(collections)},
            )

        except Exception as e:
            logger.error(f"Qdrant健康检查失败: {e}")
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                message=f"Qdrant连接失败: {e!s}",
                response_time_ms=0,
                details={"error": str(e)},
            )


# ============================================
# Neo4j健康检查
# ============================================


class Neo4jHealthCheck(HealthCheck):
    """Neo4j图数据库健康检查"""

    def __init__(self, neo4j_driver):
        super().__init__("neo4j")
        self.neo4j_driver = neo4j_driver

    async def check(self) -> HealthCheckResult:
        """检查Neo4j连接"""
        start_time = datetime.now()

        try:
            # 执行简单查询
            async with self.neo4j_driver.session() as session:
                result = await session.run("RETURN 1 as num")
                await result.single()

            elapsed = (datetime.now() - start_time).total_seconds() * 1000

            return HealthCheckResult(
                name=self.name,
                status="healthy",
                message="Neo4j连接正常",
                response_time_ms=elapsed,
                details={"response_time_ms": elapsed},
            )

        except Exception as e:
            logger.error(f"Neo4j健康检查失败: {e}")
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                message=f"Neo4j连接失败: {e!s}",
                response_time_ms=0,
                details={"error": str(e)},
            )


# ============================================
# 系统资源健康检查
# ============================================


class SystemHealthCheck(HealthCheck):
    """系统资源健康检查"""

    def __init__(self):
        super().__init__("system")

    async def check(self) -> HealthCheckResult:
        """检查系统资源"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # 磁盘使用率
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent

            # 判断健康状态
            status = "healthy"
            messages = []

            if cpu_percent > 90:
                status = "unhealthy"
                messages.append(f"CPU使用率过高: {cpu_percent}%")
            elif cpu_percent > 70:
                status = "degraded"
                messages.append(f"CPU使用率较高: {cpu_percent}%")

            if memory_percent > 90:
                status = "unhealthy"
                messages.append(f"内存使用率过高: {memory_percent}%")
            elif memory_percent > 80:
                if status != "unhealthy":
                    status = "degraded"
                messages.append(f"内存使用率较高: {memory_percent}%")

            if disk_percent > 90:
                status = "unhealthy"
                messages.append(f"磁盘使用率过高: {disk_percent}%")
            elif disk_percent > 80:
                if status != "unhealthy":
                    status = "degraded"
                messages.append(f"磁盘使用率较高: {disk_percent}%")

            if not messages:
                messages.append("系统资源正常")

            return HealthCheckResult(
                name=self.name,
                status=status,
                message="; ".join(messages),
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_free_gb": disk.free / (1024**3),
                },
            )

        except Exception as e:
            logger.error(f"系统资源检查失败: {e}")
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                message=f"系统资源检查失败: {e!s}",
                details={"error": str(e)},
            )


# ============================================
# 健康检查管理器
# ============================================


class HealthCheckManager:
    """健康检查管理器"""

    def __init__(self):
        self.checks: list[HealthCheck] = []

    def register(self, check: HealthCheck) -> Any:
        """注册健康检查"""
        self.checks.append(check)
        logger.info(f"注册健康检查: {check.name}")

    async def check_all(self) -> dict[str, Any]:
        """执行所有健康检查"""
        if not self.checks:
            return {
                "status": "healthy",
                "message": "无健康检查项",
                "checks": [],
                "timestamp": datetime.now().isoformat(),
            }

        # 并发执行所有检查
        tasks = [check.check() for check in self.checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        checks = []
        overall_status = "healthy"

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                checks.append(
                    HealthCheckResult(
                        name=self.checks[i].name,
                        status="unhealthy",
                        message=f"检查异常: {result!s}",
                    ).to_dict()
                )
                overall_status = "unhealthy"
            else:
                checks.append(result.to_dict())

                # 更新整体状态
                if result.status == "unhealthy":
                    overall_status = "unhealthy"
                elif result.status == "degraded" and overall_status != "unhealthy":
                    overall_status = "degraded"

        return {
            "status": overall_status,
            "message": self._get_status_message(overall_status),
            "checks": checks,
            "timestamp": datetime.now().isoformat(),
        }

    def _get_status_message(self, status: str) -> str:
        """获取状态消息"""
        messages = {
            "healthy": "所有系统运行正常",
            "degraded": "部分系统性能下降",
            "unhealthy": "存在系统故障",
        }
        return messages.get(status, "未知状态")


# ============================================
# FastAPI集成
# ============================================

from fastapi import APIRouter

router = APIRouter()
health_manager = HealthCheckManager()


def setup_health_checks(db_client=None, redis_client=None, qdrant_client=None, neo4j_driver=None):
    """设置健康检查"""

    # 注册系统资源检查
    health_manager.register(SystemHealthCheck())

    # 注册数据库检查
    if db_client:
        health_manager.register(DatabaseHealthCheck(db_client))

    # 注册Redis检查
    if redis_client:
        health_manager.register(RedisHealthCheck(redis_client))

    # 注册Qdrant检查
    if qdrant_client:
        health_manager.register(QdrantHealthCheck(qdrant_client))

    # 注册Neo4j检查
    if neo4j_driver:
        health_manager.register(Neo4jHealthCheck(neo4j_driver))


@router.get("/health")
async def health_check():
    """基本健康检查"""
    result = await health_manager.check_all()
    return result


@router.get("/health/detailed")
async def detailed_health_check():
    """详细健康检查"""
    result = await health_manager.check_all()

    # 添加更多信息
    result["system"] = {
        "python_version": f"{psutil.PYTHON_VERSION}",
        "cpu_count": psutil.cpu_count(),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
    }

    return result


@router.get("/health/ready")
async def readiness_check():
    """就绪检查(用于Kubernetes)"""
    result = await health_manager.check_all()

    if result["status"] == "healthy":
        return {"ready": True}
    else:
        return {"ready": False, "reason": result["message"]}


@router.get("/health/live")
async def liveness_check():
    """存活检查(用于Kubernetes)"""
    return {"alive": True}
