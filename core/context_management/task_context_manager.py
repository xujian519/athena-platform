#!/usr/bin/env python3
from __future__ import annotations
"""
任务上下文持久化管理器
Task Context Persistence Manager - 任务执行上下文的持久化和恢复

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ContextStatus(Enum):
    """上下文状态"""

    ACTIVE = "active"  # 活跃
    SUSPENDED = "suspended"  # 暂停
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class StepContext:
    """步骤上下文"""

    step_id: str
    step_name: str
    status: str
    start_time: str | None = None
    end_time: str | None = None
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    error_message: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class TaskContext:
    """任务上下文"""

    task_id: str
    task_description: str
    created_at: str
    updated_at: str
    status: ContextStatus
    current_step: int = 0
    total_steps: int = 0
    steps: list[StepContext] = field(default_factory=list)
    global_variables: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "TaskContext":
        """从字典创建"""
        data["status"] = ContextStatus(data["status"])
        steps_data = data.pop("steps", [])
        steps = [StepContext(**s) for s in steps_data]
        return cls(steps=steps, **data)


class TaskContextManager:
    """任务上下文管理器"""

    def __init__(self, storage_path: Path | None = None):
        """
        初始化上下文管理器

        Args:
            storage_path: 上下文存储路径
        """
        self.storage_path = storage_path or Path("data/task_contexts")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, threading.Lock] = {}

        logger.info(f"💾 任务上下文管理器初始化: {self.storage_path}")

    def _get_context_file(self, task_id: str) -> Path:
        """获取上下文文件路径"""
        return self.storage_path / f"{task_id}.json"

    def _get_lock_file(self, task_id: str) -> Path:
        """获取锁文件路径"""
        return self.storage_path / f"{task_id}.lock"

    def _get_lock(self, task_id: str) -> threading.Lock:
        """获取任务锁"""
        if task_id not in self._locks:
            self._locks[task_id] = threading.Lock()
        return self._locks[task_id]

    async def create_context(
        self,
        task_id: str,
        task_description: str,
        total_steps: int = 0,
        metadata: dict | None = None,
    ) -> TaskContext:
        """
        创建新的任务上下文

        Args:
            task_id: 任务ID
            task_description: 任务描述
            total_steps: 总步骤数
            metadata: 元数据

        Returns:
            TaskContext: 任务上下文
        """
        context = TaskContext(
            task_id=task_id,
            task_description=task_description,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            status=ContextStatus.ACTIVE,
            current_step=0,
            total_steps=total_steps,
            metadata=metadata or {},
        )

        await self.save_context(context)
        logger.info(f"✅ 创建任务上下文: {task_id}")

        return context

    async def load_context(self, task_id: str) -> TaskContext | None:
        """
        加载任务上下文

        Args:
            task_id: 任务ID

        Returns:
            Optional[TaskContext]: 任务上下文,不存在返回None
        """
        context_file = self._get_context_file(task_id)

        if not context_file.exists():
            logger.warning(f"⚠️ 上下文文件不存在: {task_id}")
            return None

        try:
            with open(context_file, encoding="utf-8") as f:
                data = json.load(f)

            context = TaskContext.from_dict(data)
            logger.info(f"✅ 加载任务上下文: {task_id} (状态: {context.status.value})")

            return context

        except Exception as e:
            logger.error(f"❌ 加载上下文失败: {e}")
            return None

    async def save_context(self, context: TaskContext) -> bool:
        """
        保存任务上下文

        Args:
            context: 任务上下文

        Returns:
            bool: 是否成功
        """
        lock = self._get_lock(context.task_id)

        with lock:
            try:
                context.updated_at = datetime.now().isoformat()

                context_file = self._get_context_file(context.task_id)
                temp_file = context_file.with_suffix(".tmp")

                # 写入临时文件
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(context.to_dict(), f, ensure_ascii=False, indent=2)

                # 原子性替换
                temp_file.replace(context_file)

                logger.debug(f"💾 保存上下文: {context.task_id}")
                return True

            except Exception as e:
                logger.error(f"❌ 保存上下文失败: {e}")
                return False

    async def update_step(
        self,
        task_id: str,
        step_id: str,
        step_name: str,
        status: str,
        input_data: dict | None = None,
        output_data: dict | None = None,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> bool:
        """
        更新步骤上下文

        Args:
            task_id: 任务ID
            step_id: 步骤ID
            step_name: 步骤名称
            status: 步骤状态
            input_data: 输入数据
            output_data: 输出数据
            error_message: 错误信息
            metadata: 元数据

        Returns:
            bool: 是否成功
        """
        context = await self.load_context(task_id)

        if not context:
            logger.warning(f"⚠️ 任务上下文不存在: {task_id}")
            return False

        # 查找或创建步骤上下文
        step_context = next((s for s in context.steps if s.step_id == step_id), None)

        if step_context:
            # 更新现有步骤
            step_context.status = status
            step_context.output_data = output_data
            step_context.error_message = error_message
            if metadata:
                if step_context.metadata is None:
                    step_context.metadata = {}
                step_context.metadata.update(metadata)

            if status in ["completed", "failed", "cancelled"]:
                step_context.end_time = datetime.now().isoformat()
        else:
            # 创建新步骤
            step_context = StepContext(
                step_id=step_id,
                step_name=step_name,
                status=status,
                start_time=datetime.now().isoformat(),
                end_time=(
                    datetime.now().isoformat()
                    if status in ["completed", "failed", "cancelled"]
                    else None
                ),
                input_data=input_data,
                output_data=output_data,
                error_message=error_message,
                metadata=metadata,
            )
            context.steps.append(step_context)

        # 更新当前步骤
        if status == "in_progress":
            context.current_step = len([s for s in context.steps if s.status == "completed"]) + 1

        return await self.save_context(context)

    async def set_variable(self, task_id: str, key: str, value: Any) -> bool:
        """
        设置全局变量

        Args:
            task_id: 任务ID
            key: 变量名
            value: 变量值

        Returns:
            bool: 是否成功
        """
        context = await self.load_context(task_id)

        if not context:
            return False

        context.global_variables[key] = value
        return await self.save_context(context)

    async def get_variable(self, task_id: str, key: str, default: Any = None) -> Any:
        """
        获取全局变量

        Args:
            task_id: 任务ID
            key: 变量名
            default: 默认值

        Returns:
            Any: 变量值
        """
        context = await self.load_context(task_id)

        if not context:
            return default

        return context.global_variables.get(key, default)

    async def set_status(self, task_id: str, status: ContextStatus) -> bool:
        """
        设置任务状态

        Args:
            task_id: 任务ID
            status: 新状态

        Returns:
            bool: 是否成功
        """
        context = await self.load_context(task_id)

        if not context:
            return False

        context.status = status
        return await self.save_context(context)

    async def get_progress(self, task_id: str) -> dict[str, Any] | None:
        """
        获取任务进度

        Args:
            task_id: 任务ID

        Returns:
            Optional[Dict]: 进度信息
        """
        context = await self.load_context(task_id)

        if not context:
            return None

        completed_steps = len([s for s in context.steps if s.status == "completed"])
        progress = completed_steps / context.total_steps if context.total_steps > 0 else 0.0

        return {
            "task_id": task_id,
            "status": context.status.value,
            "current_step": context.current_step,
            "total_steps": context.total_steps,
            "completed_steps": completed_steps,
            "progress": progress,
            "created_at": context.created_at,
            "updated_at": context.updated_at,
        }

    async def delete_context(self, task_id: str) -> bool:
        """
        删除任务上下文

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功
        """
        context_file = self._get_context_file(task_id)
        lock_file = self._get_lock_file(task_id)

        try:
            if context_file.exists():
                context_file.unlink()

            if lock_file.exists():
                lock_file.unlink()

            logger.info(f"🗑️ 删除上下文: {task_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 删除上下文失败: {e}")
            return False

    async def list_contexts(self, status: ContextStatus | None = None) -> list[str]:
        """
        列出所有上下文

        Args:
            status: 状态过滤

        Returns:
            list[str]: 任务ID列表
        """
        context_files = list(self.storage_path.glob("*.json"))

        if status:
            task_ids = []
            for cf in context_files:
                try:
                    with open(cf) as f:
                        data = json.load(f)
                    if data.get("status") == status.value:
                        task_ids.append(cf.stem)
                except Exception:
                    pass
            return task_ids

        return [cf.stem for cf in context_files]


# 便捷函数
async def create_task_context(
    task_id: str, task_description: str, total_steps: int = 0
) -> TaskContext:
    """创建任务上下文的便捷函数"""
    manager = TaskContextManager()
    return await manager.create_context(task_id, task_description, total_steps)


async def resume_task_context(task_id: str) -> TaskContext | None:
    """恢复任务上下文的便捷函数"""
    manager = TaskContextManager()
    return await manager.load_context(task_id)


__all__ = [
    "ContextStatus",
    "StepContext",
    "TaskContext",
    "TaskContextManager",
    "create_task_context",
    "resume_task_context",
]
