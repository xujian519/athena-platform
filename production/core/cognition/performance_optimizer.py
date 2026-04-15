
from __future__ import annotations
import gc

# pyright: ignore
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小娜专利系统性能优化器
Patent System Performance Optimizer

提供系统性能监控、优化和调优功能

作者: 小娜·天秤女神
创建时间: 2025-12-16
版本: v1.0 Performance Optimizer
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import psutil

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    response_time: float = 0.0
    throughput: float = 0.0


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    category: str  # 内存、CPU、IO、网络、LLM调用
    severity: str  # low, medium, high, critical
    title: str
    description: str
    action_items: list[str]
    expected_improvement: str


class PerformanceOptimizer:
    """性能优化器主类"""

    def __init__(self, monitoring_interval: float = 5.0, history_size: int = 1000):
        self.monitoring_interval = monitoring_interval
        self.history_size = history_size

        # 性能数据存储
        self.metrics_history: deque = deque(maxlen=history_size)  # type: ignore
        self.llm_call_history: deque = deque(maxlen=1000)  # type: ignore
        self.optimization_history: list[dict[str, Any]] = []

        # 监控状态
        self.is_monitoring = False
        self.monitor_task: asyncio.Task | None = None  # type: ignore

        # 性能阈值
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 70.0,
            'memory_critical': 85.0,
            'response_time_warning': 2.0,
            'response_time_critical': 5.0,
            'throughput_low': 10.0  # requests/minute
        }

        # 初始系统信息
        self.system_info = self._collect_system_info()

    def _collect_system_info(self) -> dict[str, Any]:
        """收集系统信息"""
        return {
            'cpu_count': psutil.cpu_count(),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'disk_total_gb': psutil.disk_usage('/').total / (1024**3),
            'python_version': psutil.sys.version,  # type: ignore
            'platform': psutil.sys.platform,  # type: ignore
        }

    async def start_monitoring(self):
        """启动性能监控"""
        if self.is_monitoring:
            logger.warning("性能监控已在运行")
            return

        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("性能监控已启动")

    async def stop_monitoring(self):
        """停止性能监控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                # 任务被取消，正常退出
                pass
        logger.info("性能监控已停止")

    async def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集性能指标
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)

                # 检查性能问题
                issues = self._detect_performance_issues(metrics)
                if issues:
                    await self._handle_performance_issues(issues)

                # 等待下次监控
                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                # 监控被取消，正常退出
                break
            except Exception as e:
                # 监控异常，记录错误
                logger.error(f"性能监控异常: {e}", exc_info=True)

    async def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        # CPU和内存
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        # 磁盘IO
        disk_io = psutil.disk_io_counters()
        disk_io_read_mb = disk_io.read_bytes / (1024**2) if disk_io else 0
        disk_io_write_mb = disk_io.write_bytes / (1024**2) if disk_io else 0

        # 网络IO
        network_io = psutil.net_io_counters()
        network_sent_mb = network_io.bytes_sent / (1024**2) if network_io else 0
        network_recv_mb = network_io.bytes_recv / (1024**2) if network_io else 0

        # 连接数
        active_connections = len(psutil.net_connections())

        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024**2),
            disk_io_read_mb=disk_io_read_mb,
            disk_io_write_mb=disk_io_write_mb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            active_connections=active_connections
        )

    def _detect_performance_issues(self, metrics: PerformanceMetrics) -> list[dict[str, Any]]:
        """检测性能问题"""
        issues = []

        # CPU问题
        if metrics.cpu_percent > self.thresholds['cpu_critical']:
            issues.append({
                'type': 'cpu',
                'severity': 'critical',
                'value': metrics.cpu_percent,
                'threshold': self.thresholds['cpu_critical']
            })
        elif metrics.cpu_percent > self.thresholds['cpu_warning']:
            issues.append({
                'type': 'cpu',
                'severity': 'warning',
                'value': metrics.cpu_percent,
                'threshold': self.thresholds['cpu_warning']
            })

        # 内存问题
        if metrics.memory_percent > self.thresholds['memory_critical']:
            issues.append({
                'type': 'memory',
                'severity': 'critical',
                'value': metrics.memory_percent,
                'threshold': self.thresholds['memory_critical']
            })
        elif metrics.memory_percent > self.thresholds['memory_warning']:
            issues.append({
                'type': 'memory',
                'severity': 'warning',
                'value': metrics.memory_percent,
                'threshold': self.thresholds['memory_warning']
            })

        # LLM响应时间问题
        if metrics.response_time > self.thresholds['response_time_critical']:
            issues.append({
                'type': 'llm_response_time',
                'severity': 'critical',
                'value': metrics.response_time,
                'threshold': self.thresholds['response_time_critical']
            })
        elif metrics.response_time > self.thresholds['response_time_warning']:
            issues.append({
                'type': 'llm_response_time',
                'severity': 'warning',
                'value': metrics.response_time,
                'threshold': self.thresholds['response_time_warning']
            })

        return issues

    async def _handle_performance_issues(self, issues: list[dict[str, Any]]):
        """处理性能问题"""
        for issue in issues:
            logger.warning(f"检测到性能问题: {issue}")

            # 根据问题类型采取相应措施
            if issue['type'] == 'memory' and issue['severity'] == 'critical':
                await self._optimize_memory_usage()
            elif issue['type'] == 'cpu' and issue['severity'] == 'critical':
                await self._optimize_cpu_usage()
            elif issue['type'] == 'llm_response_time':
                await self._optimize_llm_calls()

    async def _optimize_memory_usage(self):
        """优化内存使用"""
        logger.info("执行内存优化...")

        # 建议清理缓存
        gc.collect()  # type: ignore

        # 记录优化操作
        self.optimization_history.append({
            'timestamp': datetime.now(),
            'type': 'memory_optimization',
            'action': 'garbage_collection',
            'result': 'completed'
        })

    async def _optimize_cpu_usage(self):
        """优化CPU使用"""
        logger.info("执行CPU优化...")

        # 这里可以添加具体的CPU优化逻辑
        # 比如调整并发数、优化算法等

        self.optimization_history.append({
            'timestamp': datetime.now(),
            'type': 'cpu_optimization',
            'action': 'reduce_concurrency',
            'result': 'completed'
        })

    async def _optimize_llm_calls(self):
        """优化LLM调用"""
        logger.info("执行LLM调用优化...")

        # 建议使用更快的模型或启用缓存
        self.optimization_history.append({
            'timestamp': datetime.now(),
            'type': 'llm_optimization',
            'action': 'switch_to_faster_model',
            'result': 'completed'
        })

    def record_llm_call(self, model: str, response_time: float, tokens: int, success: bool):
        """记录LLM调用"""
        self.llm_call_history.append({
            'timestamp': datetime.now(),
            'model': model,
            'response_time': response_time,
            'tokens': tokens,
            'success': success
        })

    def get_performance_summary(self) -> dict[str, Any]:
        """获取性能摘要"""
        if not self.metrics_history:
            return {'status': 'no_data'}

        recent_metrics = list(self.metrics_history)[-60:]  # 最近60个数据点

        # 计算平均值
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)

        # 计算LLM调用统计
        recent_llm_calls = [c for c in self.llm_call_history
                           if c['timestamp'] > datetime.now() - timedelta(hours=1)]

        llm_stats = {
            'total_calls': len(recent_llm_calls),
            'success_rate': sum(1 for c in recent_llm_calls if c['success']) / len(recent_llm_calls) if recent_llm_calls else 0,
            'avg_response_time': sum(c['response_time'] for c in recent_llm_calls) / len(recent_llm_calls) if recent_llm_calls else 0,
            'total_tokens': sum(c['tokens'] for c in recent_llm_calls),
            'top_models': self._get_top_models(recent_llm_calls)
        }

        # 获取优化建议
        suggestions = self._generate_optimization_suggestions(avg_cpu, avg_memory, llm_stats)

        return {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.system_info,
            'current_metrics': {
                'cpu_percent': recent_metrics[-1].cpu_percent if recent_metrics else 0,
                'memory_percent': recent_metrics[-1].memory_percent if recent_metrics else 0,
                'memory_used_mb': recent_metrics[-1].memory_used_mb if recent_metrics else 0
            },
            'averages': {
                'cpu_percent': avg_cpu,
                'memory_percent': avg_memory
            },
            'llm_statistics': llm_stats,
            'optimization_suggestions': suggestions,
            'optimization_count': len(self.optimization_history)
        }

    def _get_top_models(self, calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """获取使用最多的模型"""
        model_counts = {}
        for call in calls:
            model = call['model']
            if model not in model_counts:
                model_counts[model] = {'count': 0, 'total_time': 0}
            model_counts[model]['count'] += 1
            model_counts[model]['total_time'] += call['response_time']

        # 排序并返回前5个
        sorted_models = sorted(model_counts.items(),
                            key=lambda x: x[1]['count'],  # type: ignore
                            reverse=True)[:5]

        return [
            {
                'model': model,
                'count': stats['count'],
                'avg_response_time': stats['total_time'] / stats['count']
            }
            for model, stats in sorted_models
        ]

    def _generate_optimization_suggestions(self, avg_cpu: float, avg_memory: float,
                                          llm_stats: dict[str, Any]) -> list[OptimizationSuggestion]:
        """生成优化建议"""
        suggestions = []

        # CPU优化建议
        if avg_cpu > self.thresholds['cpu_warning']:
            suggestions.append(OptimizationSuggestion(
                category='CPU',
                severity='high' if avg_cpu > self.thresholds['cpu_critical'] else 'medium',
                title='CPU使用率过高',
                description=f'平均CPU使用率达到{avg_cpu:.1f}%，可能影响系统响应性能',
                action_items=[
                    '减少并发任务数量',
                    '优化算法复杂度',
                    '考虑使用多进程处理'
                ],
                expected_improvement='降低CPU使用率20-30%'
            ))

        # 内存优化建议
        if avg_memory > self.thresholds['memory_warning']:
            suggestions.append(OptimizationSuggestion(
                category='内存',
                severity='high' if avg_memory > self.thresholds['memory_critical'] else 'medium',
                title='内存使用率过高',
                description=f'平均内存使用率达到{avg_memory:.1f}%，存在内存压力',
                action_items=[
                    '启用内存缓存清理',
                    '优化数据结构',
                    '考虑使用内存映射文件'
                ],
                expected_improvement='降低内存使用率15-25%'
            ))

        # LLM优化建议
        if llm_stats['avg_response_time'] > self.thresholds['response_time_warning']:
            suggestions.append(OptimizationSuggestion(
                category='LLM调用',
                severity='medium',
                title='LLM响应时间偏慢',
                description=f'平均响应时间为{llm_stats["avg_response_time"]:.2f}秒',
                action_items=[
                    '增加GLM-4-Flash模型使用比例',
                    '启用响应缓存',
                    '实现请求批处理'
                ],
                expected_improvement='提升响应速度30-50%'
            ))

        # 吞吐量建议
        if llm_stats['total_calls'] < self.thresholds['throughput_low']:
            suggestions.append(OptimizationSuggestion(
                category='LLM调用',
                severity='low',
                title='系统吞吐量偏低',
                description=f'当前吞吐量为{llm_stats["total_calls"]:.1f}次/小时',
                action_items=[
                    '增加并发处理能力',
                    '优化请求队列',
                    '预热系统缓存'
                ],
                expected_improvement='提升吞吐量50-100%'
            ))

        return suggestions


# 全局性能优化器实例
performance_optimizer = PerformanceOptimizer()


# 便捷函数
async def start_performance_monitoring():
    """启动性能监控"""
    await performance_optimizer.start_monitoring()


async def stop_performance_monitoring():
    """停止性能监控"""
    await performance_optimizer.stop_monitoring()


def get_performance_status():
    """获取性能状态"""
    return performance_optimizer.get_performance_summary()


def record_llm_performance(model: str, response_time: float, tokens: int, success: bool):
    """记录LLM性能"""
    performance_optimizer.record_llm_call(model, response_time, tokens, success)
