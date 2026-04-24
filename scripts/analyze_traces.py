#!/usr/bin/env python3
"""
追踪数据分析CLI工具

用于分析Jaeger中的追踪数据，生成性能报告。

Usage:
    # 分析特定服务的性能
    python scripts/analyze_traces.py --service xiaona-agent

    # 分析特定操作
    python scripts/analyze_traces.py --service xiaona-agent --operation patent_analysis

    # 检测瓶颈
    python scripts/analyze_traces.py --service xiaona-agent --detect-bottlenecks

    # 识别慢操作
    python scripts/analyze_traces.py --service xiaona-agent --slow-operations --threshold 200

    # 输出JSON格式
    python scripts/analyze_traces.py --service xiaona-agent --output json

Author: Athena Team
Date: 2026-04-24
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from datetime import timedelta
from typing import Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tracing.analytics import (
    PerformanceAnalyzer,
    SpanMetrics,
    SlowOperation,
    BottleneckInfo
)


def format_duration(ms: float) -> str:
    """格式化持续时间"""
    if ms < 1:
        return f"{ms * 1000:.2f}μs"
    elif ms < 1000:
        return f"{ms:.2f}ms"
    else:
        return f"{ms / 1000:.2f}s"


def format_rate(rate: float) -> str:
    """格式化比率"""
    return f"{rate * 100:.2f}%"


def print_metrics_table(metrics: SpanMetrics):
    """打印指标表格"""
    print("\n" + "=" * 60)
    print(f"性能指标: {metrics.span_name}")
    print("=" * 60)
    print(f"{'指标':<20} {'值':<35}")
    print("-" * 60)

    print(f"{'请求数量':<20} {metrics.count:<35,}")
    print(f"{'平均延迟':<20} {format_duration(metrics.avg_duration_ms):<35}")
    print(f"{'最小延迟':<20} {format_duration(metrics.min_duration_ms):<35}")
    print(f"{'最大延迟':<20} {format_duration(metrics.max_duration_ms):<35}")
    print(f"{'P50延迟':<20} {format_duration(metrics.p50_duration_ms):<35}")
    print(f"{'P95延迟':<20} {format_duration(metrics.p95_duration_ms):<35}")
    print(f"{'P99延迟':<20} {format_duration(metrics.p99_duration_ms):<35}")
    print(f"{'总持续时间':<20} {format_duration(metrics.total_duration_ms):<35}")
    print(f"{'错误数量':<20} {metrics.error_count:<35,}")
    print(f"{'错误率':<20} {format_rate(metrics.error_rate):<35}")
    print(f"{'吞吐量':<20} {metrics.throughput_qps:.2f} QPS")
    print("=" * 60)


def print_slow_operations(slow_ops: list[SlowOperation], limit: int = 10):
    """打印慢操作"""
    if not slow_ops:
        print("\n✅ 未发现慢操作")
        return

    print(f"\n⚠️  发现 {len(slow_ops)} 个慢操作（显示前 {min(limit, len(slow_ops))} 个）:")
    print("-" * 80)

    for i, op in enumerate(slow_ops[:limit], 1):
        print(f"\n{i}. {op.operation}")
        print(f"   持续时间: {format_duration(op.duration_ms)}")
        print(f"   Trace ID: {op.trace_id}")
        print(f"   时间戳: {op.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        if op.attributes:
            print(f"   属性:")
            for key, value in list(op.attributes.items())[:5]:
                print(f"     - {key}: {value}")


def print_bottlenecks(bottlenecks: list[BottleneckInfo], limit: int = 10):
    """打印瓶颈信息"""
    if not bottlenecks:
        print("\n✅ 未发现性能瓶颈")
        return

    print(f"\n🔍 发现 {len(bottlenecks)} 个潜在瓶颈（显示前 {min(limit, len(bottlenecks))} 个）:")
    print("-" * 80)

    for i, bottleneck in enumerate(bottlenecks[:limit], 1):
        impact_emoji = "🔴" if bottleneck.impact_score > 70 else "🟡" if bottleneck.impact_score > 40 else "🟢"
        print(f"\n{impact_emoji} {i}. {bottleneck.component}::{bottleneck.operation}")
        print(f"   影响分数: {bottleneck.impact_score:.1f}/100")
        print(f"   平均延迟: {format_duration(bottleneck.avg_duration_ms)}")
        print(f"   P95延迟: {format_duration(bottleneck.p95_duration_ms)}")
        print(f"   建议: {bottleneck.recommendation}")


def print_service_metrics(metrics_map: dict[str, SpanMetrics]):
    """打印服务所有操作指标"""
    if not metrics_map:
        print("\n未找到任何操作指标")
        return

    print(f"\n📊 服务操作指标汇总（共 {len(metrics_map)} 个操作）:")
    print("=" * 100)
    print(f"{'操作名称':<30} {'请求数':<10} {'平均延迟':<15} {'P95延迟':<15} {'错误率':<10}")
    print("-" * 100)

    # 按平均延迟排序
    sorted_ops = sorted(metrics_map.items(), key=lambda x: x[1].avg_duration_ms, reverse=True)

    for op_name, metrics in sorted_ops:
        print(f"{op_name:<30} {metrics.count:<10,} "
              f"{format_duration(metrics.avg_duration_ms):<15} "
              f"{format_duration(metrics.p95_duration_ms):<15} "
              f"{format_rate(metrics.error_rate):<10}")

    print("=" * 100)


async def analyze_service(
    service: str,
    operation: Optional[str],
    lookback_minutes: int,
    jaeger_endpoint: str
) -> SpanMetrics:
    """分析服务性能"""
    analyzer = PerformanceAnalyzer(jaeger_endpoint=jaeger_endpoint)

    lookback = timedelta(minutes=lookback_minutes)

    spans = await analyzer.query_spans(
        service=service,
        operation=operation,
        lookback=lookback
    )

    if not spans:
        print(f"❌ 未找到服务 '{service}' 的追踪数据")
        print(f"   请确保：")
        print(f"   1. Jaeger服务正在运行 ({jaeger_endpoint})")
        print(f"   2. 服务正在发送追踪数据")
        print(f"   3. 查询时间范围内有请求发生")
        sys.exit(1)

    metrics = analyzer.analyze_latency(spans)
    await analyzer.close()

    return metrics


async def detect_bottlenecks(
    service: str,
    lookback_minutes: int,
    jaeger_endpoint: str
) -> list[BottleneckInfo]:
    """检测性能瓶颈"""
    analyzer = PerformanceAnalyzer(jaeger_endpoint=jaeger_endpoint)

    lookback = timedelta(minutes=lookback_minutes)
    bottlenecks = await analyzer.detect_bottlenecks(service, lookback)

    await analyzer.close()
    return bottlenecks


async def find_slow_operations(
    service: str,
    operation: Optional[str],
    threshold_ms: float,
    lookback_minutes: int,
    jaeger_endpoint: str
) -> list[SlowOperation]:
    """查找慢操作"""
    analyzer = PerformanceAnalyzer(jaeger_endpoint=jaeger_endpoint)

    lookback = timedelta(minutes=lookback_minutes)

    spans = await analyzer.query_spans(
        service=service,
        operation=operation,
        lookback=lookback
    )

    slow_ops = analyzer.identify_slow_operations(spans, threshold_ms)

    await analyzer.close()
    return slow_ops


async def get_all_metrics(
    service: str,
    lookback_minutes: int,
    jaeger_endpoint: str
) -> dict[str, SpanMetrics]:
    """获取服务所有操作指标"""
    analyzer = PerformanceAnalyzer(jaeger_endpoint=jaeger_endpoint)

    lookback = timedelta(minutes=lookback_minutes)
    metrics_map = await analyzer.get_service_metrics(service, lookback)

    await analyzer.close()
    return metrics_map


async def main():
    parser = argparse.ArgumentParser(
        description="分析Jaeger追踪数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析服务性能
  %(prog)s --service xiaona-agent

  # 分析特定操作
  %(prog)s --service xiaona-agent --operation patent_analysis

  # 检测性能瓶颈
  %(prog)s --service xiaona-agent --detect-bottlenecks

  # 查找慢操作
  %(prog)s --service xiaona-agent --slow-operations --threshold 200

  # 输出JSON格式
  %(prog)s --service xiaona-agent --output json

  # 查询最近1小时的数据
  %(prog)s --service xiaona-agent --lookback 60
        """
    )

    parser.add_argument(
        "--service",
        required=True,
        help="服务名称（如 xiaona-agent, gateway）"
    )

    parser.add_argument(
        "--operation",
        help="操作名称（如 patent_analysis, llm_call）"
    )

    parser.add_argument(
        "--slow-operations",
        action="store_true",
        help="识别慢操作"
    )

    parser.add_argument(
        "--slow-threshold",
        type=float,
        default=100,
        metavar="MS",
        help="慢操作阈值（毫秒），默认100"
    )

    parser.add_argument(
        "--detect-bottlenecks",
        action="store_true",
        help="检测性能瓶颈"
    )

    parser.add_argument(
        "--all-metrics",
        action="store_true",
        help="显示所有操作指标"
    )

    parser.add_argument(
        "--lookback",
        type=int,
        default=15,
        metavar="MINUTES",
        help="查询时间范围（分钟），默认15"
    )

    parser.add_argument(
        "--jaeger",
        type=str,
        default="http://localhost:16686",
        metavar="URL",
        help="Jaeger端点地址，默认http://localhost:16686"
    )

    parser.add_argument(
        "--output",
        choices=["console", "json"],
        default="console",
        help="输出格式，默认console"
    )

    parser.add_argument(
        "--output-file",
        type=str,
        metavar="PATH",
        help="输出到文件（仅JSON格式）"
    )

    args = parser.parse_args()

    # 执行分析
    result = {
        "service": args.service,
        "operation": args.operation,
        "lookback_minutes": args.lookback,
        "timestamp": None
    }

    try:
        if args.detect_bottlenecks:
            # 检测瓶颈
            bottlenecks = await detect_bottlenecks(
                args.service, args.lookback, args.jaeger
            )

            if args.output == "json":
                result["bottlenecks"] = [
                    {
                        "component": b.component,
                        "operation": b.operation,
                        "avg_duration_ms": b.avg_duration_ms,
                        "p95_duration_ms": b.p95_duration_ms,
                        "impact_score": b.impact_score,
                        "recommendation": b.recommendation
                    }
                    for b in bottlenecks
                ]
            else:
                print_bottlenecks(bottlenecks)

        elif args.slow_operations:
            # 查找慢操作
            slow_ops = await find_slow_operations(
                args.service, args.operation,
                args.slow_threshold, args.lookback, args.jaeger
            )

            if args.output == "json":
                result["slow_operations"] = [
                    {
                        "operation": op.operation,
                        "span_id": op.span_id,
                        "trace_id": op.trace_id,
                        "duration_ms": op.duration_ms,
                        "timestamp": op.timestamp.isoformat(),
                        "attributes": op.attributes
                    }
                    for op in slow_ops
                ]
            else:
                print_slow_operations(slow_ops)

        elif args.all_metrics:
            # 获取所有指标
            metrics_map = await get_all_metrics(
                args.service, args.lookback, args.jaeger
            )

            if args.output == "json":
                result["metrics"] = {
                    op: metrics.to_dict()
                    for op, metrics in metrics_map.items()
                }
            else:
                print_service_metrics(metrics_map)

        else:
            # 标准分析
            metrics = await analyze_service(
                args.service, args.operation,
                args.lookback, args.jaeger
            )

            if args.output == "json":
                result["metrics"] = metrics.to_dict()
            else:
                print_metrics_table(metrics)

        # 输出结果
        if args.output == "json":
            import datetime
            result["timestamp"] = datetime.datetime.now().isoformat()
            json_output = json.dumps(result, indent=2, ensure_ascii=False)

            if args.output_file:
                with open(args.output_file, "w", encoding="utf-8") as f:
                    f.write(json_output)
                print(f"\n✅ 结果已保存到 {args.output_file}")
            else:
                print(json_output)

    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
