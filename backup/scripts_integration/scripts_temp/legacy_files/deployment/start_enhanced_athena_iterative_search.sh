#!/bin/bash

# 启动增强版Athena迭代式搜索系统

echo "🚀 启动Athena增强迭代式搜索系统..."

# 检查环境配置文件
ENV_FILE="/Users/xujian/Athena工作平台/services/athena_iterative_search/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  环境配置文件不存在，正在创建..."
    /Users/xujian/Athena工作平台/services/athena_iterative_search/environment_setup.sh
fi

# 加载环境变量
source "$ENV_FILE"

# 设置Python路径
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"

# 检查必要的Python包
echo "📦 检查Python依赖..."
REQUIRED_PACKAGES=("fastapi" "uvicorn" "elasticsearch" "psycopg2" "sentence_transformers" "faiss" "redis" "openai")

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python3 -c "import $package" 2>/dev/null; then
        echo "❌ 缺少依赖包: $package"
        echo "请运行: pip3 install $package"
        exit 1
    fi
done

# 检查服务状态
echo "🔍 检查服务状态..."

# PostgreSQL
if ! pg_isready -h $DB_HOST -p $DB_PORT >/dev/null 2>&1; then
    echo "⚠️  PostgreSQL未运行，请先启动PostgreSQL"
fi

# Redis
if ! redis-cli -h $REDIS_HOST -p $REDIS_PORT ping >/dev/null 2>&1; then
    echo "⚠️  Redis未运行，请先启动Redis"
fi

# Elasticsearch
if ! curl -s http://$ES_HOST:$ES_PORT/_cluster/health >/dev/null 2>&1; then
    echo "⚠️  Elasticsearch未运行，请先启动Elasticsearch"
fi

# 切换到服务目录
cd /Users/xujian/Athena工作平台/services/athena_iterative_search

# 创建日志目录
mkdir -p logs

# 创建增强版API服务文件
if [ ! -f "enhanced_api.py" ]; then
    echo "📝 创建增强版API服务..."
    cat > enhanced_api.py << 'EOF'
#!/usr/bin/env python3
"""
Athena增强迭代式搜索系统API服务
"""

