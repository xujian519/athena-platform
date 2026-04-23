#!/usr/bin/env python3
from __future__ import annotations
"""
评估指标系统
Evaluation Metrics System

提供各种评估指标的计算方法,
用于参数优化过程中的质量评估。

作者: Athena平台团队
创建时间: 2025-01-04
"""

import logging
from dataclasses import dataclass
from typing import Any

from sklearn.metrics import precision_recall_fscore_support

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """评估结果"""

    score: float  # 总分(0-1)
    metrics: dict[str, float]  # 详细指标
    details: dict[str, Any] | None = None  # 额外细节


class EvaluationMetrics:
    """
    评估指标计算器

    借鉴Heretic的评估思路:
    - Heretic: 拒绝率 + KL散度
    - 我们: 质量评分 + 相关性 + 完整性
    """

    def __init__(self, weights: dict[str, float] | None = None):
        """
        初始化评估指标

        Args:
            weights: 各指标权重
                例如: {'quality': 0.5, 'relevance': 0.3, 'completeness': 0.2}
        """
        self.weights = weights or {
            "quality": 0.4,
            "relevance": 0.3,
            "completeness": 0.2,
            "efficiency": 0.1,
        }

        logger.info(f"📊 初始化评估指标系统,权重: {self.weights}")

    async def evaluate_response(
        self, response: str, expected: str, input_text: str | None = None
    ) -> EvaluationResult:
        """
        评估单个响应质量

        Args:
            response: 实际响应
            expected: 期望响应
            input_text: 输入文本(可选,用于相关性计算)

        Returns:
            评估结果
        """
        metrics = {}

        # 1. 质量评分(基于规则)
        metrics["quality"] = self._compute_quality_score(response)

        # 2. 相关性评分
        if input_text:
            metrics["relevance"] = await self._compute_relevance(response, input_text)
        else:
            metrics["relevance"] = 0.5  # 默认值

        # 3. 完整性评分
        metrics["completeness"] = self._compute_completeness(response, expected)

        # 4. 效率评分(基于长度)
        metrics["efficiency"] = self._compute_efficiency(response)

        # 计算加权总分
        total_score = sum(metrics.get(key, 0) * weight for key, weight in self.weights.items())

        return EvaluationResult(
            score=total_score,
            metrics=metrics,
            details={"response_length": len(response), "expected_length": len(expected)},
        )

    def _compute_quality_score(self, response: str) -> float:
        """
        计算质量分数(基于启发式规则)

        规则:
        - 有结构(标题、列表、代码块)
        - 无重复
        - 语法完整
        - 格式规范
        """
        score = 0.0

        # 1. 检查结构(20分)
        if "```" in response:  # 代码块
            score += 0.05
        if "##" in response or "**" in response:  # 标题或加粗
            score += 0.05
        if any(marker in response for marker in ["1.", "-", "*"]):  # 列表
            score += 0.10

        # 2. 检查长度(20分)
        if 50 <= len(response) <= 2000:
            score += 0.20
        elif len(response) > 2000:
            score += 0.10  # 太长,适当扣分

        # 3. 检查重复(30分)
        sentences = response.split("。")
        unique_ratio = len(set(sentences)) / max(len(sentences), 1)
        score += unique_ratio * 0.30

        # 4. 检查标点符号完整性(15分)
        if response.strip().endswith(("。", "!", "?", "。", ".", "!", "?")):
            score += 0.15

        # 5. 检查特殊字符(15分)
        special_chars = sum(1 for c in response if c in ',。!?:;""' "()")
        if special_chars > 0:
            score += min(special_chars / 50, 0.15)

        return min(score, 1.0)

    async def _compute_relevance(self, response: str, input_text: str) -> float:
        """
        计算相关性(使用语义相似度)

        简化版: 使用词重叠和长度比例
        完整版: 可以使用BERT等嵌入模型
        """
        # 简化实现: 词重叠
        response_words = set(response.lower().split())
        input_words = set(input_text.lower().split())

        if len(input_words) == 0:
            return 0.5

        overlap = len(response_words & input_words)
        relevance = overlap / len(input_words)

        # 结合响应长度(太短或太长都不好)
        length_ratio = len(response) / max(len(input_text), 1)
        length_score = 1.0 - abs(1.0 - min(length_ratio, 5.0) / 5.0)

        return relevance * 0.5 + length_score * 0.5

    def _compute_completeness(self, response: str, expected: str) -> float:
        """
        计算完整性

        基于与期望响应的相似度
        """
        if not expected:
            return 1.0  # 没有期望,默认完整

        # 使用词重叠率
        response_words = set(response.lower().split())
        expected_words = set(expected.lower().split())

        if len(expected_words) == 0:
            return 1.0

        overlap = len(response_words & expected_words)
        completeness = overlap / len(expected_words)

        return min(completeness, 1.0)

    def _compute_efficiency(self, response: str) -> float:
        """
        计算效率分数

        基于响应长度的合理性
        """
        length = len(response)

        if length < 10:
            return 0.3  # 太短
        elif length < 50:
            return 0.7
        elif length < 500:
            return 1.0  # 理想长度
        elif length < 2000:
            return 0.8
        else:
            return 0.5  # 太长

    async def evaluate_batch(
        self, responses: list[str], expecteds: list[str], input_texts: list[str] = None
    ) -> EvaluationResult:
        """
        批量评估

        Returns:
            平均评估结果
        """
        if len(responses) != len(expecteds):
            raise ValueError("responses和expecteds长度不一致")

        input_texts = input_texts or [None] * len(responses)

        scores = []
        all_metrics = []

        for response, expected, input_text in zip(responses, expecteds, input_texts, strict=False):
            result = await self.evaluate_response(response, expected, input_text)
            scores.append(result.score)
            all_metrics.append(result.metrics)

        # 计算平均指标
        avg_metrics = {}
        for key in all_metrics[0]:
            avg_metrics[key] = sum(m[key] for m in all_metrics) / len(all_metrics)

        avg_score = sum(scores) / len(scores)

        return EvaluationResult(
            score=avg_score,
            metrics=avg_metrics,
            details={"num_samples": len(scores), "individual_scores": scores},
        )

    def compute_retrieval_metrics(
        self, retrieved_ids: list[str], relevant_ids: list[str], k_values: list[str] = None
    ) -> dict[str, float]:
        """
        计算检索指标

        Args:
            retrieved_ids: 检索到的ID列表(按相关性排序)
            relevant_ids: 相关的ID集合
            k_values: 计算Recall@K的K值列表

        Returns:
            指标字典
        """
        if k_values is None:
            k_values = [1, 3, 5, 10]
        metrics = {}

        relevant_set = set(relevant_ids)

        # Recall@K
        for k in k_values:
            retrieved_at_k = set(retrieved_ids[:k])
            recall = len(retrieved_at_k & relevant_set) / max(len(relevant_set), 1)
            metrics[f"recall@{k}"] = recall

        # Precision@K
        for k in k_values:
            retrieved_at_k = set(retrieved_ids[:k])
            precision = len(retrieved_at_k & relevant_set) / max(len(retrieved_at_k), 1)
            metrics[f"precision@{k}"] = precision

        # MRR (Mean Reciprocal Rank)
        mrr = 0.0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in relevant_set:
                mrr = 1.0 / (i + 1)
                break
        metrics["mrr"] = mrr

        # MAP (Mean Average Precision) - 简化版
        ap = 0.0
        num_hits = 0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in relevant_set:
                num_hits += 1
                ap += num_hits / (i + 1)
        map_score = ap / max(len(relevant_set), 1)
        metrics["map"] = map_score

        return metrics

    def compute_classification_metrics(
        self, y_true: list[Any], y_pred: list[Any]
    ) -> dict[str, float]:
        """
        计算分类指标

        Args:
            y_true: 真实标签
            y_pred: 预测标签

        Returns:
            指标字典
        """
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average="weighted", zero_division=0
        )

        # 准确率
        accuracy = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == p) / len(y_true)

        return {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1}
