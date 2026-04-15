#!/usr/bin/env python3
"""
模型量化压缩系统 (Model Quantization & Compression System)
减小模型大小和推理延迟

作者: 小诺·双鱼公主
版本: v3.0.0
优化目标: 模型大小减少 75%+, 推理速度提升 3x+
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class QuantizationType(str, Enum):
    """量化类型"""

    FP32 = "fp32"  # 32位浮点
    FP16 = "fp16"  # 16位浮点
    BF16 = "bf16"  # BFloat16
    INT8 = "int8"  # 8位整数
    INT4 = "int4"  # 4位整数
    MIXED = "mixed"  # 混合精度


class CompressionMethod(str, Enum):
    """压缩方法"""

    QUANTIZATION = "quantization"  # 量化
    PRUNING = "pruning"  # 剪枝
    KNOWLEDGE_DISTILLATION = "distillation"  # 蒸馏
    LOW_RANK = "low_rank"  # 低秩分解
    HUFFMAN = "huffman"  # 霍夫曼编码
    PRODUCT_QUANTIZATION = "pq"  # 乘积量化


@dataclass
class QuantizationConfig:
    """量化配置"""

    quant_type: QuantizationType
    per_channel: bool = False
    symmetric: bool = True
    calibration_samples: int = 100
    preserve_layers: list[str] = field(default_factory=list)


@dataclass
class PruningConfig:
    """剪枝配置"""

    method: str  # magnitude, gradient, structured
    sparsity: float  # 目标稀疏度
    prune_per_layer: bool = True
    iterative: bool = True
    prune_iterations: int = 10


@dataclass
class CompressionResult:
    """压缩结果"""

    original_size_mb: float
    compressed_size_mb: float
    compression_ratio: float
    accuracy_before: float
    accuracy_after: float
    accuracy_drop: float
    latency_before_ms: float
    latency_after_ms: float
    speedup: float
    method: CompressionMethod


class ModelCompressionSystem:
    """
    模型压缩系统

    功能:
    1. 量化(FP16/INT8/INT4)
    2. 剪枝
    3. 低秩分解
    4. 混合精度
    5. 性能评估
    """

    def __init__(self):
        self.name = "模型压缩系统"
        self.version = "3.0.0"

        # 模型参数
        self.model_params: dict[str, np.ndarray] = {}

        # 压缩历史
        self.compression_history: list[CompressionResult] = []

        # 统计信息
        self.stats = {
            "total_compressions": 0,
            "avg_compression_ratio": 0.0,
            "avg_accuracy_drop": 0.0,
            "avg_speedup": 0.0,
        }

        logger.info(f"✅ {self.name} 初始化完成")

    def load_model(self, params: dict[str, np.ndarray]) -> None:
        """加载模型参数"""
        self.model_params = params
        original_size = sum(v.nbytes for v in params.values()) / (1024 * 1024)
        logger.info(f"📦 模型已加载 (大小: {original_size:.2f}MB)")

    async def quantize(
        self, config: QuantizationConfig, validation_data: np.ndarray | None = None
    ) -> CompressionResult:
        """
        量化模型

        Args:
            config: 量化配置
            validation_data: 校准数据

        Returns:
            压缩结果
        """
        logger.info(f"🔢 开始量化: {config.quant_type.value}")

        original_size = sum(v.nbytes for v in self.model_params.values()) / (1024 * 1024)
        accuracy_before = await self._evaluate_model(self.model_params)

        # 根据量化类型量化
        if config.quant_type == QuantizationType.FP16:
            quantized_params = await self._quantize_fp16(self.model_params)
        elif config.quant_type == QuantizationType.INT8:
            quantized_params = await self._quantize_int8(self.model_params, config, validation_data)
        elif config.quant_type == QuantizationType.INT4:
            quantized_params = await self._quantize_int4(self.model_params, config)
        else:
            quantized_params = self.model_params.copy()

        compressed_size = sum(v.nbytes for v in quantized_params.values()) / (1024 * 1024)
        accuracy_after = await self._evaluate_model(quantized_params)

        # 评估延迟
        latency_before = await self._measure_inference_time(self.model_params)
        latency_after = await self._measure_inference_time(quantized_params)

        result = CompressionResult(
            original_size_mb=original_size,
            compressed_size_mb=compressed_size,
            compression_ratio=original_size / compressed_size,
            accuracy_before=accuracy_before,
            accuracy_after=accuracy_after,
            accuracy_drop=accuracy_before - accuracy_after,
            latency_before_ms=latency_before,
            latency_after_ms=latency_after,
            speedup=latency_before / latency_after,
            method=CompressionMethod.QUANTIZATION,
        )

        self.compression_history.append(result)
        self._update_stats(result)

        logger.info(
            f"✅ 量化完成: 压缩比 {result.compression_ratio:.2f}x, "
            f"准确率下降 {result.accuracy_drop:.2%}, 加速 {result.speedup:.2f}x"
        )

        return result

    async def _quantize_fp16(self, params: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        """FP16量化"""
        quantized = {}
        for key, value in params.items():
            if value.dtype == np.float32:
                quantized[key] = value.astype(np.float16)
            else:
                quantized[key] = value.copy()
        return quantized

    async def _quantize_int8(
        self,
        params: dict[str, np.ndarray],
        config: QuantizationConfig,
        calibration_data: np.ndarray,
    ) -> dict[str, np.ndarray]:
        """INT8量化"""
        quantized = {}

        for key, value in params.items():
            if value.dtype not in [np.float32, np.float64]:
                quantized[key] = value.copy()
                continue

            # 计算量化范围
            if config.symmetric:
                # 对称量化
                scale = np.max(np.abs(value)) / 127
                quantized[key] = np.round(value / scale).astype(np.int8)
            else:
                # 非对称量化
                min_val = np.min(value)
                max_val = np.max(value)
                scale = (max_val - min_val) / 255
                zero_point = np.round(-min_val / scale).astype(np.int32)
                quantized[key] = np.round(value / scale + zero_point).astype(np.uint8)

        return quantized

    async def _quantize_int4(
        self, params: dict[str, np.ndarray], config: QuantizationConfig
    ) -> dict[str, np.ndarray]:
        """INT4量化(简化版)"""
        # 简化版:实际INT4需要特殊处理
        quantized = {}
        for key, value in params.items():
            if value.dtype not in [np.float32, np.float64]:
                quantized[key] = value.copy()
                continue

            # 量化到[-8, 7]
            scale = np.max(np.abs(value)) / 8
            quantized[key] = np.clip(np.round(value / scale), -8, 7).astype(np.int8)

        return quantized

    async def prune(
        self, config: PruningConfig, gradients: dict[str, np.ndarray] | None = None
    ) -> CompressionResult:
        """
        剪枝模型

        Args:
            config: 剪枝配置
            gradients: 梯度(用于重要性评估)

        Returns:
            压缩结果
        """
        logger.info(f"✂️ 开始剪枝: {config.method}, 目标稀疏度 {config.sparsity:.1%}")

        original_size = sum(v.nbytes for v in self.model_params.values()) / (1024 * 1024)
        accuracy_before = await self._evaluate_model(self.model_params)

        pruned_params = await self._apply_pruning(self.model_params, config, gradients)

        compressed_size = sum(v.nbytes for v in pruned_params.values()) / (1024 * 1024)
        accuracy_after = await self._evaluate_model(pruned_params)

        latency_before = await self._measure_inference_time(self.model_params)
        latency_after = await self._measure_inference_time(pruned_params)

        result = CompressionResult(
            original_size_mb=original_size,
            compressed_size_mb=compressed_size,
            compression_ratio=original_size / compressed_size,
            accuracy_before=accuracy_before,
            accuracy_after=accuracy_after,
            accuracy_drop=accuracy_before - accuracy_after,
            latency_before_ms=latency_before,
            latency_after_ms=latency_after,
            speedup=latency_before / latency_after,
            method=CompressionMethod.PRUNING,
        )

        self.compression_history.append(result)
        self._update_stats(result)

        logger.info(
            f"✅ 剪枝完成: 稀疏度 {config.sparsity:.1%}, " f"准确率下降 {result.accuracy_drop:.2%}"
        )

        return result

    async def _apply_pruning(
        self,
        params: dict[str, np.ndarray],
        config: PruningConfig,
        gradients: dict[str, np.ndarray],
    ) -> dict[str, np.ndarray]:
        """应用剪枝"""
        pruned = {}

        for key, value in params.items():
            if config.method == "magnitude":
                # 基于幅度的剪枝
                threshold = np.percentile(np.abs(value), config.sparsity * 100)
                mask = np.abs(value) > threshold
                pruned[key] = value * mask

            elif config.method == "gradient" and gradients:
                # 基于梯度的剪枝
                if key in gradients:
                    importance = np.abs(value * gradients[key])
                    threshold = np.percentile(importance, config.sparsity * 100)
                    mask = importance > threshold
                    pruned[key] = value * mask
                else:
                    pruned[key] = value.copy()

            else:
                pruned[key] = value.copy()

        return pruned

    async def low_rank_decompose(self, layer_name: str, rank: int) -> tuple[np.ndarray, np.ndarray]:
        """
        低秩分解

        Args:
            layer_name: 层名称
            rank: 目标秩

        Returns:
            分解后的两个矩阵
        """
        if layer_name not in self.model_params:
            raise ValueError(f"层 {layer_name} 不存在")

        weight = self.model_params[layer_name]

        # SVD分解
        U, S, Vt = np.linalg.svd(weight, full_matrices=False)

        # 截断到目标秩
        U_r = U[:, :rank]
        S_r = np.diag(S[:rank])
        V_r = Vt[:rank, :]

        # 分解为两个矩阵
        W1 = U_r @ np.sqrt(S_r)
        W2 = np.sqrt(S_r) @ V_r

        logger.info(f"📉 低秩分解: {layer_name} {weight.shape} → {W1.shape} + {W2.shape}")

        return W1, W2

    async def _evaluate_model(self, params: dict[str, np.ndarray]) -> float:
        """评估模型性能(简化版)"""
        # 简化版:基于参数范数估算性能
        total_norm = sum(np.linalg.norm(v) for v in params.values())
        # 模拟准确率(实际需要真实评估)
        return min(1.0, 0.8 + total_norm * 0.0001)

    async def _measure_inference_time(self, params: dict[str, np.ndarray]) -> float:
        """测量推理时间(简化版)"""
        # 简化版:基于参数量估算
        total_params = sum(v.size for v in params.values())
        # 假设每百万参数需要1ms
        return total_params / 1_000_000 * 1.0

    def _update_stats(self, result: CompressionResult) -> Any:
        """更新统计信息"""
        self.stats["total_compressions"] += 1
        n = self.stats["total_compressions"]

        self.stats["avg_compression_ratio"] = (
            self.stats["avg_compression_ratio"] * (n - 1) + result.compression_ratio
        ) / n
        self.stats["avg_accuracy_drop"] = (
            self.stats["avg_accuracy_drop"] * (n - 1) + result.accuracy_drop
        ) / n
        self.stats["avg_speedup"] = (self.stats["avg_speedup"] * (n - 1) + result.speedup) / n

    def get_status(self) -> dict[str, Any]:
        """获取系统状态"""
        return {
            "name": self.name,
            "version": self.version,
            "model_loaded": len(self.model_params) > 0,
            "model_size_mb": sum(v.nbytes for v in self.model_params.values()) / (1024 * 1024),
            "compression_count": self.stats["total_compressions"],
            "statistics": self.stats,
            "recent_results": [
                {
                    "method": r.method.value,
                    "compression_ratio": f"{r.compression_ratio:.2f}x",
                    "accuracy_drop": f"{r.accuracy_drop:.2%}",
                    "speedup": f"{r.speedup:.2f}x",
                }
                for r in self.compression_history[-5:]
            ],
        }


# 全局单例
_compression_instance: ModelCompressionSystem | None = None


def get_model_compression_system() -> ModelCompressionSystem:
    """获取模型压缩系统实例"""
    global _compression_instance
    if _compression_instance is None:
        _compression_instance = ModelCompressionSystem()
    return _compression_instance
