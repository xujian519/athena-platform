#!/usr/bin/env python3

"""
Apple M4 Pro 统一内存池管理器 - 方案A(保守型)
智能管理48GB统一内存,优先保证办公流畅度

作者: 小诺·双鱼公主 🌊✨
创建时间: 2025-12-27
版本: v1.0.0 "办公优先版"
"""

import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import psutil

logger = logging.getLogger(__name__)


class MemoryTier(Enum):
    """内存层级"""

    HOT = "hot"  # 常用,立即加载
    WARM = "warm"  # 频繁使用,快速加载
    COLD = "cold"  # 偶尔使用,按需加载
    ARCHIVE = "archive"  # 稀少使用,从磁盘加载


@dataclass
class MemoryPoolConfig:
    """内存池配置 - 方案A(保守型)"""

    # 总内存: 48GB
    total_memory_gb: float = 48.0

    # 内存分配策略(保守型)
    system_reserved_gb: float = 16.0  # 系统预留 33%
    docker_pool_gb: float = 24.0  # Docker总池 50%
    safety_buffer_gb: float = 8.0  # 安全缓冲 17%

    # AI模型内存限制
    max_model_memory_gb: float = 8.0  # 最大模型内存

    # 层级内存分配
    hot_memory_mb: int = 2048  # 2GB - 常用模型
    warm_memory_mb: int = 4096  # 4GB - 频繁使用
    cold_memory_mb: int = 8192  # 8GB - 按需加载
    archive_memory_mb: int = 0  # 归档(不占用内存)

    # 监控配置
    enable_memory_monitoring: bool = True
    monitor_interval_seconds: int = 60
    memory_warning_threshold: float = 0.85  # 85%


@dataclass
class ModelInfo:
    """模型信息"""

    name: str
    path: str
    tier: MemoryTier
    size_mb: float
    loaded: bool = False
    last_used: float = 0.0
    load_count: int = 0


