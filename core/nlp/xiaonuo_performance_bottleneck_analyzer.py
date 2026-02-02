#!/usr/bin/env python3
"""
小诺性能瓶颈分析器
Xiaonuo Performance Bottleneck Analyzer

智能分析NLP系统性能瓶颈,提供优化建议和自动诊断

核心功能:
1. 实时性能监控和异常检测
2. 智能瓶颈识别和根因分析
3. 自动优化建议生成
4. 性能趋势预测
5. 资源使用效率分析

作者: 小诺AI团队
日期: 2025-12-18
"""

import json
import os
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional


from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class BottleneckType(Enum):
    """瓶颈类型"""

    CPU_BOUND = "cpu_bound"  # CPU密集型
    MEMORY_BOUND = "memory_bound"  # 内存密集型
    IO_BOUND = "io_bound"  # IO密集型
    NETWORK_BOUND = "network_bound"  # 网络密集型
    ALGORITHM_BOTTLENECK = "algorithm"  # 算法瓶颈
    DATABASE_BOTTLENECK = "infrastructure/infrastructure/database"  # 数据库瓶颈
    CACHE_EFFICIENCY = "cache"  # 缓存效率
    CONCURRENCY_BOTTLENECK = "concurrency"  # 并发瓶颈
    EXTERNAL_API_BOTTLENECK = "external_api"  # 外部API瓶颈


class SeverityLevel(Enum):
    """严重程度"""

    LOW = 1  # 轻微
    MEDIUM = 2  # 中等
    HIGH = 3  # 严重
    CRITICAL = 4  # 紧急


@dataclass
class PerformanceMetrics:
    """性能指标"""

    timestamp: datetime
    request_id: str
    operation: str

    # 时间指标
    total_time_ms: float = 0.0
    preprocessing_time_ms: float = 0.0
    model_inference_time_ms: float = 0.0
    postprocessing_time_ms: float = 0.0

    # 资源指标
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    disk_io_mb: float = 0.0
    network_io_mb: float = 0.0

    # 业务指标
    input_text_length: int = 0
    output_token_count: int = 0
    cache_hit: bool = False
    batch_size: int = 1

    # 错误信息
    error_occurred: bool = False
    error_type: str = ""
    error_message: str = ""


@dataclass
class Bottleneck:
    """性能瓶颈"""

    id: str
    type: BottleneckType
    severity: SeverityLevel
    operation: str
    description: str

    # 检测时间
    detected_at: datetime = field(default_factory=datetime.now)

    # 影响范围
    affected_requests: list[str] = field(default_factory=list)
    performance_impact_ms: float = 0.0

    # 分析结果
    root_cause: str = ""
    optimization_suggestions: list[str] = field(default_factory=list)

    # 状态
    resolved: bool = False
    resolution_notes: str = ""


@dataclass
class PerformanceTrend:
    """性能趋势"""

    operation: str
    time_window_hours: int

    # 统计数据
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float

    # 吞吐量
    requests_per_second: float

    # 错误率
    error_rate_percent: float

    # 趋势方向
    response_time_trend: str  # "improving", "degrading", "stable"
    throughput_trend: str
    error_rate_trend: str

    # 预测
    predicted_response_time_1h: float
    predicted_throughput_1h: float


