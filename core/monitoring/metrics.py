#!/usr/bin/env python3
from __future__ import annotations
"""
Prometheus监控指标
Prometheus Metrics for Search Engine

提供搜索引擎的Prometheus监控指标收集和健康检查功能
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
    start_http_server,
)

logger = logging.getLogger(__name__)

# 指标定义
search_requests_total = Counter(
    "athena_search_requests_total", "Total search requests", ["intent", "status"]
)

search_duration_seconds = Histogram(
    "athena_search_duration_seconds", "Search request duration", ["intent"]
)

active_requests = Gauge("athena_active_requests", "Active search requests")

cache_hits = Counter("athena_cache_hits_total", "Total cache hits")

cache_misses = Counter("athena_cache_misses_total", "Total cache misses")

bge_model_load_time = Histogram("athena_bge_model_load_time_seconds", "BGE model load time")

cache_size = Gauge("athena_cache_size", "Current cache size", ["cache_type"])

# 应用信息
app_info = Info("athena_app", "Athena Intelligent Router Application Info")


class MetricsRecorder:
    """指标记录器"""

    def __init__(self):
        self.start_time = None

    def record_search_start(self, intent: str) -> Any:
        """记录搜索开始"""
        self.start_time = time.time()
        active_requests.inc()

    def record_search_complete(self, intent: str, success: bool) -> Any:
        """记录搜索完成"""
        duration = time.time() - self.start_time
        search_requests_total.labels(intent=intent, status="success" if success else "error").inc()
        search_duration_seconds.labels(intent=intent).observe(duration)
        active_requests.dec()

    def record_cache_hit(self) -> Any:
        """记录缓存命中"""
        cache_hits.inc()

    def record_cache_miss(self) -> Any:
        """记录缓存未命中"""
        cache_misses.inc()


# 全局记录器
_metrics_recorder = MetricsRecorder()


def get_metrics_recorder() -> MetricsRecorder:
    """获取指标记录器"""
    return _metrics_recorder


def update_app_info(version: str, environment: str) -> None:
    """更新应用信息"""
    app_info.info({"version": version, "environment": environment})


def update_cache_metrics(cache_stats: dict) -> None:
    """更新缓存指标"""
    cache_size.labels(cache_type="query").set(cache_stats.get("size", 0))


async def metrics_endpoint():
    """Prometheus指标端点"""
    from fastapi import Response

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# =============================================================================
# 搜索结果指标
# =============================================================================

# 搜索结果数量
search_results_count = Histogram(
    "athena_search_results_count",
    "Number of results returned per search",
    ["query_type"],  # query_type: vector, graph, keyword, hybrid
    buckets=(0, 1, 5, 10, 25, 50, 100, 250, 500, 1000),
)

# =============================================================================
# 扩展的向量搜索指标
# =============================================================================

# 向量搜索请求总数(按集合)
vector_search_requests_total = Counter(
    "athena_vector_search_requests_total",
    "Total number of vector search requests",
    ["collection_name", "status"],
)

# 向量搜索延迟
vector_search_latency_seconds = Histogram(
    "athena_vector_search_latency_seconds",
    "Vector search latency in seconds",
    ["collection_name"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# =============================================================================
# 知识图谱搜索指标
# =============================================================================

# 知识图谱搜索请求总数
graph_search_requests_total = Counter(
    "athena_graph_search_requests_total",
    "Total number of knowledge graph search requests",
    ["search_type", "status"],  # search_type: entity, relation, path
)

# 知识图谱搜索延迟
graph_search_latency_seconds = Histogram(
    "athena_graph_search_latency_seconds",
    "Knowledge graph search latency in seconds",
    ["search_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

# =============================================================================
# 关键词搜索指标
# =============================================================================

# 关键词搜索请求总数
keyword_search_requests_total = Counter(
    "athena_keyword_search_requests_total", "Total number of keyword search requests", ["status"]
)

# 关键词搜索延迟
keyword_search_latency_seconds = Histogram(
    "athena_keyword_search_latency_seconds",
    "Keyword search latency in seconds",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

# =============================================================================
# 数据库指标
# =============================================================================

# 数据库查询总数
db_queries_total = Counter(
    "athena_db_queries_total",
    "Total number of database queries",
    ["query_type", "status"],  # query_type: select, insert, update, delete
)

# 数据库连接池
db_connection_pool_size = Gauge(
    "athena_db_connection_pool_size", "Current database connection pool size"
)

db_connection_pool_active = Gauge(
    "athena_db_connection_pool_active", "Number of active database connections"
)

# =============================================================================
# Qdrant指标
# =============================================================================

# Qdrant请求总数
qdrant_requests_total = Counter(
    "athena_qdrant_requests_total",
    "Total number of Qdrant requests",
    ["operation", "status"],  # operation: search, upsert, delete, create_collection
)

# Qdrant集合文档数量
qdrant_collection_size = Gauge(
    "athena_qdrant_collection_size", "Number of vectors in Qdrant collection", ["collection_name"]
)

# =============================================================================
# 装饰器
# =============================================================================


def track_search(query_type: str = "hybrid") -> Any:
    """
    跟踪搜索请求的装饰器

    Args:
        query_type: 查询类型 (vector, graph, keyword, hybrid)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)

                # 记录结果数量
                if "total_found" in result:
                    search_results_count.labels(query_type=query_type).observe(
                        result["total_found"]
                    )

                return result

            except Exception as e:
                status = "error"
                logger.error(f"Search error: {e}")
                raise

            finally:
                # 记录请求总数
                search_requests_total.labels(intent=query_type, status=status).inc()

                # 记录延迟
                latency = time.time() - start_time
                search_duration_seconds.labels(intent=query_type).observe(latency)

                logger.debug(f"{query_type} search completed in {latency:.3f}s")

        return wrapper

    return decorator


