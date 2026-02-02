#!/usr/bin/env python3
"""
Athena开发助手主程序
Athena Development Assistant Main
爸爸的专利专业助手
"""

import asyncio
from core.async_main import async_main
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from tools.patent_writing_tool import AthenaPatentWritingTool
from tools.examination_response_tool import AthenaExaminationResponseTool


class AthenaDevAssistant:
    """Athena开发助手"""

    def __init__(self):
        self.writing_tool = AthenaPatentWritingTool()
        self.response_tool = AthenaExaminationResponseTool()
        self.workspace = Path("/Users/xujian/Athena工作平台/workspaces/athena_dev")
        self.workspace.mkdir(parents=True, exist_ok=True)

    async def start_assistant(self):
        """启动助手"""
        print("🏛️  Athena 开发助手")
        print("=" * 50)
        print("💖 爸爸的专利专业助手")
        print("=" * 50)
        print()

        # 显示功能菜单
        self.show_menu()

        # 进入主循环
        while True:
            try:
                choice = input("\n请选择功能 (1-5, q退出): ").strip()

                if choice == 'q':
                    print("\n💖 Athena 期待再次为爸爸服务！")
                    break

                if choice == '1':
                    await self.handle_patent_writing()
                elif choice == '2':
                    await self.handle_examination_response()
                elif choice == '3':
                    await self.handle_patent_analysis()
                elif choice == '4':
                    await self.handle_database_query()
                elif choice == '5':
                    await self.show_recent_work()
                else:
                    print("⚠️ 请输入有效选项")

            except KeyboardInterrupt:
                print("\n\n💖 再见爸爸！")
                break

    def show_menu(self) -> Any:
        """显示功能菜单"""
        print("📋 功能菜单：")
        print("1. 专利撰写工具")
        print("2. 审查答复工具")
        print("3. 专利分析工具")
        print("4. 数据库查询")
        print("5. 查看最近工作")
        print("q. 退出")

    async def handle_patent_writing(self):
        """处理专利撰写"""
        print("\n📝 专利撰写工具")
        print("-" * 30)

        # 获取技术交底书
        print("\n请输入技术交底书内容（输入 '###' 结束）：")
        disclosure_lines = []

        while True:
            line = input()
            if line.strip() == '###':
                break
            disclosure_lines.append(line)

        disclosure = '\n'.join(disclosure_lines)

        if not disclosure.strip():
            print("⚠️ 技术交底书不能为空")
            return

        # 分析技术交底书
        print("\n🔍 正在分析技术交底书...")
        analysis = self.writing_tool.analyze_invention_disclosure(disclosure)

        # 显示分析结果
        print("\n📊 分析结果：")
        for key, value in analysis.items():
            if value and key != "关键技术创新点":
                print(f"\n{key}:")
                content = str(value)[:300] + "..." if len(str(value)) > 300 else str(value)
                print(content)

        # 询问是否生成权利要求
        if input("\n是否生成权利要求？(y/n): ").strip().lower() == 'y':
            claim_type = input("权利要求类型 (产品/方法): ").strip() or "产品"
            claims = self.writing_tool.draft_claims(analysis, claim_type)

            print("\n📋 生成的权利要求：")
            for i, claim in enumerate(claims, 1):
                print(f"\n权利要求{i}:")
                print(claim)

            # 保存草稿
            if input("\n是否保存草稿？(y/n): ").strip().lower() == 'y':
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = self.workspace / f"claims_draft_{timestamp}.txt"

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("权利要求书\n\n")
                    for i, claim in enumerate(claims, 1):
                        f.write(f"权利要求{i}: {claim}\n\n")

                print(f"✅ 草稿已保存到: {file_path}")

        # 询问是否生成说明书
        if input("\n是否生成说明书？(y/n): ").strip().lower() == 'y':
            spec = self.writing_tool.draft_specification(analysis)

            print("\n📖 说明书草稿（摘要）:")
            for section, content in spec.items():
                if content:
                    print(f"\n{section}:")
                    preview = content[:200] + "..." if len(content) > 200 else content
                    print(preview)

            # 检查专利法第26条
            check_result = self.writing_tool.check_patent_law_26('\n'.join(spec.values()))

            print("\n✅ 专利法第26条检查:")
            print(f"  是否完整: {'✅' if check_result['完整性检查']['是否完整'] else '❌'}")
            print(f"  是否清楚: {'✅' if check_result['完整性检查']['是否清楚'] else '❌'}")
            print(f"  能够实现: {'✅' if check_result['完整性检查']['能够实现'] else '❌'}")

            if check_result['完整性检查']['建议']:
                print("\n💡 建议:")
                for suggestion in check_result['完整性检查']['建议']:
                    print(f"  • {suggestion}")

    async def handle_examination_response(self):
        """处理审查答复"""
        print("\n📨 审查答复工具")
        print("-" * 30)

        # 获取审查意见
        print("\n请输入审查意见（输入 '###' 结束）：")
        opinion_lines = []

        while True:
            line = input()
            if line.strip() == '###':
                break
            opinion_lines.append(line)

        opinion_text = '\n'.join(opinion_lines)

        if not opinion_text.strip():
            print("⚠️ 审查意见不能为空")
            return

        # 分析审查意见
        print("\n🔍 正在分析审查意见...")
        analysis = self.response_tool.analyze_examination_opinion(opinion_text)

        # 显示分析结果
        print("\n📊 分析结果：")
        print(f"审查类型: {', '.join(analysis['审查类型'])}")
        print(f"涉及权利要求: {', '.join(analysis['涉及权利要求']) if analysis['涉及权利要求'] else '无'}")

        # 生成答复
        if input("\n是否生成答复草稿？(y/n): ").strip().lower() == 'y':
            # 获取专利信息
            patent_info = {
                "application_no": input("申请号: ").strip() or "待填",
                "applicant": input("申请人: ").strip() or "待填"
            }

            # 起草答复
            response = self.response_tool.draft_response(analysis, patent_info)

            print("\n📄 生成的答复（前500字）:")
            print(response[:500] + "..." if len(response) > 500 else response)

            # 生成修改建议
            suggestions = self.response_tool.generate_amendment_suggestions(analysis)
            if suggestions:
                print("\n💡 修改建议:")
                for suggestion in suggestions:
                    print(f"\n权利要求{suggestion['权利要求']}:")
                    print(f"  {suggestion['修改类型']}")
                    print(f"  {suggestion['理由']}")

            # 保存答复
            if input("\n是否保存答复？(y/n): ").strip().lower() == 'y':
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = self.workspace / f"response_{timestamp}.txt"

                self.response_tool.save_response(response, str(file_path))
                print(f"✅ 答复已保存到: {file_path}")

    async def handle_patent_analysis(self):
        """处理专利分析"""
        print("\n🔍 专利分析工具")
        print("-" * 30)

        # 获取专利号或文本
        patent_input = input("\n请输入专利号/技术要点: ").strip()

        if not patent_input:
            print("⚠️ 输入不能为空")
            return

        print("\n🔄 正在分析...")
        # 这里可以连接实际的专利数据库进行分析
        print(f"\n📊 分析结果：")
        print(f"  输入: {patent_input}")
        print(f"  状态: 需要连接专利数据库进行详细分析")
        print(f"  建议: 可以查询专利数据库获取更多信息")

    async def handle_database_query(self):
        """处理数据库查询"""
        print("\n💾 数据库查询")
        print("-" * 30)

        print("\n可用的数据库:")
        print("1. 中国专利数据库 (patent_db)")
        print("2. 技术方案数据库")
        print("3. 案例数据库")

        choice = input("\n请选择数据库 (1-3): ").strip()

        if choice == "1":
            keyword = input("请输入关键词: ").strip()
            print(f"\n查询专利数据库中的关键词: {keyword}")
            print("  (需要连接实际的patent_db数据库)")

        elif choice == "2":
            print("\n技术方案数据库")
            print("  存储您的技术方案和创意")

        elif choice == "3":
            print("\n案例数据库")
            print("  存储成功案例和经验")

    async def show_recent_work(self):
        """显示最近工作"""
        print("\n📂 最近工作")
        print("-" * 30)

        # 列出工作区文件
        files = list(self.workspace.glob("*.txt"))

        if not files:
            print("  暂无工作记录")
            return

        # 按时间排序
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        print("\n最近10项工作:")
        for i, file in enumerate(files[:10], 1):
            # 获取文件信息
            stat = file.stat()
            size = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime)

            # 根据文件名判断类型
            if "claims" in file.name:
                work_type = "权利要求"
            elif "response" in file.name:
                work_type = "审查答复"
            else:
                work_type = "其他"

            print(f"\n{i}. {file.name}")
            print(f"   类型: {work_type}")
            print(f"   大小: {size} 字节")
            print(f"   时间: {mtime.strftime('%Y-%m-%d %H:%M')}")

        if input("\n是否查看某个文件？(输入编号，n跳过): ").strip().isdigit():
            idx = int(input()) - 1
            if 0 <= idx < len(files):
                file = files[idx]
                print(f"\n📖 {file.name}:")
                print("-" * 30)

                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 只显示前1000字
                    preview = content[:1000] + "..." if len(content) > 1000 else content
                    print(preview)


# 使用示例
async def main():
    """主函数"""
    assistant = AthenaDevAssistant()
    await assistant.start_assistant()


# 入口点: @async_main装饰器已添加到main函数