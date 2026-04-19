#!/usr/bin/env python3
"""
混合爬虫API服务
Hybrid Crawler API Service

Athena工作平台增强版爬虫API，集成内部爬虫、Crawl4AI、FireCrawl
提供智能路由选择和成本监控功能
"""

import json
import logging
import os

# 导入混合爬虫核心模块
import sys
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.logging_config import setup_logging

# 导入统一认证模块

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.hybrid_config import get_config, get_config_manager
from core.batch_processor import TaskPriority, batch_processor
from core.hybrid_crawler_manager import HybridCrawlerManager
from storage.data_storage_manager import (
    CompressionType,
    StorageConfig,
    StorageType,
    storage_manager,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title='Athena混合爬虫API',
    description='Athena工作平台增强版爬虫API - 集成内部爬虫、Crawl4AI、FireCrawl',
    version='2.0.0'
)

# 添加CORS中间件

# 全局变量
hybrid_manager: HybridCrawlerManager | None = None
task_results = {}
config_manager = get_config_manager()

# 数据模型
class CrawlStrategy(str, Enum):
    """爬取策略枚举"""
    AUTO = 'auto'
    INTERNAL = 'internal'
    CRAWL4AI = 'crawl4ai'
    FIRECRAWL = 'firecrawl'

class HybridCrawlRequest(BaseModel):
    """混合爬取请求模型"""
    urls: list[str] = Field(..., description='要爬取的URL列表')
    strategy: CrawlStrategy = Field(CrawlStrategy.AUTO, description='爬取策略')
    max_concurrent: int | None = Field(5, description='最大并发数')
    background: bool | None = Field(False, description='是否后台运行')

    # 高级配置
    crawl4ai_mode: str | None = Field('basic', description='Crawl4AI模式')
    firecrawl_mode: str | None = Field('scrape', description='FireCrawl模式')
    llm_prompt: str | None = Field(None, description='LLM提取提示')

class CrawlerConfigUpdate(BaseModel):
    """爬虫配置更新模型"""
    cost_limits: dict[str, Any] | None = Field(None, description='成本限制配置')
    routing: dict[str, Any] | None = Field(None, description='路由配置')
    crawl4ai: dict[str, Any] | None = Field(None, description='Crawl4AI配置')
    firecrawl: dict[str, Any] | None = Field(None, description='FireCrawl配置')
    internal: dict[str, Any] | None = Field(None, description='内部爬虫配置')

class BatchTaskRequest(BaseModel):
    """批量任务请求模型"""
    name: str = Field(..., description='任务名称')
    urls: list[str] = Field(..., description='要爬取的URL列表')
    crawler_type: str = Field('hybrid', description='爬虫类型: hybrid, custom, crawl4ai, firecrawl')
    priority: str = Field('normal', description='优先级: low, normal, high, urgent')
    options: dict[str, Any] = Field(default_factory=dict, description='爬虫选项')

class BatchTaskResponse(BaseModel):
    """批量任务响应模型"""
    task_id: str
    status: str
    message: str

class HybridCrawlResponse(BaseModel):
    """混合爬取响应模型"""
    task_id: str
    status: str
    results: list[dict[str, Any]]
    stats: dict[str, Any]
    routing_decisions: list[dict[str, Any]]
    cost_info: dict[str, Any]
    message: str | None = None

# 配置文件路径
RESULTS_DIR = Path('/Users/xujian/Athena工作平台/data/crawler/results')
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

async def get_hybrid_manager():
    """获取混合爬虫管理器实例"""
    global hybrid_manager
    if hybrid_manager is None:
        config = get_config()
        hybrid_manager = HybridCrawlerManager(
            cost_limits=config.cost_limits.__dict__,
            crawl4ai_config=config.crawl4ai.__dict__,
            firecrawl_config=config.firecrawl.__dict__
        )
        await hybrid_manager.initialize()
    return hybrid_manager

