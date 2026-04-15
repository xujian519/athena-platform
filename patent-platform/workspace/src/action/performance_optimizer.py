#!/usr/bin/env python3
"""
专利行动层性能优化器
Patent Action Layer Performance Optimizer

提供任务调度算法优化、执行效率提升、资源管理优化等
性能增强功能。

Created by Athena + 小诺 (AI助手)
Date: 2025-12-05
"""

import asyncio
import hashlib
import json
import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import psutil

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OptimizationType(str, Enum):
    """优化类型"""
    SCHEDULING = 'scheduling'
    RESOURCE_ALLOCATION = 'resource_allocation'
    EXECUTION_ENGINE = 'execution_engine'
    CACHING = 'caching'
    PREDICTION = 'prediction'
    LOAD_BALANCING = 'load_balancing'


@dataclass
class PerformanceMetrics:
    """性能指标"""
    task_count: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    throughput: float = 0.0  # 任务/秒
    success_rate: float = 0.0
    error_rate: float = 0.0
    resource_utilization: dict[str, float] = field(default_factory=dict)
    queue_wait_time: float = 0.0
    cache_hit_rate: float = 0.0
    prediction_accuracy: float = 0.0


@dataclass
class TaskPerformanceData:
    """任务性能数据"""
    task_id: str
    task_type: str
    start_time: datetime
    end_time: datetime | None = None
    execution_time: float = 0.0
    wait_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    success: bool = True
    error_message: str | None = None
    resource_allocation: dict[str, float] = field(default_factory=dict)


class PerformancePredictor:
    """性能预测器"""

    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.task_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=history_size))
        self.model_cache: dict[str, Any] = {}
        self.logger = logging.getLogger(f"{__name__}.PerformancePredictor")

    def record_task_performance(self, task_data: TaskPerformanceData):
        """记录任务性能数据"""
        self.task_history[task_data.task_type].append(task_data)

        # 定期更新预测模型
        if len(self.task_history[task_data.task_type]) % 50 == 0:
            self._update_prediction_model(task_data.task_type)

    def predict_execution_time(self, task_type: str, task_parameters: dict[str, Any]) -> float:
        """预测任务执行时间"""
        if task_type not in self.task_history or len(self.task_history[task_type]) < 10:
            return self._get_default_execution_time(task_type)

        # 使用历史数据的加权平均
        history = list(self.task_history[task_type])
        recent_tasks = history[-20:]  # 最近20个任务

        # 计算加权执行时间（越近的任务权重越大）
        weights = [i / len(recent_tasks) for i in range(1, len(recent_tasks) + 1)]
        weighted_times = [task.execution_time * weight for task, weight in zip(recent_tasks, weights, strict=False)]

        predicted_time = sum(weighted_times) / sum(weights)

        # 根据任务参数调整预测时间
        complexity_factor = self._calculate_complexity_factor(task_parameters)
        predicted_time *= complexity_factor

        return predicted_time

    def predict_resource_usage(self, task_type: str, task_parameters: dict[str, Any]) -> dict[str, float]:
        """预测资源使用"""
        if task_type not in self.task_history or len(self.task_history[task_type]) < 10:
            return self._get_default_resource_usage(task_type)

        history = list(self.task_history[task_type])
        recent_tasks = history[-20:]

        # 计算平均资源使用
        cpu_usage = statistics.mean([task.cpu_usage for task in recent_tasks])
        memory_usage = statistics.mean([task.memory_usage for task in recent_tasks])

        # 根据任务参数调整
        resource_factor = self._calculate_resource_factor(task_parameters)

        return {
            'cpu': min(cpu_usage * resource_factor, 100.0),
            'memory': min(memory_usage * resource_factor, 100.0)
        }

    def _update_prediction_model(self, task_type: str):
        """更新预测模型"""
        history = list(self.task_history[task_type])
        if len(history) < 20:
            return

        # 简单的线性回归模型
        try:
            execution_times = [task.execution_time for task in history]
            wait_times = [task.wait_time for task in history]

            # 计算相关性
            if len(execution_times) > 1 and len(wait_times) > 1:
                correlation = statistics.correlation(execution_times, wait_times) if len(execution_times) > 1 else 0
                self.model_cache[f"{task_type}_correlation"] = correlation

        except Exception as e:
            self.logger.warning(f"更新预测模型失败: {str(e)}")

    def _calculate_complexity_factor(self, parameters: dict[str, Any]) -> float:
        """计算复杂度因子"""
        factor = 1.0

        # 根据分析深度调整
        depth = parameters.get('depth', 'standard')
        if depth == 'comprehensive':
            factor *= 2.0
        elif depth == 'quick':
            factor *= 0.5

        # 根据数据大小调整
        data_size = parameters.get('data_size', 1)
        if data_size > 10:
            factor *= 1.5
        elif data_size > 100:
            factor *= 2.0

        return factor

    def _calculate_resource_factor(self, parameters: dict[str, Any]) -> float:
        """计算资源因子"""
        factor = 1.0

        # 根据并行度调整
        parallel = parameters.get('parallel', False)
        if parallel:
            factor *= 1.5

        # 根据缓存需求调整
        cache_required = parameters.get('cache_required', False)
        if cache_required:
            factor *= 1.2

        return factor

    def _get_default_execution_time(self, task_type: str) -> float:
        """获取默认执行时间"""
        defaults = {
            'patent_analysis': 1800.0,  # 30分钟
            'patent_filing': 7200.0,    # 2小时
            'patent_monitoring': 300.0, # 5分钟
            'patent_validation': 900.0  # 15分钟
        }
        return defaults.get(task_type, 600.0)  # 默认10分钟

    def _get_default_resource_usage(self, task_type: str) -> dict[str, float]:
        """获取默认资源使用"""
        defaults = {
            'patent_analysis': {'cpu': 50.0, 'memory': 40.0},
            'patent_filing': {'cpu': 30.0, 'memory': 30.0},
            'patent_monitoring': {'cpu': 20.0, 'memory': 20.0},
            'patent_validation': {'cpu': 40.0, 'memory': 35.0}
        }
        return defaults.get(task_type, {'cpu': 30.0, 'memory': 30.0})


