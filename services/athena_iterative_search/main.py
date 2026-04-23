#!/usr/bin/env python3
"""
Athena迭代搜索服务
Athena Iterative Search Service
提供智能化的迭代搜索和查询优化功能
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 添加当前目录到Python路径
sys.path.append(str(Path(__file__).parent))

# 导入核心模块
from enhanced_core import AthenaSearchEngine
from external_search_engines import ExternalSearchEngines
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from llm_integration import LLMIntegration
from performance_optimizer import PerformanceOptimizer
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from core.security.auth import ALLOWED_ORIGINS

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class Settings(BaseSettings):
    """配置管理"""
    app_name: str = "Athena Iterative Search"
    version: str = "2.0.0"
    debug: bool = False
    port: int = 8008

    # 搜索引擎配置
    max_iterations: int = 5
    result_threshold: float = 0.8
    use_llm_enhancement: bool = True

    # 外部API配置
    google_api_key: str | None = None
    bing_api_key: str | None = None
    openai_api_key: str | None = None

    # 性能配置
    cache_enabled: bool = True
    cache_ttl: int = 3600
    parallel_search: bool = True

    class Config:
        env_file = ".env"

settings = Settings()

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="Athena平台智能迭代搜索服务",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求/响应模型
class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., description="搜索查询")
    search_type: str = Field("web", description="搜索类型: web, patent, academic")
    max_results: int = Field(10, description="最大结果数")
    iteration_config: dict[str, Any] = Field(default_factory=dict, description="迭代配置")

class IterativeSearchResponse(BaseModel):
    """迭代搜索响应"""
    query_id: str
    original_query: str
    optimized_queries: list[str]
    results: list[dict[str, Any]
    metadata: dict[str, Any]
    timestamp: str

# 服务实例管理
class SearchServiceManager:
    """搜索服务管理器"""

    def __init__(self):
        self.search_engine: AthenaSearchEngine | None = None
        self.llm_integration: LLMIntegration | None = None
        self.external_engines: ExternalSearchEngines | None = None
        self.performance_optimizer: PerformanceOptimizer | None = None

    async def initialize(self):
        """初始化所有组件"""
        try:
            # 初始化核心搜索引擎
            self.search_engine = AthenaSearchEngine()
            await self.search_engine.initialize()

            # 初始化LLM集成
            if settings.use_llm_enhancement and settings.openai_api_key:
                self.llm_integration = LLMIntegration(
                    api_key=settings.openai_api_key
                )
                await self.llm_integration.initialize()

            # 初始化外部搜索引擎
            self.external_engines = ExternalSearchEngines(
                google_api_key=settings.google_api_key,
                bing_api_key=settings.bing_api_key
            )
            await self.external_engines.initialize()

            # 初始化性能优化器
            self.performance_optimizer = PerformanceOptimizer(
                cache_enabled=settings.cache_enabled,
                cache_ttl=settings.cache_ttl
            )
            await self.performance_optimizer.initialize()

            logger.info("迭代搜索服务初始化完成")

        except Exception as e:
            logger.error(f"服务初始化失败: {e}")
            raise

    async def cleanup(self):
        """清理资源"""
        if self.search_engine:
            await self.search_engine.close()
        if self.llm_integration:
            await self.llm_integration.close()
        if self.external_engines:
            await self.external_engines.close()
        logger.info("服务资源清理完成")

search_manager = SearchServiceManager()

# 启动和关闭事件
@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    logger.info(f"启动 {settings.app_name} v{settings.version}")
    await search_manager.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理"""
    logger.info("正在关闭服务...")
    await search_manager.cleanup()

# API端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "running",
        "features": {
            "iterative_search": True,
            "llm_enhancement": settings.use_llm_enhancement,
            "external_engines": True,
            "performance_optimization": True
        },
        "message": "Athena迭代搜索服务运行正常",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """健康检查"""
    components = {
        "search_engine": search_manager.search_engine is not None,
        "llm_integration": search_manager.llm_integration is not None,
        "external_engines": search_manager.external_engines is not None,
        "performance_optimizer": search_manager.performance_optimizer is not None
    }

    all_healthy = all(components.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "components": components,
        "timestamp": datetime.now().isoformat()
    }

