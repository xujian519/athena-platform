# 访问控制系统使用指南

> **Author**: SecurityAgent
> **Date**: 2026-04-24
> **Version**: 1.0.0

---

## 目录

1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [RBAC权限管理](#rbac权限管理)
4. [上下文权限管理](#上下文权限管理)
5. [审计日志](#审计日志)
6. [安全最佳实践](#安全最佳实践)
7. [API参考](#api参考)
8. [故障排查](#故障排查)

---

## 系统概述

Athena访问控制系统提供完整的安全访问控制解决方案，包括：

- **RBAC（基于角色的访问控制）**：灵活的角色和权限管理
- **上下文权限**：细粒度的资源访问控制
- **审计日志**：完整的安全审计追踪

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    访问控制系统                          │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ RBAC Manager│  │Context Perm  │  │ Audit Logger │   │
│  │             │  │   Manager    │  │              │   │
│  │ • 角色管理  │  │ • 资源权限   │  │ • 操作记录   │   │
│  │ • 权限分配  │  │ • 访问控制   │  │ • 完整性验证 │   │
│  │ • 用户角色  │  │ • 权限继承   │  │ • 日志导出   │   │
│  └─────────────┘  └──────────────┘  └──────────────┘   │
│         │                   │                  │        │
│         └───────────────────┴──────────────────┘        │
│                            │                            │
│                    ┌───────▼────────┐                   │
│                    │  SQLite 存储   │                   │
│                    └────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 安装

访问控制系统是Athena平台的一部分，无需额外安装。

### 基本使用

```python
from core.context_management.access_control import (
    RBACManager,
    ContextPermissionManager,
    AuditLogger,
)

# 初始化管理器
rbac = RBACManager()
context_perm = ContextPermissionManager()
audit = AuditLogger()

# 分配角色
rbac.assign_role("user123", "editor", "admin")

# 授予上下文权限
context_perm.grant_permission(
    context_id="doc1",
    user_id="user123",
    level=PermissionLevel.OWNER,
    granted_by="admin",
)

# 检查权限
if rbac.check_permission("user123", "context.create"):
    print("用户可以创建上下文")

# 记录审计日志
audit.log_access(
    user_id="user123",
    resource_type="context",
    resource_id="doc1",
    success=True,
)
```

---

## RBAC权限管理

### 系统预定义角色

| 角色 | 描述 | 权限 |
|------|------|------|
| `admin` | 系统管理员 | 所有权限 |
| `moderator` | 内容审核员 | 读取、更新、审核 |
| `editor` | 编辑者 | 创建、读取、更新 |
| `viewer` | 查看者 | 仅读取 |
| `guest` | 访客 | 受限读取 |

### 创建自定义角色

```python
from core.context_management.access_control import RBACManager, Role

rbac = RBACManager()

# 创建角色
role = rbac.create_role(
    role="content_creator",
    description="内容创作者",
    permissions={
        "context.create",
        "context.read",
        "context.update",
    },
)
```

### 分配角色

```python
# 分配单个角色
user_role = rbac.assign_role(
    user_id="user123",
    role_name="editor",
    granted_by="admin",
)

# 分配多个角色
rbac.assign_roles(
    user_id="user123",
    role_names=["editor", "viewer"],
    granted_by="admin",
)

# 临时角色（带过期时间）
from datetime import datetime, timedelta

user_role = rbac.assign_role(
    user_id="temp_user",
    role_name="editor",
    granted_by="admin",
    expires_at=datetime.now() + timedelta(days=7),
)
```

### 检查权限

```python
# 检查单个权限
has_permission = rbac.check_permission("user123", "context.create")

# 检查多个权限（任一）
has_any = rbac.check_any_permission(
    user_id="user123",
    permissions=["context.create", "context.update"],
)

# 检查多个权限（全部）
has_all = rbac.check_all_permissions(
    user_id="user123",
    permissions=["context.read", "context.update"],
)

# 获取用户所有权限
permissions = rbac.get_user_permissions("user123")
```

### 管理角色权限

```python
# 授予权限
rbac.grant_permission("editor", "context.delete")

# 撤销权限
rbac.revoke_permission("editor", "context.delete")

# 获取角色权限
permissions = rbac.get_role_permissions("editor")
```

---

## 上下文权限管理

### 权限级别

| 级别 | 描述 | 读取 | 编辑 | 删除 | 分享 |
|------|------|:----:|:----:|:----:|:----:|
| `owner` | 所有者 | ✅ | ✅ | ✅ | ✅ |
| `edit` | 编辑 | ✅ | ✅ | ❌ | ❌ |
| `read` | 读取 | ✅ | ❌ | ❌ | ❌ |
| `none` | 无权限 | ❌ | ❌ | ❌ | ❌ |

### 授予权限

```python
from core.context_management.access_control import ContextPermissionManager, PermissionLevel

cpm = ContextPermissionManager()

# 授予所有者权限
cpm.grant_permission(
    context_id="document_1",
    user_id="user123",
    level=PermissionLevel.OWNER,
    granted_by="admin",
)

# 授予编辑权限（7天后过期）
from datetime import datetime, timedelta

cpm.grant_permission(
    context_id="document_1",
    user_id="user456",
    level=PermissionLevel.EDIT,
    granted_by="user123",
    expires_at=datetime.now() + timedelta(days=7),
)

# 批量授予权限
cpm.grant_batch(
    context_id="document_1",
    user_ids=["user1", "user2", "user3"],
    level=PermissionLevel.READ,
    granted_by="admin",
)
```

### 检查访问权限

```python
# 检查读取权限
can_read = cpm.can_read("document_1", "user123")

# 检查编辑权限
can_edit = cpm.can_edit("document_1", "user123")

# 检查删除权限
can_delete = cpm.can_delete("document_1", "user123")

# 检查是否是所有者
is_owner = cpm.is_owner("document_1", "user123")

# 通用访问检查
has_access = cpm.check_access(
    context_id="document_1",
    user_id="user123",
    required_level=PermissionLevel.EDIT,
)
```

### 查询权限

```python
# 获取用户对上下文的权限
permission = cpm.get_permission("document_1", "user123")

# 获取上下文的所有权限
permissions = cpm.get_context_permissions("document_1")

# 获取用户可访问的上下文
contexts = cpm.get_user_contexts("user123")

# 获取用户可编辑的上下文
editable_contexts = cpm.get_user_contexts(
    user_id="user123",
    min_level=PermissionLevel.EDIT,
)

# 获取上下文所有者
owner = cpm.get_context_owner("document_1")
```

### 撤销权限

```python
# 撤销单个权限
cpm.revoke_permission("document_1", "user123")

# 撤销上下文的所有权限
cpm.revoke_all_permissions("document_1")

# 清理用户的所有权限
cpm.cleanup_user("user123")

# 清理上下文
cpm.cleanup_context("document_1")
```

---

## 审计日志

### 记录操作

```python
from core.context_management.access_control import AuditLogger, ActionType, OperationResult

audit = AuditLogger()

# 记录访问
audit.log_access(
    user_id="user123",
    resource_type="context",
    resource_id="document_1",
    success=True,
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
)

# 记录权限变更
audit.log_permission_change(
    user_id="admin",
    target_user_id="user123",
    permission="context.read",
    granted=True,
)

# 记录通用操作
audit.log_operation(
    user_id="user123",
    operation="create_context",
    resource_type="context",
    resource_id="document_1",
    success=True,
)

# 记录失败尝试
audit.log_access(
    user_id="attacker",
    resource_type="context",
    resource_id="restricted",
    success=False,  # 记录被拒绝的访问
)
```

### 查询日志

```python
from datetime import datetime, timedelta

# 查询用户活动
activity = audit.get_user_activity("user123")

# 查询资源历史
history = audit.get_resource_history("context", "document_1")

# 查询失败尝试
failed = audit.get_failed_attempts("user123")

# 高级查询
logs = audit.query_logs(
    user_id="user123",
    action=ActionType.ACCESS,
    start_time=datetime.now() - timedelta(days=7),
    end_time=datetime.now(),
    result=OperationResult.SUCCESS,
    limit=100,
)
```

### 导出日志

```python
# 导出为JSON
audit.export_json(
    output_path="audit_logs.json",
    user_id="user123",
    start_time=datetime.now() - timedelta(days=30),
)

# 导出为CSV
audit.export_csv(
    output_path="audit_logs.csv",
    start_time=datetime.now() - timedelta(days=30),
)
```

### 完整性验证

```python
# 验证审计日志完整性
result = audit.verify_integrity()

print(f"总条目: {result['total']}")
print(f"有效: {result['valid']}")
print(f"无效: {result['invalid']}")
print(f"完整性率: {result['integrity_rate']:.2%}")
```

### 统计信息

```python
# 获取统计信息
stats = audit.get_statistics()

print(f"总日志数: {stats['total_entries']}")
print(f"按操作: {stats['by_action']}")
print(f"按结果: {stats['by_result']}")
print(f"活跃用户: {stats['top_users']}")
```

---

## 安全最佳实践

### 1. 最小权限原则

始终授予用户完成工作所需的最小权限：

```python
# ❌ 不推荐：授予过多权限
rbac.assign_role("user123", "admin", "system")

# ✅ 推荐：授予刚好够用的权限
rbac.assign_role("user123", "editor", "admin")
```

### 2. 定期审计

定期审查和清理权限：

```python
# 查找长期未活动的用户
from datetime import datetime, timedelta

cutoff = datetime.now() - timedelta(days=90)
recent_activity = audit.get_user_activity("user123", start_time=cutoff)

if not recent_activity:
    # 考虑撤销权限
    rbac.revoke_all_roles("user123", "admin")
```

### 3. 记录所有敏感操作

确保所有敏感操作都被记录：

```python
# 在权限变更前记录
audit.log_permission_change(
    user_id=current_user,
    target_user_id=target_user,
    permission=permission,
    granted=True,
)

# 执行变更
rbac.assign_role(target_user, role, current_user)
```

### 4. 使用临时权限

对于临时需求，使用带过期时间的权限：

```python
# 临时访问权限（1天）
cpm.grant_permission(
    context_id="sensitive_doc",
    user_id="temp_user",
    level=PermissionLevel.READ,
    granted_by="admin",
    expires_at=datetime.now() + timedelta(days=1),
)
```

### 5. 监控异常行为

设置告警监控异常访问模式：

```python
# 检测频繁的权限拒绝
failed_attempts = audit.get_failed_attempts("user123", limit=10)

if len(failed_attempts) > 5:
    # 可能的攻击行为，需要调查
    print(f"警告: 用户user123有{len(failed_attempts)}次失败尝试")
```

### 6. 定期清理

定期清理过期数据：

```python
# 清理过期的用户角色
rbac.cleanup_expired_roles()

# 清理过期的上下文权限
cpm.cleanup_expired_permissions()

# 清理旧的审计日志（保留失败尝试）
cutoff = datetime.now() - timedelta(days=90)
audit.cleanup_old_logs(cutoff, keep_failed=True)
```

---

## API参考

### RBACManager

| 方法 | 描述 |
|------|------|
| `create_role()` | 创建角色 |
| `get_role()` | 获取角色 |
| `list_roles()` | 列出所有角色 |
| `delete_role()` | 删除角色 |
| `grant_permission()` | 为角色授予权限 |
| `revoke_permission()` | 撤销角色权限 |
| `assign_role()` | 为用户分配角色 |
| `revoke_role()` | 撤销用户角色 |
| `get_user_roles()` | 获取用户角色 |
| `check_permission()` | 检查权限 |
| `get_user_permissions()` | 获取用户所有权限 |

### ContextPermissionManager

| 方法 | 描述 |
|------|------|
| `grant_permission()` | 授予上下文权限 |
| `revoke_permission()` | 撤销上下文权限 |
| `get_permission()` | 获取上下文权限 |
| `get_context_permissions()` | 获取上下文所有权限 |
| `get_user_contexts()` | 获取用户可访问的上下文 |
| `can_read()` | 检查读取权限 |
| `can_edit()` | 检查编辑权限 |
| `can_delete()` | 检查删除权限 |
| `is_owner()` | 检查是否是所有者 |

### AuditLogger

| 方法 | 描述 |
|------|------|
| `log()` | 记录审计日志 |
| `log_access()` | 记录访问 |
| `log_permission_change()` | 记录权限变更 |
| `query_logs()` | 查询日志 |
| `get_user_activity()` | 获取用户活动 |
| `get_resource_history()` | 获取资源历史 |
| `get_failed_attempts()` | 获取失败尝试 |
| `export_json()` | 导出为JSON |
| `export_csv()` | 导出为CSV |
| `verify_integrity()` | 验证完整性 |

---

## 故障排查

### 权限检查失败

**问题**: 用户无法访问应该有权限的资源

**排查步骤**:
1. 检查用户角色: `rbac.get_user_roles(user_id)`
2. 检查角色权限: `rbac.get_role_permissions(role_name)`
3. 检查上下文权限: `cpm.get_permission(context_id, user_id)`
4. 检查权限是否过期

### 审计日志缺失

**问题**: 某些操作没有被记录

**排查步骤**:
1. 检查审计是否启用
2. 检查操作类型是否在记录列表中
3. 检查数据库连接

### 性能问题

**问题**: 权限检查响应慢

**解决方案**:
1. 启用权限缓存
2. 定期清理过期权限
3. 优化数据库索引

---

## 配置说明

配置文件位于 `config/access_control.yaml`，主要配置项：

```yaml
# RBAC配置
rbac:
  default_role: viewer
  superusers:
    - admin

# 上下文权限配置
context_permissions:
  default_policy:
    creator_level: owner
    inherit: false

# 审计日志配置
audit:
  enabled: true
  retention_days: 90
  log_ip_address: true
```

---

## 更多信息

- **配置文件**: `config/access_control.yaml`
- **测试文件**: `tests/test_access_control.py`
- **安全测试**: `tests/security/test_access_control_security.py`
- **模块代码**: `core/context_management/access_control/`
