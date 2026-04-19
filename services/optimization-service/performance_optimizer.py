#!/usr/bin/env python3
"""
Athena平台性能优化系统
提供全面的性能监控、分析和优化功能
"""

import asyncio
import json
import statistics
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import psutil

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class PerformanceMetric(Enum):
    """性能指标类型"""
    CPU_USAGE = 'cpu_usage'
    MEMORY_USAGE = 'memory_usage'
    DISK_IO = 'disk_io'
    NETWORK_IO = 'network_io'
    RESPONSE_TIME = 'response_time'
    THROUGHPUT = 'throughput'
    ERROR_RATE = 'error_rate'
    CACHE_HIT_RATE = 'cache_hit_rate'

class OptimizationStrategy(Enum):
    """优化策略类型"""
    CACHE_OPTIMIZATION = 'cache_optimization'
    RESOURCE_SCALING = 'resource_scaling'
    ALGORITHM_OPTIMIZATION = 'algorithm_optimization'
    CONCURRENCY_OPTIMIZATION = 'concurrency_optimization'
    MEMORY_OPTIMIZATION = 'memory_optimization'
    DATABASE_OPTIMIZATION = 'database_optimization'

@dataclass
class MetricPoint:
    """性能数据点"""
    timestamp: datetime
    metric_type: PerformanceMetric
    value: float
    unit: str
    tags: dict[str, str] = field(default_factory=dict)

@dataclass
class PerformanceAlert:
    """性能告警"""
    alert_id: str
    metric_type: PerformanceMetric
    threshold: float
    current_value: float
    severity: str  # low, medium, high, critical
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: datetime | None = None

@dataclass
class OptimizationSuggestion:
    """优化建议"""
    suggestion_id: str
    strategy: OptimizationStrategy
    description: str
    expected_improvement: float
    implementation_cost: str  # low, medium, high
    priority: int
    steps: list[str]
    code_snippets: dict[str, str] = field(default_factory=dict)

class PerformanceCollector:
    """性能数据收集器"""

    def __init__(self, collection_interval: int = 30):
        """初始化收集器"""
        self.collection_interval = collection_interval
        self.metrics_buffer = deque(maxlen=10000)
        self.is_collecting = False
        self.collection_thread = None
        self.custom_collectors = {}

    def start_collection(self) -> Any:
        """开始性能数据收集"""
        if self.is_collecting:
            logger.warning('性能数据收集已在运行中')
            return

        self.is_collecting = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        logger.info('性能数据收集已启动')

    def stop_collection(self) -> Any:
        """停止性能数据收集"""
        self.is_collecting = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info('性能数据收集已停止')

    def _collection_loop(self) -> Any:
        """收集循环"""
        while self.is_collecting:
            try:
                # 收集系统指标
                self._collect_system_metrics()

                # 收集自定义指标
                self._collect_custom_metrics()

                time.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"性能数据收集异常: {e}")
                time.sleep(5)

    def _collect_system_metrics(self) -> Any:
        """收集系统性能指标"""
        timestamp = datetime.now()

        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        self._add_metric(PerformanceMetric.CPU_USAGE, cpu_percent, '%', timestamp)

        # 内存使用率
        memory = psutil.virtual_memory()
        self._add_metric(PerformanceMetric.MEMORY_USAGE, memory.percent, '%', timestamp)

        # 磁盘IO
        disk_io = psutil.disk_io_counters()
        if disk_io:
            self._add_metric(PerformanceMetric.DISK_IO, disk_io.read_bytes + disk_io.write_bytes, 'bytes', timestamp)

        # 网络IO
        network_io = psutil.net_io_counters()
        if network_io:
            self._add_metric(PerformanceMetric.NETWORK_IO, network_io.bytes_sent + network_io.bytes_recv, 'bytes', timestamp)

    def _collect_custom_metrics(self) -> Any:
        """收集自定义指标"""
        for collector_name, collector_func in self.custom_collectors.items():
            try:
                metrics = collector_func()
                for metric_data in metrics:
                    self._add_metric(**metric_data)
            except Exception as e:
                logger.error(f"自定义收集器 {collector_name} 异常: {e}")

    def _add_metric(self, metric_type: PerformanceMetric, value: float, unit: str,
                   timestamp: datetime, tags: dict[str, str] = None):
        """添加性能数据点"""
        metric_point = MetricPoint(
            timestamp=timestamp,
            metric_type=metric_type,
            value=value,
            unit=unit,
            tags=tags or {}
        )
        self.metrics_buffer.append(metric_point)

    def add_custom_collector(self, name: str, collector_func: Callable) -> None:
        """添加自定义收集器"""
        self.custom_collectors[name] = collector_func
        logger.info(f"添加自定义收集器: {name}")

    def get_metrics(self, metric_type: PerformanceMetric,
                   start_time: datetime | None = None,
                   end_time: datetime | None = None) -> list[MetricPoint]:
        """获取指定类型的性能指标"""
        metrics = []

        for metric_point in self.metrics_buffer:
            if metric_point.metric_type != metric_type:
                continue

            if start_time and metric_point.timestamp < start_time:
                continue

            if end_time and metric_point.timestamp > end_time:
                continue

            metrics.append(metric_point)

        return metrics

    def get_recent_metrics(self, metric_type: PerformanceMetric, minutes: int = 60) -> list[MetricPoint]:
        """获取最近指定时间的性能指标"""
        start_time = datetime.now() - timedelta(minutes=minutes)
        return self.get_metrics(metric_type, start_time=start_time)