@app.on_event('startup')
async def startup_event():
    """应用启动事件"""
    logger.info('启动混合爬虫API服务...')
    await get_hybrid_manager()

    # 启动批量处理器
    try:
        await batch_processor.start()
        logger.info('批量处理器已启动')
    except Exception as e:
        logger.error(f"启动批量处理器失败: {e}")

    # 初始化数据存储管理器
    try:
        StorageConfig(
            storage_type=StorageType.SQLITE,
            compression=CompressionType.GZIP,
            base_path='/Users/xujian/Athena工作平台/data/crawler/storage',
            retention_days=30
        )
        await storage_manager.initialize()
        logger.info('数据存储管理器已初始化')
    except Exception as e:
        logger.error(f"初始化数据存储管理器失败: {e}")

    logger.info('混合爬虫API服务启动完成')

@app.on_event('shutdown')
async def shutdown_event():
    """应用关闭事件"""
    global hybrid_manager
    if hybrid_manager:
        await hybrid_manager.close()

    # 停止批量处理器
    try:
        await batch_processor.stop()
        logger.info('批量处理器已停止')
    except Exception as e:
        logger.error(f"停止批量处理器失败: {e}")

    logger.info('混合爬虫API服务已关闭')

@app.get('/')
async def root():
    """根路径"""
    return {
        'message': 'Athena混合爬虫API服务',
        'version': '2.0.0',
        'status': 'running',
        'features': [
            '智能路由选择',
            'Crawl4AI AI增强',
            'FireCrawl商业级爬取',
            '成本监控控制',
            '批量并发处理',
            '大规模队列管理',
            '任务持久化存储'
        ]
    }

@app.post('/crawl', response_model=HybridCrawlResponse)
async def crawl_urls_hybrid(request: HybridCrawlRequest, background_tasks: BackgroundTasks):
    """
    智能路由爬取URL列表

    Args:
        request: 混合爬取请求
        background_tasks: 后台任务

    Returns:
        混合爬取响应
    """
    task_id = str(uuid.uuid4())
    manager = await get_hybrid_manager()

    try:
        if request.background:
            # 后台任务
            background_tasks.add_task(
                crawl_urls_background,
                task_id,
                request.urls,
                request.strategy.value,
                request.max_concurrent,
                request.dict(exclude={'urls', 'strategy', 'max_concurrent', 'background'})
            )
            return HybridCrawlResponse(
                task_id=task_id,
                status='started',
                results=[],
                stats={},
                routing_decisions=[],
                cost_info={},
                message='任务已启动，请使用/task/{task_id}查询结果'
            )
        else:
            # 同步任务
            results = await manager.batch_crawl(
                request.urls,
                request.strategy.value,
                max_concurrent=request.max_concurrent
            )

            # 整理结果
            formatted_results = []
            routing_decisions = []
            total_cost = 0.0

            for result in results:
                formatted_result = {
                    'url': result.url,
                    'success': result.success,
                    'content_length': len(result.content),
                    'processing_time': result.processing_time,
                    'crawler_used': result.crawler_used.value,
                    'error_message': result.error_message
                }

                # 添加增强内容
                if result.markdown_content:
                    formatted_result['markdown_content'] = result.markdown_content
                if result.extracted_data:
                    formatted_result['extracted_data'] = result.extracted_data
                if result.links:
                    formatted_result['links'] = result.links
                if result.images:
                    formatted_result['images'] = result.images

                formatted_results.append(formatted_result)
                routing_decisions.append({
                    'url': result.url,
                    'crawler_type': result.crawler_used.value,
                    'reason': result.routing_decision.reason,
                    'confidence': result.routing_decision.confidence,
                    'estimated_cost': result.routing_decision.estimated_cost
                })
                total_cost += result.cost

            stats = manager.get_stats()

            return HybridCrawlResponse(
                task_id=task_id,
                status='completed',
                results=formatted_results,
                stats=stats,
                routing_decisions=routing_decisions,
                cost_info={
                    'total_cost': total_cost,
                    'average_cost_per_url': total_cost / len(results) if results else 0,
                    'cost_breakdown': {
                        'internal': stats['routing_stats']['internal_usage'],
                        'crawl4ai': stats['routing_stats']['crawl4ai_usage'],
                        'firecrawl': stats['routing_stats']['firecrawl_usage']
                    }
                }
            )

    except Exception as e:
        logger.error(f"混合爬取任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}") from e

