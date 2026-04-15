#!/usr/bin/env python3
from __future__ import annotations
"""
检查点管理器 - 失败恢复核心
Checkpoint Manager - Failure Recovery Core

实现执行状态的保存和恢复，支持从失败点恢复执行

Author: Athena Team
Version: 1.0.0
Date: 2026-02-26
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ========== 检查点状态 ==========


class CheckpointStatus(Enum):
    """检查点状态"""
    ACTIVE = "active"  # 活跃
    COMPLETED = "completed"  # 已完成
    ROLLED_BACK = "rolled_back"  # 已回退
    FAILED = "failed"  # 失败


# ========== 检查点数据结构 ==========


@dataclass
class StepCheckpoint:
    """步骤检查点"""
    step_id: str
    status: str  # pending/in_progress/completed/failed
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class Checkpoint:
    """
    执行检查点

    保存特定时间点的执行状态，支持回退
    """
    task_id: str
    plan_id: str
    checkpoint_id: str
    status: CheckpointStatus
    completed_steps: list[str]  # 已完成的步骤ID列表
    current_step: str | None = None  # 当前执行的步骤
    step_states: dict[str, StepCheckpoint] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "plan_id": self.plan_id,
            "checkpoint_id": self.checkpoint_id,
            "status": self.status.value,
            "completed_steps": self.completed_steps,
            "current_step": self.current_step,
            "step_states": {
                step_id: state.to_dict()
                for step_id, state in self.step_states.items()
            },
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


# ========== 检查点管理器 ==========


class CheckpointManager:
    """
    检查点管理器

    负责保存、加载和管理检查点
    """

    def __init__(self, storage_dir: str | None = None):
        """
        初始化检查点管理器

        Args:
            storage_dir: 检查点存储目录
        """
        if storage_dir is None:
            storage_dir = "data/checkpoints"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 运行时检查点缓存
        self._checkpoints: dict[str, Checkpoint] = {}

        logger.info(f"📂 检查点管理器初始化: {self.storage_dir}")

    def create_checkpoint(
        self,
        task_id: str,
        plan_id: str,
        completed_steps: list[str],
        current_step: str,
        step_states: dict[str, StepCheckpoint],
    ) -> Checkpoint:
        """
        创建检查点

        Args:
            task_id: 任务ID
            plan_id: 方案ID
            completed_steps: 已完成的步骤ID列表
            current_step: 当前步骤
            step_states: 步骤状态

        Returns:
            Checkpoint: 创建的检查点
        """
        checkpoint_id = f"cp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        checkpoint = Checkpoint(
            task_id=task_id,
            plan_id=plan_id,
            checkpoint_id=checkpoint_id,
            status=CheckpointStatus.ACTIVE,
            completed_steps=completed_steps,
            current_step=current_step,
            step_states=step_states,
            metadata={
                "total_steps": len(step_states),
                "progress": f"{len(completed_steps)}/{len(step_states)}",
            },
        )

        # 保存到缓存
        self._checkpoints[checkpoint_id] = checkpoint

        # 持久化到文件
        self._save_checkpoint(checkpoint)

        logger.info(f"💾 创建检查点: {checkpoint_id}")
        logger.info(f"   进度: {len(completed_steps)}/{len(step_states)} 步骤完成")

        return checkpoint

    def load_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """
        加载检查点

        Args:
            checkpoint_id: 检查点ID

        Returns:
            Checkpoint: 检查点，不存在返回None
        """
        # 先检查缓存
        if checkpoint_id in self._checkpoints:
            return self._checkpoints[checkpoint_id]

        # 从文件加载
        checkpoint_file = self.storage_dir / f"{checkpoint_id}.json"
        if not checkpoint_file.exists():
            logger.warning(f"⚠️ 检查点不存在: {checkpoint_id}")
            return None

        try:
            with open(checkpoint_file, encoding='utf-8') as f:
                data = json.load(f)

            # 重建StepCheckpoint对象
            step_states = {}
            for step_id, state_data in data.get("step_states", {}).items():
                step_states[step_id] = StepCheckpoint(**state_data)

            checkpoint = Checkpoint(
                task_id=data["task_id"],
                plan_id=data["plan_id"],
                checkpoint_id=data["checkpoint_id"],
                status=CheckpointStatus(data["status"]),
                completed_steps=data["completed_steps"],
                current_step=data.get("current_step"),
                step_states=step_states,
                metadata=data.get("metadata", {}),
                created_at=data["created_at"],
            )

            self._checkpoints[checkpoint_id] = checkpoint
            logger.info(f"📂 加载检查点: {checkpoint_id}")

            return checkpoint

        except Exception as e:
            logger.error(f"❌ 加载检查点失败: {e}", exc_info=True)
            return None

    def list_checkpoints(self, task_id: str | None = None) -> list[Checkpoint]:
        """
        列出检查点

        Args:
            task_id: 可选的任务ID过滤

        Returns:
            List[Checkpoint]: 检查点列表
        """
        checkpoints = []

        # 扫描存储目录
        for checkpoint_file in self.storage_dir.glob("*.json"):
            try:
                with open(checkpoint_file, encoding='utf-8') as f:
                    data = json.load(f)

                # 过滤任务ID
                if task_id is None or data.get("task_id") == task_id:
                    checkpoints.append(data)

            except Exception:
                logger.warning(f"⚠️ 读取检查点文件失败: {checkpoint_file}")

        return checkpoints

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        删除检查点

        Args:
            checkpoint_id: 检查点ID

        Returns:
            bool: 是否成功删除
        """
        # 从缓存中删除
        if checkpoint_id in self._checkpoints:
            del self._checkpoints[checkpoint_id]

        # 删除文件
        checkpoint_file = self.storage_dir / f"{checkpoint_id}.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()

        logger.info(f"🗑️ 删除检查点: {checkpoint_id}")
        return True

    def _save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """保存检查点到文件"""
        checkpoint_file = self.storage_dir / f"{checkpoint.checkpoint_id}.json"

        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint.to_dict(), f, ensure_ascii=False, indent=2)

    def get_latest_checkpoint(self, task_id: str) -> Checkpoint | None:
        """
        获取任务的最新检查点

        Args:
            task_id: 任务ID

        Returns:
            Checkpoint: 最新检查点，不存在返回None
        """
        checkpoints = self.list_checkpoints(task_id)

        if not checkpoints:
            return None

        # 按创建时间排序，取最新的
        checkpoints.sort(key=lambda cp: cp["created_at"], reverse=True)

        # 重建Checkpoint对象
        latest_data = checkpoints[0]
        step_states = {}
        for step_id, state_data in latest_data.get("step_states", {}).items():
            step_states[step_id] = StepCheckpoint(**state_data)

        return Checkpoint(
            task_id=latest_data["task_id"],
            plan_id=latest_data["plan_id"],
            checkpoint_id=latest_data["checkpoint_id"],
            status=CheckpointStatus(latest_data["status"]),
            completed_steps=latest_data["completed_steps"],
            current_step=latest_data.get("current_step"),
            step_states=step_states,
            metadata=latest_data.get("metadata", {}),
            created_at=latest_data["created_at"],
        )


# ========== 全局检查点管理器 ==========


_global_checkpoint_manager: CheckpointManager | None = None


def get_checkpoint_manager() -> CheckpointManager:
    """获取全局检查点管理器"""
    global _global_checkpoint_manager
    if _global_checkpoint_manager is None:
        _global_checkpoint_manager = CheckpointManager()
    return _global_checkpoint_manager


# ========== 导出 ==========


__all__ = [
    "CheckpointStatus",
    "StepCheckpoint",
    "Checkpoint",
    "CheckpointManager",
    "get_checkpoint_manager",
]
