from __future__ import annotations
"""
异步处理模块 - Async Processing Module

提供异步任务执行、数据库异步化、BERT异步化、API异步调用等功能
"""

from core.async_processing.async_engine import (
    AsyncAPIClient,
    AsyncBERTClassifier,
    AsyncDatabase,
    AsyncProcessor,
    # 数据类
    AsyncTask,
    # 核心类
    AsyncTaskQueue,
    # 枚举
    TaskPriority,
    TaskStatus,
    async_task,
    gather_with_concurrency,
    # 便捷函数
    get_async_processor,
    run_in_executor,
)

__all__ = [
    "AsyncAPIClient",
    "AsyncBERTClassifier",
    "AsyncDatabase",
    "AsyncProcessor",
    # 数据类
    "AsyncTask",
    # 核心类
    "AsyncTaskQueue",
    # 枚举
    "TaskPriority",
    "TaskStatus",
    "async_task",
    "gather_with_concurrency",
    # 便捷函数
    "get_async_processor",
    "run_in_executor",
]
