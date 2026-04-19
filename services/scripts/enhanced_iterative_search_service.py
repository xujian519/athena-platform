#!/usr/bin/env python3
"""
增强版迭代式专利搜索服务
Enhanced Iterative Patent Search Service

提供高级搜索功能，包括：
1. 多维度搜索策略
2. 智能关键词扩展
3. 专利相似度计算
4. Google专利meta标签完整提取
5. 搜索结果智能排序
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

# 导入我们的搜索器
from core.iterative_patent_search import (
    IterativePatentSearcher,
    PatentInfo,
)
from core.logging_config import setup_logging

# 导入统一认证模块

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title='增强版迭代式专利搜索服务',
    description='基于PostgreSQL中国专利数据库的高级搜索服务',
    version='2.0.0'
)

# 配置CORS

# 全局搜索器实例
searcher = None

# 请求和响应模型
class SearchRequest(BaseModel):
    query: str = Field(..., description='搜索查询词')
    max_results: int = Field(50, ge=1, le=200, description='最大结果数')
    search_fields: list[str] = Field(
        default=['patent_name', 'abstract', 'claims_content'],
        description='搜索字段'
    )
    filters: dict[str, Any] | None = Field(default=None, description='搜索过滤条件')
    boost_exact_match: bool = Field(default=True, description='是否提升完全匹配的权重')

class PatentResponse(BaseModel):
    id: str
    patent_name: str
    abstract: str
    claims_content: str | None
    applicant: str
    inventor: str | None
    application_number: str | None
    publication_number: str | None
    ipc_main_class: str | None
    citation_count: int
    cited_count: int
    relevance_score: float
    google_meta: dict[str, Any] | None = None

class SearchResponse(BaseModel):
    query: str
    total_results: int
    patents: list[PatentResponse]
    search_time: float
    iterations: int
    suggestions: list[str] | None = None

class ExportRequest(BaseModel):
    search_id: str
    format: str = Field('json', regex='^(json|csv|excel)$')
    include_full_text: bool = Field(False, description='是否包含完整文本')

@app.on_event('startup')
async def startup_event():
    """服务启动事件"""
    global searcher
    try:
        searcher = IterativePatentSearcher()
        searcher.connect()
        logger.info('🚀 增强版迭代式搜索服务启动成功')
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {str(e)}")
        raise

@app.on_event('shutdown')
async def shutdown_event():
    """服务关闭事件"""
    global searcher
    if searcher:
        searcher.disconnect()
        logger.info('📌 增强版迭代式搜索服务已关闭')

@app.get('/')
async def root():
    """根路径"""
    return {
        'service': '增强版迭代式专利搜索服务',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    }

@app.get('/health')
async def health_check():
    """健康检查"""
    try:
        # 测试数据库连接
        if searcher and searcher.conn:
            with searcher.conn.cursor() as cursor:
                cursor.execute('SELECT 1')
                return {
                    'status': 'healthy',
                    'database': 'connected',
                    'timestamp': datetime.now().isoformat()
                }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}") from e

@app.post('/api/v2/search', response_model=SearchResponse)
async def search_patents(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    执行迭代式专利搜索

    Args:
        request: 搜索请求对象

    Returns:
        SearchResponse: 搜索结果
    """
    start_time = datetime.now()

    try:
        # 执行搜索
        results = await searcher.search(
            query=request.query,
            max_results=request.max_results
        )

        # 计算搜索时间
        search_time = (datetime.now() - start_time).total_seconds()

        # 转换为响应格式
        patent_responses = []
        for patent in results:
            google_meta_dict = None
            if patent.google_meta:
                google_meta_dict = {
                    'title': patent.google_meta.title,
                    'inventors': patent.google_meta.inventors,
                    'assignee': patent.google_meta.assignee,
                    'citations_count': patent.google_meta.citations_count,
                    'ipc_codes': patent.google_meta.ipc_codes,
                }

            patent_responses.append(PatentResponse(
                id=patent.id,
                patent_name=patent.patent_name,
                abstract=patent.abstract[:500] if patent.abstract else '',  # 限制摘要长度
                claims_content=patent.claims_content[:500] if patent.claims_content else '',
                applicant=patent.applicant,
                inventor=patent.inventor,
                application_number=patent.application_number,
                publication_number=patent.publication_number,
                ipc_main_class=patent.ipc_main_class,
                citation_count=patent.citation_count,
                cited_count=patent.cited_count,
                relevance_score=round(patent.relevance_score, 3),
                google_meta=google_meta_dict
            ))

        # 生成搜索建议
        suggestions = await _generate_suggestions(request.query, results)

        # 记录搜索日志（后台任务）
        background_tasks.add_task(
            _log_search,
            query=request.query,
            results_count=len(results),
            search_time=search_time
        )

        return SearchResponse(
            query=request.query,
            total_results=len(results),
            patents=patent_responses,
            search_time=search_time,
            iterations=searcher.search_history[-1]['iterations'] if searcher.search_history else 1,
            suggestions=suggestions
        )

    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") from e

