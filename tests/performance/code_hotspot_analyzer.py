#!/usr/bin/env python3
"""
代码热点和性能瓶颈分析器
Code Hotspot and Performance Bottleneck Analyzer
"""

import ast
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


class CodeHotspotAnalyzer:
    """代码热点分析器"""

    def __init__(self):
        self.complexity_patterns = {
            "nested_loops": r"for.*:\s*\n\s*for|while.*:\s*\n\s*while|for.*:\s*\n\s*if.*:\s*\n\s*for",
            "multiple_except": r"except.*:\s*\n.*except.*:\s*\n.*except",
            "deep_recursion": r"def.*:\s*\n.*return.*\(",
            "complex_condition": r"if.*and.*and|if.*or.*or.*or",
            "large_function": r"def.*\(.*,\s*.*,\s*.*,\s*.*,\s*.*\):",
            "database_operations": r"execute|fetchall|commit|cursor",
            "file_operations": r"open\(|read\(|write\(|\.close\(",
            "network_operations": r"requests\.|urllib\.|http\.|socket\.",
            "json_operations": r"json\.loads|json\.dumps|json\.load|json\.dump",
        }

        self.performance_antipatterns = {
            "inefficient_loops": r"for.*in.*range\(len\(|for.*in.*\.keys\(\)",
            "string_concatenation": r"\+.*\+|\+=.*\+",
            "regex_compilation": r"re\.\w+\(",
            "repeated_calculation": r"len\(.*\).*len\(|sum\(.*\).*sum\(",
            "blocking_io": r"requests\.(get|post)|urllib\.request|open\(",
            "memory_intensive": r"\.copy\(\)|list\(.*\)|dict\(.*\)",
        }

    def analyze_file_complexity(self, file_path: str) -> dict[str, Any]:
        """分析文件复杂度"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # 基础统计
            lines = content.split("\n")
            code_lines = [
                line for line in lines if line.strip() and not line.strip().startswith("#")
            ]
            total_lines = len(lines)
            code_line_count = len(code_lines)

            # 复杂度指标
            complexity_indicators = defaultdict(int)

            for pattern_name, pattern in self.complexity_patterns.items():
                matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
                complexity_indicators[pattern_name] = len(matches)

            # 反模式检测
            antipatterns = defaultdict(int)
            for pattern_name, pattern in self.performance_antipatterns.items():
                matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
                antipatterns[pattern_name] = len(matches)

            # 函数分析
            try:
                tree = ast.parse(content)
                functions = []
                classes = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_info = self.analyze_function(node, content)
                        functions.append(func_info)
                    elif isinstance(node, ast.ClassDef):
                        class_info = self.analyze_class(node, content)
                        classes.append(class_info)
            except Exception:
                functions = []
                classes = []

            return {
                "file_path": file_path,
                "file_size_kb": os.path.getsize(file_path) / 1024,
                "total_lines": total_lines,
                "code_lines": code_line_count,
                "complexity_indicators": dict(complexity_indicators),
                "performance_antipatterns": dict(antipatterns),
                "functions": functions,
                "classes": classes,
                "complexity_score": self.calculate_complexity_score(
                    complexity_indicators, antipatterns
                ),
            }

        except Exception as e:
            return {"file_path": file_path, "error": str(e)}

    def analyze_function(self, node: ast.FunctionDef, content: str) -> dict[str, Any]:
        """分析函数"""
        # 获取函数源码
        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, "end_lineno") else start_line + 10
        lines = content.split("\n")[start_line:end_line]
        func_content = "\n".join(lines)

        # 计算圈复杂度
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.ExceptHandler)):
                complexity += 1

        # 参数数量
        args_count = len(node.args.args)

        # 文档字符串
        has_docstring = ast.get_docstring(node) is not None or (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Str)
        )

        return {
            "name": node.name,
            "line": node.lineno,
            "args_count": args_count,
            "complexity": complexity,
            "has_docstring": has_docstring,
            "lines_count": len(lines),
            "content_sample": func_content[:200] + "..."
            if len(func_content) > 200
            else func_content,
        }

    def analyze_class(self, node: ast.ClassDef, content: str) -> dict[str, Any]:
        """分析类"""
        # 获取类源码
        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, "end_lineno") else start_line + 10
        lines = content.split("\n")[start_line:end_line]

        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]

        return {
            "name": node.name,
            "line": node.lineno,
            "methods_count": len(methods),
            "lines_count": len(lines),
            "methods": [m.name for m in methods],
        }

    def calculate_complexity_score(
        self, complexity_indicators: dict[str, int], antipatterns: dict[str, int]
    ) -> float:
        """计算复杂度评分"""
        # 复杂度指标权重
        complexity_weights = {
            "nested_loops": 3,
            "multiple_except": 2,
            "deep_recursion": 4,
            "complex_condition": 2,
            "large_function": 1,
            "database_operations": 2,
            "file_operations": 1,
            "network_operations": 3,
            "json_operations": 1,
        }

        # 反模式权重
        antipattern_weights = {
            "inefficient_loops": 3,
            "string_concatenation": 2,
            "regex_compilation": 2,
            "repeated_calculation": 2,
            "blocking_io": 4,
            "memory_intensive": 2,
        }

        complexity_score = 0.0
        for indicator, count in complexity_indicators.items():
            complexity_score += count * complexity_weights.get(indicator, 1)

        for antipattern, count in antipatterns.items():
            complexity_score += count * antipattern_weights.get(antipattern, 1)

        return complexity_score

    def analyze_codebase(self, root_path: str = "/Users/xujian/Athena工作平台") -> dict[str, Any]:
        """分析整个代码库"""
        print("🔍 开始分析代码库热点...")

        # 查找Python文件
        python_files = []
        for root, dirs, files in os.walk(root_path):
            # 跳过某些目录
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in ["__pycache__", "node_modules", ".git", "venv", "env"]
            ]

            for file in files:
                if file.endswith(".py") and not file.startswith("."):
                    file_path = os.path.join(root, file)
                    # 只分析主要目录
                    if any(
                        keyword in file_path.lower()
                        for keyword in ["core", "service", "api", "agent", "cognition", "memory"]
                    ):
                        python_files.append(file_path)

        print(f"📁 找到 {len(python_files)} 个Python文件")

        # 分析每个文件
        file_analyses = {}
        hotspots = []

        for file_path in python_files[:50]:  # 限制分析文件数量
            print(f"📋 分析文件: {Path(file_path).name}")
            analysis = self.analyze_file_complexity(file_path)
            file_analyses[Path(file_path).name] = analysis

            # 识别热点
            if "complexity_score" in analysis and analysis["complexity_score"] > 10:
                hotspots.append(
                    {
                        "file": Path(file_path).name,
                        "path": file_path,
                        "complexity_score": analysis["complexity_score"],
                        "lines": analysis.get("code_lines", 0),
                        "size_kb": analysis.get("file_size_kb", 0),
                        "top_issues": self.get_top_issues(analysis),
                    }
                )

        # 排序热点
        hotspots.sort(key=lambda x: x["complexity_score"], reverse=True)

        # 生成建议
        recommendations = self.generate_optimization_recommendations(file_analyses, hotspots)

        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_files_analyzed": len(file_analyses),
            "file_analyses": file_analyses,
            "hotspots": hotspots[:20],  # 前20个热点
            "summary": {
                "average_complexity": sum(h["complexity_score"] for h in hotspots) / len(hotspots)
                if hotspots
                else 0,
                "highest_complexity": max(h["complexity_score"] for h in hotspots)
                if hotspots
                else 0,
                "total_issues": sum(len(h["top_issues"]) for h in hotspots),
            },
            "recommendations": recommendations,
        }

    def get_top_issues(self, analysis: dict[str, Any]) -> list[str]:
        """获取主要问题"""
        issues = []

        complexity_indicators = analysis.get("complexity_indicators", {})
        for indicator, count in complexity_indicators.items():
            if count > 0:
                issues.append(f"{indicator}: {count}")

        antipatterns = analysis.get("performance_antipatterns", {})
        for antipattern, count in antipatterns.items():
            if count > 0:
                issues.append(f"{antipattern}: {count}")

        return sorted(
            issues, key=lambda x: int(x.split(": ")[1]) if ": " in x else 0, reverse=True
        )[:5]

    def generate_optimization_recommendations(
        self, file_analyses: dict[str, Any], hotspots: list[dict]
    ) -> list[str]:
        """生成优化建议"""
        recommendations = []

        if not hotspots:
            recommendations.append("✅ 未发现明显的代码热点，代码质量良好")
            return recommendations

        # 基于热点类型的建议
        total_database_ops = sum(
            analysis.get("complexity_indicators", {}).get("database_operations", 0)
            for analysis in file_analyses.values()
            if "complexity_indicators" in analysis
        )

        total_network_ops = sum(
            analysis.get("complexity_indicators", {}).get("network_operations", 0)
            for analysis in file_analyses.values()
            if "complexity_indicators" in analysis
        )

        total_blocking_io = sum(
            analysis.get("performance_antipatterns", {}).get("blocking_io", 0)
            for analysis in file_analyses.values()
            if "performance_antipatterns" in analysis
        )

        if total_database_ops > 20:
            recommendations.append(
                f"🗄️ 检测到大量数据库操作({total_database_ops}次)，建议：\n"
                f"   - 使用连接池管理数据库连接\n"
                f"   - 实现查询缓存\n"
                f"   - 优化SQL查询，添加适当索引"
            )

        if total_network_ops > 15:
            recommendations.append(
                f"🌐 检测到大量网络操作({total_network_ops}次)，建议：\n"
                f"   - 实现异步请求处理\n"
                f"   - 添加请求重试机制\n"
                f"   - 使用连接池和会话复用"
            )

        if total_blocking_io > 10:
            recommendations.append(
                f"⏱️ 检测到阻塞性IO操作({total_blocking_io}次)，建议：\n"
                f"   - 使用异步IO操作\n"
                f"   - 实现并行处理\n"
                f"   - 添加超时控制"
            )

        # 函数复杂度建议
        complex_functions = []
        for analysis in file_analyses.values():
            if "functions" in analysis:
                for func in analysis["functions"]:
                    if func.get("complexity", 0) > 10:
                        complex_functions.append(func["name"])

        if len(complex_functions) > 5:
            recommendations.append(
                f"🔧 发现{len(complex_functions)}个复杂函数，建议：\n"
                f"   - 重构复杂函数，拆分为小函数\n"
                f"   - 减少函数嵌套层级\n"
                f"   - 提取公共逻辑为独立函数"
            )

        # 性能反模式建议
        inefficient_loops = sum(
            analysis.get("performance_antipatterns", {}).get("inefficient_loops", 0)
            for analysis in file_analyses.values()
            if "performance_antipatterns" in analysis
        )

        if inefficient_loops > 5:
            recommendations.append(
                f"🔄 检测到低效循环模式({inefficient_loops}次)，建议：\n"
                f"   - 使用列表推导式替代for循环\n"
                f"   - 避免在循环中重复计算\n"
                f"   - 使用生成器减少内存占用"
            )

        # 通用建议
        recommendations.extend(
            [
                "📊 建议使用性能分析工具(cProfile, line_profiler)进行详细分析",
                "🧪 实施单元测试和性能测试覆盖热点代码",
                "📝 添加性能监控和日志记录",
                "🔍 定期进行代码审查，识别性能瓶颈",
            ]
        )

        return recommendations

    def save_results(self, results: dict[str, Any], filename: str = None):
        """保存分析结果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"code_hotspot_analysis_{timestamp}.json"

        reports_dir = Path("/Users/xujian/Athena工作平台/tests/reports")
        reports_dir.mkdir(exist_ok=True)

        report_file = reports_dir / filename
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"📄 代码热点分析报告已保存: {report_file}")
        return str(report_file)


