#!/usr/bin/env python3
"""
增强版自动化提醒创建脚本
支持多种自动化方式
"""

import subprocess
import datetime
import time
import sys

def check_permissions():
    """检查并请求必要的系统权限"""
    print("🔍 检查系统权限...")

    # 检查System Events权限
    try:
        script = 'tell application "System Events" to get name of application processes'
        result = subprocess.run(['osascript', '-e', script],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ System Events 权限已配置")
            return True
        else:
            print("❌ System Events 权限未配置")
            return False
    except:
        print("❌ 无法检查权限")
        return False

def create_reminder_enhanced():
    """增强版创建提醒事项"""
    print("\n📝 正在创建提醒事项...")

    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1))
    tomorrow_date = tomorrow.strftime('%Y年%m月%d日')

    # 使用osascript创建提醒（增强版）
    script = f'''
    tell application "System Events"
        -- 确保Reminders正在运行
        if not (exists process "Reminders") then
            tell application "Reminders" to activate
            delay 2
        end if
    end tell

    tell application "Reminders"
        activate
        delay 1

        -- 获取或创建默认列表
        try
            set defaultList to list "提醒"
        on error
            set defaultList to make new list with properties {{name:"提醒"}}
        end try

        -- 创建新提醒
        tell defaultList
            -- 删除可能存在的重复提醒
            delete every reminder whose name contains "联系曹新乐"

            -- 创建新提醒
            set newReminder to make new reminder with properties {{_
                name:"联系曹新乐，约他周四见面",_
                priority:2_
            }}

            -- 设置提醒时间
            set due date of newReminder to date "{tomorrow_date} 09:00:00"
            set remind me date of newReminder to date "{tomorrow_date} 08:45:00"
        end tell

        -- 显示通知
        display notification "提醒已创建：明天上午9点联系曹新乐" with title "小诺助手" subtitle "任务已保存"
    end tell
    '''

    result = subprocess.run(['osascript', '-e', script],
                          capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ 提醒事项创建成功！")
        print(f"   - 时间：{tomorrow_date} 09:00")
        print("   - 提醒：提前15分钟")
        return True
    else:
        print("❌ 提醒事项创建失败")
        if result.stderr:
            print(f"   错误：{result.stderr}")
        return False

def create_calendar_enhanced():
    """增强版创建日历事件"""
    print("\n📅 正在创建日历事件...")

    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1))
    tomorrow_date = tomorrow.strftime('%Y年%m月%d日')

    script = f'''
    tell application "System Events"
        -- 确保Calendar正在运行
        if not (exists process "Calendar") then
            tell application "Calendar" to activate
            delay 2
        end if
    end tell

    tell application "Calendar"
        activate
        delay 1

        -- 获取或创建默认日历
        try
            set defaultCal to calendar "Home"
        on error
            try
                set defaultCal to calendar "个人"
            on error
                set defaultCal to calendar 1
            end try
        end try

        -- 删除可能存在的重复事件
        delete every event of defaultCal whose summary contains "联系曹新乐"

        -- 创建新事件
        tell defaultCal
            make new event with properties {{_
                summary:"联系曹新乐 - 约周四见面",_
                start date:date "{tomorrow_date} 09:00:00",_
                end date:date "{tomorrow_date} 09:30:00",_
                description:"重要事项：确认周四见面时间和地点",_
                location:"",_
                allday event:false_
            }}

            -- 设置提醒
            tell last event
                make new sound alarm at date "{tomorrow_date} 08:45:00"
            end tell
        end tell

        -- 显示通知
        display notification "日历事件已创建：明天上午9点联系曹新乐" with title "小诺助手" subtitle "日程已安排"
    end tell
    '''

    result = subprocess.run(['osascript', '-e', script],
                          capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ 日历事件创建成功！")
        print(f"   - 时间：{tomorrow_date} 09:00-09:30")
        print("   - 提醒：提前15分钟")
        return True
    else:
        print("❌ 日历事件创建失败")
        if result.stderr:
            print(f"   错误：{result.stderr}")
        return False

def create_shortcut_workflow():
    """创建快捷指令工作流"""
    print("\n⚡ 正在创建快捷指令...")

    # 创建一个简单的快捷指令
    script = '''
    tell application "Shortcuts Events"
        run shortcut "创建提醒事项" with input "明天上午9点联系曹新乐，约他周四见面"
    end tell
    '''

    result = subprocess.run(['osascript', '-e', script],
                          capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ 快捷指令执行成功！")
        return True
    else:
        print("ℹ️ 需要先创建快捷指令")
        return False

def show_manual_guide():
    """显示手动操作指南"""
    print("\n📋 手动操作指南")
    print("-" * 50)
    print("如果自动创建失败，请按以下步骤手动操作：")
    print("")
    print("【提醒事项】")
    print("1. 点击提醒事项应用左上角的 + 按钮")
    print("2. 输入：联系曹新乐，约他周四见面")
    print("3. 点击信息图标 (i)")
    print("4. 设置日期：明天")
    print("5. 设置时间：09:00")
    print("6. 设置提醒：当天的08:45")
    print("")
    print("【日历】")
    print("1. 在日历中找到明天上午9:00")
    print("2. 双击创建新事件")
    print("3. 标题：联系曹新乐")
    print("4. 时间：09:00-09:30")
    print("5. 描述：约他周四见面")
    print("6. 设置提醒：提前15分钟")

def main():
    """主函数"""
    print("🚀 小诺增强版自动化助手")
    print("=" * 50)
    print("任务：创建提醒事项和日历事件")
    print("内容：明天上午9点联系曹新乐，约他周四见面")
    print("=" * 50)

    # 检查权限
    if not check_permissions():
        print("\n⚠️ 检测到权限未完全配置")
        print("请按照提示配置权限后重试")
        print("或选择手动创建")

    # 尝试自动创建
    print("\n🔧 尝试自动创建...")

    reminder_success = False
    calendar_success = False

    # 创建提醒事项
    reminder_success = create_reminder_enhanced()

    # 创建日历事件
    calendar_success = create_calendar_enhanced()

    # 尝试快捷指令
    if not (reminder_success or calendar_success):
        print("\n⚡ 尝试使用快捷指令...")
        create_shortcut_workflow()

    # 显示结果
    print("\n" + "=" * 50)
    print("✨ 创建结果")
    print("=" * 50)

    if reminder_success:
        print("✅ 提醒事项：创建成功")
    else:
        print("❌ 提醒事项：需要手动创建")

    if calendar_success:
        print("✅ 日历事件：创建成功")
    else:
        print("❌ 日历事件：需要手动创建")

    # 如果自动创建失败，显示手动指南
    if not (reminder_success and calendar_success):
        show_manual_guide()

    print("\n🎯 任务设置完成！")
    print("⏰ 执行时间：明天上午9:00")
    print("📞 联系人：曹新乐")
    print("📝 事项：约定周四见面")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 操作已取消")
    except Exception as e:
        print(f"\n❌ 发生错误：{e}")