#!/usr/bin/env python3
"""
数据库性能监控和调优工具
提供实时监控、性能分析和自动调优功能
"""

import asyncio
import contextlib
import json
import statistics
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from core.logging_config import setup_logging

from .optimized_connection_pool import connection_manager

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class QueryMetrics:
    """查询指标"""

    query_hash: str
    query_type: str
    execution_time: float
    rows_affected: int
    timestamp: datetime
    database: str
    success: bool


@dataclass
class PerformanceAlert:
    """性能告警"""

    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    metric_value: float
    threshold: float


class DatabasePerformanceMonitor:
    """数据库性能监控器"""

    def __init__(self):
        self.query_metrics: deque = deque(maxlen=10000)  # 保留最近10000条查询
        self.alerts: list[PerformanceAlert] = []
        self.performance_thresholds = {
            "slow_query_threshold": 1.0,  # 慢查询阈值(秒)
            "connection_pool_usage_threshold": 0.8,  # 连接池使用率阈值
            "error_rate_threshold": 0.05,  # 错误率阈值
            "avg_response_time_threshold": 0.5,  # 平均响应时间阈值
        }
        self.monitoring_active = False
        self.monitoring_task: asyncio.Task | None = None

    async def start_monitoring(self, interval: float = 30.0):
        """启动性能监控"""
        if self.monitoring_active:
            logger.warning("性能监控已在运行中")
            return

        self.monitoring_active = True
        self.monitoring_task = _task_2_3e187c = asyncio.create_task(self._monitoring_loop(interval))
        logger.info(f"🔍 数据库性能监控已启动 (间隔: {interval}秒)")

    async def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.monitoring_task
        logger.info("⏹️ 数据库性能监控已停止")

    async def _monitoring_loop(self, interval: float):
        """监控循环"""
        while self.monitoring_active:
            try:
                await self._collect_metrics()
                await self._analyze_performance()
                await self._cleanup_old_data()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"性能监控循环出错: {e}")
                await asyncio.sleep(interval)

    async def _collect_metrics(self):
        """收集性能指标"""
        try:
            # 收集连接池统计信息
            pool_stats = await connection_manager.get_all_stats()

            # 检查连接池使用率
            for db_name, stats in pool_stats.get("postgresql", {}).items():
                usage_rate = stats["active_connections"] / max(stats["total_connections"], 1)
                if usage_rate > self.performance_thresholds["connection_pool_usage_threshold"]:
                    await self._create_alert(
                        "connection_pool_high_usage",
                        "medium",
                        f"数据库 '{db_name}' 连接池使用率过高: {usage_rate:.2%}",
                        usage_rate,
                        self.performance_thresholds["connection_pool_usage_threshold"],
                    )

            # 检查响应时间
            for db_name, stats in pool_stats.get("postgresql", {}).items():
                avg_time = stats["avg_response_time"]
                if avg_time > self.performance_thresholds["avg_response_time_threshold"]:
                    await self._create_alert(
                        "high_response_time",
                        "medium",
                        f"数据库 '{db_name}' 平均响应时间过高: {avg_time:.3f}秒",
                        avg_time,
                        self.performance_thresholds["avg_response_time_threshold"],
                    )

            # 检查Redis连接池
            for redis_name, stats in pool_stats.get("redis", {}).items():
                if stats["failed_connections"] > 0:
                    error_rate = stats["failed_connections"] / max(stats["active_connections"], 1)
                    if error_rate > self.performance_thresholds["error_rate_threshold"]:
                        await self._create_alert(
                            "redis_high_error_rate",
                            "high",
                            f"Redis '{redis_name}' 错误率过高: {error_rate:.2%}",
                            error_rate,
                            self.performance_thresholds["error_rate_threshold"],
                        )

        except Exception as e:
            logger.error(f"收集性能指标失败: {e}")

    async def _analyze_performance(self):
        """分析性能数据"""
        if len(self.query_metrics) < 100:
            return  # 数据量不足

        # 分析查询性能
        recent_queries = [
            q for q in self.query_metrics if (datetime.now() - q.timestamp).total_seconds() < 300
        ]  # 最近5分钟

        if recent_queries:
            # 检查慢查询
            slow_queries = [
                q
                for q in recent_queries
                if q.execution_time > self.performance_thresholds["slow_query_threshold"]
            ]
            if slow_queries:
                avg_slow_time = statistics.mean([q.execution_time for q in slow_queries])
                await self._create_alert(
                    "slow_queries_detected",
                    "medium",
                    f"检测到 {len(slow_queries)} 个慢查询,平均执行时间: {avg_slow_time:.3f}秒",
                    len(slow_queries),
                    5,  # 超过5个慢查询则告警
                )

            # 检查错误率
            failed_queries = [q for q in recent_queries if not q.success]
            if (
                len(failed_queries) / len(recent_queries)
                > self.performance_thresholds["error_rate_threshold"]
            ):
                await self._create_alert(
                    "high_error_rate",
                    "high",
                    f"查询错误率过高: {len(failed_queries)}/{len(recent_queries)} ({len(failed_queries)/len(recent_queries):.2%})",
                    len(failed_queries) / len(recent_queries),
                    self.performance_thresholds["error_rate_threshold"],
                )

    async def _cleanup_old_data(self):
        """清理旧数据"""
        cutoff_time = datetime.now() - timedelta(hours=24)  # 保留24小时数据
        old_count = len(self.query_metrics)
        self.query_metrics = deque(
            [q for q in self.query_metrics if q.timestamp > cutoff_time], maxlen=10000
        )
        if len(self.query_metrics) < old_count:
            logger.debug(f"清理了 {old_count - len(self.query_metrics)} 条旧查询记录")

    async def _create_alert(
        self, alert_type: str, severity: str, message: str, metric_value: float, threshold: float
    ):
        """创建性能告警"""
        alert = PerformanceAlert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            metric_value=metric_value,
            threshold=threshold,
        )

        # 避免重复告警
        recent_alerts = [
            a
            for a in self.alerts
            if (datetime.now() - a.timestamp).total_seconds() < 300 and a.alert_type == alert_type
        ]

        if not recent_alerts:
            self.alerts.append(alert)
            logger.warning(f"🚨 性能告警 [{severity.upper()}]: {message}")

    def record_query(
        self,
        query: str,
        execution_time: float,
        rows_affected: int,
        database: str,
        success: bool = True,
    ):
        """记录查询指标"""
        query_hash = hash(query)
        query_type = self._classify_query(query)

        metric = QueryMetrics(
            query_hash=query_hash,
            query_type=query_type,
            execution_time=execution_time,
            rows_affected=rows_affected,
            timestamp=datetime.now(),
            database=database,
            success=success,
        )

        self.query_metrics.append(metric)

        # 实时慢查询检测
        if execution_time > self.performance_thresholds["slow_query_threshold"]:
            logger.warning(f"⚠️ 检测到慢查询: {query_type} - {execution_time:.3f}秒")

    def _classify_query(self, query: str) -> str:
        """查询分类"""
        query_lower = query.lower().strip()

        if query_lower.startswith("select"):
            return "SELECT"
        elif query_lower.startswith("insert"):
            return "INSERT"
        elif query_lower.startswith("update"):
            return "UPDATE"
        elif query_lower.startswith("delete"):
            return "DELETE"
        elif query_lower.startswith("create"):
            return "CREATE"
        elif query_lower.startswith("alter"):
            return "ALTER"
        elif query_lower.startswith("drop"):
            return "DROP"
        elif "index" in query_lower:
            return "INDEX"
        else:
            return "OTHER"

    async def get_performance_report(self) -> dict[str, Any]:
        """生成性能报告"""
        if not self.query_metrics:
            return {"message": "暂无性能数据"}

        # 基础统计
        all_metrics = list(self.query_metrics)
        recent_metrics = [
            q for q in all_metrics if (datetime.now() - q.timestamp).total_seconds() < 3600
        ]  # 最近1小时

        # 按查询类型分组统计
        query_type_stats = {}
        for metric in recent_metrics:
            if metric.query_type not in query_type_stats:
                query_type_stats[metric.query_type] = {
                    "count": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "max_time": 0,
                    "min_time": float("inf"),
                    "success_rate": 0,
                    "error_count": 0,
                }

            stats = query_type_stats[metric.query_type]
            stats["count"] += 1
            stats["total_time"] += metric.execution_time
            stats["max_time"] = max(stats["max_time"], metric.execution_time)
            stats["min_time"] = min(stats["min_time"], metric.execution_time)
            if not metric.success:
                stats["error_count"] += 1

        # 计算平均值
        for _query_type, stats in query_type_stats.items():
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["success_rate"] = (stats["count"] - stats["error_count"]) / stats["count"]
            if stats["min_time"] == float("inf"):
                stats["min_time"] = 0

        # 慢查询分析
        slow_queries = [
            q
            for q in recent_metrics
            if q.execution_time > self.performance_thresholds["slow_query_threshold"]
        ]

        # 错误分析
        failed_queries = [q for q in recent_metrics if not q.success]

        # 数据库性能
        pool_stats = await connection_manager.get_all_stats()

        return {
            "report_time": datetime.now().isoformat(),
            "time_range": "最近1小时",
            "summary": {
                "total_queries": len(recent_metrics),
                "avg_execution_time": (
                    statistics.mean([q.execution_time for q in recent_metrics])
                    if recent_metrics
                    else 0
                ),
                "slow_queries_count": len(slow_queries),
                "error_rate": len(failed_queries) / len(recent_metrics) if recent_metrics else 0,
                "success_rate": (
                    len([q for q in recent_metrics if q.success]) / len(recent_metrics)
                    if recent_metrics
                    else 1
                ),
            },
            "query_type_stats": query_type_stats,
            "slow_queries": [
                {
                    "query_type": q.query_type,
                    "execution_time": q.execution_time,
                    "timestamp": q.timestamp.isoformat(),
                    "infrastructure/infrastructure/database": q.database,
                }
                for q in sorted(slow_queries, key=lambda x: x.execution_time, reverse=True)[:10]
            ],
            "failed_queries": [
                {
                    "query_type": q.query_type,
                    "timestamp": q.timestamp.isoformat(),
                    "infrastructure/infrastructure/database": q.database,
                }
                for q in failed_queries[:10]
            ],
            "connection_pool_stats": pool_stats,
            "recent_alerts": [
                {
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                }
                for alert in sorted(self.alerts, key=lambda x: x.timestamp, reverse=True)[:10]
            ],
        }

    async def get_optimization_suggestions(self) -> list[dict[str, Any]]:
        """获取性能优化建议"""
        suggestions = []

        if not self.query_metrics:
            return suggestions

        recent_metrics = [
            q for q in self.query_metrics if (datetime.now() - q.timestamp).total_seconds() < 3600
        ]

        if not recent_metrics:
            return suggestions

        # 分析慢查询
        slow_queries = [
            q
            for q in recent_metrics
            if q.execution_time > self.performance_thresholds["slow_query_threshold"]
        ]
        if slow_queries:
            suggestions.append(
                {
                    "category": "查询优化",
                    "priority": "high",
                    "title": "存在慢查询需要优化",
                    "description": f"检测到 {len(slow_queries)} 个慢查询,建议检查执行计划",
                    "actions": [
                        "使用 EXPLAIN ANALYZE 检查查询执行计划",
                        "检查相关表的索引使用情况",
                        "考虑重写复杂查询逻辑",
                    ],
                }
            )

        # 分析连接池使用情况
        pool_stats = await connection_manager.get_all_stats()
        for db_name, stats in pool_stats.get("postgresql", {}).items():
            usage_rate = stats["active_connections"] / max(stats["total_connections"], 1)
            if usage_rate > 0.7:
                suggestions.append(
                    {
                        "category": "连接池优化",
                        "priority": "medium",
                        "title": f"数据库 '{db_name}' 连接池使用率较高",
                        "description": f"当前使用率: {usage_rate:.2%}",
                        "actions": [
                            "考虑增加连接池最大连接数",
                            "检查是否有连接泄漏",
                            "优化查询执行时间",
                        ],
                    }
                )

        # 分析错误率
        failed_queries = [q for q in recent_metrics if not q.success]
        error_rate = len(failed_queries) / len(recent_metrics) if recent_metrics else 0
        if error_rate > 0.01:  # 错误率超过1%
            suggestions.append(
                {
                    "category": "错误处理",
                    "priority": "high",
                    "title": "查询错误率过高",
                    "description": f"错误率: {error_rate:.2%}",
                    "actions": [
                        "检查数据库连接稳定性",
                        "验证SQL语法正确性",
                        "增加错误处理和重试机制",
                    ],
                }
            )

        # 分析查询类型分布
        query_type_counts = {}
        for metric in recent_metrics:
            query_type_counts[metric.query_type] = query_type_counts.get(metric.query_type, 0) + 1

        total_queries = len(recent_metrics)
        if query_type_counts.get("SELECT", 0) / total_queries > 0.8:
            suggestions.append(
                {
                    "category": "缓存优化",
                    "priority": "medium",
                    "title": "读查询比例较高",
                    "description": f"SELECT查询占比: {query_type_counts.get('SELECT', 0)/total_queries:.2%}",
                    "actions": ["考虑增加Redis缓存", "优化热点数据缓存策略", "使用读写分离架构"],
                }
            )

        return suggestions


