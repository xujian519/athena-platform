#!/usr/bin/env python3
"""
在线学习引擎 (Online Learning Engine)
实时学习和适应系统,持续优化性能

作者: 小诺·双鱼公主
版本: v2.0.0
优化目标: 持续提升性能,适应环境变化
"""

import asyncio
import contextlib
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LearningType(str, Enum):
    """学习类型"""

    SUPERVISED = "supervised"  # 监督学习
    REINFORCEMENT = "reinforcement"  # 强化学习
    UNSUPERVISED = "unsupervised"  # 无监督学习
    META = "meta"  # 元学习


class AdaptationTrigger(str, Enum):
    """适应触发条件"""

    PERFORMANCE_DROP = "performance_drop"  # 性能下降
    CONCEPT_DRIFT = "concept_drift"  # 概念漂移
    DATA_DISTRIBUTION_CHANGE = "data_distribution_change"  # 数据分布变化
    SCHEDULED = "scheduled"  # 定时触发
    MANUAL = "manual"  # 手动触发


@dataclass
class LearningSample:
    """学习样本"""

    features: dict[str, float]
    label: Any | None = None
    reward: float | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningBatch:
    """学习批次"""

    samples: list[LearningSample]
    batch_id: str
    created_at: datetime = field(default_factory=datetime.now)
    size: int = field(default=0)

    def __post_init__(self):
        self.size = len(self.samples)


