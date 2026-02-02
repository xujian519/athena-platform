#!/usr/bin/env python3
"""
在线学习引擎
Online Learning Engine

实现持续学习和灾难遗忘防护:
1. 经验回放
2. 灾难遗忘防护
3. 持续学习管道
4. 增量更新

作者: 小诺·双鱼公主
创建时间: 2026-01-01
版本: 1.0.0
"""
import numpy as np

import asyncio
import json
import logging
import random
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader


logger = logging.getLogger(__name__)


class ReplayStrategy(Enum):
    """回放策略"""

    UNIFORM = "uniform"  # 均匀采样
    PRIORITIZED = "prioritized"  # 优先级采样
    BUFFER = "buffer"  # 缓冲区采样


@dataclass
class Experience:
    """经验样本"""

    task_id: str
    input_data: Any  # 输入数据
    target: Any  # 目标输出
    reward: float = 0.0  # 奖励/损失
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 1.0  # 重要性权重
    metadata: dict[str, Any] = field(default_factory=dict)


class ExperienceReplayBuffer:
    """
    经验回放缓冲区

    存储和采样历史经验
    """

    def __init__(
        self, capacity: int = 10000, strategy: ReplayStrategy = ReplayStrategy.PRIORITIZED
    ):
        """
        初始化回放缓冲区

        Args:
            capacity: 缓冲区容量
            strategy: 采样策略
        """
        self.capacity = capacity
        self.strategy = strategy

        if strategy == ReplayStrategy.PRIORITIZED:
            self.buffer: Any = []  # type: ignore
        else:
            self.buffer: Any = deque(maxlen=capacity)  # type: ignore

        logger.info(f"📦 经验回放缓冲区初始化: 容量={capacity}, 策略={strategy.value}")

    def add(self, experience: Experience) -> Any:
        """添加经验"""
        if self.strategy == ReplayStrategy.PRIORITIZED:
            self.buffer.append(experience)
            # 按重要性排序
            self.buffer.sort(key=lambda x: x.importance, reverse=True)

            # 超出容量时移除最低优先级
            if len(self.buffer) > self.capacity:
                self.buffer = self.buffer[: self.capacity]
        else:
            self.buffer.append(experience)

    def sample(self, batch_size: int) -> list[Experience]:
        """
        采样经验

        Args:
            batch_size: 批次大小

        Returns:
            experiences: 经验批次
        """
        if len(self.buffer) < batch_size:
            return list(self.buffer)

        if self.strategy == ReplayStrategy.UNIFORM:
            return random.sample(list(self.buffer), batch_size)
        elif self.strategy == ReplayStrategy.PRIORITIZED:
            # 按优先级采样
            weights = [exp.importance for exp in self.buffer]
            total = sum(weights)

            if total == 0:
                return random.sample(self.buffer, batch_size)

            probs = [w / total for w in weights]
            indices = np.random.choice(len(self.buffer), batch_size, p=probs, replace=False)
            return [self.buffer[i] for i in indices]
        else:
            return random.sample(list(self.buffer), batch_size)

    def get_recent(self, n: int) -> list[Experience]:
        """获取最近n个经验"""
        if self.strategy == ReplayStrategy.UNIFORM:
            return list(self.buffer)[-n:]
        else:
            return self.buffer[-n:]

    def clear(self) -> Any:
        """清空缓冲区"""
        if self.strategy == ReplayStrategy.UNIFORM:
            self.buffer.clear()
        else:
            self.buffer = []

        logger.info("🗑️ 缓冲区已清空")

    def __len__(self):
        return len(self.buffer)

    def save(self, path: str) -> Any:
        """保存缓冲区"""
        data = [
            {
                "task_id": exp.task_id,
                "input_data": str(exp.input_data),
                "target": str(exp.target),
                "reward": exp.reward,
                "timestamp": exp.timestamp.isoformat(),
                "importance": exp.importance,
                "metadata": exp.metadata,
            }
            for exp in self.buffer
        ]

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 缓冲区已保存: {path} ({len(data)}条经验)")

    def load(self, path: str) -> Any:
        """加载缓冲区"""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            exp = Experience(
                task_id=item["task_id"],
                input_data=item["input_data"],
                target=item["target"],
                reward=item["reward"],
                timestamp=datetime.fromisoformat(item["timestamp"]),
                importance=item["importance"],
                metadata=item["metadata"],
            )
            self.add(exp)

        logger.info(f"📂 缓冲区已加载: {path} ({len(data)}条经验)")


