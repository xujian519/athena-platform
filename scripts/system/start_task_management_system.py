#!/usr/bin/env python3
"""
启动任务管理系统
Start Task Management System

集成定时提醒、持久化存储、系统通知的完整任务管理系统

作者: Athena AI系统
创建时间: 2025-12-17
版本: 1.0.0
"""

import argparse
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.tasks.enhanced_todo_write import (
        add_todo,
        complete_todo,
        get_enhanced_todo,
        get_todo_dashboard,
    )
    from core.tasks.task_scheduler import ReminderType, TaskPriority, TaskStatus, get_scheduler
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    sys.exit(1)


def print_banner() -> Any:
    """打印系统横幅"""
    print("=" * 80)
    print("🚀 Athena工作平台 - 任务管理系统")
    print("=" * 80)
    print("✅ 定时提醒 - 自动任务提醒和通知")
    print("✅ 持久化存储 - 跨会话任务保存")
    print("✅ 系统通知 - mac_os/Linux/Windows通知")
    print("✅ 任务调度 - 智能任务管理")
    print("✅ 增强TodoWrite - 持久化任务跟踪")
    print("=" * 80)
    print()


def initialize_system() -> Any:
    """初始化任务管理系统"""
    print("🔧 初始化任务管理系统...")

    # 初始化任务调度器
    scheduler = get_scheduler()
    print("✅ 任务调度器已启动")

    # 初始化增强TodoWrite
    todo_manager = get_enhanced_todo()
    print("✅ 增强TodoWrite已初始化")

    # 迁移现有任务
    print("🔄 迁移现有任务...")

    # 显示系统状态
    dashboard = get_todo_dashboard()
    print("📊 当前任务统计:")
    print(f"   总任务数: {dashboard.get('total', 0)}")
    print(f"   已完成: {dashboard.get('completed', 0)}")
    print(f"   待处理: {dashboard.get('pending', 0)}")
    print(f"   进行中: {dashboard.get('in_progress', 0)}")
    print(f"   完成率: {dashboard.get('completion_rate', '0%')}")

    return scheduler, todo_manager


def show_menu() -> Any:
    """显示主菜单"""
    print("\n📋 任务管理菜单:")
    print("1. 添加新任务")
    print("2. 查看所有任务")
    print("3. 查看待办任务")
    print("4. 查看已完成任务")
    print("5. 完成任务")
    print("6. 删除任务")
    print("7. 查看即将到期")
    print("8. 导出任务")
    print("9. 系统统计")
    print("10. 测试提醒功能")
    print("0. 退出")


def add_task_interactive(todo_manager) -> None:
    """交互式添加任务"""
    print("\n📝 添加新任务")

    try:
        content = input("任务内容: ").strip()
        if not content:
            print("❌ 任务内容不能为空")
            return

        status = input("状态 (pending/in_progress, 默认pending): ").strip() or "pending"
        priority = input("优先级 (low/normal/high/urgent, 默认normal): ").strip() or "normal"
        deadline = input("截止时间 (YYYY-MM-DD HH:MM, 可选): ").strip() or None
        tags_input = input("标签 (用逗号分隔, 可选): ").strip()
        tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
        reminder_minutes = input("提前提醒时间（分钟, 可选）: ").strip()

        reminder_minutes = int(reminder_minutes) if reminder_minutes else None

        task_id = todo_manager.add_todo(
            content=content,
            status=status,
            priority=priority,
            deadline=deadline,
            tags=tags,
            reminder_minutes=reminder_minutes
        )

        print(f"✅ 任务已添加，ID: {task_id}")

        # 如果有截止时间，询问是否添加到调度器
        if deadline:
            add_to_scheduler = input("是否添加到任务调度器? (y/N): ").strip().lower()
            if add_to_scheduler == 'y':
                try:
                    deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M")

                    # 创建调度器任务
                    scheduler = get_scheduler()
                    priority_map = {
                        "low": TaskPriority.LOW,
                        "normal": TaskPriority.NORMAL,
                        "high": TaskPriority.HIGH,
                        "urgent": TaskPriority.URGENT
                    }

                    scheduler_task = scheduler.create_task(
                        title=content,
                        description="任务从TodoWrite创建",
                        priority=priority_map.get(priority, TaskPriority.NORMAL),
                        due_at=deadline_dt,
                        tags=tags
                    )

                    # 添加提醒
                    if reminder_minutes:
                        scheduler.add_reminder(
                            scheduler_task.id,
                            ReminderType.NOTIFICATION,
                            reminder_minutes,
                            f"任务提醒: {content}"
                        )

                    print(f"✅ 任务已添加到调度器: {scheduler_task.id}")

                except ValueError:
                    print("❌ 截止时间格式错误")

    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"❌ 添加任务失败: {e}")


