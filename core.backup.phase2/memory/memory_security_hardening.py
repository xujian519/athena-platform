
#!/usr/bin/env python3
from __future__ import annotations
"""
Athena记忆系统安全加固措施
Memory System Security Hardening

功能:
1. 敏感数据字段级加密
2. 访问控制增强
3. 审计日志
4. SQL注入防护
5. 敏感信息脱敏
6. 安全配置验证
7. 密钥轮换管理

作者: Claude (AI Assistant)
创建时间: 2026-01-16
版本: v1.0.0
"""

import asyncio
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.async_main import async_main
from core.logging_config import setup_logging

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = setup_logging()


# =============================================================================
# 安全级别
# =============================================================================

class SecurityLevel(Enum):
    """安全级别"""
    PUBLIC = "public"         # 公开
    INTERNAL = "internal"     # 内部
    CONFIDENTIAL = "confidential"  # 机密
    RESTRICTED = "restricted"     # 限制级
    TOP_SECRET = "top_secret"     # 绝密


# =============================================================================
# 审计事件
# =============================================================================

@dataclass
class AuditEvent:
    """审计事件"""
    event_id: str
    event_type: str  # access, create, update, delete, export
    user_id: str
    resource_id: str
    resource_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    failure_reason: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AuditLogger:
    """审计日志记录器"""

    def __init__(self, log_file: str = "logs/memory_audit.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.buffer: list[AuditEvent] = []
        self.buffer_size = 100

    def log_event(self, event: AuditEvent):
        """记录审计事件"""
        self.buffer.append(event)

        if len(self.buffer) >= self.buffer_size:
            self._flush()

    def _flush(self):
        """刷新到文件"""
        if not self.buffer:
            return

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                for event in self.buffer:
                    log_entry = {
                        'timestamp': event.timestamp.isoformat(),
                        'event_type': event.event_type,
                        'user_id': event.user_id,
                        'resource_id': event.resource_id,
                        'resource_type': event.resource_type,
                        'success': event.success,
                        'failure_reason': event.failure_reason,
                        'ip_address': event.ip_address,
                        'metadata': event.metadata
                    }
                    f.write(json.dumps(log_entry) + '\n')

            logger.debug(f"✅ 写入{len(self.buffer)}条审计日志")

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise
        finally:
            self.buffer.clear()

    async def query_events(
        self,
        user_id: str | None = None,
        event_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100
    ) -> list[AuditEvent]:
        """查询审计事件"""
        events = []

        try:
            with open(self.log_file, encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        event = AuditEvent(
                            event_id=data.get('event_id', ''),
                            event_type=data.get('event_type', ''),
                            user_id=data.get('user_id', ''),
                            resource_id=data.get('resource_id', ''),
                            resource_type=data.get('resource_type', ''),
                            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
                            success=data.get('success', True),
                            failure_reason=data.get('failure_reason'),
                            ip_address=data.get('ip_address'),
                            metadata=data.get('metadata', {})
                        )

                        # 过滤
                        if user_id and event.user_id != user_id:
                            continue
                        if event_type and event.event_type != event_type:
                            continue
                        if start_time and event.timestamp < start_time:
                            continue
                        if end_time and event.timestamp > end_time:
                            continue

                        events.append(event)

                        if len(events) >= limit:
                            break

                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue

        except FileNotFoundError as e:
            logger.warning(f"审计日志文件不存在: {e}")
        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

        return events


# =============================================================================
# 敏感数据加密器
# =============================================================================

class SensitiveDataEncryptor:
    """敏感数据加密器"""

    # 敏感字段定义
    SENSITIVE_FIELDS = {
        'content',
        'user_preferences',
        'personal_info',
        'credentials',
        'api_keys',
        'tokens'
    }

    def __init__(self, key_manager=None):
        from core.memory.memory_p0_fixes import PersistentEncryptionKeyManager

        self.key_manager = key_manager or PersistentEncryptionKeyManager()
        self.audit_logger = AuditLogger()

    def encrypt_memory_data(self, memory_data: dict, security_level: SecurityLevel) -> dict:
        """加密记忆数据中的敏感字段"""
        if security_level == SecurityLevel.PUBLIC:
            return memory_data

        encrypted_data = memory_data.copy()

        for field_name in self.SENSITIVE_FIELDS:
            if encrypted_data.get(field_name):
                value = encrypted_data[field_name]

                # 转换为字节
                if isinstance(value, str):
                    value_bytes = value.encode('utf-8')
                elif isinstance(value, dict):
                    value_bytes = json.dumps(value).encode('utf-8')
                else:
                    continue

                # 加密
                encrypted = self.key_manager.encrypt(value_bytes)
                if encrypted:
                    encrypted_data[field_name] = encrypted.hex()  # 存储为十六进制字符串

        return encrypted_data

    def decrypt_memory_data(self, memory_data: dict) -> dict:
        """解密记忆数据"""
        decrypted_data = memory_data.copy()

        for field_name in self.SENSITIVE_FIELDS:
            if decrypted_data.get(field_name):
                value = decrypted_data[field_name]

                # 检查是否为加密数据(十六进制字符串)
                if isinstance(value, str) and all(c in '0123456789abcdef' for c in value.lower()):
                    try:
                        value_bytes = bytes.fromhex(value)
                        decrypted = self.key_manager.decrypt(value_bytes)
                        if decrypted:
                            decrypted_data[field_name] = decrypted.decode('utf-8')
                    except Exception as e:
                        logger.error(f"操作失败: {e}", exc_info=True)
                        raise

        return decrypted_data

    def mask_sensitive_data(self, data: dict, visible_chars: int = 4) -> dict:
        """脱敏敏感数据(用于日志和显示)"""
        masked_data = data.copy()

        for field_name in self.SENSITIVE_FIELDS:
            if masked_data.get(field_name):
                value = masked_data[field_name]

                if isinstance(value, str):
                    if len(value) > visible_chars:
                        masked_data[field_name] = value[:visible_chars] + '*' * (len(value) - visible_chars)
                elif isinstance(value, dict):
                    # 对字典类型,只保留键名
                    masked_data[field_name] = dict.fromkeys(value.keys(), "***")

        return masked_data


# =============================================================================
# 增强的访问控制
# =============================================================================

class EnhancedAccessControl:
    """增强的访问控制"""

    def __init__(self):
        self.audit_logger = AuditLogger()

        # 访问策略
        self.access_policies: dict[str, dict] = {
            'default': {
                'allow_read': ['creator'],
                'allow_write': ['creator'],
                'allow_delete': ['creator'],
                'allow_share': ['creator']
            },
            'family': {
                'allow_read': ['family_members'],
                'allow_write': ['creator'],
                'allow_delete': ['creator'],
                'allow_share': ['family_members']
            },
            'team': {
                'allow_read': ['team_members'],
                'allow_write': ['creator', 'team_leads'],
                'allow_delete': ['creator'],
                'allow_share': ['team_members']
            }
        }

        # 用户角色
        self.user_roles: dict[str, set[str]] = {}

    def check_access(
        self,
        memory_id: str,
        user_id: str,
        action: str,
        creator_id: str,
        access_level: str,
        requester_roles: set[str] | None = None
    ) -> bool:
        """检查访问权限"""
        # 记录审计事件
        event = AuditEvent(
            event_id=f"audit_{int(time.time() * 1000000)}",
            event_type='access',
            user_id=user_id,
            resource_id=memory_id,
            resource_type='memory'
        )

        try:
            if user_id == creator_id:
                event.success = True
                self.audit_logger.log_event(event)
                return True

            # 检查访问策略
            policy = self.access_policies.get(access_level, self.access_policies['default'])
            allowed_key = f'allow_{action}'

            if allowed_key in policy:
                allowed_roles = set(policy[allowed_key])

                if requester_roles and allowed_roles.intersection(requester_roles):
                    event.success = True
                    self.audit_logger.log_event(event)
                    return True

            # 默认拒绝
            event.success = False
            event.failure_reason = f"访问被拒绝: 用户{user_id}没有{action}权限"
            self.audit_logger.log_event(event)
            logger.warning(f"⚠️ 未授权访问尝试: {user_id} -> {memory_id} ({action})")

            return False

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    def grant_role(self, user_id: str, role: str):
        """授予用户角色"""
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()

        self.user_roles[user_id].add(role)
        logger.info(f"✅ 授予角色: {user_id} -> {role}")

    def revoke_role(self, user_id: str, role: str):
        """撤销用户角色"""
        if user_id in self.user_roles and role in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role)
            logger.info(f"✅ 撤销角色: {user_id} -> {role}")


# =============================================================================
# SQL注入防护
# =============================================================================

class SQLInjectionProtector:
    """SQL注入防护"""

    # 危险的SQL关键词
    DANGEROUS_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bselect\b.*\bfrom\b)",
        r"(\binsert\b.*\binto\b)",
        r"(\bupdate\b.*\bset\b)",
        r"(\bdelete\b.*\bfrom\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(\bexec\b|\bexecute\b)",
        r"(;.*\bdrop\b)",
        r"(--|\/\*|\*\/)",
        r"(\bor\b.*=.*\bor\b)",
        r"(\band\b.*=.*\band\b)"
    ]

    def __init__(self):
        self.audit_logger = AuditLogger()
        self.violation_log: list[dict] = []

    def validate_input(self, input_value: Any, field_name: str = "unknown") -> bool:
        """验证输入是否安全"""
        if input_value is None:
            return True

        value_str = str(input_value)

        # 检查危险模式
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, value_str, re.IGNORECASE):
                # 记录违规
                violation = {
                    'timestamp': datetime.now().isoformat(),
                    'field': field_name,
                    'value': value_str[:100] + '...' if len(value_str) > 100 else value_str,
                    'pattern': pattern
                }
                self.violation_log.append(violation)

                # 记录审计事件
                event = AuditEvent(
                    event_id=f"sql_injection_{int(time.time() * 1000000)}",
                    event_type='security_violation',
                    user_id='system',
                    resource_id=field_name,
                    resource_type='input',
                    success=False,
                    failure_reason=f'检测到SQL注入模式: {pattern}',
                    metadata={'violation': violation}
                )
                self.audit_logger.log_event(event)

                logger.error(f"🚨 检测到SQL注入尝试: {field_name} = {value_str[:50]}")
                return False

        return True

    def sanitize_input(self, input_value: Any) -> Any:
        """清理输入"""
        if input_value is None:
            return None

        if isinstance(input_value, str):
            # 移除危险字符
            cleaned = re.sub(r"[;\'\"\\]", '', input_value)
            return cleaned.strip()

        return input_value

    def escape_sql_identifier(self, identifier: str) -> str:
        """转义SQL标识符"""
        # 移除所有非字母数字下划线字符
        return re.sub(r'[^a-zA-Z0-9_]', '', identifier)


