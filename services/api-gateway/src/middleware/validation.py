"""
请求验证中间件

提供全面的请求验证功能，包括参数验证、安全检查等。
"""

import re
from collections.abc import Awaitable, Callable
from re import Pattern
from typing import Any
from urllib.parse import unquote

from fastapi import Request, Response
from pydantic import BaseModel, ValidationError

from .base import Middleware, MiddlewareContext, MiddlewareException


class ValidationMiddleware(Middleware):
    """请求验证中间件

    提供多层验证机制：
    1. 请求体大小限制
    2. SQL 注入检测
    3. XSS 攻击检测
    4. 路径遍历检测
    5. 参数格式验证
    6. Pydantic 模型验证

    配置选项：
    - max_body_size: 最大请求体大小（字节），默认 10MB
    - enable_sql_injection_check: 启用 SQL 注入检测，默认 True
    - enable_xss_check: 启用 XSS 检测，默认 True
    - enable_path_traversal_check: 启用路径遍历检测，默认 True
    - validation_models: 路径到 Pydantic 模型的映射
    - skip_paths: 跳过验证的路径列表
    """

    # SQL 注入特征模式
    SQL_INJECTION_PATTERNS = [
        r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
        r"(\bor\b|\band\b).*?(\=|\s+)(\d+|['\"][^'\"]*['\"])",
        r"(\;|\bexec\b|\bexecute\b|\bunion\b|\bselect\b|\binsert\b|\bupdate\b|\bdelete\b|\bdrop\b)",
        r"(\bxp_\w+)|(\bsp_\w+)|(\bexec\b)",
    ]

    # XSS 攻击特征模式
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<embed[^>]*>",
        r"<object[^>]*>",
        r"fromCharCode",
        r"&#\d+;",
        r"&#x[\da-f]+;",
    ]

    # 路径遍历特征模式
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\./",
        r"%2e%2e%2f",
        r"%2e%2e\\",
        r"\.\.\\",
        r"\.\.\\\\",
    ]

    def __init__(
        self,
        max_body_size: int = 10 * 1024 * 1024,  # 10MB
        enable_sql_injection_check: bool = True,
        enable_xss_check: bool = True,
        enable_path_traversal_check: bool = True,
        validation_models: dict[str, type[BaseModel]] | None = None,
        skip_paths: list[str] | None = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._max_body_size = max_body_size
        self._enable_sql_injection_check = enable_sql_injection_check
        self._enable_xss_check = enable_xss_check
        self._enable_path_traversal_check = enable_path_traversal_check
        self._validation_models = validation_models or {}
        self._skip_paths = set(skip_paths or [])

        # 编译正则表达式
        self._sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self._xss_patterns = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]
        self._path_traversal_patterns = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]

        # 统计信息
        self._stats = {
            "requests_validated": 0,
            "sql_injection_blocked": 0,
            "xss_blocked": 0,
            "path_traversal_blocked": 0,
            "validation_errors": 0,
        }

    async def process(
        self,
        ctx: MiddlewareContext,
        call_next: Callable[[MiddlewareContext], Awaitable[Response]]
    ) -> Response:
        """处理请求验证"""

        request = ctx.request
        path = request.url.path

        # 检查是否跳过验证
        if self._should_skip_validation(path):
            return await call_next(ctx)

        self._stats["requests_validated"] += 1

        # 1. 检查请求体大小
        if not await self._validate_body_size(request):
            raise ValidationException(
                "Request body too large",
                code=413,
                details={"max_size": self._max_body_size}
            )

        # 2. 检查 SQL 注入
        if self._enable_sql_injection_check:
            if await self._check_sql_injection(request):
                self._stats["sql_injection_blocked"] += 1
                raise ValidationException(
                    "Potential SQL injection detected",
                    code=403,
                    details={"threat_type": "sql_injection"}
                )

        # 3. 检查 XSS
        if self._enable_xss_check:
            if await self._check_xss(request):
                self._stats["xss_blocked"] += 1
                raise ValidationException(
                    "Potential XSS attack detected",
                    code=403,
                    details={"threat_type": "xss"}
                )

        # 4. 检查路径遍历
        if self._enable_path_traversal_check:
            if await self._check_path_traversal(request):
                self._stats["path_traversal_blocked"] += 1
                raise ValidationException(
                    "Path traversal attempt detected",
                    code=403,
                    details={"threat_type": "path_traversal"}
                )

        # 5. Pydantic 模型验证
        validation_error = await self._validate_with_model(request)
        if validation_error:
            self._stats["validation_errors"] += 1
            raise ValidationException(
                "Request validation failed",
                code=422,
                details=validation_error
            )

        return await call_next(ctx)

    def _should_skip_validation(self, path: str) -> bool:
        """检查是否跳过验证"""
        for skip_path in self._skip_paths:
            if path.startswith(skip_path):
                return True
        return False

    async def _validate_body_size(self, request: Request) -> bool:
        """验证请求体大小"""
        try:
            # 对于带 Content-Length 的请求
            content_length = request.headers.get("content-length")
            if content_length:
                if int(content_length) > self._max_body_size:
                    return False
            return True
        except (ValueError, TypeError):
            return False

    async def _check_sql_injection(self, request: Request) -> bool:
        """检查 SQL 注入"""
        # 检查查询参数
        for _key, values in request.query_params.items():
            for value in values:
                decoded = unquote(str(value))
                if self._matches_patterns(decoded, self._sql_patterns):
                    return True

        # 检查路径
        path_segments = request.url.path.split("/")
        for segment in path_segments:
            if self._matches_patterns(segment, self._sql_patterns):
                return True

        # 检查请求体（如果是 JSON）
        if "application/json" in request.headers.get("content-type", ""):
            try:
                body = await request.json()
                if self._check_json_for_patterns(body, self._sql_patterns):
                    return True
            except Exception:
                pass

        return False

    async def _check_xss(self, request: Request) -> bool:
        """检查 XSS 攻击"""
        # 检查查询参数
        for _key, values in request.query_params.items():
            for value in values:
                decoded = unquote(str(value))
                if self._matches_patterns(decoded, self._xss_patterns):
                    return True

        # 检查路径
        if self._matches_patterns(request.url.path, self._xss_patterns):
            return True

        # 检查请求体
        if "application/json" in request.headers.get("content-type", ""):
            try:
                body = await request.json()
                if self._check_json_for_patterns(body, self._xss_patterns):
                    return True
            except Exception:
                pass

        return False

    async def _check_path_traversal(self, request: Request) -> bool:
        """检查路径遍历"""
        # 检查路径
        if self._matches_patterns(request.url.path, self._path_traversal_patterns):
            return True

        # 检查查询参数
        for _key, values in request.query_params.items():
            for value in values:
                if self._matches_patterns(str(value), self._path_traversal_patterns):
                    return True

        return False

    def _matches_patterns(self, text: str, patterns: list[Pattern]) -> bool:
        """检查文本是否匹配任一模式"""
        for pattern in patterns:
            if pattern.search(text):
                return True
        return False

    def _check_json_for_patterns(
        self,
        data: Any,
        patterns: list[Pattern]
    ) -> bool:
        """递归检查 JSON 数据是否匹配模式"""
        if isinstance(data, str):
            return self._matches_patterns(data, patterns)
        elif isinstance(data, dict):
            for value in data.values():
                if self._check_json_for_patterns(value, patterns):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self._check_json_for_patterns(item, patterns):
                    return True
        return False

    async def _validate_with_model(self, request: Request) -> dict | None:
        """使用 Pydantic 模型验证"""
        # 查找匹配的验证模型
        model = self._find_validation_model(request.url.path, request.method)
        if not model:
            return None

        try:
            if "application/json" in request.headers.get("content-type", ""):
                body = await request.json()
                model(**body)
            return None
        except ValidationError as e:
            return {
                "field": e.errors()[0]["loc"][-1] if e.errors() else "unknown",
                "message": e.errors()[0]["msg"] if e.errors() else "Validation failed",
                "type": e.errors()[0]["type"] if e.errors() else "unknown"
            }

    def _find_validation_model(self, path: str, method: str) -> type[BaseModel] | None:
        """查找匹配的验证模型"""
        key = f"{method.lower()}:{path}"
        return self._validation_models.get(key)

    def add_validation_model(self, path: str, method: str, model: type[BaseModel]) -> None:
        """添加验证模型

        Args:
            path: 请求路径
            method: HTTP 方法
            model: Pydantic 模型类
        """
        key = f"{method.lower()}:{path}"
        self._validation_models[key] = model

    def remove_validation_model(self, path: str, method: str) -> bool:
        """移除验证模型"""
        key = f"{method.lower()}:{path}"
        return key in self._validation_models and self._validation_models.pop(key) is not None

    def get_stats(self) -> dict:
        """获取验证统计"""
        return self._stats.copy()

    def reset_stats(self) -> None:
        """重置统计"""
        self._stats = {
            "requests_validated": 0,
            "sql_injection_blocked": 0,
            "xss_blocked": 0,
            "path_traversal_blocked": 0,
            "validation_errors": 0,
        }


class ValidationException(MiddlewareException):
    """验证异常"""

    def __init__(self, message: str, code: int = 400, details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message, code)


# 预定义的验证模型
class PatentSearchRequest(BaseModel):
    """专利搜索请求验证模型"""
    query: str
    limit: int = 10
    offset: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "query": "人工智能",
                "limit": 10,
                "offset": 0
            }
        }


class SkillExecutionRequest(BaseModel):
    """技能执行请求验证模型"""
    skill_name: str
    parameters: dict = {}

    class Config:
        json_schema_extra = {
            "example": {
                "skill_name": "patent_search",
                "parameters": {"query": "机器学习"}
            }
        }
