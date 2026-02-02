#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法律问答支持API
为小诺和所有智能体提供法律问答服务
作者: 小诺·双鱼座
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import logging
from datetime import datetime
import asyncio
import json
from contextlib import asynccontextmanager

from legal_kg_support import LegalKnowledgeGraphSupport
from dynamic_prompt_generator import LegalPromptGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 请求模型
class QueryRequest(BaseModel):
    query: str
    context: Dict | None = None
    agent_id: str | None = None
    session_id: str | None = None
    conversation_history: Optional[List[Dict] = None

class SearchRequest(BaseModel):
    query: str
    search_type: Optional[str] = "hybrid"  # vector, graph, hybrid
    top_k: Optional[int] = 10
    filters: Dict | None = None

class PromptRequest(BaseModel):
    query: str
    query_type: str | None = None
    context: Dict | None = None

# 响应模型
class LegalBasis(BaseModel):
    title: str
    content: str
    source: str
    score: float
    similarity: float | None = None

class QAResponse(BaseModel):
    answer: str
    legal_basis: List[LegalBasis]
    confidence: float
    suggestions: List[str]
    metadata: Dict

class SearchResponse(BaseModel):
    results: List[Dict]
    total: int
    query_time: float

class PromptResponse(BaseModel):
    prompt: str
    type: str
    legal_basis: List[LegalBasis]
    confidence: float
    suggestions: List[str]

# 全局变量
kg_support = None
prompt_generator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("🚀 启动小诺法律问答API服务...")

    global kg_support, prompt_generator
    try:
        # 初始化知识图谱支持系统
        kg_support = LegalKnowledgeGraphSupport()

        # 初始化提示词生成器
        prompt_generator = LegalPromptGenerator(kg_support)

        logger.info("✅ 服务初始化完成！")

        yield

    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
        raise
    finally:
        # 关闭时清理
        if kg_support:
            kg_support.close()
        logger.info("📴 服务已关闭")

# 创建FastAPI应用
app = FastAPI(
    title="小诺法律问答API",
    description="为小诺和智能体提供专业法律问答服务",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "xiaona-legal-qa",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# 法律问答接口
@app.post("/api/v1/qa", response_model=QAResponse)
async def legal_qa(request: QueryRequest):
    """法律问答接口"""
    start_time = datetime.now()

    try:
        # 获取对话支持
        support = kg_support.get_conversation_support(
            request.query,
            request.conversation_history
        )

        # 如果是外部智能体调用，生成动态提示词
        if request.agent_id:
            prompt_result = prompt_generator.generate_prompt(request.query, request.context)
            prompt = prompt_result["prompt"]
            legal_basis = [LegalBasis(**lb) for lb in prompt_result["legal_basis"]]
            confidence = prompt_result["confidence"]
            suggestions = prompt_generator.get_prompt_suggestions(request.query)
        else:
            # 小诺内部调用
            prompt = support.get("prompt", "")
            legal_basis = [LegalBasis(**lb) for lb in support.get("references", [])]
            confidence = 0.8
            suggestions = support.get("suggestions", [])

        # 这里可以调用LLM生成实际回答
        # 暂时返回提示词作为答案
        answer = prompt if not request.agent_id else await generate_answer_with_llm(prompt)

        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()

        return QAResponse(
            answer=answer,
            legal_basis=legal_basis,
            confidence=confidence,
            suggestions=suggestions,
            metadata={
                "agent_id": request.agent_id,
                "session_id": request.session_id,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat(),
                "support_type": support.get("type", "general_qa")
            }
        )

    except Exception as e:
        logger.error(f"问答处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 法律搜索接口
@app.post("/api/v1/search", response_model=SearchResponse)
async def legal_search(request: SearchRequest):
    """法律搜索接口"""
    start_time = datetime.now()

    try:
        # 执行搜索
        if request.search_type == "vector":
            results = kg_support.search_by_vector(request.query, request.top_k)
        elif request.search_type == "graph":
            results = kg_support.search_by_graph(request.query)
        else:  # hybrid
            results = kg_support.hybrid_search(request.query, request.top_k)

        # 应用过滤器
        if request.filters:
            results = apply_filters(results, request.filters)

        # 计算查询时间
        query_time = (datetime.now() - start_time).total_seconds()

        return SearchResponse(
            results=results,
            total=len(results),
            query_time=query_time
        )

    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 动态提示词生成接口
@app.post("/api/v1/prompt", response_model=PromptResponse)
async def generate_prompt(request: PromptRequest):
    """生成动态提示词接口"""
    try:
        # 生成提示词
        result = prompt_generator.generate_prompt(request.query, request.context)

        # 转换格式
        legal_basis = [LegalBasis(**lb) for lb in result["legal_basis"]]
        suggestions = prompt_generator.get_prompt_suggestions(request.query)

        return PromptResponse(
            prompt=result["prompt"],
            type=result["type"],
            legal_basis=legal_basis,
            confidence=result["confidence"],
            suggestions=suggestions
        )

    except Exception as e:
        logger.error(f"提示词生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 规则依据查询接口
@app.post("/api/v1/rules")
async def get_rule_basis(query: str):
    """获取规则依据"""
    try:
        rule_basis = prompt_generator.generate_rule_basis(query)
        return {
            "query": query,
            "rule_tree": rule_basis["rule_tree"],
            "summary": {
                "total_rules": rule_basis["total_rules"],
                "high_confidence": rule_basis["high_confidence_rules"],
                "categories": list(rule_basis["categorized_rules"].keys())
            }
        }

    except Exception as e:
        logger.error(f"规则依据查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 相关法律推荐接口
@app.get("/api/v1/related-laws/{law_title}")
async def get_related_laws(law_title: str):
    """获取相关法律"""
    try:
        related = kg_support.get_related_laws(law_title)
        return {
            "law_title": law_title,
            "related_laws": related,
            "count": len(related)
        }

    except Exception as e:
        logger.error(f"相关法律查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 智能体支持接口
@app.post("/api/v1/agent/support")
async def agent_support(request: QueryRequest):
    """为智能体提供支持"""
    try:
        # 获取增强的支持
        support = kg_support.get_conversation_support(
            request.query,
            request.conversation_history
        )

        # 生成专业提示词
        prompt_result = prompt_generator.generate_prompt(request.query, request.context)

        # 组合支持信息
        enhanced_support = {
            **support,
            "enhanced_prompt": prompt_result["prompt"],
            "rule_basis": prompt_generator.generate_rule_basis(request.query),
            "confidence": prompt_result["confidence"]
        }

        return enhanced_support

    except Exception as e:
        logger.error(f"智能体支持失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 批量查询接口
@app.post("/api/v1/batch/query")
async def batch_query(queries: List[str]):
    """批量查询接口"""
    try:
        results = []
        for query in queries:
            # 生成提示词
            prompt_result = prompt_generator.generate_prompt(query)

            # 搜索相关法律
            search_results = kg_support.hybrid_search(query, top_k=5)

            results.append({
                "query": query,
                "prompt": prompt_result["prompt"],
                "legal_basis": search_results,
                "confidence": prompt_result["confidence"]
            })

        return {
            "results": results,
            "total": len(queries)
        }

    except Exception as e:
        logger.error(f"批量查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 辅助函数
def apply_filters(results: List[Dict], filters: Dict) -> List[Dict]:
    """应用搜索过滤器"""
    filtered = results

    # 按来源过滤
    if "source" in filters:
        filtered = [r for r in filtered if r.get("source") in filters["source"]]

    # 按相似度过滤
    if "min_similarity" in filters:
        min_sim = filters["min_similarity"]
        filtered = [r for r in filtered if r.get("similarity", 0) >= min_sim]

    # 按类型过滤
    if "type" in filters:
        filtered = [r for r in filtered if r.get("type") in filters["type"]]

    return filtered

async def generate_answer_with_llm(prompt: str) -> str:
    """使用LLM生成答案（占位函数）"""
    # 这里可以集成各种LLM服务
    # 例如OpenAI、Claude、文心一言等

    # 暂时返回模拟答案
    return f"[基于提示词生成的答案]\n{prompt[:200]}..."

# 启动服务
if __name__ == "__main__":
    uvicorn.run(
        "legal_qa_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )