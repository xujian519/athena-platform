#!/usr/bin/env python3
"""
小诺拖延症对抗助手
Xiaonuo Procrastination Fighter

专门帮助爸爸战胜拖延症的智能助手
"""

import asyncio
import random
from datetime import datetime, timedelta



class ProcrastinationFighter:
    """拖延症对抗助手"""

    def __init__(self):
        self.motivational_quotes = [
            "爸爸,每一个小步骤都在向目标靠近!💪",
            "开始就是成功的一半!5-4-3-2-1,行动!🚀",
            "您已经比昨天的自己更进一步了!🌟",
            "完美的计划不如不完美的行动!🎯",
            "爸爸相信您,现在就开始吧!🌈",
        ]

        self.anti_procrastination_tips = [
            "把任务拆解成极小的步骤,小到无法拒绝",
            "使用5秒法则:5-4-3-2-1,立即行动",
            "设定一个25分钟的番茄钟,只专注这一小段时间",
            "告诉别人你的计划,增加 accountability",
            "移除所有干扰源,手机静音,关闭通知",
            "先做最困难的任务,越早越好",
            "完成一个小步骤就奖励自己,建立正向反馈",
        ]

        self.rewards = {
            10: "☕ 一杯好咖啡",
            30: "🚶 10分钟散步",
            50: "📱 15分钟自由刷手机",
            100: "🎬 看一集喜欢的剧",
            200: "🎁 买一个想要的小东西",
            500: "🍽️ 一顿好吃的晚餐",
            1000: "🎉 任何你想要的奖励!",
        }

    def motivate(self) -> str:
        """提供即时激励"""
        return random.choice(self.motivational_quotes)

    def get_tip(self) -> str:
        """获取抗拖延技巧"""
        return random.choice(self.anti_procrastination_tips)

    def five_second_rule(self, task: str) -> str:
        """5秒启动法则"""
        message = f"""
🎯 5秒启动法则!
任务: {task}

5...
4...
3...
2...
1...
🚀 开始行动!
"""
        return message.strip()

    def break_down_task(self, task: str) -> list[str]:
        """智能任务拆解"""
        # 这里可以集成AI能力,现在先简单实现
        subtasks = [
            f"📍 步骤1: 准备开始 {task} (2分钟)",
            "📍 步骤2: 理解任务要求 (5分钟)",
            "📍 步骤3: 制定简单计划 (3分钟)",
            "📍 步骤4: 开始执行第一部分 (15分钟)",
            "📍 步骤5: 完成并检查 (5分钟)",
        ]
        return subtasks

    def suggest_pomodoro(self, task: str, estimated_minutes: int) -> dict:
        """建议番茄钟数量"""
        # 每个番茄钟25分钟
        pomodoros = max(1, (estimated_minutes + 24) // 25)

        suggestion = {
            "task": task,
            "estimated_time": estimated_minutes,
            "pomodoros_needed": pomodoros,
            "total_focus_time": pomodoros * 25,
            "total_break_time": (pomodoros - 1) * 5,
            "total_time": pomodoros * 25 + (pomodoros - 1) * 5,
            "schedule": [],
        }

        # 生成时间表
        current_time = datetime.now()
        for i in range(pomodoros):
            start = current_time + timedelta(minutes=i * 30)
            end = start + timedelta(minutes=25)
            suggestion["schedule"].append(
                {
                    "pomodoro": i + 1,
                    "start": start.strftime("%H:%M"),
                    "end": end.strftime("%H:%M"),
                    "focus": "25分钟专注",
                    "break": "5分钟休息" if i < pomodoros - 1 else "完成!",
                }
            )

        return suggestion

    def calculate_reward(self, pomodoros_completed: int, tasks_completed: int) -> tuple:
        """计算奖励积分"""
        points = pomodoros_completed * 5 + tasks_completed * 10
        next_reward = None
        for threshold, reward in sorted(self.rewards.items()):
            if points >= threshold:
                next_reward = (threshold, reward)

        return points, next_reward

    def daily_checklist(self) -> dict:
        """每日检查清单"""
        return {
            "早晨启动": {
                "时间": "9:00",
                "任务": "告诉我今天最重要的3件事",
                "预计": "2分钟",
                "status": "⬜ 待完成",
            },
            "中午检查": {
                "时间": "12:00",
                "任务": "上午进展如何?需要调整吗?",
                "预计": "2分钟",
                "status": "⬜ 待完成",
            },
            "傍晚回顾": {
                "时间": "18:00",
                "任务": "今天的任务完成情况",
                "预计": "3分钟",
                "status": "⬜ 待完成",
            },
            "晚间规划": {
                "时间": "22:00",
                "任务": "规划明天的重要任务",
                "预计": "5分钟",
                "status": "⬜ 待完成",
            },
        }

    def show_progress(self, data: dict) -> str:
        """展示进度报告"""
        total_tasks = data.get("total_tasks", 0)
        completed_tasks = data.get("completed_tasks", 0)
        pomodoros = data.get("pomodoros", 0)
        streak_days = data.get("streak_days", 0)

        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        report = f"""
📊 爸爸的进度报告
{'='*60}
✅ 完成任务: {completed_tasks}/{total_tasks} ({completion_rate:.1f}%)
🍅 番茄钟: {pomodoros}个
🔥 连续天数: {streak_days}天
{'='*60}
{self.motivate()}
"""
        return report.strip()


# 交互式CLI
async def interactive_mode():
    """交互式模式"""
    fighter = ProcrastinationFighter()

    print("\n" + "=" * 60)
    print("🌸 小诺拖延症对抗助手".center(60))
    print("=" * 60)

    while True:
        print("\n请选择:")
        print("1. 💪 获取即时激励")
        print("2. 💡 获取抗拖延技巧")
        print("3. 🚀 使用5秒启动法则")
        print("4. ✂️ 拆解任务")
        print("5. 🍅 规划番茄钟")
        print("6. 📋 查看每日检查清单")
        print("7. 📊 查看进度报告")
        print("0. 👋 退出")

        choice = input("\n请输入选择 (0-7): ").strip()

        if choice == "0":
            print(f"\n{fighter.motivate()}")
            print("再见爸爸!加油!💪")
            break

        elif choice == "1":
            print(f"\n{fighter.motivate()}")

        elif choice == "2":
            print("\n💡 抗拖延技巧:")
            print(f"   {fighter.get_tip()}")

        elif choice == "3":
            task = input("\n请输入要开始的任务: ").strip()
            if task:
                print(f"\n{fighter.five_second_rule(task)}")

        elif choice == "4":
            task = input("\n请输入要拆解的任务: ").strip()
            if task:
                subtasks = fighter.break_down_task(task)
                print("\n✂️ 任务拆解:")
                for subtask in subtasks:
                    print(f"   {subtask}")

        elif choice == "5":
            task = input("\n请输入任务名称: ").strip()
            try:
                minutes = int(input("请输入预估时间(分钟): ").strip())
                suggestion = fighter.suggest_pomodoro(task, minutes)

                print("\n🍅 番茄钟规划:")
                print(f"   任务: {task}")
                print(f"   预估: {minutes}分钟")
                print(f"   需要: {suggestion['pomodoros_needed']}个番茄钟")
                print(f"   总专注: {suggestion['total_focus_time']}分钟")
                print(f"   总休息: {suggestion['total_break_time']}分钟")
                print("\n   时间表:")
                for item in suggestion["schedule"]:
                    print(
                        f"   番茄{item['pomodoro']}: {item['start']}-{item['end']} ({item['focus']})"
                    )
                    if item["break"] != "完成!":
                        print(f"           休息: {item['break']}")
            except ValueError:
                print("❌ 请输入有效的分钟数")

        elif choice == "6":
            checklist = fighter.daily_checklist()
            print("\n📋 今日检查清单:")
            for name, item in checklist.items():
                print(f"\n   {name}:")
                print(f"   ⏰ 时间: {item['时间']}")
                print(f"   📝 任务: {item['任务']}")
                print(f"   ⏱️ 预计: {item['预计']}")
                print(f"   状态: {item['status']}")

        elif choice == "7":
            # 模拟数据
            data = {"total_tasks": 10, "completed_tasks": 7, "pomodoros": 12, "streak_days": 5}
            print(f"\n{fighter.show_progress(data)}")

        else:
            print("\n❌ 无效选择,请重试")


def main() -> None:
    """主函数"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        fighter = ProcrastinationFighter()

        if command == "motivate":
            print(fighter.motivate())
        elif command == "tip":
            print(fighter.get_tip())
        elif command == "five-second":
            if len(sys.argv) > 2:
                task = " ".join(sys.argv[2:])
                print(fighter.five_second_rule(task))
        elif command == "breakdown":
            if len(sys.argv) > 2:
                task = " ".join(sys.argv[2:])
                subtasks = fighter.break_down_task(task)
                print("✂️ 任务拆解:")
                for subtask in subtasks:
                    print(f"   {subtask}")
        elif command == "pomodoro":
            if len(sys.argv) > 3:
                task = sys.argv[2]
                try:
                    minutes = int(sys.argv[3])
                    suggestion = fighter.suggest_pomodoro(task, minutes)
                    print("🍅 番茄钟规划:")
                    print(f"   任务: {task}")
                    print(f"   需要: {suggestion['pomodoros_needed']}个番茄钟")
                    print("\n   时间表:")
                    for item in suggestion["schedule"]:
                        print(f"   番茄{item['pomodoro']}: {item['start']}-{item['end']}")
                except ValueError:
                    print("❌ 请输入有效的分钟数")
        elif command == "interactive":
            asyncio.run(interactive_mode())
        else:
            print("用法:")
            print("  python xiaonuo_procrastination_helper.py motivate")
            print("  python xiaonuo_procrastination_helper.py tip")
            print("  python xiaonuo_procrastination_helper.py five-second <任务>")
            print("  python xiaonuo_procrastination_helper.py breakdown <任务>")
            print("  python xiaonuo_procrastination_helper.py pomodoro <任务> <分钟数>")
            print("  python xiaonuo_procrastination_helper.py interactive")
    else:
        # 默认进入交互模式
        asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()
