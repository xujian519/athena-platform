#!/usr/bin/env python3
"""
通用爬虫API服务
Universal Crawler API Service

Athena工作平台公共爬虫API，提供HTTP接口调用爬虫功能
"""

import json
import logging
import os

# 导入爬虫核心模块
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.logging_config import setup_logging

# 导入统一认证模块

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.universal_crawler import CrawlerConfig, UniversalCrawler
from utils.data_processor import DataProcessor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title='Athena通用爬虫API',
    description='Athena工作平台公共爬虫工具API服务',
    version='1.0.0'
)

# 添加CORS中间件

# 全局变量
active_crawlers = {}
task_results = {}

# 数据模型
class CrawlerConfigModel(BaseModel):
    """爬虫配置模型"""
    name: str = Field(..., description='爬虫名称')
    base_url: str = Field(..., description='基础URL')
    headers: dict[str, str] | None = Field(None, description='请求头')
    timeout: int | None = Field(30, description='超时时间(秒)')
    max_retries: int | None = Field(3, description='最大重试次数')
    retry_delay: float | None = Field(1.0, description='重试延迟(秒)')
    rate_limit: float | None = Field(1.0, description='速率限制(请求/秒)')
    use_proxy: bool | None = Field(False, description='是否使用代理')
    proxy_list: list[str] | None = Field(None, description='代理列表')
    cache_enabled: bool | None = Field(True, description='是否启用缓存')
    cache_ttl: int | None = Field(3600, description='缓存时间(秒)')

class CrawlRequest(BaseModel):
    """爬取请求模型"""
    urls: list[str] = Field(..., description='要爬取的URL列表')
    config: CrawlerConfigModel = Field(..., description='爬虫配置')
    extract_selector: str | None = Field(None, description='CSS选择器')
    extract_attributes: list[str] | None = Field(None, description='要提取的属性')
    save_format: str | None = Field('json', description='保存格式(json/csv)')
    background: bool | None = Field(False, description='是否后台运行')

class CrawlResponse(BaseModel):
    """爬取响应模型"""
    task_id: str
    status: str
    results: list[dict[str, Any]
    stats: dict[str, Any]
    message: str | None = None

# 配置文件路径
CONFIG_DIR = Path('/Users/xujian/Athena工作平台/services/crawler/config')
RESULTS_DIR = Path('/Users/xujian/Athena工作平台/data/crawler/results')
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

@app.get('/')
async def root():
    """根路径"""
    return {
        'message': 'Athena通用爬虫API服务',
        'version': '1.0.0',
        'status': 'running'
    }

@app.post('/crawl', response_model=CrawlResponse)
async def crawl_urls(request: CrawlRequest, background_tasks: BackgroundTasks):
    """
    爬取URL列表

    Args:
        request: 爬取请求
        background_tasks: 后台任务

    Returns:
        爬取响应
    """
    task_id = str(uuid.uuid4())

    # 创建爬虫配置
    config = CrawlerConfig(**request.config.dict())

    try:
        if request.background:
            # 后台任务
            background_tasks.add_task(
                crawl_urls_background,
                task_id,
                request.urls,
                config,
                request.extract_selector,
                request.extract_attributes,
                request.save_format
            )
            return CrawlResponse(
                task_id=task_id,
                status='started',
                results=[],
                stats={},
                message='任务已启动，请使用/task/{task_id}查询结果'
            )
        else:
            # 同步任务
            results, stats = await crawl_urls_sync(
                request.urls,
                config,
                request.extract_selector,
                request.extract_attributes
            )

            return CrawlResponse(
                task_id=task_id,
                status='completed',
                results=results,
                stats=stats
            )

    except Exception as e:
        logger.error(f"爬取任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}") from e

async def crawl_urls_sync(urls, config, extract_selector, extract_attributes):
    """同步爬取URL"""
    results = []

    async with UniversalCrawler(config) as crawler:
        for url in urls:
            try:
                response = await crawler.get_page(url)
                result = {
                    'url': url,
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'encoding': response.encoding,
                    'request_time': response.request_time,
                    'cached': response.cached
                }

                # 提取数据
                if extract_selector or extract_attributes:
                    soup = crawler.parse_html(response.content)

                    if extract_selector:
                        if extract_attributes:
                            # 提取属性
                            data = DataProcessor.extract_attributes(soup, extract_selector, extract_attributes)
                            result['extracted_data'] = data
                        else:
                            # 提取文本
                            text = DataProcessor.extract_text(soup, extract_selector)
                            result['extracted_text'] = text

                results.append(result)

            except Exception as e:
                result = {
                    'url': url,
                    'error': str(e),
                    'status': 'failed'
                }
                results.append(result)

    stats = crawler.get_stats()
    return results, stats

async def crawl_urls_background(task_id, urls, config, extract_selector, extract_attributes, save_format):
    """后台爬取URL"""
    task_results[task_id] = {'status': 'running', 'progress': 0}

    try:
        results, stats = await crawl_urls_sync(urls, config, extract_selector, extract_attributes)

        # 保存结果
        if save_format == 'json':
            result_file = RESULTS_DIR / f"{task_id}.json"
            DataProcessor.save_to_json({
                'task_id': task_id,
                'timestamp': datetime.now().isoformat(),
                'config': config.__dict__,
                'results': results,
                'stats': stats
            }, str(result_file))
        elif save_format == 'csv':
            result_file = RESULTS_DIR / f"{task_id}.csv"
            if results:
                DataProcessor.save_to_csv(results, str(result_file))

        task_results[task_id] = {
            'status': 'completed',
            'results': results,
            'stats': stats,
            'result_file': str(result_file)
        }

    except Exception as e:
        logger.error(f"后台任务失败 {task_id}: {str(e)}")
        task_results[task_id] = {
            'status': 'failed',
            'error': str(e)
        }

@app.get('/task/{task_id}')
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail='任务不存在')

    return task_results[task_id]

