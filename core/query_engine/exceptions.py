#!/usr/bin/env python3
from __future__ import annotations
"""
Query Engine异常定义
Query Engine Exceptions

定义查询引擎系统的所有异常类型

作者: Athena平台团队
版本: 1.0.0
"""


class QueryEngineError(Exception):
    """查询引擎基础异常"""

    pass


class AdapterNotFoundError(QueryEngineError):
    """适配器未找到异常"""

    def __init__(self, data_source: str):
        self.data_source = data_source
        super().__init__(f"未找到数据源适配器: {data_source}")


class QueryExecutionError(QueryEngineError):
    """查询执行异常"""

    def __init__(self, query: str, original_error: Exception | None = None):
        self.query = query
        self.original_error = original_error
        message = f"查询执行失败: {query}"
        if original_error:
            message += f" (原因: {original_error})"
        super().__init__(message)


class InvalidQueryError(QueryEngineError):
    """无效查询异常"""

    def __init__(self, query: str, reason: str):
        self.query = query
        self.reason = reason
        super().__init__(f"无效查询: {query} (原因: {reason})")


class ConnectionError(QueryEngineError):
    """连接异常"""

    def __init__(self, data_source: str, original_error: Exception | None = None):
        self.data_source = data_source
        self.original_error = original_error
        message = f"数据源连接失败: {data_source}"
        if original_error:
            message += f" (原因: {original_error})"
        super().__init__(message)


class CacheError(QueryEngineError):
    """缓存异常"""

    pass


class CrossSourceQueryError(QueryEngineError):
    """跨数据源查询异常"""

    pass
