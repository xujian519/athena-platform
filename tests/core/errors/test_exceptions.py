#!/usr/bin/env python3
"""
统一异常定义单元测试
"""

from datetime import datetime

import pytest
from core.errors.exceptions import (
    AthenaError,
    # 基础异常
    AthenaException,
    AuthenticationException,
    AuthorizationException,
    # 业务异常
    BusinessException,
    # 缓存异常
    CacheException,
    CacheMissException,
    # 配置异常
    ConfigurationException,
    ConnectionException,
    DatabaseException,
    DuplicateResourceException,
    # 文件异常
    FileException,
    FileNotFoundException,
    FileProcessingException,
    FileSizeException,
    FileTypeException,
    FileUploadException,
    FileValidationException,
    InvalidConfigException,
    InvalidFormatException,
    MissingConfigException,
    # 网络异常
    NetworkException,
    OperationNotAllowedException,
    RequestTimeoutException,
    RequiredFieldException,
    ResourceNotFoundException,
    # 存储异常
    StorageException,
    # 验证异常
    ValidationException,
)


class TestAthenaException:
    """基础异常类测试"""

    def test_basic_exception(self):
        """测试基础异常创建"""
        exc = AthenaException("测试错误")
        assert exc.message == "测试错误"
        assert exc.code == "INTERNAL_ERROR"
        assert exc.status_code == 500
        assert isinstance(exc.timestamp, datetime)

    def test_exception_with_custom_code(self):
        """测试自定义错误代码"""
        exc = AthenaException("测试", code="CUSTOM_ERROR", status_code=400)
        assert exc.code == "CUSTOM_ERROR"
        assert exc.status_code == 400

    def test_exception_with_details(self):
        """测试带详情的异常"""
        details = {"key": "value", "number": 123}
        exc = AthenaException("测试", details=details)
        assert exc.details == details

    def test_to_dict(self):
        """测试转换为字典"""
        exc = AthenaException(
            "测试错误",
            code="TEST_ERROR",
            details={"info": "details"}
        )
        result = exc.to_dict()
        assert "error" in result
        assert result["error"]["code"] == "TEST_ERROR"
        assert result["error"]["message"] == "测试错误"
        assert result["error"]["details"]["info"] == "details"
        assert "timestamp" in result["error"]

    def test_str_representation(self):
        """测试字符串表示"""
        exc = AthenaException("测试消息", code="TEST")
        assert str(exc) == "[TEST] 测试消息"

    def test_alias(self):
        """测试别名AthenaError"""
        exc = AthenaError("测试")
        assert isinstance(exc, AthenaException)
        assert exc.message == "测试"


class TestFileExceptions:
    """文件异常测试"""

    def test_file_exception(self):
        """测试文件异常基类"""
        exc = FileException("文件错误", file_path="/test/path.txt")
        assert exc.message == "文件错误"
        assert exc.details["file_path"] == "/test/path.txt"

    def test_file_upload_exception(self):
        """测试文件上传异常"""
        exc = FileUploadException("上传失败", file_path="/test.pdf")
        assert exc.code == "FILE_UPLOAD_ERROR"
        assert exc.status_code == 400
        assert exc.details["file_path"] == "/test.pdf"

    def test_file_processing_exception(self):
        """测试文件处理异常"""
        exc = FileProcessingException(
            "处理失败",
            file_path="/test.doc",
            operation="OCR"
        )
        assert exc.code == "FILE_PROCESSING_ERROR"
        assert exc.details["operation"] == "OCR"

    def test_file_not_found_exception(self):
        """测试文件未找到异常"""
        exc = FileNotFoundException("/missing/file.txt")
        assert exc.code == "FILE_NOT_FOUND"
        assert exc.status_code == 404
        assert "file.txt" in exc.message
        assert exc.details["file_path"] == "/missing/file.txt"

    def test_file_validation_exception(self):
        """测试文件验证异常"""
        errors = ["错误1", "错误2"]
        exc = FileValidationException(
            "验证失败",
            file_path="/test.txt",
            validation_errors=errors
        )
        assert exc.code == "FILE_VALIDATION_ERROR"
        assert exc.details["validation_errors"] == errors

    def test_file_size_exception(self):
        """测试文件大小异常"""
        exc = FileSizeException(
            file_path="/large.txt",
            file_size=15 * 1024 * 1024,  # 15MB
            max_size=10 * 1024 * 1024    # 10MB
        )
        assert exc.code == "FILE_SIZE_EXCEEDED"
        assert exc.status_code == 413
        assert exc.details["file_size"] == 15 * 1024 * 1024
        assert exc.details["max_size"] == 10 * 1024 * 1024
        assert exc.details["size_mb"] == 15.0
        assert exc.details["max_mb"] == 10.0

    def test_file_type_exception(self):
        """测试文件类型异常"""
        exc = FileTypeException(
            file_path="/test.exe",
            file_type=".exe",
            allowed_types=[".pdf", ".doc", ".docx"]
        )
        assert exc.code == "FILE_TYPE_NOT_ALLOWED"
        assert exc.status_code == 415
        assert exc.details["file_type"] == ".exe"
        assert exc.details["allowed_types"] == [".pdf", ".doc", ".docx"]