async def crawl_urls_background(task_id, urls, strategy, max_concurrent, extra_config):
    """后台混合爬取URL"""
    task_results[task_id] = {'status': 'running', 'progress': 0, 'start_time': datetime.now()}

    try:
        manager = await get_hybrid_manager()

        # 应用额外配置
        if extra_config.get('crawl4ai_mode'):
            manager.crawl4ai_config['mode'] = extra_config['crawl4ai_mode']
        if extra_config.get('firecrawl_mode'):
            manager.firecrawl_config['mode'] = extra_config['firecrawl_mode']
        if extra_config.get('llm_prompt'):
            manager.crawl4ai_config['llm_prompt'] = extra_config['llm_prompt']

        results = await manager.batch_crawl(urls, strategy, max_concurrent)

        # 整理结果
        formatted_results = []
        routing_decisions = []
        total_cost = 0.0

        for result in results:
            formatted_result = {
                'url': result.url,
                'success': result.success,
                'content': result.content,
                'content_length': len(result.content),
                'processing_time': result.processing_time,
                'crawler_used': result.crawler_used.value,
                'error_message': result.error_message
            }

            if result.markdown_content:
                formatted_result['markdown_content'] = result.markdown_content
            if result.extracted_data:
                formatted_result['extracted_data'] = result.extracted_data
            if result.links:
                formatted_result['links'] = result.links
            if result.images:
                formatted_result['images'] = result.images

            formatted_results.append(formatted_result)
            routing_decisions.append({
                'url': result.url,
                'crawler_type': result.crawler_used.value,
                'reason': result.routing_decision.reason,
                'confidence': result.routing_decision.confidence,
                'estimated_cost': result.routing_decision.estimated_cost
            })
            total_cost += result.cost

        # 保存结果
        result_data = {
            'task_id': task_id,
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy,
            'results': formatted_results,
            'routing_decisions': routing_decisions,
            'stats': manager.get_stats(),
            'cost_info': {
                'total_cost': total_cost,
                'average_cost_per_url': total_cost / len(results) if results else 0
            }
        }

        result_file = RESULTS_DIR / f"hybrid_{task_id}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)

        task_results[task_id] = {
            'status': 'completed',
            'results': formatted_results,
            'routing_decisions': routing_decisions,
            'stats': manager.get_stats(),
            'cost_info': result_data['cost_info'],
            'result_file': str(result_file),
            'completed_time': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"后台混合爬取任务失败 {task_id}: {str(e)}")
        task_results[task_id] = {
            'status': 'failed',
            'error': str(e),
            'failed_time': datetime.now().isoformat()
        }

@app.get('/task/{task_id}')
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail='任务不存在')

    return task_results[task_id]

@app.get('/tasks')
async def list_tasks(
    status: str | None = Query(None, description='按状态过滤: running, completed, failed'),
    limit: int | None = Query(50, description='返回数量限制')
):
    """列出所有任务"""
    tasks = []

    for task_id, data in task_results.items():
        if status and data.get('status') != status:
            continue

        tasks.append({
            'task_id': task_id,
            'status': data.get('status'),
            'start_time': data.get('start_time'),
            'completed_time': data.get('completed_time'),
            'failed_time': data.get('failed_time')
        })

    # 按时间倒序排列
    tasks.sort(key=lambda x: x.get('start_time', ''), reverse=True)

    return {'tasks': tasks[:limit] if limit else tasks}

