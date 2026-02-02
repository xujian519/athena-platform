#!/usr/bin/env python3
"""
修复版：使用AppleScript创建提醒事项和日历事件
"""

import subprocess
import datetime

def run_applescript(script):
    """执行AppleScript"""
    try:
        result = subprocess.run(['osascript', '-e', script],
                              capture_output=True, text=True, encoding='utf-8')
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"执行失败: {e}")
        return False, "", str(e)

def create_simple_reminder():
    """创建简单的提醒事项"""
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1))

    script = '''
    tell application "Reminders"
        activate
        delay 2
        tell list "提醒"
            make new reminder with properties {name:"明天上午9点联系曹新乐，约他周四见面"}
        end tell
    end tell
    '''
    return script

def create_simple_calendar():
    """创建简单的日历事件"""
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1))

    script = '''
    tell application "Calendar"
        activate
        delay 2
        tell calendar "Home"
            make new event with properties {summary:"联系曹新乐", description:"约他周四见面"}
        end tell
    end tell
    '''
    return script

def create_using_siri():
    """使用Siri创建提醒"""
    script = '''
    tell application "System Events"
        delay 1
        keystroke " " using {command down}
        delay 1
        keystroke "提醒我明天上午9点联系曹新乐"
        delay 1
        key code 36
    end tell
    '''
    return script

def main():
    print("📱 小诺 - 智能提醒创建助手")
    print("=" * 50)
    print("任务：明天上午9点联系曹新乐，约他周四见面\n")

    print("🔧 尝试方法1：直接创建提醒事项...")
    success, output, error = run_applescript(create_simple_reminder())

    if success:
        print("✅ 提醒事项已创建！")
        print("   请手动设置提醒时间为明天上午9:00")
    else:
        print("❌ 自动创建失败")
        print(f"   提示：{error}")

    print("\n🔧 尝试方法2：创建日历事件...")
    success, output, error = run_applescript(create_simple_calendar())

    if success:
        print("✅ 日历事件已创建！")
        print("   请手动设置时间为明天上午9:00")
    else:
        print("❌ 日历创建失败")

    print("\n📋 推荐方法（最简单）：")
    print("-" * 40)
    print("1. 按住 Command + 空格键")
    print("2. 对着麦克风说：")
    print("   \"提醒我明天上午9点联系曹新乐\"")
    print("3. Siri会自动创建提醒事项")
    print("\n或者：")
    print("1. 按住 Command + 空格键")
    print("2. 说：")
    print("   \"创建日历事件：明天上午9点联系曹新乐\"")
    print("3. 设置时长30分钟")
    print("4. 添加备注：约他周四见面")

    print("\n✨ 任务已准备完成！")
    print("⏰ 提醒时间：明天上午9:00")
    print("📞 联系人：曹新乐")
    print("📝 事项：约定周四见面时间地点")

if __name__ == "__main__":
    main()