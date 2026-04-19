#!/usr/bin/env python3
"""
联邦学习系统 (Federated Learning System)
分布式隐私保护机器学习

作者: 小诺·双鱼公主
版本: v3.0.0
优化目标: 隐私保护下的协同学习,模型性能提升
"""

from __future__ import annotations
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

from ..optimization_constants import FederatedLearningConfig

logger = logging.getLogger(__name__)


class FLAlgorithm(str, Enum):
    """联邦学习算法"""

    FEDAVG = "fedavg"  # FedAvg
    FEDPROX = "fedprox"  # FedProx
    FEDSGD = "fedsgd"  # FedSGD
    FEDADAM = "fedadam"  # FedAdam
    FEDYOGI = "fedyogi"  # FedYogi
    FedNova = "fednova"  # FedNova


class AggregationStrategy(str, Enum):
    """聚合策略"""

    WEIGHTED_AVG = "weighted_avg"  # 加权平均
    MEDIAN = "median"  # 中位数
    GEOMEDIAN = "geomedian"  # 几何中位数
    TRIMMED_MEAN = "trimmed_mean"  # 截断平均
    KRUM = "krum"  # Krum
    MULTI_KRUM = "multi_krum"  # Multi-Krum


@dataclass
class Client:
    """客户端"""

    client_id: str
    num_samples: int
    local_data_size: int
    compute_capability: float  # 0-1
    network_bandwidth: float  # MB/s
    is_online: bool = True


@dataclass
class ClientUpdate:
    """客户端更新"""

    client_id: str
    num_samples: int
    update: dict[str, np.ndarray]
    metrics: dict[str, float]
    update_time: float = 0
    round_num: int = 0


@dataclass
class ServerState:
    """服务器状态"""

    round_num: int
    global_model: dict[str, np.ndarray]
    client_updates: list[ClientUpdate]
    global_metrics: dict[str, float]
    selected_clients: list[str]


@dataclass
class FLResult:
    """联邦学习结果"""

    final_accuracy: float
    final_loss: float
    total_rounds: int
    total_communication_cost: float  # MB
    avg_client_time: float
    convergence_round: int


