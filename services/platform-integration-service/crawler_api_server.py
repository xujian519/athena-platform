#!/usr/bin/env python3
"""
Athena平台爬虫API服务
为整个平台提供统一的爬虫自动化接口
"""

import asyncio
import json
from datetime import datetime
from typing import Any

import uvicorn
from crawler_integration_service import get_crawler_integration_service
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# 导入统一认证模块
from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title='Athena平台爬虫自动化API',
    description='为Athena平台和小诺提供统一的智能爬虫服务',
    version='2.0.0'
)

# 添加CORS中间件

# 请求模型
class CrawlerTaskRequest(BaseModel):
    """爬虫任务请求模型"""
    user_input: str = Field(..., description='用户输入描述')
    mode: str = Field(default='auto', description='执行模式: auto/xiaonuo/direct/scheduled')
    context: dict[str, Any] | None = Field(default=None, description='上下文信息')
    scenario: str | None = Field(default=None, description='指定场景')
    urls: list[str] | None = Field(default=None, description='目标URL列表')
    config: dict[str, Any] | None = Field(default=None, description='爬虫配置')
    priority: int = Field(default=1, description='任务优先级')
    schedule_time: str | None = Field(default=None, description='调度时间')

class BatchCrawlerRequest(BaseModel):
    """批量爬虫请求模型"""
    requests: list[CrawlerTaskRequest]
    max_concurrent: int = Field(default=5, description='最大并发数')

class ConfigUpdateRequest(BaseModel):
    """配置更新请求模型"""
    service_config: dict[str, Any] | None = None
    xiaonuo_config: dict[str, Any] | None = None

class TaskStatusRequest(BaseModel):
    """任务状态查询请求"""
    task_id: str = Field(..., description='任务ID')

# 初始化爬虫集成服务
crawler_integration_service = None

@app.on_event('startup')
async def startup_event():
    """应用启动事件"""
    global crawler_integration_service
    logger.info('启动Athena平台爬虫API服务...')

    crawler_integration_service = get_crawler_integration_service()

    # 等待服务初始化
    await asyncio.sleep(3)

    logger.info('爬虫API服务启动成功')

@app.on_event('shutdown')
async def shutdown_event():
    """应用关闭事件"""
    logger.info('正在关闭爬虫API服务...')

    if crawler_integration_service:
        await crawler_integration_service.shutdown()

    logger.info('爬虫API服务已关闭')

@app.get('/')
async def root():
    """根路径"""
    return {
        'service': 'Athena平台爬虫自动化API',
        'version': '2.0.0',
        'status': 'running',
        'features': [
            '智能爬虫控制',
            '多场景支持',
            '任务调度',
            '批量处理',
            '实时监控'
        ],
        'timestamp': datetime.now().isoformat()
    }

