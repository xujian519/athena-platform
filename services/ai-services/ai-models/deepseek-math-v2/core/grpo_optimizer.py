#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GRPO (Group Relative Policy Optimization) 核心实现
基于DeepSeekMath V2论文的无奖励强化学习算法
Athena智能工作平台专利分析专用优化器

作者: Athena AI团队
版本: 1.0.0
创建时间: 2025-11-28
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import json
from core.async_main import async_main
import logging
from core.logging_config import setup_logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class GRPOConfig:
    """GRPO算法配置"""

    group_size: int = 4  # 参考组大小
    learning_rate: float = 1e-5
    clip_ratio: float = 0.2
    value_loss_coef: float = 0.5
    entropy_coef: float = 0.01
    max_grad_norm: float = 0.5
    ppo_epochs: int = 4
    mini_batch_size: int = 32
    gamma: float = 0.99
    gae_lambda: float = 0.95
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu'


class ReferenceGroup:
    """参考组管理器 - GRPO的核心创新"""

    def __init__(self, group_size: int = 4):
        self.group_size = group_size
        self.policies = []
        self.rewards_history = []

    def create_reference_group(self, base_policy: nn.Module) -> List[nn.Module]:
        """创建参考组策略"""
        reference_policies = []

        for i in range(self.group_size):
            # 创建参考策略的副本
            ref_policy = type(base_policy)(**base_policy.__dict__).to(
                base_policy.device
            )

            # 添加轻微扰动
            self._add_policy_perturbation(ref_policy, i)
            reference_policies.append(ref_policy)

        return reference_policies

    def _add_policy_perturbation(self, policy: nn.Module, seed: int) -> Any:
        """为策略添加轻微扰动"""
        torch.manual_seed(seed)
        for param in policy.parameters():
            if param.requires_grad:
                noise = torch.randn_like(param) * 0.01
                param.data.add_(noise)

    def calculate_relative_advantages(
        self, current_rewards: List[float], reference_rewards: List[List[float]]
    ) -> List[float]:
        """计算相对优势估计 - GRPO的核心"""
        if not reference_rewards:
            return [0.0] * len(current_rewards)

        # 计算参考组平均奖励
        reference_mean = np.mean(reference_rewards)
        reference_std = np.std(reference_rewards) + 1e-8

        # 计算相对优势
        advantages = []
        for reward in current_rewards:
            relative_advantage = (reward - reference_mean) / reference_std
            advantages.append(relative_advantage)

        return advantages


