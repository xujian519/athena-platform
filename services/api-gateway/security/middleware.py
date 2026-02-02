"""
API Gateway安全中间件
作者: 徐健
创建日期: 2025-12-13
"""

import time
import hashlib
import hmac
import secrets
from typing import Dict, Optional, Callable, Any
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import redis
import jwt
from datetime import datetime, timedelta
import ipaddress
import re
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """API限流中间件"""

    def __init__(
        self,
        app,
        redis_client: redis.Redis,
        default_rate: int = 100,
        default_window: int = 3600
    ):
        super().__init__(app)
        self.redis = redis_client
        self.default_rate = default_rate
        self.default_window = default_window

        # 配置不同端点的限流规则
        self.rate_limits = {
            "/api/v1/search": {"rate": 30, "window": 60},
            "/api/v1/analyze": {"rate": 10, "window": 60},
            "/api/v1/auth/login": {"rate": 5, "window": 300},
            "/api/v1/auth/register": {"rate": 3, "window": 3600},
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取客户端标识
        client_id = self._get_client_id(request)

        # 获取限流规则
        path = request.url.path
        rate_config = self.rate_limits.get(
            path,
            {"rate": self.default_rate, "window": self.default_window}
        )

        # 检查限流
        key = f"rate_limit:{path}:{client_id}"
        if not self._check_rate_limit(key, rate_config):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

        return await call_next(request)

    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用用户ID
        if hasattr(request.state, 'user_id'):
            return f"user:{request.state.user_id}"

        # 使用IP地址
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host

        return f"ip:{ip}"

    def _check_rate_limit(self, key: str, config: Dict[str, int]) -> bool:
        """检查限流"""
        current_time = int(time.time())
        window_start = current_time - config["window"]

        # 使用Redis滑动窗口算法
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.expire(key, config["window"])

        results = pipe.execute()
        request_count = results[1]

        return request_count <= config["rate"]


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API密钥验证中间件"""

    def __init__(
        self,
        app,
        required_paths: list = None,
        exempt_paths: list = None
    ):
        super().__init__(app)
        self.required_paths = required_paths or ["/api/v1/", "/internal/"]
        self.exempt_paths = exempt_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否需要验证
        if not self._requires_auth(request.url.path):
            return await call_next(request)

        # 验证API密钥
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            api_key = request.query_params.get("api_key")

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required"
            )

        if not self._validate_api_key(api_key, request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key"
            )

        return await call_next(request)

    def _requires_auth(self, path: str) -> bool:
        """检查路径是否需要认证"""
        # 检查豁免路径
        for exempt in self.exempt_paths:
            if path.startswith(exempt):
                return False

        # 检查需要认证的路径
        for required in self.required_paths:
            if path.startswith(required):
                return True

        return False

    def _validate_api_key(self, api_key: str, request: Request) -> bool:
        """验证API密钥"""
        try:
            # 从环境变量获取有效密钥列表
            valid_keys = os.getenv("VALID_API_KEYS", "").split(",")

            # 验证密钥
            if api_key not in valid_keys:
                return False

            # 检查密钥权限
            key_permissions = self._get_key_permissions(api_key)
            if not self._check_permissions(key_permissions, request):
                return False

            # 记录API使用情况
            self._log_api_usage(api_key, request)

            return True

        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return False

    def _get_key_permissions(self, api_key: str) -> Dict[str, Any]:
        """获取API密钥权限"""
        # 这里应该从数据库或配置获取权限信息
        # 示例实现
        key_permissions = {
            "admin_key_123": {
                "permissions": ["read", "write", "delete"],
                "rate_limit": {"rate": 1000, "window": 3600},
                "ip_whitelist": []  # 空表示不限制IP
            },
            "readonly_key_456": {
                "permissions": ["read"],
                "rate_limit": {"rate": 100, "window": 3600},
                "ip_whitelist": ["192.168.1.0/24"]
            }
        }
        return key_permissions.get(api_key, {})

    def _check_permissions(self, permissions: Dict[str, Any], request: Request) -> bool:
        """检查权限"""
        method = request.method
        path = request.url.path

        # 检查IP白名单
        if permissions.get("ip_whitelist"):
            client_ip = request.client.host
            allowed = False
            for ip_range in permissions["ip_whitelist"]:
                if ipaddress.ip_address(client_ip) in ipaddress.ip_network(ip_range):
                    allowed = True
                    break
            if not allowed:
                return False

        # 检查方法权限
        if method == "GET" and "read" not in permissions.get("permissions", []):
            return False
        if method in ["POST", "PUT", "PATCH"] and "write" not in permissions.get("permissions", []):
            return False
        if method == "DELETE" and "delete" not in permissions.get("permissions", []):
            return False

        # 检查路径权限
        if path.startswith("/admin/") and "admin" not in permissions.get("permissions", []):
            return False

        return True

    def _log_api_usage(self, api_key: str, request: Request) -> Any:
        """记录API使用情况"""
        usage_data = {
            "api_key": api_key[:8] + "***",  # 只显示前8位
            "method": request.method,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"API usage: {usage_data}")


class RequestSigningMiddleware(BaseHTTPMiddleware):
    """请求签名验证中间件"""

    def __init__(self, app, required_paths: list = None):
        super().__init__(app)
        self.required_paths = required_paths or [
            "/api/v1/analyze",
            "/api/v1/export",
            "/internal/"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self._requires_signing(request.url.path):
            return await call_next(request)

        # 获取签名信息
        signature = request.headers.get("X-Signature")
        timestamp = request.headers.get("X-Timestamp")
        api_key = request.headers.get("X-API-Key")

        if not all([signature, timestamp, api_key]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing signature information"
            )

        # 验证时间戳（防止重放攻击）
        if not self._validate_timestamp(timestamp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid timestamp"
            )

        # 获取请求体
        body = await request.body()

        # 验证签名
        if not self._validate_signature(body, signature, timestamp, api_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid signature"
            )

        return await call_next(request)

    def _requires_signing(self, path: str) -> bool:
        """检查路径是否需要签名"""
        return any(path.startswith(p) for p in self.required_paths)

    def _validate_timestamp(self, timestamp: str) -> bool:
        """验证时间戳"""
        try:
            ts = int(timestamp)
            current_ts = int(time.time())

            # 时间戳必须在5分钟内
            return abs(current_ts - ts) <= 300
        except ValueError:
            return False

    def _validate_signature(
        self,
        body: bytes,
        signature: str,
        timestamp: str,
        api_key: str
    ) -> bool:
        """验证签名"""
        try:
            # 获取密钥
            secret_key = self._get_secret_key(api_key)
            if not secret_key:
                return False

            # 构建待签名字符串
            payload = body.decode('utf-8', errors='ignore') + timestamp

            # 计算期望的签名
            expected_signature = hmac.new(
                secret_key.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()

            # 安全比较签名
            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Signature validation error: {e}")
            return False

    def _get_secret_key(self, api_key: str) -> str | None:
        """获取API密钥对应的密钥"""
        # 这里应该从安全的存储中获取
        # 示例实现
        secret_keys = {
            "admin_key_123": os.getenv("ADMIN_SECRET_KEY"),
            "readonly_key_456": os.getenv("READONLY_SECRET_KEY")
        }
        return secret_keys.get(api_key)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; include_sub_domains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=()"
        )

        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """输入验证中间件"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 验证查询参数
        self._validate_query_params(request)

        # 验证请求头
        self._validate_headers(request)

        # 对于POST/PUT请求，验证请求体
        if request.method in ["POST", "PUT", "PATCH"]:
            await self._validate_body(request)

        return await call_next(request)

    def _validate_query_params(self, request: Request) -> Any:
        """验证查询参数"""
        for key, value in request.query_params.items():
            # 检查SQL注入
            if self._contains_sql_injection(value):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input detected"
                )

            # 检查XSS
            if self._contains_xss(value):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input detected"
                )

    def _validate_headers(self, request: Request) -> Any:
        """验证请求头"""
        for key, value in request.headers.items():
            # 检查恶意头
            if key.lower().startswith("x-forwarded-"):
                continue  # 跳过常见的代理头

            if self._contains_malicious_content(value):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid header detected"
                )

    async def _validate_body(self, request: Request):
        """验证请求体"""
        content_type = request.headers.get("content-type", "")

        if "application/json" in content_type:
            try:
                body = await request.json()
                self._validate_json_body(body)
            except Exception as e:
                logger.error(f"JSON validation error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON"
                )

    def _validate_json_body(self, data: Any) -> Any:
        """验证JSON数据"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    if self._contains_sql_injection(value) or self._contains_xss(value):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid input in field: {key}"
                        )
                elif isinstance(value, (dict, list)):
                    self._validate_json_body(value)

    def _contains_sql_injection(self, value: str) -> bool:
        """检测SQL注入"""
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b_or\b.+=.+|\b_and\b.+=.+)",
            r"(\b_where\b.+\b_or\b)",
            r"(\b_where\b.+\b_and\b)",
            r"(\'\s*OR\s*\')",
            r"(\"\s*OR\s*\")"
        ]

        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    def _contains_xss(self, value: str) -> bool:
        """检测XSS"""
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
            r"vbscript:",
            r"data:text/html"
        ]

        for pattern in xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    def _contains_malicious_content(self, value: str) -> bool:
        """检测恶意内容"""
        malicious_patterns = [
            r"<\?php",
            r"<%.*%>",
            r"eval\s*\(",
            r"base64_decode",
            r"system\s*\(",
            r"exec\s*\(",
            r"shell_exec",
            r"passthru"
        ]

        for pattern in malicious_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False


class CORSMiddleware(BaseHTTPMiddleware):
    """CORS中间件"""

    def __init__(
        self,
        app,
        allow_origins: list = None,
        allow_methods: list = None,
        allow_headers: list = None,
        max_age: int = 86400
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or ["http://localhost:3000"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.max_age = max_age

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 处理预检请求
        if request.method == "OPTIONS":
            response = Response()
        else:
            response = await call_next(request)

        # 添加CORS头
        origin = request.headers.get("origin")
        if origin in self.allow_origins or "*" in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin or "*"

        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        response.headers["Access-Control-Max-Age"] = str(self.max_age)
        response.headers["Access-Control-Allow-Credentials"] = "true"

        return response