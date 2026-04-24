"""
访问控制模块单元测试

测试RBAC管理器、上下文权限管理器和审计日志管理器的功能。

Author: SecurityAgent
Date: 2026-04-24
"""

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from core.context_management.access_control import (
    AuditLogger,
    ContextPermissionManager,
    RBACManager,
    SystemRoles,
)
from core.context_management.access_control.models import (
    ActionType,
    AuditLogEntry,
    ContextPermission,
    OperationResult,
    Permission,
    PermissionLevel,
    Role,
)


class TestRBACManager(unittest.TestCase):
    """RBAC管理器测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_rbac.db"
        self.rbac = RBACManager(db_path=self.db_path, auto_init=True)

    def tearDown(self):
        """清理测试环境"""
        self.rbac.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_system_roles_initialized(self):
        """测试系统角色初始化"""
        roles = self.rbac.list_roles()

        # 应该有5个系统角色
        system_roles = [r for r in roles if r.is_system_role]
        self.assertEqual(len(system_roles), 5)

        # 检查角色名称
        role_names = {r.name for r in system_roles}
        self.assertIn("admin", role_names)
        self.assertIn("moderator", role_names)
        self.assertIn("editor", role_names)
        self.assertIn("viewer", role_names)
        self.assertIn("guest", role_names)

    def test_create_role(self):
        """测试创建角色"""
        role = self.rbac.create_role(
            role="custom_role",
            description="自定义角色",
            permissions={"context.read", "context.create"},
        )

        self.assertEqual(role.name, "custom_role")
        self.assertEqual(role.description, "自定义角色")
        self.assertIn("context.read", role.permissions)

    def test_create_duplicate_role_raises_error(self):
        """测试创建重复角色抛出错误"""
        self.rbac.create_role("duplicate_role")

        with self.assertRaises(ValueError):
            self.rbac.create_role("duplicate_role")

    def test_get_role(self):
        """测试获取角色"""
        role = self.rbac.get_role("admin")

        self.assertIsNotNone(role)
        self.assertEqual(role.name, "admin")
        self.assertTrue(role.is_system_role)
        self.assertIn("context.create", role.permissions)

    def test_grant_permission(self):
        """测试授予权限"""
        success = self.rbac.grant_permission("viewer", "context.create")

        self.assertTrue(success)

        role = self.rbac.get_role("viewer")
        self.assertIn("context.create", role.permissions)

    def test_revoke_permission(self):
        """测试撤销权限"""
        success = self.rbac.revoke_permission("admin", "context.create")

        self.assertTrue(success)

        role = self.rbac.get_role("admin")
        self.assertNotIn("context.create", role.permissions)

    def test_assign_role(self):
        """测试分配角色"""
        ur = self.rbac.assign_role("user123", "editor", "admin")

        self.assertEqual(ur.user_id, "user123")
        self.assertEqual(ur.role_name, "editor")
        self.assertEqual(ur.granted_by, "admin")

    def test_get_user_roles(self):
        """测试获取用户角色"""
        self.rbac.assign_role("user123", "editor", "admin")
        self.rbac.assign_role("user123", "viewer", "admin")

        roles = self.rbac.get_user_roles("user123")

        self.assertEqual(len(roles), 2)
        role_names = {r.role_name for r in roles}
        self.assertIn("editor", role_names)
        self.assertIn("viewer", role_names)

    def test_check_permission(self):
        """测试权限检查"""
        self.rbac.assign_role("user123", "admin", "admin")

        # Admin应该有所有权限
        self.assertTrue(self.rbac.check_permission("user123", "context.create"))
        self.assertTrue(self.rbac.check_permission("user123", "user.manage"))

    def test_check_permission_with_wildcard(self):
        """测试通配符权限检查"""
        # 为viewer添加通配符权限
        self.rbac.grant_permission("viewer", "context.*")
        self.rbac.assign_role("user123", "viewer", "admin")

        self.assertTrue(self.rbac.check_permission("user123", "context.read"))
        self.assertTrue(self.rbac.check_permission("user123", "context.create"))

    def test_revoke_role(self):
        """测试撤销角色"""
        self.rbac.assign_role("user123", "editor", "admin")

        success = self.rbac.revoke_role("user123", "editor")

        self.assertTrue(success)

        roles = self.rbac.get_user_roles("user123")
        self.assertEqual(len(roles), 0)

    def test_get_statistics(self):
        """测试获取统计信息"""
        stats = self.rbac.get_statistics()

        self.assertIn("total_roles", stats)
        self.assertIn("system_roles", stats)
        self.assertGreater(stats["total_roles"], 0)

    def test_delete_custom_role(self):
        """测试删除自定义角色"""
        self.rbac.create_role("temp_role")

        success = self.rbac.delete_role("temp_role")

        self.assertTrue(success)
        self.assertIsNone(self.rbac.get_role("temp_role"))

    def test_delete_system_role_raises_error(self):
        """测试删除系统角色抛出错误"""
        with self.assertRaises(ValueError):
            self.rbac.delete_role("admin")


class TestContextPermissionManager(unittest.TestCase):
    """上下文权限管理器测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_context_perm.db"
        self.cpm = ContextPermissionManager(db_path=self.db_path, auto_init=True)

    def tearDown(self):
        """清理测试环境"""
        self.cpm.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_grant_permission(self):
        """测试授予权限"""
        cp = self.cpm.grant_permission(
            context_id="ctx1",
            user_id="user1",
            level=PermissionLevel.OWNER,
            granted_by="admin",
        )

        self.assertEqual(cp.context_id, "ctx1")
        self.assertEqual(cp.user_id, "user1")
        self.assertEqual(cp.level, PermissionLevel.OWNER)

    def test_get_permission(self):
        """测试获取权限"""
        self.cpm.grant_permission(
            context_id="ctx1",
            user_id="user1",
            level=PermissionLevel.READ,
            granted_by="admin",
        )

        cp = self.cpm.get_permission("ctx1", "user1")

        self.assertIsNotNone(cp)
        self.assertEqual(cp.level, PermissionLevel.READ)

    def test_check_access_read(self):
        """测试读取权限检查"""
        self.cpm.grant_permission(
            context_id="ctx1",
            user_id="user1",
            level=PermissionLevel.READ,
            granted_by="admin",
        )

        self.assertTrue(self.cpm.can_read("ctx1", "user1"))
        self.assertFalse(self.cpm.can_edit("ctx1", "user1"))
        self.assertFalse(self.cpm.can_delete("ctx1", "user1"))

    def test_check_access_edit(self):
        """测试编辑权限检查"""
        self.cpm.grant_permission(
            context_id="ctx1",
            user_id="user1",
            level=PermissionLevel.EDIT,
            granted_by="admin",
        )

        self.assertTrue(self.cpm.can_read("ctx1", "user1"))
        self.assertTrue(self.cpm.can_edit("ctx1", "user1"))
        self.assertFalse(self.cpm.can_delete("ctx1", "user1"))

    def test_check_access_owner(self):
        """测试所有者权限检查"""
        self.cpm.grant_permission(
            context_id="ctx1",
            user_id="user1",
            level=PermissionLevel.OWNER,
            granted_by="admin",
        )

        self.assertTrue(self.cpm.can_read("ctx1", "user1"))
        self.assertTrue(self.cpm.can_edit("ctx1", "user1"))
        self.assertTrue(self.cpm.can_delete("ctx1", "user1"))

    def test_revoke_permission(self):
        """测试撤销权限"""
        self.cpm.grant_permission(
            context_id="ctx1",
            user_id="user1",
            level=PermissionLevel.READ,
            granted_by="admin",
        )

        success = self.cpm.revoke_permission("ctx1", "user1")

        self.assertTrue(success)
        self.assertIsNone(self.cpm.get_permission("ctx1", "user1"))

    def test_get_context_permissions(self):
        """测试获取上下文所有权限"""
        self.cpm.grant_permission("ctx1", "user1", PermissionLevel.OWNER, "admin")
        self.cpm.grant_permission("ctx1", "user2", PermissionLevel.READ, "admin")
        self.cpm.grant_permission("ctx1", "user3", PermissionLevel.EDIT, "admin")

        permissions = self.cpm.get_context_permissions("ctx1")

        self.assertEqual(len(permissions), 3)

    def test_get_user_contexts(self):
        """测试获取用户上下文"""
        self.cpm.grant_permission("ctx1", "user1", PermissionLevel.READ, "admin")
        self.cpm.grant_permission("ctx2", "user1", PermissionLevel.EDIT, "admin")
        self.cpm.grant_permission("ctx3", "user1", PermissionLevel.OWNER, "admin")

        contexts = self.cpm.get_user_contexts("user1")

        self.assertEqual(len(contexts), 3)
        self.assertIn("ctx1", contexts)
        self.assertIn("ctx2", contexts)
        self.assertIn("ctx3", contexts)

    def test_get_user_contexts_with_min_level(self):
        """测试获取用户上下文（最低级别）"""
        self.cpm.grant_permission("ctx1", "user1", PermissionLevel.READ, "admin")
        self.cpm.grant_permission("ctx2", "user1", PermissionLevel.EDIT, "admin")
        self.cpm.grant_permission("ctx3", "user1", PermissionLevel.READ, "admin")

        contexts = self.cpm.get_user_contexts("user1", min_level=PermissionLevel.EDIT)

        self.assertEqual(len(contexts), 1)
        self.assertIn("ctx2", contexts)

    def test_get_context_owner(self):
        """测试获取上下文所有者"""
        self.cpm.grant_permission("ctx1", "user1", PermissionLevel.OWNER, "admin")

        owner = self.cpm.get_context_owner("ctx1")

        self.assertEqual(owner, "user1")

    def test_grant_batch(self):
        """测试批量授予权限"""
        permissions = self.cpm.grant_batch(
            context_id="ctx1",
            user_ids=["user1", "user2", "user3"],
            level=PermissionLevel.READ,
            granted_by="admin",
        )

        self.assertEqual(len(permissions), 3)

    def test_expired_permission(self):
        """测试过期权限"""
        # 使用utcnow与代码保持一致
        expires_at = datetime.utcnow() - timedelta(hours=1)

        self.cpm.grant_permission(
            context_id="ctx1",
            user_id="user1",
            level=PermissionLevel.READ,
            granted_by="admin",
            expires_at=expires_at,
        )

        # 过期的权限不应通过访问检查
        self.assertFalse(self.cpm.can_read("ctx1", "user1"))

    def test_get_statistics(self):
        """测试获取统计信息"""
        stats = self.cpm.get_statistics()

        self.assertIn("total_permissions", stats)
        self.assertIn("total_contexts", stats)
        self.assertIn("total_users", stats)


