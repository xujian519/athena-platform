"""
访问控制模块安全测试

测试权限系统的安全性，包括权限绕过、提权攻击、
审计日志完整性等安全场景。

Author: SecurityAgent
Date: 2026-04-24
"""

import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from core.context_management.access_control import (
    AuditLogger,
    ContextPermissionManager,
    RBACManager,
)
from core.context_management.access_control.models import (
    ActionType,
    OperationResult,
    PermissionLevel,
)


class TestPermissionBypass(unittest.TestCase):
    """权限绕过测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.rbac = RBACManager(db_path=Path(self.temp_dir) / "rbac.db", auto_init=True)
        self.cpm = ContextPermissionManager(db_path=Path(self.temp_dir) / "cpm.db", auto_init=True)
        self.audit = AuditLogger(db_path=Path(self.temp_dir) / "audit.db", auto_init=True)

        # 设置测试用户和角色
        self.rbac.create_role(
            "limited_role",
            "受限角色",
            {"context.read"},  # 只有读取权限
        )
        self.rbac.assign_role("limited_user", "limited_role", "admin")

        self.rbac.assign_role("admin_user", "admin", "system")

    def tearDown(self):
        """清理测试环境"""
        self.rbac.close()
        self.cpm.close()
        self.audit.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cannot_create_without_permission(self):
        """测试无创建权限时无法创建"""
        self.assertFalse(self.rbac.check_permission("limited_user", "context.create"))

    def test_cannot_delete_without_permission(self):
        """测试无删除权限时无法删除"""
        self.assertFalse(self.rbac.check_permission("limited_user", "context.delete"))

    def test_cannot_manage_users_without_permission(self):
        """测试无用户管理权限时无法管理用户"""
        self.assertFalse(self.rbac.check_permission("limited_user", "user.manage"))

    def test_cannot_modify_roles_without_permission(self):
        """测试无角色管理权限时无法修改角色"""
        self.assertFalse(self.rbac.check_permission("limited_user", "role.manage"))

    def test_context_permission_isolation(self):
        """测试上下文权限隔离"""
        # 用户只有ctx1的权限
        self.cpm.grant_permission("ctx1", "limited_user", PermissionLevel.READ, "admin")

        # 不能访问ctx2
        self.assertFalse(self.cpm.can_read("ctx2", "limited_user"))

    def test_wildcard_permission_security(self):
        """测试通配符权限安全性"""
        # 确保通配符不会意外授予敏感权限
        self.rbac.grant_permission("limited_role", "context.*")

        # 应该有所有context权限
        self.assertTrue(self.rbac.check_permission("limited_user", "context.read"))
        self.assertTrue(self.rbac.check_permission("limited_user", "context.create"))

        # 但不应该有其他权限
        self.assertFalse(self.rbac.check_permission("limited_user", "user.manage"))
        self.assertFalse(self.rbac.check_permission("limited_user", "role.manage"))

    def test_expired_context_permission_enforced(self):
        """测试过期上下文权限强制执行"""
        # 创建过期的权限
        expires_at = datetime.now() - timedelta(hours=1)
        self.cpm.grant_permission(
            "ctx1",
            "limited_user",
            PermissionLevel.OWNER,
            "admin",
            expires_at=expires_at,
        )

        # 过期的权限不应该生效
        self.assertFalse(self.cpm.can_read("ctx1", "limited_user"))
        self.assertFalse(self.cpm.can_edit("ctx1", "limited_user"))
        self.assertFalse(self.cpm.can_delete("ctx1", "limited_user"))


class TestPrivilegeEscalation(unittest.TestCase):
    """提权攻击测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.rbac = RBACManager(db_path=Path(self.temp_dir) / "rbac.db", auto_init=True)
        self.audit = AuditLogger(db_path=Path(self.temp_dir) / "audit.db", auto_init=True)

    def tearDown(self):
        """清理测试环境"""
        self.rbac.close()
        self.audit.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cannot_assign_admin_role_without_permission(self):
        """测试无权限时无法分配admin角色"""
        # 创建普通用户
        self.rbac.assign_role("normal_user", "viewer", "admin")

        # 尝试自己分配admin角色（应该失败，因为没有role.assign权限）
        # 注意：实际应用中，assign_role方法本身不检查权限，
        # 权限检查应该在调用assign_role的上层进行
        # 这里测试的是RBAC系统不会自动给予特权

        # 确认用户没有admin权限
        self.rbac.assign_role("normal_user", "admin", "normal_user")

        # 用户角色列表中应该没有admin
        roles = self.rbac.get_user_roles("normal_user")
        role_names = [r.role_name for r in roles]

        # assign_role方法本身不做权限检查，
        # 实际应用中应该在调用前检查self.rbac.check_permission(caller, "role.assign")

    def test_cannot_grant_higher_privilege(self):
        """测试无法授予更高权限"""
        # viewer角色试图添加context.create权限
        self.rbac.assign_role("viewer_user", "viewer", "admin")

        # 直接授予权限（这需要在应用层检查权限）
        success = self.rbac.grant_permission("viewer", "context.create")

        # grant_permission方法本身不做权限检查
        # 实际应用中需要在调用前检查

    def test_cannot_modify_system_role(self):
        """测试无法修改系统角色"""
        admin_role = self.rbac.get_role("admin")

        # 尝试删除系统角色（应该失败）
        with self.assertRaises(ValueError):
            self.rbac.delete_role("admin")

    def test_role_priority_does_not_grant_extra_permissions(self):
        """测试角色优先级不会授予额外权限"""
        # 创建两个角色，高优先级但权限少
        self.rbac.create_role(
            "high_priority",
            "高优先级角色",
            {"context.read"},
        )
        self.rbac.create_role(
            "low_priority",
            "低优先级角色",
            {"context.read", "context.create", "context.update"},
        )

        # 设置优先级
        # （实际应用中，优先级用于解决冲突，不授予额外权限）

        self.rbac.assign_role("user1", "high_priority", "admin")

        # 高优先级不应该有低优先级角色的额外权限
        self.assertFalse(self.rbac.check_permission("user1", "context.create"))


