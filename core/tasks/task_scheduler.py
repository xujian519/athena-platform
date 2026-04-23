#!/usr/bin/env python3
from __future__ import annotations
"""
任务调度器 - 完整的任务管理系统
Task Scheduler - Complete Task Management System

实现定时提醒、持久化存储、系统通知等功能

作者: Athena AI系统
创建时间: 2025-12-17
版本: 1.0.0
"""

import json
import platform
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any


class TaskPriority(Enum):
    """任务优先级"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class ReminderType(Enum):
    """提醒类型"""

    NOTIFICATION = "notification"
    EMAIL = "email"
    SMS = "sms"
    SOUND = "sound"
    POPUP = "popup"


@dataclass
class Reminder:
    """提醒设置"""

    reminder_type: ReminderType
    remind_before: int  # 提前提醒时间(分钟)
    message: str
    enabled: bool = True
    repeat: bool = False  # 是否重复提醒
    repeat_interval: int = 60  # 重复间隔(分钟)


@dataclass
class Task:
    """任务对象"""

    id: str
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    due_at: datetime | None = None
    completed_at: datetime | None = None
    assigned_to: str = ""
    tags: list[str] = field(default_factory=list)
    reminders: list[Reminder] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if not self.updated_at:
            self.updated_at = self.created_at

    def add_reminder(
        self, reminder_type: ReminderType, remind_before: int, message: str, repeat: bool = False
    ):
        """添加提醒"""
        reminder = Reminder(
            reminder_type=reminder_type, remind_before=remind_before, message=message, repeat=repeat
        )
        self.reminders.append(reminder)
        self.updated_at = datetime.now()

    def mark_completed(self) -> Any:
        """标记为完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()

    def is_overdue(self) -> bool:
        """检查是否过期"""
        if self.due_at and self.status != TaskStatus.COMPLETED:
            return datetime.now() > self.due_at
        return False

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "assigned_to": self.assigned_to,
            "tags": self.tags,
            "reminders": [
                {
                    "reminder_type": r.reminder_type.value,
                    "remind_before": r.remind_before,
                    "message": r.message,
                    "enabled": r.enabled,
                    "repeat": r.repeat,
                    "repeat_interval": r.repeat_interval,
                }
                for r in self.reminders
            ],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> dict[str, Any]:
        """从字典创建任务"""
        reminders = []
        for r_data in data.get("reminders", []):
            reminder = Reminder(
                reminder_type=ReminderType(r_data["reminder_type"]),
                remind_before=r_data["remind_before"],
                message=r_data["message"],
                enabled=r_data.get("enabled", True),
                repeat=r_data.get("repeat", False),
                repeat_interval=r_data.get("repeat_interval", 60),
            )
            reminders.append(reminder)

        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            priority=TaskPriority(data["priority"]),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_at=datetime.fromisoformat(data["due_at"]) if data.get("due_at") else None,
            completed_at=(
                datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
            ),
            assigned_to=data.get("assigned_to", ""),
            tags=data.get("tags", []),
            reminders=reminders,
            metadata=data.get("metadata", {}),
        )


