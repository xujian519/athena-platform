#!/usr/bin/env python3
"""
监控和健康检查API路由
Monitoring and Health Check API Routes

提供Prometheus监控指标和健康检查端点
"""

from __future__ import annotations
import logging
from typing import Any

from fastapi import APIRouter

# 导入监控模块
from core.monitoring.metrics import (
    get_health_checker,
    get_prometheus_server,
    health_endpoint,
    liveness_endpoint,
    metrics_endpoint,
    readiness_endpoint,
)

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# =============================================================================
# Prometheus指标端点
# =============================================================================


@router.get("/metrics", include_in_schema=False)
async def get_metrics():
    """
    Prometheus监控指标端点

    返回Prometheus格式的监控指标
    """
    return await metrics_endpoint()


# =============================================================================
# 健康检查端点
# =============================================================================


@router.get("/health")
async def get_health() -> dict[str, Any]:
    """
    健康检查端点

    返回所有组件的健康状态

    Returns:
        健康状态JSON
        ```json
        {
            "status": "healthy",
            "checks": {
                "database": {"status": "healthy", "last_check": 1234567890},
                "qdrant": {"status": "healthy", "last_check": 1234567890},
                "vector_model": {"status": "healthy", "last_check": 1234567890}
            },
            "timestamp": 1234567890
        }
        ```
    """
    return await health_endpoint()


@router.get("/ready")
async def get_readiness() -> dict[str, Any]:
    """
    就绪检查端点(Kubernetes就绪探针)

    检查关键组件是否就绪

    Returns:
        就绪状态JSON
        ```json
        {
            "ready": true,
            "checks": {
                "database": {"status": "healthy", "last_check": 1234567890},
                "qdrant": {"status": "healthy", "last_check": 1234567890},
                "vector_model": {"status": "healthy", "last_check": 1234567890}
            }
        }
        ```
    """
    return await readiness_endpoint()


@router.get("/live")
async def get_liveness() -> dict[str, Any]:
    """
    存活检查端点(Kubernetes存活探针)

    简单的存活检查 - 如果进程能响应就是活着的

    Returns:
        存活状态JSON
        ```json
        {
            "alive": true,
            "timestamp": 1234567890
        }
        ```
    """
    return await liveness_endpoint()


# =============================================================================
# 启动监控服务器
# =============================================================================


def start_monitoring_server(port: int = 9091):
    """
    启动Prometheus监控服务器

    Args:
        port: 监控端点端口,默认9091

    Examples:
        ```python

        # 启动监控服务器
        start_monitoring_server(port=9091)
        ```
    """
    server = get_prometheus_server(port=port)
    server.start()
    logger.info(f"✅ Monitoring server started on port {port}")


# =============================================================================
# 注册健康检查
# =============================================================================


def register_default_health_checks():
    """
    注册默认的健康检查

    注册数据库、Qdrant、向量模型等关键组件的健康检查

    Examples:
        ```python

        # 注册默认健康检查
        register_default_health_checks()
        ```
    """
    health_checker = get_health_checker()

    # 数据库健康检查
    def check_database():
        """检查数据库连接"""
        try:
            import psycopg2

            from core.config.search_config import get_search_config

            config = get_search_config()
            db_config = config.database.to_dict()

            # 尝试连接数据库
            conn = psycopg2.connect(**db_config)
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    # Qdrant健康检查
    def check_qdrant():
        """检查Qdrant连接"""
        try:
            from qdrant_client import QdrantClient

            from core.config.search_config import get_search_config

            config = get_search_config()

            # 尝试连接Qdrant
            client = QdrantClient(host=config.qdrant.host, port=config.qdrant.port, timeout=5)
            client.get_collections()
            return True

        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    # 向量模型健康检查
    def check_vector_model():
        """检查向量模型是否加载"""
        try:
            # 这里可以添加更详细的模型检查
            # 例如检查模型文件是否存在、是否可以加载等

            from sentence_transformers import SentenceTransformer

            # 简单的检查:尝试加载模型
            model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
            return model is not None

        except Exception as e:
            logger.error(f"Vector model health check failed: {e}")
            return False

    # 注册检查
    health_checker.register_check("database", check_database)
    health_checker.register_check("qdrant", check_qdrant)
    health_checker.register_check("vector_model", check_vector_model)

    logger.info("✅ Default health checks registered")


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "get_health",
    "get_liveness",
    "get_metrics",
    "get_readiness",
    "register_default_health_checks",
    "router",
    "start_monitoring_server",
]