# =============================================================================
# 健康检查
# =============================================================================


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        """初始化健康检查器"""
        self.checks = {}

    def register_check(self, name: str, check_func: Callable[[], bool]) -> Any:
        """
        注册健康检查

        Args:
            name: 检查名称
            check_func: 检查函数,返回True表示健康
        """
        self.checks[name] = check_func
        logger.info(f"Registered health check: {name}")

    async def check_health(self) -> dict[str, Any]:
        """
        执行所有健康检查

        Returns:
            健康检查结果字典
        """
        results = {"status": "healthy", "checks": {}, "timestamp": time.time()}

        all_healthy = True

        for name, check_func in self.checks.items():
            try:
                is_healthy = check_func()
                results["checks"][name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "last_check": time.time(),
                }

                if not is_healthy:
                    all_healthy = False

            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                results["checks"][name] = {
                    "status": "error",
                    "error": str(e),
                    "last_check": time.time(),
                }
                all_healthy = False

        results["status"] = "healthy" if all_healthy else "unhealthy"
        return results


# =============================================================================
# Prometheus监控服务器
# =============================================================================


class PrometheusServer:
    """Prometheus监控服务器"""

    def __init__(self, port: int = 9091):
        """
        初始化Prometheus服务器

        Args:
            port: 监控端点端口
        """
        self.port = port
        self.started = False

    def start(self) -> None:
        """启动Prometheus HTTP服务器"""
        if self.started:
            logger.warning(f"Prometheus server already started on port {self.port}")
            return

        try:
            start_http_server(self.port)
            self.started = True
            logger.info(f"✅ Prometheus metrics server started on port {self.port}")
            logger.info(f"📊 Metrics available at: http://localhost:{self.port}/metrics")

        except Exception as e:
            logger.error(f"❌ Failed to start Prometheus server: {e}")
            raise


# =============================================================================
# 全局实例
# =============================================================================

_global_health_checker: HealthChecker | None = None
_global_prometheus_server: PrometheusServer | None = None


def get_health_checker() -> HealthChecker:
    """获取全局健康检查器"""
    global _global_health_checker
    if _global_health_checker is None:
        _global_health_checker = HealthChecker()
    return _global_health_checker


def get_prometheus_server(port: int = 9091) -> PrometheusServer:
    """获取或创建Prometheus服务器"""
    global _global_prometheus_server
    if _global_prometheus_server is None:
        _global_prometheus_server = PrometheusServer(port=port)
    return _global_prometheus_server


# =============================================================================
# FastAPI健康检查端点
# =============================================================================


async def health_endpoint():
    """健康检查端点"""
    health_checker = get_health_checker()
    health_status = await health_checker.check_health()

    import json

    from fastapi import Response

    status_code = 200 if health_status["status"] == "healthy" else 503
    return Response(
        content=json.dumps(health_status, ensure_ascii=False, indent=2),
        status_code=status_code,
        media_type="application/json",
    )


async def readiness_endpoint():
    """就绪检查端点(Kubernetes就绪探针)"""
    # 检查关键组件是否就绪
    health_checker = get_health_checker()
    health_status = await health_checker.check_health()

    import json

    from fastapi import Response

    # 只检查关键组件
    critical_checks = ["database", "qdrant", "vector_model"]
    all_ready = all(
        health_status["checks"].get(check, {}).get("status") == "healthy"
        for check in critical_checks
        if check in health_status["checks"]
    )

    status_code = 200 if all_ready else 503
    return Response(
        content=json.dumps(
            {
                "ready": all_ready,
                "checks": {k: health_status["checks"].get(k) for k in critical_checks},
            },
            ensure_ascii=False,
            indent=2,
        ),
        status_code=status_code,
        media_type="application/json",
    )


async def liveness_endpoint():
    """存活检查端点(Kubernetes存活探针)"""
    import json

    from fastapi import Response

    # 简单的存活检查 - 如果进程能响应就是活着的
    return Response(
        content=json.dumps({"alive": True, "timestamp": time.time()}, ensure_ascii=False, indent=2),
        status_code=200,
        media_type="application/json",
    )


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "HealthChecker",
    # 类和函数
    "MetricsRecorder",
    "PrometheusServer",
    # 仪表
    "active_requests",
    # 信息
    "app_info",
    "cache_hits",
    "cache_misses",
    "cache_size",
    "db_connection_pool_active",
    "db_connection_pool_size",
    "db_queries_total",
    "get_health_checker",
    "get_metrics_recorder",
    "get_prometheus_server",
    "graph_search_latency_seconds",
    "graph_search_requests_total",
    "health_endpoint",
    "keyword_search_latency_seconds",
    "keyword_search_requests_total",
    "liveness_endpoint",
    # 端点
    "metrics_endpoint",
    "qdrant_collection_size",
    "qdrant_requests_total",
    "readiness_endpoint",
    # 直方图
    "search_duration_seconds",
    # 计数器
    "search_requests_total",
    "search_results_count",
    # 装饰器
    "track_search",
    "update_app_info",
    "update_cache_metrics",
    "vector_search_latency_seconds",
    "vector_search_requests_total",
]
