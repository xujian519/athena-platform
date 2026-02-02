#!/usr/bin/env python3
"""
性能数据收集系统
Performance Data Collection System

用于收集Athena优化版的性能数据,支持:
1. 实时性能监控
2. 数据持久化存储
3. 统计分析
4. 趋势分析
5. 性能报告生成

作者: Athena平台团队
创建时间: 2025-12-27
版本: v1.0.0
"""

import json
import logging
import sqlite3
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""

    TOOL_SELECTION = "tool_selection"
    PARAMETER_VALIDATION = "parameter_validation"
    ERROR_PREDICTION = "error_prediction"
    COGNITION_PROCESSING = "cognition_processing"
    END_TO_END = "end_to_end"


@dataclass
class PerformanceMetric:
    """性能指标"""

    timestamp: datetime
    metric_type: MetricType
    task_id: str
    task_description: str

    # 工具选择指标
    tools_available: int = 0
    tools_selected: int = 0
    tool_selection_time: float = 0.0
    tool_selection_accuracy: float = 0.0  # 人工标注或反馈

    # 参数验证指标
    parameters_count: int = 0
    parameters_valid: int = 0
    parameters_invalid: int = 0
    validation_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

    # 错误预测指标
    errors_predicted: int = 0
    errors_actual: int = 0
    errors_prevented: int = 0
    false_positives: int = 0
    prediction_time: float = 0.0

    # 认知处理指标
    cognition_time: float = 0.0
    cognition_confidence: float = 0.0
    reasoning_depth: int = 0

    # 端到端指标
    total_processing_time: float = 0.0
    success: bool = True
    user_satisfaction: float | None = None  # 1-5分

    # 上下文信息
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["metric_type"] = self.metric_type.value
        return data


