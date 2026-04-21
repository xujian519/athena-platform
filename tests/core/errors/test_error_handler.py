#!/usr/bin/env python3
"""错误处理器单元测试"""

import pytest


class TestErrorType:
    """ErrorType枚举测试"""

    def test_network_errors(self):
        """测试网络错误类型"""
        from core.errors.error_handler import ErrorType
        assert ErrorType.NETWORK_ERROR == "network_error"
        assert ErrorType.TIMEOUT_ERROR == "timeout_error"


class TestAthenaError:
    """AthenaError异常类测试"""

    def test_init_basic(self):
        """测试基本初始化"""
        from core.errors.error_handler import AthenaError
        error = AthenaError("test error")
        assert error.message == "test error"
        assert error.timestamp is not None


# error_handler.py是一个较大的模块(535行)
# 完整测试需要覆盖所有错误类型、重试机制等
