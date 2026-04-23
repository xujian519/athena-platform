#!/usr/bin/env python3
from __future__ import annotations
"""
搜索性能监控系统
Search Performance Monitoring System

实时监控搜索服务的性能指标,收集统计数据,提供优化建议
作者: Athena AI Team
创建时间: 2026-01-09
版本: v1.0.0
"""

import asyncio
import contextlib
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""

    COUNTER = "counter"  # 计数器
    GAUGE = "gauge"  # 仪表盘
    HISTOGRAM = "histogram"  # 直方图
    SUMMARY = "summary"  # 摘要


@dataclass
class PerformanceMetric:
    """性能指标"""

    name: str  # 指标名称
    type: MetricType  # 指标类型
    value: float  # 当前值
    timestamp: float = field(default_factory=time.time)
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "metadata": self.metadata,
        }


@dataclass
class SearchRecord:
    """搜索记录"""

    query: str  # 查询文本
    query_length: int  # 查询长度
    complexity: str  # 复杂度
    scenario: str  # 场景
    decision: str  # 路由决策
    confidence: float  # 置信度

    # 时间指标
    total_time: float  # 总时间
    vector_time: float = 0.0  # 向量搜索时间
    rerank_time: float = 0.0  # Rerank时间
    llm_time: float = 0.0  # LLM时间

    # 结果指标
    results_count: int = 0  # 结果数量
    avg_score: float = 0.0  # 平均分数
    top_score: float = 0.0  # 最高分数

    # 元数据
    success: bool = True  # 是否成功
    error: Optional[str] = None  # 错误信息
    timestamp: float = field(default_factory=time.time)
    cached: bool = False  # 是否来自缓存


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, max_records: int = 10000):
        """
        初始化性能监控器

        Args:
            max_records: 最大记录数量
        """
        self.max_records = max_records

        # 存储最近记录
        self.records = deque(maxlen=max_records)

        # 统计数据
        self.stats = {
            "total_searches": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "cached_searches": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
        }

        # 按决策分组统计
        self.decision_stats = defaultdict(
            lambda: {"count": 0, "total_time": 0.0, "avg_time": 0.0, "success_rate": 0.0}
        )

        # 按复杂度分组统计
        self.complexity_stats = defaultdict(
            lambda: {"count": 0, "avg_time": 0.0, "avg_results": 0, "avg_score": 0.0}
        )

        # 性能基线
        self.performance_baseline = {
            "vector_only": {"target_time": 0.2, "warning_time": 0.5},
            "rerank_top_k": {"target_time": 0.5, "warning_time": 1.0},
            "llm_rewrite": {"target_time": 2.0, "warning_time": 4.0},
            "llm_full": {"target_time": 3.0, "warning_time": 6.0},
        }

        logger.info("✅ 性能监控器初始化完成")

    def record_search(self, record: SearchRecord) -> Any:
        """
        记录搜索

        Args:
            record: 搜索记录
        """
        # 添加记录
        self.records.append(record)

        # 更新统计
        self.stats["total_searches"] += 1
        if record.success:
            self.stats["successful_searches"] += 1
        else:
            self.stats["failed_searches"] += 1

        if record.cached:
            self.stats["cached_searches"] += 1

        self.stats["total_time"] += record.total_time
        self.stats["avg_time"] = self.stats["total_time"] / self.stats["total_searches"]

        # 更新决策统计
        self.decision_stats[record.decision]["count"] += 1
        self.decision_stats[record.decision]["total_time"] += record.total_time
        self.decision_stats[record.decision]["avg_time"] = (
            self.decision_stats[record.decision]["total_time"]
            / self.decision_stats[record.decision]["count"]
        )

        # 更新复杂度统计
        self.complexity_stats[record.complexity]["count"] += 1
        self.complexity_stats[record.complexity]["avg_time"] = (
            self.complexity_stats[record.complexity]["avg_time"]
            * (self.complexity_stats[record.complexity]["count"] - 1)
            + record.total_time
        ) / self.complexity_stats[record.complexity]["count"]
        self.complexity_stats[record.complexity]["avg_results"] = (
            self.complexity_stats[record.complexity]["avg_results"]
            * (self.complexity_stats[record.complexity]["count"] - 1)
            + record.results_count
        ) / self.complexity_stats[record.complexity]["count"]
        self.complexity_stats[record.complexity]["avg_score"] = (
            self.complexity_stats[record.complexity]["avg_score"]
            * (self.complexity_stats[record.complexity]["count"] - 1)
            + record.avg_score
        ) / self.complexity_stats[record.complexity]["count"]

    def get_summary(self) -> dict[str, Any]:
        """获取统计摘要"""
        # 计算缓存命中率
        cache_hit_rate = (
            self.stats["cached_searches"] / self.stats["total_searches"]
            if self.stats["total_searches"] > 0
            else 0.0
        )

        # 计算成功率
        success_rate = (
            self.stats["successful_searches"] / self.stats["total_searches"]
            if self.stats["total_searches"] > 0
            else 0.0
        )

        return {
            "overview": {
                "total_searches": self.stats["total_searches"],
                "successful_searches": self.stats["successful_searches"],
                "failed_searches": self.stats["failed_searches"],
                "cached_searches": self.stats["cached_searches"],
                "success_rate": success_rate,
                "cache_hit_rate": cache_hit_rate,
                "avg_response_time": self.stats["avg_time"],
            },
            "by_decision": dict(self.decision_stats),
            "by_complexity": dict(self.complexity_stats),
            "performance_baseline": self.performance_baseline,
        }

    def get_recent_records(self, limit: int = 100) -> list[SearchRecord]:
        """获取最近的记录"""
        return list(self.records)[-limit:]

    def get_performance_issues(self) -> list[dict[str, Any]]:
        """获取性能问题"""
        issues = []

        # 检查最近100条记录
        recent_records = self.get_recent_records(100)

        if not recent_records:
            return issues

        # 按决策分组分析
        for decision, baseline in self.performance_baseline.items():
            decision_records = [r for r in recent_records if r.decision == decision]

            if not decision_records:
                continue

            # 计算平均时间
            avg_time = sum(r.total_time for r in decision_records) / len(decision_records)

            # 检查是否超出警告阈值
            if avg_time > baseline["warning_time"]:
                issues.append(
                    {
                        "severity": "warning",
                        "type": "slow_response",
                        "decision": decision,
                        "avg_time": avg_time,
                        "warning_time": baseline["warning_time"],
                        "target_time": baseline["target_time"],
                        "recommendation": f"考虑优化{decision}的性能,或减少使用频率",
                    }
                )

            # 检查是否超出目标时间
            elif avg_time > baseline["target_time"] * 1.5:
                issues.append(
                    {
                        "severity": "info",
                        "type": "performance_degradation",
                        "decision": decision,
                        "avg_time": avg_time,
                        "target_time": baseline["target_time"],
                        "recommendation": f"{decision}响应时间高于目标值,建议监控",
                    }
                )

        return issues

    def get_optimization_suggestions(self) -> list[dict[str, Any]]:
        """获取优化建议"""
        suggestions = []

        summary = self.get_summary()

        # 检查1: 缓存命中率
        if summary["overview"]["cache_hit_rate"] < 0.3:
            suggestions.append(
                {
                    "priority": "high",
                    "area": "caching",
                    "issue": "缓存命中率低",
                    "current_value": f"{summary['overview']['cache_hit_rate']:.1%}",
                    "target_value": "≥50%",
                    "suggestion": "增加缓存TTL时间,或扩大缓存容量",
                }
            )

        # 检查2: 平均响应时间
        if summary["overview"]["avg_response_time"] > 2.0:
            suggestions.append(
                {
                    "priority": "medium",
                    "area": "performance",
                    "issue": "平均响应时间过长",
                    "current_value": f"{summary['overview']['avg_response_time']:.2f}秒",
                    "target_value": "≤1.5秒",
                    "suggestion": "优化路由策略,减少LLM使用频率",
                }
            )

        # 检查3: 复杂查询分布
        total_complex_queries = summary["by_complexity"].get("complex", {}).get(
            "count", 0
        ) + summary["by_complexity"].get("very_complex", {}).get("count", 0)

        if total_complex_queries > summary["overview"]["total_searches"] * 0.5:
            suggestions.append(
                {
                    "priority": "low",
                    "area": "user_experience",
                    "issue": "复杂查询比例过高",
                    "current_value": f"{total_complex_queries / summary['overview']['total_searches']:.1%}",
                    "target_value": "≤30%",
                    "suggestion": "考虑提供查询优化建议或示例查询",
                }
            )

        return suggestions

    def export_metrics(self, filepath: Optional[str] = None) -> str:
        """
        导出指标到文件

        Args:
            filepath: 导出文件路径

        Returns:
            导出的文件路径
        """
        if filepath is None:
            filepath = f"search_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # 准备数据
        data = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "performance_issues": self.get_performance_issues(),
            "optimization_suggestions": self.get_optimization_suggestions(),
            "recent_records": [
                {
                    "query": r.query[:50],
                    "decision": r.decision,
                    "complexity": r.complexity,
                    "total_time": r.total_time,
                    "success": r.success,
                    "timestamp": datetime.fromtimestamp(r.timestamp).isoformat(),
                }
                for r in self.get_recent_records(50)
            ],
        }

        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ 指标已导出到: {filepath}")

        return filepath

    def print_dashboard(self) -> Any:
        """打印性能监控仪表盘"""
        summary = self.get_summary()

        print()
        print("=" * 80)
        print("📊 搜索性能监控仪表盘")
        print("=" * 80)
        print()

        # 总览
        print("📈 总览:")
        print(f"   总搜索数: {summary['overview']['total_searches']}")
        print(f"   成功率: {summary['overview']['success_rate']:.1%}")
        print(f"   缓存命中率: {summary['overview']['cache_hit_rate']:.1%}")
        print(f"   平均响应时间: {summary['overview']['avg_response_time']:.2f}秒")
        print()

        # 按决策分组
        print("🎯 按路由决策分组:")
        for decision, stats in summary["by_decision"].items():
            print(f"   {decision}:")
            print(f"      次数: {stats['count']}")
            print(f"      平均时间: {stats['avg_time']:.2f}秒")
            if decision in summary["performance_baseline"]:
                baseline = summary["performance_baseline"][decision]
                status = "✅" if stats["avg_time"] <= baseline["target_time"] else "⚠️"
                print(f"      状态: {status} (目标: ≤{baseline['target_time']}秒)")
        print()

        # 按复杂度分组
        print("📊 按查询复杂度分组:")
        for complexity, stats in summary["by_complexity"].items():
            print(f"   {complexity}:")
            print(f"      次数: {stats['count']}")
            print(f"      平均时间: {stats['avg_time']:.2f}秒")
            print(f"      平均结果数: {stats['avg_results']:.1f}")
            print(f"      平均分数: {stats['avg_score']:.3f}")
        print()

        # 性能问题
        issues = self.get_performance_issues()
        if issues:
            print("⚠️  性能问题:")
            for issue in issues:
                print(f"   [{issue['severity'].upper()}] {issue['type']}")
                print(f"      决策: {issue['decision']}")
                print(f"      当前: {issue['avg_time']:.2f}秒")
                print(f"      建议: {issue['recommendation']}")
            print()
        else:
            print("✅ 未检测到性能问题")
            print()

        # 优化建议
        suggestions = self.get_optimization_suggestions()
        if suggestions:
            print("💡 优化建议:")
            for suggestion in suggestions:
                print(f"   [{suggestion['priority'].upper()}] {suggestion['area']}")
                print(f"      问题: {suggestion['issue']}")
                print(
                    f"      当前: {suggestion['current_value']} → 目标: {suggestion['target_value']}"
                )
                print(f"      建议: {suggestion['suggestion']}")
            print()

        print("=" * 80)
        print()