@app.get('/tasks')
async def list_tasks():
    """列出所有任务"""
    return {
        'tasks': [
            {
                'task_id': task_id,
                'status': data.get('status'),
                'timestamp': data.get('timestamp')
            }
            for task_id, data in task_results.items()
        ]
    }

@app.post('/extract/{task_id}')
async def extract_data_from_crawled_page(task_id: str, selector: str, attributes: list[str] = None):
    """从已爬取的页面中提取数据"""
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail='任务不存在')

    task_data = task_results[task_id]
    if task_data.get('status') != 'completed':
        raise HTTPException(status_code=400, detail='任务尚未完成')

    try:
        # 读取爬取结果
        result_file = Path(task_data.get('result_file', ''))
        if not result_file.exists():
            raise HTTPException(status_code=404, detail='结果文件不存在')

        with open(result_file, encoding='utf-8') as f:
            data = json.load(f)

        # 提取数据
        extracted_data = []
        for result in data.get('results', []):
            if result.get('content'):
                from ..utils.data_processor import DataProcessor
                soup = DataProcessor.parse_html('', parser='html.parser')  # 创建空的soup
                # 这里需要重新解析content，但需要恢复HTML结构
                # 暂时返回原始数据

                if attributes:
                    extracted = DataProcessor.extract_attributes(soup, selector, attributes)
                else:
                    extracted = DataProcessor.extract_text(soup, selector)

                extracted_data.append({
                    'url': result.get('url'),
                    'extracted_data': extracted
                })

        return {
            'task_id': task_id,
            'extracted_data': extracted_data
        }

    except Exception as e:
        logger.error(f"数据提取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据提取失败: {str(e)}") from e

@app.get('/stats')
async def get_crawler_stats():
    """获取爬虫统计信息"""
    total_tasks = len(task_results)
    completed_tasks = len([t for t in task_results.values() if t.get('status') == 'completed'])
    failed_tasks = len([t for t in task_results.values() if t.get('status') == 'failed'])
    running_tasks = len([t for t in task_results.values() if t.get('status') == 'running'])

    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'failed_tasks': failed_tasks,
        'running_tasks': running_tasks,
        'success_rate': f"{(completed_tasks / total_tasks * 100):.1f}%' if total_tasks > 0 else '0%"
    }

@app.delete('/task/{task_id}')
async def delete_task(task_id: str):
    """删除任务"""
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail='任务不存在')

    # 删除任务结果
    del task_results[task_id]

    # 删除结果文件
    result_file = RESULTS_DIR / f"{task_id}.json"
    if result_file.exists():
        result_file.unlink()

    return {'message': f"任务 {task_id} 已删除"}

# 预定义的爬虫配置
PRESET_CONFIGS = {
    'news': {
        'name': '新闻爬虫',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (compatible; NewsCrawler/1.0)'
        },
        'rate_limit': 0.5,
        'cache_enabled': True
    },
    'ecommerce': {
        'name': '电商爬虫',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (compatible; EcommerceCrawler/1.0)'
        },
        'rate_limit': 1.0,
        'cache_enabled': False
    },
    'social': {
        'name': '社交媒体爬虫',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (compatible; SocialCrawler/1.0)'
        },
        'rate_limit': 2.0,
        'cache_enabled': True
    }
}

@app.get('/presets')
async def get_preset_configs():
    """获取预定义配置"""
    return PRESET_CONFIGS

@app.get('/health')
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_crawlers': len(active_crawlers),
        'total_tasks': len(task_results)
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8001)  # 内网通信，通过Gateway访问
