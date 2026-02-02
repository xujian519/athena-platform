#!/usr/bin/env python3
"""
优化的API网关主程序
性能优化版本 - 支持连接池、缓存、负载均衡
"""

import logging
from core.async_main import async_main
from core.logging_config import setup_logging
import time
import asyncio
import json
from typing import Any, Dict, Optional, List
from functools import lru_cache
from dataclasses import dataclass

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

app = FastAPI(
    title='Athena API Gateway Optimized',
    description='企业级API网关服务 - 性能优化版',
    version='2.0.0'
)

# 性能优化中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 速率限制
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 连接池配置
@dataclass
class ServiceConfig:
    name: str
    prefix: str
    urls: List[str]  # 支持多个URL用于负载均衡
    timeout: float = 30.0
    retries: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60

# 服务路由映射 - 支持负载均衡
SERVICE_ROUTES = {
    'patent-analysis': ServiceConfig(
        name='patent-analysis',
        prefix='/api/v1/patents',
        urls=['http://patent-analysis-service:8081', 'http://localhost:8081'],
        timeout=20.0,
        retries=2
    ),
    'deepseek-math': ServiceConfig(
        name='deepseek-math',
        prefix='/api/v1/ai/deepseek',
        urls=['http://deepseek-math-service:8022', 'http://localhost:8022'],
        timeout=45.0,
        retries=1
    ),
    'knowledge-graph': ServiceConfig(
        name='knowledge-graph',
        prefix='/api/v1/kg',
        urls=['http://knowledge-graph-service:8082', 'http://localhost:8082'],
        timeout=30.0,
        retries=2
    ),
    'multimodal': ServiceConfig(
        name='multimodal',
        prefix='/api/v1/files',
        urls=['http://localhost:8001'],
        timeout=60.0,
        retries=1
    ),
}

# 服务健康状态
class ServiceHealth:
    def __init__(self):
        self._healthy_urls: Dict[str, List[str]] = {}
        self._circuit_breakers: Dict[str, float] = {}

    def get_healthy_urls(self, service_name: str) -> List[str]:
        """获取健康的URL列表"""
        return self._healthy_urls.get(service_name, SERVICE_ROUTES[service_name].urls)

    def mark_unhealthy(self, service_name: str, url: str):
        """标记URL为不健康"""
        if service_name not in self._healthy_urls:
            self._healthy_urls[service_name] = SERVICE_ROUTES[service_name].urls.copy()

        if url in self._healthy_urls[service_name]:
            self._healthy_urls[service_name].remove(url)
            logger.warning(f"标记 {service_name} 的 URL {url} 为不健康")

    def is_circuit_open(self, service_name: str) -> bool:
        """检查熔断器是否打开"""
        if service_name not in self._circuit_breakers:
            return False

        if time.time() - self._circuit_breakers[service_name] > SERVICE_ROUTES[service_name].circuit_breaker_timeout:
            del self._circuit_breakers[service_name]
            return False

        return True

    def trip_circuit_breaker(self, service_name: str):
        """触发熔断器"""
        self._circuit_breakers[service_name] = time.time()
        logger.error(f"服务 {service_name} 熔断器已打开")

service_health = ServiceHealth()

# 连接池管理
class ConnectionPoolManager:
    def __init__(self):
        self._pools: Dict[str, httpx.AsyncClient] = {}

    async def get_client(self, base_url: str, timeout: float = 30.0) -> httpx.AsyncClient:
        """获取连接池客户端"""
        if base_url not in self._pools:
            self._pools[base_url] = httpx.AsyncClient(
                base_url=base_url,
                timeout=timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=50,
                    max_connections=100,
                    keepalive_expiry=30.0
                )
            )
        return self._pools[base_url]

    async def close_all(self):
        """关闭所有连接池"""
        for client in self._pools.values():
            await client.aclose()

pool_manager = ConnectionPoolManager()

# Redis缓存
class CacheManager:
    def __init__(self):
        self.redis_client: redis.Redis | None = None

    async def connect(self):
        """连接Redis"""
        try:
            self.redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
            await self.redis_client.ping()
            logger.info("Redis缓存连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}，将禁用缓存")
            self.redis_client = None

    async def get(self, key: str) -> Dict | None:
        """获取缓存"""
        if not self.redis_client:
            return None
        try:
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"缓存读取失败: {e}")
        return None

    async def set(self, key: str, data: Dict, ttl: int = 300):
        """设置缓存"""
        if not self.redis_client:
            return
        try:
            await self.redis_client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            logger.warning(f"缓存写入失败: {e}")

cache_manager = CacheManager()

# 启动时初始化
@app.on_event("startup")
async def startup_event():
    await cache_manager.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await pool_manager.close_all()

# 负载均衡选择器
def select_url(urls: List[str]) -> str:
    """简单的轮询负载均衡"""
    if not urls:
        return None
    # 这里可以实现更复杂的负载均衡算法
    return urls[time.time() % len(urls)]

# 缓存键生成
@lru_cache(maxsize=1000)
def generate_cache_key(method: str, path: str, params_str: str) -> str:
    """生成缓存键"""
    return f"gateway:{method}:{path}:{params_str}"

