#!/usr/bin/env python3
"""
使用AppleScript创建提醒事项和日历事件
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

def create_reminder_applescript():
    """创建提醒事项的AppleScript"""
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1))
    tomorrow_str = tomorrow.strftime('%B %d, %Y')

    script = f'''
    tell application "Reminders"
        activate
        delay 1

        -- 创建新提醒
        tell list "提醒"
            make new reminder with properties {{
                name: "联系曹新乐，约他周四见面",
                due date: date "{tomorrow_str} at 9:00:00 AM",
                priority: medium,
                remind me date: date "{tomorrow_str} at 8:45:00 AM"
            }}
        end tell

        display notification "提醒事项已创建：明天上午9点联系曹新乐" with title "小诺提醒"
    end tell
    '''
    return script

def create_calendar_applescript():
    """创建日历事件的AppleScript"""
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1))
    tomorrow_str = tomorrow.strftime('%A, %B %d, %Y')

    script = f'''
    tell application "Calendar"
        activate
        delay 1

        -- 创建新事件
        tell calendar "Home"
            make new event with properties {{
                summary: "联系曹新乐 - 约周四见面",
                start date: date "{tomorrow_str} at 9:00:00 AM",
                end date: date "{tomorrow_str} at 9:30:00 AM",
                location: "",
                description: "重要事项：确认周四见面时间和地点"
            }}
        end tell

        display notification "日历事件已创建：明天上午9点联系曹新乐" with title "小诺日历"
    end tell
    '''
    return script

def main():
    print("📱 小诺 - 使用AppleScript创建提醒和日历")
    print("=" * 50)

    # 创建提醒事项
    print("\n1️⃣ 正在创建提醒事项...")
    success, output, error = run_applescript(create_reminder_applescript())

    if success:
        print("✅ 提醒事项创建成功！")
        print("   - 内容：联系曹新乐，约他周四见面")
        print("   - 时间：明天上午9:00")
        print("   - 提醒：明天上午8:45")
    else:
        print("❌ 提醒事项创建失败")
        if error:
            print(f"   错误：{error}")

    # 创建日历事件
    print("\n2️⃣ 正在创建日历事件...")
    success, output, error = run_applescript(create_calendar_applescript())

    if success:
        print("✅ 日历事件创建成功！")
        print("   - 事件：联系曹新乐 - 约周四见面")
        print("   - 时间：明天上午9:00-9:30")
    else:
        print("❌ 日历事件创建失败")
        if error:
            print(f"   错误：{error}")

    print("\n✨ 任务完成！")
    print("如果创建失败，请使用以下方法：")
    print("1. 使用Siri：按住Command+空格，说'提醒我明天上午9点联系曹新乐'")
    print("2. 手动打开提醒事项和日历应用创建")

if __name__ == "__main__":
    main()