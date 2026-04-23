#!/usr/bin/env python3
"""
性能调优工具
Performance Optimization Tools

提供系统性能监控、分析和自动调优功能

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import gc
import logging
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import psutil

logger = logging.getLogger(__name__)

class OptimizationType(Enum):
    """优化类型"""
    MEMORY = 'memory'                # 内存优化
    CPU = 'cpu'                    # CPU优化
    IO = 'io'                      # IO优化
    CACHE = 'cache'                # 缓存优化
    CONCURRENCY = 'concurrency'      # 并发优化
    ALGORITHM = 'algorithm'          # 算法优化

class PerformanceLevel(Enum):
    """性能级别"""
    POOR = 0.3                     # 较差
    FAIR = 0.6                     # 一般
    GOOD = 0.8                     # 良好
    EXCELLENT = 0.95                 # 优秀

@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    unit: str
    threshold: float
    current_level: PerformanceLevel
    timestamp: datetime = field(default_factory=datetime.now)
    history: deque = field(default_factory=lambda: deque(maxlen=100))

@dataclass
class OptimizationRecommendation:
    """优化建议"""
    recommendation_id: str
    optimization_type: OptimizationType
    title: str
    description: str
    priority: str  # high, medium, low
    expected_improvement: float
    implementation_effort: str  # easy, medium, hard
    auto_applicable: bool
    applied: bool = False
    timestamp: datetime = field(default_factory=datetime.now)

class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics: dict[str, PerformanceMetric] = {}
        self.monitoring = False
        self.monitor_thread: threading.Thread | None = None
        self.monitor_interval = 5.0  # 监控间隔（秒）

        # 监控回调
        self.callbacks: list[Callable] = []

        # 历史数据
        self.performance_history = defaultdict(list)

    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            logger.warning('性能监控已在运行')
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info('🔍 性能监控已启动')

    def stop_monitoring(self):
        """停止监控"""
        if not self.monitoring:
            return

        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info('⏹️ 性能监控已停止')

    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # 收集系统指标
                metrics = self._collect_system_metrics()
                self._update_metrics(metrics)

                # 触发回调
                for callback in self.callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        logger.error(f"性能监控回调失败: {e}")

                time.sleep(self.monitor_interval)

            except Exception as e:
                logger.error(f"性能监控错误: {e}")
                time.sleep(1)

    def _collect_system_metrics(self) -> dict[str, float]:
        """收集系统指标"""
        metrics = {}

        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics['cpu_usage'] = cpu_percent

        # 内存使用
        memory = psutil.virtual_memory()
        metrics['memory_usage'] = memory.percent
        metrics['memory_available_gb'] = memory.available / (1024**3)

        # 磁盘使用
        disk = psutil.disk_usage('/')
        metrics['disk_usage'] = disk.percent
        metrics['disk_free_gb'] = disk.free / (1024**3)

        # 网络IO
        net_io = psutil.net_io_counters()
        metrics['network_bytes_sent'] = net_io.bytes_sent
        metrics['network_bytes_recv'] = net_io.bytes_recv

        # 进程信息
        process = psutil.Process()
        metrics['process_memory_mb'] = process.memory_info().rss / (1024**2)
        metrics['process_cpu_percent'] = process.cpu_percent()

        return metrics

    def _update_metrics(self, new_metrics: dict[str, float]):
        """更新指标"""
        for name, value in new_metrics.items():
            if name not in self.metrics:
                # 确定阈值和单位
                if 'cpu' in name.lower() or 'memory' in name.lower():
                    threshold = 80
                    unit = '%'
                elif 'bytes' in name.lower():
                    threshold = 1024 * 1024 * 100  # 100MB
                    unit = 'bytes'
                else:
                    threshold = 100
                    unit = 'count'

                self.metrics[name] = PerformanceMetric(
                    name=name,
                    value=value,
                    unit=unit,
                    threshold=threshold,
                    current_level=PerformanceLevel.GOOD
                )

            # 更新现有指标
            metric = self.metrics[name]
            metric.value = value
            metric.timestamp = datetime.now()
            metric.history.append(value)

            # 计算性能级别
            metric.current_level = self._calculate_performance_level(metric)

            # 保存历史
            self.performance_history[name].append({
                'value': value,
                'timestamp': metric.timestamp.isoformat()
            })

    def _calculate_performance_level(self, metric: PerformanceMetric) -> PerformanceLevel:
        """计算性能级别"""
        ratio = metric.value / metric.threshold

        if ratio <= 0.5:
            return PerformanceLevel.EXCELLENT
        elif ratio <= 0.7:
            return PerformanceLevel.GOOD
        elif ratio <= 0.9:
            return PerformanceLevel.FAIR
        else:
            return PerformanceLevel.POOR

    def add_callback(self, callback: Callable):
        """添加监控回调"""
        self.callbacks.append(callback)

    def get_metrics(self) -> dict[str, PerformanceMetric]:
        """获取当前指标"""
        return self.metrics.copy()

    def get_metric_history(self, metric_name: str, hours: int = 24) -> list[dict]:
        """获取指标历史"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        history = self.performance_history.get(metric_name, [])
        return [h for h in history if datetime.fromisoformat(h['timestamp']) >= cutoff_time]

