#!/usr/bin/env python3
"""
PQAI专利检索服务API
为Athena平台提供增强的专利检索API接口
"""

import os
import sys
from datetime import datetime
from typing import Any

from core.logging_config import setup_logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from core.pqai_search import PQAIEnhancedPatentSearcher
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

# 导入统一认证模块

logger = setup_logging()

app = FastAPI(
    title='PQAI专利检索服务',
    description='基于PQAI算法的增强专利检索API',
    version='1.0.0'
)

# 配置CORS

# 全局检索器实例
searcher = None
index_built = False

class PatentData(BaseModel):
    """专利数据模型"""
    id: str
    title: str
    abstract: str
    inventor: str | None = None
    assignee: str | None = None
    filing_date: str | None = None
    publication_date: str | None = None

class SearchRequest(BaseModel):
    """检索请求模型"""
    query: str
    top_k: int = 20
    search_type: str = 'hybrid'  # semantic, keyword, hybrid
    min_similarity: float = 0.7

class SearchResponse(BaseModel):
    """检索响应模型"""
    results: list[dict[str, Any]]
    total_found: int
    query: str
    search_type: str
    processing_time_ms: float
    timestamp: str

class IndexRequest(BaseModel):
    """索引构建请求模型"""
    patents: list[PatentData]
    rebuild: bool = False

@app.on_event('startup')
async def startup_event():
    """服务启动事件"""
    global searcher, index_built
    try:
        searcher = PQAIEnhancedPatentSearcher()
        logger.info('PQAI专利检索服务启动成功')
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        raise

@app.get('/health')
async def health_check():
    """健康检查接口"""
    global index_built
    return {
        'status': 'healthy',
        'service': 'PQAI专利检索服务',
        'index_built': index_built,
        'timestamp': datetime.now().isoformat()
    }

@app.get('/status')
async def get_status():
    """获取服务状态"""
    global searcher, index_built

    if searcher is None:
        raise HTTPException(status_code=503, detail='服务未初始化')

    stats = searcher.get_statistics()

    return {
        'service': 'PQAI专利检索服务',
        'status': 'running',
        'index_built': index_built,
        'statistics': stats,
        'timestamp': datetime.now().isoformat()
    }

@app.post('/index/build')
async def build_index(request: IndexRequest, background_tasks: BackgroundTasks):
    """构建或更新专利索引"""
    global searcher, index_built

    if searcher is None:
        raise HTTPException(status_code=503, detail='服务未初始化')

    try:
        # 转换专利数据格式
        patent_data = []
        for patent in request.patents:
            patent_dict = {
                'id': patent.id,
                'title': patent.title,
                'abstract': patent.abstract,
                'inventor': patent.inventor,
                'assignee': patent.assignee,
                'filing_date': patent.filing_date,
                'publication_date': patent.publication_date
            }
            patent_data.append(patent_dict)

        # 在后台任务中构建索引
        background_tasks.add_task(build_index_background, patent_data, request.rebuild)

        return {
            'message': '索引构建任务已启动',
            'patent_count': len(patent_data),
            'rebuild': request.rebuild,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"索引构建失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

async def build_index_background(patent_data: list[dict], rebuild: bool):
    """后台构建索引任务"""
    global index_built

    try:
        if rebuild or not index_built:
            searcher.build_index(patent_data)
            index_built = True
            logger.info(f"索引构建完成，包含{len(patent_data)}个专利")
        else:
            logger.info('索引已存在，跳过构建')

    except Exception as e:
        logger.error(f"后台索引构建失败: {e}")
        index_built = False

@app.post('/search', response_model=SearchResponse)
async def search_patents(request: SearchRequest):
    """专利检索接口"""
    global searcher, index_built

    if not index_built:
        raise HTTPException(status_code=400, detail='索引未构建，请先调用/index/build')

    if searcher is None:
        raise HTTPException(status_code=503, detail='服务未初始化')

    try:
        start_time = datetime.now()

        # 执行检索
        results = searcher.search(
            query=request.query,
            top_k=request.top_k,
            search_type=request.search_type
        )

        # 过滤低相似度结果
        filtered_results = [
            result for result in results
            if result.score >= request.min_similarity
        ]

        # 转换结果格式
        formatted_results = []
        for result in filtered_results:
            formatted_result = {
                'patent_id': result.patent_id,
                'title': result.title,
                'abstract': result.abstract,
                'score': result.score,
                'similarity_type': result.similarity_type,
                'highlight_spans': result.highlight_spans,
                'explanation': result.explanation
            }
            formatted_results.append(formatted_result)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000

        return SearchResponse(
            results=formatted_results,
            total_found=len(formatted_results),
            query=request.query,
            search_type=request.search_type,
            processing_time_ms=processing_time,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"检索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/search/similar/{patent_id}')
async def find_similar_patents(
    patent_id: str,
    top_k: int = 10,
    similarity_threshold: float = 0.7
):
    """查找相似专利"""
    global searcher, index_built

    if not index_built:
        raise HTTPException(status_code=400, detail='索引未构建')

    if searcher is None:
        raise HTTPException(status_code=503, detail='服务未初始化')

    try:
        # 查找指定专利
        target_patent = None
        for patent in searcher.patent_data:
            if patent.get('id') == patent_id:
                target_patent = patent
                break

        if not target_patent:
            raise HTTPException(status_code=404, detail='专利未找到')

        # 使用专利标题和摘要作为查询
        query = f"{target_patent.get('title', '')} {target_patent.get('abstract', '')}"

        results = searcher.search(
            query=query,
            top_k=top_k + 1,  # +1 to exclude the target patent
            search_type='hybrid'
        )

        # 排除目标专利本身
        similar_patents = [
            result for result in results
            if result.patent_id != patent_id and result.score >= similarity_threshold
        ]

        formatted_results = []
        for result in similar_patents:
            formatted_result = {
                'patent_id': result.patent_id,
                'title': result.title,
                'abstract': result.abstract,
                'score': result.score,
                'similarity_type': result.similarity_type,
                'explanation': result.explanation
            }
            formatted_results.append(formatted_result)

        return {
            'target_patent_id': patent_id,
            'similar_patents': formatted_results,
            'total_found': len(formatted_results),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"相似专利查找失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/analytics/statistics')
async def get_analytics():
    """获取检索分析统计"""
    global searcher, index_built

    if not index_built:
        raise HTTPException(status_code=400, detail='索引未构建')

    if searcher is None:
        raise HTTPException(status_code=503, detail='服务未初始化')

    stats = searcher.get_statistics()

    return {
        'index_statistics': stats,
        'service_health': {
            'status': 'healthy',
            'index_built': index_built,
            'model_loaded': searcher.model is not None
        },
        'performance_metrics': {
            'similarity_threshold': searcher.similarity_threshold,
            'retrieval_top_k': searcher.retrieval_top_k,
            'reranking_top_k': searcher.reranking_top_k
        },
        'timestamp': datetime.now().isoformat()
    }

if __name__ == '__main__':
    # setup_logging()  # 日志配置已移至模块导入

    logger.info('🚀 启动PQAI专利检索服务...')
    logger.info('📍 服务地址: http://localhost:8030')
    logger.info('🎯 核心功能: 基于PQAI算法的增强专利检索')

    uvicorn.run(app, host='0.0.0.0', port=8030, log_level='info')
