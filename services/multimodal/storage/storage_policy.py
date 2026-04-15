#!/usr/bin/env python3
"""
存储策略管理器
Storage Policy Manager

定义和管理文件的存储策略、生命周期规则、迁移策略等
"""

import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .distributed_storage import StorageTier, StorageType

logger = logging.getLogger(__name__)

class LifecycleAction(Enum):
    """生命周期动作"""
    TRANSITION = "transition"    # 转换存储层级
    DELETE = "delete"           # 删除文件
    COMPRESS = "compress"       # 压缩文件
    ARCHIVE = "archive"         # 归档文件

class TriggerType(Enum):
    """触发类型"""
    AGE_DAYS = "age_days"       # 按天数
    ACCESS_COUNT = "access_count"  # 按访问次数
    SIZE_LIMIT = "size_limit"   # 按大小限制
    CUSTOM = "custom"           # 自定义规则

@dataclass
class LifecycleRule:
    """生命周期规则"""
    rule_id: str
    name: str
    description: str
    enabled: bool = True
    priority: int = 0  # 优先级，数字越大优先级越高
    trigger_type: TriggerType = TriggerType.AGE_DAYS
    trigger_value: int = 30  # 触发值
    target_tier: StorageTier | None = None
    action: LifecycleAction = LifecycleAction.TRANSITION
    conditions: dict[str, Any] = None
    file_type_filters: list[str] = None  # 文件类型过滤
    size_filters: dict[str, int] = None   # 大小过滤 (min_size, max_size)
    custom_handler: Callable | None = None

    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}
        if self.file_type_filters is None:
            self.file_type_filters = []
        if self.size_filters is None:
            self.size_filters = {}

@dataclass
class StoragePolicy:
    """存储策略"""
    policy_id: str
    name: str
    description: str
    default_tier: StorageTier = StorageTier.HOT
    replication_enabled: bool = True
    compression_enabled: bool = False
    encryption_enabled: bool = False
    backup_enabled: bool = True
    lifecycle_rules: list[LifecycleRule] = None
    storage_preferences: dict[StorageTier, list[StorageType]] = None

    def __post_init__(self):
        if self.lifecycle_rules is None:
            self.lifecycle_rules = []
        if self.storage_preferences is None:
            self.storage_preferences = {}

