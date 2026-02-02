#!/usr/bin/env python3
"""
学习引擎 - 自适应优化器
Learning Engine - Adaptive Optimizer

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import logging
from collections import deque
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class AdaptiveOptimizer:
    """自适应优化器"""

    def __init__(self):
        self.performance_history: deque[dict[str, Any]] = deque(maxlen=1000)
        self.optimization_strategies: dict[str, Any] = {}
        self.current_strategy = "default"

    async def optimize_parameters(
        self, current_performance: float, parameters: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """优化参数"""
        # 记录性能历史
        self.performance_history.append(
            {
                "timestamp": datetime.now(),
                "performance": current_performance,
                "parameters": parameters.copy(),
                "context": context.copy(),
            }
        )

        # 分析性能趋势
        if len(self.performance_history) >= 10:
            trend = self._analyze_performance_trend()

            # 根据趋势调整策略
            if trend < -0.1:  # 性能下降
                new_strategy = await self._select_recovery_strategy(parameters, context)
            elif trend > 0.1:  # 性能提升
                new_strategy = await self._select_enhancement_strategy(parameters, context)
            else:
                new_strategy = self.current_strategy

            if new_strategy != self.current_strategy:
                logger.info(f"切换优化策略: {self.current_strategy} -> {new_strategy}")
                self.current_strategy = new_strategy

        # 应用当前策略
        optimized_params = await self._apply_strategy(parameters, context)

        return optimized_params

    def _analyze_performance_trend(self) -> float:
        """分析性能趋势"""
        if len(self.performance_history) < 5:
            return 0.0

        recent_performances = [p["performance"] for p in list(self.performance_history)[-5:]]
        early_performances = [p["performance"] for p in list(self.performance_history)[-10:-5]]

        if not early_performances:
            return 0.0

        recent_avg = sum(recent_performances) / len(recent_performances)
        early_avg = sum(early_performances) / len(early_performances)

        return (recent_avg - early_avg) / early_avg if early_avg > 0 else 0.0

    async def _select_recovery_strategy(
        self, parameters: dict[str, Any], context: dict[str, Any]
    ) -> str:
        """选择恢复策略"""
        # 根据上下文选择最适合的恢复策略
        task_type = context.get("task_type", "unknown")

        strategy_map = {
            "reasoning": "conservative_reasoning",
            "communication": "adaptive_communication",
            "learning": "enhanced_learning",
            "default": "balanced_optimization",
        }

        return strategy_map.get(task_type, "balanced_optimization")

    async def _select_enhancement_strategy(
        self, parameters: dict[str, Any], context: dict[str, Any]
    ) -> str:
        """选择增强策略"""
        task_type = context.get("task_type", "unknown")

        strategy_map = {
            "reasoning": "deep_reasoning",
            "communication": "creative_communication",
            "learning": "rapid_learning",
            "default": "performance_boost",
        }

        return strategy_map.get(task_type, "performance_boost")

    async def _apply_strategy(
        self, parameters: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """应用优化策略"""
        optimized_params = parameters.copy()

        if self.current_strategy == "conservative_reasoning":
            optimized_params["depth"] = max(3, parameters.get("depth", 5) - 1)
            optimized_params["temperature"] = max(0.1, parameters.get("temperature", 0.7) - 0.2)

        elif self.current_strategy == "deep_reasoning":
            optimized_params["depth"] = min(10, parameters.get("depth", 5) + 2)
            optimized_params["temperature"] = min(1.0, parameters.get("temperature", 0.7) + 0.1)

        elif self.current_strategy == "adaptive_communication":
            optimized_params["style"] = "adaptive"
            optimized_params["personalization"] = True

        elif self.current_strategy == "creative_communication":
            optimized_params["creativity"] = min(1.0, parameters.get("creativity", 0.5) + 0.3)
            optimized_params["temperature"] = min(1.0, parameters.get("temperature", 0.7) + 0.2)

        elif self.current_strategy == "enhanced_learning":
            optimized_params["learning_rate"] = min(1.0, parameters.get("learning_rate", 0.1) + 0.2)
            optimized_params["exploration"] = True

        elif self.current_strategy == "rapid_learning":
            optimized_params["learning_rate"] = min(1.0, parameters.get("learning_rate", 0.1) + 0.4)
            optimized_params["batch_size"] = parameters.get("batch_size", 32) * 2

        return optimized_params


__all__ = ["AdaptiveOptimizer"]
