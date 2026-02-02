#!/usr/bin/env python3
"""
简化的自动化助手
使用更可靠的方法创建提醒事项
"""

import subprocess
import datetime
import time
import os

def run_osascript_safe(script):
    """安全地运行osascript"""
    try:
        # 将脚本写入临时文件
        with open('/tmp/temp_script.scpt', 'w') as f:
            f.write(script)

        # 运行脚本
        result = subprocess.run(['osascript', '/tmp/temp_script.scpt'],
                              capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    finally:
        # 清理临时文件
        if os.path.exists('/tmp/temp_script.scpt'):
            os.remove('/tmp/temp_script.scpt')

def create_simple_reminder():
    """创建简单提醒事项"""
    script = '''
    tell application "Reminders"
        activate
    end tell
    '''

    print("📝 正在打开提醒事项应用...")
    success, output, error = run_osascript_safe(script)

    if success:
        print("✅ 提醒事项应用已打开")
        print("\n请手动完成以下步骤：")
        print("1. 点击左上角的 '+' 按钮")
        print("2. 输入：联系曹新乐，约他周四见面")
        print("3. 按回车保存")
        return True
    else:
        print("❌ 无法打开提醒事项应用")
        return False

def create_simple_calendar():
    """创建简单日历事件"""
    script = '''
    tell application "Calendar"
        activate
    end tell
    '''

    print("\n📅 正在打开日历应用...")
    success, output, error = run_osascript_safe(script)

    if success:
        print("✅ 日历应用已打开")
        print("\n请手动完成以下步骤：")
        print("1. 按 Command + N 创建新事件")
        print("2. 标题：联系曹新乐")
        print("3. 日期：明天")
        print("4. 时间：09:00-09:30")
        print("5. 描述：约他周四见面")
        return True
    else:
        print("❌ 无法打开日历应用")
        return False

def check_app_running(app_name):
    """检查应用是否正在运行"""
    script = f'''
    tell application "System Events"
        return (exists process "{app_name}")
    end tell
    '''
    success, output, error = run_osascript_safe(script)
    return success and "true" in output.lower()

def auto_type_text(text):
    """自动输入文本（需要辅助功能权限）"""
    # 使用系统命令模拟键盘输入
    # 注意：这需要辅助功能权限
    pass

def show_siri_guide():
    """显示Siri使用指南"""
    print("\n🗣️ Siri创建提醒（最简单方法）：")
    print("-" * 40)
    print("1. 按住 Command + 空格键")
    print("2. 对着麦克风说：")
    print("   \"提醒我明天上午9点联系曹新乐\"")
    print("3. Siri会自动创建提醒事项")
    print("\n创建日历事件：")
    print("1. 按住 Command + 空格键")
    print("2. 说：\"创建日历事件，明天上午9点联系曹新乐\"")

def main():
    """主函数"""
    print("🤖 小诺简化自动化助手")
    print("=" * 50)

    # 显示当前任务
    print("\n📋 任务：明天上午9点联系曹新乐，约他周四见面")
    print(f"📅 日期：{(datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y年%m月%d日')}")

    # 显示Siri指南
    show_siri_guide()

    print("\n" + "=" * 50)
    print("选择操作方式：")
    print("1. 自动打开提醒事项应用")
    print("2. 自动打开日历应用")
    print("3. 同时打开两个应用")
    print("4. 仅查看Siri指南")

    try:
        choice = input("\n请选择（1-4）：").strip()

        if choice == "1":
            create_simple_reminder()
        elif choice == "2":
            create_simple_calendar()
        elif choice == "3":
            r1 = create_simple_reminder()
            r2 = create_simple_calendar()
            if r1 and r2:
                print("\n✅ 两个应用都已打开，请分别创建提醒和日历")
        elif choice == "4":
            show_siri_guide()
        else:
            print("无效选择")
    except KeyboardInterrupt:
        print("\n\n👋 操作已取消")

    print("\n✨ 操作完成！")
    print("⏰ 提醒：明天上午9点联系曹新乐")

if __name__ == "__main__":
    main()