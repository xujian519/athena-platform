"""
API Gateway安全配置
作者: 徐健
创建日期: 2025-12-13
"""

import os
from typing import Dict, List, Optional
from pydantic import BaseSettings, validator


class SecurityConfig(BaseSettings):
    """安全配置类"""

    # JWT配置
    jwt_secret: str = os.getenv("JWT_SECRET", "your-secret-key")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720
    jwt_refresh_expire_days: int = 30

    # API密钥配置
    api_key_header: str = "X-API-Key"
    api_key_query_param: str = "api_key"

    # 密码策略
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    password_max_age_days: int = 90

    # 会话配置
    session_timeout_minutes: int = 30
    max_concurrent_sessions: int = 3

    # 限流配置
    default_rate_limit: int = 100
    default_rate_window: int = 3600
    rate_limit_redis_key: str = "athena:rate_limit"

    # IP白名单/黑名单
    ip_whitelist: List[str] = []
    ip_blacklist: List[str] = []
    trusted_proxy_ips: List[str] = ["127.0.0.1", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

    # 加密配置
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "your-encryption-key-32-chars")
    encryption_algorithm: str = "AES-256-GCM"

    # 审计配置
    audit_log_enabled: bool = True
    audit_log_file: str = "/var/log/athena/audit.log"
    audit_log_retention_days: int = 365

    # WAF配置
    waf_enabled: bool = True
    waf_rules_file: str = "/etc/athena/waf_rules.json"
    waf_mode: str = "detection"  # detection or prevention

    @validator("jwt_secret")
    def validate_jwt_secret(cls, v) -> None:
        if len(v) < 32:
            raise ValueError("JWT secret must be at least 32 characters")
        return v

    @validator("encryption_key")
    def validate_encryption_key(cls, v) -> None:
        if len(v) != 32:
            raise ValueError("Encryption key must be exactly 32 characters")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


# 预定义的API密钥（生产环境应使用数据库存储)
API_KEYS = {
    "admin_key_2024": {
        "name": "Admin API Key",
        "permissions": ["read", "write", "delete", "admin"],
        "rate_limit": {"rate": 1000, "window": 3600},
        "ip_whitelist": [],
        "expires_at": None
    },
    "service_key_yunpat": {
        "name": "YunPat Service Key",
        "permissions": ["read", "write"],
        "rate_limit": {"rate": 500, "window": 3600},
        "ip_whitelist": ["10.0.0.0/8"],
        "expires_at": None
    },
    "readonly_key_demo": {
        "name": "Read-only Demo Key",
        "permissions": ["read"],
        "rate_limit": {"rate": 100, "window": 3600},
        "ip_whitelist": [],
        "expires_at": "2024-12-31"
    }
}

# 端点权限映射
ENDPOINT_PERMISSIONS = {
    # 公开端点
    "/health": [],
    "/api/v1/auth/login": [],
    "/api/v1/auth/register": [],
    "/api/v1/auth/refresh": [],
    "/docs": [],
    "/openapi.json": [],

    # 只读权限
    "/api/v1/search": ["read"],
    "/api/v1/patents/": ["read"],
    "/api/v1/analytics/": ["read"],

    # 写权限
    "/api/v1/patents": ["write"],
    "/api/v1/analysis": ["write"],
    "/api/v1/export": ["write"],

    # 删除权限
    "/api/v1/patents/{id}": ["delete"],
    "/api/v1/users/{id}": ["delete", "admin"],

    # 管理权限
    "/api/v1/admin/": ["admin"],
    "/internal/": ["admin"],
    "/api/v1/audit/": ["admin"]
}

# 敏感操作列表
SENSITIVE_OPERATIONS = [
    "DELETE",
    "/api/v1/admin/",
    "/internal/",
    "password_change",
    "api_key_generate",
    "user_permissions_update"
]