class IntelligentCache:
    """智能缓存系统"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: dict[str, tuple[Any, datetime, int]] = {}  # key: (value, expiry_time, access_count)
        self.access_order: deque = deque(maxlen=max_size * 2)
        self.hit_count = 0
        self.miss_count = 0
        self.lock = threading.RLock()
        self.logger = logging.getLogger(f"{__name__}.IntelligentCache")

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        with self.lock:
            if key not in self.cache:
                self.miss_count += 1
                return None

            value, expiry_time, access_count = self.cache[key]

            # 检查是否过期
            if datetime.now() > expiry_time:
                del self.cache[key]
                self.miss_count += 1
                return None

            # 更新访问信息
            self.cache[key] = (value, expiry_time, access_count + 1)
            self.access_order.append(key)
            self.hit_count += 1

            return value

    def put(self, key: str, value: Any, ttl: int | None = None) -> None:
        """设置缓存值"""
        with self.lock:
            expiry_time = datetime.now() + timedelta(seconds=ttl or self.default_ttl)

            # 如果缓存已满，删除最少使用的项
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()

            self.cache[key] = (value, expiry_time, 0)
            self.access_order.append(key)

    def _evict_lru(self):
        """删除最少使用的缓存项"""
        if not self.cache:
            return

        # 找到访问次数最少的键
        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k][2])
        del self.cache[lru_key]

    def get_hit_rate(self) -> float:
        """获取缓存命中率"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0

    def clear_expired(self):
        """清理过期缓存"""
        with self.lock:
            now = datetime.now()
            expired_keys = [key for key, (_, expiry_time, _) in self.cache.items() if now > expiry_time]
            for key in expired_keys:
                del self.cache[key]

    def generate_cache_key(self, task_type: str, parameters: dict[str, Any]) -> str:
        """生成缓存键"""
        # 创建参数的哈希值
        params_str = json.dumps(parameters, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]
        return f"{task_type}_{params_hash}"


