#!/usr/bin/env python3
"""
Athena平台浏览器自动化API服务
为整个平台提供统一的浏览器自动化接口
"""

import asyncio
from core.async_main import async_main
import logging
from core.logging_config import setup_logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from browser_integration_service import get_integration_service
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title='Athena平台浏览器自动化API',
    description='为Athena平台和小诺提供统一的浏览器自动化服务',
    version='1.0.0'
)

# 添加CORS中间件

# 请求模型
class TaskRequest(BaseModel):
    """任务请求模型"""
    user_input: str
    mode: str = 'auto'  # auto, xiaonuo, athena, direct
    context: Optional[Dict[str, Any]] = None
    scenario: str | None = None
    priority: str = 'normal'  # low, normal, high, urgent

class BatchTaskRequest(BaseModel):
    """批量任务请求模型"""
    requests: List[TaskRequest]
    max_concurrent: int = 5

class ConfigUpdateRequest(BaseModel):
    """配置更新请求模型"""
    service_config: Optional[Dict[str, Any]] = None
    xiaonuo_config: Optional[Dict[str, Any]] = None

# 初始化集成服务
integration_service = None

@app.on_event('startup')
async def startup_event():
    """应用启动事件"""
    global integration_service
    logger.info('启动Athena平台浏览器自动化API服务...')

    integration_service = get_integration_service()

    # 等待服务初始化
    await asyncio.sleep(2)

    logger.info('API服务启动成功')

@app.on_event('shutdown')
async def shutdown_event():
    """应用关闭事件"""
    logger.info('正在关闭API服务...')

    if integration_service:
        await integration_service.shutdown()

    logger.info('API服务已关闭')

@app.get('/')
async def root():
    """根路径"""
    return {
        'service': 'Athena平台浏览器自动化API',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    }

@app.post('/api/v1/task')
async def execute_task(request: TaskRequest):
    """执行单个浏览器自动化任务"""
    try:
        # 构建请求参数
        task_params = {
            'user_input': request.user_input,
            'mode': request.mode,
            'context': request.context or {},
            'scenario': request.scenario
        }

        # 执行任务
        result = await integration_service.process_request(task_params)

        return {
            'success': True,
            'data': result,
            'message': '任务执行完成',
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"执行任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/v1/tasks/batch')
async def execute_batch_tasks(request: BatchTaskRequest):
    """批量执行浏览器自动化任务"""
    try:
        # 构建批量请求
        batch_requests = []
        for i, task_req in enumerate(request.requests):
            batch_requests.append({
                'request_id': f"batch_{i}",
                'user_input': task_req.user_input,
                'mode': task_req.mode,
                'context': task_req.context or {},
                'scenario': task_req.scenario
            })

        # 批量执行
        results = await integration_service.batch_process(batch_requests)

        return {
            'success': True,
            'data': {
                'results': results,
                'total': len(results),
                'successful': sum(1 for r in results if r['success']),
                'failed': sum(1 for r in results if not r['success'])
            },
            'message': '批量任务执行完成',
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"批量执行任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/v1/scenarios')
async def get_available_scenarios():
    """获取可用的自动化场景"""
    try:
        scenarios = await integration_service.get_available_scenarios()

        return {
            'success': True,
            'data': scenarios,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取场景列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/v1/status')
async def get_service_status():
    """获取服务状态"""
    try:
        status = await integration_service.get_service_status()

        return {
            'success': True,
            'data': status,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取服务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/v1/config')
async def update_config(request: ConfigUpdateRequest):
    """更新服务配置"""
    try:
        # 更新服务配置
        if request.service_config:
            await integration_service.update_config(request.service_config)

        # 更新小诺配置
        if request.xiaonuo_config:
            integration_service.xiaonuo_controller.update_config(request.xiaonuo_config)

        return {
            'success': True,
            'message': '配置更新成功',
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/v1/metrics/reset')
async def reset_metrics():
    """重置性能指标"""
    try:
        await integration_service.reset_metrics()

        return {
            'success': True,
            'message': '指标已重置',
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"重置指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/v1/xiaonuo/analyze')
async def xiaonuo_analyze(user_input: str, context: str | None = None):
    """小诺智能分析接口"""
    try:
        # 解析上下文
        context_dict = {}
        if context:
            try:
                context_dict = json.loads(context)
            except (json.JSONDecodeError, TypeError, ValueError):
                context_dict = {'raw': context}

        # 使用小诺分析
        analysis = await integration_service.xiaonuo_controller.analyze_request(
            user_input, context_dict
        )

        return {
            'success': True,
            'data': analysis,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"小诺分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/v1/health')
async def health_check():
    """健康检查"""
    try:
        status = await integration_service.get_service_status()

        return {
            'status': 'healthy' if status['status'] == 'running' else 'unhealthy',
            'service': 'BrowserIntegrationService',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# 专用的小诺接口
@app.post('/api/v1/xiaonuo/chat')
async def xiaonuo_chat(user_input: str, context: Optional[Dict[str, Any]] = None):
    """小诺聊天接口 - 智能决策是否使用浏览器自动化"""
    try:
        # 小诺智能执行
        result = await integration_service.xiaonuo_controller.smart_task_execution(
            user_input, context
        )

        return {
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"小诺聊天失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 专利检索专用接口
@app.post('/api/v1/patent/search')
async def patent_search(query: str, database: str = 'cnipa', max_results: int = 10):
    """专利检索接口"""
    try:
        # 使用专利检索场景
        result = await integration_service.process_request({
            'user_input': f"在{database}数据库中搜索专利: {query}",
            'mode': 'direct',
            'scenario': 'patent_search',
            'context': {
                'query': query,
                'database': database,
                'max_results': max_results
            }
        })

        return {
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"专利检索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 竞品监控专用接口
@app.post('/api/v1/competitor/monitor')
async def competitor_monitor(competitor_name: str, monitoring_items: List[str]):
    """竞品监控接口"""
    try:
        # 构建监控任务
        items_text = '、'.join(monitoring_items)
        user_input = f"监控{competitor_name}的{items_text}"

        result = await integration_service.process_request({
            'user_input': user_input,
            'mode': 'xiaonuo',
            'context': {
                'competitor': competitor_name,
                'items': monitoring_items
            }
        })

        return {
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"竞品监控失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    # 直接运行服务
    uvicorn.run(
        'api_server:app',
        host='0.0.0.0',
        port=8014,
        reload=True,
        log_level='info'
    )