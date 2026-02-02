#!/usr/bin/env python3
"""
Athena 平台统一健康检查服务
Unified Health Check Service for Athena Platform

提供服务健康检查、依赖检查、性能监控

作者: 小诺·双鱼公主 v4.0
创建时间: 2025-12-25
版本: 1.0.0
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """健康状态"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class CheckResult:
    """检查结果"""

    name: str
    status: HealthStatus
    message: str = ""
    response_time_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "response_time_ms": round(self.response_time_ms, 2),
            "details": self.details,
            "timestamp": datetime.now().isoformat(),
        }


class HealthChecker:
    """健康检查器"""

    def __init__(self, config=None):
        self.config = config
        self.checks = []
        self.results = []

    def register_check(self, name: str, check_func, critical: bool = True) -> None:
        """注册健康检查"""
        self.checks.append(
            {
                "name": name,
                "func": check_func,
                "critical": critical,
            }
        )
        logger.info(f"✅ 注册健康检查: {name}")

    async def check_database(self, db_url: str) -> CheckResult:
        """检查数据库连接"""
        start_time = time.time()

        try:
            engine = create_async_engine(db_url, pool_size=1)
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                await result.fetchone()

            response_time = (time.time() - start_time) * 1000

            return CheckResult(
                name="infrastructure/infrastructure/database",
                status=HealthStatus.HEALTHY,
                message="数据库连接正常",
                response_time_ms=response_time,
                details={"url": db_url.split("@")[-1] if "@" in db_url else db_url},
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return CheckResult(
                name="infrastructure/infrastructure/database",
                status=HealthStatus.UNHEALTHY,
                message=f"数据库连接失败: {e!s}",
                response_time_ms=response_time,
            )

    async def check_redis(self, redis_url: str) -> CheckResult:
        """检查Redis连接"""
        start_time = time.time()

        try:
            # 解析Redis URL
            if "redis://" in redis_url:
                url = redis_url.replace("redis://", "")
                if "@" in url:
                    auth, host_port = url.split("@")
                    password = auth.split(":")[1] if ":" in auth else None
                else:
                    host_port = url
                    password = None

                host = host_port.split(":")[0] if ":" in host_port else host_port.split("/")[0]
                port = int(host_port.split(":")[1]) if ":" in host_port else 6379

                redis = AsyncRedis(
                    host=host,
                    port=port,
                    password=password,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                await redis.ping()
                await redis.close()

            response_time = (time.time() - start_time) * 1000

            return CheckResult(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis连接正常",
                response_time_ms=response_time,
                details={"host": host if "host" in locals() else redis_url},
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return CheckResult(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis连接失败: {e!s}",
                response_time_ms=response_time,
            )

    async def check_qdrant(self, host: str, port: int = 6333) -> CheckResult:
        """检查Qdrant向量数据库"""
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"http://{host}:{port}/")

            if response.status_code == 200:
                response_time = (time.time() - start_time) * 1000
                return CheckResult(
                    name="qdrant",
                    status=HealthStatus.HEALTHY,
                    message="Qdrant服务正常",
                    response_time_ms=response_time,
                    details={"version": response.headers.get("server", "unknown")},
                )
            else:
                return CheckResult(
                    name="qdrant",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Qdrant响应异常: {response.status_code}",
                    response_time_ms=(time.time() - start_time) * 1000,
                )
        except Exception as e:
            return CheckResult(
                name="qdrant",
                status=HealthStatus.UNHEALTHY,
                message=f"Qdrant连接失败: {e!s}",
                response_time_ms=(time.time() - start_time) * 1000,
            )

    async def check_service(self, name: str, url: str) -> CheckResult:
        """检查HTTP服务"""
        start_time = time.time()

        try:
            health_url = f"{url.rstrip('/')}/health" if not url.endswith("/health") else url
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)

            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return CheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    message="服务正常",
                    response_time_ms=response_time,
                )
            else:
                return CheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"服务响应异常: {response.status_code}",
                    response_time_ms=response_time,
                )
        except Exception as e:
            return CheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"服务连接失败: {e!s}",
                response_time_ms=(time.time() - start_time) * 1000,
            )

    async def run_all_checks(self) -> dict[str, Any]:
        """运行所有健康检查"""
        self.results = []

        for check in self.checks:
            try:
                result = await check["func"]()
                self.results.append(result)
            except Exception as e:
                logger.error(f"健康检查失败 {check['name']}: {e}")
                self.results.append(
                    CheckResult(
                        name=check["name"],
                        status=HealthStatus.UNKNOWN,
                        message=f"检查执行失败: {e!s}",
                    )
                )

        # 计算总体健康状态
        critical_failures = sum(
            1
            for r in self.results
            if r.status != HealthStatus.HEALTHY
            and any(c["name"] == r.name and c["critical"] for c in self.checks)
        )

        if critical_failures > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif any(r.status == HealthStatus.DEGRADED for r in self.results) or any(r.status == HealthStatus.UNKNOWN for r in self.results):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "checks": [r.to_dict() for r in self.results],
            "summary": {
                "total": len(self.results),
                "healthy": sum(1 for r in self.results if r.status == HealthStatus.HEALTHY),
                "degraded": sum(1 for r in self.results if r.status == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for r in self.results if r.status == HealthStatus.UNHEALTHY),
                "unknown": sum(1 for r in self.results if r.status == HealthStatus.UNKNOWN),
            },
        }

    def get_fastapi_health_endpoints(self, app) -> None:
        """为FastAPI应用添加健康检查端点"""
        from fastapi import APIRouter

        router = APIRouter()

        @router.get("/health")
        async def health_check():
            """基本健康检查"""
            return {
                "status": "healthy",
                "service": "Athena Platform",
                "timestamp": datetime.now().isoformat(),
            }

        @router.get("/health/detailed")
        async def detailed_health_check():
            """详细健康检查"""
            return await self.run_all_checks()

        @router.get("/health/ready")
        async def readiness_check():
            """就绪检查"""
            result = await self.run_all_checks()
            is_ready = result["status"] == "healthy"

            return {
                "ready": is_ready,
                "timestamp": datetime.now().isoformat(),
            }

        @router.get("/health/live")
        async def liveness_check():
            """存活检查"""
            return {
                "alive": True,
                "timestamp": datetime.now().isoformat(),
            }

        app.include_router(router, tags=["Health"])

        logger.info("✅ 健康检查端点已注册")

        return router


