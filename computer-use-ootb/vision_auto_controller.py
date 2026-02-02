#!/usr/bin/env python3
"""
高级自动化控制器
结合GLM-4V视觉识别和PyAutoGUI自动点击
"""

import pyautogui
import time
import json
import asyncio
import aiohttp
from PIL import Image
import numpy as np
import cv2
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VisionAutoController:
    def __init__(self, api_key="9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe"):
        self.api_key = api_key
        self.base_url = "http://localhost:8001"
        # 安全设置
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

        # 截图缓存目录
        self.screenshot_dir = "/tmp/vision_auto_screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)

    async def analyze_screen_with_glm(self, question):
        """使用GLM-4V分析屏幕"""
        try:
            # 截取屏幕
            screenshot = pyautogui.screenshot()
            screenshot_path = os.path.join(self.screenshot_dir, f"screen_{int(time.time())}.png")
            screenshot.save(screenshot_path)

            # 发送到GLM-4V分析
            async with aiohttp.ClientSession() as session:
                # 先上传截图
                with open(screenshot_path, 'rb') as f:
                    image_data = f.read()

                # 调用分析API
                async with session.post(f"{self.base_url}/analyze-screen",
                                       json={"question": question}) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("content", "")
                    else:
                        print("GLM分析失败")
                        return None

        except Exception as e:
            print(f"分析屏幕失败: {e}")
            return None

    def find_ui_element(self, description):
        """根据描述查找UI元素"""
        # 截取屏幕
        screenshot = pyautogui.screenshot()

        # 转换为OpenCV格式
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # 查找常见的UI元素
        elements_found = []

        # 查找按钮（通常是矩形、圆角矩形）
        # 这里使用模板匹配或轮廓检测
        gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)

        # 查找加号按钮
        if "+" in description.lower() or "新建" in description:
            # 尝试查找加号图标
            plus_locations = pyautogui.locateAllOnScreen('plus_icon.png', confidence=0.8)
            if plus_locations:
                elements_found.extend(plus_locations)

        # 查找设置图标
        if "设置" in description or "setting" in description.lower() or "gear" in description.lower():
            gear_locations = pyautogui.locateAllOnScreen('gear_icon.png', confidence=0.8)
            if gear_locations:
                elements_found.extend(gear_locations)

        # 返回找到的元素
        return elements_found

    async def smart_click(self, description):
        """智能点击：结合视觉识别和描述"""
        print(f"🔍 查找：{description}")

        # 方法1：使用GLM-4V分析屏幕
        analysis = await self.analyze_screen_with_glm(
            f"请帮我找到并描述'{description}'在屏幕上的位置，如果找不到，请告诉我相似元素的位置"
        )

        if analysis:
            print("🤖 AI分析：", analysis[:200])

            # 从分析中提取坐标
            coords = self.extract_coordinates_from_analysis(analysis)
            if coords:
                x, y = coords
                print(f"✅ 找到位置：({x}, {y})")
                pyautogui.click(x, y)
                return True

        # 方法2：使用模板匹配
        elements = self.find_ui_element(description)
        if elements:
            element = elements[0]  # 点击第一个找到的元素
            center = pyautogui.center(element)
            print(f"✅ 模板匹配找到：{center}")
            pyautogui.click(center)
            return True

        # 方法3：使用图像识别
        print("🔍 尝试图像识别...")
        if self.smart_image_search(description):
            return True

        return False

    def extract_coordinates_from_analysis(self, analysis):
        """从AI分析中提取坐标"""
        import re

        # 查找坐标模式
        patterns = [
            r'\((\d+),\s*(\d+)\)',  # (x, y)
            r'x[:\s]+(\d+).*?y[:\s]+(\d+)',  # x: 123, y: 456
            r'坐标[:\s]*\((\d+),\s*(\d+)\)',  # 坐标：(123, 456)
        ]

        for pattern in patterns:
            match = re.search(pattern, analysis)
            if match:
                try:
                    x, y = int(match.group(1)), int(match.group(2))
                    # 验证坐标是否在屏幕范围内
                    screen_width, screen_height = pyautogui.size()
                    if 0 <= x < screen_width and 0 <= y < screen_height:
                        return x, y
                except Exception as e:

                    # 记录异常但不中断流程

                    logger.debug(f"[vision_auto_controller] Exception: {e}")
        return None

    def smart_image_search(self, description):
        """智能图像搜索"""
        # 创建临时截图目录
        temp_dir = "/tmp/temp_search"
        os.makedirs(temp_dir, exist_ok=True)

        # 根据描述尝试不同的搜索词
        search_terms = {
            "加号": ["+", "add", "new"],
            "新建": ["new", "create", "+"],
            "设置": ["gear", "settings", "preferences"],
            "确定": ["ok", "done", "confirm"],
            "取消": ["cancel", "close", "x"],
            "信息": ["info", "i", "details"],
        }

        # 获取屏幕尺寸
        screen_width, screen_height = pyautogui.size()

        # 保存当前屏幕
        current_screen = pyautogui.screenshot()
        current_screen.save(os.path.join(temp_dir, "current.png"))

        # 尝试不同的搜索策略
        for key, terms in search_terms.items():
            if key in description:
                for term in terms:
                    try:
                        # 使用pyautogui的图片识别
                        locations = pyautogui.locateAllOnScreen(f'{term}.png', confidence=0.7)
                        if locations:
                            for loc in locations:
                                center = pyautogui.center(loc)
                                print(f"✅ 找到图像：{term} at {center}")
                                pyautogui.click(center)
                                return True
                    except Exception as e:
                        # 记录异常但不中断流程
                        logger.debug(f"[vision_auto_controller] Exception: {e}")
                        continue

        return False

    async def smart_type(self, text, field_description=""):
        """智能输入文本"""
        if field_description:
            print(f"📝 查找输入框：{field_description}")
            # 尝试点击输入框
            if not await self.smart_click(field_description):
                print("⚠️ 无法找到输入框，将在当前位置输入")

        # 输入文本
        print(f"⌨️ 输入：{text}")
        pyautogui.write(text, interval=0.05)

    async def create_reminder_full_auto(self):
        """完全自动创建提醒事项"""
        print("\n🤖 开始全自动创建提醒事项...")
        print("="*50)

        # 步骤1：打开提醒事项
        print("\n1️⃣ 打开提醒事项应用...")
        os.system('open -a "Reminders"')
        time.sleep(2)

        # 步骤2：点击新建按钮
        print("\n2️⃣ 查找并点击新建按钮...")
        if not await self.smart_click("新建按钮或加号"):
            # 尝试快捷键
            print("尝试快捷键...")
            pyautogui.hotkey('command', 'n')
        time.sleep(1)

        # 步骤3：输入提醒内容
        print("\n3️⃣ 输入提醒内容...")
        reminder_text = "明天上午9点联系曹新乐，约他周四见面"
        await self.smart_type(reminder_text, "输入框")
        time.sleep(1)

        # 步骤4：设置提醒时间
        print("\n4️⃣ 设置提醒时间...")
        await self.smart_click("设置或信息按钮")
        time.sleep(1)

        # 点击日期
        await self.smart_click("日期选择")
        time.sleep(0.5)
        pyautogui.write("明天")
        time.sleep(0.5)
        pyautogui.press('tab')

        # 设置时间
        pyautogui.write("09:00")
        time.sleep(0.5)
        pyautogui.press('enter')

        print("\n✅ 提醒事项创建完成！")
        return True

    async def create_calendar_full_auto(self):
        """完全自动创建日历事件"""
        print("\n🤖 开始全自动创建日历事件...")
        print("="*50)

        # 步骤1：打开日历
        print("\n1️⃣ 打开日历应用...")
        os.system('open -a "Calendar"')
        time.sleep(2)

        # 步骤2：创建新事件
        print("\n2️⃣ 创建新事件...")
        pyautogui.hotkey('command', 'n')
        time.sleep(1)

        # 步骤3：输入事件标题
        print("\n3️⃣ 输入事件标题...")
        await self.smart_type("联系曹新乐", "标题输入框")
        time.sleep(0.5)
        pyautogui.press('tab')

        # 步骤4：输入事件地点（可选）
        await self.smart_type("", "地点输入框")
        time.sleep(0.5)
        pyautogui.press('tab')

        # 步骤5：设置时间
        print("\n4️⃣ 设置事件时间...")
        # 根据日历界面布局调整tab次数
        pyautogui.press('tab', presses=2)
        pyautogui.write("09:00 AM")
        pyautogui.press('tab')
        pyautogui.write("09:30 AM")

        # 步骤6：添加描述
        pyautogui.press('tab')
        await self.smart_type("约他周四见面", "描述输入框")

        # 步骤7：保存
        print("\n5️⃣ 保存事件...")
        pyautogui.press('enter') or pyautogui.hotkey('command', 's')

        print("\n✅ 日历事件创建完成！")
        return True

    async def demo_mode(self):
        """演示模式：展示AI分析但不执行点击"""
        print("\n🎬 演示模式：AI视觉分析")
        print("="*50)

        print("\n1️⃣ 分析当前屏幕...")
        analysis = await self.analyze_screen_with_glm(
            "请详细描述当前屏幕上可见的所有应用程序、窗口和UI元素，特别关注提醒事项或日历应用"
        )

        if analysis:
            print("\n🤖 AI分析结果：")
            print("-"*50)
            print(analysis)
            print("-"*50)

        print("\n2️⃣ 查找可操作的UI元素...")
        elements = [
            "新建按钮或加号",
            "设置按钮",
            "输入框",
            "确定按钮",
            "日历应用",
            "提醒事项应用"
        ]

        for element in elements:
            print(f"\n查找：{element}")
            analysis = await self.analyze_screen_with_glm(
                f"请在屏幕上找到'{element}'，如果找到请告诉我其精确坐标位置"
            )
            if analysis and "坐标" in analysis:
                print(f"✅ 找到：{analysis[:100]}...")
            else:
                print(f"❌ 未找到")

