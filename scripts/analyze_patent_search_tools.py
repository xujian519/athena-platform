#!/usr/bin/env python3
"""
专利检索工具集全面分析脚本

分析项目中所有专利检索相关的工具和模块
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class PatentSearchToolAnalyzer:
    """专利检索工具分析器"""

    def __init__(self):
        self.project_root = Path("/Users/xujian/Athena工作平台")
        self.tools = {}

    def scan_directory(self, directory: str, pattern: str = "*.py") -> List[Path]:
        """扫描目录下的Python文件"""
        dir_path = self.project_root / directory
        if not dir_path.exists():
            return []

        return list(dir_path.rglob(pattern))

    def analyze_patent_retrieval_systems(self):
        """分析专利检索系统"""
        print("\n" + "=" * 80)
        print("🔍 专利检索系统分析")
        print("=" * 80)

        systems = {
            "patent_hybrid_retrieval": {
                "path": "patent_hybrid_retrieval",
                "description": "专利混合检索系统 - 向量+全文检索",
                "main_files": [
                    "patent_hybrid_retrieval.py",
                    "hybrid_retrieval_system.py",
                    "real_patent_hybrid_retrieval.py",
                ],
                "status": "unknown",
            },
                "description": "专利平台 - 基于浏览器的检索系统",
                "main_files": [
                    "core/core_programs/enhanced_patent_search.py",
                    "core/core_programs/deepseek_direct_patent_search.py",
                ],
                "status": "unknown",
            },
            "patent-retrieval-webui": {
                "path": "patent-retrieval-webui",
                "description": "专利检索Web界面 - Vue前端+Python后端",
                "main_files": [
                    "backend/api_server.py",
                ],
                "status": "unknown",
            },
        }

        for system_name, info in systems.items():
            print(f"\n📦 {system_name}")
            print(f"   描述: {info['description']}")

            # 检查目录是否存在
            system_path = self.project_root / info["path"]
            if not system_path.exists():
                print(f"   状态: ❌ 目录不存在")
                info["status"] = "missing"
                continue

            print(f"   状态: ✅ 目录存在")

            # 检查主要文件
            for file_name in info["main_files"]:
                file_path = system_path / file_name
                if file_path.exists():
                    print(f"   ✅ {file_name}")
                else:
                    print(f"   ❌ {file_name} (缺失)")

            # 统计Python文件数量
            py_files = list(system_path.rglob("*.py"))
            print(f"   📄 Python文件总数: {len(py_files)}")

            info["status"] = "exists"
            info["py_files_count"] = len(py_files)

    def analyze_tools_directory(self):
        """分析tools目录下的专利检索工具"""
        print("\n" + "=" * 80)
        print("🔧 tools/ 目录下的专利检索工具")
        print("=" * 80)

        patent_tools = {
            "检索相关": [
                "tools/search/athena_search_platform.py",
                "tools/search/external_search_platform.py",
                "tools/cli/search/athena_search_cli.py",
                "tools/patent_search_schemes_flexible.py",
                "tools/patent_search_schemes_analyzer.py",
            ],
            "下载相关": [
                "tools/download/download_cn_patents.py",
                "tools/download/download_cn_patents_cnipa.py",
                "tools/patent_downloader.py",
                "tools/google_patents_downloader.py",
            ],
            "分析相关": [
                "tools/patent_ai_analyzer.py",
                "tools/patent_3d_search_enhanced.py",
                "tools/patent_claim_tools.py",
            ],
            "数据库相关": [
                "tools/patent_pgsql_searcher.py",
                "tools/patent_db_import.py",
                "tools/restructure_patent_db.py",
            ],
        }

        total_files = 0
        existing_files = 0

        for category, files in patent_tools.items():
            print(f"\n📂 {category}")
            for file_path in files:
                total_files += 1
                full_path = self.project_root / file_path
                if full_path.exists():
                    print(f"   ✅ {Path(file_path).name}")
                    existing_files += 1
                else:
                    print(f"   ❌ {Path(file_path).name}")

        print(f"\n📊 统计: {existing_files}/{total_files} 个文件存在")

    def analyze_core_tools(self):
        """分析core/tools中定义的专利检索工具"""
        print("\n" + "=" * 80)
        print("🏗️ core/tools/ 中的专利检索工具定义")
        print("=" * 80)

        try:
            from core.tools.base import get_global_registry

            registry = get_global_registry()

            # 获取所有工具
            all_tools = registry._tools

            # 筛选专利相关工具
            patent_tools = {}
            for tool_id, tool in all_tools.items():
                if any(
                    keyword in tool_id.lower()
                    for keyword in ["patent", "检索", "search", "retrieval"]
                ):
                    patent_tools[tool_id] = tool

            if patent_tools:
                print(f"\n✅ 已注册的专利相关工具: {len(patent_tools)} 个\n")

                for tool_id, tool in patent_tools.items():
                    status = "✅" if tool.enabled else "❌"
                    print(f"  {status} {tool_id}")
                    print(f"     名称: {tool.name}")
                    print(f"     分类: {tool.category.value}")
                    print(f"     优先级: {tool.priority.value}")
                    print(f"     描述: {tool.description[:80]}...")
                    print()
            else:
                print("\n⚠️  没有找到已注册的专利相关工具")

            # 检查工具集中的专利工具定义
            print("\n📋 工具集(patent_search)中定义的工具:")
            print("-" * 80)

            from core.tools.toolsets import ToolsetManager

            manager = ToolsetManager()
            patent_toolset = manager.get_toolset("patent_search")

            if patent_toolset:
                print(f"✅ 找到专利检索工具集")
                print(f"   工具数量: {patent_toolset.get_tool_count()}")
                print(f"   包含工具:")
                for tool_id in patent_toolset.tools:
                    tool = registry.get_tool(tool_id)
                    if tool:
                        status = "✅" if tool.enabled else "❌"
                        print(f"     {status} {tool_id} - {tool.name}")
                    else:
                        print(f"     ❌ {tool_id} - 未注册")
            else:
                print("❌ 未找到专利检索工具集")

        except Exception as e:
            print(f"\n❌ 分析core/tools时出错: {e}")

    def analyze_duplicates(self):
        """分析重复的功能"""
        print("\n" + "=" * 80)
        print("🔁 功能重复分析")
        print("=" * 80)

        duplicates = {
            "专利检索": [
                "patent_hybrid_retrieval/patent_hybrid_retrieval.py",
                "tools/search/athena_search_platform.py",
                "tools/patent_search_schemes_flexible.py",
            ],
            "专利下载": [
                "tools/download/download_cn_patents.py",
                "tools/download/download_cn_patents_final.py",
                "tools/download/download_cn_patents_direct.py",
                "tools/download/download_cn_patents_cnipa.py",
                "tools/patent_downloader.py",
                "tools/google_patents_downloader.py",
            ],
            "专利分析": [
                "tools/patent_ai_analyzer.py",
                "tools/patent_ai_simple.py",
                "tools/patent_3d_search_enhanced.py",
                "tools/patent_3d_search_analyzer.py",
            ],
        }

        for category, files in duplicates.items():
            print(f"\n📂 {category} (可能存在重复)")
            existing_count = 0
            for file_path in files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    existing_count += 1
                    print(f"   ✅ {Path(file_path).name}")

            if existing_count > 3:
                print(f"   ⚠️  警告: 该类别有{existing_count}个文件，可能存在功能重复")

    def generate_recommendations(self):
        """生成优化建议"""
        print("\n" + "=" * 80)
        print("💡 优化建议")
        print("=" * 80)

        recommendations = [
            {
                "priority": "高",
                "issue": "专利检索功能分散",
                "recommendation": "统一到patent_hybrid_retrieval系统",
                "action": [
                    "评估各检索系统的优缺点",
                    "选择最佳方案作为主系统",
                    "迁移其他系统的有用功能",
                    "删除重复代码",
                ],
            },
            {
                "priority": "高",
                "issue": "专利下载工具过多",
                "recommendation": "合并为统一的下载工具",
                "action": [
                    "分析各个下载器的特点",
                    "创建统一的下载API",
                    "支持多数据源（CNIPA、Google Patents等）",
                    "添加断点续传和错误重试",
                ],
            },
            {
                "priority": "中",
                "issue": "core/tools中未注册专利检索工具",
                "recommendation": "创建统一的专利检索工具接口",
                "action": [
                    "在core/tools/中定义专利检索工具",
                    "实现统一的handler",
                    "注册到全局工具注册表",
                    "通过工具系统调用",
                ],
            },
            {
                "priority": "中",
                "issue": "tools/目录下工具过于分散",
                "recommendation": "整理和归类tools目录",
                "action": [
                    "按功能重新组织tools目录结构",
                    "删除废弃的工具",
                    "添加文档说明",
                    "创建工具索引",
                ],
            },
            {
                "priority": "低",
                "issue": "Web界面和核心系统分离",
                "recommendation": "考虑集成或明确职责",
                "action": [
                    "明确各系统的定位",
                    "如果集成，设计统一API",
                    "如果分离，文档说明使用场景",
                ],
            },
        ]

        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['priority']}优先级 - {rec['issue']}")
            print(f"   建议: {rec['recommendation']}")
            print(f"   行动:")
            for action in rec["action"]:
                print(f"     • {action}")

    def run_analysis(self):
        """运行完整分析"""
        print("\n" + "=" * 80)
        print("📊 Athena平台专利检索工具集分析")
        print("=" * 80)
        print(f"\n项目路径: {self.project_root}")

        # 运行各项分析
        self.analyze_patent_retrieval_systems()
        self.analyze_tools_directory()
        self.analyze_core_tools()
        self.analyze_duplicates()
        self.generate_recommendations()

        print("\n" + "=" * 80)
        print("✅ 分析完成")
        print("=" * 80)


def main():
    """主函数"""
    analyzer = PatentSearchToolAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
