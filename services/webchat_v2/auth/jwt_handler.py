#!/usr/bin/env python3
"""
JWT认证处理器
提供JWT token生成和验证功能

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.1
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from pydantic import BaseModel, ValidationError


# Token数据模型
class TokenPayload(BaseModel):
    """Token载荷"""
    user_id: str
    exp: int
    iat: int
    iss: str = "webchat-gateway"


class JWTAuthHandler:
    """JWT认证处理器"""

    # 默认配置
    DEFAULT_ALGORITHM = "HS256"
    DEFAULT_SECRET_KEY = "webchat-v2-secret-key-change-in-production"
    DEFAULT_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = DEFAULT_ALGORITHM,
        token_expire_minutes: int = DEFAULT_TOKEN_EXPIRE_MINUTES
    ):
        """
        初始化JWT处理器

        Args:
            secret_key: 密钥（生产环境必须配置）
            algorithm: 加密算法
            token_expire_minutes: Token过期时间（分钟）
        """
        self.secret_key = secret_key or self.DEFAULT_SECRET_KEY
        self.algorithm = algorithm
        self.token_expire_minutes = token_expire_minutes

        # 警告：使用默认密钥
        if secret_key is None:
            print("⚠️  警告: 使用默认JWT密钥，生产环境请配置GATEWAY_JWT_SECRET")

    def create_token(self, user_id: str, extra_claims: Optional[Dict] = None) -> str:
        """
        创建访问token

        Args:
            user_id: 用户ID
            extra_claims: 额外的声明

        Returns:
            JWT token字符串
        """
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.token_expire_minutes)

        payload = {
            "user_id": user_id,
            "exp": expire,
            "iat": now,
            "iss": "webchat-gateway",
        }

        if extra_claims:
            payload.update(extra_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        return token

    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """
        验证token

        Args:
            token: JWT token字符串

        Returns:
            TokenPayload对象，验证失败返回None
        """
        try:
            # 解码token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={
                    "require": ["user_id", "exp", "iat"],
                    "verify_exp": True,
                }
            )

            # 验证载荷格式
            return TokenPayload(**payload)

        except jwt.ExpiredSignatureError:
            # Token已过期
            return None
        except jwt.InvalidTokenError:
            # Token无效
            return None
        except ValidationError:
            # 载荷格式错误
            return None
        except Exception:
            # 其他错误
            return None

    def refresh_token(self, token: str) -> Optional[str]:
        """
        刷新token

        Args:
            token: 旧token

        Returns:
            新token，失败返回None
        """
        payload = self.verify_token(token)
        if not payload:
            return None

        return self.create_token(payload.user_id)

    def extract_user_id(self, token: str) -> Optional[str]:
        """
        从token中提取user_id（不验证过期时间）

        Args:
            token: JWT token字符串

        Returns:
            user_id，失败返回None
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            return payload.get("user_id")
        except Exception:
            return None


# 全局实例
_jwt_handler: Optional[JWTAuthHandler] = None


def get_jwt_handler() -> JWTAuthHandler:
    """获取JWT处理器单例"""
    global _jwt_handler
    if _jwt_handler is None:
        # 尝试从环境变量读取配置
        import os
        secret_key = os.getenv("GATEWAY_JWT_SECRET")
        expire_minutes = int(os.getenv("GATEWAY_JWT_EXPIRE_MINUTES", "1440"))

        _jwt_handler = JWTAuthHandler(
            secret_key=secret_key,
            token_expire_minutes=expire_minutes
        )
    return _jwt_handler
