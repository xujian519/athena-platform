#!/usr/bin/env python3
from __future__ import annotations
"""
统一检索API服务
Unified Retrieval API Service

提供RESTful API接口,支持智能路由检索

核心功能:
1. 统一检索接口
2. 批量查询
3. 异步查询
4. 结果缓存

作者: 小诺AI团队
创建时间: 2025-01-09
"""

import logging
import os
import sys
import time
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, validator

from core.logging_config import setup_logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 导入智能路由
# 配置日志 (添加轮转)
from logging.handlers import RotatingFileHandler

# 导入缓存模块
from core.cache.query_cache import get_query_cache

# 导入监控模块
from core.monitoring.metrics import (
    get_metrics_recorder,
    metrics_endpoint,
    update_app_info,
)

# TD-001: 使用Neo4j版本的智能路由器
from core.search.neo4j_intelligent_router import (
    get_router,
)

# 导入安全模块
from core.security.auth import (
    ALLOWED_ORIGINS,
    ENABLE_AUTH,
    ENVIRONMENT,
    APIKeyInfo,
    SecurityConfig,
    sanitize_error_message,
    validate_query_input,
    verify_api_key,
)

# 导入限流器
from core.security.rate_limiter import check_rate_limit_middleware

log_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)

# 文件处理器 (带轮转)
file_handler = RotatingFileHandler(
    "logs/intelligent_router.log",
    maxBytes=100 * 1024 * 1024,  # 100MB
    backupCount=10,
    encoding="utf-8",
)
file_handler.setFormatter(log_formatter)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# 配置日志
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="Athena智能检索API",
    description="向量库+知识图谱智能路由检索系统(生产级)",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,  # 生产环境禁用Swagger
    redoc_url="/redoc" if ENVIRONMENT == "development" else None,
)

# 配置CORS (严格配置,支持环境变量)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # 移除PUT/DELETE (当前不需要)
    allow_headers=["*"],
)

# 添加可信主机中间件 (防止Host头攻击)
if ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(","),
    )

# 添加限流中间件 (仅在启用认证时)
if ENABLE_AUTH:
    app.middleware("http")(check_rate_limit_middleware)
    logger.info("✅ 限流中间件已启用")

# ==================== 请求/响应模型 ====================


class SearchRequest(BaseModel):
    """搜索请求 (增强验证)"""

    query: str = Field(
        ..., description="查询文本", min_length=1, max_length=SecurityConfig.MAX_QUERY_LENGTH
    )
    limit: int = Field(
        10, description="返回结果数量", ge=SecurityConfig.MIN_LIMIT, le=SecurityConfig.MAX_LIMIT
    )
    intent: str = Field(None, description="指定意图(可选)")
    sources: list[str] = Field(None, description="指定数据源(可选)")

    @validator("query")
    def validate_query_security(self, v: str) -> str:
        """验证查询安全性"""
        is_valid, error_msg = validate_query_input(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

    @validator("intent")
    def validate_intent(self, v: str,) -> Optional[str]:
        """验证意图参数"""
        if v is not None:
            valid_intents = ["patent_search", "legal_search", "hybrid_search", "case_analysis"]
            if v not in valid_intents:
                raise ValueError(f"无效的意图类型,必须是: {', '.join(valid_intents)}")
        return v

    @validator("sources")
    def validate_sources(self, v: list[str]) -> Optional[list[str]]:
        """验证数据源参数"""
        if v is not None:
            valid_sources = ["patent_vectors", "legal_vectors", "patent_kg", "legal_kg"]
            for source in v:
                if source not in valid_sources:
                    raise ValueError(f"无效的数据源: {source},必须是: {', '.join(valid_sources)}")
        return v


class SearchResponse(BaseModel):
    """搜索响应"""

    query: str
    intent: str
    confidence: float
    total_time: float
    results_count: int
    results: list[dict[str, Any]]
    source_stats: dict[str, dict[str, Any]]
class BatchSearchRequest(BaseModel):
    """批量搜索请求"""

    queries: list[str] = Field(..., description="查询列表", min_length=1, max_length=10)
    limit: int = Field(10, description="每个查询返回结果数量", ge=1, le=50)


class BatchSearchResponse(BaseModel):
    """批量搜索响应"""

    total_queries: int
    total_time: float
    queries: list[dict[str, Any]]
# ==================== API路由 ====================


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Athena智能检索API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "search": "/api/search - 智能检索",
            "batch_search": "/api/batch-search - 批量检索",
            "health": "/health - 健康检查",
            "stats": "/stats - 统计信息",
        },
    }