@dataclass
class AdaptationEvent:
    """适应事件"""

    event_id: str
    trigger: AdaptationTrigger
    description: str
    metrics_before: dict[str, float]
    metrics_after: dict[str, float] | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ModelPerformanceMetrics:
    """模型性能指标"""

    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    latency_ms: float = 0.0
    success_rate: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class OnlineLearningEngine:
    """
    在线学习引擎

    功能:
    1. 实时样本收集
    2. 增量模型更新
    3. 概念漂移检测
    4. 自适应触发
    5. 性能监控
    6. A/B测试支持
    """

    def __init__(
        self, batch_size: int = 32, learning_window: int = 1000, adaptation_threshold: float = 0.05
    ):
        self.name = "在线学习引擎"
        self.version = "2.0.0"
        self.batch_size = batch_size
        self.learning_window = learning_window
        self.adaptation_threshold = adaptation_threshold

        # 样本缓冲区
        self.sample_buffer: deque = deque(maxlen=learning_window)

        # 学习批次历史
        self.batch_history: list[LearningBatch] = []

        # 性能指标历史
        self.performance_history: deque = deque(maxlen=100)

        # 适应事件历史
        self.adaptation_events: list[AdaptationEvent] = []

        # 模型参数(简化版)
        self.model_params: dict[str, float] = defaultdict(float)

        # 基线性能(用于检测性能下降)
        self.baseline_performance: ModelPerformanceMetrics | None = None

        # A/B测试支持
        self.ab_test_models: dict[str, dict[str, Any]] = {}

        # 学习锁(异步安全)
        self.learning_lock = asyncio.Lock()

        # 统计信息
        self.stats = {
            "total_samples": 0,
            "batches_processed": 0,
            "adaptations_triggered": 0,
            "last_adaptation_time": None,
            "learning_rate": 0.01,
        }

        # 运行状态
        self.is_running = False
        self.learning_task: asyncio.Task | None = None

        logger.info(f"✅ {self.name} 初始化完成")

    async def start(self):
        """启动在线学习"""
        if self.is_running:
            logger.warning("⚠️ 在线学习已在运行")
            return

        self.is_running = True
        self.learning_task = asyncio.create_task(self._learning_loop())

        logger.info(f"🚀 {self.name} 已启动")

    async def stop(self):
        """停止在线学习"""
        if not self.is_running:
            return

        self.is_running = False

        if self.learning_task:
            self.learning_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.learning_task

        logger.info(f"🛑 {self.name} 已停止")

    async def _learning_loop(self):
        """学习循环"""
        while self.is_running:
            try:
                # 检查是否有足够样本进行学习
                if len(self.sample_buffer) >= self.batch_size:
                    await self._process_batch()

                # 检测概念漂移
                await self._detect_concept_drift()

                # 等待下一次检查
                await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 学习循环错误: {e}", exc_info=True)
                await asyncio.sleep(10)

    async def add_sample(
        self,
        features: dict[str, float],
        label: Any | None = None,
        reward: float | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        添加学习样本

        Args:
            features: 特征
            label: 标签(监督学习)
            reward: 奖励(强化学习)
            metadata: 元数据
        """
        sample = LearningSample(
            features=features, label=label, reward=reward, metadata=metadata or {}
        )

        async with self.learning_lock:
            self.sample_buffer.append(sample)
            self.stats["total_samples"] += 1

        logger.debug(f"📝 样本已添加 (总计: {self.stats['total_samples']})")

    async def _process_batch(self):
        """处理一个批次"""
        async with self.learning_lock:
            # 取出一个批次
            batch_samples = []
            for _ in range(min(self.batch_size, len(self.sample_buffer))):
                if self.sample_buffer:
                    batch_samples.append(self.sample_buffer.popleft())

            if not batch_samples:
                return

            batch = LearningBatch(
                samples=batch_samples,
                batch_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            )

            self.batch_history.append(batch)
            self.stats["batches_processed"] += 1

        # 执行学习
        await self._learn_from_batch(batch)

        logger.info(f"📦 批次 {batch.batch_id} 已处理 ({len(batch_samples)} 样本)")

    async def _learn_from_batch(self, batch: LearningBatch):
        """从批次中学习"""
        # 简化版:在线梯度下降

        learning_rate = self.stats["learning_rate"]

        for sample in batch.samples:
            for feature_name, feature_value in sample.features.items():
                # 计算梯度(简化版:基于奖励或标签)
                if sample.reward is not None:
                    gradient = sample.reward * feature_value
                elif sample.label is not None:
                    # 假设标签是0或1
                    gradient = (sample.label - feature_value) * feature_value
                else:
                    continue

                # 更新参数
                async with self.learning_lock:
                    self.model_params[feature_name] += learning_rate * gradient

        # 记录性能
        await self._record_performance()

    async def _detect_concept_drift(self):
        """检测概念漂移"""
        if not self.performance_history or len(self.performance_history) < 10:
            return

        # 获取最近性能
        recent_metrics = list(self.performance_history)[-10:]
        current_accuracy = sum(m.accuracy for m in recent_metrics) / len(recent_metrics)

        # 与基线比较
        if self.baseline_performance:
            baseline_accuracy = self.baseline_performance.accuracy
            drop = baseline_accuracy - current_accuracy

            if drop > self.adaptation_threshold:
                await self._trigger_adaptation(
                    AdaptationTrigger.PERFORMANCE_DROP,
                    f"性能下降 {drop:.1%}",
                    {"accuracy_drop": drop},
                )

        # 检测数据分布变化(简化版:方差分析)
        recent_var = self._compute_feature_variance(recent_metrics)
        if recent_var > 0.5:  # 阈值
            await self._trigger_adaptation(
                AdaptationTrigger.DATA_DISTRIBUTION_CHANGE,
                f"数据分布变化 (方差: {recent_var:.2f})",
                {"variance": recent_var},
            )

    def _compute_feature_variance(self, metrics: list[ModelPerformanceMetrics]) -> float:
        """计算特征方差(简化版)"""
        if not metrics:
            return 0.0

        accuracies = [m.accuracy for m in metrics]
        if len(accuracies) < 2:
            return 0.0

        mean = sum(accuracies) / len(accuracies)
        variance = sum((a - mean) ** 2 for a in accuracies) / len(accuracies)

        return variance

    async def _trigger_adaptation(
        self, trigger: AdaptationTrigger, description: str, metrics: dict[str, float]
    ):
        """触发适应"""
        event_id = f"adapt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        event = AdaptationEvent(
            event_id=event_id, trigger=trigger, description=description, metrics_before=metrics
        )

        self.adaptation_events.append(event)
        self.stats["adaptations_triggered"] += 1
        self.stats["last_adaptation_time"] = datetime.now()

        logger.warning(f"🔄 触发适应: {description}")

        # 执行适应动作
        await self._adapt_to_change(event)

    async def _adapt_to_change(self, event: AdaptationEvent):
        """适应变化"""
        # 1. 调整学习率
        if event.trigger == AdaptationTrigger.PERFORMANCE_DROP:
            self.stats["learning_rate"] *= 1.5  # 提高学习率
            logger.info(f"📈 学习率调整为: {self.stats['learning_rate']:.4f}")

        # 2. 重置基线
        if event.trigger == AdaptationTrigger.DATA_DISTRIBUTION_CHANGE:
            await self._reset_baseline()

        # 3. 清空旧样本
        if event.trigger == AdaptationTrigger.CONCEPT_DRIFT:
            async with self.learning_lock:
                self.sample_buffer.clear()
            logger.info("🗑️ 样本缓冲区已清空")

        # 记录适应后的性能
        await self._record_performance()
        event.metrics_after = self._get_current_metrics()

    async def _reset_baseline(self):
        """重置基线"""
        if self.performance_history:
            recent = list(self.performance_history)[-10:]
            self.baseline_performance = ModelPerformanceMetrics(
                accuracy=sum(m.accuracy for m in recent) / len(recent),
                precision=sum(m.precision for m in recent) / len(recent),
                recall=sum(m.recall for m in recent) / len(recent),
                f1_score=sum(m.f1_score for m in recent) / len(recent),
                latency_ms=sum(m.latency_ms for m in recent) / len(recent),
                success_rate=sum(m.success_rate for m in recent) / len(recent),
            )
            logger.info(f"🔄 基线已重置: 准确率={self.baseline_performance.accuracy:.2%}")

    async def _record_performance(self):
        """记录性能指标"""
        # 简化版:基于模型参数计算性能
        metrics = ModelPerformanceMetrics(
            accuracy=self._compute_accuracy(),
            precision=self._compute_precision(),
            recall=self._compute_recall(),
            f1_score=self._compute_f1(),
            latency_ms=self._compute_latency(),
            success_rate=self._compute_success_rate(),
        )

        self.performance_history.append(metrics)

    def _compute_accuracy(self) -> float:
        """计算准确率(简化版)"""
        if not self.model_params:
            return 0.8  # 默认值
        # 基于参数绝对值估算
        param_sum = sum(abs(v) for v in self.model_params.values())
        return min(1.0, 0.7 + param_sum * 0.1)

    def _compute_precision(self) -> float:
        """计算精确率(简化版)"""
        accuracy = self._compute_accuracy()
        return accuracy * 0.95

    def _compute_recall(self) -> float:
        """计算召回率(简化版)"""
        accuracy = self._compute_accuracy()
        return accuracy * 0.9

    def _compute_f1(self) -> float:
        """计算F1分数"""
        precision = self._compute_precision()
        recall = self._compute_recall()
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)

    def _compute_latency(self) -> float:
        """计算延迟(简化版)"""
        return 150 + (1 - self._compute_accuracy()) * 100

    def _compute_success_rate(self) -> float:
        """计算成功率"""
        return self._compute_accuracy() * 0.98

    def _get_current_metrics(self) -> dict[str, float]:
        """获取当前指标"""
        return {
            "accuracy": self._compute_accuracy(),
            "precision": self._compute_precision(),
            "recall": self._compute_recall(),
            "f1_score": self._compute_f1(),
            "latency_ms": self._compute_latency(),
            "success_rate": self._compute_success_rate(),
        }

    async def run_ab_test(
        self, model_a_name: str, model_b_name: str, test_duration_seconds: int = 300
    ) -> dict[str, Any]:
        """
        运行A/B测试

        Args:
            model_a_name: 模型A名称
            model_b_name: 模型B名称
            test_duration_seconds: 测试时长

        Returns:
            测试结果
        """
        logger.info(f"🧪 开始A/B测试: {model_a_name} vs {model_b_name}")

        # 注册模型
        self.ab_test_models[model_a_name] = {"samples": 0, "correct": 0, "total_latency": 0}
        self.ab_test_models[model_b_name] = {"samples": 0, "correct": 0, "total_latency": 0}

        # 模拟运行测试
        await asyncio.sleep(test_duration_seconds)

        # 生成结果
        result = {
            "model_a": self.ab_test_models[model_a_name],
            "model_b": self.ab_test_models[model_b_name],
            "winner": None,
            "improvement": 0.0,
        }

        # 比较结果
        accuracy_a = result["model_a"]["correct"] / max(1, result["model_a"]["samples"])
        accuracy_b = result["model_b"]["correct"] / max(1, result["model_b"]["samples"])

        if accuracy_a > accuracy_b:
            result["winner"] = model_a_name
            result["improvement"] = (accuracy_a - accuracy_b) / accuracy_b
        else:
            result["winner"] = model_b_name
            result["improvement"] = (accuracy_b - accuracy_a) / max(accuracy_a, 0.01)

        logger.info(f"✅ A/B测试完成: 胜者 {result['winner']}")

        return result

    def get_status(self) -> dict[str, Any]:
        """获取引擎状态"""
        current_metrics = self._get_current_metrics()

        return {
            "name": self.name,
            "version": self.version,
            "is_running": self.is_running,
            "learning_stats": self.stats,
            "current_metrics": current_metrics,
            "baseline_metrics": {
                "accuracy": (
                    self.baseline_performance.accuracy if self.baseline_performance else None
                ),
                "f1_score": (
                    self.baseline_performance.f1_score if self.baseline_performance else None
                ),
            },
            "buffer_info": {
                "current_size": len(self.sample_buffer),
                "max_size": self.learning_window,
                "batches_processed": self.stats["batches_processed"],
            },
            "adaptation_events": len(self.adaptation_events),
            "model_params": dict(self.model_params),
        }


# 全局单例
_online_learner_instance: OnlineLearningEngine | None = None


def get_online_learning_engine() -> OnlineLearningEngine:
    """获取在线学习引擎实例"""
    global _online_learner_instance
    if _online_learner_instance is None:
        _online_learner_instance = OnlineLearningEngine()
    return _online_learner_instance