class MemoryOptimizer:
    """内存优化器"""

    def __init__(self):
        self.optimization_history = []
        self.optimization_stats = {
            'gc_runs': 0,
            'memory_freed_mb': 0,
            'cache_cleared': 0
        }

    async def optimize_memory(self, force_gc: bool = False) -> dict[str, Any]:
        """优化内存"""
        start_time = time.time()
        initial_memory = psutil.virtual_memory().used

        results = {
            'initial_memory_mb': initial_memory / (1024**2),
            'optimizations_applied': []
        }

        # 1. 强制垃圾回收
        if force_gc:
            gc.collect()
            results['optimizations_applied'].append('forced_garbage_collection')
            self.optimization_stats['gc_runs'] += 1

        # 2. 清理缓存（如果有的话）
        cache_cleared = self._clear_caches()
        if cache_cleared > 0:
            results['optimizations_applied'].append(f'cache_cleared_{cache_cleared}')
            self.optimization_stats['cache_cleared'] += cache_cleared

        # 3. 优化对象池
        pool_optimized = self._optimize_object_pools()
        if pool_optimized:
            results['optimizations_applied'].append('object_pool_optimized')

        # 4. 内存碎片整理
        if hasattr(gc, 'collect'):
            gc.collect()
            results['optimizations_applied'].append('memory_compaction')

        final_memory = psutil.virtual_memory().used
        memory_freed = (initial_memory - final_memory) / (1024**2)

        results.update({
            'final_memory_mb': final_memory / (1024**2),
            'memory_freed_mb': memory_freed,
            'optimization_time_seconds': time.time() - start_time,
            'success': memory_freed > 0
        })

        if memory_freed > 0:
            self.optimization_stats['memory_freed_mb'] += memory_freed
            logger.info(f"🧹 内存优化完成，释放 {memory_freed:.2f} MB")

        # 记录优化历史
        self.optimization_history.append({
            'timestamp': datetime.now().isoformat(),
            'memory_freed_mb': memory_freed,
            'optimizations': results['optimizations_applied']
        })

        return results

    def _clear_caches(self) -> int:
        """清理缓存"""
        cleared = 0

        # 清理模块缓存
        for module_name in list(sys.modules.keys()):
            if module_name.startswith('cache'):
                del sys.modules[module_name]
                cleared += 1

        # 清理装饰器缓存
        for obj in gc.get_objects():
            if hasattr(obj, '__wrapped__'):
                if hasattr(obj, 'cache'):
                    obj.cache.clear()
                    cleared += 1

        return cleared

    def _optimize_object_pools(self) -> bool:
        """优化对象池"""
        try:
            # 简化的对象池优化
            # 实际应用中可以维护专门的对象池
            return True
        except:
            return False

class CacheOptimizer:
    """缓存优化器"""

    def __init__(self):
        self.cache_policies = {
            'lru': self._lru_policy,
            'lfu': self._lfu_policy,
            'random': self._random_policy
        }
        self.current_policy = 'lru'
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }

    def set_policy(self, policy: str):
        """设置缓存策略"""
        if policy in self.cache_policies:
            self.current_policy = policy
            logger.info(f"缓存策略已设置为: {policy}")
        else:
            logger.error(f"未知的缓存策略: {policy}")

    def get_hit_rate(self) -> float:
        """获取缓存命中率"""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        return self.cache_stats['hits'] / total if total > 0 else 0

    def optimize_cache_size(self, current_size: int, max_size: int) -> dict[str, Any]:
        """优化缓存大小"""
        hit_rate = self.get_hit_rate()

        recommendations = []
        optimal_size = current_size

        # 基于命中率调整缓存大小
        if hit_rate < 0.6:
            # 命中率低，可能缓存太小
            optimal_size = min(current_size * 2, max_size)
            recommendations.append(f"命中率低({hit_rate:.1%})，建议增加缓存大小到 {optimal_size}")
        elif hit_rate > 0.9:
            # 命中率高，可能缓存过大
            optimal_size = max(current_size * 0.8, 100)
            recommendations.append(f"命中率高({hit_rate:.1%})，可以减少缓存大小到 {optimal_size}")

        return {
            'current_size': current_size,
            'optimal_size': optimal_size,
            'hit_rate': hit_rate,
            'recommendations': recommendations
        }

    def _lru_policy(self, cache: dict, key: Any):
        """LRU缓存策略"""
        # 简化的LRU实现
        pass

    def _lfu_policy(self, cache: dict, key: Any):
        """LFU缓存策略"""
        # 简化的LFU实现
        pass

    def _random_policy(self, cache: dict, key: Any):
        """随机缓存策略"""
        # 简化的随机策略实现
        pass

