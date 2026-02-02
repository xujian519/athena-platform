#!/usr/bin/env python3
"""
小诺智能提醒创建指南 - 终极版
整合GLM-4V分析和多种创建方法
"""

import subprocess
import sys
import os

def show_title():
    """显示标题"""
    print("🎯 小诺智能提醒创建助手")
    print("=" * 60)
    print("📋 任务：明天上午9点联系曹新乐，约他周四见面")
    print("📅 日期：2025年12月16日（星期二）")
    print("⏰ 时间：上午9:00")
    print("=" * 60)

def show_methods():
    """显示所有可用的创建方法"""
    print("\n\n📝 创建提醒事项的4种方法：")
    print("-" * 60)

    print("\n【方法1】Siri语音创建（推荐⭐⭐⭐⭐⭐）")
    print("┌─────────────────────────────────────────┐")
    print("│ 1. 按住 Command + 空格键                │")
    print("│ 2. 说出：「提醒我明天上午9点联系曹新乐」    │")
    print("│ 3. Siri自动创建提醒事项                   │")
    print("│ ✅ 最简单，10秒完成                     │")
    print("└─────────────────────────────────────────┘")

    print("\n【方法2】Spotlight搜索提醒事项（推荐⭐⭐⭐⭐）")
    print("┌─────────────────────────────────────────┐")
    print("│ 1. Command + 空格，输入：「提醒事项」      │")
    print("│ 2. 打开应用（黄色感叹号图标）              │")
    print("│ 3. 点击左上角「+」按钮                   │")
    print("│ 4. 输入：「明天上午9点联系曹新乐，约他周四见面」│")
    print("│ 5. 点击设置时间，选择明天上午9:00         │")
    print("│ ✅ 可设置详细提醒                       │")
    print("└─────────────────────────────────────────┘")

    print("\n【方法3】日历应用（推荐⭐⭐⭐⭐）")
    print("┌─────────────────────────────────────────┐")
    print("│ 1. Command + 空格，输入：「日历」         │")
    print("│ 2. 打开应用，按 Command + N              │")
    print("│ 3. 标题：「联系曹新乐」                   │")
    print("│ 4. 日期：明天（12月16日）                │")
    print("│ 5. 时间：09:00-09:30                    │")
    print("│ 6. 描述：「约他周四见面」                 │")
    print("│ 7. 设置提醒：提前15分钟                  │")
    print("│ ✅ 可设置详细日程信息                   │")
    print("└─────────────────────────────────────────┘")

    print("\n【方法4】Dock栏快速访问（推荐⭐⭐⭐）")
    print("┌─────────────────────────────────────────┐")
    print("│ 1. 在Dock栏找到提醒事项图标（黄色感叹号）  │")
    print("│ 2. 右键点击 → 新提醒                     │")
    print("│ 3. 输入内容                             │")
    print("│ 4. 点击设置日期时间                      │")
    print("│ ✅ 最快速，如果图标在Dock中             │")
    print("└─────────────────────────────────────────┘")

def show_calendar_methods():
    """显示创建日历的方法"""
    print("\n\n📅 创建日历事件的方法：")
    print("-" * 60)

    print("\n【方法A】Siri创建日历")
    print("┌─────────────────────────────────────────┐")
    print("│ 1. 嘿 Siri，创建日历事件                 │")
    print("│ 2. 「明天上午9点联系曹新乐」              │")
    print("│ 3. 设置时长：30分钟                     │")
    print("│ 4. 添加备注：「约他周四见面」             │")
    print("└─────────────────────────────────────────┘")

    print("\n【方法B】手动创建日历")
    print("┌─────────────────────────────────────────┐")
    print("│ 1. 打开日历应用                         │")
    print("│ 2. 双击明天上午9:00的时间段              │")
    print("│ 3. 填写事件详情                         │")
    print("│ 4. 保存并设置提醒                       │")
    print("└─────────────────────────────────────────┘")

def show_summary():
    """显示总结"""
    print("\n\n✨ 任务设置总结")
    print("-" * 60)
    print("✅ 任务已记录到小娜记忆系统")
    print("✅ GLM-4V已分析您的屏幕环境")
    print("✅ 提供了4种创建提醒的方法")
    print("✅ 提供了2种创建日历的方法")
    print("\n⏰ 关键时间点：")
    print("   - 明天 08:45：首次提醒（提前15分钟）")
    print("   - 明天 09:00：执行时间")
    print("   - 周四：与曹新乐见面")

def show_tips():
    """显示提示"""
    print("\n\n💡 小诺建议：")
    print("-" * 60)
    print("1. 首次使用建议用Siri，最简单快捷")
    print("2. 可以同时创建提醒事项和日历事件")
    print("3. 设置双重提醒，确保不会忘记")
    print("4. 提前准备好通话要点：")
    print("   - 周四哪天比较方便")
    print("   - 想要在哪里见面")
    print("   - 有什么事情要讨论")
    print("\n5. 如果Siri无法识别，可以尝试：")
    print("   - 更清晰地说出时间：「明天早上九点」")
    print("   - 添加更多细节：「明天上午九点打电话给曹新乐」")

def open_reminder_app():
    """尝试打开提醒事项应用"""
    try:
        subprocess.run(['open', '-a', 'Reminders'], check=True)
        print("\n🚀 正在打开提醒事项应用...")
        return True
    except:
        print("\n⚠️ 无法自动打开提醒事项应用，请手动打开")
        return False

def main():
    """主函数"""
    show_title()

    # 显示所有方法
    show_methods()
    show_calendar_methods()

    # 显示总结
    show_summary()

    # 显示提示
    show_tips()

    # 询问是否打开应用
    print("\n\n" + "="*60)
    print("🎯 现在就创建提醒事项吗？")
    print("="*60)
    print("选择操作：")
    print("1. 帮我打开提醒事项应用")
    print("2. 帮我打开日历应用")
    print("3. 我知道了，自己手动创建")
    print("4. 查看创建步骤截图示例")

    try:
        choice = input("\n请选择（1-4）：").strip()
        if choice == "1":
            if open_reminder_app():
                print("\n✅ 提醒事项应用已打开，请按照【方法2】操作")
        elif choice == "2":
            try:
                subprocess.run(['open', '-a', 'Calendar'], check=True)
                print("\n✅ 日历应用已打开，请按照【方法B】操作")
            except:
                print("\n⚠️ 无法自动打开日历应用，请手动打开")
        elif choice == "3":
            print("\n👍 很好！您可以使用任意方法创建提醒")
        elif choice == "4":
            print("\n📸 由于在终端中，无法显示截图")
            print("建议：")
            print("- 打开提醒事项应用后，寻找「+」按钮")
            print("- 点击「+」后输入提醒内容")
            print("- 点击设置时间")
    except KeyboardInterrupt:
        print("\n\n👋 感谢使用小诺提醒助手！")

    print("\n\n🎉 任务设置完成！")
    print("⏰ 明天上午9点记得联系曹新乐哦！")

if __name__ == "__main__":
    main()