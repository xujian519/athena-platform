#!/usr/bin/env python3
"""
专利智能检索API服务
Patent Intelligent Retrieval API Service

生产环境专利检索、语义分析、案例推荐API

作者: Athena AI系统
创建时间: 2025-12-22
版本: 1.0.0 (生产就绪)
"""

from __future__ import annotations
import logging

# Athena核心组件
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.security.auth import ALLOWED_ORIGINS

sys.path.append('/Users/xujian/Athena工作平台')

from core.knowledge.patent_analysis.knowledge_graph import PatentKnowledgeGraph
from core.nlp.universal_nlp_provider import TaskType, get_nlp_service
from core.nlp.xiaonuo_nlp_analyzer import XiaonuoNLPAnalyzer
from core.rag.athena_hybrid_rag_service import AthenaHybridRAGService, RAGQuery

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler('logs/patent_retrieval_api.log', encoding='utf-8'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI应用
app = FastAPI(
    title="专利智能检索API",
    description="基于NLP增强的专利检索、语义分析、案例推荐系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
rag_service = None
nlp_service = None
xiaonuo_analyzer = None
knowledge_graph = None

# 请求/响应模型
class PatentQueryRequest(BaseModel):
    """专利查询请求"""
    query: str = Field(..., description="查询内容", min_length=1, max_length=1000)
    top_k: int = Field(10, description="返回结果数量", ge=1, le=50)
    search_type: str = Field("hybrid", description="搜索类型", pattern="^(hybrid|vector|text|kg)$")
    patent_type: str | None = Field(None, description="专利类型过滤", pattern="^(invention|utility|design)$")
    date_range: dict[str, str] | None = Field(None, description="日期范围过滤")

class PatentQueryResponse(BaseModel):
    """专利查询响应"""
    query: str
    total_results: int
    processing_time: float
    results: list[dict[str, Any]]
    search_type: str
    nlp_enhanced: bool
    suggestions: list[str]

class SemanticAnalysisRequest(BaseModel):
    """语义分析请求"""
    text: str = Field(..., description="待分析文本", min_length=1, max_length=5000)
    analysis_type: str = Field("comprehensive", description="分析类型", pattern="^(comprehensive|intent|entities|sentiment)$")

class CaseRecommendationRequest(BaseModel):
    """案例推荐请求"""
    case_description: str = Field(..., description="案例描述", min_length=1, max_length=2000)
    similarity_threshold: float = Field(0.7, description="相似度阈值", ge=0.1, le=1.0)
    max_recommendations: int = Field(5, description="最大推荐数", ge=1, le=20)

class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: datetime
    services: dict[str, str]
    performance: dict[str, float]

# 系统统计
system_stats = {
    "total_queries": 0,
    "successful_queries": 0,
    "error_queries": 0,
    "avg_response_time": 0.0,
    "uptime": time.time()
}

async def initialize_services():
    """初始化核心服务"""
    global rag_service, nlp_service, xiaonuo_analyzer, knowledge_graph

    logger.info("🔄 初始化生产服务...")

    try:
        # RAG服务
        rag_service = AthenaHybridRAGService()
        logger.info("✅ RAG服务初始化成功")

        # NLP服务
        nlp_service = await get_nlp_service({
            'enable_glm': False,  # 生产环境优先使用本地服务
            'enable_local': True
        })
        logger.info("✅ NLP服务初始化成功")

        # 小诺分析器
        xiaonuo_analyzer = XiaonuoNLPAnalyzer()
        logger.info("✅ 小诺分析器初始化成功")

        # 知识图谱
        knowledge_graph = PatentKnowledgeGraph()
        logger.info("✅ 知识图谱服务初始化成功")

        logger.info("🎉 所有生产服务初始化完成")

    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    await initialize_services()

@app.get("/", response_model=dict[str, str])
async def root():
    """根路径"""
    return {
        "service": "专利智能检索API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """健康检查"""
    services_status = {}

    # 检查各服务状态
    try:
        if rag_service:
            services_status["rag"] = "healthy"
        else:
            services_status["rag"] = "unhealthy"
    except Exception as e:
        logger.debug(f"空except块已触发: {e}")
        services_status["rag"] = "error"

    try:
        if nlp_service:
            services_status["nlp"] = "healthy"
        else:
            services_status["nlp"] = "unavailable"
    except Exception as e:
        logger.debug(f"空except块已触发: {e}")
        services_status["nlp"] = "error"

    try:
        if knowledge_graph:
            services_status["knowledge_graph"] = "healthy"
    except Exception as e:
        logger.debug(f"空except块已触发: {e}")
        services_status["knowledge_graph"] = "error"

    # 计算性能指标
    uptime = time.time() - system_stats["uptime"]
    avg_time = system_stats["avg_response_time"]
    success_rate = (system_stats["successful_queries"] / max(system_stats["total_queries"], 1)) * 100

    overall_status = "healthy" if all(status == "healthy" for status in services_status.values()) else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.now(),
        services=services_status,
        performance={
            "uptime_seconds": uptime,
            "avg_response_time": avg_time,
            "success_rate": success_rate,
            "total_queries": system_stats["total_queries"]
        }
    )

@app.post("/api/v1/search", response_model=PatentQueryResponse)
async def search_patents(request: PatentQueryRequest):
    """专利检索"""
    start_time = time.time()
    system_stats["total_queries"] += 1

    try:
        logger.info(f"🔍 专利检索查询: {request.query[:100]}...")

        # 执行检索
        rag_query = RAGQuery(
            query=request.query,
            top_k=request.top_k,
            doc_types=[request.patent_type] if request.patent_type else None
        )

        # 根据搜索类型执行不同检索策略
        if request.search_type == "vector":
            response = await rag_service.search(rag_query)
        elif request.search_type == "text":
            response = await rag_service.search(rag_query)
        elif request.search_type == "kg":
            # 知识图谱搜索
            kg_results = await knowledge_graph.search_entities(request.query, limit=request.top_k)
            results = [
                {
                    "id": result["id"],
                    "title": result["title"],
                    "content": result["description"],
                    "type": result["type"],
                    "score": result.get("relevance", 0.8),
                    "metadata": result.get("properties", {})
                }
                for result in kg_results
            ]
            response = type('Response', (), {
                'reports/reports/results': results,
                'total_results': len(results),
                'processing_time': time.time() - start_time
            })()
        else:
            # 混合检索 (默认)
            response = await rag_service.search(rag_query)

        # 格式化结果
        formatted_results = []
        for result in response.results[:request.top_k]:
            formatted_results.append({
                "id": getattr(result, 'id', f"doc_{len(formatted_results)}"),
                "title": getattr(result, 'title', result.text[:100] + "..."),
                "content": getattr(result, 'text', str(result)),
                "score": getattr(result, 'score', 0.5),
                "metadata": getattr(result, 'metadata', {}),
                "source": getattr(result, 'source', 'patent_database')
            })

        # 生成查询建议
        suggestions = await generate_query_suggestions(request.query)

        processing_time = time.time() - start_time
        system_stats["successful_queries"] += 1
        system_stats["avg_response_time"] = (
            (system_stats["avg_response_time"] * (system_stats["successful_queries"] - 1) + processing_time)
            / system_stats["successful_queries"]
        )

        logger.info(f"✅ 检索完成: {len(formatted_results)} 个结果，耗时 {processing_time:.2f}秒")

        return PatentQueryResponse(
            query=request.query,
            total_results=len(formatted_results),
            processing_time=processing_time,
            results=formatted_results,
            search_type=request.search_type,
            nlp_enhanced=True,
            suggestions=suggestions
        )

    except Exception as e:
        system_stats["error_queries"] += 1
        logger.error(f"❌ 专利检索失败: {e}")
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}") from e

@app.post("/api/v1/semantic-analysis")
async def semantic_analysis(request: SemanticAnalysisRequest):
    """语义分析"""
    try:
        logger.info(f"🧠 语义分析: {request.text[:100]}...")

        start_time = time.time()

        if request.analysis_type == "comprehensive":
            # 综合分析
            nlp_result = await nlp_service.process(request.text, TaskType.PATENT_ANALYSIS)
            xiaonuo_result = await xiaonuo_analyzer.analyze_capability(request.text)

            result = {
                "nlp_analysis": nlp_result,
                "intent_analysis": xiaonuo_result,
                "analysis_type": "comprehensive"
            }
        elif request.analysis_type == "intent":
            # 意图分析
            result = await xiaonuo_analyzer.analyze_capability(request.text)
        elif request.analysis_type == "entities":
            # 实体分析
            result = await nlp_service.process(request.text, TaskType.PATENT_ANALYSIS)
        else:
            # 默认分析
            result = await nlp_service.process(request.text, TaskType.PATENT_ANALYSIS)

        processing_time = time.time() - start_time
        result["processing_time"] = processing_time

        logger.info(f"✅ 语义分析完成，耗时 {processing_time:.2f}秒")

        return result

    except Exception as e:
        logger.error(f"❌ 语义分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}") from e

@app.post("/api/v1/case-recommendation")
async def case_recommendation(request: CaseRecommendationRequest):
    """案例推荐"""
    try:
        logger.info(f"🎯 案例推荐: {request.case_description[:100]}...")

        start_time = time.time()

        # 使用语义检索查找相似案例
        rag_query = RAGQuery(
            query=request.case_description,
            top_k=request.max_recommendations
        )

        response = await rag_service.search(rag_query)

        # 过滤相似度
        recommendations = []
        for result in response.results:
            if getattr(result, 'score', 0) >= request.similarity_threshold:
                recommendations.append({
                    "id": getattr(result, 'id', f"case_{len(recommendations)}"),
                    "title": getattr(result, 'title', result.text[:100] + "..."),
                    "content": getattr(result, 'text', str(result)),
                    "similarity": getattr(result, 'score', 0.5),
                    "metadata": getattr(result, 'metadata', {}),
                    "recommendation_reason": "基于语义相似度匹配"
                })

        # 如果推荐数量不足，使用知识图谱补充
        if len(recommendations) < request.max_recommendations:
            kg_results = await knowledge_graph.search_entities(
                request.case_description,
                limit=request.max_recommendations - len(recommendations)
            )

            for kg_result in kg_results:
                recommendations.append({
                    "id": kg_result["id"],
                    "title": kg_result["title"],
                    "content": kg_result["description"],
                    "similarity": kg_result.get("relevance", 0.7),
                    "metadata": kg_result.get("properties", {}),
                    "recommendation_reason": "基于知识图谱关联"
                })

        processing_time = time.time() - start_time

        logger.info(f"✅ 案例推荐完成: {len(recommendations)} 个推荐，耗时 {processing_time:.2f}秒")

        return {
            "case_description": request.case_description,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "similarity_threshold": request.similarity_threshold,
            "processing_time": processing_time
        }

    except Exception as e:
        logger.error(f"❌ 案例推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}") from e

@app.get("/api/v1/stats")
async def get_system_stats():
    """获取系统统计"""
    uptime = time.time() - system_stats["uptime"]

    return {
        "system_stats": system_stats,
        "uptime_hours": uptime / 3600,
        "queries_per_hour": system_stats["total_queries"] / max(uptime / 3600, 1),
        "success_rate": (system_stats["successful_queries"] / max(system_stats["total_queries"], 1)) * 100,
        "error_rate": (system_stats["error_queries"] / max(system_stats["total_queries"], 1)) * 100
    }

async def generate_query_suggestions(query: str) -> list[str]:
    """生成查询建议"""
    suggestions = []

    try:
        # 基于小诺分析器生成建议
        xiaonuo_result = await xiaonuo_analyzer.analyze_capability(f"为以下查询生成3个相关建议: {query}")

        # 简单提取建议关键词
        if isinstance(xiaonuo_result, dict) and "tool_selection" in xiaonuo_result:
            tool_selection = xiaonuo_result["tool_selection"]
            if hasattr(tool_selection, "selected_tools") and tool_selection.selected_tools:
                for tool in tool_selection.selected_tools[:3]:
                    if hasattr(tool, "name"):
                        suggestions.append(f"{tool.name} 相关专利")

        # 默认建议
        if not suggestions:
            if "专利" not in query:
                suggestions.append(f"{query} 相关专利")
            if "发明" not in query and "创造" not in query:
                suggestions.append(f"{query} 发明专利")
            if "申请" not in query:
                suggestions.append(f"{query} 专利申请")

    except Exception as e:
        logger.warning(f"生成查询建议失败: {e}")
        suggestions = [f"{query} 相关专利", f"{query} 法律规定", f"{query} 审查指南"]

    return suggestions[:5]

if __name__ == "__main__":
    # 确保日志目录存在
    Path("logs").mkdir(exist_ok=True)

    # 启动生产服务
    uvicorn.run(
        "patent_retrieval_api:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # 生产环境多进程
        reload=False,  # 生产环境关闭热重载
        access_log=True,
        log_level="info"
    )
