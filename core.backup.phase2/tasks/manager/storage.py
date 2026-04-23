#!/usr/bin/env python3
from __future__ import annotations

"""
任务存储管理
Task Storage Management

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0
"""

import json
import logging
import threading
from pathlib import Path
from typing import Any

from .exceptions import TaskStorageError
from .models import Task

logger = logging.getLogger(__name__)


class TaskStorage:
    """任务存储基类"""

    def save(self, task: Task) -> bool:
        """保存任务

        Args:
            task: 任务对象

        Returns:
            bool: 是否保存成功
        """
        raise NotImplementedError

    def load(self, task_id: str) -> Task | None:
        """加载任务

        Args:
            task_id: 任务ID

        Returns:
            Task | None: 任务对象，不存在则返回None
        """
        raise NotImplementedError

    def delete(self, task_id: str) -> bool:
        """删除任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否删除成功
        """
        raise NotImplementedError

    def exists(self, task_id: str) -> bool:
        """检查任务是否存在

        Args:
            task_id: 任务ID

        Returns:
            bool: 任务是否存在
        """
        raise NotImplementedError

    def load_all(self) -> dict[str, Task]:
        """加载所有任务

        Returns:
            dict: {task_id: Task} 字典
        """
        raise NotImplementedError

    def load_by_status(self, status: Any) -> list[Task]:
        """按状态加载任务

        Args:
            status: 任务状态

        Returns:
            list: 任务列表
        """
        raise NotImplementedError

    def load_by_agent(self, agent_id: str) -> list[Task]:
        """按Agent ID加载任务

        Args:
            agent_id: Agent ID

        Returns:
            list: 任务列表
        """
        raise NotImplementedError

    def load_by_session(self, session_id: str) -> list[Task]:
        """按会话ID加载任务

        Args:
            session_id: 会话ID

        Returns:
            list: 任务列表
        """
        raise NotImplementedError


class FileTaskStorage(TaskStorage):
    """文件任务存储"""

    def __init__(self, storage_dir: str | Path | None = None):
        """初始化文件存储

        Args:
            storage_dir: 存储目录路径
        """
        if storage_dir is None:
            storage_dir = Path(__file__).parent.parent.parent.parent / "data" / "tasks"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.tasks_file = self.storage_dir / "tasks.json"
        self._lock = threading.RLock()
        self._index: dict[str, Task] = {}

        # 加载现有任务到内存索引
        self._load_index()

    def _load_index(self) -> None:
        """加载任务到内存索引"""
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, encoding="utf-8") as f:
                    data = json.load(f)

                for task_id, task_data in data.items():
                    try:
                        self._index[task_id] = Task.from_dict(task_data)
                    except Exception as e:
                        logger.error(f"加载任务 {task_id} 失败: {e}")

                logger.info(f"已加载 {len(self._index)} 个任务到内存索引")
        except Exception as e:
            logger.error(f"加载任务索引失败: {e}")
            self._index = {}

    def _save_index(self) -> None:
        """保存内存索引到文件"""
        try:
            data = {
                task_id: task.to_dict()
                for task_id, task in self._index.items()
            }

            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存任务索引失败: {e}")
            raise TaskStorageError("save", str(e))

    def save(self, task: Task) -> bool:
        """保存任务

        Args:
            task: 任务对象

        Returns:
            bool: 是否保存成功
        """
        with self._lock:
            try:
                self._index[task.id] = task
                self._save_index()
                return True
            except Exception as e:
                logger.error(f"保存任务 {task.id} 失败: {e}")
                raise TaskStorageError("save", str(e))

    def load(self, task_id: str) -> Task | None:
        """加载任务

        Args:
            task_id: 任务ID

        Returns:
            Task | None: 任务对象
        """
        with self._lock:
            return self._index.get(task_id)

    def delete(self, task_id: str) -> bool:
        """删除任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否删除成功
        """
        with self._lock:
            if task_id not in self._index:
                return False

            try:
                del self._index[task_id]
                self._save_index()
                return True
            except Exception as e:
                logger.error(f"删除任务 {task_id} 失败: {e}")
                raise TaskStorageError("delete", str(e))

    def exists(self, task_id: str) -> bool:
        """检查任务是否存在

        Args:
            task_id: 任务ID

        Returns:
            bool: 任务是否存在
        """
        with self._lock:
            return task_id in self._index

    def load_all(self) -> dict[str, Task]:
        """加载所有任务

        Returns:
            dict: {task_id: Task} 字典
        """
        with self._lock:
            return dict(self._index)

    def load_by_status(self, status: Any) -> list[Task]:
        """按状态加载任务

        Args:
            status: 任务状态

        Returns:
            list: 任务列表
        """
        with self._lock:
            return [task for task in self._index.values() if task.status == status]

    def load_by_agent(self, agent_id: str) -> list[Task]:
        """按Agent ID加载任务

        Args:
            agent_id: Agent ID

        Returns:
            list: 任务列表
        """
        with self._lock:
            return [task for task in self._index.values() if task.assigned_to == agent_id]

    def load_by_session(self, session_id: str) -> list[Task]:
        """按会话ID加载任务

        Args:
            session_id: 会话ID

        Returns:
            list: 任务列表
        """
        with self._lock:
            return [task for task in self._index.values() if task.session_id == session_id]

    def clear(self) -> bool:
        """清空所有任务

        Returns:
            bool: 是否清空成功
        """
        with self._lock:
            try:
                self._index.clear()
                self._save_index()
                return True
            except Exception as e:
                logger.error(f"清空任务失败: {e}")
                raise TaskStorageError("clear", str(e))

    def get_stats(self) -> dict[str, Any]:
        """获取存储统计信息

        Returns:
            dict: 统计信息
        """
        with self._lock:
            total_tasks = len(self._index)
            status_counts: dict[str, int] = {}
            agent_counts: dict[str, int] = {}
            session_counts: dict[str, int] = {}

            for task in self._index.values():
                status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1

                if task.assigned_to:
                    agent_counts[task.assigned_to] = agent_counts.get(task.assigned_to, 0) + 1

                if task.session_id:
                    session_counts[task.session_id] = session_counts.get(task.session_id, 0) + 1

            return {
                "total_tasks": total_tasks,
                "status_counts": status_counts,
                "agent_counts": agent_counts,
                "session_counts": session_counts,
                "storage_file": str(self.tasks_file),
            }