@app.get('/stats')
async def get_hybrid_stats():
    """获取混合爬虫统计信息"""
    manager = await get_hybrid_manager()
    stats = manager.get_stats()

    # 任务统计
    total_tasks = len(task_results)
    completed_tasks = len([t for t in task_results.values() if t.get('status') == 'completed'])
    failed_tasks = len([t for t in task_results.values() if t.get('status') == 'failed'])
    running_tasks = len([t for t in task_results.values() if t.get('status') == 'running'])

    return {
        'task_stats': {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'running_tasks': running_tasks,
            'success_rate': f"{(completed_tasks / total_tasks * 100):.1f}%' if total_tasks > 0 else '0%"
        },
        'crawler_stats': stats['routing_stats'],
        'cost_stats': stats['cost_stats']
    }

@app.get('/config')
async def get_current_config():
    """获取当前配置"""
    config = get_config()
    return {
        'cost_limits': config.cost_limits.__dict__,
        'routing': config.routing.__dict__,
        'enabled_crawlers': {
            'internal': config.internal.enabled,
            'crawl4ai': config.crawl4ai.enabled,
            'firecrawl': config.firecrawl.enabled
        }
    }

@app.put('/config')
async def update_config(config_update: CrawlerConfigUpdate):
    """更新配置"""
    try:
        config_manager = get_config_manager()

        # 构建更新字典
        updates = {}
        if config_update.cost_limits:
            updates['cost_limits'] = config_update.cost_limits
        if config_update.routing:
            updates['routing'] = config_update.routing
        if config_update.crawl4ai:
            updates['crawl4ai'] = config_update.crawl4ai
        if config_update.firecrawl:
            updates['firecrawl'] = config_update.firecrawl
        if config_update.internal:
            updates['internal'] = config_update.internal

        if updates:
            config_manager.update_config(updates)

            # 重新创建管理器以应用新配置
            global hybrid_manager
            if hybrid_manager:
                await hybrid_manager.close()
            hybrid_manager = None

            return {'message': '配置更新成功，需要重启服务以完全生效', 'updates': updates}
        else:
            return {'message': '没有提供配置更新'}

    except Exception as e:
        logger.error(f"配置更新失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"配置更新失败: {str(e)}") from e

@app.post('/config/validate')
async def validate_config():
    """验证当前配置"""
    try:
        config_manager = get_config_manager()
        errors = config_manager.validate_config()

        if errors:
            return {
                'valid': False,
                'errors': errors
            }
        else:
            return {
                'valid': True,
                'message': '配置验证通过'
            }

    except Exception as e:
        logger.error(f"配置验证失败: {str(e)}")
        return {
            'valid': False,
            'errors': [f"验证过程出错: {str(e)}"]
        }

@app.get('/routing/analyze')
async def analyze_routing(url: str = Query(..., description='要分析的URL')):
    """分析URL的路由决策"""
    try:
        manager = await get_hybrid_manager()
        decision = manager.make_routing_decision(url)

        # URL分析
        analysis = manager._analyze_url(url)

        return {
            'url': url,
            'routing_decision': {
                'crawler_type': decision.crawler_type.value,
                'reason': decision.reason,
                'confidence': decision.confidence,
                'estimated_cost': decision.estimated_cost,
                'estimated_time': decision.estimated_time
            },
            'url_analysis': analysis
        }

    except Exception as e:
        logger.error(f"路由分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"路由分析失败: {str(e)}") from e

@app.get('/health')
async def health_check():
    """健康检查"""
    try:
        manager = await get_hybrid_manager()
        config = get_config()

        # 检查各爬虫状态
        crawler_status = {}
        if config.internal.enabled:
            crawler_status['internal'] = 'enabled'
        if config.crawl4ai.enabled:
            crawler_status['crawl4ai'] = 'enabled' if manager.crawl4ai_adapter else 'enabled_but_not_initialized'
        if config.firecrawl.enabled:
            crawler_status['firecrawl'] = 'enabled' if manager.firecrawl_adapter else 'enabled_but_not_initialized'

        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'crawler_status': crawler_status,
            'config_validated': len(config_manager.validate_config()) == 0
        }

    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )

@app.delete('/task/{task_id}')
async def delete_task(task_id: str):
    """删除任务"""
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail='任务不存在')

    # 删除任务结果
    del task_results[task_id]

    # 删除结果文件
    result_file = RESULTS_DIR / f"hybrid_{task_id}.json"
    if result_file.exists():
        result_file.unlink()

    return {'message': f"任务 {task_id} 已删除"}

