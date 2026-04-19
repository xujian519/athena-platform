#!/usr/bin/env python3
"""
法律向量数据库API服务
提供RESTful接口，支持法律文档的智能检索和分析
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    # 导入统一认证模块
    import uvicorn
    from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    from shared.auth.auth_middleware import create_auth_middleware, setup_cors

except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"❌ 缺少依赖包: {e}")
    logger.info('请运行: pip install fastapi uvicorn pydantic')
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('legal_vector_api.log'), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title='法律向量数据库API',
    description='AI驱动的法律文档智能检索和分析系统',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc',
)

# 添加CORS中间件

# 全局配置
SERVICE_CONFIG = {'host': 'localhost', 'port': 8005, 'version': '1.0.0', 'debug': False}

# 服务状态
service_status = {
    'name': '法律向量数据库API',
    'status': 'starting',
    'start_time': datetime.now().isoformat(),
    'version': SERVICE_CONFIG['version'],
    'uptime_seconds': 0,
    'total_requests': 0,
    'successful_requests': 0,
    'error_requests': 0,
}


# Pydantic模型定义
class SearchRequest(BaseModel):
    query: str = Field(..., description='搜索查询文本', min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=100, description='返回结果数量限制')
    filters: dict[str, Any] | None = Field(default=None, description='过滤条件')
    use_rerank: bool = Field(default=True, description='是否使用重排序')
    category: str | None = Field(default=None, description='法律类别过滤')
    similarity_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description='相似度阈值'
    )


class SearchResult(BaseModel):
    id: str
    score: float
    text: str
    filename: str
    category: str
    law_type: str
    section_num: str | None = None
    chunk_index: int


class SearchResponse(BaseModel):
    query: str
    total_results: int
    processing_time_ms: float
    results: list[SearchResult]
    suggested_queries: list[str] = Field(default_factory=list)


class LegalStats(BaseModel):
    total_documents: int
    total_vectors: int
    collections: dict[str, int]
    categories: dict[str, int]
    last_updated: str


class HealthStatus(BaseModel):
    status: str
    uptime_seconds: int
    version: str
    qdrant_connected: bool
    vector_model_loaded: bool
    memory_usage_mb: float


# 模拟数据存储（实际应用中会连接真实数据库）
LEGAL_DATABASE = {'documents': [], 'vectors': [], 'metadata': {}}


# 模拟的搜索结果
def simulate_legal_search(
    query: str, limit: int = 10, filters: dict[str, Any] = None
) -> list[dict[str, Any]]:
    """模拟法律搜索结果"""
    import random

    # 模拟法律文档数据
    sample_documents = [
        {
            'id': 'criminal_law_001',
            'score': random.uniform(0.8, 0.95),
            'text': '《中华人民共和国刑法》第二百六十四条【盗窃罪】盗窃公私财物，数额较大的，或者多次盗窃、入户盗窃、携带凶器盗窃、扒窃的，处三年以下有期徒刑、拘役或者管制，并处或者单处罚金...',
            'filename': '刑法.md',
            'category': '刑法',
            'law_type': '法律',
            'section_num': '第二百六十四条',
            'chunk_index': 1,
        },
        {
            'id': 'contract_law_001',
            'score': random.uniform(0.7, 0.9),
            'text': '《中华人民共和国合同法》第一百零七条当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任...',
            'filename': '合同法.md',
            'category': '民法',
            'law_type': '法律',
            'section_num': '第一百零七条',
            'chunk_index': 3,
        },
        {
            'id': 'ip_law_001',
            'score': random.uniform(0.6, 0.85),
            'text': '《中华人民共和国著作权法》第十条著作权包括下列人身权和财产权：（一）发表权；（二）署名权；（三）修改权；（四）保护作品完整权；（五）复制权；（六）发行权...',
            'filename': '著作权法.md',
            'category': '知识产权',
            'law_type': '法律',
            'section_num': '第十条',
            'chunk_index': 0,
        },
        {
            'id': 'civil_procedure_001',
            'score': random.uniform(0.5, 0.8),
            'text': '《中华人民共和国民事诉讼法》第六十四条当事人对自己提出的主张，有责任提供证据。当事人及其诉讼代理人因客观原因不能自行收集的证据，或者人民法院认为审理案件需要的证据，人民法院应当调查收集...',
            'filename': '民事诉讼法.md',
            'category': '程序法',
            'law_type': '法律',
            'section_num': '第六十四条',
            'chunk_index': 2,
        },
        {
            'id': 'criminal_procedure_001',
            'score': random.uniform(0.4, 0.75),
            'text': '《中华人民共和国刑事诉讼法》第五十二条人民法院、人民检察院和公安机关有权向有关单位和个人收集、调取证据。有关单位和个人应当如实提供证据...',
            'filename': '刑事诉讼法.md',
            'category': '程序法',
            'law_type': '法律',
            'section_num': '第五十二条',
            'chunk_index': 1,
        },
    ]

    # 根据查询关键词过滤结果
    filtered_results = []
    query_lower = query.lower()

    for doc in sample_documents:
        text_lower = doc['text'].lower()
        # 简单的关键词匹配
        if any(
            keyword in text_lower for keyword in query_lower.split() if len(keyword) > 1
        ):
            # 应用过滤条件
            if filters:
                if 'category' in filters and filters['category'] != doc['category']:
                    continue
                if 'law_type' in filters and filters['law_type'] != doc['law_type']:
                    continue

            filtered_results.append(doc)

    # 如果没有匹配结果，返回随机结果
    if not filtered_results:
        filtered_results = sample_documents[:limit]

    return filtered_results[:limit]


# API端点
@app.get('/')
async def root():
    """根路径 - API信息"""
    return {
        'service': '法律向量数据库API',
        'version': SERVICE_CONFIG['version'],
        'description': 'AI驱动的法律文档智能检索和分析系统',
        'docs': '/docs',
        'health': '/health',
        'timestamp': datetime.now().isoformat(),
    }


@app.get('/health')
async def health_check():
    """健康检查端点"""

    import psutil

    # 计算运行时间
    uptime = int(
        (
            datetime.now() - datetime.fromisoformat(service_status['start_time'])
        ).total_seconds()
    )

    # 获取内存使用情况
    try:
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
    except Exception:
        memory_usage = 0.0

    health_status = {
        'status': 'healthy',
        'uptime_seconds': uptime,
        'version': SERVICE_CONFIG['version'],
        'qdrant_connected': True,  # 实际应用中需要检查Qdrant连接
        'vector_model_loaded': True,  # 实际应用中需要检查模型加载状态
        'memory_usage_mb': round(memory_usage, 2),
        'total_requests': service_status['total_requests'],
        'success_rate': (
            service_status['successful_requests']
            / max(service_status['total_requests'], 1)
            * 100
        ),
    }

    return health_status


@app.get('/stats')
async def get_statistics():
    """获取数据库统计信息"""
    stats = LegalStats(
        total_documents=len(LEGAL_DATABASE['documents']),
        total_vectors=len(LEGAL_DATABASE['vectors']),
        collections={'legal_database': len(LEGAL_DATABASE['vectors'])},
        categories={
            '刑法': 156,
            '民法': 203,
            '宪法相关法': 89,
            '司法解释': 412,
            '程序法': 67,
            '知识产权': 78,
            '其他': 352,
        },
        last_updated=datetime.now().isoformat(),
    )

    return stats


@app.post('/api/v1/legal/search', response_model=SearchResponse)
async def search_legal_documents(request: SearchRequest):
    """搜索法律文档"""
    import time

    start_time = time.time()
    service_status['total_requests'] += 1

    try:
        # 构建过滤条件
        filters = {}
        if request.category:
            filters['category'] = request.category
        if request.filters:
            filters.update(request.filters)

        # 执行搜索
        results = simulate_legal_search(
            query=request.query, limit=request.limit, filters=filters
        )

        # 构建搜索结果
        search_results = []
        for result in results:
            search_result = SearchResult(
                id=result['id'],
                score=result['score'],
                text=result['text'],
                filename=result['filename'],
                category=result['category'],
                law_type=result['law_type'],
                section_num=result.get('section_num'),
                chunk_index=result['chunk_index'],
            )
            search_results.append(search_result)

        # 生成建议查询（基于搜索词的扩展）
        suggested_queries = []
        if '盗窃' in request.query:
            suggested_queries.extend(['抢劫罪', '诈骗罪', '抢夺罪'])
        if '合同' in request.query:
            suggested_queries.extend(['违约责任', '合同解除', '违约金'])

        # 计算处理时间
        processing_time = (time.time() - start_time) * 1000

        response = SearchResponse(
            query=request.query,
            total_results=len(results),
            processing_time_ms=round(processing_time, 2),
            results=search_results,
            suggested_queries=suggested_queries[:3],
        )

        service_status['successful_requests'] += 1
        return response

    except Exception as e:
        service_status['error_requests'] += 1
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get('/api/v1/legal/categories')
async def get_legal_categories():
    """获取法律分类列表"""
    categories = {
        '宪法相关法': {
            'description': '宪法及宪法性法律文件',
            'count': 89,
            'examples': ['宪法', '选举法', '立法法'],
        },
        '刑法': {
            'description': '刑事法律规范及修正案',
            'count': 156,
            'examples': ['刑法', '刑法修正案', '刑事诉讼法'],
        },
        '民法': {
            'description': '民事法律规范',
            'count': 203,
            'examples': ['民法典', '合同法', '侵权责任法'],
        },
        '行政法': {
            'description': '行政法律规范',
            'count': 145,
            'examples': ['行政处罚法', '行政许可法', '行政复议法'],
        },
        '程序法': {
            'description': '诉讼程序法律',
            'count': 67,
            'examples': ['民事诉讼法', '刑事诉讼法', '行政诉讼法'],
        },
        '司法解释': {
            'description': '最高法院司法解释',
            'count': 412,
            'examples': ['民商事司法解释', '刑事司法解释'],
        },
        '知识产权': {
            'description': '知识产权相关法律',
            'count': 78,
            'examples': ['专利法', '商标法', '著作权法'],
        },
        '其他': {
            'description': '其他法律法规',
            'count': 352,
            'examples': ['劳动法', '环保法', '金融法规'],
        },
    }

    return categories


@app.get('/api/v1/legal/suggestions')
async def get_search_suggestions(query: str = Query(..., description='查询文本')):
    """获取搜索建议"""

    suggestions = []

    # 基于查询内容生成建议
    if len(query) < 2:
        return []

    # 法律术语扩展
    legal_terms = {
        '盗窃': ['抢劫', '诈骗', '抢夺', '侵占'],
        '合同': ['违约', '解除', '无效', '撤销'],
        '侵权': ['责任', '赔偿', '损害', '精神损害'],
        '诉讼': ['起诉', '应诉', '举证', '执行'],
        '知识产权': ['专利', '商标', '著作权', '商业秘密'],
        '劳动': ['劳动合同', '工资', '工伤', '解除'],
        '婚姻': ['离婚', '财产分割', '子女抚养', '抚养费'],
    }

    for term, expansions in legal_terms.items():
        if term in query:
            suggestions.extend(expansions)

    # 去重并限制数量
    unique_suggestions = list(set(suggestions))[:5]

    return {'query': query, 'suggestions': unique_suggestions}


@app.post('/api/v1/legal/analyze')
async def analyze_legal_text(
    text: str = Query(..., description='待分析的法律文本'),
    analysis_type: str = Query('general', description='分析类型'),
):
    """法律文本分析"""

    analysis_result = {
        'text': text,
        'analysis_type': analysis_type,
        'timestamp': datetime.now().isoformat(),
        'results': {},
    }

    if analysis_type == 'general':
        # 通用分析
        analysis_result['results'] = {
            'legal_terms': extract_legal_terms(text),
            'potential_issues': detect_legal_issues(text),
            'suggested_actions': generate_suggestions(text),
            'confidence': 0.85,
        }
    elif analysis_type == 'risk':
        # 风险评估
        analysis_result['results'] = {
            'risk_level': assess_risk_level(text),
            'risk_factors': identify_risk_factors(text),
            'mitigation_strategies': suggest_mitigation(text),
            'compliance_status': check_compliance(text),
        }
    elif analysis_type == 'clause':
        # 条款分析
        analysis_result['results'] = {
            'clause_types': identify_clause_types(text),
            'missing_elements': check_missing_elements(text),
            'improvements': suggest_improvements(text),
            'completeness': assess_completeness(text),
        }

    return analysis_result


# 辅助函数
def extract_legal_terms(text: str) -> list[str]:
    """提取法律术语"""
    legal_terms = [
        '合同',
        '违约',
        '赔偿',
        '侵权',
        '诉讼',
        '仲裁',
        '调解',
        '当事人',
        '权利',
        '义务',
        '责任',
        '法律',
        '法规',
        '条例',
    ]

    found_terms = []
    text_lower = text.lower()
    for term in legal_terms:
        if term in text_lower:
            found_terms.append(term)

    return found_terms


def detect_legal_issues(text: str) -> list[str]:
    """检测潜在法律问题"""
    issues = []

    # 简单的风险检测逻辑
    if '赔偿' in text and '责任' not in text:
        issues.append('缺少责任承担条款')

    if '合同' in text and '期限' not in text:
        issues.append('缺少合同期限约定')

    return issues


def generate_suggestions(text: str) -> list[str]:
    """生成改进建议"""
    suggestions = []

    if '合同' in text:
        suggestions.append('建议明确约定违约责任')
        suggestions.append('建议约定争议解决方式')

    if len(text) < 100:
        suggestions.append('建议增加更详细的条款描述')

    return suggestions


def assess_risk_level(text: str) -> str:
    """评估风险等级"""
    risk_keywords = ['违约', '赔偿', '责任', '争议', '纠纷']
    risk_count = sum(1 for keyword in risk_keywords if keyword in text.lower())

    if risk_count >= 3:
        return '高风险'
    elif risk_count >= 1:
        return '中风险'
    else:
        return '低风险'


def identify_risk_factors(text: str) -> list[str]:
    """识别风险因素"""
    factors = []

    if '口头' in text and '书面' not in text:
        factors.append('口头协议风险')

    if '金额' in text and '具体' not in text:
        factors.append('金额约定不明确')

    return factors


def suggest_mitigation(text: str) -> list[str]:
    """建议风险缓解措施"""
    return [
        '明确约定各方的权利义务',
        '制定详细的违约责任条款',
        '约定争议解决方式',
        '完善合同形式要求',
    ]


def check_compliance(text: str) -> bool:
    """检查合规性"""
    # 简化的合规检查
    return len(text) > 50 and '合同' in text or '协议' in text


def identify_clause_types(text: str) -> list[str]:
    """识别条款类型"""
    clause_types = []

    if '付款' in text or '金额' in text:
        clause_types.append('付款条款')

    if '违约' in text or '责任' in text:
        clause_types.append('违约责任条款')

    if '争议' in text or '仲裁' in text or '诉讼' in text:
        clause_types.append('争议解决条款')

    return clause_types


def check_missing_elements(text: str) -> list[str]:
    """检查缺失要素"""
    missing = []

    if '当事人' not in text and '甲方' not in text and '乙方' not in text:
        missing.append('缺少当事人信息')

    if '期限' not in text and '时间' not in text:
        missing.append('缺少有效期限')

    return missing


def suggest_improvements(text: str) -> list[str]:
    """建议改进方向"""
    improvements = []

    if len(text) < 200:
        improvements.append('建议增加条款的详细程度')

    if '具体' not in text and '明确' not in text:
        improvements.append('建议使用更明确的表述')

    return improvements


def assess_completeness(text: str) -> float:
    """评估完整性得分"""
    score = 0.0

    # 检查基本要素
    if any(keyword in text for keyword in ['当事人', '甲方', '乙方']):
        score += 0.3

    if any(keyword in text for keyword in ['权利', '义务', '责任']):
        score += 0.3

    if any(keyword in text for keyword in ['期限', '时间', '日期']):
        score += 0.2

    if len(text) >= 100:
        score += 0.2

    return min(score, 1.0)


# 启动服务
if __name__ == '__main__':
    logger.info('🚀 启动法律向量数据库API服务...')
    logger.info(f"📊 服务配置: {SERVICE_CONFIG}")

    service_status['status'] = 'running'

    try:
        uvicorn.run(
            app,
            host=SERVICE_CONFIG['host'],
            port=SERVICE_CONFIG['port'],
            log_level='info',
        )
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        service_status['status'] = 'error'
        sys.exit(1)
