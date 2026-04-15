#!/usr/bin/env python3
"""
认证中间件
Authentication Middleware for Browser Automation Service

提供JWT和API Key认证功能

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import uuid
from datetime import datetime, timedelta
from typing import Any

from config.settings import logger, settings
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from core.exceptions import AuthenticationError

# API Key认证
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# JWT Bearer认证
bearer_security = HTTPBearer(auto_error=False)


class TokenData:
    """Token数据模型"""

    def __init__(
        self,
        user_id: str | None = None,
        exp: datetime | None = None,
        scopes: list[str] | None = None,
    ):
        self.user_id = user_id
        self.exp = exp
        self.scopes = scopes or []


class AuthManager:
    """
    认证管理器

    提供JWT生成、验证和API Key验证功能
    """

    def __init__(self):
        """初始化认证管理器"""
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

        # 验证密钥强度
        if self.secret_key == "athena_browser_secret_key" or len(self.secret_key) < 32:
            if settings.ENVIRONMENT == "production":
                logger.warning("🔒 生产环境使用弱密钥，建议立即更换")

    def create_access_token(
        self,
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        创建访问令牌

        Args:
            data: 要编码的数据
            expires_delta: 过期时间增量

        Returns:
            str: JWT令牌
        """
        try:
            import jwt

            to_encode = data.copy()

            # 设置过期时间
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

            to_encode.update({
                "exp": expire,
                "iat": datetime.utcnow(),
                "jti": str(uuid.uuid4()),  # JWT ID for tracking
            })

            # 编码JWT
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

            logger.debug(f"✅ 创建访问令牌: {to_encode.get('sub', 'unknown')}")
            return encoded_jwt

        except ImportError:
            logger.warning("⚠️ PyJWT未安装，JWT功能不可用")
            raise AuthenticationError("JWT功能未启用，请安装pyjwt") from None
        except Exception as e:
            logger.error(f"❌ 创建令牌失败: {e}")
            raise AuthenticationError(f"创建令牌失败: {e}") from e

    def decode_token(self, token: str) -> TokenData:
        """
        解码并验证令牌

        Args:
            token: JWT令牌

        Returns:
            TokenData: 令牌数据

        Raises:
            AuthenticationError: 令牌无效或过期
        """
        try:
            import jwt

            # 解码JWT
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )

            # 提取数据
            user_id = payload.get("sub")
            exp = payload.get("exp")
            scopes = payload.get("scopes", [])

            # 检查过期时间
            if exp:
                exp_datetime = datetime.fromtimestamp(exp)
                if exp_datetime < datetime.utcnow():
                    raise AuthenticationError("令牌已过期")

            return TokenData(
                user_id=user_id,
                exp=exp_datetime if exp else None,
                scopes=scopes,
            )

        except jwt.ExpiredSignatureError:
            raise AuthenticationError("令牌已过期") from None
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"无效的令牌: {e}") from e
        except Exception as e:
            logger.error(f"❌ 解码令牌失败: {e}")
            raise AuthenticationError(f"解码令牌失败: {e}") from e

    def verify_api_key(self, api_key: str) -> bool:
        """
        验证API Key

        Args:
            api_key: API密钥

        Returns:
            bool: 是否有效
        """
        if not api_key:
            return False

        # 检查配置的API Key
        configured_key = getattr(settings, "API_KEY", "")
        if not configured_key:
            return False

        # 常量时间比较，防止时序攻击
        import hmac

        return hmac.compare_digest(api_key.encode(), configured_key.encode())


# 全局认证管理器实例
_auth_manager: AuthManager | None = None


def get_auth_manager() -> AuthManager:
    """获取全局认证管理器实例"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


# =============================================================================
# FastAPI依赖函数
# =============================================================================


async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_security),
) -> TokenData:
    """
    验证JWT令牌的依赖函数

    Args:
        credentials: Bearer认证凭据

    Returns:
        TokenData: 令牌数据

    Raises:
        HTTPException: 认证失败
    """
    if not settings.ENABLE_AUTH:
        # 认证未启用，返回默认token
        return TokenData(user_id="anonymous", scopes=["*"])

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        auth_manager = get_auth_manager()
        token_data = auth_manager.decode_token(credentials.credentials)
        return token_data

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def verify_api_key(
    api_key: str | None = Depends(api_key_header),
) -> bool:
    """
    验证API Key的依赖函数

    Args:
        api_key: API密钥

    Returns:
        bool: 是否有效

    Raises:
        HTTPException: 认证失败
    """
    if not settings.ENABLE_AUTH:
        return True

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供API Key",
        )

    auth_manager = get_auth_manager()
    if not auth_manager.verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API Key",
        )

    return True


async def verify_any_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_security),
    api_key: str | None = Depends(api_key_header),
) -> TokenData | bool:
    """
    验证任一种认证方式（JWT或API Key）

    Args:
        credentials: Bearer认证凭据
        api_key: API密钥

    Returns:
        TokenData | bool: 认证结果

    Raises:
        HTTPException: 认证失败
    """
    if not settings.ENABLE_AUTH:
        return TokenData(user_id="anonymous", scopes=["*"])

    # 尝试JWT认证
    if credentials:
        try:
            return await verify_jwt_token(credentials)
        except HTTPException:
            pass

    # 尝试API Key认证
    if api_key:
        try:
            await verify_api_key(api_key)
            return True
        except HTTPException:
            pass

    # 都失败了
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证失败，请提供有效的JWT令牌或API Key",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_admin(token_data: TokenData = Depends(verify_jwt_token)) -> TokenData:
    """
    要求管理员权限的依赖函数

    Args:
        token_data: 令牌数据

    Returns:
        TokenData: 令牌数据

    Raises:
        HTTPException: 权限不足
    """
    if "admin" not in token_data.scopes and "*" not in token_data.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )

    return token_data


# =============================================================================
# 辅助函数
# =============================================================================


def generate_error_id() -> str:
    """生成错误追踪ID"""
    return f"ERR-{uuid.uuid4().hex[:12].upper()}"


def create_auth_response(
    user_id: str,
    scopes: list[str] | None = None,
    expires_in: int | None = None,
) -> dict[str, Any]:
    """
    创建认证响应

    Args:
        user_id: 用户ID
        scopes: 权限范围
        expires_in: 过期时间（秒）

    Returns:
        dict: 认证响应
    """
    auth_manager = get_auth_manager()

    # 创建令牌
    expires_delta = timedelta(seconds=expires_in) if expires_in else None
    access_token = auth_manager.create_access_token(
        data={"sub": user_id, "scopes": scopes or []},
        expires_delta=expires_delta,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_id,
        "scopes": scopes or [],
        "expires_in": expires_in or auth_manager.access_token_expire_minutes * 60,
    }


# 导出
__all__ = [
    "AuthManager",
    "TokenData",
    "get_auth_manager",
    "verify_jwt_token",
    "verify_api_key",
    "verify_any_auth",
    "require_admin",
    "generate_error_id",
    "create_auth_response",
]
