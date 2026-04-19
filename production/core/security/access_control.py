#!/usr/bin/env python3
from __future__ import annotations
"""
访问控制系统
Access Control System

提供细粒度的访问控制、权限验证和资源保护
支持基于角色和基于属性的访问控制

作者: Athena AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .auth_manager import Permission, UserRole

logger = logging.getLogger(__name__)


class Resource(Enum):
    """资源类型枚举"""

    AGENT = "agent"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    API = "api"
    SYSTEM = "system"
    DATA = "data"
    CONFIG = "config"


class Action(Enum):
    """操作类型枚举"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class AccessDecision(Enum):
    """访问决策枚举"""

    ALLOW = "allow"
    DENY = "deny"
    ABSTAIN = "abstain"


@dataclass
class ResourcePolicy:
    """资源策略"""

    resource: Resource
    action: Action
    effect: AccessDecision
    conditions: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessRequest:
    """访问请求"""

    user_id: str
    resource: Resource
    action: Action
    resource_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    ip_address: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AccessResult:
    """访问结果"""

    decision: AccessDecision
    reason: str
    policies_applied: list[str] = field(default_factory=list)
    processing_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class ConditionEvaluator:
    """条件评估器"""

    @staticmethod
    def evaluate_time_condition(condition: dict[str, Any], context: dict[str, Any]) -> bool:
        """评估时间条件"""
        current_time = datetime.now()

        # 时间范围条件
        if "start_time" in condition and "end_time" in condition:
            start = datetime.strptime(condition["start_time"], "%H:%M").time()
            end = datetime.strptime(condition["end_time"], "%H:%M").time()
            current = current_time.time()

            if start <= end:
                return start <= current <= end
            else:
                # 跨午夜的情况
                return current >= start or current <= end

        # 星期条件
        if "allowed_days" in condition:
            allowed_days = set(condition["allowed_days"])
            current_day = current_time.strftime("%A").lower()
            return current_day in allowed_days

        return True

    @staticmethod
    def evaluate_ip_condition(condition: dict[str, Any], context: dict[str, Any]) -> bool:
        """评估IP条件"""
        if "ip_address" not in context:
            return False

        ip = context["ip_address"]

        # 白名单
        if "allowed_ips" in condition:
            allowed_ips = set(condition["allowed_ips"])
            if ip not in allowed_ips:
                return False

        # 黑名单
        if "blocked_ips" in condition:
            blocked_ips = set(condition["blocked_ips"])
            if ip in blocked_ips:
                return False

        # IP段匹配
        if "allowed_subnets" in condition:
            import ipaddress

            try:
                user_ip = ipaddress.ip_address(ip)
                for subnet in condition["allowed_subnets"]:
                    if user_ip in ipaddress.ip_network(subnet):
                        return True
                return False
            except ValueError:
                return False

        return True

    @staticmethod
    def evaluate_attribute_condition(condition: dict[str, Any], context: dict[str, Any]) -> bool:
        """评估属性条件"""
        for attr, expected_value in condition.items():
            if attr == "user_attributes":
                # 用户属性条件
                if "user_attributes" not in context:
                    return False

                user_attrs = context["user_attributes"]
                for user_attr, user_value in expected_value.items():
                    if user_attr not in user_attrs or user_attrs[user_attr] != user_value:
                        return False
            elif attr == "resource_attributes":
                # 资源属性条件
                if "resource_attributes" not in context:
                    return False

                resource_attrs = context["resource_attributes"]
                for res_attr, res_value in expected_value.items():
                    if res_attr not in resource_attrs or resource_attrs[res_attr] != res_value:
                        return False
            else:
                # 通用属性条件
                if attr not in context or context[attr] != expected_value:
                    return False

        return True

    @staticmethod
    def evaluate_rate_limit_condition(condition: dict[str, Any], context: dict[str, Any]) -> bool:
        """评估频率限制条件"""
        if "rate_limit" not in context:
            return True

        rate_limit = condition["rate_limit"]
        current_requests = context.get("current_requests", 0)

        return current_requests <= rate_limit