class ConcurrencyOptimizer:
    """并发优化器"""

    def __init__(self):
        self.thread_pool_size = None
        self.async_concurrency_limit = None
        self.resource_limits = {}

    def analyze_concurrency(self) -> dict[str, Any]:
        """分析并发配置"""
        cpu_count = psutil.cpu_count()
        current_threads = threading.active_count()

        recommendations = []

        # 线程池大小建议
        if self.thread_pool_size is None:
            # 建议线程池大小 = CPU核心数 * 2
            optimal_pool_size = cpu_count * 2
            recommendations.append(f"建议设置线程池大小为 {optimal_pool_size} (当前CPU核心数: {cpu_count})")
        else:
            optimal_pool_size = self.thread_pool_size

        # 异步并发限制建议
        if self.async_concurrency_limit is None:
            # 建议并发限制 = CPU核心数 * 5
            optimal_concurrency = cpu_count * 5
            recommendations.append(f"建议设置异步并发限制为 {optimal_concurrency}")
        else:
            optimal_concurrency = self.async_concurrency_limit

        return {
            'cpu_count': cpu_count,
            'current_threads': current_threads,
            'optimal_pool_size': optimal_pool_size,
            'optimal_concurrency': optimal_concurrency,
            'recommendations': recommendations
        }

    def optimize_thread_pool(self, pool_size: int | None = None) -> dict[str, Any]:
        """优化线程池"""
        cpu_count = psutil.cpu_count()

        if pool_size is None:
            pool_size = cpu_count * 2

        return {
            'recommended_size': pool_size,
            'cpu_count': cpu_count,
            'ratio': pool_size / cpu_count
        }

class AutoTuner:
    """自动调优器"""

    def __init__(self):
        self.memory_optimizer = MemoryOptimizer()
        self.cache_optimizer = CacheOptimizer()
        self.concurrency_optimizer = ConcurrencyOptimizer()
        self.auto_tuning_enabled = False
        self.tuning_interval = 300  # 5分钟
        self.tuning_thread: threading.Thread | None = None

        # 调优历史
        self.tuning_history = []

    def start_auto_tuning(self):
        """启动自动调优"""
        if self.auto_tuning_enabled:
            logger.warning('自动调优已在运行')
            return

        self.auto_tuning_enabled = True
        self.tuning_thread = threading.Thread(target=self._tuning_loop, daemon=True)
        self.tuning_thread.start()
        logger.info('🔧 自动调优已启动')

    def stop_auto_tuning(self):
        """停止自动调优"""
        if not self.auto_tuning_enabled:
            return

        self.auto_tuning_enabled = False
        if self.tuning_thread:
            self.tuning_thread.join(timeout=5)
        logger.info('⏹️ 自动调优已停止')

    def _tuning_loop(self):
        """调优循环"""
        while self.auto_tuning_enabled:
            try:
                # 执行自动调优
                await self._perform_auto_tuning()

                time.sleep(self.tuning_interval)

            except Exception as e:
                logger.error(f"自动调优错误: {e}")
                time.sleep(10)

    async def _perform_auto_tuning(self):
        """执行自动调优"""
        tuning_results = {
            'timestamp': datetime.now().isoformat(),
            'optimizations': []
        }

        # 1. 内存优化
        memory_stats = psutil.virtual_memory()
        if memory_stats.percent > 80:
            logger.info('内存使用率高，执行内存优化')
            memory_result = await self.memory_optimizer.optimize_memory(force_gc=True)
            tuning_results['optimizations'].append({
                'type': 'memory',
                'result': memory_result
            })

        # 2. 缓存优化
        hit_rate = self.cache_optimizer.get_hit_rate()
        if hit_rate < 0.6:
            logger.info(f"缓存命中率低({hit_rate:.1%})，优化缓存策略")
            # 切换缓存策略
            policies = list(self.cache_optimizer.cache_policies.keys())
            current_index = policies.index(self.cache_optimizer.current_policy)
            new_policy = policies[(current_index + 1) % len(policies)]
            self.cache_optimizer.set_policy(new_policy)
            tuning_results['optimizations'].append({
                'type': 'cache_policy',
                'old_policy': self.cache_optimizer.current_policy,
                'new_policy': new_policy
            })

        # 3. 并发优化
        concurrency_analysis = self.concurrency_optimizer.analyze_concurrency()
        if concurrency_analysis['recommendations']:
            logger.info('应用并发优化建议')
            tuning_results['optimizations'].append({
                'type': 'concurrency',
                'recommendations': concurrency_analysis['recommendations']
            })

        # 记录调优历史
        self.tuning_history.append(tuning_results)

        logger.info(f"自动调优完成，应用了 {len(tuning_results['optimizations'])} 个优化")

