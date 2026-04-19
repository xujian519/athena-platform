#!/usr/bin/env python3
"""
API网关主程序 - 增强版本
集成统一身份服务和协作中枢
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

# 导入统一认证模块
from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

app = FastAPI(
    title='Athena Enhanced API Gateway',
    description='企业级API网关服务 - 集成身份管理与协作中枢',
    version='2.0.0'
)

# CORS配置

# 增强的服务路由映射 - 添加新服务
SERVICE_ROUTES = {
    # 原有服务
    'athena-memory': {
        'prefix': '/api/v1/athena/memory',
        'url': 'http://localhost:8008',
    },
    'xiaonuo-memory': {
        'prefix': '/api/v1/xiaonuo/memory',
        'url': 'http://localhost:8083',
    },
    'pqai-integration': {
        'prefix': '/api/v1/pqai',
        'url': 'http://localhost:8084',
    },
    'bge-vector-service': {
        'prefix': '/api/v1/vector',
        'url': 'http://localhost:8087',
    },

    # 新增服务 - 身份管理与协作
    'unified-identity': {
        'prefix': '/api/v1/identity',
        'url': 'http://localhost:8090',
        'features': ['identity_management', 'role_switching', 'collaboration_config']
    },
    'intelligent-collaboration': {
        'prefix': '/api/v1/collaboration',
        'url': 'http://localhost:8091',
        'features': ['task_routing', 'result_synthesis', 'ai_coordination']
    },

    # AI服务
    'deepseek-service': {
        'prefix': '/api/v1/ai/deepseek',
        'url': 'http://localhost:8020',
    },
    'glm-service': {
        'prefix': '/api/v1/ai/glm',
        'url': 'http://localhost:8021',
    },

    # 核心业务服务
    'patent-service': {
        'prefix': '/api/v1/patents',
        'url': 'http://localhost:8081',
    },
    'knowledge-graph': {
        'prefix': '/api/v1/knowledge',
        'url': 'http://localhost:8082',
    }
}

# 服务健康状态缓存
service_health_cache = {}
last_health_check = None

# 智能路由配置
INTELLIGENT_ROUTING = {
    '/api/v1/family': {
        'description': 'AI家庭服务 - 智能路由到最适合的AI',
        'routing_strategy': 'ai_family'
    },
    '/api/v1/unified': {
        'description': '统一服务接口 - 整合多个AI能力',
        'routing_strategy': 'unified_service'
    }
}

@app.get('/')
async def root():
    """网关根路径"""
    return {
        'service': 'athena-enhanced-api-gateway',
        'status': 'running',
        'version': '2.0.0',
        'message': '🚀 Athena增强版API网关 - 集成身份管理与协作中枢',
        'features': [
            '统一身份管理',
            '智能任务路由',
            'AI协作协调',
            '服务健康监控'
        ],
        'routes': {
            'standard': list(SERVICE_ROUTES.keys()),
            'intelligent': list(INTELLIGENT_ROUTING.keys())
        },
        'total_services': len(SERVICE_ROUTES)
    }

@app.get('/health')
async def health_check():
    """网关健康检查"""
    healthy_services = await check_all_services_health()
    return {
        'status': 'healthy',
        'service': 'athena-enhanced-api-gateway',
        'timestamp': time.strftime('%Y-%m-%d_t%H:%M:%SZ'),
        'healthy_services': healthy_services,
        'total_services': len(SERVICE_ROUTES),
        'health_percentage': len(healthy_services) / len(SERVICE_ROUTES) * 100
    }

@app.get('/api/v1/services/status')
async def get_services_status():
    """获取所有服务状态"""
    healthy_services = await check_all_services_health()
    status_info = {}

    for service_name, config in SERVICE_ROUTES.items():
        status_info[service_name] = {
            'url': config['url'],
            'prefix': config['prefix'],
            'healthy': service_name in healthy_services,
            'features': config.get('features', []),
            'last_check': service_health_cache.get(service_name, {}).get('last_check')
        }

    return {
        'total_services': len(SERVICE_ROUTES),
        'healthy_count': len(healthy_services),
        'services': status_info,
        'timestamp': datetime.now().isoformat()
    }

# AI家庭服务智能路由
@app.post('/api/v1/family/collaborate')
async def family_collaborate(request: Request):
    """AI家庭协作接口"""
    try:
        # 解析请求
        request_data = await request.json()
        task_type = request_data.get('task_type', 'technical')
        complexity = request_data.get('complexity', 0.5)

        # 智能路由到身份服务获取协作配置
        async with httpx.AsyncClient() as client:
            # 请求身份服务获取最优参与者
            identity_response = await client.post(
                'http://localhost:8090/api/v1/collaboration',
                json=request_data,
                timeout=5.0
            )

            if identity_response.status_code == 200:
                collaboration_config = identity_response.json()

                # 创建协作任务
                task_request = {
                    'type': task_type,
                    'description': request_data.get('task', ''),
                    'complexity': complexity,
                    'priority': request_data.get('priority', 1),
                    'requirements': request_data.get('requirements', {})
                }

                # 提交到协作中枢
                collaboration_response = await client.post(
                    'http://localhost:8091/api/v1/tasks',
                    json=task_request,
                    timeout=5.0
                )

                if collaboration_response.status_code == 200:
                    task_info = collaboration_response.json()
                    return {
                        'status': 'success',
                        'message': 'AI家庭协作任务已创建',
                        'task_id': task_info['task_id'],
                        'collaboration_config': collaboration_config,
                        'participants': collaboration_config['participants'],
                        'mode': collaboration_config['mode'],
                        'estimated_efficiency': collaboration_config['estimated_efficiency']
                    }

        # 如果路由失败，返回错误
        raise HTTPException(status_code=500, detail='协作路由失败')

    except Exception as e:
        logger.error(f"AI家庭协作失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"协作请求失败: {str(e)}") from e

@app.get('/api/v1/family/{task_id}/status')
async def get_family_task_status(task_id: str):
    """获取AI家庭任务状态"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8091/api/v1/tasks/{task_id}",
                timeout=5.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=404, detail='任务未找到')

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}") from e

