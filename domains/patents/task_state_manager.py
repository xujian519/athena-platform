#!/usr/bin/env python3
from __future__ import annotations

"""
专利撰写任务状态管理器 (Patent Drafting Task State Manager)

支持长任务的持久化存储和跨会话恢复。

功能：
- 任务状态YAML持久化
- 阶段进度跟踪
- 断点续传支持
- 子任务管理

参考：
- OpenClaw patent-drafting skill task_state.yaml
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class PhaseStatus(Enum):
    """阶段状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class PhaseState:
    """阶段状态"""

    phase_id: int
    phase_name: str
    status: str = "pending"
    subagent_id: str | None = None
    output_file: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TaskState:
    """任务状态"""

    task_id: str
    task_type: str = "patent-drafting"
    client: str = ""
    created: str = ""
    updated: str = ""
    status: str = "pending"
    current_phase: int = 0
    phases: list[dict] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class TaskStateManager:
    """
    任务状态管理器

    支持长任务的持久化存储和跨会话恢复。
    """

    # 专利撰写9阶段定义（参考OpenClaw）
    DEFAULT_PHASES = [
        {"phase_id": 0, "phase_name": "技术交底书理解", "status": "pending"},
        {"phase_id": 1, "phase_name": "现有技术检索", "status": "pending"},
        {"phase_id": 2, "phase_name": "对比分析", "status": "pending"},
        {"phase_id": 3, "phase_name": "发明点确定", "status": "pending"},
        {"phase_id": 4, "phase_name": "说明书撰写", "status": "pending"},
        {"phase_id": 5, "phase_name": "权利要求撰写", "status": "pending"},
        {"phase_id": 6, "phase_name": "审查员模拟", "status": "pending"},
        {"phase_id": 7, "phase_name": "修改完善", "status": "pending"},
        {"phase_id": 8, "phase_name": "最终确认", "status": "pending"},
    ]

    def __init__(self, storage_dir: str = "cases"):
        """
        初始化任务状态管理器

        Args:
            storage_dir: 存储目录（默认cases/）
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ 任务状态管理器初始化完成，存储目录: {self.storage_dir}")

    def create_task(
        self,
        task_id: str,
        client: str = "",
        task_type: str = "patent-drafting",
        custom_phases: list[dict] | None = None,
    ) -> TaskState:
        """
        创建新任务

        Args:
            task_id: 任务ID
            client: 客户名称
            task_type: 任务类型
            custom_phases: 自定义阶段列表

        Returns:
            TaskState: 任务状态
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        task = TaskState(
            task_id=task_id,
            task_type=task_type,
            client=client,
            created=now,
            updated=now,
            status=TaskStatus.PENDING.value,
            current_phase=0,
            phases=custom_phases or self.DEFAULT_PHASES.copy(),
            context={},
            notes=[],
        )

        # 保存到文件
        self._save_task(task)

        logger.info(f"✅ 创建任务: {task_id}")
        return task

    def load_task(self, task_id: str) -> TaskState | None:
        """
        加载任务状态

        Args:
            task_id: 任务ID

        Returns:
            TaskState or None: 任务状态
        """
        task_file = self.storage_dir / task_id / "task_state.yaml"

        if not task_file.exists():
            # 尝试JSON格式
            task_file = self.storage_dir / task_id / "task_state.json"
            if not task_file.exists():
                logger.warning(f"任务不存在: {task_id}")
                return None

        try:
            with open(task_file, encoding="utf-8") as f:
                if task_file.suffix == ".yaml":
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)

            task = TaskState(**data)
            logger.info(f"✅ 加载任务: {task_id}, 当前阶段: {task.current_phase}")
            return task

        except Exception as e:
            logger.error(f"加载任务失败: {task_id}, 错误: {e}")
            return None

    def save_task(self, task: TaskState) -> bool:
        """
        保存任务状态

        Args:
            task: 任务状态

        Returns:
            bool: 是否成功
        """
        task.updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self._save_task(task)

    def _save_task(self, task: TaskState) -> bool:
        """内部保存方法"""
        task_dir = self.storage_dir / task.task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        task_file = task_dir / "task_state.yaml"

        try:
            with open(task_file, "w", encoding="utf-8") as f:
                yaml.dump(task.to_dict(), f, allow_unicode=True, default_flow_style=False)

            logger.info(f"✅ 保存任务: {task.task_id}")
            return True

        except Exception as e:
            logger.error(f"保存任务失败: {task.task_id}, 错误: {e}")
            return False

    def update_phase(
        self,
        task_id: str,
        phase_id: int,
        status: str,
        output_file: str | None = None,
        notes: list[str] | None = None,
    ) -> TaskState | None:
        """
        更新阶段状态

        Args:
            task_id: 任务ID
            phase_id: 阶段ID
            status: 阶段状态
            output_file: 输出文件路径
            notes: 备注列表

        Returns:
            TaskState or None: 更新后的任务状态
        """
        task = self.load_task(task_id)
        if not task:
            return None

        # 更新阶段状态
        for phase in task.phases:
            if phase["phase_id"] == phase_id:
                phase["status"] = status

                if status == PhaseStatus.IN_PROGRESS.value:
                    phase["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                elif status == PhaseStatus.COMPLETED.value:
                    phase["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if output_file:
                    phase["output_file"] = output_file
                if notes:
                    phase["notes"] = notes
                break

        # 更新当前阶段
        if status == PhaseStatus.COMPLETED.value:
            # 找到下一个未完成的阶段
            for _i, phase in enumerate(task.phases):
                if phase["status"] == PhaseStatus.PENDING.value:
                    task.current_phase = phase["phase_id"]
                    break
            else:
                # 所有阶段完成
                task.status = TaskStatus.COMPLETED.value

        self.save_task(task)
        return task

    def advance_phase(self, task_id: str) -> TaskState | None:
        """
        推进到下一阶段

        Args:
            task_id: 任务ID

        Returns:
            TaskState or None: 更新后的任务状态
        """
        task = self.load_task(task_id)
        if not task:
            return None

        # 标记当前阶段完成
        for phase in task.phases:
            if phase["phase_id"] == task.current_phase:
                phase["status"] = PhaseStatus.COMPLETED.value
                phase["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break

        # 找到下一阶段
        for phase in task.phases:
            if (
                phase["phase_id"] > task.current_phase
                and phase["status"] == PhaseStatus.PENDING.value
            ):
                task.current_phase = phase["phase_id"]
                phase["status"] = PhaseStatus.IN_PROGRESS.value
                phase["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break
        else:
            # 所有阶段完成
            task.status = TaskStatus.COMPLETED.value

        self.save_task(task)
        return task

    def pause_task(self, task_id: str, reason: str = "") -> TaskState | None:
        """
        暂停任务

        Args:
            task_id: 任务ID
            reason: 暂停原因

        Returns:
            TaskState or None: 更新后的任务状态
        """
        task = self.load_task(task_id)
        if not task:
            return None

        task.status = TaskStatus.PAUSED.value
        if reason:
            task.notes.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 暂停: {reason}")

        self.save_task(task)
        logger.info(f"⏸️ 暂停任务: {task_id}")
        return task

    def resume_task(self, task_id: str) -> TaskState | None:
        """
        恢复任务

        Args:
            task_id: 任务ID

        Returns:
            TaskState or None: 更新后的任务状态
        """
        task = self.load_task(task_id)
        if not task:
            return None

        if task.status != TaskStatus.PAUSED.value:
            logger.warning(f"任务未暂停，无法恢复: {task_id}")
            return task

        task.status = TaskStatus.IN_PROGRESS.value
        task.notes.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 恢复任务")

        self.save_task(task)
        logger.info(f"▶️ 恢复任务: {task_id}")
        return task

    def get_progress(self, task_id: str) -> dict[str, Any]:
        """
        获取任务进度

        Args:
            task_id: 任务ID

        Returns:
            Dict: 进度信息
        """
        task = self.load_task(task_id)
        if not task:
            return {"error": "任务不存在"}

        completed = sum(1 for p in task.phases if p["status"] == PhaseStatus.COMPLETED.value)
        total = len(task.phases)
        progress_pct = (completed / total * 100) if total > 0 else 0

        return {
            "task_id": task_id,
            "status": task.status,
            "current_phase": task.current_phase,
            "current_phase_name": next(
                (
                    p["phase_name"]
                    for p in task.phases
                    if p["phase_id"] == task.current_phase
                ),
                "未知",
            ),
            "completed_phases": completed,
            "total_phases": total,
            "progress_percentage": f"{progress_pct:.1f}%",
            "created": task.created,
            "updated": task.updated,
        }

    def list_tasks(self, status: str | None = None) -> list[dict]:
        """
        列出所有任务

        Args:
            status: 筛选状态

        Returns:
            List[Dict]: 任务列表
        """
        tasks = []

        for task_dir in self.storage_dir.iterdir():
            if task_dir.is_dir():
                task = self.load_task(task_dir.name)
                if task:
                    if status is None or task.status == status:
                        tasks.append(
                            {
                                "task_id": task.task_id,
                                "client": task.client,
                                "status": task.status,
                                "current_phase": task.current_phase,
                                "updated": task.updated,
                            }
                        )

        # 按更新时间排序
        tasks.sort(key=lambda x: x["updated"], reverse=True)
        return tasks

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功
        """
        import shutil

        task_dir = self.storage_dir / task_id
        if task_dir.exists():
            shutil.rmtree(task_dir)
            logger.info(f"🗑️ 删除任务: {task_id}")
            return True

        return False


# 便捷函数
def create_task_manager(storage_dir: str = "cases") -> TaskStateManager:
    """创建任务管理器"""
    return TaskStateManager(storage_dir)


# 测试
if __name__ == "__main__":
    # 创建任务管理器
    manager = TaskStateManager(storage_dir="test_cases")

    # 创建新任务
    task = manager.create_task(task_id="CASE-2026-TEST", client="测试客户")
    print(f"创建任务: {task.task_id}")

    # 查看进度
    progress = manager.get_progress("CASE-2026-TEST")
    print(f"进度: {progress}")

    # 更新阶段
    manager.update_phase("CASE-2026-TEST", 0, "completed", output_file="phase0_output.md")
    manager.advance_phase("CASE-2026-TEST")

    # 查看更新后的进度
    progress = manager.get_progress("CASE-2026-TEST")
    print(f"更新后进度: {progress}")

    # 暂停/恢复
    manager.pause_task("CASE-2026-TEST", "等待客户确认")
    manager.resume_task("CASE-2026-TEST")

    # 列出任务
    tasks = manager.list_tasks()
    print(f"任务列表: {tasks}")

    # 清理测试
    manager.delete_task("CASE-2026-TEST")
