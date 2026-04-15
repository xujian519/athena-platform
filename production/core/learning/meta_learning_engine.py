#!/usr/bin/env python3
"""
元学习引擎
Meta Learning Engine

实现"学会学习"的能力:
1. MAML (Model-Agnostic Meta-Learning)
2. 快速适应新任务
3. 少样本学习

作者: 小诺·双鱼公主
创建时间: 2026-01-01
版本: 1.0.0
"""
from __future__ import annotations
import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset


@runtime_checkable
class SizedDataset(Protocol):
    """定义Dataset的大小协议"""

    def __len__(self) -> int: ...  # type: ignore
    def __getitem__(self, idx: int) -> Any: ...  # type: ignore


logger = logging.getLogger(__name__)


class MetaAlgorithm(Enum):
    """元学习算法"""

    MAML = "maml"  # Model-Agnostic Meta-Learning
    FOMAML = "fomaml"  # First-Order MAML
    REPTILE = "reptile"  # Reptile (简化版MAML)
    PROTO_NET = "prototypical_network"  # 原型网络
    METASGD = "metasgd"  # Meta-SGD


@dataclass
class Task:
    """任务定义"""

    task_id: str
    name: str
    support_set: Dataset  # 支持集 (用于内层适应)
    query_set: Dataset  # 查询集 (用于外层评估)
    num_samples: int = 5  # 每类样本数 (k-shot)
    num_classes: int = 5  # 类别数 (n-way)


@dataclass
class MetaExperience:
    """元学习经验"""

    episode: int
    task_id: str
    support_loss: float
    query_loss: float
    adaptation_steps: int
    adapted_params: dict[str, torch.Tensor]
    timestamp: datetime = field(default_factory=datetime.now)


