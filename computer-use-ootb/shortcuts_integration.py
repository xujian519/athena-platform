#!/usr/bin/env python3
"""
Shortcuts应用集成
创建和管理macOS快捷指令
"""

import subprocess
import json
import plistlib
import os
from datetime import datetime, timedelta

def create_shortcut_plist():
    """创建创建提醒的快捷指令plist"""

    shortcut_data = {
        'WFWorkflowMinimumClientVersionString': '900',
        'WFWorkflowMinimumClientVersion': 900,
        'WFWorkflowIcon': {
            'WFWorkflowIconStartColor': 1996589439,
            'WFWorkflowIconGlyphNumber': 61440,
        },
        'WFWorkflowInputContentItemClasses': [],
        'WFWorkflowActions': [
            {
                'WFWorkflowActionIdentifier': 'is.workflow.actions.createtodo',
                'WFWorkflowActionParameters': {
                    'WFTitle': '联系曹新乐，约他周四见面',
                    'WFDefaultPriority': '0',
                    'WFDefaultFlag': False,
                },
            },
            {
                'WFWorkflowActionIdentifier': 'is.workflow.actions.date',
                'WFWorkflowActionParameters': {
                    'WFDateActionMode': 'Specify',
                    'WFDateActionDate': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT09:00:00'),
                },
            },
        ],
        'WFWorkflowClientVersion': '2305.0.3',
        'WFWorkflowTypes': ['NCWidget', 'WatchKit', 'ActionExtension'],
        'WFWorkflowImportQuestions': [],
        'WFWorkflowHasShortcutInputVariables': False,
    }

    # 创建快捷指令目录
    shortcut_dir = os.path.expanduser('~/Library/Shortcuts')
    os.makedirs(shortcut_dir, exist_ok=True)

    # 保存plist文件
    plist_path = os.path.join(shortcut_dir, '小诺提醒.workflow/Contents/document.wflow')
    os.makedirs(os.path.dirname(plist_path), exist_ok=True)

    with open(plist_path, 'wb') as f:
        plistlib.dump(shortcut_data, f)

    print(f"✅ 快捷指令已创建：{plist_path}")
    return plist_path

def create_calendar_shortcut():
    """创建日历快捷指令"""

    shortcut_data = {
        'WFWorkflowMinimumClientVersionString': '900',
        'WFWorkflowMinimumClientVersion': 900,
        'WFWorkflowIcon': {
            'WFWorkflowIconStartColor': 2853292031,
            'WFWorkflowIconGlyphNumber': 61440,
        },
        'WFWorkflowActions': [
            {
                'WFWorkflowActionIdentifier': 'is.workflow.actions.createcalendar',
                'WFWorkflowActionParameters': {
                    'WFEventTitle': '联系曹新乐',
                    'WFEventNotes': '约他周四见面',
                    'WFEventAllDay': False,
                    'WFEventStartDate': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT09:00:00'),
                    'WFEventEndDate': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT09:30:00'),
                },
            },
        ],
        'WFWorkflowClientVersion': '2305.0.3',
    }

    shortcut_dir = os.path.expanduser('~/Library/Shortcuts')
    plist_path = os.path.join(shortcut_dir, '小诺日历.workflow/Contents/document.wflow')
    os.makedirs(os.path.dirname(plist_path), exist_ok=True)

    with open(plist_path, 'wb') as f:
        plistlib.dump(shortcut_data, f)

    print(f"✅ 日历快捷指令已创建：{plist_path}")
    return plist_path

def run_shortcut(shortcut_name):
    """运行指定的快捷指令"""
    try:
        script = f'tell application "Shortcuts Events" to run shortcut "{shortcut_name}"'
        result = subprocess.run(['osascript', '-e', script],
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def setup_shortcuts():
    """设置快捷指令"""
    print("🔧 设置Shortcuts自动化")
    print("=" * 50)

    # 创建快捷指令
    print("\n1. 创建提醒快捷指令...")
    try:
        create_shortcut_plist()
    except Exception as e:
        print(f"❌ 创建提醒快捷指令失败：{e}")

    print("\n2. 创建日历快捷指令...")
    try:
        create_calendar_shortcut()
    except Exception as e:
        print(f"❌ 创建日历快捷指令失败：{e}")

    print("\n3. 测试快捷指令...")

    if run_shortcut("小诺提醒"):
        print("✅ 提醒快捷指令运行成功")
    else:
        print("ℹ️ 提醒快捷指令需要手动添加到Shortcuts应用")

    if run_shortcut("小诺日历"):
        print("✅ 日历快捷指令运行成功")
    else:
        print("ℹ️ 日历快捷指令需要手动添加到Shortcuts应用")

    print("\n📋 使用说明：")
    print("1. 打开Shortcuts应用")
    print("2. 查找名为'小诺提醒'和'小诺日历'的快捷指令")
    print("3. 点击运行或设置语音触发")
    print("4. 可以添加到Siri短语中")

def create_siri_phrase():
    """创建Siri触发短语"""
    print("\n🗣️ 设置Siri语音触发")
    print("-" * 50)
    print("请按以下步骤设置Siri触发：")
    print("")
    print("1. 打开Shortcuts应用")
    print("2. 选择'小诺提醒'快捷指令")
    print("3. 点击右上角的齿轮图标")
    print("4. 点击'添加到Siri'")
    print("5. 录入语音短语，例如：'小诺提醒'或'联系曹新乐'")
    print("")
    print("设置后，您可以对Siri说：'小诺提醒'来创建提醒")

def main():
    """主函数"""
    print("⚡ Shortcuts自动化集成")
    print("=" * 50)

    # 设置快捷指令
    setup_shortcuts()

    # 创建Siri短语指导
    create_siri_phrase()

    print("\n✨ 设置完成！")
    print("现在您可以通过以下方式创建提醒：")
    print("1. 直接运行Shortcuts应用中的快捷指令")
    print("2. 使用Siri语音触发（需要先设置）")
    print("3. 在小娜中调用快捷指令")

if __name__ == "__main__":
    main()