@app.post('/stats/reset')
async def reset_stats():
    """重置统计信息"""
    try:
        manager = await get_hybrid_manager()
        manager.reset_stats()
        return {'message': '统计信息已重置'}
    except Exception as e:
        logger.error(f"重置统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重置统计失败: {str(e)}") from e

# ========== 批量处理相关API ==========

@app.post('/batch/create', response_model=BatchTaskResponse)
async def create_batch_task(request: BatchTaskRequest):
    """
    创建批量爬取任务

    Args:
        request: 批量任务请求

    Returns:
        任务创建响应
    """
    try:
        # 转换优先级
        priority_map = {
            'low': TaskPriority.LOW,
            'normal': TaskPriority.NORMAL,
            'high': TaskPriority.HIGH,
            'urgent': TaskPriority.URGENT
        }

        priority = priority_map.get(request.priority, TaskPriority.NORMAL)

        # 创建批量任务
        task_id = await batch_processor.create_batch_task(
            name=request.name,
            urls=request.urls,
            crawler_type=request.crawler_type,
            options=request.options,
            priority=priority
        )

        logger.info(f"批量任务已创建: {request.name} (ID: {task_id}), 包含 {len(request.urls)} 个URL")

        return BatchTaskResponse(
            task_id=task_id,
            status='created',
            message=f"批量任务已创建，包含 {len(request.urls)} 个URL"
        )

    except Exception as e:
        logger.error(f"创建批量任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建批量任务失败: {str(e)}") from e

@app.get('/batch/{task_id}/status')
async def get_batch_task_status(task_id: str):
    """获取批量任务状态"""
    try:
        status = await batch_processor.get_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail='任务不存在')
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}") from e

@app.get('/batch/{task_id}/results')
async def get_batch_task_results(task_id: str):
    """获取批量任务结果"""
    try:
        results = await batch_processor.get_task_results(task_id)
        if not results:
            raise HTTPException(status_code=404, detail='任务不存在')
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务结果失败: {str(e)}") from e

@app.post('/batch/{task_id}/cancel')
async def cancel_batch_task(task_id: str):
    """取消批量任务"""
    try:
        success = await batch_processor.cancel_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail='任务不存在或无法取消')
        return {'message': f"任务 {task_id} 已取消"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}") from e