class LoadBalancer:
    """负载均衡器"""

    def __init__(self):
        self.nodes: dict[str, dict[str, Any]] = {}
        self.node_weights: dict[str, float] = {}
        self.current_assignments: dict[str, set[str]] = defaultdict(set)
        self.logger = logging.getLogger(f"{__name__}.LoadBalancer")

    def register_node(self, node_id: str, capabilities: dict[str, Any], weight: float = 1.0):
        """注册执行节点"""
        self.nodes[node_id] = {
            'capabilities': capabilities,
            'current_load': 0.0,
            'max_capacity': capabilities.get('max_tasks', 10),
            'last_heartbeat': datetime.now(),
            'status': 'active'
        }
        self.node_weights[node_id] = weight
        self.logger.info(f"注册执行节点: {node_id}")

    def select_best_node(self, task_requirements: dict[str, Any]) -> str | None:
        """选择最佳执行节点"""
        available_nodes = [
            node_id for node_id, node_info in self.nodes.items()
            if node_info['status'] == 'active' and
               node_info['current_load'] < node_info['max_capacity']
        ]

        if not available_nodes:
            return None

        # 计算每个节点的适合度分数
        node_scores = []
        for node_id in available_nodes:
            node_info = self.nodes[node_id]
            score = self._calculate_node_score(node_id, node_info, task_requirements)
            node_scores.append((score, node_id))

        # 选择分数最高的节点
        node_scores.sort(reverse=True)
        return node_scores[0][1]

    def assign_task(self, node_id: str, task_id: str):
        """分配任务到节点"""
        if node_id in self.nodes:
            self.nodes[node_id]['current_load'] += 1
            self.current_assignments[node_id].add(task_id)

    def release_task(self, node_id: str, task_id: str):
        """释放节点上的任务"""
        if node_id in self.nodes:
            self.nodes[node_id]['current_load'] = max(0, self.nodes[node_id]['current_load'] - 1)
            self.current_assignments[node_id].discard(task_id)

    def _calculate_node_score(self, node_id: str, node_info: dict[str, Any], task_requirements: dict[str, Any]) -> float:
        """计算节点适合度分数"""
        # 基础分数
        base_score = 100.0

        # 负载惩罚
        load_ratio = node_info['current_load'] / node_info['max_capacity']
        load_penalty = load_ratio * 50  # 负载越高惩罚越大

        # 权重加成
        weight_bonus = self.node_weights.get(node_id, 1.0) * 20

        # 能力匹配度
        capabilities = node_info['capabilities']
        capability_match = 0.0

        if 'required_cpu' in task_requirements:
            available_cpu = capabilities.get('cpu_cores', 1)
            required_cpu = task_requirements['required_cpu']
            if available_cpu >= required_cpu:
                capability_match += 25
            else:
                capability_match -= 25

        if 'required_memory' in task_requirements:
            available_memory = capabilities.get('memory_gb', 1)
            required_memory = task_requirements['required_memory']
            if available_memory >= required_memory:
                capability_match += 25
            else:
                capability_match -= 25

        return base_score - load_penalty + weight_bonus + capability_match