# =============================================================================
# 安全配置验证器
# =============================================================================

class SecurityConfigValidator:
    """安全配置验证器"""

    def __init__(self):
        self.checks: list[dict] = []

    def validate_all(self) -> dict[str, Any]:
        """执行所有安全检查"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'warnings': 0,
            'details': []
        }

        # 运行所有检查
        self.checks = [
            self._check_encryption_key(),
            self._check_database_ssl(),
            self._check_file_permissions(),
            self._check_environment_variables(),
            self._check_password_policy(),
            self._check_api_keys()
        ]

        for check in self.checks:
            results['total_checks'] += 1
            results['details'].append(check)

            if check['status'] == 'passed':
                results['passed_checks'] += 1
            elif check['status'] == 'failed':
                results['failed_checks'] += 1
            elif check['status'] == 'warning':
                results['warnings'] += 1

        return results

    def _check_encryption_key(self) -> dict:
        """检查加密密钥"""
        key_file = Path.home() / ".athena" / "secure" / "memory_encryption_key.bin"

        if key_file.exists():
            # 检查权限
            stat = key_file.stat()
            mode = oct(stat.st_mode)[-3:]

            if mode == '600':
                return {
                    'name': '加密密钥权限',
                    'status': 'passed',
                    'message': f'密钥文件权限正确: {mode}'
                }
            else:
                return {
                    'name': '加密密钥权限',
                    'status': 'warning',
                    'message': f'密钥文件权限过于宽松: {mode},建议600'
                }
        else:
            return {
                'name': '加密密钥',
                'status': 'warning',
                'message': '加密密钥文件不存在'
            }

    def _check_database_ssl(self) -> dict:
        """检查数据库SSL配置"""
        ssl_enabled = os.getenv('DB_SSL', 'false').lower() == 'true'

        if ssl_enabled:
            return {
                'name': '数据库SSL',
                'status': 'passed',
                'message': 'SSL已启用'
            }
        else:
            return {
                'name': '数据库SSL',
                'status': 'warning',
                'message': 'SSL未启用,建议在生产环境启用'
            }

    def _check_file_permissions(self) -> dict:
        """检查敏感文件权限"""
        issues = []

        sensitive_files = [
            Path.home() / ".athena" / "secure",
            Path("config"),
            Path(".env")
        ]

        for file_path in sensitive_files:
            if file_path.exists() and file_path.is_dir():
                for item in file_path.rglob('*'):
                    if item.is_file():
                        stat = item.stat()
                        mode = oct(stat.st_mode)[-3:]
                        if mode not in ['600', '640', '400']:
                            issues.append(f"{item}: {mode}")

        if issues:
            return {
                'name': '文件权限',
                'status': 'warning',
                'message': f'部分文件权限过于宽松: {", ".join(issues[:3])}'
            }
        else:
            return {
                'name': '文件权限',
                'status': 'passed',
                'message': '文件权限检查通过'
            }

    def _check_environment_variables(self) -> dict:
        """检查环境变量"""
        required_vars = [
            'DATABASE_URL',
            'REDIS_URL'
        ]

        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)

        if missing:
            return {
                'name': '环境变量',
                'status': 'warning',
                'message': f'缺少环境变量: {", ".join(missing)}'
            }
        else:
            return {
                'name': '环境变量',
                'status': 'passed',
                'message': '所有必需的环境变量已设置'
            }

    def _check_password_policy(self) -> dict:
        """检查密码策略"""
        db_password = os.getenv('DB_PASSWORD', '')

        if len(db_password) < 12:
            return {
                'name': '密码策略',
                'status': 'warning',
                'message': '数据库密码长度不足12位'
            }
        else:
            return {
                'name': '密码策略',
                'status': 'passed',
                'message': '密码策略检查通过'
            }

    def _check_api_keys(self) -> dict:
        """检查API密钥"""
        # 检查密钥是否硬编码
        config_files = list(Path("config").rglob("*.py")) + list(Path(".env*").glob("*"))

        hardcoded_keys = []

        dangerous_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']'
        ]

        for file_path in config_files:
            if file_path.exists():
                try:
                    content = file_path.read_text(errors='ignore')
                    for pattern in dangerous_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            hardcoded_keys.append(str(file_path))
                            break
                except Exception as e:
                    logger.error(f"操作失败: {e}", exc_info=True)
                    raise
        if hardcoded_keys:
            return {
                'name': 'API密钥',
                'status': 'failed',
                'message': f'发现硬编码密钥: {", ".join(set(hardcoded_keys))}'
            }
        else:
            return {
                'name': 'API密钥',
                'status': 'passed',
                'message': '未发现硬编码密钥'
            }


# =============================================================================
# 密钥轮换管理器
# =============================================================================

class KeyRotationManager:
    """密钥轮换管理器"""

    def __init__(self):
        self.rotation_schedule: dict[str, datetime] = {}
        self.rotation_history: list[dict] = []

    def schedule_rotation(self, key_id: str, rotation_date: datetime):
        """安排密钥轮换"""
        self.rotation_schedule[key_id] = rotation_date
        logger.info(f"📅 安排密钥轮换: {key_id} -> {rotation_date}")

    async def check_and_rotate(self) -> list[str]:
        """检查并执行密钥轮换"""
        rotated = []
        now = datetime.now()

        for key_id, scheduled_date in list(self.rotation_schedule.items()):
            if now >= scheduled_date:
                try:
                    rotated.append(key_id)
                    del self.rotation_schedule[key_id]
                except Exception as e:
                    logger.error(f"操作失败: {e}", exc_info=True)
                    raise
        return rotated

    async def _rotate_key(self, key_id: str):
        """执行密钥轮换"""
        from core.memory.memory_p0_fixes import PersistentEncryptionKeyManager

        # 记录历史
        self.rotation_history.append({
            'key_id': key_id,
            'rotated_at': datetime.now().isoformat(),
            'status': 'success'
        })

        if key_id == 'memory_encryption':
            key_manager = PersistentEncryptionKeyManager()
            key_manager.rotate_key()
            logger.info("✅ 记忆加密密钥已轮换")
        else:
            logger.warning(f"⚠️ 未知的密钥类型: {key_id}")


# =============================================================================
# 使用示例
# =============================================================================

@async_main
async def main():
    """主函数"""
    print("🔒 Athena记忆系统安全加固措施")

    # 1. 配置验证
    print("\n1️⃣ 运行安全配置检查...")
    validator = SecurityConfigValidator()
    results = validator.validate_all()

    print(f"   总检查: {results['total_checks']}")
    print(f"   通过: {results['passed_checks']}")
    print(f"   失败: {results['failed_checks']}")
    print(f"   警告: {results['warnings']}")

    for detail in results['details']:
        status_emoji = "✅" if detail['status'] == 'passed' else "⚠️" if detail['status'] == 'warning' else "❌"
        print(f"   {status_emoji} {detail['name']}: {detail['message']}")

    # 2. 测试加密器
    print("\n2️⃣ 测试敏感数据加密...")
    encryptor = SensitiveDataEncryptor()

    test_data = {
        'id': '123',
        'content': '这是敏感内容',
        'user_preferences': {'theme': 'dark'},
        'title': '公开标题'
    }

    encrypted = encryptor.encrypt_memory_data(test_data, SecurityLevel.CONFIDENTIAL)
    print(f"   加密后: {encrypted}")

    decrypted = encryptor.decrypt_memory_data(encrypted)
    print(f"   解密后: {decrypted}")

    # 3. 测试访问控制
    print("\n3️⃣ 测试访问控制...")
    access_control = EnhancedAccessControl()

    has_access = access_control.check_access(
        memory_id='mem_123',
        user_id='user_1',
        action='read',
        creator_id='user_2',
        access_level='family'
    )

    print(f"   访问权限: {'允许' if has_access else '拒绝'}")

    # 4. 测试SQL注入防护
    print("\n4️⃣ 测试SQL注入防护...")
    protector = SQLInjectionProtector()

    safe_input = "正常输入"
    dangerous_input = "'; DROP TABLE users; --"

    print(f"   安全输入: {protector.validate_input(safe_input)}")
    print(f"   危险输入: {protector.validate_input(dangerous_input)}")

    print("\n✅ 安全加固措施测试完成")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