@app.get('/')
@limiter.limit("100/minute")
async def root(request: Request):
    """网关根路径"""
    return {
        'service': 'api-gateway-optimized',
        'status': 'running',
        'version': '2.0.0',
        'message': 'Athena API网关服务 - 性能优化版已启动',
        'routes': [config.name for config in SERVICE_ROUTES.values()],
        'features': ['负载均衡', '连接池', '缓存', '熔断器', '速率限制']
    }

@app.get('/health')
async def health_check():
    """健康检查端点"""
    services_status = {}
    for name, config in SERVICE_ROUTES.items():
        healthy_urls = service_health.get_healthy_urls(name)
        services_status[name] = {
            'status': 'healthy' if healthy_urls else 'unhealthy',
            'healthy_urls': len(healthy_urls),
            'circuit_open': service_health.is_circuit_open(name)
        }

    return {
        'status': 'healthy',
        'service': 'api-gateway',
        'timestamp': time.time(),
        'services': services_status
    }

@app.api_route('/api/v1/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@limiter.limit("200/minute")
async def proxy_request(request: Request, path: str):
    """优化的代理请求处理"""

    start_time = time.time()

    # 确定目标服务
    target_service = None
    target_config = None

    for service_name, config in SERVICE_ROUTES.items():
        if path.startswith(config.prefix.replace('/api/v1/', '')):
            target_service = service_name
            target_config = config
            break

    if not target_service:
        raise HTTPException(status_code=404, detail='服务未找到')

    # 检查熔断器
    if service_health.is_circuit_open(target_service):
        raise HTTPException(status_code=503, detail=f'服务 {target_service} 熔断器已打开')

    # 缓存检查（仅对GET请求）
    if request.method == 'GET':
        params_str = str(sorted(request.query_params.items()))
        cache_key = generate_cache_key(request.method, request.url.path, params_str)
        cached_response = await cache_manager.get(cache_key)
        if cached_response:
            logger.info(f"缓存命中: {request.url.path}")
            return JSONResponse(
                content=cached_response['data'],
                status_code=cached_response['status'],
                headers=cached_response.get('headers', {})
            )

    # 获取健康的URL
    healthy_urls = service_health.get_healthy_urls(target_service)
    if not healthy_urls:
        raise HTTPException(status_code=503, detail='服务不可用')

    target_url = select_url(healthy_urls)
    full_target_url = f"{target_url}/{path}"

    # 请求处理
    last_error = None
    for attempt in range(target_config.retries + 1):
        try:
            client = await pool_manager.get_client(target_url, target_config.timeout)

            # 转发请求
            response = await client.request(
                method=request.method,
                url=full_target_url[len(target_url):],  # 移除base_url部分
                headers=dict(request.headers),
                content=await request.body(),
                params=request.query_params,
            )

            # 记录响应时间
            response_time = time.time() - start_time
            logger.info(f"请求转发到 {target_service}({target_url}), 耗时: {response_time:.3f}s")

            # 缓存响应（仅对成功的GET请求）
            if request.method == 'GET' and response.status_code == 200:
                try:
                    response_data = response.json()
                    await cache_manager.set(cache_key, {
                        'data': response_data,
                        'status': response.status_code,
                        'headers': dict(response.headers)
                    }, ttl=300)  # 5分钟缓存
                except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)

            return JSONResponse(
                content=response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        except httpx.TimeoutException:
            last_error = "请求超时"
            logger.warning(f"请求超时: {target_service}({target_url}) - 尝试 {attempt + 1}")
            service_health.mark_unhealthy(target_service, target_url)

        except Exception as e:
            last_error = str(e)
            logger.warning(f"请求失败: {target_service}({target_url}) - {e} - 尝试 {attempt + 1}")
            service_health.mark_unhealthy(target_service, target_url)

        # 选择下一个URL重试
        healthy_urls = service_health.get_healthy_urls(target_service)
        if healthy_urls:
            target_url = select_url(healthy_urls)
            full_target_url = f"{target_url}/{path}"

    # 所有重试都失败
    if attempt >= target_config.retries:
        service_health.trip_circuit_breaker(target_service)
        raise HTTPException(status_code=502, detail=f'服务不可用: {last_error}')

@app.get('/services')
async def list_services():
    """列出所有可用服务及其状态"""
    services = []
    for name, config in SERVICE_ROUTES.items():
        healthy_urls = service_health.get_healthy_urls(name)
        services.append({
            'name': name,
            'prefix': config.prefix,
            'urls': config.urls,
            'healthy_urls': healthy_urls,
            'circuit_open': service_health.is_circuit_open(name)
        })
    return {'services': services}

@app.delete('/cache')
async def clear_cache():
    """清除所有缓存"""
    if cache_manager.redis_client:
        await cache_manager.redis_client.flushdb()
        return {'message': '缓存已清除'}
    return {'message': 'Redis未连接，无需清除缓存'}

if __name__ == '__main__':
    uvicorn.run(
        'optimized_main:app',
        host='0.0.0.0',
        port=8080,
        workers=4,  # 增加工作进程
        log_level='info',
        access_log=True,
        loop='uvloop'  # 使用更高性能的事件循环
    )