class AdaptiveScheduler:
    """自适应调度器"""

    def __init__(self, performance_predictor: PerformancePredictor):
        self.predictor = performance_predictor
        self.cache = IntelligentCache()
        self.load_balancer = LoadBalancer()
        self.optimization_history: list[dict[str, Any]] = []
        self.logger = logging.getLogger(f"{__name__}.AdaptiveScheduler")

    async def optimize_task_scheduling(self, tasks: list[Any], current_performance: PerformanceMetrics) -> list[Any]:
        """优化任务调度"""
        optimization_start = time.time()

        try:
            # 1. 预测任务性能
            enhanced_tasks = []
            for task in tasks:
                predicted_time = self.predictor.predict_execution_time(task.task_type, task.parameters)
                predicted_resources = self.predictor.predict_resource_usage(task.task_type, task.parameters)

                # 增强任务信息
                task.estimated_duration = timedelta(seconds=predicted_time)
                task.predicted_resources = predicted_resources
                task.optimization_score = self._calculate_optimization_score(task, current_performance)
                enhanced_tasks.append(task)

            # 2. 缓存优化
            cache_optimized_tasks = await self._apply_cache_optimization(enhanced_tasks)

            # 3. 负载均衡优化
            balanced_tasks = await self._apply_load_balancing(cache_optimized_tasks)

            # 4. 动态优先级调整
            priority_adjusted_tasks = await self._apply_dynamic_priorities(balanced_tasks, current_performance)

            # 5. 批处理优化
            batch_optimized_tasks = await self._apply_batch_optimization(priority_adjusted_tasks)

            # 记录优化结果
            optimization_time = time.time() - optimization_start
            self._record_optimization_result(len(tasks), optimization_time, current_performance)

            self.logger.info(f"任务调度优化完成，处理 {len(tasks)} 个任务，耗时 {optimization_time:.3f}秒")

            return batch_optimized_tasks

        except Exception as e:
            self.logger.error(f"任务调度优化失败: {str(e)}")
            return tasks

    def _calculate_optimization_score(self, task, current_performance: PerformanceMetrics) -> float:
        """计算优化分数"""
        score = 0.0

        # 基于当前系统性能调整
        if current_performance.throughput < 10:  # 低吞吐量
            score += 20 if task.priority >= 3 else 5

        if current_performance.success_rate < 0.9:  # 低成功率
            score += 15 if task.parameters.get('reliable', True) else 0

        # 基于任务特征
        if task.parameters.get('cacheable', False):
            score += 10

        if task.parameters.get('parallelizable', False):
            score += 15

        return score

    async def _apply_cache_optimization(self, tasks: list[Any]) -> list[Any]:
        """应用缓存优化"""
        cache_optimized_tasks = []

        for task in tasks:
            # 生成缓存键
            cache_key = self.cache.generate_cache_key(task.task_type, task.parameters)

            # 检查缓存
            cached_result = self.cache.get(cache_key)
            if cached_result:
                # 从缓存中直接获得结果的任务可以跳过或快速处理
                task.cached = True
                task.cached_result = cached_result
                self.logger.debug(f"任务 {task.task_id} 使用缓存结果")
            else:
                task.cached = False
                task.cache_key = cache_key

            cache_optimized_tasks.append(task)

        return cache_optimized_tasks

    async def _apply_load_balancing(self, tasks: list[Any]) -> list[Any]:
        """应用负载均衡"""
        balanced_tasks = []

        for task in tasks:
            if hasattr(task, 'predicted_resources'):
                # 选择最佳执行节点
                best_node = self.load_balancer.select_best_node({
                    'required_cpu': task.predicted_resources.get('cpu', 1),
                    'required_memory': task.predicted_resources.get('memory', 1)
                })

                if best_node:
                    task.assigned_node = best_node
                    self.load_balancer.assign_task(best_node, task.task_id)
                else:
                    task.assigned_node = None
                    self.logger.warning(f"无法为任务 {task.task_id} 分配合适的执行节点")

            balanced_tasks.append(task)

        return balanced_tasks

    async def _apply_dynamic_priorities(self, tasks: list[Any], current_performance: PerformanceMetrics) -> list[Any]:
        """应用动态优先级调整"""
        priority_adjusted_tasks = []

        for task in tasks:

            # 根据系统性能动态调整优先级
            if current_performance.queue_wait_time > 300:  # 队列等待时间过长
                task.priority += 1
                self.logger.debug(f"任务 {task.task_id} 因队列等待时间过长提升优先级")

            if task.deadline:
                time_to_deadline = (task.deadline - datetime.now()).total_seconds()
                if time_to_deadline < 3600:  # 1小时内到期
                    task.priority += 2
                    self.logger.debug(f"任务 {task.task_id} 因临近截止时间提升优先级")

            # 优先级不能超过最大值
            task.priority = min(task.priority, 10)

            priority_adjusted_tasks.append(task)

        return priority_adjusted_tasks

    async def _apply_batch_optimization(self, tasks: list[Any]) -> list[Any]:
        """应用批处理优化"""
        batch_groups = defaultdict(list)

        # 按任务类型和参数相似性分组
        for task in tasks:
            if task.parameters.get('batchable', False):
                # 生成批次键
                batch_key = f"{task.task_type}_{task.parameters.get('batch_group', 'default')}"
                batch_groups[batch_key].append(task)
            else:
                batch_groups['individual'].append(task)

        optimized_tasks = []

        # 处理批次任务
        for batch_key, batch_tasks in batch_groups.items():
            if batch_key != 'individual' and len(batch_tasks) > 1:
                # 合并相似任务
                merged_task = await self._merge_batch_tasks(batch_tasks)
                if merged_task:
                    optimized_tasks.append(merged_task)
            else:
                optimized_tasks.extend(batch_tasks)

        return optimized_tasks

    async def _merge_batch_tasks(self, tasks: list[Any]) -> Any | None:
        """合并批次任务"""
        if len(tasks) < 2:
            return None

        try:
            # 选择第一个任务作为基础
            base_task = tasks[0]

            # 合并任务数据
            merged_data = []
            for task in tasks:
                if hasattr(task, 'patent_data'):
                    merged_data.append(task.patent_data)

            # 创建合并后的任务
            base_task.merged = True
            base_task.batch_size = len(tasks)
            base_task.merged_data = merged_data
            base_task.original_task_ids = [task.task_id for task in tasks]

            # 调整执行时间估算
            base_task.estimated_duration = timedelta(
                seconds=base_task.estimated_duration.total_seconds() * 0.7  # 批处理效率提升30%
            )

            self.logger.debug(f"合并 {len(tasks)} 个任务为批次任务")

            return base_task

        except Exception as e:
            self.logger.error(f"任务合并失败: {str(e)}")
            return None

    def _record_optimization_result(self, task_count: int, optimization_time: float, performance: PerformanceMetrics):
        """记录优化结果"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'task_count': task_count,
            'optimization_time': optimization_time,
            'performance_before': {
                'throughput': performance.throughput,
                'success_rate': performance.success_rate,
                'average_execution_time': performance.average_execution_time
            }
        }

        self.optimization_history.append(result)

        # 保留最近100条记录
        if len(self.optimization_history) > 100:
            self.optimization_history = self.optimization_history[-100:]

    def get_optimization_stats(self) -> dict[str, Any]:
        """获取优化统计信息"""
        if not self.optimization_history:
            return {}

        recent_optimizations = self.optimization_history[-10:]

        return {
            'total_optimizations': len(self.optimization_history),
            'average_optimization_time': statistics.mean(opt['optimization_time'] for opt in recent_optimizations),
            'cache_hit_rate': self.cache.get_hit_rate(),
            'node_count': len(self.load_balancer.nodes),
            'last_optimization': self.optimization_history[-1]['timestamp'] if self.optimization_history else None
        }


class ResourceMonitor:
    """资源监控器"""

    def __init__(self, monitoring_interval: int = 5):
        self.monitoring_interval = monitoring_interval
        self.monitoring_active = False
        self.resource_history: deque = deque(maxlen=1000)
        self.alerts: list[dict[str, Any]] = []
        self.logger = logging.getLogger(f"{__name__}.ResourceMonitor")

    def start_monitoring(self):
        """开始资源监控"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        self.logger.info('资源监控已启动')

    def stop_monitoring(self):
        """停止资源监控"""
        self.monitoring_active = False
        self.logger.info('资源监控已停止')

    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring_active:
            try:
                metrics = self._collect_metrics()
                self.resource_history.append(metrics)
                self._check_alerts(metrics)
            except Exception as e:
                self.logger.error(f"资源监控错误: {str(e)}")

            time.sleep(self.monitoring_interval)

    def _collect_metrics(self) -> dict[str, Any]:
        """收集系统指标"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {},
            'process_count': len(psutil.pids())
        }

    def _check_alerts(self, metrics: dict[str, Any]):
        """检查告警条件"""
        alerts = []

        # CPU告警
        if metrics['cpu_percent'] > 90:
            alerts.append({
                'type': 'cpu_high',
                'value': metrics['cpu_percent'],
                'threshold': 90,
                'timestamp': metrics['timestamp']
            })

        # 内存告警
        if metrics['memory_percent'] > 85:
            alerts.append({
                'type': 'memory_high',
                'value': metrics['memory_percent'],
                'threshold': 85,
                'timestamp': metrics['timestamp']
            })

        # 磁盘告警
        if metrics['disk_percent'] > 95:
            alerts.append({
                'type': 'disk_high',
                'value': metrics['disk_percent'],
                'threshold': 95,
                'timestamp': metrics['timestamp']
            })

        if alerts:
            self.alerts.extend(alerts)
            self.logger.warning(f"触发 {len(alerts)} 个资源告警")

    def get_current_metrics(self) -> dict[str, Any | None]:
        """获取当前指标"""
        return self.resource_history[-1] if self.resource_history else None

    def get_average_metrics(self, duration_minutes: int = 10) -> dict[str, float]:
        """获取平均指标"""
        if not self.resource_history:
            return {}

        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_metrics = [
            m for m in self.resource_history
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]

        if not recent_metrics:
            return {}

        return {
            'cpu_percent': statistics.mean(m['cpu_percent'] for m in recent_metrics),
            'memory_percent': statistics.mean(m['memory_percent'] for m in recent_metrics),
            'disk_percent': statistics.mean(m['disk_percent'] for m in recent_metrics)
        }


# 性能优化器主类
class PatentActionOptimizer:
    """专利行动层性能优化器"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PatentActionOptimizer")

        # 初始化各个优化组件
        self.performance_predictor = PerformancePredictor()
        self.adaptive_scheduler = AdaptiveScheduler(self.performance_predictor)
        self.resource_monitor = ResourceMonitor()

        # 性能指标
        self.current_metrics = PerformanceMetrics()
        self.optimization_enabled = True

        self.logger.info('专利行动层性能优化器初始化完成')

    async def optimize_task_execution(self, tasks: list[Any]) -> list[Any]:
        """优化任务执行"""
        if not self.optimization_enabled:
            return tasks

        self.logger.info(f"开始优化 {len(tasks)} 个任务的执行")

        # 1. 预测和缓存检查
        for task in tasks:
            if hasattr(task, 'parameters'):
                # 预测执行时间
                predicted_time = self.performance_predictor.predict_execution_time(
                    task.task_type if hasattr(task, 'task_type') else 'unknown',
                    task.parameters
                )

                # 设置预测的执行时间
                if hasattr(task, 'estimated_duration'):
                    task.estimated_duration = timedelta(seconds=predicted_time)

        # 2. 自适应调度优化
        optimized_tasks = await self.adaptive_scheduler.optimize_task_scheduling(tasks, self.current_metrics)

        # 3. 更新性能指标
        self._update_performance_metrics()

        return optimized_tasks

    def record_task_completion(self, task_data: TaskPerformanceData):
        """记录任务完成情况"""
        self.performance_predictor.record_task_performance(task_data)

        # 更新当前指标
        self._update_current_metrics(task_data)

    def _update_current_metrics(self, task_data: TaskPerformanceData):
        """更新当前性能指标"""
        self.current_metrics.task_count += 1
        self.current_metrics.total_execution_time += task_data.execution_time
        self.current_metrics.average_execution_time = (
            self.current_metrics.total_execution_time / self.current_metrics.task_count
        )

        if task_data.success:
            self.current_metrics.success_rate = (
                (self.current_metrics.success_rate * (self.current_metrics.task_count - 1) + 1.0) /
                self.current_metrics.task_count
            )
        else:
            self.current_metrics.error_rate = (
                (self.current_metrics.error_rate * (self.current_metrics.task_count - 1) + 1.0) /
                self.current_metrics.task_count
            )

    def _update_performance_metrics(self):
        """更新性能指标"""
        current_resource_metrics = self.resource_monitor.get_current_metrics()
        if current_resource_metrics:
            self.current_metrics.resource_utilization = {
                'cpu': current_resource_metrics.get('cpu_percent', 0) / 100,
                'memory': current_resource_metrics.get('memory_percent', 0) / 100,
                'disk': current_resource_metrics.get('disk_percent', 0) / 100
            }

        # 计算吞吐量（任务/秒）
        if self.current_metrics.task_count > 0:
            self.current_metrics.throughput = (
                self.current_metrics.task_count /
                max(1, (datetime.now() - datetime.now().replace(hour=0, minute=0, second=0)).total_seconds())
            )

        # 更新缓存命中率
        optimization_stats = self.adaptive_scheduler.get_optimization_stats()
        self.current_metrics.cache_hit_rate = optimization_stats.get('cache_hit_rate', 0.0)

    def start_optimization(self):
        """启动优化服务"""
        self.resource_monitor.start_monitoring()
        self.optimization_enabled = True
        self.logger.info('性能优化服务已启动')

    def stop_optimization(self):
        """停止优化服务"""
        self.resource_monitor.stop_monitoring()
        self.optimization_enabled = False
        self.logger.info('性能优化服务已停止')

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        return {
            'current_metrics': {
                'task_count': self.current_metrics.task_count,
                'average_execution_time': self.current_metrics.average_execution_time,
                'throughput': self.current_metrics.throughput,
                'success_rate': self.current_metrics.success_rate,
                'error_rate': self.current_metrics.error_rate,
                'cache_hit_rate': self.current_metrics.cache_hit_rate,
                'resource_utilization': self.current_metrics.resource_utilization
            },
            'optimization_stats': self.adaptive_scheduler.get_optimization_stats(),
            'resource_metrics': self.resource_monitor.get_average_metrics(),
            'alerts': self.resource_monitor.alerts[-10:] if self.resource_monitor.alerts else []
        }

    def enable_optimization(self):
        """启用优化"""
        self.optimization_enabled = True
        self.logger.info('性能优化已启用')

    def disable_optimization(self):
        """禁用优化"""
        self.optimization_enabled = False
        self.logger.info('性能优化已禁用')