class PolicyEngine:
    """策略引擎"""

    def __init__(self):
        self.policies: list[ResourcePolicy] = []
        self.role_based_policies: dict[UserRole, list[ResourcePolicy]] = {}
        self.resource_based_policies: dict[Resource, list[ResourcePolicy]] = {}
        self.condition_evaluator = ConditionEvaluator()
        self.lock = asyncio.Lock()

    async def add_policy(
        self,
        policy: ResourcePolicy,
        roles: list[UserRole] | None = None,
        resources: list[Resource] | None = None,
    ):
        """添加策略"""
        async with self.lock:
            policy_id = f"{policy.resource.value}:{policy.action.value}:{len(self.policies)}"
            policy.metadata = policy.metadata or {}
            policy.metadata["policy_id"] = policy_id

            self.policies.append(policy)

            # 按角色分组
            if roles:
                for role in roles:
                    if role not in self.role_based_policies:
                        self.role_based_policies[role] = []
                    self.role_based_policies[role].append(policy)

            # 按资源分组
            if resources:
                for resource in resources:
                    if resource not in self.resource_based_policies:
                        self.resource_based_policies[resource] = []
                    self.resource_based_policies[resource].append(policy)

            logger.info(f"📋 添加策略: {policy_id} ({policy.effect.value})")

    async def remove_policy(self, policy_id: str) -> bool:
        """移除策略"""
        async with self.lock:
            for i, policy in enumerate(self.policies):
                if policy.metadata.get("policy_id") == policy_id:
                    self.policies.pop(i)

                    # 从角色分组中移除
                    for role, role_policies in self.role_based_policies.items():
                        self.role_based_policies[role] = [
                            p for p in role_policies if p.metadata.get("policy_id") != policy_id
                        ]

                    # 从资源分组中移除
                    for resource, resource_policies in self.resource_based_policies.items():
                        self.resource_based_policies[resource] = [
                            p for p in resource_policies if p.metadata.get("policy_id") != policy_id
                        ]

                    logger.info(f"🗑️ 移除策略: {policy_id}")
                    return True

            return False

    async def evaluate_access(
        self, request: AccessRequest, user_role: UserRole, user_permissions: set[Permission]
    ) -> AccessResult:
        """评估访问请求"""
        start_time = datetime.now()
        policies_applied = []

        # 获取适用的策略
        applicable_policies = []

        # 资源特定策略
        if request.resource in self.resource_based_policies:
            applicable_policies.extend(self.resource_based_policies[request.resource])

        # 角色特定策略
        if user_role in self.role_based_policies:
            applicable_policies.extend(self.role_based_policies[user_role])

        # 通用策略
        applicable_policies.extend(self.policies)

        # 按优先级排序
        applicable_policies.sort(key=lambda p: p.priority, reverse=True)

        # 评估策略
        for policy in applicable_policies:
            # 检查资源和操作匹配
            if policy.resource != request.resource or policy.action != request.action:
                continue

            # 评估条件
            if not self._evaluate_conditions(policy.conditions, request):
                continue

            policies_applied.append(policy.metadata.get("policy_id", "unknown"))

            # 应用策略效果
            processing_time = (datetime.now() - start_time).total_seconds()

            if policy.effect == AccessDecision.DENY:
                return AccessResult(
                    decision=AccessDecision.DENY,
                    reason=f"策略拒绝: {policy.description or '未指定原因'}",
                    policies_applied=policies_applied,
                    processing_time=processing_time,
                )
            elif policy.effect == AccessDecision.ALLOW:
                return AccessResult(
                    decision=AccessDecision.ALLOW,
                    reason=f"策略允许: {policy.description or '未指定原因'}",
                    policies_applied=policies_applied,
                    processing_time=processing_time,
                )

        # 检查基于权限的默认访问
        if self._check_permission_based_access(request, user_permissions):
            processing_time = (datetime.now() - start_time).total_seconds()
            return AccessResult(
                decision=AccessDecision.ALLOW,
                reason="基于权限的默认访问",
                policies_applied=policies_applied,
                processing_time=processing_time,
            )

        # 默认拒绝
        processing_time = (datetime.now() - start_time).total_seconds()
        return AccessResult(
            decision=AccessDecision.DENY,
            reason="默认拒绝:无适用策略",
            policies_applied=policies_applied,
            processing_time=processing_time,
        )

    def _evaluate_conditions(self, conditions: dict[str, Any], request: AccessRequest) -> bool:
        """评估策略条件"""
        if not conditions:
            return True

        context = {
            **request.context,
            "ip_address": request.ip_address,
            "timestamp": request.timestamp,
        }

        # 时间条件
        if "time" in conditions:
            if not self.condition_evaluator.evaluate_time_condition(conditions["time"], context):
                return False

        # IP条件
        if "ip" in conditions:
            if not self.condition_evaluator.evaluate_ip_condition(conditions["ip"], context):
                return False

        # 属性条件
        if "attributes" in conditions:
            if not self.condition_evaluator.evaluate_attribute_condition(
                conditions["attributes"], context
            ):
                return False

        # 频率限制条件
        if "rate_limit" in conditions:
            if not self.condition_evaluator.evaluate_rate_limit_condition(
                conditions["rate_limit"], context
            ):
                return False

        return True

    def _check_permission_based_access(
        self, request: AccessRequest, user_permissions: set[Permission]
    ) -> bool:
        """检查基于权限的默认访问"""
        # 资源-操作到权限的映射
        permission_map = {
            (Resource.AGENT, Action.CREATE): Permission.AGENT_CREATE,
            (Resource.AGENT, Action.READ): Permission.AGENT_READ,
            (Resource.AGENT, Action.UPDATE): Permission.AGENT_WRITE,
            (Resource.AGENT, Action.DELETE): Permission.AGENT_DELETE,
            (Resource.DATA, Action.READ): Permission.DATA_READ,
            (Resource.DATA, Action.WRITE): Permission.DATA_WRITE,
            (Resource.DATA, Action.DELETE): Permission.DATA_DELETE,
            (Resource.SYSTEM, Action.READ): Permission.SYSTEM_READ,
            (Resource.SYSTEM, Action.WRITE): Permission.SYSTEM_WRITE,
            (Resource.SYSTEM, Action.ADMIN): Permission.SYSTEM_ADMIN,
            (Resource.API, Action.READ): Permission.API_ACCESS,
            (Resource.API, Action.ADMIN): Permission.API_ADMIN,
        }

        required_permission = permission_map.get((request.resource, request.action))
        if required_permission:
            return required_permission in user_permissions

        return False

    async def get_policies(
        self, resource: Resource | None = None, action: Action | None = None
    ) -> list[dict[str, Any]]:
        """获取策略列表"""
        async with self.lock:
            policies = self.policies

            if resource:
                policies = [p for p in policies if p.resource == resource]
            if action:
                policies = [p for p in policies if p.action == action]

            return [
                {
                    "policy_id": p.metadata.get("policy_id"),
                    "resource": p.resource.value,
                    "action": p.action.value,
                    "effect": p.effect.value,
                    "conditions": p.conditions,
                    "priority": p.priority,
                    "description": p.description,
                    "created_at": p.created_at.isoformat(),
                }
                for p in policies
            ]


