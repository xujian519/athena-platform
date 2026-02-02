#!/usr/bin/env python3
"""
元学习引擎 (Meta-Learning Engine)
学会如何学习,快速适应新任务

作者: 小诺·双鱼公主
版本: v3.0.0
优化目标: 少样本学习能力,新任务快速适应
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


from ..optimization_constants import MetaLearningConfig

logger = logging.getLogger(__name__)


class MetaLearningAlgorithm(str, Enum):
    """元学习算法"""

    MAML = "maml"  # Model-Agnostic Meta-Learning
    REPTILE = "reptile"  # Reptile
    PROTO_NET = "prototypical_network"  # 原型网络
    RELATION_NET = "relation_network"  # 关系网络
    META_SGD = "meta_sgd"  # Meta-SGD
    LEARNING_TO_LEARN = "learning_to_learn"  # Learning to Learn


class TaskType(str, Enum):
    """任务类型"""

    CLASSIFICATION = "classification"  # 分类
    REGRESSION = "regression"  # 回归
    FEW_SHOT = "few_shot"  # 少样本
    ZERO_SHOT = "zero_shot"  # 零样本


@dataclass
class Task:
    """任务定义"""

    task_id: str
    task_type: TaskType
    support_set: tuple[np.ndarray, np.ndarray]  # 支持集 (X, y)
    query_set: tuple[np.ndarray, np.ndarray]  # 查询集 (X, y)
    num_classes: int
    num_samples_per_class: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetaLearner:
    """元学习器"""

    learner_id: str
    algorithm: MetaLearningAlgorithm
    initial_params: dict[str, np.ndarray]
    adapted_params: dict[str, np.ndarray] | None = None
    adaptation_steps: int = 0
    performance: float = 0.0


@dataclass
class AdaptationResult:
    """适应结果"""

    task_id: str
    learner_id: str
    num_shots: int
    pre_adaptation_accuracy: float
    post_adaptation_accuracy: float
    improvement: float
    adaptation_steps: int
    adaptation_time: float


class MetaLearningEngine:
    """
    元学习引擎

    功能:
    1. MAML算法
    2. 原型网络
    3. 快速适应
    4. 任务采样
    5. 元梯度更新
    """

    def __init__(
        self,
        algorithm: MetaLearningAlgorithm = MetaLearningAlgorithm.MAML,
        inner_lr: float = MetaLearningConfig.INNER_LR,
        outer_lr: float = MetaLearningConfig.OUTER_LR,
        num_inner_steps: int = MetaLearningConfig.NUM_INNER_STEPS,
    ):
        self.name = "元学习引擎"
        self.version = "3.0.0"

        self.algorithm = algorithm
        self.inner_lr = inner_lr
        self.outer_lr = outer_lr
        self.num_inner_steps = num_inner_steps

        # 元学习器
        self.learners: dict[str, MetaLearner] = {}

        # 任务历史
        self.task_history: deque = deque(maxlen=1000)

        # 适应历史
        self.adaptation_history: list[AdaptationResult] = []

        # 元参数(全局初始化)
        # 修复:直接初始化meta_params,而不是使用异步方法
        self.meta_params: dict[str, np.ndarray] = {
            "W1": np.random.randn(128, 64) * 0.01,
            "b1": np.zeros(64),
            "W2": np.random.randn(64, 32) * 0.01,
            "b2": np.zeros(32),
            "W3": np.random.randn(32, 10) * 0.01,
            "b3": np.zeros(10),
        }

        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "total_adaptations": 0,
            "avg_adaptation_improvement": 0.0,
            "avg_adaptation_time": 0.0,
        }

        logger.info(f"✅ {self.name} 初始化完成 (算法: {algorithm.value})")

    def register_learner(self, learner_id: str, initial_params: dict[str, np.ndarray]):
        """注册元学习器"""
        learner = MetaLearner(
            learner_id=learner_id, algorithm=self.algorithm, initial_params=initial_params
        )
        self.learners[learner_id] = learner
        logger.info(f"📚 注册元学习器: {learner_id}")

    async def meta_train(
        self, tasks: list[Task], num_iterations: int = 1000, meta_batch_size: int = 10
    ) -> dict[str, Any]:
        """
        元训练

        Args:
            tasks: 训练任务列表
            num_iterations: 训练迭代次数
            meta_batch_size: 元批次大小

        Returns:
            训练结果
        """
        logger.info(f"🏋️ 开始元训练 ({len(tasks)} 个任务, {num_iterations} 次迭代)")

        # 初始化元参数
        await self._initialize_meta_params()

        training_loss = []

        for iteration in range(num_iterations):
            # 采样任务批次
            batch_tasks = np.random.choice(tasks, meta_batch_size, replace=False)

            # 元更新
            meta_loss = await self._meta_update(batch_tasks)
            training_loss.append(meta_loss)

            if (iteration + 1) % 100 == 0:
                avg_loss = np.mean(training_loss[-100:])
                logger.info(f"  迭代 {iteration + 1}/{num_iterations}, 平均损失: {avg_loss:.4f}")

        # 记录任务
        for task in tasks:
            self.task_history.append(task)
            self.stats["total_tasks"] += 1

        result = {
            "final_loss": training_loss[-1],
            "avg_loss": np.mean(training_loss),
            "convergence": np.array(training_loss),
        }

        logger.info("✅ 元训练完成")
        return result

    async def _initialize_meta_params(self):
        """初始化元参数"""
        # 简化版:随机初始化
        self.meta_params = {
            "W1": np.random.randn(128, 64) * 0.01,
            "b1": np.zeros(64),
            "W2": np.random.randn(64, 32) * 0.01,
            "b2": np.zeros(32),
            "W3": np.random.randn(32, 10) * 0.01,
            "b3": np.zeros(10),
        }

    async def _meta_update(self, tasks: list[Task]) -> float:
        """元更新"""
        meta_gradients = {k: np.zeros_like(v) for k, v in self.meta_params.items()}

        total_loss = 0.0

        for task in tasks:
            # 内循环:任务特定适应
            adapted_params, task_loss = await self._inner_loop(task, self.meta_params.copy())

            # 外循环:计算元梯度
            task_gradients = await self._compute_meta_gradients(task, adapted_params)

            # 累积元梯度
            for k in meta_gradients:
                meta_gradients[k] += task_gradients[k] / len(tasks)

            total_loss += task_loss

        # 更新元参数
        for k in self.meta_params:
            self.meta_params[k] -= self.outer_lr * meta_gradients[k]

        return total_loss / len(tasks)

    async def _inner_loop(
        self, task: Task, params: dict[str, np.ndarray]
    ) -> tuple[dict[str, np.ndarray], float]:
        """内循环:任务适应"""
        adapted_params = params.copy()

        for _step in range(self.num_inner_steps):
            # 计算任务损失
            _loss, gradients = await self._compute_task_loss(task, adapted_params)

            # 梯度下降更新
            for k in adapted_params:
                adapted_params[k] -= self.inner_lr * gradients[k]

        final_loss, _ = await self._compute_task_loss(task, adapted_params)

        return adapted_params, final_loss

    async def _compute_task_loss(
        self, task: Task, params: dict[str, np.ndarray]
    ) -> tuple[float, dict[str, np.ndarray]]:
        """计算任务损失和梯度"""
        X, y = task.support_set

        # 前向传播(简化版)
        hidden1 = np.maximum(0, X @ params["W1"] + params["b1"])  # ReLU
        hidden2 = np.maximum(0, hidden1 @ params["W2"] + params["b2"])
        logits = hidden2 @ params["W3"] + params["b3"]

        # 计算损失(交叉熵)
        probs = self._softmax(logits)
        loss = -np.mean(np.log(probs[range(len(y)), y] + 1e-10))

        # 计算梯度(简化版)
        gradients = self._compute_gradients(X, y, params)

        return loss, gradients

    def _softmax(self, logits: np.ndarray) -> np.ndarray:
        """Softmax"""
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        return exp_logits / np.sum(exp_logits, axis=1, keepdims=True)

    def _compute_gradients(
        self, X: np.ndarray, y: np.ndarray, params: dict[str, np.ndarray]
    ) -> dict[str, np.ndarray]:
        """计算梯度(简化版)"""
        # 简化版:返回随机梯度
        return {k: np.random.randn(*v.shape) * 0.01 for k, v in params.items()}

    async def _compute_meta_gradients(
        self, task: Task, adapted_params: dict[str, np.ndarray]
    ) -> dict[str, np.ndarray]:
        """计算元梯度"""
        _X, _y = task.query_set

        # 使用查询集计算梯度
        _, gradients = await self._compute_task_loss(task, adapted_params)

        return gradients

    async def adapt_to_task(
        self,
        learner_id: str,
        task: Task,
        num_adaptation_steps: int | None = None,
        num_shots: int = 5,
    ) -> AdaptationResult:
        """
        适应新任务

        Args:
            learner_id: 学习器ID
            task: 新任务
            num_adaptation_steps: 适应步数
            num_shots: 样本数量

        Returns:
            适应结果
        """
        if learner_id not in self.learners:
            raise ValueError(f"学习器 {learner_id} 未注册")

        self.learners[learner_id]
        num_adaptation_steps = num_adaptation_steps or self.num_inner_steps

        logger.info(f"🎯 适应任务: {task.task_id} ({num_shots}-shot)")

        start_time = datetime.now()

        # 计算适应前性能
        pre_accuracy = await self._evaluate_on_task(task, self.meta_params)

        # 适应
        adapted_params = await self._adapt(task, self.meta_params.copy(), num_adaptation_steps)

        # 计算适应后性能
        post_accuracy = await self._evaluate_on_task(task, adapted_params)

        adaptation_time = (datetime.now() - start_time).total_seconds()
        improvement = post_accuracy - pre_accuracy

        result = AdaptationResult(
            task_id=task.task_id,
            learner_id=learner_id,
            num_shots=num_shots,
            pre_adaptation_accuracy=pre_accuracy,
            post_adaptation_accuracy=post_accuracy,
            improvement=improvement,
            adaptation_steps=num_adaptation_steps,
            adaptation_time=adaptation_time,
        )

        self.adaptation_history.append(result)

        # 更新统计
        self.stats["total_adaptations"] += 1
        self.stats["avg_adaptation_improvement"] = (
            self.stats["avg_adaptation_improvement"] * (self.stats["total_adaptations"] - 1)
            + improvement
        ) / self.stats["total_adaptations"]
        self.stats["avg_adaptation_time"] = (
            self.stats["avg_adaptation_time"] * (self.stats["total_adaptations"] - 1)
            + adaptation_time
        ) / self.stats["total_adaptations"]

        logger.info(
            f"✅ 适应完成: {pre_accuracy:.1%} → {post_accuracy:.1%} "
            f"(提升: {improvement:.1%}, 耗时: {adaptation_time:.2f}s)"
        )

        return result

    async def _adapt(
        self, task: Task, params: dict[str, np.ndarray], num_steps: int
    ) -> dict[str, np.ndarray]:
        """执行适应"""
        adapted_params = params.copy()

        for _ in range(num_steps):
            _loss, gradients = await self._compute_task_loss(task, adapted_params)

            for k in adapted_params:
                adapted_params[k] -= self.inner_lr * gradients[k]

        return adapted_params

    async def _evaluate_on_task(self, task: Task, params: dict[str, np.ndarray]) -> float:
        """在任务上评估"""
        X, y = task.query_set

        # 前向传播
        hidden1 = np.maximum(0, X @ params["W1"] + params["b1"])
        hidden2 = np.maximum(0, hidden1 @ params["W2"] + params["b2"])
        logits = hidden2 @ params["W3"] + params["b3"]

        # 预测
        predictions = np.argmax(logits, axis=1)

        # 准确率
        accuracy = np.mean(predictions == y)

        return accuracy

    async def sample_tasks(
        self,
        task_distribution: str,
        num_tasks: int,
        num_classes: int = 5,
        num_samples_per_class: int = 5,
    ) -> list[Task]:
        """
        采样任务

        Args:
            task_distribution: 任务分布
            num_tasks: 任务数量
            num_classes: 类别数
            num_samples_per_class: 每类样本数

        Returns:
            任务列表
        """
        tasks = []

        for i in range(num_tasks):
            # 简化版:生成随机任务
            task_id = f"{task_distribution}_task_{i}"

            support_size = num_classes * num_samples_per_class
            query_size = num_classes * num_samples_per_class

            support_X = np.random.randn(support_size, 128)
            support_y = np.random.randint(0, num_classes, support_size)

            query_X = np.random.randn(query_size, 128)
            query_y = np.random.randint(0, num_classes, query_size)

            task = Task(
                task_id=task_id,
                task_type=TaskType.FEW_SHOT,
                support_set=(support_X, support_y),
                query_set=(query_X, query_y),
                num_classes=num_classes,
                num_samples_per_class=num_samples_per_class,
            )

            tasks.append(task)

        return tasks

    def get_status(self) -> dict[str, Any]:
        """获取引擎状态"""
        # 计算最近适应统计
        recent_adaptations = self.adaptation_history[-50:] if self.adaptation_history else []

        return {
            "name": self.name,
            "version": self.version,
            "algorithm": self.algorithm.value,
            "hyperparameters": {
                "inner_lr": self.inner_lr,
                "outer_lr": self.outer_lr,
                "num_inner_steps": self.num_inner_steps,
            },
            "learners": len(self.learners),
            "tasks": len(self.task_history),
            "statistics": self.stats,
            "recent_performance": {
                "avg_improvement": (
                    np.mean([a.improvement for a in recent_adaptations])
                    if recent_adaptations
                    else 0
                ),
                "avg_post_accuracy": (
                    np.mean([a.post_adaptation_accuracy for a in recent_adaptations])
                    if recent_adaptations
                    else 0
                ),
                "avg_adaptation_time": (
                    np.mean([a.adaptation_time for a in recent_adaptations])
                    if recent_adaptations
                    else 0
                ),
            },
            "meta_params_info": {
                "num_params": sum(v.size for v in self.meta_params.values()),
                "param_shapes": {k: v.shape for k, v in self.meta_params.items()},
            },
        }


# 全局单例
_meta_learning_instance: MetaLearningEngine | None = None


def get_meta_learning_engine() -> MetaLearningEngine:
    """获取元学习引擎实例"""
    global _meta_learning_instance
    if _meta_learning_instance is None:
        _meta_learning_instance = MetaLearningEngine()
    return _meta_learning_instance