# 统一服务接口
@app.post('/api/v1/unified/process')
async def unified_process(request: Request):
    """统一处理接口 - 智能分配任务"""
    try:
        request_data = await request.json()
        process_type = request_data.get('type', 'auto')

        # 智能分析任务类型
        if process_type == 'auto':
            process_type = await analyze_task_type(request_data)

        # 根据类型路由到相应服务
        if process_type in ['technical', 'implementation']:
            # 路由到小诺相关的服务
            return await route_to_service(request_data, 'xiaonuo-memory')
        elif process_type in ['analytical', 'strategic']:
            # 路由到Athena相关的服务
            return await route_to_service(request_data, 'athena-memory')
        else:
            # 需要协作
            return await route_to_collaboration(request_data)

    except Exception as e:
        logger.error(f"统一处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}") from e

async def analyze_task_type(request_data: dict) -> str:
    """分析任务类型"""
    content = request_data.get('content', '').lower()

    if any(keyword in content for keyword in ['分析', '策略', '评估', '建议']):
        return 'analytical'
    elif any(keyword in content for keyword in ['实现', '代码', '开发', '优化']):
        return 'technical'
    else:
        return 'collaborative'

async def route_to_service(request_data: dict, service_name: str) -> dict:
    """路由到特定服务"""
    service_config = SERVICE_ROUTES.get(service_name)
    if not service_config:
        raise HTTPException(status_code=404, detail=f"服务未找到: {service_name}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{service_config['url']}/process",
                json=request_data,
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务调用失败: {str(e)}") from e

async def route_to_collaboration(request_data: dict) -> dict:
    """路由到协作服务"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'http://localhost:8091/api/v1/tasks',
                json={
                    'type': 'collaborative',
                    'description': request_data.get('content', ''),
                    'requirements': request_data
                },
                timeout=5.0
            )

            if response.status_code == 200:
                task_info = response.json()
                return {
                    'status': 'task_created',
                    'task_id': task_info['task_id'],
                    'message': '协作任务已创建，正在处理中'
                }
            else:
                raise HTTPException(status_code=500, detail='创建协作任务失败')

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"协作路由失败: {str(e)}") from e

# 通用代理处理函数
@app.api_route('/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
async def proxy_request(request: Request, path: str):
    """通用请求代理"""
    # 查找匹配的服务
    for service_name, config in SERVICE_ROUTES.items():
        if path.startswith(config['prefix'].lstrip('/')):
            return await proxy_to_service(request, service_name, config)

    # 检查智能路由
    for route_path, route_config in INTELLIGENT_ROUTING.items():
        if path.startswith(route_path.lstrip('/')):
            return await handle_intelligent_route(request, path, route_config)

    # 未找到匹配的路由
    raise HTTPException(status_code=404, detail='服务未找到')

async def proxy_to_service(request: Request, service_name: str, config: dict):
    """代理到具体服务"""
    target_url = f"{config['url']}/{request.url.path.lstrip('/').lstrip(config['prefix'].lstrip('/'))}"

    # 转发查询参数
    query_params = str(request.url.query) if request.url.query else ''
    if query_params:
        target_url += f"?{query_params}"

    try:
        # 获取请求数据
        body = await request.body()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=dict(request.headers),
                content=body
            )

            return JSONResponse(
                content=response.json(),
                status_code=response.status_code,
                headers=dict(response.headers)
            )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail='服务超时') from None
    except Exception as e:
        logger.error(f"代理请求失败 {service_name}: {str(e)}")
        raise HTTPException(status_code=502, detail='服务错误') from e

async def handle_intelligent_route(request: Request, path: str, config: dict):
    """处理智能路由"""
    # 这里可以实现更复杂的智能路由逻辑
    # 例如基于请求内容、AI负载、服务健康状况等

    # 示例：AI家庭服务路由
    if path.startswith('family/collaborate'):
        return await family_collaborate(request)
    elif path.startswith('family/'):
        # 其他AI家庭服务
        task_id = path.split('/')[-1] if len(path.split('/')) > 1 else None
        if task_id and request.method == 'GET':
            return await get_family_task_status(task_id)

    raise HTTPException(status_code=404, detail='智能路由未实现')

# 服务健康检查相关函数
async def check_service_health(service_name: str, service_config: dict) -> bool:
    """检查单个服务健康状态"""
    try:
        health_url = f"{service_config['url']}/health"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(health_url)
            is_healthy = response.status_code == 200

            # 更新缓存
            service_health_cache[service_name] = {
                'healthy': is_healthy,
                'last_check': datetime.now().isoformat(),
                'response_time': response.elapsed.total_seconds()
            }

            return is_healthy
    except Exception as e:
        logger.warning(f"服务 {service_name} 健康检查失败: {e}")
        service_health_cache[service_name] = {
            'healthy': False,
            'last_check': datetime.now().isoformat(),
            'error': str(e)
        }
        return False

async def check_all_services_health() -> dict[str, bool]:
    """检查所有服务健康状态"""
    global last_health_check

    # 如果距离上次检查不到30秒，使用缓存
    if last_health_check and (datetime.now() - last_health_check) < timedelta(seconds=30):
        return {
            name: info['healthy']
            for name, info in service_health_cache.items()
        }

    # 执行健康检查
    healthy_services = {}
    tasks = []

    for service_name, config in SERVICE_ROUTES.items():
        task = asyncio.create_task(check_service_health(service_name, config))
        tasks.append((service_name, task))

    for service_name, task in tasks:
        try:
            healthy_services[service_name] = await task
        except Exception as e:
            logger.error(f"健康检查异常 {service_name}: {e}")
            healthy_services[service_name] = False

    last_health_check = datetime.now()
    return healthy_services

# 后台任务：定期健康检查
async def periodic_health_check():
    """定期健康检查"""
    while True:
        await check_all_services_health()
        await asyncio.sleep(60)  # 每分钟检查一次

# 启动时运行后台任务
@app.on_event('startup')
async def startup_event():
    """启动事件"""
    # 启动健康检查任务
    asyncio.create_task(periodic_health_check())
    logger.info('🚀 Athena增强版API网关已启动')
    logger.info('✨ 新增功能: 统一身份管理 & 智能协作中枢')

# 启动服务
if __name__ == '__main__':
    logger.info(str("\n" + '='*60))
    logger.info('🚀 Athena增强版API网关启动')
    logger.info(str('='*60))
    logger.info('📍 服务地址: http://localhost:8080')
    logger.info('📖 API文档: http://localhost:8080/docs')
    logger.info('💚 健康检查: http://localhost:8080/health')
    logger.info('🔍 服务状态: http://localhost:8080/api/v1/services/status')
    logger.info("\n🎯 集成的新服务:")
    logger.info('  • 统一身份服务 (端口8090)')
    logger.info('  • 智能协作中枢 (端口8091)')
    logger.info("\n🤖 AI家庭服务端点:")
    logger.info('  • POST /api/v1/family/collaborate - 创建协作任务')
    logger.info('  • GET  /api/v1/family/{task_id}/status - 查询任务状态')
    logger.info(str('='*60 + "\n"))

    uvicorn.run(
        'main_enhanced:app',
        host='0.0.0.0',
        port=8081,
        reload=True,
        log_level='info'
    )
