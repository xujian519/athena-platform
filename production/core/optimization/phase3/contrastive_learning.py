#!/usr/bin/env python3
"""
对比学习模块 (Contrastive Learning Module)
学习相似和不相似的样本表示

作者: 小诺·双鱼公主
版本: v3.0.0
优化目标: 表征学习质量提升,迁移性能增强
"""

from __future__ import annotations
import logging
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

from ..optimization_constants import ContrastiveLearningConfig

logger = logging.getLogger(__name__)


class ContrastiveMethod(str, Enum):
    """对比学习方法"""

    SIMCLR = "simclr"  # SimCLR
    MOCO = "moco"  # MoCo
    BYOL = "byol"  # BYOL
    SIMSIAM = "simsiam"  # SimSiam
    CONTRASTIVE_MULTIVIEW = "contrastive_multiview"  # 多视图对比
    SUPERVISED_CONTRASTIVE = "supervised_contrastive"  # 监督对比


class AugmentationType(str, Enum):
    """数据增强类型"""

    CROP = "crop"  # 裁剪
    FLIP = "flip"  # 翻转
    ROTATE = "rotate"  # 旋转
    COLOR_JITTER = "color_jitter"  # 颜色抖动
    GAUSSIAN_BLUR = "gaussian_blur"  # 高斯模糊
    NOISE = "noise"  # 噪声


@dataclass
class Augmentation:
    """数据增强"""

    augmentation_type: AugmentationType
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContrastivePair:
    """对比样本对"""

    anchor: np.ndarray
    positive: np.ndarray
    negatives: list[np.ndarray]
    label: int | None = None


@dataclass
class EmbeddingResult:
    """嵌入结果"""

    embeddings: np.ndarray
    projections: np.ndarray
    labels: np.ndarray
    batch_size: int
    embedding_dim: int


@dataclass
class ContrastiveLoss:
    """对比损失"""

    loss: float
    accuracy: float  # 对比准确率
    pos_sim: float  # 正样本相似度
    neg_sim: float  # 负样本相似度