def main():
    """主函数"""
    print("🔍 开始代码热点和性能瓶颈分析...")
    print("=" * 60)

    analyzer = CodeHotspotAnalyzer()

    # 分析代码库
    results = analyzer.analyze_codebase()

    # 保存结果
    report_file = analyzer.save_results(results)

    # 显示摘要
    print("\n" + "=" * 60)
    print("📊 代码热点分析摘要")
    print("=" * 60)

    summary = results["summary"]
    hotspots = results["hotspots"]

    print(f"📁 分析了 {results['total_files_analyzed']} 个文件")
    print(f"🔥 发现 {len(hotspots)} 个代码热点")
    print(f"📈 平均复杂度: {summary['average_complexity']:.2f}")
    print(f"⚡ 最高复杂度: {summary['highest_complexity']:.2f}")
    print(f"❌ 总问题数: {summary['total_issues']}")

    if hotspots:
        print("\n🏆 前5个代码热点:")
        for i, hotspot in enumerate(hotspots[:5], 1):
            print(f"   {i}. {hotspot['file']} (复杂度: {hotspot['complexity_score']:.1f})")
            print(f"      路径: {hotspot['path']}")
            print(f"      主要问题: {', '.join(hotspot['top_issues'][:3])}")

    print("\n💡 主要优化建议:")
    recommendations = results["recommendations"]
    for i, rec in enumerate(recommendations[:3]):
        print(f"   {i + 1}. {rec}")

    print(f"\n📋 详细报告: {report_file}")


if __name__ == "__main__":
    main()
