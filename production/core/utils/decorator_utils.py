#!/usr/bin/env python3
"""
通用装饰器模块
"""
from __future__ import annotations
import functools
import logging
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)

def log_errors(logger_obj: logging.Logger | None | None = None):
    """记录错误的装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log = logger_obj or logger
                log.error(f"{func.__name__}执行失败: {e}", exc_info=True)
                raise
        return wrapper
    return decorator

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"{func.__name__}失败,{delay}秒后重试 ({attempt+1}/{max_attempts})")
                        time.sleep(delay)
                    else:
                        logger.error(f"{func.__name__}重试{max_attempts}次后仍失败")
            raise last_exception
        return wrapper
    return decorator

def timer(func: Callable) -> Callable:
    """计时装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.time() - start
            logger.debug(f"{func.__name__}耗时: {elapsed:.2f}秒")
    return wrapper

__all__ = ['log_errors', 'retry', 'timer']