# WAF规则示例
WAF_RULES = {
    "sql_injection": {
        "enabled": True,
        "patterns": [
            r"(?i)(union\s+select|drop\s+table|delete\s+from|insert\s+into)",
            r"(?i)(\b(select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(?i)(\b(or|and)\s+\d+\s*=\s*\d+)",
            r"(?i)(--|#|/\*|\*/)",
            r"(?i)('|(\\')|(;)|(\s+(or|and)\s+.*(=|like)))"
        ],
        "action": "block",
        "severity": "high"
    },
    "xss": {
        "enabled": True,
        "patterns": [
            r"(?i)(<script[^>]*>.*?</script>)",
            r"(?i)(javascript:|vbscript:|data:text/html)",
            r"(?i)(on\w+\s*=)",
            r"(?i)(<iframe[^>]*>|<object[^>]*>|<embed[^>]*>)",
            r"(?i)(eval\s*\(|expression\s*\()"
        ],
        "action": "block",
        "severity": "high"
    },
    "path_traversal": {
        "enabled": True,
        "patterns": [
            r"(\.\./|\.\.\\ )",
            r"(%2e%2e%2f|%2e%2e\\)",
            r"(/etc/passwd|/proc/self/environ)",
            r"(windows/system32|winnt/system32)"
        ],
        "action": "block",
        "severity": "high"
    },
    "command_injection": {
        "enabled": True,
        "patterns": [
            r"(?i)(;|\||&|\$\(|\`|\${)",
            r"(?i)(eval\s*\(|exec\s*\(|system\s*\()",
            r"(?i)(base64_decode|shell_exec|passthru)",
            r"(?i)(wget|curl|nc|netcat)",
            r"(?i)(>|>>|<)"
        ],
        "action": "block",
        "severity": "high"
    },
    "file_inclusion": {
        "enabled": True,
        "patterns": [
            r"(?i)(include\s*\(|require\s*\()",
            r"(?i)(file_get_contents|file_put_contents)",
            r"(?i)(fopen\s*\(|readfile\s*\()",
            r"(?i)(php://|file://|ftp://)"
        ],
        "action": "block",
        "severity": "medium"
    },
    "xxe": {
        "enabled": True,
        "patterns": [
            r"(?i)(<!DOCTYPE[^>]*\[[^>]*>",
            r"(?i)(<!ENTITY[^>]*SYSTEM)",
            r"(?i)(%[^;]*;)",
            r"(?i)(&[a-z_a-Z0-9#]+;)"
        ],
        "action": "block",
        "severity": "high"
    },
    "ssrf": {
        "enabled": True,
        "patterns": [
            r"(?i)(http://|https://|ftp://).*(localhost|127\.0\.0\.1|0\.0\.0\.0)",
            r"(?i)(http://|https://).*(192\.168\.|10\.|172\.1[6-9]\.|172\.2[0-9]\.|172\.3[0-1]\.)",
            r"(?i)(http://|https://).*(169\.254\.|::1)",
            r"(?i)(file://|gopher://|dict://|ldap://)"
        ],
        "action": "block",
        "severity": "high"
    }
}

# 安全事件类型
SECURITY_EVENT_TYPES = {
    "AUTH_SUCCESS": "用户认证成功",
    "AUTH_FAILURE": "用户认证失败",
    "AUTH_LOCKOUT": "账户被锁定",
    "PERMISSION_DENIED": "权限拒绝",
    "RATE_LIMIT_EXCEEDED": "超出限流",
    "INVALID_API_KEY": "无效API密钥",
    "INVALID_SIGNATURE": "无效签名",
    "SUSPICIOUS_REQUEST": "可疑请求",
    "WAF_BLOCK": "WAF拦截",
    "DATA_EXFILTRATION": "数据泄露尝试",
    "PRIVILEGE_ESCALATION": "权限提升尝试"
}

# 加密字段配置
ENCRYPTED_FIELDS = {
    "users": ["password", "email", "phone", "id_card"],
    "api_keys": ["key", "secret"],
    "audit_logs": ["request_body", "response_body"],
    "configuration": ["secret", "password", "key"]
}

# 数据脱敏配置
DATA_MASKING_RULES = {
    "email": {
        "pattern": r"(.{2}).*(@.*)",
        "replacement": r"\1***\2"
    },
    "phone": {
        "pattern": r"(\d{3})\d{4}(\d{4})",
        "replacement": r"\1****\2"
    },
    "id_card": {
        "pattern": r"(\d{6})\d{8}(\d{4})",
        "replacement": r"\1********\2"
    },
    "ip_address": {
        "pattern": r"(\d+\.\d+\.\d+\.)\d+",
        "replacement": r"\1***"
    }
}