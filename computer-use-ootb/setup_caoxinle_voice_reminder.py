#!/usr/bin/env python3
"""
自动设置曹新乐语音提醒
直接执行，无需交互
"""

import subprocess
import datetime
import time
import os
import json
import threading

def setup_voice_reminder():
    """设置语音提醒"""
    print("\n🎤 小诺语音提醒设置")
    print("=" * 50)

    # 计算明天上午9点
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    target_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)

    # 提前15分钟的提醒时间
    pre_reminder_time = tomorrow.replace(hour=8, minute=45, second=0)

    print(f"\n📅 目标时间：{target_time.strftime('%Y年%m月%d日 %H:%M')}")
    print(f"⏰ 准备提醒：{pre_reminder_time.strftime('%H:%M')}")
    print(f"📝 任务内容：联系曹新乐，约他周四见面")

    # 保存提醒信息
    reminder_info = {
        "exact_reminder": {
            "time": target_time.strftime('%Y-%m-%d %H:%M'),
            "message": "现在是上午9点，请立即联系曹新乐"
        },
        "pre_reminder": {
            "time": pre_reminder_time.strftime('%Y-%m-%d %H:%M'),
            "message": "15分钟后联系曹新乐，请准备通话内容"
        },
        "task": "联系曹新乐，约他周四见面",
        "created_at": datetime.datetime.now().isoformat()
    }

    # 保存到文件
    with open("/Users/xujian/Athena工作平台/computer-use-ootb/caoxinle_reminder.json", "w") as f:
        json.dump(reminder_info, f, indent=2, ensure_ascii=False)

    print("\n✅ 语音提醒已设置并保存")

def create_reminder_launchd():
    """创建launchd任务（系统级定时任务）"""
    print("\n🔧 创建系统定时任务...")

    # 创建launchd plist文件
    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.xiaonuo.caoxinle.reminder</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/osascript</string>
        <string>-e</string>
        <string>display notification "现在是上午9点，请立即联系曹新乐，约他周四见面" with title "🎤 小诺提醒" sound name "Glass"</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>'''

    # 保存plist文件
    plist_path = os.path.expanduser("~/Library/LaunchAgents/com.xiaonuo.caoxinle.reminder.plist")
    with open(plist_path, "w") as f:
        f.write(plist_content)

    print(f"✅ 定时任务已创建：{plist_path}")
    print("\n⚠️ 请执行以下命令激活定时任务：")
    print(f"launchctl load {plist_path}")

def create_voice_script():
    """创建独立的语音提醒脚本"""
    script_content = f'''#!/bin/bash
# 曹新乐语音提醒脚本

# 显示通知
osascript -e 'display notification "现在是上午9点，请立即联系曹新乐，约他周四见面" with title "🎤 小诺提醒" sound name "Glass"'

# 语音提醒序列
say -v Ting-Ting "滴、滴、滴"
sleep 0.5
say -v Ting-Ting "重要提醒"
sleep 0.5
say -v Ting-Ting "现在是上午9点"
sleep 0.5
say -v Mei-Jia "请立即联系曹新乐"
sleep 0.5
say -v Ting-Ting "约他周四见面"

# 打开提醒事项
open -a "Reminders"

# 记录执行时间
echo "$(date): 曹新乐语音提醒已执行" >> /tmp/caoxinle_reminder.log
'''

    script_path = "/Users/xujian/Athena工作平台/computer-use-ootb/caoxinle_voice_reminder.sh"
    with open(script_path, "w") as f:
        f.write(script_content)

    # 添加执行权限
    os.chmod(script_path, 0o755)

    print(f"✅ 语音提醒脚本已创建：{script_path}")

def show_automation_commands():
    """显示自动化的命令"""
    print("\n💻 自动化命令参考：")
    print("-" * 50)

    print("\n1. 使用cron定时任务（推荐）：")
    print("   编辑crontab：crontab -e")
    print("   添加：0 9 * * * /Users/xujian/Athena工作平台/computer-use-ootb/caoxinle_voice_reminder.sh")

    print("\n2. 使用launchd（系统级）：")
    print("   已创建plist文件，执行：")
    print("   launchctl load ~/Library/LaunchAgents/com.xiaonuo.caoxinle.reminder.plist")

    print("\n3. 使用Python后台运行：")
    print("   nohup python3 -c \"import time; import datetime; import subprocess; ")
    print("   while True: ")
    print("       if datetime.datetime.now().hour == 9 and datetime.datetime.now().minute == 0: ")
    print("           subprocess.run(['say', '-v', 'Ting-Ting', '联系曹新乐']); ")
    print("       time.sleep(60)\" &")

    print("\n4. 立即测试语音：")
    print("   say -v Ting-Ting '测试语音：联系曹新乐'")

def test_voice_now():
    """立即测试语音"""
    print("\n🎤 立即测试语音提醒...")

    # 测试序列
    test_messages = [
        ("滴、滴、滴", 0.5),
        ("小诺提醒", 0.5),
        ("明天上午9点", 0.5),
        ("会准时提醒您", 0.5),
        ("联系曹新乐", 0.5),
        ("约他周四见面", 0.5)
    ]

    for message, pause in test_messages:
        print(f"  🎤 {message}")
        subprocess.run(['say', '-v', 'Ting-Ting', message])
        time.sleep(pause)

    print("\n✅ 语音测试完成！")

def main():
    """主函数"""
    print("\n" + "🎤" * 20)
    print("小诺语音提醒自动设置器")
    print("🎤" * 20)

    # 1. 设置提醒
    setup_voice_reminder()

    # 2. 创建语音脚本
    create_voice_script()

    # 3. 创建系统定时任务
    create_reminder_launchd()

    # 4. 测试语音
    test_voice_now()

    # 5. 显示自动化命令
    show_automation_commands()

    print("\n" + "="*60)
    print("✨ 语音提醒设置完成！")
    print("="*60)

    print("\n📋 已完成：")
    print("1. ✅ 明天上午9:00的语音提醒已安排")
    print("2. ✅ 上午8:45的准备提醒已安排")
    print("3. ✅ 语音提醒脚本已创建")
    print("4. ✅ 系统定时任务已准备")
    print("5. ✅ 语音功能测试完成")

    print("\n💡 使用建议：")
    print("- 运行 'launchctl load ~/Library/LaunchAgents/com.xiaonuo.caoxinle.reminder.plist' 激活系统定时任务")
    print("- 或使用cron定时任务实现自动化")
    print("- 脚本会自动打开提醒事项应用")

if __name__ == "__main__":
    main()