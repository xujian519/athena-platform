#!/usr/bin/env python3
"""
权限控制器
Permissions Controller - 实现分层权限控制和操作验证
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

class PermissionLevel(Enum):
    """权限级别"""
    NONE = 0      # 无权限
    READ = 1      # 只读权限
    WRITE = 2     # 写入权限
    DELETE = 3    # 删除权限
    ADMIN = 4     # 管理权限
    ROOT = 5      # 根权限

class OperationRisk(Enum):
    """操作风险级别"""
    LOW = 1       # 低风险
    MEDIUM = 2    # 中等风险
    HIGH = 3      # 高风险
    CRITICAL = 4  # 关键风险

@dataclass
class PermissionRule:
    """权限规则"""
    data_type: str
    operation: str
    required_level: PermissionLevel
    risk_level: OperationRisk
    requires_dual_auth: bool = False
    requires_confirmation: bool = False
    time_restriction: tuple[int, int] | None = None  # (start_hour, end_hour)
    description: str = ""

@dataclass
class AccessLog:
    """访问日志"""
    user: str
    operation: str
    data_type: str
    target: str
    granted: bool
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)
    ip_address: str = "localhost"
    session_id: str = ""

class PermissionsController:
    """权限控制器"""

    def __init__(self):
        self.permission_rules: dict[str, PermissionRule] = {}
        self.user_permissions: dict[str, dict[str, PermissionLevel] = {}
        self.access_logs: list[AccessLog] = []
        self.session_tokens: dict[str, dict[str, Any] = {}
        self.dual_auth_requests: dict[str, dict[str, Any] = {}

        self._initialize_permission_rules()
        self._initialize_user_permissions()

    def _initialize_permission_rules(self):
        """初始化权限规则"""
        self.permission_rules = {
            # 客户资料相关
            ("customer", "query"): PermissionRule(
                data_type="customer",
                operation="query",
                required_level=PermissionLevel.READ,
                risk_level=OperationRisk.LOW,
                description="查询客户资料"
            ),
            ("customer", "create"): PermissionRule(
                data_type="customer",
                operation="create",
                required_level=PermissionLevel.WRITE,
                risk_level=OperationRisk.LOW,
                description="创建客户资料"
            ),
            ("customer", "update"): PermissionRule(
                data_type="customer",
                operation="update",
                required_level=PermissionLevel.WRITE,
                risk_level=OperationRisk.MEDIUM,
                requires_confirmation=True,
                description="更新客户资料"
            ),
            ("customer", "delete"): PermissionRule(
                data_type="customer",
                operation="delete",
                required_level=PermissionLevel.DELETE,
                risk_level=OperationRisk.HIGH,
                requires_dual_auth=True,
                requires_confirmation=True,
                description="删除客户资料"
            ),

            # 专利相关
            ("patent", "query"): PermissionRule(
                data_type="patent",
                operation="query",
                required_level=PermissionLevel.READ,
                risk_level=OperationRisk.LOW,
                description="查询专利信息"
            ),
            ("patent", "create"): PermissionRule(
                data_type="patent",
                operation="create",
                required_level=PermissionLevel.WRITE,
                risk_level=OperationRisk.MEDIUM,
                requires_confirmation=True,
                description="创建专利记录"
            ),
            ("patent", "update"): PermissionRule(
                data_type="patent",
                operation="update",
                required_level=PermissionLevel.WRITE,
                risk_level=OperationRisk.HIGH,
                requires_confirmation=True,
                description="更新专利记录"
            ),
            ("patent", "delete"): PermissionRule(
                data_type="patent",
                operation="delete",
                required_level=PermissionLevel.ADMIN,
                risk_level=OperationRisk.CRITICAL,
                requires_dual_auth=True,
                requires_confirmation=True,
                description="删除专利记录"
            ),

            # IP管理相关
            ("ip_management", "query"): PermissionRule(
                data_type="ip_management",
                operation="query",
                required_level=PermissionLevel.READ,
                risk_level=OperationRisk.LOW,
                description="查询IP管理信息"
            ),
            ("ip_management", "create"): PermissionRule(
                data_type="ip_management",
                operation="create",
                required_level=PermissionLevel.WRITE,
                risk_level=OperationRisk.MEDIUM,
                requires_confirmation=True,
                description="创建IP管理记录"
            ),
            ("ip_management", "update"): PermissionRule(
                data_type="ip_management",
                operation="update",
                required_level=PermissionLevel.WRITE,
                risk_level=OperationRisk.HIGH,
                requires_confirmation=True,
                description="更新IP管理记录"
            ),
            ("ip_management", "delete"): PermissionRule(
                data_type="ip_management",
                operation="delete",
                required_level=PermissionLevel.ADMIN,
                risk_level=OperationRisk.CRITICAL,
                requires_dual_auth=True,
                requires_confirmation=True,
                description="删除IP管理记录"
            ),

            # 知识图谱相关
            ("knowledge_graph", "query"): PermissionRule(
                data_type="knowledge_graph",
                operation="query",
                required_level=PermissionLevel.READ,
                risk_level=OperationRisk.LOW,
                description="查询知识图谱"
            ),
            ("knowledge_graph", "create"): PermissionRule(
                data_type="knowledge_graph",
                operation="create",
                required_level=PermissionLevel.WRITE,
                risk_level=OperationRisk.MEDIUM,
                requires_confirmation=True,
                description="创建知识图谱节点"
            ),
            ("knowledge_graph", "update"): PermissionRule(
                data_type="knowledge_graph",
                operation="update",
                required_level=PermissionLevel.ADMIN,
                risk_level=OperationRisk.HIGH,
                requires_dual_auth=True,
                requires_confirmation=True,
                description="更新知识图谱"
            ),
            ("knowledge_graph", "delete"): PermissionRule(
                data_type="knowledge_graph",
                operation="delete",
                required_level=PermissionLevel.ADMIN,
                risk_level=OperationRisk.CRITICAL,
                requires_dual_auth=True,
                requires_confirmation=True,
                description="删除知识图谱节点"
            ),

            # 向量数据相关
            ("vector_data", "query"): PermissionRule(
                data_type="vector_data",
                operation="query",
                required_level=PermissionLevel.READ,
                risk_level=OperationRisk.LOW,
                description="查询向量数据"
            ),
            ("vector_data", "create"): PermissionRule(
                data_type="vector_data",
                operation="create",
                required_level=PermissionLevel.WRITE,
                risk_level=OperationRisk.MEDIUM,
                requires_confirmation=True,
                description="创建向量数据"
            ),
            ("vector_data", "delete"): PermissionRule(
                data_type="vector_data",
                operation="delete",
                required_level=PermissionLevel.ADMIN,
                risk_level=OperationRisk.HIGH,
                requires_dual_auth=True,
                requires_confirmation=True,
                description="删除向量数据"
            ),

            # 性能指标相关
            ("performance", "query"): PermissionRule(
                data_type="performance",
                operation="query",
                required_level=PermissionLevel.READ,
                risk_level=OperationRisk.LOW,
                description="查询性能指标"
            ),
            ("performance", "create"): PermissionRule(
                data_type="performance",
                operation="create",
                required_level=PermissionLevel.WRITE,
                risk_level=OperationRisk.LOW,
                description="创建性能记录"
            ),

            # 配置相关
            ("config", "query"): PermissionRule(
                data_type="config",
                operation="query",
                required_level=PermissionLevel.READ,
                risk_level=OperationRisk.MEDIUM,
                description="查询配置信息"
            ),
            ("config", "update"): PermissionRule(
                data_type="config",
                operation="update",
                required_level=PermissionLevel.ADMIN,
                risk_level=OperationRisk.CRITICAL,
                requires_dual_auth=True,
                requires_confirmation=True,
                time_restriction=(9, 18),  # 只允许工作时间
                description="更新配置信息"
            ),
            ("config", "delete"): PermissionRule(
                data_type="config",
                operation="delete",
                required_level=PermissionLevel.ROOT,
                risk_level=OperationRisk.CRITICAL,
                requires_dual_auth=True,
                requires_confirmation=True,
                time_restriction=(9, 18),
                description="删除配置信息"
            ),

            # 财务数据相关
            ("finance", "query"): PermissionRule(
                data_type="finance",
                operation="query",
                required_level=PermissionLevel.READ,
                risk_level=OperationRisk.MEDIUM,
                description="查询财务数据"
            ),
            ("finance", "create"): PermissionRule(
                data_type="finance",
                operation="create",
                required_level=PermissionLevel.WRITE,
                risk_level=OperationRisk.HIGH,
                requires_confirmation=True,
                description="创建财务记录"
            ),
            ("finance", "update"): PermissionRule(
                data_type="finance",
                operation="update",
                required_level=PermissionLevel.ADMIN,
                risk_level=OperationRisk.HIGH,
                requires_dual_auth=True,
                requires_confirmation=True,
                description="更新财务数据"
            )
        }

    def _initialize_user_permissions(self):
        """初始化用户权限"""
        self.user_permissions = {
            "爸爸": {
                "customer": PermissionLevel.ROOT,
                "patent": PermissionLevel.ADMIN,
                "ip_management": PermissionLevel.ADMIN,
                "knowledge_graph": PermissionLevel.WRITE,
                "vector_data": PermissionLevel.WRITE,
                "performance": PermissionLevel.ROOT,
                "config": PermissionLevel.ADMIN,
                "finance": PermissionLevel.ADMIN
            },
            "小诺": {
                "customer": PermissionLevel.WRITE,
                "patent": PermissionLevel.READ,
                "ip_management": PermissionLevel.READ,
                "knowledge_graph": PermissionLevel.READ,
                "vector_data": PermissionLevel.READ,
                "performance": PermissionLevel.ADMIN,
                "config": PermissionLevel.READ,
                "finance": PermissionLevel.READ
            },
            "小娜": {
                "patent": PermissionLevel.ADMIN,
                "customer": PermissionLevel.WRITE,
                "knowledge_graph": PermissionLevel.WRITE
            },
            "云熙": {
                "ip_management": PermissionLevel.ADMIN,
                "customer": PermissionLevel.WRITE,
                "patent": PermissionLevel.READ
            },
            "athena": {
                "knowledge_graph": PermissionLevel.ROOT,
                "vector_data": PermissionLevel.ADMIN,
                "config": PermissionLevel.ADMIN
            }
        }

    def check_permission(self, user: str, data_type: str, operation: str, target: str = "",
                        session_id: str = "", ip_address: str = "localhost") -> tuple[bool, str]:
        """检查权限"""
        rule_key = (data_type, operation)

        # 检查规则是否存在
        if rule_key not in self.permission_rules:
            reason = f"未找到操作规则: {data_type}.{operation}"
            self._log_access(user, operation, data_type, target, False, reason, session_id, ip_address)
            return False, reason

        rule = self.permission_rules[rule_key]

        # 检查用户权限
        user_perm = self.user_permissions.get(user, {}).get(data_type, PermissionLevel.NONE)
        if user_perm.value < rule.required_level.value:
            reason = f"权限不足: 需要 {rule.required_level.name}, 当前 {user_perm.name}"
            self._log_access(user, operation, data_type, target, False, reason, session_id, ip_address)
            return False, reason

        # 检查时间限制
        if rule.time_restriction:
            current_hour = datetime.now().hour
            start_hour, end_hour = rule.time_restriction
            if not (start_hour <= current_hour <= end_hour):
                reason = f"时间限制: 只允许在 {start_hour}:00-{end_hour}:00 执行"
                self._log_access(user, operation, data_type, target, False, reason, session_id, ip_address)
                return False, reason

        # 检查会话有效性
        if session_id and not self._validate_session(session_id):
            reason = "会话无效或已过期"
            self._log_access(user, operation, data_type, target, False, reason, session_id, ip_address)
            return False, reason

        # 权限通过
        reason = "权限检查通过"
        self._log_access(user, operation, data_type, target, True, reason, session_id, ip_address)
        return True, reason

    def requires_dual_authentication(self, data_type: str, operation: str) -> bool:
        """检查是否需要双重认证"""
        rule_key = (data_type, operation)
        if rule_key in self.permission_rules:
            return self.permission_rules[rule_key].requires_dual_auth
        return False

    def requires_confirmation(self, data_type: str, operation: str) -> bool:
        """检查是否需要确认"""
        rule_key = (data_type, operation)
        if rule_key in self.permission_rules:
            return self.permission_rules[rule_key].requires_confirmation
        return False

    def get_risk_level(self, data_type: str, operation: str) -> OperationRisk:
        """获取操作风险级别"""
        rule_key = (data_type, operation)
        if rule_key in self.permission_rules:
            return self.permission_rules[rule_key].risk_level
        return OperationRisk.MEDIUM

    def create_session(self, user: str, duration_hours: int = 8) -> str:
        """创建会话"""
        session_id = hashlib.sha256(f"{user}{datetime.now().isoformat()}".encode()).hexdigest()[:32]

        self.session_tokens[session_id] = {
            "user": user,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=duration_hours),
            "last_activity": datetime.now()
        }

        return session_id

    def _validate_session(self, session_id: str) -> bool:
        """验证会话"""
        if session_id not in self.session_tokens:
            return False

        session = self.session_tokens[session_id]
        if datetime.now() > session["expires_at"]:
            del self.session_tokens[session_id]
            return False

        # 更新最后活动时间
        session["last_activity"] = datetime.now()
        return True

    def request_dual_authentication(self, user: str, operation: str, data_type: str,
                                  target: str, details: dict[str, Any]) -> str:
        """请求双重认证"""
        request_id = hashlib.sha256(f"{user}{operation}{datetime.now().isoformat()}".encode()).hexdigest()[:32]

        self.dual_auth_requests[request_id] = {
            "user": user,
            "operation": operation,
            "data_type": data_type,
            "target": target,
            "details": details,
            "created_at": datetime.now(),
            "approvals": set(),
            "required_approvers": ["小娜", "athena"],  # 需要的批准者
            "status": "pending"
        }

        logger.info(f"🔐 双重认证请求已创建: {request_id}")
        return request_id

    def approve_dual_authentication(self, request_id: str, approver: str, approval_token: str) -> bool:
        """批准双重认证"""
        if request_id not in self.dual_auth_requests:
            return False

        request = self.dual_auth_requests[request_id]

        # 验证批准者权限
        if approver not in request["required_approvers"]:
            logger.warning(f"未授权的批准者: {approver}")
            return False

        # 添加批准
        request["approvals"].add(approver)

        # 检查是否获得足够批准
        if len(request["approvals"]) >= len(request["required_approvers"]):
            request["status"] = "approved"
            logger.info(f"✅ 双重认证请求已批准: {request_id}")
            return True

        return True

    def is_dual_authentication_approved(self, request_id: str) -> bool:
        """检查双重认证是否已批准"""
        if request_id not in self.dual_auth_requests:
            return False

        return self.dual_auth_requests[request_id]["status"] == "approved"

    def _log_access(self, user: str, operation: str, data_type: str, target: str,
                   granted: bool, reason: str, session_id: str = "", ip_address: str = ""):
        """记录访问日志"""
        log_entry = AccessLog(
            user=user,
            operation=operation,
            data_type=data_type,
            target=target,
            granted=granted,
            reason=reason,
            session_id=session_id,
            ip_address=ip_address
        )

        self.access_logs.append(log_entry)

        # 只保留最近10000条日志
        if len(self.access_logs) > 10000:
            self.access_logs = self.access_logs[-10000:]

        # 记录到日志文件
        log_level = logging.INFO if granted else logging.WARNING
        logger.log(log_level, f"权限检查: {user} {operation} {data_type} - {granted} - {reason}")

    def get_access_logs(self, user: str | None = None, data_type: str | None = None,
                       start_time: datetime | None = None,
                       end_time: datetime | None = None,
                       limit: int = 100) -> list[dict[str, Any]:
        """获取访问日志"""
        logs = self.access_logs

        # 应用过滤条件
        if user:
            logs = [log for log in logs if log.user == user]
        if data_type:
            logs = [log for log in logs if log.data_type == data_type]
        if start_time:
            logs = [log for log in logs if log.timestamp >= start_time]
        if end_time:
            logs = [log for log in logs if log.timestamp <= end_time]

        # 按时间倒序排列
        logs.sort(key=lambda x: x.timestamp, reverse=True)

        # 转换为字典并限制数量
        result = []
        for log in logs[:limit]:
            result.append({
                "user": log.user,
                "operation": log.operation,
                "data_type": log.data_type,
                "target": log.target,
                "granted": log.granted,
                "reason": log.reason,
                "timestamp": log.timestamp.isoformat(),
                "ip_address": log.ip_address,
                "session_id": log.session_id
            })

        return result

    def get_permission_matrix(self) -> dict[str, dict[str, str]:
        """获取权限矩阵"""
        matrix = {}

        for user, permissions in self.user_permissions.items():
            matrix[user] = {}
            for data_type, level in permissions.items():
                matrix[user][data_type] = level.name

        return matrix

    def export_access_report(self, days: int = 7) -> dict[str, Any]:
        """导出访问报告"""
        start_time = datetime.now() - timedelta(days=days)
        logs = self.get_access_logs(start_time=start_time)

        # 统计信息
        total_requests = len(logs)
        successful_requests = len([log for log in logs if log["granted"])
        failed_requests = total_requests - successful_requests

        # 按用户统计
        user_stats = {}
        for log in logs:
            user = log["user"]
            if user not in user_stats:
                user_stats[user] = {"total": 0, "success": 0, "failed": 0}

            user_stats[user]["total"] += 1
            if log["granted"]:
                user_stats[user]["success"] += 1
            else:
                user_stats[user]["failed"] += 1

        # 按操作类型统计
        operation_stats = {}
        for log in logs:
            operation = f"{log['operation']}.{log['data_type']}"
            if operation not in operation_stats:
                operation_stats[operation] = {"total": 0, "success": 0, "failed": 0}

            operation_stats[operation]["total"] += 1
            if log["granted"]:
                operation_stats[operation]["success"] += 1
            else:
                operation_stats[operation]["failed"] += 1

        return {
            "period": f"{days} days",
            "summary": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": successful_requests / total_requests if total_requests > 0 else 0
            },
            "user_statistics": user_stats,
            "operation_statistics": operation_stats,
            "generated_at": datetime.now().isoformat()
        }

# 全局权限控制器实例
permissions_controller = PermissionsController()

# 测试代码
if __name__ == "__main__":
    # 测试权限检查
    print("🔐 权限控制器测试")
    print("=" * 50)

    # 测试基本权限检查
    granted, reason = permissions_controller.check_permission("爸爸", "customer", "query")
    print(f"爸爸查询客户资料: {granted} - {reason}")

    granted, reason = permissions_controller.check_permission("小诺", "config", "update")
    print(f"小诺更新配置: {granted} - {reason}")

    granted, reason = permissions_controller.check_permission("小娜", "patent", "delete")
    print(f"小娜删除专利: {granted} - {reason}")

    # 测试会话创建
    session_id = permissions_controller.create_session("爸爸")
    print(f"\n创建会话: {session_id}")

    # 测试双重认证
    request_id = permissions_controller.request_dual_authentication(
        "爸爸", "delete", "knowledge_graph", "节点123", {"reason": "测试删除"}
    )
    print(f"\n双重认证请求: {request_id}")

    # 批准双重认证
    approval_result = permissions_controller.approve_dual_authentication(request_id, "小娜", "token123")
    print(f"小娜批准结果: {approval_result}")

    approval_result = permissions_controller.approve_dual_authentication(request_id, "athena", "token456")
    print(f"Athena批准结果: {approval_result}")

    # 检查双重认证状态
    approved = permissions_controller.is_dual_authentication_approved(request_id)
    print(f"双重认证已批准: {approved}")

    # 导出访问报告
    report = permissions_controller.export_access_report(1)
    print(f"\n访问报告: {report}")

    # 获取权限矩阵
    matrix = permissions_controller.get_permission_matrix()
    print(f"\n权限矩阵: {json.dumps(matrix, indent=2, ensure_ascii=False)}")
