#!/usr/bin/env python3
"""
API认证和安全模块
API Authentication and Security Module for Athena Platform

提供API Key认证、请求验证、安全检查等功能

作者: 小诺AI团队
创建时间: 2025-01-09
"""

import logging
import os
import re
import secrets
from datetime import datetime

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel, Field

# 配置日志
logger = logging.getLogger(__name__)

# API Key配置
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEY_QUERY = APIKeyQuery(name="api_key", auto_error=False)

# 环境配置
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "true").lower() == "true"

# 预定义的API Keys (生产环境应从数据库或密钥管理服务获取)
VALID_API_KEYS = {
    # 开发环境测试密钥
    os.getenv("API_KEY_DEV", "dev-test-key-123456"): {
        "name": "开发测试",
        "environment": "development",
        "rate_limit": 1000,
        "permissions": ["read", "write"],
        "created_at": "2025-01-09",
        "expires_at": None,
    },
    # 生产环境密钥 (从环境变量读取)
    os.getenv("API_KEY_PROD", "change-me-in-production"): {
        "name": "生产环境",
        "environment": "production",
        "rate_limit": 100,
        "permissions": ["read"],
        "created_at": "2025-01-09",
        "expires_at": None,
    },
}


class APIKeyInfo(BaseModel):
    """API Key信息"""

    key: str = Field(..., description="API密钥")
    name: str = Field(..., description="密钥名称")
    environment: str = Field(..., description="环境")
    rate_limit: int = Field(..., description="速率限制")
    permissions: list[str] = Field(..., description="权限列表")


class SecurityConfig:
    """安全配置"""

    # 输入验证规则
    MAX_QUERY_LENGTH = 500
    MAX_LIMIT = 100
    MIN_LIMIT = 1

    # 允许的字符 (防止注入攻击)
    ALLOWED_CHARS = re.compile(
        r"^[\u4e00-\u9fa5a-zA-Z0-9\s\.,;:!?()《》[]、。,;:!?()\-\'\"\n\r]+$"
    )

    # 危险关键词检测
    DANGEROUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # XSS
        r"javascript:",  # JavaScript注入
        r"on\w+\s*=",  # 事件处理器注入
        r"(union|select|insert|update|delete|drop|alter)\s+",  # SQL注入 (简单检测)
    ]

    # IP白名单 (生产环境)
    IP_WHITELIST = os.getenv("IP_WHITELIST", "").split(",") if os.getenv("IP_WHITELIST") else []

    # CORS配置
    if ENVIRONMENT == "production":
        ALLOWED_ORIGINS_CONFIG = os.getenv("ALLOWED_ORIGINS", "").split(",")
        if not ALLOWED_ORIGINS_CONFIG:
            ALLOWED_ORIGINS_CONFIG = []  # 生产环境必须明确配置
    else:
        ALLOWED_ORIGINS_CONFIG = [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://192.168.1.100:3000",  # 具体IP而非通配符
        ]


# 模块级变量供外部导入
ALLOWED_ORIGINS = SecurityConfig.ALLOWED_ORIGINS_CONFIG


def validate_query_input(text: str) -> tuple[bool, str | None]:
    """
    验证查询输入安全性

    Args:
        text: 输入文本

    Returns:
        (是否有效, 错误消息)
    """
    # 长度检查
    if len(text) > SecurityConfig.MAX_QUERY_LENGTH:
        return False, f"查询长度不能超过{SecurityConfig.MAX_QUERY_LENGTH}字符"

    if len(text.strip()) == 0:
        return False, "查询不能为空"

    # 字符白名单检查 (宽松版,允许中文)
    if not SecurityConfig.ALLOWED_CHARS.match(text):
        return False, "查询包含非法字符"

    # 危险模式检测
    for pattern in SecurityConfig.DANGEROUS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False, "查询包含潜在危险内容"

    return True, None


def validate_limit(limit: int) -> tuple[bool, str | None]:
    """验证limit参数"""
    if limit < SecurityConfig.MIN_LIMIT:
        return False, f"limit不能小于{SecurityConfig.MIN_LIMIT}"

    if limit > SecurityConfig.MAX_LIMIT:
        return False, f"limit不能大于{SecurityConfig.MAX_LIMIT}"

    return True, None


