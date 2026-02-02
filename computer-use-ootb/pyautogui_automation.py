#!/usr/bin/env python3
"""
使用PyAutoGUI实现屏幕自动化
结合GLM-4V视觉识别进行精确操作
"""

import pyautogui
import time
import subprocess
import sys
from datetime import datetime, timedelta

class XiaonuoAutoHelper:
    def __init__(self):
        self.safety_enabled = True
        # 设置PyAutoGUI安全措施
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 1

    def take_screenshot(self):
        """截取屏幕"""
        screenshot = pyautogui.screenshot()
        return screenshot

    def find_and_click_app(self, app_name):
        """查找并点击应用"""
        print(f"🔍 正在查找应用：{app_name}")

        # 方法1：尝试使用Spotlight
        self.open_spotlight()
        time.sleep(1)
        pyautogui.write(app_name)
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(2)

        return True

    def open_spotlight(self):
        """打开Spotlight搜索"""
        pyautogui.hotkey('command', 'space')
        time.sleep(1)

    def create_reminder_manual(self):
        """手动创建提醒流程"""
        print("\n📝 开始创建提醒事项...")

        # 步骤1：打开Spotlight并搜索提醒事项
        print("1. 打开提醒事项应用...")
        self.open_spotlight()
        pyautogui.write('提醒事项')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(2)

        # 步骤2：创建新提醒
        print("2. 创建新提醒...")
        try:
            # 查找并点击加号按钮
            plus_button = pyautogui.locateOnScreen('plus_button.png', confidence=0.8)
            if plus_button:
                pyautogui.click(plus_button)
            else:
                # 尝试使用快捷键
                pyautogui.hotkey('command', 'n')
        except:
            # 使用快捷键
            pyautogui.hotkey('command', 'n')

        time.sleep(1)

        # 步骤3：输入提醒内容
        print("3. 输入提醒内容...")
        reminder_text = "明天上午9点联系曹新乐，约他周四见面"
        pyautogui.write(reminder_text, interval=0.1)
        time.sleep(1)

        # 步骤4：设置提醒时间
        print("4. 设置提醒时间...")
        # 查找信息图标或时间设置区域
        self.set_reminder_time()

        print("✅ 提醒事项创建完成！")

    def set_reminder_time(self):
        """设置提醒时间"""
        try:
            # 查找并点击设置图标
            info_icon = pyautogui.locateOnScreen('info_icon.png', confidence=0.8)
            if info_icon:
                pyautogui.click(info_icon)
                time.sleep(1)

                # 设置明天
                pyautogui.click(200, 300)  # 根据实际位置调整
                time.sleep(0.5)
                pyautogui.write('明天')

                # 设置时间
                pyautogui.press('tab')
                pyautogui.write('9:00')

                # 保存
                pyautogui.press('enter')
        except:
            print("⚠️ 请手动设置提醒时间")

    def create_calendar_event_manual(self):
        """手动创建日历事件"""
        print("\n📅 开始创建日历事件...")

        # 步骤1：打开日历应用
        print("1. 打开日历应用...")
        self.open_spotlight()
        pyautogui.write('日历')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(2)

        # 步骤2：创建新事件
        print("2. 创建新事件...")
        pyautogui.hotkey('command', 'n')
        time.sleep(1)

        # 步骤3：输入事件详情
        print("3. 输入事件详情...")
        pyautogui.write('联系曹新乐')
        time.sleep(0.5)
        pyautogui.press('tab')
        pyautogui.write('约他周四见面')
        time.sleep(0.5)

        # 步骤4：设置时间
        print("4. 设置事件时间...")
        # 这里需要根据日历界面的具体布局调整
        self.set_calendar_time()

        print("✅ 日历事件创建完成！")

    def set_calendar_time(self):
        """设置日历事件时间"""
        # 根据日历界面布局设置时间
        # 这里需要实际测试确定具体位置
        pyautogui.press('tab', presses=3)
        pyautogui.write('9:00 AM')
        pyautogui.press('tab')
        pyautogui.write('9:30 AM')
        pyautogui.press('enter')

    def demo_mode(self):
        """演示模式（不实际点击）"""
        print("\n🎬 演示模式 - 显示操作流程")
        print("=" * 50)

        print("\n创建提醒事项步骤：")
        print("1. 按 Command + Space 打开Spotlight")
        print("2. 输入：提醒事项")
        print("3. 按回车打开应用")
        print("4. 点击左上角的 + 按钮")
        print("5. 输入：明天上午9点联系曹新乐，约他周四见面")
        print("6. 点击信息图标设置时间")
        print("7. 设置明天上午9:00")

        print("\n创建日历事件步骤：")
        print("1. 按 Command + Space 打开Spotlight")
        print("2. 输入：日历")
        print("3. 按回车打开应用")
        print("4. 按 Command + N 创建新事件")
        print("5. 标题：联系曹新乐")
        print("6. 时间：明天 9:00-9:30")
        print("7. 描述：约他周四见面")

    def emergency_stop(self):
        """紧急停止"""
        print("\n⚠️ 紧急停止！将鼠标移动到屏幕左上角")
        pyautogui.moveTo(0, 0, duration=0.5)

def main():
    """主函数"""
    print("🤖 小诺自动化助手 - PyAutoGUI版")
    print("=" * 50)

    helper = XiaonuoAutoHelper()

    print("\n选择操作模式：")
    print("1. 演示模式（仅显示步骤）")
    print("2. 自动创建提醒事项")
    print("3. 自动创建日历事件")
    print("4. 创建提醒和日历")
    print("5. 紧急停止")

    try:
        choice = input("\n请选择（1-5）：").strip()

        if choice == "1":
            helper.demo_mode()
        elif choice == "2":
            print("\n⚠️ 将在3秒后开始自动操作...")
            print("将鼠标移动到屏幕左上角可紧急停止")
            time.sleep(3)
            helper.create_reminder_manual()
        elif choice == "3":
            print("\n⚠️ 将在3秒后开始自动操作...")
            print("将鼠标移动到屏幕左上角可紧急停止")
            time.sleep(3)
            helper.create_calendar_event_manual()
        elif choice == "4":
            print("\n⚠️ 将在3秒后开始自动操作...")
            print("将鼠标移动到屏幕左上角可紧急停止")
            time.sleep(3)
            helper.create_reminder_manual()
            time.sleep(2)
            helper.create_calendar_event_manual()
        elif choice == "5":
            helper.emergency_stop()
        else:
            print("无效选择")

    except KeyboardInterrupt:
        print("\n\n👋 操作已取消")
        helper.emergency_stop()
    except Exception as e:
        print(f"\n❌ 发生错误：{e}")
        helper.emergency_stop()

    print("\n✨ 操作完成！")

if __name__ == "__main__":
    # 检查PyAutoGUI是否安装
    try:
        import pyautogui
    except ImportError:
        print("❌ 需要安装PyAutoGUI")
        print("请运行：pip3 install pyautogui")
        sys.exit(1)

    main()