def show_all_tasks(todo_manager) -> Any:
    """显示所有任务"""
    print("\n📋 所有任务:")
    todos = todo_manager.get_todos()

    if not todos:
        print("   暂无任务")
        return

    for i, todo in enumerate(todos, 1):
        status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}.get(todo.get("status"), "❓")
        priority_color = {"low": "🟢", "normal": "🟡", "high": "🟠", "urgent": "🔴"}.get(todo.get("priority"), "⚪")

        print(f"{i:2d}. {status_icon} {priority_color} {todo.get('content', '')}")

        if todo.get("deadline"):
            print(f"     📅 截止: {todo['deadline']}")

        if todo.get("tags"):
            tags_str = ", ".join(todo["tags"])
            print(f"     🏷️  标签: {tags_str}")


def complete_task_interactive(todo_manager) -> Any:
    """交互式完成任务"""
    print("\n✅ 完成任务")

    todos = todo_manager.get_todos_by_status("pending")
    if not todos:
        todos = todo_manager.get_todos_by_status("in_progress")

    if not todos:
        print("   暂无可完成的任务")
        return

    print("可选择完成的任务:")
    for i, todo in enumerate(todos, 1):
        print(f"{i}. {todo.get('content', '')}")

    try:
        choice = input("选择要完成的任务编号: ").strip()
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(todos):
                todo = todos[index]
                if todo_manager.update_todo_status(todo.get("id"), "completed"):
                    print(f"✅ 任务已完成: {todo.get('content', '')}")
                else:
                    print("❌ 更新任务状态失败")
            else:
                print("❌ 无效的选择")
        else:
            print("❌ 请输入有效的数字")
    except ValueError:
        print("❌ 请输入有效的数字")
    except KeyboardInterrupt:
        print("\n操作已取消")


def show_due_soon(todo_manager, scheduler) -> Any:
    """显示即将到期的任务"""
    print("\n⏰ 即将到期任务 (24小时内):")

    # 从TodoWrite获取
    due_todos = todo_manager.get_due_todos(hours_ahead=24)

    if not due_todos:
        print("   暂无即将到期的任务")
        return

    for todo in due_todos:
        status_icon = {"pending": "⏳", "in_progress": "🔄"}.get(todo.get("status"), "❓")
        print(f"{status_icon} {todo.get('content', '')} - {todo.get('deadline')}")

    # 从调度器获取
    scheduler_tasks = scheduler.get_due_tasks(hours_ahead=24)
    if scheduler_tasks:
        print("\n📅 调度器即将到期任务:")
        for task in scheduler_tasks:
            print(f"🔔 {task.title} - {task.due_at.strftime('%Y-%m-%d %H:%M')}")


def export_tasks(todo_manager) -> Any:
    """导出任务"""
    print("\n📤 导出任务")

    try:
        format_choice = input("选择导出格式 (1:JSON, 2:Markdown, 3:CSV): ").strip()

        format_map = {"1": "json", "2": "markdown", "3": "csv"}
        format_type = format_map.get(format_choice, "json")

        custom_path = input("导出文件路径 (可选，按回车使用默认): ").strip()

        file_path = todo_manager.export_todos(format_type, custom_path)

        print(f"✅ 任务已导出到: {file_path}")

    except Exception as e:
        print(f"❌ 导出失败: {e}")


def show_system_statistics(scheduler, todo_manager) -> Any:
    """显示系统统计"""
    print("\n📊 系统统计信息")

    # TodoWrite统计
    todo_dashboard = get_todo_dashboard()
    print("\n📝 TodoWrite统计:")
    for key, value in todo_dashboard.items():
        print(f"   {key}: {value}")

    # 调度器统计
    scheduler_dashboard = scheduler.get_dashboard_summary()
    print("\n🔔 调度器统计:")
    for key, value in scheduler_dashboard.items():
        print(f"   {key}: {value}")


