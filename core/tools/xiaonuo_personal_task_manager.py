#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺个人任务管理器
Xiaonuo Personal Task Manager

专为爸爸设计的任务管理系统,包含:
1. 快速任务捕获
2. 智能任务分类
3. 可视化展示
4. 拖延症对抗机制
"""

import json
from core.async_main import async_main
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import asyncio

class TaskPriority(Enum):
    """任务优先级"""
    URGENT_IMPORTANT = "urgent_important"  # 紧急且重要
    IMPORTANT = "important"  # 重要但不紧急
    URGENT = "urgent"  # 紧急但不重要
    NORMAL = "normal"  # 普通
    LOW = "low"  # 低优先级

class TaskCategory(Enum):
    """任务分类"""
    WORK = "work"  # 工作
    LIFE = "life"  # 生活
    LEARNING = "learning"  # 学习
    HEALTH = "health"  # 健康
    FAMILY = "family"  # 家庭
    PROJECT = "project"  # 项目

class TaskStatus(Enum):
    """任务状态"""
    TODO = "todo"  # 待办
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    BLOCKED = "blocked"  # 被阻塞

class Task:
    """任务对象"""

    def __init__(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        category: TaskCategory = TaskCategory.WORK,
        estimated_time: int = 30,  # 预估时间(分钟)
        due_date: datetime | None = None,
        tags: list[str] | None = None,
        parent_task: str | None = None,
        subtasks: list[str] | None = None,
        created_at: datetime | None = None,
        task_id: str | None = None
    ):
        self.task_id = task_id or self._generate_task_id()
        self.title = title
        self.description = description
        self.priority = priority
        self.category = category
        self.estimated_time = estimated_time
        self.due_date = due_date
        self.tags = tags or []
        self.parent_task = parent_task
        self.subtasks = subtasks or []
        self.status = TaskStatus.TODO
        self.created_at = created_at or datetime.now()
        self.updated_at = datetime.now()
        self.completed_at = None
        self.pomodoros_completed = 0  # 完成的番茄钟数量
        self.procrastination_score = 0  # 拖延评分(越高越拖延)

    def _generate_task_id(self) -> str:
        """生成任务ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"task_{timestamp}"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "category": self.category.value,
            "estimated_time": self.estimated_time,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "tags": self.tags,
            "parent_task": self.parent_task,
            "subtasks": self.subtasks,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "pomodoros_completed": self.pomodoros_completed,
            "procrastination_score": self.procrastination_score
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """从字典创建任务"""
        task = cls(
            title=data["title"],
            description=data.get("description", ""),
            priority=TaskPriority(data.get("priority", TaskPriority.NORMAL.value)),
            category=TaskCategory(data.get("category", TaskCategory.WORK.value)),
            estimated_time=data.get("estimated_time", 30),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            tags=data.get("tags", []),
            parent_task=data.get("parent_task"),
            subtasks=data.get("subtasks", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            task_id=data.get("task_id")
        )
        task.status = TaskStatus(data.get("status", TaskStatus.TODO.value))
        task.updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()
        if data.get("completed_at"):
            task.completed_at = datetime.fromisoformat(data["completed_at"])
        task.pomodoros_completed = data.get("pomodoros_completed", 0)
        task.procrastination_score = data.get("procrastination_score", 0)
        return task

class XiaonuoPersonalTaskManager:
    """小诺个人任务管理器"""

    def __init__(self, storage_path: str = None):
        """初始化任务管理器

        Args:
            storage_path: 任务存储路径
        """
        self.storage_path = storage_path or os.path.expanduser("~/Athena工作平台/data/tasks")
        os.makedirs(self.storage_path, exist_ok=True)

        self.tasks: dict[str, Task] = {}
        self.daily_notes: dict[str, list[str]] = {}  # 每日笔记
        self.habits: list[Dict] = []  # 习惯追踪

        # 加载已有任务
        asyncio.run(self._load_tasks())

    async def _load_tasks(self):
        """加载任务数据"""
        try:
            task_file = os.path.join(self.storage_path, "tasks.json")
            if os.path.exists(task_file):
                with open(task_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_data in data.get("tasks", []):
                        task = Task.from_dict(task_data)
                        self.tasks[task.task_id] = task

                # 加载每日笔记
                notes_file = os.path.join(self.storage_path, "daily_notes.json")
                if os.path.exists(notes_file):
                    with open(notes_file, 'r', encoding='utf-8') as f:
                        self.daily_notes = json.load(f)

                # 加载习惯数据
                habits_file = os.path.join(self.storage_path, "habits.json")
                if os.path.exists(habits_file):
                    with open(habits_file, 'r', encoding='utf-8') as f:
                        self.habits = json.load(f)

                print(f"✅ 成功加载 {len(self.tasks)} 个任务")
        except Exception as e:
            print(f"⚠️ 加载任务数据失败: {e}")

    async def _save_tasks(self):
        """保存任务数据"""
        try:
            task_file = os.path.join(self.storage_path, "tasks.json")
            data = {
                "tasks": [task.to_dict() for task in self.tasks.values()],
                "last_updated": datetime.now().isoformat()
            }
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 保存每日笔记
            notes_file = os.path.join(self.storage_path, "daily_notes.json")
            with open(notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.daily_notes, f, ensure_ascii=False, indent=2)

            # 保存习惯数据
            habits_file = os.path.join(self.storage_path, "habits.json")
            with open(habits_file, 'w', encoding='utf-8') as f:
                json.dump(self.habits, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"❌ 保存任务数据失败: {e}")

    def quick_add_task(
        self,
        title: str,
        priority: str = "normal",
        category: str = "work",
        estimated_time: int = 30
    ) -> Task:
        """快速添加任务

        Args:
            title: 任务标题
            priority: 优先级 (urgent_important/important/urgent/normal/low)
            category: 分类 (work/life/learning/health/family/project)
            estimated_time: 预估时间(分钟)

        Returns:
            创建的任务对象
        """
        try:
            priority_map = {
                "紧急重要": TaskPriority.URGENT_IMPORTANT,
                "重要": TaskPriority.IMPORTANT,
                "紧急": TaskPriority.URGENT,
                "普通": TaskPriority.NORMAL,
                "低": TaskPriority.LOW
            }

            category_map = {
                "工作": TaskCategory.WORK,
                "生活": TaskCategory.LIFE,
                "学习": TaskCategory.LEARNING,
                "健康": TaskCategory.HEALTH,
                "家庭": TaskCategory.FAMILY,
                "项目": TaskCategory.PROJECT
            }

            task = Task(
                title=title,
                priority=priority_map.get(priority, TaskPriority.NORMAL),
                category=category_map.get(category, TaskCategory.WORK),
                estimated_time=estimated_time
            )

            self.tasks[task.task_id] = task
            asyncio.run(self._save_tasks())

            print(f"✅ 任务已添加: {title}")
            return task

        except Exception as e:
            print(f"❌ 添加任务失败: {e}")
            return None

    def complete_task(self, task_id: str) -> bool:
        """完成任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功完成
        """
        try:
            if task_id not in self.tasks:
                print(f"❌ 任务不存在: {task_id}")
                return False

            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.updated_at = datetime.now()

            asyncio.run(self._save_tasks())

            print(f"✅ 任务已完成: {task.title}")
            return True

        except Exception as e:
            print(f"❌ 完成任务失败: {e}")
            return False

    def get_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        """按状态获取任务

        Args:
            status: 任务状态

        Returns:
            任务列表
        """
        return [task for task in self.tasks.values() if task.status == status]

    def get_tasks_by_category(self, category: TaskCategory) -> list[Task]:
        """按分类获取任务

        Args:
            category: 任务分类

        Returns:
            任务列表
        """
        return [task for task in self.tasks.values() if task.category == category]

    def get_tasks_by_priority(self, priority: TaskPriority) -> list[Task]:
        """按优先级获取任务

        Args:
            priority: 任务优先级

        Returns:
            任务列表
        """
        return [task for task in self.tasks.values() if task.priority == priority]

    def get_overdue_tasks(self) -> list[Task]:
        """获取逾期任务"""
        now = datetime.now()
        return [
            task for task in self.tasks.values()
            if task.due_date and task.due_date < now and task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
        ]

    def get_today_tasks(self) -> list[Task]:
        """获取今天的任务"""
        today = datetime.now().date()
        return [
            task for task in self.tasks.values()
            if task.due_date and task.due_date.date() == today and task.status != TaskStatus.COMPLETED
        ]

    def get_week_tasks(self) -> list[Task]:
        """获取本周的任务"""
        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=6)

        return [
            task for task in self.tasks.values()
            if task.due_date and week_start <= task.due_date <= week_end and task.status != TaskStatus.COMPLETED
        ]

    def visualize_tasks(self):
        """可视化任务展示"""
        print("\n" + "="*80)
        print("📋 小诺个人任务看板".center(80))
        print("="*80)
        print(f"⏰ 查看时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 1. 紧急重要任务(第一象限)
        print("🔴 第一象限:紧急且重要")
        print("-" * 80)
        urgent_important = self.get_tasks_by_priority(TaskPriority.URGENT_IMPORTANT)
        urgent_important = [t for t in urgent_important if t.status == TaskStatus.TODO]
        if urgent_important:
            for task in urgent_important[:5]:
                print(f"  ⚡ {task.title}")
                if task.due_date:
                    print(f"     📅 截止: {task.due_date.strftime('%Y-%m-%d %H:%M')}")
                print(f"     ⏱️ 预估: {task.estimated_time}分钟")
        else:
            print("  ✨ 暂无紧急重要任务")
        print()

        # 2. 重要但不紧急(第二象限)
        print("🟡 第二象限:重要但不紧急")
        print("-" * 80)
        important = self.get_tasks_by_priority(TaskPriority.IMPORTANT)
        important = [t for t in important if t.status == TaskStatus.TODO]
        if important:
            for task in important[:5]:
                print(f"  📌 {task.title}")
                if task.due_date:
                    print(f"     📅 截止: {task.due_date.strftime('%Y-%m-%d')}")
                print(f"     ⏱️ 预估: {task.estimated_time}分钟")
        else:
            print("  ✨ 暂无重要任务")
        print()

        # 3. 今天的任务
        print("📅 今天的任务")
        print("-" * 80)
        today_tasks = self.get_today_tasks()
        if today_tasks:
            for task in today_tasks:
                status_icon = {
                    TaskStatus.TODO: "⬜",
                    TaskStatus.IN_PROGRESS: "🟦",
                    TaskStatus.COMPLETED: "✅",
                    TaskStatus.BLOCKED: "🚫"
                }.get(task.status, "⬜")

                print(f"  {status_icon} {task.title}")
                print(f"     分类: {task.category.value} | 预估: {task.estimated_time}分钟")
        else:
            print("  ✨ 今天暂无任务")
        print()

        # 4. 本周任务概览
        print("📊 本周任务概览")
        print("-" * 80)
        week_tasks = self.get_week_tasks()
        if week_tasks:
            # 按日期分组
            tasks_by_date = {}
            for task in week_tasks:
                date_str = task.due_date.strftime("%Y-%m-%d")
                if date_str not in tasks_by_date:
                    tasks_by_date[date_str] = []
                tasks_by_date[date_str].append(task)

            for date_str, tasks in sorted(tasks_by_date.items()):
                print(f"  📆 {date_str}: {len(tasks)}个任务")
                for task in tasks[:3]:
                    print(f"     • {task.title}")
                if len(tasks) > 3:
                    print(f"     ...还有 {len(tasks)-3} 个任务")
        else:
            print("  ✨ 本周暂无任务")
        print()

        # 5. 任务统计
        print("📈 任务统计")
        print("-" * 80)
        total = len(self.tasks)
        completed = len(self.get_tasks_by_status(TaskStatus.COMPLETED))
        in_progress = len(self.get_tasks_by_status(TaskStatus.IN_PROGRESS))
        todo = len(self.get_tasks_by_status(TaskStatus.TODO))
        overdue = len(self.get_overdue_tasks())

        completion_rate = (completed / total * 100) if total > 0 else 0

        print(f"  总任务数: {total}")
        print(f"  ✅ 已完成: {completed} ({completion_rate:.1f}%)")
        print(f"  🟦 进行中: {in_progress}")
        print(f"  ⬜ 待办: {todo}")
        print(f"  ⚠️ 逾期: {overdue}")
        print()

        # 6. 拖延症诊断
        if todo > 10:
            print("⚠️ 拖延症诊断")
            print("-" * 80)
            print("  📊 爸爸,您有较多待办任务,建议:")
            print("     1. 使用番茄工作法(25分钟专注+5分钟休息)")
            print("     2. 将大任务拆解为小步骤")
            print("     3. 优先完成\"紧急重要\"任务")
            print("     4. 每天只选择3个最重要的任务完成")
            print()

        print("="*80)
        print()

    def add_daily_note(self, note: str):
        """添加每日笔记"""
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.daily_notes:
            self.daily_notes[today] = []
        self.daily_notes[today].append({
            "content": note,
            "time": datetime.now().strftime("%H:%M:%S")
        })
        asyncio.run(self._save_tasks())
        print(f"✅ 笔记已添加: {note}")

    def view_daily_notes(self, date: str = None):
        """查看每日笔记"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        notes = self.daily_notes.get(date, [])
        if notes:
            print(f"\n📝 {date} 的笔记:")
            print("-" * 60)
            for note in notes:
                print(f"  [{note['time']}] {note['content']}")
        else:
            print(f"📝 {date} 暂无笔记")

# CLI接口
def main():
    """命令行接口"""
    import sys

    manager = XiaonuoPersonalTaskManager()

    if len(sys.argv) < 2:
        manager.visualize_tasks()
        return

    command = sys.argv[1]

    if command == "add":
        if len(sys.argv) < 3:
            print("用法: python xiaonuo_personal_task_manager.py add <任务标题>")
            return
        title = " ".join(sys.argv[2:])
        manager.quick_add_task(title)

    elif command == "complete":
        if len(sys.argv) < 3:
            print("用法: python xiaonuo_personal_task_manager.py complete <任务ID>")
            return
        task_id = sys.argv[2]
        manager.complete_task(task_id)

    elif command == "list":
        manager.visualize_tasks()

    elif command == "today":
        today_tasks = manager.get_today_tasks()
        if today_tasks:
            print(f"\n📅 今天的任务 ({len(today_tasks)}个):")
            for task in today_tasks:
                print(f"  • {task.title}")
        else:
            print("✨ 今天暂无任务")

    elif command == "note":
        if len(sys.argv) < 3:
            print("用法: python xiaonuo_personal_task_manager.py note <笔记内容>")
            return
        note = " ".join(sys.argv[2:])
        manager.add_daily_note(note)

    elif command == "notes":
        date = sys.argv[2] if len(sys.argv) > 2 else None
        manager.view_daily_notes(date)

    else:
        print(f"❌ 未知命令: {command}")
        print("可用命令: add, complete, list, today, note, notes")

if __name__ == "__main__":
    main()
