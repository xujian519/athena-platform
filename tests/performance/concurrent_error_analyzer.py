#!/usr/bin/env python3
"""
并发错误日志分析器
Concurrent Error Log Analyzer
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


class ConcurrentErrorAnalyzer:
    """并发错误分析器"""

    def __init__(self):
        self.error_patterns = {
            "connection_refused": re.compile(
                r"connection refused|connect.*refused|Connection.*refused", re.IGNORECASE
            ),
            "timeout": re.compile(r"timeout|timed out|Time.*out", re.IGNORECASE),
            "connection_pool": re.compile(
                r"pool.*exhaust|connection.*pool|pool.*full", re.IGNORECASE
            ),
            "concurrent_limit": re.compile(
                r"concurrent|parallel|simultaneous|too.*many", re.IGNORECASE
            ),
            "resource_exhaust": re.compile(
                r"out of memory|resource.*exhaust|disk.*full", re.IGNORECASE
            ),
            "deadlock": re.compile(r"deadlock|lock.*timeout|race.*condition", re.IGNORECASE),
            "database_error": re.compile(r"database|sql|sqlite|connection.*lost", re.IGNORECASE),
            "network_error": re.compile(r"network|socket|host.*unreachable|dns", re.IGNORECASE),
        }

        self.time_patterns = {
            "timestamp": re.compile(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})"),
            "iso_timestamp": re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"),
            "simple_time": re.compile(r"(\d{2}:\d{2}:\d{2})"),
        }

    def parse_log_line(self, line: str) -> dict[str, Any]:
        """解析日志行"""
        # 提取时间戳
        timestamp = None
        for pattern_name, pattern in self.time_patterns.items():
            match = pattern.search(line)
            if match:
                timestamp_str = match.group(1)
                try:
                    if pattern_name == "iso_timestamp":
                        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    else:
                        timestamp = datetime.strptime(
                            timestamp_str,
                            "%Y-%m-%d %H:%M:%S" if pattern_name == "timestamp" else "%H:%M:%S",
                        )
                except Exception:
                    continue
                break

        # 识别错误类型
        error_types = []
        for error_name, pattern in self.error_patterns.items():
            if pattern.search(line):
                error_types.append(error_name)

        # 检查是否为错误级别
        error_level = None
        if re.search(r"error|exception|failed|critical", line, re.IGNORECASE):
            error_level = "error"
        elif re.search(r"warning|warn", line, re.IGNORECASE):
            error_level = "warning"
        elif re.search(r"info", line, re.IGNORECASE):
            error_level = "info"

        return {
            "timestamp": timestamp.isoformat() if timestamp else None,
            "error_types": error_types,
            "error_level": error_level,
            "raw_line": line.strip(),
            "line_length": len(line.strip()),
        }

    def analyze_log_file(self, log_file_path: str, max_lines: int = 10000) -> dict[str, Any]:
        """分析单个日志文件"""
        try:
            with open(log_file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-max_lines:]  # 只分析最新的行

            parsed_lines = []
            error_frequency = defaultdict(int)
            hourly_errors = defaultdict(int)
            error_patterns = defaultdict(list)

            for line in lines:
                parsed = self.parse_log_line(line)
                parsed_lines.append(parsed)

                # 统计错误频率
                for error_type in parsed["error_types"]:
                    error_frequency[error_type] += 1
                    error_patterns[error_type].append(parsed)

            # 按小时统计错误
            if parsed["timestamp"] and parsed["error_types"]:
                ts = datetime.fromisoformat(parsed["timestamp"]) if isinstance(parsed["timestamp"], str) else parsed["timestamp"]
            hour_key = ts.strftime("%Y-%m-%d %H:00")
            hourly_errors[hour_key] += len(parsed["error_types"])

            # 分析并发模式
            concurrent_patterns = self.identify_concurrent_patterns(error_patterns, parsed_lines)

            return {
                "file_path": log_file_path,
                "total_lines_analyzed": len(lines),
                "error_lines": len([p for p in parsed_lines if p["error_types"]]),
                "error_frequency": dict(error_frequency),
                "hourly_errors": dict(hourly_errors),
                "concurrent_patterns": concurrent_patterns,
                "recent_errors": [p for p in parsed_lines if p["error_types"]][
                    -10:
                ],  # 最近10个错误
            }

        except Exception as e:
            return {"file_path": log_file_path, "error": str(e)}

    def identify_concurrent_patterns(
        self, error_patterns: dict[str, list], parsed_lines: list[dict]
    ) -> dict[str, Any]:
        """识别并发模式"""
        concurrent_insights = {
            "connection_issues": {},
            "timing_patterns": {},
            "error_sequences": {},
        }

        # 连接问题分析
        connection_errors = error_patterns.get("connection_refused", []) + error_patterns.get(
            "timeout", []
        )
        if connection_errors:
            concurrent_insights["connection_issues"] = {
                "total_occurrences": len(connection_errors),
                "peak_hour": self.find_peak_hour(connection_errors),
                "correlation_with_other_errors": self.find_error_correlation(
                    connection_errors, error_patterns
                ),
            }

        # 时间模式分析
        timing_errors = error_patterns.get("timeout", []) + error_patterns.get("deadlock", [])
        if timing_errors:
            concurrent_insights["timing_patterns"] = {
                "total_occurrences": len(timing_errors),
                "time_distribution": self.analyze_time_distribution(timing_errors),
                "frequent_sequences": self.find_error_sequences(timing_errors, parsed_lines),
            }

        # 资源竞争分析
        resource_errors = error_patterns.get("concurrent_limit", []) + error_patterns.get(
            "resource_exhaust", []
        )
        if resource_errors:
            concurrent_insights["resource_contention"] = {
                "total_occurrences": len(resource_errors),
                "patterns": [e["raw_line"] for e in resource_errors[:5]],  # 前5个例子
            }

        return concurrent_insights

    def find_peak_hour(self, errors: list[dict]) -> str:
        """找出错误发生的高峰时间"""
        hour_counts = defaultdict(int)
        for error in errors:
            if error["timestamp"]:
                hour_key = error["timestamp"].strftime("%H:00")
                hour_counts[hour_key] += 1

        if hour_counts:
            return max(hour_counts.items(), key=lambda x: x[1])[0]
        return "未知"

    def find_error_correlation(
        self, target_errors: list[dict], all_error_patterns: dict[str, list]
    ) -> dict[str, int]:
        """找出与其他错误的相关性"""
        correlations = {}
        target_timestamps = [e["timestamp"] for e in target_errors if e["timestamp"]]

        for error_type, errors in all_error_patterns.items():
            if error_type in ["connection_refused", "timeout"]:
                continue

            correlated_count = 0
            for error in errors:
                if error["timestamp"]:
                    for target_ts in target_timestamps:
                        time_diff = abs((error["timestamp"] - target_ts).total_seconds())
                        if time_diff < 60:  # 1分钟内
                            correlated_count += 1
                            break

            if correlated_count > 0:
                correlations[error_type] = correlated_count

        return correlations

    def analyze_time_distribution(self, errors: list[dict]) -> dict[str, Any]:
        """分析时间分布"""
        if not errors:
            return {}

        timestamps = [e["timestamp"] for e in errors if e["timestamp"]]
        if not timestamps:
            return {}

        # 按小时分组
        hourly_dist = defaultdict(int)
        for ts in timestamps:
            hourly_dist[ts.strftime("%H")] += 1

        return {
            "peak_hours": dict(sorted(hourly_dist.items(), key=lambda x: x[1], reverse=True)[:3]),
            "total_span_hours": (max(timestamps) - min(timestamps)).total_seconds() / 3600
            if len(timestamps) > 1
            else 0,
        }

    def find_error_sequences(self, target_errors: list[dict], all_lines: list[dict]) -> list[str]:
        """找出错误序列模式"""
        sequences = []
        target_timestamps = {e["timestamp"]: e for e in target_errors if e["timestamp"]}

        for ts, _error in target_timestamps.items():
            # 查找错误前后5分钟内的其他错误
            surrounding_errors = []
            for line in all_lines:
                if line["timestamp"] and line["error_types"]:
                    time_diff = abs((line["timestamp"] - ts).total_seconds())
                    if 0 < time_diff <= 300:  # 5分钟内
                        surrounding_errors.append(
                            f"{line['timestamp'].strftime('%H:%M:%S')}:{line['error_types']}"
                        )

            if surrounding_errors:
                sequences.append(
                    f"目标错误 {ts.strftime('%H:%M:%S')} 周围错误: {surrounding_errors[:3]}"
                )

        return sequences[:3]  # 返回前3个序列

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
                "concurrent_issues": {},
                "recommendations": [],
            },
        }

        # 分析每个日志文件
        for log_file in all_logs:
            print(f"📋 分析日志文件: {log_file.name}")
            result = self.analyze_log_file(str(log_file))
            analysis_results["file_analyses"][log_file.name] = result

            if "error_frequency" in result:
                for error_type, count in result["error_frequency"].items():
                    analysis_results["summary"]["total_errors"] += count
                    if error_type in analysis_results["summary"]["most_common_errors"]:
                        analysis_results["summary"]["most_common_errors"][error_type] += count
                    else:
                        analysis_results["summary"]["most_common_errors"][error_type] = count

        # 生成并发问题摘要
        analysis_results["summary"]["concurrent_issues"] = self.generate_concurrent_summary(
            analysis_results["file_analyses"]
        )

        # 生成优化建议
        analysis_results["summary"]["recommendations"] = self.generate_recommendations(
            analysis_results["summary"]
        )

        return analysis_results

    def generate_concurrent_summary(self, file_analyses: dict[str, Any]) -> dict[str, Any]:
        """生成并发问题摘要"""
        concurrent_summary = {
            "connection_issues": 0,
            "timeout_issues": 0,
            "resource_contention": 0,
            "database_issues": 0,
            "affected_files": [],
        }

        for file_name, analysis in file_analyses.items():
            if "concurrent_patterns" in analysis:
                patterns = analysis["concurrent_patterns"]

                if "connection_issues" in patterns:
                    concurrent_summary["connection_issues"] += patterns["connection_issues"].get(
                        "total_occurrences", 0
                    )
                    concurrent_summary["affected_files"].append(file_name)

                if "timing_patterns" in patterns:
                    concurrent_summary["timeout_issues"] += patterns["timing_patterns"].get(
                        "total_occurrences", 0
                    )

                if "resource_contention" in patterns:
                    concurrent_summary["resource_contention"] += patterns[
                        "resource_contention"
                    ].get("total_occurrences", 0)

        # 统计数据库问题
        for file_name, analysis in file_analyses.items():
            if "error_frequency" in analysis and "database_error" in analysis["error_frequency"]:
                concurrent_summary["database_issues"] += analysis["error_frequency"][
                    "database_error"
                ]

        return concurrent_summary

    def generate_recommendations(self, summary: dict[str, Any]) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # 基于错误频率的建议
        if summary.get("most_common_errors", {}):
            most_common = max(summary["most_common_errors"].items(), key=lambda x: x[1])
            if most_common[1] > 10:
                recommendations.append(
                    f"🚨 最常见错误类型 '{most_common[0]}' 发生了 {most_common[1]} 次，需要优先处理"
                )

        # 并发问题建议
        concurrent_issues = summary.get("concurrent_issues", {})
        if concurrent_issues.get("connection_issues", 0) > 5:
            recommendations.append(
                "🔗 检测到频繁的连接问题，建议：\n   - 增加连接池大小\n   - 优化连接超时设置\n   - 实现连接重试机制"
            )

        if concurrent_issues.get("timeout_issues", 0) > 5:
            recommendations.append(
                "⏱️ 检测到频繁的超时问题，建议：\n   - 优化查询性能\n   - 调整超时阈值\n   - 实现异步处理"
            )

        if concurrent_issues.get("resource_contention", 0) > 3:
            recommendations.append(
                "🔄 检测到资源竞争问题，建议：\n   - 实现更好的锁机制\n   - 优化资源分配\n   - 增加资源监控"
            )

        if concurrent_issues.get("database_issues", 0) > 5:
            recommendations.append(
                "🗄️ 检测到数据库相关错误，建议：\n   - 优化数据库查询\n   - 添加适当的索引\n   - 实现数据库连接池"
            )

        # 通用建议
        recommendations.extend(
            [
                "📊 建议实现实时错误监控和告警系统",
                "🔍 定期进行性能基准测试",
                "🛠️ 实现优雅的错误恢复机制",
                "📝 改进日志记录，包含更详细的上下文信息",
            ]
        )

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

    analyzer = ConcurrentErrorAnalyzer()

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
    print(f"❌ 总共发现 {summary['total_errors']} 个错误")

    if summary["most_common_errors"]:
        print("\n🏆 最常见的错误类型:")
        for error_type, count in sorted(
            summary["most_common_errors"].items(), key=lambda x: x[1], reverse=True
        )[:5]:
            print(f"   {error_type}: {count} 次")

    concurrent_issues = summary.get("concurrent_issues", {})
    if any(concurrent_issues.values()):
        print("\n⚠️ 并发问题统计:")
        if concurrent_issues.get("connection_issues", 0) > 0:
            print(f"   🔗 连接问题: {concurrent_issues['connection_issues']} 次")
        if concurrent_issues.get("timeout_issues", 0) > 0:
            print(f"   ⏱️ 超时问题: {concurrent_issues['timeout_issues']} 次")
        if concurrent_issues.get("resource_contention", 0) > 0:
            print(f"   🔄 资源竞争: {concurrent_issues['resource_contention']} 次")
        if concurrent_issues.get("database_issues", 0) > 0:
            print(f"   🗄️ 数据库问题: {concurrent_issues['database_issues']} 次")

    print("\n💡 主要优化建议:")
    for i, rec in enumerate(summary["recommendations"][:3]):
        print(f"   {i + 1}. {rec}")

    print(f"\n📋 详细报告: {report_file}")


if __name__ == "__main__":
    main()