class M4UnifiedMemoryPool:
    """Apple M4 Pro 统一内存池管理器"""

    def __init__(self, config: MemoryPoolConfig = None):
        self.config = config or MemoryPoolConfig()
        self.lock = threading.RLock()

        # 模型注册表
        self.models: dict[str, ModelInfo] = {}

        # 当前使用统计
        self.current_hot_mb = 0.0
        self.current_warm_mb = 0.0
        self.current_cold_mb = 0.0

        logger.info("🍎 M4统一内存池初始化完成")
        logger.info(f"💾 总内存: {self.config.total_memory_gb}GB")
        logger.info(f"🖥️  系统预留: {self.config.system_reserved_gb}GB")
        logger.info(f"🐳 Docker池: {self.config.docker_pool_gb}GB")
        logger.info(f"🛡️  安全缓冲: {self.config.safety_buffer_gb}GB")
        logger.info(f"🤖 最大模型内存: {self.config.max_model_memory_gb}GB")

    def register_model(self, name: str, path: str, tier: MemoryTier, size_mb: float) -> Any:
        """注册模型到内存池"""
        with self.lock:
            model = ModelInfo(name=name, path=path, tier=tier, size_mb=size_mb)
            self.models[name] = model
            logger.info(f"📝 模型已注册: {name} ({tier.value}, {size_mb}MB)")

    def allocate_memory(self, model_name: str, size_mb: float) -> bool:
        """分配内存给模型"""
        with self.lock:
            # 检查模型是否存在
            if model_name not in self.models:
                logger.warning(f"⚠️ 模型未注册: {model_name}")
                return False

            model = self.models[model_name]

            # 检查是否有足够内存
            available_mb = self._get_available_memory()
            if size_mb > available_mb:
                logger.warning(f"⚠️ 内存不足: 需要{size_mb}MB, 可用{available_mb:.0f}MB")
                # 尝试释放低优先级模型
                self._free_low_priority_memory(size_mb)
                available_mb = self._get_available_memory()

                if size_mb > available_mb:
                    logger.error(f"❌ 内存分配失败: {model_name}")
                    return False

            # 更新使用统计
            if model.tier == MemoryTier.HOT:
                self.current_hot_mb += size_mb
            elif model.tier == MemoryTier.WARM:
                self.current_warm_mb += size_mb
            elif model.tier == MemoryTier.COLD:
                self.current_cold_mb += size_mb

            model.loaded = True
            model.last_used = time.time()
            model.load_count += 1

            logger.info(f"✅ 内存已分配: {model_name} ({size_mb}MB)")
            return True

    def free_memory(self, model_name: str) -> Any:
        """释放模型内存"""
        with self.lock:
            if model_name not in self.models:
                return

            model = self.models[model_name]
            if not model.loaded:
                return

            # 更新使用统计
            if model.tier == MemoryTier.HOT:
                self.current_hot_mb -= model.size_mb
            elif model.tier == MemoryTier.WARM:
                self.current_warm_mb -= model.size_mb
            elif model.tier == MemoryTier.COLD:
                self.current_cold_mb -= model.size_mb

            model.loaded = False
            logger.info(f"🗑️ 内存已释放: {model_name} ({model.size_mb}MB)")

    def _get_available_memory(self) -> float:
        """获取可用模型内存(MB)"""
        total_model_mb = self.config.max_model_memory_gb * 1024
        used_mb = self.current_hot_mb + self.current_warm_mb + self.current_cold_mb
        available_mb = total_model_mb - used_mb

        # 检查系统内存压力
        system_memory = psutil.virtual_memory()
        if system_memory.percent > self.config.memory_warning_threshold * 100:
            logger.warning(f"⚠️ 系统内存压力大: {system_memory.percent:.1f}%")
            # 减少可用内存,给系统留更多空间
            available_mb = available_mb * 0.5

        return max(0, available_mb)

    def _free_low_priority_memory(self, required_mb: float) -> Any:
        """释放低优先级模型内存"""
        # 优先级:COLD > WARM > HOT
        tiers_to_free = [MemoryTier.COLD, MemoryTier.WARM]

        for tier in tiers_to_free:
            # 找出该层级的已加载模型
            loaded_models = [
                (name, model)
                for name, model in self.models.items()
                if model.tier == tier and model.loaded
            ]

            # 按最后使用时间排序
            loaded_models.sort(key=lambda x: x[1].last_used)

            freed_mb = 0.0
            for name, model in loaded_models:
                if freed_mb >= required_mb:
                    break

                self.free_memory(name)
                freed_mb += model.size_mb
                logger.info(f"🔄 释放低优先级模型: {name}")

            if freed_mb >= required_mb:
                break

    def get_memory_status(self) -> dict[str, Any]:
        """获取内存状态"""
        with self.lock:
            total_model_mb = self.config.max_model_memory_gb * 1024
            used_mb = self.current_hot_mb + self.current_warm_mb + self.current_cold_mb
            available_mb = total_model_mb - used_mb

            # 系统内存信息
            system_memory = psutil.virtual_memory()

            return {
                "model_memory": {
                    "total_mb": total_model_mb,
                    "used_mb": used_mb,
                    "available_mb": available_mb,
                    "usage_percent": (
                        (used_mb / total_model_mb * 100) if total_model_mb > 0 else 0.0
                    ),
                    "hot_mb": self.current_hot_mb,
                    "warm_mb": self.current_warm_mb,
                    "cold_mb": self.current_cold_mb,
                },
                "system_memory": {
                    "total_gb": system_memory.total / (1024**3),
                    "used_gb": system_memory.used / (1024**3),
                    "available_gb": system_memory.available / (1024**3),
                    "percent": system_memory.percent,
                },
                "models": {
                    name: {
                        "tier": model.tier.value,
                        "size_mb": model.size_mb,
                        "loaded": model.loaded,
                        "load_count": model.load_count,
                        "last_used": model.last_used,
                    }
                    for name, model in self.models.items()
                },
            }

    def optimize_model_placement(self) -> Any:
        """优化模型放置策略"""
        status = self.get_memory_status()
        usage_percent = status["model_memory"]["usage_percent"]

        # 如果内存使用率>80%,释放低优先级模型
        if usage_percent > 80:
            logger.info(f"🔄 内存使用率{usage_percent:.1f}%,优化模型放置...")
            self._free_low_priority_memory(float("inf"))


# 全局单例
_memory_pool: Optional[M4UnifiedMemoryPool] = None
_pool_lock = threading.Lock()


def get_memory_pool() -> M4UnifiedMemoryPool:
    """获取全局内存池实例"""
    global _memory_pool
    if _memory_pool is None:
        with _pool_lock:
            if _memory_pool is None:
                _memory_pool = M4UnifiedMemoryPool()
    return _memory_pool

