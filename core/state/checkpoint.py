#!/usr/bin/env python3
from __future__ import annotations
"""
检查点管理器
Checkpoint Manager

管理关键节点的状态检查点:
- 自动保存检查点
- 检查点恢复
- 检查点清理

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .state_module import StateModule

logger = logging.getLogger(__name__)


@dataclass
class CheckpointInfo:
    """检查点信息"""
    checkpoint_id: str
    file_path: str
    created_at: datetime
    size_bytes: int
    metadata: dict[str, Any]
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "checkpoint_id": self.checkpoint_id,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat(),
            "size_bytes": self.size_bytes,
            "metadata": self.metadata
        }


class CheckpointManager:
    """
    检查点管理器

    管理状态检查点的保存、恢复和清理。
    """

    def __init__(
        self,
        checkpoint_dir: str = "data/checkpoints",
        max_checkpoints: int = 10,
        auto_cleanup: bool = True
    ):
        """
        初始化检查点管理器

        Args:
            checkpoint_dir: 检查点目录
            max_checkpoints: 最大保留检查点数量
            auto_cleanup: 是否自动清理旧检查点
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.max_checkpoints = max_checkpoints
        self.auto_cleanup = auto_cleanup

        # 确保目录存在
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"🔖 CheckpointManager初始化完成 "
            f"(目录: {checkpoint_dir}, 最大: {max_checkpoints})"
        )

    async def save_checkpoint(
        self,
        state_module: StateModule,
        checkpoint_id: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> CheckpointInfo:
        """
        保存检查点

        Args:
            state_module: 要保存的状态模块
            checkpoint_id: 检查点ID(可选,默认使用时间戳)
            metadata: 元数据(可选)

        Returns:
            检查点信息
        """
        if checkpoint_id is None:
            checkpoint_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        file_name = f"{checkpoint_id}.json"
        file_path = self.checkpoint_dir / file_name

        # 保存状态
        await state_module.save_state(str(file_path))

        # 获取文件大小
        size_bytes = file_path.stat().st_size

        # 创建检查点信息
        info = CheckpointInfo(
            checkpoint_id=checkpoint_id,
            file_path=str(file_path),
            created_at=datetime.now(),
            size_bytes=size_bytes,
            metadata=metadata or {}
        )

        logger.info(
            f"💾 检查点已保存: {checkpoint_id} "
            f"({size_bytes} bytes)"
        )

        # 自动清理旧检查点
        if self.auto_cleanup:
            await self._cleanup_old_checkpoints()

        return info

    async def load_checkpoint(
        self,
        state_module: StateModule,
        checkpoint_id: str | None = None
    ) -> CheckpointInfo | None:
        """
        加载检查点

        Args:
            state_module: 要恢复的状态模块
            checkpoint_id: 检查点ID(可选,默认加载最新的)

        Returns:
            检查点信息,如果失败返回None
        """
        file_path = await self._find_checkpoint_file(checkpoint_id)

        if file_path is None:
            logger.warning(f"⚠️ 检查点不存在: {checkpoint_id or 'latest'}")
            return None

        try:
            await state_module.load_state(file_path)

            # 提取checkpoint_id
            if checkpoint_id is None:
                checkpoint_id = Path(file_path).stem

            info = CheckpointInfo(
                checkpoint_id=checkpoint_id,
                file_path=file_path,
                created_at=datetime.fromtimestamp(Path(file_path).stat().st_mtime),
                size_bytes=Path(file_path).stat().st_size,
                metadata={}
            )

            logger.info(f"📂 检查点已加载: {checkpoint_id}")

            return info

        except Exception as e:
            logger.error(f"❌ 加载检查点失败: {checkpoint_id} - {e}", exc_info=True)
            return None

    async def _find_checkpoint_file(
        self,
        checkpoint_id: str | None = None
    ) -> str | None:
        """
        查找检查点文件

        Args:
            checkpoint_id: 检查点ID,None表示查找最新的

        Returns:
            文件路径,如果不存在返回None
        """
        if checkpoint_id is not None:
            # 查找指定ID的检查点
            file_path = self.checkpoint_dir / f"{checkpoint_id}.json"
            if file_path.exists():
                return str(file_path)
            return None

        # 查找最新的检查点
        checkpoints = list(self.checkpoint_dir.glob("*.json"))

        if not checkpoints:
            return None

        # 按修改时间排序,返回最新的
        latest = max(checkpoints, key=lambda p: p.stat().st_mtime)
        return str(latest)

    async def list_checkpoints(
        self,
        sort_by: str = "created_at",
        reverse: bool = True
    ) -> list[CheckpointInfo]:
        """
        列出所有检查点

        Args:
            sort_by: 排序字段 (created_at, size_bytes)
            reverse: 是否降序

        Returns:
            检查点信息列表
        """
        checkpoints = []

        for file_path in self.checkpoint_dir.glob("*.json"):
            stat = file_path.stat()

            # 读取元数据
            metadata = {}
            try:
                with open(file_path, encoding='utf-8') as f:
                    data = json.load(f)
                    metadata = data.get("_metadata", {})
            except Exception as e:
                # 记录异常但不中断流程
                logger.debug(f"[checkpoint] Exception: {e}")

            checkpoints.append(CheckpointInfo(
                checkpoint_id=file_path.stem,
                file_path=str(file_path),
                created_at=datetime.fromtimestamp(stat.st_mtime),
                size_bytes=stat.st_size,
                metadata=metadata
            ))

        # 排序
        if sort_by == "created_at":
            checkpoints.sort(key=lambda c: c.created_at, reverse=reverse)
        elif sort_by == "size_bytes":
            checkpoints.sort(key=lambda c: c.size_bytes, reverse=reverse)

        return checkpoints

    async def delete_checkpoint(
        self,
        checkpoint_id: str
    ) -> bool:
        """
        删除检查点

        Args:
            checkpoint_id: 检查点ID

        Returns:
            是否成功删除
        """
        file_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not file_path.exists():
            logger.warning(f"⚠️ 检查点不存在: {checkpoint_id}")
            return False

        try:
            file_path.unlink()
            logger.info(f"🗑️ 检查点已删除: {checkpoint_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 删除检查点失败: {checkpoint_id} - {e}")
            return False

    async def delete_all_checkpoints(self) -> int:
        """
        删除所有检查点

        Returns:
            删除的检查点数量
        """
        count = 0

        for file_path in self.checkpoint_dir.glob("*.json"):
            try:
                file_path.unlink()
                count += 1
            except Exception as e:
                logger.error(f"❌ 删除检查点失败: {file_path} - {e}")

        logger.info(f"🗑️ 已删除 {count} 个检查点")
        return count

    async def _cleanup_old_checkpoints(self) -> None:
        """清理旧检查点,保留最新的max_checkpoints个"""
        checkpoints = list(self.checkpoint_dir.glob("*.json"))

        if len(checkpoints) <= self.max_checkpoints:
            return

        # 按修改时间排序
        checkpoints.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # 删除超出数量限制的旧检查点
        for old_checkpoint in checkpoints[self.max_checkpoints:]:
            try:
                old_checkpoint.unlink()
                logger.debug(f"🗑️ 清理旧检查点: {old_checkpoint.stem}")
            except Exception as e:
                logger.warning(f"清理检查点失败: {old_checkpoint} - {e}")

    async def get_checkpoint_info(
        self,
        checkpoint_id: str
    ) -> CheckpointInfo | None:
        """
        获取检查点信息

        Args:
            checkpoint_id: 检查点ID

        Returns:
            检查点信息,如果不存在返回None
        """
        file_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not file_path.exists():
            return None

        stat = file_path.stat()

        # 读取元数据
        metadata = {}
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
                metadata = data.get("_metadata", {})
        except Exception as e:
            # 记录异常但不中断流程
            logger.debug(f"[checkpoint] Exception: {e}")

        return CheckpointInfo(
            checkpoint_id=checkpoint_id,
            file_path=str(file_path),
            created_at=datetime.fromtimestamp(stat.st_mtime),
            size_bytes=stat.st_size,
            metadata=metadata
        )

    async def save_with_metadata(
        self,
        state_module: StateModule,
        checkpoint_id: str | None = None,
        **metadata
    ) -> CheckpointInfo:
        """
        保存检查点并附加元数据

        Args:
            state_module: 状态模块
            checkpoint_id: 检查点ID
            **metadata: 元数据键值对

        Returns:
            检查点信息
        """
        # 生成ID
        if checkpoint_id is None:
            checkpoint_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 准备元数据
        full_metadata = {
            "_metadata": {
                "saved_at": datetime.now().isoformat(),
                "module_class": state_module.__class__.__name__,
                **metadata
            }
        }

        # 临时添加元数据到状态
        original_metadata = {}
        for key, value in metadata.items():
            attr_name = f"_meta_{key}"
            if hasattr(state_module, attr_name):
                original_metadata[attr_name] = getattr(state_module, attr_name)
            setattr(state_module, attr_name, value)

        try:
            # 保存检查点
            info = await self.save_checkpoint(
                state_module,
                checkpoint_id=checkpoint_id,
                metadata=full_metadata
            )

            # 更新文件,添加元数据
            file_path = Path(info.file_path)
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)

            data.update(full_metadata)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            return info

        finally:
            # 恢复原始状态
            for attr_name, value in original_metadata.items():
                setattr(state_module, attr_name, value)


__all__ = [
    'CheckpointInfo',
    'CheckpointManager'
]
