#!/usr/bin/env python3
"""
Athena平台管理中心
Athena Platform Management Center
提供平台级的用户管理、资源监控、安全管理和合规监控
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import jwt
import uvicorn
import yaml

# FastAPI相关
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr

# 导入统一认证模块

# 数据库相关
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

# 加密相关
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = logging.getLogger('AthenaPlatformManager')

# 枚举类型
class UserRole(Enum):
    """用户角色"""
    ADMIN = 'admin'
    OPERATOR = 'operator'
    ANALYST = 'analyst'
    VIEWER = 'viewer'

class UserStatus(Enum):
    """用户状态"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'
    DELETED = 'deleted'

class ResourceType(Enum):
    """资源类型"""
    SERVICE = 'service'
    API = 'api'
    DATA = 'data'
    FILE = 'file'
    CONFIG = 'config'

@dataclass
class User:
    """用户信息"""
    user_id: str
    username: str
    email: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    last_login: datetime | None = None
    permissions: list[str] = field(default_factory=list)
    api_keys: list[str] = field(default_factory=list)

@dataclass
class ResourceAccess:
    """资源访问记录"""
    user_id: str
    resource_type: ResourceType
    resource_id: str
    action: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    success: bool

# Pydantic模型
class UserCreate(BaseModel):
    """创建用户请求"""
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.VIEWER

class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str

class UserUpdate(BaseModel):
    """更新用户请求"""
    email: EmailStr | None = None
    role: UserRole | None = None
    status: UserStatus | None = None
    permissions: list[str] | None = None

class APIKeyRequest(BaseModel):
    """API密钥请求"""
    user_id: str
    description: str = ''

class AccessLog(BaseModel):
    """访问日志"""
    user_id: str
    resource_type: str
    resource_id: str
    action: str
    ip_address: str
    user_agent: str
    success: bool
    timestamp: datetime

class SystemMetrics(BaseModel):
    """系统指标"""
    active_users: int
    total_requests: int
    error_rate: float
    average_response_time: float
    resource_usage: dict[str, float]
    timestamp: datetime

