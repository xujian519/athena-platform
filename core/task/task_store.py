from __future__ import annotations
"""
TaskStore - 任务存储系统

集成Athena四层记忆系统，提供任务的持久化存储和查询。
"""

import json
import sqlite3
import threading
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any

from core.agents.task_tool.models import TaskRecord, TaskStatus


class TaskStore:
    """任务存储类

    集成Athena四层记忆系统：
    - HOT层: 内存存储（LRU缓存）
    - WARM层: Redis缓存（可选）
    - COLD层: SQLite持久化
    - ARCHIVE层: 长期存储（未来扩展）
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """初始化TaskStore

        Args:
            config: 配置字典
                - hot_limit_mb: 热层大小限制（MB），默认100
                - warm_ttl: 温层TTL（秒），默认3600
                - cold_db_path: 冷层数据库路径，默认"data/tasks.db"
                - redis_host: Redis主机，默认"localhost"
                - redis_port: Redis端口，默认6379
        """
        self.config = config or {}

        # 热层配置
        self.hot_limit_bytes = self.config.get("hot_limit_mb", 100) * 1024 * 1024
        self.hot_cache: OrderedDict[str, TaskRecord] = OrderedDict()
        self.hot_cache_size = 0
        self.hot_lock = threading.RLock()

        # 温层配置
        self.warm_ttl = self.config.get("warm_ttl", 3600)
        self.redis_client = None
        self._init_warm_tier()

        # 冷层配置
        self.cold_db_path = self.config.get("cold_db_path", "data/tasks.db")
        self.cold_conn = None
        self._init_cold_tier()

    def _init_warm_tier(self) -> bool:
        """初始化温层（Redis）"""
        try:
            import redis

            self.redis_client = redis.Redis(
                host=self.config.get("redis_host", "localhost"),
                port=self.config.get("redis_port", 6379),
                db=self.config.get("redis_db", 0),
                decode_responses=False,
            )
            # 测试连接
            self.redis_client.ping()
            return True
        except Exception as e:
            print(f"Redis连接失败，跳过温层: {e}")
            return False

    def _init_cold_tier(self) -> None:
        """初始化冷层（SQLite）"""
        # 确保目录存在
        Path(self.cold_db_path).parent.mkdir(parents=True, exist_ok=True)

        self.cold_conn = sqlite3.connect(self.cold_db_path)
        self.cold_conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """创建数据库表"""
        self.cold_conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                model TEXT NOT NULL,
                status TEXT NOT NULL,
                prompt TEXT,
                tools TEXT,
                context TEXT,
                output_content TEXT,
                tool_uses INTEGER DEFAULT 0,
                duration REAL DEFAULT 0.0,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        self.cold_conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON tasks(agent_id)")
        self.cold_conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)")
        self.cold_conn.execute("CREATE INDEX IF NOT EXISTS idx_updated_at ON tasks(updated_at)")
        self.cold_conn.commit()

    def save_task(self, task_record: TaskRecord) -> bool:
        """保存任务

        Args:
            task_record: 任务记录

        Returns:
            True如果保存成功，False如果失败
        """
        try:
            # 先保存到冷层
            self._save_to_cold_tier(task_record)

            # 更新热层
            self._save_to_hot_tier(task_record)

            # 更新温层（如果Redis可用）
            if self.redis_client:
                self._save_to_warm_tier(task_record)

            return True
        except Exception as e:
            print(f"保存任务失败: {e}")
            return False

    def _save_to_hot_tier(self, task_record: TaskRecord) -> None:
        """保存到热层"""
        with self.hot_lock:
            # 计算任务大小（简化估算）
            task_size = len(task_record.to_dict().__str__())

            # 检查并清理空间
            while self.hot_cache_size + task_size > self.hot_limit_bytes and self.hot_cache:
                lru_task_id = next(iter(self.hot_cache))
                lru_task = self.hot_cache.pop(lru_task_id)
                self.hot_cache_size -= len(lru_task.to_dict().__str__())

            # 添加或更新任务
            if task_record.task_id in self.hot_cache:
                old_task = self.hot_cache[task_record.task_id]
                self.hot_cache_size -= len(old_task.to_dict().__str__())

            self.hot_cache[task_record.task_id] = task_record
            self.hot_cache_size += task_size

            # 移动到最前面
            self.hot_cache.move_to_end(task_record.task_id, last=False)

    def _save_to_warm_tier(self, task_record: TaskRecord) -> None:
        """保存到温层（Redis）"""
        try:
            import pickle

            key = f"task:{task_record.task_id}"
            value = pickle.dumps(task_record)
            self.redis_client.set(key, value, ex=self.warm_ttl)
        except Exception as e:
            print(f"保存到温层失败: {e}")

    def _save_to_cold_tier(self, task_record: TaskRecord) -> None:
        """保存到冷层（SQLite）"""
        self.cold_conn.execute(
            """
            INSERT OR REPLACE INTO tasks (
                task_id, agent_id, model, status,
                prompt, tools, context,
                output_content, tool_uses, duration, success,
                error_message, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_record.task_id,
                task_record.agent_id,
                task_record.model,
                task_record.status.value,
                task_record.input.prompt,
                json.dumps(task_record.input.tools),
                json.dumps(task_record.input.context),
                task_record.output.content if task_record.output else None,
                task_record.output.tool_uses if task_record.output else 0,
                task_record.output.duration if task_record.output else 0.0,
                task_record.output.success if task_record.output else True,
                task_record.error_message,
                task_record.created_at,
                task_record.updated_at,
            ),
        )
        self.cold_conn.commit()

    def get_task(self, task_id: str) -> TaskRecord | None:
        """获取任务

        Args:
            task_id: 任务ID

        Returns:
            TaskRecord对象，如果不存在则返回None
        """
        # 先从热层查找
        task = self._get_from_hot_tier(task_id)
        if task:
            return task

        # 从温层查找
        if self.redis_client:
            task = self._get_from_warm_tier(task_id)
            if task:
                # 加载到热层
                self._save_to_hot_tier(task)
                return task

        # 从冷层查找
        task = self._get_from_cold_tier(task_id)
        if task:
            # 加载到热层
            self._save_to_hot_tier(task)
            return task

        return None

    def _get_from_hot_tier(self, task_id: str) -> TaskRecord | None:
        """从热层获取"""
        with self.hot_lock:
            if task_id in self.hot_cache:
                task = self.hot_cache[task_id]
                # 更新访问信息
                task.updated_at = datetime.utcnow().isoformat() + "Z"
                # 移动到最前面
                self.hot_cache.move_to_end(task_id, last=False)
                return task
        return None

    def _get_from_warm_tier(self, task_id: str) -> TaskRecord | None:
        """从温层获取"""
        try:
            import pickle

            key = f"task:{task_id}"
            value = self.redis_client.get(key)
            if value:
                task = pickle.loads(value)
                # 延长TTL
                self.redis_client.expire(key, self.warm_ttl)
                return task
        except Exception as e:
            print(f"从温层获取失败: {e}")
        return None

    def _get_from_cold_tier(self, task_id: str) -> TaskRecord | None:
        """从冷层获取"""

        cursor = self.cold_conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()

        if row:
            return self._row_to_task_record(row)
        return None

    def _row_to_task_record(self, row: sqlite3.Row) -> TaskRecord:
        """将数据库行转换为TaskRecord"""
        from core.agents.task_tool.models import TaskInput, TaskOutput, TaskStatus

        status = TaskStatus(row["status"])

        task_input = TaskInput(
            prompt=row["prompt"],
            tools=json.loads(row["tools"]) if row["tools"] else [],
            context=json.loads(row["context"]) if row["context"] else {},
        )

        task_output = None
        if row["output_content"]:
            task_output = TaskOutput(
                content=row["output_content"],
                tool_uses=row["tool_uses"],
                duration=row["duration"],
                success=row["success"],
            )

        return TaskRecord(
            task_id=row["task_id"],
            agent_id=row["agent_id"],
            model=row["model"],
            status=status,
            input=task_input,
            output=task_output,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error_message=row["error_message"],
        )

    def get_active_tasks(self, agent_id: Optional[str] = None) -> list[TaskRecord]:
        """获取活动任务

        Args:
            agent_id: 可选的代理ID过滤

        Returns:
            活动任务列表
        """
        active_statuses = [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]

        if agent_id:
            cursor = self.cold_conn.execute(
                "SELECT * FROM tasks WHERE agent_id = ? AND status IN (?, ?)",
                (agent_id, *active_statuses),
            )
        else:
            cursor = self.cold_conn.execute(
                "SELECT * FROM tasks WHERE status IN (?, ?)",
                active_statuses,
            )

        return [self._row_to_task_record(row) for row in cursor.fetchall()]

    def get_task_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TaskRecord]:
        """获取任务历史

        Args:
            agent_id: 可选的代理ID过滤
            limit: 最大返回数量
            offset: 偏移量

        Returns:
            任务历史列表
        """
        if agent_id:
            cursor = self.cold_conn.execute(
                """
                SELECT * FROM tasks WHERE agent_id = ?
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
                """,
                (agent_id, limit, offset),
            )
        else:
            cursor = self.cold_conn.execute(
                """
                SELECT * FROM tasks
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )

        return [self._row_to_task_record(row) for row in cursor.fetchall()]

    def close(self) -> None:
        """关闭存储"""
        if self.cold_conn:
            self.cold_conn.close()
        if self.redis_client:
            self.redis_client.close()

    def __enter__(self):
        """支持上下文管理器协议"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器协议"""
        self.close()
