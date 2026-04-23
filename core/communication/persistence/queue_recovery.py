#!/usr/bin/env python3
from __future__ import annotations
"""
队列恢复管理器
Queue Recovery Manager

负责在系统重启后恢复消息队列状态：
- 恢复未处理的消息
- 恢复处理中的消息
- 重试失败的消息
- 清理过期消息

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from .base_persistence import BaseMessagePersistence, MessageState
from .persistence_manager import PersistenceManager

logger = logging.getLogger(__name__)


class QueueRecoveryManager:
    """
    队列恢复管理器

    负责在系统启动时恢复消息队列状态。
    """

    def __init__(
        self,
        persistence: PersistenceManager | BaseMessagePersistence,
        config: Optional[dict[str, Any]] = None,
    ):
        """
        初始化队列恢复管理器

        Args:
            persistence: 持久化管理器或后端
            config: 配置参数
                - recovery_timeout: 恢复超时时间（秒，默认：300）
                - max_retry_attempts: 最大重试次数（默认：3）
                - cleanup_on_recovery: 恢复时是否清理过期消息（默认：True）
                - retry_failed: 是否重试失败消息（默认：True）
        """
        if isinstance(persistence, PersistenceManager):
            self.persistence = persistence.backend
        else:
            self.persistence = persistence

        self.config = config or {}
        self.recovery_timeout = self.config.get("recovery_timeout", 300)
        self.max_retry_attempts = self.config.get("max_retry_attempts", 3)
        self.cleanup_on_recovery = self.config.get("cleanup_on_recovery", True)
        self.retry_failed = self.config.get("retry_failed", True)

        self._recovery_stats: dict[str, Any] = {}
        self._is_recovering = False

    async def recover_all(self) -> dict[str, Any]:
        """
        执行完整的队列恢复

        恢复步骤：
        1. 清理过期消息
        2. 恢复处理中的消息
        3. 恢复等待中的消息
        4. 重试失败的消息

        Returns:
            恢复统计信息
        """
        if self._is_recovering:
            logger.warning("队列恢复已在进行中")
            return self._recovery_stats

        self._is_recovering = True
        start_time = datetime.now()
        self._recovery_stats = {
            "start_time": start_time.isoformat(),
            "cleaned_expired": 0,
            "recovered_processing": 0,
            "recovered_pending": 0,
            "retried_failed": 0,
            "errors": [],
        }

        try:
            logger.info("🔄 开始队列恢复...")

            # 使用超时控制
            await asyncio.wait_for(self._do_recover(), timeout=self.recovery_timeout)

            elapsed = (datetime.now() - start_time).total_seconds()
            self._recovery_stats["elapsed_seconds"] = elapsed
            self._recovery_stats["success"] = True

            logger.info(
                f"✅ 队列恢复完成: "
                f"清理{self._recovery_stats['cleaned_expired']}条过期消息, "
                f"恢复{self._recovery_stats['recovered_processing']}条处理中消息, "
                f"恢复{self._recovery_stats['recovered_pending']}条等待中消息, "
                f"重试{self._recovery_stats['retried_failed']}条失败消息, "
                f"耗时{elapsed:.2f}秒"
            )

        except asyncio.TimeoutError:
            logger.error(f"❌ 队列恢复超时（{self.recovery_timeout}秒）")
            self._recovery_stats["success"] = False
            self._recovery_stats["error"] = "timeout"

        except Exception as e:
            logger.error(f"❌ 队列恢复失败: {e}")
            self._recovery_stats["success"] = False
            self._recovery_stats["error"] = str(e)

        finally:
            self._is_recovering = False

        return self._recovery_stats

    async def _do_recover(self) -> None:
        """执行恢复逻辑"""
        # 1. 清理过期消息
        if self.cleanup_on_recovery:
            await self._cleanup_expired_messages()

        # 2. 恢复处理中的消息（可能因崩溃而卡住）
        await self._recover_processing_messages()

        # 3. 确认等待中的消息状态
        await self._recover_pending_messages()

        # 4. 重试失败的消息
        if self.retry_failed:
            await self._retry_failed_messages()

    async def _cleanup_expired_messages(self) -> None:
        """清理过期消息"""
        try:
            expired = await self.persistence.get_expired_messages()

            for msg in expired:
                try:
                    # 删除过期消息
                    await self.persistence.delete_message(msg.message.id)
                    self._recovery_stats["cleaned_expired"] += 1
                except Exception as e:
                    self._recovery_stats["errors"].append(
                        f"清理过期消息失败 {msg.message.id}: {e}"
                    )

            if expired:
                logger.info(f"🧹 清理了 {len(expired)} 条过期消息")

        except Exception as e:
            logger.error(f"清理过期消息失败: {e}")
            self._recovery_stats["errors"].append(f"清理过期消息: {e}")

    async def _recover_processing_messages(self) -> None:
        """恢复处理中的消息"""
        try:
            # 获取所有处理中的消息
            processing = await self.persistence.get_messages_by_state(
                MessageState.PROCESSING, limit=1000
            )

            for msg in processing:
                try:
                    # 检查是否超时（处理时间超过1小时视为超时）
                    timeout_threshold = datetime.now() - timedelta(hours=1)
                    if msg.updated_at < timeout_threshold:
                        # 重置为等待状态，允许重新处理
                        await self.persistence.update_message_state(
                            msg.message.id, MessageState.PENDING
                        )
                        self._recovery_stats["recovered_processing"] += 1
                        logger.debug(
                            f"恢复超时的处理中消息: {msg.message.id} "
                            f"(更新于{msg.updated_at.isoformat()})"
                        )
                except Exception as e:
                    self._recovery_stats["errors"].append(
                        f"恢复处理中消息失败 {msg.message.id}: {e}"
                    )

            if processing:
                logger.info(f"🔄 恢复了 {self._recovery_stats['recovered_processing']} 条处理中消息")

        except Exception as e:
            logger.error(f"恢复处理中消息失败: {e}")
            self._recovery_stats["errors"].append(f"恢复处理中消息: {e}")

    async def _recover_pending_messages(self) -> None:
        """恢复等待中的消息"""
        try:
            pending = await self.persistence.get_messages_by_state(
                MessageState.PENDING, limit=1000
            )

            # 统计但不修改状态
            self._recovery_stats["recovered_pending"] = len(pending)

            if pending:
                logger.info(f"📋 发现 {len(pending)} 条等待中的消息")

        except Exception as e:
            logger.error(f"恢复等待中消息失败: {e}")
            self._recovery_stats["errors"].append(f"恢复等待中消息: {e}")

    async def _retry_failed_messages(self) -> None:
        """重试失败的消息"""
        try:
            failed = await self.persistence.get_failed_messages()

            retried = 0
            for msg in failed:
                try:
                    # 检查重试次数
                    if msg.attempt_count < self.max_retry_attempts:
                        # 重置为等待状态
                        await self.persistence.update_message_state(
                            msg.message.id, MessageState.PENDING
                        )
                        retried += 1
                    else:
                        # 超过最大重试次数，移至死信队列
                        await self.persistence.move_to_dead_letter(
                            msg.message.id,
                            f"超过最大重试次数({self.max_retry_attempts})",
                        )
                        logger.warning(
                            f"消息超过最大重试次数，移至死信队列: {msg.message.id}"
                        )
                except Exception as e:
                    self._recovery_stats["errors"].append(
                        f"重试失败消息失败 {msg.message.id}: {e}"
                    )

            self._recovery_stats["retried_failed"] = retried

            if failed:
                logger.info(
                    f"🔁 重试了 {retried}/{len(failed)} 条失败消息"
                )

        except Exception as e:
            logger.error(f"重试失败消息失败: {e}")
            self._recovery_stats["errors"].append(f"重试失败消息: {e}")

    async def get_recovery_stats(self) -> dict[str, Any]:
        """
        获取恢复统计信息

        Returns:
            恢复统计信息
        """
        return self._recovery_stats.copy()

    def is_recovering(self) -> bool:
        """
        检查是否正在恢复

        Returns:
            是否正在恢复
        """
        return self._is_recovering


async def recover_queue(
    persistence: PersistenceManager | BaseMessagePersistence,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    便捷函数：恢复队列

    Args:
        persistence: 持久化管理器或后端
        config: 配置参数

    Returns:
        恢复统计信息
    """
    recovery_manager = QueueRecoveryManager(persistence, config)
    return await recovery_manager.recover_all()


def get_recovery_manager(
    persistence: PersistenceManager | BaseMessagePersistence,
    config: Optional[dict[str, Any]] = None,
) -> QueueRecoveryManager:
    """
    获取或创建队列恢复管理器实例

    Args:
        persistence: 持久化管理器或后端
        config: 配置参数

    Returns:
        QueueRecoveryManager 实例
    """
    return QueueRecoveryManager(persistence, config)


__all__ = [
    "QueueRecoveryManager",
    "recover_queue",
    "get_recovery_manager",
]
