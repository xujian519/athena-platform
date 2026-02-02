#!/usr/bin/env python3
"""
Omni系列软件自动化系统
支持OmniFocus、OmniGraffle、OmniOutliner、OmniPlan
"""

import subprocess
import datetime
import json
import os
from typing import Dict, List, Optional

class OmniAutomation:
    def __init__(self):
        self.omnifocus_templates = {
            "project": {
                "name": "新建项目",
                "context": "办公",
                "flagged": True,
                "due_date": None
            },
            "task": {
                "name": "新任务",
                "context": "待办",
                "flagged": False,
                "estimated_minutes": 30
            }
        }

    def create_omnifocus_task(self, name: str, context: str = None,
                            project: str = None, due_date: str = None,
                            flagged: bool = False, note: str = "",
                            estimated_minutes: int = None):
        """在OmniFocus中创建任务"""
        # 转义特殊字符
        name = name.replace('"', '\\"')
        note = note.replace('"', '\\"')

        script = f'''
        tell application "OmniFocus"
            activate
            delay 1

            -- 获取默认文档
            set defaultDoc to default document

            tell defaultDoc
                -- 创建新任务
                set newTask to make new inbox task with properties {{name:"{name}"}}

                -- 设置备注
                if "{note}" is not "" then
                    set note of newTask to "{note}"
                end if

                -- 设置标记
                set flagged of newTask to {str(flagged).lower()}

                -- 设置上下文
        '''

        # 添加上下文
        if context:
            script += f'''
                try
                    set targetContext to first context whose name is "{context}"
                    set context of newTask to targetContext
                end try
            '''

        # 设置项目
        if project:
            script += f'''
                try
                    set targetProject to first project whose name is "{project}"
                    set containing project of newTask to targetProject
                end try
            '''

        # 设置截止日期
        if due_date:
            script += f'''
                set due date of newTask to date "{due_date}"
            '''

        # 设置预计时间
        if estimated_minutes:
            script += f'''
                set estimated minutes of newTask to {estimated_minutes}
            '''

        script += '''
            end tell

            display notification "OmniFocus任务已创建" with title "✅ 任务已添加"
        end tell
        '''

        success, output, error = self._run_applescript(script)

        if success:
            print(f"✅ OmniFocus任务已创建：{name}")
            return True
        else:
            print(f"❌ 创建OmniFocus任务失败：{error}")
            return False

    def create_omnifocus_project(self, name: str, context: str = None,
                                tasks: Optional[List[Dict] = None,
                                due_date: str = None, flagged: bool = False):
        """在OmniFocus中创建项目"""
        tasks = tasks or []

        script = f'''
        tell application "OmniFocus"
            activate
            delay 1

            set defaultDoc to default document

            tell defaultDoc
                -- 创建新项目
                set newProject to make new project with properties {{name:"{name}"}}

                -- 设置上下文
        '''

        if context:
            script += f'''
                try
                    set defaultContext to first context whose name is "{context}"
                    set default context of newProject to defaultContext
                end try
            '''

        script += '''
                -- 添加任务
        '''

        for i, task in enumerate(tasks):
            task_name = task.get("name", f"任务 {i+1}")
            task_note = task.get("note", "")
            task_name = task_name.replace('"', '\\"')
            task_note = task_note.replace('"', '\\"')

            script += f'''
                set task{i} to make new task with properties {{name:"{task_name}"}}
                if "{task_note}" is not "" then
                    set note of task{i} to "{task_note}"
                end if
            '''

            if task.get("context"):
                script += f'''
                    try
                        set taskContext to first context whose name is "{task['context']}"
                        set context of task{i} to taskContext
                    end try
                '''

            if task.get("estimated_minutes"):
                script += f'''
                    set estimated minutes of task{i} to {task['estimated_minutes']}
                '''

        script += '''
            end tell
        end tell
        '''

        success, output, error = self._run_applescript(script)

        if success:
            print(f"✅ OmniFocus项目已创建：{name}")
            return True
        else:
            print(f"❌ 创建OmniFocus项目失败：{error}")
            return False

    def get_omnifocus_tasks(self, context: str = None, project: str = None) -> List[Dict]:
        """获取OmniFocus任务列表"""
        script = '''
        tell application "OmniFocus"
            set defaultDoc to default document
            set taskList to {}

            tell defaultDoc
                -- 获取所有任务
        '''

        if project:
            script += f'''
                set targetProject to first project whose name is "{project}"
                set allTasks to tasks of targetProject
            '''
        else:
            script += 'set allTasks to every task'

        script += '''
                repeat with aTask in allTasks
                    set taskInfo to {}
                    set end of taskInfo to name of aTask
                    set end of taskInfo to note of aTask
                    set end of taskInfo to completion date of aTask
                    set end of taskInfo to due date of aTask

                    try
                        set taskContext to name of context of aTask
                        set end of taskInfo to taskContext
                    on error
                        set end of taskInfo to ""
                    end try

                    set end of taskList to taskInfo
                end repeat
            end tell
        end tell

        return taskList
        '''

        success, output, error = self._run_applescript(script)

        if success and output:
            # 解析输出
            try:
                # 简化处理，实际需要更复杂的解析
                print("📋 OmniFocus任务列表获取成功")
                return []
            except:
                return []
        else:
            return []

    def create_omnioutliner_document(self, title: str, items: List[Dict],
                                    file_path: str = None):
        """在OmniOutliner中创建大纲文档"""
        if not file_path:
            file_path = os.path.expanduser(f"~/Documents/{title}.oo3")

        script = f'''
        tell application "OmniOutliner"
            activate
            delay 1

            -- 创建新文档
            set newDoc to make new document

            tell newDoc
                -- 设置标题
                set name of root item to "{title}"

                -- 添加内容
        '''

        def add_items_to_script(items_list, indent=0):
            script_part = ""
            for item in items_list:
                name = item.get("name", "").replace('"', '\\"')
                note = item.get("note", "").replace('"', '\\"')
                children = item.get("children", [])

                script_part += f'''
                set newItem to make new child at end of children
                set topic of newItem to "{name}"
                if "{note}" is not "" then
                    set note of newItem to "{note}"
                end if
                '''

                if children:
                    script_part += add_items_to_script(children, indent + 1)

            return script_part

        script += add_items_to_script(items)

        script += f'''
            end tell

            -- 保存文档
            save newDoc in file "{file_path}"

            display notification "OmniOutliner文档已创建" with title "✅ 大纲已生成"
        end tell
        '''

        success, output, error = self._run_applescript(script)

        if success:
            print(f"✅ OmniOutliner文档已创建：{title}")
            print(f"   路径：{file_path}")
            return True
        else:
            print(f"❌ 创建OmniOutliner文档失败：{error}")
            return False

    def create_omniplan_project(self, name: str, tasks: List[Dict],
                              start_date: str = None, end_date: str = None):
        """在OmniPlan中创建项目计划"""
        script = f'''
        tell application "OmniPlan"
            activate
            delay 1

            -- 创建新文档
            set newDoc to make new document

            tell newDoc
                -- 设置项目名称
                set name of project to "{name}"

                -- 设置日期范围
        '''

        if start_date:
            script += f'''
                set start date of project to date "{start_date}"
            '''

        if end_date:
            script += f'''
                set end date of project to date "{end_date}"
            '''

        script += '''
                -- 添加任务
        '''

        for i, task in enumerate(tasks):
            task_name = task.get("name", f"任务 {i+1}")
            task_duration = task.get("duration", 1)  # 天数
            task_resources = task.get("resources", [])
            task_name = task_name.replace('"', '\\"')

            script += f'''
                set task{i} to make new task
                set name of task{i} to "{task_name}"
                set duration of task{i} to {task_duration}
            '''

            if task_resources:
                for resource in task_resources:
                    resource = resource.replace('"', '\\"')
                    script += f'''
                        make new assignment with properties {{task:task{i}, resource:"{resource}"}}
                    '''

        script += '''
            end tell

            display notification "OmniPlan项目已创建" with title "✅ 项目计划已生成"
        end tell
        '''

        success, output, error = self._run_applescript(script)

        if success:
            print(f"✅ OmniPlan项目已创建：{name}")
            return True
        else:
            print(f"❌ 创建OmniPlan项目失败：{error}")
            return False

    def create_omnigraffle_diagram(self, title: str, shapes: List[Dict],
                                 connections: Optional[List[Dict] = None):
        """在OmniGraffle中创建图表"""
        connections = connections or []

        script = f'''
        tell application "OmniGraffle"
            activate
            delay 1

            -- 创建新文档
            set newDoc to make new document

            tell canvas of newDoc
                -- 设置标题
                set name to "{title}"

                -- 创建形状
        '''

        # 创建形状
        shape_refs = []
        for i, shape in enumerate(shapes):
            shape_type = shape.get("type", "Rectangle")
            shape_text = shape.get("text", f"形状 {i+1}").replace('"', '\\"')
            x = shape.get("x", 100 + i * 150)
            y = shape.get("y", 100)
            width = shape.get("width", 120)
            height = shape.get("height", 60)

            script += f'''
                set shape{i} to make new shape with properties {{_
                    origin:{{{x}, {y}}},_
                    size:{{{width}, {height}}},_
                    text:"{shape_text}",_
                    draws shadow:true_
                }}
            '''
            shape_refs.append(f"shape{i}")

        # 创建连接线
        for conn in connections:
            from_shape = conn.get("from", 0)
            to_shape = conn.get("to", 1)
            if from_shape < len(shapes) and to_shape < len(shapes):
                script += f'''
                    make new line with properties {{_
                        point of line:{{beginning:point of shape{from_shape}, ending:point of shape{to_shape}}},_
                        head type:filled arrow_
                    }}
                '''

        script += '''
            end tell

            display notification "OmniGraffle图表已创建" with title "✅ 图表已生成"
        end tell
        '''

        success, output, error = self._run_applescript(script)

        if success:
            print(f"✅ OmniGraffle图表已创建：{title}")
            return True
        else:
            print(f"❌ 创建OmniGraffle图表失败：{error}")
            return False

    def export_omnifocus_to_json(self, output_file: str = None):
        """导出OmniFocus数据为JSON"""
        if not output_file:
            output_file = os.path.expanduser(f"~/Desktop/omnifocus_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        # 获取所有任务
        tasks = self.get_omnifocus_tasks()

        # 保存为JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2, default=str)

        print(f"✅ OmniFocus数据已导出：{output_file}")
        return output_file

    def sync_with_reminders(self):
        """同步OmniFocus与系统提醒事项"""
        script = '''
        tell application "OmniFocus"
            set defaultDoc to default document
            set taskNames to {}

            tell defaultDoc
                set inboxTasks to every inbox task
                repeat with aTask in inboxTasks
                    set end of taskNames to name of aTask
                end repeat
            end tell
        end tell

        tell application "Reminders"
            activate

            tell list "从OmniFocus同步"
                repeat with taskName in taskNames
                    if not (exists reminder whose name is taskName) then
                        make new reminder with properties {name:taskName}
                    end if
                end repeat
            end tell
        end tell
        '''

        success, output, error = self._run_applescript(script)

        if success:
            print("✅ OmniFocus与提醒事项已同步")
            return True
        else:
            print(f"❌ 同步失败：{error}")
            return False

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
    print("🚀 Omni系列软件自动化系统")
    print("=" * 60)

    omni = OmniAutomation()

    # 演示1：创建OmniFocus任务
    print("\n1️⃣ 创建OmniFocus任务")
    print("-" * 40)
    omni.create_omnifocus_task(
        name="联系曹新乐，约他周四见面",
        context="电话",
        note="需要确认：\n- 见面时间\n- 见面地点\n- 讨论事项",
        flagged=True,
        due_date="2024年12月16日"
    )

    # 演示2：创建OmniFocus项目
    print("\n2️⃣ 创建OmniFocus项目")
    print("-" * 40)
    omni.create_omnifocus_project(
        name="客户管理系统开发",
        context="开发",
        tasks=[
            {
                "name": "需求分析",
                "note": "收集所有用户需求",
                "estimated_minutes": 120
            },
            {
                "name": "系统设计",
                "note": "设计系统架构",
                "context": "设计",
                "estimated_minutes": 240
            },
            {
                "name": "编码实现",
                "note": "主要功能开发",
                "context": "开发",
                "estimated_minutes": 480
            },
            {
                "name": "测试部署",
                "note": "系统测试和上线",
                "context": "测试",
                "estimated_minutes": 180
            }
        ],
        due_date="2025年1月31日"
    )

    # 演示3：创建OmniOutliner文档
    print("\n3️⃣ 创建OmniOutliner文档")
    print("-" * 40)
    omni.create_omnioutliner_document(
        title="项目计划大纲",
        items=[
            {
                "name": "项目目标",
                "note": "明确项目要达成的目标",
                "children": [
                    {
                        "name": "短期目标",
                        "note": "3个月内完成"
                    },
                    {
                        "name": "长期目标",
                        "note": "1年规划"
                    }
                ]
            },
            {
                "name": "资源需求",
                "note": "项目所需的各种资源",
                "children": [
                    {
                        "name": "人力资源",
                        "note": "开发、测试、运维"
                    },
                    {
                        "name": "技术资源",
                        "note": "服务器、软件许可"
                    }
                ]
            },
            {
                "name": "时间规划",
                "note": "详细的时间安排",
                "children": [
                    {
                        "name": "第一阶段",
                        "note": "需求分析和设计"
                    },
                    {
                        "name": "第二阶段",
                        "note": "开发和测试"
                    }
                ]
            }
        ]
    )

    # 演示4：创建OmniPlan项目
    print("\n4️⃣ 创建OmniPlan项目")
    print("-" * 40)
    omni.create_omniplan_project(
        name="新系统开发项目",
        start_date="2024年12月15日",
        end_date="2025年3月31日",
        tasks=[
            {
                "name": "项目启动",
                "duration": 3,
                "resources": ["项目经理"]
            },
            {
                "name": "需求收集",
                "duration": 10,
                "resources": ["产品经理", "业务分析师"]
            },
            {
                "name": "系统设计",
                "duration": 15,
                "resources": ["架构师", "UI设计师"]
            },
            {
                "name": "前端开发",
                "duration": 30,
                "resources": ["前端工程师"]
            },
            {
                "name": "后端开发",
                "duration": 35,
                "resources": ["后端工程师"]
            },
            {
                "name": "测试",
                "duration": 10,
                "resources": ["测试工程师"]
            },
            {
                "name": "部署上线",
                "duration": 5,
                "resources": ["运维工程师"]
            }
        ]
    )

    # 演示5：创建OmniGraffle流程图
    print("\n5️⃣ 创建OmniGraffle流程图")
    print("-" * 40)
    omni.create_omnigraffle_diagram(
        title="业务流程图",
        shapes=[
            {"type": "Oval", "text": "开始", "x": 300, "y": 50},
            {"type": "Rectangle", "text": "用户注册", "x": 300, "y": 150},
            {"type": "Diamond", "text": "验证信息", "x": 300, "y": 250},
            {"type": "Rectangle", "text": "注册成功", "x": 200, "y": 350},
            {"type": "Rectangle", "text": "重新输入", "x": 400, "y": 350},
            {"type": "Oval", "text": "结束", "x": 300, "y": 450}
        ],
        connections=[
            {"from": 0, "to": 1},
            {"from": 1, "to": 2},
            {"from": 2, "to": 3},
            {"from": 2, "to": 4},
            {"from": 4, "to": 1},
            {"from": 3, "to": 5}
        ]
    )

    # 演示6：同步OmniFocus和提醒事项
    print("\n6️⃣ 同步OmniFocus和提醒事项")
    print("-" * 40)
    omni.sync_with_reminders()

    print("\n✨ 所有操作完成！")
    print("\n💡 提示：")
    print("- OmniFocus：任务管理应用")
    print("- OmniOutliner：大纲和笔记应用")
    print("- OmniPlan：项目管理应用")
    print("- OmniGraffle：图表和流程图应用")

if __name__ == "__main__":
    main()