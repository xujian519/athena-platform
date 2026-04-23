#!/usr/bin/env python3
"""
感知模块异常类测试
Tests for Perception Module Exception Classes
"""


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.ai.perception.exceptions import (
    AudioFormatError,
    CacheError,
    ConcurrencyError,
    ConfigurationError,
    FileReadError,
    FormatError,
    ImageFormatError,
    InitializationError,
    MemoryError,
    ModelLoadError,
    NetworkError,
    PerceptionError,
    ProcessingError,
    RateLimitError,
    ResourceError,
    TimeoutError,
    ValidationError,
    VideoFormatError,
)


class TestPerceptionError:
    """测试基础异常类"""

    def test_basic_exception(self):
        """测试基本异常"""
        error = PerceptionError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "PERCEPTION_ERROR"
        assert error.details == {}

    def test_exception_with_error_code(self):
        """测试带错误码的异常"""
        error = PerceptionError(
            "Test error",
            error_code="CUSTOM_ERROR"
        )
        assert error.error_code == "CUSTOM_ERROR"

    def test_exception_with_details(self):
        """测试带详情的异常"""
        details = {"key1": "value1", "key2": "value2"}
        error = PerceptionError(
            "Test error",
            details=details
        )
        assert error.details == details

    def test_to_dict(self):
        """测试转换为字典"""
        error = PerceptionError(
            "Test error",
            error_code="TEST_CODE",
            details={"info": "test"}
        )
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "PerceptionError"
        assert error_dict["error_code"] == "TEST_CODE"
        assert error_dict["message"] == "Test error"
        assert error_dict["details"]["info"] == "test"


class TestProcessingError:
    """测试处理错误"""

    def test_basic_processing_error(self):
        """测试基本处理错误"""
        error = ProcessingError("Processing failed")
        assert error.message == "Processing failed"
        assert error.error_code == "PROCESSING_ERROR"

    def test_processing_error_with_processor_id(self):
        """测试带处理器ID的处理错误"""
        error = ProcessingError(
            "Processing failed",
            processor_id="text_processor_1"
        )
        assert error.processor_id == "text_processor_1"
        assert error.details["processor_id"] == "text_processor_1"

    def test_processing_error_with_input_type(self):
        """测试带输入类型的处理错误"""
        error = ProcessingError(
            "Processing failed",
            input_type="text"
        )
        assert error.input_type == "text"
        assert error.details["input_type"] == "text"

    def test_processing_error_full(self):
        """测试完整的处理错误"""
        error = ProcessingError(
            "Processing failed",
            processor_id="text_processor_1",
            input_type="text"
        )
        assert error.processor_id == "text_processor_1"
        assert error.input_type == "text"
        assert len(error.details) == 2


class TestValidationError:
    """测试验证错误"""

    def test_basic_validation_error(self):
        """测试基本验证错误"""
        error = ValidationError("Invalid input")
        assert error.message == "Invalid input"
        assert error.error_code == "VALIDATION_ERROR"

    def test_validation_error_with_field_name(self):
        """测试带字段名的验证错误"""
        error = ValidationError(
            "Invalid input",
            field_name="email"
        )
        assert error.field_name == "email"
        assert error.details["field_name"] == "email"

    def test_validation_error_with_value(self):
        """测试带值的验证错误"""
        error = ValidationError(
            "Invalid input",
            value="test@example.com"
        )
        assert error.details["value"] == "test@example.com"

    def test_validation_error_value_truncation(self):
        """测试值截断"""
        long_value = "a" * 200
        error = ValidationError(
            "Invalid input",
            value=long_value
        )
        # 值应该被截断到100个字符
        assert len(error.details["value"]) <= 100


class TestInitializationError:
    """测试初始化错误"""

    def test_basic_initialization_error(self):
        """测试基本初始化错误"""
        error = InitializationError("Failed to initialize")
        assert error.error_code == "INITIALIZATION_ERROR"

    def test_initialization_error_with_component(self):
        """测试带组件名的初始化错误"""
        error = InitializationError(
            "Failed to initialize",
            component="TextProcessor"
        )
        assert error.details["component"] == "TextProcessor"


class TestConfigurationError:
    """测试配置错误"""

    def test_basic_configuration_error(self):
        """测试基本配置错误"""
        error = ConfigurationError("Invalid configuration")
        assert error.error_code == "CONFIGURATION_ERROR"

    def test_configuration_error_with_key(self):
        """测试带配置键的配置错误"""
        error = ConfigurationError(
            "Invalid configuration",
            config_key="max_length"
        )
        assert error.details["config_key"] == "max_length"

    def test_configuration_error_with_value(self):
        """测试带配置值的配置错误"""
        error = ConfigurationError(
            "Invalid configuration",
            config_value="invalid_value"
        )
        assert error.details["config_value"] == "invalid_value"

    def test_configuration_error_value_truncation(self):
        """测试值截断"""
        long_value = "a" * 200
        error = ConfigurationError(
            "Invalid configuration",
            config_value=long_value
        )
        assert len(error.details["config_value"]) <= 100


