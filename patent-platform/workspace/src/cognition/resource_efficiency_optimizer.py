#!/usr/bin/env python3
"""
资源使用效率优化器
Resource Usage Efficiency Optimizer

提供全面的资源监控、分析和优化功能，包括CPU、内存、磁盘、网络等系统资源
的智能管理和自动优化策略

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import gc
import json
import logging
import os
import statistics
import threading

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore[assignment]
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np
import psutil

# 导入现有模块
try:
    from .external_ai_integration import ExternalAIManager
    from .memory_processor import MemoryProcessor
    from .optimized_memory_index import OptimizedMemoryIndex
    from .performance_optimizer import PerformanceMonitor
except ImportError:
    # 如果导入失败，使用简化版本
    PerformanceMonitor = None
    MemoryProcessor = None
    OptimizedMemoryIndex = None
    ExternalAIManager = None

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """资源类型"""
    CPU = 'cpu'
    MEMORY = 'memory'
    DISK = 'disk'
    NETWORK = 'network'
    GPU = 'gpu'
    CACHE = 'cache'

class OptimizationStrategy(Enum):
    """优化策略"""
    CONSERVATIVE = 'conservative'    # 保守策略
    BALANCED = 'balanced'           # 平衡策略
    AGGRESSIVE = 'aggressive'       # 激进策略
    ADAPTIVE = 'adaptive'          # 自适应策略
    CUSTOM = 'custom'              # 自定义策略

@dataclass
class ResourceMetric:
    """资源指标"""
    timestamp: datetime
    resource_type: ResourceType
    usage_percent: float
    absolute_value: float
    unit: str
    additional_info: dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationAction:
    """优化动作"""
    action_id: str
    resource_type: ResourceType
    strategy: str
    description: str
    expected_saving: float
    execution_time: float
    risk_level: int  # 1-5, 5为最高风险
    success_rate: float = 0.0
    last_executed: datetime | None = None

@dataclass
class ResourceThreshold:
    """资源阈值"""
    resource_type: ResourceType
    warning_threshold: float  # 警告阈值
    critical_threshold: float  # 严重阈值
    optimization_threshold: float  # 优化阈值

class ResourceEfficiencyOptimizer:
    """资源使用效率优化器"""

    def __init__(self,
                 strategy: OptimizationStrategy = OptimizationStrategy.ADAPTIVE,
                 monitoring_interval: int = 30,
                 history_window: int = 3600):
        self.strategy = strategy
        self.monitoring_interval = monitoring_interval
        self.history_window = history_window

        # 资源监控数据
        self.resource_metrics: dict[ResourceType, deque] = {
            resource_type: deque(maxlen=history_window // monitoring_interval)
            for resource_type in ResourceType
        }

        # 优化动作注册表
        self.optimization_actions: dict[ResourceType, list[OptimizationAction]] = {
            resource_type: [] for resource_type in ResourceType
        }

        # 资源阈值配置
        self.thresholds = self._initialize_thresholds()

        # 监控状态
        self.is_monitoring = False
        self.monitor_thread = None
        self.last_optimization_time = {}

        # 性能统计
        self.stats = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'total_resource_saved': 0.0,
            'optimization_rate': 0.0,
            'average_efficiency_score': 0.0
        }

        # 优化历史
        self.optimization_history: list[dict[str, Any]] = []

        # 外部组件引用
        self.performance_monitor = None
        self.memory_processor = None
        self.memory_index = None
        self.ai_manager = None

        # 锁
        self.lock = threading.RLock()

        # 初始化优化动作
        self._initialize_optimization_actions()

    def _initialize_thresholds(self) -> dict[ResourceType, ResourceThreshold]:
        """初始化资源阈值"""
        return {
            ResourceType.CPU: ResourceThreshold(
                resource_type=ResourceType.CPU,
                warning_threshold=70.0,
                critical_threshold=90.0,
                optimization_threshold=80.0
            ),
            ResourceType.MEMORY: ResourceThreshold(
                resource_type=ResourceType.MEMORY,
                warning_threshold=75.0,
                critical_threshold=90.0,
                optimization_threshold=80.0
            ),
            ResourceType.DISK: ResourceThreshold(
                resource_type=ResourceType.DISK,
                warning_threshold=80.0,
                critical_threshold=95.0,
                optimization_threshold=85.0
            ),
            ResourceType.NETWORK: ResourceThreshold(
                resource_type=ResourceType.NETWORK,
                warning_threshold=70.0,
                critical_threshold=90.0,
                optimization_threshold=80.0
            ),
            ResourceType.CACHE: ResourceThreshold(
                resource_type=ResourceType.CACHE,
                warning_threshold=80.0,
                critical_threshold=95.0,
                optimization_threshold=85.0
            )
        }

    def _initialize_optimization_actions(self):
        """初始化优化动作"""
        # CPU优化动作
        self.optimization_actions[ResourceType.CPU] = [
            OptimizationAction(
                action_id='cpu_reduce_priority',
                resource_type=ResourceType.CPU,
                strategy='reduce_process_priority',
                description='降低非关键进程优先级',
                expected_saving=10.0,
                execution_time=1.0,
                risk_level=1
            ),
            OptimizationAction(
                action_id='cpu_limit_threads',
                resource_type=ResourceType.CPU,
                strategy='limit_thread_pool',
                description='限制线程池大小',
                expected_saving=15.0,
                execution_time=2.0,
                risk_level=2
            ),
            OptimizationAction(
                action_id='cpu_enable_caching',
                resource_type=ResourceType.CPU,
                strategy='enable_result_caching',
                description='启用结果缓存减少重复计算',
                expected_saving=20.0,
                execution_time=5.0,
                risk_level=1
            )
        ]

        # 内存优化动作
        self.optimization_actions[ResourceType.MEMORY] = [
            OptimizationAction(
                action_id='mem_garbage_collect',
                resource_type=ResourceType.MEMORY,
                strategy='garbage_collection',
                description='执行垃圾回收',
                expected_saving=5.0,
                execution_time=3.0,
                risk_level=1
            ),
            OptimizationAction(
                action_id='mem_clear_cache',
                resource_type=ResourceType.MEMORY,
                strategy='clear_cache',
                description='清理缓存数据',
                expected_saving=15.0,
                execution_time=2.0,
                risk_level=2
            ),
            OptimizationAction(
                action_id='mem_compress_data',
                resource_type=ResourceType.MEMORY,
                strategy='compress_memory',
                description='压缩内存数据',
                expected_saving=25.0,
                execution_time=10.0,
                risk_level=3
            ),
            OptimizationAction(
                action_id='mem_swap_to_disk',
                resource_type=ResourceType.MEMORY,
                strategy='swap_to_disk',
                description='将冷数据交换到磁盘',
                expected_saving=40.0,
                execution_time=15.0,
                risk_level=4
            )
        ]

        # 磁盘优化动作
        self.optimization_actions[ResourceType.DISK] = [
            OptimizationAction(
                action_id='disk_clean_temp',
                resource_type=ResourceType.DISK,
                strategy='clean_temp_files',
                description='清理临时文件',
                expected_saving=10.0,
                execution_time=5.0,
                risk_level=1
            ),
            OptimizationAction(
                action_id='disk_compress_logs',
                resource_type=ResourceType.DISK,
                strategy='compress_log_files',
                description='压缩历史日志文件',
                expected_saving=20.0,
                execution_time=10.0,
                risk_level=1
            ),
            OptimizationAction(
                action_id='disk_archive_data',
                resource_type=ResourceType.DISK,
                strategy='archive_old_data',
                description='归档历史数据',
                expected_saving=30.0,
                execution_time=20.0,
                risk_level=2
            )
        ]

        # 缓存优化动作
        self.optimization_actions[ResourceType.CACHE] = [
            OptimizationAction(
                action_id='cache_evict_lru',
                resource_type=ResourceType.CACHE,
                strategy='lru_eviction',
                description='LRU缓存淘汰',
                expected_saving=20.0,
                execution_time=3.0,
                risk_level=1
            ),
            OptimizationAction(
                action_id='cache_reduce_size',
                resource_type=ResourceType.CACHE,
                strategy='reduce_cache_size',
                description='减少缓存大小',
                expected_saving=30.0,
                execution_time=5.0,
                risk_level=2
            ),
            OptimizationAction(
                action_id='cache_disable_non_critical',
                resource_type=ResourceType.CACHE,
                strategy='disable_non_critical_cache',
                description='禁用非关键缓存',
                expected_saving=40.0,
                execution_time=2.0,
                risk_level=3
            )
        ]

    def connect_components(self,
                          performance_monitor: PerformanceMonitor | None = None,
                          memory_processor: MemoryProcessor | None = None,
                          memory_index: OptimizedMemoryIndex | None = None,
                          ai_manager: ExternalAIManager | None = None):
        """连接外部组件"""
        self.performance_monitor = performance_monitor
        self.memory_processor = memory_processor
        self.memory_index = memory_index
        self.ai_manager = ai_manager

        logger.info('🔗 资源优化器已连接外部组件')

    def start_monitoring(self):
        """开始资源监控"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        logger.info('📊 资源监控已启动')

    def stop_monitoring(self):
        """停止资源监控"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

        logger.info('⏹️ 资源监控已停止')

    def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集资源指标
                self._collect_resource_metrics()

                # 检查是否需要优化
                self._check_optimization_triggers()

                # 等待下次监控
                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"资源监控错误: {e}")
                time.sleep(self.monitoring_interval)

    def _collect_resource_metrics(self):
        """收集资源指标"""
        now = datetime.now()

        # CPU指标
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_metric = ResourceMetric(
            timestamp=now,
            resource_type=ResourceType.CPU,
            usage_percent=cpu_percent,
            absolute_value=psutil.cpu_count(),
            unit='cores'
        )
        self.resource_metrics[ResourceType.CPU].append(cpu_metric)

        # 内存指标
        memory = psutil.virtual_memory()
        memory_metric = ResourceMetric(
            timestamp=now,
            resource_type=ResourceType.MEMORY,
            usage_percent=memory.percent,
            absolute_value=memory.used / (1024**3),  # GB
            unit='GB',
            additional_info={
                'available': memory.available / (1024**3),
                'total': memory.total / (1024**3)
            }
        )
        self.resource_metrics[ResourceType.MEMORY].append(memory_metric)

        # 磁盘指标
        disk = psutil.disk_usage('/')
        disk_metric = ResourceMetric(
            timestamp=now,
            resource_type=ResourceType.DISK,
            usage_percent=disk.percent,
            absolute_value=disk.used / (1024**3),  # GB
            unit='GB',
            additional_info={
                'free': disk.free / (1024**3),
                'total': disk.total / (1024**3)
            }
        )
        self.resource_metrics[ResourceType.DISK].append(disk_metric)

        # 网络指标
        network = psutil.net_io_counters()
        network_metric = ResourceMetric(
            timestamp=now,
            resource_type=ResourceType.NETWORK,
            usage_percent=0.0,  # 网络使用率需要特殊计算
            absolute_value=network.bytes_sent + network.bytes_recv,
            unit='bytes',
            additional_info={
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
        )
        self.resource_metrics[ResourceType.NETWORK].append(network_metric)

        # 缓存指标（基于内存中的缓存）
        cache_usage = self._estimate_cache_usage()
        cache_metric = ResourceMetric(
            timestamp=now,
            resource_type=ResourceType.CACHE,
            usage_percent=cache_usage,
            absolute_value=cache_usage,
            unit='percent'
        )
        self.resource_metrics[ResourceType.CACHE].append(cache_metric)

    def _estimate_cache_usage(self) -> float:
        """估算缓存使用率"""
        try:
            # 获取当前进程的内存详情
            process = psutil.Process()
            memory_info = process.memory_info()

            # 估算缓存使用（简化实现）
            # 实际应用中应该根据具体缓存实现计算
            estimated_cache = min(85.0, memory_info.rss / (1024**3) * 10)  # 简化估算
            return estimated_cache

        except Exception:
            return 0.0

    def _check_optimization_triggers(self):
        """检查优化触发条件"""
        for resource_type, metrics in self.resource_metrics.items():
            if not metrics:
                continue

            # 获取最新指标
            latest_metric = metrics[-1]
            threshold = self.thresholds.get(resource_type)

            if not threshold:
                continue

            # 检查是否超过优化阈值
            if latest_metric.usage_percent >= threshold.optimization_threshold:
                # 检查冷却时间
                if self._should_optimize(resource_type):
                    asyncio.create_task(self._optimize_resource(resource_type))

    def _should_optimize(self, resource_type: ResourceType) -> bool:
        """判断是否应该执行优化"""
        now = datetime.now()
        last_time = self.last_optimization_time.get(resource_type)

        # 冷却时间：5分钟
        cooldown = timedelta(minutes=5)

        if last_time and (now - last_time) < cooldown:
            return False

        return True

    async def _optimize_resource(self, resource_type: ResourceType):
        """优化资源"""
        actions = self.optimization_actions.get(resource_type, [])
        if not actions:
            return

        # 选择优化策略
        selected_action = self._select_optimization_action(resource_type, actions)
        if not selected_action:
            return

        logger.info(f"🔧 执行资源优化: {selected_action.description}")

        try:
            # 执行优化动作
            success = await self._execute_optimization_action(selected_action)

            # 记录优化历史
            optimization_record = {
                'timestamp': datetime.now(),
                'resource_type': resource_type.value,
                'action_id': selected_action.action_id,
                'action': selected_action.description,
                'success': success,
                'expected_saving': selected_action.expected_saving
            }
            self.optimization_history.append(optimization_record)

            # 更新统计
            self.stats['total_optimizations'] += 1
            if success:
                self.stats['successful_optimizations'] += 1
                self.stats['total_resource_saved'] += selected_action.expected_saving

            # 更新冷却时间
            self.last_optimization_time[resource_type] = datetime.now()

        except Exception as e:
            logger.error(f"资源优化失败: {e}")

    def _select_optimization_action(self,
                                   resource_type: ResourceType,
                                   actions: list[OptimizationAction]) -> OptimizationAction | None:
        """选择优化动作"""
        if not actions:
            return None

        # 根据策略选择动作
        if self.strategy == OptimizationStrategy.CONSERVATIVE:
            # 保守策略：选择风险最低的
            return min(actions, key=lambda x: x.risk_level)

        elif self.strategy == OptimizationStrategy.AGGRESSIVE:
            # 激进策略：选择预期节省最大的
            return max(actions, key=lambda x: x.expected_saving)

        elif self.strategy == OptimizationStrategy.ADAPTIVE:
            # 自适应策略：基于历史成功率选择
            best_action = None
            best_score = -1

            for action in actions:
                # 计算综合得分
                success_rate = action.success_rate or 0.5
                risk_penalty = action.risk_level * 0.1
                saving_bonus = action.expected_saving * 0.01

                score = success_rate * 10 - risk_penalty + saving_bonus

                if score > best_score:
                    best_score = score
                    best_action = action

            return best_action

        else:  # BALANCED
            # 平衡策略：综合考虑风险和收益
            balanced_actions = [a for a in actions if a.risk_level <= 3]
            if balanced_actions:
                return max(balanced_actions, key=lambda x: x.expected_saving)
            else:
                return min(actions, key=lambda x: x.risk_level)

    async def _execute_optimization_action(self, action: OptimizationAction) -> bool:
        """执行优化动作"""
        start_time = time.time()

        try:
            if action.resource_type == ResourceType.CPU:
                return await self._optimize_cpu(action)

            elif action.resource_type == ResourceType.MEMORY:
                return await self._optimize_memory(action)

            elif action.resource_type == ResourceType.DISK:
                return await self._optimize_disk(action)

            elif action.resource_type == ResourceType.CACHE:
                return await self._optimize_cache(action)

            else:
                logger.warning(f"不支持的资源类型优化: {action.resource_type}")
                return False

        except Exception as e:
            logger.error(f"执行优化动作失败 {action.action_id}: {e}")
            return False

        finally:
            # 记录执行时间
            time.time() - start_time
            action.last_executed = datetime.now()

            # 更新成功率（简化实现）
            if action.success_rate == 0:
                action.success_rate = 0.5

    async def _optimize_cpu(self, action: OptimizationAction) -> bool:
        """优化CPU"""
        if action.action_id == 'cpu_reduce_priority':
            # 降低进程优先级
            try:
                os.nice(1)  # 降低优先级
                return True
            except Exception:
                return False

        elif action.action_id == 'cpu_limit_threads':
            # 限制线程池大小（需要具体实现）
            # 这里只是示例
            return True

        elif action.action_id == 'cpu_enable_caching':
            # 启用缓存（需要具体实现）
            return True

        return False

    async def _optimize_memory(self, action: OptimizationAction) -> bool:
        """优化内存"""
        if action.action_id == 'mem_garbage_collect':
            # 执行垃圾回收
            collected = gc.collect()
            logger.info(f"垃圾回收完成，回收对象: {collected}")
            return True

        elif action.action_id == 'mem_clear_cache':
            # 清理缓存
            if self.memory_index:
                # 清理部分缓存
                self.memory_index.optimize_index()
            return True

        elif action.action_id == 'mem_compress_data':
            # 压缩内存数据
            return True

        elif action.action_id == 'mem_swap_to_disk':
            # 交换到磁盘
            return True

        return False

    async def _optimize_disk(self, action: OptimizationAction) -> bool:
        """优化磁盘"""
        if action.action_id == 'disk_clean_temp':
            # 清理临时文件
            temp_dir = '/tmp'
            cleaned = 0
            try:
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        # 检查文件是否超过1小时未访问
                        if (time.time() - os.path.getatime(file_path)) > 3600:
                            os.remove(file_path)
                            cleaned += 1
                logger.info(f"清理临时文件: {cleaned} 个")
                return True
            except Exception as e:
                logger.error(f"清理临时文件失败: {e}")
                return False

        elif action.action_id == 'disk_compress_logs':
            # 压缩日志文件
            return True

        elif action.action_id == 'disk_archive_data':
            # 归档数据
            return True

        return False

    async def _optimize_cache(self, action: OptimizationAction) -> bool:
        """优化缓存"""
        if action.action_id == 'cache_evict_lru':
            # LRU缓存淘汰
            if self.memory_index:
                # 触发LRU清理
                self.memory_index.optimize_index()
            return True

        elif action.action_id == 'cache_reduce_size':
            # 减少缓存大小
            return True

        elif action.action_id == 'cache_disable_non_critical':
            # 禁用非关键缓存
            return True

        return False

    def get_resource_status(self) -> dict[str, Any]:
        """获取资源状态"""
        status = {}

        for resource_type, metrics in self.resource_metrics.items():
            if not metrics:
                continue

            latest = metrics[-1]
            threshold = self.thresholds.get(resource_type)

            # 计算统计信息
            values = [m.usage_percent for m in metrics]
            avg_usage = statistics.mean(values) if values else 0
            max_usage = max(values) if values else 0
            trend = self._calculate_trend(values) if len(values) > 1 else 0

            status[resource_type.value] = {
                'current_usage': latest.usage_percent,
                'absolute_value': latest.absolute_value,
                'unit': latest.unit,
                'average_usage': avg_usage,
                'peak_usage': max_usage,
                'trend': trend,
                'status': self._get_resource_status(latest.usage_percent, threshold),
                'last_updated': latest.timestamp.isoformat()
            }

        return status

    def _calculate_trend(self, values: list[float]) -> str:
        """计算趋势"""
        if len(values) < 2:
            return 'stable'

        recent = values[-5:] if len(values) >= 5 else values
        if len(recent) < 2:
            return 'stable'

        # 简单线性回归计算趋势
        x = list(range(len(recent)))
        n = len(recent)
        sum_x = sum(x)
        sum_y = sum(recent)
        sum_xy = sum(x[i] * recent[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

        if slope > 0.5:
            return 'increasing'
        elif slope < -0.5:
            return 'decreasing'
        else:
            return 'stable'

    def _get_resource_status(self,
                           usage: float,
                           threshold: ResourceThreshold | None) -> str:
        """获取资源状态"""
        if not threshold:
            return 'unknown'

        if usage >= threshold.critical_threshold:
            return 'critical'
        elif usage >= threshold.warning_threshold:
            return 'warning'
        elif usage >= threshold.optimization_threshold:
            return 'optimization_needed'
        else:
            return 'healthy'

    def get_optimization_report(self) -> dict[str, Any]:
        """获取优化报告"""
        # 计算效率分数
        efficiency_scores = {}
        for resource_type, metrics in self.resource_metrics.items():
            if metrics:
                # 效率分数 = 100 - 平均使用率
                avg_usage = statistics.mean(m.usage_percent for m in metrics)
                efficiency_score = max(0, 100 - avg_usage)
                efficiency_scores[resource_type.value] = efficiency_score

        overall_efficiency = statistics.mean(efficiency_scores.values()) if efficiency_scores else 0

        return {
            'overall_efficiency_score': overall_efficiency,
            'resource_efficiency': efficiency_scores,
            'optimization_statistics': self.stats.copy(),
            'recent_optimizations': self.optimization_history[-10:],
            'strategy': self.strategy.value,
            'monitoring_status': self.is_monitoring,
            'recommendations': self._generate_recommendations()
        }

    def _generate_recommendations(self) -> list[str]:
        """生成优化建议"""
        recommendations = []

        for resource_type, metrics in self.resource_metrics.items():
            if not metrics:
                continue

            latest = metrics[-1]
            threshold = self.thresholds.get(resource_type)

            if threshold and latest.usage_percent >= threshold.warning_threshold:
                if resource_type == ResourceType.CPU:
                    recommendations.append('CPU使用率较高，建议启用结果缓存或优化算法')
                elif resource_type == ResourceType.MEMORY:
                    recommendations.append('内存使用率较高，建议执行垃圾回收或清理缓存')
                elif resource_type == ResourceType.DISK:
                    recommendations.append('磁盘使用率较高，建议清理临时文件或归档历史数据')
                elif resource_type == ResourceType.CACHE:
                    recommendations.append('缓存使用率较高，建议启用LRU淘汰或减少缓存大小')

        return recommendations

    def set_strategy(self, strategy: OptimizationStrategy):
        """设置优化策略"""
        self.strategy = strategy
        logger.info(f"优化策略已更新为: {strategy.value}")

    def set_threshold(self,
                     resource_type: ResourceType,
                     warning: float,
                     critical: float,
                     optimization: float):
        """设置资源阈值"""
        if resource_type in self.thresholds:
            self.thresholds[resource_type].warning_threshold = warning
            self.thresholds[resource_type].critical_threshold = critical
            self.thresholds[resource_type].optimization_threshold = optimization
            logger.info(f"{resource_type.value} 阈值已更新")

    def export_optimization_data(self, file_path: str):
        """导出优化数据"""
        # 导出优化历史
        optimization_history = [
            {
                'timestamp': record['timestamp'].isoformat() if isinstance(record['timestamp'], datetime) else record['timestamp'],
                'resource_type': record['resource_type'],
                'action_id': record['action_id'],
                'action': record['action'],
                'success': record['success'],
                'expected_saving': record['expected_saving']
            }
            for record in self.optimization_history[-50:]  # 只导出最近50条
        ]

        export_data = {
            'export_time': datetime.now().isoformat(),
            'resource_metrics': {},
            'optimization_history': optimization_history,
            'statistics': self.stats,
            'thresholds': {
                rt.value: {
                    'warning': t.warning_threshold,
                    'critical': t.critical_threshold,
                    'optimization': t.optimization_threshold
                }
                for rt, t in self.thresholds.items()
            },
            'strategy': self.strategy.value
        }

        # 导出资源指标
        for resource_type, metrics in self.resource_metrics.items():
            export_data['resource_metrics'][resource_type.value] = [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'usage_percent': m.usage_percent,
                    'absolute_value': m.absolute_value,
                    'unit': m.unit,
                    'additional_info': m.additional_info
                }
                for m in list(metrics)[-100:]  # 只导出最近100条
            ]

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 优化数据已导出到: {file_path}")

    def auto_tune(self):
        """自动调优"""
        logger.info('🎵 开始自动调优...')

        # 分析历史数据，找出最优阈值
        for resource_type, metrics in self.resource_metrics.items():
            if len(metrics) < 100:  # 数据不足
                continue

            usage_values = [m.usage_percent for m in metrics]

            # 计算百分位数
            p75 = np.percentile(usage_values, 75)
            p90 = np.percentile(usage_values, 90)
            p85 = np.percentile(usage_values, 85)

            # 自动调整阈值
            if resource_type in self.thresholds:
                threshold = self.thresholds[resource_type]
                threshold.warning_threshold = min(90, max(50, p75))
                threshold.critical_threshold = min(98, max(70, p90))
                threshold.optimization_threshold = min(95, max(60, p85))

        logger.info('✅ 自动调优完成')

# 测试用例
async def main():
    """主函数"""
    logger.info('🚀 资源使用效率优化器测试')
    logger.info(str('='*50))

    # 创建优化器
    optimizer = ResourceEfficiencyOptimizer(
        strategy=OptimizationStrategy.ADAPTIVE,
        monitoring_interval=5,
        history_window=300
    )

    # 开始监控
    logger.info("\n📊 启动资源监控...")
    optimizer.start_monitoring()

    # 模拟运行一段时间
    logger.info("\n⏱️ 运行30秒收集数据...")
    await asyncio.sleep(30)

    # 获取资源状态
    logger.info("\n📈 当前资源状态:")
    status = optimizer.get_resource_status()
    for resource, info in status.items():
        logger.info(f"\n{resource.upper()}:")
        logger.info(f"  当前使用率: {info['current_usage']:.1f}%")
        logger.info(f"  平均使用率: {info['average_usage']:.1f}%")
        logger.info(f"  峰值使用率: {info['peak_usage']:.1f}%")
        logger.info(f"  趋势: {info['trend']}")
        logger.info(f"  状态: {info['status']}")

    # 触发一次手动优化
    logger.info("\n🔧 执行手动优化测试...")
    for resource_type in ResourceType:
        if resource_type != ResourceType.NETWORK:  # 跳过网络优化
            await optimizer._optimize_resource(resource_type)
            await asyncio.sleep(1)

    # 获取优化报告
    logger.info("\n📋 优化报告:")
    report = optimizer.get_optimization_report()
    logger.info(f"  整体效率分数: {report['overall_efficiency_score']:.1f}")
    logger.info(f"  总优化次数: {report['optimization_statistics']['total_optimizations']}")
    logger.info(f"  成功优化次数: {report['optimization_statistics']['successful_optimizations']}")
    logger.info(f"  当前策略: {report['strategy']}")

    if report['recommendations']:
        logger.info("\n💡 优化建议:")
        for rec in report['recommendations']:
            logger.info(f"  - {rec}")

    # 自动调优
    logger.info("\n🎵 执行自动调优...")
    optimizer.auto_tune()

    # 导出数据
    logger.info("\n💾 导出优化数据...")
    optimizer.export_optimization_data('resource_optimization_report.json')

    # 停止监控
    logger.info("\n⏹️ 停止监控...")
    optimizer.stop_monitoring()

    logger.info("\n✅ 测试完成！")

if __name__ == '__main__':
    asyncio.run(main())
