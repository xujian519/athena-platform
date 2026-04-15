#!/usr/bin/env python3
"""
性能监控单元测试
Performance Monitoring Unit Tests
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from core.perception.monitoring import (
    PerformanceMetrics,
    PerformanceMonitor,
    PerformanceTracker,
    get_global_monitor,
    track_performance,
)


@pytest.mark.asyncio
@pytest.mark.unit
class TestPerformanceMonitor:
    """性能监控器测试类"""

    async def test_initialization(self):
        """测试初始化"""
        monitor = PerformanceMonitor(window_size=100, update_interval=0.5, enable_alerts=False)

        assert monitor.window_size == 100
        assert monitor.update_interval == 0.5
        assert not monitor.enable_alerts
        assert not monitor.is_monitoring
        assert len(monitor.latencies) == 0

    async def test_record_request(self):
        """测试记录请求"""
        monitor = PerformanceMonitor(enable_alerts=False)

        # 记录成功请求
        monitor.record_request(latency=0.1, success=True)

        assert monitor.metrics.total_requests == 1
        assert monitor.metrics.successful_requests == 1
        assert monitor.metrics.failed_requests == 0
        assert len(monitor.latencies) == 1

        # 记录失败请求
        monitor.record_request(latency=0.2, success=False)

        assert monitor.metrics.total_requests == 2
        assert monitor.metrics.successful_requests == 1
        assert monitor.metrics.failed_requests == 1

    async def test_latency_tracking(self):
        """测试延迟跟踪"""
        monitor = PerformanceMonitor(enable_alerts=False)

        # 记录多个请求
        latencies = [0.1, 0.2, 0.15, 0.3, 0.05, 0.25, 0.18]
        for latency in latencies:
            monitor.record_request(latency=latency, success=True)

        # 更新指标
        monitor._update_metrics()

        # 验证统计数据
        assert monitor.metrics.average_latency > 0
        assert monitor.metrics.min_latency > 0
        assert monitor.metrics.max_latency > 0
        assert monitor.metrics.min_latency <= monitor.metrics.average_latency
        assert monitor.metrics.average_latency <= monitor.metrics.max_latency

    async def test_percentile_calculation(self):
        """测试百分位数计算"""
        monitor = PerformanceMonitor(enable_alerts=False)

        # 记录100个请求
        import random

        random.seed(42)
        for _ in range(100):
            latency = random.uniform(0.01, 1.0)
            monitor.record_request(latency=latency, success=True)

        monitor._update_metrics()

        # 验证百分位数
        assert monitor.metrics.p50_latency > 0
        assert monitor.metrics.p95_latency > 0
        assert monitor.metrics.p99_latency > 0

        # 验证顺序: p50 <= p95 <= p99
        assert monitor.metrics.p50_latency <= monitor.metrics.p95_latency
        assert monitor.metrics.p95_latency <= monitor.metrics.p99_latency

    async def test_throughput_calculation(self):
        """测试吞吐量计算"""
        monitor = PerformanceMonitor(enable_alerts=False)

        # 记录请求
        for _ in range(10):
            monitor.record_request(latency=0.1, success=True)

        monitor._update_metrics()

        # 验证吞吐量
        assert monitor.metrics.throughput_per_second > 0
        assert monitor.metrics.throughput_per_minute > 0

    async def test_sliding_window(self):
        """测试滑动窗口"""
        window_size = 5
        monitor = PerformanceMonitor(window_size=window_size, enable_alerts=False)

        # 记录超过窗口大小的请求数
        for _i in range(10):
            monitor.record_request(latency=0.1, success=True)

        # 验证窗口大小限制
        assert len(monitor.latencies) == window_size
        assert monitor.metrics.total_requests == 10  # 总计数不受窗口限制

    async def test_get_metrics(self):
        """测试获取指标"""
        monitor = PerformanceMonitor(enable_alerts=False)

        # 记录一些数据
        monitor.record_request(latency=0.1, success=True)
        monitor.record_request(latency=0.2, success=False)
        monitor._update_metrics()

        # 获取指标
        metrics = monitor.get_metrics()

        # 验证指标结构
        assert "total_requests" in metrics
        assert "successful_requests" in metrics
        assert "failed_requests" in metrics
        assert "success_rate" in metrics
        assert "error_rate" in metrics
        assert "latency" in metrics
        assert "throughput" in metrics
        assert "resources" in metrics
        assert "window" in metrics

        # 验证指标值
        assert metrics["total_requests"] == 2
        assert metrics["successful_requests"] == 1
        assert metrics["failed_requests"] == 1
        assert metrics["success_rate"] == 0.5
        assert metrics["error_rate"] == 0.5

    async def test_performance_report(self):
        """测试性能报告"""
        monitor = PerformanceMonitor(enable_alerts=False)

        # 记录一些数据
        for _ in range(5):
            monitor.record_request(latency=0.1, success=True)

        # 获取报告
        report = monitor.get_performance_report()

        # 验证报告结构
        assert "summary" in report
        assert "recommendations" in report

        # 验证摘要
        summary = report["summary"]
        assert "total_time" in summary
        assert "total_requests" in summary
        assert "average_latency_ms" in summary

    async def test_recommendations_generation(self):
        """测试优化建议生成"""
        monitor = PerformanceMonitor(enable_alerts=False)

        # 记录高延迟请求（触发建议）
        for _ in range(10):
            monitor.record_request(latency=4.0, success=True)
        monitor.record_request(latency=0.1, success=True)
        monitor.record_request(latency=0.1, success=False)

        monitor._update_metrics()

        # 获取报告
        report = monitor.get_performance_report()
        recommendations = report["recommendations"]

        # 验证建议
        assert isinstance(recommendations, list)
        # 应该有至少一个建议（由于高延迟或低吞吐量）
        # 注意：具体建议内容取决于实现

    async def test_start_stop_monitoring(self):
        """测试启动和停止监控"""
        monitor = PerformanceMonitor(update_interval=0.1, enable_alerts=False)

        # 启动监控
        await monitor.start_monitoring()
        assert monitor.is_monitoring
        assert monitor._monitor_task is not None

        # 等待一会儿
        await asyncio.sleep(0.2)

        # 停止监控
        await monitor.stop_monitoring()
        assert not monitor.is_monitoring

    async def test_alert_thresholds(self):
        """测试告警阈值"""
        monitor = PerformanceMonitor(enable_alerts=False)

        # 验证默认阈值
        assert "p95_latency" in monitor.alert_thresholds
        assert "error_rate" in monitor.alert_thresholds
        assert "memory_usage" in monitor.alert_thresholds

        # 修改阈值
        monitor.alert_thresholds["p95_latency"] = 10.0
        assert monitor.alert_thresholds["p95_latency"] == 10.0


@pytest.mark.asyncio
@pytest.mark.unit
class TestPerformanceTracker:
    """性能追踪器测试类"""

    async def test_context_manager(self):
        """测试上下文管理器"""
        monitor = PerformanceMonitor(enable_alerts=False)

        with PerformanceTracker(monitor, "test_operation"):
            # 模拟操作
            await asyncio.sleep(0.01)

        # 验证请求被记录
        assert monitor.metrics.total_requests == 1
        assert monitor.metrics.successful_requests == 1

    async def test_exception_handling(self):
        """测试异常处理"""
        monitor = PerformanceMonitor(enable_alerts=False)

        with pytest.raises(ValueError), PerformanceTracker(monitor, "failing_operation"):
            raise ValueError("Test error")

        # 验证失败请求被记录
        assert monitor.metrics.total_requests == 1
        assert monitor.metrics.failed_requests == 1
        assert monitor.metrics.successful_requests == 0


@pytest.mark.asyncio
@pytest.mark.unit
class TestTrackPerformanceDecorator:
    """性能追踪装饰器测试类"""

    async def test_decorator_success(self):
        """测试装饰器 - 成功情况"""
        monitor = PerformanceMonitor(enable_alerts=False)

        @track_performance(monitor, "test_func")
        async def test_function():
            await asyncio.sleep(0.01)
            return "success"

        result = await test_function()

        # 验证结果
        assert result == "success"
        assert monitor.metrics.total_requests == 1
        assert monitor.metrics.successful_requests == 1

    async def test_decorator_failure(self):
        """测试装饰器 - 失败情况"""
        monitor = PerformanceMonitor(enable_alerts=False)

        @track_performance(monitor, "failing_func")
        async def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await failing_function()

        # 验证失败被记录
        assert monitor.metrics.total_requests == 1
        assert monitor.metrics.failed_requests == 1


@pytest.mark.asyncio
@pytest.mark.unit
class TestGlobalMonitor:
    """全局监控器测试类"""

    async def test_get_global_monitor(self):
        """测试获取全局监控器"""
        monitor = get_global_monitor()

        assert isinstance(monitor, PerformanceMonitor)
        assert monitor is not None

    async def test_global_monitor_singleton(self):
        """测试全局监控器单例"""
        monitor1 = get_global_monitor()
        monitor2 = get_global_monitor()

        # 应该是同一个实例
        assert monitor1 is monitor2


@pytest.mark.asyncio
@pytest.mark.unit
class TestPerformanceMetrics:
    """性能指标数据类测试"""

    def test_metrics_initialization(self):
        """测试指标初始化"""
        metrics = PerformanceMetrics()

        # 验证默认值
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.requests_in_progress == 0
        assert metrics.average_latency == 0.0
        assert metrics.p50_latency == 0.0
        assert metrics.cache_hit_rate == 0.0

    def test_metrics_timestamps(self):
        """测试时间戳"""
        before = datetime.now()
        metrics = PerformanceMetrics()
        after = datetime.now()

        # 验证时间戳在合理范围内
        assert before <= metrics.window_start <= after
        assert before <= metrics.last_update <= after


@pytest.mark.asyncio
@pytest.mark.performance
class TestPerformanceMonitorPerformance:
    """性能监控器性能测试"""

    async def test_high_throughput_recording(self):
        """测试高吞吐量记录"""
        monitor = PerformanceMonitor(window_size=10000, enable_alerts=False)

        import time

        start = time.time()

        # 记录1000个请求
        for _ in range(1000):
            monitor.record_request(latency=0.001, success=True)

        elapsed = time.time() - start

        # 应该快速完成
        assert elapsed < 1.0
        assert monitor.metrics.total_requests == 1000

    async def test_concurrent_recording(self):
        """测试并发记录"""
        monitor = PerformanceMonitor(enable_alerts=False)

        async def record_requests():
            for _ in range(100):
                monitor.record_request(latency=0.001, success=True)
                await asyncio.sleep(0)

        # 并发记录
        tasks = [record_requests() for _ in range(10)]
        await asyncio.gather(*tasks)

        # 验证所有请求都被记录
        assert monitor.metrics.total_requests == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
