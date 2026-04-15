#!/usr/bin/env python3
"""
安全测试
Security Tests for Browser Automation Service

测试认证、授权、JavaScript沙箱等安全功能

作者: 小诺·双鱼公主
版本: 1.0.0
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from api.middleware.auth_middleware import (
    AuthManager,
    TokenData,
    create_auth_response,
    generate_error_id,
    get_auth_manager,
    require_admin,
    verify_any_auth,
    verify_api_key,
    verify_jwt_token,
)
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from core.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
)


class TestGenerateErrorId:
    """测试错误ID生成"""

    def test_generate_error_id_unique(self):
        """测试错误ID唯一性"""
        ids = [generate_error_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_generate_error_id_format(self):
        """测试错误ID格式"""
        error_id = generate_error_id()
        assert error_id.startswith("ERR-")
        assert len(error_id) == 17


class TestAuthManager:
    """测试认证管理器"""

    def test_auth_manager_initialization(self):
        """测试认证管理器初始化"""
        manager = AuthManager()

        assert manager.secret_key is not None
        assert manager.algorithm == "HS256"
        assert manager.access_token_expire_minutes > 0

    @pytest.mark.asyncio
    async def test_create_access_token(self):
        """测试创建访问令牌"""
        manager = AuthManager()

        token = manager.create_access_token(
            data={"sub": "user123", "scopes": ["read", "write"]},
        )

        assert isinstance(token, str)
        assert len(token) > 50  # JWT应该足够长

    @pytest.mark.asyncio
    async def test_create_token_with_expiration(self):
        """测试创建带过期时间的令牌"""
        manager = AuthManager()

        token = manager.create_access_token(
            data={"sub": "user123"},
            expires_delta=timedelta(minutes=30),
        )

        assert isinstance(token, str)

    @pytest.mark.asyncio
    async def test_decode_valid_token(self):
        """测试解码有效令牌"""
        manager = AuthManager()

        # 创建令牌
        token = manager.create_access_token(
            data={"sub": "user123", "scopes": ["read"]},
        )

        # 解码令牌
        token_data = manager.decode_token(token)

        assert token_data.user_id == "user123"
        assert token_data.scopes == ["read"]
        assert token_data.exp is not None

    @pytest.mark.asyncio
    async def test_decode_invalid_token(self):
        """测试解码无效令牌"""
        manager = AuthManager()

        with pytest.raises(InvalidTokenError) as exc_info:
            manager.decode_token("invalid_token")

        assert "无效" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_decode_expired_token(self):
        """测试解码过期令牌"""
        manager = AuthManager()

        # 创建一个已过期的令牌
        token = manager.create_access_token(
            data={"sub": "user123"},
            expires_delta=timedelta(seconds=-1),  # 已过期
        )

        with pytest.raises(TokenExpiredError) as exc_info:
            manager.decode_token(token)

        assert "过期" in str(exc_info.value)

    def test_verify_api_key_valid(self):
        """测试验证有效API Key"""
        manager = AuthManager()

        # 模拟配置的API Key
        with patch("api.middleware.auth_middleware.settings") as mock_settings:
            mock_settings.API_KEY = "test_api_key_123"

            result = manager.verify_api_key("test_api_key_123")
            assert result is True

    def test_verify_api_key_invalid(self):
        """测试验证无效API Key"""
        manager = AuthManager()

        # 模拟配置的API Key
        with patch("api.middleware.auth_middleware.settings") as mock_settings:
            mock_settings.API_KEY = "test_api_key_123"

            result = manager.verify_api_key("wrong_key")
            assert result is False

    def test_verify_api_key_missing(self):
        """测试验证缺失API Key"""
        manager = AuthManager()

        # 模拟未配置API Key
        with patch("api.middleware.auth_middleware.settings") as mock_settings:
            mock_settings.API_KEY = ""

            result = manager.verify_api_key("any_key")
            assert result is False


class TestJWTVerification:
    """测试JWT验证"""

    @pytest.mark.asyncio
    async def test_verify_jwt_token_valid(self):
        """测试验证有效JWT令牌"""
        manager = get_auth_manager()
        token = manager.create_access_token(data={"sub": "user123"})

        credentials = HTTPAuthorizationCredentials(
            scheme="bearer",
            credentials=token,
        )

        # 模拟认证启用
        with patch("api.middleware.auth_middleware.settings") as mock_settings:
            mock_settings.ENABLE_AUTH = True

            token_data = await verify_jwt_token(credentials)

            assert token_data.user_id == "user123"

    @pytest.mark.asyncio
    async def test_verify_jwt_token_missing(self):
        """测试验证缺失JWT令牌"""
        with patch("api.middleware.auth_middleware.settings") as mock_settings:
            mock_settings.ENABLE_AUTH = True

            with pytest.raises(HTTPException) as exc_info:
                await verify_jwt_token(None)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_jwt_token_auth_disabled(self):
        """测试认证禁用时验证JWT"""
        with patch("api.middleware.auth_middleware.settings") as mock_settings:
            mock_settings.ENABLE_AUTH = False

            token_data = await verify_jwt_token(None)

            assert token_data.user_id == "anonymous"


class TestAPIKeyVerification:
    """测试API Key验证"""

    @pytest.mark.asyncio
    async def test_verify_api_key_valid(self):
        """测试验证有效API Key"""
        with patch("api.middleware.auth_middleware.settings") as mock_settings:
            mock_settings.ENABLE_AUTH = False
            mock_settings.API_KEY = "test_key_123"

            result = await verify_api_key("test_key_123")
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_api_key_invalid(self):
        """测试验证无效API Key"""
        with patch("api.middleware.auth_middleware.settings") as mock_settings:
            mock_settings.ENABLE_AUTH = True
            mock_settings.API_KEY = "test_key_123"

            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key("wrong_key")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_api_key_auth_disabled(self):
        """测试认证禁用时验证API Key"""
        with patch("api.middleware.auth_middleware.settings") as mock_settings:
            mock_settings.ENABLE_AUTH = False

            result = await verify_api_key(None)
            assert result is True


class TestAnyAuthVerification:
    """测试任意认证验证"""

    @pytest.mark.asyncio
    async def test_verify_any_auth_with_jwt(self):
        """测试使用JWT认证"""
        manager = get_auth_manager()
        token = manager.create_access_token(data={"sub": "user123"})

        credentials = HTTPAuthorizationCredentials(
            scheme="bearer",
            credentials=token,
        )

        with patch("api.middleware.auth_middleware.settings") as mock_settings:
            mock_settings.ENABLE_AUTH = True

            result = await verify_any_auth(credentials, None)
            assert result.user_id == "user123"

    @pytest.mark.asyncio
    async def test_verify_any_auth_with_api_key(self):
        """测试使用API Key认证"""
        with patch("api.middleware.auth_middleware.settings") as mock_settings:
            mock_settings.ENABLE_AUTH = True
            mock_settings.API_KEY = "test_key_123"

            result = await verify_any_auth(None, "test_key_123")
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_any_auth_auth_disabled(self):
        """测试认证禁用时的任意认证"""
        with patch("api.middleware.auth_middleware.settings") as mock_settings:
            mock_settings.ENABLE_AUTH = False

            result = await verify_any_auth(None, None)
            assert result.user_id == "anonymous"

    @pytest.mark.asyncio
    async def test_verify_any_auth_both_invalid(self):
        """测试两种认证都无效"""
        with patch("api.middleware.auth_middleware.settings") as mock_settings:
            mock_settings.ENABLE_AUTH = True
            mock_settings.API_KEY = "config_key"

            with pytest.raises(HTTPException) as exc_info:
                await verify_any_auth(None, "wrong_key")

            assert exc_info.value.status_code == 401


class TestAdminRequirement:
    """测试管理员权限要求"""

    @pytest.mark.asyncio
    async def test_require_admin_with_admin_scope(self):
        """测试拥有管理员权限"""
        token_data = TokenData(
            user_id="admin",
            exp=None,
            scopes=["admin", "read"],
        )

        result = await require_admin(token_data)
        assert result.user_id == "admin"

    @pytest.mark.asyncio
    async def test_require_admin_with_wildcard(self):
        """测试拥有通配符权限"""
        token_data = TokenData(
            user_id="superuser",
            exp=None,
            scopes=["*"],
        )

        result = await require_admin(token_data)
        assert result.user_id == "superuser"

    @pytest.mark.asyncio
    async def test_require_admin_without_admin_scope(self):
        """测试没有管理员权限"""
        token_data = TokenData(
            user_id="user",
            exp=None,
            scopes=["read"],
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(token_data)

        assert exc_info.value.status_code == 403
        assert "权限" in str(exc_info.value.detail)


class TestAuthResponse:
    """测试认证响应"""

    def test_create_auth_response(self):
        """测试创建认证响应"""
        get_auth_manager()

        response = create_auth_response(
            user_id="user123",
            scopes=["read", "write"],
            expires_in=3600,
        )

        assert "access_token" in response
        assert response["token_type"] == "bearer"
        assert response["user_id"] == "user123"
        assert response["scopes"] == ["read", "write"]
        assert response["expires_in"] == 3600


class TestJavaScriptSandbox:
    """测试JavaScript沙箱"""

    def test_validate_safe_script(self):
        """测试验证安全脚本"""
        from api.routes.browser_routes import validate_javascript_safety

        is_safe, error = validate_javascript_safety("document.title")
        assert is_safe is True
        assert error is None

    def test_validate_dangerous_location(self):
        """测试验证危险location操作"""
        from api.routes.browser_routes import validate_javascript_safety

        is_safe, error = validate_javascript_safety("window.location.href = 'http://evil.com'")
        assert is_safe is False
        assert "window.location" in error

    def test_validate_dangerous_cookie(self):
        """测试验证危险cookie操作"""
        from api.routes.browser_routes import validate_javascript_safety

        is_safe, error = validate_javascript_safety("document.cookie = 'session=123'")
        assert is_safe is False
        assert "cookie" in error

    def test_validate_dangerous_fetch(self):
        """测试验证危险fetch操作"""
        from api.routes.browser_routes import validate_javascript_safety

        is_safe, error = validate_javascript_safety("fetch('http://api.example.com/data')")
        assert is_safe is False
        assert "fetch" in error

    def test_validate_dangerous_eval(self):
        """测试验证危险eval操作"""
        from api.routes.browser_routes import validate_javascript_safety

        is_safe, error = validate_javascript_safety("eval('console.log(1)')")
        assert is_safe is False
        assert "eval" in error

    def test_validate_script_too_long(self):
        """测试验证超长脚本"""
        from api.routes.browser_routes import validate_javascript_safety

        long_script = "document.title" * 1000  # > 10000字符
        is_safe, error = validate_javascript_safety(long_script)

        assert is_safe is False
        assert "长度" in error

    def test_validate_safe_document_access(self):
        """测试验证安全document访问"""
        from api.routes.browser_routes import validate_javascript_safety

        is_safe, error = validate_javascript_safety("document.querySelector('.btn').click()")
        assert is_safe is True

    def test_validate_safe_window_access(self):
        """测试验证安全window访问"""
        from api.routes.browser_routes import validate_javascript_safety

        is_safe, error = validate_javascript_safety("window.innerWidth")
        assert is_safe is True


class TestSecurityHeaders:
    """测试安全头"""

    def test_security_headers_configured(self):
        """测试安全头已配置"""
        from main import create_app

        app = create_app()

        # 检查CORS中间件已添加
        middleware_types = [type(m) for m in app.user_middleware]
        from fastapi.middleware.cors import CORSMiddleware

        assert CORSMiddleware in middleware_types


class TestRateLimiting:
    """测试速率限制"""

    @pytest.mark.asyncio
    async def test_rate_limit_check(self):
        """测试速率限制检查"""
        from core.concurrency import get_concurrency_manager

        manager = get_concurrency_manager()

        # 应该能获取一些许可
        success_count = 0
        for _ in range(10):
            if await manager.check_rate_limit():
                success_count += 1

        assert success_count > 0
        assert success_count <= 10


class TestCSRFProtection:
    """测试CSRF保护"""

    def test_cors_origins_restricted(self):
        """测试CORS来源受限"""
        from config.settings import settings

        origins = settings.allowed_origins_list

        # 应该有一些来源限制
        assert len(origins) > 0

        # 不应该允许所有来源
        assert "*" not in origins


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