class ContrastiveLearningModule:
    """
    对比学习模块

    功能:
    1. 多种对比学习算法
    2. 数据增强策略
    3. 对比损失计算
    4. 表示学习
    5. 迁移学习
    """

    def __init__(
        self,
        method: ContrastiveMethod = ContrastiveMethod.SIMCLR,
        embedding_dim: int = ContrastiveLearningConfig.EMBEDDING_DIM,
        projection_dim: int = ContrastiveLearningConfig.PROJECTION_DIM,
        temperature: float = ContrastiveLearningConfig.TEMPERATURE,
    ):
        self.name = "对比学习模块"
        self.version = "3.0.0"

        self.method = method
        self.embedding_dim = embedding_dim
        self.projection_dim = projection_dim
        self.temperature = temperature

        # 编码器参数(简化版)
        self.encoder_params: dict[str, np.ndarray] = {}
        self.projection_params: dict[str, np.ndarray] = {}

        # 动量编码器(用于MoCo)
        self.momentum_encoder_params: dict[str, np.ndarray] = {}
        self.momentum = ContrastiveLearningConfig.MOMENTUM

        # 队列(用于MoCo)
        self.queue: deque = deque(maxlen=ContrastiveLearningConfig.QUEUE_SIZE)

        # 增强策略
        self.augmentations: list[Augmentation] = []

        # 训练历史
        self.loss_history: deque = deque(maxlen=1000)
        self.accuracy_history: deque = deque(maxlen=1000)

        # 统计信息
        self.stats = {
            "total_batches": 0,
            "avg_loss": 0.0,
            "avg_accuracy": 0.0,
            "best_accuracy": 0.0,
        }

        # 初始化参数
        self._initialize_parameters()

        logger.info(f"✅ {self.name} 初始化完成 (方法: {method.value})")

    def _initialize_parameters(self) -> Any:
        """初始化网络参数"""
        # 编码器
        self.encoder_params = {
            "W1": np.random.randn(256, self.embedding_dim) * 0.01,
            "b1": np.zeros(self.embedding_dim),
            "W2": np.random.randn(self.embedding_dim, self.embedding_dim // 2) * 0.01,
            "b2": np.zeros(self.embedding_dim // 2),
        }

        # 投影头
        self.projection_params = {
            "W1": np.random.randn(self.embedding_dim // 2, self.projection_dim) * 0.01,
            "b1": np.zeros(self.projection_dim),
        }

        # 动量编码器
        self.momentum_encoder_params = {k: v.copy() for k, v in self.encoder_params.items()}

    def set_augmentations(self, augmentations: list[Augmentation]) -> None:
        """设置数据增强策略"""
        self.augmentations = augmentations
        logger.info(f"📝 设置增强策略: {len(augmentations)} 种增强")

    async def encode(self, x: np.ndarray, use_momentum: bool = False) -> np.ndarray:
        """
        编码输入

        Args:
            x: 输入数据
            use_momentum: 是否使用动量编码器

        Returns:
            嵌入向量
        """
        params = self.momentum_encoder_params if use_momentum else self.encoder_params

        # 简化版:两层MLP
        hidden = np.maximum(0, x @ params["W1"] + params["b1"])  # ReLU
        embedding = hidden @ params["W2"] + params["b2"]

        return embedding

    async def project(self, embeddings: np.ndarray) -> np.ndarray:
        """
        投影嵌入

        Args:
            embeddings: 嵌入向量

        Returns:
            投影向量
        """
        hidden = np.maximum(
            0, embeddings @ self.projection_params["W1"] + self.projection_params["b1"]
        )
        # L2归一化
        projections = hidden / (np.linalg.norm(hidden, axis=1, keepdims=True) + 1e-8)
        return projections

    async def forward(self, x: np.ndarray, augment: bool = True) -> EmbeddingResult:
        """
        前向传播

        Args:
            x: 输入批次 (batch_size, input_dim)
            augment: 是否应用增强

        Returns:
            嵌入结果
        """
        batch_size = x.shape[0]

        # 应用增强
        if augment and self.augmentations:
            x = await self._apply_augmentation(x)

        # 编码
        embeddings = await self.encode(x)

        # 投影
        projections = await self.project(embeddings)

        # 简化版:生成虚拟标签
        labels = np.arange(batch_size) % 10

        return EmbeddingResult(
            embeddings=embeddings,
            projections=projections,
            labels=labels,
            batch_size=batch_size,
            embedding_dim=embeddings.shape[1],
        )

    async def _apply_augmentation(self, x: np.ndarray) -> np.ndarray:
        """应用数据增强"""
        augmented = x.copy()

        for aug in self.augmentations:
            if aug.augmentation_type == AugmentationType.NOISE:
                noise_level = aug.parameters.get("level", 0.1)
                augmented += np.random.randn(*augmented.shape) * noise_level

            # 其他增强类型...

        return augmented

    async def compute_contrastive_loss(
        self,
        projections1: np.ndarray,
        projections2: np.ndarray,
        labels: np.ndarray | None = None,
    ) -> ContrastiveLoss:
        """
        计算对比损失

        Args:
            projections1: 第一组投影 (batch_size, projection_dim)
            projections2: 第二组投影(正样本)
            labels: 标签(用于监督对比学习)

        Returns:
            对比损失
        """
        projections1.shape[0]

        if self.method == ContrastiveMethod.SIMCLR:
            loss, accuracy, pos_sim, neg_sim = await self._simclr_loss(projections1, projections2)
        elif self.method == ContrastiveMethod.MOCO:
            loss, accuracy, pos_sim, neg_sim = await self._moco_loss(projections1, projections2)
        elif self.method == ContrastiveMethod.BYOL:
            loss, accuracy, pos_sim, neg_sim = await self._byol_loss(projections1, projections2)
        elif self.method == ContrastiveMethod.SUPERVISED_CONTRASTIVE:
            if labels is None:
                raise ValueError("监督对比学习需要标签")
            loss, accuracy, pos_sim, neg_sim = await self._supervised_contrastive_loss(
                projections1, projections2, labels
            )
        else:
            loss, accuracy, pos_sim, neg_sim = await self._simclr_loss(projections1, projections2)

        return ContrastiveLoss(loss=loss, accuracy=accuracy, pos_sim=pos_sim, neg_sim=neg_sim)

    async def _simclr_loss(
        self, z1: np.ndarray, z2: np.ndarray
    ) -> tuple[float, float, float, float]:
        """SimCLR损失(NT-Xent)"""
        batch_size = z1.shape[0]

        # 拼接两个视角
        z = np.concatenate([z1, z2], axis=0)  # (2N, D)

        # 计算相似度矩阵
        sim_matrix = self._compute_similarity_matrix(z)  # (2N, 2N)

        # 创建标签(对角线为正样本)
        labels = np.arange(2 * batch_size)
        # 正样本在batch_size偏移处
        positives = np.roll(labels, batch_size)

        # 计算损失
        exp_sim = np.exp(sim_matrix / self.temperature)

        # 正样本相似度
        pos_sim = np.mean(np.diag(sim_matrix)[batch_size:])

        # 负样本相似度(排除自己)
        neg_sim = np.mean(sim_matrix[np.eye(2 * batch_size, dtype=bool) == 0])

        # NT-Xent损失
        num = np.diag(exp_sim, batch_size)
        num = np.concatenate([num, np.diag(exp_sim, -batch_size)])

        den = np.sum(exp_sim, axis=1) - np.diag(exp_sim)

        loss = -np.mean(np.log(num / (den + 1e-8) + 1e-8))

        # 对比准确率
        predictions = np.argmax(sim_matrix, axis=1)
        accuracy = np.mean(predictions == positives)

        return loss, accuracy, pos_sim, neg_sim

    async def _moco_loss(
        self, z_q: np.ndarray, z_k: np.ndarray
    ) -> tuple[float, float, float, float]:
        """MoCo损失"""
        batch_size = z_q.shape[0]

        # 正样本(来自动量编码器)
        pos_logits = np.sum(z_q * z_k, axis=1) / self.temperature

        # 负样本(来自队列)
        if len(self.queue) >= batch_size:
            neg_samples = np.array(list(self.queue)[-batch_size:])
            neg_logits = z_q @ neg_samples.T / self.temperature

            # 拼接
            logits = np.concatenate([pos_logits.reshape(-1, 1), neg_logits], axis=1)

            # 标签(正样本在第0位)
            labels = np.zeros(batch_size, dtype=int)

            # 交叉熵损失
            exp_logits = np.exp(logits)
            loss = -np.mean(
                np.log(
                    exp_logits[range(batch_size), labels] / (np.sum(exp_logits, axis=1) + 1e-8)
                    + 1e-8
                )
            )

            # 准确率
            predictions = np.argmax(logits, axis=1)
            accuracy = np.mean(predictions == labels)

            pos_sim = np.mean(pos_logits)
            neg_sim = np.mean(neg_logits)

        else:
            # 队列未满,使用简单损失
            loss = -np.mean(pos_logits)
            accuracy = 0.0
            pos_sim = np.mean(pos_logits)
            neg_sim = 0.0

        return loss, accuracy, pos_sim, neg_sim

    async def _byol_loss(
        self, z_online: np.ndarray, z_target: np.ndarray
    ) -> tuple[float, float, float, float]:
        """BYOL损失"""
        # L2归一化
        z_online = z_online / (np.linalg.norm(z_online, axis=1, keepdims=True) + 1e-8)
        z_target = z_target / (np.linalg.norm(z_target, axis=1, keepdims=True) + 1e-8)

        # 均方误差损失
        loss = 2 - 2 * np.sum(z_online * z_target, axis=1)

        # 简化准确率(基于余弦相似度)
        similarity = np.sum(z_online * z_target, axis=1)
        accuracy = np.mean(similarity > 0.5)

        pos_sim = np.mean(similarity)
        neg_sim = 0.0  # BYOL没有显式负样本

        return np.mean(loss), accuracy, pos_sim, neg_sim

    async def _supervised_contrastive_loss(
        self, z1: np.ndarray, z2: np.ndarray, labels: np.ndarray
    ) -> tuple[float, float, float, float]:
        """监督对比损失"""
        z1.shape[0]

        # 拼接两个增强
        z = np.concatenate([z1, z2], axis=0)
        labels_all = np.concatenate([labels, labels])

        # 计算相似度矩阵
        sim_matrix = self._compute_similarity_matrix(z)

        # 构建掩码(同类为正样本)
        label_mask = labels_all[:, None] == labels_all[None, :]

        # 排除自己
        np.fill_diagonal(label_mask, False)

        # 计算损失
        exp_sim = np.exp(sim_matrix / self.temperature)

        # 正样本
        pos_mask = label_mask
        pos_sim = np.sum(sim_matrix * pos_mask, axis=1) / (np.sum(pos_mask, axis=1) + 1e-8)

        # 负样本
        neg_mask = ~pos_mask
        neg_sim = np.sum(sim_matrix * neg_mask, axis=1) / (np.sum(neg_mask, axis=1) + 1e-8)

        # SupCon损失
        num = np.sum(exp_sim * pos_mask, axis=1)
        den = np.sum(exp_sim * neg_mask, axis=1)
        loss = -np.mean(np.log(num / (den + 1e-8) + 1e-8))

        # 准确率
        predictions = np.argmax(sim_matrix, axis=1)
        true_positives = np.sum(predictions * pos_mask, axis=1)
        accuracy = np.mean(true_positives > 0)

        return loss, accuracy, np.mean(pos_sim), np.mean(neg_sim)

    def _compute_similarity_matrix(self, z: np.ndarray) -> np.ndarray:
        """计算相似度矩阵"""
        # L2归一化
        z = z / (np.linalg.norm(z, axis=1, keepdims=True) + 1e-8)
        # 余弦相似度
        return z @ z.T

    async def update_momentum_encoder(self):
        """更新动量编码器"""
        for key in self.momentum_encoder_params:
            self.momentum_encoder_params[key] = (
                self.momentum * self.momentum_encoder_params[key]
                + (1 - self.momentum) * self.encoder_params[key]
            )

    async def update_queue(self, embeddings: np.ndarray):
        """更新队列"""
        for emb in embeddings:
            self.queue.append(emb.copy())

    def get_status(self) -> dict[str, Any]:
        """获取模块状态"""
        return {
            "name": self.name,
            "version": self.version,
            "method": self.method.value,
            "dimensions": {"embedding": self.embedding_dim, "projection": self.projection_dim},
            "statistics": self.stats,
            "recent_performance": {
                "avg_loss": np.mean(list(self.loss_history)) if self.loss_history else 0,
                "avg_accuracy": (
                    np.mean(list(self.accuracy_history)) if self.accuracy_history else 0
                ),
            },
            "queue_info": {"size": len(self.queue), "max_size": self.queue.maxlen},
            "augmentation_count": len(self.augmentations),
        }


# 全局单例
_contrastive_instance: ContrastiveLearningModule | None = None


def get_contrastive_learning_module() -> ContrastiveLearningModule:
    """获取对比学习模块实例"""
    global _contrastive_instance
    if _contrastive_instance is None:
        _contrastive_instance = ContrastiveLearningModule()
    return _contrastive_instance