@app.get('/api/v2/patent/{patent_id}')
async def get_patent_detail(patent_id: str):
    """获取专利详细信息"""
    try:
        # 从数据库获取专利详情
        query = """
        SELECT *,
               -- 提取主权项
               CASE
                   WHEN claims_content LIKE '%1. %'
                   THEN SUBSTRING(claims_content FROM POSITION('1. ' IN claims_content) + 3)
                   ELSE claims_content
               END as main_claim
        FROM patents
        WHERE id = %s OR application_number = %s OR publication_number = %s
        LIMIT 1
        """

        with searcher.conn.cursor() as cursor:
            cursor.execute(query, (patent_id, patent_id, patent_id))
            result = cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail='Patent not found')

            # 提取完整的Google meta信息
            google_meta = searcher._extract_google_meta_data(dict(result))

            return {
                'patent': dict(result),
                'google_meta': google_meta.__dict__ if google_meta else None,
                'similar_patents': await _find_similar_patents(patent_id, limit=5)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取专利详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get patent detail: {str(e)}") from e

@app.post('/api/v2/export')
async def export_results(request: ExportRequest, background_tasks: BackgroundTasks):
    """导出搜索结果"""
    try:
        # 生成导出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"patent_search_{timestamp}.{request.format}"
        filepath = Path('exports') / filename

        # 确保导出目录存在
        filepath.parent.mkdir(exist_ok=True)

        # 在后台执行导出
        background_tasks.add_task(
            _export_search_results,
            search_id=request.search_id,
            filepath=str(filepath),
            format=request.format,
            include_full_text=request.include_full_text
        )

        return {
            'message': 'Export started',
            'filename': filename,
            'download_url': f"/api/v2/download/{filename}"
        }

    except Exception as e:
        logger.error(f"导出失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}") from e

@app.get('/api/v2/suggestions/{query}')
async def get_search_suggestions(query: str, limit: int = Query(10, ge=1, le=20)):
    """获取搜索建议"""
    try:
        suggestions = await _generate_search_suggestions(query, limit)
        return {'suggestions': suggestions}
    except Exception as e:
        logger.error(f"获取搜索建议失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}") from e

@app.get('/api/v2/statistics')
async def get_search_statistics():
    """获取搜索统计信息"""
    try:
        stats = {
            'total_patents': await _get_total_patents(),
            'search_history': len(searcher.search_history),
            'last_searches': searcher.search_history[-5:] if searcher.search_history else [],
            'database_info': await _get_database_info()
        }
        return stats
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}") from e

# 辅助函数
async def _generate_suggestions(query: str, results: list[PatentInfo]) -> list[str]:
    """生成搜索建议"""
    suggestions = []

    # 基于搜索结果生成建议
    if results:
        # 提取高频IPC分类
        ipc_classes = [p.ipc_main_class for p in results if p.ipc_main_class]
        ipc_counter = {}
        for ipc in ipc_classes:
            if ipc:
                ipc_counter[ipc[:3]] = ipc_counter.get(ipc[:3], 0) + 1

        # 添加IPC分类建议
        for ipc, count in sorted(ipc_counter.items(), key=lambda x: x[1], reverse=True)[:3]:
            suggestions.append(f"IPC分类: {ipc}")

        # 提取申请人建议
        applicants = [p.applicant for p in results if p.applicant]
        applicant_counter = {}
        for app in applicants[:10]:
            if app:
                # 提取公司关键词
                if '科技' in app:
                    applicant_counter['科技公司'] = applicant_counter.get('科技公司', 0) + 1
                if '大学' in app:
                    applicant_counter['大学'] = applicant_counter.get('大学', 0) + 1

        for app_type, count in applicant_counter.items():
            if count > 1:
                suggestions.append(f"申请人类型: {app_type}")

    # 基于查询扩展建议
    expanded_keywords = searcher._expand_keywords(query)
    for keyword in expanded_keywords[1:4]:  # 前3个扩展词
        if keyword != query:
            suggestions.append(f"相关词: {keyword}")

    return suggestions[:5]  # 最多返回5个建议

