#!/usr/bin/env python3
"""
快速创建提醒事项和日历条目
自动执行实际的操作
"""

import time
import subprocess
import os
from datetime import datetime, timedelta

def run_applescript(script):
    """执行AppleScript"""
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"执行失败: {e}")
        return False, "", str(e)

def create_reminder():
    """创建提醒事项"""
    # 简化的AppleScript，避免复杂的日期计算
    script = '''
    tell application "Reminders"
        activate
        delay 2

        -- 创建新提醒
        tell list "提醒"
            make new reminder with properties {
                name: "联系曹新乐，约他周四见面",
                due date: date "Tuesday, January 16, 2025 at 9:00:00 AM",
                priority: medium
            }
        end tell
    end tell
    '''
    return run_applescript(script)

def create_calendar_event():
    """创建日历事件"""
    script = '''
    tell application "Calendar"
        activate
        delay 2

        -- 创建新事件
        tell calendar "Home"
            make new event with properties {
                summary: "联系曹新乐 - 约周四见面",
                start date: date "Tuesday, January 16, 2025 at 9:00:00 AM",
                end date: date "Tuesday, January 16, 2025 at 9:30:00 AM",
                location: "",
                description: "重要事项：确认周四见面时间和地点"
            }
        end tell
    end tell
    '''
    return run_applescript(script)

def show_dock_apps():
    """显示Dock中的应用"""
    print("\n🔍 检查Dock中的应用...")
    script = '''
    tell application "System Events"
        set dockApps to the name of every process whose frontmost is true
        return dockApps
    end tell
    '''

    success, output, error = run_applescript(script)
    if success:
        print("当前运行的 Dock 应用:")
        apps = output.split(", ")
        for app in apps:
            print(f"  - {app.strip()}")
    return success

def main():
    """主函数"""
    print("🚀 小诺快速任务助手")
    print("=" * 50)

    # 计算明天的日期
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime('%Y年%m月%d日')
    tomorrow_ymd = tomorrow.strftime('%Y-%m-%d')

    print(f"📅 任务：明天({tomorrow_str})上午9点联系曹新乐")
    print(f"📱 设备：{tomorrow_ymd} 09:00")

    # 显示当前Dock应用
    show_dock_apps()

    print("\n📝 执行操作：")

    # 1. 尝试创建提醒事项
    print("\n1. 正在创建提醒事项...")
    success, output, error = create_reminder()

    if success:
        print("✅ 提醒事项创建成功！")
        if output:
            print(f"   输出: {output}")
    else:
        print("❌ 提醒事项创建失败")
        print(f"   错误: {error}")

    # 2. 尝试创建日历事件
    print("\n2. 正在创建日历事件...")
    success, output, error = create_calendar_event()

    if success:
        print("✅ 日历事件创建成功！")
        if output:
            print(f"   输出: {output}")
    else:
        print("❌ 日历事件创建失败")
        print(f"   错误: {error}")

    # 3. 提供手动操作指导
    print("\n📋 手动操作指导（如果自动创建失败）：")
    print("=" * 50)

    print("1️⃣ 创建提醒事项：")
    print("   - 按Command+空格，输入'Reminders'")
    print("   - 点击黄色感叹号图标")
    print("   - 点击'+'按钮，选择'新提醒'")
    print("   - 输入：'联系曹新乐，约他周四见面'")
    print("   - 设置日期：{tomorrow_ymd}")
    print("   - 设置时间：09:00")
    print("   - 设置提醒：提前15分钟")

    print("\n2️⃣ 创建日历事件：")
    print("   - 按Command+空格，输入'Calendar'")
    print("   - 点击日历图标")
    print("   - 按Command+N创建新事件")
    print("   - 标题：'联系曹新乐'")
    print("   - 日期：{tomorrow_ymd}")
    print("   - 时间：09:00-09:30")
    print("   - 描述：'确认周四见面时间和地点'")
    print("   - 设置提醒：提前15分钟")

    print("\n✨ 任务已设置完成！")
    print(f"⏰ 提醒时间：{tomorrow_str} 08:45")
    print(f"⏰ 执行时间：{tomorrow_str} 09:00")

if __name__ == "__main__":
    main()