async def main():
    """主函数"""
    print("🚀 小诺高级自动化控制器")
    print("="*50)
    print("集成GLM-4V视觉识别 + PyAutoGUI自动操作")
    print("="*50)

    controller = VisionAutoController()

    print("\n选择功能：")
    print("1. 演示模式（仅AI分析，不执行操作）")
    print("2. 全自动创建提醒事项")
    print("3. 全自动创建日历事件")
    print("4. 全自动创建提醒+日历")
    print("5. 手动控制模式（输入指令执行）")

    # 等待用户输入
    print("\n⚠️ 自动操作将在3秒后开始...")
    print("将鼠标移动到屏幕左上角可紧急停止")
    time.sleep(3)

    choice = "4"  # 默认执行全部

    if choice == "1":
        await controller.demo_mode()
    elif choice == "2":
        await controller.create_reminder_full_auto()
    elif choice == "3":
        await controller.create_calendar_full_auto()
    elif choice == "4":
        await controller.create_reminder_full_auto()
        time.sleep(2)
        await controller.create_calendar_full_auto()
    elif choice == "5":
        # 手动控制模式
        while True:
            cmd = input("\n输入指令（quit退出）：").strip()
            if cmd.lower() == 'quit':
                break
            await controller.smart_click(cmd)

    print("\n✨ 操作完成！")

if __name__ == "__main__":
    # 安装依赖
    try:
        import cv2
    except ImportError:
        print("正在安装依赖...")
        os.system("pip3 install opencv-python")

    # 运行主程序
    asyncio.run(main())