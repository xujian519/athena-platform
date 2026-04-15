# ============================================================
# AI伦理框架 - 健康检查API
# AI Ethics Framework - Health Check API
# ============================================================

from __future__ import annotations
import logging
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, Response

from core.ethics import (
    EthicsContainer,
    get_container,
)
from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="Athena AI伦理框架 - 健康检查",
    description="AI伦理框架健康检查和监控端点",
    version="1.0.0",
)

# 全局状态
_container: EthicsContainer | None = None
_startup_time: datetime | None = None


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global _container, _startup_time

    logger.info("AI伦理框架健康检查API启动中...")

    try:
        # 初始化容器
        _container = get_container()
        _container.initialize()

        _startup_time = datetime.now()

        logger.info("AI伦理框架健康检查API启动成功")

    except Exception as e:
        logger.error(f"启动失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("AI伦理框架健康检查API关闭中...")


@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "Athena AI伦理框架",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """健康检查端点

    返回服务整体健康状态
    """
    try:
        checks = await run_health_checks()
        all_healthy = all(check["healthy"] for check in checks.values())

        response = {
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (
                (datetime.now() - _startup_time).total_seconds() if _startup_time else 0
            ),
            "checks": checks,
        }

        status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(content=response, status_code=status_code)

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"健康检查失败: {e!s}"
        ) from e


@app.get("/health/evaluator")
async def check_evaluator():
    """检查评估器健康状态"""
    try:
        if _container is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="容器未初始化"
            )

        evaluator = _container.create_evaluator()

        # 执行测试评估
        result = evaluator.evaluate_action(agent_id="health_check", action="健康检查", context={})

        statistics = evaluator.get_statistics()

        return {
            "healthy": True,
            "statistics": statistics,
            "test_result": {"status": result.status.value, "score": result.overall_score},
        }

    except Exception as e:
        logger.error(f"评估器健康检查失败: {e}")
        return {"healthy": False, "error": str(e)}


@app.get("/health/monitor")
async def check_monitor():
    """检查监控器健康状态"""
    try:
        if _container is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="容器未初始化"
            )

        monitor = _container.create_monitor()
        metrics = monitor.get_current_metrics()

        return {
            "healthy": True,
            "metrics": {
                "total_evaluations": metrics.total_evaluations,
                "compliant_count": metrics.compliant_count,
                "violation_count": metrics.violation_count,
                "compliance_rate": metrics.compliance_rate,
            },
        }

    except Exception as e:
        logger.error(f"监控器健康检查失败: {e}")
        return {"healthy": False, "error": str(e)}


@app.get("/health/prometheus")
async def check_prometheus():
    """检查Prometheus监控器健康状态"""
    try:
        if _container is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="容器未初始化"
            )

        prometheus = _container.create_prometheus_monitor()
        summary = prometheus.get_metrics_summary()

        return {"healthy": True, "summary": summary}

    except Exception as e:
        logger.error(f"Prometheus健康检查失败: {e}")
        return {"healthy": False, "error": str(e)}


@app.get("/health/cache")
async def check_cache():
    """检查缓存健康状态"""
    try:
        import redis

        redis_url = "redis://:athena123@localhost:6379/0"
        r = redis.from_url(redis_url, decode_responses=True)

        # 测试连接
        r.ping()

        # 测试读写
        test_key = "health_check_test"
        r.set(test_key, "test", ex=10)
        value = r.get(test_key)
        r.delete(test_key)

        return {"healthy": True, "cache": "redis", "test_value": value if value else None}

    except Exception as e:
        logger.error(f"缓存健康检查失败: {e}")
        return {"healthy": False, "error": str(e)}


@app.get("/metrics")
async def metrics():
    """Prometheus指标端点(代理)"""
    try:
        from prometheus_client import (
            CONTENT_TYPE_LATEST,
            REGISTRY,
            generate_latest,
        )

        # 获取Prometheus指标

        output = generate_latest(REGISTRY)

        return Response(content=output, media_type=CONTENT_TYPE_LATEST)

    except Exception as e:
        logger.error(f"获取指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取指标失败: {e!s}"
        ) from e


@app.get("/status")
async def get_status():
    """获取详细状态信息"""
    try:
        container_info = _container.get_container_info() if _container else {}

        return {
            "service": "Athena AI伦理框架",
            "version": "1.0.0",
            "environment": "production",
            "startup_time": _startup_time.isoformat() if _startup_time else None,
            "uptime_seconds": (
                (datetime.now() - _startup_time).total_seconds() if _startup_time else 0
            ),
            "container": container_info,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取状态失败: {e!s}"
        ) from e


# ============================================================
# 辅助函数
# ============================================================


async def run_health_checks() -> dict[str, dict[str, Any]]:
    """运行所有健康检查"""

    checks = {}

    # 检查评估器
    try:
        evaluator_health = await check_evaluator()
        checks["evaluator"] = evaluator_health
    except Exception as e:
        checks["evaluator"] = {"healthy": False, "error": str(e)}

    # 检查监控器
    try:
        monitor_health = await check_monitor()
        checks["monitor"] = monitor_health
    except Exception as e:
        checks["monitor"] = {"healthy": False, "error": str(e)}

    # 检查Prometheus
    try:
        prometheus_health = await check_prometheus()
        checks["prometheus"] = prometheus_health
    except Exception as e:
        checks["prometheus"] = {"healthy": False, "error": str(e)}

    # 检查缓存
    try:
        cache_health = await check_cache()
        checks["cache"] = cache_health
    except Exception as e:
        checks["cache"] = {"healthy": False, "error": str(e)}

    return checks


# ============================================================
# 主函数(用于直接运行)
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
