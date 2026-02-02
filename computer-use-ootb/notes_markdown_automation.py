#!/usr/bin/env python3
"""
备忘录Markdown自动化系统
支持自动创建、格式化和管理Markdown备忘录
"""

import subprocess
import datetime
import os
import re
from typing import Dict, List, Optional
import json

class NotesMarkdownAutomation:
    def __init__(self):
        self.templates_dir = "/Users/xujian/Athena工作平台/computer-use-ootb/notes_templates"
        self.notes_dir = "/Users/xujian/Athena工作平台/notes_backup"
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.notes_dir, exist_ok=True)

        # Markdown模板
        self.templates = {
            "meeting": """# {title}

**会议时间：** {date} {time}
**参会人：** {attendees}
**地点：** {location}

## 议程
{agenda}

## 会议记录
{notes}

## 决议事项
- [ ]
- [ ]
- [ ]

## 后续行动
- [ ]
- [ ]
- [ ]

---
*记录人：{recorder}*
*记录时间：{timestamp}*
""",
            "daily": """# {date} 工作日志

## 今日完成
{completed}

## 遇到的问题
{problems}

## 明日计划
{tomorrow_plan}

## 心得体会
{thoughts}

---
{author} - {date}
""",
            "project": """# {project_name}

## 项目概述
{description}

## 目标
{goals}

## 进度跟踪
### 已完成
- [ ]
- [ ]

### 进行中
- [ ]
- [ ]

### 待处理
- [ ]
- [ ]

## 里程碑
{milestones}

## 资源链接
{resources}

---
创建于：{created_date}
""",
            "idea": """# 💡 {title}

**时间：** {timestamp}

## 想法来源
{source}

## 核心概念
{concept}

## 实现方案
{implementation}

## 相关链接
{links}

## 后续思考
{next_steps}

---
标签：{tags}
"""
        }

    def create_note_in_app(self, title: str, content: str, folder: str = "备忘录"):
        """在备忘录应用中创建笔记"""
        # 转义AppleScript字符串中的特殊字符
        title = title.replace('"', '\\"')
        content = content.replace('"', '\\"')

        script = f'''
        tell application "Notes"
            activate
            delay 1

            -- 获取或创建文件夹
            try
                set targetFolder to folder "{folder}"
            on error
                set targetFolder to make new folder with properties {{name:"{folder}"}}
            end try

            -- 创建新笔记
            tell targetFolder
                make new note with properties {{name:"{title}", body:"{content}"}}
            end tell

            display notification "备忘录已创建：{title}" with title "📝 小诺笔记"
        end tell
        '''

        success, output, error = self._run_applescript(script)

        if success:
            print(f"✅ 备忘录已创建：{title}")
            return True
        else:
            print(f"❌ 创建备忘录失败：{error}")
            return False

    def create_markdown_note(self, template_name: str, **kwargs):
        """使用模板创建Markdown格式的备忘录"""
        if template_name not in self.templates:
            print(f"❌ 模板不存在：{template_name}")
            return False

        # 获取模板
        template = self.templates[template_name]

        # 设置默认值
        defaults = {
            "date": datetime.datetime.now().strftime("%Y年%m月%d日"),
            "time": datetime.datetime.now().strftime("%H:%M"),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "recorder": "小诺",
            "author": "徐健"
        }
        defaults.update(kwargs)

        # 格式化模板
        try:
            content = template.format(**defaults)
        except KeyError as e:
            print(f"❌ 缺少必要的参数：{e}")
            return False

        # 提取标题
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else f"新笔记 - {template_name}"

        # 在备忘录应用中创建
        return self.create_note_in_app(title, content)

    def create_meeting_notes(self, title: str, attendees: List[str],
                           agenda: Optional[List[str] = None, location: str = "未定",
                           template_name: str = "meeting"):
        """创建会议笔记"""
        # 处理参会人列表
        attendees_str = "、".join(attendees) if attendees else "待定"

        # 处理议程
        agenda_str = ""
        if agenda:
            for i, item in enumerate(agenda, 1):
                agenda_str += f"{i}. {item}\n"

        return self.create_markdown_note(
            template_name,
            title=title,
            attendees=attendees_str,
            location=location,
            agenda=agenda_str
        )

    def create_daily_log(self, completed: Optional[List[str] = None,
                        problems: Optional[List[str] = None,
                        tomorrow_plan: Optional[List[str] = None,
                        thoughts: str = ""):
        """创建每日工作日志"""
        completed_str = ""
        if completed:
            for item in completed:
                completed_str += f"- [ ] {item}\n"

        problems_str = ""
        if problems:
            for item in problems:
                problems_str += f"- [ ] {item}\n"

        tomorrow_str = ""
        if tomorrow_plan:
            for item in tomorrow_plan:
                tomorrow_str += f"- [ ] {item}\n"

        return self.create_markdown_note(
            "daily",
            completed=completed_str or "- [ ] ",
            problems=problems_str or "- [ ] ",
            tomorrow_plan=tomorrow_str or "- [ ] ",
            thoughts=thoughts
        )

    def create_project_note(self, project_name: str, description: str,
                           goals: Optional[List[str] = None, milestones: Optional[List[str] = None):
        """创建项目笔记"""
        goals_str = ""
        if goals:
            for goal in goals:
                goals_str += f"- {goal}\n"

        milestones_str = ""
        if milestones:
            for milestone in milestones:
                milestones_str += f"- [ ] {milestone}\n"

        return self.create_markdown_note(
            "project",
            project_name=project_name,
            description=description,
            goals=goals_str or "- ",
            milestones=milestones_str or "- "
        )

    def capture_idea(self, title: str, concept: str,
                    source: str = "", implementation: str = "",
                    links: Optional[List[str] = None, tags: Optional[List[str] = None):
        """快速记录想法"""
        links_str = ""
        if links:
            for link in links:
                links_str += f"- [{link}]({link})\n"

        tags_str = ""
        if tags:
            tags_str = ", ".join(tags)

        return self.create_markdown_note(
            "idea",
            title=title,
            concept=concept,
            source=source,
            implementation=implementation,
            links=links_str,
            tags=tags_str
        )

    def import_markdown_file(self, file_path: str, folder: str = "备忘录"):
        """导入Markdown文件到备忘录"""
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在：{file_path}")
            return False

        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取标题
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else os.path.basename(file_path)

        # 转换为备忘录格式
        # 将Markdown转换为HTML（备忘录支持）
        content = content.replace('\n# ', '\n<h1>').replace('\n## ', '\n<h2>').replace('\n### ', '\n<h3>')
        content = re.sub(r'\n- (.+)', r'\n• \1', content)

        return self.create_note_in_app(title, content, folder)

    def export_notes_to_markdown(self, folder: str = "备忘录"):
        """导出备忘录到Markdown文件"""
        script = f'''
        tell application "Notes"
            set output to ""

            try
                set targetFolder to folder "{folder}"
                set allNotes to every note in targetFolder

                repeat with aNote in allNotes
                    set noteName to name of aNote
                    set noteBody to body of aNote

                    set output to output & "# " & noteName & "\n\n" & noteBody & "\n\n---\n\n"
                end repeat
            end try
        end tell

        return output
        '''

        success, output, error = self._run_applescript(script)

        if success and output:
            # 保存到文件
            filename = f"notes_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            filepath = os.path.join(self.notes_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output)

            print(f"✅ 备忘录已导出：{filepath}")
            return filepath
        else:
            print(f"❌ 导出失败：{error}")
            return None

    def create_custom_template(self, name: str, template: str):
        """创建自定义模板"""
        template_path = os.path.join(self.templates_dir, f"{name}.md")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template)

        self.templates[name] = template
        print(f"✅ 模板已创建：{name}")

    def list_available_templates(self):
        """列出所有可用模板"""
        print("\n📝 可用的模板：")
        print("-" * 40)
        for name in self.templates:
            print(f"- {name}")

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

def main():
    """主函数 - 演示所有功能"""
    print("📝 备忘录Markdown自动化系统")
    print("=" * 60)

    nma = NotesMarkdownAutomation()

    # 演示1：创建会议笔记
    print("\n1️⃣ 创建会议笔记")
    print("-" * 40)
    nma.create_meeting_notes(
        title="项目启动会议",
        attendees=["曹新乐", "张三", "李四"],
        agenda=[
            "项目背景介绍",
            "团队成员分工",
            "项目计划讨论",
            "Q&A环节"
        ],
        location="会议室A"
    )

    # 演示2：创建每日日志
    print("\n2️⃣ 创建每日工作日志")
    print("-" * 40)
    nma.create_daily_log(
        completed=[
            "完成项目提案文档",
            "与客户确认需求",
            "安排下周会议"
        ],
        problems=[
            "开发资源不足",
            "部分功能技术难度较大"
        ],
        tomorrow_plan=[
            "解决技术难题",
            "准备演示材料",
            "联系潜在用户"
        ],
        thoughts="今天整体进展顺利，但需要加强团队协作"
    )

    # 演示3：创建项目笔记
    print("\n3️⃣ 创建项目笔记")
    print("-" * 40)
    nma.create_project_note(
        project_name="智能助手升级计划",
        description="将小诺助手升级为支持更多自动化功能的智能系统",
        goals=[
            "实现日历自动化",
            "支持Markdown备忘录",
            "集成Omni系列软件"
        ],
        milestones=[
            "完成基础功能开发",
            "进行内部测试",
            "收集用户反馈",
            "正式发布"
        ]
    )

    # 演示4：快速记录想法
    print("\n4️⃣ 快速记录想法")
    print("-" * 40)
    nma.capture_idea(
        title="使用AI优化工作流程",
        concept="通过AI助手自动化处理重复性工作，提高效率",
        source="日常工作中的痛点",
        implementation="1. 识别重复性任务 2. 开发自动化脚本 3. 持续优化",
        links=["https://www.apple.com/shortcuts/", "https://www.apple.com/reminders/"],
        tags=["AI", "自动化", "效率"]
    )

    # 演示5：创建自定义模板
    print("\n5️⃣ 创建自定义模板")
    print("-" * 40)
    book_template = """# 《{book_title}》读书笔记

**作者：** {author}
**阅读时间：** {read_date}
**评分：** {rating}/5

## 核心观点
{key_points}

## 精彩摘录
{quotes}

## 个人感悟
{thoughts}

## 可应用的建议
{action_items}

---
记录于：{timestamp}
"""
    nma.create_custom_template("book_review", book_template)

    # 演示6：使用自定义模板
    print("\n6️⃣ 使用自定义模板")
    print("-" * 40)
    nma.create_markdown_note(
        "book_review",
        book_title="自动化之道",
        author="张三",
        rating=5,
        key_points="- 自动化是提升效率的关键\n- 从小处着手，逐步完善",
        quotes="- "让机器做机器擅长的事，让人做人擅长的事"",
        thoughts="这本书改变了我对工作的看法"
    )

    # 演示7：列出所有模板
    print("\n7️⃣ 查看所有可用模板")
    print("-" * 40)
    nma.list_available_templates()

    print("\n✨ 所有操作完成！")
    print("💡 提示：打开备忘录应用查看创建的笔记")

if __name__ == "__main__":
    main()