class PerformanceDataCollector:
    """
    性能数据收集器

    核心功能:
    1. 实时数据收集
    2. 数据持久化
    3. 统计分析
    4. 趋势分析
    5. 报告生成
    """

    def __init__(self, db_path: str = "data/athena_performance.db"):
        self.db_path = db_path

        # 内存缓存(最近N条记录)
        self.metrics_cache: deque = deque(maxlen=10000)

        # 统计缓存
        self.statistics_cache: dict[str, Any] = {}
        self.statistics_cache_updated = None

        # 初始化数据库
        self._init_database()

        logger.info("📊 性能数据收集器初始化完成")

    def _init_database(self) -> Any:
        """初始化数据库"""
        # 确保目录存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建性能指标表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                task_id TEXT NOT NULL,
                task_description TEXT,

                tools_available INTEGER,
                tools_selected INTEGER,
                tool_selection_time REAL,
                tool_selection_accuracy REAL,

                parameters_count INTEGER,
                parameters_valid INTEGER,
                parameters_invalid INTEGER,
                validation_time REAL,
                cache_hits INTEGER,
                cache_misses INTEGER,

                errors_predicted INTEGER,
                errors_actual INTEGER,
                errors_prevented INTEGER,
                false_positives INTEGER,
                prediction_time REAL,

                cognition_time REAL,
                cognition_confidence REAL,
                reasoning_depth INTEGER,

                total_processing_time REAL,
                success BOOLEAN,
                user_satisfaction REAL,

                context TEXT,

                INDEX(timestamp),
                INDEX(metric_type),
                INDEX(task_id)
            )
        """)

        # 创建权重配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weight_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component TEXT NOT NULL,
                weight_name TEXT NOT NULL,
                current_value REAL NOT NULL,
                optimal_value REAL,
                performance_impact REAL,
                last_updated TEXT,
                INDEX(component)
            )
        """)

        # 创建优化建议表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                implemented BOOLEAN DEFAULT 0,
                result REAL,
                INDEX(timestamp),
                INDEX(category)
            )
        """)

        conn.commit()
        conn.close()

        logger.info("✅ 数据库初始化完成")

    async def record_metric(self, metric: PerformanceMetric):
        """记录性能指标"""
        # 添加到内存缓存
        self.metrics_cache.append(metric)

        # 保存到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO performance_metrics (
                timestamp, metric_type, task_id, task_description,
                tools_available, tools_selected, tool_selection_time, tool_selection_accuracy,
                parameters_count, parameters_valid, parameters_invalid, validation_time,
                cache_hits, cache_misses,
                errors_predicted, errors_actual, errors_prevented, false_positives, prediction_time,
                cognition_time, cognition_confidence, reasoning_depth,
                total_processing_time, success, user_satisfaction,
                context
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                metric.timestamp.isoformat(),
                metric.metric_type.value,
                metric.task_id,
                metric.task_description,
                metric.tools_available,
                metric.tools_selected,
                metric.tool_selection_time,
                metric.tool_selection_accuracy,
                metric.parameters_count,
                metric.parameters_valid,
                metric.parameters_invalid,
                metric.validation_time,
                metric.cache_hits,
                metric.cache_misses,
                metric.errors_predicted,
                metric.errors_actual,
                metric.errors_prevented,
                metric.false_positives,
                metric.prediction_time,
                metric.cognition_time,
                metric.cognition_confidence,
                metric.reasoning_depth,
                metric.total_processing_time,
                metric.success,
                metric.user_satisfaction,
                json.dumps(metric.context, ensure_ascii=False),
            ),
        )

        conn.commit()
        conn.close()

        # 使统计缓存失效
        self.statistics_cache_updated = None

        logger.debug(f"📊 已记录性能指标: {metric.task_id}")

    async def get_statistics(
        self, time_range: timedelta = timedelta(hours=24), metric_type: MetricType | None = None
    ) -> dict[str, Any]:
        """获取统计数据"""
        # 检查缓存
        cache_key = f"{time_range}_{metric_type}"
        if (
            self.statistics_cache_updated
            and datetime.now() - self.statistics_cache_updated < timedelta(minutes=5)
            and cache_key in self.statistics_cache
        ):
            return self.statistics_cache[cache_key]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 计算时间范围
        start_time = datetime.now() - time_range

        # 构建查询
        query = """
            SELECT
                COUNT(*) as total_requests,
                AVG(tool_selection_accuracy) as avg_accuracy,
                AVG(tool_selection_time) as avg_selection_time,
                AVG(validation_time) as avg_validation_time,
                AVG(cache_hits) as avg_cache_hits,
                AVG(cache_misses) as avg_cache_misses,
                AVG(errors_prevented) as avg_errors_prevented,
                AVG(cognition_time) as avg_cognition_time,
                AVG(total_processing_time) as avg_processing_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
            FROM performance_metrics
            WHERE timestamp > ?
        """

        params = [start_time.isoformat()]

        if metric_type:
            query += " AND metric_type = ?"
            params.append(metric_type.value)

        cursor.execute(query, params)
        row = cursor.fetchone()

        if row:
            stats = {
                "total_requests": row[0] or 0,
                "avg_accuracy": row[1] or 0.0,
                "avg_selection_time": row[2] or 0.0,
                "avg_validation_time": row[3] or 0.0,
                "avg_cache_hits": row[4] or 0.0,
                "avg_cache_misses": row[5] or 0.0,
                "avg_errors_prevented": row[6] or 0.0,
                "avg_cognition_time": row[7] or 0.0,
                "avg_processing_time": row[8] or 0.0,
                "success_rate": row[9] or 0.0,
            }

            # 计算缓存命中率
            total_cache_ops = stats["avg_cache_hits"] + stats["avg_cache_misses"]
            stats["cache_hit_rate"] = (
                stats["avg_cache_hits"] / total_cache_ops if total_cache_ops > 0 else 0.0
            )
        else:
            stats = {}

        conn.close()

        # 更新缓存
        self.statistics_cache[cache_key] = stats
        self.statistics_cache_updated = datetime.now()

        return stats

    async def get_trends(
        self,
        metric_name: str,
        time_range: timedelta = timedelta(days=7),
        interval: timedelta = timedelta(hours=1),
    ) -> list[dict[str, Any]]:
        """获取趋势数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        end_time = datetime.now()
        start_time = end_time - time_range

        # 简化实现:按小时聚合
        cursor.execute(
            f"""
            SELECT
                strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                AVG({metric_name}) as avg_value,
                COUNT(*) as count
            FROM performance_metrics
            WHERE timestamp > ? AND timestamp < ?
            GROUP BY hour
            ORDER BY hour
        """,
            (start_time.isoformat(), end_time.isoformat()),
        )

        rows = cursor.fetchall()
        conn.close()

        trends = []
        for row in rows:
            trends.append({"timestamp": row[0], "avg_value": row[1], "count": row[2]})

        return trends

    async def generate_performance_report(
        self, time_range: timedelta = timedelta(days=1)
    ) -> dict[str, Any]:
        """生成性能报告"""
        # 获取统计数据
        stats = await self.get_statistics(time_range)

        # 获取趋势数据
        accuracy_trend = await self.get_trends("tool_selection_accuracy", time_range)
        processing_time_trend = await self.get_trends("total_processing_time", time_range)

        # 分析趋势
        def analyze_trend(trend_data) -> None:
            if len(trend_data) < 2:
                return "stable"

            recent = trend_data[-5:] if len(trend_data) >= 5 else trend_data
            values = [t["avg_value"] for t in recent if t["avg_value"] is not None]

            if len(values) < 2:
                return "stable"

            # 简单线性趋势分析
            avg_first = sum(values[: len(values) // 2]) / (len(values) // 2)
            avg_last = sum(values[len(values) // 2 :]) / (len(values) - len(values) // 2)

            change = (avg_last - avg_first) / (avg_first if avg_first > 0 else 1)

            if change > 0.05:
                return (
                    "improving"
                    if metric_name == "accuracy" or metric_name == "success_rate"
                    else "degrading"
                )
            elif change < -0.05:
                return (
                    "degrading"
                    if metric_name == "accuracy" or metric_name == "success_rate"
                    else "improving"
                )
            else:
                return "stable"

        # 分析各项趋势
        accuracy_trend = analyze_trend(accuracy_trend)
        processing_time_trend = analyze_trend(processing_time_trend)

        # 生成建议
        suggestions = []

        if stats.get("avg_accuracy", 0) < 0.9:
            suggestions.append(
                {
                    "category": "tool_selection",
                    "priority": "high",
                    "suggestion": "工具选择准确率低于90%,建议调整语义匹配权重",
                }
            )

        if stats.get("cache_hit_rate", 0) < 0.7:
            suggestions.append(
                {
                    "category": "parameter_validation",
                    "priority": "medium",
                    "suggestion": "缓存命中率低于70%,建议增加参数复用或扩大缓存容量",
                }
            )

        if stats.get("avg_processing_time", 0) > 1.0:
            suggestions.append(
                {
                    "category": "performance",
                    "priority": "high",
                    "suggestion": "平均处理时间超过1秒,建议优化认知处理流程",
                }
            )

        if stats.get("success_rate", 0) < 0.95:
            suggestions.append(
                {
                    "category": "reliability",
                    "priority": "critical",
                    "suggestion": f'成功率仅{stats["success_rate"]:.1%},需要提升系统稳定性',
                }
            )

        return {
            "time_range": str(time_range),
            "statistics": stats,
            "trends": {"accuracy": accuracy_trend, "processing_time": processing_time_trend},
            "suggestions": suggestions,
            "generated_at": datetime.now().isoformat(),
        }

    async def record_user_feedback(self, task_id: str, satisfaction: float, feedback: str):
        """记录用户反馈"""
        # 找到对应的指标记录
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE performance_metrics
            SET user_satisfaction = ?
            WHERE task_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """,
            (satisfaction, task_id),
        )

        conn.commit()
        conn.close()

        logger.info(f"📝 已记录用户反馈: {task_id} - {satisfaction}/5")


# 导出便捷函数
_collector: PerformanceDataCollector | None = None


def get_performance_collector() -> PerformanceDataCollector:
    """获取性能数据收集器单例"""
    global _collector
    if _collector is None:
        _collector = PerformanceDataCollector()
    return _collector


# 便捷使用函数
async def record_tool_selection_metric(
    task_id: str,
    task_description: str,
    tools_available: int,
    tools_selected: int,
    selection_time: float,
    accuracy: float | None = None,
):
    """记录工具选择指标"""
    collector = get_performance_collector()

    metric = PerformanceMetric(
        timestamp=datetime.now(),
        metric_type=MetricType.TOOL_SELECTION,
        task_id=task_id,
        task_description=task_description,
        tools_available=tools_available,
        tools_selected=tools_selected,
        tool_selection_time=selection_time,
        tool_selection_accuracy=accuracy or 0.0,
    )

    await collector.record_metric(metric)


async def record_validation_metric(
    task_id: str,
    parameters_count: int,
    valid_count: int,
    invalid_count: int,
    validation_time: float,
    cache_hits: int,
    cache_misses: int,
):
    """记录参数验证指标"""
    collector = get_performance_collector()

    metric = PerformanceMetric(
        timestamp=datetime.now(),
        metric_type=MetricType.PARAMETER_VALIDATION,
        task_id=task_id,
        task_description="",
        parameters_count=parameters_count,
        parameters_valid=valid_count,
        parameters_invalid=invalid_count,
        validation_time=validation_time,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
    )

    await collector.record_metric(metric)


async def record_end_to_end_metric(
    task_id: str,
    task_description: str,
    total_time: float,
    success: bool,
    user_satisfaction: float | None = None,
):
    """记录端到端指标"""
    collector = get_performance_collector()

    metric = PerformanceMetric(
        timestamp=datetime.now(),
        metric_type=MetricType.END_TO_END,
        task_id=task_id,
        task_description=task_description,
        total_processing_time=total_time,
        success=success,
        user_satisfaction=user_satisfaction,
    )

    await collector.record_metric(metric)


# 使用示例
async def main():
    """主函数示例"""

    print("=" * 60)
    print("性能数据收集系统演示")
    print("=" * 60)

    # 记录一些示例数据
    print("\n📊 记录示例数据...")

    # 工具选择指标
    await record_tool_selection_metric(
        task_id="task_001",
        task_description="分析专利CN1234567",
        tools_available=10,
        tools_selected=3,
        selection_time=0.15,
        accuracy=0.95,
    )

    # 参数验证指标
    await record_validation_metric(
        task_id="task_001",
        parameters_count=5,
        valid_count=4,
        invalid_count=1,
        validation_time=0.08,
        cache_hits=3,
        cache_misses=2,
    )

    # 端到端指标
    await record_end_to_end_metric(
        task_id="task_001",
        task_description="分析专利CN1234567",
        total_time=0.65,
        success=True,
        user_satisfaction=4.5,
    )

    print("✅ 数据记录完成")

    # 获取统计数据
    print("\n📈 获取统计数据...")
    stats = await get_performance_collector().get_statistics()
    print(f"总请求数: {stats.get('total_requests', 0)}")
    print(f"平均准确率: {stats.get('avg_accuracy', 0):.2%}")
    print(f"平均处理时间: {stats.get('avg_processing_time', 0):.3f}秒")
    print(f"成功率: {stats.get('success_rate', 0):.2%}")
    print(f"缓存命中率: {stats.get('cache_hit_rate', 0):.2%}")

    # 生成性能报告
    print("\n📋 生成性能报告...")
    report = await get_performance_collector().generate_performance_report()

    print(f"报告时间范围: {report['time_range']}")
    print(f"准确率趋势: {report['trends']['accuracy']}")
    print(f"处理时间趋势: {report['trends']['processing_time']}")

    if report["suggestions"]:
        print("\n💡 优化建议:")
        for i, suggestion in enumerate(report["suggestions"], 1):
            print(f"{i}. [{suggestion['priority'].upper()}] {suggestion['suggestion']}")

    print("\n✅ 演示完成")


# 入口点: @async_main装饰器已添加到main函数
