#!/usr/bin/env python3
"""
智能定时任务系统
支持定时执行自动化任务
"""

import schedule
import time
import asyncio
import subprocess
from datetime import datetime, timedelta
import json
import os

class TaskScheduler:
    def __init__(self):
        self.tasks = []
        self.task_file = "/Users/xujian/Athena工作平台/computer-use-ootb/scheduled_tasks.json"
        self.load_tasks()

    def load_tasks(self):
        """加载已保存的任务"""
        if os.path.exists(self.task_file):
            try:
                with open(self.task_file, 'r') as f:
                    self.tasks = json.load(f)
            except:
                self.tasks = []

    def save_tasks(self):
        """保存任务到文件"""
        with open(self.task_file, 'w') as f:
            json.dump(self.tasks, f, indent=2)

    def add_task(self, name, task_type, schedule_time, params):
        """添加新任务"""
        task = {
            "id": len(self.tasks) + 1,
            "name": name,
            "type": task_type,
            "schedule": schedule_time,
            "params": params,
            "created_at": datetime.now().isoformat(),
            "active": True,
            "last_run": None,
            "next_run": None
        }
        self.tasks.append(task)
        self.save_tasks()
        return task

    def create_reminder_task(self):
        """创建提醒任务"""
        # 计算明天上午9点
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_9am = tomorrow.replace(hour=9, minute=0, second=0)

        # 添加任务
        task = self.add_task(
            name="提醒：联系曹新乐",
            task_type="reminder",
            schedule_time=tomorrow_9am.strftime("%Y-%m-%d %H:%M"),
            params={
                "content": "联系曹新乐，约他周四见面",
                "app": "Reminders"
            }
        )

        # 设置schedule
        schedule.every().day.at("09:00").do(self.run_reminder_task, task).tag(str(task["id"]))

        print(f"✅ 已添加提醒任务：{task['name']}")
        print(f"   时间：{task['schedule']}")

    def create_notification_task(self, minutes_before=15):
        """创建通知任务（提前提醒）"""
        # 计算明天上午8:45（提前15分钟）
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_845 = tomorrow.replace(hour=8, minute=45, second=0)

        task = self.add_task(
            name=f"提前通知：联系曹新乐（{minutes_before}分钟前）",
            task_type="notification",
            schedule_time=tomorrow_845.strftime("%Y-%m-%d %H:%M"),
            params={
                "title": "任务提醒",
                "message": "15分钟后联系曹新乐，约他周四见面",
                "app": "System Notifications"
            }
        )

        schedule.every().day.at("08:45").do(self.run_notification_task, task).tag(str(task["id"]))

        print(f"✅ 已添加通知任务：{task['name']}")

    def run_reminder_task(self, task):
        """运行提醒任务"""
        print(f"\n⏰ 执行提醒任务：{task['name']} - {datetime.now()}")

        # 显示系统通知
        subprocess.run(['osascript', '-e', f'''
            display notification "{task['params']['content']}" with title "⏰ 小诺提醒" subtitle "任务时间到了！"
        '''])

        # 打开提醒事项应用
        subprocess.run(['open', '-a', 'Reminders'])

        # 自动创建提醒（如果可能）
        self.auto_create_reminder(task['params']['content'])

        # 记录执行
        task['last_run'] = datetime.now().isoformat()
        self.save_tasks()

    def run_notification_task(self, task):
        """运行通知任务"""
        print(f"\n🔔 执行通知任务：{task['name']} - {datetime.now()}")

        params = task['params']
        subprocess.run(['osascript', '-e', f'''
            display notification "{params['message']}" with title "{params['title']}" sound name "Glass"
        '''])

        # 记录执行
        task['last_run'] = datetime.now().isoformat()
        self.save_tasks()

    def auto_create_reminder(self, content):
        """自动创建提醒事项"""
        try:
            script = f'''
            tell application "Reminders"
                activate
                delay 1
                tell list "提醒"
                    make new reminder with properties {{name:"{content}"}}
                end tell
            end tell
            '''
            subprocess.run(['osascript', '-e', script])
            print("✅ 自动创建提醒成功")
        except:
            print("⚠️ 自动创建提醒失败，请手动创建")

    def add_recurring_task(self, name, interval, task_func):
        """添加重复任务"""
        if interval == "daily":
            schedule.every().day.at("09:00").do(task_func).tag(name)
        elif interval == "hourly":
            schedule.every().hour.do(task_func).tag(name)
        elif interval == "weekly":
            schedule.every().monday.at("09:00").do(task_func).tag(name)

    def show_tasks(self):
        """显示所有任务"""
        print("\n📋 已安排的任务：")
        print("=" * 50)

        for task in self.tasks:
            status = "✅ 活跃" if task['active'] else "❌ 停用"
            last_run = task.get('last_run', '从未')
            print(f"\n任务 {task['id']}: {task['name']}")
            print(f"  类型：{task['type']}")
            print(f"  时间：{task['schedule']}")
            print(f"  状态：{status}")
            print(f"  上次执行：{last_run}")

    def run_scheduler(self):
        """运行调度器"""
        print("\n🚀 任务调度器已启动")
        print("=" * 50)
        print("按 Ctrl+C 停止调度器")

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️  调度器已停止")

    def test_notification(self):
        """测试通知功能"""
        print("\n🔔 测试通知功能...")
        subprocess.run(['osascript', '-e', '''
            display notification "这是测试通知" with title "小诺测试" subtitle "系统正常工作"
        '''])
        print("✅ 通知测试完成")

def setup_recurring_reminders():
    """设置定期提醒"""
    print("\n⏰ 设置定期提醒...")

    # 每天上午9点的健康提醒
    schedule.every().day.at("09:00").do(
        lambda: subprocess.run(['osascript', '-e', '''
            display notification "记得查看今天的任务安排" with title "📅 每日提醒"
        '''])
    )

    # 每周五下午5点的工作总结提醒
    schedule.every().friday.at("17:00").do(
        lambda: subprocess.run(['osascript', '-e', '''
            display notification "记得做本周工作总结" with title "💼 周五提醒"
        '''])
    )

def main():
    """主函数"""
    print("🕐 小诺智能定时任务系统")
    print("=" * 50)

    scheduler = TaskScheduler()

    print("\n选择功能：")
    print("1. 添加明天9点的提醒任务")
    print("2. 添加提前15分钟的通知")
    print("3. 添加明天9点的提醒+提前通知")
    print("4. 查看所有任务")
    print("5. 测试通知功能")
    print("6. 启动调度器")
    print("7. 设置定期提醒")

    choice = input("\n请选择（1-7）：").strip()

    if choice == "1":
        scheduler.create_reminder_task()
    elif choice == "2":
        scheduler.create_notification_task()
    elif choice == "3":
        scheduler.create_reminder_task()
        scheduler.create_notification_task()
    elif choice == "4":
        scheduler.show_tasks()
    elif choice == "5":
        scheduler.test_notification()
    elif choice == "6":
        # 先添加任务
        print("\n先添加明天9点的提醒和提前通知...")
        scheduler.create_reminder_task()
        scheduler.create_notification_task()
        # 启动调度器
        scheduler.run_scheduler()
    elif choice == "7":
        setup_recurring_reminders()
        print("\n✅ 定期提醒已设置，请选择6启动调度器")
    else:
        print("无效选择")

    print("\n✨ 操作完成！")

if __name__ == "__main__":
    main()