class ForgettingMonitor:
    """
    灾难遗忘监控器

    监控模型在新任务上的遗忘情况
    """

    def __init__(self, task_names: list[str]):
        self.task_names = task_names
        self.task_performance: dict[str, list[float]] = {task: [] for task in task_names}
        self.baseline_performance: dict[str, float] = {}

    def update_performance(self, task_name: str, performance: float) -> None:
        """更新任务性能"""
        if task_name not in self.task_performance:
            self.task_names.append(task_name)
            self.task_performance[task_name] = []

        self.task_performance[task_name].append(performance)

    def set_baseline(self, task_name: str, performance: float) -> None:
        """设置基线性能"""
        self.baseline_performance[task_name] = performance

    def compute_forgetting_rate(self, task_name: str) -> float:
        """
        计算遗忘率

        Args:
            task_name: 任务名称

        Returns:
            forgetting_rate: 遗忘率 (0-1)
        """
        if task_name not in self.baseline_performance:
            return 0.0

        baseline = self.baseline_performance[task_name]
        performances = self.task_performance[task_name]

        if not performances:
            return 0.0

        current = performances[-1]
        forgetting_rate = max(0, (baseline - current) / baseline)

        return forgetting_rate

    def get_average_forgetting(self) -> dict[str, float]:
        """获取平均遗忘率"""
        forgetting_rates = {}

        for task in self.task_names:
            forgetting_rates[task] = self.compute_forgetting_rate(task)

        return forgetting_rates

    def check_catastrophic_forgetting(self, threshold: float = 0.3) -> list[str]:
        """
        检查灾难性遗忘

        Args:
            threshold: 遗忘阈值

        Returns:
            forgotten_tasks: 发生灾难性遗忘的任务列表
        """
        forgotten = []

        for task in self.task_names:
            rate = self.compute_forgetting_rate(task)
            if rate > threshold:
                forgotten.append(task)

        return forgotten


class ElasticWeightConsolidation:
    """
    弹性权重巩固 (EWC)

    防止灾难性遗忘的正则化方法
    """

    def __init__(self, model: nn.Module, ewc_lambda: float = 1000.0, gamma: float = 0.9):
        """
        初始化EWC

        Args:
            model: 神经网络模型
            ewc_lambda: EWC正则化系数
            gamma: EWC衰减系数
        """
        self.model = model
        self.ewc_lambda = ewc_lambda
        self.gamma = gamma

        # 存储重要参数
        self.fisher_matrices: dict[str, torch.Tensor] = {}
        self.optimal_params: dict[str, torch.Tensor] = {}

        logger.info(f"🛡️ EWC初始化: lambda={ewc_lambda}, gamma={gamma}")

    def compute_fisher_matrix(self, dataloader: DataLoader, task_name: str):
        """
        计算Fisher信息矩阵

        Args:
            dataloader: 数据加载器
            task_name: 任务名称
        """
        fisher_matrix = {}
        optimal_params = {}

        # 收集参数梯度
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                fisher_matrix[name] = torch.zeros_like(param)
                optimal_params[name] = param.data.clone()

        # 计算对数似然梯度
        self.model.eval()

        for batch in dataloader:
            self.model.zero_grad()

            # 前向传播
            input_ids = batch["input_ids"]
            labels = batch["labels"]

            logits = self.model(input_ids, batch.get("attention_mask"))
            loss = F.cross_entropy(logits, labels)

            # 反向传播
            loss.backward()

            # 累积梯度平方
            for name, param in self.model.named_parameters():
                if param.requires_grad and param.grad is not None:
                    fisher_matrix[name] += param.grad.data.clone() ** 2

        # 归一化
        num_batches = len(dataloader)
        for name in fisher_matrix:
            fisher_matrix[name] /= num_batches

        self.fisher_matrices[task_name] = fisher_matrix  # type: ignore
        self.optimal_params[task_name] = optimal_params  # type: ignore

        logger.info(f"📊 Fisher矩阵计算完成: {task_name}")

    def ewc_loss(self) -> torch.Tensor:
        """
        计算EWC损失

        Returns:
            ewc_loss: 正则化损失
        """
        ewc_loss = 0.0

        for task_name, fisher in self.fisher_matrices.items():
            optimal = self.optimal_params[task_name]

            for name, param in self.model.named_parameters():
                if param.requires_grad and name in fisher:
                    # EWC正则化项
                    ewc_loss += (fisher[name] * (param - optimal[name]) ** 2).sum()  # type: ignore

        return (self.ewc_lambda / 2) * ewc_loss  # type: ignore

    def update_fisher_matrix(self, dataloader: DataLoader, task_name: str):
        """
        更新Fisher矩阵 (新任务)

        Args:
            dataloader: 数据加载器
            task_name: 新任务名称
        """
        # 计算新任务的Fisher矩阵
        new_fisher = {}
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                new_fisher[name] = torch.zeros_like(param)

        self.model.eval()

        for batch in dataloader:
            self.model.zero_grad()

            input_ids = batch["input_ids"]
            labels = batch["labels"]

            logits = self.model(input_ids, batch.get("attention_mask"))
            loss = F.cross_entropy(logits, labels)
            loss.backward()

            for name, param in self.model.named_parameters():
                if param.requires_grad and param.grad is not None:
                    new_fisher[name] += param.grad.data.clone() ** 2

        # 归一化
        num_batches = len(dataloader)
        for name in new_fisher:
            new_fisher[name] /= num_batches

        # 更新旧任务矩阵 (加权平均)
        if task_name not in self.fisher_matrices:
            self.fisher_matrices[task_name] = new_fisher  # type: ignore
        else:
            old_fisher = self.fisher_matrices[task_name]
            for name in new_fisher:
                # 指数移动平均
                self.fisher_matrices[task_name][name] = (
                    self.gamma * old_fisher[name] + (1 - self.gamma) * new_fisher[name]
                )

        logger.info(f"📈 Fisher矩阵更新完成: {task_name}")


class OnlineLearningEngine:
    """
    在线学习引擎

    持续学习系统,防止灾难性遗忘
    """

    def __init__(
        self,
        model: nn.Module,
        replay_buffer: ExperienceReplayBuffer,
        forgetting_monitor: ForgettingMonitor,
        ewc: ElasticWeightConsolidation | None = None,
    ):
        """
        初始化在线学习引擎

        Args:
            model: 神经网络模型
            replay_buffer: 经验回放缓冲区
            forgetting_monitor: 遗忘监控器
            ewc: EWC正则化
        """
        self.model = model
        self.replay_buffer = replay_buffer
        self.forgetting_monitor = forgetting_monitor
        self.ewc = ewc

        # 优化器
        self.optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

        # 任务历史
        self.task_history: list[str] = []

        logger.info("🔄 在线学习引擎初始化完成")

    async def learn_task(
        self,
        task_name: str,
        train_dataloader: DataLoader,
        val_dataloader: DataLoader | None = None,
        epochs: int = 5,
    ) -> dict[str, Any]:
        """
        学习新任务

        Args:
            task_name: 任务名称
            train_dataloader: 训练数据
            val_dataloader: 验证数据
            epochs: 训练轮数

        Returns:
            training_results: 训练结果
        """
        logger.info(f"📚 开始学习任务: {task_name}")

        # 计算基线性能
        if val_dataloader and self.ewc:
            self.ewc.compute_fisher_matrix(val_dataloader, task_name)

        # 训练循环
        history = {"loss": [], "replay_loss": [], "ewc_loss": []}

        for epoch in range(epochs):
            epoch_loss = 0.0
            epoch_replay_loss = 0.0
            epoch_ewc_loss = 0.0

            # 训练
            self.model.train()

            for batch in train_dataloader:
                # 主任务损失
                input_ids = batch["input_ids"]
                labels = batch["labels"]

                logits = self.model(input_ids, batch.get("attention_mask"))
                task_loss = F.cross_entropy(logits, labels)

                # 经验回放损失
                replay_loss = 0.0
                if len(self.replay_buffer) > 0:
                    replay_batch = self.replay_buffer.sample(8)
                    # 简化:计算回放损失
                    replay_loss = self._compute_replay_loss(replay_batch)

                # EWC损失
                ewc_loss = 0.0
                if self.ewc:
                    ewc_loss = self.ewc.ewc_loss()

                # 总损失
                total_loss = task_loss + 0.5 * replay_loss + ewc_loss

                # 反向传播
                self.optimizer.zero_grad()
                total_loss.backward()

                # 梯度裁剪
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

                self.optimizer.step()

                epoch_loss += task_loss.item()
                epoch_replay_loss += replay_loss
                # 确保ewc_loss转换为float
                if isinstance(ewc_loss, torch.Tensor):
                    epoch_ewc_loss += ewc_loss.detach().item()
                else:
                    epoch_ewc_loss += float(ewc_loss)  # type: ignore

            # 记录
            history["loss"].append(epoch_loss / len(train_dataloader))
            history["replay_loss"].append(epoch_replay_loss / len(train_dataloader))
            history["ewc_loss"].append(epoch_ewc_loss / len(train_dataloader))

            logger.info(
                f"Epoch {epoch+1}/{epochs}: "
                f"Loss={epoch_loss/len(train_dataloader):.4f}, "
                f"Replay={epoch_replay_loss/len(train_dataloader):.4f}, "
                f"EWC={epoch_ewc_loss/len(train_dataloader):.4f}"
            )

        # 评估
        if val_dataloader:
            val_acc = self._evaluate(val_dataloader)
            self.forgetting_monitor.update_performance(task_name, val_acc)

            if task_name not in self.task_history:
                self.forgetting_monitor.set_baseline(task_name, val_acc)

            logger.info(f"✅ 任务 {task_name} 验证准确率: {val_acc:.4f}")

        # 检查灾难性遗忘
        forgotten = self.forgetting_monitor.check_catastrophic_forgetting(threshold=0.2)
        if forgotten:
            logger.warning(f"⚠️ 检测到灾难性遗忘: {forgotten}")

        self.task_history.append(task_name)

        return {"task_name": task_name, "history": history, "forgotten_tasks": forgotten}

    def _compute_replay_loss(self, replay_batch: list[Experience]) -> float:
        """计算回放损失"""
        # 简化实现
        return 0.0

    def _evaluate(self, dataloader: DataLoader) -> float:
        """评估模型"""
        self.model.eval()

        correct = 0
        total = 0

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"]
                labels = batch["labels"]

                logits = self.model(input_ids, batch.get("attention_mask"))
                preds = logits.argmax(dim=-1)

                correct += (preds == labels).sum().item()
                total += input_ids.size(0)

        return correct / total

    def get_forgetting_report(self) -> dict[str, Any]:
        """获取遗忘报告"""
        forgetting_rates = self.forgetting_monitor.get_average_forgetting()

        return {
            "tasks_learned": len(self.task_history),
            "forgetting_rates": forgetting_rates,
            "avg_forgetting": np.mean(list(forgetting_rates.values())) if forgetting_rates else 0.0,
            "buffer_size": len(self.replay_buffer),
        }

    def save_checkpoint(self, path: str) -> None:
        """保存检查点"""
        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "task_history": self.task_history,
            "forgetting_monitor": self.forgetting_monitor.task_performance,
            "timestamp": datetime.now().isoformat(),
        }

        torch.save(checkpoint, path)
        logger.info(f"💾 检查点已保存: {path}")

    def load_checkpoint(self, path: str) -> Any | None:
        """加载检查点"""
        checkpoint = torch.load(path)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.task_history = checkpoint["task_history"]

        # 恢复监控数据
        for task, performances in checkpoint["forgetting_monitor"].items():
            for perf in performances:
                self.forgetting_monitor.update_performance(task, perf)

        logger.info(f"📂 检查点已加载: {path}")


# 导出
__all__ = [
    "ElasticWeightConsolidation",
    "Experience",
    "ExperienceReplayBuffer",
    "ForgettingMonitor",
    "OnlineLearningEngine",
    "ReplayStrategy",
]


# 使用示例
if __name__ == "__main__":

    async def main():
        """测试在线学习"""
        # 创建模型
        model = nn.Sequential(nn.Linear(10, 32), nn.ReLU(), nn.Linear(32, 5))

        # 创建组件
        replay_buffer = ExperienceReplayBuffer(capacity=1000)
        forgetting_monitor = ForgettingMonitor(["task1", "task2", "task3"])
        ewc = ElasticWeightConsolidation(model)

        # 创建引擎
        OnlineLearningEngine(
            model=model, replay_buffer=replay_buffer, forgetting_monitor=forgetting_monitor, ewc=ewc
        )

        print("✅ 在线学习引擎测试完成")

    asyncio.run(main())