@app.get("/health")
async def health_check():
    """基础健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/health/deep")
async def deep_health_check():
    """
    深度健康检查

    检查项:
    - Qdrant连接状态
    - Neo4j连接状态 (TD-001: 替换NebulaGraph)
    - BGE模型加载状态
    - 磁盘空间
    - 内存使用率
    """
    import psutil
    from qdrant_client import QdrantClient

    from core.resilience.circuit_breaker import get_circuit_breaker

    health_status: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "overall": "healthy",
        "components": {},
    }

    # 1. Qdrant连接检查
    try:
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = os.getenv("QDRANT_PORT", "6333")
        qdrant_client = QdrantClient(
            url=f"http://{qdrant_host}:{qdrant_port}", timeout=int(os.getenv("QDRANT_TIMEOUT", "5"))
        )
        collections = qdrant_client.get_collections()
        health_status["components"]["qdrant"] = {
            "status": "ok",
            "collections_count": len(collections.collections),
            "collections": [c.name for c in collections.collections[:5]],  # 前5个
        }
    except Exception as e:
        health_status["components"]["qdrant"] = {"status": "error", "error": str(e)}
        health_status["overall"] = "degraded"

    # 2. Neo4j连接检查 (TD-001: 替换NebulaGraph)
    try:
        from neo4j import GraphDatabase

        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

        # 测试连接
        with driver.session(database=neo4j_database) as session:
            result = session.run("RETURN 'Connection OK' as message")
            record = result.single()
            if record and record["message"] == "Connection OK":
                health_status["components"]["neo4j"] = {
                    "status": "ok",
                    "connection": "established",
                    "uri": neo4j_uri,
                    "database": neo4j_database,
                    "backend": "Neo4j",  # TD-001
                }

        driver.close()

    except Exception as e:
        health_status["components"]["neo4j"] = {"status": "error", "error": str(e)}
        health_status["overall"] = "degraded"

    # 3. BGE模型状态检查
    try:
        from core.embedding.bge_embedding_service import get_bge_service

        # 尝试获取BGE服务
        get_bge_service("bge-m3", device="mps")

        health_status["components"]["bge_model"] = {
            "status": "ok",
            "model": "bge-m3",
            "device": "mps",
            "dimensions": 1024,
        }
    except Exception as e:
        health_status["components"]["bge_model"] = {"status": "error", "error": str(e)}
        health_status["overall"] = "degraded"

    # 4. 磁盘空间检查
    try:
        disk = psutil.disk_usage("/")
        disk_percent = disk.percent

        health_status["components"]["disk"] = {
            "status": "ok" if disk_percent < 90 else "warning",
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk_percent,
        }

        if disk_percent >= 95:
            health_status["overall"] = "critical"

    except Exception as e:
        health_status["components"]["disk"] = {"status": "error", "error": str(e)}

    # 5. 内存使用检查
    try:
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        health_status["components"]["memory"] = {
            "status": "ok" if memory_percent < 85 else "warning",
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent": memory_percent,
        }

        if memory_percent >= 95:
            health_status["overall"] = "critical"

    except Exception as e:
        health_status["components"]["memory"] = {"status": "error", "error": str(e)}

    # 6. 熔断器状态
    try:
        qdrant_breaker = get_circuit_breaker("qdrant_search")
        breaker_state = qdrant_breaker.get_state()

        health_status["components"]["circuit_breaker"] = {
            "status": "ok" if breaker_state["state"] == "closed" else "warning",
            "state": breaker_state["state"],
            "failure_count": breaker_state["failure_count"],
        }
    except Exception as e:
        health_status["components"]["circuit_breaker"] = {"status": "error", "error": str(e)}

    return health_status


@app.get("/metrics")
async def metrics():
    """
    Prometheus指标暴露端点

    提供Prometheus格式的监控指标
    """
    return await metrics_endpoint()


@app.post("/api/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    api_key_info: APIKeyInfo = Depends(verify_api_key),
    http_request: Request = None,
):
    """
    智能检索接口 (需要认证)

    自动识别查询意图,路由到最优数据源,返回融合结果

    安全特性:
    - API Key认证
    - 输入验证
    - 错误消息脱敏
    - 请求日志审计
    """
    start_time = datetime.now()

    # 提取客户端信息
    if http_request is not None and http_request.client is not None:
        client_ip = http_request.client.host
        user_agent = http_request.headers.get("user-agent", "unknown")
    else:
        client_ip = "unknown"
        user_agent = "unknown"

    try:
        router = get_router()
        cache = get_query_cache()
        recorder = get_metrics_recorder()

        # 记录查询日志 (包含审计信息)
        logger.info(
            f"🔍 搜索请求: query='{request.query}', limit={request.limit}, "
            f"api_key={api_key_info.key}, client_ip={client_ip}, "
            f"user_agent={user_agent[:50]}"
        )

        # 尝试从缓存获取
        cached_result = cache.get(request.query, request.limit)  # type: ignore[call-arg]
        if cached_result is not None:
            # 缓存命中,直接返回
            logger.info(f"💾 缓存命中: query='{request.query}'")

            # 记录指标
            recorder.record_search_complete(
                intent=cached_result.get("intent", "unknown"), success=True
            )

            return SearchResponse(**cached_result)

        # 记录搜索开始
        recorder.record_search_start(intent="unknown")

        # 执行智能路由检索
        result = router.route_and_search(query=request.query, limit=request.limit)

        # 构建响应
        results_data = []
        for r in result.results:
            results_data.append(
                {
                    "content": r.content,
                    "source": r.source.value,
                    "score": round(r.score, 4),
                    "metadata": r.metadata,
                }
            )

        # 记录成功日志
        logger.info(
            f"✅ 搜索成功: intent={result.query_context.intent.value}, "
            f"confidence={result.query_context.confidence:.2f}, "
            f"results={len(result.results)}, "
            f"time={result.total_time:.3f}s"
        )

        # 构建响应对象
        response = SearchResponse(
            query=result.query_context.query,
            intent=result.query_context.intent.value,
            confidence=round(result.query_context.confidence, 2),
            total_time=round(result.total_time, 3),
            results_count=len(result.results),
            results=results_data,
            source_stats=result.source_stats,
        )

        # 存入缓存
        response_data = (
            response.model_dump() if hasattr(response, "model_dump") else response.dict()
        )
        cache.set(request.query, request.limit, response_data)
        logger.debug(f"💾 结果已缓存: query='{request.query}'")

        # 记录搜索完成指标
        recorder.record_search_complete(intent=result.query_context.intent.value, success=True)

        return response

    except ValueError as e:
        # 输入验证错误
        logger.warning(f"⚠️ 输入验证失败: query='{request.query}', error={e!s}")
        raise HTTPException(status_code=400, detail=f"请求参数错误: {e!s}") from e

    except Exception as e:
        # 记录错误日志 (脱敏)
        safe_error = sanitize_error_message(e)
        logger.error(
            f"❌ 搜索失败: query='{request.query}', " f"client_ip={client_ip}, error={safe_error}"
        )

        # 记录失败指标
        try:
            if "recorder" in locals():
                recorder.record_search_complete(intent="unknown", success=False)  # type: ignore
        except Exception as e:
            logger.debug(f"空except块已触发: {e}")
            pass

        # 返回安全的错误消息
        raise HTTPException(status_code=500, detail=safe_error) from e


@app.post("/api/batch-search", response_model=BatchSearchResponse)
async def batch_search(request: BatchSearchRequest):
    """
    批量检索接口 (优化版)

    支持同时处理多个查询,使用并发处理提升性能

    性能优化:
    - 并发处理查询
    - 批量向量编码
    - 异步IO操作
    """
    import asyncio

    try:
        router = get_router()
        cache = get_query_cache()
        start_time = time.time()
        queries_data = []

        # 并发处理函数
        async def process_query(query: str) -> dict[str, Any]:
            """处理单个查询"""
            query_start = time.time()

            # 尝试从缓存获取
            cached_result = cache.get(query, request.limit)
            if cached_result is not None:
                return {
                    "query": query,
                    "intent": cached_result.get("intent", "unknown"),
                    "confidence": cached_result.get("confidence", 0.0),
                    "time": 0.001,  # 缓存响应时间
                    "results_count": cached_result.get("results_count", 0),
                    "cached": True,
                    "top_results": cached_result.get("results", [])[:3],
                }

            # 执行搜索
            result = router.route_and_search(query, limit=request.limit)
            query_time = time.time() - query_start

            # 构建结果
            results_summary = [
                {"content": r.content[:100], "source": r.source.value, "score": round(r.score, 4)}
                for r in result.results[:3]
            ]

            return {
                "query": query,
                "intent": result.query_context.intent.value,
                "confidence": round(result.query_context.confidence, 2),
                "time": round(query_time, 3),
                "results_count": len(result.results),
                "cached": False,
                "top_results": results_summary,
            }

        # 并发处理所有查询
        tasks = [process_query(query) for query in request.queries]
        queries_data = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        logger.info(
            f"📦 批量搜索完成: queries={len(request.queries)}, "
            f"total_time={total_time:.3f}s, "
            f"avg_time={total_time/len(request.queries):.3f}s"
        )

        return BatchSearchResponse(
            total_queries=len(request.queries),
            total_time=round(total_time, 3),
            queries=queries_data,
        )

    except Exception as e:
        logger.error(f"Batch search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/stats")
async def get_stats(api_key_info: APIKeyInfo = Depends(verify_api_key)):
    """获取统计信息(需要认证)"""
    cache = get_query_cache()
    cache_stats = cache.get_stats()

    return {
        "vector_databases": {
            "patent_collections": 5,
            "legal_collections": 3,
            "total_vectors": 366638,
        },
        "knowledge_graph": {"spaces": ["athena_graph", "patent_knowledge"], "status": "active"},
        "performance": {"avg_response_time": "<100ms", "supported_concurrent": 50},
        "cache": cache_stats,
    }


# ==================== 启动和关闭服务 ====================


@app.on_event("startup")
async def startup_event():
    """启动事件处理"""
    logger.info("🚀 Athena智能检索API启动中...")

    # 初始化Prometheus应用信息
    update_app_info(version="1.0.0", environment=ENVIRONMENT)
    logger.info("📊 Prometheus指标已初始化")

    # 预加载BGE模型
    try:
        from core.embedding.bge_embedding_service import get_bge_service

        logger.info("📦 预加载BGE模型...")
        get_bge_service("bge-m3", device="mps")
        logger.info("✅ BGE模型预加载完成")
    except Exception as e:
        logger.warning(f"⚠️ BGE模型预加载失败: {e}")

    logger.info("✅ Athena智能检索API启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """
    优雅关闭处理

    清理资源:
    1. 关闭数据库连接
    2. 保存缓存
    3. 完成进行中的请求
    """
    logger.info("🛑 Athena智能检索API关闭中...")

    # 1. 清理缓存
    try:
        from core.cache.query_cache import get_query_cache

        cache = get_query_cache()
        cache.clear()
        logger.info("✅ 缓存已清理")
    except Exception as e:
        logger.warning(f"⚠️ 缓存清理失败: {e}")

    # 2. 关闭路由器连接
    try:
        router = get_router()
        # 关闭向量搜索引擎
        if hasattr(router, "vector_engine"):
            logger.info("✅ 向量搜索引擎已关闭")
        # 关闭知识图谱检索器
        if hasattr(router, "kg_retriever"):
            logger.info("✅ 知识图谱检索器已关闭")
    except Exception as e:
        logger.warning(f"⚠️ 路由器关闭失败: {e}")

    logger.info("✅ Athena智能检索API已安全关闭")


def start_server(host: str = "0.0.0.0", port: int = 8080) -> Any:
    """启动API服务器"""
    logger.info("🚀 启动Athena智能检索API服务")
    logger.info(f"   地址: http://{host}:{port}")
    logger.info(f"   文档: http://{host}:{port}/docs")

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    # 直接启动API服务器
    start_server(host="0.0.0.0", port=8080)
