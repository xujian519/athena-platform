#!/usr/bin/env python3
"""
文件系统消息持久化实现
File System Message Persistence Implementation

使用文件系统作为消息持久化后端，适用于简单的部署场景。

功能特性：
- 消息持久化到JSON文件
- 消息状态跟踪
- 过期消息清理
- 死信队列管理

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import fcntl
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from core.communication.types import Message
from .base_persistence import (
    BaseMessagePersistence,
    MessageState,
    PersistedMessage,
)

logger = logging.getLogger(__name__)


class FilePersistence(BaseMessagePersistence):
    """
    文件系统持久化实现

    使用JSON文件存储消息，支持并发访问控制。
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化文件持久化

        Args:
            config: 配置参数
                - base_dir: 基础目录（默认：./data/messages）
                - sync_interval: 同步间隔（秒，默认：5）
                - auto_cleanup: 自动清理过期消息（默认：True）
        """
        super().__init__(config)
        self.base_dir = Path(config.get("base_dir", "./data/messages"))
        self.sync_interval = config.get("sync_interval", 5)
        self.auto_cleanup = config.get("auto_cleanup", True)

        # 创建目录结构
        self.state_dirs = {
            state: self.base_dir / "states" / state.value for state in MessageState
        }
        self.dead_letter_dir = self.base_dir / "dead_letter"
        self.index_file = self.base_dir / "index.json"

        self._file_locks: dict[str, Any] = {}
        self._index: dict[str, str] = {}  # message_id -> state

    async def initialize(self) -> bool:
        """初始化文件系统"""
        try:
            # 创建所有必要的目录
            self.base_dir.mkdir(parents=True, exist_ok=True)
            for state_dir in self.state_dirs.values():
                state_dir.mkdir(parents=True, exist_ok=True)
            self.dead_letter_dir.mkdir(parents=True, exist_ok=True)

            # 加载索引
            await self._load_index()

            self.logger.info(f"文件持久化初始化成功: {self.base_dir}")
            return True

        except Exception as e:
            self.logger.error(f"文件持久化初始化失败: {e}")
            return False

    async def shutdown(self) -> bool:
        """关闭文件持久化"""
        try:
            # 保存索引
            await self._save_index()
            self.logger.info("文件持久化已关闭")
            return True
        except Exception as e:
            self.logger.error(f"关闭文件持久化失败: {e}")
            return False

    def _get_message_path(self, message_id: str, state: MessageState) -> Path:
        """获取消息文件路径"""
        return self.state_dirs[state] / f"{message_id}.json"

    def _get_dead_letter_path(self, message_id: str) -> Path:
        """获取死信文件路径"""
        return self.dead_letter_dir / f"{message_id}.json"

    def _acquire_lock(self, file_path: Path) -> Any:
        """获取文件锁"""
        if str(file_path) not in self._file_locks:
            self._file_locks[str(file_path)] = open(file_path, "a+")
        return self._file_locks[str(file_path)]

    def _release_lock(self, file_path: Path) -> None:
        """释放文件锁"""
        if str(file_path) in self._file_locks:
            try:
                self._file_locks[str(file_path)].close()
            except Exception:
                pass
            del self._file_locks[str(file_path)]

    async def save_message(
        self, message: Message, state: MessageState = MessageState.PENDING
    ) -> bool:
        """保存消息"""
        try:
            persisted = PersistedMessage(message=message, state=state)
            file_path = self._get_message_path(message.id, state)

            # 写入文件
            with open(file_path, "w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(persisted.to_dict(), f, indent=2)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # 更新索引
            self._index[message.id] = state.value
            await self._save_index()

            return True

        except Exception as e:
            self.logger.error(f"保存消息失败: {e}")
            return False

    async def get_message(self, message_id: str) -> PersistedMessage | None:
        """获取消息"""
        try:
            # 从索引查找状态
            state_str = self._index.get(message_id)
            if not state_str:
                return None

            state = MessageState(state_str)
            file_path = self._get_message_path(message_id, state)

            if not file_path.exists():
                return None

            with open(file_path, "r") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                data = json.load(f)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            return PersistedMessage.from_dict(data)

        except Exception as e:
            self.logger.error(f"获取消息失败: {e}")
            return None

    async def update_message_state(
        self, message_id: str, state: MessageState, error_message: str | None = None
    ) -> bool:
        """更新消息状态"""
        try:
            # 获取当前状态
            current_state_str = self._index.get(message_id)
            if not current_state_str:
                return False

            current_state = MessageState(current_state_str)
            old_path = self._get_message_path(message_id, current_state)

            if not old_path.exists():
                return False

            # 读取当前消息
            with open(old_path, "r") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                data = json.load(f)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            persisted = PersistedMessage.from_dict(data)
            persisted.state = state
            persisted.updated_at = datetime.now()
            if error_message:
                persisted.error_message = error_message

            # 写入新位置
            new_path = self._get_message_path(message_id, state)
            with open(new_path, "w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(persisted.to_dict(), f, indent=2)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # 删除旧文件
            old_path.unlink()

            # 更新索引
            self._index[message_id] = state.value
            await self._save_index()

            return True

        except Exception as e:
            self.logger.error(f"更新消息状态失败: {e}")
            return False

    async def increment_attempt(self, message_id: str) -> bool:
        """增加尝试次数"""
        try:
            state_str = self._index.get(message_id)
            if not state_str:
                return False

            state = MessageState(state_str)
            file_path = self._get_message_path(message_id, state)

            with open(file_path, "r+") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                data = json.load(f)
                persisted = PersistedMessage.from_dict(data)
                persisted.attempt_count += 1
                persisted.updated_at = datetime.now()
                f.seek(0)
                json.dump(persisted.to_dict(), f, indent=2)
                f.truncate()
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            return True

        except Exception as e:
            self.logger.error(f"增加尝试次数失败: {e}")
            return False

    async def delete_message(self, message_id: str) -> bool:
        """删除消息"""
        try:
            state_str = self._index.get(message_id)
            if not state_str:
                return False

            state = MessageState(state_str)
            file_path = self._get_message_path(message_id, state)

            if file_path.exists():
                file_path.unlink()

            # 更新索引
            del self._index[message_id]
            await self._save_index()

            return True

        except Exception as e:
            self.logger.error(f"删除消息失败: {e}")
            return False

    async def get_messages_by_state(
        self, state: MessageState, limit: int = 100
    ) -> list[PersistedMessage]:
        """按状态获取消息"""
        try:
            state_dir = self.state_dirs[state]
            messages = []

            for file_path in sorted(state_dir.glob("*.json"))[:limit]:
                try:
                    with open(file_path, "r") as f:
                        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                        data = json.load(f)
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    messages.append(PersistedMessage.from_dict(data))
                except Exception as e:
                    self.logger.warning(f"读取消息文件失败 {file_path}: {e}")

            return messages

        except Exception as e:
            self.logger.error(f"按状态获取消息失败: {e}")
            return []

    async def get_expired_messages(self) -> list[PersistedMessage]:
        """获取过期消息"""
        try:
            now = datetime.now()
            expired = []

            for state in MessageState:
                messages = await self.get_messages_by_state(state, limit=1000)
                for msg in messages:
                    if msg.expires_at and msg.expires_at < now:
                        expired.append(msg)

            return expired

        except Exception as e:
            self.logger.error(f"获取过期消息失败: {e}")
            return []

    async def get_failed_messages(self) -> list[PersistedMessage]:
        """获取失败消息"""
        return await self.get_messages_by_state(MessageState.FAILED, limit=1000)

    async def move_to_dead_letter(
        self, message_id: str, reason: str
    ) -> bool:
        """移至死信队列"""
        try:
            state_str = self._index.get(message_id)
            if not state_str:
                return False

            state = MessageState(state_str)
            old_path = self._get_message_path(message_id, state)

            if not old_path.exists():
                return False

            # 读取消息
            with open(old_path, "r") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                data = json.load(f)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            persisted = PersistedMessage.from_dict(data)
            persisted.state = MessageState.DEAD_LETTER
            persisted.updated_at = datetime.now()
            persisted.metadata["dead_letter_reason"] = reason

            # 写入死信目录
            dead_path = self._get_dead_letter_path(message_id)
            with open(dead_path, "w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(persisted.to_dict(), f, indent=2)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # 删除旧文件
            old_path.unlink()

            # 更新索引
            self._index[message_id] = MessageState.DEAD_LETTER.value
            await self._save_index()

            return True

        except Exception as e:
            self.logger.error(f"移至死信队列失败: {e}")
            return False

    async def get_dead_letter_messages(self) -> list[PersistedMessage]:
        """获取死信消息"""
        try:
            messages = []

            for file_path in sorted(self.dead_letter_dir.glob("*.json")):
                try:
                    with open(file_path, "r") as f:
                        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                        data = json.load(f)
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    messages.append(PersistedMessage.from_dict(data))
                except Exception as e:
                    self.logger.warning(f"读取死信文件失败 {file_path}: {e}")

            return messages

        except Exception as e:
            self.logger.error(f"获取死信消息失败: {e}")
            return []

    async def clear_dead_letter(self, older_than: datetime | None = None) -> int:
        """清理死信队列"""
        try:
            count = 0

            for file_path in self.dead_letter_dir.glob("*.json"):
                try:
                    if older_than is None:
                        file_path.unlink()
                        count += 1
                    else:
                        # 检查文件修改时间
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if mtime < older_than:
                            file_path.unlink()
                            count += 1
                except Exception as e:
                    self.logger.warning(f"删除死信文件失败 {file_path}: {e}")

            return count

        except Exception as e:
            self.logger.error(f"清理死信队列失败: {e}")
            return 0

    async def get_queue_size(self, state: MessageState | None = None) -> int:
        """获取队列大小"""
        try:
            if state is None:
                return len(self._index)

            state_dir = self.state_dirs[state]
            return len(list(state_dir.glob("*.json")))

        except Exception as e:
            self.logger.error(f"获取队列大小失败: {e}")
            return 0

    async def _load_index(self) -> None:
        """加载索引"""
        try:
            if self.index_file.exists():
                with open(self.index_file, "r") as f:
                    self._index = json.load(f)
            else:
                self._index = {}
        except Exception as e:
            self.logger.warning(f"加载索引失败: {e}，重建索引")
            await self._rebuild_index()

    async def _save_index(self) -> None:
        """保存索引"""
        try:
            with open(self.index_file, "w") as f:
                json.dump(self._index, f, indent=2)
        except Exception as e:
            self.logger.error(f"保存索引失败: {e}")

    async def _rebuild_index(self) -> None:
        """重建索引"""
        try:
            self._index = {}

            for state, state_dir in self.state_dirs.items():
                for file_path in state_dir.glob("*.json"):
                    message_id = file_path.stem
                    self._index[message_id] = state.value

            # 死信队列
            for file_path in self.dead_letter_dir.glob("*.json"):
                message_id = file_path.stem
                self._index[message_id] = MessageState.DEAD_LETTER.value

            await self._save_index()

        except Exception as e:
            self.logger.error(f"重建索引失败: {e}")


# =============================================================================
# === 别名和兼容性 ===
# =============================================================================

# 为保持兼容性，提供 FilePersistenceBackend 作为别名
FilePersistenceBackend = FilePersistence


__all__ = [
    "FilePersistence",
    "FilePersistenceBackend",  # 别名
]