async def _find_similar_patents(patent_id: str, limit: int = 5) -> list[dict]:
    """查找相似专利"""
    try:
        # 获取当前专利信息
        query = 'SELECT patent_name, abstract, ipc_main_class FROM patents WHERE id = %s LIMIT 1'
        with searcher.conn.cursor() as cursor:
            cursor.execute(query, (patent_id,))
            current = cursor.fetchone()
            if not current:
                return []

        # 基于IPC分类和关键词查找相似专利
        similar_query = """
        SELECT id, patent_name, applicant, ipc_main_class,
               similarity(patent_name, %s) as name_similarity,
               similarity(COALESCE(abstract, ''), %s) as abstract_similarity
        FROM patents
        WHERE id != %s
        AND (ipc_main_class = %s OR patent_name LIKE %s OR abstract LIKE %s)
        ORDER BY (name_similarity + abstract_similarity) DESC
        LIMIT %s
        """

        with searcher.conn.cursor() as cursor:
            cursor.execute(
                similar_query,
                (
                    current['patent_name'],
                    current['abstract'] or '',
                    patent_id,
                    current['ipc_main_class'],
                    f"%{current['patent_name'][:20]}%",
                    f"%{(current['abstract'] or '')[:50]}%",
                    limit
                )
            )
            results = cursor.fetchall()

        return [dict(row) for row in results]

    except Exception as e:
        logger.error(f"查找相似专利失败: {str(e)}")
        return []

async def _generate_search_suggestions(query: str, limit: int) -> list[str]:
    """生成搜索建议"""
    suggestions = []

    # 从数据库中查询包含相似关键词的专利标题
    suggest_query = """
    SELECT DISTINCT patent_name
    FROM patents
    WHERE patent_name LIKE %s
    ORDER BY citation_count DESC
    LIMIT %s
    """

    try:
        with searcher.conn.cursor() as cursor:
            cursor.execute(suggest_query, (f"%{query}%", limit * 2))
            results = cursor.fetchall()

            # 提取关键词作为建议
            for row in results:
                title = row['patent_name']
                if query in title:
                    # 提取包含查询词的短语
                    words = title.split()
                    for i, word in enumerate(words):
                        if query in word:
                            # 提取前后词组成短语
                            phrase_words = words[max(0, i-1):i+2]
                            phrase = ' '.join(phrase_words)
                            if phrase not in suggestions:
                                suggestions.append(phrase)
                                break

        return suggestions[:limit]

    except Exception as e:
        logger.error(f"生成搜索建议失败: {str(e)}")
        return []

async def _get_total_patents() -> int:
    """获取专利总数"""
    try:
        with searcher.conn.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM patents')
            return cursor.fetchone()['count']
    except (ConnectionError, OSError, TimeoutError):
        return 0

async def _get_database_info() -> dict:
    """获取数据库信息"""
    try:
        with searcher.conn.cursor() as cursor:
            # 获取表信息
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = 'public' AND tablename = 'patents'
            """)
            table_info = cursor.fetchone()

            return {
                'table_size': table_info['size'] if table_info else 'Unknown',
                'last_update': datetime.now().isoformat()
            }
    except (ConnectionError, OSError, TimeoutError):
        return {'table_size': 'Unknown', 'last_update': datetime.now().isoformat()}

def _log_search(query: str, results_count: int, search_time: float) -> Any:
    """记录搜索日志"""
    try:
        log_entry = {
            'query': query,
            'results_count': results_count,
            'search_time': search_time,
            'timestamp': datetime.now().isoformat()
        }

        # 这里可以保存到日志文件或数据库
        logger.info(f"搜索日志: {json.dumps(log_entry, ensure_ascii=False)}")

    except Exception as e:
        logger.error(f"记录搜索日志失败: {str(e)}")

async def _export_search_results(search_id: str, filepath: str, format: str, include_full_text: bool):
    """导出搜索结果（后台任务）"""
    try:
        # 这里应该从缓存或数据库获取搜索结果
        # 暂时使用模拟数据
        results = []  # 实际应用中需要从search_id获取结果

        if format == 'json':
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'search_id': search_id,
                    'export_time': datetime.now().isoformat(),
                    'results': results
                }, f, ensure_ascii=False, indent=2, default=str)

        elif format == 'csv':
            import csv
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if results:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)

        logger.info(f"导出完成: {filepath}")

    except Exception as e:
        logger.error(f"导出失败: {str(e)}")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'enhanced_iterative_search_service:app',
        host='0.0.0.0',
        port=8009,
        reload=True,
        log_level='info'
    )
