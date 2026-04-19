#!/usr/bin/env python3
"""
Athena API Gateway 安全认证和授权中间件
提供JWT令牌认证、API密钥管理和权限控制功能
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import bcrypt
import jwt
from fastapi import HTTPException, Request

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 数据模型 ====================


@dataclass
class User:
    """用户模型"""

    user_id: str
    username: str
    email: str
    roles: list[str]
    permissions: set[str]
    created_at: datetime
    last_login: datetime | None = None
    is_active: bool = True


@dataclass
class APIKey:
    """API密钥模型"""

    key_id: str
    user_id: str
    key_name: str
    permissions: set[str]
    created_at: datetime
    expires_at: datetime | None = None
    is_active: bool = True
    usage_count: int = 0


@dataclass
class Role:
    """角色模型"""

    role_name: str
    description: str
    permissions: set[str]
    is_default: bool = False


# ==================== 认证管理器 ====================


class AuthManager:
    """认证管理器"""

    def __init__(self, secret_key: str = "athena-gateway-secret", algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expiry = timedelta(hours=24)
        self.users_file = Path("data/auth_users.json")
        self.api_keys_file = Path("data/auth_api_keys.json")
        self.roles_file = Path("data/auth_roles.json")

        # 内存缓存
        self.users: dict[str, User] = {}
        self.api_keys: dict[str, APIKey] = {}
        self.roles: dict[str, Role] = {}

        self._load_data()
        self._init_default_data()

    def _load_data(self):
        """加载认证数据"""
        try:
            # 加载用户数据
            if self.users_file.exists():
                with open(self.users_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for user_id, user_data in data.get("users", {}).items():
                        self.users[user_id] = User(
                            user_id=user_id,
                            username=user_data["username"],
                            email=user_data["email"],
                            roles=user_data["roles"],
                            permissions=set(user_data["permissions"]),
                            created_at=datetime.fromisoformat(user_data["created_at"]),
                            last_login=datetime.fromisoformat(user_data.get("last_login"))
                            if user_data.get("last_login")
                            else None,
                            is_active=user_data.get("is_active", True),
                        )

            # 加载API密钥
            if self.api_keys_file.exists():
                with open(self.api_keys_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for key_id, key_data in data.get("api_keys", {}).items():
                        self.api_keys[key_id] = APIKey(
                            key_id=key_id,
                            user_id=key_data["user_id"],
                            key_name=key_data["key_name"],
                            permissions=set(key_data["permissions"]),
                            created_at=datetime.fromisoformat(key_data["created_at"]),
                            expires_at=datetime.fromisoformat(key_data["expires_at"])
                            if key_data.get("expires_at")
                            else None,
                            is_active=key_data.get("is_active", True),
                            usage_count=key_data.get("usage_count", 0),
                        )

            # 加载角色数据
            if self.roles_file.exists():
                with open(self.roles_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for role_name, role_data in data.get("roles", {}).items():
                        self.roles[role_name] = Role(
                            role_name=role_name,
                            description=role_data["description"],
                            permissions=set(role_data["permissions"]),
                            is_default=role_data.get("is_default", False),
                        )

            logger.info(
                f"加载认证数据: {len(self.users)} 用户, {len(self.api_keys)} API密钥, {len(self.roles)} 角色"
            )

        except Exception as e:
            logger.error(f"加载认证数据失败: {e}")

    def _save_data(self):
        """保存认证数据"""
        try:
            # 保存用户数据
            self.users_file.parent.mkdir(parents=True, exist_ok=True)
            users_data = {
                user_id: {
                    "username": user.username,
                    "email": user.email,
                    "roles": user.roles,
                    "permissions": list(user.permissions),
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "is_active": user.is_active,
                }
                for user_id, user in self.users.items()
            }

            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(
                    {"users": users_data, "updated_at": datetime.now().isoformat()},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            # 保存API密钥
            api_keys_data = {
                key_id: {
                    "user_id": api_key.user_id,
                    "key_name": api_key.key_name,
                    "permissions": list(api_key.permissions),
                    "created_at": api_key.created_at.isoformat(),
                    "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                    "is_active": api_key.is_active,
                    "usage_count": api_key.usage_count,
                }
                for key_id, api_key in self.api_keys.items()
            }

            with open(self.api_keys_file, "w", encoding="utf-8") as f:
                json.dump(
                    {"api_keys": api_keys_data, "updated_at": datetime.now().isoformat()},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            # 保存角色数据
            roles_data = {
                role_name: {
                    "description": role.description,
                    "permissions": list(role.permissions),
                    "is_default": role.is_default,
                }
                for role_name, role in self.roles.items()
            }

            with open(self.roles_file, "w", encoding="utf-8") as f:
                json.dump(
                    {"roles": roles_data, "updated_at": datetime.now().isoformat()},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

        except Exception as e:
            logger.error(f"保存认证数据失败: {e}")

    def _init_default_data(self):
        """初始化默认数据"""
        if not self.roles:
            # 创建默认角色
            self.roles["admin"] = Role(
                role_name="admin",
                description="系统管理员",
                permissions={"*"},  # 所有权限
                is_default=False,
            )

            self.roles["user"] = Role(
                role_name="user",
                description="普通用户",
                permissions={"read:api", "write:api"},
                is_default=True,
            )

            self.roles["readonly"] = Role(
                role_name="readonly",
                description="只读用户",
                permissions={"read:api"},
                is_default=False,
            )

        if not self.users:
            # 创建默认管理员用户
            default_password = "admin123"
            bcrypt.hashpw(default_password.encode("utf-8"), bcrypt.gensalt())

            admin_user = User(
                user_id="admin",
                username="admin",
                email="admin@athena.local",
                roles=["admin"],
                permissions=self.roles["admin"].permissions,
                created_at=datetime.now(),
            )

            self.users["admin"] = admin_user
            # 在实际应用中，应该存储hashed_password

            # 创建测试用户
            test_user = User(
                user_id="testuser",
                username="testuser",
                email="test@athena.local",
                roles=["user"],
                permissions=self.roles["user"].permissions,
                created_at=datetime.now(),
            )

            self.users["testuser"] = test_user

            # 创建API密钥
            test_api_key = APIKey(
                key_id="athena-test-key-12345",
                user_id="testuser",
                key_name="Test API Key",
                permissions={"read:api", "write:api"},
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=365),
            )

            self.api_keys["athena-test-key-12345"] = test_api_key

        self._save_data()
        logger.info("初始化默认认证数据完成")

    def generate_jwt_token(self, user_id: str) -> str:
        """生成JWT令牌"""
        payload = {
            "user_id": user_id,
            "exp": datetime.now() + self.token_expiry,
            "iat": datetime.now(),
            "type": "access",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_jwt_token(self, token: str) -> dict[str, Any] | None:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT令牌已过期")
            return None
        except jwt.InvalidTokenError:
            logger.warning("无效的JWT令牌")
            return None

    def verify_api_key(self, api_key: str) -> APIKey | None:
        """验证API密钥"""
        if api_key not in self.api_keys:
            return None

        key_obj = self.api_keys[api_key]

        # 检查密钥是否激活
        if not key_obj.is_active:
            return None

        # 检查是否过期
        if key_obj.expires_at and datetime.now() > key_obj.expires_at:
            return None

        # 更新使用计数
        key_obj.usage_count += 1
        self._save_data()

        return key_obj

    def get_user_by_id(self, user_id: str) -> User | None:
        """根据用户ID获取用户"""
        return self.users.get(user_id)

    def check_permission(self, user: User, required_permission: str) -> bool:
        """检查用户权限"""
        # 超级管理员权限
        if "*" in user.permissions:
            return True

        # 精确匹配
        if required_permission in user.permissions:
            return True

        # 模糊匹配 (例如 read:api 匹配 read:api:users)
        for permission in user.permissions:
            if permission.endswith(":*"):
                prefix = permission[:-2]
                if required_permission.startswith(prefix):
                    return True

        return False

    def check_api_key_permission(self, api_key: APIKey, required_permission: str) -> bool:
        """检查API密钥权限"""
        # 超级管理员权限
        if "*" in api_key.permissions:
            return True

        # 精确匹配
        if required_permission in api_key.permissions:
            return True

        # 模糊匹配
        for permission in api_key.permissions:
            if permission.endswith(":*"):
                prefix = permission[:-2]
                if required_permission.startswith(prefix):
                    return True

        return False


# ==================== FastAPI 中间件 ====================


class JWTAuthMiddleware:
    """JWT认证中间件"""

    def __init__(self, auth_manager: AuthManager, exclude_paths: list[str] = None):
        self.auth_manager = auth_manager
        self.exclude_paths = exclude_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
        ]

    async def __call__(self, request: Request, call_next):
        """中间件处理函数"""
        path = request.url.path

        # 跳过不需要认证的路径
        if any(path.startswith(exclude) for exclude in self.exclude_paths):
            return await call_next(request)

        # 检查Authorization头
        authorization = request.headers.get("Authorization")

        if not authorization:
            raise HTTPException(
                status_code=401, detail="缺少认证信息", headers={"WWW-Authenticate": "Bearer"}
            )

        try:
            # 解析Bearer token
            scheme, token = authorization.split(" ", 1)
            if scheme.lower() != "bearer":
                raise ValueError("无效的认证方案")

            # 验证JWT令牌
            payload = self.auth_manager.verify_jwt_token(token)
            if not payload:
                raise HTTPException(
                    status_code=401, detail="无效的认证令牌", headers={"WWW-Authenticate": "Bearer"}
                )

            # 获取用户信息
            user = self.auth_manager.get_user_by_id(payload["user_id"])
            if not user or not user.is_active:
                raise HTTPException(status_code=401, detail="用户不存在或已禁用")

            # 将用户信息添加到请求状态
            request.state.user = user
            request.state.auth_type = "jwt"
            request.state.auth_payload = payload

            return await call_next(request)

        except ValueError:
            raise HTTPException(
                status_code=401, detail="无效的认证格式", headers={"WWW-Authenticate": "Bearer"}
            ) from None
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"认证处理异常: {e}")
            raise HTTPException(status_code=401, detail="认证失败") from e


class APIKeyAuthMiddleware:
    """API密钥认证中间件"""

    def __init__(self, auth_manager: AuthManager, exclude_paths: list[str] = None):
        self.auth_manager = auth_manager
        self.exclude_paths = exclude_paths or ["/", "/health", "/docs", "/redoc", "/openapi.json"]

    async def __call__(self, request: Request, call_next):
        """中间件处理函数"""
        path = request.url.path

        # 跳过不需要认证的路径
        if any(path.startswith(exclude) for exclude in self.exclude_paths):
            return await call_next(request)

        # 检查X-API-Key头
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            raise HTTPException(
                status_code=401, detail="缺少API密钥", headers={"WWW-Authenticate": "ApiKey"}
            )

        # 验证API密钥
        key_obj = self.auth_manager.verify_api_key(api_key)
        if not key_obj:
            raise HTTPException(status_code=401, detail="无效的API密钥")

        # 将API密钥信息添加到请求状态
        request.state.api_key = key_obj
        request.state.auth_type = "api_key"

        return await call_next(request)


class PermissionMiddleware:
    """权限检查中间件"""

    def __init__(self, auth_manager: AuthManager, permission_map: dict[str, str]):
        self.auth_manager = auth_manager
        self.permission_map = permission_map  # 路径 -> 权限映射

    async def __call__(self, request: Request, call_next):
        """中间件处理函数"""
        path = request.url.path

        # 检查是否需要权限验证
        required_permission = None
        for route_path, permission in self.permission_map.items():
            if self._path_matches(path, route_path):
                required_permission = permission
                break

        if not required_permission:
            return await call_next(request)

        # 检查用户权限
        if hasattr(request.state, "user"):
            user = request.state.user
            if not self.auth_manager.check_permission(user, required_permission):
                raise HTTPException(
                    status_code=403, detail=f"权限不足，需要权限: {required_permission}"
                )

        # 检查API密钥权限
        elif hasattr(request.state, "api_key"):
            api_key = request.state.api_key
            if not self.auth_manager.check_api_key_permission(api_key, required_permission):
                raise HTTPException(
                    status_code=403, detail=f"API密钥权限不足，需要权限: {required_permission}"
                )

        return await call_next(request)

    def _path_matches(self, request_path: str, route_path: str) -> bool:
        """检查路径是否匹配"""
        if route_path == request_path:
            return True

        # 支持通配符
        if route_path.endswith("/*"):
            prefix = route_path[:-2]
            return request_path.startswith(prefix + "/") or request_path == prefix

        return False


# 全局认证管理器实例
auth_manager = AuthManager()

# 中间件实例
jwt_middleware = JWTAuthMiddleware(auth_manager)
api_key_middleware = APIKeyAuthMiddleware(auth_manager)

# 权限映射
permission_map = {
    "/api/v1/services/*": "admin:services",
    "/api/v1/routes/*": "admin:routes",
    "/api/v1/auth/*": "auth:manage",
    "/api/users/*": "read:api",
    "/api/products/*": "read:api",
    "/api/categories": "read:api",
}

permission_middleware = PermissionMiddleware(auth_manager, permission_map)