class AthenaPlatformManager:
    """Athena平台管理器"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or '/Users/xujian/Athena工作平台/deploy/multimodal_platform_config.yaml'
        self.config = self._load_config()

        # 数据库连接
        self.db_connection = None
        self._initialize_database()

        # 加密密钥
        self.encryption_key = self._load_encryption_key()

        # JWT密钥
        self.jwt_secret = self.config.get('security', {}).get('authentication', {}).get('jwt_secret', 'athena_secret_key')

        # 用户管理
        self.users: dict[str, User] = {}
        self.sessions: dict[str, dict[str, Any] = {}

        # 访问日志
        self.access_logs: list[ResourceAccess] = []

        # API密钥管理
        self.api_keys: dict[str, dict[str, Any] = {}

        # 权限定义
        self.role_permissions = self._define_role_permissions()

        # 初始化默认管理员用户
        self._initialize_admin_user()

        logger.info('Athena平台管理器初始化完成')

    def _load_config(self) -> dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            return {}

    def _initialize_database(self) -> Any:
        """初始化数据库连接"""
        if not DATABASE_AVAILABLE:
            logger.warning('数据库不可用，使用内存存储')
            return

        try:
            db_config = self.config.get('storage', {}).get('database', {})
            self.db_connection = psycopg2.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 5432),
                database=db_config.get('database', 'athena_multimodal'),
                user=db_config.get('username', 'athena_user'),
                password=os.environ.get('DB_PASSWORD', '')
            )
            self._create_tables()
            logger.info('数据库连接成功')
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            self.db_connection = None

    def _create_tables(self) -> Any:
        """创建数据库表"""
        if not self.db_connection:
            return

        try:
            with self.db_connection.cursor() as cursor:
                # 用户表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id VARCHAR(36) PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(20) NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        permissions TEXT
                    )
                """)

                # API密钥表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS api_keys (
                        key_id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(36) REFERENCES users(user_id),
                        api_key VARCHAR(255) UNIQUE NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_used TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)

                # 访问日志表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS access_logs (
                        log_id SERIAL PRIMARY KEY,
                        user_id VARCHAR(36),
                        resource_type VARCHAR(50),
                        resource_id VARCHAR(100),
                        action VARCHAR(50),
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        success BOOLEAN,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                self.db_connection.commit()
                logger.info('数据库表创建成功')

        except Exception as e:
            logger.error(f"数据库表创建失败: {e}")

    def _load_encryption_key(self) -> bytes:
        """加载加密密钥"""
        if CRYPTO_AVAILABLE:
            key_file = '/etc/athena/encryption.key'
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    return f.read()
            else:
                # 生成新密钥
                key = Fernet.generate_key()
                os.makedirs(os.path.dirname(key_file), exist_ok=True)
                with open(key_file, 'wb') as f:
                    f.write(key)
                return key
        else:
            return b"default_encryption_key"

    def _define_role_permissions(self) -> dict[UserRole, list[str]:
        """定义角色权限"""
        return {
            UserRole.ADMIN: [
                'user:read', 'user:write', 'user:delete',
                'service:start', 'service:stop', 'service:restart', 'service:scale',
                'config:read', 'config:write',
                'metrics:read', 'logs:read',
                'api_key:create', 'api_key:delete',
                'system:manage', 'security:manage'
            ],
            UserRole.OPERATOR: [
                'service:start', 'service:stop', 'service:restart',
                'metrics:read', 'logs:read',
                'config:read'
            ],
            UserRole.ANALYST: [
                'metrics:read', 'logs:read',
                'config:read',
                'api:analyze'
            ],
            UserRole.VIEWER: [
                'metrics:read',
                'config:read'
            ]
        }

    def _initialize_admin_user(self) -> Any:
        """初始化默认管理员用户"""
        admin_user = User(
            user_id='admin_001',
            username='admin',
            email='admin@athena.ai',
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            permissions=self.role_permissions[UserRole.ADMIN]
        )

        self.users[admin_user.user_id] = admin_user
        logger.info('默认管理员用户初始化完成')

    def hash_password(self, password: str) -> str:
        """密码哈希"""
        if CRYPTO_AVAILABLE:
            key = Fernet(self.encryption_key)
            hashed_password = key.encrypt(password.encode())
            return hashed_password.decode()
        else:
            # 简单的哈希（生产环境应使用更安全的方法）
            return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码"""
        if CRYPTO_AVAILABLE:
            key = Fernet(self.encryption_key)
            try:
                decrypted_password = key.decrypt(hashed_password.encode())
                return decrypted_password.decode() == password
            except Exception:  # TODO: 指定具体异常类型
                return False
        else:
            return hashlib.sha256(password.encode()).hexdigest() == hashed_password

    def create_user(self, user_data: UserCreate) -> dict[str, Any]:
        """创建用户"""
        # 检查用户名是否已存在
        for user in self.users.values():
            if user.username == user_data.username or user.email == user_data.email:
                return {'success': False, 'error': '用户名或邮箱已存在'}

        # 创建新用户
        user_id = f"user_{int(time.time())}_{len(self.users)}"
        new_user = User(
            user_id=user_id,
            username=user_data.username,
            email=user_data.email,
            role=user_data.role,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            permissions=self.role_permissions[user_data.role]
        )

        # 保存到数据库
        if self.db_connection:
            try:
                with self.db_connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO users (user_id, username, email, password_hash, role, status, permissions)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_id,
                        user_data.username,
                        user_data.email,
                        self.hash_password(user_data.password),
                        user_data.role.value,
                        UserStatus.ACTIVE.value,
                        json.dumps(new_user.permissions)
                    ))
                    self.db_connection.commit()
            except Exception as e:
                logger.error(f"保存用户到数据库失败: {e}")
                return {'success': False, 'error': '数据库保存失败'}

        self.users[user_id] = new_user
        return {'success': True, 'user_id': user_id}

    def authenticate_user(self, username: str, password: str) -> dict[str, Any | None]:
        """用户认证"""
        for user in self.users.values():
            if user.username == username and user.status == UserStatus.ACTIVE:
                if self.db_connection:
                    # 从数据库验证
                    try:
                        with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                            cursor.execute("""
                                SELECT user_id, password_hash FROM users WHERE username = %s AND status = 'active'
                            """, (username,))
                            result = cursor.fetchone()
                            if result and self.verify_password(password, result['password_hash']):
                                # 更新最后登录时间
                                cursor.execute("""
                                    UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s
                                """, (result['user_id'],))
                                self.db_connection.commit()

                                user.last_login = datetime.now()
                                return {
                                    'user_id': user.user_id,
                                    'username': user.username,
                                    'role': user.role.value,
                                    'permissions': user.permissions
                                }
                    except Exception as e:
                        logger.error(f"数据库认证失败: {e}")
                else:
                    # 内存验证
                    if self.verify_password(password, user.password_hash):
                        user.last_login = datetime.now()
                        return {
                            'user_id': user.user_id,
                            'username': user.username,
                            'role': user.role.value,
                            'permissions': user.permissions
                        }

        return None

    def generate_jwt_token(self, user_info: dict[str, Any]) -> str:
        """生成JWT令牌"""
        payload = {
            'user_id': user_info['user_id'],
            'username': user_info['username'],
            'role': user_info['role'],
            'permissions': user_info['permissions'],
            'exp': datetime.now() + timedelta(hours=24),
            'iat': datetime.now()
        }

        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')

    def verify_jwt_token(self, token: str) -> dict[str, Any | None]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def check_permission(self, user_info: dict[str, Any], required_permission: str) -> bool:
        """检查用户权限"""
        user_permissions = user_info.get('permissions', [])
        return required_permission in user_permissions

    def log_access(self, user_info: dict[str, Any], resource_type: str, resource_id: str,
                   action: str, ip_address: str, user_agent: str, success: bool = True):
        """记录访问日志"""
        access_log = ResourceAccess(
            user_id=user_info['user_id'],
            resource_type=ResourceType(resource_type),
            resource_id=resource_id,
            action=action,
            timestamp=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )

        self.access_logs.append(access_log)

        # 保存到数据库
        if self.db_connection:
            try:
                with self.db_connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO access_logs (user_id, resource_type, resource_id, action, ip_address, user_agent, success)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        access_log.user_id,
                        access_log.resource_type.value,
                        access_log.resource_id,
                        access_log.action,
                        access_log.ip_address,
                        access_log.user_agent,
                        access_log.success
                    ))
                    self.db_connection.commit()
            except Exception as e:
                logger.error(f"保存访问日志失败: {e}")

        # 限制日志数量
        if len(self.access_logs) > 10000:
            self.access_logs = self.access_logs[-5000]

    def generate_api_key(self, user_id: str, description: str = '') -> str:
        """生成API密钥"""
        key_id = f"key_{int(time.time())}"
        api_key = f"ath_{hashlib.sha256(f'{user_id}_{time.time()}'.encode()).hexdigest()[:32]}"

        # 保存到内存
        self.api_keys[api_key] = {
            'key_id': key_id,
            'user_id': user_id,
            'description': description,
            'created_at': datetime.now(),
            'last_used': None,
            'is_active': True
        }

        # 保存到数据库
        if self.db_connection:
            try:
                with self.db_connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO api_keys (key_id, user_id, api_key, description)
                        VALUES (%s, %s, %s, %s)
                    """, (key_id, user_id, api_key, description))
                    self.db_connection.commit()
            except Exception as e:
                logger.error(f"保存API密钥失败: {e}")

        return api_key

    def validate_api_key(self, api_key: str) -> dict[str, Any | None]:
        """验证API密钥"""
        key_info = self.api_keys.get(api_key)
        if key_info and key_info['is_active']:
            # 更新最后使用时间
            key_info['last_used'] = datetime.now()
            return {
                'user_id': key_info['user_id'],
                'key_id': key_info['key_id']
            }

        # 从数据库验证
        if self.db_connection:
            try:
                with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT user_id, key_id FROM api_keys WHERE api_key = %s AND is_active = TRUE
                    """, (api_key,))
                    result = cursor.fetchone()
                    if result:
                        # 更新最后使用时间
                        cursor.execute("""
                            UPDATE api_keys SET last_used = CURRENT_TIMESTAMP WHERE api_key = %s
                        """, (api_key,))
                        self.db_connection.commit()
                        return {
                            'user_id': result['user_id'],
                            'key_id': result['key_id']
                        }
            except Exception as e:
                logger.error(f"数据库API密钥验证失败: {e}")

        return None

    def get_system_metrics(self) -> SystemMetrics:
        """获取系统指标"""
        # 计算活跃用户数
        active_users = len([u for u in self.users.values() if u.status == UserStatus.ACTIVE])

        # 计算总请求数和错误率（最近1小时）
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        recent_logs = [log for log in self.access_logs if log.timestamp > one_hour_ago]
        total_requests = len(recent_logs)
        error_count = len([log for log in recent_logs if not log.success])
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0.0

        # 获取资源使用情况
        resource_usage = {
            'cpu': self._get_cpu_usage(),
            'memory': self._get_memory_usage(),
            'disk': self._get_disk_usage()
        }

        return SystemMetrics(
            active_users=active_users,
            total_requests=total_requests,
            error_rate=error_rate,
            average_response_time=0.0,  # 需要实际实现
            resource_usage=resource_usage,
            timestamp=now
        )

    def _get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 0.0

    def _get_memory_usage(self) -> float:
        """获取内存使用率"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            return 0.0

    def _get_disk_usage(self) -> float:
        """获取磁盘使用率"""
        try:
            import psutil
            return psutil.disk_usage('/').percent
        except ImportError:
            return 0.0