class NotificationManager:
    """通知管理器"""

    def __init__(self):
        self.system = platform.system()
        self.notification_methods = {
            "macos": self._send_macos_notification,
            "linux": self._send_linux_notification,
            "windows": self._send_windows_notification,
            "default": self._send_console_notification,
        }

    def send_notification(
        self, title: str, message: str, reminder_type: ReminderType = ReminderType.NOTIFICATION
    ) -> Any:
        """发送通知"""
        try:
            if self.system.lower() == "darwin":
                self._send_macos_notification(title, message)
            elif self.system.lower() == "linux":
                self._send_linux_notification(title, message)
            elif self.system.lower() == "windows":
                self._send_windows_notification(title, message)
            else:
                self._send_console_notification(title, message)

            # 记录通知日志
            self._log_notification(title, message, reminder_type)

        except Exception as e:
            print(f"发送通知失败: {e}")
            self._send_console_notification(title, message)

    def _send_macos_notification(self, title: str, message: str) -> Any:
        """发送macOS通知"""
        script = f"""
        display notification "{message}" with title "{title}" sound name "Glass"
        """
        subprocess.run(["osascript", "-e", script], check=True)

    def _send_linux_notification(self, title: str, message: str) -> Any:
        """发送Linux通知"""
        try:
            subprocess.run(["notify-send", title, message], check=True)
        except FileNotFoundError:
            self._send_console_notification(title, message)

    def _send_windows_notification(self, title: str, message: str) -> Any:
        """发送Windows通知"""
        try:
            from win10toast import ToastNotifier

            toaster = ToastNotifier()
            toaster.show_toast(title, message, duration=5)
        except ImportError:
            self._send_console_notification(title, message)

    def _send_console_notification(self, title: str, message: str) -> Any:
        """发送控制台通知"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n🔔 [{timestamp}] {title}")
        print(f"   {message}")
        print("-" * 60)

    def _log_notification(self, title: str, message: str, reminder_type: ReminderType) -> Any:
        """记录通知日志"""
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / "notifications.log"
        timestamp = datetime.now().isoformat()

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{reminder_type.value.upper()}] {title}: {message}\n")


class TaskStorage:
    """任务存储管理"""

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            storage_path = Path(__file__).parent.parent.parent / "data" / "tasks"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.tasks_file = self.storage_path / "tasks.json"
        self.todos_file = self.storage_path / "todos.json"

    def save_task(self, task: Task) -> None:
        """保存任务"""
        tasks = self.load_all_tasks()
        tasks[task.id] = task.to_dict()

        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2, default=str)

    def load_task(self, task_id: str) -> Task | None:
        """加载任务"""
        tasks = self.load_all_tasks()
        if task_id in tasks:
            return Task.from_dict(tasks[task_id])
        return None

    def load_all_tasks(self) -> dict[str, dict]:
        """加载所有任务"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载任务失败: {e}")
        return {}

    def delete_task(self, task_id: str) -> None:
        """删除任务"""
        tasks = self.load_all_tasks()
        if task_id in tasks:
            del tasks[task_id]
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2, default=str)

    def get_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        """按状态获取任务"""
        tasks_data = self.load_all_tasks()
        return [
            Task.from_dict(task_data)
            for task_data in tasks_data.values()
            if TaskStatus(task_data["status"]) == status
        ]

    def get_due_tasks(self, hours_ahead: int = 24) -> list[Task]:
        """获取即将到期的任务"""
        tasks_data = self.load_all_tasks()
        due_tasks = []
        cutoff_time = datetime.now() + timedelta(hours=hours_ahead)

        for task_data in tasks_data.values():
            task = Task.from_dict(task_data)
            if task.due_at and task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                if datetime.now() <= task.due_at <= cutoff_time:
                    due_tasks.append(task)

        return sorted(due_tasks, key=lambda x: x.due_at)

    def save_todos(self, todos: list[dict]) -> None:
        """保存TodoWrite数据"""
        with open(self.todos_file, "w", encoding="utf-8") as f:
            json.dump(todos, f, ensure_ascii=False, indent=2, default=str)

    def load_todos(self) -> list[dict]:
        """加载TodoWrite数据"""
        if self.todos_file.exists():
            try:
                with open(self.todos_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载Todos失败: {e}")
        return []


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.storage = TaskStorage()
        self.notification_manager = NotificationManager()
        self.running = False
        self.scheduler_thread = None

        # 从存储加载现有任务
        self._load_existing_tasks()

    def _load_existing_tasks(self) -> Any:
        """加载现有任务"""
        # 将现有的任务文件加载到调度器
        tasks_dir = Path(__file__).parent.parent.parent / "tasks"
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.json"):
                if "tasks_list" not in task_file.name:
                    try:
                        with open(task_file, encoding="utf-8") as f:
                            task_data = json.load(f)

                        # 转换为标准任务格式
                        if "任务标题" in task_data:
                            task = Task(
                                id=task_data.get("任务编号", f"task_{int(time.time())}"),
                                title=task_data.get("任务标题", ""),
                                description=task_data.get("任务详情", ""),
                                priority=TaskPriority.NORMAL,
                                status=TaskStatus.PENDING,
                                created_at=datetime.now(),
                                updated_at=datetime.now(),
                                assigned_to=task_data.get("创建人", ""),
                                metadata=task_data,
                            )

                            # 设置截止时间
                            if "截止时间" in task_data:
                                task.due_at = datetime.strptime(
                                    task_data["截止时间"], "%Y-%m-%d %H:%M"
                                )

                            # 添加提醒
                            if "任务提醒" in task_data:
                                reminder_data = task_data["任务提醒"]
                                if "提醒时间" in reminder_data:
                                    due_time = task.due_at or datetime.now()
                                    remind_before = (
                                        due_time
                                        - datetime.strptime(
                                            reminder_data["提醒时间"], "%Y-%m-%d %H:%M"
                                        )
                                    ).total_seconds() / 60
                                    task.add_reminder(
                                        ReminderType.NOTIFICATION,
                                        int(remind_before),
                                        reminder_data.get("提醒内容", f"任务提醒: {task.title}"),
                                    )

                            self.storage.save_task(task)

                    except Exception as e:
                        print(f"加载任务文件 {task_file} 失败: {e}")

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        due_at: datetime | None = None,
        assigned_to: str = "",
        tags: Optional[list[str]] = None,
    ) -> Task:
        """创建任务"""
        task_id = f"task_{int(time.time())}"
        task = Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            due_at=due_at,
            assigned_to=assigned_to,
            tags=tags or [],
        )

        self.storage.save_task(task)
        self.notification_manager.send_notification(
            "任务创建", f"新任务已创建: {title}", ReminderType.NOTIFICATION
        )

        return task

    def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """更新任务状态"""
        task = self.storage.load_task(task_id)
        if task:
            task.status = status
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now()
                self.notification_manager.send_notification(
                    "任务完成", f"任务已完成: {task.title}", ReminderType.NOTIFICATION
                )

            task.updated_at = datetime.now()
            self.storage.save_task(task)

    def add_reminder(
        self,
        task_id: str,
        reminder_type: ReminderType,
        remind_before: int,
        message: str,
        repeat: bool = False,
    ):
        """添加提醒"""
        task = self.storage.load_task(task_id)
        if task:
            task.add_reminder(reminder_type, remind_before, message, repeat)
            self.storage.save_task(task)

    def start_scheduler(self) -> Any:
        """启动调度器"""
        if self.running:
            return

        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        print("🔔 任务调度器已启动")

    def stop_scheduler(self) -> Any:
        """停止调度器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("🛑 任务调度器已停止")

    def _scheduler_loop(self) -> Any:
        """调度器主循环"""
        while self.running:
            try:
                # 检查即将到期的任务
                self._check_upcoming_tasks()

                # 检查过期任务
                self._check_overdue_tasks()

                # 每5分钟检查一次
                time.sleep(300)

            except Exception as e:
                print(f"调度器错误: {e}")
                time.sleep(60)

    def _check_upcoming_tasks(self) -> Any:
        """检查即将到期的任务"""
        upcoming_tasks = self.storage.get_due_tasks(hours_ahead=1)

        for task in upcoming_tasks:
            if task.due_at:
                time_until_due = (task.due_at - datetime.now()).total_seconds()

                for reminder in task.reminders:
                    if reminder.enabled:
                        remind_seconds = reminder.remind_before * 60

                        # 检查是否需要提醒
                        if 0 < time_until_due <= remind_seconds:
                            self.notification_manager.send_notification(
                                f"任务提醒: {task.title}", reminder.message, reminder.reminder_type
                            )

    def _check_overdue_tasks(self) -> Any:
        """检查过期任务"""
        overdue_tasks = []
        tasks_data = self.storage.load_all_tasks()

        for task_data in tasks_data.values():
            task = Task.from_dict(task_data)
            if task.is_overdue() and task.status == TaskStatus.PENDING:
                overdue_tasks.append(task)

        if overdue_tasks:
            for task in overdue_tasks:
                task.status = TaskStatus.OVERDUE
                self.storage.save_task(task)

                self.notification_manager.send_notification(
                    "任务过期", f"任务已过期: {task.title}", ReminderType.NOTIFICATION
                )

    def get_dashboard_summary(self) -> dict[str, Any]:
        """获取仪表板摘要"""
        tasks_data = self.storage.load_all_tasks()

        status_counts = {}
        priority_counts = {}

        for task_data in tasks_data.values():
            status = task_data["status"]
            priority = task_data["priority"]

            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        return {
            "total_tasks": len(tasks_data),
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "due_soon": len(self.storage.get_due_tasks(hours_ahead=24)),
            "overdue": len(
                [t for t in tasks_data.values() if TaskStatus(t["status"]) == TaskStatus.OVERDUE]
            ),
        }

    def get_tasks_for_todo(self) -> list[dict]:
        """获取TodoWrite格式的任务"""
        tasks = []
        tasks_data = self.storage.load_all_tasks()

        for task_data in tasks_data.values():
            if TaskStatus(task_data["status"]) in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                task_data.get("description", task_data["title"])

                todos = {
                    "todos": [
                        {
                            "content": task_data["title"],
                            "status": (
                                "in_progress"
                                if TaskStatus(task_data["status"]) == TaskStatus.IN_PROGRESS
                                else "pending"
                            ),
                            "active_form": f"{task_data['title']} - {task_data.get('assigned_to', '未分配')}",
                            "deadline": task_data.get("due_at"),
                            "priority": task_data.get("priority", 2),
                        }
                    ],
                    "updated_at": datetime.now().isoformat(),
                }

                tasks.append(todos)

        return tasks


# 全局任务调度器实例
_global_scheduler: TaskScheduler | None = None


def get_scheduler() -> TaskScheduler:
    """获取全局任务调度器实例"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = TaskScheduler()
        _global_scheduler.start_scheduler()
    return _global_scheduler