class StoragePolicyManager:
    """存储策略管理器"""

    def __init__(self):
        self.policies: dict[str, StoragePolicy] = {}
        self.file_policy_mapping: dict[str, str] = {}  # file_id -> policy_id
        self.default_policy_id: str | None = None
        self.lifecycle_task: asyncio.Task | None = None
        self.running = False
        self.lifecycle_interval = 3600  # 1小时执行一次生命周期检查

    def create_policy(self, policy: StoragePolicy) -> str:
        """创建存储策略"""
        self.policies[policy.policy_id] = policy

        # 设置默认策略
        if self.default_policy_id is None:
            self.default_policy_id = policy.policy_id

        logger.info(f"创建存储策略: {policy.name} ({policy.policy_id})")
        return policy.policy_id

    def get_policy(self, policy_id: str) -> StoragePolicy | None:
        """获取存储策略"""
        return self.policies.get(policy_id)

    def update_policy(self, policy_id: str, policy: StoragePolicy) -> bool:
        """更新存储策略"""
        if policy_id not in self.policies:
            return False

        self.policies[policy_id] = policy
        logger.info(f"更新存储策略: {policy.name} ({policy_id})")
        return True

    def delete_policy(self, policy_id: str) -> bool:
        """删除存储策略"""
        if policy_id not in self.policies:
            return False

        # 不能删除默认策略
        if policy_id == self.default_policy_id:
            logger.warning("无法删除默认存储策略")
            return False

        # 解除文件映射
        files_to_update = [
            file_id for file_id, pid in self.file_policy_mapping.items()
            if pid == policy_id
        ]
        for file_id in files_to_update:
            self.file_policy_mapping[file_id] = self.default_policy_id

        del self.policies[policy_id]
        logger.info(f"删除存储策略: {policy_id}")
        return True

    def assign_file_policy(self, file_id: str, policy_id: str,
                          file_type: str = None, file_size: int = 0) -> bool:
        """为文件分配存储策略"""
        if policy_id not in self.policies:
            # 如果策略不存在，使用默认策略
            policy_id = self.default_policy_id

        self.file_policy_mapping[file_id] = policy_id

        # 应用策略的初始设置
        policy = self.policies[policy_id]
        logger.info(f"文件 {file_id} 分配策略: {policy.name}")

        return True

    def get_file_policy(self, file_id: str) -> StoragePolicy | None:
        """获取文件的存储策略"""
        policy_id = self.file_policy_mapping.get(file_id, self.default_policy_id)
        return self.policies.get(policy_id) if policy_id else None

    def add_lifecycle_rule(self, policy_id: str, rule: LifecycleRule) -> bool:
        """添加生命周期规则"""
        policy = self.get_policy(policy_id)
        if not policy:
            return False

        policy.lifecycle_rules.append(rule)
        # 按优先级排序
        policy.lifecycle_rules.sort(key=lambda r: r.priority, reverse=True)

        logger.info(f"策略 {policy_id} 添加生命周期规则: {rule.name}")
        return True

    def remove_lifecycle_rule(self, policy_id: str, rule_id: str) -> bool:
        """移除生命周期规则"""
        policy = self.get_policy(policy_id)
        if not policy:
            return False

        original_count = len(policy.lifecycle_rules)
        policy.lifecycle_rules = [
            rule for rule in policy.lifecycle_rules
            if rule.rule_id != rule_id
        ]

        removed = len(policy.lifecycle_rules) < original_count
        if removed:
            logger.info(f"策略 {policy_id} 移除生命周期规则: {rule_id}")

        return removed

    async def start_lifecycle_management(self):
        """启动生命周期管理"""
        if self.running:
            return

        self.running = True
        self.lifecycle_task = asyncio.create_task(self._lifecycle_loop())
        logger.info("生命周期管理已启动")

    async def stop_lifecycle_management(self):
        """停止生命周期管理"""
        self.running = False
        if self.lifecycle_task:
            self.lifecycle_task.cancel()
            try:
                await self.lifecycle_task
            except asyncio.CancelledError as e:
                logger.error(f"Error: {e}", exc_info=True)
        logger.info("生命周期管理已停止")

    async def _lifecycle_loop(self):
        """生命周期管理循环"""
        while self.running:
            try:
                await self._process_lifecycle_rules()
                await asyncio.sleep(self.lifecycle_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"生命周期处理异常: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟

    async def _process_lifecycle_rules(self):
        """处理生命周期规则"""
        # 这里需要遍历所有文件并应用生命周期规则
        # 实际实现时需要从数据库或存储中获取文件列表
        pass

    async def evaluate_file_lifecycle(self, file_id: str, file_info: dict[str, Any]) -> list[dict[str, Any]]:
        """评估单个文件的生命周期"""
        policy = self.get_file_policy(file_id)
        if not policy:
            return []

        actions = []
        current_time = datetime.now()

        for rule in policy.lifecycle_rules:
            if not rule.enabled:
                continue

            # 检查文件类型过滤
            if rule.file_type_filters and file_info.get('file_type') not in rule.file_type_filters:
                continue

            # 检查大小过滤
            if rule.size_filters:
                file_size = file_info.get('file_size', 0)
                min_size = rule.size_filters.get('min_size', 0)
                max_size = rule.size_filters.get('max_size', float('inf'))
                if file_size < min_size or file_size > max_size:
                    continue

            # 评估触发条件
            if await self._evaluate_trigger_condition(rule, file_info, current_time):
                action = {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.name,
                    "action": rule.action.value,
                    "target_tier": rule.target_tier.value if rule.target_tier else None,
                    "priority": rule.priority,
                    "evaluated_at": current_time.isoformat()
                }
                actions.append(action)

                # 如果是高优先级规则，可以停止评估
                if rule.priority >= 100:
                    break

        return actions

    async def _evaluate_trigger_condition(self, rule: LifecycleRule,
                                        file_info: dict[str, Any],
                                        current_time: datetime) -> bool:
        """评估触发条件"""
        if rule.trigger_type == TriggerType.AGE_DAYS:
            # 基于文件年龄
            created_time = datetime.fromisoformat(
                file_info.get('created_at', current_time.isoformat())
            )
            age_days = (current_time - created_time).days
            return age_days >= rule.trigger_value

        elif rule.trigger_type == TriggerType.ACCESS_COUNT:
            # 基于访问次数
            access_count = file_info.get('access_count', 0)
            return access_count >= rule.trigger_value

        elif rule.trigger_type == TriggerType.SIZE_LIMIT:
            # 基于大小限制
            file_size = file_info.get('file_size', 0)
            return file_size >= rule.trigger_value

        elif rule.trigger_type == TriggerType.CUSTOM:
            # 自定义规则
            if rule.custom_handler:
                return await rule.custom_handler(file_info, current_time, rule.trigger_value)

        return False

    def create_default_policy(self) -> str:
        """创建默认存储策略"""
        policy = StoragePolicy(
            policy_id="default",
            name="默认存储策略",
            description="系统的默认存储策略",
            default_tier=StorageTier.HOT,
            replication_enabled=True,
            compression_enabled=False,
            encryption_enabled=False,
            backup_enabled=True,
            storage_preferences={
                StorageTier.HOT: [StorageType.LOCAL],
                StorageTier.WARM: [StorageType.S3],
                StorageTier.COLD: [StorageType.ALIYUN_OSS]
            }
        )

        # 添加生命周期规则
        rules = [
            LifecycleRule(
                rule_id="hot_to_warm_30d",
                name="30天后热转温存储",
                description="文件30天未访问后从热存储迁移到温存储",
                priority=80,
                trigger_type=TriggerType.AGE_DAYS,
                trigger_value=30,
                target_tier=StorageTier.WARM,
                action=LifecycleAction.TRANSITION
            ),
            LifecycleRule(
                rule_id="warm_to_cold_90d",
                name="90天后温转冷存储",
                description="文件90天未访问后从温存储迁移到冷存储",
                priority=70,
                trigger_type=TriggerType.AGE_DAYS,
                trigger_value=90,
                target_tier=StorageTier.COLD,
                action=LifecycleAction.TRANSITION
            ),
            LifecycleRule(
                rule_id="delete_365d",
                name="365天后删除",
                description="文件365天后自动删除",
                priority=60,
                trigger_type=TriggerType.AGE_DAYS,
                trigger_value=365,
                action=LifecycleAction.DELETE
            ),
            LifecycleRule(
                rule_id="compress_large_files",
                name="压缩大文件",
                description="大于100MB的文件自动压缩",
                priority=90,
                trigger_type=TriggerType.SIZE_LIMIT,
                trigger_value=100 * 1024 * 1024,
                action=LifecycleAction.COMPRESS,
                size_filters={"min_size": 100 * 1024 * 1024}
            )
        ]

        policy.lifecycle_rules = rules

        return self.create_policy(policy)

    def get_policy_summary(self, policy_id: str) -> dict[str, Any]:
        """获取策略摘要"""
        policy = self.get_policy(policy_id)
        if not policy:
            return {}

        # 统计文件分配情况
        file_count = sum(
            1 for pid in self.file_policy_mapping.values()
            if pid == policy_id
        )

        return {
            "policy_id": policy.policy_id,
            "name": policy.name,
            "description": policy.description,
            "default_tier": policy.default_tier.value,
            "replication_enabled": policy.replication_enabled,
            "compression_enabled": policy.compression_enabled,
            "encryption_enabled": policy.encryption_enabled,
            "backup_enabled": policy.backup_enabled,
            "lifecycle_rules_count": len(policy.lifecycle_rules),
            "assigned_files_count": file_count,
            "is_default": policy_id == self.default_policy_id
        }

    def export_policies(self) -> str:
        """导出策略配置"""
        policies_data = {
            "default_policy_id": self.default_policy_id,
            "policies": {
                policy_id: asdict(policy)
                for policy_id, policy in self.policies.items()
            },
            "file_policy_mapping": self.file_policy_mapping,
            "exported_at": datetime.now().isoformat()
        }

        return json.dumps(policies_data, ensure_ascii=False, indent=2)

    def import_policies(self, policies_json: str, merge: bool = False) -> bool:
        """导入策略配置"""
        try:
            policies_data = json.loads(policies_json)

            if not merge:
                # 替换模式：清空现有策略
                self.policies.clear()
                self.file_policy_mapping.clear()

            # 导入策略
            for policy_id, policy_data in policies_data.get("policies", {}).items():
                # 重建对象
                policy_data['default_tier'] = StorageTier(policy_data.get('default_tier', 'hot'))
                policy_data['lifecycle_rules'] = [
                    LifecycleRule(
                        rule_id=rule.get('rule_id'),
                        name=rule.get('name'),
                        description=rule.get('description'),
                        enabled=rule.get('enabled', True),
                        priority=rule.get('priority', 0),
                        trigger_type=TriggerType(rule.get('trigger_type', 'age_days')),
                        trigger_value=rule.get('trigger_value', 30),
                        target_tier=StorageTier(rule['target_tier']) if rule.get('target_tier') else None,
                        action=LifecycleAction(rule.get('action', 'transition')),
                        conditions=rule.get('conditions', {}),
                        file_type_filters=rule.get('file_type_filters', []),
                        size_filters=rule.get('size_filters', {})
                    )
                    for rule in policy_data.get('lifecycle_rules', [])
                ]

                policy = StoragePolicy(**policy_data)
                self.policies[policy_id] = policy

            # 导入文件映射
            if merge:
                self.file_policy_mapping.update(policies_data.get("file_policy_mapping", {}))
            else:
                self.file_policy_mapping = policies_data.get("file_policy_mapping", {})

            # 设置默认策略
            self.default_policy_id = policies_data.get("default_policy_id")

            logger.info(f"导入策略配置成功，共 {len(self.policies)} 个策略")
            return True

        except Exception as e:
            logger.error(f"导入策略配置失败: {e}")
            return False

# 全局存储策略管理器实例
storage_policy_manager = StoragePolicyManager()

# 使用示例
if __name__ == "__main__":
    async def example_usage():
        """使用示例"""
        # 创建默认策略
        storage_policy_manager.create_default_policy()

        # 创建自定义策略
        custom_policy = StoragePolicy(
            policy_id="archive_policy",
            name="归档策略",
            description="长期归档存储策略",
            default_tier=StorageTier.WARM,
            compression_enabled=True,
            encryption_enabled=True
        )

        custom_policy_id = storage_policy_manager.create_policy(custom_policy)

        # 添加生命周期规则
        rule = LifecycleRule(
            rule_id="compress_7d",
            name="7天后压缩",
            trigger_type=TriggerType.AGE_DAYS,
            trigger_value=7,
            action=LifecycleAction.COMPRESS
        )

        storage_policy_manager.add_lifecycle_rule(custom_policy_id, rule)

        # 为文件分配策略
        file_id = "test_file_123"
        storage_policy_manager.assign_file_policy(file_id, custom_policy_id)

        # 评估文件生命周期
        file_info = {
            "file_id": file_id,
            "file_type": "document",
            "file_size": 50 * 1024 * 1024,  # 50MB
            "created_at": "2024-01-01T00:00:00",
            "access_count": 5
        }

        actions = await storage_policy_manager.evaluate_file_lifecycle(file_id, file_info)
        print(f"生命周期动作: {actions}")

        # 导出策略
        policies_json = storage_policy_manager.export_policies()
        print(f"导出的策略: {len(policies_json)} 字符")

    asyncio.run(example_usage())
