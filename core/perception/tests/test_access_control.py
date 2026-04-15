#!/usr/bin/env python3
from __future__ import annotations
"""
测试：权限控制系统
Test: Access Control System
"""

import sys
from pathlib import Path

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.perception.access_control import (
    AccessControl,
    Permission,
    PermissionDenied,
    Role,
    User,
    get_global_access_control,
    require_permission,
)


class TestPermission:
    """测试权限枚举"""

    def test_permission_values(self):
        """测试权限值"""
        assert Permission.READ.value == "read"
        assert Permission.WRITE.value == "write"
        assert Permission.DELETE.value == "delete"
        assert Permission.PROCESS_TEXT.value == "process_text"
        assert Permission.PROCESS_IMAGE.value == "process_image"


class TestRole:
    """测试角色枚举"""

    def test_role_values(self):
        """测试角色值"""
        assert Role.ADMIN.value == "admin"
        assert Role.USER.value == "user"
        assert Role.GUEST.value == "guest"
        assert Role.SERVICE.value == "service"


class TestUser:
    """测试用户类"""

    def test_create_user(self):
        """测试创建用户"""
        user = User(user_id="test_user", username="Test User", role=Role.USER)
        assert user.user_id == "test_user"
        assert user.role == Role.USER
        assert user.permissions == set()

    def test_user_with_permissions(self):
        """测试带权限的用户"""
        user = User(
            user_id="admin_user",
            username="Admin User",
            role=Role.ADMIN,
            permissions={Permission.READ, Permission.WRITE, Permission.DELETE}
        )
        assert len(user.permissions) == 3
        assert Permission.READ in user.permissions

    def test_user_grant_permission(self):
        """测试授予权限"""
        user = User(user_id="test_user", username="Test User", role=Role.USER)
        user.add_permission(Permission.PROCESS_TEXT)
        assert Permission.PROCESS_TEXT in user.permissions
        assert user.has_permission(Permission.PROCESS_TEXT)

    def test_user_revoke_permission(self):
        """测试撤销权限"""
        user = User(
            user_id="test_user",
            username="Test User",
            role=Role.USER,
            permissions={Permission.READ, Permission.WRITE}
        )
        user.remove_permission(Permission.WRITE)
        assert Permission.READ in user.permissions
        assert Permission.WRITE not in user.permissions

    def test_user_has_permission(self):
        """测试检查权限"""
        user = User(
            user_id="test_user",
            username="Test User",
            role=Role.USER,
            permissions={Permission.READ}
        )
        assert user.has_permission(Permission.READ)
        assert not user.has_permission(Permission.DELETE)


class TestAccessControl:
    """测试访问控制类"""

    def test_create_access_control(self):
        """测试创建访问控制"""
        ac = AccessControl()
        assert ac.users == {}

    def test_register_user(self):
        """测试注册用户"""
        ac = AccessControl()
        user = User(user_id="test_user", username="Test User", role=Role.USER)
        ac.add_user(user)
        assert "test_user" in ac.users
        assert ac.users["test_user"] == user

    def test_check_permission_with_permission(self):
        """测试检查权限（有权限）"""
        ac = AccessControl()
        user = User(
            user_id="test_user",
            username="Test User",
            role=Role.USER,
            permissions={Permission.READ}
        )
        ac.add_user(user)
        assert ac.check_permission("test_user", Permission.READ)

    def test_check_permission_without_permission(self):
        """测试检查权限（无权限）"""
        ac = AccessControl()
        user = User(
            user_id="guest_user",
            username="Guest User",
            role=Role.GUEST,
            permissions={Permission.READ}
        )
        ac.add_user(user)
        assert not ac.check_permission("guest_user", Permission.DELETE)

    def test_grant_permission(self):
        """测试授予权限"""
        ac = AccessControl()
        user = User(user_id="test_user", username="Test User", role=Role.USER)
        ac.add_user(user)
        ac.grant_permission("test_user", Permission.WRITE)
        assert ac.users["test_user"].has_permission(Permission.WRITE)

    def test_revoke_permission(self):
        """测试撤销权限"""
        ac = AccessControl()
        user = User(
            user_id="test_user",
            username="Test User",
            role=Role.USER,
            permissions={Permission.READ, Permission.WRITE}
        )
        ac.add_user(user)
        ac.revoke_permission("test_user", Permission.WRITE)
        assert not ac.users["test_user"].has_permission(Permission.WRITE)

    def test_get_user(self):
        """测试获取用户"""
        ac = AccessControl()
        user = User(user_id="test_user", username="Test User", role=Role.USER)
        ac.add_user(user)
        retrieved_user = ac.get_user("test_user")
        assert retrieved_user.user_id == "test_user"
        assert retrieved_user.role == Role.USER

    def test_get_nonexistent_user(self):
        """测试获取不存在的用户"""
        ac = AccessControl()
        user = ac.get_user("nonexistent")
        assert user is None


class TestPermissionDenied:
    """测试权限拒绝异常"""

    def test_permission_denied_exception(self):
        """测试权限拒绝异常"""
        exc = PermissionDenied("Access denied")
        assert str(exc) == "Access denied"
        assert isinstance(exc, Exception)


class TestRequirePermissionDecorator:
    """测试权限装饰器"""

    def test_require_permission_with_permission(self):
        """测试有权限时调用成功"""
        ac = AccessControl()
        user = User(
            user_id="admin_user",
            username="Admin User",
            role=Role.ADMIN,
            permissions={Permission.READ, Permission.WRITE}
        )
        ac.add_user(user)

        @require_permission(Permission.READ, ac)
        def read_function():
            return "success"

        result = read_function("admin_user")
        assert result == "success"

    def test_require_permission_without_permission(self):
        """测试无权限时抛出异常"""
        ac = AccessControl()
        user = User(user_id="guest_user", username="Guest User", role=Role.GUEST, permissions={Permission.READ})
        ac.add_user(user)

        @require_permission(Permission.DELETE, ac)
        def delete_function():
            return "success"

        with pytest.raises(PermissionDenied):
            delete_function("guest_user")


class TestGlobalAccessControl:
    """测试全局访问控制"""

    def test_get_global_access_control(self):
        """测试获取全局访问控制"""
        ac = get_global_access_control()
        assert ac is not None
        assert isinstance(ac, AccessControl)

    def test_global_access_control_singleton(self):
        """测试全局访问控制是单例"""
        ac1 = get_global_access_control()
        ac2 = get_global_access_control()
        assert ac1 is ac2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