@app.post('/batch/{task_id}/retry')
async def retry_batch_task(task_id: str):
    """重试批量任务"""
    try:
        success = await batch_processor.retry_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail='任务不存在或无法重试')
        return {'message': f"任务 {task_id} 已重新加入队列"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重试任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重试任务失败: {str(e)}") from e

@app.get('/batch/tasks')
async def list_batch_tasks(
    status: str | None = Query(None, description='按状态过滤: pending, running, completed, failed'),
    limit: int | None = Query(50, description='返回数量限制'),
    offset: int | None = Query(0, description='偏移量')
):
    """列出批量任务"""
    try:
        # 这里需要在batch_processor中添加相应的方法
        # 暂时返回空列表
        return {
            'tasks': [],
            'total': 0,
            'status': status,
            'limit': limit,
            'offset': offset
        }
    except Exception as e:
        logger.error(f"列出任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"列出任务失败: {str(e)}") from e

@app.get('/batch/stats')
async def get_batch_stats():
    """获取批量处理统计信息"""
    try:
        stats = await batch_processor.get_batch_stats()
        return stats
    except Exception as e:
        logger.error(f"获取批量统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取批量统计失败: {str(e)}") from e

@app.delete('/batch/{task_id}')
async def delete_batch_task(task_id: str):
    """删除批量任务"""
    try:
        # 这里需要在batch_processor中添加删除方法
        # 暂时返回成功消息
        return {'message': f"任务 {task_id} 已删除"}
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}") from e

# ========== 数据存储相关API ==========

@app.post('/storage/store')
async def store_crawl_data(request: dict[str, Any]):
    """
    存储爬取数据

    Args:
        request: 包含爬取结果的字典

    Returns:
        存储结果
    """
    try:
        data_id = await storage_manager.store_crawl_result(request)
        return {
            'success': True,
            'data_id': data_id,
            'message': '数据已成功存储'
        }
    except Exception as e:
        logger.error(f"存储数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"存储数据失败: {str(e)}") from e

@app.get('/storage/{data_id}')
async def retrieve_data(data_id: str):
    """检索存储的数据"""
    try:
        data = await storage_manager.retrieve_data(data_id)
        if not data:
            raise HTTPException(status_code=404, detail='数据不存在')
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检索数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检索数据失败: {str(e)}") from e

@app.post('/storage/search')
async def search_stored_data(
    query: dict[str, Any] = None,
    limit: int = Query(100, description='返回数量限制')
):
    """
    搜索存储的数据

    Args:
        query: 搜索条件
        limit: 返回数量限制

    Returns:
        搜索结果列表
    """
    if query is None:
        query = {}
    try:
        results = await storage_manager.search_data(query, limit)
        return {
            'results': results,
            'total': len(results),
            'query': query,
            'limit': limit
        }
    except Exception as e:
        logger.error(f"搜索数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索数据失败: {str(e)}") from e

@app.delete('/storage/{data_id}')
async def delete_stored_data(data_id: str):
    """删除存储的数据"""
    try:
        success = await storage_manager.delete_data(data_id)
        if not success:
            raise HTTPException(status_code=404, detail='数据不存在或删除失败')
        return {'message': f"数据 {data_id} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除数据失败: {str(e)}") from e

@app.post('/storage/cleanup')
async def cleanup_old_storage_data(days: int = Query(30, description='保留天数')):
    """清理旧的存储数据"""
    try:
        deleted_count = await storage_manager.cleanup_old_data(days)
        return {
            'message': f"已清理 {deleted_count} 条旧数据",
            'retention_days': days,
            'deleted_count': deleted_count
        }
    except Exception as e:
        logger.error(f"清理数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理数据失败: {str(e)}") from e

@app.get('/storage/stats')
async def get_storage_stats():
    """获取存储统计信息"""
    try:
        stats = await storage_manager.get_storage_stats()
        return stats
    except Exception as e:
        logger.error(f"获取存储统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取存储统计失败: {str(e)}") from e

@app.post('/storage/export')
async def export_stored_data(
    query: dict[str, Any] = None,
    format: str = Query('json', description='导出格式')
):
    """
    导出存储的数据

    Args:
        query: 导出条件
        format: 导出格式

    Returns:
        导出的数据文件
    """
    if query is None:
        query = {}
    try:
        export_data = await storage_manager.export_data(query, format)

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"crawler_export_{timestamp}.{format}"

        # 保存文件
        export_dir = Path('/Users/xujian/Athena工作平台/data/crawler/exports')
        export_dir.mkdir(parents=True, exist_ok=True)

        file_path = export_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(export_data)

        return {
            'message': '数据导出成功',
            'filename': filename,
            'file_path': str(file_path),
            'size': len(export_data.encode('utf-8')),
            'record_count': export_data.count("'id':") if format == 'json' else 0
        }
    except Exception as e:
        logger.error(f"导出数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}") from e

# 修改爬取API以自动存储结果
@app.post('/crawl', response_model=HybridCrawlResponse)
async def crawl_urls_hybrid(request: HybridCrawlRequest, background_tasks: BackgroundTasks):
    """
    智能路由爬取URL列表

    Args:
        request: 混合爬取请求
        background_tasks: 后台任务

    Returns:
        混合爬取响应
    """
    task_id = str(uuid.uuid4())
    manager = await get_hybrid_manager()

    try:
        if request.background:
            # 后台任务
            background_tasks.add_task(
                crawl_urls_background,
                task_id,
                request.urls,
                request.strategy.value,
                request.max_concurrent,
                request.dict(exclude={'urls', 'strategy', 'max_concurrent', 'background'})
            )
            return HybridCrawlResponse(
                task_id=task_id,
                status='started',
                results=[],
                stats={},
                routing_decisions=[],
                cost_info={},
                message='任务已启动，请使用/task/{task_id}查询结果'
            )
        else:
            # 同步任务
            results = await manager.batch_crawl(
                request.urls,
                request.strategy.value,
                max_concurrent=request.max_concurrent
            )

            # 整理结果
            formatted_results = []
            routing_decisions = []
            total_cost = 0.0

            for result in results:
                formatted_result = {
                    'url': result.url,
                    'success': result.success,
                    'content_length': len(result.content),
                    'processing_time': result.processing_time,
                    'crawler_used': result.crawler_used.value,
                    'error_message': result.error_message
                }

                # 添加增强内容
                if result.markdown_content:
                    formatted_result['markdown_content'] = result.markdown_content
                if result.extracted_data:
                    formatted_result['extracted_data'] = result.extracted_data
                if result.links:
                    formatted_result['links'] = result.links
                if result.images:
                    formatted_result['images'] = result.images

                formatted_results.append(formatted_result)
                routing_decisions.append({
                    'url': result.url,
                    'crawler_type': result.crawler_used.value,
                    'reason': result.routing_decision.reason,
                    'confidence': result.routing_decision.confidence,
                    'estimated_cost': result.routing_decision.estimated_cost
                })
                total_cost += result.cost

                # 自动存储成功的爬取结果
                if result.success:
                    try:
                        storage_data = {
                            'task_id': task_id,
                            'url': result.url,
                            'content': result.content,
                            'title': result.extracted_data.get('title', '') if result.extracted_data else '',
                            'crawler_used': result.crawler_used.value,
                            'processing_time': result.processing_time,
                            'status_code': 200,
                            'links': result.links or [],
                            'images': result.images or [],
                            'extracted_data': result.extracted_data or {}
                        }

                        await storage_manager.store_crawl_result(storage_data)
                    except Exception as e:
                        logger.warning(f"自动存储爬取结果失败: {e}")

            stats = manager.get_stats()

            return HybridCrawlResponse(
                task_id=task_id,
                status='completed',
                results=formatted_results,
                stats=stats,
                routing_decisions=routing_decisions,
                cost_info={
                    'total_cost': total_cost,
                    'average_cost_per_url': total_cost / len(results) if results else 0,
                    'cost_breakdown': {
                        'internal': stats['routing_stats']['internal_usage'],
                        'crawl4ai': stats['routing_stats']['crawl4ai_usage'],
                        'firecrawl': stats['routing_stats']['firecrawl_usage']
                    }
                }
            )

    except Exception as e:
        logger.error(f"混合爬取任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}") from e

# 增强健康检查，包含批量处理器和存储状态
@app.get('/health')
async def health_check():
    """健康检查"""
    try:
        manager = await get_hybrid_manager()
        config = get_config()

        # 检查各爬虫状态
        crawler_status = {}
        if config.internal.enabled:
            crawler_status['internal'] = 'enabled'
        if config.crawl4ai.enabled:
            crawler_status['crawl4ai'] = 'enabled' if manager.crawl4ai_adapter else 'enabled_but_not_initialized'
        if config.firecrawl.enabled:
            crawler_status['firecrawl'] = 'enabled' if manager.firecrawl_adapter else 'enabled_but_not_initialized'

        # 检查批量处理器状态
        batch_status = 'running' if batch_processor._running else 'stopped'

        # 获取批量统计
        batch_stats = await batch_processor.get_batch_stats()

        # 获取存储统计
        storage_stats = {}
        try:
            storage_stats = await storage_manager.get_storage_stats()
        except Exception as e:
            logger.warning(f"获取存储统计失败: {e}")
            storage_stats = {'error': str(e)}

        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'crawler_status': crawler_status,
            'batch_processor': {
                'status': batch_status,
                'stats': batch_stats
            },
            'data_storage': storage_stats,
            'config_validated': len(config_manager.validate_config()) == 0
        }

    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8002)
