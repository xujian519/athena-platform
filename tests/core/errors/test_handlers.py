#!/usr/bin/env python3
"""错误处理器单元测试"""

import pytest


class TestFormatErrorResponse:
    """format_error_response函数测试"""

    def test_basic_response(self):
        """测试基本错误响应"""
        from core.errors.handlers import format_error_response
        response = format_error_response(
            code="TEST_ERROR",
            message="Test error message"
        )
        assert response["success"] is False
        assert response["error"]["code"] == "TEST_ERROR"


# handlers.py是一个FastAPI错误处理模块(428行)
# 涉及HTTP异常、请求验证等
