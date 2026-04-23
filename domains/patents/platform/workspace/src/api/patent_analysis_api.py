#!/usr/bin/env python3
"""
专利分析API服务
Patent Analysis API Service

提供RESTful API接口供其他系统调用
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

import logging

# 导入分析系统
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

# FastAPI相关
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.logging_config import setup_logging

# 导入统一认证模块

sys.path.append(str(Path(__file__).parent.parent))
from perception.advanced_technical_knowledge_graph import get_knowledge_graph
from perception.enhanced_vector_database import get_vector_database
from perception.ipc_classification_system import get_ipc_system
from perception.knowledge_enhanced_patent_analyzer import (
    KnowledgeEnhancedPatentAnalyzer,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/Users/xujian/Athena工作平台/documentation/logs/api.log')
    ]
)
logger = setup_logging()

# 初始化FastAPI应用
app = FastAPI(
    title='专利分析API',
    description='基于知识图谱的专利技术分析API',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)

# 添加CORS中间件

# Pydantic模型
class PatentInput(BaseModel):
    """专利输入模型"""
    patent_id: str = Field(..., description='专利ID')
    title: str = Field(..., description='专利标题')
    abstract: str = Field(..., description='专利摘要')
    claims: list[str] = Field(..., description='权利要求列表')

class FeatureExtractionRequest(BaseModel):
    """特征提取请求"""
    patent: PatentInput
    analysis_level: str = Field('standard', description='分析级别: basic/standard/enhanced')

class SimilaritySearchRequest(BaseModel):
    """相似度搜索请求"""
    query_text: str = Field(..., description='查询文本')
    top_k: int = Field(10, description='返回结果数量')
    search_type: str = Field('semantic', description='搜索类型: keyword/semantic/hybrid')

class TechTermSearchRequest(BaseModel):
    """技术术语搜索请求"""
    query: str = Field(..., description='查询词')
    domain: str | None = Field(None, description='技术领域过滤')
    limit: int = Field(20, description='返回结果数量')

class IpcClassificationRequest(BaseModel):
    """IPC分类请求"""
    patent_text: str = Field(..., description='专利文本')
    title: str | None = Field(None, description='专利标题')
    abstract: str | None = Field(None, description='专利摘要')

# 全局变量
analyzer: KnowledgeEnhancedPatentAnalyzer | None = None
vector_db = None
knowledge_graph = None
ipc_system = None

# 依赖注入
def get_analyzer() -> KnowledgeEnhancedPatentAnalyzer:
    """获取分析器实例"""
    global analyzer
    if analyzer is None:
        analyzer = KnowledgeEnhancedPatentAnalyzer()
        analyzer.initialize()
    return analyzer

def get_vector_db() -> Any | None:
    """获取向量数据库"""
    global vector_db
    if vector_db is None:
        vector_db = get_vector_database()
        vector_db.initialize()
    return vector_db

def get_knowledge_graph() -> Any | None:
    """获取知识图谱"""
    global knowledge_graph
    if knowledge_graph is None:
        knowledge_graph = get_knowledge_graph()
    return knowledge_graph

def get_ipc_system() -> Any | None:
    """获取IPC系统"""
    global ipc_system
    if ipc_system is None:
        ipc_system = get_ipc_system()
        ipc_system.load_ipc_data()
    return ipc_system

# API路由
@app.get('/')
async def root():
    """根路径"""
    return {
        'message': '专利分析API服务',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'patent_analysis': '/api/v1/patent/analyze',
            'feature_extraction': '/api/v1/patent/extract-features',
            'similarity_search': '/api/v1/search/similarity',
            'tech_term_search': '/api/v1/search/tech-terms',
            'ipc_classification': '/api/v1/ipc/classify',
            'knowledge_graph': '/api/v1/kg',
            'health_check': '/api/v1/health'
        }
    }

@app.get('/api/v1/health')
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'analyzer': analyzer is not None,
            'vector_db': vector_db is not None,
            'knowledge_graph': knowledge_graph is not None,
            'ipc_system': ipc_system is not None
        }
    }

@app.post('/api/v1/patent/analyze')
async def analyze_patent(request: PatentInput):
    """分析专利"""
    try:
        analyzer = get_analyzer()

        # 执行分析
        result = analyzer.analyze_patent_with_kg(
            patent_id=request.patent_id,
            title=request.title,
            abstract=request.abstract,
            claims=request.claims
        )

        # 构建响应
        response = {
            'patent_id': result.base_result.patent_id,
            'ipc_classifications': result.base_result.ipc_classifications,
            'technical_features': [
                {
                    'claim_number': f['claim_number'],
                    'text': f['text'],
                    'type': f['type'],
                    'importance': f.get('importance', 'medium')
                }
                for f in result.base_result.technical_features
            ],
            'knowledge_graph_analysis': {
                'matched_entities': len(result.matched_entities) if result.matched_entities else 0,
                'related_entities': len(result.related_entities) if result.related_entities else 0,
                'kg_confidence_score': result.kg_confidence_score
            },
            'innovation_insights': result.innovation_insights or [],
            'scores': {
                'novelty': result.base_result.novelty_assessment.get('overall_score', 0),
                'clarity': result.base_result.quality_scores.get('clarity_score', 0),
                'completeness': result.base_result.quality_scores.get('completeness_score', 0),
                'technical_strength': result.technical_strength_score
            },
            'search_strategy': result.base_result.search_strategy,
            'expert_considerations': result.expert_considerations or []
        }

        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        logger.error(f"专利分析失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}") from e

@app.post('/api/v1/patent/extract-features')
async def extract_features(request: FeatureExtractionRequest):
    """提取技术特征"""
    try:
        analyzer = get_analyzer()

        # 执行分析
        result = analyzer.analyze_patent_with_kg(
            patent_id=request.patent.patent_id,
            title=request.patent.title,
            abstract=request.patent.abstract,
            claims=request.patent.claims
        )

        # 返回特征
        features = []
        for feature in result.base_result.technical_features:
            features.append({
                'claim_number': feature.get('claim_number'),
                'text': feature.get('text'),
                'type': feature.get('type'),
                'importance': feature.get('importance'),
                'confidence': feature.get('confidence', 1.0)
            })

        return {
            'patent_id': request.patent.patent_id,
            'total_features': len(features),
            'features': features,
            'feature_statistics': result.base_result.feature_statistics
        }

    except Exception as e:
        logger.error(f"特征提取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"提取失败: {str(e)}") from e

@app.post('/api/v1/search/similarity')
async def search_similarity(request: SimilaritySearchRequest):
    """相似度搜索"""
    try:
        vector_db = get_vector_db()

        results = []
        if request.search_type == 'keyword':
            # 关键词搜索
            for keyword in [request.query_text]:
                matches = vector_db.search_by_text(keyword, top_k=request.top_k)
                results.extend([(id, sim, text) for id, sim, text in matches])
        elif request.search_type == 'semantic':
            # 语义搜索
            query_vector = vector_db._text_to_vector(request.query_text)
            if query_vector is not None:
                results = vector_db.search_similar_vectors(query_vector, top_k=request.top_k)

        # 去重并格式化
        seen = set()
        unique_results = []
        for vector_id, similarity, text in results:
            if text not in seen and len(unique_results) < request.top_k:
                seen.add(text)
                unique_results.append({
                    'text': text,
                    'similarity': round(similarity, 3),
                    'vector_id': vector_id
                })

        return {
            'query': request.query_text,
            'search_type': request.search_type,
            'total_results': len(unique_results),
            'reports/reports/results': unique_results
        }

    except Exception as e:
        logger.error(f"相似度搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}") from e

@app.post('/api/v1/search/tech-terms')
async def search_tech_terms(request: TechTermSearchRequest):
    """搜索技术术语"""
    try:
        kg = get_knowledge_graph()

        # 搜索实体
        matches = kg.search_entities(request.query, limit=request.limit)

        # 过滤领域
        if request.domain:
            matches = [(e, s) for e, s in matches if e.domain == request.domain]

        # 格式化结果
        results = []
        for entity, score in matches:
            results.append({
                'name': entity.name,
                'category': entity.category,
                'domain': entity.domain,
                'ipc_codes': entity.ipc_codes,
                'definition': entity.definition,
                'score': round(score, 3),
                'source': entity.source
            })

        return {
            'query': request.query,
            'domain_filter': request.domain,
            'total_results': len(results),
            'reports/reports/results': results
        }

    except Exception as e:
        logger.error(f"技术术语搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}") from e

@app.post('/api/v1/ipc/classify')
async def classify_ipc(request: IpcClassificationRequest):
    """IPC分类"""
    try:
        ipc_system = get_ipc_system()

        # 构建完整文本
        full_text = f"{request.title or ''} {request.abstract or ''} {request.patent_text}"

        # 执行分类
        match_result = ipc_system.match_patent_to_ipc(
            claims=request.patent_text,
            title=request.title or '',
            abstract=request.abstract or ''
        )

        # 格式化结果
        classifications = []
        for ipc_class, confidence, keywords in zip(
            match_result.matched_codes,
            match_result.confidence_scores,
            match_result.matching_keywords, strict=False
        ):
            classifications.append({
                'code': ipc_class.code,
                'name': ipc_class.name,
                'section': ipc_class.section,
                'domain': ipc_class.domain,
                'confidence': round(confidence, 3),
                'keywords': keywords
            })

        return {
            'text_snippet': full_text[:100] + '...' if len(full_text) > 100 else full_text,
            'primary_ipc': classifications[0]['code'] if classifications else None,
            'classifications': classifications,
            'analysis_summary': match_result.analysis_summary,
            'novelty_implications': match_result.novelty_implications
        }

    except Exception as e:
        logger.error(f"IPC分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分类失败: {str(e)}") from e

@app.get('/api/v1/kg/statistics')
async def get_kg_statistics():
    """获取知识图谱统计"""
    try:
        kg = get_knowledge_graph()
        stats = kg.get_statistics()

        return {
            'knowledge_graph': {
                'total_entities': stats['total_entities'],
                'total_relations': stats['total_relations'],
                'ipc_coverage': stats['ipc_coverage_count'],
                'category_distribution': stats['category_distribution'],
                'domain_distribution': stats['domain_distribution']
            }
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}") from e

@app.get('/api/v1/vector/statistics')
async def get_vector_statistics():
    """获取向量数据库统计"""
    try:
        vector_db = get_vector_db()
        stats = vector_db.get_vector_statistics()

        return stats

    except Exception as e:
        logger.error(f"获取向量统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}") from e

# 错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={'error': exc.detail, 'type': 'HTTPException'}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={'error': '内部服务器错误', 'type': 'GeneralException'}
    )

# 启动服务器
if __name__ == '__main__':
    import uvicorn

    # 创建日志目录
    Path('/Users/xujian/Athena工作平台/logs').mkdir(parents=True, exist_ok=True)

    logger.info('🚀 启动专利分析API服务...')
    logger.info('📚 文档地址: http://localhost:8000/docs')
    logger.info('🔍 ReDoc地址: http://localhost:8000/redoc')
    logger.info('💡 API地址: http://localhost:8000')

    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
        reload=True,
        log_level='info'
    )
