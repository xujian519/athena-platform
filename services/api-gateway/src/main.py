#!/usr/bin/env python3
"""
API网关主程序
Enterprise API Gateway
"""

import logging
import time

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

# 导入统一认证模块
from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

app = FastAPI(title='Athena API Gateway', description='企业级API网关服务', version='1.0.0')

# CORS配置

# 服务路由映射
SERVICE_ROUTES = {
    'patent-analysis': {
        'prefix': '/api/v1/patents',
        'url': 'http://patent-analysis-service:8081',
    },
    'deepseek-math': {
        'prefix': '/api/v1/ai/deepseek',
        'url': 'http://deepseek-math-service:8022',
    },
    'knowledge-graph': {
        'prefix': '/api/v1/kg',
        'url': 'http://knowledge-graph-service:8082',
    },
    'multimodal': {
        'prefix': '/api/v1/files',
        'url': 'http://localhost:8001',
    },
}


@app.get('/')
async def root():
    """网关根路径"""
    return {
        'service': 'api-gateway',
        'status': 'running',
        'version': '1.0.0',
        'message': 'Athena API网关服务已启动',
        'routes': list(SERVICE_ROUTES.keys()),
    }


@app.get('/health')
async def health_check():
    """健康检查端点"""
    return {
        'status': 'healthy',
        'service': 'api-gateway',
        'timestamp': '2025-11-28T22:45:00Z',
    }


@app.api_route('/api/v1/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
async def proxy_request(request: Request, path: str):
    """代理请求到后端服务"""

    # 确定目标服务
    target_service = None
    target_url = None

    for service_name, config in SERVICE_ROUTES.items():
        if path.startswith(config['prefix'].replace('/api/v1/', '')):
            target_service = service_name
            target_url = config['url']
            break

    if not target_service:
        raise HTTPException(status_code=404, detail='服务未找到')

    # 构建目标URL
    full_path = f"/{path}"
    target_service_url = f"{target_url}{full_path}"

    # 记录请求开始时间
    start_time = time.time()

    try:
        async with httpx.AsyncClient() as client:
            # 转发请求
            response = await client.request(
                method=request.method,
                url=target_service_url,
                headers=dict(request.headers),
                content=await request.body(),
                params=request.query_params,
                timeout=30.0,
            )

            # 记录响应时间
            response_time = time.time() - start_time
            logger.info(f"请求转发到 {target_service}, 耗时: {response_time:.3f}s")

            return JSONResponse(
                content=response.json()
                if response.headers.get('content-type', '').startswith(
                    'application/json'
                )
                else response.text,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

    except httpx.TimeoutException:
        logger.error(f"请求超时: {target_service}")
        raise HTTPException(status_code=504, detail='服务响应超时') from None
    except Exception as e:
        logger.error(f"请求转发失败: {e}")
        raise HTTPException(status_code=502, detail='服务不可用') from e


@app.get('/services')
async def list_services():
    """列出所有可用服务"""
    services = []
    for name, config in SERVICE_ROUTES.items():
        services.append(
            {'name': name, 'prefix': config['prefix'], 'url': config['url']}
        )
    return {'services': services}


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8080, reload=True, log_level='info')
