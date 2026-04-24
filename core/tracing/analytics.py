"""
性能分析器模块 - 从Jaeger获取并分析追踪数据

本模块提供性能分析功能，包括：
- 延迟指标分析（P50, P95, P99）
- 慢操作识别
- 性能瓶颈检测
- 错误率统计

Author: Athena Team
Date: 2026-04-24
"""

from opentelemetry import trace
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import statistics
import asyncio
import aiohttp
import json
from pathlib import Path


@dataclass
class SpanMetrics:
    """Span指标数据类

    用于存储和分析单个操作的性能指标。

    Attributes:
        span_name: Span/操作名称
        operation: 操作类型
        count: 请求数量
        total_duration_ms: 总持续时间（毫秒）
        avg_duration_ms: 平均延迟（毫秒）
        min_duration_ms: 最小延迟（毫秒）
        max_duration_ms: 最大延迟（毫秒）
        p50_duration_ms: P50延迟（中位数）
        p95_duration_ms: P95延迟
        p99_duration_ms: P99延迟
        error_count: 错误数量
        error_rate: 错误率
        throughput_qps: 吞吐量（每秒请求数）
    """
    span_name: str
    operation: str = ""
    count: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    min_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    p50_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0
    error_count: int = 0
    error_rate: float = 0.0
    throughput_qps: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "span_name": self.span_name,
            "operation": self.operation,
            "count": self.count,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "min_duration_ms": round(self.min_duration_ms, 2),
            "max_duration_ms": round(self.max_duration_ms, 2),
            "p50_duration_ms": round(self.p50_duration_ms, 2),
            "p95_duration_ms": round(self.p95_duration_ms, 2),
            "p99_duration_ms": round(self.p99_duration_ms, 2),
            "error_count": self.error_count,
            "error_rate": round(self.error_rate, 4),
            "throughput_qps": round(self.throughput_qps, 2)
        }


@dataclass
class SlowOperation:
    """慢操作数据类"""
    operation: str
    span_id: str
    trace_id: str
    duration_ms: float
    timestamp: datetime
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BottleneckInfo:
    """瓶颈信息数据类"""
    component: str
    operation: str
    avg_duration_ms: float
    p95_duration_ms: float
    impact_score: float  # 影响分数 0-100
    recommendation: str


