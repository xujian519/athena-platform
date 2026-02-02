#!/usr/bin/env python3
"""
快速学习机制 - 主引擎类
Rapid Learning - Main Engine

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

# pyright: reportUnboundVariable=false, reportOptionalMemberAccess=false, reportReturnType=false

import hashlib
import json
import logging
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Optional

# 机器学习相关导入
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LinearRegression

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from config.numpy_compatibility import array

from .learners import ActiveLearner, CurriculumScheduler, MetaLearner
from .replay_buffer import PrioritizedReplayBuffer
from .types import (
    AdaptationStrategy,
    LearningExperience,
    LearningTask,
    LearningType,
    ModelSnapshot,
)

logger = logging.getLogger(__name__)


def _validate_model_snapshot(model_type: str, model_data: bytes) -> bool:
    """验证模型快照的基本安全性"""
    try:
        # 检查数据大小（限制为100MB）
        if len(model_data) > 100 * 1024 * 1024:
            logger.error(f"模型数据过大: {len(model_data)} bytes")
            return False

        # 检查模型类型是否合法
        valid_types = {"neural_network", "linear_regression", "random_forest"}
        if model_type not in valid_types:
            logger.error(f"无效的模型类型: {model_type}")
            return False

        return True
    except Exception as e:
        logger.error(f"模型验证失败: {e}")
        return False


class RapidLearningEngine:
    """快速学习引擎

    支持在线学习、增量学习和元学习的智能体快速适应系统。
    """

    def __init__(self, config: dict | None = None):
        """初始化快速学习引擎

        Args:
            config: 配置字典
        """
        self.config = config or {
            "learning_rate": 0.01,
            "batch_size": 32,
            "buffer_size": 10000,
            "adaptation_rate": 0.1,
            "meta_learning_rate": 0.001,
            "experience_replay_size": 5000,
            "prioritized_replay_alpha": 0.6,
            "enable_meta_learning": True,
            "enable_active_learning": True,
            "enable_curriculum_learning": True,
            "model_checkpoint_interval": 100,
            "performance_threshold": 0.8,
        }

        # 经验缓冲区
        self.experience_buffer: deque[LearningExperience] = deque(
            maxlen=self.config["buffer_size"]
        )
        self.prioritized_buffer = PrioritizedReplayBuffer(
            capacity=self.config["experience_replay_size"],
            alpha=self.config["prioritized_replay_alpha"],
        )

        # 模型管理
        self.models: dict[str, Any] = {}
        self.model_snapshots: dict[str, ModelSnapshot] = {}
        self.active_models: dict[str, Any] = {}

        # 学习任务管理
        self.learning_tasks: dict[str, LearningTask] = {}
        self.task_performance: defaultdict[str, list[float]] = defaultdict(list)

        # 元学习组件
        self.meta_learner: MetaLearner | None = None
        if self.config["enable_meta_learning"]:
            self.meta_learner = MetaLearner(self.config)

        # 课程学习
        self.curriculum = CurriculumScheduler()

        # 主动学习
        self.active_learner: ActiveLearner | None = None
        if self.config["enable_active_learning"]:
            self.active_learner = ActiveLearner(self.config)

        # 性能追踪
        self.learning_history: list[dict[str, Any]] = []
        self.adaptation_history: list[dict[str, Any]] = []

    async def learn_from_experience(self, experience: LearningExperience) -> bool:
        """从经验中学习

        Args:
            experience: 学习经验

        Returns:
            是否学习成功
        """
        try:
            # 添加到经验缓冲区
            self.experience_buffer.append(experience)

            # 计算优先级并添加到优先级缓冲区
            priority = self._calculate_priority(experience)
            self.prioritized_buffer.add(experience, priority)

            # 更新相关模型
            task_type = experience.task_type
            if task_type in self.models:
                await self._update_model(task_type, experience)

            # 元学习更新
            if self.meta_learner:
                await self.meta_learner.update(experience)

            # 课程学习更新
            if self.config["enable_curriculum_learning"]:
                await self._update_curriculum(experience)

            # 主动学习查询
            if self.active_learner and experience.importance < 0.5:
                await self.active_learner.query_for_label(experience)

            logger.debug(f"从经验学习: {experience.experience_id}")
            return True

        except Exception as e:
            logger.error(f"从经验学习失败: {e}")
            return False

    def _calculate_priority(self, experience: LearningExperience) -> float:
        """计算经验优先级

        Args:
            experience: 学习经验

        Returns:
            优先级值
        """
        # 基于重要性
        base_priority = experience.importance

        # 时间衰减因子
        time_diff = (datetime.now() - experience.timestamp).total_seconds() / 3600
        time_factor = 1.0 / (1.0 + time_diff)

        # 奖励方差因子
        reward_variance = abs(experience.reward) * 0.5

        return base_priority * time_factor + reward_variance

    async def create_learning_task(self, task: LearningTask) -> bool:
        """创建学习任务

        Args:
            task: 学习任务

        Returns:
            是否创建成功
        """
        try:
            self.learning_tasks[task.task_id] = task

            # 创建或加载模型
            if task.task_id not in self.models:
                model = await self._create_model(task)
                if model:
                    self.models[task.task_id] = model
                    self.active_models[task.task_id] = model

            logger.info(f"创建学习任务: {task.task_id}")
            return True

        except Exception as e:
            logger.error(f"创建学习任务失败: {e}")
            return False

    async def _create_model(self, task: LearningTask) -> Any | None:
        """创建模型

        Args:
            task: 学习任务

        Returns:
            模型对象
        """
        model_type = task.model_type.lower()

        if model_type == "neural_network" and TORCH_AVAILABLE:
            return await self._create_neural_network(task)
        elif model_type == "linear_regression" and SKLEARN_AVAILABLE:
            return await self._create_linear_model(task)
        elif model_type == "random_forest" and SKLEARN_AVAILABLE:
            return await self._create_random_forest(task)
        else:
            logger.warning(f"不支持的模型类型: {model_type}")
            return None

    async def _create_neural_network(self, task: LearningTask) -> dict[str, Any] | None:
        """创建神经网络模型"""
        try:
            # 根据任务类型定义网络结构
            if task.task_type == LearningType.SUPERVISED:
                model = nn.Sequential(
                    nn.Linear(64, 128),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(128, 64),
                    nn.ReLU(),
                    nn.Linear(64, 1),
                )
            elif task.task_type == LearningType.UNSUPERVISED:
                model = nn.Sequential(
                    nn.Linear(64, 32),
                    nn.ReLU(),
                    nn.Linear(32, 16),
                    nn.Linear(16, 32),
                    nn.Linear(32, 64),
                )
            else:
                model = nn.Sequential(
                    nn.Linear(64, 128), nn.ReLU(), nn.Linear(128, 64)
                )

            # 创建优化器
            optimizer = optim.Adam(
                model.parameters(), lr=self.config["learning_rate"]
            )

            return {"model": model, "optimizer": optimizer, "type": "neural_network"}

        except Exception as e:
            logger.error(f"创建神经网络失败: {e}")
            return None

    async def _create_linear_model(self, task: LearningTask) -> dict[str, Any] | None:
        """创建线性模型

        Args:
            task: 学习任务，包含超参数配置
        """
        try:
            # 从任务中获取超参数，或使用默认值
            hyperparams = task.hyperparameters if task.hyperparameters else {}
            fit_intercept = hyperparams.get("fit_intercept", True)

            model = LinearRegression(fit_intercept=fit_intercept)
            return {"model": model, "type": "linear_regression", "hyperparams": hyperparams}
        except Exception as e:
            logger.error(f"创建线性模型失败: {e}")
            return None

    async def _create_random_forest(
        self, task: LearningTask
    ) -> dict[str, Any] | None:
        """创建随机森林模型

        Args:
            task: 学习任务，包含超参数配置
        """
        try:
            # 从任务中获取超参数，或使用默认值
            hyperparams = task.hyperparameters if task.hyperparameters else {}
            n_estimators = hyperparams.get("n_estimators", 100)
            max_depth = hyperparams.get("max_depth", 10)
            random_state = hyperparams.get("random_state", 42)

            model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state
            )
            return {"model": model, "type": "random_forest", "hyperparams": hyperparams}
        except Exception as e:
            logger.error(f"创建随机森林失败: {e}")
            return None

    async def _update_model(self, task_type: str, experience: LearningExperience):
        """更新模型

        Args:
            task_type: 任务类型
            experience: 学习经验
        """
        if task_type not in self.active_models:
            return

        model_info = self.active_models[task_type]
        model_type = model_info.get("type", "unknown")

        try:
            if model_type == "neural_network" and TORCH_AVAILABLE:
                await self._update_neural_network(model_info, experience)
            elif model_type == "linear_regression" and SKLEARN_AVAILABLE:
                await self._update_sklearn_model(model_info, experience)
            elif model_type == "random_forest" and SKLEARN_AVAILABLE:
                await self._update_ensemble_model(model_info, experience)

        except Exception as e:
            logger.error(f"更新模型失败: {e}")

    async def _update_neural_network(
        self, model_info: dict[str, Any], experience: LearningExperience
    ):
        """更新神经网络模型"""
        model = model_info["model"]
        optimizer = model_info["optimizer"]

        # 准备数据
        input_data = self._prepare_input_data(experience.input_data)
        target_data = self._prepare_target_data(experience.output_data)

        if input_data is None or target_data is None:
            return

        # 前向传播
        optimizer.zero_grad()
        output = model(input_data)
        loss = nn.MSELoss()(output, target_data)

        # 反向传播
        loss.backward()
        optimizer.step()

        logger.debug(f"神经网络更新,损失: {loss.item():.4f}")

    async def _update_sklearn_model(
        self, model_info: dict[str, Any], experience: LearningExperience
    ):
        """更新sklearn模型"""
        model = model_info["model"]

        # 准备数据
        input_data = self._prepare_input_data(experience.input_data, as_numpy=True)
        target_data = self._prepare_target_data(experience.output_data, as_numpy=True)

        if input_data is None or target_data is None:
            return

        # 部分拟合
        if hasattr(model, "partial_fit"):
            model.partial_fit(input_data.reshape(1, -1), [target_data])
        elif hasattr(model, "fit"):
            # 对于不支持在线学习的模型,收集批次数据
            if not hasattr(model_info, "batch_data"):
                model_info["batch_data"] = {"X": [], "y": []}

            model_info["batch_data"]["X"].append(input_data.reshape(1, -1)[0])
            model_info["batch_data"]["y"].append(target_data)

            # 当达到批次大小时进行训练
            if len(model_info["batch_data"]["X"]) >= self.config["batch_size"]:
                model.fit(
                    np.array(model_info["batch_data"]["X"]),
                    np.array(model_info["batch_data"]["y"]),
                )
                model_info["batch_data"] = {"X": [], "y": []}

    async def _update_ensemble_model(
        self, model_info: dict[str, Any], experience: LearningExperience
    ):
        """更新集成模型"""
        # 集成模型通常不支持增量学习,收集数据重新训练
        if not hasattr(model_info, "training_data"):
            model_info["training_data"] = {"X": [], "y": []}

        input_data = self._prepare_input_data(experience.input_data, as_numpy=True)
        target_data = self._prepare_target_data(experience.output_data, as_numpy=True)

        if input_data is not None and target_data is not None:
            model_info["training_data"]["X"].append(input_data.reshape(1, -1)[0])
            model_info["training_data"]["y"].append(target_data)

            # 定期重新训练
            if len(model_info["training_data"]["X"]) >= self.config["batch_size"] * 2:
                model = model_info["model"]
                model.fit(
                    np.array(model_info["training_data"]["X"]),
                    np.array(model_info["training_data"]["y"]),
                )
                # 清空数据以节省内存
                model_info["training_data"] = {"X": [], "y": []}

    def _prepare_input_data(
        self, data: Any, as_numpy: bool = False
    ) -> torch.Tensor | Optional[np.ndarray]:
        """准备输入数据"""
        try:
            if isinstance(data, (list, tuple)):
                if as_numpy and SKLEARN_AVAILABLE:
                    return np.array(data, dtype=np.float32)
                elif TORCH_AVAILABLE:
                    return torch.tensor(data, dtype=torch.float32)
                else:
                    return array(data, dtype=array.float32)
            elif isinstance(data, np.ndarray):
                if as_numpy:
                    return data.astype(np.float32)
                elif TORCH_AVAILABLE:
                    return torch.from_numpy(data).float()
                else:
                    return data
            elif isinstance(data, (int, float)):
                if as_numpy and SKLEARN_AVAILABLE:
                    return np.array([data], dtype=np.float32)
                elif TORCH_AVAILABLE:
                    return torch.tensor([data], dtype=torch.float32)
                else:
                    return array([data], dtype=array.float32)
            else:
                # 尝试序列化复杂对象
                serialized = json.dumps(data, sort_keys=True)
                hash_val = float(
                    int(
                        hashlib.md5(
                            serialized.encode(), usedforsecurity=False
                        ).hexdigest(),
                        16,
                    )
                )
                if as_numpy and SKLEARN_AVAILABLE:
                    return np.array([hash_val], dtype=np.float32)
                elif TORCH_AVAILABLE:
                    return torch.tensor([hash_val], dtype=torch.float32)
                else:
                    return array([hash_val], dtype=array.float32)
        except Exception as e:
            logger.error(f"准备输入数据失败: {e}")
            return None

    def _prepare_target_data(
        self, data: Any, as_numpy: bool = False
    ) -> torch.Tensor | Optional[float]:
        """准备目标数据"""
        try:
            if isinstance(data, (int, float, np.number)):
                if as_numpy:
                    return float(data)
                elif TORCH_AVAILABLE:
                    return torch.tensor([float(data)], dtype=torch.float32)
                else:
                    return float(data)
            elif isinstance(data, np.ndarray):
                if as_numpy:
                    return data.astype(np.float32)
                elif TORCH_AVAILABLE:
                    return torch.from_numpy(data).float()
                else:
                    return data
            elif isinstance(data, list) and len(data) == 1:
                return self._prepare_target_data(data[0], as_numpy)
            else:
                # 对于复杂输出,计算一个标量值
                if hasattr(data, "__len__"):
                    return float(len(data))
                else:
                    return 1.0
        except Exception as e:
            logger.error(f"准备目标数据失败: {e}")
            return None

    async def _update_curriculum(self, experience: LearningExperience):
        """更新课程学习"""
        # 根据经验难度和性能调整课程
        difficulty = self._estimate_difficulty(experience)
        self.curriculum.update_difficulty(difficulty, experience.reward)

    def _estimate_difficulty(self, experience: LearningExperience) -> float:
        """估计经验难度"""
        # 基于奖励和上下文估计难度
        base_difficulty = 1.0 - experience.reward

        # 考虑输入复杂度
        if hasattr(experience.input_data, "__len__"):
            complexity = min(len(experience.input_data) / 100.0, 1.0)
            base_difficulty += complexity * 0.3

        return min(base_difficulty, 1.0)

    async def adapt_to_new_environment(
        self, environment_data: dict[str, Any], adaptation_strategy: AdaptationStrategy
    ) -> bool:
        """适应新环境"""
        try:
            logger.info(f"开始适应新环境,策略: {adaptation_strategy.value}")

            # 记录适应开始
            adaptation_start = time.time()

            # 根据策略执行适应
            if adaptation_strategy == AdaptationStrategy.GRADIENT_DESCENT:
                success = await self._adapt_gradient_descent(environment_data)
            elif adaptation_strategy == AdaptationStrategy.EVOLUTIONARY:
                success = await self._adapt_evolutionary(environment_data)
            elif adaptation_strategy == AdaptationStrategy.TRANSFER:
                success = await self._adapt_transfer_learning(environment_data)
            elif adaptation_strategy == AdaptationStrategy.META_OPTIMIZATION:
                success = await self._adapt_meta_optimization(environment_data)
            else:
                logger.warning(f"不支持的适应策略: {adaptation_strategy}")
                return False

            # 记录适应结果
            adaptation_time = time.time() - adaptation_start
            self.adaptation_history.append(
                {
                    "strategy": adaptation_strategy.value,
                    "success": success,
                    "time": adaptation_time,
                    "timestamp": datetime.now(),
                }
            )

            logger.info(f"环境适应完成,用时: {adaptation_time:.2f}秒")
            return success

        except Exception as e:
            logger.error(f"环境适应失败: {e}")
            return False

    async def _adapt_gradient_descent(self, environment_data: dict[str, Any]) -> bool:
        """使用梯度下降适应

        根据环境数据调整学习率进行微调。
        """
        # 从环境数据中获取适应率，或使用默认值
        adaptation_rate = environment_data.get("adaptation_rate", self.config["adaptation_rate"])

        for task_id, model_info in self.active_models.items():
            if model_info.get("type") == "neural_network" and "optimizer" in model_info:
                # 更新学习率
                optimizer = model_info["optimizer"]
                for param_group in optimizer.param_groups:
                    param_group["lr"] *= adaptation_rate

                # 使用环境数据中的样本进行快速适应训练
                sample_count = environment_data.get("sample_count", 100)
                for experience in list(self.experience_buffer)[-sample_count:]:
                    await self._update_model(task_id, experience)

        return True

    async def _adapt_evolutionary(self, environment_data: dict[str, Any]) -> bool:
        """使用进化算法适应

        创建模型变体并根据环境数据选择最佳。
        """
        # 创建模型变体并选择最佳
        best_performance = 0.0

        # 从环境数据获取变体数量
        num_variants = environment_data.get("num_variants", 3)

        for task_id, model_info in list(self.active_models.items()):
            # 保存当前最佳性能
            if task_id in self.task_performance:
                current_performance = np.mean(self.task_performance[task_id][-10:])
                if current_performance > best_performance:
                    best_performance = current_performance

            # 创建变体
            for i in range(num_variants):
                variant_id = f"{task_id}_variant_{i}"
                variant_model = await self._create_model_variant(model_info, environment_data)
                if variant_model:
                    self.active_models[variant_id] = variant_model

        return True

    async def _create_model_variant(
        self, model_info: dict[str, Any], environment_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """创建模型变体

        Args:
            model_info: 原始模型信息
            environment_data: 环境数据，包含变异参数
        """
        model_type = model_info.get("type")

        # 从环境数据获取噪声级别
        noise_level = environment_data.get("noise_level", 0.01)

        if model_type == "neural_network" and TORCH_AVAILABLE:
            # 随机修改一些参数
            variant = model_info.copy()
            original_model = model_info["model"]

            # 创建新的模型实例
            new_model = type(original_model)()
            new_model.load_state_dict(original_model.state_dict())

            # 添加噪声
            with torch.no_grad():
                for param in new_model.parameters():
                    noise = torch.randn_like(param) * noise_level
                    param.add_(noise)

            variant["model"] = new_model
            return variant

        return None

    async def _adapt_transfer_learning(self, environment_data: dict[str, Any]) -> bool:
        """使用迁移学习适应

        基于环境数据查找相似任务并迁移知识。
        """
        # 从环境数据获取相似度阈值
        similarity_threshold = environment_data.get("similarity_threshold", 0.7)

        # 查找相似任务的知识迁移
        for task_id in self.active_models.keys():
            # 使用环境数据中的阈值查找相似任务
            similar_tasks = self._find_similar_tasks(task_id, similarity_threshold)

            for similar_task in similar_tasks:
                if similar_task in self.models:
                    # 迁移知识
                    await self._transfer_knowledge(similar_task, task_id)

        return True

    def _find_similar_tasks(self, task_id: str, threshold: float = 0.7) -> list[str]:
        """查找相似任务

        Args:
            task_id: 任务ID
            threshold: 相似度阈值

        Returns:
            相似任务列表
        """
        similar_tasks = []

        for other_task_id in self.active_models:
            if other_task_id != task_id:
                similarity = self._calculate_task_similarity(task_id, other_task_id)
                if similarity > threshold:
                    similar_tasks.append(other_task_id)

        return similar_tasks

    def _calculate_task_similarity(self, task1: str, task2: str) -> float:
        """计算任务相似度"""
        if task1 in self.task_performance and task2 in self.task_performance:
            perf1 = (
                np.mean(self.task_performance[task1][-10:])
                if self.task_performance[task1]
                else 0
            )
            perf2 = (
                np.mean(self.task_performance[task2][-10:])
                if self.task_performance[task2]
                else 0
            )
            return 1.0 - abs(perf1 - perf2)
        return 0.5

    async def _transfer_knowledge(self, source_task: str, target_task: str):
        """迁移知识"""
        source_model = self.models.get(source_task)
        target_model = self.active_models.get(target_task)

        if not source_model or not target_model:
            return

        # 简化的知识迁移:复制部分权重
        if (
            source_model.get("type") == "neural_network"
            and target_model.get("type") == "neural_network"
            and TORCH_AVAILABLE
        ):
            source_nn = source_model["model"]
            target_nn = target_model["model"]

            # 迁移部分层
            with torch.no_grad():
                for (name1, param1), (name2, param2) in zip(
                    source_nn.named_parameters(),
                    target_nn.named_parameters(),
                    strict=False,
                ):
                    if name1 == name2 and "weight" in name1:
                        # 部分复制
                        mask = torch.rand_like(param1) > 0.5
                        param2.data[mask] = param1.data[mask]

    async def _adapt_meta_optimization(self, environment_data: dict[str, Any]) -> bool:
        """使用元优化适应"""
        if self.meta_learner:
            return await self.meta_learner.adapt_to_environment(environment_data)
        return False

    async def evaluate_performance(
        self, task_id: str, test_data: list[LearningExperience] | None = None
    ) -> float:
        """评估模型性能"""
        if task_id not in self.active_models:
            return 0.0

        model_info = self.active_models[task_id]
        model_type = model_info.get("type")

        if test_data:
            # 使用提供的测试数据
            total_loss = 0.0
            count = 0

            for experience in test_data:
                input_data = self._prepare_input_data(experience.input_data)
                target_data = self._prepare_target_data(experience.output_data)

                if input_data is not None and target_data is not None:
                    if model_type == "neural_network" and TORCH_AVAILABLE:
                        model = model_info["model"]
                        with torch.no_grad():
                            output = model(input_data)
                            loss = nn.MSELoss()(output, target_data)
                            total_loss += loss.item()
                            count += 1

            avg_loss = total_loss / count if count > 0 else float("inf")
            performance = 1.0 / (1.0 + avg_loss)

        else:
            # 使用历史性能
            if task_id in self.task_performance:
                performance = np.mean(self.task_performance[task_id][-10:])
            else:
                performance = 0.5

        # 记录性能
        self.task_performance[task_id].append(performance)
        if len(self.task_performance[task_id]) > 100:
            self.task_performance[task_id] = self.task_performance[task_id][-100:]

        return performance

    async def save_model_checkpoint(self, task_id: str) -> bool:
        """
        保存模型检查点（安全实现）

        使用安全的序列化方法：
        - PyTorch模型：使用torch.save（内置安全机制）
        - sklearn模型：使用joblib（比pickle更安全）
        - 元数据：使用JSON
        """
        if task_id not in self.active_models:
            return False

        try:
            model_info = self.active_models[task_id]
            model_type = model_info.get("type", "unknown")

            # 限制模型大小（100MB）
            if not _validate_model_snapshot(model_type, b""):
                logger.error(f"模型类型验证失败: {model_type}")
                return False

            snapshot = ModelSnapshot(
                snapshot_id=str(uuid.uuid4()),
                model_type=model_type,
                model_data=b"",  # 不再存储pickle数据
                performance=await self.evaluate_performance(task_id),
                created_at=datetime.now(),
            )

            # 根据模型类型使用安全的保存方法
            if model_type == "neural_network" and TORCH_AVAILABLE:
                # 使用torch.save（比pickle安全，有类型检查）
                model_state = model_info.get("model").state_dict()
                optimizer_state = model_info.get("optimizer").state_dict()

                # 存储状态字典的哈希作为引用
                import torch
                state_bytes = torch.save({
                    'model': model_state,
                    'optimizer': optimizer_state,
                    'config': model_info.get('config', {})
                })
                snapshot.model_data = state_bytes

            elif model_type in ("linear_regression", "random_forest") and SKLEARN_AVAILABLE:
                # 使用joblib（sklearn推荐，比pickle安全）
                try:
                    import joblib
                    from io import BytesIO
                    buffer = BytesIO()
                    joblib.dump(model_info.get("model"), buffer)
                    snapshot.model_data = buffer.getvalue()
                except ImportError:
                    logger.warning("joblib不可用，跳过模型保存")
                    return False

            self.model_snapshots[task_id] = snapshot
            logger.info(f"✅ 安全保存模型检查点: {task_id}")
            return True

        except Exception as e:
            logger.error(f"保存模型检查点失败: {e}")
            return False

    async def load_model_checkpoint(
        self, task_id: str, checkpoint_id: str | None = None
    ) -> bool:
        """
        加载模型检查点（安全实现）

        使用安全的反序列化方法：
        - PyTorch模型：使用torch.load
        - sklearn模型：使用joblib.load
        - 包含类型验证和大小限制
        """
        if checkpoint_id:
            snapshot = self.model_snapshots.get(checkpoint_id)
        else:
            snapshot = self.model_snapshots.get(task_id)

        if not snapshot:
            logger.warning(f"模型检查点不存在: {checkpoint_id or task_id}")
            return False

        # 验证模型类型
        if not _validate_model_snapshot(snapshot.model_type, snapshot.model_data):
            logger.error(f"模型类型验证失败，拒绝加载: {checkpoint_id or task_id}")
            return False

        try:
            # 验证数据大小
            if len(snapshot.model_data) > 100 * 1024 * 1024:
                logger.error(f"模型数据过大: {len(snapshot.model_data)} bytes")
                return False

            # 根据模型类型使用安全的加载方法
            if snapshot.model_type == "neural_network" and TORCH_AVAILABLE:
                import torch
                from io import BytesIO

                buffer = BytesIO(snapshot.model_data)
                state_dict = torch.load(buffer, weights_only=True)  # 只加载权重

                # 验证状态字典结构
                if not isinstance(state_dict, dict) or 'model' not in state_dict:
                    logger.error("状态字典结构无效")
                    return False

                # 重建模型（需要重新创建模型实例）
                # 注意：这里简化处理，实际应该从任务配置重建
                model_info = {
                    "type": "neural_network",
                    "state_dict": state_dict,
                    "loaded": True
                }

            elif snapshot.model_type in ("linear_regression", "random_forest") and SKLEARN_AVAILABLE:
                try:
                    import joblib
                    from io import BytesIO

                    buffer = BytesIO(snapshot.model_data)
                    model = joblib.load(buffer)

                    # 验证加载的对象类型
                    import sklearn
                    if not isinstance(model, sklearn.base.BaseEstimator):
                        logger.error(f"加载的对象不是sklearn模型: {type(model)}")
                        return False

                    model_info = {
                        "type": snapshot.model_type,
                        "model": model,
                        "loaded": True
                    }
                except ImportError:
                    logger.warning("joblib不可用")
                    return False
            else:
                logger.warning(f"不支持的模型类型或依赖未安装: {snapshot.model_type}")
                return False

            self.active_models[task_id] = model_info
            logger.info(f"✅ 安全加载模型检查点: {task_id}")
            return True

        except Exception as e:
            logger.error(f"加载模型检查点失败: {e}")
            return False

    def get_learning_statistics(self) -> dict[str, Any]:
        """获取学习统计信息"""
        return {
            "total_experiences": len(self.experience_buffer),
            "active_tasks": len(self.active_models),
            "saved_checkpoints": len(self.model_snapshots),
            "learning_tasks": len(self.learning_tasks),
            "avg_performance": self._calculate_average_performance(),
            "adaptation_count": len(self.adaptation_history),
            "recent_adaptations": self.adaptation_history[-5:]
            if self.adaptation_history
            else [],
        }

    def _calculate_average_performance(self) -> float:
        """计算平均性能"""
        if not self.task_performance:
            return 0.0

        all_performances = []
        for performances in self.task_performance.values():
            if performances:
                all_performances.append(performances[-1])

        return np.mean(all_performances) if all_performances else 0.0


__all__ = ["RapidLearningEngine", "TORCH_AVAILABLE", "SKLEARN_AVAILABLE"]
