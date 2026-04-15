#!/usr/bin/env python3
"""
访问控制系统测试
Tests for Access Control System
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.perception.access_control import (
    AccessControl,
    Permission,
    Role,
    User,
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
        assert Permission.PROCESS_AUDIO.value == "process_audio"
        assert Permission.PROCESS_VIDEO.value == "process_video"
        assert Permission.BATCH_PROCESS.value == "batch_process"
        assert Permission.STREAM_PROCESS.value == "stream_process"
        assert Permission.ACCESS_CACHE.value == "access_cache"
        assert Permission.CLEAR_CACHE.value == "clear_cache"
        assert Permission.VIEW_METRICS.value == "view_metrics"
        assert Permission.MODIFY_CONFIG.value == "modify_config"
        assert Permission.RESTART_PROCESSOR.value == "restart_processor"


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

    def test_user_creation(self):
        """测试用户创建"""
        user = User(
            user_id="123",
            username="testuser",
            role=Role.USER
        )
        assert user.user_id == "123"
        assert user.username == "testuser"
        assert user.role == Role.USER
        assert len(user.permissions) == 0

    def test_user_with_permissions(self):
        """测试带权限的用户"""
        permissions = {Permission.READ, Permission.WRITE}
        user = User(
            user_id="123",
            username="testuser",
            role=Role.USER,
            permissions=permissions
        )
        assert len(user.permissions) == 2
        assert Permission.READ in user.permissions

    def test_user_with_metadata(self):
        """测试带元数据的用户"""
        metadata = {"department": "IT", "level": 2}
        user = User(
            user_id="123",
            username="testuser",
            role=Role.USER,
            metadata=metadata
        )
        assert user.metadata["department"] == "IT"
        assert user.metadata["level"] == 2

    def test_has_permission_true(self):
        """测试有权限"""
        user = User(
            user_id="123",
            username="testuser",
            role=Role.USER,
            permissions={Permission.READ, Permission.WRITE}
        )
        assert user.has_permission(Permission.READ) is True
        assert user.has_permission(Permission.WRITE) is True

    def test_has_permission_false(self):
        """测试无权限"""
        user = User(
            user_id="123",
            username="testuser",
            role=Role.USER,
            permissions={Permission.READ}
        )
        assert user.has_permission(Permission.WRITE) is False
        assert user.has_permission(Permission.DELETE) is False

    def test_add_permission(self):
        """测试添加权限"""
        user = User(
            user_id="123",
            username="testuser",
            role=Role.USER,
            permissions={Permission.READ}
        )
        user.add_permission(Permission.WRITE)
        assert user.has_permission(Permission.WRITE) is True
        assert len(user.permissions) == 2

    def test_add_duplicate_permission(self):
        """测试添加重复权限"""
        user = User(
            user_id="123",
            username="testuser",
            role=Role.USER,
            permissions={Permission.READ}
        )
        user.add_permission(Permission.READ)
        # 重复添加不影响
        assert len(user.permissions) == 1

    def test_remove_permission(self):
        """测试移除权限"""
        user = User(
            user_id="123",
            username="testuser",
            role=Role.USER,
            permissions={Permission.READ, Permission.WRITE}
        )
        user.remove_permission(Permission.WRITE)
        assert user.has_permission(Permission.WRITE) is False
        assert len(user.permissions) == 1

    def test_remove_nonexistent_permission(self):
        """测试移除不存在的权限"""
        user = User(
            user_id="123",
            username="testuser",
            role=Role.USER,
            permissions={Permission.READ}
        )
        user.remove_permission(Permission.WRITE)
        # 移除不存在的权限不影响
        assert len(user.permissions) == 1


class TestAccessControl:
    """测试访问控制系统"""

    @pytest.fixture
    def access_control(self):
        """创建访问控制系统实例"""
        return AccessControl()

    def test_initialization(self, access_control):
        """测试初始化"""
        assert len(access_control.users) == 0
        assert len(access_control.roles) == 0

    def test_create_user(self, access_control):
        """测试创建用户"""
        user = access_control.create_user(
            user_id="123",
            username="testuser",
            role=Role.USER
        )
        assert user.user_id == "123"
        assert user.username == "testuser"
        assert user.role == Role.USER
        # 用户应该被添加到系统中
        assert "123" in access_control.users

    def test_create_user_with_permissions(self, access_control):
        """测试创建带权限的用户"""
        permissions = {Permission.READ, Permission.WRITE}
        user = access_control.create_user(
            user_id="123",
            username="testuser",
            role=Role.USER,
            permissions=permissions
        )
        assert user.has_permission(Permission.READ) is True
        assert user.has_permission(Permission.WRITE) is True

    def test_get_user(self, access_control):
        """测试获取用户"""
        # 创建用户
        access_control.create_user(
            user_id="123",
            username="testuser",
            role=Role.USER
        )
        # 获取用户
        user = access_control.get_user("123")
        assert user is not None
        assert user.username == "testuser"

    def test_get_nonexistent_user(self, access_control):
        """测试获取不存在的用户"""
        user = access_control.get_user("nonexistent")
        assert user is None

    def test_delete_user(self, access_control):
        """测试删除用户"""
        # 创建用户
        access_control.create_user(
            user_id="123",
            username="testuser",
            role=Role.USER
        )
        # 删除用户
        result = access_control.delete_user("123")
        assert result is True
        assert "123" not in access_control.users

    def test_delete_nonexistent_user(self, access_control):
        """测试删除不存在的用户"""
        result = access_control.delete_user("nonexistent")
        assert result is False

    def test_grant_permission(self, access_control):
        """测试授予权限"""
        # 创建用户
        access_control.create_user(
            user_id="123",
            username="testuser",
            role=Role.GUEST
        )
        # 授予权限
        result = access_control.grant_permission("123", Permission.WRITE)
        assert result is True
        # 验证权限
        user = access_control.get_user("123")
        assert user.has_permission(Permission.WRITE) is True

    def test_grant_permission_nonexistent_user(self, access_control):
        """测试给不存在的用户授予权限"""
        result = access_control.grant_permission("nonexistent", Permission.WRITE)
        assert result is False

    def test_revoke_permission(self, access_control):
        """测试撤销权限"""
        # 创建带权限的用户
        access_control.create_user(
            user_id="123",
            username="testuser",
            role=Role.USER,
            permissions={Permission.READ, Permission.WRITE}
        )
        # 撤销权限
        result = access_control.revoke_permission("123", Permission.WRITE)
        assert result is True
        # 验证权限已撤销
        user = access_control.get_user("123")
        assert user.has_permission(Permission.WRITE) is False

    def test_revoke_permission_nonexistent_user(self, access_control):
        """测试撤销不存在用户的权限"""
        result = access_control.revoke_permission("nonexistent", Permission.WRITE)
        assert result is False

    def test_check_permission_allowed(self, access_control):
        """测试检查权限-允许"""
        # 创建带权限的用户
        access_control.create_user(
            user_id="123",
            username="testuser",
            role=Role.USER,
            permissions={Permission.READ}
        )
        # 检查权限
        result = access_control.check_permission("123", Permission.READ)
        assert result is True

    def test_check_permission_denied(self, access_control):
        """测试检查权限-拒绝"""
        # 创建用户
        access_control.create_user(
            user_id="123",
            username="testuser",
            role=Role.GUEST
        )
        # 检查权限
        result = access_control.check_permission("123", Permission.WRITE)
        assert result is False

    def test_check_permission_nonexistent_user(self, access_control):
        """测试检查不存在用户的权限"""
        result = access_control.check_permission("nonexistent", Permission.READ)
        assert result is False

    def test_get_role_permissions(self, access_control):
        """测试获取角色权限"""
        admin_perms = access_control.get_role_permissions(Role.ADMIN)
        assert Permission.DELETE in admin_perms
        assert Permission.MODIFY_CONFIG in admin_perms

        guest_perms = access_control.get_role_permissions(Role.GUEST)
        assert Permission.READ in guest_perms
        assert Permission.DELETE not in guest_perms

    def test_user_has_role_permission(self, access_control):
        """测试用户拥有角色权限"""
        # 创建ADMIN用户（不带额外权限）
        access_control.create_user(
            user_id="admin1",
            username="admin",
            role=Role.ADMIN
        )
        # ADMIN角色应该有DELETE权限
        result = access_control.check_permission("admin1", Permission.DELETE)
        assert result is True

    def test_list_users_by_role(self, access_control):
        """测试按角色列出用户"""
        # 创建多个用户
        access_control.create_user("1", "user1", Role.USER)
        access_control.create_user("2", "user2", Role.USER)
        access_control.create_user("3", "admin1", Role.ADMIN)

        user_list = access_control.list_users_by_role(Role.USER)
        assert len(user_list) == 2
        usernames = [u.username for u in user_list]
        assert "user1" in usernames
        assert "user2" in usernames