# 测试代码
async def test_performance_optimizer():
    """测试性能优化器"""
    optimizer = PatentActionOptimizer()
    optimizer.start_optimization()

    # 创建模拟任务
    class MockTask:
        def __init__(self, task_id, task_type, priority, parameters):
            self.task_id = task_id
            self.task_type = task_type
            self.priority = priority
            self.parameters = parameters
            self.estimated_duration = timedelta(minutes=30)

    tasks = [
        MockTask('task_1', 'patent_analysis', 3, {'depth': 'comprehensive', 'cacheable': True}),
        MockTask('task_2', 'patent_analysis', 2, {'depth': 'quick'}),
        MockTask('task_3', 'patent_filing', 5, {'parallelizable': True, 'batchable': True}),
        MockTask('task_4', 'patent_filing', 4, {'parallelizable': True, 'batchable': True}),
        MockTask('task_5', 'patent_monitoring', 1, {'reliable': True})
    ]

    logger.info(f"原始任务数: {len(tasks)}")

    # 优化任务执行
    optimized_tasks = await optimizer.optimize_task_execution(tasks)

    logger.info(f"优化后任务数: {len(optimized_tasks)}")

    for task in optimized_tasks:
        logger.info(f"任务 {task.task_id}: 类型={task.task_type}, 优先级={task.priority}, 缓存={getattr(task, 'cached', False)}")

    # 模拟任务完成
    task_performance = TaskPerformanceData(
        task_id='task_1',
        task_type='patent_analysis',
        start_time=datetime.now(),
        execution_time=120.5,
        success=True,
        cpu_usage=45.2,
        memory_usage=35.8
    )

    optimizer.record_task_completion(task_performance)

    # 获取性能报告
    report = optimizer.get_performance_report()
    logger.info("\n性能报告:")
    logger.info(f"  任务总数: {report['current_metrics']['task_count']}")
    logger.info(f"  平均执行时间: {report['current_metrics']['average_execution_time']:.2f}秒")
    logger.info(f"  成功率: {report['current_metrics']['success_rate']:.2%}")
    logger.info(f"  缓存命中率: {report['current_metrics']['cache_hit_rate']:.2%}")

    optimizer.stop_optimization()


if __name__ == '__main__':
    asyncio.run(test_performance_optimizer())
