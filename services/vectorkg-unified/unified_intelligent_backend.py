#!/usr/bin/env python3
"""
统一智能后端服务
Unified Intelligent Backend Service

基于向量库+知识图谱的通用智能后端，支持多专业领域应用

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from domain_adapters import DomainAdapterFactory
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from vector_knowledge_infrastructure import get_vector_knowledge_infrastructure

from core.logging_config import setup_logging
from core.security.auth import ALLOWED_ORIGINS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 请求模型
class QueryRequest(BaseModel):
    query: str
    domain: str = "patent"  # 默认专利领域
    context: dict[str, Any] | None = None
    user_id: str | None = None
    application_id: str | None = None

class BatchQueryRequest(BaseModel):
    queries: list[QueryRequest]
    max_parallel: int = 5

class RuleExtractionRequest(BaseModel):
    text: str
    domain: str = "patent"
    rule_types: list[str] = []
    keywords: list[str] | None = None

class ChatRequest(BaseModel):
    message: str
    domain: str = "patent"
    context: dict[str, Any] | None = None
    conversation_id: str | None = None

# 创建FastAPI应用
app = FastAPI(
    title="统一智能后端服务",
    description="基于向量库+知识图谱的通用智能后端，支持多专业领域",
    version="2.0.0",
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

# 全局变量
infrastructure = None
adapters = {}

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global infrastructure, adapters

    logger.info("正在初始化统一智能后端...")

    # 初始化基础设施
    infrastructure = await get_vector_knowledge_infrastructure()

    # 初始化各领域适配器
    for domain in DomainAdapterFactory.get_supported_domains():
        adapters[domain.value] = DomainAdapterFactory.create_adapter(
            domain,
            infrastructure
        )
        logger.info(f"✅ {domain.value}领域适配器已初始化")

    logger.info("✅ 统一智能后端初始化完成")

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    global infrastructure
    if infrastructure:
        infrastructure.close()
    logger.info("统一智能后端服务已关闭")

# API端点

@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "统一智能后端服务",
        "architecture": "Vector Library + Knowledge Graph",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "supported_domains": [d.value for d in DomainAdapterFactory.get_supported_domains()],
        "features": {
            "vector_search": True,
            "graph_traversal": True,
            "hybrid_search": True,
            "domain_adaptation": True,
            "multi_domain_support": True
        }
    }

@app.post("/query")
async def domain_query(request: QueryRequest):
    """
    领域智能查询

    支持的领域：
    - patent: 专利领域
    - legal: 法律领域
    - medical: 医疗领域
    - technical: 技术领域
    """
    try:
        # 获取领域适配器
        adapter = adapters.get(request.domain)
        if not adapter:
            raise HTTPException(
                status_code=400,
                detail=f"不支持领域: {request.domain}。支持的领域: {list(adapters.keys())}"
            )

        # 处理查询
        response = await adapter.process_query(
            query=request.query,
            context=request.context or {}
        )

        # 添加请求元数据
        response["request_metadata"] = {
            "query_id": f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
            "domain": request.domain,
            "user_id": request.user_id,
            "application_id": request.application_id,
            "timestamp": datetime.now().isoformat()
        }

        return response

    except Exception as e:
        logger.error(f"领域查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}") from e

@app.post("/batch/query")
async def batch_domain_query(request: BatchQueryRequest):
    """批量领域查询"""
    try:
        # 限制批量查询数量
        if len(request.queries) > 50:
            raise HTTPException(status_code=400, detail="批量查询最多支持50个")

        # 并行处理查询
        semaphore = asyncio.Semaphore(request.max_parallel)

        async def process_single_query(query_req):
            async with semaphore:
                adapter = adapters.get(query_req.domain)
                if adapter:
                    return await adapter.process_query(
                        query=query_req.query,
                        context=query_req.context or {}
                    )
                else:
                    return {
                        "error": f"不支持领域: {query_req.domain}",
                        "query": query_req.query
                    }

        # 执行批量查询
        tasks = [process_single_query(q) for q in request.queries]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        processed_results = []
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                processed_results.append({
                    "error": str(result),
                    "query": request.queries[i].query
                })
            else:
                processed_results.append(result)

        return {
            "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
            "total_queries": len(request.queries),
            "successful_queries": len([r for r in processed_results if "error" not in r]),
            "processed_at": datetime.now().isoformat(),
            "results": processed_results
        }

    except Exception as e:
        logger.error(f"批量查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch query failed: {str(e)}") from e

@app.post("/rules/extract")
async def extract_domain_rules(request: RuleExtractionRequest):
    """提取领域规则"""
    try:
        # 获取领域适配器
        adapter = adapters.get(request.domain)
        if not adapter:
            raise HTTPException(
                status_code=400,
                detail=f"不支持领域: {request.domain}"
            )

        # 提取规则
        rules = adapter.extract_domain_rules(
            text=request.text,
            rule_types=request.rule_types
        )

        return {
            "domain": request.domain,
            "text_length": len(request.text),
            "rule_types": request.rule_types,
            **rules,
            "extraction_time": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"规则提取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rule extraction failed: {str(e)}") from e

@app.post("/chat/intelligent")
async def intelligent_chat(request: ChatRequest):
    """
    智能对话接口

    支持多领域智能对话，自动识别意图并调用相应的领域适配器
    """
    try:
        # 获取领域适配器
        adapter = adapters.get(request.domain)
        if not adapter:
            raise HTTPException(
                status_code=400,
                detail=f"不支持领域: {request.domain}"
            )

        # 处理对话
        response = await adapter.process_query(
            query=request.message,
            context=request.context or {}
        )

        # 添加对话元数据
        response["chat_metadata"] = {
            "conversation_id": request.conversation_id or f"conv_{uuid.uuid4().hex[:8]}",
            "domain": request.domain,
            "turn_id": uuid.uuid4().hex[:8],
            "timestamp": datetime.now().isoformat()
        }

        return response

    except Exception as e:
        logger.error(f"智能对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}") from e

@app.post("/search/hybrid")
async def universal_hybrid_search(request: dict):
    """
    通用混合搜索

    支持跨领域的向量检索+知识图谱推理
    """
    if not infrastructure:
        raise HTTPException(status_code=503, detail="Infrastructure not initialized")

    try:
        # 提取参数
        query_text = request.get('query', '')
        domain = request.get('domain', 'patent')
        collections = request.get('collections')

        # 如果没有指定集合，使用领域默认集合
        if not collections:
            adapter = adapters.get(domain)
            if adapter:
                collections = adapter._get_relevant_collections()

        # 执行混合搜索
        results = await infrastructure.hybrid_search(
            query_text=query_text,
            collections=collections,
            vector_threshold=request.get('vector_threshold', 0.7),
            max_vector_results=request.get('max_vector_results', 10),
            max_graph_paths=request.get('max_graph_paths', 5)
        )

        # 添加领域分析
        if domain in adapters:
            adapter = adapters[domain]
            domain_analysis = {
                "domain": domain,
                "intent": adapter._classify_intent(query_text) if hasattr(adapter, '_classify_intent') else "general",
                "relevant_collections": collections,
                "suggested_actions": adapter._get_suggested_actions(
                    adapter._classify_intent(query_text)
                ) if hasattr(adapter, '_get_suggested_actions') else []
            }
            results['domain_analysis'] = domain_analysis

        # 添加元数据
        results['query_metadata'] = {
            "query_length": len(query_text),
            "search_time": datetime.now().isoformat(),
            "domain": domain,
            "parameters": {
                "vector_threshold": request.get('vector_threshold', 0.7),
                "max_vector_results": request.get('max_vector_results', 10),
                "max_graph_paths": request.get('max_graph_paths', 5)
            }
        }

        return results

    except Exception as e:
        logger.error(f"混合搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}") from e

@app.get("/domains/list")
async def list_supported_domains():
    """获取支持的领域列表"""
    domains_info = []
    for domain in DomainAdapterFactory.get_supported_domains():
        adapter = adapters.get(domain.value)
        domains_info.append({
            "domain": domain.value,
            "name": domain.value.title(),
            "supported": adapter is not None,
            "vector_collections": adapter._get_relevant_collections() if adapter else [],
            "knowledge_graphs": adapter._get_relevant_knowledge_graphs() if adapter else []
        })

    return {
        "total_domains": len(domains_info),
        "domains": domains_info,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/infrastructure/stats")
async def get_infrastructure_stats():
    """获取基础设施统计"""
    if not infrastructure:
        raise HTTPException(status_code=503, detail="Infrastructure not initialized")

    stats = await infrastructure.get_infrastructure_stats()

    # 添加领域统计
    stats['domains'] = {
        "total": len(adapters),
        "active": len([a for a in adapters.values() if a is not None]),
        "list": [domain for domain in adapters.keys() if adapters[domain] is not None]
    }

    return stats

@app.get("/health")
async def health_check():
    """健康检查"""
    health_status = {
        "status": "healthy" if infrastructure else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "infrastructure": infrastructure is not None,
        "active_adapters": len([a for a in adapters.values() if a is not None]),
        "total_adapters": len(adapters)
    }

    # 检查各适配器状态
    adapter_status = {}
    for domain, adapter in adapters.items():
        adapter_status[domain] = {
            "loaded": adapter is not None,
            "collections": len(adapter._get_relevant_collections()) if adapter else 0,
            "knowledge_graphs": len(adapter._get_relevant_knowledge_graphs()) if adapter else 0
        }

    health_status["adapters"] = adapter_status

    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)  # 内网通信