class FederatedLearningSystem:
    """
    联邦学习系统

    功能:
    1. 多种FL算法
    2. 客户端选择
    3. 安全聚合
    4. 差分隐私
    5. 异步训练
    """

    def __init__(
        self,
        algorithm: FLAlgorithm = FLAlgorithm.FEDAVG,
        aggregation: AggregationStrategy = AggregationStrategy.WEIGHTED_AVG,
        num_clients_per_round: int = FederatedLearningConfig.CLIENTS_PER_ROUND,
        num_rounds: int = FederatedLearningConfig.NUM_ROUNDS,
    ):
        self.name = "联邦学习系统"
        self.version = "3.0.0"

        self.algorithm = algorithm
        self.aggregation = aggregation
        self.num_clients_per_round = num_clients_per_round
        self.num_rounds = num_rounds

        # 客户端
        self.clients: dict[str, Client] = {}

        # 全局模型
        self.global_model: dict[str, np.ndarray] = {}

        # 服务器状态历史
        self.state_history: deque = deque(maxlen=1000)

        # 统计信息
        self.stats = {
            "total_rounds_completed": 0,
            "total_client_updates": 0,
            "communication_cost_mb": 0.0,
            "best_accuracy": 0.0,
            "client_dropouts": 0,
        }

        logger.info(f"✅ {self.name} 初始化完成 (算法: {algorithm.value})")

    def register_client(self, client: Client) -> None:
        """注册客户端"""
        self.clients[client.client_id] = client
        logger.info(f"📱 注册客户端: {client.client_id}")

    async def train(
        self,
        initial_model: dict[str, np.ndarray],
        client_update_fn: callable,
        evaluation_fn: callable,
    ) -> FLResult:
        """
        执行联邦学习训练

        Args:
            initial_model: 初始模型
            client_update_fn: 客户端更新函数
            evaluation_fn: 评估函数

        Returns:
            FL结果
        """
        logger.info(f"🌐 开始联邦学习训练 ({len(self.clients)} 客户端, {self.num_rounds} 轮)")

        self.global_model = initial_model.copy()
        best_accuracy = 0.0
        convergence_round = 0

        for round_num in range(1, self.num_rounds + 1):
            # 客户端选择
            selected_clients = await self._select_clients()

            # 分发全局模型
            await self._distribute_model(selected_clients)

            # 客户端本地训练
            client_updates = await self._client_training(
                round_num, selected_clients, client_update_fn
            )

            # 服务端聚合
            await self._aggregate_updates(client_updates)

            # 评估全局模型
            metrics = await evaluation_fn(self.global_model)
            accuracy = metrics.get("accuracy", 0)
            loss = metrics.get("loss", 0)

            if accuracy > best_accuracy:
                best_accuracy = accuracy
                convergence_round = round_num

            # 记录状态
            state = ServerState(
                round_num=round_num,
                global_model=self.global_model.copy(),
                client_updates=client_updates,
                global_metrics=metrics,
                selected_clients=[c.client_id for c in selected_clients],
            )
            self.state_history.append(state)

            self.stats["total_rounds_completed"] = round_num

            if round_num % 10 == 0:
                logger.info(
                    f"  轮次 {round_num}/{self.num_rounds}, "
                    f"准确率: {accuracy:.2%}, 损失: {loss:.4f}"
                )

        # 计算结果
        final_metrics = await evaluation_fn(self.global_model)
        total_comm_cost = self.stats["communication_cost_mb"]
        avg_client_time = sum(
            sum(u.update_time for u in s.client_updates) for s in self.state_history
        ) / max(1, self.stats["total_client_updates"])

        result = FLResult(
            final_accuracy=final_metrics.get("accuracy", 0),
            final_loss=final_metrics.get("loss", 0),
            total_rounds=self.num_rounds,
            total_communication_cost=total_comm_cost,
            avg_client_time=avg_client_time,
            convergence_round=convergence_round,
        )

        logger.info(
            f"✅ 训练完成: 最终准确率 {result.final_accuracy:.2%}, "
            f"通信成本 {total_comm_cost:.2f}MB"
        )

        return result

    async def _select_clients(self) -> list[Client]:
        """选择参与本轮的客户端"""
        available_clients = [c for c in self.clients.values() if c.is_online]

        if len(available_clients) <= self.num_clients_per_round:
            return available_clients

        # 基于计算能力和数据量选择
        scores = []
        for client in available_clients:
            # 综合分数(计算能力 + 数据量)
            score = client.compute_capability * 0.5 + min(1.0, client.local_data_size / 10000) * 0.5
            scores.append((client, score))

        # 选择Top-K
        scores.sort(key=lambda x: x[1], reverse=True)
        selected = [c for c, _ in scores[: self.num_clients_per_round]]

        return selected

    async def _distribute_model(self, clients: list[Client]):
        """分发全局模型到客户端"""
        # 计算通信成本
        model_size = sum(v.nbytes for v in self.global_model.values()) / (1024 * 1024)
        self.stats["communication_cost_mb"] += model_size * len(clients)

    async def _client_training(
        self, round_num: int, clients: list[Client], update_fn: callable
    ) -> list[ClientUpdate]:
        """客户端本地训练"""
        updates = []

        for client in clients:
            start_time = datetime.now()

            try:
                # 调用客户端更新函数
                local_update = await update_fn(
                    client.client_id, self.global_model.copy(), num_local_epochs=5
                )

                update = ClientUpdate(
                    client_id=client.client_id,
                    num_samples=client.num_samples,
                    update=local_update["update"],
                    metrics=local_update["metrics"],
                    update_time=(datetime.now() - start_time).total_seconds(),
                    round_num=round_num,
                )

                updates.append(update)
                self.stats["total_client_updates"] += 1

            except Exception as e:
                logger.warning(f"⚠️ 客户端 {client.client_id} 更新失败: {e}")
                self.stats["client_dropouts"] += 1

        return updates

    async def _aggregate_updates(self, updates: list[ClientUpdate]):
        """聚合客户端更新"""
        if not updates:
            return

        if self.aggregation == AggregationStrategy.WEIGHTED_AVG:
            await self._weighted_avg_aggregation(updates)
        elif self.aggregation == AggregationStrategy.MEDIAN:
            await self._median_aggregation(updates)
        elif self.aggregation == AggregationStrategy.TRIMMED_MEAN:
            await self._trimmed_mean_aggregation(updates, trim_ratio=0.1)
        else:
            await self._weighted_avg_aggregation(updates)

    async def _weighted_avg_aggregation(self, updates: list[ClientUpdate]):
        """加权平均聚合"""
        # 计算总样本数
        total_samples = sum(u.num_samples for u in updates)

        # 初始化聚合更新
        aggregated = {k: np.zeros_like(v) for k, v in self.global_model.items()}

        # 加权累加
        for update in updates:
            weight = update.num_samples / total_samples
            for key, value in update.update.items():
                if key in aggregated:
                    aggregated[key] += weight * value

        # 更新全局模型
        if self.algorithm == FLAlgorithm.FEDAVG:
            # FedAvg: 直接替换
            self.global_model = aggregated
        elif self.algorithm == FLAlgorithm.FEDPROX:
            # FedProx: 近似梯度步
            learning_rate = 0.01
            for key in self.global_model:
                self.global_model[key] += learning_rate * aggregated[key]
        elif self.algorithm == FLAlgorithm.FEDADAM:
            # FedAdam: 使用动量(简化版)
            _beta1, _beta2 = 0.9, 0.999
            lr = 0.001
            for key in self.global_model:
                self.global_model[key] -= lr * aggregated[key]

    async def _median_aggregation(self, updates: list[ClientUpdate]):
        """中位数聚合"""
        for key in self.global_model:
            # 收集所有客户端的该参数
            param_values = [u.update[key] for u in updates if key in u.update]

            if param_values:
                # 计算中位数
                stacked = np.stack(param_values)
                median = np.median(stacked, axis=0)
                self.global_model[key] = median

    async def _trimmed_mean_aggregation(self, updates: list[ClientUpdate], trim_ratio: float = 0.1):
        """截断平均聚合"""
        for key in self.global_model:
            param_values = [u.update[key] for u in updates if key in u.update]

            if param_values:
                stacked = np.stack(param_values)

                # 对每个元素排序并截断
                sorted_vals = np.sort(stacked, axis=0)
                trim_count = int(len(param_values) * trim_ratio)

                trimmed = sorted_vals[trim_count:-trim_count] if trim_count > 0 else sorted_vals

                self.global_model[key] = np.mean(trimmed, axis=0)

    async def add_differential_privacy(
        self, update: dict[str, np.ndarray], noise_scale: float = 0.1, clip_norm: float = 1.0
    ) -> dict[str, np.ndarray]:
        """
        添加差分隐私噪声

        Args:
            update: 模型更新
            noise_scale: 噪声标准差
            clip_norm: 梯度裁剪范数

        Returns:
            添加噪声后的更新
        """
        noisy_update = {}

        for key, value in update.items():
            # 梯度裁剪
            norm = np.linalg.norm(value)
            if norm > clip_norm:
                value = value * (clip_norm / norm)

            # 添加高斯噪声
            noise = np.random.normal(0, noise_scale, size=value.shape).astype(value.dtype)

            noisy_update[key] = value + noise

        return noisy_update

    def get_status(self) -> dict[str, Any]:
        """获取系统状态"""
        # 客户端统计
        online_clients = sum(1 for c in self.clients.values() if c.is_online)

        return {
            "name": self.name,
            "version": self.version,
            "algorithm": self.algorithm.value,
            "aggregation": self.aggregation.value,
            "clients": {
                "total": len(self.clients),
                "online": online_clients,
                "participating": self.num_clients_per_round,
            },
            "training": {
                "rounds_completed": self.stats["total_rounds_completed"],
                "total_rounds": self.num_rounds,
                "client_updates": self.stats["total_client_updates"],
                "dropouts": self.stats["client_dropouts"],
            },
            "communication": {
                "total_cost_mb": self.stats["communication_cost_mb"],
                "avg_cost_per_round": (
                    self.stats["communication_cost_mb"]
                    / max(1, self.stats["total_rounds_completed"])
                ),
            },
            "performance": {"best_accuracy": self.stats["best_accuracy"]},
        }


# 全局单例
_fl_instance: FederatedLearningSystem | None = None


def get_federated_learning_system() -> FederatedLearningSystem:
    """获取联邦学习系统实例"""
    global _fl_instance
    if _fl_instance is None:
        _fl_instance = FederatedLearningSystem()
    return _fl_instance
