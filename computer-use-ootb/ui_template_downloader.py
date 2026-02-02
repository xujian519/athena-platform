#!/usr/bin/env python3
"""
UI元素模板下载器
下载和创建常见的UI元素图标
"""

import requests
import os
from PIL import Image, ImageDraw
import base64

def create_ui_templates():
    """创建基础UI模板"""
    template_dir = "/Users/xujian/Athena工作平台/computer-use-ootb/ui_templates"
    os.makedirs(template_dir, exist_ok=True)

    # 创建加号图标
    print("创建加号图标...")
    size = (32, 32)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 画加号
    draw.rectangle([12, 2, 20, 30], fill=(52, 199, 89))  # 绿色背景
    draw.rectangle([14, 14, 18, 18], fill=(255, 255, 255))  # 白色横条
    draw.rectangle([10, 16, 22, 18], fill=(255, 255, 255))  # 白色竖条

    img.save(os.path.join(template_dir, "plus_icon.png"))
    img.save(os.path.join(template_dir, "plus_button.png"))

    # 创建设置齿轮图标
    print("创建齿轮图标...")
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 简化的齿轮形状
    draw.ellipse([6, 6, 26, 26], outline=(100, 100, 100), width=2)
    draw.ellipse([14, 14, 18, 18], fill=(100, 100, 100))

    img.save(os.path.join(template_dir, "gear_icon.png"))
    img.save(os.path.join(template_dir, "settings_icon.png"))

    # 创建信息图标
    print("创建信息图标...")
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # i图标
    draw.ellipse([6, 6, 26, 26], outline=(0, 122, 255), width=2)
    draw.rectangle([15, 10, 17, 20], fill=(0, 122, 255))
    draw.rectangle([15, 8, 17, 10], fill=(0, 122, 255))

    img.save(os.path.join(template_dir, "info_icon.png"))
    img.save(os.path.join(template_dir, "info_button.png"))

    # 创建X按钮
    print("创建关闭图标...")
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # X形状
    draw.line([8, 8, 24, 24], fill=(255, 59, 48), width=3)
    draw.line([24, 8, 8, 24], fill=(255, 59, 48), width=3)

    img.save(os.path.join(template_dir, "close_icon.png"))
    img.save(os.path.join(template_dir, "x_button.png"))

    # 创建勾选图标
    print("创建勾选图标...")
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 勾形状
    draw.line([6, 16, 12, 22], fill=(52, 199, 89), width=3)
    draw.line([12, 22, 26, 8], fill=(52, 199, 89), width=3)

    img.save(os.path.join(template_dir, "check_icon.png"))
    img.save(os.path.join(template_dir, "done_button.png"))

    print("\n✅ UI模板创建完成！")
    print(f"模板保存在：{template_dir}")

def download_macos_icons():
    """下载macOS系统图标"""
    # 这里可以添加从网络下载官方图标的代码
    print("\n提示：可以从以下位置获取更多macOS系统图标：")
    print("1. /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/")
    print("2. Apple Human Interface Guidelines")
    print("3. SF Symbols（macOS内置）")

def create_screensaver_templates():
    """创建特定应用的截图模板"""
    print("\n创建应用特定模板...")

    # 提示用户创建模板
    print("\n要创建更准确的模板，请：")
    print("1. 打开提醒事项应用")
    print("2. 截取新建按钮的截图")
    print("3. 保存为 reminder_new_button.png")
    print("\n对日历应用重复相同操作")

if __name__ == "__main__":
    create_ui_templates()
    download_macos_icons()
    create_screensaver_templates()