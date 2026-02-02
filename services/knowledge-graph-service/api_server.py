#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱服务 - 混合搜索API
结合JanusGraph和Qdrant的智能搜索服务
"""

import asyncio
from core.async_main import async_main
import json
import logging
from core.logging_config import setup_logging
import uvicorn
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 导入审查指南集成模块
from api.guideline_integration import GuidelineIntegration, add_guideline_routes

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="Athena知识图谱服务",
    description="结合JanusGraph和Qdrant的混合搜索API",
    version="1.0.0",
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

# 创建审查指南集成实例
guideline_integration = GuidelineIntegration()

# 注册审查指南路由
add_guideline_routes(app)

# 数据模型
class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询文本")
    entity_type: Optional[str] = Field(None, description="实体类型过滤")
    limit: int = Field(10, ge=1, le=100, description="返回结果数量")
    filters: Optional[Dict[str, Any]] = Field(None, description="额外过滤条件")

class GraphQueryRequest(BaseModel):
    gremlin: str = Field(..., description="Gremlin查询语句")
    explain: bool = Field(False, description="是否返回查询解释")

class RelationAnalysisRequest(BaseModel):
    entity_id: str = Field(..., description="起始实体ID")
    depth: int = Field(2, ge=1, le=5, description="搜索深度")
    relation_types: Optional[List[str]] = Field(None, description="关系类型过滤")

# 服务状态
service_status = {
    "service": "知识图谱混合搜索服务",
    "version": "1.0.0",
    "uptime": datetime.now().isoformat(),
    "apis": {
        "/health": "健康检查",
        "/api/v1/search/hybrid": "混合搜索",
        "/api/v1/search/vector": "向量搜索",
        "/api/v1/search/graph": "图搜索",
        "/api/v1/graph/query": "Gremlin查询",
        "/api/v1/analysis/relations": "关系分析"
    }
}

class HybridSearchEngine:
    """混合搜索引擎核心"""

    def __init__(self):
        self.qdrant_host = "localhost"
        self.qdrant_port = 6333
        self.janusgraph_url = "ws://localhost:8182/gremlin"
        self.collections = {
            "patents": "patent_vectors",
            "companies": "company_vectors",
            "technologies": "tech_vectors",
            "entities": "knowledge_graph_entities"
        }

    async def health_check(self) -> Dict:
        """健康检查"""
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }

        # 检查Qdrant
        try:
            import requests
            response = requests.get(f"http://{self.qdrant_host}:{self.qdrant_port}/health", timeout=5)
            health["services"]["qdrant"] = response.status_code == 200
        except (ConnectionError, OSError, asyncio.TimeoutError):
            health["services"]["qdrant"] = False

        # 检查JanusGraph
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("localhost", 8182))
            sock.close()
            health["services"]["janusgraph"] = result == 0
        except (ConnectionError, OSError, asyncio.TimeoutError):
            health["services"]["janusgraph"] = False

        # 整体状态
        if all(health["services"].values()):
            health["status"] = "healthy"
        else:
            health["status"] = "degraded"

        return health

    async def hybrid_search(self, request: SearchRequest) -> Dict:
        """混合搜索"""
        try:
            # 1. 向量搜索
            vector_results = await self._vector_search(request.query, request.limit)

            # 2. 图搜索（如果指定了实体类型）
            graph_results = []
            if request.entity_type:
                graph_results = await self._graph_search(request.entity_type)

            # 3. 融合结果
            merged_results = self._merge_results(vector_results, graph_results)

            return {
                "query": request.query,
                "entity_type": request.entity_type,
                "total_found": len(merged_results),
                "search_time_ms": 0,  # 实际实现中需要计算
                "results": merged_results,
                "stats": {
                    "vector_results": len(vector_results),
                    "graph_results": len(graph_results),
                    "merged_results": len(merged_results)
                }
            }

        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _vector_search(self, query: str, limit: int) -> List[Dict]:
        """执行向量搜索（模拟实现）"""
        # 这里应该连接到真实的Qdrant
        # 返回模拟结果用于演示
        return [
            {
                "id": "patent_001",
                "type": "Patent",
                "title": "基于深度学习的专利分析方法",
                "score": 0.95,
                "properties": {
                    "inventor": "张三",
                    "assignee": "Athena科技公司"
                }
            },
            {
                "id": "patent_002",
                "type": "Patent",
                "title": "智能专利检索系统",
                "score": 0.87,
                "properties": {
                    "inventor": "李四",
                    "assignee": "创新科技公司"
                }
            }
        ][:limit]

    async def _graph_search(self, entity_type: str) -> List[Dict]:
        """执行图搜索（模拟实现）"""
        # 这里应该连接到真实的JanusGraph
        # 返回模拟结果用于演示
        return [
            {
                "id": "company_001",
                "type": "Company",
                "name": "Athena科技公司",
                "relationships": [
                    {"type": "OWNS_PATENT", "target": "patent_001"},
                    {"type": "EMPLOYS", "target": "inventor_001"}
                ]
            },
            {
                "id": "company_002",
                "type": "Company",
                "name": "创新科技公司",
                "relationships": [
                    {"type": "OWNS_PATENT", "target": "patent_002"}
                ]
            }
        ]

    def _merge_results(self, vector_results: List[Dict], graph_results: List[Dict]) -> List[Dict]:
        """融合向量搜索和图搜索结果"""
        merged = []

        # 合并逻辑
        vector_ids = {r["id"] for r in vector_results}
        graph_ids = {r["id"] for r in graph_results}

        # 添加向量结果
        for result in vector_results:
            # 查找对应的图信息
            graph_info = next((g for g in graph_results if g["id"] == result["id"]), None)

            enhanced = result.copy()
            if graph_info:
                enhanced["graph_relationships"] = graph_info.get("relationships", [])
                enhanced["enhanced_score"] = result["score"] + 0.1  # 提升有图信息的分数
            else:
                enhanced["enhanced_score"] = result["score"]

            merged.append(enhanced)

        # 添加纯图结果
        for result in graph_results:
            if result["id"] not in vector_ids:
                merged.append({
                    **result,
                    "score": 0.7,  # 纯图结果的基础分数
                    "enhanced_score": 0.7,
                    "search_source": "graph_only"
                })

        # 按增强分数排序
        merged.sort(key=lambda x: x.get("enhanced_score", x.get("score", 0)), reverse=True)

        return merged

    async def execute_graph_query(self, request: GraphQueryRequest) -> Dict:
        """执行Gremlin查询"""
        try:
            # 这里应该连接到真实的JanusGraph执行Gremlin查询
            # 返回模拟结果用于演示

            # 模拟解析查询类型
            query_lower = request.gremlin.lower()
            if "v()" in query_lower:
                result_type = "vertex_query"
            elif "e()" in query_lower:
                result_type = "edge_query"
            elif "count()" in query_lower:
                result_type = "count_query"
            else:
                result_type = "general_query"

            return {
                "query": request.gremlin,
                "result_type": result_type,
                "execution_time_ms": 15,
                "results": [
                    {"id": "v1", "label": "Patent", "properties": {"title": "示例专利"}},
                    {"id": "v2", "label": "Company", "properties": {"name": "示例公司"}}
                ],
                "explain": request.explain
            }

        except Exception as e:
            logger.error(f"图查询失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def analyze_relations(self, request: RelationAnalysisRequest) -> Dict:
        """分析实体关系"""
        try:
            # 这里应该执行真正的关系分析
            # 返回模拟结果用于演示

            return {
                "entity_id": request.entity_id,
                "depth": request.depth,
                "relation_network": [
                    {
                        "id": "related_1",
                        "type": "Patent",
                        "relationship": "cites",
                        "distance": 1,
                        "weight": 0.8
                    },
                    {
                        "id": "related_2",
                        "type": "Company",
                        "relationship": "owns",
                        "distance": 2,
                        "weight": 0.6
                    }
                ],
                "analysis": {
                    "total_connections": 2,
                    "centrality_score": 0.75,
                    "cluster_coefficient": 0.3
                }
            }

        except Exception as e:
            logger.error(f"关系分析失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# API路由
@app.get("/")
async def root():
    """根路径"""
    return service_status

@app.get("/health")
async def health():
    """健康检查"""
    search_engine = HybridSearchEngine()
    return await search_engine.health_check()

@app.post("/api/v1/search/hybrid")
async def hybrid_search(request: SearchRequest):
    """混合搜索API"""
    search_engine = HybridSearchEngine()
    return await search_engine.hybrid_search(request)

@app.get("/api/v1/search/vector")
async def vector_search(
    query: str = Query(..., description="搜索查询"),
    limit: int = Query(10, ge=1, le=100, description="返回数量")
):
    """纯向量搜索"""
    request = SearchRequest(query=query, limit=limit)
    search_engine = HybridSearchEngine()

    # 只返回向量搜索结果
    vector_results = await search_engine._vector_search(query, limit)

    return {
        "query": query,
        "results": vector_results,
        "total": len(vector_results)
    }

@app.get("/api/v1/search/graph")
async def graph_search(
    entity_type: str = Query(..., description="实体类型"),
    limit: int = Query(10, ge=1, le=100, description="返回数量")
):
    """纯图搜索"""
    search_engine = HybridSearchEngine()
    graph_results = await search_engine._graph_search(entity_type)

    return {
        "entity_type": entity_type,
        "results": graph_results,
        "total": len(graph_results)
    }

@app.post("/api/v1/graph/query")
async def graph_query(request: GraphQueryRequest):
    """Gremlin查询API"""
    search_engine = HybridSearchEngine()
    return await search_engine.execute_graph_query(request)

@app.post("/api/v1/analysis/relations")
async def relation_analysis(request: RelationAnalysisRequest):
    """关系分析API"""
    search_engine = HybridSearchEngine()
    return await search_engine.analyze_relations(request)

@app.get("/api/v1/collections")
async def list_collections():
    """列出可用的向量集合"""
    search_engine = HybridSearchEngine()
    return {
        "collections": search_engine.collections,
        "total": len(search_engine.collections)
    }

@app.get("/api/v1/stats")
async def get_stats():
    """获取服务统计信息"""
    # 这里应该收集真实的统计数据
    return {
        "total_queries": 0,
        "avg_response_time": 0,
        "cache_hit_rate": 0,
        "active_collections": 0,
        "service_uptime": service_status["uptime"]
    }

# 启动配置
if __name__ == "__main__":
    import os

    # 获取端口配置
    port = int(os.getenv("PORT", 8080))

    logger.info("🚀 启动知识图谱混合搜索服务...")
    logger.info(f"📡 服务地址: http://localhost:{port}")
    logger.info("📖 API文档: http://localhost:{port}/docs")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )