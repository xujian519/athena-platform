#!/usr/bin/env python3
from __future__ import annotations
"""
雅典娜知识图谱系统生产环境API主程序
Production API Main Entry Point for Athena Knowledge Graph System
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

from core.async_main import async_main
from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 加载环境变量
from dotenv import load_dotenv

load_dotenv()

try:
    import uvicorn
    from fastapi import FastAPI, Request, Response, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles

    # 导入安全中间件
    try:
        from core.middleware.csrf import CSRFProtection
        from core.middleware.rate_limit import MemoryRateLimiter, RateLimitConfig

        SECURITY_MIDDLEWARE_AVAILABLE = True
    except ImportError:
        print("⚠️ 安全中间件未找到")
        SECURITY_MIDDLEWARE_AVAILABLE = False

    FASTAPI_AVAILABLE = True

    # 导入API版本控制系统
    from core.api.versioning import (
        APIResponse,
        APIVersion,
        deprecated_v1,
        setup_versioning,
    )

    VERSIONING_AVAILABLE = True

    # 导入意图识别服务路由
    try:

        INTENT_SERVICE_AVAILABLE = True
    except ImportError:
        print("⚠️ 意图识别服务路由未找到")
        INTENT_SERVICE_AVAILABLE = False
except ImportError:
    print("❌ FastAPI未安装,无法启动API服务")
    FASTAPI_AVAILABLE = False
    VERSIONING_AVAILABLE = False
    INTENT_SERVICE_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.getenv("LOG_FILE", "/tmp/athena-kg.log")),
        logging.StreamHandler(),
    ],
)
logger = setup_logging()


class ProductionAPI:
    """生产环境API"""

    def __init__(self):
        self.app = None
        self.components = {}
        self.version_router = None
        self.performance_optimizer = None
        self.rate_limiter = None
        self.csrf_protection = None

        if FASTAPI_AVAILABLE:
            self._create_app()
            self._setup_middleware()
            self._setup_versioning()
            self._register_routes()
            self._mount_static_files()

    def _create_app(self) -> Any:
        """创建FastAPI应用"""
        self.app = FastAPI(
            title="雅典娜知识图谱系统",
            description="Athena Knowledge Graph System - Production API",
            version=os.getenv("APP_VERSION", "v2.0.0"),
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
        )

        # ⚠️ 重要:必须在注册路由之前进行FastAPI插桩
        # 这样OpenTelemetry才能自动追踪所有HTTP请求
        self._setup_tracing_instrumentation()

        # 注册启动事件 - 启用性能优化(不包含追踪,追踪已在上一步设置)
        @self.app.on_event("startup")
        async def startup_event():
            """应用启动时执行"""
            logger.info("🚀 雅典娜知识图谱系统启动中...")

            # 启用性能优化(不包含分布式追踪,已在 _setup_tracing_instrumentation 中处理)
            await self._enable_performance_optimizations_without_tracing()

            logger.info("✅ 雅典娜知识图谱系统已启动")

        # 注册关闭事件
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """应用关闭时执行"""
            logger.info("⏹️ 雅典娜知识图谱系统关闭中...")

            # 关闭性能优化器
            await self._disable_performance_optimizations()

            logger.info("✅ 雅典娜知识图谱系统已关闭")

    def _setup_middleware(self) -> Any:
        """设置中间件"""
        # CORS中间件配置 - 从环境变量读取
        cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
        cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]
        cors_allow_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
        cors_allow_methods = os.getenv("CORS_ALLOW_METHODS", "*")
        cors_allow_headers = os.getenv("CORS_ALLOW_HEADERS", "*")

        # 开发环境允许所有来源
        if os.getenv("APP_ENV", "development") == "development":
            cors_origins = ["*"]

        # CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=cors_allow_credentials,
            allow_methods=cors_allow_methods.split(",") if cors_allow_methods != "*" else ["*"],
            allow_headers=cors_allow_headers.split(",") if cors_allow_headers != "*" else ["*"],
        )

        # 可信主机中间件配置
        allowed_hosts_str = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
        allowed_hosts = [host.strip() for host in allowed_hosts_str.split(",")]

        # 开发环境允许所有主机
        if os.getenv("APP_ENV", "development") == "development":
            allowed_hosts = ["*"]

        # 可信主机中间件
        self.app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

        # 初始化速率限制器(如果安全中间件可用)
        if (
            SECURITY_MIDDLEWARE_AVAILABLE
            and os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        ):
            try:
                rate_limit_config = RateLimitConfig(
                    requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
                    requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "1000")),
                    requests_per_day=int(os.getenv("RATE_LIMIT_PER_DAY", "10000")),
                )
                self.rate_limiter = MemoryRateLimiter(rate_limit_config)

                # 添加速率限制中间件
                @self.app.middleware("http")
                async def rate_limit_middleware(request: Request, call_next):
                    """速率限制中间件"""
                    # 跳过健康检查和文档
                    if request.url.path in ["/health", "/docs", "/openapi.json", "/metrics"]:
                        return await call_next(request)

                    # 检查速率限制
                    is_allowed, _retry_after = await self.rate_limiter.check_rate_limit(request)
                    if not is_allowed:
                        return JSONResponse(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            content={"detail": "请求过于频繁,请稍后再试"},
                        )

                    return await call_next(request)

                logger.info("✅ 速率限制中间件已启用")
            except Exception as e:
                logger.warning(f"⚠️ 速率限制中间件初始化失败: {e}")

        # 初始化CSRF保护(如果安全中间件可用且启用)
        if SECURITY_MIDDLEWARE_AVAILABLE and os.getenv("CSRF_ENABLED", "true").lower() == "true":
            try:
                csrf_secret = os.getenv("CSRF_SECRET")
                if csrf_secret:
                    self.csrf_protection = CSRFProtection(
                        secret=csrf_secret,
                        token_age=int(os.getenv("CSRF_TOKEN_AGE", "3600")),
                        secure=os.getenv("CSRF_SECURE", "false").lower() == "true",
                    )

                    # 添加CSRF保护中间件
                    @self.app.middleware("http")
                    async def csrf_middleware(request: Request, call_next):
                        """CSRF保护中间件"""
                        # 跳过 exempt 路径
                        if request.url.path in self.csrf_protection.exclude_paths:
                            return await call_next(request)

                        # 跳过GET、HEAD、OPTIONS方法(安全方法)
                        if request.method in ["GET", "HEAD", "OPTIONS"]:
                            return await call_next(request)

                        # 验证CSRF token
                        if not self.csrf_protection.validate_token(request):
                            return JSONResponse(
                                status_code=status.HTTP_403_FORBIDDEN,
                                content={"detail": "CSRF token验证失败"},
                            )

                        return await call_next(request)

                    logger.info("✅ CSRF保护中间件已启用")
                else:
                    logger.warning("⚠️ CSRF_SECRET未设置,CSRF保护未启用")
            except Exception as e:
                logger.warning(f"⚠️ CSRF保护中间件初始化失败: {e}")

    def _setup_versioning(self) -> Any:
        """设置API版本控制"""
        if VERSIONING_AVAILABLE:
            self.version_router = setup_versioning(self.app, default_version=APIVersion.V2)
            logger.info("✅ API版本控制系统已启用")

            # 创建v1和v2路由器
            self.v1_router = self.version_router.create_version_router(APIVersion.V1)
            self.v2_router = self.version_router.create_version_router(APIVersion.V2)

            # 注册路由器
            self.version_router.register_router(self.v1_router, APIVersion.V1)
            self.version_router.register_router(self.v2_router, APIVersion.V2)

            # 注册版本化端点
            self._register_versioned_endpoints()
        else:
            logger.warning("⚠️  API版本控制系统不可用")

    def _register_versioned_endpoints(self) -> Any:
        """注册版本化端点"""

        # === v2 API端点 ===

        @self.v2_router.post("/search")
        async def search_v2(request: Request):
            """v2搜索接口 - 增强版"""
            try:
                # 解析请求
                body = await request.json()
                query = body.get("query")
                domain = body.get("domain", "mixed")
                limit = body.get("limit", 10)
                body.get("filters", {})
                body.get("sort", None)

                if not query:
                    return JSONResponse(
                        APIResponse.error("validation_error", "Query is required", code=400),
                        status_code=400,
                    )

                # 使用统一向量管理器进行搜索
                from core.vector import UnifiedVectorManager

                vector_manager = UnifiedVectorManager()
                await vector_manager.initialize()

                search_result = await vector_manager.hybrid_search(query, domain, limit)

                return JSONResponse(
                    APIResponse.success(
                        data={
                            "results": search_result.get("results", []),
                            "total": search_result.get("total", 0),
                            "query": query,
                            "domain": search_result.get("domain", domain),
                        },
                        message="Search completed",
                        meta={
                            "response_time": search_result.get("response_time", 0),
                            "collections_searched": search_result.get("collections_searched", []),
                        },
                    )
                )

            except Exception as e:
                logger.error(f"搜索失败: {e}")
                return JSONResponse(
                    APIResponse.error("search_failed", str(e), code=500), status_code=500
                )

        @self.v2_router.post("/reason")
        async def reason_v2(request: Request):
            """v2推理接口 - 增强版"""
            try:
                # 解析请求
                body = await request.json()
                query = body.get("query")
                context = body.get("context")
                domain = body.get("domain", "mixed")
                reasoning_types = body.get("reasoning_types", ["rule_based", "semantic"])

                if not query:
                    return JSONResponse(
                        APIResponse.error("validation_error", "Query is required", code=400),
                        status_code=400,
                    )

                # 使用语义推理引擎
                from core.reasoning.semantic_reasoning_engine import (
                    SemanticReasoningEngine,
                )

                reasoning_engine = SemanticReasoningEngine()

                reasoning_results = await reasoning_engine.reason(
                    query=query,
                    context=context,
                    reasoning_types=[rt for rt in reasoning_types if isinstance(rt, str)],
                    domain=domain,
                )

                # 转换结果为可序列化格式
                serialized_results = []
                for result in reasoning_results:
                    serialized_results.append(
                        {
                            "reasoning_type": result.reasoning_type.value,
                            "conclusion": result.conclusion,
                            "confidence": result.confidence,
                            "evidence": result.evidence,
                            "reasoning_path": result.reasoning_path,
                            "metadata": result.metadata,
                            "timestamp": result.timestamp.isoformat(),
                        }
                    )

                return JSONResponse(
                    APIResponse.success(
                        data={
                            "reasoning_results": serialized_results,
                            "query": query,
                            "domain": domain,
                        },
                        message="Reasoning completed",
                    )
                )

            except Exception as e:
                logger.error(f"推理失败: {e}")
                return JSONResponse(
                    APIResponse.error("reasoning_failed", str(e), code=500), status_code=500
                )

        # === v1 API端点(兼容性) ===

        @self.v1_router.post("/search")
        @deprecated_v1("Use /api/v2/search instead")
        async def search_v1(request: Request):
            """v1搜索接口 - 已弃用"""
            try:
                # 解析请求
                body = await request.json()
                query = body.get("query")
                domain = body.get("domain", "mixed")
                limit = body.get("limit", 10)

                if not query:
                    return JSONResponse({"error": "Query is required"}, status_code=400)

                # 使用统一向量管理器进行搜索
                from core.vector import UnifiedVectorManager

                vector_manager = UnifiedVectorManager()
                await vector_manager.initialize()

                search_result = await vector_manager.hybrid_search(query, domain, limit)

                return JSONResponse(
                    {
                        "query": query,
                        "domain": domain,
                        "results": search_result.get("results", []),
                        "response_time": search_result.get("response_time", 0),
                        "collections_searched": search_result.get("collections_searched", []),
                    }
                )

            except Exception as e:
                logger.error(f"搜索失败: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.v1_router.post("/reason")
        @deprecated_v1("Use /api/v2/reason instead")
        async def reason_v1(request: Request):
            """v1推理接口 - 已弃用"""
            try:
                # 解析请求
                body = await request.json()
                query = body.get("query")
                context = body.get("context")
                domain = body.get("domain", "mixed")
                reasoning_types = body.get("reasoning_types", ["rule_based", "semantic"])

                if not query:
                    return JSONResponse({"error": "Query is required"}, status_code=400)

                # 使用语义推理引擎
                from core.reasoning.semantic_reasoning_engine import (
                    SemanticReasoningEngine,
                )

                reasoning_engine = SemanticReasoningEngine()

                reasoning_results = await reasoning_engine.reason(
                    query=query,
                    context=context,
                    reasoning_types=[rt for rt in reasoning_types if isinstance(rt, str)],
                    domain=domain,
                )

                # 转换结果为可序列化格式
                serialized_results = []
                for result in reasoning_results:
                    serialized_results.append(
                        {
                            "reasoning_type": result.reasoning_type.value,
                            "conclusion": result.conclusion,
                            "confidence": result.confidence,
                            "evidence": result.evidence,
                            "reasoning_path": result.reasoning_path,
                            "metadata": result.metadata,
                            "timestamp": result.timestamp.isoformat(),
                        }
                    )

                return JSONResponse(
                    {
                        "query": query,
                        "context": context,
                        "domain": domain,
                        "reasoning_results": serialized_results,
                    }
                )

            except Exception as e:
                logger.error(f"推理失败: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

    def _register_routes(self) -> Any:
        """注册路由"""

        @self.app.get("/")
        async def root():
            """根路径"""
            return HTMLResponse(
                """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>雅典娜知识图谱系统</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 500px;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
            font-size: 2.5em;
        }
        .status {
            color: #10b981;
            font-size: 1.2em;
            margin-bottom: 30px;
        }
        .links {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .link {
            background: #667eea;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            transition: background 0.3s ease;
        }
        .link:hover {
            background: #5a67d8;
        }
        .version {
            color: #666;
            font-size: 0.9em;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 雅典娜知识图谱系统</h1>
        <div class="status">✅ 生产环境运行中</div>
        <div class="links">
            <a href="/docs" class="link">📋 API文档</a>
            <a href="/dashboard" class="link">📊 监控仪表板</a>
            <a href="/api/health" class="link">💚 健康检查</a>
        </div>
        <div class="version">版本: """
                + os.getenv("APP_VERSION", "v2.0.0")
                + """</div>
    </div>
</body>
</html>
            """
            )

        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            health_status = {
                "status": "healthy",
                "service": os.getenv("APP_NAME", "athena-kg-system"),
                "version": os.getenv("APP_VERSION", "v2.0.0"),
                "environment": os.getenv("APP_ENV", "production"),
                "timestamp": str(asyncio.get_event_loop().time()),
                "components": {},
            }

            degraded_components = []

            # 检查统一向量管理器
            try:
                from core.vector import UnifiedVectorManager

                vector_manager = UnifiedVectorManager()
                # 修复: 检查正确的属性 bge_service 而非不存在的 embedding_model
                if vector_manager.bge_service is not None:
                    health_status["components"]["vector_manager"] = "healthy"
                    health_status["components"]["semantic_router"] = "healthy"
                else:
                    health_status["components"]["vector_manager"] = "degraded"
                    health_status["components"]["semantic_router"] = "degraded"
                    degraded_components.append("vector_manager")
            except Exception as e:
                logger.error(f"向量管理器健康检查异常: {e}")
                health_status["components"]["vector_manager"] = "error"
                health_status["components"]["semantic_router"] = "error"
                degraded_components.append("vector_manager")

            # 检查性能监控
            try:
                from core.monitoring.performance_monitor import (
                    get_performance_monitor,
                )

                monitor = await get_performance_monitor()
                if monitor:
                    health_status["components"]["performance_monitor"] = "healthy"
                else:
                    health_status["components"]["performance_monitor"] = "unhealthy"
                    degraded_components.append("performance_monitor")
            except Exception as e:
                logger.error(f"性能监控健康检查异常: {e}")
                health_status["components"]["performance_monitor"] = "error"
                degraded_components.append("performance_monitor")

            # 根据组件状态设置整体状态
            if degraded_components:
                health_status["status"] = "degraded"
                health_status["degraded_components"] = degraded_components

            return JSONResponse(health_status)

        @self.app.get("/dashboard")
        async def dashboard_redirect():
            """重定向到监控仪表板"""
            return HTMLResponse("""
<script>
// 自动重定向到监控仪表板
window.location.href = 'http://localhost:8899';
</script>
            """)

        @self.app.get("/api/components")
        async def get_components():
            """获取组件状态"""
            components = {
                "vector_manager": {
                    "name": "智能向量管理器",
                    "status": "initialized",
                    "description": "统一管理6个专业向量集合",
                },
                "semantic_router": {
                    "name": "智能语义路由器",
                    "status": "initialized",
                    "description": "基于查询内容的智能路由决策",
                },
                "domain_preprocessor": {
                    "name": "领域预处理器",
                    "status": "initialized",
                    "description": "法律和专利专业文本处理",
                },
                "legal_enhancer": {
                    "name": "法律知识图谱增强器",
                    "status": "initialized",
                    "description": "实时更新和语义推理能力",
                },
                "patent_vectorizer": {
                    "name": "专利规则向量化器",
                    "status": "initialized",
                    "description": "专利规则的专业向量化",
                },
                "reasoning_engine": {
                    "name": "语义推理引擎",
                    "status": "initialized",
                    "description": "多类型智能推理能力",
                },
                "performance_monitor": {
                    "name": "性能监控系统",
                    "status": "infrastructure/infrastructure/monitoring",
                    "description": "实时性能监控和可视化",
                },
            }

            return JSONResponse(components)

        @self.app.get("/api/metrics")
        async def get_metrics():
            """获取性能指标"""
            try:
                from core.monitoring.performance_monitor import (
                    get_performance_monitor,
                )

                monitor = await get_performance_monitor()
                if monitor:
                    dashboard_data = monitor.get_dashboard_data()
                    return JSONResponse(dashboard_data)
                else:
                    return JSONResponse({"error": "Performance monitor not available"})
            except Exception as e:
                logger.error(f"获取性能指标失败: {e}")
                return JSONResponse({"error": str(e)})

        @self.app.get("/api/performance/status")
        async def get_performance_status():
            """获取性能优化状态"""
            try:
                status = {
                    "performance_optimizations": {
                        "enabled": self.performance_optimizer is not None,
                    }
                }

                if self.performance_optimizer:
                    # 获取并发限制器状态
                    from core.performance.concurrency_control import get_limiters_status

                    limiters_status = get_limiters_status()
                    status["concurrency_limiters"] = limiters_status

                    # 获取批处理器状态
                    from core.performance.batch_processor import _batch_processors

                    status["batch_processors"] = {
                        name: {
                            "stats": processor.get_stats(),
                            "running": (
                                processor.stats.total_requests > 0
                                if hasattr(processor, "stats")
                                else False
                            ),
                        }
                        for name, processor in _batch_processors.items()
                    }

                return JSONResponse(status)
            except Exception as e:
                logger.error(f"获取性能状态失败: {e}")
                return JSONResponse({"error": str(e)})

        @self.app.get("/api/performance/stats")
        async def get_performance_stats():
            """获取详细性能统计"""
            try:
                stats = {"timestamp": str(asyncio.get_event_loop().time()), "optimizations": {}}

                if self.performance_optimizer:
                    # 获取各优化器的统计信息
                    from core.performance.concurrency_control import get_limiter

                    # API限流器统计
                    api_limiter = get_limiter("api_requests", max_concurrent=100)
                    stats["optimizations"]["api_limiter"] = api_limiter.get_stats()

                    # 数据库限流器统计
                    db_limiter = get_limiter("db_queries", max_concurrent=50)
                    stats["optimizations"]["db_limiter"] = db_limiter.get_stats()

                    # 速率限制器统计
                    rate_limiter = get_limiter("external_api_rate", max_concurrent=100)
                    stats["optimizations"]["rate_limiter"] = rate_limiter.get_stats()

                return JSONResponse(stats)
            except Exception as e:
                logger.error(f"获取性能统计失败: {e}")
                return JSONResponse({"error": str(e)})

        # === 旧版API端点(已弃用,保留向后兼容) ===

        @self.app.post("/api/search")
        async def search_legacy(request: Request):
            """旧版搜索接口 - 已弃用,请使用 /api/v2/search"""
            logger.warning("Legacy /api/search endpoint called")

            # 添加弃用警告响应头
            response = await self._legacy_search_handler(request)
            response.headers["X-API-Deprecation"] = (
                "This endpoint is deprecated. Use /api/v2/search instead."
            )
            response.headers["X-API-Migration-Guide"] = "/docs/api/v1-to-v2-migration"
            return response

        @self.app.post("/api/reason")
        async def reason_legacy(request: Request):
            """旧版推理接口 - 已弃用,请使用 /api/v2/reason"""
            logger.warning("Legacy /api/reason endpoint called")

            # 添加弃用警告响应头
            response = await self._legacy_reason_handler(request)
            response.headers["X-API-Deprecation"] = (
                "This endpoint is deprecated. Use /api/v2/reason instead."
            )
            response.headers["X-API-Migration-Guide"] = "/docs/api/v1-to-v2-migration"
            return response

        # ========== 专利全文处理服务 ==========
        try:
            from services.patent_full_text_service.api import register_patent_routes

            register_patent_routes(self.app)
            logger.info("✅ 专利全文处理API已注册")
        except ImportError:
            logger.warning("⚠️  专利全文处理服务未找到,跳过注册")
        except Exception as e:
            logger.error(f"❌ 专利全文处理API注册失败: {e}")

        # ========== Dolphin文档解析服务 ==========
        try:
            from core.api.dolphin_routes import register_dolphin_routes

            register_dolphin_routes(self.app)
            logger.info("✅ Dolphin文档解析API已注册")
        except ImportError:
            logger.warning("⚠️  Dolphin文档解析服务未找到,跳过注册")
        except Exception as e:
            logger.error(f"❌ Dolphin文档解析API注册失败: {e}")

        # ========== 统一报告服务 (Dolphin + NetworkX + Athena) ==========
        try:
            from core.api.unified_report_routes import register_unified_report_routes

            register_unified_report_routes(self.app)
            logger.info("✅ 统一报告服务API已注册 (Dolphin + NetworkX + Athena)")
        except ImportError:
            logger.warning("⚠️  统一报告服务未找到,跳过注册")
        except Exception as e:
            logger.error(f"❌ 统一报告服务API注册失败: {e}")

        # ========== IPC分类服务 ==========
        try:
            from core.api.ipc_routes import router as ipc_router

            self.app.include_router(ipc_router)
            logger.info("✅ IPC分类服务API已注册 (2026.01版)")
        except ImportError as e:
            logger.warning(f"⚠️  IPC分类服务未找到,跳过注册: {e}")
        except Exception as e:
            logger.error(f"❌ IPC分类服务API注册失败: {e}")

        # ========== 智能意图识别服务 ==========
        try:
            from core.api.intelligent_intent_routes import register_intelligent_intent_routes

            register_intelligent_intent_routes(self.app)
            logger.info("✅ 智能意图识别API已注册 (三层识别:规则+语义+深度)")
        except ImportError as e:
            logger.warning(f"⚠️  智能意图识别服务未找到,跳过注册: {e}")
        except Exception as e:
            logger.error(f"❌ 智能意图识别API注册失败: {e}")

        # ========== 意图识别服务 ==========
        try:
            from core.api.intent_routes import router as intent_router

            self.app.include_router(intent_router)
            logger.info("✅ 意图识别服务API已注册 (v1.0.0)")
        except ImportError as e:
            logger.warning(f"⚠️  意图识别服务未找到,跳过注册: {e}")
        except Exception as e:
            logger.error(f"❌ 意图识别服务API注册失败: {e}")

        # ========== Athena客户端支持 ==========
        try:
            from core.api.client_routes import router as client_router

            self.app.include_router(client_router)
            logger.info("✅ Athena客户端注册API已启用")
        except ImportError as e:
            logger.warning(f"⚠️  客户端注册API未找到,跳过注册: {e}")
        except Exception as e:
            logger.error(f"❌ 客户端注册API注册失败: {e}")

        try:
            from core.api.client_task_routes import router as client_tasks_router

            self.app.include_router(client_tasks_router)
            logger.info("✅ Athena客户端任务API已启用")
        except ImportError as e:
            logger.warning(f"⚠️  客户端任务API未找到,跳过注册: {e}")
        except Exception as e:
            logger.error(f"❌ 客户端任务API注册失败: {e}")

        # ========== 动态提示词系统 ==========
        try:
            from core.api.prompt_system_routes import router as prompt_system_router

            self.app.include_router(prompt_system_router)
            logger.info("✅ 动态提示词系统API已注册 (v2.0.0)")
        except ImportError as e:
            logger.warning(f"⚠️  动态提示词系统未找到,跳过注册: {e}")
        except Exception as e:
            logger.error(f"❌ 动态提示词系统API注册失败: {e}")

        # ========== 健康检查API ==========
        try:
            from core.api.health import router as health_router

            self.app.include_router(health_router)
            logger.info("✅ 健康检查API已注册")
        except ImportError as e:
            logger.warning(f"⚠️  健康检查API未找到,跳过注册: {e}")
        except Exception as e:
            logger.error(f"❌ 健康检查API注册失败: {e}")

        # ========== 专利AI服务API ==========
        try:
            from core.api.patent_ai_routes import register_patent_ai_routes

            register_patent_ai_routes(self.app)
            logger.info("✅ 专利AI服务API已注册 (分类/修订/无效性预测/质量评分)")
        except ImportError as e:
            logger.warning(f"⚠️  专利AI服务未找到,跳过注册: {e}")
        except Exception as e:
            logger.error(f"❌ 专利AI服务API注册失败: {e}")

    def _mount_static_files(self) -> Any:
        """挂载静态文件"""
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_dir), name="static"))

    def _setup_tracing_instrumentation(self):
        """
        设置分布式追踪插桩

        ⚠️ 重要:此方法必须在FastAPI app创建后立即调用,在注册路由之前!
        这样FastAPIInstrumentor才能自动拦截所有HTTP请求。
        """
        try:
            from core.tracing.opentelemetry_setup import OTEL_AVAILABLE, setup_tracing

            if not OTEL_AVAILABLE:
                logger.warning("⚠️  OpenTelemetry库未安装,跳过分布式追踪配置")
                self.tracing_manager = None
                return

            # 配置OpenTelemetry追踪
            self.tracing_manager = setup_tracing(
                service_name="athena-prompt-system",
                jaeger_host="127.0.0.1",
                jaeger_port=6831,
                instrument_fastapi=True,  # 对FastAPI进行插桩
                instrument_httpx=True,
                instrument_sqlalchemy=False,
                app=self.app,  # 传入app实例进行插桩
            )

            # 验证追踪是否真正启用
            if self.tracing_manager and self.tracing_manager.enabled:
                logger.info("✅ OpenTelemetry分布式追踪已配置")
                logger.info("   - 服务名称: athena-prompt-system")
                logger.info("   - Jaeger UI: http://localhost:16686")
                logger.info("   - FastAPI自动追踪: 已启用")
            else:
                logger.warning("⚠️  分布式追踪管理器创建失败")
                self.tracing_manager = None

        except Exception as e:
            logger.warning(f"⚠️  分布式追踪配置失败: {e}")
            import traceback

            logger.debug(traceback.format_exc())
            self.tracing_manager = None

    async def _enable_performance_optimizations_without_tracing(self):
        """启用性能优化(不包含分布式追踪,追踪已在 _setup_tracing_instrumentation 中处理)"""
        try:
            # 导入性能优化模块
            from scripts.enable_performance_optimizations import PerformanceOptimizer

            # 创建性能优化器实例
            self.performance_optimizer = PerformanceOptimizer()

            # 启用所有优化
            await self.performance_optimizer.enable_all()

            logger.info("✅ 性能优化已启用")
            logger.info("   - API限流: 100并发")
            logger.info("   - 数据库限流: 50并发")
            logger.info("   - 速率限制: 100请求/秒")

        except Exception as e:
            logger.error(f"❌ 性能优化启用失败: {e}")
            # 不阻止应用启动,性能优化失败不应影响核心功能
            self.performance_optimizer = None

    async def _disable_performance_optimizations(self):
        """禁用性能优化"""
        try:
            if self.performance_optimizer:
                # 关闭批处理器
                from core.performance.batch_processor import shutdown_all_batch_processors

                await shutdown_all_batch_processors()

                logger.info("✅ 性能优化已关闭")
        except Exception as e:
            logger.error(f"❌ 性能优化关闭失败: {e}")

    async def _legacy_search_handler(self, request: Request):
        """旧版搜索处理方法"""
        try:
            # 解析请求
            body = await request.json()
            query = body.get("query")
            domain = body.get("domain", "mixed")
            limit = body.get("limit", 10)

            if not query:
                return JSONResponse({"error": "Query is required"}, status_code=400)

            # 使用统一向量管理器进行搜索
            from core.vector import UnifiedVectorManager

            vector_manager = UnifiedVectorManager()
            await vector_manager.initialize()

            search_result = await vector_manager.hybrid_search(query, domain, limit)

            return JSONResponse(
                {
                    "query": query,
                    "domain": domain,
                    "results": search_result.get("results", []),
                    "response_time": search_result.get("response_time", 0),
                    "collections_searched": search_result.get("collections_searched", []),
                }
            )

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def _legacy_reason_handler(self, request: Request):
        """旧版推理处理方法"""
        try:
            # 解析请求
            body = await request.json()
            query = body.get("query")
            context = body.get("context")
            domain = body.get("domain", "mixed")
            reasoning_types = body.get("reasoning_types", ["rule_based", "semantic"])

            if not query:
                return JSONResponse({"error": "Query is required"}, status_code=400)

            # 使用语义推理引擎
            from core.reasoning.semantic_reasoning_engine import (
                SemanticReasoningEngine,
            )

            reasoning_engine = SemanticReasoningEngine()

            reasoning_results = await reasoning_engine.reason(
                query=query,
                context=context,
                reasoning_types=[rt for rt in reasoning_types if isinstance(rt, str)],
                domain=domain,
            )

            # 转换结果为可序列化格式
            serialized_results = []
            for result in reasoning_results:
                serialized_results.append(
                    {
                        "reasoning_type": result.reasoning_type.value,
                        "conclusion": result.conclusion,
                        "confidence": result.confidence,
                        "evidence": result.evidence,
                        "reasoning_path": result.reasoning_path,
                        "metadata": result.metadata,
                        "timestamp": result.timestamp.isoformat(),
                    }
                )

            return JSONResponse(
                {
                    "query": query,
                    "context": context,
                    "domain": domain,
                    "reasoning_results": serialized_results,
                }
            )

        except Exception as e:
            logger.error(f"推理失败: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def run(self, host: str = "0.0.0.0", port: int = 8000):
        """运行API服务"""
        if not FASTAPI_AVAILABLE:
            logger.error("FastAPI不可用,无法启动API服务")
            return

        # 配置uvicorn
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            workers=int(os.getenv("WORKERS", 4)),
            log_level=os.getenv("LOG_LEVEL", "info").lower(),
            access_log=True,
            use_colors=False,
            reload=False,  # 生产环境不使用reload
        )

        logger.info(f"🚀 启动生产环境API服务: http://{host}:{port}")
        logger.info(f"📋 API文档: http://{host}:{port}/docs")
        logger.info(f"💚 健康检查: http://{host}:{port}/health")

        # 运行服务器
        server = uvicorn.Server(config)
        await server.serve()


# 创建应用实例
def create_app() -> Any:
    """创建应用实例"""
    api = ProductionAPI()
    return api.app


# 全局应用实例
app = create_app()


# 主函数
@async_main
async def main():
    """主函数"""
    api = ProductionAPI()

    # 获取配置
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))

    # 运行服务
    await api.run(host, port)


if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        asyncio.run(main())
    else:
        print("❌ FastAPI未安装,无法启动服务")
        sys.exit(1)