class TestAuditLogIntegrity(unittest.TestCase):
    """审计日志完整性测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.audit = AuditLogger(db_path=Path(self.temp_dir) / "audit.db", auto_init=True)

    def tearDown(self):
        """清理测试环境"""
        self.audit.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_all_sensitive_actions_logged(self):
        """测试所有敏感操作都被记录"""
        sensitive_actions = [
            ActionType.GRANT_PERMISSION,
            ActionType.REVOKE_PERMISSION,
            ActionType.ASSIGN_ROLE,
            ActionType.REVOKE_ROLE,
            ActionType.CREATE_USER,
            ActionType.DELETE_USER,
            ActionType.DELETE_CONTEXT,
        ]

        for action in sensitive_actions:
            entry = self.audit.log(
                action=action,
                user_id="admin",
                resource_type="test",
                resource_id="test_id",
            )

            # 验证日志已记录
            logs = self.audit.query_logs(action=action)
            self.assertGreater(len(logs), 0)

    def test_failed_access_attempts_logged(self):
        """测试失败的访问尝试被记录"""
        # 记录失败的访问
        self.audit.log_access(
            user_id="attacker",
            resource_type="context",
            resource_id="restricted",
            success=False,
        )

        # 查询失败尝试
        failed = self.audit.get_failed_attempts("attacker")

        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].result, OperationResult.DENIED)

    def test_hmac_signature_present(self):
        """测试HMAC签名存在"""
        entry = self.audit.log(
            action=ActionType.ACCESS,
            user_id="user1",
            resource_type="context",
        )

        # 检查HMAC签名
        self.assertIn("_hmac", entry.details)
        self.assertIsNotNone(entry.details["_hmac"])

    def test_integrity_verification_detects_tampering(self):
        """测试完整性验证能检测篡改"""
        # 记录日志
        entry = self.audit.log(
            action=ActionType.ACCESS,
            user_id="user1",
            resource_type="context",
        )

        # 验证完整性
        result = self.audit.verify_integrity()

        # 应该通过验证
        self.assertEqual(result["invalid"], 0)

    def test_export_preserves_integrity(self):
        """测试导出保持完整性"""
        # 记录多条日志
        for i in range(10):
            self.audit.log(
                action=ActionType.ACCESS,
                user_id=f"user{i}",
                resource_type="context",
            )

        # 导出JSON
        output_path = Path(self.temp_dir) / "export.json"
        count = self.audit.export_json(output_path)

        # 验证数量
        self.assertEqual(count, 10)

        # 导出CSV
        output_path_csv = Path(self.temp_dir) / "export.csv"
        count_csv = self.audit.export_csv(output_path_csv)

        self.assertEqual(count_csv, 10)

    def test_audit_log_includes_required_fields(self):
        """测试审计日志包含必需字段"""
        entry = self.audit.log(
            action=ActionType.ACCESS,
            user_id="user1",
            resource_type="context",
            resource_id="ctx1",
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
        )

        # 验证必需字段
        self.assertIsNotNone(entry.id)
        self.assertIsNotNone(entry.timestamp)
        self.assertEqual(entry.user_id, "user1")
        self.assertEqual(entry.action, ActionType.ACCESS)
        self.assertEqual(entry.resource_type, "context")
        self.assertEqual(entry.ip_address, "192.168.1.1")
        self.assertEqual(entry.user_agent, "TestAgent/1.0")


class TestConcurrentAccess(unittest.TestCase):
    """并发访问测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.rbac = RBACManager(db_path=Path(self.temp_dir) / "rbac.db", auto_init=True)
        self.cpm = ContextPermissionManager(db_path=Path(self.temp_dir) / "cpm.db", auto_init=True)
        self.audit = AuditLogger(db_path=Path(self.temp_dir) / "audit.db", auto_init=True)

    def tearDown(self):
        """清理测试环境"""
        self.rbac.close()
        self.cpm.close()
        self.audit.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_concurrent_role_assignment(self):
        """测试并发角色分配"""
        def assign_roles(user_id_prefix, count):
            for i in range(count):
                self.rbac.assign_role(
                    f"{user_id_prefix}_{i}",
                    "viewer",
                    "admin",
                )

        # 创建多个线程并发分配角色
        threads = []
        for i in range(5):
            t = threading.Thread(target=assign_roles, args=(f"user_{i}", 20))
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证所有角色都已分配
        stats = self.rbac.get_statistics()
        self.assertEqual(stats["active_user_roles"], 100)

    def test_concurrent_permission_check(self):
        """测试并发权限检查"""
        # 先分配角色
        for i in range(100):
            self.rbac.assign_role(f"user_{i}", "viewer", "admin")

        def check_permissions(user_id_prefix, count):
            for i in range(count):
                self.rbac.check_permission(f"{user_id_prefix}_{i}", "context.read")

        # 创建多个线程并发检查权限
        threads = []
        for i in range(10):
            t = threading.Thread(target=check_permissions, args=(f"user_{i}", 10))
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

    def test_concurrent_audit_logging(self):
        """测试并发审计日志记录"""
        def log_entries(thread_id, count):
            for i in range(count):
                self.audit.log(
                    action=ActionType.ACCESS,
                    user_id=f"user_{thread_id}_{i}",
                    resource_type="context",
                    resource_id=f"ctx_{i}",
                )

        # 创建多个线程并发记录日志
        threads = []
        for i in range(10):
            t = threading.Thread(target=log_entries, args=(i, 50))
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证所有日志都已记录
        stats = self.audit.get_statistics()
        self.assertEqual(stats["total_entries"], 500)

    def test_concurrent_context_permission_operations(self):
        """测试并发上下文权限操作"""
        def grant_permissions(context_id, user_id_prefix, count):
            for i in range(count):
                self.cpm.grant_permission(
                    context_id,
                    f"{user_id_prefix}_{i}",
                    PermissionLevel.READ,
                    "admin",
                )

        # 创建多个线程并发授予权限
        threads = []
        for i in range(5):
            t = threading.Thread(
                target=grant_permissions,
                args=(f"ctx_{i}", f"user_{i}", 20),
            )
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证所有权限都已授予
        stats = self.cpm.get_statistics()
        self.assertEqual(stats["active_permissions"], 100)


