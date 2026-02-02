#!/usr/bin/env python3
"""
快速演示所有自动化功能
"""

import subprocess
import datetime
import time

def demo_calendar_reminder():
    """演示日历和提醒自动化"""
    print("\n📅 演示：日历和提醒自动化")
    print("-" * 50)

    # 打开提醒事项
    print("1. 打开提醒事项应用...")
    subprocess.run(['open', '-a', 'Reminders'])
    time.sleep(2)

    # 使用AppleScript创建提醒
    script = '''
    tell application "Reminders"
        activate
        delay 1
        tell list "提醒"
            make new reminder with properties {name:"联系曹新乐，约他周四见面"}
        end tell
        display notification "提醒已创建" with title "✅ 成功"
    end tell
    '''
    subprocess.run(['osascript', '-e', script])

    # 打开日历
    print("\n2. 打开日历应用...")
    subprocess.run(['open', '-a', 'Calendar'])
    time.sleep(2)

    print("✅ 日历和提醒应用已打开")

def demo_notes_markdown():
    """演示备忘录Markdown自动化"""
    print("\n📝 演示：备忘录Markdown自动化")
    print("-" * 50)

    # 创建Markdown格式的笔记内容
    note_title = "项目会议纪要"
    note_content = f"""# {note_title}

**时间**：{datetime.datetime.now().strftime('%Y年%m月%d日')}
**参会人**：曹新乐、张三、李四

## 会议议程
1. 项目进展汇报
2. 下阶段工作安排
3. 资源协调

## 会议决议
- [ ] 完成需求文档
- [ ] 安排开发资源
- [ ] 制定测试计划

## 后续行动
- 联系曹新乐确认周四见面时间
- 准备项目提案
- 更新项目计划

---
记录人：小诺智能助手
"""

    # 打开备忘录应用
    print("1. 打开备忘录应用...")
    subprocess.run(['open', '-a', 'Notes'])
    time.sleep(2)

    # 使用AppleScript创建笔记
    # 转义引号
    note_title_escaped = note_title.replace('"', '\\"')
    note_content_escaped = note_content.replace('"', '\\"')

    script = f'''
    tell application "Notes"
        activate
        delay 1
        tell folder "备忘录"
            make new note with properties {{name:"{note_title_escaped}", body:"{note_content_escaped}"}}
        end tell
        display notification "Markdown笔记已创建" with title "✅ 成功"
    end tell
    '''
    subprocess.run(['osascript', '-e', script])

    print("✅ Markdown格式的备忘录已创建")

def demo_omni_automation():
    """演示Omni系列软件自动化"""
    print("\n🚀 演示：Omni系列软件自动化")
    print("-" * 50)

    # 检查Omni应用是否安装
    try:
        # 尝试打开OmniFocus
        print("1. 尝试打开OmniFocus...")
        result = subprocess.run(['open', '-a', 'OmniFocus'], capture_output=True)
        if result.returncode == 0:
            print("✅ OmniFocus已打开")
            # 创建任务
            script = '''
            tell application "OmniFocus"
                activate
                delay 1
                tell default document
                    make new inbox task with properties {name:"联系曹新乐 - 约周四见面", note:"重要事项，需要跟进"}
                end tell
                display notification "OmniFocus任务已创建" with title "✅ 成功"
            end tell
            '''
            subprocess.run(['osascript', '-e', script])
        else:
            print("ℹ️ OmniFocus未安装")
    except:
        print("ℹ️ OmniFocus未安装")

    time.sleep(1)

    # 检查其他Omni应用
    omni_apps = [
        ("OmniGraffle", "图表设计"),
        ("OmniOutliner", "大纲笔记"),
        ("OmniPlan", "项目管理")
    ]

    for app, desc in omni_apps:
        try:
            result = subprocess.run(['open', '-a', app], capture_output=True)
            if result.returncode == 0:
                print(f"✅ {app}已打开 - {desc}")
            else:
                print(f"ℹ️ {app}未安装")
        except:
            print(f"ℹ️ {app}未安装")

def demo_integration():
    """演示集成功能"""
    print("\n🔄 演示：系统集成功能")
    print("-" * 50)

    # 显示通知
    print("1. 显示系统通知...")
    subprocess.run(['osascript', '-e', '''
        display notification "小诺自动化系统已准备就绪" with title "🤖 智能助手" subtitle "所有功能已集成"
    '''])

    # 创建系统语音提醒
    print("2. 创建语音提醒...")
    subprocess.run(['say', '小诺提醒您，记得联系曹新乐'])

    print("\n✨ 集成演示完成！")

def show_features():
    """显示所有功能"""
    print("\n🎯 小诺高级自动化系统功能清单")
    print("=" * 60)

    features = [
        ("📅 日历自动化", [
            "智能创建日历事件",
            "批量导入日程",
            "自动设置提醒",
            "模板管理"
        ]),
        ("📝 提醒事项自动化", [
            "快速创建提醒",
            "智能分类管理",
            "批量操作",
            "优先级设置"
        ]),
        ("📋 备忘录Markdown", [
            "Markdown格式支持",
            "模板化笔记",
            "会议纪要生成",
            "项目文档管理"
        ]),
        ("🚀 Omni系列集成", [
            "OmniFocus任务管理",
            "OmniGraffle图表",
            "OmniOutliner大纲",
            "OmniPlan项目计划"
        ]),
        ("🔄 工作流自动化", [
            "会议包创建",
            "项目工作流",
            "每日工作流",
            "自定义工作流"
        ]),
        ("💾 数据管理", [
            "数据导出",
            "备份恢复",
            "同步集成",
            "历史记录"
        ])
    ]

    for category, items in features:
        print(f"\n{category}:")
        for item in items:
            print(f"  ✅ {item}")

    print("\n" + "=" * 60)
    print("🎉 自动化系统开发完成！")

def main():
    """主函数"""
    import time

    print("🎯 小诺高级自动化系统 - 快速演示")
    print("=" * 60)

    print("\n正在运行演示...\n")

    # 演示1：日历和提醒
    demo_calendar_reminder()

    time.sleep(2)

    # 演示2：备忘录
    demo_notes_markdown()

    time.sleep(2)

    # 演示3：Omni系列
    demo_omni_automation()

    time.sleep(1)

    # 演示4：集成功能
    demo_integration()

    # 显示功能清单
    show_features()

    print("\n💡 使用提示：")
    print("1. 所有应用已经打开，可以直接查看创建的内容")
    print("2. 可以运行automation_center.py使用完整功能")
    print("3. 支持Siri语音：'提醒我明天上午9点联系曹新乐'")
    print("4. 支持自定义工作流和模板")

if __name__ == "__main__":
    main()