# 全局性能监控器实例
performance_monitor = DatabasePerformanceMonitor()


# 装饰器:自动记录查询性能
def monitored_query(database: str = "patent_legal_db") -> Any:
    """查询性能监控装饰器"""

    def decorator(func) -> None:
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            rows_affected = 0

            try:
                result = await func(*args, **kwargs)

                # 尝试估算影响行数
                if isinstance(result, list) or hasattr(result, "__len__"):
                    rows_affected = len(result)

                return result

            except Exception as e:
                success = False
                logger.error(f"查询执行失败: {e}")
                raise

            finally:
                execution_time = time.time() - start_time
                query_name = func.__name__
                performance_monitor.record_query(
                    query=query_name,
                    execution_time=execution_time,
                    rows_affected=rows_affected,
                    database=database,
                    success=success,
                )

        return wrapper

    return decorator


# 便捷函数
async def start_performance_monitoring(interval: float = 30.0):
    """启动性能监控"""
    await performance_monitor.start_monitoring(interval)


async def stop_performance_monitoring():
    """停止性能监控"""
    await performance_monitor.stop_monitoring()


async def get_performance_report():
    """获取性能报告"""
    return await performance_monitor.get_performance_report()


async def get_optimization_suggestions():
    """获取优化建议"""
    return await performance_monitor.get_optimization_suggestions()


# 示例使用
async def example_usage():
    """示例用法"""
    # 启动监控
    await start_performance_monitoring()

    try:
        # 模拟一些查询
        patent_db = await get_patent_legal_db()

        # 使用监控装饰器
        @monitored_query("patent_legal_db")
        async def sample_query():
            return await patent_db.execute_query(
                "SELECT COUNT(*) FROM legal_entities WHERE entity_type = %s",
                "legal_concept",
                fetch="val",
            )

        # 执行查询
        result = await sample_query()
        print(f"查询结果: {result}")

        # 等待收集一些数据
        await asyncio.sleep(5)

        # 获取性能报告
        report = await get_performance_report()
        print("性能报告:", json.dumps(report, indent=2, ensure_ascii=False))

        # 获取优化建议
        suggestions = await get_optimization_suggestions()
        print("优化建议:", json.dumps(suggestions, indent=2, ensure_ascii=False))

    finally:
        await stop_performance_monitoring()


if __name__ == "__main__":
    from .optimized_connection_pool import (
        get_patent_legal_db,
        initialize_connection_manager,
    )

    async def main():
        await initialize_connection_manager()
        await example_usage()

    asyncio.run(main())
