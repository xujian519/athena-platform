#!/usr/bin/env python3
"""
企业级多租户系统
Enterprise Multi-Tenant System

实现企业级特性:
1. 多租户隔离和管理
2. 租户级资源配置
3. 租户数据隔离
4. 租户性能监控
5. 租户计费系统
6. 租户生命周期管理

作者: Athena平台团队
创建时间: 2025-12-30
版本: v1.0.0 "企业级"
"""

from __future__ import annotations
import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TenantStatus(Enum):
    """租户状态"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    TRIAL = "trial"


class TenantTier(Enum):
    """租户等级"""

    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class TenantConfig:
    """租户配置"""

    tenant_id: str
    tenant_name: str
    tier: TenantTier
    status: TenantStatus
    max_users: int
    max_storage_gb: float
    max_requests_per_day: int
    allowed_capabilities: list[str]
    created_at: datetime
    expires_at: datetime | None = None

    # 资源使用
    used_storage_gb: float = 0.0
    daily_request_count: int = 0

    # 自定义配置
    custom_settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantMetrics:
    """租户指标"""

    tenant_id: str
    timestamp: datetime
    active_users: int
    total_requests: int
    avg_response_time_ms: float
    error_rate: float
    storage_used_gb: float
    cpu_usage_percent: float
    memory_usage_percent: float


class MultiTenantSystem:
    """
    企业级多租户系统

    核心功能:
    1. 租户管理(创建、更新、删除)
    2. 租户隔离(数据、资源、配置)
    3. 资源配额(存储、请求、用户)
    4. 性能监控(租户级监控)
    5. 计费系统(按使用量计费)
    6. 生命周期管理(试用→正式→续费)
    """

    def __init__(self):
        # 租户存储
        self.tenants: dict[str, TenantConfig] = {}

        # 租户索引
        self.tenant_by_name: dict[str, str] = {}
        self.tenant_by_tier: dict[TenantTier, set[str]] = defaultdict(set)

        # 性能指标
        self.metrics_history: dict[str, list[TenantMetrics]] = defaultdict(list)

        # 资源配额定义
        self.tier_quotas = {
            TenantTier.BASIC: {
                "max_users": 5,
                "max_storage_gb": 10,
                "max_requests_per_day": 1000,
                "allowed_capabilities": ["daily_chat", "platform_controller"],
            },
            TenantTier.STANDARD: {
                "max_users": 20,
                "max_storage_gb": 50,
                "max_requests_per_day": 10000,
                "allowed_capabilities": [
                    "daily_chat",
                    "platform_controller",
                    "coding_assistant",
                    "patent",
                ],
            },
            TenantTier.PREMIUM: {
                "max_users": 100,
                "max_storage_gb": 200,
                "max_requests_per_day": 100000,
                "allowed_capabilities": [
                    "daily_chat",
                    "platform_controller",
                    "coding_assistant",
                    "patent",
                    "legal",
                    "nlp",
                ],
            },
            TenantTier.ENTERPRISE: {
                "max_users": -1,  # 无限
                "max_storage_gb": -1,
                "max_requests_per_day": -1,
                "allowed_capabilities": ["all"],  # 全部能力
            },
        }

        # 计费配置
        self.pricing = {
            TenantTier.BASIC: {"monthly": 99, "per_gb": 1.0, "per_request": 0.001},
            TenantTier.STANDARD: {"monthly": 299, "per_gb": 0.5, "per_request": 0.0005},
            TenantTier.PREMIUM: {"monthly": 999, "per_gb": 0.2, "per_request": 0.0002},
            TenantTier.ENTERPRISE: {"monthly": 2999, "per_gb": 0.1, "per_request": 0.0001},
        }

        logger.info("🏢 企业级多租户系统初始化完成")

    def create_tenant(
        self, tenant_name: str, tier: TenantTier, trial_days: int = 30
    ) -> TenantConfig:
        """
        创建新租户

        Args:
            tenant_name: 租户名称
            tier: 租户等级
            trial_days: 试用天数

        Returns:
            TenantConfig: 租户配置
        """
        # 生成租户ID
        tenant_id = self._generate_tenant_id(tenant_name)

        # 获取配额
        quota = self.tier_quotas[tier]

        # 创建租户配置
        tenant = TenantConfig(
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            tier=tier,
            status=TenantStatus.TRIAL,
            max_users=quota["max_users"],
            max_storage_gb=quota["max_storage_gb"],
            max_requests_per_day=quota["max_requests_per_day"],
            allowed_capabilities=quota["allowed_capabilities"],
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=trial_days),
        )

        # 保存租户
        self.tenants[tenant_id] = tenant
        self.tenant_by_name[tenant_name] = tenant_id
        self.tenant_by_tier[tier].add(tenant_id)

        logger.info(f"🏢 租户已创建: {tenant_name} ({tier.value}) - 试用期{trial_days}天")

        return tenant

    def _generate_tenant_id(self, tenant_name: str) -> str:
        """生成租户ID"""
        # 使用名称+时间戳+哈希生成唯一ID
        timestamp = datetime.now().strftime("%Y%m%d")
        hash_val = hashlib.md5(
            f"{tenant_name}{timestamp}".encode('utf-8', usedforsecurity=False), usedforsecurity=False
        ).hexdigest()[:8]
        return f"tenant_{timestamp}_{hash_val}"

    async def check_tenant_access(
        self, tenant_id: str, capability: str, user_id: str | None = None
    ) -> dict[str, Any]:
        """
        检查租户访问权限

        Args:
            tenant_id: 租户ID
            capability: 需要的能力
            user_id: 用户ID

        Returns:
            访问检查结果
        """
        tenant = self.tenants.get(tenant_id)

        if not tenant:
            return {"allowed": False, "reason": "tenant_not_found", "message": "租户不存在"}

        # 检查状态
        if tenant.status != TenantStatus.ACTIVE and tenant.status != TenantStatus.TRIAL:
            return {
                "allowed": False,
                "reason": "tenant_suspended",
                "message": f"租户状态为: {tenant.status.value}",
            }

        # 检查过期
        if tenant.expires_at and datetime.now() > tenant.expires_at:
            return {"allowed": False, "reason": "tenant_expired", "message": "租户已过期"}

        # 检查能力权限
        if "all" not in tenant.allowed_capabilities:
            if capability not in tenant.allowed_capabilities:
                return {
                    "allowed": False,
                    "reason": "capability_not_allowed",
                    "message": f"租户等级不支持: {capability}",
                }

        # 检查请求配额
        if tenant.daily_request_count >= tenant.max_requests_per_day:
            return {"allowed": False, "reason": "quota_exceeded", "message": "每日请求配额已用完"}

        # 检查存储配额
        if tenant.used_storage_gb >= tenant.max_storage_gb:
            return {"allowed": False, "reason": "storage_exceeded", "message": "存储配额已用完"}

        return {
            "allowed": True,
            "tenant_id": tenant_id,
            "tier": tenant.tier.value,
            "remaining_requests": tenant.max_requests_per_day - tenant.daily_request_count,
            "remaining_storage_gb": tenant.max_storage_gb - tenant.used_storage_gb,
        }

    async def record_tenant_usage(
        self, tenant_id: str, request_type: str, storage_delta_gb: float = 0.0
    ):
        """记录租户使用量"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return

        # 更新请求计数
        tenant.daily_request_count += 1

        # 更新存储使用
        tenant.used_storage_gb += storage_delta_gb

        logger.debug(
            f"📊 租户使用: {tenant_id} - 请求: {tenant.daily_request_count}, "
            f"存储: {tenant.used_storage_gb:.2f}GB"
        )

    async def get_tenant_metrics(self, tenant_id: str, hours: int = 24) -> list[TenantMetrics]:
        """获取租户指标"""
        metrics_list = self.metrics_history.get(tenant_id, [])

        # 过滤时间范围
        cutoff_time = datetime.now() - timedelta(hours=hours)
        filtered = [m for m in metrics_list if m.timestamp > cutoff_time]

        return filtered

    async def collect_tenant_metrics(self, tenant_id: str) -> TenantMetrics:
        """收集租户当前指标"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return None

        metrics = TenantMetrics(
            tenant_id=tenant_id,
            timestamp=datetime.now(),
            active_users=0,  # 从实际系统获取
            total_requests=tenant.daily_request_count,
            avg_response_time_ms=0.0,
            error_rate=0.0,
            storage_used_gb=tenant.used_storage_gb,
            cpu_usage_percent=0.0,
            memory_usage_percent=0.0,
        )

        # 保存历史
        self.metrics_history[tenant_id].append(metrics)

        # 保持历史长度(最近7天)
        cutoff = datetime.now() - timedelta(days=7)
        self.metrics_history[tenant_id] = [
            m for m in self.metrics_history[tenant_id] if m.timestamp > cutoff
        ]

        return metrics

    async def calculate_tenant_billing(
        self, tenant_id: str, month: datetime | None = None
    ) -> dict[str, Any]:
        """
        计算租户账单

        Args:
            tenant_id: 租户ID
            month: 账单月份(默认为当前月)

        Returns:
            账单详情
        """
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return None

        if month is None:
            month = datetime.now()

        pricing = self.pricing[tenant.tier]

        # 基础费用
        base_fee = pricing["monthly"]

        # 存储费用
        storage_fee = 0
        if tenant.used_storage_gb > tenant.max_storage_gb:
            extra_storage = tenant.used_storage_gb - tenant.max_storage_gb
            storage_fee = extra_storage * pricing["per_gb"]

        # 请求费用
        request_fee = 0
        if tenant.daily_request_count > tenant.max_requests_per_day:
            # 假设30天
            extra_requests = (tenant.daily_request_count - tenant.max_requests_per_day) * 30
            request_fee = extra_requests * pricing["per_request"]

        total_fee = base_fee + storage_fee + request_fee

        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.tenant_name,
            "tier": tenant.tier.value,
            "month": month.strftime("%Y-%m"),
            "billing": {
                "base_fee": base_fee,
                "storage_fee": storage_fee,
                "request_fee": request_fee,
                "total_fee": total_fee,
            },
            "usage": {
                "storage_used_gb": tenant.used_storage_gb,
                "storage_quota_gb": tenant.max_storage_gb,
                "requests_per_day": tenant.daily_request_count,
                "request_quota": tenant.max_requests_per_day,
            },
        }

    async def upgrade_tier(self, tenant_id: str, new_tier: TenantTier) -> bool:
        """升级租户等级"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return False

        old_tier = tenant.tier

        # 更新租户配额
        quota = self.tier_quotas[new_tier]
        tenant.tier = new_tier
        tenant.max_users = quota["max_users"]
        tenant.max_storage_gb = quota["max_storage_gb"]
        tenant.max_requests_per_day = quota["max_requests_per_day"]
        tenant.allowed_capabilities = quota["allowed_capabilities"]

        # 更新索引
        self.tenant_by_tier[old_tier].discard(tenant_id)
        self.tenant_by_tier[new_tier].add(tenant_id)

        logger.info(f"⬆️ 租户升级: {tenant.tenant_name} {old_tier.value} → {new_tier.value}")

        return True

    async def get_all_tenants(
        self, status_filter: TenantStatus | None = None
    ) -> list[TenantConfig]:
        """获取所有租户"""
        tenants = list(self.tenants.values())

        if status_filter:
            tenants = [t for t in tenants if t.status == status_filter]

        return tenants

    async def get_system_overview(self) -> dict[str, Any]:
        """获取系统概览"""
        total_tenants = len(self.tenants)

        tenants_by_status = defaultdict(int)
        tenants_by_tier = defaultdict(int)

        total_users = 0
        total_storage = 0.0
        total_requests = 0

        for tenant in self.tenants.values():
            tenants_by_status[tenant.status.value] += 1
            tenants_by_tier[tenant.tier.value] += 1

            if tenant.max_users > 0:
                total_users += tenant.max_users
            total_storage += tenant.used_storage_gb
            total_requests += tenant.daily_request_count

        # 估算月收入
        estimated_mrr = sum(
            self.pricing[tenant.tier]["monthly"]
            for tenant in self.tenants.values()
            if tenant.status == TenantStatus.ACTIVE
        )

        return {
            "tenants": {
                "total": total_tenants,
                "by_status": dict(tenants_by_status),
                "by_tier": dict(tenants_by_tier),
            },
            "usage": {
                "total_users": total_users,
                "total_storage_gb": total_storage,
                "total_requests_per_day": total_requests,
            },
            "revenue": {"estimated_monthly_recurring_revenue": estimated_mrr},
        }


# 单例实例
_multitenant_system: MultiTenantSystem | None = None


def get_multitenant_system() -> MultiTenantSystem:
    """获取多租户系统单例"""
    global _multitenant_system
    if _multitenant_system is None:
        _multitenant_system = MultiTenantSystem()
    return _multitenant_system
