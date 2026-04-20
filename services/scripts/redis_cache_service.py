#!/usr/bin/env python3
"""
Redis缓存服务
为Athena平台提供缓存功能
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'core'))

from cache_manager import cache_manager

app = FastAPI(
    title='Redis缓存服务',
    description='Athena平台缓存管理服务',
    version='1.0.0'
)

class CacheRequest(BaseModel):
    key: str
    value: Any
    ttl: int | None = None

class CacheResponse(BaseModel):
    success: bool
    message: str
    data: Any = None

# 缓存服务状态
cache_status = {
    'service_name': 'redis-cache',
    'version': '1.0.0',
    'status': 'running',
    'start_time': datetime.now().isoformat(),
    'total_operations': 0,
    'cache_hits': 0,
    'cache_misses': 0
}

@app.get('/')
async def root():
    return {
        'service': 'Redis缓存服务',
        'status': 'running',
        'port': 6001,
        'version': '1.0.0',
        'message': '⚡ Redis缓存系统已启动',
        'features': [
            '🚀 高速缓存',
            '📊 智能管理',
            '🔄 自动过期',
            '📈 性能监控'
        ]
    }

@app.get('/health')
async def health():
    return {
        'status': 'healthy',
        'service': 'redis-cache',
        'timestamp': datetime.now().isoformat(),
        'cache_status': cache_status,
        'redis_stats': cache_manager.get_stats()
    }

@app.post('/cache/set')
async def set_cache(request: CacheRequest) -> CacheResponse:
    """设置缓存"""
    try:
        cache_status['total_operations'] += 1
        success = cache_manager.set(request.key, request.value, request.ttl)

        if success:
            return CacheResponse(
                success=True,
                message=f"缓存设置成功: {request.key}",
                data={'key': request.key, 'ttl': request.ttl}
            )
        else:
            return CacheResponse(
                success=False,
                message=f"缓存设置失败: {request.key}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/cache/get/{key}')
async def get_cache(key: str):
    """获取缓存"""
    try:
        cache_status['total_operations'] += 1
        value = cache_manager.get(key)

        if value is not None:
            cache_status['cache_hits'] += 1
            return {
                'success': True,
                'key': key,
                'value': value,
                'cached': True
            }
        else:
            cache_status['cache_misses'] += 1
            return {
                'success': False,
                'key': key,
                'message': '缓存未找到',
                'cached': False
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.delete('/cache/delete/{key}')
async def delete_cache(key: str) -> CacheResponse:
    """删除缓存"""
    try:
        cache_status['total_operations'] += 1
        success = cache_manager.delete(key)

        return CacheResponse(
            success=success,
            message=f"缓存删除: {key}" + ('成功' if success else '失败')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/cache/stats')
async def get_cache_stats():
    """获取缓存统计"""
    try:
        stats = cache_manager.get_stats()
        stats.update(cache_status)

        # 计算命中率
        total_requests = cache_status['cache_hits'] + cache_status['cache_misses']
        hit_rate = (cache_status['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        stats['service_hit_rate'] = f"{hit_rate:.1f}%"

        return {
            'success': True,
            'stats': stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/cache/clear')
async def clear_cache(pattern: str = '*') -> CacheResponse:
    """清理缓存"""
    try:
        deleted_count = cache_manager.clear(pattern)
        return CacheResponse(
            success=True,
            message="缓存清理完成",
            data={'deleted_count': deleted_count, 'pattern': pattern}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/service/cache/{service_name}')
async def cache_service_data(service_name: str, data: dict, ttl: int = 300):
    """缓存服务数据"""
    try:
        success = cache_manager.set_service_cache(service_name, data, ttl)
        return {
            'success': success,
            'service': service_name,
            'ttl': ttl,
            'message': '服务数据缓存' + ('成功' if success else '失败')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/service/cache/{service_name}')
async def get_service_cache(service_name: str):
    """获取服务缓存数据"""
    try:
        data = cache_manager.get_service_cache(service_name)
        return {
            'success': True,
            'service': service_name,
            'data': data,
            'cached': bool(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

if __name__ == '__main__':
    logger.info('⚡ 启动Redis缓存服务...')
    logger.info("📊 端口: 6001")
    logger.info("🔗 Redis: 127.0.0.1:6379")
    uvicorn.run(app, host='127.0.0.1', port=6001)  # 内网通信，通过Gateway访问