class TestConfigurationExceptions:
    """配置异常测试"""

    def test_configuration_exception(self):
        """测试配置异常"""
        exc = ConfigurationException("配置错误", config_key="api.key")
        assert exc.code == "CONFIGURATION_ERROR"
        assert exc.details["config_key"] == "api.key"

    def test_missing_config_exception(self):
        """测试缺少配置异常"""
        exc = MissingConfigException("database.url")
        assert exc.code == "MISSING_CONFIG"
        assert "database.url" in exc.message
        assert exc.details["config_key"] == "database.url"

    def test_invalid_config_exception(self):
        """测试无效配置异常"""
        exc = InvalidConfigException(
            config_key="timeout",
            value="invalid",
            reason="必须是数字"
        )
        assert exc.code == "INVALID_CONFIG"
        assert exc.details["config_key"] == "timeout"
        assert exc.details["value"] == "invalid"
        assert exc.details["reason"] == "必须是数字"


class TestCacheExceptions:
    """缓存异常测试"""

    def test_cache_exception(self):
        """测试缓存异常基类"""
        exc = CacheException("缓存错误", cache_key="user:123")
        assert exc.code == "CACHE_ERROR"
        assert exc.details["cache_key"] == "user:123"

    def test_cache_miss_exception(self):
        """测试缓存未命中异常"""
        exc = CacheMissException("session:abc")
        assert exc.code == "CACHE_MISS"
        assert exc.status_code == 404
        assert "session:abc" in exc.message


class TestNetworkExceptions:
    """网络异常测试"""

    def test_network_exception(self):
        """测试网络异常基类"""
        exc = NetworkException("网络错误", url="http://example.com")
        assert exc.code == "NETWORK_ERROR"
        assert exc.status_code == 503
        assert exc.details["url"] == "http://example.com"

    def test_authentication_exception(self):
        """测试认证异常"""
        exc = AuthenticationException("认证失败")
        assert exc.code == "AUTHENTICATION_ERROR"
        assert exc.status_code == 401
        assert exc.message == "认证失败"

    def test_authorization_exception(self):
        """测试授权异常"""
        exc = AuthorizationException(
            "权限不足",
            required_permission="admin:write"
        )
        assert exc.code == "AUTHORIZATION_ERROR"
        assert exc.status_code == 403
        assert exc.details["required_permission"] == "admin:write"

    def test_request_timeout_exception(self):
        """测试请求超时异常"""
        exc = RequestTimeoutException(
            url="http://slow-api.com",
            timeout=30.0
        )
        assert exc.code == "NETWORK_ERROR"
        assert exc.status_code == 504
        assert exc.details["timeout_seconds"] == 30.0
        assert "slow-api.com" in exc.message


class TestStorageExceptions:
    """存储异常测试"""

    def test_storage_exception(self):
        """测试存储异常基类"""
        exc = StorageException("存储错误", storage_type="s3")
        assert exc.code == "STORAGE_ERROR"
        assert exc.details["storage_type"] == "s3"

    def test_database_exception(self):
        """测试数据库异常"""
        query = "SELECT * FROM users WHERE id = ?"
        exc = DatabaseException("查询失败", query=query)
        assert exc.code == "DATABASE_ERROR"
        assert exc.details["query"] == query

    def test_database_exception_query_truncation(self):
        """测试长查询被截断"""
        long_query = "SELECT * FROM table WHERE " + "x=1 AND " * 200
        exc = DatabaseException("查询失败", query=long_query)
        assert len(exc.details["query"]) <= 500

    def test_connection_exception(self):
        """测试连接异常"""
        exc = ConnectionException(
            "无法连接",
            connection_string="postgresql://user:password@localhost/db"
        )
        assert exc.code == "CONNECTION_ERROR"
        assert exc.status_code == 503
        assert "connection" in exc.details
        # 敏感信息应被隐藏
        assert "password" not in str(exc.details["connection"])


