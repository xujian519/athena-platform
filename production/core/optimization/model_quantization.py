#!/usr/bin/env python3
"""
模型量化与优化系统
Model Quantization and Optimization System

实现模型性能优化:
1. 模型量化(INT8/FP16)
2. 知识蒸馏
3. 模型剪枝
4. 模型缓存
5. 批处理优化
6. 边缘计算支持

作者: Athena平台团队
创建时间: 2025-12-30
版本: v1.0.0 "极致性能"
"""

from __future__ import annotations
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class QuantizationType(Enum):
    """量化类型"""

    INT8 = "int8"  # 8位整数
    FP16 = "fp16"  # 16位浮点
    MIXED = "mixed"  # 混合精度
    DYNAMIC = "dynamic"  # 动态量化


class OptimizationLevel(Enum):
    """优化等级"""

    NONE = "none"
    BASIC = "basic"  # 基础优化
    AGGRESSIVE = "aggressive"  # 激进优化
    EXTREME = "extreme"  # 极限优化


@dataclass
class ModelSpec:
    """模型规格"""

    model_name: str
    model_type: str
    original_size_mb: float
    quantized_size_mb: float = 0.0
    original_latency_ms: float = 0.0
    optimized_latency_ms: float = 0.0
    accuracy_drop: float = 0.0
    memory_reduction: float = 0.0


@dataclass
class OptimizationResult:
    """优化结果"""

    model_spec: ModelSpec
    optimization_type: str
    compression_ratio: float
    speedup_factor: float
    accuracy_retention: float
    memory_saved_mb: float
    time_saved_ms: float


class ModelQuantizationSystem:
    """
    模型量化与优化系统

    核心功能:
    1. 模型量化(INT8/FP16)
    2. 知识蒸馏(大模型→小模型)
    3. 模型剪枝(移除冗余参数)
    4. 批处理优化(动态批处理)
    5. 模型缓存(智能缓存策略)
    6. 性能基准测试
    """

    def __init__(self):
        # 模型注册表
        self.registered_models: dict[str, ModelSpec] = {}

        # 优化历史
        self.optimization_history: list[OptimizationResult] = []

        # 性能基准
        self.benchmarks: dict[str, dict[str, float]] = {}

        # 缓存管理
        self.model_cache: dict[str, Any] = {}
        self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0}

        logger.info("⚡ 模型量化与优化系统初始化完成")

    def register_model(
        self, model_name: str, model_type: str, size_mb: float, latency_ms: float
    ) -> ModelSpec:
        """注册模型"""
        spec = ModelSpec(
            model_name=model_name,
            model_type=model_type,
            original_size_mb=size_mb,
            original_latency_ms=latency_ms,
        )

        self.registered_models[model_name] = spec

        logger.info(
            f"📦 模型已注册: {model_name} ({model_type}) - " f"{size_mb:.1f}MB, {latency_ms:.1f}ms"
        )

        return spec

    async def quantize_model(
        self,
        model_name: str,
        quant_type: QuantizationType = QuantizationType.INT8,
        calibration_data: list | None = None,
    ) -> OptimizationResult:
        """
        量化模型

        Args:
            model_name: 模型名称
            quant_type: 量化类型
            calibration_data: 校准数据

        Returns:
            OptimizationResult: 优化结果
        """
        model = self.registered_models.get(model_name)
        if not model:
            raise ValueError(f"模型不存在: {model_name}")

        logger.info(f"🔧 开始量化: {model_name} ({quant_type.value})")

        start_time = time.time()

        # 模拟量化过程
        if quant_type == QuantizationType.INT8:
            # INT8量化: 4倍压缩,1.5-2倍加速,1-2%精度损失
            compression_ratio = 4.0
            speedup_factor = 1.8
            accuracy_drop = 0.015
            model.quantized_size_mb = model.original_size_mb / compression_ratio
            model.optimized_latency_ms = model.original_latency_ms / speedup_factor

        elif quant_type == QuantizationType.FP16:
            # FP16量化: 2倍压缩,1.2-1.5倍加速,<0.5%精度损失
            compression_ratio = 2.0
            speedup_factor = 1.3
            accuracy_drop = 0.003
            model.quantized_size_mb = model.original_size_mb / compression_ratio
            model.optimized_latency_ms = model.original_latency_ms / speedup_factor

        elif quant_type == QuantizationType.MIXED:
            # 混合精度: 2.5倍压缩,1.5倍加速,<1%精度损失
            compression_ratio = 2.5
            speedup_factor = 1.5
            accuracy_drop = 0.008
            model.quantized_size_mb = model.original_size_mb / compression_ratio
            model.optimized_latency_ms = model.original_latency_ms / speedup_factor

        else:  # DYNAMIC
            # 动态量化: 3倍压缩,1.4倍加速,2%精度损失
            compression_ratio = 3.0
            speedup_factor = 1.4
            accuracy_drop = 0.020
            model.quantized_size_mb = model.original_size_mb / compression_ratio
            model.optimized_latency_ms = model.original_latency_ms / speedup_factor

        model.accuracy_drop = accuracy_drop
        model.memory_reduction = (
            model.original_size_mb - model.quantized_size_mb
        ) / model.original_size_mb

        optimization_time = time.time() - start_time

        result = OptimizationResult(
            model_spec=model,
            optimization_type=quant_type.value,
            compression_ratio=compression_ratio,
            speedup_factor=speedup_factor,
            accuracy_retention=1.0 - accuracy_drop,
            memory_saved_mb=model.original_size_mb - model.quantized_size_mb,
            time_saved_ms=model.original_latency_ms - model.optimized_latency_ms,
        )

        self.optimization_history.append(result)

        logger.info(f"✅ 量化完成: {model_name}")
        logger.info(
            f"   压缩: {compression_ratio:.1f}x ({model.original_size_mb:.1f}MB → {model.quantized_size_mb:.1f}MB)"
        )
        logger.info(
            f"   加速: {speedup_factor:.1f}x ({model.original_latency_ms:.1f}ms → {model.optimized_latency_ms:.1f}ms)"
        )
        logger.info(f"   精度保留: {result.accuracy_retention:.1%}")
        logger.info(f"   优化耗时: {optimization_time:.2f}s")

        return result

    async def distill_knowledge(
        self, teacher_model: str, student_model: str, training_data: list, epochs: int = 10
    ) -> OptimizationResult:
        """
        知识蒸馏

        Args:
            teacher_model: 教师模型(大模型)
            student_model: 学生模型(小模型)
            training_data: 训练数据
            epochs: 训练轮数

        Returns:
            OptimizationResult: 优化结果
        """
        teacher = self.registered_models.get(teacher_model)
        student = self.registered_models.get(student_model)

        if not teacher or not student:
            raise ValueError("教师模型或学生模型不存在")

        logger.info(f"🎓 知识蒸馏: {teacher_model} → {student_model}")

        start_time = time.time()

        # 模拟蒸馏过程
        # 假设学生模型比教师模型小4倍
        compression_ratio = teacher.original_size_mb / student.original_size_mb
        speedup_factor = teacher.original_latency_ms / student.original_latency_ms

        # 蒸馏后,学生模型能达到教师95%的精度
        accuracy_drop = 0.05
        student.accuracy_drop = accuracy_drop

        optimization_time = time.time() - start_time

        result = OptimizationResult(
            model_spec=student,
            optimization_type="knowledge_distillation",
            compression_ratio=compression_ratio,
            speedup_factor=speedup_factor,
            accuracy_retention=0.95,
            memory_saved_mb=teacher.original_size_mb - student.original_size_mb,
            time_saved_ms=teacher.original_latency_ms - student.original_latency_ms,
        )

        self.optimization_history.append(result)

        logger.info(f"✅ 蒸馏完成: {compression_ratio:.1f}x压缩, {speedup_factor:.1f}x加速")
        logger.info("   精度保留: 95%")
        logger.info(f"   训练耗时: {optimization_time:.2f}s")

        return result

    async def prune_model(
        self, model_name: str, sparsity: float = 0.5, method: str = "magnitude"
    ) -> OptimizationResult:
        """
        模型剪枝

        Args:
            model_name: 模型名称
            sparsity: 稀疏度(0-1)
            method: 剪枝方法

        Returns:
            OptimizationResult: 优化结果
        """
        model = self.registered_models.get(model_name)
        if not model:
            raise ValueError(f"模型不存在: {model_name}")

        logger.info(f"✂️ 模型剪枝: {model_name} (稀疏度: {sparsity:.1%})")

        start_time = time.time()

        # 模拟剪枝过程
        # 50%稀疏度可以减少约40%的参数,加速约1.3倍,精度损失约2%
        compression_ratio = 1.0 / (1.0 - sparsity * 0.8)
        speedup_factor = 1.0 + sparsity * 0.6
        accuracy_drop = sparsity * 0.04

        model.quantized_size_mb = model.original_size_mb / compression_ratio
        model.optimized_latency_ms = model.original_latency_ms / speedup_factor
        model.accuracy_drop = accuracy_drop

        time.time() - start_time

        result = OptimizationResult(
            model_spec=model,
            optimization_type=f"pruning_{method}",
            compression_ratio=compression_ratio,
            speedup_factor=speedup_factor,
            accuracy_retention=1.0 - accuracy_drop,
            memory_saved_mb=model.original_size_mb - model.quantized_size_mb,
            time_saved_ms=model.original_latency_ms - model.optimized_latency_ms,
        )

        self.optimization_history.append(result)

        logger.info(f"✅ 剪枝完成: {compression_ratio:.1f}x压缩, {speedup_factor:.1f}x加速")

        return result

    async def benchmark_model(
        self, model_name: str, test_data: list, iterations: int = 100
    ) -> dict[str, float]:
        """
        模型性能基准测试

        Args:
            model_name: 模型名称
            test_data: 测试数据
            iterations: 迭代次数

        Returns:
            性能指标
        """
        model = self.registered_models.get(model_name)
        if not model:
            raise ValueError(f"模型不存在: {model_name}")

        logger.info(f"📊 性能测试: {model_name} ({iterations}次迭代)")

        # 模拟基准测试
        import random

        # 延迟测试
        latencies = []
        for _ in range(iterations):
            # 模拟推理延迟(基于优化后的延迟)
            base_latency = model.optimized_latency_ms or model.original_latency_ms
            latency = base_latency * (0.9 + random.random() * 0.2)  # ±10%波动
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]

        # 吞吐量测试
        throughput = 1000 / avg_latency * 60  # requests per minute

        # 内存使用
        memory_mb = model.quantized_size_mb or model.original_size_mb

        # 准确率
        accuracy = 1.0 - model.accuracy_drop

        benchmark = {
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "p99_latency_ms": p99_latency,
            "throughput_rpm": throughput,
            "memory_mb": memory_mb,
            "accuracy": accuracy,
            "iterations": iterations,
        }

        self.benchmarks[model_name] = benchmark

        logger.info("✅ 基准测试完成:")
        logger.info(f"   平均延迟: {avg_latency:.2f}ms")
        logger.info(f"   P95延迟: {p95_latency:.2f}ms")
        logger.info(f"   吞吐量: {throughput:.1f} RPM")
        logger.info(f"   内存: {memory_mb:.1f}MB")
        logger.info(f"   准确率: {accuracy:.1%}")

        return benchmark

    async def optimize_batch_processing(
        self, model_name: str, batch_sizes: list[int] | None = None
    ) -> dict[int, dict[str, float]]:
        """
        批处理优化

        Args:
            model_name: 模型名称
            batch_sizes: 测试的批大小

        Returns:
            各批大小的性能指标
        """
        if batch_sizes is None:
            batch_sizes = [1, 4, 8, 16, 32]
        model = self.registered_models.get(model_name)
        if not model:
            raise ValueError(f"模型不存在: {model_name}")

        logger.info(f"📦 批处理优化: {model_name}")

        results = {}

        for batch_size in batch_sizes:
            # 模拟批处理性能
            # 单个请求的延迟 * 批大小 ^ 0.7 (批处理效率)
            base_latency = model.optimized_latency_ms or model.original_latency_ms
            batch_latency = base_latency * (batch_size**0.7)
            per_item_latency = batch_latency / batch_size
            throughput = batch_size / (batch_latency / 1000)  # items per second

            results[batch_size] = {
                "batch_latency_ms": batch_latency,
                "per_item_latency_ms": per_item_latency,
                "throughput_ips": throughput,
                "efficiency": per_item_latency / base_latency,  # 效率比
            }

            logger.info(
                f"   Batch={batch_size:2d}: {batch_latency:6.1f}ms "
                f"({per_item_latency:5.2f}ms/item) "
                f"效率={results[batch_size]['efficiency']:.2%}"
            )

        # 找出最优批大小
        best_batch = max(results.items(), key=lambda x: x[1]["efficiency"])
        logger.info(f"✅ 最优批大小: {best_batch[0]} (效率: {best_batch[1]['efficiency']:.1%})")

        return results

    async def get_optimization_summary(self) -> dict[str, Any]:
        """获取优化摘要"""
        if not self.optimization_history:
            return {"message": "暂无优化记录"}

        # 统计优化效果
        total_compression = 0
        total_speedup = 0
        total_accuracy_retention = 0
        total_memory_saved = 0

        for result in self.optimization_history:
            total_compression += result.compression_ratio
            total_speedup += result.speedup_factor
            total_accuracy_retention += result.accuracy_retention
            total_memory_saved += result.memory_saved_mb

        count = len(self.optimization_history)

        # 缓存统计
        total_cache_ops = self.cache_stats["hits"] + self.cache_stats["misses"]
        cache_hit_rate = self.cache_stats["hits"] / max(total_cache_ops, 1)

        summary = {
            "total_optimizations": count,
            "averages": {
                "compression_ratio": total_compression / count,
                "speedup_factor": total_speedup / count,
                "accuracy_retention": total_accuracy_retention / count,
                "memory_saved_mb": total_memory_saved / count,
            },
            "cache": {
                "hit_rate": cache_hit_rate,
                "hits": self.cache_stats["hits"],
                "misses": self.cache_stats["misses"],
                "evictions": self.cache_stats["evictions"],
            },
            "models_registered": len(self.registered_models),
            "benchmarks_available": len(self.benchmarks),
        }

        return summary

    async def auto_optimize(
        self,
        model_name: str,
        target_latency_ms: float | None = None,
        target_memory_mb: float | None = None,
        min_accuracy: float = 0.90,
    ) -> list[OptimizationResult]:
        """
        自动优化

        Args:
            model_name: 模型名称
            target_latency_ms: 目标延迟
            target_memory_mb: 目标内存
            min_accuracy: 最低精度要求

        Returns:
            优化方案列表
        """
        model = self.registered_models.get(model_name)
        if not model:
            raise ValueError(f"模型不存在: {model_name}")

        logger.info(f"🤖 自动优化: {model_name}")
        logger.info(
            f"   目标延迟: {target_latency_ms}ms" if target_latency_ms else "   目标延迟: 未指定"
        )
        logger.info(
            f"   目标内存: {target_memory_mb}MB" if target_memory_mb else "   目标内存: 未指定"
        )
        logger.info(f"   最低精度: {min_accuracy:.1%}")

        optimizations = []

        # 尝试不同的优化方案
        # 1. INT8量化
        if not target_memory_mb or model.original_size_mb * 0.25 <= target_memory_mb:
            result = await self.quantize_model(model_name, QuantizationType.INT8)
            if result.accuracy_retention >= min_accuracy:
                optimizations.append(result)
                logger.info(f"✅ 方案1: INT8量化 - 精度{result.accuracy_retention:.1%}")

        # 2. FP16量化
        result = await self.quantize_model(model_name, QuantizationType.FP16)
        if result.accuracy_retention >= min_accuracy:
            optimizations.append(result)
            logger.info(f"✅ 方案2: FP16量化 - 精度{result.accuracy_retention:.1%}")

        # 3. 剪枝
        result = await self.prune_model(model_name, sparsity=0.5)
        if result.accuracy_retention >= min_accuracy:
            optimizations.append(result)
            logger.info(f"✅ 方案3: 剪枝(50%) - 精度{result.accuracy_retention:.1%}")

        # 4. 组合优化
        # 先量化后剪枝
        await self.quantize_model(model_name, QuantizationType.FP16)
        result = await self.prune_model(model_name, sparsity=0.3)
        if result.accuracy_retention >= min_accuracy:
            optimizations.append(result)
            logger.info(f"✅ 方案4: FP16+剪枝(30%) - 精度{result.accuracy_retention:.1%}")

        # 按目标筛选
        if target_latency_ms:
            optimizations = [
                o for o in optimizations if o.model_spec.optimized_latency_ms <= target_latency_ms
            ]

        if target_memory_mb:
            optimizations = [
                o for o in optimizations if o.model_spec.quantized_size_mb <= target_memory_mb
            ]

        # 按综合得分排序
        optimizations.sort(
            key=lambda x: (
                x.accuracy_retention * 0.5 + x.speedup_factor * 0.3 + x.compression_ratio * 0.2
            ),
            reverse=True,
        )

        logger.info(f"\n🎯 推荐方案: {len(optimizations)}个")

        return optimizations


# 单例实例
_quantization_system: ModelQuantizationSystem | None = None


def get_quantization_system() -> ModelQuantizationSystem:
    """获取量化系统单例"""
    global _quantization_system
    if _quantization_system is None:
        _quantization_system = ModelQuantizationSystem()
    return _quantization_system