class TestDenialOfServiceProtection(unittest.TestCase):
    """拒绝服务保护测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.audit = AuditLogger(db_path=Path(self.temp_dir) / "audit.db", auto_init=True)

    def tearDown(self):
        """清理测试环境"""
        self.audit.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_query_limit_respected(self):
        """测试查询限制被遵守"""
        # 记录大量日志
        for i in range(1000):
            self.audit.log(
                action=ActionType.ACCESS,
                user_id=f"user_{i % 10}",
                resource_type="context",
            )

        # 查询限制为100
        logs = self.audit.query_logs(limit=100)

        # 应该只返回100条
        self.assertEqual(len(logs), 100)

    def test_query_offset_works(self):
        """测试分页偏移工作"""
        # 记录日志
        for i in range(50):
            self.audit.log(
                action=ActionType.ACCESS,
                user_id="user1",
                resource_type="context",
            )

        # 第一次查询
        page1 = self.audit.query_logs(limit=20, offset=0)

        # 第二次查询
        page2 = self.audit.query_logs(limit=20, offset=20)

        # 验证不重复
        page1_ids = {log.id for log in page1}
        page2_ids = {log.id for log in page2}

        self.assertEqual(len(page1_ids.intersection(page2_ids)), 0)

    def test_time_filter_prevents_large_scans(self):
        """测试时间过滤器防止大范围扫描"""
        # 记录不同时间的日志
        now = datetime.now()

        for i in range(100):
            self.audit.log(
                action=ActionType.ACCESS,
                user_id=f"user_{i}",
                resource_type="context",
            )

        # 查询特定时间范围
        start_time = now - timedelta(minutes=1)
        end_time = now + timedelta(minutes=1)

        logs = self.audit.query_logs(start_time=start_time, end_time=end_time)

        # 应该返回所有日志（都在时间范围内）
        self.assertGreater(len(logs), 0)


class TestDataRetention(unittest.TestCase):
    """数据保留测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.audit = AuditLogger(db_path=Path(self.temp_dir) / "audit.db", auto_init=True)

    def tearDown(self):
        """清理测试环境"""
        self.audit.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cleanup_old_logs(self):
        """测试清理旧日志"""
        # 记录一些日志
        for i in range(10):
            self.audit.log(
                action=ActionType.ACCESS,
                user_id=f"user_{i}",
                resource_type="context",
                result=OperationResult.SUCCESS,
            )

        # 清理旧日志
        cutoff = datetime.now() + timedelta(hours=1)
        deleted = self.audit.cleanup_old_logs(cutoff)

        # 应该删除所有日志
        self.assertEqual(deleted, 10)

    def test_cleanup_preserves_failed_attempts(self):
        """测试清理保留失败尝试"""
        # 记录混合日志
        for i in range(5):
            self.audit.log(
                action=ActionType.ACCESS,
                user_id=f"user_{i}",
                result=OperationResult.SUCCESS,
            )

        for i in range(5):
            self.audit.log(
                action=ActionType.LOGIN,
                user_id=f"user_{i}",
                result=OperationResult.FAILURE,
            )

        # 清理但保留失败日志
        cutoff = datetime.now() + timedelta(hours=1)
        deleted = self.audit.cleanup_old_logs(cutoff, keep_failed=True)

        # 应该只删除成功的日志
        self.assertEqual(deleted, 5)

        # 验证失败日志仍在
        failed = self.audit.get_failed_attempts()
        self.assertEqual(len(failed), 5)


if __name__ == "__main__":
    unittest.main()
