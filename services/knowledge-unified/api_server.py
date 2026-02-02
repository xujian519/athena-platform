#!/usr/bin/env python3
"""
统一知识图谱API服务器
Unified Knowledge Graph API Server

提供RESTful API接口，支持各种专利应用调用

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
from core.async_main import async_main
import logging
from core.logging_config import setup_logging
import asyncio
from datetime import datetime
import uuid

# 导入服务
from integrated_patent_service import get_integrated_patent_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="专利知识图谱API服务",
    description="基于统一知识图谱的智能专利服务API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class PatentQuery(BaseModel):
    query: str = Field(..., description="用户查询问题")
    patent_text: Optional[str] = Field(None, description="专利文本内容")
    context_type: Optional[str] = Field("general", description="上下文类型")
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文信息")
    user_id: Optional[str] = Field(None, description="用户ID")
    application_id: Optional[str] = Field(None, description="应用ID")

class BatchQuery(BaseModel):
    queries: List[PatentQuery] = Field(..., description="批量查询列表")
    max_parallel: Optional[int] = Field(5, description="最大并行数")

class RuleExtraction(BaseModel):
    patent_text: str = Field(..., description="专利文本")
    rule_types: Optional[List[str]] = Field(["novelty", "creativity", "procedure"], description="规则类型")
    keywords: Optional[List[str]] = Field(None, description="指定关键词")

class SimilaritySearch(BaseModel):
    text: str = Field(..., description="搜索文本")
    similarity_threshold: Optional[float] = Field(0.7, description="相似度阈值")
    max_results: Optional[int] = Field(10, description="最大结果数")
    collection: Optional[str] = Field("patent_legal_vectors_1024", description="搜索集合")

# 全局服务实例
service = None

# 启动时初始化
@app.on_event("startup")
async def startup_event():
    global service
    logger.info("正在初始化知识图谱服务...")
    service = await get_integrated_patent_service()
    logger.info("✅ 知识图谱服务初始化完成")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("知识图谱API服务正在关闭...")

# API端点

@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "专利知识图谱API服务",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "query": "/query",
            "batch_query": "/batch/query",
            "extract_rules": "/rules/extract",
            "similarity_search": "/search/similarity",
            "statistics": "/stats"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        stats = await service.get_service_statistics()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service_stats": stats['statistics']
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/query")
async def query_knowledge(query: PatentQuery):
    """单个知识查询"""
    try:
        # 处理查询
        response = await service.process_patent_query(
            query=query.query,
            patent_text=query.patent_text or "",
            context=query.context or {},
            user_id=query.user_id
        )

        # 添加请求元数据
        response['request_metadata'] = {
            "application_id": query.application_id,
            "timestamp": datetime.now().isoformat()
        }

        return response

    except Exception as e:
        logger.error(f"查询处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.post("/batch/query")
async def batch_query(batch: BatchQuery):
    """批量知识查询"""
    try:
        # 限制批量大小
        if len(batch.queries) > 50:
            raise HTTPException(status_code=400, detail="Too many queries in batch (max 50)")

        # 处理批量查询
        results = await service.batch_process_queries([
            {
                "query": q.query,
                "patent_text": q.patent_text,
                "context": q.context,
                "user_id": q.user_id
            }
            for q in batch.queries
        ])

        return {
            "batch_id": str(uuid.uuid4()),
            "total_queries": len(batch.queries),
            "processed_at": datetime.now().isoformat(),
            "results": results
        }

    except Exception as e:
        logger.error(f"批量查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch query failed: {str(e)}")

@app.post("/rules/extract")
async def extract_rules(request: RuleExtraction):
    """提取专利规则"""
    try:
        # 获取相关规则
        rules = await service.knowledge_service.get_comprehensive_rules(
            request.patent_text
        )

        # 过滤规则类型
        if request.rule_types:
            rules = {
                rule_type: rule_list
                for rule_type, rule_list in rules.items()
                if rule_type in request.rule_types
            }

        return {
            "patent_text_length": len(request.patent_text),
            "extracted_rules": rules,
            "rule_count": sum(len(rules) for rules in rules.values()),
            "extraction_time": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"规则提取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rule extraction failed: {str(e)}")

@app.post("/search/similarity")
async def similarity_search(request: SimilaritySearch):
    """相似度搜索"""
    try:
        # 这里应该使用实际的向量搜索
        # 简化示例
        mock_results = [
            {
                "id": "doc_001",
                "content": "相似文档内容...",
                "similarity": 0.95,
                "metadata": {"type": "patent", "year": "2023"}
            },
            {
                "id": "doc_002",
                "content": "另一个相似文档...",
                "similarity": 0.87,
                "metadata": {"type": "guideline", "section": "novelty"}
            }
        ]

        return {
            "query": request.text,
            "collection": request.collection,
            "threshold": request.similarity_threshold,
            "results": mock_results[:request.max_results],
            "total_found": len(mock_results)
        }

    except Exception as e:
        logger.error(f"相似度搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Similarity search failed: {str(e)}")

@app.get("/stats")
async def get_statistics():
    """获取服务统计"""
    try:
        stats = await service.get_service_statistics()
        insights = await service.export_knowledge_insights()

        return {
            "service_statistics": stats,
            "knowledge_insights": insights,
            "system_status": "operational",
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")

@app.get("/capabilities")
async def get_capabilities():
    """获取服务能力"""
    return {
        "supported_intents": [
            "patent_review",
            "legal_advice",
            "technical_analysis",
            "patent_search",
            "patent_filing",
            "patent_value",
            "general_inquiry"
        ],
        "knowledge_sources": [
            {
                "name": "SQLite专利知识图谱",
                "size": "2.8GB",
                "entities": "125万+",
                "relations": "329万+"
            },
            {
                "name": "法律法规知识图谱",
                "entities": 45,
                "relations": 202
            },
            {
                "name": "审查指南向量库",
                "vectors": 53,
                "dimensions": 768
            },
            {
                "name": "专利法律向量库",
                "vectors": 191,
                "dimensions": 1024
            }
        ],
        "features": [
            "智能意图识别",
            "动态提示词生成",
            "规则自动提取",
            "相似度搜索",
            "批量处理",
            "上下文感知"
        ]
    }

# 中间件
@app.middleware("http")
async def add_process_time_header(request, call_next):
    """添加处理时间头"""
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

# 启动服务器
if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )