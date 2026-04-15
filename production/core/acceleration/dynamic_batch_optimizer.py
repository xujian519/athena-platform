#!/usr/bin/env python3
"""
动态批处理优化器 - 阶段3优化
根据GPU内存实时调整批处理大小,最大化吞吐量

作者: 小诺·双鱼公主 🌊✨
创建时间: 2025-12-27
版本: v1.0.0
"""

from __future__ import annotations
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any

import torch

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class BatchPerformanceMetrics:
    """批处理性能指标"""

    batch_size: int
    avg_latency_ms: float
    throughput_per_second: float
    gpu_memory_mb: float
    gpu_utilization_percent: float
    timestamp: float


@dataclass
class DynamicBatchConfig:
    """动态批处理配置"""

    # 批次大小范围
    min_batch_size: int = 8
    max_batch_size: int = 256
    initial_batch_size: int = 64

    # GPU内存目标
    target_gpu_memory_percent: float = 0.85  # 目标GPU内存使用率85%
    max_gpu_memory_percent: float = 0.95  # 最大GPU内存使用率95%

    # 性能优化参数
    warmup_batches: int = 5  # 预热批次数量
    measurement_batches: int = 10  # 测量批次数量
    adjustment_step: int = 8  # 每次调整步长

    # 自适应调整
    enable_adaptive: bool = True
    performance_window: int = 20  # 性能历史窗口大小


class DynamicBatchOptimizer:
    """动态批处理优化器"""

    def __init__(self, config: DynamicBatchConfig = None):
        self.config = config or DynamicBatchConfig()
        self.device = self._select_device()

        # 当前批次大小
        self.current_batch_size = self.config.initial_batch_size

        # 性能历史
        self.performance_history: deque = deque(maxlen=self.config.performance_window)
        self.history_lock = threading.Lock()

        # 统计信息
        self.stats = {
            "total_batches": 0,
            "batch_adjustments": 0,
            "avg_batch_size": 0.0,
            "best_batch_size": self.config.initial_batch_size,
            "best_throughput": 0.0,
        }
        self.stats_lock = threading.Lock()

        logger.info("🔄 动态批处理优化器初始化完成")
        logger.info(f"📦 批次范围: {self.config.min_batch_size}-{self.config.max_batch_size}")
        logger.info(f"🎯 目标GPU内存: {self.config.target_gpu_memory_percent*100}%")

    def _select_device(self) -> torch.device:
        """选择最优设备"""
        if torch.backends.mps.is_available():
            return torch.device("mps")
        elif torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")

    def get_optimal_batch_size(self, num_inputs: int, model_type: str = "bert") -> int:
        """
        获取最优批处理大小

        Args:
            num_inputs: 输入数量
            model_type: 模型类型

        Returns:
            最优批次大小
        """
        # 获取当前GPU内存情况
        gpu_memory_info = self._get_gpu_memory_info()

        # 基于内存使用率动态调整
        memory_usage_ratio = gpu_memory_info["used_mb"] / gpu_memory_info["total_mb"]

        if memory_usage_ratio > self.config.max_gpu_memory_percent:
            # 内存使用率过高,减小批次
            self.current_batch_size = max(
                self.config.min_batch_size, self.current_batch_size - self.config.adjustment_step
            )
            logger.warning(
                f"⚠️ GPU内存压力大({memory_usage_ratio*100:.1f}%),减小批次至{self.current_batch_size}"
            )

        elif memory_usage_ratio < self.config.target_gpu_memory_percent * 0.8:
            # 内存使用率较低,可以增加批次
            self.current_batch_size = min(
                self.config.max_batch_size, self.current_batch_size + self.config.adjustment_step
            )
            logger.info(
                f"✅ GPU内存充足({memory_usage_ratio*100:.1f}%),增加批次至{self.current_batch_size}"
            )

        # 根据模型类型微调
        if model_type == "bert":
            # BERT模型可以较大批次
            model_factor = 1.0
        elif model_type == "intent":
            # 意图识别模型中等批次
            model_factor = 0.75
        elif model_type == "embedding":
            # 向量嵌入模型可以很大批次
            model_factor = 1.5
        else:
            model_factor = 1.0

        adjusted_batch_size = int(self.current_batch_size * model_factor)
        adjusted_batch_size = max(
            self.config.min_batch_size, min(self.config.max_batch_size, adjusted_batch_size)
        )

        # 最终限制:不超过输入数量
        final_batch_size = min(adjusted_batch_size, num_inputs)

        return final_batch_size

    def record_batch_performance(
        self, batch_size: int, latency_ms: float, throughput: float, gpu_memory_mb: float
    ):
        """
        记录批处理性能

        Args:
            batch_size: 批次大小
            latency_ms: 延迟(毫秒)
            throughput: 吞吐量(请求/秒)
            gpu_memory_mb: GPU内存使用(MB)
        """
        metrics = BatchPerformanceMetrics(
            batch_size=batch_size,
            avg_latency_ms=latency_ms,
            throughput_per_second=throughput,
            gpu_memory_mb=gpu_memory_mb,
            gpu_utilization_percent=gpu_memory_mb / self._get_total_gpu_memory_mb() * 100,
            timestamp=time.time(),
        )

        with self.history_lock:
            self.performance_history.append(metrics)

        # 更新统计
        with self.stats_lock:
            self.stats["total_batches"] += 1
            self.stats["avg_batch_size"] = (
                self.stats["avg_batch_size"] * (self.stats["total_batches"] - 1) + batch_size
            ) / self.stats["total_batches"]

            # 跟踪最佳批次大小
            if throughput > self.stats["best_throughput"]:
                self.stats["best_throughput"] = throughput
                self.stats["best_batch_size"] = batch_size

        # 自适应调整
        if self.config.enable_adaptive:
            self._adaptive_adjustment(metrics)

    def _adaptive_adjustment(self, metrics: BatchPerformanceMetrics) -> Any:
        """自适应调整批次大小"""
        with self.history_lock:
            if len(self.performance_history) < self.config.measurement_batches:
                return

            # 分析最近N个批次的性能
            recent_metrics = list(self.performance_history)[-self.config.measurement_batches :]

            # 计算平均吞吐量
            avg_throughput = sum(m.throughput_per_second for m in recent_metrics) / len(
                recent_metrics
            )

            # 尝试调整批次大小
            current_batch = metrics.batch_size

            # 如果当前批次不是最大值,尝试增加
            if current_batch < self.config.max_batch_size:
                # 检查增加批次是否能提升吞吐量
                next_batch = min(
                    self.config.max_batch_size, current_batch + self.config.adjustment_step
                )

                # 如果吞吐量还在提升,继续增加
                if avg_throughput > self.stats["best_throughput"] * 0.95:
                    self.current_batch_size = next_batch
                    with self.stats_lock:
                        self.stats["batch_adjustments"] += 1
                    logger.info(f"📈 增加批次: {current_batch} → {next_batch}")

            # 如果当前批次不是最小值,考虑减少
            elif current_batch > self.config.min_batch_size:
                # 如果内存使用率过高,减少批次
                if metrics.gpu_utilization_percent > self.config.max_gpu_memory_percent * 100:
                    next_batch = max(
                        self.config.min_batch_size, current_batch - self.config.adjustment_step
                    )
                    self.current_batch_size = next_batch
                    with self.stats_lock:
                        self.stats["batch_adjustments"] += 1
                    logger.info(f"📉 减少批次: {current_batch} → {next_batch}")

    def _get_gpu_memory_info(self) -> dict[str, float]:
        """获取GPU内存信息"""
        if self.device.type == "mps":
            if hasattr(torch.mps, "current_allocated_memory"):
                used_mb = torch.mps.current_allocated_memory() / (1024 * 1024)
                total_mb = 48 * 1024  # M4 Pro 48GB
                return {"used_mb": used_mb, "total_mb": total_mb, "free_mb": total_mb - used_mb}
        elif self.device.type == "cuda" and torch.cuda.is_available():
            used_mb = torch.cuda.memory_allocated() / (1024 * 1024)
            total_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
            return {"used_mb": used_mb, "total_mb": total_mb, "free_mb": total_mb - used_mb}

        # 默认返回
        return {"used_mb": 0, "total_mb": 48 * 1024, "free_mb": 48 * 1024}

    def _get_total_gpu_memory_mb(self) -> float:
        """获取GPU总内存"""
        return self._get_gpu_memory_info()["total_mb"]

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        with self.history_lock:
            if len(self.performance_history) == 0:
                return {"message": "暂无性能数据"}

            recent = list(self.performance_history)[-10:]

            return {
                "current_batch_size": self.current_batch_size,
                "avg_latency_ms": sum(m.avg_latency_ms for m in recent) / len(recent),
                "avg_throughput": sum(m.throughput_per_second for m in recent) / len(recent),
                "avg_gpu_memory_mb": sum(m.gpu_memory_mb for m in recent) / len(recent),
                "avg_gpu_utilization_percent": sum(m.gpu_utilization_percent for m in recent)
                / len(recent),
                "stats": self.stats.copy(),
                "performance_history_size": len(self.performance_history),
            }

    def reset_history(self) -> Any:
        """重置性能历史"""
        with self.history_lock:
            self.performance_history.clear()
        logger.info("🗑️ 性能历史已重置")

    def get_recommendations(self) -> list[str]:
        """获取优化建议"""
        recommendations = []

        gpu_memory = self._get_gpu_memory_info()
        memory_usage_ratio = gpu_memory["used_mb"] / gpu_memory["total_mb"]

        if memory_usage_ratio > self.config.max_gpu_memory_percent:
            recommendations.append(
                f"⚠️ GPU内存使用率过高({memory_usage_ratio*100:.1f}%),建议减小批次大小或释放未使用的模型"
            )

        elif memory_usage_ratio < self.config.target_gpu_memory_percent * 0.7:
            recommendations.append(
                f"💡 GPU内存使用率较低({memory_usage_ratio*100:.1f}%),可以增加批次大小提升吞吐量"
            )

        with self.stats_lock:
            if self.stats["total_batches"] > 20:
                if self.stats["avg_batch_size"] < self.config.min_batch_size * 2:
                    recommendations.append(
                        f"💡 平均批次大小较小({self.stats['avg_batch_size']:.1f}),可能需要优化模型或输入处理"
                    )

        return recommendations


# 全局单例
_batch_optimizer: DynamicBatchOptimizer | None = None
_optimizer_lock = threading.Lock()


def get_batch_optimizer() -> DynamicBatchOptimizer:
    """获取全局批处理优化器实例"""
    global _batch_optimizer
    if _batch_optimizer is None:
        with _optimizer_lock:
            if _batch_optimizer is None:
                _batch_optimizer = DynamicBatchOptimizer()
    return _batch_optimizer


def get_optimal_batch_size(num_inputs: int, model_type: str = "bert") -> int:
    """便捷函数:获取最优批次大小"""
    optimizer = get_batch_optimizer()
    return optimizer.get_optimal_batch_size(num_inputs, model_type)


if __name__ == "__main__":
    # 测试动态批处理优化器
    logging.basicConfig(level=logging.INFO)

    optimizer = DynamicBatchOptimizer()

    # 模拟不同输入数量
    test_cases = [(10, "bert"), (50, "bert"), (100, "embedding"), (200, "intent"), (500, "bert")]

    print("\n📊 最优批次大小测试:")
    print("=" * 50)
    for num_inputs, model_type in test_cases:
        batch_size = optimizer.get_optimal_batch_size(num_inputs, model_type)
        print(f"输入: {num_inputs:4d}, 模型: {model_type:10s} → 批次大小: {batch_size}")

    # 模拟性能记录
    print("\n📊 模拟性能记录:")
    print("=" * 50)
    for i in range(20):
        batch_size = 32 + (i % 5) * 16  # 32, 48, 64, 80, 96
        latency = 10 + batch_size * 0.1
        throughput = batch_size / (latency / 1000)
        gpu_memory = 4000 + batch_size * 50

        optimizer.record_batch_performance(
            batch_size=batch_size,
            latency_ms=latency,
            throughput=throughput,
            gpu_memory_mb=gpu_memory,
        )

    # 显示报告
    report = optimizer.get_performance_report()
    print(f"\n当前批次大小: {report['current_batch_size']}")
    print(f"平均延迟: {report['avg_latency_ms']:.2f}ms")
    print(f"平均吞吐量: {report['avg_throughput']:.2f} 请求/秒")
    print(f"平均GPU利用率: {report['avg_gpu_utilization_percent']:.1f}%")
    print(f"总批次数: {report['stats']['total_batches']}")
    print(f"最佳批次大小: {report['stats']['best_batch_size']}")
    print(f"最佳吞吐量: {report['stats']['best_throughput']:.2f} 请求/秒")

    # 显示建议
    print("\n💡 优化建议:")
    for rec in optimizer.get_recommendations():
        print(f"  {rec}")
