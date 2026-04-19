#!/usr/bin/env python3
from __future__ import annotations
"""
快速学习机制 - 优先级经验回放缓冲区
Rapid Learning - Prioritized Replay Buffer

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import logging

from config.numpy_compatibility import np

from .types import LearningExperience

logger = logging.getLogger(__name__)


class PrioritizedReplayBuffer:
    """优先级经验回放缓冲区

    基于TD误差的经验优先级存储和采样。
    """

    def __init__(self, capacity: int, alpha: float = 0.6):
        """初始化优先级经验回放缓冲区

        Args:
            capacity: 缓冲区容量
            alpha: 优先级指数
        """
        self.capacity = capacity
        self.alpha = alpha
        self.buffer: list[LearningExperience] = []
        self.priorities = np.zeros((capacity,), dtype=np.float32)
        self.position = 0
        self.epsilon = 1e-6

    def add(self, experience: LearningExperience, priority: float):
        """添加经验

        Args:
            experience: 学习经验
            priority: 优先级
        """
        max_priority = self.priorities.max() if self.buffer else 1.0

        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.position] = experience

        self.priorities[self.position] = max(priority, max_priority)
        self.position = (self.position + 1) % self.capacity

    def sample(
        self, batch_size: int, beta: float = 0.4
    ) -> tuple[list[LearningExperience], "np.ndarray", "np.ndarray"]:
        """采样经验

        Args:
            batch_size: 批次大小
            beta: 重要性采样指数

        Returns:
            (经验列表, 索引数组, 权重数组)
        """
        if len(self.buffer) == 0:
            return [], np.array([]), np.array([])

        # 计算采样概率
        priorities = self.priorities[: len(self.buffer)]
        probs = priorities**self.alpha
        probs /= probs.sum()

        # 采样索引
        indices = np.random.choice(len(self.buffer), batch_size, p=probs)
        samples = [self.buffer[i] for i in indices]

        # 计算重要性权重
        weights = (len(self.buffer) * probs[indices]) ** (-beta)
        weights /= weights.max()

        return samples, indices, weights

    def update_priorities(self, indices: np.ndarray, priorities: np.ndarray):
        """更新优先级

        Args:
            indices: 索引数组
            priorities: 优先级数组
        """
        for idx, priority in zip(indices, priorities, strict=False):
            self.priorities[idx] = priority + self.epsilon

    def __len__(self) -> int:
        """返回缓冲区大小"""
        return len(self.buffer)


__all__ = ["PrioritizedReplayBuffer"]
