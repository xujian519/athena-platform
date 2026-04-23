#!/usr/bin/env python3
"""
工具迁移识别脚本
识别需要迁移到统一工具注册表的工具
"""

import ast
import json
import logging
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolIdentifier:
    """工具识别器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.core_dir = project_root / "core"
        self.tools_found = []

    def scan_for_tools(self) -> list[dict[str, Any]:
        """扫描core目录，查找工具定义"""
        tools = []

        # 扫描所有Python文件
        for py_file in self.core_dir.rglob("*.py"):
            # 跳过测试文件和__pycache__
            if "__pycache__" in str(py_file) or py_file.name.startswith("test_"):
                continue

            try:
                file_tools = self._extract_tools_from_file(py_file)
                if file_tools:
                    tools.extend(file_tools)
            except Exception as e:
                logger.debug(f"扫描文件失败 {py_file}: {e}")

        return tools

    def _extract_tools_from_file(self, file_path: Path) -> list[dict[str, Any]:
        """从文件中提取工具定义"""
        tools = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # 查找函数定义
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    tool_info = self._analyze_function(node, file_path)
                    if tool_info:
                        tools.append(tool_info)

                # 查找类定义（可能是工具类）
                elif isinstance(node, ast.ClassDef):
                    class_tools = self._analyze_class(node, file_path)
                    if class_tools:
                        tools.extend(class_tools)

        except Exception as e:
            logger.debug(f"解析文件失败 {file_path}: {e}")

        return tools

    def _analyze_function(self, node: ast.FunctionDef, file_path: Path) -> dict[str, Any] | None:
        """分析函数是否是工具"""

        # 检查函数名
        if not any(keyword in node.name.lower() for keyword in
                   ["handler", "tool", "search", "retrieve", "parse", "analyze", "process"]):
            return None

        # 提取信息
        tool_info = {
            "name": node.name,
            "type": "function",
            "file": str(file_path.relative_to(self.project_root)),
            "line": node.lineno,
            "docstring": ast.get_docstring(node),
            "args": [arg.arg for arg in node.args.args],
            "is_registered": self._check_if_registered(node.name, str(file_path)),
        }

        return tool_info

    def _analyze_class(self, node: ast.ClassDef, file_path: Path) -> list[dict[str, Any]:
        """分析类是否包含工具"""

        tools = []

        # 检查类名
        if not any(keyword in node.name.lower() for keyword in
                   ["tool", "handler", "parser", "analyzer", "searcher"]):
            return tools

        # 查找类中的方法
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_name = item.name

                # 只关注公共方法
                if not method_name.startswith("_"):
                    tool_info = {
                        "name": f"{node.name}.{method_name}",
                        "type": "method",
                        "class": node.name,
                        "file": str(file_path.relative_to(self.project_root)),
                        "line": item.lineno,
                        "docstring": ast.get_docstring(item),
                    }
                    tools.append(tool_info)

        return tools

    def _check_if_registered(self, tool_name: str, file_path: str) -> bool:
        """检查工具是否已注册"""

        # 检查是否有@tool装饰器
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # 简单检查：查找@tool或register_tool
            if "@tool" in content or "register_tool" in content:
                return True

        except Exception:
            pass

        return False

    def categorize_tools(self, tools: list[dict[str, Any]) -> dict[str, list[dict[str, Any]]:
        """对工具进行分类"""

        categories = {
            "已注册": [],
            "未注册": [],
            "核心工具": [],
            "分析工具": [],
            "搜索工具": [],
            "其他": [],
        }

        for tool in tools:
            # 已注册工具
            if tool.get("is_registered"):
                categories["已注册"].append(tool)

            # 未注册工具
            else:
                categories["未注册"].append(tool)

            # 按功能分类
            name = tool["name"].lower()
            if any(kw in name for kw in ["search", "retrieve", "find"]):
                categories["搜索工具"].append(tool)
            elif any(kw in name for kw in ["analyze", "parser", "extract"]):
                categories["分析工具"].append(tool)
            elif any(kw in name for kw in ["patent", "document", "web"]):
                categories["核心工具"].append(tool)
            else:
                categories["其他"].append(tool)

        return categories

    def generate_report(self, tools: list[dict[str, Any], output_path: Path):
        """生成工具迁移报告"""

        categories = self.categorize_tools(tools)

        report = {
            "summary": {
                "total_tools": len(tools),
                "registered": len(categories["已注册"]),
                "unregistered": len(categories["未注册"]),
                "by_category": {
                    cat: len(tools_list)
                    for cat, tools_list in categories.items()
                    if cat != "已注册" and cat != "未注册"
                },
            },
            "categories": categories,
            "tools": tools,
        }

        # 保存报告
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 工具迁移报告已生成: {output_path}")

        return report


def main():
    """主函数"""

    print("=" * 80)
    print("🔍 工具迁移识别脚本")
    print("=" * 80)
    print()

    project_root = Path("/Users/xujian/Athena工作平台")
    identifier = ToolIdentifier(project_root)

    # 扫描工具
    logger.info("🔍 扫描core目录...")
    tools = identifier.scan_for_tools()
    logger.info(f"✅ 发现 {len(tools)} 个潜在工具")

    # 生成报告
    report_path = project_root / "reports" / "tool_migration_identification.json"
    identifier.generate_report(tools, report_path)

    # 打印摘要
    categories = identifier.categorize_tools(tools)
    print()
    print("📊 工具分类摘要:")
    print(f"   总计: {len(tools)}")
    print(f"   已注册: {len(categories['已注册'])}")
    print(f"   未注册: {len(categories['未注册'])}")
    print(f"   核心工具: {len(categories['核心工具'])}")
    print(f"   分析工具: {len(categories['分析工具'])}")
    print(f"   搜索工具: {len(categories['搜索工具'])}")
    print()

    print("✅ 识别完成")
    print(f"   报告路径: {report_path}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