class RealTimeMonitor:
    """实时监控器"""

    def __init__(self, monitor: PerformanceMonitor, interval: float = 60.0):
        """
        初始化实时监控器

        Args:
            monitor: 性能监控器
            interval: 监控间隔(秒)
        """
        self.monitor = monitor
        self.interval = interval
        self.is_running = False
        self.task = None

        logger.info(f"✅ 实时监控器初始化完成 (间隔: {interval}秒)")

    async def start(self):
        """启动实时监控"""
        if self.is_running:
            logger.warning("⚠️ 实时监控已在运行")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._monitor_loop())

        logger.info("🚀 实时监控已启动")

    async def stop(self):
        """停止实时监控"""
        if not self.is_running:
            return

        self.is_running = False

        if self.task:
            self.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.task

        logger.info("🛑 实时监控已停止")

    async def _monitor_loop(self):
        """监控循环"""
        try:
            while self.is_running:
                # 打印仪表盘
                self.monitor.print_dashboard()

                # 检查性能问题
                issues = self.monitor.get_performance_issues()
                if issues:
                    logger.warning(f"⚠️ 检测到 {len(issues)} 个性能问题")

                # 等待下一个监控周期
                await asyncio.sleep(self.interval)

        except asyncio.CancelledError:
            logger.info("📊 监控循环已取消")
        except Exception as e:
            logger.error(f"❌ 监控循环异常: {e}")

    def get_alerts(self) -> list[str]:
        """获取警报"""
        alerts = []

        summary = self.monitor.get_summary()

        # 检查成功率
        if summary["overview"]["success_rate"] < 0.95:
            alerts.append(f"⚠️ 成功率低于95%: {summary['overview']['success_rate']:.1%}")

        # 检查平均响应时间
        if summary["overview"]["avg_response_time"] > 3.0:
            alerts.append(f"⚠️ 平均响应时间过长: {summary['overview']['avg_response_time']:.2f}秒")

        # 检查缓存命中率
        if summary["overview"]["cache_hit_rate"] < 0.2:
            alerts.append(f"⚠️ 缓存命中率低: {summary['overview']['cache_hit_rate']:.1%}")

        return alerts