class TestResourceError:
    """测试资源错误"""

    def test_basic_resource_error(self):
        """测试基本资源错误"""
        error = ResourceError("Resource unavailable")
        assert error.error_code == "RESOURCE_ERROR"

    def test_resource_error_with_type(self):
        """测试带资源类型的资源错误"""
        error = ResourceError(
            "Resource unavailable",
            resource_type="file"
        )
        assert error.details["resource_type"] == "file"

    def test_resource_error_with_path(self):
        """测试带路径的资源错误"""
        error = ResourceError(
            "Resource unavailable",
            resource_path="/path/to/resource"
        )
        assert error.details["resource_path"] == "/path/to/resource"


class TestModelLoadError:
    """测试模型加载错误"""

    def test_basic_model_load_error(self):
        """测试基本模型加载错误"""
        error = ModelLoadError("Failed to load model")
        assert error.error_code == "MODEL_LOAD_ERROR"
        assert error.details["resource_type"] == "model"

    def test_model_load_error_with_model_name(self):
        """测试带模型名的模型加载错误"""
        error = ModelLoadError(
            "Failed to load model",
            model_name="bert-base-chinese"
        )
        assert error.model_name == "bert-base-chinese"
        assert error.details["resource_path"] == "bert-base-chinese"


class TestFileReadError:
    """测试文件读取错误"""

    def test_basic_file_read_error(self):
        """测试基本文件读取错误"""
        error = FileReadError("Failed to read file")
        assert error.error_code == "FILE_READ_ERROR"
        assert error.details["resource_type"] == "file"

    def test_file_read_error_with_path(self):
        """测试带路径的文件读取错误"""
        error = FileReadError(
            "Failed to read file",
            file_path="/path/to/file.txt"
        )
        assert error.file_path == "/path/to/file.txt"
        assert error.details["resource_path"] == "/path/to/file.txt"


class TestNetworkError:
    """测试网络错误"""

    def test_basic_network_error(self):
        """测试基本网络错误"""
        error = NetworkError("Network request failed")
        assert error.error_code == "NETWORK_ERROR"

    def test_network_error_with_url(self):
        """测试带URL的网络错误"""
        error = NetworkError(
            "Network request failed",
            url="https://api.example.com"
        )
        assert error.url == "https://api.example.com"
        assert error.details["url"] == "https://api.example.com"

    def test_network_error_with_status_code(self):
        """测试带状态码的网络错误"""
        error = NetworkError(
            "Network request failed",
            status_code=404
        )
        assert error.status_code == 404
        assert error.details["status_code"] == 404

    def test_network_error_full(self):
        """测试完整的网络错误"""
        error = NetworkError(
            "Network request failed",
            url="https://api.example.com",
            status_code=500
        )
        assert error.url == "https://api.example.com"
        assert error.status_code == 500
        assert len(error.details) == 2


class TestTimeoutError:
    """测试超时错误"""

    def test_basic_timeout_error(self):
        """测试基本超时错误"""
        error = TimeoutError("Operation timed out")
        assert error.error_code == "TIMEOUT_ERROR"

    def test_timeout_error_with_seconds(self):
        """测试带超时秒数的超时错误"""
        error = TimeoutError(
            "Operation timed out",
            timeout_seconds=30.0
        )
        assert error.timeout_seconds == 30.0
        assert error.details["timeout_seconds"] == 30.0


class TestRateLimitError:
    """测试速率限制错误"""

    def test_basic_rate_limit_error(self):
        """测试基本速率限制错误"""
        error = RateLimitError("Rate limit exceeded")
        assert error.error_code == "RATE_LIMIT_ERROR"

    def test_rate_limit_error_with_retry_after(self):
        """测试带重试时间的速率限制错误"""
        error = RateLimitError(
            "Rate limit exceeded",
            retry_after=60.0
        )
        assert error.retry_after == 60.0
        assert error.details["retry_after"] == 60.0


class TestMemoryError:
    """测试内存错误"""

    def test_basic_memory_error(self):
        """测试基本内存错误"""
        error = MemoryError("Out of memory")
        assert error.error_code == "MEMORY_ERROR"

    def test_memory_error_with_required_mb(self):
        """测试带所需MB数的内存错误"""
        error = MemoryError(
            "Out of memory",
            required_mb=1024
        )
        assert error.details["required_mb"] == 1024

    def test_memory_error_with_available_mb(self):
        """测试带可用MB数的内存错误"""
        error = MemoryError(
            "Out of memory",
            available_mb=512
        )
        assert error.details["available_mb"] == 512

    def test_memory_error_full(self):
        """测试完整的内存错误"""
        error = MemoryError(
            "Out of memory",
            required_mb=1024,
            available_mb=512
        )
        assert error.details["required_mb"] == 1024
        assert error.details["available_mb"] == 512


class TestConcurrencyError:
    """测试并发错误"""

    def test_basic_concurrency_error(self):
        """测试基本并发错误"""
        error = ConcurrencyError("Concurrency limit exceeded")
        assert error.error_code == "CONCURRENCY_ERROR"

    def test_concurrency_error_with_max_concurrent(self):
        """测试带最大并发数的并发错误"""
        error = ConcurrencyError(
            "Concurrency limit exceeded",
            max_concurrent=10
        )
        assert error.details["max_concurrent"] == 10