import os
import sys
sys.path.append('/Users/xujian/Athena工作平台')

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# 导入增强搜索系统
from services.athena_iterative_search.enhanced_core import AthenaEnhancedIterativeSearchEngine
from services.athena_iterative_search.config_enhanced import (
    get_config_by_environment, SearchStrategy, SearchDepth
)
from services.athena_iterative_search.types import (
    PatentSearchResult, SearchSession, ResearchSummary
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全局搜索引擎实例
search_engine: Optional[AthenaEnhancedIterativeSearchEngine] = None

app = FastAPI(
    title="Athena增强迭代式搜索系统",
    description="基于Qwen LLM和多引擎融合的专利智能搜索系统",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API模型
class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询")
    strategy: str = Field("hybrid", description="搜索策略")
    max_results: int = Field(10, ge=1, le=100, description="最大结果数")
    filters: Optional[Dict[str, Any]] = Field(None, description="搜索过滤器")

class IterativeSearchRequest(BaseModel):
    initial_query: str = Field(..., description="初始查询")
    max_iterations: int = Field(3, ge=1, le=10, description="最大迭代次数")
    depth: str = Field("standard", description="搜索深度")
    focus_areas: Optional[List[str]] = Field(None, description="关注领域")

class CompetitiveAnalysisRequest(BaseModel):
    company_name: str = Field(..., description="公司名称")
    technology_domain: str = Field(..., description="技术领域")

# 启动事件
@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global search_engine
    try:
        logger.info("初始化增强搜索引擎...")
        search_engine = AthenaEnhancedIterativeSearchEngine()
        logger.info("搜索引擎初始化成功")
    except Exception as e:
        logger.error(f"搜索引擎初始化失败: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理"""
    global search_engine
    if search_engine:
        await search_engine.close()
        logger.info("搜索引擎已关闭")

# API端点
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

    # 检查各组件状态
    if search_engine:
        stats = await search_engine.get_statistics()
        health_data["services"] = {
            "search_engine": "running",
            "llm_provider": stats.get("llm_provider", "unknown"),
            "external_engines": stats.get("enabled_external_engines", [])
        }
    else:
        health_data["services"] = {
            "search_engine": "not_initialized"
        }

    return health_data

@app.post("/api/search", response_model=Dict[str, Any], tags=["搜索"])
async def search_patents(request: SearchRequest):
    """专利搜索"""
    if not search_engine:
        raise HTTPException(status_code=503, detail="搜索引擎未初始化")

    try:
        # 转换搜索策略
        strategy_map = {
            "hybrid": SearchStrategy.HYBRID,
            "fulltext": SearchStrategy.FULLTEXT,
            "semantic": SearchStrategy.SEMANTIC,
            "external": SearchStrategy.EXTERNAL
        }
        strategy = strategy_map.get(request.strategy, SearchStrategy.HYBRID)

        # 执行搜索
        results = await search_engine.search(
            query=request.query,
            strategy=strategy,
            max_results=request.max_results,
            filters=request.filters
        )

        # 转换结果为可序列化格式
        patents = []
        for result in results:
            patent_data = {
                "id": result.id,
                "title": result.title,
                "content": result.content,
                "score": result.score,
                "combined_score": result.combined_score,
                "similarity_score": result.similarity_score,
                "relevance": result.relevance.value,
                "engine_type": result.engine_type.value,
                "patent_metadata": None
            }

            if result.patent_metadata:
                patent_data["patent_metadata"] = {
                    "patent_id": result.patent_metadata.patent_id,
                    "patent_name": result.patent_metadata.patent_name,
                    "applicant": result.patent_metadata.applicant,
                    "ipc_code": result.patent_metadata.ipc_code,
                    "application_date": result.patent_metadata.application_date.isoformat() if result.patent_metadata.application_date else None
                }

            patents.append(patent_data)

        return {
            "success": True,
            "data": {
                "query": request.query,
                "strategy": request.strategy,
                "total_results": len(patents),
                "patents": patents
            }
        }

    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/iterative-search", response_model=Dict[str, Any], tags=["搜索"])
async def iterative_search(request: IterativeSearchRequest):
    """迭代式深度搜索"""
    if not search_engine:
        raise HTTPException(status_code=503, detail="搜索引擎未初始化")

    try:
        # 转换搜索深度
        depth_map = {
            "basic": SearchDepth.BASIC,
            "standard": SearchDepth.STANDARD,
            "deep": SearchDepth.DEEP,
            "comprehensive": SearchDepth.COMPREHENSIVE
        }
        depth = depth_map.get(request.depth, SearchDepth.STANDARD)

        # 执行迭代搜索
        session = await search_engine.iterative_search(
            initial_query=request.initial_query,
            max_iterations=request.max_iterations,
            depth=depth,
            focus_areas=request.focus_areas
        )

        # 保存会话
        await search_engine.save_session(session)

        # 转换结果
        iterations_data = []
        for iteration in session.iterations:
            iteration_data = {
                "iteration_number": iteration.iteration_number,
                "query": {
                    "text": iteration.query.text,
                    "original_text": iteration.query.original_text
                },
                "total_results": iteration.total_results,
                "quality_score": iteration.quality_score,
                "insights": iteration.insights,
                "next_query_suggestion": iteration.next_query_suggestion
            }
            iterations_data.append(iteration_data)

        # 研究摘要
        summary_data = None
        if session.research_summary:
            summary_data = {
                "key_findings": session.research_summary.key_findings,
                "main_patents": session.research_summary.main_patents,
                "technological_trends": session.research_summary.technological_trends,
                "competing_applicants": session.research_summary.competing_applicants,
                "innovation_insights": session.research_summary.innovation_insights,
                "recommendations": session.research_summary.recommendations,
                "confidence_level": session.research_summary.confidence_level,
                "completeness_score": session.research_summary.completeness_score
            }

        return {
            "success": True,
            "data": {
                "session_id": session.id,
                "topic": session.topic,
                "status": session.status.value,
                "max_iterations": session.max_iterations,
                "current_iteration": session.current_iteration,
                "total_patents_found": session.total_patents_found,
                "unique_patents": session.unique_patents,
                "iterations": iterations_data,
                "research_summary": summary_data,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat()
            }
        }

    except Exception as e:
        logger.error(f"迭代搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}", response_model=Dict[str, Any], tags=["会话"])
async def get_search_session(session_id: str):
    """获取搜索会话"""
    if not search_engine:
        raise HTTPException(status_code=503, detail="搜索引擎未初始化")

    session = await search_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {
        "success": True,
        "data": {
            "session_id": session.id,
            "topic": session.topic,
            "status": session.status.value,
            "total_patents_found": session.total_patents_found,
            "unique_patents": session.unique_patents,
            "created_at": session.created_at.isoformat()
        }
    }

@app.get("/api/statistics", response_model=Dict[str, Any], tags=["系统"])
async def get_search_statistics():
    """获取搜索统计"""
    if not search_engine:
        raise HTTPException(status_code=503, detail="搜索引擎未初始化")

    stats = await search_engine.get_statistics()
    return {
        "success": True,
        "data": stats
    }

if __name__ == "__main__":
    uvicorn.run(
        "enhanced_api:app",
        host="0.0.0.0",
        port=5002,
        reload=False,
        log_level="info"
    )
EOF

    chmod +x enhanced_api.py
fi

# 启动API服务
echo "🌐 启动增强版API服务..."
echo "   API地址: http://localhost:5002"
echo "   API文档: http://localhost:5002/docs"
echo "   健康检查: http://localhost:5002/health"
echo ""

# 使用Python直接运行
python3 enhanced_api.py