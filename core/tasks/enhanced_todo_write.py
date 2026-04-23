#!/usr/bin/env python3
from __future__ import annotations
"""
增强的TodoWrite工具 - 持久化版本
Enhanced TodoWrite Tool - Persistent Version

扩展原始TodoWrite功能,添加持久化存储、定时提醒和系统通知

作者: Athena AI系统
创建时间: 2025-12-17
版本: 1.0.0
"""

import contextlib
import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .task_scheduler import ReminderType, TaskPriority, get_scheduler


class EnhancedTodoWrite:
    """增强的TodoWrite工具"""

    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化增强TodoWrite

        Args:
            storage_path: 存储路径
        """
        if storage_path is None:
            storage_path = Path(__file__).parent.parent.parent / "data" / "todos"

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.todos_file = self.storage_path / "enhanced_todos.json"
        self.scheduler = get_scheduler()

        # 加载现有任务
        self.todos = self._load_todos()

        # 启动自动保存
        self.auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
        self.auto_save_thread.start()

        # 启动提醒检查
        self.reminder_thread = threading.Thread(target=self._reminder_check_loop, daemon=True)
        self.reminder_thread.start()

    def write(self, todos: list[dict]) -> None:
        """
        写入任务列表

        Args:
            todos: 任务列表
        """
        # 验证任务格式
        validated_todos = []
        for todo in todos:
            validated_todo = self._validate_todo(todo)
            if validated_todo:
                validated_todos.append(validated_todo)

        self.todos = validated_todos
        self._save_todos()
        self._sync_with_scheduler()

        # 立即保存到文件
        self._force_save()

    def _validate_todo(self, todo: dict) -> dict | None:
        """验证任务格式"""
        if not isinstance(todo, dict):
            return None

        required_fields = ["content", "status", "active_form"]
        for field in required_fields:
            if field not in todo:
                print(f"⚠️ 任务缺少必需字段: {field}")
                return None

        # 添加时间戳
        todo["updated_at"] = datetime.now().isoformat()

        return todo

    def get_todos(self) -> list[dict]:
        """获取所有任务"""
        return self.todos.copy()

    def add_todo(
        self,
        content: str,
        status: str = "pending",
        active_form: str = "",
        priority: str = "normal",
        deadline: Optional[str] = None,
        tags: Optional[list[str]] = None,
        reminder_minutes: Optional[int] = None,
    ) -> str:
        """
        添加单个任务

        Args:
            content: 任务内容
            status: 任务状态
            active_form: 活跃形式描述
            priority: 优先级
            deadline: 截止时间
            tags: 标签
            reminder_minutes: 提醒时间(分钟)

        Returns:
            任务ID
        """
        import uuid

        todo_id = str(uuid.uuid4())

        todo = {
            "id": todo_id,
            "content": content,
            "status": status,
            "active_form": active_form or content,
            "priority": priority,
            "deadline": deadline,
            "tags": tags or [],
            "reminder_minutes": reminder_minutes,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "completed_at": None,
        }

        self.todos.append(todo)
        self._save_todos()
        self._sync_with_scheduler()

        print(f"✅ 任务已添加: {content}")

        return todo_id

    def update_todo_status(self, todo_id: str, status: str) -> bool:
        """
        更新任务状态

        Args:
            todo_id: 任务ID
            status: 新状态

        Returns:
            是否更新成功
        """
        for todo in self.todos:
            if todo.get("id") == todo_id:
                todo["status"] = status
                todo["updated_at"] = datetime.now().isoformat()

                if status == "completed":
                    todo["completed_at"] = datetime.now().isoformat()
                    self._send_completion_notification(todo)

                self._save_todos()
                self._sync_with_scheduler()

                print(f"✅ 任务状态已更新: {todo.get('content', '')} -> {status}")
                return True

        return False

    def delete_todo(self, todo_id: str) -> bool:
        """
        删除任务

        Args:
            todo_id: 任务ID

        Returns:
            是否删除成功
        """
        for i, todo in enumerate(self.todos):
            if todo.get("id") == todo_id:
                deleted_todo = self.todos.pop(i)
                self._save_todos()
                self._sync_with_scheduler()

                print(f"🗑️ 任务已删除: {deleted_todo.get('content', '')}")
                return True

        return False

    def get_todos_by_status(self, status: str) -> list[dict]:
        """按状态获取任务"""
        return [todo for todo in self.todos if todo.get("status") == status]

    def get_todos_by_priority(self, priority: str) -> list[dict]:
        """按优先级获取任务"""
        return [todo for todo in self.todos if todo.get("priority") == priority]

    def get_due_todos(self, hours_ahead: int = 24) -> list[dict]:
        """获取即将到期的任务"""
        due_todos = []
        cutoff_time = datetime.now() + timedelta(hours=hours_ahead)

        for todo in self.todos:
            if todo.get("deadline") and todo.get("status") != "completed":
                try:
                    deadline = datetime.fromisoformat(todo["deadline"])
                    if datetime.now() <= deadline <= cutoff_time:
                        due_todos.append(todo)
                except ValueError:
                    continue

        return sorted(due_todos, key=lambda x: x.get("deadline", ""))

    def get_dashboard_summary(self) -> dict[str, Any]:
        """获取仪表板摘要"""
        total = len(self.todos)
        completed = len(self.get_todos_by_status("completed"))
        pending = len(self.get_todos_by_status("pending"))
        in_progress = len(self.get_todos_by_status("in_progress"))

        # 优先级统计
        priority_counts = {}
        for todo in self.todos:
            priority = todo.get("priority", "normal")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        # 即将到期
        due_soon = len(self.get_due_todos(hours_ahead=24))

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "in_progress": in_progress,
            "completion_rate": f"{(completed/total*100):.1f}%" if total > 0 else "0%",
            "priority_counts": priority_counts,
            "due_soon": due_soon,
            "last_updated": (
                max(todo.get("updated_at", "") for todo in self.todos) if self.todos else None
            ),
        }

    def export_todos(self, format_type: str = "json", file_path: Optional[str] = None) -> str:
        """
        导出任务

        Args:
            format_type: 导出格式 (json, markdown, csv)
            file_path: 导出文件路径

        Returns:
            导出文件路径
        """
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"todos_export_{timestamp}.{format_type}"

        if format_type == "json":
            export_data = {
                "export_time": datetime.now().isoformat(),
                "summary": self.get_dashboard_summary(),
                "todos": self.todos,
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

        elif format_type == "markdown":
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# 任务列表 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                summary = self.get_dashboard_summary()
                f.write("## 摘要\n")
                f.write(f"- 总任务数: {summary['total']}\n")
                f.write(f"- 已完成: {summary['completed']}\n")
                f.write(f"- 待处理: {summary['pending']}\n")
                f.write(f"- 进行中: {summary['in_progress']}\n")
                f.write(f"- 完成率: {summary['completion_rate']}\n\n")

                # 按状态分组
                for status in ["pending", "in_progress", "completed"]:
                    status_todos = self.get_todos_by_status(status)
                    if status_todos:
                        f.write(f"## {status.title()}\n\n")
                        for todo in status_todos:
                            f.write(f"- {todo.get('content', '')}")
                            if todo.get("deadline"):
                                f.write(f" (截止: {todo['deadline']})")
                            f.write("\n")
                        f.write("\n")

        elif format_type == "csv":
            import csv

            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["ID", "内容", "状态", "优先级", "截止时间", "创建时间", "更新时间"]
                )

                for todo in self.todos:
                    writer.writerow(
                        [
                            todo.get("id", ""),
                            todo.get("content", ""),
                            todo.get("status", ""),
                            todo.get("priority", ""),
                            todo.get("deadline", ""),
                            todo.get("created_at", ""),
                            todo.get("updated_at", ""),
                        ]
                    )

        print(f"📁 任务已导出到: {file_path}")
        return file_path

    def _load_todos(self) -> list[dict]:
        """从文件加载任务"""
        if self.todos_file.exists():
            try:
                with open(self.todos_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 加载任务文件失败: {e}")

        # 尝试从原始TodoWrite文件迁移
        self._migrate_from_original()

        return []

    def _migrate_from_original(self) -> Any:
        """从原始TodoWrite文件迁移"""
        try:
            # 查找原始TodoWrite存储
            possible_paths = [
                Path("/Users/xujian/Athena工作平台/data/todos.json"),
                Path(__file__).parent.parent.parent / "data" / "todos.json",
            ]

            for path in possible_paths:
                if path.exists():
                    print(f"🔄 从原始文件迁移任务: {path}")

                    with open(path, encoding="utf-8") as f:
                        original_todos = json.load(f)

                    # 转换为增强格式
                    for todo in original_todos:
                        if "todos" in todo:
                            for todo_item in todo["todos"]:
                                self.add_todo(
                                    content=todo_item.get("content", ""),
                                    status=todo_item.get("status", "pending"),
                                    active_form=todo_item.get("active_form", ""),
                                    priority=todo_item.get("priority", "normal"),
                                )

                    break

        except Exception as e:
            print(f"⚠️ 迁移任务失败: {e}")

    def _save_todos(self) -> Any:
        """保存任务到文件"""
        try:
            with open(self.todos_file, "w", encoding="utf-8") as f:
                json.dump(self.todos, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ 保存任务文件失败: {e}")

    def _force_save(self) -> Any:
        """强制保存任务"""
        self._save_todos()

    def _auto_save_loop(self) -> Any:
        """自动保存循环"""
        while True:
            time.sleep(60)  # 每分钟自动保存一次
            self._save_todos()

    def _reminder_check_loop(self) -> Any:
        """提醒检查循环"""
        while True:
            try:
                self._check_reminders()
                time.sleep(300)  # 每5分钟检查一次提醒
            except Exception as e:
                print(f"⚠️ 提醒检查失败: {e}")
                time.sleep(60)

    def _check_reminders(self) -> Any:
        """检查提醒"""
        for todo in self.todos:
            if todo.get("status") == "completed":
                continue

            if todo.get("reminder_minutes") and todo.get("deadline"):
                try:
                    deadline = datetime.fromisoformat(todo["deadline"])
                    reminder_time = deadline - timedelta(minutes=todo["reminder_minutes"])

                    # 检查是否到了提醒时间
                    if datetime.now() >= reminder_time and datetime.now() < deadline:
                        # 检查是否已经提醒过(避免重复提醒)
                        last_reminder = todo.get("last_reminder")
                        if (
                            not last_reminder
                            or datetime.fromisoformat(last_reminder) < reminder_time
                        ):
                            self._send_reminder_notification(todo)

                            # 更新最后提醒时间
                            todo["last_reminder"] = datetime.now().isoformat()
                            self._save_todos()

                except ValueError:
                    continue

    def _sync_with_scheduler(self) -> Any:
        """与任务调度器同步"""
        try:
            # 将TodoWrite任务同步到调度器
            for todo in self.todos:
                if todo.get("status") not in ["completed", "cancelled"]:
                    # 检查调度器中是否已有此任务
                    existing_tasks = self.scheduler.storage.load_all_tasks()

                    found = False
                    for task_data in existing_tasks.values():
                        if todo.get("content") in task_data.get("title", ""):
                            found = True
                            break

                    if not found:
                        # 创建新任务到调度器
                        due_at = None
                        if todo.get("deadline"):
                            with contextlib.suppress(ValueError):
                                due_at = datetime.fromisoformat(todo["deadline"])

                        priority_map = {
                            "low": TaskPriority.LOW,
                            "normal": TaskPriority.NORMAL,
                            "high": TaskPriority.HIGH,
                            "urgent": TaskPriority.URGENT,
                            "critical": TaskPriority.CRITICAL,
                        }

                        task = self.scheduler.create_task(
                            title=todo.get("content", ""),
                            description=todo.get("active_form", ""),
                            priority=priority_map.get(
                                todo.get("priority", "normal"), TaskPriority.NORMAL
                            ),
                            due_at=due_at,
                            tags=todo.get("tags", []),
                        )

                        # 添加提醒
                        if todo.get("reminder_minutes"):
                            self.scheduler.add_reminder(
                                task.id,
                                ReminderType.NOTIFICATION,
                                todo["reminder_minutes"],
                                f"任务提醒: {todo.get('content', '')}",
                                repeat=False,
                            )

                        # 保存任务ID到TodoWrite
                        todo["scheduler_task_id"] = task.id
                        self._save_todos()

        except Exception as e:
            print(f"⚠️ 同步调度器失败: {e}")

    def _send_reminder_notification(self, todo: dict) -> Any:
        """发送提醒通知"""
        try:
            from .task_scheduler import NotificationManager

            notification_manager = NotificationManager()
            notification_manager.send_notification(
                "任务提醒",
                f"🔔 {todo.get('content', '')}\n截止时间: {todo.get('deadline', '未设置')}",
                ReminderType.NOTIFICATION,
            )
        except Exception as e:
            print(f"⚠️ 发送提醒通知失败: {e}")

    def _send_completion_notification(self, todo: dict) -> Any:
        """发送完成通知"""
        try:
            from .task_scheduler import NotificationManager

            notification_manager = NotificationManager()
            notification_manager.send_notification(
                "任务完成", f"✅ {todo.get('content', '')}", ReminderType.NOTIFICATION
            )
        except Exception as e:
            print(f"⚠️ 发送完成通知失败: {e}")


# 全局增强TodoWrite实例
_global_enhanced_todo: EnhancedTodoWrite | None = None


def get_enhanced_todo() -> EnhancedTodoWrite:
    """获取全局增强TodoWrite实例"""
    global _global_enhanced_todo
    if _global_enhanced_todo is None:
        _global_enhanced_todo = EnhancedTodoWrite()
    return _global_enhanced_todo


# 兼容性函数 - 替换原始TodoWrite
def TodoWrite(todos: list[dict]) -> None:
    """增强的TodoWrite函数(兼容原始接口)"""
    enhanced_todo = get_enhanced_todo()
    enhanced_todo.write(todos)


# 快捷函数
def add_todo(
    content: str,
    status: str = "pending",
    active_form: str = "",
    priority: str = "normal",
    deadline: Optional[str] = None,
    tags: Optional[list[str]] = None,
    reminder_minutes: Optional[int] = None,
) -> str:
    """快捷添加任务"""
    enhanced_todo = get_enhanced_todo()
    return enhanced_todo.add_todo(
        content, status, active_form, priority, deadline, tags, reminder_minutes
    )


def complete_todo(content: str) -> bool:
    """快捷完成任务"""
    enhanced_todo = get_enhanced_todo()

    for todo in enhanced_todo.todos:
        if todo.get("content") == content:
            return enhanced_todo.update_todo_status(todo.get("id"), "completed")

    return False


def get_todo_dashboard() -> dict[str, Any]:
    """获取任务仪表板"""
    enhanced_todo = get_enhanced_todo()
    return enhanced_todo.get_dashboard_summary()


if __name__ == "__main__":
    # 使用示例
    print("🔧 增强TodoWrite工具测试")

    # 获取实例
    todo_manager = get_enhanced_todo()

    # 添加测试任务
    print("\n📝 添加测试任务...")

    task1_id = todo_manager.add_todo(
        content="明天上午给范文新的实用新型专利确定名称(3件)",
        status="pending",
        active_form="待明天上午执行",
        priority="high",
        deadline="2025-12-18T12:00:00",
        tags=["专利", "范文新", "工作"],
        reminder_minutes=120,
    )

    task2_id = todo_manager.add_todo(
        content="完成性能优化系统测试",
        status="completed",
        active_form="已完成测试和验证",
        priority="normal",
        tags=["系统", "优化"],
    )

    task3_id = todo_manager.add_todo(
        content="准备专利申请材料",
        status="pending",
        active_form="准备孙俊霞项目材料",
        priority="medium",
        deadline="2025-12-20T18:00:00",
        tags=["专利", "孙俊霞"],
        reminder_minutes=60,
    )

    # 显示仪表板
    print("\n📊 任务仪表板:")
    dashboard = todo_manager.get_dashboard_summary()
    for key, value in dashboard.items():
        print(f"  {key}: {value}")

    # 显示待办任务
    print("\n📋 待办任务:")
    pending_todos = todo_manager.get_todos_by_status("pending")
    for todo in pending_todos:
        deadline_str = f" (截止: {todo['deadline']})" if todo.get("deadline") else ""
        print(f"  • {todo['content']}{deadline_str}")

    # 显示即将到期
    print("\n⏰ 即将到期:")
    due_todos = todo_manager.get_due_todos(hours_ahead=24)
    for todo in due_todos:
        print(f"  • {todo['content']} - {todo['deadline']}")

    print(f"\n💾 任务已保存到: {todo_manager.todos_file}")
    print("🔔 提醒系统已启动")

    # 保持运行以测试提醒
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n👋 退出测试")
