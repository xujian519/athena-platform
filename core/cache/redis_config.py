#!/usr/bin/env python3
"""
Redis配置辅助模块
提供统一的Redis连接配置
"""
import os
from typing import Optional

def get_redis_config() -> dict:
    """
    获取Redis连接配置
    
    Returns:
        dict: Redis连接配置
    """
    return {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", 6379)),
        "db": int(os.getenv("REDIS_DB", 0)),
        "password": os.getenv("REDIS_PASSWORD", "redis123"),
        "decode_responses": True,
        "socket_connect_timeout": 5,
        "socket_timeout": 5,
        "retry_on_timeout": True,
    }


def get_redis_password() -> str:
    """
    获取Redis密码
    
    Returns:
        str: Redis密码
    """
    return os.getenv("REDIS_PASSWORD", "redis123")


# 便捷函数
def create_redis_client(redis_module=None, **kwargs):
    """
    创建Redis客户端（使用默认配置）
    
    Args:
        redis_module: redis模块（如果为None，自动导入）
        **kwargs: 额外的连接参数（会覆盖默认配置）
    
    Returns:
        Redis客户端实例
    """
    if redis_module is None:
        try:
            import redis
            redis_module = redis
        except ImportError:
            raise ImportError("redis包未安装，请运行: pip install redis")
    
    # 获取默认配置
    config = get_redis_config()
    
    # 合并额外参数
    config.update(kwargs)
    
    # 创建客户端
    return redis_module.Redis(**config)
