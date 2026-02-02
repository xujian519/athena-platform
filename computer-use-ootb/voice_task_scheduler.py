#!/usr/bin/env python3
"""
语音任务调度器
专为"联系曹新乐"任务创建语音提醒
"""

import subprocess
import datetime
import time
import os
import threading
import json

class VoiceTaskScheduler:
    def __init__(self):
        self.tasks = []
        self.running = True

    def schedule_caoxinle_reminder(self):
        """安排曹新乐提醒任务"""
        # 计算明天上午9点
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        target_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)

        # 创建任务信息
        task = {
            "title": "联系曹新乐提醒",
            "target_time": target_time,
            "message": "明天上午9点联系曹新乐，约他周四见面",
            "voice_sequence": [
                ("滴、滴、滴", 0.5),
                ("重要提醒", 0.5),
                ("现在是上午9点", 0.5),
                ("请立即联系曹新乐", 0.5),
                "约他周四见面"
            ]
        }

        print(f"\n📅 已安排语音提醒任务")
        print(f"⏰ 提醒时间：{target_time.strftime('%Y年%m月%d日 %H:%M')}")
        print(f"📝 任务内容：{task['message']}")
        print(f"🎤 将使用中文语音进行提醒")

        self.tasks.append(task)
        return task

    def schedule_advanced_reminder(self):
        """安排高级提醒序列（提前15分钟 + 准时提醒）"""
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)

        # 提前15分钟提醒（8:45）
        pre_reminder_time = tomorrow.replace(hour=8, minute=45, second=0)
        # 准时提醒（9:00）
        exact_reminder_time = tomorrow.replace(hour=9, minute=0, second=0)

        tasks = [
            {
                "title": "曹新乐见面准备提醒",
                "target_time": pre_reminder_time,
                "message": "15分钟后联系曹新乐，请准备通话内容",
                "voice": "Ting-Ting",
                "notification": True
            },
            {
                "title": "曹新乐准时提醒",
                "target_time": exact_reminder_time,
                "message": "现在是上午9点，请立即联系曹新乐",
                "voice": "Mei-Jia",
                "notification": True
            }
        ]

        print("\n📅 已安排高级语音提醒序列：")
        print("-" * 50)
        for task in tasks:
            print(f"⏰ {task['target_time'].strftime('%H:%M')} - {task['title']}")
            print(f"   内容：{task['message']}")
            print()

        self.tasks.extend(tasks)
        return tasks

    def execute_voice_reminder(self, task):
        """执行语音提醒"""
        print(f"\n🎤 执行语音提醒：{task['title']}")
        print(f"⏰ 当前时间：{datetime.datetime.now().strftime('%H:%M:%S')}")

        # 显示通知
        if task.get("notification", True):
            subprocess.run(['osascript', '-e', f'''
                display notification "{task['message']}" with title "🎤 语音提醒：{task['title']}" sound name "Glass"
            '''])

        # 执行语音序列
        if "voice_sequence" in task:
            # 使用自定义语音序列
            for item in task["voice_sequence"]:
                if isinstance(item, tuple):
                    text, pause = item
                else:
                    text = item
                    pause = 0.5

                subprocess.run(['say', '-v', 'Ting-Ting', text])
                time.sleep(pause)
        else:
            # 单条语音提醒
            voice = task.get("voice", "Ting-Ting")
            subprocess.run(['say', '-v', voice, task['message']])

        print("✅ 语音提醒已执行")

    def run_scheduler(self):
        """运行调度器"""
        print("\n🚀 语音任务调度器启动")
        print("=" * 50)
        print("按 Ctrl+C 停止调度器")

        # 创建持续运行的线程
        def scheduler_thread():
            while self.running:
                now = datetime.datetime.now()

                # 检查每个任务
                for task in self.tasks:
                    target_time = task["target_time"]

                    # 检查是否到了提醒时间（误差1分钟内）
                    time_diff = abs((now - target_time).total_seconds())
                    if time_diff < 60 and not task.get("executed", False):
                        # 执行提醒
                        self.execute_voice_reminder(task)
                        task["executed"] = True

                # 每分钟检查一次
                time.sleep(60)

        # 启动线程
        thread = threading.Thread(target=scheduler_thread)
        thread.daemon = True
        thread.start()

        return thread

    def test_voice_now(self):
        """立即测试语音功能"""
        print("\n🎤 立即测试语音提醒...")

        # 测试序列
        test_sequence = [
            ("滴、滴、滴", 0.5),
            ("小诺测试", 0.5),
            ("语音提醒功能正常", 1),
            ("明天上午9点", 0.5),
            ("会准时提醒您联系曹新乐", 0.5)
        ]

        for item in test_sequence:
            if isinstance(item, tuple):
                text, pause = item
            else:
                text = item
                pause = 0.5

            print(f"  播报：{text}")
            subprocess.run(['say', '-v', 'Ting-Ting', text])
            time.sleep(pause)

        print("\n✅ 语音测试完成！")

    def save_schedule(self):
        """保存调度到文件"""
        schedule_data = {
            "created_at": datetime.datetime.now().isoformat(),
            "tasks": []
        }

        for task in self.tasks:
            schedule_data["tasks"].append({
                "title": task["title"],
                "target_time": task["target_time"].isoformat(),
                "message": task["message"]
            })

        with open("/Users/xujian/Athena工作平台/computer-use-ootb/voice_schedule.json", "w") as f:
            json.dump(schedule_data, f, indent=2, ensure_ascii=False)

        print("\n💾 调度已保存到 voice_schedule.json")

def main():
    """主函数"""
    print("🎤 小诺语音任务调度器")
    print("=" * 60)
    print("专为'联系曹新乐'任务设置语音提醒")
    print("=" * 60)

    scheduler = VoiceTaskScheduler()

    print("\n请选择提醒方案：")
    print("1. 基础提醒（明天9:00）")
    print("2. 高级提醒（8:45准备 + 9:00准时）")
    print("3. 测试语音功能")
    print("4. 查看已安排的任务")

    choice = input("\n请选择（1-4）：").strip()

    if choice == "1":
        # 基础提醒
        task = scheduler.schedule_caoxinle_reminder()
        scheduler.save_schedule()

        print("\n启动调度器...")
        thread = scheduler.run_scheduler()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️ 调度器已停止")
            scheduler.running = False

    elif choice == "2":
        # 高级提醒
        tasks = scheduler.schedule_advanced_reminder()
        scheduler.save_schedule()

        print("\n启动调度器...")
        thread = scheduler.run_scheduler()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️ 调度器已停止")
            scheduler.running = False

    elif choice == "3":
        # 测试语音
        scheduler.test_voice_now()

    elif choice == "4":
        # 查看任务
        scheduler.schedule_caoxinle_reminder()
        scheduler.schedule_advanced_reminder()

    print("\n✨ 操作完成！")

if __name__ == "__main__":
    main()