class TestCacheError:
    """测试缓存错误"""

    def test_basic_cache_error(self):
        """测试基本缓存错误"""
        error = CacheError("Cache operation failed")
        assert error.error_code == "CACHE_ERROR"

    def test_cache_error_with_key(self):
        """测试带缓存键的缓存错误"""
        error = CacheError(
            "Cache operation failed",
            cache_key="user:123:data"
        )
        assert error.details["cache_key"] == "user:123:data"

    def test_cache_error_with_operation(self):
        """测试带操作的缓存错误"""
        error = CacheError(
            "Cache operation failed",
            operation="set"
        )
        assert error.details["operation"] == "set"


class TestFormatError:
    """测试格式错误"""

    def test_basic_format_error(self):
        """测试基本格式错误"""
        error = FormatError("Invalid format")
        assert error.error_code == "FORMAT_ERROR"

    def test_format_error_with_expected_format(self):
        """测试带期望格式的格式错误"""
        error = FormatError(
            "Invalid format",
            expected_format="JSON"
        )
        assert error.details["expected_format"] == "JSON"

    def test_format_error_with_actual_format(self):
        """测试带实际格式的格式错误"""
        error = FormatError(
            "Invalid format",
            actual_format="XML"
        )
        assert error.details["actual_format"] == "XML"


class TestImageFormatError:
    """测试图像格式错误"""

    def test_basic_image_format_error(self):
        """测试基本图像格式错误"""
        error = ImageFormatError("Invalid image format")
        assert error.error_code == "IMAGE_FORMAT_ERROR"

    def test_image_format_error_with_supported_formats(self):
        """测试带支持格式的图像格式错误"""
        error = ImageFormatError(
            "Invalid image format",
            supported_formats=["jpg", "png", "gif"]
        )
        assert "jpg" in error.details["supported_formats"]
        assert error.details["supported_formats"] == "jpg, png, gif"


class TestAudioFormatError:
    """测试音频格式错误"""

    def test_basic_audio_format_error(self):
        """测试基本音频格式错误"""
        error = AudioFormatError("Invalid audio format")
        assert error.error_code == "AUDIO_FORMAT_ERROR"

    def test_audio_format_error_with_supported_formats(self):
        """测试带支持格式的音频格式错误"""
        error = AudioFormatError(
            "Invalid audio format",
            supported_formats=["mp3", "wav", "flac"]
        )
        assert "mp3" in error.details["supported_formats"]
        assert error.details["supported_formats"] == "mp3, wav, flac"


class TestVideoFormatError:
    """测试视频格式错误"""

    def test_basic_video_format_error(self):
        """测试基本视频格式错误"""
        error = VideoFormatError("Invalid video format")
        assert error.error_code == "VIDEO_FORMAT_ERROR"

    def test_video_format_error_with_supported_formats(self):
        """测试带支持格式的视频格式错误"""
        error = VideoFormatError(
            "Invalid video format",
            supported_formats=["mp4", "avi", "mkv"]
        )
        assert "mp4" in error.details["supported_formats"]
        assert error.details["supported_formats"] == "mp4, avi, mkv"


class TestExceptionHierarchy:
    """测试异常继承关系"""

    def test_all_exceptions_inherit_from_perception_error(self):
        """测试所有异常都继承自PerceptionError"""
        exception_classes = [
            ProcessingError,
            ValidationError,
            InitializationError,
            ConfigurationError,
            ResourceError,
            ModelLoadError,
            FileReadError,
            NetworkError,
            TimeoutError,
            RateLimitError,
            MemoryError,
            ConcurrencyError,
            CacheError,
            FormatError,
            ImageFormatError,
            AudioFormatError,
            VideoFormatError,
        ]

        for exception_class in exception_classes:
            # 检查是否是PerceptionError的子类
            assert issubclass(exception_class, PerceptionError)
            # 创建实例验证
            error = exception_class("Test message")
            assert isinstance(error, PerceptionError)

    def test_specific_errors_inherit_from_base_errors(self):
        """测试特定错误继承自基础错误"""
        # ModelLoadError应该继承自ResourceError
        assert issubclass(ModelLoadError, ResourceError)

        # FileReadError应该继承自ResourceError
        assert issubclass(FileReadError, ResourceError)

        # ImageFormatError应该继承自FormatError
        assert issubclass(ImageFormatError, FormatError)

        # AudioFormatError应该继承自FormatError
        assert issubclass(AudioFormatError, FormatError)

        # VideoFormatError应该继承自FormatError
        assert issubclass(VideoFormatError, FormatError)


class TestExceptionChaining:
    """测试异常链"""

    def test_exception_from_other_exception(self):
        """测试从其他异常创建"""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise ProcessingError("Processing failed") from e
        except ProcessingError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)

    def test_exception_context(self):
        """测试异常上下文"""
        try:
            try:
                raise ValueError("Original error")
            except ValueError:
                raise ProcessingError("Processing failed") from None
        except ProcessingError as e:
            # 应该有异常上下文
            assert e.__context__ is not None