class TestAuditLogger(unittest.TestCase):
    """审计日志管理器测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_audit.db"
        self.audit = AuditLogger(db_path=self.db_path, auto_init=True)

    def tearDown(self):
        """清理测试环境"""
        self.audit.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_basic(self):
        """测试基本日志记录"""
        entry = self.audit.log(
            action=ActionType.ACCESS,
            user_id="user1",
            resource_type="context",
            resource_id="ctx1",
            result=OperationResult.SUCCESS,
        )

        self.assertIsNotNone(entry)
        self.assertEqual(entry.user_id, "user1")
        self.assertEqual(entry.action, ActionType.ACCESS)

    def test_log_access(self):
        """测试记录访问"""
        entry = self.audit.log_access(
            user_id="user1",
            resource_type="context",
            resource_id="ctx1",
            success=True,
        )

        self.assertEqual(entry.action, ActionType.ACCESS)
        self.assertEqual(entry.result, OperationResult.SUCCESS)

    def test_log_permission_change(self):
        """测试记录权限变更"""
        entry = self.audit.log_permission_change(
            user_id="admin",
            target_user_id="user1",
            permission="context.read",
            granted=True,
        )

        self.assertEqual(entry.action, ActionType.GRANT_PERMISSION)
        self.assertEqual(entry.details["target_user_id"], "user1")
        self.assertEqual(entry.details["change_type"], "grant")

    def test_query_logs_by_user(self):
        """测试按用户查询日志"""
        self.audit.log(ActionType.ACCESS, user_id="user1", resource_type="context")
        self.audit.log(ActionType.CREATE_CONTEXT, user_id="user1", resource_type="context")
        self.audit.log(ActionType.ACCESS, user_id="user2", resource_type="context")

        logs = self.audit.query_logs(user_id="user1")

        self.assertEqual(len(logs), 2)

    def test_query_logs_by_action(self):
        """测试按操作类型查询日志"""
        self.audit.log(ActionType.ACCESS, user_id="user1", resource_type="context")
        self.audit.log(ActionType.CREATE_CONTEXT, user_id="user1", resource_type="context")
        self.audit.log(ActionType.ACCESS, user_id="user2", resource_type="context")

        logs = self.audit.query_logs(action=ActionType.ACCESS)

        self.assertEqual(len(logs), 2)

    def test_query_logs_by_result(self):
        """测试按结果查询日志"""
        self.audit.log(ActionType.ACCESS, user_id="user1", result=OperationResult.SUCCESS)
        self.audit.log(ActionType.ACCESS, user_id="user1", result=OperationResult.DENIED)
        self.audit.log(ActionType.ACCESS, user_id="user1", result=OperationResult.SUCCESS)

        logs = self.audit.query_logs(result=OperationResult.DENIED)

        self.assertEqual(len(logs), 1)

    def test_get_user_activity(self):
        """测试获取用户活动"""
        self.audit.log(ActionType.ACCESS, user_id="user1", resource_type="context")
        self.audit.log(ActionType.CREATE_CONTEXT, user_id="user1", resource_type="context")

        activity = self.audit.get_user_activity("user1")

        self.assertEqual(len(activity), 2)

    def test_get_resource_history(self):
        """测试获取资源历史"""
        self.audit.log(ActionType.UPDATE_CONTEXT, resource_type="context", resource_id="ctx1")
        self.audit.log(ActionType.READ_CONTEXT, resource_type="context", resource_id="ctx1")
        self.audit.log(ActionType.UPDATE_CONTEXT, resource_type="context", resource_id="ctx2")

        history = self.audit.get_resource_history("context", "ctx1")

        self.assertEqual(len(history), 2)

    def test_get_failed_attempts(self):
        """测试获取失败尝试"""
        self.audit.log(ActionType.ACCESS, user_id="user1", result=OperationResult.SUCCESS)
        self.audit.log(ActionType.LOGIN, user_id="user1", result=OperationResult.FAILURE)
        self.audit.log(ActionType.LOGIN, user_id="user1", result=OperationResult.FAILURE)

        failed = self.audit.get_failed_attempts("user1")

        self.assertEqual(len(failed), 2)

    def test_export_json(self):
        """测试JSON导出"""
        self.audit.log(ActionType.ACCESS, user_id="user1", resource_type="context")
        self.audit.log(ActionType.CREATE_CONTEXT, user_id="user1", resource_type="context")

        output_path = Path(self.temp_dir) / "export.json"
        count = self.audit.export_json(output_path)

        self.assertEqual(count, 2)
        self.assertTrue(output_path.exists())

    def test_export_csv(self):
        """测试CSV导出"""
        self.audit.log(ActionType.ACCESS, user_id="user1", resource_type="context")
        self.audit.log(ActionType.CREATE_CONTEXT, user_id="user1", resource_type="context")

        output_path = Path(self.temp_dir) / "export.csv"
        count = self.audit.export_csv(output_path)

        self.assertEqual(count, 2)
        self.assertTrue(output_path.exists())

    def test_verify_integrity(self):
        """测试完整性验证"""
        self.audit.log(ActionType.ACCESS, user_id="user1", resource_type="context")

        result = self.audit.verify_integrity()

        self.assertEqual(result["invalid"], 0)
        self.assertEqual(result["integrity_rate"], 1.0)

    def test_get_statistics(self):
        """测试获取统计信息"""
        self.audit.log(ActionType.ACCESS, user_id="user1", result=OperationResult.SUCCESS)
        self.audit.log(ActionType.LOGIN, user_id="user1", result=OperationResult.FAILURE)

        stats = self.audit.get_statistics()

        self.assertIn("total_entries", stats)
        self.assertIn("by_action", stats)
        self.assertIn("by_result", stats)
        self.assertGreater(stats["total_entries"], 0)


class TestPermissionModel(unittest.TestCase):
    """权限模型测试"""

    def test_permission_matches_exact(self):
        """测试精确匹配"""
        perm = Permission("context.read")

        self.assertTrue(perm.matches("context.read"))
        self.assertFalse(perm.matches("context.write"))

    def test_permission_matches_wildcard_resource(self):
        """测试通配符资源匹配"""
        perm = Permission("context.read")

        self.assertTrue(perm.matches("*.read"))
        self.assertFalse(perm.matches("*.write"))

    def test_permission_matches_wildcard_action(self):
        """测试通配符操作匹配"""
        perm = Permission("context.read")

        self.assertTrue(perm.matches("context.*"))
        self.assertFalse(perm.matches("user.*"))

    def test_permission_matches_double_wildcard(self):
        """测试双通配符匹配"""
        perm = Permission("context.read")

        self.assertTrue(perm.matches("*"))

    def test_permission_invalid_format_raises_error(self):
        """测试无效格式抛出错误"""
        with self.assertRaises(ValueError):
            Permission("invalid_format")


class TestRoleModel(unittest.TestCase):
    """角色模型测试"""

    def test_role_add_permission(self):
        """测试添加权限"""
        role = Role(name="test", permissions=set())

        role.add_permission("context.read")
        role.add_permission(Permission("context.write"))

        self.assertIn("context.read", role.permissions)
        self.assertIn("context.write", role.permissions)

    def test_role_has_permission(self):
        """测试检查权限"""
        role = Role(name="test", permissions={"context.read", "context.write"})

        self.assertTrue(role.has_permission("context.read"))
        self.assertTrue(role.has_permission(Permission("context.write")))
        self.assertFalse(role.has_permission("context.delete"))

    def test_role_matches_permission_wildcard(self):
        """测试通配符权限匹配"""
        role = Role(name="test", permissions={"context.*", "user.manage"})

        self.assertTrue(role.matches_permission("context.read"))
        self.assertTrue(role.matches_permission("context.write"))
        self.assertTrue(role.matches_permission("context.delete"))
        self.assertFalse(role.matches_permission("user.read"))

    def test_role_priority_comparison(self):
        """测试角色优先级"""
        admin = SystemRoles.admin()
        viewer = SystemRoles.viewer()

        self.assertGreater(admin.priority, viewer.priority)


class TestContextPermissionModel(unittest.TestCase):
    """上下文权限模型测试"""

    def test_owner_permissions(self):
        """测试所有者权限"""
        from datetime import datetime

        cp = ContextPermission(
            context_id="ctx1",
            user_id="user1",
            level=PermissionLevel.OWNER,
            granted_by="admin",
        )

        self.assertTrue(cp.can_read())
        self.assertTrue(cp.can_edit())
        self.assertTrue(cp.can_delete())

    def test_edit_permissions(self):
        """测试编辑权限"""
        cp = ContextPermission(
            context_id="ctx1",
            user_id="user1",
            level=PermissionLevel.EDIT,
            granted_by="admin",
        )

        self.assertTrue(cp.can_read())
        self.assertTrue(cp.can_edit())
        self.assertFalse(cp.can_delete())

    def test_read_permissions(self):
        """测试读取权限"""
        cp = ContextPermission(
            context_id="ctx1",
            user_id="user1",
            level=PermissionLevel.READ,
            granted_by="admin",
        )

        self.assertTrue(cp.can_read())
        self.assertFalse(cp.can_edit())
        self.assertFalse(cp.can_delete())

    def test_expired_permission(self):
        """测试过期权限"""
        expires_at = datetime.utcnow() - timedelta(hours=1)

        cp = ContextPermission(
            context_id="ctx1",
            user_id="user1",
            level=PermissionLevel.READ,
            granted_by="admin",
            expires_at=expires_at,
        )

        self.assertTrue(cp.is_expired())
        self.assertFalse(cp.can_read())

    def test_inactive_permission(self):
        """测试非激活权限"""
        cp = ContextPermission(
            context_id="ctx1",
            user_id="user1",
            level=PermissionLevel.READ,
            granted_by="admin",
            is_active=False,
        )

        self.assertFalse(cp.can_read())


class TestIntegration(unittest.TestCase):
    """集成测试"""

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

    def test_complete_access_control_workflow(self):
        """测试完整访问控制流程"""
        # 1. 创建自定义角色
        role = self.rbac.create_role(
            role="content_creator",
            description="内容创作者",
            permissions={"context.create", "context.read", "context.update"},
        )

        # 2. 分配角色给用户
        ur = self.rbac.assign_role("user123", "content_creator", "admin")

        # 3. 检查RBAC权限
        self.assertTrue(self.rbac.check_permission("user123", "context.create"))
        self.assertFalse(self.rbac.check_permission("user123", "context.delete"))

        # 4. 授予上下文权限
        cp = self.cpm.grant_permission(
            context_id="doc1",
            user_id="user123",
            level=PermissionLevel.OWNER,
            granted_by="admin",
        )

        # 5. 检查上下文权限
        self.assertTrue(self.cpm.can_read("doc1", "user123"))
        self.assertTrue(self.cpm.can_edit("doc1", "user123"))
        self.assertTrue(self.cpm.can_delete("doc1", "user123"))

        # 6. 记录审计日志
        entry = self.audit.log(
            action=ActionType.GRANT_PERMISSION,
            user_id="admin",
            resource_type="context_permission",
            resource_id="doc1",
            details={"target_user": "user123", "level": "owner"},
        )

        # 7. 验证审计日志
        logs = self.audit.query_logs(user_id="admin")
        self.assertGreater(len(logs), 0)

    def test_permission_denied_workflow(self):
        """测试权限拒绝流程"""
        # 创建只有读取权限的用户
        self.rbac.assign_role("user_readonly", "viewer", "admin")

        # 检查权限
        self.assertTrue(self.rbac.check_permission("user_readonly", "context.read"))
        self.assertFalse(self.rbac.check_permission("user_readonly", "context.create"))

        # 记录拒绝的访问
        entry = self.audit.log_access(
            user_id="user_readonly",
            resource_type="context",
            resource_id="ctx1",
            success=False,
        )

        self.assertEqual(entry.result, OperationResult.DENIED)

    def test_role_revocation_workflow(self):
        """测试角色撤销流程"""
        # 分配角色
        self.rbac.assign_role("user123", "editor", "admin")

        # 验证权限
        self.assertTrue(self.rbac.check_permission("user123", "context.create"))

        # 撤销角色
        self.rbac.revoke_role("user123", "editor")

        # 验证权限已移除
        self.assertFalse(self.rbac.check_permission("user123", "context.create"))

        # 记录撤销操作
        self.audit.log(
            action=ActionType.REVOKE_ROLE,
            user_id="admin",
            resource_type="user_role",
            resource_id="user123",
            details={"revoked_role": "editor"},
        )


if __name__ == "__main__":
    unittest.main()
