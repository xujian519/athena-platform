"""
认证服务适配器
将认证服务适配到统一的API网关，提供统一的身份认证和授权功能
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import aiohttp
import bcrypt
import jwt
from patent_search_adapter import AdapterConfig, BaseAdapter

logger = logging.getLogger(__name__)


@dataclass
class User:
    """用户数据模型"""

    id: str
    username: str
    email: str
    password_hash: str
    roles: list[str] = None
    profile: dict = None
    created_at: str = None
    updated_at: str = None
    last_login: str = None
    is_active: bool = True

    def __post_init__(self):
        if self.roles is None:
            self.roles = ["user"]
        if self.profile is None:
            self.profile = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()


@dataclass
class TokenData:
    """令牌数据模型"""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400  # 24小时
    scope: str = "read write"


class JWTService:
    """JWT服务"""

    def __init__(self, secret: str, algorithm: str = "HS256", expires_in: int = 86400):
        self.secret = secret
        self.algorithm = algorithm
        self.expires_in = expires_in

    def generate_tokens(self, user: User) -> TokenData:
        """生成访问令牌和刷新令牌"""
        now = datetime.utcnow()

        # 访问令牌负载
        access_payload = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "roles": user.roles,
            "iat": now,
            "exp": now + timedelta(seconds=self.expires_in),
            "type": "access",
        }

        # 刷新令牌负载
        refresh_payload = {
            "sub": user.id,
            "iat": now,
            "exp": now + timedelta(days=30),  # 30天有效期
            "type": "refresh",
        }

        access_token = jwt.encode(access_payload, self.secret, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret, algorithm=self.algorithm)

        return TokenData(
            access_token=access_token, refresh_token=refresh_token, expires_in=self.expires_in
        )

    def verify_token(self, token: str, token_type: str = "access") -> dict | None:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])

            if payload.get("type") != token_type:
                return None

            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as error:
            logger.warning(f"Invalid token: {error}")
            return None

    def refresh_access_token(self, refresh_token: str) -> TokenData | None:
        """使用刷新令牌生成新的访问令牌"""
        payload = self.verify_token(refresh_token, "refresh")

        if not payload:
            return None

        # 创建临时用户对象用于生成新令牌
        temp_user = User(id=payload["sub"], username="", email="", password_hash="")

        return self.generate_tokens(temp_user)


class AuthService:
    """认证服务"""

    def __init__(self, service_url: str, bcrypt_rounds: int = 12):
        self.service_url = service_url
        self.bcrypt_rounds = bcrypt_rounds
        self.session = None

    async def initialize(self):
        """初始化服务"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """清理资源"""
        if self.session:
            await self.session.close()

    async def check_connection(self) -> bool:
        """检查连接状态"""
        try:
            if not self.session:
                await self.initialize()

            async with self.session.get(f"{self.service_url}/health") as response:
                return response.status == 200
        except Exception as error:
            logger.error(f"Auth service connection check failed: {error}")
            return False

    def hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception:
            return False

    async def create_user(self, user_data: dict) -> User | None:
        """创建用户"""
        try:
            # 密码哈希处理
            password_hash = self.hash_password(user_data["password"])

            create_request = {
                "username": user_data["username"],
                "email": user_data["email"],
                "password_hash": password_hash,
                "roles": user_data.get("roles", ["user"]),
                "profile": user_data.get("profile", {}),
                "is_active": True,
            }

            async with self.session.post(
                f"{self.service_url}/users", json=create_request
            ) as response:
                if response.status == 201:
                    response_data = await response.json()
                    return User(**response_data)
                else:
                    logger.error(f"Failed to create user: {response.status}")
                    return None

        except Exception as error:
            logger.error(f"Create user error: {error}")
            return None

    async def authenticate_user(self, username: str, password: str) -> User | None:
        """用户认证"""
        try:
            async with self.session.get(f"{self.service_url}/users/{username}") as response:
                if response.status == 200:
                    user_data = await response.json()
                    user = User(**user_data)

                    if self.verify_password(password, user.password_hash):
                        # 更新最后登录时间
                        await self.update_last_login(user.id)
                        return user

            return None

        except Exception as error:
            logger.error(f"Authentication error: {error}")
            return None

    async def get_user_by_id(self, user_id: str) -> User | None:
        """根据ID获取用户"""
        try:
            async with self.session.get(f"{self.service_url}/users/id/{user_id}") as response:
                if response.status == 200:
                    user_data = await response.json()
                    return User(**user_data)
                return None

        except Exception as error:
            logger.error(f"Get user by ID error: {error}")
            return None

    async def update_last_login(self, user_id: str):
        """更新最后登录时间"""
        try:
            update_data = {"last_login": datetime.now().isoformat()}
            async with self.session.patch(
                f"{self.service_url}/users/{user_id}", json=update_data
            ) as response:
                if response.status != 200:
                    logger.warning(f"Failed to update last login for user {user_id}")

        except Exception as error:
            logger.error(f"Update last login error: {error}")


class AuthenticationAdapter(BaseAdapter):
    """认证服务适配器"""

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self.service_name = "authentication-service"
        self.api_prefix = "/api/v1/auth"

        # 初始化JWT和认证服务
        jwt_config = config.circuit_breaker or {}  # 复用配置字段存储JWT设置
        self.jwt_service = JWTService(
            secret=jwt_config.get("secret", "default-secret-change-in-production"),
            algorithm=jwt_config.get("algorithm", "HS256"),
            expires_in=jwt_config.get("expires_in", 86400),
        )

        auth_config = config.circuit_breaker or {}  # 复用配置字段存储认证设置
        self.auth_service = AuthService(
            service_url=config.service_url, bcrypt_rounds=auth_config.get("bcrypt_rounds", 12)
        )

    async def initialize(self):
        """初始化适配器"""
        await super().initialize()
        await self.auth_service.initialize()

    async def cleanup(self):
        """清理资源"""
        await super().cleanup()
        await self.auth_service.cleanup()

    async def ping_service(self):
        """ping服务检查"""
        is_connected = await self.auth_service.check_connection()
        if not is_connected:
            raise Exception("Authentication service connection failed")
        return {"status": "healthy", "connection": "ok"}

    async def transform_request(self, request: dict) -> dict:
        """
        将统一请求格式转换为认证服务格式
        """
        try:
            auth_type = request.get("type", "login")

            if auth_type == "login":
                return {
                    "username": request.get("username"),
                    "password": request.get("password"),
                    "remember_me": request.get("rememberMe", False),
                }

            elif auth_type == "register":
                return {
                    "username": request.get("username"),
                    "email": request.get("email"),
                    "password": request.get("password"),
                    "roles": request.get("roles", ["user"]),
                    "profile": request.get("profile", {}),
                }

            elif auth_type == "refresh":
                return {"refresh_token": request.get("refreshToken")}

            else:
                raise ValueError(f"Unsupported auth request type: {auth_type}")

        except Exception as error:
            self.logger.error(f"Request transformation failed: {error}")
            raise

    async def transform_response(self, response_data: Any, auth_type: str = "login") -> dict:
        """
        将认证服务响应转换为统一格式
        """
        try:
            if isinstance(response_data, str):
                response_data = json.loads(response_data)

            if not response_data.get("success", True):
                return {
                    "success": False,
                    "error": {
                        "code": response_data.get("error_code", "AUTH_ERROR"),
                        "message": response_data.get("message", "Authentication failed"),
                    },
                    "timestamp": datetime.now().isoformat(),
                }

            # 处理成功响应
            if auth_type in ["login", "register"]:
                user_data = response_data.get("user", {})
                user = User(
                    id=user_data.get("id", ""),
                    username=user_data.get("username", ""),
                    email=user_data.get("email", ""),
                    password_hash="",
                    roles=user_data.get("roles", ["user"]),
                    profile=user_data.get("profile", {}),
                    is_active=user_data.get("is_active", True),
                )

                # 生成令牌
                tokens = self.jwt_service.generate_tokens(user)

                return {
                    "success": True,
                    "data": {
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "roles": user.roles,
                            "profile": user.profile,
                        },
                        "tokens": {
                            "accessToken": tokens.access_token,
                            "refreshToken": tokens.refresh_token,
                            "expiresIn": tokens.expires_in,
                        },
                    },
                    "timestamp": datetime.now().isoformat(),
                }

            elif auth_type == "refresh":
                token_data = response_data.get("tokens", {})
                return {
                    "success": True,
                    "data": {"tokens": token_data},
                    "timestamp": datetime.now().isoformat(),
                }

            else:
                return {
                    "success": True,
                    "data": response_data,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as error:
            self.logger.error(f"Response transformation failed: {error}")
            raise

    async def login(self, request: dict) -> dict:
        """
        用户登录
        """
        try:
            # 使用本地认证服务进行验证
            username = request.get("username")
            password = request.get("password")

            if not username or not password:
                return await self._handle_error(Exception("Username and password are required"))

            user = await self.auth_service.authenticate_user(username, password)

            if not user:
                return {
                    "success": False,
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid username or password",
                    },
                    "timestamp": datetime.now().isoformat(),
                }

            # 生成令牌
            tokens = self.jwt_service.generate_tokens(user)

            return {
                "success": True,
                "data": {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "roles": user.roles,
                        "profile": user.profile,
                    },
                    "tokens": {
                        "accessToken": tokens.access_token,
                        "refreshToken": tokens.refresh_token,
                        "expiresIn": tokens.expires_in,
                    },
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as error:
            return await self._handle_error(error)

    async def register(self, request: dict) -> dict:
        """
        用户注册
        """
        try:
            # 使用本地认证服务创建用户
            user_data = {
                "username": request.get("username"),
                "email": request.get("email"),
                "password": request.get("password"),
                "roles": request.get("roles", ["user"]),
                "profile": request.get("profile", {}),
            }

            user = await self.auth_service.create_user(user_data)

            if not user:
                return {
                    "success": False,
                    "error": {
                        "code": "REGISTRATION_FAILED",
                        "message": "Failed to create user account",
                    },
                    "timestamp": datetime.now().isoformat(),
                }

            # 生成令牌
            tokens = self.jwt_service.generate_tokens(user)

            return {
                "success": True,
                "data": {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "roles": user.roles,
                        "profile": user.profile,
                    },
                    "tokens": {
                        "accessToken": tokens.access_token,
                        "refreshToken": tokens.refresh_token,
                        "expiresIn": tokens.expires_in,
                    },
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as error:
            return await self._handle_error(error)

    async def refresh_token(self, request: dict) -> dict:
        """
        刷新令牌
        """
        try:
            refresh_token = request.get("refreshToken")

            if not refresh_token:
                return await self._handle_error(Exception("Refresh token is required"))

            # 验证刷新令牌
            token_data = self.jwt_service.refresh_access_token(refresh_token)

            if not token_data:
                return {
                    "success": False,
                    "error": {
                        "code": "INVALID_REFRESH_TOKEN",
                        "message": "Invalid or expired refresh token",
                    },
                    "timestamp": datetime.now().isoformat(),
                }

            return {
                "success": True,
                "data": {
                    "tokens": {
                        "accessToken": token_data.access_token,
                        "refreshToken": token_data.refresh_token,
                        "expiresIn": token_data.expires_in,
                    }
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as error:
            return await self._handle_error(error)

    async def verify_token(self, token: str) -> dict:
        """
        验证令牌
        """
        try:
            payload = self.jwt_service.verify_token(token, "access")

            if not payload:
                return {
                    "success": False,
                    "error": {"code": "INVALID_TOKEN", "message": "Invalid or expired token"},
                    "timestamp": datetime.now().isoformat(),
                }

            # 获取用户信息
            user = await self.auth_service.get_user_by_id(payload["sub"])

            if not user or not user.is_active:
                return {
                    "success": False,
                    "error": {"code": "USER_NOT_FOUND", "message": "User not found or inactive"},
                    "timestamp": datetime.now().isoformat(),
                }

            return {
                "success": True,
                "data": {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "roles": user.roles,
                        "profile": user.profile,
                    },
                    "tokenPayload": payload,
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as error:
            return await self._handle_error(error)

    async def logout(self, request: dict) -> dict:
        """
        用户登出
        """
        try:
            # 在实际实现中，这里可以将令牌加入黑名单
            # 目前简单返回成功响应

            return {
                "success": True,
                "data": {"message": "Logged out successfully"},
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as error:
            return await self._handle_error(error)

    async def get_profile(self, request: dict) -> dict:
        """
        获取用户档案
        """
        try:
            user_id = request.get("userId")

            if not user_id:
                return await self._handle_error(Exception("User ID is required"))

            user = await self.auth_service.get_user_by_id(user_id)

            if not user:
                return {
                    "success": False,
                    "error": {"code": "USER_NOT_FOUND", "message": "User not found"},
                    "timestamp": datetime.now().isoformat(),
                }

            return {
                "success": True,
                "data": {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "roles": user.roles,
                        "profile": user.profile,
                        "createdAt": user.created_at,
                        "lastLogin": user.last_login,
                    }
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as error:
            return await self._handle_error(error)


# 注册适配器
from patent_search_adapter import AdapterFactory

AdapterFactory.register("authentication", AuthenticationAdapter)


# 使用示例
async def test_authentication_adapter():
    """测试认证适配器"""
    config = {
        "authentication": {
            "service_url": "http://localhost:8052",
            "health_threshold": 3000,
            "timeout": 10000,
            "retry_attempts": 1,
            "debug_mode": True,
            "circuit_breaker": {  # 复用此字段存储JWT和认证配置
                "secret": "test-secret-key-change-in-production",
                "algorithm": "HS256",
                "expires_in": 86400,
                "bcrypt_rounds": 12,
            },
        }
    }

    from patent_search_adapter import AdapterManager

    manager = AdapterManager(config)
    await manager.initialize()

    try:
        adapter = await manager.get_adapter("authentication")

        # 健康检查
        health = await adapter.health_check()
        print(f"Health status: {health}")

        # 测试登录
        login_request = {
            "type": "login",
            "username": "testuser",
            "password": "testpass123",
            "rememberMe": True,
        }

        result = await adapter.login(login_request)
        print(f"Login result: {json.dumps(result, indent=2, ensure_ascii=False)}")

        # 如果登录成功，测试令牌验证
        if result.get("success") and "tokens" in result.get("data", {}):
            access_token = result["data"]["tokens"]["accessToken"]
            verify_result = await adapter.verify_token({"token": access_token})
            print(
                f"Token verification result: {json.dumps(verify_result, indent=2, ensure_ascii=False)}"
            )

    finally:
        await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(test_authentication_adapter())
