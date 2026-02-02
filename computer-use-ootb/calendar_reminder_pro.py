#!/usr/bin/env python3
"""
专业版日历和提醒事项自动化系统
支持智能创建、批量操作和模板管理
"""

import subprocess
import datetime
import json
import os
from typing import Dict, List, Optional
import time

class CalendarReminderPro:
    def __init__(self):
        self.templates_file = "/Users/xujian/Athena工作平台/computer-use-ootb/task_templates.json"
        self.history_file = "/Users/xujian/Athena工作平台/computer-use-ootb/task_history.json"
        self.load_data()

    def load_data(self):
        """加载模板和历史数据"""
        self.templates = self.load_json(self.templates_file, {})
        self.history = self.load_json(self.history_file, [])

    def load_json(self, file_path, default):
        """加载JSON文件"""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default
        return default

    def save_json(self, file_path, data):
        """保存JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_smart_reminder(self, title: str, content: str = "",
                             due_date: str = None, priority: str = "medium",
                             list_name: str = "提醒", tags: Optional[List[str] = None):
        """创建智能提醒事项"""
        # 设置默认日期
        if not due_date:
            tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
            due_date = tomorrow.strftime("%Y年%m月%d日")

        # 构建AppleScript
        script = f'''
        tell application "Reminders"
            activate
            delay 1

            -- 获取或创建指定列表
            try
                set targetList to list "{list_name}"
            on error
                set targetList to make new list with properties {{name:"{list_name}"}}
            end try

            -- 创建提醒
            tell targetList
                set newReminder to make new reminder with properties {{_
                    name:"{title}",_
                    priority:{self._get_priority_value(priority)}_
                }}

                -- 设置内容
                if "{content}" is not "" then
                    set body of newReminder to "{content}"
                end if

                -- 设置截止日期
                try
                    set due date of newReminder to date "{due_date}"
                end try

                -- 设置提醒时间
                try
                    set remind me date of newReminder to date "{due_date} 08:45:00"
                end try
            end tell

            display notification "提醒已创建：{title}" with title "✅ 小诺提醒"
        end tell
        '''

        # 执行脚本
        success, output, error = self._run_applescript(script)

        if success:
            # 记录历史
            task_record = {
                "type": "reminder",
                "title": title,
                "content": content,
                "due_date": due_date,
                "list_name": list_name,
                "priority": priority,
                "created_at": datetime.datetime.now().isoformat(),
                "tags": tags or []
            }
            self.history.append(task_record)
            self.save_json(self.history_file, self.history)

            print(f"✅ 提醒已创建：{title}")
            print(f"   日期：{due_date}")
            print(f"   列表：{list_name}")
            return True
        else:
            print(f"❌ 创建提醒失败：{error}")
            return False

    def create_smart_calendar_event(self, title: str, description: str = "",
                                  start_date: str = None, duration: int = 30,
                                  location: str = "", calendar_name: str = "Home",
                                  alert_minutes: int = 15, all_day: bool = False):
        """创建智能日历事件"""
        # 设置默认日期
        if not start_date:
            tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
            start_date = tomorrow.strftime("%Y年%m月%d日") + " 09:00:00"

        # 计算结束时间
        if not all_day:
            start_dt = datetime.datetime.strptime(start_date, "%Y年%m月%d日 %H:%M:%S")
            end_dt = start_dt + datetime.timedelta(minutes=duration)
            end_date = end_dt.strftime("%Y年%m月%d日 %H:%M:%S")
        else:
            end_date = start_date

        # 构建AppleScript
        script = f'''
        tell application "Calendar"
            activate
            delay 1

            -- 获取指定日历
            try
                set targetCal to calendar "{calendar_name}"
            on error
                set targetCal to calendar 1
            end try

            -- 创建事件
            tell targetCal
                set newEvent to make new event with properties {{_
                    summary:"{title}",_
                    start date:date "{start_date}",_
                    end date:date "{end_date}",_
                    location:"{location}",_
                    description:"{description}",_
                    allday event:{str(all_day).lower()}_
                }}

                -- 添加提醒
                if {alert_minutes} > 0 then
                    tell newEvent
                        make new sound alarm at (start date - {alert_minutes} * minutes)
                    end tell
                end if
            end tell

            display notification "日历事件已创建：{title}" with title "📅 小诺日历"
        end tell
        '''

        # 执行脚本
        success, output, error = self._run_applescript(script)

        if success:
            # 记录历史
            task_record = {
                "type": "calendar",
                "title": title,
                "description": description,
                "start_date": start_date,
                "duration": duration,
                "location": location,
                "calendar": calendar_name,
                "alert_minutes": alert_minutes,
                "all_day": all_day,
                "created_at": datetime.datetime.now().isoformat()
            }
            self.history.append(task_record)
            self.save_json(self.history_file, self.history)

            print(f"✅ 日历事件已创建：{title}")
            print(f"   时间：{start_date}")
            if not all_day:
                print(f"   时长：{duration}分钟")
            print(f"   日历：{calendar_name}")
            return True
        else:
            print(f"❌ 创建日历事件失败：{error}")
            return False

    def create_meeting_reminder(self, title: str, participant: str,
                               meeting_type: str = "电话", date: str = None,
                               agenda: Optional[List[str] = None):
        """创建会议专用提醒"""
        # 构建会议提醒内容
        content = f"会议类型：{meeting_type}\n参会人：{participant}\n"
        if agenda:
            content += "议程：\n" + "\n".join(f"- {item}" for item in agenda)

        # 创建提醒
        self.create_smart_reminder(
            title=f"{meeting_type}会议：{title}",
            content=content,
            due_date=date,
            list_name="会议",
            tags=["会议", meeting_type]
        )

        # 如果是具体时间，同时创建日历事件
        if date and ":" in date:
            self.create_smart_calendar_event(
                title=f"{meeting_type}：{title}",
                description=f"参会人：{participant}\n" + "\n".join(agenda or []),
                start_date=f"{date} 09:00:00",
                duration=30,
                calendar_name="工作",
                alert_minutes=15
            )

    def create_recurring_reminder(self, title: str, frequency: str,
                                content: str = "", start_date: str = None):
        """创建重复提醒（通过模板批量创建）"""
        print(f"📅 创建重复提醒：{title}（{frequency}）")

        # 根据频率创建多个提醒
        if frequency == "daily":
            for i in range(7):  # 创建一周的提醒
                date = (datetime.datetime.now() + datetime.timedelta(days=i)).strftime("%Y年%m月%d日")
                self.create_smart_reminder(
                    title=title,
                    content=content,
                    due_date=date,
                    list_name="日常"
                )
        elif frequency == "weekly":
            for i in range(4):  # 创建四周的提醒
                date = (datetime.datetime.now() + datetime.timedelta(weeks=i)).strftime("%Y年%m月%d日")
                self.create_smart_reminder(
                    title=title,
                    content=content,
                    due_date=date,
                    list_name="每周"
                )
        elif frequency == "monthly":
            for i in range(3):  # 创建三个月的提醒
                date = (datetime.datetime.now() + datetime.timedelta(days=30*i)).strftime("%Y年%m月%d日")
                self.create_smart_reminder(
                    title=title,
                    content=content,
                    due_date=date,
                    list_name="每月"
                )

    def batch_create_from_template(self, template_name: str,
                                  custom_values: Dict = None):
        """从模板批量创建任务"""
        if template_name not in self.templates:
            print(f"❌ 模板不存在：{template_name}")
            return False

        template = self.templates[template_name]

        # 应用自定义值
        if custom_values:
            template.update(custom_values)

        # 根据模板类型创建
        if template.get("type") == "reminder":
            self.create_smart_reminder(**template)
        elif template.get("type") == "calendar":
            self.create_smart_calendar_event(**template)
        elif template.get("type") == "batch":
            # 批量创建
            for item in template.get("items", []):
                if item.get("type") == "reminder":
                    self.create_smart_reminder(**item)
                elif item.get("type") == "calendar":
                    self.create_smart_calendar_event(**item)

        return True

    def save_template(self, name: str, template_data: Dict):
        """保存任务模板"""
        self.templates[name] = template_data
        self.save_json(self.templates_file, self.templates)
        print(f"✅ 模板已保存：{name}")

    def get_reminders_for_date(self, date: str = None) -> List[Dict]:
        """获取指定日期的提醒"""
        if not date:
            date = datetime.datetime.now().strftime("%Y年%m月%d日")

        reminders = []
        for task in self.history:
            if (task["type"] == "reminder" and
                task.get("due_date") == date):
                reminders.append(task)

        return reminders

    def get_calendar_events_for_date(self, date: str = None) -> List[Dict]:
        """获取指定日期的日历事件"""
        if not date:
            date = datetime.datetime.now().strftime("%Y年%m月%d日")

        events = []
        for task in self.history:
            if (task["type"] == "calendar" and
                date in task.get("start_date", "")):
                events.append(task)

        return events

    def _run_applescript(self, script: str) -> tuple:
        """执行AppleScript"""
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def _get_priority_value(self, priority: str) -> int:
        """获取优先级数值"""
        priority_map = {
            "low": 0,
            "medium": 5,
            "high": 9
        }
        return priority_map.get(priority.lower(), 5)

    def create_daily_agenda(self, date: str = None):
        """创建每日日程汇总"""
        if not date:
            date = datetime.datetime.now().strftime("%Y年%m月%d日")

        # 获取当天的提醒和事件
        reminders = self.get_reminders_for_date(date)
        events = self.get_calendar_events_for_date(date)

        # 创建汇总提醒
        agenda_title = f"每日日程汇总 - {date}"
        agenda_content = f"今天的安排：\n\n"

        if reminders:
            agenda_content += "📝 提醒事项：\n"
            for i, reminder in enumerate(reminders, 1):
                agenda_content += f"{i}. {reminder['title']}\n"
                if reminder.get('content'):
                    agenda_content += f"   {reminder['content']}\n"
            agenda_content += "\n"

        if events:
            agenda_content += "📅 日历事件：\n"
            for i, event in enumerate(events, 1):
                agenda_content += f"{i}. {event['title']} ({event.get('duration', 30)}分钟)\n"
                if event.get('description'):
                    agenda_content += f"   {event['description']}\n"

        self.create_smart_reminder(
            title=agenda_title,
            content=agenda_content,
            due_date=date,
            list_name="日程汇总",
            priority="high"
        )

def main():
    """主函数 - 演示所有功能"""
    print("🚀 专业版日历和提醒自动化系统")
    print("=" * 60)

    crp = CalendarReminderPro()

    # 演示1：创建智能提醒
    print("\n1️⃣ 创建智能提醒事项")
    print("-" * 40)
    crp.create_smart_reminder(
        title="联系曹新乐，约他周四见面",
        content="需要确认：\n- 见面时间\n- 见面地点\n- 讨论事项",
        due_date="2024年12月16日",
        priority="high",
        tags=["重要", "客户"]
    )

    # 演示2：创建日历事件
    print("\n2️⃣ 创建日历事件")
    print("-" * 40)
    crp.create_smart_calendar_event(
        title="联系曹新乐",
        description="约他周四见面时间",
        start_date="2024年12月16日 09:00:00",
        duration=30,
        location="",
        calendar_name="工作",
        alert_minutes=15
    )

    # 演示3：创建会议提醒
    print("\n3️⃣ 创建会议提醒")
    print("-" * 40)
    crp.create_meeting_reminder(
        title="项目讨论",
        participant="曹新乐",
        meeting_type="电话",
        date="2024年12月16日",
        agenda=[
            "项目进展同步",
            "下周工作计划",
            "资源需求确认"
        ]
    )

    # 演示4：创建重复提醒
    print("\n4️⃣ 创建重复提醒")
    print("-" * 40)
    crp.create_recurring_reminder(
        title="每日工作总结",
        frequency="daily",
        content="1. 完成工作总结\n2. 规划明日任务\n3. 整理邮件"
    )

    # 演示5：创建每日日程汇总
    print("\n5️⃣ 创建每日日程汇总")
    print("-" * 40)
    crp.create_daily_agenda()

    # 演示6：保存和使用模板
    print("\n6️⃣ 任务模板管理")
    print("-" * 40)

    # 保存会议模板
    meeting_template = {
        "type": "batch",
        "items": [
            {
                "type": "reminder",
                "title": "{meeting_title} - 准备",
                "content": "会议准备事项：\n- 查看资料\n- 准备问题\n- 测试设备",
                "list_name": "会议准备",
                "priority": "high"
            },
            {
                "type": "calendar",
                "title": "{meeting_title}",
                "description": "参会人：{participants}",
                "duration": 60,
                "calendar_name": "工作",
                "alert_minutes": 30
            }
        ]
    }
    crp.save_template("标准会议", meeting_template)

    # 使用模板创建会议
    print("\n使用模板创建会议...")
    crp.batch_create_from_template(
        "标准会议",
        {
            "meeting_title": "周例会",
            "participants": "团队成员"
        }
    )

    print("\n✨ 所有操作完成！")

if __name__ == "__main__":
    main()