class AccessController:
    """访问控制器"""

    def __init__(self, auth_manager, config: dict[str, Any] | None = None):
        self.auth_manager = auth_manager
        self.config = config or {}
        self.initialized = False

        # 策略引擎
        self.policy_engine = PolicyEngine()

        # 访问日志
        self.access_logs: list[dict[str, Any]] = []
        self.max_log_entries = self.config.get("max_log_entries", 10000)

        # 速率限制跟踪
        self.rate_limiters: dict[str, dict[str, Any]] = {}

        logger.info("🛡️ 访问控制器创建")

    async def initialize(self):
        """初始化访问控制器"""
        if self.initialized:
            return

        logger.info("🚀 启动访问控制器")

        # 设置默认策略
        await self._setup_default_policies()

        self.initialized = True
        logger.info("✅ 访问控制器启动完成")

    async def _setup_default_policies(self):
        """设置默认策略"""
        from .auth_manager import UserRole

        # 管理员完全访问
        admin_policy = ResourcePolicy(
            resource=Resource.SYSTEM,
            action=Action.ADMIN,
            effect=AccessDecision.ALLOW,
            description="管理员完全访问权限",
            priority=100,
        )
        await self.policy_engine.add_policy(admin_policy, roles=[UserRole.ADMIN])

        # 开发者Agent管理权限
        developer_agent_policy = ResourcePolicy(
            resource=Resource.AGENT,
            action=Action.CREATE,
            effect=AccessDecision.ALLOW,
            description="开发者可以创建Agent",
            priority=90,
        )
        await self.policy_engine.add_policy(developer_agent_policy, roles=[UserRole.DEVELOPER])

        # 普通用户只读权限
        user_read_policy = ResourcePolicy(
            resource=Resource.AGENT,
            action=Action.READ,
            effect=AccessDecision.ALLOW,
            description="普通用户可以查看Agent",
            priority=80,
        )
        await self.policy_engine.add_policy(user_read_policy, roles=[UserRole.USER])

        # 访客限制访问
        guest_policy = ResourcePolicy(
            resource=Resource.SYSTEM,
            action=Action.ADMIN,
            effect=AccessDecision.DENY,
            description="访客禁止系统管理",
            priority=95,
        )
        await self.policy_engine.add_policy(guest_policy, roles=[UserRole.GUEST])

    async def check_access(
        self,
        user_id: str,
        resource: Resource,
        action: Action,
        resource_id: str | None = None,
        context: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AccessResult:
        """检查访问权限"""
        if not self.initialized:
            raise RuntimeError("访问控制器未初始化")

        start_time = datetime.now()

        # 获取用户信息
        user = self.auth_manager.users.get(user_id)
        if not user or not user.is_active:
            return AccessResult(
                decision=AccessDecision.DENY,
                reason="用户不存在或已禁用",
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

        # 构建访问请求
        request = AccessRequest(
            user_id=user_id,
            resource=resource,
            action=action,
            resource_id=resource_id,
            context=context or {},
            ip_address=ip_address,
            timestamp=start_time,
        )

        # 添加用户属性到上下文
        request.context["user_attributes"] = {
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
        }

        # 检查速率限制
        rate_limit_key = f"{user_id}:{resource.value}:{action.value}"
        if not self._check_rate_limit(rate_limit_key, user.role):
            return AccessResult(
                decision=AccessDecision.DENY,
                reason="超出速率限制",
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

        # 评估访问请求
        result = await self.policy_engine.evaluate_access(request, user.role, user.permissions)

        # 记录访问日志
        await self._log_access_attempt(request, result, user)

        return result

    def _check_rate_limit(self, key: str, role: UserRole) -> bool:
        """检查速率限制"""
        # 角色特定的速率限制
        rate_limits = {
            UserRole.ADMIN: 1000,  # 管理员:1000请求/分钟
            UserRole.DEVELOPER: 500,  # 开发者:500请求/分钟
            UserRole.USER: 100,  # 用户:100请求/分钟
            UserRole.GUEST: 20,  # 访客:20请求/分钟
            UserRole.AGENT: 200,  # Agent:200请求/分钟
        }

        limit = rate_limits.get(role, 50)
        now = datetime.now()

        if key not in self.rate_limiters:
            self.rate_limiters[key] = {"count": 0, "reset_time": now + timedelta(minutes=1)}

        rate_limiter = self.rate_limiters[key]

        # 重置计数器
        if now > rate_limiter["reset_time"]:
            rate_limiter["count"] = 0
            rate_limiter["reset_time"] = now + timedelta(minutes=1)

        # 检查限制
        if rate_limiter["count"] >= limit:
            return False

        rate_limiter["count"] += 1
        return True

    async def _log_access_attempt(self, request: AccessRequest, result: AccessResult, user):
        """记录访问日志"""
        log_entry = {
            "timestamp": request.timestamp.isoformat(),
            "user_id": request.user_id,
            "username": user.username,
            "user_role": user.role.value,
            "resource": request.resource.value,
            "action": request.action.value,
            "resource_id": request.resource_id,
            "ip_address": request.ip_address,
            "decision": result.decision.value,
            "reason": result.reason,
            "policies_applied": result.policies_applied,
            "processing_time": result.processing_time,
        }

        self.access_logs.append(log_entry)

        # 限制日志条目数量
        if len(self.access_logs) > self.max_log_entries:
            self.access_logs = self.access_logs[-self.max_log_entries :]

        # 记录到日志
        log_level = logging.INFO if result.decision == AccessDecision.ALLOW else logging.WARNING
        logger.log(
            log_level,
            f"🔒 访问{'允许' if result.decision == AccessDecision.ALLOW else '拒绝'}: "
            f"{user.username} -> {request.resource.value}:{request.action.value}",
        )

    async def add_policy(
        self,
        resource: Resource,
        action: Action,
        effect: AccessDecision,
        conditions: dict[str, Any] | None = None,
        description: str = "",
        priority: int = 0,
    ) -> str:
        """添加访问策略"""
        from .auth_manager import ResourcePolicy

        policy = ResourcePolicy(
            resource=resource,
            action=action,
            effect=effect,
            conditions=conditions or {},
            priority=priority,
            description=description,
        )

        await self.policy_engine.add_policy(policy)
        return policy.metadata.get("policy_id")

    async def remove_policy(self, policy_id: str) -> bool:
        """移除访问策略"""
        return await self.policy_engine.remove_policy(policy_id)

    async def get_access_logs(
        self,
        user_id: str | None = None,
        resource: Resource | None = None,
        action: Action | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """获取访问日志"""
        logs = self.access_logs

        # 过滤条件
        if user_id:
            logs = [log for log in logs if log["user_id"] == user_id]
        if resource:
            logs = [log for log in logs if log["resource"] == resource.value]
        if action:
            logs = [log for log in logs if log["action"] == action.value]

        # 按时间倒序排列
        logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)

        return logs[:limit]

    async def get_access_stats(self) -> dict[str, Any]:
        """获取访问统计"""
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)

        # 过滤时间范围内的日志
        recent_logs = [
            log for log in self.access_logs if datetime.fromisoformat(log["timestamp"]) >= last_hour
        ]
        daily_logs = [
            log for log in self.access_logs if datetime.fromisoformat(log["timestamp"]) >= last_day
        ]

        # 统计决策
        recent_decisions = {"allow": 0, "deny": 0}
        daily_decisions = {"allow": 0, "deny": 0}

        for log in recent_logs:
            if log["decision"] == "allow":
                recent_decisions["allow"] += 1
            else:
                recent_decisions["deny"] += 1

        for log in daily_logs:
            if log["decision"] == "allow":
                daily_decisions["allow"] += 1
            else:
                daily_decisions["deny"] += 1

        return {
            "total_requests": len(self.access_logs),
            "last_hour": {
                "total": len(recent_logs),
                "allowed": recent_decisions["allow"],
                "denied": recent_decisions["deny"],
                "allow_rate": recent_decisions["allow"] / max(len(recent_logs), 1) * 100,
            },
            "last_day": {
                "total": len(daily_logs),
                "allowed": daily_decisions["allow"],
                "denied": daily_decisions["deny"],
                "allow_rate": daily_decisions["allow"] / max(len(daily_logs), 1) * 100,
            },
            "active_rate_limiters": len(self.rate_limiters),
            "timestamp": now.isoformat(),
        }

    async def cleanup_old_logs(self, days: int = 30):
        """清理旧日志"""
        cutoff_time = datetime.now() - timedelta(days=days)
        original_count = len(self.access_logs)

        self.access_logs = [
            log
            for log in self.access_logs
            if datetime.fromisoformat(log["timestamp"]) >= cutoff_time
        ]

        removed_count = original_count - len(self.access_logs)
        if removed_count > 0:
            logger.info(f"🧹 清理旧访问日志: {removed_count} 条")

    async def shutdown(self):
        """关闭访问控制器"""
        logger.info("🔄 关闭访问控制器")
        self.initialized = False
        logger.info("✅ 访问控制器已关闭")


__all__ = [
    "AccessController",
    "AccessDecision",
    "AccessRequest",
    "AccessResult",
    "Action",
    "ConditionEvaluator",
    "PolicyEngine",
    "Resource",
    "ResourcePolicy",
]
