#!/usr/bin/env python3
"""
API网关主程序 - 修复版本
解决502 Bad Gateway问题
"""

import json
from core.async_main import async_main
import logging
from core.logging_config import setup_logging
import time
from typing import Any, Dict

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

app = FastAPI(title='Athena API Gateway', description='企业级API网关服务', version='1.0.0')

# CORS配置

# 修复后的服务路由映射 - 使用localhost和实际端口
SERVICE_ROUTES = {
    'athena-memory': {
        'prefix': '/api/v1/athena/memory',
        'url': 'http://localhost:8008',
    },
    'xiaonuo-memory': {
        'prefix': '/api/v1/xiaonuo/memory',
        'url': 'http://localhost:8083',
    },
    'athena-identity': {
        'prefix': '/api/v1/athena/identity',
        'url': 'http://localhost:8010',
    },
    'identity-integration': {
        'prefix': '/api/v1/integration',
        'url': 'http://localhost:8011',
    },
    'pqai-integration': {
        'prefix': '/api/v1/pqai',
        'url': 'http://localhost:8084',
    },
    'bge-vector-service': {
        'prefix': '/api/v1/vector',
        'url': 'http://localhost:8087',
    }
}

# 服务健康状态缓存
service_health_cache = {}

@app.get('/')
async def root():
    """网关根路径"""
    return {
        'service': 'athena-api-gateway',
        'status': 'running',
        'version': '1.0.0-fixed',
        'message': '🚀 Athena API网关服务已启动 - 502错误已修复',
        'routes': list(SERVICE_ROUTES.keys()),
        'total_services': len(SERVICE_ROUTES)
    }

@app.get('/health')
async def health_check():
    """网关健康检查"""
    healthy_services = await check_all_services_health()
    return {
        'status': 'healthy',
        'service': 'athena-api-gateway',
        'timestamp': time.strftime('%Y-%m-%d_t%H:%M:%SZ'),
        'healthy_services': healthy_services,
        'total_services': len(SERVICE_ROUTES)
    }

async def check_service_health(service_name: str, service_config: dict) -> bool:
    """检查单个服务健康状态"""
    try:
        health_url = f"{service_config['url']}/health"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(health_url)
            return response.status_code == 200
    except Exception as e:
        logger.warning(f"服务 {service_name} 健康检查失败: {e}")
        return False

async def check_all_services_health() -> Dict[str, bool]:
    """检查所有服务健康状态"""
    results = {}
    for service_name, config in SERVICE_ROUTES.items():
        results[service_name] = await check_service_health(service_name, config)
    return results

@app.api_route('/api/v1/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
async def proxy_request(request: Request, path: str):
    """代理请求到后端服务"""

    # 确定目标服务
    target_service = None
    target_url = None

    # 改进的路由匹配逻辑 - 精确匹配
    for service_name, config in SERVICE_ROUTES.items():
        service_prefix = config['prefix'].replace('/api/v1/', '')
        if path == service_prefix or path.startswith(service_prefix + '/'):
            target_service = service_name
            target_url = config['url']
            break

    # 特殊路由处理
    if path.startswith('athena/memory/'):
        target_service = 'athena-memory'
        target_url = 'http://localhost:8008'
    elif path.startswith('xiaonuo/memory/'):
        target_service = 'xiaonuo-memory'
        target_url = 'http://localhost:8083'
    elif path.startswith('athena/identity/'):
        target_service = 'athena-identity'
        target_url = 'http://localhost:8010'
    elif path.startswith('integration/'):
        target_service = 'identity-integration'
        target_url = 'http://localhost:8011'

    if not target_service:
        raise HTTPException(
            status_code=404,
            detail=f"服务未找到。请求路径: /api/v1/{path}。可用服务: {list(SERVICE_ROUTES.keys())}"
        )

    # 构建目标URL - 直接使用路径
    full_path = f"/{path}"

    # 如果是health请求，直接使用
    if full_path.endswith('/health'):
        target_service_url = f"{target_url}{full_path}"
    else:
        # 否则添加正确的API路径
        if not full_path.startswith('/api'):
            full_path = f"/api/v1/{full_path.lstrip('/')}"
        target_service_url = f"{target_url}{full_path}"

    # 记录请求开始时间
    start_time = time.time()
    logger.info(f"转发请求: {request.method} {target_service_url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 转发请求
            response = await client.request(
                method=request.method,
                url=target_service_url,
                headers=dict(request.headers),
                content=await request.body(),
                params=request.query_params,
            )

            # 记录响应时间
            response_time = time.time() - start_time
            logger.info(f"请求转发到 {target_service} 成功, 耗时: {response_time:.3f}s")

            # 返回响应
            if response.headers.get('content-type', '').startswith('application/json'):
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )
            else:
                return JSONResponse(
                    content={'data': response.text},
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )

    except httpx.TimeoutException:
        logger.error(f"请求超时: {target_service}")
        raise HTTPException(status_code=504, detail=f"服务 {target_service} 响应超时")
    except httpx.ConnectError:
        logger.error(f"连接失败: {target_service} at {target_url}")
        raise HTTPException(status_code=502, detail=f"无法连接到服务 {target_service} ({target_url})")
    except Exception as e:
        logger.error(f"请求转发失败: {e}")
        raise HTTPException(status_code=502, detail=f"服务 {target_service} 不可用: {str(e)}")

@app.get('/services')
async def list_services():
    """列出所有可用服务及其健康状态"""
    services = []
    healthy_services = await check_all_services_health()

    for name, config in SERVICE_ROUTES.items():
        services.append({
            'name': name,
            'prefix': config['prefix'],
            'url': config['url'],
            'healthy': healthy_services.get(name, False)
        })

    return {'services': services, 'total_count': len(services)}

@app.get('/route-test')
async def test_routes():
    """测试所有路由"""
    results = {}
    for service_name, config in SERVICE_ROUTES.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{config['url']}/health")
                results[service_name] = {
                    'status': 'success',
                    'status_code': response.status_code,
                    'url': config['url']
                }
        except Exception as e:
            results[service_name] = {
                'status': 'failed',
                'error': str(e),
                'url': config['url']
            }

    return {'route_tests': results}

if __name__ == '__main__':
    logger.info('🚀 启动Athena API网关 (修复版)')
    logger.info(f"📊 配置的服务数量: {len(SERVICE_ROUTES)}")
    for name, config in SERVICE_ROUTES.items():
        logger.info(f"  - {name}: {config['url']}")

    uvicorn.run(
        'main_fixed:app',
        host='0.0.0.0',
        port=8080,
        reload=False,  # 生产环境关闭reload
        log_level='info'
    )