class PerformanceBottleneckAnalyzer:
    """性能瓶颈分析器"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or self._get_default_config()

        # 数据存储
        self.metrics_history: deque = deque(maxlen=self.config["metrics_history_size"])
        self.bottlenecks: list[Bottleneck] = []
        self.trends_cache: dict[str, PerformanceTrend] = {}

        # 分析配置
        self.bottleneck_thresholds = {
            "response_time_ms": self.config["slow_request_threshold_ms"],
            "error_rate_percent": self.config["high_error_rate_percent"],
            "cpu_usage_percent": self.config["high_cpu_usage_percent"],
            "memory_usage_mb": self.config["high_memory_usage_mb"],
        }

        # 智能分析配置
        self.anomaly_detector = AnomalyDetector(self.config)
        self.trend_analyzer = TrendAnalyzer(self.config)
        self.recommendation_engine = RecommendationEngine()

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=self.config["analysis_workers"])
        self.analysis_lock = threading.RLock()

        # 自动分析调度
        self.auto_analysis_enabled = self.config.get("auto_analysis_enabled", True)
        self.analysis_interval_seconds = self.config.get("analysis_interval_seconds", 60)
        self.analysis_timer: threading.Timer | None = None

        if self.auto_analysis_enabled:
            self._start_auto_analysis()

        logger.info("🚀 小诺性能瓶颈分析器初始化完成")
        logger.info(f"📊 分析间隔: {self.analysis_interval_seconds}秒")
        logger.info(f"🔍 自动分析: {'启用' if self.auto_analysis_enabled else '禁用'}")

    def _get_default_config(self) -> dict[str, Any]:
        """获取默认配置"""
        return {
            "metrics_history_size": 10000,
            "slow_request_threshold_ms": 500.0,
            "high_error_rate_percent": 5.0,
            "high_cpu_usage_percent": 80.0,
            "high_memory_usage_mb": 1024.0,
            "analysis_workers": 4,
            "auto_analysis_enabled": True,
            "analysis_interval_seconds": 60,
            "trend_analysis_window_hours": 24,
            "min_samples_for_analysis": 100,
            "enable_predictions": True,
        }

    def _start_auto_analysis(self) -> Any:
        """启动自动分析"""
        self.analysis_timer = threading.Timer(
            self.analysis_interval_seconds, self._auto_analysis_loop
        )
        self.analysis_timer.daemon = True
        self.analysis_timer.start()

    def _auto_analysis_loop(self) -> Any:
        """自动分析循环"""
        try:
            self.analyze_performance()
            logger.debug("🔍 自动性能分析完成")
        except Exception as e:
            logger.error(f"❌ 自动性能分析失败: {e}")
        finally:
            # 重新调度下一次分析
            if self.auto_analysis_enabled:
                self._start_auto_analysis()

    def record_metrics(self, metrics: PerformanceMetrics) -> Any:
        """记录性能指标"""
        with self.analysis_lock:
            self.metrics_history.append(metrics)

            # 异步进行实时异常检测
            if self.anomaly_detector.detect_anomaly(metrics):
                self._handle_potential_bottleneck(metrics)

    def analyze_performance(self) -> dict[str, Any]:
        """执行完整的性能分析"""
        logger.info("🔍 开始性能瓶颈分析...")

        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "total_metrics_analyzed": len(self.metrics_history),
            "bottlenecks_found": [],
            "performance_trends": {},
            "optimization_recommendations": [],
            "health_score": 0.0,
        }

        try:
            # 1. 瓶颈检测
            bottlenecks = self._detect_bottlenecks()
            analysis_results["bottlenecks_found"] = [
                self._bottleneck_to_dict(b) for b in bottlenecks
            ]

            # 2. 趋势分析
            trends = self._analyze_trends()
            analysis_results["performance_trends"] = {
                op: self._trend_to_dict(trend) for op, trend in trends.items()
            }

            # 3. 生成优化建议
            recommendations = self._generate_recommendations(bottlenecks, trends)
            analysis_results["optimization_recommendations"] = recommendations

            # 4. 计算健康分数
            analysis_results["health_score"] = self._calculate_health_score(bottlenecks, trends)

            logger.info(
                f"✅ 性能分析完成: 发现{len(bottlenecks)}个瓶颈,健康分数{analysis_results['health_score']:.1f}"
            )

        except Exception as e:
            logger.error(f"❌ 性能分析失败: {e}")
            analysis_results["error"] = str(e)

        return analysis_results

    def _detect_bottlenecks(self) -> list[Bottleneck]:
        """检测性能瓶颈"""
        if len(self.metrics_history) < 10:
            return []

        bottlenecks = []
        recent_metrics = list(self.metrics_history)[-1000:]  # 最近1000条记录

        # 按操作分组分析
        operations_metrics = defaultdict(list)
        for metrics in recent_metrics:
            operations_metrics[metrics.operation].append(metrics)

        for operation, metrics_list in operations_metrics.items():
            operation_bottlenecks = []

            # 1. 响应时间瓶颈
            response_time_bottleneck = self._detect_response_time_bottleneck(
                operation, metrics_list
            )
            if response_time_bottleneck:
                operation_bottlenecks.append(response_time_bottleneck)

            # 2. 错误率瓶颈
            error_rate_bottleneck = self._detect_error_rate_bottleneck(operation, metrics_list)
            if error_rate_bottleneck:
                operation_bottlenecks.append(error_rate_bottleneck)

            # 3. 资源使用瓶颈
            resource_bottlenecks = self._detect_resource_bottlenecks(operation, metrics_list)
            operation_bottlenecks.extend(resource_bottlenecks)

            # 4. 缓存效率瓶颈
            cache_bottleneck = self._detect_cache_efficiency_bottleneck(operation, metrics_list)
            if cache_bottleneck:
                operation_bottlenecks.append(cache_bottleneck)

            bottlenecks.extend(operation_bottlenecks)

        # 更新瓶颈列表
        with self.analysis_lock:
            self.bottlenecks.extend(bottlenecks)
            # 保持最新的100个瓶颈
            self.bottlenecks = self.bottlenecks[-100:]

        return bottlenecks

    def _detect_response_time_bottleneck(
        self, operation: str, metrics_list: list[PerformanceMetrics]
    ) -> Bottleneck | None:
        """检测响应时间瓶颈"""
        response_times = [m.total_time_ms for m in metrics_list]

        if len(response_times) < 10:
            return None

        avg_time = np.mean(response_times)
        p95_time = np.percentile(response_times, 95)

        threshold = self.bottleneck_thresholds["response_time_ms"]

        if avg_time > threshold or p95_time > threshold * 2:
            severity = self._calculate_severity(avg_time, threshold)

            bottleneck = Bottleneck(
                id=f"response_time_{operation}_{int(time.time())}",
                type=BottleneckType.CPU_BOUND,
                severity=severity,
                operation=operation,
                description=f"响应时间过长: 平均{avg_time:.1f}ms, P95{p95_time:.1f}ms",
                affected_requests=[
                    m.request_id for m in metrics_list if m.total_time_ms > threshold
                ],
                performance_impact_ms=avg_time - threshold,
                root_cause=self._analyze_response_time_root_cause(operation, metrics_list),
                optimization_suggestions=self._generate_response_time_suggestions(
                    operation, metrics_list
                ),
            )

            return bottleneck

        return None

    def _detect_error_rate_bottleneck(
        self, operation: str, metrics_list: list[PerformanceMetrics]
    ) -> Bottleneck | None:
        """检测错误率瓶颈"""
        if len(metrics_list) < 10:
            return None

        error_count = sum(1 for m in metrics_list if m.error_occurred)
        error_rate = (error_count / len(metrics_list)) * 100

        threshold = self.bottleneck_thresholds["error_rate_percent"]

        if error_rate > threshold:
            severity = SeverityLevel.CRITICAL if error_rate > threshold * 2 else SeverityLevel.HIGH

            # 分析错误类型
            error_types = defaultdict(int)
            for m in metrics_list:
                if m.error_occurred:
                    error_types[m.error_type] += 1

            most_common_error = (
                max(error_types.items(), key=lambda x: x[1]) if error_types else ("Unknown", 0)
            )

            bottleneck = Bottleneck(
                id=f"error_rate_{operation}_{int(time.time())}",
                type=BottleneckType.ALGORITHM_BOTTLENECK,
                severity=severity,
                operation=operation,
                description=f"错误率过高: {error_rate:.2f}%, 主要错误类型: {most_common_error[0]}",
                affected_requests=[m.request_id for m in metrics_list if m.error_occurred],
                performance_impact_ms=0.0,
                root_cause=f"错误率{error_rate:.2f}%超过阈值{threshold}%, 主要错误: {most_common_error[0]}",
                optimization_suggestions=self._generate_error_rate_suggestions(
                    operation, error_types, metrics_list
                ),
            )

            return bottleneck

        return None

    def _detect_resource_bottlenecks(
        self, operation: str, metrics_list: list[PerformanceMetrics]
    ) -> list[Bottleneck]:
        """检测资源使用瓶颈"""
        bottlenecks = []

        if len(metrics_list) < 10:
            return bottlenecks

        # CPU使用率瓶颈
        cpu_usages = [m.cpu_usage_percent for m in metrics_list if m.cpu_usage_percent > 0]
        if cpu_usages:
            avg_cpu = np.mean(cpu_usages)
            threshold = self.bottleneck_thresholds["high_cpu_usage_percent"]

            if avg_cpu > threshold:
                bottleneck = Bottleneck(
                    id=f"cpu_{operation}_{int(time.time())}",
                    type=BottleneckType.CPU_BOUND,
                    severity=self._calculate_severity(avg_cpu, threshold),
                    operation=operation,
                    description=f"CPU使用率过高: 平均{avg_cpu:.1f}%",
                    root_cause="CPU密集型操作或算法复杂度过高",
                    optimization_suggestions=[
                        "优化算法复杂度",
                        "使用并行处理",
                        "考虑使用更高效的库或算法",
                        "增加批处理大小以摊薄成本",
                    ],
                )
                bottlenecks.append(bottleneck)

        # 内存使用瓶颈
        memory_usages = [m.memory_usage_mb for m in metrics_list if m.memory_usage_mb > 0]
        if memory_usages:
            avg_memory = np.mean(memory_usages)
            threshold = self.bottleneck_thresholds["high_memory_usage_mb"]

            if avg_memory > threshold:
                bottleneck = Bottleneck(
                    id=f"memory_{operation}_{int(time.time())}",
                    type=BottleneckType.MEMORY_BOUND,
                    severity=self._calculate_severity(avg_memory, threshold),
                    operation=operation,
                    description=f"内存使用过高: 平均{avg_memory:.1f}MB",
                    root_cause="内存密集型操作或内存泄漏",
                    optimization_suggestions=[
                        "优化数据结构",
                        "使用生成器或流式处理",
                        "定期清理缓存",
                        "增加内存池管理",
                    ],
                )
                bottlenecks.append(bottleneck)

        return bottlenecks

    def _detect_cache_efficiency_bottleneck(
        self, operation: str, metrics_list: list[PerformanceMetrics]
    ) -> Bottleneck | None:
        """检测缓存效率瓶颈"""
        cache_metrics = [m for m in metrics_list if hasattr(m, "cache_hit")]

        if len(cache_metrics) < 20:
            return None

        cache_hits = sum(1 for m in cache_metrics if m.cache_hit)
        cache_hit_rate = (cache_hits / len(cache_metrics)) * 100

        if cache_hit_rate < 70:  # 缓存命中率低于70%
            severity = SeverityLevel.MEDIUM if cache_hit_rate > 50 else SeverityLevel.HIGH

            bottleneck = Bottleneck(
                id=f"cache_{operation}_{int(time.time())}",
                type=BottleneckType.CACHE_EFFICIENCY,
                severity=severity,
                operation=operation,
                description=f"缓存效率低: 命中率仅{cache_hit_rate:.1f}%",
                root_cause="缓存策略不当或缓存容量不足",
                optimization_suggestions=[
                    "增加缓存容量",
                    "优化缓存键设计",
                    "调整缓存过期策略",
                    "实现预热机制",
                    "考虑使用多级缓存",
                ],
            )

            return bottleneck

        return None

    def _analyze_trends(self) -> dict[str, PerformanceTrend]:
        """分析性能趋势"""
        if len(self.metrics_history) < 100:
            return {}

        # 按操作分组分析趋势
        operations = {m.operation for m in self.metrics_history}
        trends = {}

        window_hours = self.config["trend_analysis_window_hours"]
        cutoff_time = datetime.now() - timedelta(hours=window_hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

        for operation in operations:
            op_metrics = [m for m in recent_metrics if m.operation == operation]

            if len(op_metrics) < 20:  # 样本太少
                continue

            # 检查缓存中是否有现有趋势
            cache_key = f"{operation}_{window_hours}h"
            if cache_key in self.trends_cache:
                cached_trend = self.trends_cache[cache_key]
                # 如果缓存是最近1小时内的,直接使用
                if (datetime.now() - cached_trend.timestamp).seconds < 3600:
                    trends[operation] = cached_trend
                    continue

            # 计算新的趋势
            trend = self._calculate_trend(operation, op_metrics, window_hours)
            trends[operation] = trend

            # 缓存趋势
            self.trends_cache[cache_key] = trend

            # 清理过期缓存
            self._cleanup_trends_cache()

        return trends

    def _calculate_trend(
        self, operation: str, metrics_list: list[PerformanceMetrics], window_hours: int
    ) -> PerformanceTrend:
        """计算性能趋势"""
        response_times = [m.total_time_ms for m in metrics_list]

        # 时间窗口内的请求统计
        time_span = (metrics_list[-1].timestamp - metrics_list[0].timestamp).total_seconds()
        rps = len(metrics_list) / max(time_span, 1)

        # 错误率
        errors = sum(1 for m in metrics_list if m.error_occurred)
        error_rate = (errors / len(metrics_list)) * 100

        # 分位数
        p50 = np.percentile(response_times, 50)
        p95 = np.percentile(response_times, 95)
        p99 = np.percentile(response_times, 99)

        # 趋势分析(简化版本,使用线性回归斜率)
        response_time_trend = self._analyze_trend_direction(
            response_times[:50], response_times[-50:]
        )
        throughput_trend = "stable"  # 简化处理
        error_rate_trend = "stable"  # 简化处理

        # 简单预测(使用历史平均值)
        predicted_response_time = (
            np.mean(response_times[-10:]) if len(response_times) >= 10 else np.mean(response_times)
        )
        predicted_throughput = rps  # 简化预测

        return PerformanceTrend(
            operation=operation,
            time_window_hours=window_hours,
            avg_response_time_ms=np.mean(response_times),
            p50_response_time_ms=p50,
            p95_response_time_ms=p95,
            p99_response_time_ms=p99,
            requests_per_second=rps,
            error_rate_percent=error_rate,
            response_time_trend=response_time_trend,
            throughput_trend=throughput_trend,
            error_rate_trend=error_rate_trend,
            predicted_response_time_1h=predicted_response_time,
            predicted_throughput_1h=predicted_throughput,
            timestamp=datetime.now(),
        )

    def _analyze_trend_direction(self, early_data: list[float], late_data: list[float]) -> str:
        """分析趋势方向"""
        if len(early_data) < 5 or len(late_data) < 5:
            return "stable"

        early_avg = np.mean(early_data)
        late_avg = np.mean(late_data)

        change_percent = ((late_avg - early_avg) / early_avg) * 100

        if abs(change_percent) < 5:
            return "stable"
        elif change_percent > 0:
            return "degrading"
        else:
            return "improving"

    def _generate_recommendations(
        self, bottlenecks: list[Bottleneck], trends: dict[str, PerformanceTrend]
    ) -> list[dict[str, Any]]:
        """生成优化建议"""
        recommendations = []

        # 基于瓶颈的建议
        bottleneck_types = defaultdict(int)
        for bottleneck in bottlenecks:
            bottleneck_types[bottleneck.type] += 1
            if bottleneck.optimization_suggestions:
                recommendations.extend(
                    [
                        {
                            "type": "bottleneck_specific",
                            "category": bottleneck.type.value,
                            "operation": bottleneck.operation,
                            "severity": bottleneck.severity.value,
                            "suggestion": suggestion,
                            "impact": "high",
                            "estimated_improvement": "20-50%",
                        }
                        for suggestion in bottleneck.optimization_suggestions
                    ]
                )

        # 基于趋势的建议
        for operation, trend in trends.items():
            if trend.response_time_trend == "degrading":
                recommendations.append(
                    {
                        "type": "trend_based",
                        "category": "performance_degradation",
                        "operation": operation,
                        "suggestion": f"{operation}操作响应时间呈恶化趋势,建议立即优化",
                        "impact": "high",
                        "estimated_improvement": "30-70%",
                    }
                )

            if trend.error_rate_trend == "degrading":
                recommendations.append(
                    {
                        "type": "trend_based",
                        "category": "error_rate_increase",
                        "operation": operation,
                        "suggestion": f"{operation}操作错误率上升,需要加强错误处理和监控",
                        "impact": "critical",
                        "estimated_improvement": "50-90%",
                    }
                )

        # 去重并按优先级排序
        unique_recommendations = []
        seen = set()

        for rec in recommendations:
            key = (rec["operation"], rec["suggestion"])
            if key not in seen:
                unique_recommendations.append(rec)
                seen.add(key)

        # 按严重程度排序
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        unique_recommendations.sort(
            key=lambda x: severity_order.get(x.get("impact", "low"), 1), reverse=True
        )

        return unique_recommendations[:10]  # 返回前10个最重要的建议

    def _calculate_health_score(
        self, bottlenecks: list[Bottleneck], trends: dict[str, PerformanceTrend]
    ) -> float:
        """计算系统健康分数 (0-100)"""
        base_score = 100.0

        # 根据瓶颈扣分
        for bottleneck in bottlenecks:
            penalty = {
                SeverityLevel.LOW: 2,
                SeverityLevel.MEDIUM: 5,
                SeverityLevel.HIGH: 10,
                SeverityLevel.CRITICAL: 20,
            }.get(bottleneck.severity, 5)

            base_score -= penalty

        # 根据趋势扣分
        for trend in trends.values():
            if trend.response_time_trend == "degrading":
                base_score -= 5
            if trend.error_rate_trend == "degrading":
                base_score -= 8
            if trend.error_rate_percent > 5:
                base_score -= 10

        return max(0.0, min(100.0, base_score))

    def _handle_potential_bottleneck(self, metrics: PerformanceMetrics) -> Any:
        """处理潜在瓶颈"""
        # 异步处理异常检测
        self.executor.submit(self._analyze_anomaly_details, metrics)

    def _analyze_anomaly_details(self, metrics: PerformanceMetrics) -> Any:
        """分析异常详情"""
        try:
            # 这里可以添加更详细的异常分析逻辑
            logger.debug(f"分析异常: {metrics.request_id} - {metrics.operation}")
        except Exception as e:
            logger.error(f"异常详情分析失败: {e}")

    # 辅助方法
    def _calculate_severity(self, value: float, threshold: float) -> SeverityLevel:
        """计算严重程度"""
        ratio = value / threshold
        if ratio > 3:
            return SeverityLevel.CRITICAL
        elif ratio > 2:
            return SeverityLevel.HIGH
        elif ratio > 1.5:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW

    def _analyze_response_time_root_cause(
        self, operation: str, metrics_list: list[PerformanceMetrics]
    ) -> str:
        """分析响应时间根因"""
        avg_total = np.mean([m.total_time_ms for m in metrics_list])
        avg_preprocessing = np.mean([m.preprocessing_time_ms for m in metrics_list])
        avg_inference = np.mean([m.model_inference_time_ms for m in metrics_list])
        avg_postprocessing = np.mean([m.postprocessing_time_ms for m in metrics_list])

        max_phase = max(
            [
                ("预处理", avg_preprocessing),
                ("模型推理", avg_inference),
                ("后处理", avg_postprocessing),
            ],
            key=lambda x: x[1],
        )

        return f"{max_phase[0]}是主要瓶颈({max_phase[1]:.1f}ms), 占总时间的{max_phase[1]/avg_total*100:.1f}%"

    def _generate_response_time_suggestions(
        self, operation: str, metrics_list: list[PerformanceMetrics]
    ) -> list[str]:
        """生成响应时间优化建议"""
        suggestions = []

        avg_inference = np.mean([m.model_inference_time_ms for m in metrics_list])
        if avg_inference > 200:
            suggestions.extend(
                ["考虑使用更小的模型或模型量化", "启用模型并行或批处理", "优化输入数据预处理"]
            )

        avg_batch_size = np.mean([m.batch_size for m in metrics_list])
        if avg_batch_size < 4:
            suggestions.append("增加批处理大小以提高吞吐量")

        return suggestions[:3]

    def _generate_error_rate_suggestions(
        self, operation: str, error_types: dict[str, int], metrics_list: list[PerformanceMetrics]
    ) -> list[str]:
        """生成错误率优化建议"""
        suggestions = []

        most_common_error = max(error_types.items(), key=lambda x: x[1])
        error_type, _count = most_common_error

        if "timeout" in error_type.lower():
            suggestions.extend(["增加超时时间设置", "优化处理逻辑减少处理时间", "实现异步处理"])

        if "modules/modules/memory/modules/memory/modules/memory/memory" in error_type.lower():
            suggestions.extend(["增加内存限制", "优化内存使用", "实现内存监控和预警"])

        if "validation" in error_type.lower():
            suggestions.extend(["改进输入验证逻辑", "提供更友好的错误提示", "实现数据预处理清理"])

        return suggestions[:4]

    def _cleanup_trends_cache(self) -> Any:
        """清理趋势缓存"""
        max_cache_size = 100
        if len(self.trends_cache) > max_cache_size:
            # 删除最旧的缓存项
            oldest_keys = sorted(
                self.trends_cache.keys(), key=lambda k: self.trends_cache[k].timestamp
            )[: len(self.trends_cache) - max_cache_size]

            for key in oldest_keys:
                del self.trends_cache[key]

    def _bottleneck_to_dict(self, bottleneck: Bottleneck) -> dict[str, Any]:
        """瓶颈转字典"""
        result = asdict(bottleneck)
        result["type"] = bottleneck.type.value
        result["severity"] = bottleneck.severity.value
        result["detected_at"] = bottleneck.detected_at.isoformat()
        return result

    def _trend_to_dict(self, trend: PerformanceTrend) -> dict[str, Any]:
        """趋势转字典"""
        result = asdict(trend)
        if hasattr(trend, "timestamp"):
            result["timestamp"] = trend.timestamp.isoformat()
        return result

    def get_bottleneck_report(self) -> dict[str, Any]:
        """获取瓶颈报告"""
        with self.analysis_lock:
            active_bottlenecks = [b for b in self.bottlenecks if not b.resolved]
            resolved_bottlenecks = [b for b in self.bottlenecks if b.resolved]

            return {
                "timestamp": datetime.now().isoformat(),
                "total_bottlenecks": len(self.bottlenecks),
                "active_bottlenecks": len(active_bottlenecks),
                "resolved_bottlenecks": len(resolved_bottlenecks),
                "active_bottleneck_details": [
                    self._bottleneck_to_dict(b) for b in active_bottlenecks
                ],
                "bottleneck_by_type": self._count_bottlenecks_by_type(active_bottlenecks),
                "bottleneck_by_severity": self._count_bottlenecks_by_severity(active_bottlenecks),
            }

    def _count_bottlenecks_by_type(self, bottlenecks: list[Bottleneck]) -> dict[str, int]:
        """按类型统计瓶颈"""
        counts = defaultdict(int)
        for bottleneck in bottlenecks:
            counts[bottleneck.type.value] += 1
        return dict(counts)

    def _count_bottlenecks_by_severity(self, bottlenecks: list[Bottleneck]) -> dict[str, int]:
        """按严重程度统计瓶颈"""
        counts = defaultdict(int)
        for bottleneck in bottlenecks:
            counts[bottleneck.severity.name] += 1
        return dict(counts)

    def resolve_bottleneck(self, bottleneck_id: str, resolution_notes: str = "") -> Any:
        """标记瓶颈为已解决"""
        with self.analysis_lock:
            for bottleneck in self.bottlenecks:
                if bottleneck.id == bottleneck_id:
                    bottleneck.resolved = True
                    bottleneck.resolution_notes = resolution_notes
                    logger.info(f"✅ 瓶颈已解决: {bottleneck_id}")
                    return True
        return False

    def save_analysis_data(self, filepath: str | None = None) -> None:
        """保存分析数据"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"data/performance_analysis_{timestamp}.json"

        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            data = {
                "timestamp": datetime.now().isoformat(),
                "config": self.config,
                "bottlenecks": [self._bottleneck_to_dict(b) for b in self.bottlenecks],
                "trends_cache": {
                    key: self._trend_to_dict(trend) for key, trend in self.trends_cache.items()
                },
                "metrics_count": len(self.metrics_history),
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"💾 性能分析数据已保存: {filepath}")

        except Exception as e:
            logger.error(f"❌ 保存分析数据失败: {e}")

    def cleanup(self) -> Any:
        """清理资源"""
        logger.info("🧹 正在清理性能瓶颈分析器资源...")

        if self.analysis_timer:
            self.analysis_timer.cancel()

        self.executor.shutdown(wait=True)

        with self.analysis_lock:
            self.metrics_history.clear()
            self.bottlenecks.clear()
            self.trends_cache.clear()

        logger.info("✅ 性能瓶颈分析器资源清理完成")