# 全局实例
platform_manager = None

def get_platform_manager() -> Any | None:
    """获取平台管理器实例"""
    global platform_manager
    if platform_manager is None:
        platform_manager = AthenaPlatformManager()
    return platform_manager

# 认证依赖
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """获取当前用户"""
    token = credentials.credentials
    pm = get_platform_manager()
    user_info = pm.verify_jwt_token(token)

    if not user_info:
        raise HTTPException(status_code=401, detail='无效的认证令牌')

    return user_info

# 创建FastAPI应用
app = FastAPI(
    title='Athena平台管理中心',
    description='Athena多模态文件系统平台管理',
    version='1.0.0'
)


# API端点
@app.post('/auth/login')
async def login(login_data: UserLogin):
    """用户登录"""
    pm = get_platform_manager()
    user_info = pm.authenticate_user(login_data.username, login_data.password)

    if not user_info:
        raise HTTPException(status_code=401, detail='用户名或密码错误')

    token = pm.generate_jwt_token(user_info)
    return {
        'access_token': token,
        'token_type': 'bearer',
        'user_info': user_info
    }

@app.post('/users')
async def create_user(user_data: UserCreate, current_user: dict = Depends(get_current_user)):
    """创建用户"""
    pm = get_platform_manager()

    # 检查权限
    if not pm.check_permission(current_user, 'user:write'):
        raise HTTPException(status_code=403, detail='权限不足')

    result = pm.create_user(user_data)
    return result

