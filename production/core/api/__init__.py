"""
Athena工作平台 - API模块
API Module for Athena Platform

提供标准化的API基础设施,包括:
- 响应格式标准化
- 错误处理
- OpenAPI/Swagger文档配置
- API请求/响应模型
- 限流控制和AI客户端
"""

from __future__ import annotations
from .api_models import (
    AlertChannelEnum,
    # 告警模型
    AlertSeverityEnum,
    AlertTestRequest,
    AlertTestResponse,
    CapabilitiesListResponse,
    # 能力相关模型
    CapabilityInfo,
    Entity,
    EntityTypeEnum,
    # 通用模型
    ErrorDetail,
    ErrorResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    LanguageStyleEnum,
    OutputFormatEnum,
    Relation,
    RelationDirectionEnum,
    # Phase 2扩展模型
    ResponseDetailEnum,
    SuccessResponse,
    TaskResult,
    TechnicalDepthEnum,
    UserPreferenceRequest,
    UserPreferenceResponse,
    WorkflowRequest,
    WorkflowResponse,
    WorkflowTaskDefinition,
)
from .openapi_config import (
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
    CONTACT_INFO,
    EXAMPLE_REQUESTS,
    EXAMPLE_RESPONSES,
    LICENSE_INFO,
    SERVERS,
    TAGS_METADATA,
    get_openapi_config,
    setup_openapi_docs,
)
from .standards import (
    APIError,
    APIResponse,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PaginatedResponse,
    PermissionError,
    RateLimitError,
    ValidationError,
    error_response,
    paginated_response,
    setup_api_middleware,
    success_response,
)

# 限流控制和AI客户端
try:
    from .rate_limiter import (
        APIRateLimiter,
        BackoffStrategy,
        RateLimitConfig,
        RetryConfig,
        SlidingWindowRateLimiter,
        TokenBucket,
        async_call_with_retry,
        call_with_retry,
        get_default_limiter,
        rate_limited,
    )

    RATE_LIMITER_AVAILABLE = True
except ImportError:
    RATE_LIMITER_AVAILABLE = False

try:
    from .zhipu_client import (
        ZhipuClient,
        ZhipuModel,
        ZhipuRateLimitConfig,
        ZhipuResponse,
        achat,
        chat,
        create_zhipu_client,
        get_default_client,
    )

    ZHIPU_CLIENT_AVAILABLE = True
except ImportError:
    ZHIPU_CLIENT_AVAILABLE = False

__all__ = [
    "API_DESCRIPTION",
    # ========== OpenAPI文档配置 ==========
    "API_TITLE",
    "API_VERSION",
    "CONTACT_INFO",
    "EXAMPLE_REQUESTS",
    "EXAMPLE_RESPONSES",
    "LICENSE_INFO",
    "SERVERS",
    "TAGS_METADATA",
    # 错误类
    "APIError",
    # ========== 标准化响应和错误 ==========
    "APIResponse",
    "AlertChannelEnum",
    # 告警模型
    "AlertSeverityEnum",
    "AlertTestRequest",
    "AlertTestResponse",
    "AuthenticationError",
    "CapabilitiesListResponse",
    # 能力相关模型
    "CapabilityInfo",
    "ConflictError",
    "Entity",
    "EntityTypeEnum",
    # ========== API模型 ==========
    # 通用模型
    "ErrorDetail",
    "ErrorResponse",
    "KnowledgeSearchRequest",
    "KnowledgeSearchResponse",
    "LanguageStyleEnum",
    "NotFoundError",
    "OutputFormatEnum",
    "PaginatedResponse",
    "PermissionError",
    "RateLimitError",
    "Relation",
    "RelationDirectionEnum",
    # Phase 2扩展模型
    "ResponseDetailEnum",
    "SuccessResponse",
    "TaskResult",
    "TechnicalDepthEnum",
    "UserPreferenceRequest",
    "UserPreferenceResponse",
    "ValidationError",
    "WorkflowRequest",
    "WorkflowResponse",
    "WorkflowTaskDefinition",
    "error_response",
    "get_openapi_config",
    "paginated_response",
    # 中间件和工具
    "setup_api_middleware",
    "setup_openapi_docs",
    "success_response",
]

# 添加限流控制和AI客户端到导出列表(如果可用)
if RATE_LIMITER_AVAILABLE:
    __all__.extend(
        [
            "APIRateLimiter",
            "BackoffStrategy",
            "RateLimitConfig",
            "RetryConfig",
            "SlidingWindowRateLimiter",
            "TokenBucket",
            "async_call_with_retry",
            "call_with_retry",
            "get_default_limiter",
            "rate_limited",
        ]
    )

if ZHIPU_CLIENT_AVAILABLE:
    __all__.extend(
        [
            "ZhipuClient",
            "ZhipuModel",
            "ZhipuRateLimitConfig",
            "ZhipuResponse",
            "achat",
            "chat",
            "create_zhipu_client",
            "get_default_client",
        ]
    )