async def verify_api_key(
    header_key: str = Security(API_KEY_HEADER),
    query_key: str = Security(API_KEY_QUERY),
) -> APIKeyInfo:
    """
    验证API Key

    Args:
        header_key: Header中的API Key
        query_key: Query参数中的API Key

    Returns:
        APIKeyInfo: API Key信息

    Raises:
        HTTPException: 认证失败
    """
    # 开发环境可以跳过认证
    if ENVIRONMENT == "development" and not ENABLE_AUTH:
        return APIKeyInfo(
            key="dev-bypass",
            name="开发环境绕过",
            environment="development",
            rate_limit=10000,
            permissions=["read", "write"],
        )

    # 优先使用Header中的Key
    api_key = header_key or query_key

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key缺失。请在请求头中添加 X-API-Key 或在查询参数中添加 api_key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # 验证Key
    key_info = VALID_API_KEYS.get(api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # 检查环境匹配
    if key_info["environment"] != ENVIRONMENT and key_info["environment"] != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"此API Key仅适用于 {key_info['environment']} 环境",
        )

    # 检查过期时间
    if key_info.get("expires_at"):
        try:
            expires_at = datetime.fromisoformat(key_info["expires_at"])
            if datetime.now() > expires_at:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API Key已过期")
        except ValueError as e:
            # 过期时间格式错误,记录警告但继续验证
            # 这样可以避免因格式问题导致整个验证失败
            logger.warning(f"API Key过期时间格式错误: {e}, Key: {api_key[:8]}")
        except Exception as e:
            # 其他意外错误,记录并拒绝访问以确保安全
            logger.error(f"验证API Key过期时间时发生错误: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="验证API Key时发生错误"
            )

    return APIKeyInfo(
        key=api_key[:8] + "...",  # 只返回前8位
        name=key_info["name"],
        environment=key_info["environment"],
        rate_limit=key_info["rate_limit"],
        permissions=key_info["permissions"],
    )


def sanitize_error_message(error: Exception) -> str:
    """
    脱敏错误消息,避免泄露内部信息

    Args:
        error: 异常对象

    Returns:
        脱敏后的错误消息
    """
    error_str = str(error)

    # 生产环境隐藏详细信息
    if ENVIRONMENT == "production":
        # 返回通用错误消息
        return "处理请求时发生错误,请稍后重试"

    # 开发环境可以显示更多细节
    # 但仍然隐藏敏感路径信息
    sensitive_patterns = [
        r"/Users/[^/]+/",  # 用户目录
        r'password["\']?\s*[:=]["\']?[^"\'\s]+',  # 密码
        r'api_key["\']?\s*[:=]["\']?[^"\'\s]+',  # API Key
    ]

    for pattern in sensitive_patterns:
        error_str = re.sub(pattern, "[REDACTED]", error_str, flags=re.IGNORECASE)

    return error_str


def check_ip_whitelist(client_ip: str) -> tuple[bool, str | None]:
    """
    检查IP是否在白名单中

    Args:
        client_ip: 客户端IP

    Returns:
        (是否允许, 错误消息)
    """
    # 动态读取环境变量以支持测试
    ip_whitelist_str = os.getenv("IP_WHITELIST", "")
    ip_whitelist = ip_whitelist_str.split(",") if ip_whitelist_str else []

    if not ip_whitelist:
        return True, None  # 未配置白名单,允许所有

    if client_ip in ip_whitelist:
        return True, None

    return False, f"IP {client_ip} 不在白名单中"


def generate_api_key(name: str, environment: str = "production") -> tuple[str, str]:
    """
    生成新的API Key

    Args:
        name: 密钥名称
        environment: 环境

    Returns:
        (api_key, key_id)
    """
    # 生成随机密钥 (32字节 = 64个十六进制字符)
    api_key = secrets.token_hex(32)

    # 生成密钥ID (前8位)
    key_id = api_key[:8]

    # 存储密钥信息 (生产环境应存储到数据库)
    VALID_API_KEYS[api_key] = {
        "name": name,
        "environment": environment,
        "rate_limit": 100 if environment == "production" else 1000,
        "permissions": ["read", "write"] if environment == "development" else ["read"],
        "created_at": datetime.now().isoformat(),
        "expires_at": None,
    }

    return api_key, key_id


# 导出
__all__ = [
    "ALLOWED_ORIGINS",
    "ENABLE_AUTH",
    "ENVIRONMENT",
    "APIKeyInfo",
    "SecurityConfig",
    "check_ip_whitelist",
    "generate_api_key",
    "sanitize_error_message",
    "validate_limit",
    "validate_query_input",
    "verify_api_key",
]
