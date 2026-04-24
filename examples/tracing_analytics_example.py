#!/usr/bin/env python3
"""
追踪数据分析示例

演示如何使用PerformanceAnalyzer进行性能分析。

Author: Athena Team
Date: 2026-04-24
"""

import asyncio
from datetime import timedelta
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tracing.analytics import (
    PerformanceAnalyzer,
    SpanMetrics,
    SlowOperation,
    BottleneckInfo
)


async def example_basic_analysis():
    """示例1: 基本性能分析"""
    print("=" * 60)
    print("示例1: 基本性能分析")
    print("=" * 60)

    analyzer = PerformanceAnalyzer()

    # 查询最近15分钟的Spans
    spans = await analyzer.query_spans(
        service="xiaona-agent",
        operation="patent_analysis",
        lookback=timedelta(minutes=15)
    )

    if spans:
        # 分析性能
        metrics = analyzer.analyze_latency(spans)

        print(f"\n操作名称: {metrics.span_name}")
        print(f"请求数量: {metrics.count}")
        print(f"平均延迟: {metrics.avg_duration_ms:.2f}ms")
        print(f"P50延迟: {metrics.p50_duration_ms:.2f}ms")
        print(f"P95延迟: {metrics.p95_duration_ms:.2f}ms")
        print(f"P99延迟: {metrics.p99_duration_ms:.2f}ms")
        print(f"错误率: {metrics.error_rate:.2%}")
        print(f"吞吐量: {metrics.throughput_qps:.2f} QPS")
    else:
        print("未找到追踪数据")

    await analyzer.close()


async def example_slow_operations():
    """示例2: 识别慢操作"""
    print("\n" + "=" * 60)
    print("示例2: 识别慢操作")
    print("=" * 60)

    analyzer = PerformanceAnalyzer()

    # 查询Spans
    spans = await analyzer.query_spans(
        service="xiaona-agent",
        lookback=timedelta(minutes=15)
    )

    # 识别慢操作（阈值200ms）
    slow_ops = analyzer.identify_slow_operations(spans, threshold_ms=200)

    print(f"\n发现 {len(slow_ops)} 个慢操作（>200ms）")

    for i, op in enumerate(slow_ops[:5], 1):
        print(f"\n{i}. {op.operation}")
        print(f"   持续时间: {op.duration_ms:.2f}ms")
        print(f"   Trace ID: {op.trace_id}")

    await analyzer.close()


async def example_bottleneck_detection():
    """示例3: 检测性能瓶颈"""
    print("\n" + "=" * 60)
    print("示例3: 检测性能瓶颈")
    print("=" * 60)

    analyzer = PerformanceAnalyzer()

    # 检测瓶颈
    bottlenecks = await analyzer.detect_bottlenecks(
        service="xiaona-agent",
        lookback=timedelta(minutes=15)
    )

    print(f"\n发现 {len(bottlenecks)} 个潜在瓶颈")

    for i, b in enumerate(bottlenecks[:3], 1):
        print(f"\n{i}. {b.component}::{b.operation}")
        print(f"   影响分数: {b.impact_score:.1f}/100")
        print(f"   平均延迟: {b.avg_duration_ms:.2f}ms")
        print(f"   P95延迟: {b.p95_duration_ms:.2f}ms")
        print(f"   建议: {b.recommendation}")

    await analyzer.close()


async def example_service_metrics():
    """示例4: 获取服务所有操作指标"""
    print("\n" + "=" * 60)
    print("示例4: 服务所有操作指标")
    print("=" * 60)

    analyzer = PerformanceAnalyzer()

    # 获取所有操作指标
    metrics_map = await analyzer.get_service_metrics(
        service="xiaona-agent",
        lookback=timedelta(minutes=15)
    )

    print(f"\n服务共有 {len(metrics_map)} 个操作:\n")

    # 按平均延迟排序
    sorted_ops = sorted(
        metrics_map.items(),
        key=lambda x: x[1].avg_duration_ms,
        reverse=True
    )

    for op_name, metrics in sorted_ops[:5]:
        print(f"{op_name}:")
        print(f"  请求: {metrics.count}, "
              f"平均延迟: {metrics.avg_duration_ms:.2f}ms, "
              f"P95: {metrics.p95_duration_ms:.2f}ms, "
              f"错误率: {metrics.error_rate:.2%}")

    await analyzer.close()


async def example_trace_analysis():
    """示例5: 分析完整Trace"""
    print("\n" + "=" * 60)
    print("示例5: 分析完整Trace")
    print("=" * 60)

    analyzer = PerformanceAnalyzer()

    # 获取完整Traces
    traces = await analyzer.query_traces(
        service="xiaona-agent",
        lookback=timedelta(minutes=15),
        limit=5
    )

    if traces:
        for i, trace in enumerate(traces[:3], 1):
            print(f"\nTrace {i}: {trace.get('traceID', 'unknown')}")
            analysis = analyzer.analyze_trace_tree(trace)

            print(f"  Span总数: {analysis.get('total_spans', 0)}")
            print(f"  总持续时间: {analysis.get('total_duration_us', 0) / 1000:.2f}ms")

            # 显示操作分布
            span_count = analysis.get('span_count_by_operation', {})
            if span_count:
                print(f"  操作分布:")
                for op, count in sorted(span_count.items(), key=lambda x: -x[1])[:5]:
                    print(f"    {op}: {count}")
    else:
        print("未找到Trace数据")

    await analyzer.close()


async def example_metrics_comparison():
    """示例6: 指标对比"""
    print("\n" + "=" * 60)
    print("示例6: 指标对比")
    print("=" * 60)

    analyzer = PerformanceAnalyzer()

    # 模拟两组指标
    from core.tracing.analytics import SpanMetrics

    baseline = SpanMetrics(
        span_name="patent_analysis",
        count=100,
        avg_duration_ms=150.0,
        p95_duration_ms=300.0,
        p99_duration_ms=500.0,
        error_rate=0.01,
        throughput_qps=10.0
    )

    current = SpanMetrics(
        span_name="patent_analysis",
        count=120,
        avg_duration_ms=120.0,
        p95_duration_ms=250.0,
        p99_duration_ms=400.0,
        error_rate=0.005,
        throughput_qps=12.0
    )

    # 对比
    comparison = analyzer.compare_metrics(baseline, current)

    print(f"\n操作: {baseline.span_name}")
    print(f"  平均延迟变化: {comparison['avg_duration_change']:+.1f}%")
    print(f"  P95延迟变化: {comparison['p95_duration_change']:+.1f}%")
    print(f"  P99延迟变化: {comparison['p99_duration_change']:+.1f}%")
    print(f"  错误率变化: {comparison['error_rate_change']:+.1f}%")
    print(f"  吞吐量变化: {comparison['throughput_change']:+.1f}%")

    await analyzer.close()


async def main():
    """运行所有示例"""
    examples = [
        ("基本性能分析", example_basic_analysis),
        ("识别慢操作", example_slow_operations),
        ("检测性能瓶颈", example_bottleneck_detection),
        ("服务所有操作指标", example_service_metrics),
        ("分析完整Trace", example_trace_analysis),
        ("指标对比", example_metrics_comparison),
    ]

    print("\n" + "=" * 60)
    print("追踪数据分析示例")
    print("=" * 60)
    print("\n注意: 这些示例需要Jaeger服务正在运行且有追踪数据")
    print("如果没有数据，示例将显示空结果\n")

    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n❌ {name} 示例执行失败: {e}")

    print("\n" + "=" * 60)
    print("示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
