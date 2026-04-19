#!/usr/bin/env python3
"""
测试：自定义异常类
Test: Custom Exception Classes
"""

from __future__ import annotations
import sys
from pathlib import Path

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.perception.exceptions import (
    FileReadError,
    ImageFormatError,
    ModelLoadError,
    NetworkError,
    PerceptionError,
    ProcessingError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)


class TestPerceptionError:
    """测试基础异常类"""

    def test_basic_error(self):
        """测试基础异常"""
        error = PerceptionError("Test error")
        assert str(error) == "Test error"
        assert error.error_code == "PERCEPTION_ERROR"
        assert error.to_dict()["error_type"] == "PerceptionError"

    def test_error_with_details(self):
        """测试带详情的异常"""
        error = PerceptionError(
            message="Test error",
            error_code="CUSTOM_ERROR",
            details={"key": "value"}
        )
        assert error.to_dict()["details"]["key"] == "value"


class TestProcessingError:
    """测试处理异常"""

    def test_processing_error(self):
        """测试处理异常"""
        error = ProcessingError(
            message="Processing failed",
            processor_id="test_processor",
            input_type="text"
        )
        assert error.processor_id == "test_processor"
        assert error.input_type == "text"
        assert error.to_dict()["details"]["processor_id"] == "test_processor"


class TestValidationError:
    """测试验证异常"""

    def test_validation_error(self):
        """测试验证异常"""
        error = ValidationError(
            message="Invalid input",
            field_name="username",
            value="test value"
        )
        assert error.field_name == "username"
        assert "test value" in error.to_dict()["details"]["value"]


class TestResourceErrors:
    """测试资源异常"""

    def test_model_load_error(self):
        """测试模型加载错误"""
        error = ModelLoadError(
            message="Failed to load model",
            model_name="bert-base"
        )
        assert error.model_name == "bert-base"
        assert error.error_code == "MODEL_LOAD_ERROR"

    def test_file_read_error(self):
        """测试文件读取错误"""
        error = FileReadError(
            message="Cannot read file",
            file_path="/path/to/file.txt"
        )
        assert error.file_path == "/path/to/file.txt"
        assert error.error_code == "FILE_READ_ERROR"

    def test_network_error(self):
        """测试网络错误"""
        error = NetworkError(
            message="Request failed",
            url="https://api.example.com",
            status_code=404
        )
        assert error.url == "https://api.example.com"
        assert error.status_code == 404


class TestTimeoutErrors:
    """测试超时异常"""

    def test_timeout_error(self):
        """测试超时错误"""
        error = TimeoutError(
            message="Operation timed out",
            timeout_seconds=30.0
        )
        assert error.timeout_seconds == 30.0
        assert error.error_code == "TIMEOUT_ERROR"


class TestRateLimitError:
    """测试速率限制异常"""

    def test_rate_limit_error(self):
        """测试速率限制错误"""
        error = RateLimitError(
            message="Rate limit exceeded",
            retry_after=60.0
        )
        assert error.retry_after == 60.0
        assert error.error_code == "RATE_LIMIT_ERROR"


class TestFormatErrors:
    """测试格式异常"""

    def test_image_format_error(self):
        """测试图像格式错误"""
        error = ImageFormatError(
            message="Unsupported image format",
            supported_formats=[".jpg", ".png", ".gif"]
        )
        assert ".jpg" in error.to_dict()["details"]["supported_formats"]
        assert error.error_code == "IMAGE_FORMAT_ERROR"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
