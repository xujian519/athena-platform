#!/usr/bin/env python3
"""
缓存预热模块
Cache Warmer Module

提供缓存预热功能,在系统启动时或后台预先加载热点数据,
提升首次请求的性能。

预热策略:
1. 主动预热 - 系统启动时加载
2. 被动预热 - 后台异步加载
3. 智能预热 - 基于访问频率预测

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import contextlib
import logging
import threading
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class WarmupStrategy(Enum):
    """预热策略"""

    ACTIVE = "active"  # 主动预热(启动时加载)
    PASSIVE = "passive"  # 被动预热(后台异步加载)
    INTELLIGENT = "intelligent"  # 智能预热(基于访问频率)


@dataclass
class WarmupConfig:
    """预热配置"""

    strategy: WarmupStrategy = WarmupStrategy.ACTIVE
    max_concurrent: int = 5  # 最大并发预热数
    timeout: float = 30.0  # 预热超时时间(秒)
    enable_priority: bool = True  # 是否启用优先级预热
    min_access_count: int = 3  # 最小访问次数才考虑预热

    # 热点数据配置
    hot_data_window: int = 1000  # 热点数据窗口大小
    hot_data_threshold: float = 0.7  # 热点阈值(前70%)

    # 预热源配置
    preload_files: list[Path] = field(default_factory=list)
    preload_queries: list[str] = field(default_factory=list)

    # 后台预热配置
    background_interval: int = 3600  # 后台预热间隔(秒)
    background_batch_size: int = 10  # 每批预热数量


@dataclass
class WarmupItem:
    """预热项"""

    key: str  # 缓存键
    data: Any  # 要预加载的数据
    priority: int = 0  # 优先级(越高越优先)
    estimated_cost: float = 0.0  # 预估加载成本(时间/资源)
    access_count: int = 0  # 访问次数
    last_accessed: datetime = field(default_factory=datetime.now)

    @property
    def score(self) -> float:
        """预热分数(优先级和访问频率的综合)"""
        frequency_score = self.access_count
        priority_score = self.priority * 10
        return frequency_score + priority_score


@dataclass
class WarmupResult:
    """预热结果"""

    total_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    total_time: float = 0.0
    errors: list[tuple[str, Exception]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """成功率"""
        return self.successful_items / max(self.total_items, 1)

    def __str__(self) -> str:
        return (
            f"WarmupResult(成功={self.successful_items}, "
            f"失败={self.failed_items}, "
            f"跳过={self.skipped_items}, "
            f"耗时={self.total_time:.2f}s, "
            f"成功率={self.success_rate:.1%})"
        )


class CacheWarmer:
    """缓存预热器

    提供智能的缓存预热功能,提升系统启动后的首次请求性能。

    使用示例:
        >>> warmer = CacheWarmer()
        >>> # 添加预热项
        >>> warmer.add_item("hot_document_1", document_data, priority=10)
        >>> # 执行预热
        >>> result = await warmer.warmup()
        >>> print(result)
    """

    def __init__(self, config: WarmupConfig | None = None):
        """初始化缓存预热器

        Args:
            config: 预热配置
        """
        self.config = config or WarmupConfig()
        self.warmup_items: dict[str, WarmupItem] = {}
        self.access_history: Counter = Counter()

        # 预热任务
        self._warmup_task: asyncio.Task | None = None
        self._background_task: asyncio.Task | None = None
        self._is_warming_up = False

        # 线程锁
        self._lock = threading.RLock()

        logger.info(f"🔥 初始化缓存预热器 (策略={self.config.strategy.value})")

    def add_item(
        self,
        key: str,
        data: Any,
        priority: int = 0,
        estimated_cost: float = 0.0,
    ) -> None:
        """添加预热项

        Args:
            key: 缓存键
            data: 要预加载的数据
            priority: 优先级(越高越优先)
            estimated_cost: 预估加载成本
        """
        with self._lock:
            item = WarmupItem(
                key=key,
                data=data,
                priority=priority,
                estimated_cost=estimated_cost,
                access_count=self.access_history.get(key, 0),
            )
            self.warmup_items[key] = item

        logger.debug(f"📦 添加预热项: {key} (优先级={priority})")

    def record_access(self, key: str) -> None:
        """记录访问(用于智能预热)

        Args:
            key: 缓存键
        """
        self.access_history[key] += 1

        # 更新现有预热项的访问计数
        with self._lock:
            if key in self.warmup_items:
                self.warmup_items[key].access_count = self.access_history[key]
                self.warmup_items[key].last_accessed = datetime.now()

    def get_hot_items(self, top_k: int = 100) -> list[WarmupItem]:
        """获取热点数据

        Args:
            top_k: 返回前k个热点数据

        Returns:
            热点预热项列表
        """
        with self._lock:
            items = list(self.warmup_items.values())

            # 按分数排序
            items.sort(key=lambda x: x.score, reverse=True)

            # 过滤低频访问项
            if self.config.min_access_count > 0:
                items = [i for i in items if i.access_count >= self.config.min_access_count]

            return items[:top_k]

    async def warmup(
        self,
        cache_store: dict[str, Any] | None = None,
        progress_callback: Callable[..., Any] | None = None,
    ) -> WarmupResult:
        """执行预热

        Args:
            cache_store: 缓存存储(字典)
            progress_callback: 进度回调函数

        Returns:
            预热结果
        """
        if cache_store is None:
            logger.warning("⚠️ 未提供缓存存储,跳过预热")
            return WarmupResult()

        if self._is_warming_up:
            logger.warning("⚠️ 预热正在进行中,跳过")
            return WarmupResult()

        self._is_warming_up = True
        result = WarmupResult()
        start_time = time.time()

        try:
            # 获取要预热的项目
            items_to_warmup = self._get_items_for_warmup()
            result.total_items = len(items_to_warmup)

            if not items_to_warmup:
                logger.info("✅ 没有需要预热的项")
                return result

            logger.info(f"🔥 开始预热 {len(items_to_warmup)} 个项...")

            # 按优先级分组
            if self.config.enable_priority:
                items_to_warmup.sort(key=lambda x: x.priority, reverse=True)

            # 使用信号量控制并发
            semaphore = asyncio.Semaphore(self.config.max_concurrent)

            async def warmup_single_item(item: WarmupItem) -> bool:
                """预热单个项"""
                async with semaphore:
                    try:
                        # 模拟预热过程
                        await asyncio.sleep(min(item.estimated_cost, 1.0))

                        # 添加到缓存
                        cache_store[item.key] = item.data

                        logger.debug(f"✅ 预热成功: {item.key}")
                        return True

                    except Exception as e:
                        logger.error(f"❌ 预热失败 {item.key}: {e}")
                        result.errors.append((item.key, e))
                        return False

            # 执行预热
            tasks = [warmup_single_item(item) for item in items_to_warmup]

            for i, task in enumerate(asyncio.as_completed(tasks)):
                success = await task
                if success:
                    result.successful_items += 1
                else:
                    result.failed_items += 1

                # 进度回调
                if progress_callback:
                    progress = (i + 1) / len(tasks)
                    await progress_callback(progress, result.successful_items, result.failed_items)

            result.total_time = time.time() - start_time

            logger.info(f"✅ 预热完成: {result}")

            return result

        except asyncio.CancelledError:
            logger.warning("⚠️ 预热被取消")
            result.total_time = time.time() - start_time
            return result

        except Exception as e:
            logger.error(f"❌ 预热过程出错: {e}")
            result.total_time = time.time() - start_time
            return result

        finally:
            self._is_warming_up = False

    def _get_items_for_warmup(self) -> list[WarmupItem]:
        """获取需要预热的项"""
        with self._lock:
            items = list(self.warmup_items.values())

            if self.config.strategy == WarmupStrategy.ACTIVE:
                # 主动预热:返回所有项
                return items

            elif self.config.strategy == WarmupStrategy.PASSIVE:
                # 被动预热:只返回高优先级项
                return [i for i in items if i.priority >= 5]

            elif self.config.strategy == WarmupStrategy.INTELLIGENT:
                # 智能预热:返回热点数据
                return self.get_hot_items(top_k=int(len(items) * self.config.hot_data_threshold))

            return items

    async def start_background_warmup(
        self,
        cache_store: dict[str, Any],    ) -> None:
        """启动后台预热任务

        Args:
            cache_store: 缓存存储
        """
        if self._background_task is not None and not self._background_task.done():
            logger.warning("⚠️ 后台预热任务已在运行")
            return

        async def background_loop():
            """后台预热循环"""
            while True:
                try:
                    await asyncio.sleep(self.config.background_interval)

                    logger.info("🔄 执行后台预热...")
                    result = await self.warmup(cache_store)
                    logger.info(f"✅ 后台预热完成: {result}")

                except asyncio.CancelledError:
                    logger.info("⏹️ 后台预热任务已停止")
                    break
                except Exception as e:
                    logger.error(f"❌ 后台预热失败: {e}")

        self._background_task = asyncio.create_task(background_loop())
        logger.info("🚀 后台预热任务已启动")

    async def stop_background_warmup(self) -> None:
        """停止后台预热任务"""
        if self._background_task:
            self._background_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._background_task
            logger.info("⏹️ 后台预热任务已停止")

    def clear(self) -> None:
        """清空预热项"""
        with self._lock:
            self.warmup_items.clear()
            self.access_history.clear()
        logger.info("🧹 预热项已清空")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            total_items = len(self.warmup_items)
            hot_items = len(self.get_hot_items())

            return {
                "total_items": total_items,
                "hot_items": hot_items,
                "is_warming_up": self._is_warming_up,
                "background_running": (
                    self._background_task is not None and not self._background_task.done()
                ),
                "strategy": self.config.strategy.value,
                "max_concurrent": self.config.max_concurrent,
            }


class CacheWarmerManager:
    """缓存预热管理器

    管理多个缓存预热器,提供统一的预热接口。
    """

    def __init__(self):
        """初始化预热管理器"""
        self.warmers: dict[str, CacheWarmer] = {}
        logger.info("🔥 缓存预热管理器初始化完成")

    def register_warmer(self, name: str, warmer: CacheWarmer) -> None:
        """注册预热器

        Args:
            name: 预热器名称
            warmer: 预热器实例
        """
        self.warmers[name] = warmer
        logger.info(f"📦 注册预热器: {name}")

    async def warmup_all(
        self,
        cache_store: dict[str, Any],        progress_callback: Callable[..., Any] | None = None,
    ) -> dict[str, WarmupResult]:
        """预热所有预热器

        Args:
            cache_store: 缓存存储
            progress_callback: 进度回调

        Returns:
            每个预热器的预热结果
        """
        results = {}

        for name, warmer in self.warmers.items():
            logger.info(f"🔥 预热 {name}...")
            result = await warmer.warmup(cache_store, progress_callback)
            results[name] = result

        return results

    async def start_all_background_warmup(
        self,
        cache_store: dict[str, Any],    ) -> None:
        """启动所有后台预热任务

        Args:
            cache_store: 缓存存储
        """
        for name, warmer in self.warmers.items():
            logger.info(f"🚀 启动 {name} 后台预热...")
            await warmer.start_background_warmup(cache_store)

    async def stop_all_background_warmup(self) -> None:
        """停止所有后台预热任务"""
        for name, warmer in self.warmers.items():
            logger.info(f"⏹️ 停止 {name} 后台预热...")
            await warmer.stop_background_warmup()

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """获取所有预热器的统计信息"""
        return {name: warmer.get_stats() for name, warmer in self.warmers.items()}


# 全局预热管理器实例
_global_warmer_manager: CacheWarmerManager | None = None


def get_warmer_manager() -> CacheWarmerManager:
    """获取全局预热管理器"""
    global _global_warmer_manager
    if _global_warmer_manager is None:
        _global_warmer_manager = CacheWarmerManager()
    return _global_warmer_manager


# 便捷函数
def create_cache_warmer(
    strategy: WarmupStrategy = WarmupStrategy.ACTIVE,
    max_concurrent: int = 5,
) -> CacheWarmer:
    """创建缓存预热器"""
    config = WarmupConfig(strategy=strategy, max_concurrent=max_concurrent)
    return CacheWarmer(config)


__all__ = [
    "CacheWarmer",
    "CacheWarmerManager",
    "WarmupConfig",
    "WarmupItem",
    "WarmupResult",
    "WarmupStrategy",
    "create_cache_warmer",
    "get_warmer_manager",
]