class TestValidationExceptions:
    """验证异常测试"""

    def test_validation_exception(self):
        """测试验证异常基类"""
        exc = ValidationException("验证失败", field="email", value="invalid")
        assert exc.code == "VALIDATION_ERROR"
        assert exc.status_code == 400
        assert exc.details["field"] == "email"
        assert exc.details["value"] == "invalid"

    def test_required_field_exception(self):
        """测试必填字段异常"""
        exc = RequiredFieldException("password")
        assert exc.code == "REQUIRED_FIELD"
        assert "password" in exc.message
        assert exc.details["field"] == "password"

    def test_invalid_format_exception(self):
        """测试无效格式异常"""
        exc = InvalidFormatException(
            field="phone",
            value="abc",
            expected_format="1开头的11位数字"
        )
        assert exc.code == "INVALID_FORMAT"
        assert exc.details["field"] == "phone"
        assert exc.details["value"] == "abc"
        assert exc.details["expected_format"] == "1开头的11位数字"


class TestBusinessExceptions:
    """业务异常测试"""

    def test_business_exception(self):
        """测试业务异常基类"""
        exc = BusinessException("业务错误")
        assert exc.code == "BUSINESS_ERROR"
        assert exc.status_code == 400

    def test_resource_not_found_exception(self):
        """测试资源未找到异常"""
        exc = ResourceNotFoundException(
            resource_type="用户",
            resource_id="123"
        )
        assert exc.code == "RESOURCE_NOT_FOUND"
        assert exc.status_code == 404
        assert exc.details["resource_type"] == "用户"
        assert exc.details["resource_id"] == "123"

    def test_duplicate_resource_exception(self):
        """测试重复资源异常"""
        exc = DuplicateResourceException(
            resource_type="邮箱",
            identifier="test@example.com"
        )
        assert exc.code == "DUPLICATE_RESOURCE"
        assert exc.status_code == 409
        assert exc.details["resource_type"] == "邮箱"
        assert exc.details["identifier"] == "test@example.com"

    def test_operation_not_allowed_exception(self):
        """测试操作不允许异常"""
        exc = OperationNotAllowedException(
            message="无法删除",
            operation="delete",
            reason="资源正在使用中"
        )
        assert exc.code == "OPERATION_NOT_ALLOWED"
        assert exc.status_code == 403
        assert exc.details["operation"] == "delete"
        assert exc.details["reason"] == "资源正在使用中"


class TestExceptionInheritance:
    """异常继承关系测试"""

    def test_file_exception_inheritance(self):
        """测试文件异常继承"""
        assert issubclass(FileException, AthenaException)
        assert issubclass(FileUploadException, FileException)
        assert issubclass(FileNotFoundException, FileException)

    def test_all_exceptions_athena_based(self):
        """测试所有异常都继承自AthenaException"""
        exc_classes = [
            FileException, ConfigurationException, CacheException,
            NetworkException, StorageException, ValidationException,
            BusinessException
        ]
        for cls in exc_classes:
            assert issubclass(cls, AthenaException), f"{cls} should inherit from AthenaException"


class TestExceptionUsage:
    """异常使用场景测试"""

    def test_raise_and_catch_athena_exception(self):
        """测试抛出和捕获Athena异常"""
        with pytest.raises(AthenaException) as exc_info:
            raise AthenaException("测试异常")
        assert exc_info.value.message == "测试异常"

    def test_catch_by_base_type(self):
        """测试通过基类捕获子类异常"""
        with pytest.raises(AthenaException) as exc_info:
            raise FileNotFoundException("/missing.txt")
        assert isinstance(exc_info.value, FileException)

    def test_catch_specific_exception(self):
        """测试捕获特定异常"""
        with pytest.raises(FileNotFoundException) as exc_info:
            raise FileNotFoundException("/test.txt")
        assert exc_info.value.code == "FILE_NOT_FOUND"

    def test_exception_details_preservation(self):
        """测试异常详情保留"""
        try:
            raise InvalidConfigException(
                config_key="timeout",
                value="abc",
                reason="必须是数字"
            )
        except InvalidConfigException as e:
            assert e.details["config_key"] == "timeout"
            assert e.details["value"] == "abc"
            assert e.details["reason"] == "必须是数字"
