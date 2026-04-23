#!/usr/bin/env python3
"""
会话存储接口

定义会话持久化的抽象接口。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Optional

from .types import SessionMemory

logger = logging.getLogger(__name__)


class SessionStorage:
    """会话存储基类"""

    def save(self, memory: SessionMemory) -> bool:
        """保存会话

        Args:
            memory: 会话记忆

        Returns:
            bool: 是否成功
        """
        raise NotImplementedError

    def load(self, session_id: str) -> SessionMemory | None:
        """加载会话

        Args:
            session_id: 会话ID

        Returns:
            SessionMemory | None: 会话记忆
        """
        raise NotImplementedError

    def delete(self, session_id: str) -> bool:
        """删除会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功
        """
        raise NotImplementedError

    def exists(self, session_id: str) -> bool:
        """检查会话是否存在

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否存在
        """
        raise NotImplementedError


class FileSessionStorage(SessionStorage):
    """文件会话存储

    使用文件系统存储会话。
    """

    def __init__(self, storage_dir: str = "data/sessions"):
        """初始化文件存储

        Args:
            storage_dir: 存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"💾 文件会话存储初始化: {self.storage_dir}")

    def _get_file_path(self, session_id: str) -> Path:
        """获取会话文件路径

        Args:
            session_id: 会话ID

        Returns:
            Path: 文件路径
        """
        return self.storage_dir / f"{session_id}.pkl"

    def save(self, memory: SessionMemory) -> bool:
        """保存会话

        Args:
            memory: 会话记忆

        Returns:
            bool: 是否成功
        """
        try:
            file_path = self._get_file_path(memory.context.session_id)
            with open(file_path, "wb") as f:
                pickle.dump(memory, f)
            logger.debug(f"💾 保存会话: {memory.context.session_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 保存会话失败 {memory.context.session_id}: {e}")
            return False

    def load(self, session_id: str) -> SessionMemory | None:
        """加载会话

        Args:
            session_id: 会话ID

        Returns:
            SessionMemory | None: 会话记忆
        """
        try:
            file_path = self._get_file_path(session_id)
            if not file_path.exists():
                return None

            with open(file_path, "rb") as f:
                memory = pickle.load(f)

            logger.debug(f"📂 加载会话: {session_id}")
            return memory
        except Exception as e:
            logger.error(f"❌ 加载会话失败 {session_id}: {e}")
            return None

    def delete(self, session_id: str) -> bool:
        """删除会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功
        """
        try:
            file_path = self._get_file_path(session_id)
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"🗑️ 删除会话文件: {session_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 删除会话文件失败 {session_id}: {e}")
            return False

    def exists(self, session_id: str) -> bool:
        """检查会话是否存在

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否存在
        """
        file_path = self._get_file_path(session_id)
        return file_path.exists()


__all__ = [
    "SessionStorage",
    "FileSessionStorage",
]