class MAMLEngine:
    """
    MAML元学习引擎

    实现:
    1. 内层循环: 快速适应特定任务
    2. 外层循环: 优化初始参数
    """

    def __init__(
        self,
        model: nn.Module,
        inner_lr: float = 0.01,
        meta_lr: float = 1e-3,
        inner_steps: int = 5,
        first_order: bool = False,
    ):
        """
        初始化MAML引擎

        Args:
            model: 基础模型
            inner_lr: 内层学习率
            meta_lr: 外层(元)学习率
            inner_steps: 内层适应步数
            first_order: 是否使用一阶近似(FOMAML)
        """
        self.model = model
        self.inner_lr = inner_lr
        self.meta_lr = meta_lr
        self.inner_steps = inner_steps
        self.first_order = first_order

        # 元优化器
        self.meta_optimizer = torch.optim.Adam(self.model.parameters(), lr=meta_lr)

        # 经验回放
        self.experience_buffer: list[MetaExperience] = []

        # 统计信息
        self.episode = 0
        self.best_meta_loss = float("inf")

        logger.info("🧠 MAML引擎初始化完成")
        logger.info(f"   内层学习率: {inner_lr}")
        logger.info(f"   元学习率: {meta_lr}")
        logger.info(f"   内层步数: {inner_steps}")
        logger.info(f"   一阶近似: {first_order}")

    def inner_loop(
        self, task: Task, keep_graph: bool = True
    ) -> tuple[dict[str, torch.Tensor], float]:
        """
        内层循环: 快速适应当前任务

        Args:
            task: 当前任务
            keep_graph: 是否保持计算图

        Returns:
            adapted_params: 适应后的参数
            support_loss: 支持集损失
        """
        # 复制当前参数
        params = {
            k: v.clone().detach().requires_grad_(True) for k, v in self.model.named_parameters()
        }

        # 创建支持集数据加载器
        support_loader = DataLoader(
            task.support_set, batch_size=len(task.support_set), shuffle=True  # type: ignore
        )

        # 获取支持集数据
        support_batch = next(iter(support_loader))

        # 初始化loss(防止循环未执行时未定义)
        loss = torch.tensor(0.0, requires_grad=True)

        # 内层适应
        for _step in range(self.inner_steps):
            # 使用适应后的参数进行前向传播(functional方式)
            with torch.set_grad_enabled(True):
                # 使用functional API,传入适应后的参数
                loss = self._compute_loss_with_params(self.model, support_batch, params)

                # 计算梯度(允许未使用的参数)
                grads = torch.autograd.grad(
                    loss,
                    params.values(),
                    create_graph=keep_graph and not self.first_order,
                    allow_unused=True,  # 允许某些参数未使用
                )

                # 只对有梯度的参数进行更新
                params = {
                    k: (v - self.inner_lr * g) if g is not None else v
                    for (k, v), g in zip(params.items(), grads, strict=False)
                }

        return params, loss.item()

    def outer_loop(self, tasks: list[Task], update: bool = True) -> float:
        """
        外层循环: 元学习

        Args:
            tasks: 任务批次
            update: 是否更新元参数

        Returns:
            meta_loss: 元损失
        """
        meta_loss = 0.0
        all_query_losses = []

        for task in tasks:
            # 1. 内层适应
            adapted_params, support_loss = self.inner_loop(task)

            # 2. 在查询集上评估(使用适应后的参数)
            query_loader = DataLoader(
                task.query_set, batch_size=len(task.query_set), shuffle=True  # type: ignore
            )
            query_batch = next(iter(query_loader))

            # 使用适应后的参数计算查询损失(关键修复)
            query_loss = self._compute_loss_with_params(self.model, query_batch, adapted_params)
            all_query_losses.append(query_loss.item())

            meta_loss += query_loss

            # 记录经验
            self.experience_buffer.append(
                MetaExperience(
                    episode=self.episode,
                    task_id=task.task_id,
                    support_loss=support_loss,
                    query_loss=query_loss.item(),
                    adaptation_steps=self.inner_steps,
                    adapted_params=adapted_params,
                )
            )

        # 平均元损失
        meta_loss = meta_loss / len(tasks) if tasks else torch.tensor(0.0, requires_grad=True)

        # 3. 元参数更新
        if update and tasks:
            self.meta_optimizer.zero_grad()
            # meta_loss是Tensor,可以调用backward()
            if isinstance(meta_loss, torch.Tensor):
                meta_loss.backward()
                self.meta_optimizer.step()

        # 更新统计
        self.episode += 1
        if isinstance(meta_loss, torch.Tensor):
            meta_loss_value = meta_loss.item()
        else:
            meta_loss_value = float(meta_loss)

        if meta_loss_value < self.best_meta_loss:
            self.best_meta_loss = meta_loss_value

        return meta_loss_value

    def fast_adapt(self, task: Task, num_steps: int | None = None) -> float:
        """
        快速适应新任务

        Args:
            task: 新任务
            num_steps: 适应步数 (默认使用inner_steps)

        Returns:
            query_loss: 查询集损失
        """
        num_steps = num_steps or self.inner_steps

        # 内层适应
        adapted_params, support_loss = self.inner_loop(task, keep_graph=False)

        # 在查询集上评估(使用适应后的参数)
        query_loader = DataLoader(task.query_set, batch_size=len(task.query_set))  # type: ignore
        query_batch = next(iter(query_loader))

        # 使用适应后的参数计算查询损失(关键修复)
        query_loss = self._compute_loss_with_params(self.model, query_batch, adapted_params)

        logger.info("🎯 快速适应完成")
        logger.info(f"   支持集损失: {support_loss:.4f}")
        logger.info(f"   查询集损失: {query_loss.item():.4f}")

        return query_loss.item()

    def _compute_loss(self, model: nn.Module, batch: Any) -> torch.Tensor:
        """
        计算损失 (需要根据具体任务实现)

        Args:
            model: 模型
            batch: 批次数据

        Returns:
            loss: 损失值
        """
        # 这里需要根据具体任务实现
        # 简化示例: 假设batch包含inputs和targets
        if isinstance(batch, (list, tuple)):
            inputs, targets = batch
        else:
            inputs = batch.get("inputs")
            targets = batch.get("targets")

        # 前向传播
        outputs = model(inputs)

        # 计算损失 (示例: MSE)
        if outputs.dim() > 1 and targets.dim() == 1:
            # 分类任务
            loss = F.cross_entropy(outputs, targets)
        else:
            # 回归任务
            loss = F.mse_loss(outputs, targets)

        return loss

    def _compute_loss_with_params(
        self, model: nn.Module, batch: Any, params: dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """
        使用指定参数计算损失(functional API)

        Args:
            model: 模型
            batch: 批次数据
            params: 参数字典

        Returns:
            loss: 损失值
        """
        # 这里需要根据具体任务实现
        # 简化示例: 假设batch包含inputs和targets
        if isinstance(batch, (list, tuple)):
            inputs, targets = batch
        else:
            inputs = batch.get("inputs")
            targets = batch.get("targets")

        # 使用functional API进行前向传播,使用adapted参数
        # 这是一个简化的实现,实际使用时需要更复杂的处理
        output = inputs
        for name, module in model.named_children():
            if isinstance(module, nn.Linear):
                # 获取该层的adapted参数
                weight_key = f"{name}.weight"
                bias_key = f"{name}.bias"

                weight = params.get(weight_key, module.weight)
                bias = params.get(bias_key, module.bias) if module.bias is not None else None

                # 使用adapted参数进行线性变换
                output = torch.nn.functional.linear(output, weight, bias)
            else:
                output = module(output)

        # 计算损失 (示例: CrossEntropy)
        if output.dim() > 1 and targets.dim() == 1:
            loss = F.cross_entropy(output, targets)
        else:
            loss = F.mse_loss(output, targets)

        return loss

    def save_checkpoint(self, path: str) -> None:
        """保存检查点"""
        checkpoint = {
            "episode": self.episode,
            "model_state_dict": self.model.state_dict(),
            "meta_optimizer_state_dict": self.meta_optimizer.state_dict(),
            "best_meta_loss": self.best_meta_loss,
            "experience_buffer": self.experience_buffer[-1000:],  # 保存最近1000个
        }

        torch.save(checkpoint, path)
        logger.info(f"💾 检查点已保存: {path}")

    def load_checkpoint(self, path: str) -> Any | None:
        """加载检查点"""
        # 使用weights_only=False以加载包含自定义类的检查点
        checkpoint = torch.load(path, map_location="cpu", weights_only=False)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.meta_optimizer.load_state_dict(checkpoint["meta_optimizer_state_dict"])
        self.episode = checkpoint["episode"]
        self.best_meta_loss = checkpoint["best_meta_loss"]
        self.experience_buffer = checkpoint.get("experience_buffer", [])

        logger.info(f"📂 检查点已加载: {path}")
        logger.info(f"   已训练episodes: {self.episode}")

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        if not self.experience_buffer:
            return {}

        recent = self.experience_buffer[-100:]

        return {
            "episode": self.episode,
            "best_meta_loss": self.best_meta_loss,
            "avg_support_loss": np.mean([e.support_loss for e in recent]),
            "avg_query_loss": np.mean([e.query_loss for e in recent]),
            "total_experiences": len(self.experience_buffer),
        }


class TaskSampler:
    """
    任务采样器

    用于元学习中的任务采样
    """

    def __init__(self, tasks: list[Task], batch_size: int = 4, shuffle: bool = True):
        """
        初始化任务采样器

        Args:
            tasks: 任务列表
            batch_size: 每批任务数
            shuffle: 是否打乱
        """
        self.tasks = tasks
        self.batch_size = batch_size
        self.shuffle = shuffle

    def sample(self) -> list[Task]:
        """采样一批任务"""
        if self.shuffle:
            return random.sample(self.tasks, self.batch_size)
        else:
            return self.tasks[: self.batch_size]

    def __len__(self):
        return len(self.tasks) // self.batch_size


class FewShotDataset(Dataset):
    """
    少样本数据集

    用于构建n-way k-shot任务
    """

    def __init__(self, dataset: Dataset, num_classes: int = 5, num_samples: int = 5):
        """
        初始化少样本数据集

        Args:
            dataset: 原始数据集
            num_classes: 类别数 (n-way)
            num_samples: 每类样本数 (k-shot)
        """
        self.dataset = dataset
        self.num_classes = num_classes
        self.num_samples = num_samples

        # 按类别组织数据
        self.class_indices = self._organize_by_class()

    def _organize_by_class(self) -> dict[int, list[int]]:
        """按类别组织索引"""
        class_indices = {}

        for idx, (_, label) in enumerate(self.dataset):  # type: ignore
            if label not in class_indices:
                class_indices[label] = []
            class_indices[label].append(idx)

        return class_indices

    def sample_task(self) -> Task:
        """
        采样一个任务

        Returns:
            Task: n-way k-shot任务
        """
        # 随机选择n个类
        classes = random.sample(list(self.class_indices.keys()), self.num_classes)

        # 为每个类选择k个样本
        support_indices = []
        query_indices = []

        for cls in classes:
            cls_indices = self.class_indices[cls]
            samples = random.sample(cls_indices, self.num_samples * 2)

            # 前k个作为支持集,后k个作为查询集
            support_indices.extend(samples[: self.num_samples])
            query_indices.extend(samples[self.num_samples :])

        # 创建支持集和查询集
        support_set = torch.utils.data.Subset(self.dataset, support_indices)
        query_set = torch.utils.data.Subset(self.dataset, query_indices)

        return Task(
            task_id=f"task_{random.randint(1000, 9999)}",
            name=f"{self.num_classes}-way {self.num_samples}-shot",
            support_set=support_set,
            query_set=query_set,
            num_samples=self.num_samples,
            num_classes=self.num_classes,
        )


# 导出
__all__ = ["FewShotDataset", "MAMLEngine", "MetaAlgorithm", "MetaExperience", "Task", "TaskSampler"]


# ==================== 使用示例 ====================

if __name__ == "__main__":

    async def main():
        """测试元学习引擎"""
        # 创建一个简单模型
        model = nn.Sequential(nn.Linear(10, 32), nn.ReLU(), nn.Linear(32, 5))

        # 创建MAML引擎
        maml = MAMLEngine(model=model, inner_lr=0.01, meta_lr=1e-3, inner_steps=5)

        print("✅ MAML引擎创建成功")
        print(f"   参数量: {sum(p.numel() for p in model.parameters())}")

        # 模拟元训练
        print("\n🔄 模拟元训练...")

        for episode in range(5):
            # 模拟外层循环
            meta_loss = maml.outer_loop([], update=False)  # 空任务列表用于测试

            print(f"Episode {episode + 1}: Meta Loss = {meta_loss:.4f}")

        # 获取统计
        stats = maml.get_statistics()
        print(f"\n📊 统计信息: {stats}")

    asyncio.run(main())


# =============================================================================
# === 元学习引擎别名 ===
# =============================================================================

# 为保持兼容性，提供 MetaLearningEngine 作为 MAMLEngine 的别名
MetaLearningEngine = MAMLEngine


__all__ = [
    "MetaAlgorithm",
    "TaskType",
    "MetaLearningResult",
    "MAMLEngine",
    "MetaLearningEngine",  # 别名
]
