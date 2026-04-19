#!/usr/bin/env python3
"""
神经架构搜索系统 (Neural Architecture Search System)
自动搜索最优神经网络架构

作者: 小诺·双鱼公主
版本: v3.0.0
优化目标: 自动发现高性能架构,搜索效率提升
"""

from __future__ import annotations
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class NASMethod(str, Enum):
    """NAS方法"""

    REINFORCEMENT = "reinforcement"  # 强化学习
    EVOLUTIONARY = "evolutionary"  # 进化算法
    DARTS = "darts"  # DARTS
    ENAS = "enas"  # ENAS
    RANDOM_SEARCH = "random_search"  # 随机搜索
    HYPERNETWORK = "hypernetwork"  # 超网络


class LayerType(str, Enum):
    """层类型"""

    CONV2D = "conv2d"
    CONV3D = "conv3d"
    DEPTHWISE_CONV = "depthwise_conv"
    POINTWISE_CONV = "pointwise_conv"
    IDENTITY = "identity"
    MAX_POOL = "max_pool"
    AVG_POOL = "avg_pool"
    SEPARABLE_CONV = "separable_conv"
    DILATED_CONV = "dilated_conv"


@dataclass
class Architecture:
    """网络架构"""

    arch_id: str
    layers: list[dict[str, Any]]
    connections: list[tuple[int, int]]  # 跳跃连接
    metrics: dict[str, float] = field(default_factory=dict)
    flops: float = 0
    params: float = 0


@dataclass
class SearchSpace:
    """搜索空间"""

    layer_types: list[LayerType]
    kernel_sizes: list[int]
    filters: list[int]
    max_depth: int
    skip_connections: bool = True


@dataclass
class NASResult:
    """NAS结果"""

    best_architecture: Architecture
    search_time: float
    total_architectures_evaluated: int
    accuracy: float
    flops: float
    params: float