@app.post('/api/v1/crawler/task')
async def execute_crawler_task(request: CrawlerTaskRequest):
    """执行单个爬虫任务"""
    try:
        # 构建请求参数
        task_params = {
            'user_input': request.user_input,
            'mode': request.mode,
            'context': request.context or {},
            'scenario': request.scenario,
            'urls': request.urls or [],
            'config': request.config or {},
            'priority': request.priority
        }

        # 执行任务
        result = await crawler_integration_service.process_request(task_params)

        return {
            'success': True,
            'data': result,
            'message': '爬虫任务执行完成',
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"执行爬虫任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/api/v1/crawler/tasks/batch')
async def execute_batch_crawler_tasks(request: BatchCrawlerRequest):
    """批量执行爬虫任务"""
    try:
        # 构建批量请求
        batch_requests = []
        for i, task_req in enumerate(request.requests):
            batch_requests.append({
                'request_id': f"batch_{i}",
                'user_input': task_req.user_input,
                'mode': task_req.mode,
                'context': task_req.context or {},
                'scenario': task_req.scenario,
                'urls': task_req.urls or [],
                'config': task_req.config or {},
                'priority': task_req.priority
            })

        # 批量执行
        results = await crawler_integration_service.batch_process(batch_requests)

        return {
            'success': True,
            'data': {
                'results': results,
                'total': len(results),
                'successful': sum(1 for r in results if r['success']),
                'failed': sum(1 for r in results if not r['success'])
            },
            'message': '批量爬虫任务执行完成',
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"批量执行爬虫任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/api/v1/crawler/scenarios')
async def get_available_crawler_scenarios():
    """获取可用的爬虫场景"""
    try:
        scenarios = await crawler_integration_service.get_available_scenarios()

        return {
            'success': True,
            'data': scenarios,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取爬虫场景列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/api/v1/crawler/status')
async def get_crawler_service_status():
    """获取爬虫服务状态"""
    try:
        status = await crawler_integration_service.get_service_status()

        return {
            'success': True,
            'data': status,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取爬虫服务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/api/v1/crawler/task/status')
async def get_crawler_task_status(request: TaskStatusRequest):
    """获取爬虫任务状态"""
    try:
        task_status = await crawler_integration_service.get_task_status(request.task_id)

        if not task_status:
            return {
                'success': False,
                'message': f"任务 {request.task_id} 不存在",
                'timestamp': datetime.now().isoformat()
            }

        return {
            'success': True,
            'data': task_status,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/api/v1/crawler/task/cancel')
async def cancel_crawler_task(request: TaskStatusRequest):
    """取消爬虫任务"""
    try:
        result = await crawler_integration_service.cancel_task(request.task_id)

        return {
            'success': result['success'],
            'message': result.get('message', '操作完成'),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/api/v1/crawler/config')
async def update_crawler_config(request: ConfigUpdateRequest):
    """更新爬虫服务配置"""
    try:
        # 更新服务配置
        if request.service_config:
            await crawler_integration_service.update_config(request.service_config)

        return {
            'success': True,
            'message': '爬虫服务配置更新成功',
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"更新爬虫配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/api/v1/crawler/metrics/reset')
async def reset_crawler_metrics():
    """重置爬虫性能指标"""
    try:
        await crawler_integration_service.reset_metrics()

        return {
            'success': True,
            'message': '爬虫指标已重置',
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"重置爬虫指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/api/v1/xiaonuo/crawler/analyze')
async def xiaonuo_crawler_analyze(user_input: str, context: str | None = None):
    """小诺爬虫智能分析接口"""
    try:
        # 解析上下文
        context_dict = {}
        if context:
            try:
                context_dict = json.loads(context)
            except (json.JSONDecodeError, TypeError, ValueError):
                context_dict = {'raw': context}

        # 使用小诺分析
        analysis = await crawler_integration_service.xiaonuo_controller.analyze_request(
            user_input, context_dict
        )

        return {
            'success': True,
            'data': analysis,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"小诺爬虫分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/api/v1/xiaonuo/crawler/chat')
async def xiaonuo_crawler_chat(user_input: str, context: dict[str, Any] | None = None):
    """小诺爬虫聊天接口 - 智能决策是否使用爬虫"""
    try:
        # 小诺智能执行
        result = await crawler_integration_service.xiaonuo_controller.smart_crawler_execution(
            user_input, context
        )

        return {
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"小诺爬虫聊天失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

# 专用场景接口
@app.post('/api/v1/crawler/patent/search')
async def patent_search(
    query: str,
    max_results: int = 100,
    include_claims: bool = True,
    date_range: str | None = None
):
    """专利检索接口"""
    try:
        result = await crawler_integration_service.process_request({
            'user_input': f"搜索专利: {query}",
            'mode': 'direct',
            'scenario': 'patent_search',
            'config': {
                'query': query,
                'max_results': max_results,
                'include_claims': include_claims,
                'date_range': date_range
            }
        })

        return {
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"专利检索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/api/v1/crawler/website/scrape')
async def website_scrape(
    urls: list[str],
    depth: int = 2,
    extract_links: bool = False,
    extract_images: bool = False
):
    """网站内容抓取接口"""
    try:
        result = await crawler_integration_service.process_request({
            'user_input': f"抓取网站内容: {len(urls)}个URL",
            'mode': 'direct',
            'scenario': 'website_scraping',
            'urls': urls,
            'config': {
                'depth': depth,
                'extract_links': extract_links,
                'extract_images': extract_images
            }
        })

        return {
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"网站抓取失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/api/v1/crawler/data/collect')
async def data_collect(
    sources: list[str],
    data_type: str = 'text',
    batch_size: int = 50,
    parallel_requests: int = 10
):
    """大规模数据收集接口"""
    try:
        result = await crawler_integration_service.process_request({
            'user_input': f"收集数据: {data_type}",
            'mode': 'scheduled',
            'scenario': 'data_collection',
            'urls': sources,
            'config': {
                'data_type': data_type,
                'batch_size': batch_size,
                'parallel_requests': parallel_requests
            }
        })

        return {
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"数据收集失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/api/v1/crawler/news/monitor')
async def news_monitor(
    keywords: list[str],
    sources: list[str] | None = None,
    time_range: str = '24h'
):
    """新闻监控接口"""
    try:
        result = await crawler_integration_service.process_request({
            'user_input': f"监控新闻: {', '.join(keywords)}",
            'mode': 'direct',
            'scenario': 'news_monitoring',
            'config': {
                'keywords': keywords,
                'sources': sources,
                'time_range': time_range
            }
        })

        return {
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"新闻监控失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/api/v1/crawler/competitor/analyze')
async def competitor_analyze(
    competitors: list[str],
    analysis_type: str = 'basic',
    include_pricing: bool = True
):
    """竞品分析接口"""
    try:
        result = await crawler_integration_service.process_request({
            'user_input': f"分析竞品: {', '.join(competitors)}",
            'mode': 'xiaonuo',
            'scenario': 'competitor_analysis',
            'config': {
                'competitors': competitors,
                'analysis_type': analysis_type,
                'include_pricing': include_pricing
            }
        })

        return {
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"竞品分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/api/v1/health')
async def health_check():
    """健康检查"""
    try:
        status = await crawler_integration_service.get_service_status()

        return {
            'status': 'healthy' if status['status'] == 'running' else 'unhealthy',
            'service': 'CrawlerIntegrationService',
            'version': '2.0.0',
            'components': {
                'crawler_tool': status['components']['crawler_tool']['tool']['status'],
                'xiaonuo_controller': 'XiaoNuoCrawlerController',
                'task_scheduler': status['components']['task_scheduler']['enabled']
            },
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# 获取任务列表
@app.get('/api/v1/crawler/tasks')
async def get_running_tasks():
    """获取正在运行的任务列表"""
    try:
        status = await crawler_integration_service.get_service_status()

        return {
            'success': True,
            'data': {
                'active_tasks': status['running_tasks'],
                'total_active': len(status['running_tasks']),
                'queue_size': status['components']['task_scheduler']['queue_size']
            },
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

if __name__ == '__main__':
    # 直接运行服务
    uvicorn.run(
        'crawler_api_server:app',
        host='0.0.0.0',
        port=8015,
        reload=True,
        log_level='info'
    )
