"""
自主控制系统安全认证模块
"""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import config

# 安全配置
security = HTTPBearer()

@dataclass
class User:
    """用户信息"""
    id: str
    username: str
    role: str
    permissions: list

class AuthManager:
    """认证管理器"""

    def __init__(self):
        self.secret_key = config.security.secret_key
        self.algorithm = config.security.algorithm
        self.access_token_expire_minutes = config.security.access_token_expire_minutes

        # 预定义的用户（生产环境应使用数据库）
        self.users = {
            'athena_admin': {
                'id': 'admin_001',
                'username': 'athena_admin',
                'password_hash': self._hash_password('athena_admin_2024'),
                'role': 'admin',
                'permissions': ['*']  # 所有权限
            },
            'athena_operator': {
                'id': 'operator_001',
                'username': 'athena_operator',
                'password_hash': self._hash_password('operator_2024'),
                'role': 'operator',
                'permissions': [
                    'read:system',
                    'write:tasks',
                    'control:services',
                    'read:agents'
                ]
            },
            'athena_viewer': {
                'id': 'viewer_001',
                'username': 'athena_viewer',
                'password_hash': self._hash_password('viewer_2024'),
                'role': 'viewer',
                'permissions': [
                    'read:system',
                    'read:tasks',
                    'read:agents'
                ]
            }
        }

        # API访问令牌（用于服务间调用）
        self.api_tokens = {
            'athena-autonomous-2024': {
                'user_id': 'admin_001',
                'role': 'service',
                'permissions': ['*'],
                'expires': None  # 永不过期
            },
            'xiaonuo-service-2024': {
                'user_id': 'operator_001',
                'role': 'service',
                'permissions': [
                    'write:tasks',
                    'read:agents',
                    'control:services'
                ],
                'expires': None
            }
        }

    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256',
                                          password.encode('utf-8'),
                                          salt.encode('utf-8'),
                                          100000)
        return f"{salt}${password_hash.hex()}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            salt, hash_value = password_hash.split('$')
            computed_hash = hashlib.pbkdf2_hmac('sha256',
                                             password.encode('utf-8'),
                                             salt.encode('utf-8'),
                                             100000)
            return computed_hash.hex() == hash_value
        except Exception:  # TODO: 指定具体异常类型
            return False

    def authenticate_user(self, username: str, password: str) -> User | None:
        """用户认证"""
        user_data = self.users.get(username)
        if not user_data:
            return None

        if not self._verify_password(password, user_data['password_hash']):
            return None

        return User(
            id=user_data['id'],
            username=user_data['username'],
            role=user_data['role'],
            permissions=user_data['permissions']
        )

    def authenticate_token(self, token: str) -> User | None:
        """令牌认证"""
        # 检查API令牌
        if token in self.api_tokens:
            token_data = self.api_tokens[token]
            if token_data['expires'] and datetime.now() > token_data['expires']:
                return None

            return User(
                id=token_data['user_id'],
                username=f"service_{token_data['user_id']}",
                role=token_data['role'],
                permissions=token_data['permissions']
            )

        # 检查JWT令牌
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username = payload.get('sub')
            if username is None:
                return None

            user_data = self.users.get(username)
            if not user_data:
                return None

            return User(
                id=user_data['id'],
                username=user_data['username'],
                role=user_data['role'],
                permissions=user_data['permissions']
            )
        except jwt.PyJWTError:
            return None

    def create_access_token(self, username: str, expires_delta: timedelta | None = None) -> str:
        """创建访问令牌"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode = {'sub': username, 'exp': expire}
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def check_permission(self, user: User, required_permission: str) -> bool:
        """检查权限"""
        # 管理员有所有权限
        if '*' in user.permissions:
            return True

        # 检查具体权限
        if required_permission in user.permissions:
            return True

        # 检查通配符权限
        resource = required_permission.split(':')[0]
        wildcard_permission = f"{resource}:*"
        if wildcard_permission in user.permissions:
            return True

        return False

# 全局认证管理器实例
auth_manager = AuthManager()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> User:
    """获取当前用户"""
    if not config.security.enable_authentication:
        # 如果禁用认证，返回管理员用户
        return User(
            id='debug_admin',
            username='debug_admin',
            role='admin',
            permissions=['*']
        )

    user = auth_manager.authenticate_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail='无效的认证凭据',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    return user

def require_permission(permission: str) -> Any:
    """权限检查装饰器"""
    def permission_checker(current_user: User = Depends(get_current_user)):
        if not auth_manager.check_permission(current_user, permission):
            raise HTTPException(
                status_code=403,
                detail=f"权限不足，需要权限: {permission}"
            )
        return current_user
    return permission_checker

# 权限常量
class Permissions:
    # 系统权限
    READ_SYSTEM = 'read:system'
    WRITE_SYSTEM = 'write:system'

    # 任务权限
    READ_TASKS = 'read:tasks'
    WRITE_TASKS = 'write:tasks'
    DELETE_TASKS = 'delete:tasks'

    # 服务权限
    READ_SERVICES = 'read:services'
    CONTROL_SERVICES = 'control:services'

    # Agent权限
    READ_AGENTS = 'read:agents'
    WRITE_AGENTS = 'write:agents'

    # 决策权限
    READ_DECISIONS = 'read:decisions'
    WRITE_DECISIONS = 'write:decisions'

    # 目标权限
    READ_GOALS = 'read:goals'
    WRITE_GOALS = 'write:goals'
