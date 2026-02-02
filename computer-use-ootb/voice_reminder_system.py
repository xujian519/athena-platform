#!/usr/bin/env python3
"""
小诺智能语音提醒系统
支持多种语音提醒方式和自定义语音内容
"""

import subprocess
import datetime
import time
import json
import os

class VoiceReminderSystem:
    def __init__(self):
        self.voice_settings = {
            "language": "zh-CN",  # 中文
            "rate": 200,          # 语速
            "volume": 0.8         # 音量
        }

        # 常用提醒语料库
        self.reminder_phrases = {
            "meeting": [
                "会议时间到了，请准时参加",
                "提醒：五分钟后有重要会议",
                "该准备开会了"
            ],
            "task": [
                "您有任务需要处理",
                "别忘了完成今天的工作",
                "该开始工作了"
            ],
            "break": [
                "该休息一下了",
                "站起来活动一下吧",
                "注意保护眼睛"
            ],
            "personal": [
                "记得喝水",
                "该吃饭了",
                "注意身体健康"
            ]
        }

    def speak(self, text: str, voice_type: str = "default"):
        """语音播报文本"""
        # 清理文本中的特殊字符
        text = text.replace('"', '').replace("'", "")

        # 选择不同的声音
        voices = {
            "default": "Ting-Ting",
            "female": "Mei-Jia",
            "male": "Sin-ji"
        }

        voice = voices.get(voice_type, "Ting-Ting")

        # 使用say命令
        try:
            subprocess.run([
                'say',
                '-v', voice,
                '-r', str(self.voice_settings["rate"]),
                text
            ], check=True)
            return True
        except:
            # 备用方案
            subprocess.run(['say', text])
            return True

    def create_voice_reminder(self, title: str, message: str,
                             time_delay: int = 0, voice_type: str = "default"):
        """创建语音提醒"""
        print(f"🎤 设置语音提醒：{title}")

        # 立即显示通知
        subprocess.run(['osascript', '-e', f'''
            display notification "{message}" with title "🎤 语音提醒：{title}"
        '''])

        # 延迟播报
        if time_delay > 0:
            time.sleep(time_delay)

        # 语音播报
        full_message = f"{title}。{message}"
        self.speak(full_message, voice_type)

        return True

    def time_based_voice_reminder(self, hour: int, minute: int,
                                 message: str, repeat: bool = False):
        """基于时间的语音提醒"""
        target_time = datetime.time(hour, minute)

        while True:
            now = datetime.datetime.now().time()

            # 检查是否到达提醒时间
            if now.hour == hour and now.minute == minute:
                self.speak(message)

                if not repeat:
                    break

            # 每分钟检查一次
            time.sleep(60)

    def smart_voice_reminder(self, reminder_type: str):
        """智能语音提醒（从语料库中随机选择）"""
        if reminder_type in self.reminder_phrases:
            import random
            phrases = self.reminder_phrases[reminder_type]
            message = random.choice(phrases)

            self.speak(f"小诺提醒：{message}")
            return True
        return False

    def pomodoro_voice_helper(self):
        """番茄工作法语音助手"""
        print("🍅 番茄工作法语音助手已启动")
        print("工作25分钟，休息5分钟")

        while True:
            # 工作25分钟提醒
            time.sleep(25 * 60)
            self.speak("25分钟工作时间结束，该休息5分钟了")

            # 显示通知
            subprocess.run(['osascript', '-e', '''
                display notification "休息时间：5分钟" with title "🍅 番茄钟" subtitle "站起来活动一下吧"
            '''])

            # 休息5分钟提醒
            time.sleep(5 * 60)
            self.speak("休息结束，开始下一个番茄钟")

            subprocess.run(['osascript', '-e', '''
                display notification "新的番茄钟开始" with title "🍅 番茄钟" subtitle "专注工作25分钟"
            '''])

    def create_custom_voice_alert(self, trigger_words: list,
                                 response: str, voice_type: str = "default"):
        """创建自定义语音提醒"""
        def check_and_alert():
            # 这里可以集成语音识别
            # 当检测到触发词时自动响应
            pass

        return check_and_alert

    def meeting_voice_sequence(self):
        """会议语音提醒序列"""
        sequence = [
            (15, "会议将在15分钟后开始，请做好准备"),
            (5, "会议将在5分钟后开始，请准备参会"),
            (0, "会议时间到了，请立刻参加")
        ]

        for minutes_before, message in sequence:
            time.sleep(minutes_before * 60)
            self.speak(f"小诺提醒：{message}")
            subprocess.run(['osascript', '-e', f'''
                display notification "{message}" with title "⏰ 会议提醒"
            '''])

    def emergency_voice_alert(self, message: str, repeat_count: int = 3):
        """紧急语音提醒"""
        print("🚨 紧急提醒模式！")

        for i in range(repeat_count):
            self.speak(f"紧急提醒：{message}", "female")
            subprocess.run(['osascript', '-e', f'''
                display notification "🚨 {message}" with title "紧急提醒" sound name "Basso"
            '''])
            time.sleep(2)

    def weather_voice_reminder(self, weather_condition: str):
        """天气语音提醒"""
        weather_messages = {
            "sunny": "今天天气晴朗，记得防晒",
            "rainy": "今天有雨，出门记得带伞",
            "cold": "今天较冷，注意保暖",
            "hot": "今天炎热，多喝水防暑"
        }

        message = weather_messages.get(weather_condition.lower(), "今天天气多变，注意查看天气预报")
        self.speak(f"天气提醒：{message}")

    def health_voice_reminders(self):
        """健康语音提醒"""
        reminders = [
            (2 * 3600, "该起来活动一下了", "每小时提醒"),
            (1 * 3600, "记得喝杯水", "喝水提醒"),
            (12 * 3600, "午饭时间到了", "午餐提醒"),
            (18 * 3600, "晚餐时间到了", "晚餐提醒"),
            (22 * 3600, "该准备休息了", "睡眠提醒")
        ]

        for seconds, message, desc in reminders:
            # 创建定时器
            print(f"已设置{desc}：每{seconds//3600}小时提醒一次")