@app.get('/users')
async def get_users(current_user: dict = Depends(get_current_user)):
    """获取用户列表"""
    pm = get_platform_manager()

    if not pm.check_permission(current_user, 'user:read'):
        raise HTTPException(status_code=403, detail='权限不足')

    users_list = []
    for user in pm.users.values():
        users_list.append({
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'role': user.role.value,
            'status': user.status.value,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        })

    return {'users': users_list, 'total': len(users_list)}

@app.post('/api_keys')
async def create_api_key(request: APIKeyRequest, current_user: dict = Depends(get_current_user)):
    """创建API密钥"""
    pm = get_platform_manager()

    if not pm.check_permission(current_user, 'api_key:create'):
        raise HTTPException(status_code=403, detail='权限不足')

    if request.user_id != current_user['user_id'] and not pm.check_permission(current_user, 'user:manage'):
        raise HTTPException(status_code=403, detail='只能为自己创建API密钥')

    api_key = pm.generate_api_key(request.user_id, request.description)
    return {'api_key': api_key, 'message': 'API密钥创建成功'}

@app.get('/metrics/system')
async def get_system_metrics(current_user: dict = Depends(get_current_user)):
    """获取系统指标"""
    pm = get_platform_manager()

    if not pm.check_permission(current_user, 'metrics:read'):
        raise HTTPException(status_code=403, detail='权限不足')

    metrics = pm.get_system_metrics()
    return metrics.dict()

@app.get('/logs/access')
async def get_access_logs(limit: int = 100, current_user: dict = Depends(get_current_user)):
    """获取访问日志"""
    pm = get_platform_manager()

    if not pm.check_permission(current_user, 'logs:read'):
        raise HTTPException(status_code=403, detail='权限不足')

    logs = pm.access_logs[-limit:]
    return {
        'logs': [
            {
                'user_id': log.user_id,
                'resource_type': log.resource_type.value,
                'resource_id': log.resource_id,
                'action': log.action,
                'ip_address': log.ip_address,
                'success': log.success,
                'timestamp': log.timestamp.isoformat()
            }
            for log in logs
        ],
        'total': len(pm.access_logs)
    }

@app.get('/health')
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'service': 'Athena平台管理中心',
        'timestamp': datetime.now().isoformat()
    }

# 启动服务
if __name__ == '__main__':
    manager_config = {
        'host': '0.0.0.0',
        'port': 9000,
        'reload': False,
        'log_level': 'info'
    }

    uvicorn.run(
        'athena_platform_manager:app',
        **manager_config
    )