class PerformanceAnalyzer:
    """性能分析器"""

    def __init__(self, collector: PerformanceCollector):
        """初始化分析器"""
        self.collector = collector
        self.alert_rules = {}
        self.analysis_cache = {}

    def add_alert_rule(self, metric_type: PerformanceMetric, threshold: float,
                      severity: str = 'medium', message: str = None):
        """添加告警规则"""
        rule_id = f"{metric_type.value}_{threshold}"
        self.alert_rules[rule_id] = {
            'metric_type': metric_type,
            'threshold': threshold,
            'severity': severity,
            'message': message or f"{metric_type.value} 超过阈值 {threshold}"
        }
        logger.info(f"添加告警规则: {rule_id}")

    def check_alerts(self) -> list[PerformanceAlert]:
        """检查性能告警"""
        alerts = []

        for rule_id, rule in self.alert_rules.items():
            # 获取最近的指标数据
            recent_metrics = self.collector.get_recent_metrics(
                rule['metric_type'], minutes=5
            )

            if not recent_metrics:
                continue

            # 检查最新的值是否超过阈值
            latest_metric = recent_metrics[-1]
            if latest_metric.value > rule['threshold']:
                alert = PerformanceAlert(
                    alert_id=f"alert_{rule_id}_{int(time.time())}",
                    metric_type=rule['metric_type'],
                    threshold=rule['threshold'],
                    current_value=latest_metric.value,
                    severity=rule['severity'],
                    message=rule['message'],
                    timestamp=latest_metric.timestamp
                )
                alerts.append(alert)

        return alerts

    def analyze_trend(self, metric_type: PerformanceMetric, hours: int = 24) -> dict[str, Any]:
        """分析性能趋势"""
        # 获取指定时间范围内的指标
        start_time = datetime.now() - timedelta(hours=hours)
        metrics = self.collector.get_metrics(metric_type, start_time=start_time)

        if len(metrics) < 10:
            return {
                'trend': 'insufficient_data',
                'analysis': '数据不足，无法进行趋势分析'
            }

        values = [m.value for m in metrics]

        # 计算统计指标
        avg_value = statistics.mean(values)
        min_value = min(values)
        max_value = max(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0

        # 趋势分析（简单线性回归）
        x_values = list(range(len(values)))
        n = len(values)

        # 计算斜率
        x_mean = statistics.mean(x_values)
        y_mean = avg_value

        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0

        # 判断趋势
        if abs(slope) < 0.01:
            trend = 'stable'
        elif slope > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'

        # 性能评级
        performance_grade = self._calculate_performance_grade(metric_type, avg_value)

        return {
            'metric_type': metric_type.value,
            'trend': trend,
            'slope': slope,
            'statistics': {
                'average': avg_value,
                'minimum': min_value,
                'maximum': max_value,
                'std_dev': std_dev
            },
            'performance_grade': performance_grade,
            'analysis': self._generate_trend_analysis(trend, performance_grade, metric_type),
            'recommendations': self._generate_trend_recommendations(trend, performance_grade, metric_type)
        }

    def _calculate_performance_grade(self, metric_type: PerformanceMetric, value: float) -> str:
        """计算性能评级"""
        grade_thresholds = {
            PerformanceMetric.CPU_USAGE: {'A': 30, 'B': 50, 'C': 70, 'D': 90},
            PerformanceMetric.MEMORY_USAGE: {'A': 40, 'B': 60, 'C': 80, 'D': 90},
            PerformanceMetric.RESPONSE_TIME: {'A': 100, 'B': 300, 'C': 1000, 'D': 3000},
            PerformanceMetric.ERROR_RATE: {'A': 0.1, 'B': 1, 'C': 5, 'D': 10}
        }

        thresholds = grade_thresholds.get(metric_type, {'A': 20, 'B': 40, 'C': 60, 'D': 80})

        if value <= thresholds['A']:
            return 'A'
        elif value <= thresholds['B']:
            return 'B'
        elif value <= thresholds['C']:
            return 'C'
        elif value <= thresholds['D']:
            return 'D'
        else:
            return 'F'

    def _generate_trend_analysis(self, trend: str, grade: str, metric_type: PerformanceMetric) -> str:
        """生成趋势分析"""
        if grade in ['A', 'B']:
            if trend == 'stable':
                return f"{metric_type.value} 性能表现优秀且稳定"
            elif trend == 'increasing' and metric_type in [PerformanceMetric.CPU_USAGE, PerformanceMetric.MEMORY_USAGE]:
                return f"{metric_type.value} 虽然在增加，但仍在可接受范围内"
            elif trend == 'decreasing' and metric_type not in [PerformanceMetric.CPU_USAGE, PerformanceMetric.MEMORY_USAGE]:
                return f"{metric_type.value} 正在改善"
        elif grade == 'C':
            if trend == 'increasing':
                return f"{metric_type.value} 性能中等且有上升趋势，需要关注"
            elif trend == 'stable':
                return f"{metric_type.value} 性能中等但稳定，有优化空间"
        else:
            if trend == 'increasing':
                return f"{metric_type.value} 性能较差且在恶化，需要立即优化"
            else:
                return f"{metric_type.value} 性能较差，需要优化"

        return f"{metric_type.value} 性能评级: {grade}，趋势: {trend}"

    def _generate_trend_recommendations(self, trend: str, grade: str, metric_type: PerformanceMetric) -> list[str]:
        """生成优化建议"""
        recommendations = []

        if grade in ['D', 'F']:
            recommendations.append('立即进行性能优化')

            if metric_type == PerformanceMetric.CPU_USAGE:
                recommendations.extend([
                    '优化算法复杂度',
                    '增加缓存使用',
                    '考虑水平扩展'
                ])
            elif metric_type == PerformanceMetric.MEMORY_USAGE:
                recommendations.extend([
                    '检查内存泄漏',
                    '优化数据结构',
                    '增加内存容量'
                ])
            elif metric_type == PerformanceMetric.RESPONSE_TIME:
                recommendations.extend([
                    '优化数据库查询',
                    '使用异步处理',
                    '增加CDN缓存'
                ])

        elif grade == 'C' and trend == 'increasing':
            recommendations.append('开始规划性能优化')
            recommendations.append('监控系统发展趋势')

        return recommendations

class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self, analyzer: PerformanceAnalyzer):
        """初始化优化器"""
        self.analyzer = analyzer
        self.optimization_history = []
        self.active_optimizations = {}

    def generate_optimization_suggestions(self) -> list[OptimizationSuggestion]:
        """生成优化建议"""
        suggestions = []

        # 分析各种性能指标
        metrics_to_analyze = [
            PerformanceMetric.CPU_USAGE,
            PerformanceMetric.MEMORY_USAGE,
            PerformanceMetric.RESPONSE_TIME,
            PerformanceMetric.ERROR_RATE
        ]

        for metric in metrics_to_analyze:
            analysis = self.analyzer.analyze_trend(metric, hours=24)

            # 根据分析结果生成建议
            metric_suggestions = self._generate_metric_suggestions(metric, analysis)
            suggestions.extend(metric_suggestions)

        # 按优先级排序
        suggestions.sort(key=lambda x: x.priority, reverse=True)

        return suggestions[:10]  # 返回前10个最重要的建议

    def _generate_metric_suggestions(self, metric: PerformanceMetric, analysis: dict[str, Any]) -> list[OptimizationSuggestion]:
        """为特定指标生成建议"""
        suggestions = []
        grade = analysis.get('performance_grade', 'C')
        trend = analysis.get('trend', 'stable')

        if metric == PerformanceMetric.CPU_USAGE:
            if grade in ['D', 'F'] or trend == 'increasing':
                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"cpu_optimization_{int(time.time())}",
                    strategy=OptimizationStrategy.ALGORITHM_OPTIMIZATION,
                    description='优化CPU密集型算法，减少计算复杂度',
                    expected_improvement=30.0,
                    implementation_cost='medium',
                    priority=8 if grade in ['D', 'F'] else 5,
                    steps=[
                        '识别CPU热点函数',
                        '使用性能分析工具定位瓶颈',
                        '优化算法和数据结构',
                        '使用编译优化和JIT技术'
                    ],
                    code_snippets={
                        "example": """
# 使用缓存减少重复计算
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(x, y):
    # 复杂计算逻辑
    return result
                        """
                    }
                ))

                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"async_optimization_{int(time.time())}",
                    strategy=OptimizationStrategy.CONCURRENCY_OPTIMIZATION,
                    description='使用异步编程和并发处理提高CPU利用率',
                    expected_improvement=40.0,
                    implementation_cost='high',
                    priority=7,
                    steps=[
                        '识别可并行化的任务',
                        '使用async/await重构同步代码',
                        '实现线程池或进程池',
                        '使用消息队列解耦处理'
                    ],
                    code_snippets={
                        "example": """
import asyncio

async def process_data_concurrently(data_list):
    tasks = [process_single_item(item) for item in data_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
                        """
                    }
                ))

        elif metric == PerformanceMetric.MEMORY_USAGE:
            if grade in ['D', 'F'] or trend == 'increasing':
                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"memory_optimization_{int(time.time())}",
                    strategy=OptimizationStrategy.MEMORY_OPTIMIZATION,
                    description='优化内存使用，减少内存占用和泄漏',
                    expected_improvement=50.0,
                    implementation_cost='medium',
                    priority=9,
                    steps=[
                        '使用内存分析工具检测泄漏',
                        '优化数据结构和对象池',
                        '实现内存缓存策略',
                        '定期清理无用对象'
                    ],
                    code_snippets={
                        "example": """
# 使用弱引用避免循环引用
import weakref

class ResourceManager:
    def __init__(self):
        self.resources = weakref.WeakValueDictionary()

    def get_resource(self, key):
        return self.resources.get(key)
                        """
                    }
                ))

        elif metric == PerformanceMetric.RESPONSE_TIME:
            if grade in ['C', 'D', 'F']:
                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"cache_optimization_{int(time.time())}",
                    strategy=OptimizationStrategy.CACHE_OPTIMIZATION,
                    description='实现多层缓存策略，减少响应时间',
                    expected_improvement=60.0,
                    implementation_cost='low',
                    priority=8,
                    steps=[
                        '设计缓存架构（L1/L2/L3）',
                        '实现Redis分布式缓存',
                        '添加本地内存缓存',
                        '实现缓存预热和失效策略'
                    ],
                    code_snippets={
                        "example": """
# 多层缓存实现
import redis
from cachetools import TTLCache

class CacheManager:
    def __init__(self):
        self.l1_cache = TTLCache(maxsize=1000, ttl=300)  # 5分钟
        self.redis_client = redis.Redis(host='localhost', port=6379)

    def get(self, key):
        # L1缓存
        if key in self.l1_cache:
            return self.l1_cache[key]

        # L2缓存（Redis）
        value = self.redis_client.get(key)
        if value:
            self.l1_cache[key] = value
            return value

        return None
                        """
                    }
                ))

        return suggestions

    def apply_optimization(self, suggestion_id: str) -> dict[str, Any]:
        """应用优化建议"""
        # 这里应该实现具体的优化逻辑
        # 由于优化需要根据具体情况执行，这里提供框架

        result = {
            'suggestion_id': suggestion_id,
            'applied': False,
            'message': '自动优化功能需要根据具体情况实现',
            'manual_steps': '请根据建议手动实施优化'
        }

        return result

