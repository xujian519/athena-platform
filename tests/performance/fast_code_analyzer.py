#!/usr/bin/env python3
"""
快速代码热点分析器
Fast Code Hotspot Analyzer
"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


class FastCodeAnalyzer:
    """快速代码分析器"""

    def __init__(self):
        self.performance_patterns = {
            "database_operations": r"execute|fetchall|commit|cursor|\.query\(|\.find\(",
            "blocking_io": r"open\(|requests\.(get|post)|urllib\.|\.read\(|\.write\(",
            "complex_loops": r"for.*:\s*\n.*for|while.*:\s*\n.*while",
            "exception_handling": r"try.*:.*except.*:.*finally",
            "nested_functions": r"def.*:\s*\n.*def.*:\s*\n.*def",
            "string_operations": r"\+.*\+|\.format\(|f\"",
            "list_operations": r"\.append\(.*\)\.append|\.extend\(.*\)\.extend",
            "regex_operations": r"re\.\w+\(|re\.compile\(",
        }

    def quick_analyze_file(self, file_path: str) -> dict[str, Any]:
        """快速分析文件"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # 基础统计
            lines = content.split("\n")
            code_lines = [
                line for line in lines if line.strip() and not line.strip().startswith("#")
            ]

            # 性能模式计数
            pattern_counts = {}
            for pattern_name, pattern in self.performance_patterns.items():
                matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
                pattern_counts[pattern_name] = len(matches)

            # 函数统计
            func_matches = re.findall(r"def\s+(\w+)\s*\(", content)

            # 类统计
            class_matches = re.findall(r"class\s+(\w+)\s*[:(]", content)

            # 计算复杂度评分
            complexity_score = self.calculate_simple_complexity(pattern_counts, len(code_lines))

            return {
                "file": Path(file_path).name,
                "path": file_path,
                "total_lines": len(lines),
                "code_lines": len(code_lines),
                "functions": len(func_matches),
                "classes": len(class_matches),
                "patterns": pattern_counts,
                "complexity_score": complexity_score,
                "size_kb": os.path.getsize(file_path) / 1024,
            }

        except Exception as e:
            return {"file": Path(file_path).name, "path": file_path, "error": str(e)}

    def calculate_simple_complexity(self, patterns: dict[str, int], code_lines: int) -> float:
        """计算简单复杂度"""
        weights = {
            "database_operations": 3,
            "blocking_io": 4,
            "complex_loops": 3,
            "exception_handling": 2,
            "nested_functions": 4,
            "string_operations": 1,
            "list_operations": 2,
            "regex_operations": 2,
        }

        score = 0.0
        for pattern, count in patterns.items():
            score += count * weights.get(pattern, 1)

        # 基于代码行数的复杂度
        if code_lines > 500:
            score += code_lines / 100

        return score

    def analyze_core_files(self, root_path: str = "/Users/xujian/Athena工作平台") -> dict[str, Any]:
        """分析核心文件"""
        print("🔍 快速分析核心文件...")

        # 目标文件模式

        # 收集文件
        files_to_analyze = []
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
                    # 检查是否匹配目标模式
                    if any(
                        keyword in file_path.lower()
                        for keyword in ["core", "service", "api", "agent"]
                    ):
                        files_to_analyze.append(file_path)

        print(f"📁 找到 {len(files_to_analyze)} 个文件")

        # 分析文件
        analyses = []
        hotspots = []

        for file_path in files_to_analyze[:30]:  # 限制数量
            print(f"📋 分析: {Path(file_path).name}")
            analysis = self.quick_analyze_file(file_path)
            analyses.append(analysis)

            # 识别热点
            if "complexity_score" in analysis and analysis["complexity_score"] > 5:
                hotspots.append(analysis)

        # 排序热点
        hotspots.sort(key=lambda x: x["complexity_score"], reverse=True)

        # 生成建议
        recommendations = self.generate_recommendations(analyses, hotspots)

        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_files": len(analyses),
            "hotspots": hotspots[:10],
            "pattern_summary": self.summarize_patterns(analyses),
            "recommendations": recommendations,
        }

    def summarize_patterns(self, analyses: list[dict]) -> dict[str, int]:
        """总结模式"""
        summary = defaultdict(int)
        for analysis in analyses:
            if "patterns" in analysis:
                for pattern, count in analysis["patterns"].items():
                    summary[pattern] += count
        return dict(summary)

    def generate_recommendations(self, analyses: list[dict], hotspots: list[dict]) -> list[str]:
        """生成优化建议"""
        recommendations = []

        if not hotspots:
            recommendations.append("✅ 未发现明显的性能热点")
            return recommendations

        # 基于模式分析的推荐
        pattern_summary = self.summarize_patterns(analyses)

        if pattern_summary.get("database_operations", 0) > 10:
            recommendations.append(
                "🗄️ 检测到数据库操作，建议：\n   - 使用连接池\n   - 实现查询缓存\n   - 优化SQL语句"
            )

        if pattern_summary.get("blocking_io", 0) > 15:
            recommendations.append(
                "⏱️ 检测到阻塞性IO，建议：\n   - 使用异步IO\n   - 实现超时控制\n   - 添加错误重试"
            )

        if pattern_summary.get("complex_loops", 0) > 5:
            recommendations.append(
                "🔄 检测到复杂循环，建议：\n"
                "   - 简化循环逻辑\n"
                "   - 避免深层嵌套\n"
                "   - 使用高效的数据结构"
            )

        # 基于热点的推荐
        high_complexity_files = [h for h in hotspots if h["complexity_score"] > 15]
        if high_complexity_files:
            recommendations.append(
                f"🔧 发现{len(high_complexity_files)}个高复杂度文件，建议：\n"
                "   - 重构复杂逻辑\n"
                "   - 拆分大函数\n"
                "   - 提取公共模块"
            )

        # 通用建议
        recommendations.extend(
            [
                "📊 使用性能分析工具进行详细分析",
                "🧪 添加性能测试覆盖热点代码",
                "📝 实现性能监控和告警",
            ]
        )

        return recommendations

    def save_results(self, results: dict[str, Any], filename: str = None):
        """保存结果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fast_code_hotspot_analysis_{timestamp}.json"

        reports_dir = Path("/Users/xujian/Athena工作平台/tests/reports")
        reports_dir.mkdir(exist_ok=True)

        report_file = reports_dir / filename
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"📄 代码热点分析报告已保存: {report_file}")
        return str(report_file)


def main():
    """主函数"""
    print("🚀 开始快速代码热点分析...")
    print("=" * 50)

    analyzer = FastCodeAnalyzer()

    # 分析核心文件
    results = analyzer.analyze_core_files()

    # 保存结果
    report_file = analyzer.save_results(results)

    # 显示摘要
    print("\n" + "=" * 50)
    print("📊 代码热点分析摘要")
    print("=" * 50)

    hotspots = results["hotspots"]
    pattern_summary = results["pattern_summary"]

    print(f"📁 分析了 {results['total_files']} 个文件")
    print(f"🔥 发现 {len(hotspots)} 个热点")

    if hotspots:
        print("\n🏆 前5个热点:")
        for i, hotspot in enumerate(hotspots[:5], 1):
            print(f"   {i}. {hotspot['file']} (复杂度: {hotspot['complexity_score']:.1f})")
            print(f"      路径: {hotspot['path']}")
            print(f"      代码行: {hotspot['code_lines']}")

    print("\n📈 模式统计:")
    for pattern, count in sorted(pattern_summary.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   {pattern}: {count}")

    print("\n💡 优化建议:")
    for i, rec in enumerate(results["recommendations"][:3], 1):
        print(f"   {i}. {rec}")

    print(f"\n📋 详细报告: {report_file}")


if __name__ == "__main__":
    main()
