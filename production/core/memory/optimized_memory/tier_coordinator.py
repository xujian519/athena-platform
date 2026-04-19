#!/usr/bin/env python3
"""
优化记忆系统 - 分层协调器
Optimized Memory System - Tier Coordinator

智能分层管理器，协调热层、温层、冷层的数据迁移

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.1.0
"""

from __future__ import annotations
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from core.logging_config import setup_logging
from core.memory.optimized_memory.migration import MigrationExecutor
from core.memory.optimized_memory.tier_managers import (
    ColdTierManager,
    HotTierManager,
    WarmTierManager,
)
from core.memory.optimized_memory.types import MemoryData, MemoryTier

logger = setup_logging()


class IntelligentTierManager:
    """智能分层管理器 - 协调各层级数据存储和迁移"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.tier_limits = {
            MemoryTier.HOT: config.get("hot_limit_mb", 100) * 1024 * 1024,  # 100MB
            MemoryTier.WARM: config.get("warm_limit_mb", 500) * 1024 * 1024,  # 500MB
            MemoryTier.COLD: config.get("cold_limit_gb", 10) * 1024 * 1024 * 1024,  # 10GB
            MemoryTier.ARCHIVE: float("inf"),  # 无限制
        }

        # 层级顺序映射（用于比较）
        self.tier_order = {
            MemoryTier.HOT: 3,
            MemoryTier.WARM: 2,
            MemoryTier.COLD: 1,
            MemoryTier.ARCHIVE: 0,
        }

        self.access_thresholds = {
            MemoryTier.HOT: config.get("hot_threshold", 10),  # 10次/分钟
            MemoryTier.WARM: config.get("warm_threshold", 1),  # 1次/分钟
            MemoryTier.COLD: config.get("cold_threshold", 0.1),
        }  # 0.1次/分钟

        self.tier_promotion_rules = {
            MemoryTier.HOT: {
                "min_access_count": 50,
                "min_frequency": 5.0,
                "recent_access_window": timedelta(minutes=5),
            },
            MemoryTier.WARM: {
                "min_access_count": 10,
                "min_frequency": 1.0,
                "recent_access_window": timedelta(minutes=30),
            },
        }

        self.tier_demotion_rules = {
            MemoryTier.WARM: {
                "max_access_count": 5,
                "max_frequency": 0.5,
                "idle_time": timedelta(minutes=15),
            },
            MemoryTier.COLD: {
                "max_access_count": 2,
                "max_frequency": 0.1,
                "idle_time": timedelta(hours=1),
            },
        }

        self.tier_managers = {
            MemoryTier.HOT: HotTierManager(config),
            MemoryTier.WARM: WarmTierManager(config),
            MemoryTier.COLD: ColdTierManager(config),
        }

        # 迁移执行器作为独立组件
        self.migration_executor = MigrationExecutor(config)

        # 统计信息
        self.stats: dict[str, Any] = {
            "total_data_items": 0,
            "promotions": 0,
            "demotions": 0,
            "access_patterns": defaultdict(int),
            "migration_time": 0.0,
            "memory_efficiency": 0.0,
        }

        logger.info("🗄️ 智能分层管理器初始化完成")

    def evaluate_data_placement(self, data: MemoryData) -> MemoryTier:
        """评估数据应该放置的层级"""
        current_tier = data.tier

        # 检查是否需要提升
        if self._should_promote(data, current_tier):
            if current_tier == MemoryTier.COLD:
                return MemoryTier.WARM
            elif current_tier == MemoryTier.WARM:
                return MemoryTier.HOT

        # 检查是否需要降级
        if self._should_demote(data, current_tier):
            if current_tier == MemoryTier.HOT:
                return MemoryTier.WARM
            elif current_tier == MemoryTier.WARM:
                return MemoryTier.COLD
            elif current_tier == MemoryTier.COLD:
                return MemoryTier.ARCHIVE

        return current_tier

    def _should_promote(self, data: MemoryData, current_tier: MemoryTier) -> bool:
        """判断是否应该提升层级"""
        if current_tier not in self.tier_promotion_rules:
            return False

        rules = self.tier_promotion_rules[current_tier]

        # 检查访问次数
        if data.access_count < rules["min_access_count"]:
            return False

        # 检查访问频率
        if data.access_frequency < rules["min_frequency"]:
            return False

        # 检查最近访问
        time_since_last_access = datetime.now() - data.last_accessed
        return not time_since_last_access > rules["recent_access_window"]

    def _should_demote(self, data: MemoryData, current_tier: MemoryTier) -> bool:
        """判断是否应该降级层级"""
        if current_tier not in self.tier_demotion_rules:
            return False

        rules = self.tier_demotion_rules[current_tier]

        # 检查访问次数
        if data.access_count > rules["max_access_count"]:
            return False

        # 检查访问频率
        if data.access_frequency > rules["max_frequency"]:
            return False

        # 检查空闲时间
        time_since_last_access = datetime.now() - data.last_accessed
        return not time_since_last_access < rules["idle_time"]

    async def execute_tier_migration(
        self, data: MemoryData, target_tier: MemoryTier
    ) -> bool:
        """执行层级迁移"""
        start_time = time.time()

        try:
            source_tier = data.tier

            # 衰减访问频率
            data.access_frequency *= data.decay_factor

            # 执行实际迁移
            success = await self.migration_executor.migrate(data, source_tier, target_tier)

            if success:
                data.tier = target_tier
                is_promotion = self.tier_order[target_tier] > self.tier_order[source_tier]
                self.stats["promotions" if is_promotion else "demotions"] += 1
                self.stats["access_patterns"][data.access_pattern.value] += 1

            self.stats["migration_time"] += time.time() - start_time
            return success

        except Exception as e:
            logger.error(f"❌ 层级迁移失败: {e}")
            return False

    def get_tier_statistics(self) -> dict[str, Any]:
        """获取层级统计信息"""
        return {
            "tier_limits_mb": {
                k.value: v // (1024 * 1024) for k, v in self.tier_limits.items() if v != float("inf")
            },
            "access_thresholds": {k.value: v for k, v in self.access_thresholds.items()},
            "migration_stats": self.stats,
            "total_items": self.stats["total_data_items"],
            "promotion_rate": self.stats["promotions"] / max(self.stats["total_data_items"], 1),
            "demotion_rate": self.stats["demotions"] / max(self.stats["total_data_items"], 1),
        }
