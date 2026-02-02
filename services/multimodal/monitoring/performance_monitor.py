#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控系统
Performance Monitoring System

实时监控系统性能、API调用、文件处理等指标
"""

import time
from core.async_main import async_main
import psutil
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """性能指标数据类"""

    def __init__(self):
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
        self.disk_usage = 0.0
        self.network_io = {'bytes_sent': 0, 'bytes_recv': 0}
        self.active_connections = 0
        self.request_count = 0
        self.error_count = 0
        self.avg_response_time = 0.0
        self.file_processing_count = 0
        self.cache_hit_rate = 0.0

class APICallTracker:
    """API调用跟踪器"""

    def __init__(self, max_records: int = 1000):
        self.max_records = max_records
        self.calls = deque(maxlen=max_records)
        self.endpoints = defaultdict(list)
        self.status_codes = defaultdict(int)
        self.response_times = deque(maxlen=max_records)

    def record_call(self, endpoint: str, method: str,
                   status_code: int, response_time: float,
                   user_id: str | None = None, ip_address: str | None = None):
        """记录API调用"""
        call_data = {
            'timestamp': datetime.now(),
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time': response_time,
            'user_id': user_id,
            'ip_address': ip_address
        }

        self.calls.append(call_data)
        self.endpoints[f"{method} {endpoint}"].append(call_data)
        self.status_codes[status_code] += 1
        self.response_times.append(response_time)

    def get_stats(self, time_window: int = 300) -> Dict[str, Any]:
        """获取API调用统计（最近N秒）"""
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        recent_calls = [call for call in self.calls if call['timestamp'] > cutoff_time]

        if not recent_calls:
            return {
                'total_calls': 0,
                'avg_response_time': 0,
                'error_rate': 0,
                'calls_per_minute': 0,
                'top_endpoints': [],
                'status_distribution': {}
            }

        # 计算统计信息
        total_calls = len(recent_calls)
        response_times = [call['response_time'] for call in recent_calls]
        error_calls = sum(1 for call in recent_calls if call['status_code'] >= 400)

        # 端点统计
        endpoint_counts = defaultdict(int)
        for call in recent_calls:
            endpoint_counts[f"{call['method']} {call['endpoint']}"] += 1

        top_endpoints = sorted(endpoint_counts.items(),
                             key=lambda x: x[1], reverse=True)[:10]

        # 状态码分布
        status_distribution = defaultdict(int)
        for call in recent_calls:
            status_distribution[call['status_code']] += 1

        return {
            'total_calls': total_calls,
            'avg_response_time': sum(response_times) / len(response_times),
            'error_rate': error_calls / total_calls * 100,
            'calls_per_minute': total_calls / (time_window / 60),
            'top_endpoints': top_endpoints,
            'status_distribution': dict(status_distribution)
        }

class FileProcessingTracker:
    """文件处理跟踪器"""

    def __init__(self, max_records: int = 1000):
        self.max_records = max_records
        self.operations = deque(maxlen=max_records)
        self.file_types = defaultdict(list)
        self.operation_types = defaultdict(list)
        self.processing_times = deque(maxlen=max_records)

    def record_operation(self, operation_type: str, file_type: str,
                        file_size: int, processing_time: float,
                        success: bool, user_id: str | None = None):
        """记录文件操作"""
        operation_data = {
            'timestamp': datetime.now(),
            'operation_type': operation_type,  # upload, download, process, analyze
            'file_type': file_type,
            'file_size': file_size,
            'processing_time': processing_time,
            'success': success,
            'user_id': user_id
        }

        self.operations.append(operation_data)
        self.file_types[file_type].append(operation_data)
        self.operation_types[operation_type].append(operation_data)
        self.processing_times.append(processing_time)

    def get_stats(self, time_window: int = 3600) -> Dict[str, Any]:
        """获取文件处理统计"""
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        recent_ops = [op for op in self.operations if op['timestamp'] > cutoff_time]

        if not recent_ops:
            return {
                'total_operations': 0,
                'success_rate': 100,
                'avg_processing_time': 0,
                'total_bytes_processed': 0,
                'file_type_distribution': {},
                'operation_type_distribution': {},
                'processing_speed': 0
            }

        total_ops = len(recent_ops)
        successful_ops = sum(1 for op in recent_ops if op['success'])
        processing_times = [op['processing_time'] for op in recent_ops]
        total_bytes = sum(op['file_size'] for op in recent_ops)

        # 文件类型分布
        file_type_counts = defaultdict(int)
        for op in recent_ops:
            file_type_counts[op['file_type']] += 1

        # 操作类型分布
        operation_type_counts = defaultdict(int)
        for op in recent_ops:
            operation_type_counts[op['operation_type']] += 1

        return {
            'total_operations': total_ops,
            'success_rate': successful_ops / total_ops * 100,
            'avg_processing_time': sum(processing_times) / len(processing_times),
            'total_bytes_processed': total_bytes,
            'file_type_distribution': dict(file_type_counts),
            'operation_type_distribution': dict(operation_type_counts),
            'processing_speed': total_bytes / sum(processing_times) if sum(processing_times) > 0 else 0
        }

class SystemResourceMonitor:
    """系统资源监控器"""

    def __init__(self, update_interval: int = 5):
        self.update_interval = update_interval
        self.metrics_history = deque(maxlen=1000)
        self.alerts = deque(maxlen=100)
        self.thresholds = {
            'cpu_warning': 80,
            'cpu_critical': 95,
            'memory_warning': 80,
            'memory_critical': 95,
            'disk_warning': 85,
            'disk_critical': 95
        }
        self.running = False
        self.monitor_thread = None

    def start(self) -> None:
        """启动监控"""
        if self.running:
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("系统资源监控已启动")

    def stop(self) -> None:
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("系统资源监控已停止")

    def _monitor_loop(self) -> Any:
        """监控循环"""
        while self.running:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                self._check_alerts(metrics)
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                time.sleep(self.update_interval)

    def _collect_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent

        # 网络IO
        network = psutil.net_io_counters()

        # 进程信息
        process_count = len(psutil.pids())

        # 系统负载（仅Unix系统）
        try:
            load_avg = psutil.getloadavg()
        except (KeyError, TypeError, IndexError, ValueError):
            load_avg = [0, 0, 0]

        return {
            'timestamp': datetime.now(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_used': memory.used,
            'memory_available': memory.available,
            'disk_percent': disk_percent,
            'disk_used': disk.used,
            'disk_free': disk.free,
            'network_bytes_sent': network.bytes_sent,
            'network_bytes_recv': network.bytes_recv,
            'process_count': process_count,
            'load_avg': load_avg
        }

    def _check_alerts(self, metrics: Dict[str, Any]) -> Any:
        """检查告警条件"""
        alerts = []

        # CPU告警
        if metrics['cpu_percent'] >= self.thresholds['cpu_critical']:
            alerts.append({
                'level': 'critical',
                'type': 'cpu',
                'message': f"CPU使用率过高: {metrics['cpu_percent']:.1f}%",
                'timestamp': datetime.now()
            })
        elif metrics['cpu_percent'] >= self.thresholds['cpu_warning']:
            alerts.append({
                'level': 'warning',
                'type': 'cpu',
                'message': f"CPU使用率警告: {metrics['cpu_percent']:.1f}%",
                'timestamp': datetime.now()
            })

        # 内存告警
        if metrics['memory_percent'] >= self.thresholds['memory_critical']:
            alerts.append({
                'level': 'critical',
                'type': 'memory',
                'message': f"内存使用率过高: {metrics['memory_percent']:.1f}%",
                'timestamp': datetime.now()
            })
        elif metrics['memory_percent'] >= self.thresholds['memory_warning']:
            alerts.append({
                'level': 'warning',
                'type': 'memory',
                'message': f"内存使用率警告: {metrics['memory_percent']:.1f}%",
                'timestamp': datetime.now()
            })

        # 磁盘告警
        if metrics['disk_percent'] >= self.thresholds['disk_critical']:
            alerts.append({
                'level': 'critical',
                'type': 'disk',
                'message': f"磁盘使用率过高: {metrics['disk_percent']:.1f}%",
                'timestamp': datetime.now()
            })
        elif metrics['disk_percent'] >= self.thresholds['disk_warning']:
            alerts.append({
                'level': 'warning',
                'type': 'disk',
                'message': f"磁盘使用率警告: {metrics['disk_percent']:.1f}%",
                'timestamp': datetime.now()
            })

        # 添加告警记录
        for alert in alerts:
            self.alerts.append(alert)
            logger.warning(f"性能告警: {alert['message']}")

    def get_current_metrics(self) -> Dict[str, Any | None]:
        """获取当前指标"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None

    def get_metrics_history(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """获取历史指标"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [m for m in self.metrics_history if m['timestamp'] > cutoff_time]

    def get_alerts(self, level: str | None = None,
                   hours: int = 24) -> List[Dict[str, Any]]:
        """获取告警记录"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        alerts = [a for a in self.alerts if a['timestamp'] > cutoff_time]

        if level:
            alerts = [a for a in alerts if a['level'] == level]

        return alerts

class PerformanceMonitor:
    """性能监控主控制器"""

    def __init__(self):
        self.api_tracker = APICallTracker()
        self.file_tracker = FileProcessingTracker()
        self.system_monitor = SystemResourceMonitor()
        self.custom_metrics = defaultdict(deque)
        self.metrics_file = Path("/tmp/performance_metrics.json")
        self.reporting_interval = 300  # 5分钟
        self.reporting_task = None

    async def start(self):
        """启动性能监控"""
        # 启动系统资源监控
        self.system_monitor.start()

        # 启动定期报告任务
        self.reporting_task = asyncio.create_task(self._reporting_loop())

        logger.info("性能监控系统已启动")

    async def stop(self):
        """停止性能监控"""
        if self.reporting_task:
            self.reporting_task.cancel()

        self.system_monitor.stop()
        logger.info("性能监控系统已停止")

    async def _reporting_loop(self):
        """定期报告循环"""
        while True:
            try:
                await self._generate_report()
                await asyncio.sleep(self.reporting_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"性能报告生成失败: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再试

    def record_api_call(self, endpoint: str, method: str,
                       status_code: int, response_time: float,
                       user_id: str | None = None, ip_address: str | None = None):
        """记录API调用"""
        self.api_tracker.record_call(
            endpoint, method, status_code, response_time,
            user_id, ip_address
        )

    def record_file_operation(self, operation_type: str, file_type: str,
                            file_size: int, processing_time: float,
                            success: bool, user_id: str | None = None):
        """记录文件操作"""
        self.file_tracker.record_operation(
            operation_type, file_type, file_size,
            processing_time, success, user_id
        )

    def add_custom_metric(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """添加自定义指标"""
        metric_data = {
            'timestamp': datetime.now(),
            'value': value,
            'tags': tags or {}
        }
        self.custom_metrics[name].append(metric_data)

    async def _generate_report(self):
        """生成性能报告"""
        try:
            # 收集各项指标
            system_metrics = self.system_monitor.get_current_metrics()
            api_stats = self.api_tracker.get_stats()
            file_stats = self.file_tracker.get_stats()

            # 生成综合报告
            report = {
                'timestamp': datetime.now().isoformat(),
                'system': system_metrics,
                'api': api_stats,
                'file_processing': file_stats,
                'custom_metrics': {
                    name: list(data)[-10:]  # 最近10个数据点
                    for name, data in self.custom_metrics.items()
                },
                'alerts': self.system_monitor.get_alerts(hours=1)
            }

            # 保存到文件
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)

            logger.debug(f"性能报告已生成: {len(str(report))} bytes")

        except Exception as e:
            logger.error(f"生成性能报告失败: {e}")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        return {
            'system': {
                'current': self.system_monitor.get_current_metrics(),
                'alerts': self.system_monitor.get_alerts(hours=24),
                'history': self.system_monitor.get_metrics_history(minutes=60)
            },
            'api': {
                'stats': self.api_tracker.get_stats(),
                'recent_calls': list(self.api_tracker.calls)[-20:],
                'top_endpoints': self.api_tracker.get_stats()['top_endpoints']
            },
            'files': {
                'stats': self.file_tracker.get_stats(),
                'recent_operations': list(self.file_tracker.operations)[-20:]
            },
            'summary': {
                'total_api_calls': len(self.api_tracker.calls),
                'total_file_operations': len(self.file_tracker.operations),
                'active_alerts': len(self.system_monitor.get_alerts(hours=1)),
                'uptime': time.time() - (self.system_monitor.metrics_history[0]['timestamp'].timestamp()
                                       if self.system_monitor.metrics_history else time.time())
            }
        }

# 全局性能监控实例
performance_monitor = PerformanceMonitor()

# 装饰器：自动记录API调用性能
def monitor_performance(endpoint: str = None, method: str = None) -> Any:
    """性能监控装饰器"""
    def decorator(func) -> None:
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            user_id = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                logger.error(f"API调用异常 {endpoint}: {e}")
                raise
            finally:
                response_time = time.time() - start_time

                # 记录API调用
                performance_monitor.record_api_call(
                    endpoint=endpoint or func.__name__,
                    method=method or 'GET',
                    status_code=status_code,
                    response_time=response_time,
                    user_id=user_id
                )

        return wrapper
    return decorator

# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_monitor():
        """测试性能监控"""
        monitor = PerformanceMonitor()
        await monitor.start()

        # 模拟API调用
        monitor.record_api_call("/api/upload", "POST", 200, 0.5)
        monitor.record_api_call("/api/search", "GET", 200, 0.2)

        # 模拟文件操作
        monitor.record_file_operation("upload", "jpg", 1024*1024, 1.5, True)

        # 获取仪表板数据
        dashboard = monitor.get_dashboard_data()
        print(json.dumps(dashboard, ensure_ascii=False, indent=2, default=str))

        await asyncio.sleep(10)
        await monitor.stop()

    asyncio.run(test_monitor())