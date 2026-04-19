#!/usr/bin/env python3
from __future__ import annotations
"""
工具性能跟踪和优化建议系统
Tool Performance Tracker and Optimization Advisor

实时跟踪工具使用效果,提供智能优化建议

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import asyncio
import json
import logging
import sqlite3
import statistics
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

# 导入标准化数据库工具

logger = logging.getLogger(__name__)


class PerformanceMetric(Enum):
    """性能指标类型"""

    SUCCESS_RATE = "success_rate"
    RESPONSE_TIME = "response_time"
    USER_SATISFACTION = "user_satisfaction"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    RESOURCE_USAGE = "resource_usage"


@dataclass
class ToolExecutionRecord:
    """工具执行记录"""

    tool_name: str
    intent_type: str
    start_time: datetime
    end_time: datetime
    success: bool
    error_message: str
    user_input_length: int
    output_length: int
    user_satisfaction: float  # 1-5分
    resource_usage: dict[str, float]  # CPU, Memory等
    context: dict[str, Any] | None = None


@dataclass
class PerformanceReport:
    """性能报告"""

    tool_name: str
    period: str
    execution_count: int
    success_rate: float
    avg_response_time: float
    avg_satisfaction: float
    error_rate: float
    top_error_types: list[tuple[str, int]]
    performance_trend: str  # improving, stable, declining
    optimization_suggestions: list[str]
    comparison_with_period: dict[str, float] | None = None


class ToolPerformanceTracker:
    """工具性能跟踪器"""

    def __init__(self, db_path: str = "/Users/xujian/Athena工作平台/data/performance_metrics.db"):
        self.db_path = db_path
        self.conn = None
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

        # 优化规则库
        self.optimization_rules = self._initialize_optimization_rules()

        # 性能基准
        self.performance_benchmarks = self._initialize_benchmarks()

        # 监控指标阈值
        self.alert_thresholds = {
            "success_rate": 0.8,  # 成功率低于80%告警
            "response_time": 120.0,  # 响应时间超过2分钟告警
            "satisfaction": 3.5,  # 用户满意度低于3.5告警
            "error_rate": 0.2,  # 错误率超过20%告警
        }

        self._initialize_database()
        self.logger.info("📊 工具性能跟踪系统初始化完成")

    def _initialize_database(self):
        """初始化数据库"""
        try:
            # 确保目录存在
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.conn.cursor()

            # 创建表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    intent_type TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    user_input_length INTEGER,
                    output_length INTEGER,
                    user_satisfaction REAL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    context TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS optimization_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    suggestion TEXT,
                    priority INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    implemented_at TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tool_name ON tool_executions(tool_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_start_time ON tool_executions(start_time)
            """)

            self.conn.commit()
            self.logger.info("✅ 数据库初始化完成")

        except Exception as e:
            self.logger.error(f"❌ 数据库初始化失败: {e!s}")
            raise

    def _initialize_optimization_rules(self) -> dict[str, list[dict[str, Any]]]:
        """初始化优化规则库"""
        return {
            "low_success_rate": [
                {
                    "condition": "success_rate < 0.8",
                    "suggestion": "工具成功率过低,建议检查工具配置和输入数据质量",
                    "priority": 1,
                    "actions": ["检查工具依赖", "更新工具版本", "添加错误处理"],
                }
            ],
            "slow_response": [
                {
                    "condition": "avg_response_time > 120",
                    "suggestion": "响应时间过长,建议优化算法或增加资源",
                    "priority": 2,
                    "actions": ["性能分析", "资源扩容", "算法优化"],
                }
            ],
            "high_error_rate": [
                {
                    "condition": "error_rate > 0.2",
                    "suggestion": "错误率过高,需要紧急修复",
                    "priority": 1,
                    "actions": ["错误日志分析", "代码审查", "测试验证"],
                }
            ],
            "low_satisfaction": [
                {
                    "condition": "avg_satisfaction < 3.5",
                    "suggestion": "用户满意度低,需要改进工具功能或用户体验",
                    "priority": 2,
                    "actions": ["用户反馈收集", "功能增强", "UI优化"],
                }
            ],
        }

    def _initialize_benchmarks(self) -> dict[str, dict[str, float]]:
        """初始化性能基准"""
        return {
            "patent_professional_workflow": {
                "success_rate": 0.94,
                "response_time": 180.0,
                "satisfaction": 4.2,
            },
            "enhanced_patent_perception": {
                "success_rate": 0.95,
                "response_time": 20.0,
                "satisfaction": 4.0,
            },
            "patent_crawler": {"success_rate": 0.92, "response_time": 30.0, "satisfaction": 3.8},
            "xiaonuo_enhanced": {"success_rate": 0.96, "response_time": 30.0, "satisfaction": 4.5},
        }

    def record_execution(self, record: ToolExecutionRecord):
        """记录工具执行"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO tool_executions
                    (tool_name, intent_type, start_time, end_time, success,
                     error_message, user_input_length, output_length, user_satisfaction,
                     cpu_usage, memory_usage, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        record.tool_name,
                        record.intent_type,
                        record.start_time,
                        record.end_time,
                        record.success,
                        record.error_message,
                        record.user_input_length,
                        record.output_length,
                        record.user_satisfaction,
                        record.resource_usage.get("cpu", 0),
                        record.resource_usage.get("memory", 0),
                        json.dumps(record.context) if record.context else None,
                    ),
                )

                self.conn.commit()

                # 实时检查告警条件
                self._check_performance_alerts(record.tool_name)

            except Exception as e:
                self.logger.error(f"❌ 记录执行失败: {e!s}")

    def _check_performance_alerts(self, tool_name: str):
        """检查性能告警"""
        try:
            # 获取最近的性能数据
            recent_data = self.get_tool_performance(tool_name, hours=1)

            if not recent_data:
                return

            # 检查各项指标
            alerts = []

            if recent_data.success_rate < self.alert_thresholds["success_rate"]:
                alerts.append(f"成功率过低: {recent_data.success_rate:.1%}")

            if recent_data.avg_response_time > self.alert_thresholds["response_time"]:
                alerts.append(f"响应时间过长: {recent_data.avg_response_time:.1f}秒")

            if recent_data.error_rate > self.alert_thresholds["error_rate"]:
                alerts.append(f"错误率过高: {recent_data.error_rate:.1%}")

            if (
                recent_data.avg_satisfaction
                and recent_data.avg_satisfaction < self.alert_thresholds["satisfaction"]
            ):
                alerts.append(f"用户满意度低: {recent_data.avg_satisfaction:.1f}")

            # 发送告警
            if alerts:
                self.logger.warning(f"⚠️ 工具性能告警 [{tool_name}]: ' + '; ".join(alerts))
                self._generate_optimization_suggestions(tool_name, alerts)

        except Exception as e:
            self.logger.error(f"❌ 性能告警检查失败: {e!s}")

    def _generate_optimization_suggestions(self, tool_name: str, issues: list[str]):
        """生成优化建议"""
        try:
            cursor = self.conn.cursor()

            for issue in issues:
                for category, rules in self.optimization_rules.items():
                    for rule in rules:
                        if any(keyword in issue for keyword in rule["condition"].split()):
                            cursor.execute(
                                """
                                INSERT INTO optimization_suggestions
                                (tool_name, suggestion, priority, status)
                                VALUES (?, ?, ?, ?)
                            """,
                                (
                                    tool_name,
                                    f"[{category}] {rule['suggestion']}",
                                    rule["priority"],
                                    "pending",
                                ),
                            )

            self.conn.commit()
            self.logger.info(f"✅ 已生成 {len(issues)} 条优化建议")

        except Exception as e:
            self.logger.error(f"❌ 生成优化建议失败: {e!s}")

    def get_tool_performance(
        self, tool_name: str, days: int = 7, hours: float | None = None
    ) -> PerformanceReport | None:
        """获取工具性能报告"""
        try:
            cursor = self.conn.cursor()

            # 验证输入参数(防止SQL注入)
            if hours is not None:
                if not isinstance(hours, (int, float)) or hours <= 0:
                    raise ValueError(f"hours必须是正数,收到: {hours}")
                hours_str = str(hours)
                time_filter = f"AND start_time >= datetime('now', '-{hours_str} hours')"
                period = f"过去{hours_str}小时"
            else:
                if not isinstance(days, int) or days <= 0:
                    raise ValueError(f"days必须是正整数,收到: {days}")
                days_str = str(days)
                time_filter = f"AND start_time >= datetime('now', '-{days_str} days')"
                period = f"过去{days_str}天"

            # 获取执行记录 - hours/days已验证为数字,time_filter安全
            cursor.execute(
                f"""
                SELECT * FROM tool_executions
                WHERE tool_name = ? {time_filter}
                ORDER BY start_time DESC
            """,
                (tool_name,),
            )

            records = cursor.fetchall()
            if not records:
                return None

            # 分析性能数据
            execution_count = len(records)
            success_count = sum(1 for r in records if r[4])  # success column
            success_rate = success_count / execution_count

            response_times = []
            satisfaction_scores = []
            error_types = {}

            for r in records:
                # 计算响应时间
                start_time = datetime.fromisoformat(r[2])
                end_time = datetime.fromisoformat(r[3])
                response_time = (end_time - start_time).total_seconds()
                response_times.append(response_time)

                # 收集满意度
                if r[8] is not None:  # user_satisfaction
                    satisfaction_scores.append(r[8])

                # 收集错误信息
                if not r[4] and r[5]:  # failed and has error_message
                    error_type = r[5].split(":")[0] if ":" in r[5] else r[5]
                    error_types[error_type] = error_types.get(error_type, 0) + 1

            avg_response_time = statistics.mean(response_times) if response_times else 0
            avg_satisfaction = statistics.mean(satisfaction_scores) if satisfaction_scores else 0
            error_rate = 1 - success_rate

            # 错误类型排序
            top_error_types = sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]

            # 性能趋势分析
            performance_trend = self._analyze_performance_trend(tool_name, records)

            # 生成优化建议
            optimization_suggestions = self._generate_specific_suggestions(
                tool_name, success_rate, avg_response_time, avg_satisfaction
            )

            report = PerformanceReport(
                tool_name=tool_name,
                period=period,
                execution_count=execution_count,
                success_rate=success_rate,
                avg_response_time=avg_response_time,
                avg_satisfaction=avg_satisfaction,
                error_rate=error_rate,
                top_error_types=top_error_types,
                performance_trend=performance_trend,
                optimization_suggestions=optimization_suggestions,
            )

            return report

        except Exception as e:
            self.logger.error(f"❌ 获取性能报告失败: {e!s}")
            return None

    def _analyze_performance_trend(self, tool_name: str, records: list) -> str:
        """分析性能趋势"""
        try:
            if len(records) < 10:
                return "insufficient_data"

            # 分为前后两半进行比较
            mid_point = len(records) // 2
            first_half = records[:mid_point]
            second_half = records[mid_point:]

            # 计算前半段成功率
            first_success_rate = sum(1 for r in first_half if r[4]) / len(first_half)

            # 计算后半段成功率
            second_success_rate = sum(1 for r in second_half if r[4]) / len(second_half)

            # 判断趋势
            improvement = second_success_rate - first_success_rate

            if improvement > 0.05:
                return "improving"
            elif improvement < -0.05:
                return "declining"
            else:
                return "stable"

        except Exception:
            return "unknown"

    def _generate_specific_suggestions(
        self, tool_name: str, success_rate: float, response_time: float, satisfaction: float
    ) -> list[str]:
        """生成具体的优化建议"""
        suggestions = []

        # 获取基准数据
        benchmark = self.performance_benchmarks.get(tool_name, {})

        # 成功率分析
        if success_rate < 0.8:
            suggestions.append("工具成功率较低,建议增加错误处理和重试机制")
        elif benchmark and success_rate < benchmark.get("success_rate", 1.0):
            suggestions.append(
                f"成功率({success_rate:.1%})低于基准({benchmark['success_rate']:.1%}),建议优化工具稳定性"
            )

        # 响应时间分析
        if response_time > 120:
            suggestions.append("响应时间超过2分钟,建议优化算法或增加资源")
        elif benchmark and response_time > benchmark.get("response_time", float("inf")):
            suggestions.append(
                f"响应时间({response_time:.1f}s)长于基准({benchmark['response_time']:.1f}s)"
            )

        # 用户满意度分析
        if satisfaction < 3.5:
            suggestions.append("用户满意度较低,建议收集反馈并改进功能")
        elif benchmark and satisfaction < benchmark.get("satisfaction", 5.0):
            suggestions.append(
                f"满意度({satisfaction:.1f})低于基准({benchmark['satisfaction']:.1f})"
            )

        return suggestions

    def get_system_overview(self) -> dict[str, Any]:
        """获取系统性能概览"""
        try:
            cursor = self.conn.cursor()

            # 总体统计
            cursor.execute("""
                SELECT tool_name, COUNT(*) as executions,
                       AVG(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_rate,
                       AVG((julianday(end_time) - julianday(start_time)) * 24 * 3600) as avg_response_time,
                       AVG(user_satisfaction) as avg_satisfaction
                FROM tool_executions
                WHERE start_time >= datetime('now', '-7 days')
                GROUP BY tool_name
            """)

            tools_performance = cursor.fetchall()

            # 优化建议统计
            cursor.execute("""
                SELECT COUNT(*) as pending_suggestions
                FROM optimization_suggestions
                WHERE status = 'pending'
            """)

            pending_suggestions = cursor.fetchone()[0]

            # 系统健康状态
            total_tools = len(tools_performance)
            healthy_tools = sum(
                1 for _, _, success_rate, _, _ in tools_performance if success_rate > 0.8
            )

            overview = {
                "total_tools_tracked": total_tools,
                "healthy_tools": healthy_tools,
                "health_percentage": healthy_tools / total_tools if total_tools > 0 else 0,
                "pending_suggestions": pending_suggestions,
                "tools_performance": [],
                "last_updated": datetime.now().isoformat(),
            }

            # 详细工具性能
            for (
                tool_name,
                executions,
                success_rate,
                avg_response,
                avg_satisfaction,
            ) in tools_performance:
                overview["tools_performance"].append(
                    {
                        "tool_name": tool_name,
                        "executions": executions,
                        "success_rate": success_rate,
                        "avg_response_time": avg_response,
                        "avg_satisfaction": avg_satisfaction or 0,
                    }
                )

            return overview

        except Exception as e:
            self.logger.error(f"❌ 获取系统概览失败: {e!s}")
            return {"error": str(e)}

    def get_optimization_suggestions(
        self, tool_name: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """获取优化建议"""
        try:
            cursor = self.conn.cursor()

            if tool_name:
                cursor.execute(
                    """
                    SELECT * FROM optimization_suggestions
                    WHERE tool_name = ?
                    ORDER BY priority ASC, created_at DESC
                    LIMIT ?
                """,
                    (tool_name, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM optimization_suggestions
                    ORDER BY priority ASC, created_at DESC
                    LIMIT ?
                """,
                    (limit,),
                )

            suggestions = []
            for row in cursor.fetchall():
                suggestions.append(
                    {
                        "id": row[0],
                        "tool_name": row[1],
                        "suggestion": row[2],
                        "priority": row[3],
                        "status": row[4],
                        "created_at": row[5],
                        "implemented_at": row[6],
                    }
                )

            return suggestions

        except Exception as e:
            self.logger.error(f"❌ 获取优化建议失败: {e!s}")
            return []

    def mark_suggestion_implemented(self, suggestion_id: int):
        """标记建议已实现"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE optimization_suggestions
                SET status = 'implemented', implemented_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (suggestion_id,),
            )

            self.conn.commit()
            self.logger.info(f"✅ 建议 {suggestion_id} 已标记为已实现")

        except Exception as e:
            self.logger.error(f"❌ 标记建议失败: {e!s}")

    async def start_monitoring(self):
        """启动性能监控"""
        self.logger.info("🔍 启动性能监控服务")

        # 定期清理旧数据(保留30天)
        while True:
            try:
                await asyncio.sleep(24 * 3600)  # 24小时
                self._cleanup_old_data()

                # 生成每日报告
                overview = self.get_system_overview()
                self.logger.info(f"📊 每日性能报告: {overview}")

            except Exception as e:
                self.logger.error(f"❌ 监控服务错误: {e!s}")

    def _cleanup_old_data(self):
        """清理旧数据"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM tool_executions
                WHERE start_time < datetime('now', '-30 days')
            """)

            deleted_rows = cursor.rowcount
            self.conn.commit()

            if deleted_rows > 0:
                self.logger.info(f"🧹 清理了 {deleted_rows} 条旧记录")

        except Exception as e:
            self.logger.error(f"❌ 清理旧数据失败: {e!s}")

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.logger.info("📊 性能跟踪器已关闭")


# 使用示例
async def test_performance_tracker():
    """测试性能跟踪系统"""
    logger.info("📊 测试工具性能跟踪系统")

    tracker = ToolPerformanceTracker()

    # 模拟一些执行记录
    now = datetime.now()

    # 模拟专利工作流执行
    test_records = [
        ToolExecutionRecord(
            tool_name="patent_professional_workflow",
            intent_type="opinion_response",
            start_time=now - timedelta(minutes=5),
            end_time=now - timedelta(minutes=2),
            success=True,
            error_message=None,
            user_input_length=150,
            output_length=2000,
            user_satisfaction=4.5,
            resource_usage={"cpu": 0.6, "memory": 0.4},
        ),
        ToolExecutionRecord(
            tool_name="enhanced_patent_perception",
            intent_type="patent_search",
            start_time=now - timedelta(minutes=3),
            end_time=now - timedelta(minutes=2, seconds=50),
            success=True,
            error_message=None,
            user_input_length=100,
            output_length=800,
            user_satisfaction=4.2,
            resource_usage={"cpu": 0.3, "memory": 0.2},
        ),
        ToolExecutionRecord(
            tool_name="patent_crawler",
            intent_type="patent_search",
            start_time=now - timedelta(minutes=2),
            end_time=now - timedelta(minutes=1, seconds=30),
            success=False,
            error_message="网络连接超时",
            user_input_length=80,
            output_length=0,
            user_satisfaction=2.0,
            resource_usage={"cpu": 0.1, "memory": 0.1},
        ),
    ]

    # 记录执行
    for record in test_records:
        tracker.record_execution(record)

    logger.info(f"✅ 记录了 {len(test_records)} 条执行记录")

    # 获取性能报告
    logger.info("\n📋 性能报告:")
    report = tracker.get_tool_performance("patent_professional_workflow")
    if report:
        logger.info(f"工具: {report.tool_name}")
        logger.info(f"成功率: {report.success_rate:.1%}")
        logger.info(f"平均响应时间: {report.avg_response_time:.1f}秒")
        logger.info(f"用户满意度: {report.avg_satisfaction:.1f}/5")
        logger.info(f"性能趋势: {report.performance_trend}")

    # 获取系统概览
    logger.info("\n📊 系统概览:")
    overview = tracker.get_system_overview()
    if "error" not in overview:
        logger.info(f"跟踪工具数量: {overview['total_tools_tracked']}")
        logger.info(f"健康工具数量: {overview['healthy_tools']}")
        logger.info(f"系统健康度: {overview['health_percentage']:.1%}")
        logger.info(f"待处理建议: {overview['pending_suggestions']}")

    # 获取优化建议
    logger.info("\n💡 优化建议:")
    suggestions = tracker.get_optimization_suggestions()
    for suggestion in suggestions[:5]:
        logger.info(f"  • {suggestion['suggestion']} ({suggestion['tool_name']})")

    tracker.close()


if __name__ == "__main__":
    asyncio.run(test_performance_tracker())
