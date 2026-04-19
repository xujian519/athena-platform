#!/usr/bin/env python3
"""
安全验证和权限管理
Security Authentication and Authorization Manager

提供JWT认证、权限控制、文件安全验证等功能
"""

import logging
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import jwt

logger = logging.getLogger(__name__)

class AuthManager:
    """认证管理器"""

    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.algorithm = "HS256"
        self.token_expire_hours = 24
        self.refresh_token_expire_days = 7

    def generate_tokens(self, user_id: str, user_data: dict[str, Any]) -> dict[str, str]:
        """生成访问令牌和刷新令牌"""
        try:
            # 生成访问令牌
            access_payload = {
                "user_id": user_id,
                "user_data": user_data,
                "type": "access",
                "exp": datetime.utcnow() + timedelta(hours=self.token_expire_hours),
                "iat": datetime.utcnow()
            }

            # 生成刷新令牌
            refresh_payload = {
                "user_id": user_id,
                "type": "refresh",
                "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
                "iat": datetime.utcnow()
            }

            access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
            refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": self.token_expire_hours * 3600
            }

        except Exception as e:
            logger.error(f"生成令牌失败: {e}")
            return {}

    def verify_token(self, token: str) -> dict[str, Any | None]:
        """验证访问令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # 检查令牌类型
            if payload.get("type") != "access":
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("令牌签名过期")
            return None
        except jwt.InvalidTokenError:
            logger.warning("无效令牌")
            return None

    def refresh_access_token(self, refresh_token: str) -> dict[str, str | None]:
        """刷新访问令牌"""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])

            if payload.get("type") != "refresh":
                return None

            # 获取用户信息
            user_id = payload["user_id"]
            user_data = payload.get("user_data", {})

            # 生成新的访问令牌
            return self.generate_tokens(user_id, user_data)

        except Exception as e:
            logger.error(f"刷新令牌失败: {e}")
            return None

class FileSecurityValidator:
    """文件安全验证器"""

    def __init__(self):
        self.dangerous_extensions = [
            '.exe', '.bat', '.cmd', '.com', '.scr', '.pif',
            '.vbs', '.js', '.jar', '.php', '.asp', '.aspx',
            '.sh', '.pyc', '.pyo', '.pyd', '.dll'
        ]

        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.scanned_files_cache = {}

    def validate_file_type(self, filename: str, content_type: str) -> dict[str, Any]:
        """验证文件类型"""
        result = {
            "valid": True,
            "warnings": [],
            "blocked": False
        }

        # 检查文件扩展名
        file_ext = Path(filename).suffix.lower()
        if file_ext in self.dangerous_extensions:
            result["valid"] = False
            result["blocked"] = True
            result["warnings"].append(f"危险文件类型: {file_ext}")

        # 检查MIME类型
        if content_type:
            dangerous_mimes = [
                'application/x-executable',
                'application/x-msdownload',
                'application/x-msdos-program',
                'application/x-msdownload'
            ]
            if content_type in dangerous_mimes:
                result["valid"] = False
                result["blocked"] = True
                result["warnings"].append(f"危险MIME类型: {content_type}")

        return result

    def validate_file_size(self, file_size: int) -> dict[str, Any]:
        """验证文件大小"""
        result = {
            "valid": True,
            "warnings": [],
            "blocked": False
        }

        if file_size > self.max_file_size:
            result["valid"] = False
            result["blocked"] = True
            result["warnings"].append(f"文件过大: {file_size / (1024*1024):.1f}MB (限制: {self.max_file_size / (1024*1024):.1f}MB)")

        return result

    def scan_file_content(self, content: bytes, filename: str) -> dict[str, Any]:
        """扫描文件内容"""
        result = {
            "safe": True,
            "warnings": [],
            "detected_patterns": []
        }

        try:
            # 文件头检查
            content_sample = content[:1024]  # 只检查前1KB

            # 检查可疑模式
            suspicious_patterns = [
                b'eval(',
                b'exec(',
                b'system(',
                b'shell_exec',
                b'os.system',
                b'subprocess.',
                b'__import__',
                b'compile(',
                b'execfile(',
                b'open(',
                b'reload('
            ]

            for pattern in suspicious_patterns:
                if pattern in content_sample:
                    result["safe"] = False
                    result["detected_patterns"].append(pattern.decode('utf-8', errors='ignore'))
                    result["warnings"].append("检测到可疑代码模式")

            # 检查PE文件头（Windows可执行文件）
            if content.startswith(b'MZ') and filename.lower().endswith('.exe'):
                result["safe"] = False
                result["warnings"].append("检测到PE可执行文件头")

            # 检查ELF文件头（Linux可执行文件）
            if content.startswith(b'\x7fELF') and not filename.lower().endswith(('.txt', '.md', '.json')):
                result["safe"] = False
                result["warnings"].append("检测到ELF可执行文件头")

        except Exception as e:
            logger.error(f"文件内容扫描失败: {e}")
            result["safe"] = False
            result["warnings"].append(f"扫描异常: {e}")

        return result

    def is_file_scanned(self, file_hash: str) -> bool:
        """检查文件是否已扫描"""
        return file_hash in self.scanned_files_cache

    def mark_file_scanned(self, file_hash: str, scan_result: dict[str, Any]) -> Any:
        """标记文件已扫描"""
        self.scanned_files_cache[file_hash] = {
            "scanned_at": datetime.now().isoformat(),
            "result": scan_result
        }

class PermissionManager:
    """权限管理器"""

    def __init__(self):
        self.role_permissions = {
            "admin": ["read", "write", "delete", "admin", "upload", "download", "manage"],
            "user": ["read", "write", "delete", "upload", "download"],
            "guest": ["read", "download"]
        }

    def has_permission(self, user_role: str, permission: str) -> bool:
        """检查用户是否有指定权限"""
        return permission in self.role_permissions.get(user_role, [])

    def check_file_access(self, user_id: str, file_id: str, action: str,
                           file_info: dict[str, Any] = None) -> dict[str, Any]:
        """检查文件访问权限"""
        result = {
            "allowed": True,
            "reason": ""
        }

        # 这里可以实现更复杂的权限逻辑
        # 例如：文件所有者权限、项目权限等

        return result

# 全局实例
auth_manager = AuthManager()
file_validator = FileSecurityValidator()
permission_manager = PermissionManager()

# 装饰器
def require_auth(permission: str = None) -> Any:
    """认证装饰器"""
    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> Any:
            # 从请求头获取令牌
            # 这里需要根据实际的web框架实现
            pass
        return wrapper
    return decorator

# 使用示例
def test_security() -> Any:
    """测试安全功能"""
    print("=== 安全系统测试 ===")

    # 测试JWT认证
    print("\n1. JWT认证测试:")
    tokens = auth_manager.generate_tokens("user123", {
        "role": "user",
        "name": "测试用户"
    })
    print(f"生成令牌成功: {'access_token': '✅', 'refresh_token': '✅'}")

    # 测试令牌验证
    if "access_token" in tokens:
        payload = auth_manager.verify_token(tokens["access_token"])
        if payload:
            print(f"令牌验证成功: {payload['user_id']}")
        else:
            print("令牌验证失败")

    # 测试文件安全验证
    print("\n2. 文件安全验证测试:")

    # 测试危险文件
    dangerous_file = "test.exe"
    file_validator.validate_file_type(dangerous_file, "application/x-executable")
    print(f"危险文件验证: {'blocked': result['blocked'], 'warnings': result['warnings']}")

    # 测试文件大小
    large_file_size = 200 * 1024 * 1024  # 200MB
    file_validator.validate_file_size(large_file_size)
    print(f"大文件验证: {'blocked': size_result['blocked'], 'warnings': size_result['warnings']}")

    # 测试内容扫描
    file_validator.scan_file_content(b"eval('malicious code')", "test.py")
    print(f"内容扫描: {'safe': scan_result['safe'], 'warnings': scan_result['warnings']}")

if __name__ == "__main__":
    test_security()