class PerformanceOptimizer:
    """性能优化器主类"""

    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.memory_optimizer = MemoryOptimizer()
        self.cache_optimizer = CacheOptimizer()
        self.concurrency_optimizer = ConcurrencyOptimizer()
        self.auto_tuner = AutoTuner()

        # 优化建议
        self.recommendations: list[OptimizationRecommendation] = []

        # 优化统计
        self.optimization_stats = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'performance_improvements': {}
        }

    def start(self):
        """启动性能优化器"""
        self.monitor.start_monitoring()
        self.auto_tuner.start_auto_tuning()

        # 添加性能监控回调
        self.monitor.add_callback(self._performance_callback)

        logger.info('🚀 性能优化器已启动')

    def stop(self):
        """停止性能优化器"""
        self.monitor.stop_monitoring()
        self.auto_tuner.stop_auto_tuning()
        logger.info('🛑 性能优化器已停止')

    def _performance_callback(self, metrics: dict[str, float]):
        """性能监控回调"""
        # 检查是否需要优化
        for name, value in metrics.items():
            if 'cpu_usage' in name.lower() and value > 90:
                self._add_recommendation(
                    OptimizationType.CPU,
                    'CPU使用率过高',
                    f"当前CPU使用率为{value:.1f}%，超过90%阈值",
                    'high',
                    20.0,
                    'medium',
                    False
                )

            if 'memory_usage' in name.lower() and value > 85:
                self._add_recommendation(
                    OptimizationType.MEMORY,
                    '内存使用率过高',
                    f"当前内存使用率为{value:.1f}%，建议执行内存优化",
                    'high',
                    30.0,
                    'easy',
                    True
                )

    def _add_recommendation(self,
                          opt_type: OptimizationType,
                          title: str,
                          description: str,
                          priority: str,
                          expected_improvement: float,
                          effort: str,
                          auto_applicable: bool):
        """添加优化建议"""
        rec_id = f"rec_{len(self.recommendations)}"

        recommendation = OptimizationRecommendation(
            recommendation_id=rec_id,
            optimization_type=opt_type,
            title=title,
            description=description,
            priority=priority,
            expected_improvement=expected_improvement,
            implementation_effort=effort,
            auto_applicable=auto_applicable
        )

        self.recommendations.append(recommendation)

    async def apply_recommendation(self, recommendation_id: str) -> dict[str, Any]:
        """应用优化建议"""
        rec = None
        for r in self.recommendations:
            if r.recommendation_id == recommendation_id:
                rec = r
                break

        if not rec:
            return {'success': False, 'error': 'Recommendation not found'}

        if rec.applied:
            return {'success': False, 'error': 'Recommendation already applied'}

        result = {'success': False}

        try:
            if rec.optimization_type == OptimizationType.MEMORY:
                result = await self.memory_optimizer.optimize_memory(force_gc=True)
            elif rec.optimization_type == OptimizationType.CACHE:
                cache_result = self.cache_optimizer.optimize_cache_size(1000, 2000)
                result = {'success': True, 'details': cache_result}
            elif rec.optimization_type == OptimizationType.CONCURRENCY:
                concurrency_result = self.concurrency_optimizer.optimize_thread_pool()
                result = {'success': True, 'details': concurrency_result}
            else:
                result = {'success': True, 'message': f"已记录{rec.optimization_type.value}类型优化建议"}

            if result.get('success', False):
                rec.applied = True
                self.optimization_stats['successful_optimizations'] += 1
                logger.info(f"✅ 应用优化建议: {rec.title}")
            else:
                logger.error(f"❌ 应用优化建议失败: {rec.title}")

        except Exception as e:
            logger.error(f"应用优化建议异常: {e}")
            result['success'] = False
            result['error'] = str(e)

        result['recommendation_id'] = recommendation_id
        return result

    async def auto_optimize(self) -> dict[str, Any]:
        """自动优化"""
        auto_applicable = [r for r in self.recommendations if r.auto_applicable and not r.applied]

        results = {
            'applied': 0,
            'failed': 0,
            'details': []
        }

        for rec in auto_applicable[:3]:  # 限制同时应用的优化数量
            try:
                result = await self.apply_recommendation(rec.recommendation_id)
                if result.get('success', False):
                    results['applied'] += 1
                    results['details'].append({
                        'id': rec.recommendation_id,
                        'title': rec.title,
                        'result': result
                    })
                else:
                    results['failed'] += 1
            except Exception as e:
                logger.error(f"自动优化失败: {e}")
                results['failed'] += 1

        return results

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        metrics = self.monitor.get_metrics()

        report = {
            'current_metrics': {
                name: {
                    'value': metric.value,
                    'unit': metric.unit,
                    'threshold': metric.threshold,
                    'level': metric.current_level.value
                } for name, metric in metrics.items()
            },
            'recommendations': {
                'total': len(self.recommendations),
                'pending': len([r for r in self.recommendations if not r.applied]),
                'applied': len([r for r in self.recommendations if r.applied]),
                'by_type': {},
                'by_priority': {'high': 0, 'medium': 0, 'low': 0}
            },
            'optimization_stats': self.optimization_stats.copy(),
            'auto_tuner': {
                'enabled': self.auto_tuner.auto_tuning_enabled,
                'tuning_count': len(self.auto_tuner.tuning_history)
            }
        }

        # 统计建议按类型
        for rec in self.recommendations:
            opt_type = rec.optimization_type.value
            if opt_type not in report['recommendations']['by_type']:
                report['recommendations']['by_type'][opt_type] = 0
            report['recommendations']['by_type'][opt_type] += 1

        # 统计建议按优先级
        for rec in self.recommendations:
            report['recommendations']['by_priority'][rec.priority] += 1

        return report

