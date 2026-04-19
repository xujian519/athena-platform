#!/usr/bin/env python3
"""
核心工具分析脚本
分析核心工具的功能、作用和可用性
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoreToolAnalyzer:
    """核心工具分析器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.core_tools = []

    def identify_core_tools(self) -> List[Dict[str, Any]]:
        """识别核心工具"""

        # 核心工具列表（基于实际使用情况）
        core_tool_files = [
            {
                "name": "patent_search",
                "file": "core/tools/patent_retrieval.py",
                "handler": "patent_search_handler",
                "category": "patent_search",
                "priority": "P0",
                "status": "已迁移",
                "description": "在专利数据库中搜索专利（支持本地PostgreSQL和Google Patents）"
            },
            {
                "name": "patent_download",
                "file": "core/tools/patent_download.py",
                "handler": "patent_download_handler",
                "category": "data_extraction",
                "priority": "P0",
                "status": "已迁移",
                "description": "从Google Patents下载专利PDF文件"
            },
            {
                "name": "enhanced_document_parser",
                "file": "core/tools/enhanced_document_parser.py",
                "handler": "enhanced_document_parser_handler",
                "category": "data_extraction",
                "priority": "P0",
                "status": "已迁移",
                "description": "增强文档解析器（支持OCR、PDF、DOCX等）"
            },
            {
                "name": "local_web_search",
                "file": "core/tools/real_tool_implementations.py",
                "handler": "local_web_search_handler",
                "category": "web_search",
                "priority": "P0",
                "status": "已迁移",
                "description": "本地网络搜索（支持多个搜索引擎）"
            },
            {
                "name": "vector_search",
                "file": "core/vector/intelligent_vector_manager.py",
                "handler": "vector_search_handler",
                "category": "vector_search",
                "priority": "P0",
                "status": "待迁移",
                "description": "向量语义搜索（基于BGE-M3模型）"
            },
            {
                "name": "academic_search",
                "file": "core/search/tools/google_scholar_tool.py",
                "handler": "google_scholar_search_handler",
                "category": "academic_search",
                "priority": "P1",
                "status": "待迁移",
                "description": "学术文献搜索（Google Scholar）"
            },
            {
                "name": "legal_analysis",
                "file": "core/legal/legal_vector_retrieval_service.py",
                "handler": "legal_vector_retrieval_handler",
                "category": "legal_analysis",
                "priority": "P1",
                "status": "待迁移",
                "description": "法律文献向量检索和分析"
            },
            {
                "name": "semantic_analysis",
                "file": "core/nlp/semantic_analyzer.py",
                "handler": "semantic_analysis_handler",
                "category": "semantic_analysis",
                "priority": "P1",
                "status": "待迁移",
                "description": "文本语义分析和理解"
            },
            {
                "name": "patent_analysis",
                "file": "core/patent/patent_analyzer.py",
                "handler": "patent_analysis_handler",
                "category": "patent_analysis",
                "priority": "P1",
                "status": "待迁移",
                "description": "专利内容分析和创造性评估"
            },
            {
                "name": "knowledge_graph_search",
                "file": "core/knowledge_graph/graph_manager.py",
                "handler": "knowledge_graph_search_handler",
                "category": "knowledge_graph",
                "priority": "P2",
                "status": "待迁移",
                "description": "知识图谱搜索和推理"
            },
            {
                "name": "browser_automation",
                "file": "core/tools/browser_automation_tool.py",
                "handler": "browser_automation_handler",
                "category": "web_automation",
                "priority": "P2",
                "status": "待迁移",
                "description": "浏览器自动化工具（Playwright）"
            },
            {
                "name": "cache_management",
                "file": "core/cache/unified_cache.py",
                "handler": "cache_management_handler",
                "category": "cache_management",
                "priority": "P1",
                "status": "待迁移",
                "description": "统一缓存管理"
            },
            {
                "name": "data_transformation",
                "file": "core/data/transformation.py",
                "handler": "data_transformation_handler",
                "category": "data_transformation",
                "priority": "P2",
                "status": "待迁移",
                "description": "数据转换和格式化"
            }
        ]

        return core_tool_files

    def analyze_tool(self, tool_info: Dict[str, Any]) -> Dict[str, Any]:
        """分析单个工具"""

        file_path = self.project_root / tool_info["file"]

        analysis = {
            **tool_info,
            "file_exists": file_path.exists(),
            "can_import": False,
            "has_handler": False,
            "dependencies": [],
            "issues": [],
            "recommendations": []
        }

        if not file_path.exists():
            analysis["issues"].append(f"文件不存在: {file_path}")
            return analysis

        # 检查是否可以导入
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(tool_info["name"], file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                analysis["can_import"] = True

                # 检查handler是否存在
                if hasattr(module, tool_info["handler"]):
                    analysis["has_handler"] = True
                else:
                    analysis["issues"].append(f"Handler不存在: {tool_info['handler']}")

        except Exception as e:
            analysis["issues"].append(f"导入失败: {str(e)}")

        # 生成建议
        if tool_info["status"] == "待迁移":
            if tool_info["priority"] == "P0":
                analysis["recommendations"].append("高优先级工具，建议立即迁移")
            elif tool_info["priority"] == "P1":
                analysis["recommendations"].append("中优先级工具，建议本周迁移")
            else:
                analysis["recommendations"].append("低优先级工具，可按需迁移")

        return analysis

    def generate_report(self) -> Dict[str, Any]:
        """生成分析报告"""

        tools = self.identify_core_tools()
        analyzed_tools = []

        for tool_info in tools:
            analyzed = self.analyze_tool(tool_info)
            analyzed_tools.append(analyzed)

        # 统计信息
        stats = {
            "total": len(analyzed_tools),
            "migrated": len([t for t in analyzed_tools if t["status"] == "已迁移"]),
            "pending": len([t for t in analyzed_tools if t["status"] == "待迁移"]),
            "file_exists": len([t for t in analyzed_tools if t["file_exists"]]),
            "can_import": len([t for t in analyzed_tools if t["can_import"]]),
            "has_handler": len([t for t in analyzed_tools if t["has_handler"]]),
            "by_priority": {
                "P0": len([t for t in analyzed_tools if t["priority"] == "P0"]),
                "P1": len([t for t in analyzed_tools if t["priority"] == "P1"]),
                "P2": len([t for t in analyzed_tools if t["priority"] == "P2"]),
            }
        }

        return {
            "summary": stats,
            "tools": analyzed_tools
        }


def main():
    """主函数"""

    print("=" * 80)
    print("🔍 核心工具分析")
    print("=" * 80)
    print()

    project_root = Path("/Users/xujian/Athena工作平台")
    analyzer = CoreToolAnalyzer(project_root)

    # 生成报告
    report = analyzer.generate_report()

    # 保存报告
    report_path = project_root / "reports" / "core_tools_analysis.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 打印摘要
    stats = report["summary"]
    print("📊 核心工具统计:")
    print(f"   总计: {stats['total']}")
    print(f"   已迁移: {stats['migrated']}")
    print(f"   待迁移: {stats['pending']}")
    print(f"   文件存在: {stats['file_exists']}")
    print(f"   可导入: {stats['can_import']}")
    print(f"   有Handler: {stats['has_handler']}")
    print()
    print(f"   P0 (高优先级): {stats['by_priority']['P0']}")
    print(f"   P1 (中优先级): {stats['by_priority']['P1']}")
    print(f"   P2 (低优先级): {stats['by_priority']['P2']}")
    print()

    # 打印待迁移工具详情
    print("📋 待迁移工具详情:")
    print()
    for tool in report["tools"]:
        if tool["status"] == "待迁移":
            print(f"工具: {tool['name']}")
            print(f"  描述: {tool['description']}")
            print(f"  文件: {tool['file']}")
            print(f"  优先级: {tool['priority']}")
            print(f"  状态: ", end="")

            if tool["file_exists"]:
                print("✅ 文件存在", end=" ")
            else:
                print("❌ 文件不存在", end=" ")

            if tool["can_import"]:
                print("✅ 可导入", end=" ")
            else:
                print("❌ 不可导入", end=" ")

            if tool["has_handler"]:
                print("✅ 有Handler")
            else:
                print("❌ 无Handler")

            if tool["issues"]:
                print("  问题:")
                for issue in tool["issues"]:
                    print(f"    - {issue}")

            if tool["recommendations"]:
                print("  建议:")
                for rec in tool["recommendations"]:
                    print(f"    - {rec}")

            print()

    print("✅ 分析完成")
    print(f"   报告路径: {report_path}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
