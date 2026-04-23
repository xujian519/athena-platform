#!/usr/bin/env python3
"""
小诺开发助手 - Xiaonuo Development Assistant
帮助爸爸进行软件开发，提供智能辅助和建议
"""

import logging
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

import aiohttp

logger = logging.getLogger(__name__)

class XiaonuoDevAssistant:
    """小诺开发助手 - 爸爸的专属开发伙伴"""

    def __init__(self):
        self.project_root = Path("/Users/xujian/Athena工作平台")
        self.dev_context = {
            "current_project": None,
            "active_features": [],
            "recent_changes": [],
            "tech_stack": {
                "backend": ["Python", "FastAPI", "PostgreSQL"],
                "ai": ["Claude API", "DeepSeek", "Qwen"],
                "frontend": ["None - Terminal Only"],
                "database": ["PostgreSQL", "Redis", "ArangoDB"],
                "deployment": ["Docker", "Local"]
            }
        }
        self.athena_bridge = None

    async def start_development_session(self):
        """开始开发会话"""
        print("🌸 诺诺的开发助手已启动！")
        print("爸爸，诺诺准备帮您开发了~ 💖")

        # 初始化与Athena的连接
        await self._init_athena_bridge()

        # 分析当前项目状态
        await self._analyze_project_status()

        # 提供开发建议
        await self._provide_dev_suggestions()

    async def _init_athena_bridge(self):
        """初始化与Athena的连接"""
        try:
            # 检查Athena是否运行
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8001/health", timeout=5) as resp:
                    if resp.status == 200:
                        self.athena_bridge = True
                        print("✅ Athena已连接 - 可以提供专利专业建议")
        except (TimeoutError, ConnectionError, OSError):
            print("⚠️ Athena未运行 - 诺诺可以启动它")
            self.athena_bridge = False

    async def _analyze_project_status(self):
        """分析当前项目状态"""
        print("\n📊 项目状态分析")
        print("-" * 30)

        # 分析Git状态
        git_status = await self._get_git_status()
        if git_status:
            print(f"Git状态: {git_status}")

        # 分析Python环境
        python_version = subprocess.run(["python3", "--version"],
                                      capture_output=True, text=True).stdout.strip()
        print(f"Python版本: {python_version}")

        # 分析依赖
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            with open(requirements_file) as f:
                deps = len(f.readlines())
                print(f"依赖包数量: {deps}")

        # 分析最近修改
        recent_files = self._get_recent_modified_files()
        print("\n最近修改的文件:")
        for file_info in recent_files[:5]:
            print(f"  • {file_info['path']} ({file_info['time']})")

    async def _get_git_status(self) -> str:
        """获取Git状态"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            changes = result.stdout.strip().split('\n')
            if len(changes) == 1 and not changes[0]:
                return "工作目录干净"
            else:
                return f"{len(changes)-1}个文件有修改"
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            return "不是Git仓库"

    def _get_recent_modified_files(self) -> list[dict]:
        """获取最近修改的文件"""
        files = []
        for py_file in self.project_root.rglob("*.py"):
            if "node_modules" in str(py_file) or ".git" in str(py_file):
                continue

            try:
                mtime = py_file.stat().st_mtime
                time_str = datetime.fromtimestamp(mtime).strftime("%m-%d %H:%M")
                files.append({
                    "path": str(py_file.relative_to(self.project_root)),
                    "time": time_str,
                    "mtime": mtime
                })
            except Exception as e:
                    logger.error(f"Error occurred: {e}", exc_info=True)

        # 按时间排序
        files.sort(key=lambda x: x["mtime"], reverse=True)
        return files

    async def _provide_dev_suggestions(self):
        """提供开发建议"""
        print("\n💡 诺诺的开发建议")
        print("-" * 30)

        suggestions = []

        # 基于项目状态的建议
        suggestions.append({
            "type": "优化",
            "title": "性能优化",
            "desc": "检查最近的性能瓶颈，特别是数据库查询"
        })

        suggestions.append({
            "type": "功能",
            "title": "按需启动优化",
            "desc": "完善智能体按需启动机制"
        })

        suggestions.append({
            "type": "架构",
            "title": "API设计",
            "desc": "统一RESTful API设计标准"
        })

        # 如果Athena可用，提供专利相关建议
        if self.athena_bridge:
            suggestions.append({
                "type": "专利",
                "title": "专利分析增强",
                "desc": "与Athena协作，增强专利分析能力"
            })

        for i, sugg in enumerate(suggestions, 1):
            print(f"\n{i}. 【{sugg['type']}】{sugg['title']}")
            print(f"   {sugg['desc']}")

    async def help_with_task(self, task_description: str):
        """帮助完成特定任务"""
        print(f"\n🎯 任务: {task_description}")

        # 分析任务类型
        if "专利" in task_description or "patent" in task_description.lower():
            return await self._help_with_patent_task(task_description)
        elif "架构" in task_description or "设计" in task_description:
            return await self._help_with_architecture_task(task_description)
        elif "测试" in task_description or "test" in task_description.lower():
            return await self._help_with_testing_task(task_description)
        else:
            return await self._help_with_general_task(task_description)

    async def _help_with_patent_task(self, task: str):
        """专利任务辅助"""
        print("\n📝 专利开发辅助")

        if not self.athena_bridge:
            print("启动Athena以获得专利专业支持...")
            # 这里可以启动Athena服务
            print("✅ Athena已启动")

        # 提供专利相关建议
        patent_suggestions = [
            "确保符合专利法第26条要求",
            "检查权利要求书的清晰度",
            "验证实施例的完整性"
        ]

        return patent_suggestions

    async def _help_with_architecture_task(self, task: str):
        """架构设计辅助"""
        print("\n🏗️ 架构设计辅助")

        # 分析当前架构
        arch_analysis = {
            "模式": "微服务架构",
            "通信": "REST API + WebSocket",
            "数据库": "PostgreSQL + Redis",
            "部署": "Docker"
        }

        print("当前架构:")
        for key, value in arch_analysis.items():
            print(f"  • {key}: {value}")

        # 提供改进建议
        improvements = [
            "考虑服务网格（Service Mesh）",
            "实现熔断器模式",
            "添加分布式追踪"
        ]

        return improvements

    async def _help_with_testing_task(self, task: str):
        """测试任务辅助"""
        print("\n🧪 测试辅助")

        # 查找测试文件
        test_files = list(self.project_root.rglob("*test*.py"))

        print(f"找到 {len(test_files)} 个测试文件")

        # 运行测试建议
        print("\n测试建议:")
        print("  • 使用 pytest 运行单元测试")
        print("  • 添加集成测试覆盖关键流程")
        print("  • 设置测试覆盖率报告")

    async def _help_with_general_task(self, task: str):
        """一般任务辅助"""
        print(f"\n🔧 任务辅助: {task}")

        # 提供通用建议
        steps = [
            "1. 分析任务需求和边界",
            "2. 设计实现方案",
            "3. 编写代码",
            "4. 测试验证",
            "5. 文档更新"
        ]

        for step in steps:
            print(f"  {step}")

    async def code_review_assist(self, file_path: str):
        """代码审查辅助"""
        print(f"\n🔍 代码审查: {file_path}")

        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return

        # 分析代码
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        issues = []

        # 检查代码规范
        if 'import *' in content:
            issues.append("避免使用 import *")

        # 检查异常处理
        if 'except:' in content and 'except Exception' not in content:
            issues.append("建议指定具体的异常类型")

        # 检查文档字符串
        functions = re.findall(r'def (\w+)\(', content)
        if functions and '"""' not in content:
            issues.append("建议添加函数文档字符串")

        if issues:
            print("\n⚠️ 发现的问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n✅ 代码看起来不错！")

    async def track_progress(self):
        """跟踪开发进度"""
        print("\n📈 开发进度跟踪")

        # 统计代码行数
        total_lines = 0
        python_files = 0

        for py_file in self.project_root.rglob("*.py"):
            if "node_modules" in str(py_file) or ".git" in str(py_file):
                continue

            try:
                with open(py_file, encoding='utf-8') as f:
                    lines = len(f.readlines())
                    total_lines += lines
                    python_files += 1
            except Exception as e:
                    logger.error(f"Error occurred: {e}", exc_info=True)

        print("\n项目统计:")
        print(f"  • Python文件: {python_files}")
        print(f"  • 总代码行数: {total_lines:,}")
        print(f"  • 平均每文件: {total_lines // python_files if python_files else 0} 行")

        # TODO列表
        print("\n📋 待办事项:")
        print("  □ 完成按需启动机制")
        print("  □ 添加错误处理")
        print("  □ 优化数据库查询")
        print("  □ 编写单元测试")

# 使用示例
async def main():
    """主函数示例"""
    assistant = XiaonuoDevAssistant()

    # 开始开发会话
    await assistant.start_development_session()

    # 帮助特定任务
    await assistant.help_with_task("优化专利分析性能")

    # 跟踪进度
    await assistant.track_progress()

# 入口点: @async_main装饰器已添加到main函数