# 便捷函数
async def quick_health_check(config) -> dict[str, Any]:
    """快速健康检查"""
    checker = HealthChecker(config)

    # 注册标准检查
    if hasattr(config, "infrastructure/infrastructure/database"):
        checker.register_check(
            "infrastructure/infrastructure/database",
            lambda: checker.check_database(config.get_database_url()),
            critical=True,
        )

    if hasattr(config, "redis"):
        checker.register_check(
            "redis", lambda: checker.check_redis(config.get_redis_url()), critical=True
        )

    if hasattr(config, "qdrant"):
        checker.register_check(
            "qdrant",
            lambda: checker.check_qdrant(config.qdrant.host, config.qdrant.port),
            critical=False,
        )

    return await checker.run_all_checks()


if __name__ == "__main__":
    # 测试健康检查器
    async def test():
        from config.central_config import get_config

        config = get_config()
        result = await quick_health_check(config)

        print("🏥 Athena 平台健康检查")
        print("=" * 60)
        print(f"总体状态: {result['status'].upper()}")
        print()
        print("📊 检查详情:")
        for check in result["checks"]:
            print(f"  {check['name']}: {check['status']} ({check['response_time_ms']:.2f}ms)")
        print()
        print("📈 统计:")
        summary = result["summary"]
        print(f"  总计: {summary['total']}")
        print(f"  健康: {summary['healthy']}")
        print(f"  降级: {summary['degraded']}")
        print(f"  不健康: {summary['unhealthy']}")
        print(f"  未知: {summary['unknown']}")

    asyncio.run(test())