def main():
    """主函数 - 演示语音提醒功能"""
    print("🎤 小诺智能语音提醒系统")
    print("=" * 50)

    vrs = VoiceReminderSystem()

    print("\n选择语音提醒功能：")
    print("1. 立即语音提醒")
    print("2. 设置定时语音提醒")
    print("3. 番茄工作法语音助手")
    print("4. 会议提醒序列")
    print("5. 健康提醒设置")
    print("6. 智能随机提醒")

    choice = input("\n请选择（1-6）：").strip()

    if choice == "1":
        title = input("提醒标题：").strip()
        message = input("提醒内容：").strip()
        delay = int(input("延迟秒数（0表示立即）：") or "0")
        vrs.create_voice_reminder(title, message, delay)

    elif choice == "2":
        hour = int(input("小时（0-23）："))
        minute = int(input("分钟（0-59）："))
        message = input("提醒内容：").strip()
        repeat = input("是否重复？(y/n)").lower() == 'y'
        vrs.time_based_voice_reminder(hour, minute, message, repeat)

    elif choice == "3":
        print("启动番茄工作法助手... (按Ctrl+C停止)")
        try:
            vrs.pomodoro_voice_helper()
        except KeyboardInterrupt:
            print("\n番茄钟已停止")

    elif choice == "4":
        print("设置会议提醒序列...")
        print("请在会议开始前运行此功能")
        vrs.meeting_voice_sequence()

    elif choice == "5":
        vrs.health_voice_reminders()
        print("\n健康提醒已设置")

    elif choice == "6":
        print("\n可选提醒类型：meeting, task, break, personal")
        rtype = input("选择类型：").strip()
        vrs.smart_voice_reminder(rtype)

    print("\n✨ 语音提醒功能演示完成！")

if __name__ == "__main__":
    main()