# 测试用例
async def main():
    """主函数"""
    logger.info('🚀 性能优化工具测试')
    logger.info(str('='*50))

    # 创建优化器
    optimizer = PerformanceOptimizer()

    # 启动优化器
    optimizer.start()

    # 等待监控数据收集
    logger.info("\n📊 收集性能数据...")
    await asyncio.sleep(2)

    # 模拟高负载情况
    logger.info("\n⚡ 模拟高负载...")

    # 触发一些优化建议
    optimizer._performance_callback({
        'cpu_usage': 95.0,
        'memory_usage': 88.0
    })

    # 获取性能报告
    logger.info("\n📋 性能报告:")
    report = optimizer.get_performance_report()
    logger.info(f"  当前指标数量: {len(report['current_metrics'])}")
    logger.info(f"  优化建议总数: {report['recommendations']['total']}")
    logger.info(f"  待处理建议: {report['recommendations']['pending']}")
    logger.info(f"  已应用建议: {report['recommendations']['applied']}")

    # 执行自动优化
    logger.info("\n🔧 执行自动优化...")
    auto_results = await optimizer.auto_optimize()
    logger.info(f"  应用优化: {auto_results['applied']} 个")
    logger.info(f"  失败优化: {auto_results['failed']} 个")

    # 获取优化统计
    logger.info("\n📈 优化统计:")
    stats = optimizer.optimization_stats
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

    # 停止优化器
    logger.info("\n⏹️ 停止性能优化器...")
    optimizer.stop()

    logger.info("\n✅ 性能优化工具测试完成！")

if __name__ == '__main__':
    import sys
    sys.modules['psutil'] = type('MockPsutil', (), {
        'cpu_percent': lambda x: 75.0,
        'virtual_memory': lambda: type('MockMemory', (), {
            'percent': 70.0,
            'used': 8 * 1024**3,
            'available': 4 * 1024**3
        })(),
        'disk_usage': lambda x: type('MockDisk', (), {
            'percent': 50.0,
            'free': 20 * 1024**3
        })(),
        'net_io_counters': lambda: type('MockNetIO', (), {
            'bytes_sent': 1000000,
            'bytes_recv': 2000000
        })(),
        'Process': lambda x: type('MockProcess', (), {
            'memory_info': lambda: type('MockMemInfo', (), {'rss': 200 * 1024**2})(),
            'cpu_percent': lambda: 15.0
        })(),
        'cpu_count': lambda: 4
    })()

    asyncio.run(main())
