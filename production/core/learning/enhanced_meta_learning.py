#!/usr/bin/env python3
"""
元学习引擎增强版 - Enhanced Meta-Learning Engine
实现"如何学习"的学习能力

核心功能:
1. 学习策略评估 - 评估不同学习策略的效果
2. 超参数优化 - 自动优化学习参数
3. 任务泛化 - 从少数样本中快速学习
4. 迁移学习 - 跨领域知识迁移

作者: Athena平台团队
创建时间: 2026-01-23
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.learning.input_validator import get_input_validator
from core.logging_config import setup_logging

logger = setup_logging()


class LearningStrategy(Enum):
    """学习策略"""

    RAPID_LEARNING = "rapid_learning"  # 快速学习
    DEEP_LEARNING = "deep_learning"  # 深度学习
    SPACED_REPETITION = "spaced_repetition"  # 间隔重复
    ACTIVE_RECALL = "active_recall"  # 主动回忆
    INTERLEAVING = "interleaving"  # 交叉学习


@dataclass
class StrategyPerformance:
    """策略性能"""

    strategy: LearningStrategy
    accuracy: float
    efficiency: float  # 学习效率
    retention: float  # 知识保留率
    transferability: float  # 可迁移性
    last_updated: datetime
    usage_count: int = 0


@dataclass
class MetaLearningTask:
    """元学习任务"""

    task_id: str
    task_type: str
    support_set: list[dict[str, Any]]  # 支持集(训练样本)
    query_set: list[dict[str, Any]]  # 查询集(测试样本)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningResult:
    """学习结果"""

    task_id: str
    strategy_used: LearningStrategy
    accuracy: float
    efficiency: float
    retention: float
    transferability: float
    learning_time: float
    timestamp: datetime


class EnhancedMetaLearningEngine:
    """
    增强元学习引擎

    实现:
    - 学习策略自动选择
    - 超参数自动优化
    - 少样本快速学习
    - 跨域知识迁移
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

        # 策略性能跟踪
        self.strategy_performance: dict[LearningStrategy, StrategyPerformance] = {}

        # 任务历史
        self.task_history: list[MetaLearningTask] = []
        self.learning_results: list[LearningResult] = []

        # 学习超参数
        self.hyperparameters = {
            "learning_rate": 0.01,
            "batch_size": 32,
            "memory_window": 10,
            "forgetting_factor": 0.1,
            "exploration_rate": 0.2,
        }

        # 策略权重(动态调整)
        self.strategy_weights = {
            LearningStrategy.RAPID_LEARNING: 0.2,
            LearningStrategy.DEEP_LEARNING: 0.2,
            LearningStrategy.SPACED_REPETITION: 0.2,
            LearningStrategy.ACTIVE_RECALL: 0.2,
            LearningStrategy.INTERLEAVING: 0.2,
        }

        # 元学习统计
        self.stats = {
            "total_tasks": 0,
            "strategies_tried": defaultdict(int),
            "best_strategies": defaultdict(int),
            "improvements": [],
            "total_learning_time": 0.0,
        }

        logger.info(f"🧠 元学习引擎初始化: {agent_id}")

    async def _validate_task(self, task: MetaLearningTask) -> None:
        """
        验证元学习任务

        Args:
            task: 元学习任务

        Raises:
            ValueError: 验证失败
        """
        validator = get_input_validator()

        # 验证任务ID
        if not task.task_id or not isinstance(task.task_id, str):
            raise ValueError("任务ID必须是非空字符串")

        if len(task.task_id) > 100:
            raise ValueError("任务ID过长，最大100字符")

        # 验证任务类型
        if not task.task_type or not isinstance(task.task_type, str):
            raise ValueError("任务类型必须是非空字符串")

        # 验证支持集
        if not isinstance(task.support_set, list):
            raise ValueError("支持集必须是列表类型")

        if len(task.support_set) > 1000:
            raise ValueError("支持集过大，最大1000个样本")

        # 验证查询集
        if not isinstance(task.query_set, list):
            raise ValueError("查询集必须是列表类型")

        if len(task.query_set) > 1000:
            raise ValueError("查询集过大，最大1000个样本")

        # 验证每个样本
        for i, sample in enumerate(task.support_set):
            if not isinstance(sample, dict):
                raise ValueError(f"支持集[{i}]必须是字典类型")

            sample_result = await validator.validate_context(sample)
            if sample_result.errors:
                raise ValueError(f"支持集[{i}]验证失败: {sample_result.errors}")

        for i, sample in enumerate(task.query_set):
            if not isinstance(sample, dict):
                raise ValueError(f"查询集[{i}]必须是字典类型")

            sample_result = await validator.validate_context(sample)
            if sample_result.errors:
                raise ValueError(f"查询集[{i}]验证失败: {sample_result.errors}")

    async def select_learning_strategy(self, task: MetaLearningTask) -> LearningStrategy:
        """
        为任务选择最优学习策略

        Args:
            task: 元学习任务

        Returns:
            推荐的学习策略
        """
        # 验证任务
        await self._validate_task(task)

        # 1. 分析任务特征
        task_features = await self._analyze_task_features(task)

        # 2. 评估候选策略
        strategy_scores = {}

        for strategy in LearningStrategy:
            score = await self._evaluate_strategy_for_task(strategy, task, task_features)
            strategy_scores[strategy] = score

        # 3. 选择最优策略
        best_strategy = max(strategy_scores, key=strategy_scores.get)  # type: ignore

        logger.info(f"📊 为任务 {task.task_id} 选择策略: {best_strategy.value}")

        self.stats["strategies_tried"][best_strategy] += 1

        return best_strategy

    async def learn_from_few_shots(
        self, task: MetaLearningTask, strategy: LearningStrategy | None = None
    ) -> LearningResult:
        """
        从少量样本中学习(少样本学习)

        Args:
            task: 元学习任务
            strategy: 学习策略(如果为None,自动选择)

        Returns:
            学习结果
        """
        # 验证任务
        await self._validate_task(task)

        learning_start = datetime.now()

        # 1. 选择策略
        if strategy is None:
            strategy = await self.select_learning_strategy(task)

        # 2. 执行学习
        learning_result = await self._execute_learning(task, strategy)

        # 3. 更新策略性能
        await self._update_strategy_performance(strategy, learning_result)

        # 4. 记录任务和结果
        self.task_history.append(task)
        self.learning_results.append(learning_result)
        self.stats["total_tasks"] += 1

        learning_time = (datetime.now() - learning_start).total_seconds()
        self.stats["total_learning_time"] += learning_time

        return learning_result

    async def optimize_hyperparameters(
        self, validation_tasks: list[MetaLearningTask], max_iterations: int = 10
    ) -> dict[str, float]:
        """
        优化超参数

        Args:
            validation_tasks: 验证任务列表
            max_iterations: 最大迭代次数

        Returns:
            优化后的超参数
        """
        logger.info("🔧 开始超参数优化...")

        best_params = self.hyperparameters.copy()
        best_score = await self._evaluate_parameters(best_params, validation_tasks)

        # 简化的网格搜索(实际可使用贝叶斯优化)
        param_grid = {
            "learning_rate": [0.001, 0.01, 0.1],
            "batch_size": [16, 32, 64],
            "memory_window": [5, 10, 20],
            "exploration_rate": [0.1, 0.2, 0.3],
        }

        from itertools import product

        # 生成参数组合(限制数量)
        param_combinations = list(
            product(
                param_grid["learning_rate"],
                param_grid["batch_size"],
                param_grid["memory_window"],
                param_grid["exploration_rate"],
            )
        )

        # 评估每个组合
        for _i, (lr, bs, mw, er) in enumerate(param_combinations[:max_iterations]):
            test_params = {
                "learning_rate": lr,
                "batch_size": bs,
                "memory_window": mw,
                "exploration_rate": er,
                "forgetting_factor": self.hyperparameters["forgetting_factor"],
            }

            # 评估参数性能
            avg_score = await self._evaluate_parameters(test_params, validation_tasks)

            if avg_score > best_score:
                best_score = avg_score
                best_params = test_params

        # 更新为最优参数
        self.hyperparameters = best_params

        logger.info(f"✅ 超参数优化完成: {best_params}")
        logger.info(f"   最优分数: {best_score:.3f}")

        return best_params

    async def transfer_knowledge(
        self, source_domain: str, target_domain: str, transfer_samples: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        知识迁移

        Args:
            source_domain: 源域
            target_domain: 目标域
            transfer_samples: 迁移样本

        Returns:
            迁移结果
        """
        logger.info(f"🔄 知识迁移: {source_domain} -> {target_domain}")

        # 1. 提取源域知识
        source_knowledge = await self._extract_domain_knowledge(source_domain)

        # 2. 适配到目标域
        adapted_knowledge = await self._adapt_knowledge_to_target(
            source_knowledge, target_domain, transfer_samples
        )

        # 3. 验证迁移效果
        transfer_score = await self._validate_transfer(adapted_knowledge, transfer_samples)

        result = {
            "source_domain": source_domain,
            "target_domain": target_domain,
            "transfer_score": transfer_score,
            "adapted_knowledge_count": len(adapted_knowledge),
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"✅ 知识迁移完成: 分数={transfer_score:.3f}")

        return result

    # ========== 辅助方法 ==========

    async def _analyze_task_features(self, task: MetaLearningTask) -> dict[str, Any]:
        """分析任务特征"""
        features = {
            "sample_count": len(task.support_set),
            "task_type": task.task_type,
            "complexity": self._calculate_task_complexity(task),
            "domain": task.metadata.get("domain", "unknown"),
            "has_context": bool(task.metadata.get("context")),
        }
        return features

    async def _evaluate_strategy_for_task(
        self, strategy: LearningStrategy, task: MetaLearningTask, task_features: dict[str, Any]
    ) -> float:
        """评估策略对任务的适用性"""
        base_score = 0.5

        # 基础权重
        weight = self.strategy_weights.get(strategy, 0.2)

        # 如果有历史性能数据
        if strategy in self.strategy_performance:
            perf = self.strategy_performance[strategy]
            performance_score = perf.accuracy * 0.4 + perf.efficiency * 0.3 + perf.retention * 0.3
            base_score = performance_score * 0.7 + weight * 0.3
        else:
            base_score = weight

        # 根据任务特征调整
        if task_features["sample_count"] < 10:
            if strategy == LearningStrategy.RAPID_LEARNING:
                base_score *= 1.2  # 少样本偏好快速学习
            elif strategy == LearningStrategy.DEEP_LEARNING:
                base_score *= 0.8  # 深度学习需要更多样本

        if task_features["complexity"] > 0.7 and strategy == LearningStrategy.DEEP_LEARNING:
            base_score *= 1.15  # 复杂任务偏好深度学习

        return min(base_score, 1.0)

    def _calculate_task_complexity(self, task: MetaLearningTask) -> float:
        """计算任务复杂度"""
        sample_count = len(task.support_set)

        if sample_count == 0:
            return 0.0

        # 计算平均特征数量
        feature_counts = []
        for sample in task.support_set:
            if isinstance(sample, dict):
                feature_counts.append(len(sample))

        avg_features = sum(feature_counts) / len(feature_counts) if feature_counts else 0

        # 简化的复杂度计算
        complexity = (sample_count * avg_features) / 1000.0
        return min(complexity, 1.0)

    async def _execute_learning(
        self, task: MetaLearningTask, strategy: LearningStrategy
    ) -> LearningResult:
        """执行学习"""
        learning_start = datetime.now()

        # 根据策略执行不同的学习算法
        if strategy == LearningStrategy.RAPID_LEARNING:
            result = await self._rapid_learning(task)
        elif strategy == LearningStrategy.SPACED_REPETITION:
            result = await self._spaced_repetition_learning(task)
        elif strategy == LearningStrategy.ACTIVE_RECALL:
            result = await self._active_recall_learning(task)
        else:
            result = await self._default_learning(task)

        learning_time = (datetime.now() - learning_start).total_seconds()

        # 创建学习结果
        learning_result = LearningResult(
            task_id=task.task_id,
            strategy_used=strategy,
            accuracy=result["accuracy"],
            efficiency=result["efficiency"],
            retention=result["retention"],
            transferability=result["transferability"],
            learning_time=learning_time,
            timestamp=datetime.now(),
        )

        return learning_result

    async def _rapid_learning(self, task: MetaLearningTask) -> dict[str, Any]:
        """快速学习（基于相似度匹配的简化实现）"""
        # 分析支持集特征
        feature_vectors = []
        for sample in task.support_set:
            # 简化的特征提取：基于关键词和上下文的哈希
            if isinstance(sample, dict):
                features = hash(str(sample.get("input", "")) + str(sample.get("output", "")))
                feature_vectors.append(features)

        # 计算查询集与支持集的相似度
        if task.query_set and feature_vectors:
            similarity_scores = []
            for query in task.query_set:
                if isinstance(query, dict):
                    query_features = hash(str(query.get("input", "")))
                    # 计算与支持集的相似度
                    similarities = [1.0 if abs(query_features - f) < 1000 else 0.0 for f in feature_vectors]
                    similarity_scores.append(max(similarities) if similarities else 0.0)

            avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.5

            # 基于相似度计算性能指标
            accuracy = min(0.95, 0.5 + avg_similarity * 0.4)
            efficiency = min(0.95, 0.6 + avg_similarity * 0.3)
            retention = max(0.6, 0.9 - avg_similarity * 0.2)  # 快速学习的保留率较低
            transferability = min(0.85, 0.5 + avg_similarity * 0.3)
        else:
            # 无足够数据时的默认值
            accuracy = 0.70
            efficiency = 0.85
            retention = 0.65
            transferability = 0.60

        return {
            "accuracy": accuracy,
            "efficiency": efficiency,
            "retention": retention,
            "transferability": transferability,
        }

    async def _spaced_repetition_learning(self, task: MetaLearningTask) -> dict[str, Any]:
        """间隔重复学习（基于复习间隔的优化）"""
        # 分析样本数量和复杂度
        sample_count = len(task.support_set)
        complexity = self._calculate_task_complexity(task)

        # 间隔重复学习的特点：高保留率，较低效率（需要多次复习）
        # 样本越多，初始准确率越低，但保留率越高
        base_accuracy = min(0.95, 0.6 + sample_count * 0.02)
        # 复杂度越高，需要更多复习时间，效率越低
        efficiency = max(0.65, 0.85 - complexity * 0.2)
        # 间隔重复的核心优势：高保留率
        retention = min(0.98, 0.85 + sample_count * 0.01)
        # 间隔重复的迁移能力一般
        transferability = max(0.55, 0.75 - complexity * 0.2)

        return {
            "accuracy": base_accuracy,
            "efficiency": efficiency,
            "retention": retention,
            "transferability": transferability,
        }

    async def _active_recall_learning(self, task: MetaLearningTask) -> dict[str, Any]:
        """主动回忆学习（基于测试效应的实现）"""
        # 主动回忆通过主动提取记忆来增强学习
        sample_count = len(task.support_set)
        complexity = self._calculate_task_complexity(task)

        # 计算多样性分数（基于样本的差异）
        diversity_score = min(1.0, sample_count * 0.1)

        # 主动回忆的特点：平衡的性能
        accuracy = min(0.92, 0.65 + diversity_score * 0.25 + (1 - complexity) * 0.1)
        efficiency = min(0.90, 0.70 + diversity_score * 0.15)
        # 主动回忆有较好的保留率
        retention = min(0.93, 0.75 + diversity_score * 0.15)
        # 主动回忆的迁移能力较好
        transferability = min(0.88, 0.65 + diversity_score * 0.20)

        return {
            "accuracy": accuracy,
            "efficiency": efficiency,
            "retention": retention,
            "transferability": transferability,
        }

    async def _default_learning(self, task: MetaLearningTask) -> dict[str, Any]:
        """默认学习（基于简单的频率统计）"""
        sample_count = len(task.support_set)

        # 统计学学习：基于样本频率和模式
        if sample_count > 0:
            # 样本数量越多，准确率越高
            accuracy = min(0.85, 0.5 + sample_count * 0.03)
            # 效率随样本增加略微下降
            efficiency = max(0.70, 0.85 - sample_count * 0.005)
            # 保留率中等
            retention = min(0.85, 0.65 + sample_count * 0.02)
            # 迁移能力中等
            transferability = min(0.75, 0.55 + sample_count * 0.02)
        else:
            accuracy = 0.60
            efficiency = 0.80
            retention = 0.65
            transferability = 0.55

        return {
            "accuracy": accuracy,
            "efficiency": efficiency,
            "retention": retention,
            "transferability": transferability,
        }

    async def _update_strategy_performance(
        self, strategy: LearningStrategy, result: LearningResult
    ):
        """更新策略性能"""
        if strategy in self.strategy_performance:
            # 更新现有性能
            existing = self.strategy_performance[strategy]
            # 使用指数移动平均
            alpha = 0.3  # 学习率
            existing.accuracy = (1 - alpha) * existing.accuracy + alpha * result.accuracy
            existing.efficiency = (1 - alpha) * existing.efficiency + alpha * result.efficiency
            existing.retention = (1 - alpha) * existing.retention + alpha * result.retention
            existing.transferability = (
                1 - alpha
            ) * existing.transferability + alpha * result.transferability
            existing.last_updated = datetime.now()
            existing.usage_count += 1
        else:
            # 创建新性能记录
            self.strategy_performance[strategy] = StrategyPerformance(
                strategy=strategy,
                accuracy=result.accuracy,
                efficiency=result.efficiency,
                retention=result.retention,
                transferability=result.transferability,
                last_updated=datetime.now(),
                usage_count=1,
            )

        # 更新最佳策略统计
        if result.accuracy > 0.85:
            self.stats["best_strategies"][strategy] += 1

        # 记录改进
        self.stats["improvements"].append(
            {
                "strategy": strategy.value,
                "accuracy": result.accuracy,
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def _evaluate_parameters(
        self, params: dict[str, float], tasks: list[MetaLearningTask]
    ) -> float:
        """评估参数性能"""
        if not tasks:
            return 0.5

        total_score = 0.0

        for _task in tasks:
            # 模拟使用参数进行学习
            # 在实际实现中,这里会真正使用参数执行学习
            task_score = 0.7 + (params.get("learning_rate", 0.01) * 5)
            total_score += task_score

        return total_score / len(tasks)

    async def _extract_domain_knowledge(self, domain: str) -> list[dict[str, Any]]:
        """提取域知识"""
        # 简化实现:返回模拟知识
        return [
            {"type": "pattern", "domain": domain, "confidence": 0.8},
            {"type": "rule", "domain": domain, "confidence": 0.7},
        ]

    async def _adapt_knowledge_to_target(
        self,
        source_knowledge: list[dict[str, Any]],        target_domain: str,
        samples: list[dict[str, Any]],    ) -> list[dict[str, Any]]:
        """适配知识到目标域"""
        # 简化实现:直接复制并标记
        adapted = []

        for knowledge in source_knowledge:
            adapted_knowledge = knowledge.copy()
            adapted_knowledge["target_domain"] = target_domain
            adapted_knowledge["adaptation_confidence"] = 0.7
            adapted.append(adapted_knowledge)

        return adapted

    async def _validate_transfer(
        self, knowledge: list[dict[str, Any]], samples: list[dict[str, Any]]
    ) -> float:
        """验证迁移效果"""
        # 简化实现:基于知识数量和样本数量计算
        base_score = min(len(knowledge) * 0.3, 0.9)
        sample_bonus = min(len(samples) * 0.05, 0.1)

        return min(base_score + sample_bonus, 1.0)

    async def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        # 计算平均性能
        if self.strategy_performance:
            avg_accuracy = sum(perf.accuracy for perf in self.strategy_performance.values()) / len(
                self.strategy_performance
            )
        else:
            avg_accuracy = 0.0

        return {
            "agent_id": self.agent_id,
            "stats": self.stats,
            "hyperparameters": self.hyperparameters,
            "strategy_weights": {k.value: v for k, v in self.strategy_weights.items()},
            "strategy_performance": {
                k.value: {
                    "accuracy": v.accuracy,
                    "efficiency": v.efficiency,
                    "retention": v.retention,
                    "usage_count": v.usage_count,
                }
                for k, v in self.strategy_performance.items()
            },
            "avg_accuracy": avg_accuracy,
            "total_strategies": len(self.strategy_performance),
        }


# 测试和实用函数
async def test_meta_learning():
    """测试元学习引擎"""
    logger.info("🧪 测试元学习引擎...")

    # 创建元学习引擎
    engine = EnhancedMetaLearningEngine(agent_id="xiaonuo_test")

    # 创建测试任务
    task = MetaLearningTask(
        task_id="test_task_001",
        task_type="classification",
        support_set=[
            {"input": "专利分析", "output": "legal_domain"},
            {"input": "内容创作", "output": "media_domain"},
        ],
        query_set=[{"input": "IP管理"}],
        metadata={"domain": "patent_analysis"},
    )

    # 执行少样本学习
    result = await engine.learn_from_few_shots(task)

    print(f"学习结果: {result}")
    print(f"策略: {result.strategy_used.value}")
    print(f"准确率: {result.accuracy:.2f}")

    # 获取统计
    stats = await engine.get_statistics()
    print(f"统计信息: {stats}")

    return engine


if __name__ == "__main__":
    # 配置日志
    # setup_logging()  # 日志配置已移至模块导入

    # 运行测试
    asyncio.run(test_meta_learning())


# 为保持兼容性，提供 EnhancedMetaLearning 作为 EnhancedMetaLearningEngine 的别名
EnhancedMetaLearning = EnhancedMetaLearningEngine


# 导出公共接口
__all__ = [
    "LearningStrategy",
    "StrategyPerformance",
    "MetaLearningTask",
    "LearningResult",
    "EnhancedMetaLearningEngine",
    "EnhancedMetaLearning",  # 别名
]
