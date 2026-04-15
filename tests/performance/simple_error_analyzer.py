#!/usr/bin/env python3
"""
简化的并发错误日志分析器
Simplified Concurrent Error Log Analyzer
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


class SimpleErrorAnalyzer:
    """简化的错误分析器"""

    def __init__(self):
        self.error_patterns = {
            "connection_refused": re.compile(
                r"connection refused|connect.*refused|Connection.*refused", re.IGNORECASE
            ),
            "timeout": re.compile(r"timeout|timed out|Time.*out", re.IGNORECASE),
            "concurrent_limit": re.compile(
                r"concurrent|parallel|simultaneous|too.*many", re.IGNORECASE
            ),
            "resource_exhaust": re.compile(
                r"out of memory|resource.*exhaust|disk.*full", re.IGNORECASE
            ),
            "database_error": re.compile(r"database|sql|sqlite|connection.*lost", re.IGNORECASE),
            "network_error": re.compile(r"network|socket|host.*unreachable|dns", re.IGNORECASE),
        }

    def analyze_log_file(self, log_file_path: str, max_lines: int = 1000) -> dict[str, Any]:
        """分析单个日志文件"""
        try:
            with open(log_file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-max_lines:]

            error_count = 0
            error_types = defaultdict(int)
            sample_errors = []

            for line_num, line in enumerate(lines, 1):
                line_errors = []
                for error_name, pattern in self.error_patterns.items():
                    if pattern.search(line):
                        line_errors.append(error_name)
                        error_types[error_name] += 1

                if line_errors:
                    error_count += 1
                    if len(sample_errors) < 5:  # 只保存前5个样本
                        sample_errors.append(
                            {
                                "line_number": line_num,
                                "error_types": line_errors,
                                "content": line.strip()[:200] + "..."
                                if len(line.strip()) > 200
                                else line.strip(),
                            }
                        )

            return {
                "file_path": log_file_path,
                "total_lines": len(lines),
                "error_count": error_count,
                "error_types": dict(error_types),
                "sample_errors": sample_errors,
            }

        except Exception as e:
            return {"file_path": log_file_path, "error": str(e)}

    def analyze_all_logs(self) -> dict[str, Any]:
        """分析所有日志文件"""
        log_directories = [
            "/Users/xujian/Athena工作平台/data/logs",
            "/Users/xujian/Athena工作平台/logs",
        ]

        all_logs = []
        for log_dir in log_directories:
            if Path(log_dir).exists():
                all_logs.extend(Path(log_dir).glob("*.log"))

        analysis_results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_log_files": len(all_logs),
            "file_analyses": {},
            "summary": {
                "total_errors": 0,
                "most_common_errors": {},
                "files_with_errors": 0,
                "recommendations": [],
            },
        }

        # 分析每个日志文件
        for log_file in all_logs:
            print(f"📋 分析日志文件: {log_file.name}")
            result = self.analyze_log_file(str(log_file))
            analysis_results["file_analyses"][log_file.name] = result

            if "error_count" in result and result["error_count"] > 0:
                analysis_results["summary"]["files_with_errors"] += 1
                analysis_results["summary"]["total_errors"] += result["error_count"]

                for error_type, count in result["error_types"].items():
                    if error_type in analysis_results["summary"]["most_common_errors"]:
                        analysis_results["summary"]["most_common_errors"][error_type] += count
                    else:
                        analysis_results["summary"]["most_common_errors"][error_type] = count

        # 生成优化建议
        analysis_results["summary"]["recommendations"] = self.generate_recommendations(
            analysis_results["summary"]
        )

        return analysis_results

    def generate_recommendations(self, summary: dict[str, Any]) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # 基于错误频率的建议
        if summary.get("most_common_errors", {}):
            most_common = max(summary["most_common_errors"].items(), key=lambda x: x[1])
            if most_common[1] > 5:
                recommendations.append(
                    f"🚨 最常见错误类型 '{most_common[0]}' 发生了 {most_common[1]} 次，需要优先处理"
                )

        # 具体错误类型的建议
        error_types = summary.get("most_common_errors", {})
        if "connection_refused" in error_types and error_types["connection_refused"] > 3:
            recommendations.append(
                "🔗 检测到频繁的连接拒绝错误，建议：\n   - 检查服务是否正常运行\n   - 增加连接池大小\n   - 实现连接重试机制"
            )

        if "timeout" in error_types and error_types["timeout"] > 3:
            recommendations.append(
                "⏱️ 检测到频繁的超时错误，建议：\n   - 优化查询性能\n   - 调整超时阈值\n   - 实现异步处理"
            )

        if "concurrent_limit" in error_types and error_types["concurrent_limit"] > 2:
            recommendations.append(
                "🔄 检测到并发限制错误，建议：\n   - 增加并发处理能力\n   - 实现请求队列\n   - 优化资源分配"
            )

        if "resource_exhaust" in error_types and error_types["resource_exhaust"] > 2:
            recommendations.append(
                "💾 检测到资源耗尽错误，建议：\n   - 增加系统内存\n   - 优化内存使用\n   - 实现资源监控"
            )

        if "database_error" in error_types and error_types["database_error"] > 3:
            recommendations.append(
                "🗄️ 检测到数据库错误，建议：\n   - 优化数据库查询\n   - 添加适当的索引\n   - 实现数据库连接池"
            )

        if "network_error" in error_types and error_types["network_error"] > 3:
            recommendations.append(
                "🌐 检测到网络错误，建议：\n   - 检查网络连接\n   - 实现重试机制\n   - 添加网络监控"
            )

        # 通用建议
        if summary["files_with_errors"] > 0:
            recommendations.extend(
                [
                    "📊 建议实现实时错误监控和告警系统",
                    "🔍 定期进行性能基准测试",
                    "🛠️ 实现优雅的错误恢复机制",
                    "📝 改进日志记录，包含更详细的上下文信息",
                ]
            )
        else:
            recommendations.append("✅ 未检测到明显的并发错误，系统运行正常")

        return recommendations

    def save_results(self, results: dict[str, Any], filename: str = None):
        """保存分析结果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"concurrent_error_analysis_{timestamp}.json"

        reports_dir = Path("/Users/xujian/Athena工作平台/tests/reports")
        reports_dir.mkdir(exist_ok=True)

        report_file = reports_dir / filename
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"📄 并发错误分析报告已保存: {report_file}")
        return str(report_file)


def main():
    """主函数"""
    print("🔍 开始并发错误日志分析...")
    print("=" * 60)

    analyzer = SimpleErrorAnalyzer()

    # 分析所有日志
    results = analyzer.analyze_all_logs()

    # 保存结果
    report_file = analyzer.save_results(results)

    # 显示摘要
    print("\n" + "=" * 60)
    print("📊 并发错误分析摘要")
    print("=" * 60)

    summary = results["summary"]
    print(f"📁 分析了 {results['total_log_files']} 个日志文件")
    print(f"📄 发现错误的文件: {summary['files_with_errors']} 个")
    print(f"❌ 总共发现 {summary['total_errors']} 个错误")

    if summary["most_common_errors"]:
        print("\n🏆 最常见的错误类型:")
        for error_type, count in sorted(
            summary["most_common_errors"].items(), key=lambda x: x[1], reverse=True
        ):
            print(f"   {error_type}: {count} 次")

    print("\n💡 主要优化建议:")
    for i, rec in enumerate(summary["recommendations"][:3]):
        print(f"   {i + 1}. {rec}")

    print(f"\n📋 详细报告: {report_file}")


if __name__ == "__main__":
    main()