def test_reminder_system(scheduler, todo_manager) -> Any:
    """测试提醒系统"""
    print("\n🧪 测试提醒系统")

    try:
        # 创建测试任务
        test_time = datetime.now() + timedelta(seconds=30)  # 30秒后

        task = scheduler.create_task(
            title="测试提醒任务",
            description="这是一个用于测试提醒功能的任务",
            priority=TaskPriority.NORMAL,
            due_at=test_time,
            tags=["测试", "提醒"]
        )

        # 添加提醒（提前10秒）
        scheduler.add_reminder(
            task.id,
            ReminderType.NOTIFICATION,
            0,  # 立即提醒
            "🧪 这是一个测试提醒",
            repeat=False
        )

        print(f"✅ 测试任务已创建: {task.title}")
        print("   提醒时间: 立即")
        print(f"   截止时间: {test_time.strftime('%Y-%m-%d %H:%M:%S')}")

        print("📱 请检查系统通知...")

    except Exception as e:
        print(f"❌ 测试失败: {e}")


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description='Athena任务管理系统')
    parser.add_argument('--daemon', action='store_true', help='以守护进程模式运行')
    parser.add_argument('--test', action='store_true', help='运行测试')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')

    args = parser.parse_args()

    print_banner()

    # 初始化系统
    scheduler, todo_manager = initialize_system()

    # 测试模式
    if args.test:
        print("🧪 运行测试模式")
        test_reminder_system(scheduler, todo_manager)
        return

    # 统计信息模式
    if args.stats:
        show_system_statistics(scheduler, todo_manager)
        return

    # 守护进程模式
    if args.daemon:
        print("🔄 守护进程模式已启动")
        print("按 Ctrl+C 停止")

        try:
            while True:
                time.sleep(60)

                # 定期检查即将到期任务
                due_tasks = todo_manager.get_due_todos(hours_ahead=2)
                if due_tasks:
                    print(f"⏰ 发现 {len(due_tasks)} 个即将到期的任务")

        except KeyboardInterrupt:
            print("\n🛑 守护进程已停止")
        return

    # 交互模式
    print("💬 交互模式已启动")

    try:
        while True:
            show_menu()

            try:
                choice = input("\n请选择操作 (0-10): ").strip()

                if choice == "0":
                    print("👋 退出任务管理系统")
                    break

                elif choice == "1":
                    add_task_interactive(todo_manager)

                elif choice == "2":
                    show_all_tasks(todo_manager)

                elif choice == "3":
                    pending_todos = todo_manager.get_todos_by_status("pending")
                    print("\n⏳ 待办任务:")
                    if pending_todos:
                        for i, todo in enumerate(pending_todos, 1):
                            print(f"{i}. {todo.get('content', '')}")
                    else:
                        print("   暂无待办任务")

                elif choice == "4":
                    completed_todos = todo_manager.get_todos_by_status("completed")
                    print("\n✅ 已完成任务:")
                    if completed_todos:
                        for i, todo in enumerate(completed_todos, 1):
                            completed_time = todo.get("completed_at", "")
                            print(f"{i}. {todo.get('content', '')} ({completed_time})")
                    else:
                        print("   暂无已完成任务")

                elif choice == "5":
                    complete_task_interactive(todo_manager)

                elif choice == "6":
                    delete_choice = input("删除任务 (1:按内容, 2:按ID): ").strip()

                    if delete_choice == "1":
                        content = input("输入要删除的任务内容: ").strip()
                        for todo in todo_manager.todos:
                            if todo.get("content") == content:
                                if todo_manager.delete_todo(todo.get("id")):
                                    print(f"✅ 任务已删除: {content}")
                                    break
                        else:
                            print("❌ 未找到匹配的任务")

                    elif delete_choice == "2":
                        todo_id = input("输入要删除的任务ID: ").strip()
                        if todo_manager.delete_todo(todo_id):
                            print(f"✅ 任务已删除: {todo_id}")
                        else:
                            print("❌ 未找到该ID的任务")

                    else:
                        print("❌ 无效的选择")

                elif choice == "7":
                    show_due_soon(todo_manager, scheduler)

                elif choice == "8":
                    export_tasks(todo_manager)

                elif choice == "9":
                    show_system_statistics(scheduler, todo_manager)

                elif choice == "10":
                    test_reminder_system(scheduler, todo_manager)

                else:
                    print("❌ 无效的选择，请输入 0-10")

            except KeyboardInterrupt:
                print("\n操作已取消")
            except ValueError:
                print("❌ 输入格式错误")

    except KeyboardInterrupt:
        print("\n👋 退出任务管理系统")


if __name__ == "__main__":
    main()
