"""
性能分析器测试

测试PerformanceAnalyzer的各项功能。

Author: Athena Team
Date: 2026-04-24
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from core.tracing.analytics import (
    PerformanceAnalyzer,
    SpanMetrics,
    SlowOperation,
    BottleneckInfo
)


# 模拟Jaeger API响应数据
MOCK_SPANS_RESPONSE = {
    "data": [
        {
            "traceID": "trace1",
            "spans": [
                {
                    "traceID": "trace1",
                    "spanID": "span1",
                    "operationName": "test_operation",
                    "duration": 50000,  # 50ms
                    "startTime": int(datetime.now().timestamp() * 1_000_000) - 100000,
                    "tags": [{"key": "success", "value": True}],
                    "process": {"serviceName": "test-service"}
                },
                {
                    "traceID": "trace1",
                    "spanID": "span2",
                    "operationName": "test_operation",
                    "duration": 100000,  # 100ms
                    "startTime": int(datetime.now().timestamp() * 1_000_000) - 50000,
                    "tags": [{"key": "error", "value": True}],
                    "process": {"serviceName": "test-service"}
                }
            ]
        }
    ]
}

MOCK_OPERATIONS_RESPONSE = {
    "data": ["operation1", "operation2", "slow_operation"]
}

MOCK_EMPTY_RESPONSE = {"data": []}


@pytest.fixture
def mock_span_data():
    """创建模拟的span数据"""
    return [
        {
            "traceID": "trace1",
            "spanID": "span1",
            "operationName": "fast_op",
            "duration": 10000,  # 10ms
            "startTime": int(datetime.now().timestamp() * 1_000_000),
            "tags": [],
            "process": {"serviceName": "test"}
        },
        {
            "traceID": "trace2",
            "spanID": "span2",
            "operationName": "fast_op",
            "duration": 20000,  # 20ms
            "startTime": int(datetime.now().timestamp() * 1_000_000),
            "tags": [],
            "process": {"serviceName": "test"}
        },
        {
            "traceID": "trace3",
            "spanID": "span3",
            "operationName": "fast_op",
            "duration": 30000,  # 30ms
            "startTime": int(datetime.now().timestamp() * 1_000_000),
            "tags": [],
            "process": {"serviceName": "test"}
        },
        {
            "traceID": "trace4",
            "spanID": "span4",
            "operationName": "slow_op",
            "duration": 150000,  # 150ms
            "startTime": int(datetime.now().timestamp() * 1_000_000),
            "tags": [{"key": "error", "value": True}],
            "process": {"serviceName": "test"}
        }
    ]


@pytest.fixture
def mock_trace_data():
    """创建模拟的trace数据"""
    return {
        "traceID": "trace1",
        "spans": [
            {
                "traceID": "trace1",
                "spanID": "root1",
                "operationName": "root_operation",
                "duration": 200000,  # 200ms
                "startTime": int(datetime.now().timestamp() * 1_000_000),
                "tags": [],
                "process": {"serviceName": "test"},
                "references": []
            },
            {
                "traceID": "trace1",
                "spanID": "child1",
                "operationName": "child_operation",
                "duration": 100000,  # 100ms
                "startTime": int(datetime.now().timestamp() * 1_000_000) + 20000,
                "tags": [],
                "process": {"serviceName": "test"},
                "references": [{"refType": "CHILD_OF", "spanID": "root1"}]
            }
        ]
    }


class TestPerformanceAnalyzer:
    """测试PerformanceAnalyzer类"""

    def test_init(self):
        """测试初始化"""
        analyzer = PerformanceAnalyzer()
        assert analyzer.jaeger_endpoint == "http://localhost:16686"
        assert analyzer.timeout == 30

    def test_init_with_custom_endpoint(self):
        """测试自定义端点初始化"""
        analyzer = PerformanceAnalyzer(
            jaeger_endpoint="http://custom:16686",
            timeout=60
        )
        assert analyzer.jaeger_endpoint == "http://custom:16686"
        assert analyzer.timeout == 60


class TestSpanMetrics:
    """测试SpanMetrics数据类"""

    def test_span_metrics_creation(self):
        """测试SpanMetrics创建"""
        metrics = SpanMetrics(
            span_name="test_op",
            operation="test_operation",
            count=100,
            avg_duration_ms=50.0,
            p95_duration_ms=100.0,
            p99_duration_ms=150.0,
            error_count=5,
            error_rate=0.05
        )

        assert metrics.span_name == "test_op"
        assert metrics.count == 100
        assert metrics.avg_duration_ms == 50.0
        assert metrics.error_rate == 0.05

    def test_to_dict(self):
        """测试转换为字典"""
        metrics = SpanMetrics(
            span_name="test_op",
            count=100,
            avg_duration_ms=50.123
        )

        result = metrics.to_dict()

        assert isinstance(result, dict)
        assert result["span_name"] == "test_op"
        assert result["count"] == 100
        assert result["avg_duration_ms"] == 50.12  # 四舍五入


class TestAnalyzeLatency:
    """测试延迟分析功能"""

    def test_analyze_latency_empty_spans(self):
        """测试空span列表"""
        analyzer = PerformanceAnalyzer()
        metrics = analyzer.analyze_latency([])

        assert metrics.span_name == ""
        assert metrics.count == 0

    def test_analyze_latency_basic(self, mock_span_data):
        """测试基本延迟分析"""
        analyzer = PerformanceAnalyzer()
        metrics = analyzer.analyze_latency(mock_span_data)

        assert metrics.count == 4
        assert metrics.avg_duration_ms == pytest.approx(52.5, rel=0.1)  # (10+20+30+150)/4
        assert metrics.min_duration_ms == 10.0
        assert metrics.max_duration_ms == 150.0
        assert metrics.error_count == 1
        assert metrics.error_rate == 0.25

    def test_analyze_latency_percentiles(self, mock_span_data):
        """测试分位数计算"""
        analyzer = PerformanceAnalyzer()
        metrics = analyzer.analyze_latency(mock_span_data)

        # 验证分位数合理
        assert metrics.p50_duration_ms >= metrics.min_duration_ms
        assert metrics.p95_duration_ms >= metrics.p50_duration_ms
        assert metrics.p99_duration_ms >= metrics.p95_duration_ms


class TestIdentifySlowOperations:
    """测试慢操作识别功能"""

    def test_identify_slow_operations_basic(self, mock_span_data):
        """测试基本慢操作识别"""
        analyzer = PerformanceAnalyzer()
        slow_ops = analyzer.identify_slow_operations(mock_span_data, threshold_ms=100)

        # 只有一个操作超过100ms
        assert len(slow_ops) == 1
        assert slow_ops[0].operation == "slow_op"
        assert slow_ops[0].duration_ms == 150.0

    def test_identify_slow_operations_empty(self):
        """测试空列表"""
        analyzer = PerformanceAnalyzer()
        slow_ops = analyzer.identify_slow_operations([], threshold_ms=100)

        assert len(slow_ops) == 0

    def test_identify_slow_operations_sorting(self, mock_span_data):
        """测试排序"""
        analyzer = PerformanceAnalyzer()
        slow_ops = analyzer.identify_slow_operations(mock_span_data, threshold_ms=5)

        # 应该按持续时间降序排序
        durations = [op.duration_ms for op in slow_ops]
        assert durations == sorted(durations, reverse=True)


class TestTraceAnalysis:
    """测试Trace分析功能"""

    def test_analyze_trace_tree_empty(self):
        """测试空trace"""
        analyzer = PerformanceAnalyzer()
        result = analyzer.analyze_trace_tree({})

        assert result == {}

    def test_analyze_trace_tree_basic(self, mock_trace_data):
        """测试基本trace分析"""
        analyzer = PerformanceAnalyzer()
        result = analyzer.analyze_trace_tree(mock_trace_data)

        assert result["trace_id"] == "trace1"
        assert result["total_spans"] == 2
        assert result["total_duration_us"] > 0
        assert len(result["root_spans"]) == 1

    def test_analyze_trace_tree_span_count(self, mock_trace_data):
        """测试span计数"""
        analyzer = PerformanceAnalyzer()
        result = analyzer.analyze_trace_tree(mock_trace_data)

        span_count = result.get("span_count_by_operation", {})
        assert span_count.get("root_operation") == 1
        assert span_count.get("child_operation") == 1


class TestCalculateSelfDuration:
    """测试自身耗时计算"""

    def test_calculate_self_duration_no_children(self):
        """测试无子span的情况"""
        analyzer = PerformanceAnalyzer()
        span = {"duration": 100000}

        self_duration = analyzer._calculate_self_duration(span, [])

        assert self_duration == 100000

    def test_calculate_self_duration_with_children(self):
        """测试有子span的情况"""
        analyzer = PerformanceAnalyzer()
        span = {"duration": 200000}  # 200ms
        child = {"duration": 100000}  # 100ms

        self_duration = analyzer._calculate_self_duration(span, [child])

        # 自身时间应该是200ms - 100ms = 100ms
        assert self_duration == 100000


class TestGenerateRecommendation:
    """测试建议生成"""

    def test_recommendation_high_latency(self):
        """测试高延迟建议"""
        analyzer = PerformanceAnalyzer()

        metrics = SpanMetrics(
            span_name="test",
            avg_duration_ms=1500,
            p95_duration_ms=2000,
            error_rate=0
        )

        recommendation = analyzer._generate_recommendation(metrics)

        assert "超时" in recommendation or "数据库" in recommendation

    def test_recommendation_high_error_rate(self):
        """测试高错误率建议"""
        analyzer = PerformanceAnalyzer()

        metrics = SpanMetrics(
            span_name="test",
            avg_duration_ms=100,
            p95_duration_ms=200,
            error_rate=0.1
        )

        recommendation = analyzer._generate_recommendation(metrics)

        assert "错误率" in recommendation

    def test_recommendation_good_performance(self):
        """测试良好性能建议"""
        analyzer = PerformanceAnalyzer()

        metrics = SpanMetrics(
            span_name="test",
            avg_duration_ms=50,
            p95_duration_ms=100,
            error_rate=0
        )

        recommendation = analyzer._generate_recommendation(metrics)

        assert "良好" in recommendation or "监控" in recommendation


class TestCompareMetrics:
    """测试指标对比"""

    def test_compare_metrics_basic(self):
        """测试基本对比"""
        analyzer = PerformanceAnalyzer()

        baseline = SpanMetrics(
            span_name="test",
            count=100,
            avg_duration_ms=100,
            p95_duration_ms=200,
            p99_duration_ms=300,
            error_rate=0.01,
            throughput_qps=10
        )

        current = SpanMetrics(
            span_name="test",
            count=120,
            avg_duration_ms=80,  # 改善20%
            p95_duration_ms=160,
            p99_duration_ms=240,
            error_rate=0.005,
            throughput_qps=12
        )

        comparison = analyzer.compare_metrics(baseline, current)

        assert comparison["avg_duration_change"] == pytest.approx(-20.0, rel=0.1)
        assert comparison["p95_duration_change"] == pytest.approx(-20.0, rel=0.1)
        assert comparison["error_rate_change"] == pytest.approx(-50.0, rel=0.1)
        assert comparison["throughput_change"] == pytest.approx(20.0, rel=0.1)
        assert comparison["count_change"] == 20


@pytest.mark.asyncio
class TestAsyncOperations:
    """测试异步操作"""

    async def test_query_spans_with_mock(self):
        """测试查询spans（带mock）"""
        analyzer = PerformanceAnalyzer()

        with patch.object(analyzer, "_get_session") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=MOCK_SPANS_RESPONSE)

            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            spans = await analyzer.query_spans("test-service")

            # 验证返回了spans
            assert isinstance(spans, list)

    async def test_close_session(self):
        """测试关闭会话"""
        analyzer = PerformanceAnalyzer()

        # 创建会话
        session = await analyzer._get_session()
        assert session is not None

        # 关闭会话
        await analyzer.close()

        # 验证会话已关闭
        assert analyzer._session.closed


class TestEdgeCases:
    """测试边缘情况"""

    def test_empty_spans_analyze_latency(self):
        """测试空span列表的延迟分析"""
        analyzer = PerformanceAnalyzer()
        metrics = analyzer.analyze_latency([])

        assert metrics.count == 0
        assert metrics.avg_duration_ms == 0

    def test_single_span_analyze_latency(self):
        """测试单个span的延迟分析"""
        analyzer = PerformanceAnalyzer()
        single_span = [
            {
                "duration": 100000,
                "operationName": "single_op",
                "tags": []
            }
        ]

        metrics = analyzer.analyze_latency(single_span)

        assert metrics.count == 1
        assert metrics.avg_duration_ms == 100.0
        assert metrics.p50_duration_ms == 100.0

    def test_zero_threshold_slow_operations(self):
        """测试零阈值"""
        analyzer = PerformanceAnalyzer()
        spans = [
            {"duration": 1000, "operationName": "op1", "spanID": "s1", "traceID": "t1"},
            {"duration": 2000, "operationName": "op2", "spanID": "s2", "traceID": "t2"}
        ]

        # 零阈值应该返回所有操作
        slow_ops = analyzer.identify_slow_operations(spans, threshold_ms=0)
        assert len(slow_ops) == 2


@pytest.mark.integration
class TestIntegration:
    """集成测试（需要实际Jaeger服务）"""

    @pytest.mark.skip(reason="需要实际Jaeger服务")
    async def test_real_jaeger_query(self):
        """测试真实Jaeger查询"""
        analyzer = PerformanceAnalyzer()

        spans = await analyzer.query_spans(
            service="xiaona-agent",
            lookback=timedelta(minutes=5)
        )

        assert isinstance(spans, list)
        await analyzer.close()

    @pytest.mark.skip(reason="需要实际Jaeger服务")
    async def test_real_bottleneck_detection(self):
        """测试真实瓶颈检测"""
        analyzer = PerformanceAnalyzer()

        bottlenecks = await analyzer.detect_bottlenecks(
            service="xiaona-agent",
            lookback=timedelta(minutes=5)
        )

        assert isinstance(bottlenecks, list)
        await analyzer.close()