def create_task(
    title: str,
    description: str = "",
    priority: TaskPriority = TaskPriority.NORMAL,
    due_at: datetime | None = None,
    assigned_to: str = "",
    tags: Optional[list[str]] = None,
) -> Task:
    """创建任务(快捷函数)"""
    scheduler = get_scheduler()
    return scheduler.create_task(title, description, priority, due_at, assigned_to, tags)


def complete_task(task_id: str) -> Any:
    """完成任务(快捷函数)"""
    scheduler = get_scheduler()
    scheduler.update_task_status(task_id, TaskStatus.COMPLETED)


# 示例使用
if __name__ == "__main__":
    # 创建任务调度器
    scheduler = get_scheduler()

    # 创建测试任务
    print("📝 创建测试任务...")

    # 创建明天上午的专利命名任务
    tomorrow_morning = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    if tomorrow_morning <= datetime.now():
        tomorrow_morning += timedelta(days=1)

    patent_task = scheduler.create_task(
        title="为范文新客户确定3件实用新型专利名称",
        description="根据客户农业种植、种业推广的专业背景,确定具体、准确、有价值的专利名称。需要联系客户确认技术方案细节,进行专利检索分析,制定准确的专利名称方案。",
        priority=TaskPriority.HIGH,
        due_at=tomorrow_morning.replace(hour=12, minute=0),
        assigned_to="徐健",
        tags=["专利", "范文新", "实用新型", "命名"],
    )

    # 添加提醒
    scheduler.add_reminder(
        patent_task.id,
        ReminderType.NOTIFICATION,
        120,  # 提前2小时提醒
        "🔔 任务提醒: 请在上午9点联系范文新确定专利名称",
        repeat=False,
    )

    print(f"✅ 任务已创建: {patent_task.id}")
    print(f"   标题: {patent_task.title}")
    print(f"   截止时间: {patent_task.due_at}")
    print(f"   优先级: {patent_task.priority.name}")

    # 显示仪表板
    print("\n📊 任务仪表板:")
    summary = scheduler.get_dashboard_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")

    # 保持调度器运行
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n👋 停止任务调度器")
        scheduler.stop_scheduler()
