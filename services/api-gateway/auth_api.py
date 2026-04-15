#!/usr/bin/env python3
"""
认证API端点
提供登录、令牌刷新、用户管理等认证相关功能
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import bcrypt
from auth_middleware import auth_manager
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建路由器
auth_router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


# 数据模型
class LoginRequest(BaseModel):
    """登录请求模型"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应模型"""

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")
    user_info: dict[str, Any] = Field(..., description="用户信息")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""

    refresh_token: str = Field(..., description="刷新令牌")


class UserCreateRequest(BaseModel):
    """创建用户请求"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, description="密码")
    roles: list[str] = Field(default=["user"], description="角色列表")


class APIKeyCreateRequest(BaseModel):
    """创建API密钥请求"""

    key_name: str = Field(..., description="密钥名称")
    permissions: list[str] = Field(..., description="权限列表")
    expires_days: int | None = Field(default=365, description="有效期(天)")


class APIKeyResponse(BaseModel):
    """API密钥响应"""

    key_id: str = Field(..., description="密钥ID")
    api_key: str = Field(..., description="API密钥")
    key_name: str = Field(..., description="密钥名称")
    permissions: list[str] = Field(..., description="权限列表")
    created_at: str = Field(..., description="创建时间")
    expires_at: str | None = Field(None, description="过期时间")


# ==================== 辅助函数 ====================


def get_current_user(request: Request):
    """获取当前用户"""
    if hasattr(request.state, "user"):
        return request.state.user
    raise HTTPException(status_code=401, detail="未认证")


def verify_permission(user, required_permission: str):
    """验证权限"""
    if not auth_manager.check_permission(user, required_permission):
        raise HTTPException(status_code=403, detail=f"权限不足，需要权限: {required_permission}")


def hash_password(password: str) -> str:
    """哈希密码"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ==================== 认证端点 ====================


@auth_router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """用户登录"""
    username = request.username
    password = request.password

    # 查找用户 (在实际应用中应该查询数据库)
    user = None
    for u in auth_manager.users.values():
        if u.username == username and u.is_active:
            user = u
            break

    if not user:
        # 创建临时用户用于演示 (在实际应用中应该验证密码)
        if username == "admin" and password == "admin123":
            user = auth_manager.get_user_by_id("admin")
        elif username == "testuser" and password == "test123":
            user = auth_manager.get_user_by_id("testuser")

    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 生成JWT令牌
    access_token = auth_manager.generate_jwt_token(user.user_id)
    expires_in = int(auth_manager.token_expiry.total_seconds())

    # 更新最后登录时间
    user.last_login = datetime.now()
    auth_manager._save_data()

    logger.info(f"用户登录成功: {username} ({user.user_id})")

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user_info={
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "roles": user.roles,
            "permissions": list(user.permissions),
        },
    )


