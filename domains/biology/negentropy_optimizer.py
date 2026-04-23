#!/usr/bin/env python3
from __future__ import annotations

"""
负熵优化系统
Negentropy Optimization System

基于薛定谔"生命以负熵为食"的思想,建立信息熵减优化系统:
- 生命从混乱中建立有序
- AI系统从混乱信息中提取有序知识
- 负熵 = 信息熵减 = 智能的核心度量

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

import json
import logging
import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class NegentropyMetric(Enum):
    """负熵度量类型"""

    INFORMATION_ENTROPY = "information_entropy"  # 信息熵
    STRUCTURAL_ENTROPY = "structural_entropy"  # 结构熵
    SEMANTIC_ENTROPY = "semantic_entropy"  # 语义熵
    PREDICTIVE_ENTROPY = "predictive_entropy"  # 预测熵


@dataclass
class NegentropyScore:
    """负熵分数"""

    metric_type: NegentropyMetric
    input_entropy: float  # 输入熵(混乱度)
    output_entropy: float  # 输出熵(有序度)
    negentropy: float  # 负熵 = input - output
    efficiency: float  # 效率 = negentropy / input
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class NegentropyOptimizer:
    """
    负熵优化器

    核心思想:
    1. 信息熵减 = AI智能的核心
    2. 从混乱输入到有序输出 = 负熵产生
    3. 最大化负熵 = 最优化系统
    """

    def __init__(self):
        """初始化负熵优化器"""
        self.name = "负熵优化系统"
        self.version = "v0.1.2"

        # 历史记录
        self.optimization_history: list[NegentropyScore] = []

        logger.info(f"📊 {self.name} ({self.version}) 初始化完成")

    def calculate_information_entropy(self, data: list[Any], normalize: bool = True) -> float:
        """
        计算信息熵(Shannon Entropy)

        Args:
            data: 数据列表
            normalize: 是否归一化

        Returns:
            信息熵值
        """
        if not data:
            return 0.0

        # 计算频率分布
        counter = Counter(data)
        total = len(data)

        # 计算熵
        entropy = 0.0
        for count in counter.values():
            if count > 0:
                probability = count / total
                entropy -= probability * math.log2(probability)

        # 归一化到[0, 1]
        if normalize and total > 0:
            max_entropy = math.log2(total) if total > 1 else 1.0
            entropy = entropy / max_entropy if max_entropy > 0 else 0.0

        return entropy

    def calculate_structural_entropy(self, data: dict[str, Any]) -> float:
        """
        计算结构熵(衡量数据结构的有序程度)

        Args:
            data: 结构化数据

        Returns:
            结构熵值
        """
        if not data:
            return 0.0

        # 基于键的分布计算熵
        keys = list(data.keys())
        key_entropy = self.calculate_information_entropy(keys, normalize=True)

        # 基于值类型的分布
        value_types = [type(v).__name__ for v in data.values()]
        type_entropy = self.calculate_information_entropy(value_types, normalize=True)

        # 综合结构熵
        return (key_entropy + type_entropy) / 2

    def calculate_semantic_entropy(
        self, texts: list[str], vocabulary: dict[str, int] | None = None
    ) -> float:
        """
        计算语义熵(衡量文本的语义混乱程度)

        Args:
            texts: 文本列表
            vocabulary: 词汇表(可选)

        Returns:
            语义熵值
        """
        if not texts:
            return 0.0

        # 构建词频统计
        all_words = []
        for text in texts:
            # 简单分词(按空格和标点)
            words = text.replace(".", " ").replace(",", " ").split()
            all_words.extend(words)

        # 计算词频熵
        return self.calculate_information_entropy(all_words, normalize=True)

    def measure_negentropy(
        self,
        input_data: Any,
        output_data: Any,
        metric_type: NegentropyMetric = NegentropyMetric.INFORMATION_ENTROPY,
    ) -> NegentropyScore:
        """
        测量负熵(信息熵减)

        Args:
            input_data: 输入数据(混乱)
            output_data: 输出数据(有序)
            metric_type: 度量类型

        Returns:
            负熵分数
        """
        # 根据类型计算熵
        if metric_type == NegentropyMetric.INFORMATION_ENTROPY:
            input_entropy = self.calculate_information_entropy(input_data)
            output_entropy = self.calculate_information_entropy(output_data)

        elif metric_type == NegentropyMetric.STRUCTURAL_ENTROPY:
            input_entropy = self.calculate_structural_entropy(input_data)
            output_entropy = self.calculate_structural_entropy(output_data)

        elif metric_type == NegentropyMetric.SEMANTIC_ENTROPY:
            input_entropy = self.calculate_semantic_entropy(input_data)
            output_entropy = self.calculate_semantic_entropy(output_data)

        else:
            # 默认使用信息熵
            input_entropy = self.calculate_information_entropy(input_data)
            output_entropy = self.calculate_information_entropy(output_data)

        # 计算负熵
        negentropy = input_entropy - output_entropy

        # 计算效率
        efficiency = negentropy / input_entropy if input_entropy > 0 else 0.0

        score = NegentropyScore(
            metric_type=metric_type,
            input_entropy=input_entropy,
            output_entropy=output_entropy,
            negentropy=max(0, negentropy),  # 负熵不能为负
            efficiency=efficiency,
        )

        # 记录历史
        self.optimization_history.append(score)

        return score

    def optimize_for_negentropy(
        self,
        candidates: list[Any],
        metric_type: NegentropyMetric = NegentropyMetric.INFORMATION_ENTROPY,
        target_entropy: float | None = None,
    ) -> tuple[Any, NegentropyScore]:
        """
        为最大化负熵而优化选择

        Args:
            candidates: 候选方案列表
            metric_type: 度量类型
            target_entropy: 目标熵值(可选)

        Returns:
            (最优方案, 负熵分数)
        """
        if not candidates:
            return None, None

        best_candidate = None
        best_score = None
        best_negentropy = -1

        for candidate in candidates:
            # 根据候选类型计算熵
            if metric_type == NegentropyMetric.STRUCTURAL_ENTROPY and isinstance(candidate, dict):
                entropy = self.calculate_structural_entropy(candidate)
            elif metric_type == NegentropyMetric.SEMANTIC_ENTROPY and isinstance(candidate, list):
                entropy = self.calculate_semantic_entropy(candidate)
            else:
                # 默认
                if isinstance(candidate, list):
                    entropy = self.calculate_information_entropy(candidate)
                else:
                    # 无法计算,跳过
                    continue

            # 如果有目标熵,找最接近的
            if target_entropy is not None:
                distance = abs(entropy - target_entropy)
                if (
                    distance < abs(best_negentropy - target_entropy)
                    if best_negentropy >= 0
                    else True
                ):
                    best_negentropy = entropy
                    best_candidate = candidate
            else:
                # 找熵最小的(最有序的)
                if entropy < best_negentropy or best_negentropy < 0:
                    best_negentropy = entropy
                    best_candidate = candidate

        # 创建分数
        best_score = NegentropyScore(
            metric_type=metric_type,
            input_entropy=1.0,  # 假设最大混乱
            output_entropy=best_negentropy,
            negentropy=1.0 - best_negentropy,
            efficiency=(1.0 - best_negentropy) if best_negentropy > 0 else 1.0,
        )

        return best_candidate, best_score

    def get_optimization_summary(self) -> dict[str, Any]:
        """获取优化摘要"""
        if not self.optimization_history:
            return {"message": "暂无优化记录"}

        # 统计
        avg_negentropy = sum(s.negentropy for s in self.optimization_history) / len(
            self.optimization_history
        )
        avg_efficiency = sum(s.efficiency for s in self.optimization_history) / len(
            self.optimization_history
        )

        # 按类型分组
        by_type = {}
        for score in self.optimization_history:
            metric = score.metric_type.value
            if metric not in by_type:
                by_type[metric] = []
            by_type[metric].append(score)

        return {
            "total_optimizations": len(self.optimization_history),
            "average_negentropy": avg_negentropy,
            "average_efficiency": avg_efficiency,
            "by_metric_type": {
                metric: {
                    "count": len(scores),
                    "avg_negentropy": sum(s.negentropy for s in scores) / len(scores),
                }
                for metric, scores in by_type.items()
            },
            "latest_score": {
                "negentropy": self.optimization_history[-1].negentropy,
                "efficiency": self.optimization_history[-1].efficiency,
                "timestamp": self.optimization_history[-1].timestamp,
            },
        }


# 全局单例
_negentropy_optimizer_instance = None


def get_negentropy_optimizer() -> NegentropyOptimizer:
    """获取负熵优化器单例"""
    global _negentropy_optimizer_instance
    if _negentropy_optimizer_instance is None:
        _negentropy_optimizer_instance = NegentropyOptimizer()
    return _negentropy_optimizer_instance


# 测试代码
async def main():
    """测试负熵优化系统"""

    print("\n" + "=" * 60)
    print("📊 负熵优化系统测试")
    print("=" * 60 + "\n")

    optimizer = get_negentropy_optimizer()

    # 测试1:信息熵计算
    print("📝 测试1: 信息熵计算")
    ordered_data = [1, 1, 1, 1, 1, 2, 2, 2, 2, 2]  # 高度有序
    random_data = list(range(100))  # 高度混乱

    print(f"混乱数据熵: {optimizer.calculate_information_entropy(random_data):.3f}")
    print(f"有序数据熵: {optimizer.calculate_information_entropy(ordered_data):.3f}")
    print()

    # 测试2:负熵测量
    print("📝 测试2: 负熵测量")
    score = optimizer.measure_negentropy(input_data=random_data, output_data=ordered_data)
    print(f"输入熵: {score.input_entropy:.3f}")
    print(f"输出熵: {score.output_entropy:.3f}")
    print(f"负熵: {score.negentropy:.3f}")
    print(f"效率: {score.efficiency:.1%}")
    print()

    # 测试3:优化选择
    print("📝 测试3: 优化选择")
    candidates = [
        [1, 1, 1, 2, 2, 2],  # 最有序
        [1, 2, 3, 4, 5],  # 中等
        list(range(20)),  # 最混乱
    ]

    _best, best_score = optimizer.optimize_for_negentropy(candidates)
    print(f"最优方案熵: {best_score.output_entropy:.3f}")
    print(f"负熵增益: {best_score.negentropy:.3f}")
    print()

    # 测试4:系统摘要
    print("📝 测试4: 优化摘要")
    summary = optimizer.get_optimization_summary()
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