class PerformanceMonitor:
    """性能监控器主类"""

    def __init__(self, collection_interval: int = 30):
        """初始化性能监控器"""
        self.collector = PerformanceCollector(collection_interval)
        self.analyzer = PerformanceAnalyzer(self.collector)
        self.optimizer = PerformanceOptimizer(self.analyzer)
        self.alert_handlers = []
        self.is_running = False

        # 添加默认告警规则
        self._setup_default_alert_rules()

    def _setup_default_alert_rules(self) -> Any:
        """设置默认告警规则"""
        # CPU使用率告警
        self.analyzer.add_alert_rule(PerformanceMetric.CPU_USAGE, 80, 'medium', 'CPU使用率过高')
        self.analyzer.add_alert_rule(PerformanceMetric.CPU_USAGE, 95, 'high', 'CPU使用率严重过高')

        # 内存使用率告警
        self.analyzer.add_alert_rule(PerformanceMetric.MEMORY_USAGE, 85, 'medium', '内存使用率过高')
        self.analyzer.add_alert_rule(PerformanceMetric.MEMORY_USAGE, 95, 'high', '内存使用率严重过高')

        # 响应时间告警
        self.analyzer.add_alert_rule(PerformanceMetric.RESPONSE_TIME, 1000, 'medium', '响应时间过长')
        self.analyzer.add_alert_rule(PerformanceMetric.RESPONSE_TIME, 3000, 'high', '响应时间严重过长')

    def start_monitoring(self) -> Any:
        """开始监控"""
        if self.is_running:
            logger.warning('性能监控已在运行中')
            return

        self.is_running = True
        self.collector.start_collection()

        # 启动后台监控任务
        asyncio.create_task(self._monitoring_loop())

        logger.info('性能监控已启动')

    def stop_monitoring(self) -> Any:
        """停止监控"""
        self.is_running = False
        self.collector.stop_collection()
        logger.info('性能监控已停止')

    async def _monitoring_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                # 检查告警
                alerts = self.analyzer.check_alerts()

                # 处理告警
                for alert in alerts:
                    await self._handle_alert(alert)

                # 每5分钟检查一次
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                await asyncio.sleep(60)

    async def _handle_alert(self, alert: PerformanceAlert):
        """处理告警"""
        logger.warning(f"性能告警: {alert.message} (当前值: {alert.current_value})")

        # 调用告警处理器
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"告警处理器异常: {e}")

    def add_alert_handler(self, handler: Callable) -> None:
        """添加告警处理器"""
        self.alert_handlers.append(handler)

    def get_performance_report(self, hours: int = 24) -> dict[str, Any]:
        """获取性能报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'report_period_hours': hours,
            'metrics_analysis': {},
            'optimization_suggestions': [],
            'summary': {}
        }

        # 分析各种性能指标
        for metric in PerformanceMetric:
            analysis = self.analyzer.analyze_trend(metric, hours)
            if analysis.get('trend') != 'insufficient_data':
                report['metrics_analysis'][metric.value] = analysis

        # 生成优化建议
        suggestions = self.optimizer.generate_optimization_suggestions()
        report['optimization_suggestions'] = [
            {
                'id': s.suggestion_id,
                'strategy': s.strategy.value,
                'description': s.description,
                'expected_improvement': s.expected_improvement,
                'cost': s.implementation_cost,
                'priority': s.priority,
                'steps': s.steps
            }
            for s in suggestions
        ]

        # 生成总结
        report['summary'] = self._generate_performance_summary(report['metrics_analysis'])

        return report

    def _generate_performance_summary(self, metrics_analysis: dict[str, Any]) -> dict[str, Any]:
        """生成性能总结"""
        summary = {
            'overall_grade': 'C',
            'critical_issues': 0,
            'optimization_opportunities': 0,
            'key_metrics': {}
        }

        grades = []

        for metric_name, analysis in metrics_analysis.items():
            grade = analysis.get('performance_grade', 'C')
            grades.append(grade)

            if grade in ['D', 'F']:
                summary['critical_issues'] += 1
            elif grade == 'C':
                summary['optimization_opportunities'] += 1

            summary['key_metrics'][metric_name] = {
                'grade': grade,
                'trend': analysis.get('trend', 'stable'),
                'average': analysis.get('statistics', {}).get('average', 0)
            }

        # 计算总体评级
        if grades:
            grade_values = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}
            avg_grade_value = sum(grade_values[g] for g in grades) / len(grades)

            if avg_grade_value >= 3.5:
                summary['overall_grade'] = 'A'
            elif avg_grade_value >= 2.5:
                summary['overall_grade'] = 'B'
            elif avg_grade_value >= 1.5:
                summary['overall_grade'] = 'C'
            elif avg_grade_value >= 0.5:
                summary['overall_grade'] = 'D'
            else:
                summary['overall_grade'] = 'F'

        return summary

# 全局监控器实例
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器实例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

# 工具函数
async def start_performance_monitoring():
    """启动性能监控"""
    monitor = get_performance_monitor()
    monitor.start_monitoring()

def add_application_metrics_collector(app_name: str, get_metrics_func: Callable) -> None:
    """添加应用级指标收集器"""
    monitor = get_performance_monitor()
    monitor.collector.add_custom_collector(app_name, get_metrics_func)

if __name__ == '__main__':
    async def test_performance_monitoring():
        """测试性能监控"""
        monitor = get_performance_monitor()

        # 添加自定义应用指标
        def collect_app_metrics() -> Any:
            return [
                {
                    'metric_type': PerformanceMetric.RESPONSE_TIME,
                    'value': 150 + (hash(str(time.time())) % 100),
                    'unit': 'ms',
                    'timestamp': datetime.now(),
                    'tags': {'endpoint': '/api/extract'}
                }
            ]

        monitor.collector.add_custom_collector('test_app', collect_app_metrics)

        # 启动监控
        monitor.start_monitoring()

        # 运行一段时间收集数据
        await asyncio.sleep(60)

        # 生成报告
        report = monitor.get_performance_report(hours=1)

        logger.info('性能报告:')
        print(json.dumps(report, indent=2, default=str, ensure_ascii=False))

        # 停止监控
        monitor.stop_monitoring()

    asyncio.run(test_performance_monitoring())