# 迭代搜索接口
@app.post("/api/v2/search/iterative", response_model=IterativeSearchResponse)
async def iterative_search(request: SearchRequest):
    """执行迭代搜索"""
    import uuid
    query_id = str(uuid.uuid4())

    try:
        # 1. 初始查询分析
        initial_analysis = await search_manager.search_engine.analyze_query(
            request.query,
            search_type=request.search_type
        )

        # 2. 查询优化
        optimized_queries = []
        if search_manager.llm_integration:
            optimized_queries = await search_manager.llm_integration.optimize_query(
                request.query,
                initial_analysis,
                num_variations=settings.max_iterations
            )

        # 3. 执行搜索
        all_results = []

        # 并行执行搜索
        if settings.parallel_search:
            tasks = []
            for query in optimized_queries + [request.query]:
                task = search_manager.search_engine.search(
                    query=query,
                    search_type=request.search_type,
                    max_results=request.max_results // (len(optimized_queries) + 1)
                )
                tasks.append(task)

            results_list = await asyncio.gather(*tasks)
            all_results = [result for sublist in results_list for result in sublist]
        else:
            # 串行搜索
            for query in [request.query] + optimized_queries:
                results = await search_manager.search_engine.search(
                    query=query,
                    search_type=request.search_type,
                    max_results=request.max_results
                )
                all_results.extend(results)

        # 4. 结果去重和排序
        if search_manager.performance_optimizer:
            all_results = await search_manager.performance_optimizer.deduplicate_and_rank(
                all_results,
                relevance_threshold=request.iteration_config.get("threshold", settings.result_threshold)
            )

        # 5. 限制结果数量
        all_results = all_results[:request.max_results]

        # 构建响应
        response = IterativeSearchResponse(
            query_id=query_id,
            original_query=request.query,
            optimized_queries=optimized_queries,
            results=all_results,
            metadata={
                "search_type": request.search_type,
                "iterations": len(optimized_queries),
                "total_found": len(all_results),
                "performance_metrics": {
                    "search_time": 0,  # TODO: 计算实际搜索时间
                    "cache_hits": 0,
                    "external_calls": 0
                }
            },
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"迭代搜索完成: {query_id} - 找到 {len(all_results)} 个结果")
        return response

    except Exception as e:
        logger.error(f"迭代搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post("/api/v2/search/enhanced")
async def enhanced_search(
    query: str,
    search_type: str = "web",
    use_llm: bool = True,
    max_results: int = 10
):
    """增强搜索（单次查询）"""
    request = SearchRequest(
        query=query,
        search_type=search_type,
        max_results=max_results,
        iteration_config={"use_llm": use_llm}
    )
    return await iterative_search(request)

@app.get("/api/v2/search/suggest")
async def get_query_suggestions(query: str, limit: int = 5):
    """获取查询建议"""
    try:
        if search_manager.llm_integration:
            suggestions = await search_manager.llm_integration.suggest_queries(
                query,
                limit=limit
            )
            return {
                "query": query,
                "suggestions": suggestions,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 简单的查询建议
            return {
                "query": query,
                "suggestions": [
                    f"{query} tutorial",
                    f"{query} examples",
                    f"{query} best practices",
                    f"{query} guide",
                    f"{query} documentation"
                ],
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"获取查询建议失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/api/v2/search/history")
async def get_search_history(limit: int = 50):
    """获取搜索历史"""
    # TODO: 实现搜索历史功能
    return {
        "history": [],
        "limit": limit,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v2/search/export")
async def export_results(
    query_id: str,
    format: str = "json",
    include_metadata: bool = True
):
    """导出搜索结果"""
    # TODO: 实现结果导出功能
    return {
        "query_id": query_id,
        "format": format,
        "include_metadata": include_metadata,
        "export_url": "",  # TODO: 生成导出文件URL
        "timestamp": datetime.now().isoformat()
    }

# 性能监控接口
@app.get("/api/v2/performance/metrics")
async def get_performance_metrics():
    """获取性能指标"""
    if search_manager.performance_optimizer:
        metrics = await search_manager.performance_optimizer.get_metrics()
        return {
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "metrics": {},
            "message": "Performance optimizer not initialized",
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/v2/performance/optimize")
async def optimize_performance():
    """执行性能优化"""
    if search_manager.performance_optimizer:
        result = await search_manager.performance_optimizer.optimize()
        return {
            "optimization_result": result,
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=503, detail="Performance optimizer not available")

# 配置接口
@app.get("/api/v2/config")
async def get_config():
    """获取当前配置"""
    return {
        "config": {
            "max_iterations": settings.max_iterations,
            "result_threshold": settings.result_threshold,
            "use_llm_enhancement": settings.use_llm_enhancement,
            "cache_enabled": settings.cache_enabled,
            "parallel_search": settings.parallel_search
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v2/config")
async def update_config(config_updates: dict[str, Any]):
    """更新配置"""
    try:
        # 更新允许的配置项
        allowed_keys = [
            "max_iterations", "result_threshold", "use_llm_enhancement",
            "cache_enabled", "parallel_search"
        ]

        for key, value in config_updates.items():
            if key in allowed_keys:
                setattr(settings, key, value)
                logger.info(f"配置更新: {key} = {value}")

        return {
            "message": "配置更新成功",
            "updated_keys": [k for k in config_updates.keys() if k in allowed_keys],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"配置更新失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

if __name__ == "__main__":
    import uvicorn
    logger.info(f"启动 {settings.app_name} v{settings.version}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug
    )