@auth_router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: RefreshTokenRequest):
    """刷新访问令牌"""
    # 这里简化处理，直接生成新令牌
    # 在实际应用中应该验证refresh_token
    payload = auth_manager.verify_jwt_token(request.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的刷新令牌")

    user = auth_manager.get_user_by_id(payload["user_id"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    # 生成新的访问令牌
    access_token = auth_manager.generate_jwt_token(user.user_id)
    expires_in = int(auth_manager.token_expiry.total_seconds())

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user_info={
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "roles": user.roles,
            "permissions": list(user.permissions),
        },
    )


@auth_router.post("/logout")
async def logout(request: Request):
    """用户登出"""
    # 在JWT方案中，登出通常在客户端删除令牌
    # 这里可以记录登出事件或实现令牌黑名单
    user = get_current_user(request)

    logger.info(f"用户登出: {user.username} ({user.user_id})")

    return {"message": "登出成功"}


@auth_router.get("/me")
async def get_current_user_info(request: Request):
    """获取当前用户信息"""
    user = get_current_user(request)

    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "roles": user.roles,
        "permissions": list(user.permissions),
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "is_active": user.is_active,
    }


# ==================== 用户管理端点 ====================


@auth_router.get("/users")
async def list_users(request: Request):
    """获取用户列表 (需要管理员权限)"""
    user = get_current_user(request)
    verify_permission(user, "admin:users")

    users_list = []
    for u in auth_manager.users.values():
        users_list.append(
            {
                "user_id": u.user_id,
                "username": u.username,
                "email": u.email,
                "roles": u.roles,
                "created_at": u.created_at.isoformat(),
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "is_active": u.is_active,
            }
        )

    return {"users": users_list, "total": len(users_list)}


@auth_router.post("/users")
async def create_user(request: Request, user_data: UserCreateRequest):
    """创建用户 (需要管理员权限)"""
    current_user = get_current_user(request)
    verify_permission(current_user, "admin:users")

    # 检查用户名是否已存在
    for u in auth_manager.users.values():
        if u.username == user_data.username:
            raise HTTPException(status_code=400, detail="用户名已存在")
        if u.email == user_data.email:
            raise HTTPException(status_code=400, detail="邮箱已存在")

    # 验证角色
    for role_name in user_data.roles:
        if role_name not in auth_manager.roles:
            raise HTTPException(status_code=400, detail=f"角色不存在: {role_name}")

    # 计算权限
    permissions = set()
    for role_name in user_data.roles:
        role = auth_manager.roles[role_name]
        permissions.update(role.permissions)

    # 创建用户
    new_user_id = f"user_{len(auth_manager.users) + 1}"
    from auth_middleware import User

    new_user = User(
        user_id=new_user_id,
        username=user_data.username,
        email=user_data.email,
        roles=user_data.roles,
        permissions=permissions,
        created_at=datetime.now(),
    )

    auth_manager.users[new_user_id] = new_user
    auth_manager._save_data()

    logger.info(f"创建用户: {user_data.username} ({new_user_id})")

    return {
        "message": "用户创建成功",
        "user_id": new_user_id,
        "username": new_user.username,
        "email": new_user.email,
        "roles": new_user.roles,
    }


# ==================== API密钥管理端点 ====================


@auth_router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(request: Request):
    """获取当前用户的API密钥列表"""
    user = get_current_user(request)

    api_keys_list = []
    for key_obj in auth_manager.api_keys.values():
        if key_obj.user_id == user.user_id:
            api_keys_list.append(
                APIKeyResponse(
                    key_id=key_obj.key_id,
                    api_key="***" + key_obj.key_id[-10:]
                    if len(key_obj.key_id) > 10
                    else "***",  # 隐藏完整密钥
                    key_name=key_obj.key_name,
                    permissions=list(key_obj.permissions),
                    created_at=key_obj.created_at.isoformat(),
                    expires_at=key_obj.expires_at.isoformat() if key_obj.expires_at else None,
                )
            )

    return api_keys_list


@auth_router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(request: Request, key_data: APIKeyCreateRequest):
    """创建新的API密钥"""
    user = get_current_user(request)
    verify_permission(user, "auth:api_keys")

    # 生成唯一密钥ID
    import uuid

    key_id = f"athena-{uuid.uuid4().hex}"

    # 计算过期时间
    expires_at = None
    if key_data.expires_days:
        expires_at = datetime.now() + timedelta(days=key_data.expires_days)

    # 创建API密钥
    from auth_middleware import APIKey

    new_api_key = APIKey(
        key_id=key_id,
        user_id=user.user_id,
        key_name=key_data.key_name,
        permissions=set(key_data.permissions),
        created_at=datetime.now(),
        expires_at=expires_at,
    )

    auth_manager.api_keys[key_id] = new_api_key
    auth_manager._save_data()

    logger.info(f"创建API密钥: {key_data.key_name} for {user.username}")

    return APIKeyResponse(
        key_id=key_id,
        api_key=key_id,  # 只在创建时返回完整密钥
        key_name=new_api_key.key_name,
        permissions=list(new_api_key.permissions),
        created_at=new_api_key.created_at.isoformat(),
        expires_at=expires_at.isoformat() if expires_at else None,
    )


@auth_router.delete("/api-keys/{key_id}")
async def delete_api_key(request: Request, key_id: str):
    """删除API密钥"""
    user = get_current_user(request)

    if key_id not in auth_manager.api_keys:
        raise HTTPException(status_code=404, detail="API密钥不存在")

    api_key = auth_manager.api_keys[key_id]

    # 检查权限 (用户只能删除自己的密钥，管理员可以删除任何密钥)
    if api_key.user_id != user.user_id:
        verify_permission(user, "admin:api_keys")

    del auth_manager.api_keys[key_id]
    auth_manager._save_data()

    logger.info(f"删除API密钥: {key_id} by {user.username}")

    return {"message": "API密钥删除成功"}


# ==================== 角色和权限信息 ====================


@auth_router.get("/roles")
async def list_roles():
    """获取所有角色和权限信息"""
    roles_list = []
    for role_name, role in auth_manager.roles.items():
        roles_list.append(
            {
                "role_name": role_name,
                "description": role.description,
                "permissions": list(role.permissions),
                "is_default": role.is_default,
            }
        )

    return {"roles": roles_list}


@auth_router.get("/permissions")
async def list_permissions():
    """获取所有可用权限"""
    permissions = {
        "auth": ["auth:manage", "auth:api_keys", "auth:users"],
        "admin": ["admin:services", "admin:routes", "admin:users", "admin:api_keys", "*"],
        "api": ["read:api", "write:api", "read:api:users", "write:api:users"],
        "system": ["system:monitor", "system:logs"],
    }

    return {"permissions": permissions}