class PatentGRPOOptimizer:
    """专利分析专用的GRPO优化器"""

    def __init__(self, policy_model: nn.Module, config: GRPOConfig = None):
        self.policy_model = policy_model
        self.config = config or GRPOConfig()
        self.reference_group = ReferenceGroup(self.config.group_size)
        self.optimizer = optim.Adam(
            policy_model.parameters(), lr=self.config.learning_rate
        )

        # 创建参考组
        self.reference_policies = self.reference_group.create_reference_group(
            policy_model
        )

        logger.info(f"GRPO优化器初始化完成 - 组大小: {self.config.group_size}")

    def optimize_step(
        self,
        states: List[Dict],
        actions: List[int],
        rewards: List[float],
        next_states: List[Dict] = None,
        dones: List[bool] = None,
    ) -> Dict[str, float]:
        """执行一次GRPO优化步骤"""

        # 1. 生成参考组策略的响应
        reference_rewards = self._generate_reference_responses(states, actions)

        # 2. 计算相对优势
        advantages = self.reference_group.calculate_relative_advantages(
            rewards, reference_rewards
        )

        # 3. PPO更新
        metrics = self._ppo_update(states, actions, advantages)

        return metrics

    def _generate_reference_responses(
        self, states: List[Dict], actions: List[int]
    ) -> List[List[float]]:
        """生成参考组策略的奖励"""
        reference_rewards = []

        for ref_policy in self.reference_policies:
            ref_policy.eval()
            rewards = []

            with torch.no_grad():
                for state, action in zip(states, actions):
                    # 使用参考策略计算奖励
                    state_tensor = self._state_to_tensor(state)
                    action_probs = ref_policy(state_tensor)
                    reward = self._calculate_patent_reward(action_probs, action)
                    rewards.append(reward.item())

            reference_rewards.append(rewards)

        return reference_rewards

    def _ppo_update(
        self, states: List[Dict], actions: List[int], advantages: List[float]
    ) -> Dict[str, float]:
        """PPO算法更新"""
        self.policy_model.train()

        # 转换为张量
        states_tensor = torch.stack([self._state_to_tensor(s) for s in states])
        actions_tensor = torch.tensor(actions, dtype=torch.long)
        advantages_tensor = torch.tensor(advantages, dtype=torch.float32)

        # 标准化优势
        advantages_tensor = (advantages_tensor - advantages_tensor.mean()) / (
            advantages_tensor.std() + 1e-8
        )

        total_policy_loss = 0
        total_entropy_loss = 0

        for _ in range(self.config.ppo_epochs):
            # 前向传播
            action_probs = self.policy_model(states_tensor)
            dist = torch.distributions.Categorical(action_probs)

            # 计算策略损失
            log_probs = dist.log_prob(actions_tensor)
            clipped_ratio = torch.clamp(
                torch.exp(log_probs - self._old_log_probs.detach()),
                1 - self.config.clip_ratio,
                1 + self.config.clip_ratio,
            )

            policy_loss = -torch.min(
                log_probs * advantages_tensor, clipped_ratio * advantages_tensor
            ).mean()

            # 熵损失
            entropy = dist.entropy().mean()
            entropy_loss = -self.config.entropy_coef * entropy

            # 总损失
            loss = policy_loss + entropy_loss

            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                self.policy_model.parameters(), self.config.max_grad_norm
            )
            self.optimizer.step()

            total_policy_loss += policy_loss.item()
            total_entropy_loss += entropy_loss.item()

        # 保存旧的log_probs用于下次更新
        with torch.no_grad():
            action_probs = self.policy_model(states_tensor)
            dist = torch.distributions.Categorical(action_probs)
            self._old_log_probs = dist.log_prob(actions_tensor)

        return {
            'policy_loss': total_policy_loss / self.config.ppo_epochs,
            'entropy_loss': total_entropy_loss / self.config.ppo_epochs,
            'avg_advantage': torch.mean(advantages_tensor).item(),
        }

    def _state_to_tensor(self, state: Dict) -> torch.Tensor:
        """将状态转换为张量"""
        # 这里需要根据具体的状态表示来实现
        # 示例实现：假设状态是专利特征向量
        if isinstance(state, dict):
            features = []
            for key, value in state.items():
                if isinstance(value, (int, float)):
                    features.append(value)
                elif isinstance(value, str):
                    # 文本特征需要转换为数值
                    features.append(hash(value) % 1000)
                elif isinstance(value, list):
                    features.extend([hash(str(x)) % 1000 for x in value[:10]])

            # 填充或截断到固定长度
            while len(features) < 512:  # 假设512维特征
                features.append(0.0)
            features = features[:512]

            return torch.tensor(
                features, dtype=torch.float32, device=self.config.device
            )
        else:
            # 简单的数值状态
            return torch.tensor([state], dtype=torch.float32, device=self.config.device)

    def _calculate_patent_reward(
        self, action_probs: torch.Tensor, action: int
    ) -> torch.Tensor:
        """计算专利分析奖励"""
        # 基于动作概率计算奖励
        prob = action_probs[action]
        # 添加专利特定的奖励计算逻辑
        reward = prob + 0.1 * torch.log(prob + 1e-8)  # 鼓励高置信度

        return reward

    def save_checkpoint(self, filepath: str) -> None:
        """保存模型检查点"""
        checkpoint = {
            'policy_model_state': self.policy_model.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'config': self.config,
            'timestamp': datetime.now().isoformat(),
        }
        torch.save(checkpoint, filepath)
        logger.info(f"GRPO检查点已保存: {filepath}")

    def load_checkpoint(self, filepath: str) -> Any | None:
        """加载模型检查点"""
        checkpoint = torch.load(filepath, map_location=self.config.device)
        self.policy_model.load_state_dict(checkpoint['policy_model_state'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state'])
        logger.info(f"GRPO检查点已加载: {filepath}")


class PatentPolicyNetwork(nn.Module):
    """专利分析策略网络"""

    def __init__(
        self,
        input_dim: int = 512,
        hidden_dim: int = 256,
        output_dim: int = 100,  # 专利分析动作数量
        num_layers: int = 3,
    ):
        super().__init__()

        layers = []
        current_dim = input_dim

        for i in range(num_layers):
            layers.extend(
                [nn.Linear(current_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.1)]
            )
            current_dim = hidden_dim
            hidden_dim = hidden_dim // 2

        layers.append(nn.Linear(current_dim, output_dim))
        layers.append(nn.Softmax(dim=-1))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


# 使用示例和测试代码
if __name__ == '__main__':
    # 配置
    config = GRPOConfig(group_size=4, learning_rate=1e-4, ppo_epochs=2)

    # 创建策略网络
    policy_net = PatentPolicyNetwork()

    # 创建GRPO优化器
    grpo_optimizer = PatentGRPOOptimizer(policy_net, config)

    # 模拟训练数据
    states = [
        {'patent_id': i, 'features': random((100)).tolist()} for i in range(10)
    ]
    actions = [np.random.randint(0, 100) for _ in range(10)]
    rewards = [np.random.random() for _ in range(10)]

    # 执行优化步骤
    metrics = grpo_optimizer.optimize_step(states, actions, rewards)

    logger.info('GRPO优化完成!')
    logger.info(f"策略损失: {metrics['policy_loss']:.4f}")
    logger.info(f"熵损失: {metrics['entropy_loss']:.4f}")
    logger.info(f"平均优势: {metrics['avg_advantage']:.4f}")

    # 保存模型
    grpo_optimizer.save_checkpoint('/tmp/patent_grpo_model.pth')