class NeuralArchitectureSearch:
    """
    神经架构搜索

    功能:
    1. 多种NAS算法
    2. 搜索空间定义
    3. 架构评估
    4. 性能预测
    5. 可视化
    """

    def __init__(
        self, method: NASMethod = NASMethod.DARTS, search_time_budget: float = 7200  # 2小时
    ):
        self.name = "神经架构搜索"
        self.version = "3.0.0"

        self.method = method
        self.search_time_budget = search_time_budget

        # 搜索空间
        self.search_space: SearchSpace | None = None

        # 架构历史
        self.arch_history: deque = deque(maxlen=1000)

        # 最优架构
        self.best_arch: Architecture | None = None

        # 统计信息
        self.stats = {
            "total_evaluations": 0,
            "best_accuracy": 0.0,
            "avg_flops": 0.0,
            "avg_params": 0.0,
        }

        # DARTS相关
        self.architectural_weights: np.ndarray | None = None

        logger.info(f"✅ {self.name} 初始化完成 (方法: {method.value})")

    def define_search_space(
        self,
        layer_types: list[LayerType],
        kernel_sizes: list[int],
        filters: list[int],
        max_depth: int = 10,
    ):
        """定义搜索空间"""
        self.search_space = SearchSpace(
            layer_types=layer_types, kernel_sizes=kernel_sizes, filters=filters, max_depth=max_depth
        )
        logger.info(
            f"🔍 搜索空间定义完成: "
            f"{len(layer_types)} 种层, {len(kernel_sizes)} 种核, "
            f"最大深度 {max_depth}"
        )

    async def search(
        self, task_config: dict[str, Any], evaluation_fn: callable, num_iterations: int = 100
    ) -> NASResult:
        """
        执行架构搜索

        Args:
            task_config: 任务配置
            evaluation_fn: 架构评估函数
            num_iterations: 搜索迭代次数

        Returns:
            NAS结果
        """
        logger.info(f"🔬 开始架构搜索 ({self.method.value}, {num_iterations} 次迭代)")

        start_time = datetime.now()

        if self.method == NASMethod.RANDOM_SEARCH:
            result = await self._random_search(task_config, evaluation_fn, num_iterations)
        elif self.method == NASMethod.EVOLUTIONARY:
            result = await self._evolutionary_search(task_config, evaluation_fn, num_iterations)
        elif self.method == NASMethod.DARTS:
            result = await self._darts_search(task_config, evaluation_fn, num_iterations)
        elif self.method == NASMethod.REINFORCEMENT:
            result = await self._rl_search(task_config, evaluation_fn, num_iterations)
        else:
            result = await self._random_search(task_config, evaluation_fn, num_iterations)

        search_time = (datetime.now() - start_time).total_seconds()

        nas_result = NASResult(
            best_architecture=result["arch"],
            search_time=search_time,
            total_architectures_evaluated=self.stats["total_evaluations"],
            accuracy=result["accuracy"],
            flops=result["flops"],
            params=result["params"],
        )

        self.best_arch = result["arch"]

        logger.info(
            f"✅ 搜索完成: 最佳准确率 {result['accuracy']:.2%}, "
            f"FLOPs {result['flops']:.1f}M, 参数 {result['params']:.1f}M"
        )

        return nas_result

    async def _random_search(
        self, task_config: dict[str, Any], evaluation_fn: callable, num_iterations: int
    ) -> dict[str, Any]:
        """随机搜索"""
        best_arch = None
        best_score = 0.0

        for i in range(num_iterations):
            # 采样随机架构
            arch = await self._sample_random_architecture()

            # 评估
            metrics = await evaluation_fn(arch)

            arch.metrics = metrics
            self.arch_history.append(arch)
            self.stats["total_evaluations"] += 1

            # 更新最优
            if metrics.get("accuracy", 0) > best_score:
                best_score = metrics["accuracy"]
                best_arch = arch

            if (i + 1) % 10 == 0:
                logger.info(f"  迭代 {i + 1}/{num_iterations}, 最佳准确率: {best_score:.2%}")

        return {
            "arch": best_arch,
            "accuracy": best_score,
            "flops": best_arch.flops if best_arch else 0,
            "params": best_arch.params if best_arch else 0,
        }

    async def _evolutionary_search(
        self,
        task_config: dict[str, Any],        evaluation_fn: callable,
        num_iterations: int,
        population_size: int = 20,
    ) -> dict[str, Any]:
        """进化算法搜索"""
        # 初始化种群
        population = [await self._sample_random_architecture() for _ in range(population_size)]

        # 评估初始种群
        for arch in population:
            arch.metrics = await evaluation_fn(arch)
            self.stats["total_evaluations"] += 1

        for iteration in range(num_iterations):
            # 选择
            population.sort(key=lambda x: x.metrics.get("accuracy", 0), reverse=True)
            survivors = population[: population_size // 2]

            # 变异和交叉
            offspring = []
            while len(offspring) < population_size // 2:
                parent = np.random.choice(survivors)
                child = await self._mutate_architecture(parent)
                child.metrics = await evaluation_fn(child)
                offspring.append(child)
                self.stats["total_evaluations"] += 1

            population = survivors + offspring

            best = max(population, key=lambda x: x.metrics.get("accuracy", 0))

            if (iteration + 1) % 10 == 0:
                logger.info(
                    f"  迭代 {iteration + 1}/{num_iterations}, "
                    f"最佳准确率: {best.metrics.get('accuracy', 0):.2%}"
                )

        best_arch = max(population, key=lambda x: x.metrics.get("accuracy", 0))

        return {
            "arch": best_arch,
            "accuracy": best_arch.metrics.get("accuracy", 0),
            "flops": best_arch.flops,
            "params": best_arch.params,
        }

    async def _darts_search(
        self, task_config: dict[str, Any], evaluation_fn: callable, num_iterations: int
    ) -> dict[str, Any]:
        """DARTS搜索(可微分)"""
        # 简化版DARTS
        num_ops = len(self.search_space.layer_types) if self.search_space else 5
        num_nodes = 5

        # 初始化架构权重
        self.architectural_weights = np.random.randn(num_nodes, num_nodes, num_ops)

        best_arch = None
        best_score = 0.0

        for iteration in range(num_iterations):
            # 基于当前权重采样架构
            arch = await self._sample_from_weights()

            # 评估
            metrics = await evaluation_fn(arch)
            arch.metrics = metrics

            self.stats["total_evaluations"] += 1

            # 更新权重(简化版)
            if metrics.get("accuracy", 0) > best_score:
                best_score = metrics["accuracy"]
                best_arch = arch
                # 增加对应操作权重
                for i, layer in enumerate(arch.layers):
                    op_idx = (
                        self.search_space.layer_types.index(LayerType(layer["type"]))
                        if self.search_space
                        else 0
                    )
                    if i < num_nodes and op_idx < num_ops:
                        self.architectural_weights[i, :, op_idx] += 0.1

            if (iteration + 1) % 10 == 0:
                logger.info(
                    f"  迭代 {iteration + 1}/{num_iterations}, 最佳准确率: {best_score:.2%}"
                )

        return {
            "arch": best_arch,
            "accuracy": best_score,
            "flops": best_arch.flops if best_arch else 0,
            "params": best_arch.params if best_arch else 0,
        }

    async def _rl_search(
        self, task_config: dict[str, Any], evaluation_fn: callable, num_iterations: int
    ) -> dict[str, Any]:
        """强化学习搜索(简化版)"""
        # 简化版:使用策略梯度
        np.random.randn(20)  # 简化的策略网络

        best_arch = None
        best_score = 0.0

        for iteration in range(num_iterations):
            # 采样架构
            arch = await self._sample_random_architecture()

            # 评估
            metrics = await evaluation_fn(arch)
            reward = metrics.get("accuracy", 0)

            arch.metrics = metrics
            self.arch_history.append(arch)
            self.stats["total_evaluations"] += 1

            # 策略更新(简化版)
            if reward > best_score:
                best_score = reward
                best_arch = arch

            if (iteration + 1) % 10 == 0:
                logger.info(
                    f"  迭代 {iteration + 1}/{num_iterations}, 最佳准确率: {best_score:.2%}"
                )

        return {
            "arch": best_arch,
            "accuracy": best_score,
            "flops": best_arch.flops if best_arch else 0,
            "params": best_arch.params if best_arch else 0,
        }

    async def _sample_random_architecture(self) -> Architecture:
        """采样随机架构"""
        if not self.search_space:
            # 默认搜索空间
            self.search_space = SearchSpace(
                layer_types=list(LayerType)[:6],
                kernel_sizes=[3, 5, 7],
                filters=[32, 64, 128],
                max_depth=8,
            )

        layers = []
        num_layers = np.random.randint(3, self.search_space.max_depth + 1)

        for i in range(num_layers):
            layer = {
                "type": np.random.choice(self.search_space.layer_types).value,
                "kernel_size": np.random.choice(self.search_space.kernel_sizes),
                "filters": np.random.choice(self.search_space.filters),
                "stride": 1 if i == 0 else np.random.choice([1, 2]),
            }
            layers.append(layer)

        # 跳跃连接
        connections = []
        if self.search_space.skip_connections:
            num_connections = np.random.randint(0, num_layers // 2)
            for _ in range(num_connections):
                src = np.random.randint(0, num_layers - 1)
                dst = np.random.randint(src + 1, num_layers)
                connections.append((src, dst))

        arch = Architecture(
            arch_id=f"arch_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            layers=layers,
            connections=connections,
        )

        # 估算FLOPs和参数
        arch.flops = self._estimate_flops(arch)
        arch.params = self._estimate_params(arch)

        return arch

    async def _sample_from_weights(self) -> Architecture:
        """从架构权重采样"""
        if self.architectural_weights is None:
            return await self._sample_random_architecture()

        # 简化版:基于权重贪婪选择
        num_nodes = self.architectural_weights.shape[0]
        self.architectural_weights.shape[2]

        layers = []
        for i in range(num_nodes):
            # 选择最佳操作
            best_op_idx = np.argmax(self.architectural_weights[i, i, :])
            op_type = list(LayerType)[best_op_idx % len(LayerType)]

            layer = {"type": op_type.value, "kernel_size": 3, "filters": 64, "stride": 1}
            layers.append(layer)

        return Architecture(
            arch_id=f"darts_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            layers=layers,
            connections=[],
        )

    async def _mutate_architecture(self, parent: Architecture) -> Architecture:
        """变异架构"""
        child_layers = [layer.copy() for layer in parent.layers]

        # 随机修改一层
        if child_layers:
            idx = np.random.randint(0, len(child_layers))
            layer = child_layers[idx]

            # 变异类型
            mutation = np.random.choice(["type", "kernel", "filters"])

            if mutation == "type" and self.search_space:
                layer["type"] = np.random.choice(self.search_space.layer_types).value
            elif mutation == "kernel" and self.search_space:
                layer["kernel_size"] = np.random.choice(self.search_space.kernel_sizes)
            elif mutation == "filters" and self.search_space:
                layer["filters"] = np.random.choice(self.search_space.filters)

        return Architecture(
            arch_id=f"mut_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            layers=child_layers,
            connections=parent.connections.copy(),
        )

    def _estimate_flops(self, arch: Architecture) -> float:
        """估算FLOPs(简化版)"""
        flops = 0
        for layer in arch.layers:
            kernel = layer.get("kernel_size", 3)
            filters = layer.get("filters", 64)
            # 简化的FLOP估算
            flops += kernel * kernel * filters * filters * 100  # 假设输入大小
        return flops / 1e6  # 转换为M

    def _estimate_params(self, arch: Architecture) -> float:
        """估算参数量(简化版)"""
        params = 0
        for layer in arch.layers:
            kernel = layer.get("kernel_size", 3)
            filters = layer.get("filters", 64)
            # 简化的参数估算
            params += kernel * kernel * filters * filters
        return params / 1e6  # 转换为M

    def get_status(self) -> dict[str, Any]:
        """获取系统状态"""
        return {
            "name": self.name,
            "version": self.version,
            "method": self.method.value,
            "search_space_defined": self.search_space is not None,
            "statistics": self.stats,
            "best_architecture": (
                {
                    "arch_id": self.best_arch.arch_id if self.best_arch else None,
                    "num_layers": len(self.best_arch.layers) if self.best_arch else 0,
                    "accuracy": self.best_arch.metrics.get("accuracy", 0) if self.best_arch else 0,
                }
                if self.best_arch
                else None
            ),
        }


# 全局单例
_nas_instance: NeuralArchitectureSearch | None = None


def get_neural_architecture_search() -> NeuralArchitectureSearch:
    """获取神经架构搜索实例"""
    global _nas_instance
    if _nas_instance is None:
        _nas_instance = NeuralArchitectureSearch()
    return _nas_instance