# 辅助类
class AnomalyDetector:
    """异常检测器"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.threshold_multiplier = 2.0

    def detect_anomaly(self, metrics: PerformanceMetrics) -> bool:
        """检测异常"""
        # 简化的异常检测逻辑
        return (
            metrics.total_time_ms
            > self.config["slow_request_threshold_ms"] * self.threshold_multiplier
            or metrics.memory_usage_mb
            > self.config["high_memory_usage_mb"] * self.threshold_multiplier
        )


class TrendAnalyzer:
    """趋势分析器"""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    def analyze_trend(self, data_points: list[float]) -> str:
        """分析趋势"""
        if len(data_points) < 10:
            return "insufficient_data"

        # 简化的趋势分析
        first_half = data_points[: len(data_points) // 2]
        second_half = data_points[len(data_points) // 2 :]

        first_avg = np.mean(first_half)
        second_avg = np.mean(second_half)

        if abs(second_avg - first_avg) / first_avg < 0.05:
            return "stable"
        elif second_avg > first_avg:
            return "increasing"
        else:
            return "decreasing"


class RecommendationEngine:
    """推荐引擎"""

    def __init__(self):
        self.recommendations_db = {
            "cpu_bound": ["优化算法复杂度", "使用并行处理", "考虑使用更高效的库"],
            "memory_bound": ["优化数据结构", "使用生成器或流式处理", "定期清理缓存"],
            "io_bound": ["使用异步IO", "增加缓存层", "优化数据库查询"],
        }

    def get_recommendations(self, bottleneck_type: str) -> list[str]:
        """获取推荐"""
        return self.recommendations_db.get(bottleneck_type, [])


def create_performance_analyzer() -> PerformanceBottleneckAnalyzer:
    """创建性能分析器实例"""
    return PerformanceBottleneckAnalyzer()


# 测试代码
if __name__ == "__main__":
    # 创建分析器
    analyzer = create_performance_analyzer()

    # 模拟一些性能数据
    print("🧪 开始测试性能瓶颈分析器...")

    # 正常数据
    for i in range(50):
        metrics = PerformanceMetrics(
            timestamp=datetime.now() - timedelta(minutes=i),
            request_id=f"req_{i}",
            operation="intent_classification",
            total_time_ms=50 + np.random.normal(0, 10),
            cpu_usage_percent=30 + np.random.normal(0, 5),
            memory_usage_mb=200 + np.random.normal(0, 20),
        )
        analyzer.record_metrics(metrics)

    # 模拟一些瓶颈数据
    for i in range(20):
        metrics = PerformanceMetrics(
            timestamp=datetime.now() - timedelta(minutes=i / 2),
            request_id=f"slow_req_{i}",
            operation="semantic_similarity",
            total_time_ms=800 + np.random.normal(0, 100),  # 慢请求
            cpu_usage_percent=90 + np.random.normal(0, 5),  # 高CPU
            memory_usage_mb=1500 + np.random.normal(0, 100),  # 高内存
            error_occurred=i < 3,  # 一些错误
        )
        analyzer.record_metrics(metrics)

    # 执行分析
    print("\n🔍 执行性能分析...")
    analysis_results = analyzer.analyze_performance()

    print("\n📊 分析结果:")
    print(f"   总指标数: {analysis_results['total_metrics_analyzed']}")
    print(f"   发现瓶颈: {len(analysis_results['bottlenecks_found'])}")
    print(f"   健康分数: {analysis_results['health_score']:.1f}")

    if analysis_results["bottlenecks_found"]:
        print("\n⚠️ 主要瓶颈:")
        for bottleneck in analysis_results["bottlenecks_found"][:3]:
            print(f"   - {bottleneck['description']}")

    if analysis_results["optimization_recommendations"]:
        print("\n💡 优化建议:")
        for rec in analysis_results["optimization_recommendations"][:3]:
            print(f"   - {rec['suggestion']}")

    # 清理
    analyzer.cleanup()
    print("\n✅ 性能瓶颈分析器测试完成!")