class PerformanceAnalyzer:
    """性能分析器 - 从Jaeger获取并分析追踪数据

    支持从Jaeger API查询追踪数据，并进行性能分析。

    Args:
        jaeger_endpoint: Jaeger UI端点地址
        jaeger_api_endpoint: Jaeger API端点地址（可选，默认为UI端点的/api）
        timeout: API请求超时时间（秒）

    Example:
        >>> analyzer = PerformanceAnalyzer()
        >>> spans = await analyzer.query_spans("xiaona-agent", "patent_analysis")
        >>> metrics = analyzer.analyze_latency(spans)
        >>> print(f"平均延迟: {metrics.avg_duration_ms:.2f}ms")
    """

    def __init__(
        self,
        jaeger_endpoint: str = "http://localhost:16686",
        jaeger_api_endpoint: Optional[str] = None,
        timeout: int = 30
    ):
        self.jaeger_endpoint = jaeger_endpoint.rstrip("/")
        self.jaeger_api_endpoint = (
            jaeger_api_endpoint
            if jaeger_api_endpoint
            else f"{jaeger_endpoint.rstrip('/').replace('16686', '16686')}/api"
        )
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """关闭HTTP会话"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def query_spans(
        self,
        service: str,
        operation: Optional[str] = None,
        lookback: timedelta = timedelta(minutes=15),
        limit: int = 1000
    ) -> List[Dict]:
        """从Jaeger查询Spans

        Args:
            service: 服务名称
            operation: 操作名称（可选）
            lookback: 查询时间范围
            limit: 返回结果数量限制

        Returns:
            Span列表
        """
        session = await self._get_session()

        # 计算时间范围（微秒时间戳）
        end_time = datetime.now()
        start_time = end_time - lookback

        start_micros = int(start_time.timestamp() * 1_000_000)
        end_micros = int(end_time.timestamp() * 1_000_000)

        # 构建查询参数
        params = {
            "service": service,
            "start": start_micros,
            "end": end_micros,
            "limit": limit
        }

        if operation:
            params["operation"] = operation

        try:
            # 使用Jaeger API查询
            url = f"{self.jaeger_api_endpoint}/traces"
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return []

                data = await response.json()

                # 提取所有spans
                spans = []
                for trace in data.get("data", []):
                    for span in trace.get("spans", []):
                        spans.append({
                            "traceID": span.get("traceID"),
                            "spanID": span.get("spanID"),
                            "operationName": span.get("operationName"),
                            "duration": span.get("duration", 0),  # 微秒
                            "startTime": span.get("startTime", 0),
                            "tags": span.get("tags", []),
                            "process": span.get("process", {}),
                            "references": span.get("references", [])
                        })

                return spans

        except Exception as e:
            print(f"查询Jaeger API失败: {e}")
            return []

    async def query_traces(
        self,
        service: str,
        operation: Optional[str] = None,
        lookback: timedelta = timedelta(minutes=15),
        limit: int = 100
    ) -> List[Dict]:
        """从Jaeger查询完整Traces

        Args:
            service: 服务名称
            operation: 操作名称（可选）
            lookback: 查询时间范围
            limit: 返回结果数量限制

        Returns:
            Trace列表（包含完整的span树）
        """
        session = await self._get_session()

        end_time = datetime.now()
        start_time = end_time - lookback

        start_micros = int(start_time.timestamp() * 1_000_000)
        end_micros = int(end_time.timestamp() * 1_000_000)

        params = {
            "service": service,
            "start": start_micros,
            "end": end_micros,
            "limit": limit
        }

        if operation:
            params["operation"] = operation

        try:
            url = f"{self.jaeger_api_endpoint}/traces"
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return []

                data = await response.json()
                return data.get("data", [])

        except Exception as e:
            print(f"查询Jaeger API失败: {e}")
            return []

    def analyze_latency(self, spans: List[Dict]) -> SpanMetrics:
        """分析延迟指标

        Args:
            spans: Span列表

        Returns:
            SpanMetrics对象，包含延迟统计数据
        """
        if not spans:
            return SpanMetrics(span_name="")

        # 提取持续时间（微秒转毫秒）
        durations = [s.get("duration", 0) / 1000 for s in spans]

        # 统计错误
        error_count = 0
        for span in spans:
            tags = span.get("tags", [])
            for tag in tags:
                if tag.get("key") == "error" and tag.get("value") is True:
                    error_count += 1
                    break

        # 计算分位数
        sorted_durations = sorted(durations)

        def safe_quantile(data, q):
            """安全计算分位数"""
            if not data:
                return 0
            if len(data) == 1:
                return data[0]
            index = int(len(data) * q)
            if index >= len(data):
                index = len(data) - 1
            return data[index]

        p50 = safe_quantile(sorted_durations, 0.50)
        p95 = safe_quantile(sorted_durations, 0.95)
        p99 = safe_quantile(sorted_durations, 0.99)

        # 获取操作名称
        operation_name = spans[0].get("operationName", "unknown")

        # 计算吞吐量（基于时间范围）
        if spans:
            start_times = [s.get("startTime", 0) for s in spans]
            min_start = min(start_times) / 1_000_000  # 转换为秒
            max_start = max(start_times) / 1_000_000
            time_range = max(max_start - min_start, 1)  # 至少1秒
            throughput = len(spans) / time_range
        else:
            throughput = 0

        return SpanMetrics(
            span_name=operation_name,
            operation=operation_name,
            count=len(spans),
            total_duration_ms=sum(durations),
            avg_duration_ms=statistics.mean(durations) if durations else 0,
            min_duration_ms=min(durations) if durations else 0,
            max_duration_ms=max(durations) if durations else 0,
            p50_duration_ms=p50,
            p95_duration_ms=p95,
            p99_duration_ms=p99,
            error_count=error_count,
            error_rate=error_count / len(spans) if spans else 0,
            throughput_qps=throughput
        )

    def identify_slow_operations(
        self,
        spans: List[Dict],
        threshold_ms: float = 100
    ) -> List[SlowOperation]:
        """识别慢操作

        Args:
            spans: Span列表
            threshold_ms: 慢操作阈值（毫秒）

        Returns:
            慢操作列表，按持续时间降序排列
        """
        slow_ops = []

        for span in spans:
            duration_ms = span.get("duration", 0) / 1000

            if duration_ms >= threshold_ms:
                # 提取属性
                attributes = {}
                for tag in span.get("tags", []):
                    key = tag.get("key")
                    value = tag.get("value")
                    if key and value is not None:
                        attributes[key] = str(value)

                # 转换时间戳
                start_time = span.get("startTime", 0)
                timestamp = datetime.fromtimestamp(start_time / 1_000_000)

                slow_ops.append(SlowOperation(
                    operation=span.get("operationName", "unknown"),
                    span_id=span.get("spanID", ""),
                    trace_id=span.get("traceID", ""),
                    duration_ms=duration_ms,
                    timestamp=timestamp,
                    attributes=attributes
                ))

        # 按持续时间降序排序
        slow_ops.sort(key=lambda x: x.duration_ms, reverse=True)
        return slow_ops

    async def detect_bottlenecks(
        self,
        service: str,
        lookback: timedelta = timedelta(minutes=15)
    ) -> List[BottleneckInfo]:
        """检测性能瓶颈

        分析指定服务的所有操作，识别性能瓶颈。

        Args:
            service: 服务名称
            lookback: 分析时间范围

        Returns:
            瓶颈信息列表，按影响分数降序排列
        """
        # 获取服务的所有操作
        session = await self._get_session()

        try:
            # 获取服务操作列表
            url = f"{self.jaeger_api_endpoint}/operations"
            params = {"service": service}

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return []

                operations_data = await response.json()
                operations = operations_data.get("data", [])

        except Exception as e:
            print(f"获取操作列表失败: {e}")
            return []

        bottlenecks = []

        for operation in operations:
            op_name = operation if isinstance(operation, str) else operation.get("name", "")

            # 查询该操作的spans
            spans = await self.query_spans(service, op_name, lookback)

            if not spans:
                continue

            metrics = self.analyze_latency(spans)

            # 计算影响分数
            # 分数基于：平均延迟、P95延迟、请求频率
            impact_score = (
                min(metrics.avg_duration_ms / 100, 1) * 40 +  # 平均延迟贡献40%
                min(metrics.p95_duration_ms / 500, 1) * 30 +  # P95延迟贡献30%
                min(metrics.count / 100, 1) * 30  # 请求频率贡献30%
            )

            # 生成建议
            recommendation = self._generate_recommendation(metrics)

            bottlenecks.append(BottleneckInfo(
                component=service,
                operation=op_name,
                avg_duration_ms=metrics.avg_duration_ms,
                p95_duration_ms=metrics.p95_duration_ms,
                impact_score=impact_score,
                recommendation=recommendation
            ))

        # 按影响分数降序排序
        bottlenecks.sort(key=lambda x: x.impact_score, reverse=True)
        return bottlenecks

    def _generate_recommendation(self, metrics: SpanMetrics) -> str:
        """生成优化建议"""
        if metrics.avg_duration_ms > 1000:
            return "平均延迟超过1秒，建议：检查LLM调用超时配置、优化数据库查询"
        elif metrics.p95_duration_ms > 500:
            return "P95延迟较高，建议：分析长尾请求、添加重试机制"
        elif metrics.error_rate > 0.05:
            return f"错误率较高({metrics.error_rate:.1%})，建议：检查错误日志、添加降级策略"
        elif metrics.avg_duration_ms > 100:
            return "平均延迟偏高，建议：启用缓存、优化算法"
        else:
            return "性能良好，持续监控"

    def analyze_trace_tree(self, trace: Dict) -> Dict[str, Any]:
        """分析完整的Trace树

        分析一个完整trace的span树结构，识别关键路径和耗时分布。

        Args:
            trace: Jaeger trace对象

        Returns:
            分析结果字典
        """
        spans = trace.get("spans", [])

        if not spans:
            return {}

        # 构建span关系
        span_map = {s["spanID"]: s for s in spans}
        root_spans = [s for s in spans if not s.get("references")]

        # 分析每个根span
        analysis = {
            "trace_id": trace.get("traceID", ""),
            "root_spans": [],
            "total_spans": len(spans),
            "total_duration_us": max(s.get("duration", 0) for s in spans),
            "span_count_by_operation": {}
        }

        # 统计操作数量
        for span in spans:
            op_name = span.get("operationName", "unknown")
            analysis["span_count_by_operation"][op_name] = \
                analysis["span_count_by_operation"].get(op_name, 0) + 1

        # 分析根span
        for root in root_spans:
            root_analysis = self._analyze_span_branch(root, span_map)
            analysis["root_spans"].append(root_analysis)

        return analysis

    def _analyze_span_branch(
        self,
        span: Dict,
        span_map: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """递归分析span分支"""
        span_id = span["spanID"]
        children = [
            span_map[ref["spanID"]]
            for ref in span.get("references", [])
            if ref.get("refType") == "CHILD_OF" and ref.get("spanID") in span_map
        ]

        result = {
            "operation_name": span.get("operationName", ""),
            "span_id": span_id,
            "duration_us": span.get("duration", 0),
            "self_duration_us": self._calculate_self_duration(span, children),
            "children_count": len(children),
            "children": []
        }

        for child in children:
            result["children"].append(self._analyze_span_branch(child, span_map))

        return result

    def _calculate_self_duration(self, span: Dict, children: List[Dict]) -> int:
        """计算span自身耗时（排除子span）"""
        span_duration = span.get("duration", 0)

        if not children:
            return span_duration

        # 简单计算：总时长 - 最长子链时长
        # 注意：这是近似值，精确计算需要考虑并发
        child_durations = [c.get("duration", 0) for c in children]
        max_child_duration = max(child_durations) if child_durations else 0

        return max(span_duration - max_child_duration, 0)

    async def get_service_metrics(
        self,
        service: str,
        lookback: timedelta = timedelta(minutes=15)
    ) -> Dict[str, SpanMetrics]:
        """获取服务的所有操作指标

        Args:
            service: 服务名称
            lookback: 查询时间范围

        Returns:
            操作名到SpanMetrics的映射
        """
        session = await self._get_session()

        try:
            url = f"{self.jaeger_api_endpoint}/operations"
            params = {"service": service}

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return {}

                operations_data = await response.json()
                operations = operations_data.get("data", [])

        except Exception as e:
            print(f"获取操作列表失败: {e}")
            return {}

        metrics_map = {}

        for operation in operations:
            op_name = operation if isinstance(operation, str) else operation.get("name", "")

            spans = await self.query_spans(service, op_name, lookback)

            if spans:
                metrics = self.analyze_latency(spans)
                metrics_map[op_name] = metrics

        return metrics_map

    def compare_metrics(
        self,
        baseline: SpanMetrics,
        current: SpanMetrics
    ) -> Dict[str, Any]:
        """对比两组指标

        Args:
            baseline: 基线指标
            current: 当前指标

        Returns:
            对比结果
        """
        def calc_percent_change(base: float, curr: float) -> float:
            if base == 0:
                return 0
            return ((curr - base) / base) * 100

        return {
            "avg_duration_change": calc_percent_change(
                baseline.avg_duration_ms, current.avg_duration_ms
            ),
            "p95_duration_change": calc_percent_change(
                baseline.p95_duration_ms, current.p95_duration_ms
            ),
            "p99_duration_change": calc_percent_change(
                baseline.p99_duration_ms, current.p99_duration_ms
            ),
            "error_rate_change": calc_percent_change(
                baseline.error_rate, current.error_rate
            ),
            "throughput_change": calc_percent_change(
                baseline.throughput_qps, current.throughput_qps
            ),
            "count_change": current.count - baseline.count
        }


# 单例模式的全局分析器
_global_analyzer: Optional[PerformanceAnalyzer] = None


def get_performance_analyzer() -> PerformanceAnalyzer:
    """获取全局性能分析器实例"""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = PerformanceAnalyzer()
    return _global_analyzer