# 全局单例
_performance_monitor: PerformanceMonitor | None = None
_realtime_monitor: RealTimeMonitor | None = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器单例"""
    global _performance_monitor

    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()

    return _performance_monitor


def get_realtime_monitor() -> RealTimeMonitor:
    """获取实时监控器单例"""
    global _realtime_monitor

    if _realtime_monitor is None:
        monitor = get_performance_monitor()
        _realtime_monitor = RealTimeMonitor(monitor)

    return _realtime_monitor


# 示例使用
async def main():
    """主函数示例"""
    print("🔍 性能监控系统演示")
    print()

    # 获取监控器
    monitor = get_performance_monitor()

    # 模拟一些搜索记录
    print("📝 模拟搜索记录...")

    test_records = [
        SearchRecord(
            query="专利侵权",
            query_length=4,
            complexity="simple",
            scenario="quick_preview",
            decision="vector_only",
            confidence=0.95,
            total_time=0.15,
            results_count=5,
            avg_score=0.75,
            top_score=0.85,
        ),
        SearchRecord(
            query="发明专利的保护期是多久?",
            query_length=12,
            complexity="simple",
            scenario="answer_generation",
            decision="rerank_top_k",
            confidence=0.90,
            total_time=0.35,
            rerank_time=0.20,
            results_count=5,
            avg_score=0.82,
            top_score=0.90,
        ),
        SearchRecord(
            query="请解释专利权的无效宣告程序是什么?",
            query_length=18,
            complexity="medium",
            scenario="answer_generation",
            decision="llm_full",
            confidence=0.85,
            total_time=2.5,
            vector_time=0.2,
            rerank_time=0.2,
            llm_time=2.1,
            results_count=3,
            avg_score=0.88,
            top_score=0.92,
        ),
    ]

    for record in test_records:
        monitor.record_search(record)

    # 显示仪表盘
    monitor.print_dashboard()

    # 显示优化建议
    print("💡 优化建议:")
    suggestions = monitor.get_optimization_suggestions()
    for suggestion in suggestions:
        print(f"   - {suggestion['suggestion']}")

    # 启动实时监控
    print()
    print("🚀 启动实时监控 (10秒)...")
    rt_monitor = get_realtime_monitor()
    await rt_monitor.start()

    await asyncio.sleep(10)
    await rt_monitor.stop()


# 入口点: @async_main装饰器已添加到main函数
