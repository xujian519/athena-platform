#!/usr/bin/env python3
"""
小诺自动化控制中心
统一管理所有自动化功能
"""

import sys
import os
import json
import datetime
from typing import Dict, List, Optional

# 导入各模块
from calendar_reminder_pro import CalendarReminderPro
from notes_markdown_automation import NotesMarkdownAutomation
from omni_automation import OmniAutomation

class AutomationCenter:
    def __init__(self):
        self.cr_pro = CalendarReminderPro()
        self.nma = NotesMarkdownAutomation()
        self.omni = OmniAutomation()

        # 配置文件
        self.config_file = "/Users/xujian/Athena工作平台/computer-use-ootb/automation_config.json"
        self.load_config()

    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "default_settings": {
                    "calendar": "Home",
                    "reminder_list": "提醒",
                    "notes_folder": "备忘录",
                    "omni_context": "办公"
                },
                "workflows": {}
            }

    def save_config(self):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def quick_create_reminder(self, title: str, content: str = ""):
        """快速创建提醒事项"""
        return self.cr_pro.create_smart_reminder(
            title=title,
            content=content,
            list_name=self.config["default_settings"]["reminder_list"]
        )

    def quick_create_calendar(self, title: str, duration: int = 30):
        """快速创建日历事件"""
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y年%m月%d日")
        return self.cr_pro.create_smart_calendar_event(
            title=title,
            start_date=f"{tomorrow} 09:00:00",
            duration=duration,
            calendar_name=self.config["default_settings"]["calendar"]
        )

    def create_meeting_package(self, title: str, attendees: List[str],
                              agenda: Optional[List[str] = None, date: str = None):
        """创建完整的会议包（提醒、日历、笔记）"""
        print(f"\n📦 创建会议包：{title}")
        print("-" * 50)

        # 1. 创建日历事件
        print("1. 创建日历事件...")
        if date:
            start_date = f"{date} 09:00:00"
        else:
            tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y年%m月%d日")
            start_date = f"{tomorrow} 09:00:00"

        self.cr_pro.create_smart_calendar_event(
            title=f"会议：{title}",
            description=f"参会人：{', '.join(attendees)}\n议程：\n" + "\n".join(f"- {item}" for item in (agenda or [])),
            start_date=start_date,
            duration=60,
            calendar_name="工作"
        )

        # 2. 创建提醒事项
        print("2. 创建提醒事项...")
        self.cr_pro.create_meeting_reminder(
            title=title,
            participant=", ".join(attendees),
            meeting_type="会议",
            date=date or "明天",
            agenda=agenda
        )

        # 3. 创建会议笔记
        print("3. 创建会议笔记...")
        self.nma.create_meeting_notes(
            title=title,
            attendees=attendees,
            agenda=agenda,
            location="待定"
        )

        # 4. 创建OmniFocus任务（准备任务）
        print("4. 创建准备任务...")
        self.omni.create_omnifocus_task(
            name=f"准备会议：{title}",
            context="会议准备",
            note=f"参会人：{', '.join(attendees)}\n议程：\n" + "\n".join(f"- {item}" for item in (agenda or [])),
            flagged=True
        )

        print("\n✅ 会议包创建完成！")

    def create_project_workflow(self, project_name: str, description: str,
                              milestones: Optional[List[str] = None):
        """创建完整的项目工作流"""
        print(f"\n🚀 创建项目工作流：{project_name}")
        print("-" * 50)

        milestones = milestones or []

        # 1. 创建项目笔记（备忘录）
        print("1. 创建项目笔记...")
        self.nma.create_project_note(
            project_name=project_name,
            description=description,
            milestones=milestones
        )

        # 2. 创建OmniFocus项目
        print("2. 创建OmniFocus项目...")
        tasks = []
        for milestone in milestones:
            tasks.append({
                "name": milestone,
                "context": "项目"
            })
        tasks.append({
            "name": "项目验收",
            "context": "项目",
            "note": "确认所有目标达成"
        })

        self.omni.create_omnifocus_project(
            name=project_name,
            context="项目",
            tasks=tasks
        )

        # 3. 创建项目里程碑日历
        print("3. 创建里程碑日历...")
        for i, milestone in enumerate(milestones, 1):
            date = (datetime.datetime.now() + datetime.timedelta(days=i*7)).strftime("%Y年%m月%d日")
            self.cr_pro.create_smart_calendar_event(
                title=f"[里程碑] {milestone}",
                description=f"项目：{project_name}",
                start_date=f"{date} 10:00:00",
                duration=30,
                calendar_name="项目"
            )

        # 4. 创建项目跟踪提醒
        print("4. 创建跟踪提醒...")
        self.cr_pro.create_recurring_reminder(
            title=f"项目跟踪：{project_name}",
            frequency="weekly",
            content="检查项目进度\n更新任务状态\n同步团队"
        )

        print("\n✅ 项目工作流创建完成！")

    def create_daily_workflow(self, completed_tasks: Optional[List[str] = None,
                            tomorrow_tasks: Optional[List[str] = None,
                            ideas: Optional[List[str] = None):
        """创建每日工作流"""
        print("\n📅 创建每日工作流")
        print("-" * 50)

        completed_tasks = completed_tasks or []
        tomorrow_tasks = tomorrow_tasks or []
        ideas = ideas or []

        # 1. 创建每日日志
        print("1. 创建每日日志...")
        self.nma.create_daily_log(
            completed=completed_tasks,
            tomorrow_plan=tomorrow_tasks
        )

        # 2. 创建明日OmniFocus任务
        print("2. 创建明日任务...")
        for task in tomorrow_tasks:
            self.omni.create_omnifocus_task(
                name=task,
                context="明日待办"
            )

        # 3. 记录想法
        print("3. 记录想法...")
        for idea in ideas:
            self.nma.capture_idea(
                title=idea[:30] + "...",
                concept=idea,
                source="日常思考",
                tags=["想法", "待整理"]
            )

        # 4. 创建明日日程汇总
        print("4. 创建明日日程汇总...")
        self.cr_pro.create_daily_agenda()

        print("\n✅ 每日工作流创建完成！")

    def export_all_data(self):
        """导出所有数据"""
        print("\n📤 导出所有数据")
        print("-" * 50)

        # 1. 导出OmniFocus数据
        print("1. 导出OmniFocus数据...")
        self.omni.export_omnifocus_to_json()

        # 2. 导出备忘录
        print("2. 导出备忘录...")
        self.nma.export_notes_to_markdown()

        print("\n✅ 数据导出完成！")

    def save_workflow(self, name: str, workflow_type: str, params: Dict):
        """保存工作流"""
        if "workflows" not in self.config:
            self.config["workflows"] = {}

        self.config["workflows"][name] = {
            "type": workflow_type,
            "params": params,
            "created_at": datetime.datetime.now().isoformat()
        }
        self.save_config()
        print(f"✅ 工作流已保存：{name}")

    def run_workflow(self, name: str):
        """运行保存的工作流"""
        if name not in self.config.get("workflows", {}):
            print(f"❌ 工作流不存在：{name}")
            return

        workflow = self.config["workflows"][name]
        workflow_type = workflow["type"]
        params = workflow["params"]

        print(f"\n🔄 运行工作流：{name}")
        print("-" * 50)

        if workflow_type == "meeting":
            self.create_meeting_package(**params)
        elif workflow_type == "project":
            self.create_project_workflow(**params)
        elif workflow_type == "daily":
            self.create_daily_workflow(**params)

    def show_status(self):
        """显示系统状态"""
        print("\n📊 系统状态")
        print("=" * 50)

        # 显示配置
        print("\n🔧 默认配置：")
        for key, value in self.config["default_settings"].items():
            print(f"  {key}: {value}")

        # 显示工作流
        print("\n🔄 已保存的工作流：")
        for name, workflow in self.config.get("workflows", {}).items():
            print(f"  - {name} ({workflow['type']})")

        # 显示今日任务
        print("\n📋 今日任务概览：")
        reminders = self.cr_pro.get_reminders_for_date()
        events = self.cr_pro.get_calendar_events_for_date()

        if reminders:
            print("\n提醒事项：")
            for reminder in reminders[:5]:  # 只显示前5个
                print(f"  ✓ {reminder['title']}")

        if events:
            print("\n日历事件：")
            for event in events[:5]:
                print(f"  📅 {event['title']}")

def main():
    """主函数"""
    print("🎯 小诺自动化控制中心")
    print("=" * 60)

    center = AutomationCenter()

    print("\n选择功能：")
    print("1. 快速创建提醒事项")
    print("2. 快速创建日历事件")
    print("3. 创建会议包")
    print("4. 创建项目工作流")
    print("5. 创建每日工作流")
    print("6. 导出所有数据")
    print("7. 保存工作流")
    print("8. 运行工作流")
    print("9. 查看系统状态")
    print("0. 运行所有演示")

    choice = input("\n请选择（0-9）：").strip()

    if choice == "1":
        title = input("提醒标题：").strip()
        content = input("备注（可选）：").strip()
        center.quick_create_reminder(title, content)

    elif choice == "2":
        title = input("事件标题：").strip()
        duration = input("时长（分钟，默认30）：").strip() or "30"
        center.quick_create_calendar(title, int(duration))

    elif choice == "3":
        title = input("会议标题：").strip()
        attendees = input("参会人（逗号分隔）：").strip().split(",")
        agenda_input = input("议程（每行一个）：").strip()
        agenda = agenda_input.split("\n") if agenda_input else []
        date = input("日期（如：明天或2024-12-16，可选）：").strip() or None
        center.create_meeting_package(title, attendees, agenda, date)

    elif choice == "4":
        project_name = input("项目名称：").strip()
        description = input("项目描述：").strip()
        milestones_input = input("里程碑（每行一个）：").strip()
        milestones = milestones_input.split("\n") if milestones_input else []
        center.create_project_workflow(project_name, description, milestones)

    elif choice == "5":
        completed_input = input("今日完成（每行一个）：").strip()
        completed = completed_input.split("\n") if completed_input else []
        tomorrow_input = input("明日计划（每行一个）：").strip()
        tomorrow = tomorrow_input.split("\n") if tomorrow_input else []
        ideas_input = input("想法记录（每行一个）：").strip()
        ideas = ideas_input.split("\n") if ideas_input else []
        center.create_daily_workflow(completed, tomorrow, ideas)

    elif choice == "6":
        center.export_all_data()

    elif choice == "7":
        name = input("工作流名称：").strip()
        print("工作流类型：meeting/project/daily")
        workflow_type = input("类型：").strip()
        # 这里简化处理，实际需要更复杂的参数输入
        params = {}
        center.save_workflow(name, workflow_type, params)

    elif choice == "8":
        center.show_status()
        name = input("工作流名称：").strip()
        center.run_workflow(name)

    elif choice == "9":
        center.show_status()

    elif choice == "0":
        # 运行所有演示
        print("\n🎬 运行所有演示")
        print("-" * 50)

        # 演示1：会议包
        center.create_meeting_package(
            title="项目启动会",
            attendees=["张三", "李四", "王五"],
            agenda=["项目介绍", "分工安排", "时间计划"]
        )

        # 演示2：项目工作流
        center.create_project_workflow(
            project_name="AI助手升级",
            description="升级小诺助手的自动化功能",
            milestones=["需求分析", "系统设计", "开发实现", "测试优化"]
        )

        # 演示3：每日工作流
        center.create_daily_workflow(
            completed_tasks=["完成自动化脚本", "优化用户体验"],
            tomorrow_tasks=["测试新功能", "编写文档"],
            ideas=["添加语音控制", "集成更多应用"]
        )

        center.show_status()

    print("\n✨ 操作完成！")

if __name__ == "__main__":
    main()