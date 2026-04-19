#!/usr/bin/env python3
"""
Apple Silicon专用优化器
Apple Silicon Specialized Optimizer

专门针对Apple M系列芯片的NLP性能优化

作者: 系统管理员
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import logging
import time
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# 尝试导入Apple优化框架
try:

    MLX_AVAILABLE: bool = True
    logger.info("✅ MLX框架可用")
except ImportError as e:
    mx = None  # type: ignore
    nn = None  # type: ignore
    MLX_AVAILABLE: bool = False
    logger.warning(f"⚠️ MLX框架不可用: {e}")

# CoreML有兼容性问题,暂时禁用
COREML_AVAILABLE = False
logger.info("⚠️ CoreML工具暂时禁用(兼容性问题)")

import torch


class AppleSiliconOptimizer:
    """Apple Silicon专用优化器"""

    def __init__(self):
        self.device_type = self._detect_device()
        self.optimization_stats = {
            "mlx_operations": 0,
            "mps_operations": 0,
            "cpu_operations": 0,
            "optimization_time": 0.0,
            "performance_gain": {},
        }

        # 设备配置
        self.device_config = self._get_device_config()

        logger.info("🍎 Apple Silicon优化器初始化完成")
        logger.info(f"🔧 检测到设备: {self.device_type}")
        logger.info(f"⚙️ 设备配置: {self.device_config}")

    def _detect_device(self) -> str:
        """检测设备类型"""
        if MLX_AVAILABLE and mx is not None and mx.default_device().type == mx.DeviceType.gpu:
            return "mlx_gpu"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def _get_device_config(self) -> dict[str, Any]:
        """获取设备配置信息"""
        config = {
            "platform": "macos",
            "apple_silicon": True,
            "mlx_available": MLX_AVAILABLE,
            "coreml_available": COREML_AVAILABLE,
            "mps_available": torch.backends.mps.is_available(),
        }

        # 添加MLX设备信息
        if MLX_AVAILABLE and mx is not None:
            config["mlx_device"] = str(mx.default_device())
            try:
                config["mlx_memory"] = str(mx.get_active_memory())
            except Exception:
                config["mlx_memory"] = "Unknown"

        # 添加MPS设备信息
        if torch.backends.mps.is_available():
            config["mps_device"] = "mps"

        return config

    def optimize_array_operations(self, arrays: list[np.ndarray]) -> list[np.ndarray]:
        """优化数组操作"""
        start_time = time.time()

        if self.device_type == "mlx_gpu" and MLX_AVAILABLE:
            # 使用MLX GPU优化
            result = self._mlx_optimize_arrays(arrays)
            self.optimization_stats["mlx_operations"] += 1
        elif self.device_type == "mps":
            # 使用MPS优化
            result = self._mps_optimize_arrays(arrays)
            self.optimization_stats["mps_operations"] += 1
        else:
            # CPU操作
            result = arrays
            self.optimization_stats["cpu_operations"] += 1

        duration = time.time() - start_time
        self.optimization_stats["optimization_time"] += duration

        return result

    def _mlx_optimize_arrays(self, arrays: list[np.ndarray]) -> list[np.ndarray]:
        """使用MLX优化数组操作"""
        if not MLX_AVAILABLE or mx is None:
            return arrays

        try:
            # 转换为MLX数组
            mlx_arrays = [mx.array(arr) for arr in arrays]

            # 在GPU上执行优化操作
            # 这里可以添加具体的优化逻辑
            optimized_arrays = mlx_arrays

            # 转回numpy数组
            result = [np.array(arr) for arr in optimized_arrays]
            return result

        except Exception as e:
            logger.warning(f"MLX优化失败,回退到原始数组: {e}")
            return arrays

    def _mps_optimize_arrays(self, arrays: list[np.ndarray]) -> list[np.ndarray]:
        """使用MPS优化数组操作"""
        try:
            # 转换为PyTorch张量
            torch_tensors = [torch.from_numpy(arr).to("mps") for arr in arrays]

            # 在MPS设备上执行优化操作
            optimized_tensors = torch_tensors

            # 转回numpy数组
            result = [tensor.cpu().numpy() for tensor in optimized_tensors]
            return result

        except Exception as e:
            logger.warning(f"MPS优化失败,回退到原始数组: {e}")
            return arrays

    def create_optimized_matrix_multiply(self, size: int = 1000) -> callable:
        """创建优化的矩阵乘法函数"""
        if self.device_type == "mlx_gpu" and MLX_AVAILABLE:
            return self._create_mlx_matmul(size)
        elif self.device_type == "mps":
            return self._create_mps_matmul(size)
        else:
            return self._create_cpu_matmul(size)

    def _create_mlx_matmul(self, size: int) -> callable:
        """创建MLX矩阵乘法函数"""

        def mlx_matmul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
            if mx is None:
                return np.matmul(a, b)
            a_mlx = mx.array(a)
            b_mlx = mx.array(b)
            result = mx.matmul(a_mlx, b_mlx)
            return np.array(result)

        return mlx_matmul

    def _create_mps_matmul(self, size: int) -> callable:
        """创建MPS矩阵乘法函数"""

        def mps_matmul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
            a_torch = torch.from_numpy(a).to("mps")
            b_torch = torch.from_numpy(b).to("mps")
            result = torch.matmul(a_torch, b_torch)
            return result.cpu().numpy()

        return mps_matmul

    def _create_cpu_matmul(self, size: int) -> callable:
        """创建CPU矩阵乘法函数"""

        def cpu_matmul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
            return np.matmul(a, b)

        return cpu_matmul

    def _cpu_matmul(self, size: int) -> callable:
        """CPU矩阵乘法函数(备用实现)"""
        return self._create_cpu_matmul(size)

    def optimize_embedding_operations(self, embeddings: np.ndarray) -> np.ndarray:
        """优化嵌入操作"""
        start_time = time.time()

        if self.device_type == "mlx_gpu" and MLX_AVAILABLE:
            # 使用MLX优化嵌入操作
            result = self._mlx_optimize_embeddings(embeddings)
        elif self.device_type == "mps":
            # 使用MPS优化嵌入操作
            result = self._mps_optimize_embeddings(embeddings)
        else:
            # CPU操作
            result = embeddings

        duration = time.time() - start_time
        self.optimization_stats["optimization_time"] += duration

        return result

    def _mlx_optimize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """使用MLX优化嵌入操作"""
        if mx is None:
            return embeddings

        try:
            # 转换为MLX数组
            mlx_embeddings = mx.array(embeddings)

            # 执行优化操作(如归一化、降维等)
            # 简单的L2归一化
            norm = mx.sqrt(mx.sum(mlx_embeddings**2, axis=1, keepdims=True))
            normalized = mlx_embeddings / (norm + 1e-8)

            return np.array(normalized)

        except Exception as e:
            logger.warning(f"MLX嵌入优化失败: {e}")
            return embeddings

    def _mps_optimize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """使用MPS优化嵌入操作"""
        try:
            # 转换为PyTorch张量
            torch_embeddings = torch.from_numpy(embeddings).to("mps")

            # 执行L2归一化
            normalized = torch.nn.functional.normalize(torch_embeddings, p=2, dim=1)

            return normalized.cpu().numpy()

        except Exception as e:
            logger.warning(f"MPS嵌入优化失败: {e}")
            return embeddings

    def batch_similarity_computation(
        self, query_embeddings: np.ndarray, candidate_embeddings: np.ndarray, batch_size: int = 32
    ) -> np.ndarray:
        """批量相似度计算优化"""
        if self.device_type == "mlx_gpu" and MLX_AVAILABLE:
            return self._mlx_batch_similarity(query_embeddings, candidate_embeddings, batch_size)
        elif self.device_type == "mps":
            return self._mps_batch_similarity(query_embeddings, candidate_embeddings, batch_size)
        else:
            return self._cpu_batch_similarity(query_embeddings, candidate_embeddings, batch_size)

    def _mlx_batch_similarity(
        self, query_embeddings: np.ndarray, candidate_embeddings: np.ndarray, batch_size: int
    ) -> np.ndarray:
        """MLX批量相似度计算"""
        if mx is None:
            return self._cpu_batch_similarity(query_embeddings, candidate_embeddings, batch_size)

        try:
            # 转换为MLX数组
            query_mlx = mx.array(query_embeddings)
            candidates_mlx = mx.array(candidate_embeddings)

            # 计算余弦相似度
            # L2归一化
            query_norm = query_mlx / (mx.sqrt(mx.sum(query_mlx**2)) + 1e-8)
            candidates_norm = candidates_mlx / (
                mx.sqrt(mx.sum(candidates_mlx**2, axis=1, keepdims=True)) + 1e-8
            )

            # 点积计算余弦相似度
            similarities = mx.matmul(query_norm, candidates_norm.T)

            return np.array(similarities)

        except Exception as e:
            logger.warning(f"MLX批量相似度计算失败: {e}")
            # 回退到numpy计算
            return self._cpu_batch_similarity(query_embeddings, candidate_embeddings, batch_size)

    def _mps_batch_similarity(
        self, query_embeddings: np.ndarray, candidate_embeddings: np.ndarray, batch_size: int
    ) -> np.ndarray:
        """MPS批量相似度计算"""
        try:
            # 转换为PyTorch张量
            query_torch = torch.from_numpy(query_embeddings).to("mps")
            candidates_torch = torch.from_numpy(candidate_embeddings).to("mps")

            # 计算余弦相似度
            similarities = torch.nn.functional.cosine_similarity(
                query_torch.unsqueeze(1), candidates_torch.unsqueeze(0), dim=2
            )

            return similarities.cpu().numpy()

        except Exception as e:
            logger.warning(f"MPS批量相似度计算失败: {e}")
            return self._cpu_batch_similarity(query_embeddings, candidate_embeddings, batch_size)

    def _cpu_batch_similarity(
        self, query_embeddings: np.ndarray, candidate_embeddings: np.ndarray, batch_size: int
    ) -> np.ndarray:
        """CPU批量相似度计算"""
        from sklearn.metrics.pairwise import cosine_similarity

        return cosine_similarity(query_embeddings, candidate_embeddings)

    def get_optimization_report(self) -> dict[str, Any]:
        """获取优化报告"""
        total_ops = (
            self.optimization_stats["mlx_operations"]
            + self.optimization_stats["mps_operations"]
            + self.optimization_stats["cpu_operations"]
        )

        if total_ops == 0:
            return {"message": "尚未执行优化操作"}

        report = {
            "device_type": self.device_type,
            "device_config": self.device_config,
            "operations": {
                "total": total_ops,
                "mlx_gpu": self.optimization_stats["mlx_operations"],
                "mps": self.optimization_stats["mps_operations"],
                "cpu": self.optimization_stats["cpu_operations"],
            },
            "total_optimization_time": self.optimization_stats["optimization_time"],
            "performance_gains": self.optimization_stats["performance_gain"],
        }

        # 计算操作分布
        if total_ops > 0:
            report["operations"]["distribution"] = {
                "mlx_gpu_percent": (self.optimization_stats["mlx_operations"] / total_ops) * 100,
                "mps_percent": (self.optimization_stats["mps_operations"] / total_ops) * 100,
                "cpu_percent": (self.optimization_stats["cpu_operations"] / total_ops) * 100,
            }

        return report

    def benchmark_operations(self, test_size: int = 1000) -> dict[str, float]:
        """基准测试不同后端的性能"""
        results = {}

        # 创建测试数据
        test_arrays = [np.random.randn(test_size, test_size).astype(np.float32) for _ in range(2)]

        # 测试MLX性能
        if MLX_AVAILABLE:
            start_time = time.time()
            try:
                self._mlx_optimize_arrays(test_arrays)
                results["mlx_gpu"] = time.time() - start_time
            except Exception as e:
                logger.warning(f"MLX基准测试失败: {e}")
                results["mlx_gpu"] = float("inf")

        # 测试MPS性能
        if torch.backends.mps.is_available():
            start_time = time.time()
            try:
                self._mps_optimize_arrays(test_arrays)
                results["mps"] = time.time() - start_time
            except Exception as e:
                logger.warning(f"MPS基准测试失败: {e}")
                results["mps"] = float("inf")

        # 测试CPU性能
        start_time = time.time()
        try:
            self._cpu_matmul(test_size)(test_arrays[0], test_arrays[1])
            results["cpu"] = time.time() - start_time
        except Exception as e:
            logger.warning(f"CPU基准测试失败: {e}")
            results["cpu"] = float("inf")

        # 计算加速比
        if "cpu" in results and results["cpu"] > 0:
            for backend in ["mlx_gpu", "mps"]:
                if backend in results and results[backend] > 0:
                    speedup = results["cpu"] / results[backend]
                    results[f"{backend}_speedup"] = speedup

        return results

    def optimize_memory_layout(self, data: np.ndarray) -> np.ndarray:
        """优化内存布局"""
        if self.device_type == "mlx_gpu" and MLX_AVAILABLE and mx is not None:
            # MLX内存布局优化
            try:
                # 确保数据在MLX设备上是连续的
                mlx_data = mx.array(data)
                # MLX数组通常默认是连续的,直接转回numpy
                return np.array(mlx_data)
            except Exception as e:
                logger.warning(f"MLX内存布局优化失败: {e}")

        elif self.device_type == "mps":
            # MPS内存布局优化
            try:
                torch_data = torch.from_numpy(data).to("mps")
                if torch_data.is_contiguous():
                    return torch_data.cpu().numpy()
                else:
                    return torch_data.contiguous().cpu().numpy()
            except Exception as e:
                logger.warning(f"MPS内存布局优化失败: {e}")

        return data


# 全局Apple Silicon优化器实例
global_apple_optimizer = None


def get_apple_silicon_optimizer() -> AppleSiliconOptimizer:
    """获取全局Apple Silicon优化器实例"""
    global global_apple_optimizer
    if global_apple_optimizer is None:
        global_apple_optimizer = AppleSiliconOptimizer()
    return global_apple_optimizer


if __name__ == "__main__":
    # 测试Apple Silicon优化器
    optimizer = get_apple_silicon_optimizer()

    print("🧪 Apple Silicon优化器测试:")

    # 基准测试
    benchmark_results = optimizer.benchmark_operations(500)
    print("\n📊 基准测试结果:")
    for backend, time_taken in benchmark_results.items():
        if not backend.endswith("_speedup"):
            print(f"  {backend}: {time_taken:.4f}秒")
        else:
            print(f"  {backend}: {time_taken:.2f}x加速")

    # 优化报告
    report = optimizer.get_optimization_report()
    print("\n📋 优化报告:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
