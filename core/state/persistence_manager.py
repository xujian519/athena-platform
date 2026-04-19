#!/usr/bin/env python3
from __future__ import annotations
"""
状态持久化管理器
State Persistence Manager

管理状态持久化策略,包括:
- 持久化策略选择
- 自动持久化触发
- 持久化性能监控

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

import asyncio
import contextlib
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .state_module import StateModule

logger = logging.getLogger(__name__)


class PersistenceStrategy(str, Enum):
    """持久化策略"""

    IMMEDIATE = "immediate"  # 立即持久化
    DELAYED = "delayed"  # 延迟持久化(批量)
    PERIODIC = "periodic"  # 定期持久化
    MANUAL = "manual"  # 手动持久化


@dataclass
class PersistenceConfig:
    """持久化配置"""

    strategy: PersistenceStrategy = PersistenceStrategy.DELAYED
    delay_seconds: float = 5.0  # 延迟持久化的延迟时间
    periodic_interval: float = 60.0  # 定期持久化的间隔
    auto_save_on_change: bool = True  # 状态变化时自动保存
    max_pending_changes: int = 100  # 最大挂起变化数
    compression: bool = False  # 是否压缩
    backup_count: int = 5  # 保留备份数

    # 持久化目录
    persistence_dir: str = "data/state"

    # 文件命名
    use_timestamp: bool = True  # 文件名包含时间戳
    file_prefix: str = ""  # 文件前缀


@dataclass
class PersistenceMetrics:
    """持久化指标"""

    total_saves: int = 0
    total_loads: int = 0
    failed_saves: int = 0
    failed_loads: int = 0
    total_save_time: float = 0.0
    total_load_time: float = 0.0
    last_save_time: datetime | None = None
    last_load_time: datetime | None = None

    def get_save_success_rate(self) -> float:
        """获取保存成功率"""
        if self.total_saves == 0:
            return 1.0
        return (self.total_saves - self.failed_saves) / self.total_saves

    def get_load_success_rate(self) -> float:
        """获取加载成功率"""
        if self.total_loads == 0:
            return 1.0
        return (self.total_loads - self.failed_loads) / self.total_loads


class StatePersistenceManager:
    """
    状态持久化管理器

    管理多个StateModule的持久化策略。
    """

    def __init__(self, config: PersistenceConfig | None = None):
        """
        初始化持久化管理器

        Args:
            config: 持久化配置
        """
        self.config = config or PersistenceConfig()
        self._modules: dict[str, StateModule] = {}
        self._pending_saves: dict[str, asyncio.Task] = {}
        self._save_lock = asyncio.Lock()
        self._metrics: dict[str, PersistenceMetrics] = {}
        self._periodic_task: asyncio.Task | None = None

        # 确保持久化目录存在
        Path(self.config.persistence_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"💾 StatePersistenceManager初始化完成 (策略: {self.config.strategy.value})")

    def register_module(self, name: str, module: StateModule, auto_save: bool | None = None) -> None:
        """
        注册状态模块

        Args:
            name: 模块名称
            module: StateModule实例
            auto_save: 是否自动保存(默认使用配置)
        """
        self._modules[name] = module
        self._metrics[name] = PersistenceMetrics()

        logger.info(f"✅ 状态模块已注册: {name}")

        # 根据策略启动自动保存
        if auto_save or (auto_save is None and self.config.auto_save_on_change):
            if self.config.strategy == PersistenceStrategy.PERIODIC:
                self._start_periodic_save()
            elif self.config.strategy == PersistenceStrategy.IMMEDIATE:
                # 立即策略在每次变化时保存
                pass

    def unregister_module(self, name: str) -> None:
        """
        取消注册状态模块

        Args:
            name: 模块名称
        """
        if name in self._modules:
            # 取消待处理的保存
            if name in self._pending_saves:
                self._pending_saves[name].cancel()
                del self._pending_saves[name]

            del self._modules[name]
            logger.info(f"❌ 状态模块已取消注册: {name}")

    async def save_module(self, name: str, force: bool = False) -> str | None:
        """
        保存模块状态

        Args:
            name: 模块名称
            force: 是否强制保存(忽略延迟策略)

        Returns:
            保存的文件路径,如果失败返回None
        """
        if name not in self._modules:
            logger.error(f"❌ 模块未注册: {name}")
            return None

        module = self._modules[name]
        metrics = self._metrics[name]

        # 根据策略决定是否立即保存
        if not force and self.config.strategy == PersistenceStrategy.DELAYED:
            # 延迟保存:创建延迟任务
            if name in self._pending_saves:
                self._pending_saves[name].cancel()

            self._pending_saves[name] = asyncio.create_task(self._delayed_save(name))
            return None

        # 立即保存
        async with self._save_lock:
            start_time = datetime.now()

            try:
                file_path = self._get_file_path(name)

                await module.save_state(file_path)

                # 更新指标
                metrics.total_saves += 1
                metrics.total_save_time += (datetime.now() - start_time).total_seconds()
                metrics.last_save_time = datetime.now()

                # 创建备份
                if self.config.backup_count > 0:
                    await self._create_backup(name, file_path)

                return file_path

            except Exception as e:
                metrics.failed_saves += 1
                logger.error(f"❌ 保存失败: {name} - {e}", exc_info=True)
                return None

    async def _delayed_save(self, name: str) -> str | None:
        """
        延迟保存

        Args:
            name: 模块名称

        Returns:
            保存的文件路径
        """
        await asyncio.sleep(self.config.delay_seconds)

        if name in self._pending_saves:
            result = await self.save_module(name, force=True)
            del self._pending_saves[name]
            return result

        return None

    async def load_module(self, name: str, file_path: str | None = None) -> bool:
        """
        加载模块状态

        Args:
            name: 模块名称
            file_path: 文件路径(默认使用最新文件)

        Returns:
            是否成功加载
        """
        if name not in self._modules:
            logger.error(f"❌ 模块未注册: {name}")
            return False

        module = self._modules[name]
        metrics = self._metrics[name]

        # 确定文件路径
        if file_path is None:
            file_path = self._get_latest_file_path(name)
            if file_path is None:
                logger.warning(f"⚠️ 没有找到状态文件: {name}")
                return False

        start_time = datetime.now()

        try:
            await module.load_state(file_path)

            # 更新指标
            metrics.total_loads += 1
            metrics.total_load_time += (datetime.now() - start_time).total_seconds()
            metrics.last_load_time = datetime.now()

            logger.info(f"✅ 状态已加载: {name}")
            return True

        except Exception as e:
            metrics.failed_loads += 1
            logger.error(f"❌ 加载失败: {name} - {e}", exc_info=True)
            return False

    def _get_file_path(self, name: str) -> str:
        """
        获取状态文件路径

        Args:
            name: 模块名称

        Returns:
            文件路径
        """
        filename = f"{self.config.file_prefix}{name}"

        if self.config.use_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename}_{timestamp}"

        filename = f"{filename}.json"

        return str(Path(self.config.persistence_dir) / filename)

    def _get_latest_file_path(self, name: str) -> str | None:
        """
        获取最新的状态文件路径

        Args:
            name: 模块名称

        Returns:
            文件路径,如果不存在返回None
        """
        pattern = f"{self.config.file_prefix}{name}_*.json"
        files = list(Path(self.config.persistence_dir).glob(pattern))

        if not files:
            # 尝试不带时间戳的文件
            no_timestamp = (
                Path(self.config.persistence_dir) / f"{self.config.file_prefix}{name}.json"
            )
            if no_timestamp.exists():
                return str(no_timestamp)
            return None

        # 按修改时间排序,返回最新的
        latest = max(files, key=lambda p: p.stat().st_mtime)
        return str(latest)

    async def _create_backup(self, name: str, current_file: str) -> None:
        """
        创建备份

        Args:
            name: 模块名称
            current_file: 当前文件路径
        """
        backup_dir = Path(self.config.persistence_dir) / "backups" / name
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 复制文件
        import shutil

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{timestamp}.json"

        shutil.copy2(current_file, backup_path)

        # 清理旧备份
        backups = sorted(backup_dir.glob("*.json"), reverse=True)
        for old_backup in backups[self.config.backup_count :]:
            old_backup.unlink()

    def _start_periodic_save(self) -> None:
        """启动定期保存任务"""
        if self._periodic_task is None or self._periodic_task.done():

            async def periodic_save_loop():
                while True:
                    await asyncio.sleep(self.config.periodic_interval)

                    for name in self._modules:
                        await self.save_module(name)

            self._periodic_task = asyncio.create_task(periodic_save_loop())
            logger.info(f"🔄 定期保存任务已启动 (间隔: {self.config.periodic_interval}秒)")

    async def save_all(self, force: bool = True) -> dict[str, str | None]:
        """
        保存所有模块

        Args:
            force: 是否强制保存

        Returns:
            保存结果字典 {name: file_path}
        """
        results = {}

        for name in self._modules:
            results[name] = await self.save_module(name, force=force)

        saved_count = sum(1 for v in results.values() if v is not None)
        logger.info(f"💾 批量保存完成: {saved_count}/{len(results)} 个模块")

        return results

    async def load_all(self) -> dict[str, bool]:
        """
        加载所有模块

        Returns:
            加载结果字典 {name: success}
        """
        results = {}

        for name in self._modules:
            results[name] = await self.load_module(name)

        loaded_count = sum(1 for v in results.values() if v)
        logger.info(f"📂 批量加载完成: {loaded_count}/{len(results)} 个模块")

        return results

    def get_metrics(self, name: str | None = None) -> Any:
        """
        获取持久化指标

        Args:
            name: 模块名称,None表示获取所有模块的指标

        Returns:
            指标数据
        """
        if name:
            if name not in self._metrics:
                return None
            return self._metrics[name]

        # 返回所有模块的指标汇总
        return {
            name: {
                "total_saves": m.total_saves,
                "total_loads": m.total_loads,
                "save_success_rate": m.get_save_success_rate(),
                "load_success_rate": m.get_load_success_rate(),
                "last_save_time": m.last_save_time.isoformat() if m.last_save_time else None,
                "last_load_time": m.last_load_time.isoformat() if m.last_load_time else None,
            }
            for name, m in self._metrics.items()
        }

    async def close(self) -> None:
        """关闭持久化管理器"""
        # 保存所有待处理的保存
        for name, task in list(self._pending_saves.items()):
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            await self.save_module(name, force=True)

        # 取消定期任务
        if self._periodic_task and not self._periodic_task.done():
            self._periodic_task.cancel()

        logger.info("⏹️ StatePersistenceManager已关闭")


__all__ = [
    "PersistenceConfig",
    "PersistenceMetrics",
    "PersistenceStrategy",
    "StatePersistenceManager",
]
