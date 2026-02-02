#!/usr/bin/env python3
"""
自适应元规划器 - 性能跟踪器
Adaptive Meta Planner - Performance Tracker

作者: Athena平台团队
创建时间: 2026-01-20
重构时间: 2026-01-26
版本: 2.0.0
"""

import logging
from typing import Any

from ..models import ComplexityLevel, StrategyType
from .types import StrategyPerformance


logger = logging.getLogger(__name__)


class PerformanceTracker:
    """性能跟踪器"""

    def __init__(self):
        # 性能数据: (task_type, complexity, strategy) -> StrategyPerformance
        self._performance: dict[tuple, StrategyPerformance] = {}

        logger.info("📊 性能跟踪器初始化完成")

    def get_performance(
        self, task_type: str, complexity: ComplexityLevel, strategy: StrategyType
    ) -> StrategyPerformance | None:
        """获取策略性能数据"""
        key = (task_type, complexity, strategy)
        return self._performance.get(key)

    def record_performance(
        self,
        task_type: str,
        complexity: ComplexityLevel,
        strategy: StrategyType,
        success: bool,
        execution_time: float,
        quality_score: float,
    ) -> None:
        """记录策略性能"""
        key = (task_type, complexity, strategy)

        if key not in self._performance:
            self._performance[key] = StrategyPerformance(
                strategy=strategy, task_type=task_type, complexity=complexity
            )

        self._performance[key].update(success, execution_time, quality_score)

        logger.debug(
            f"📈 性能记录: {strategy.value} | "
            f"{'成功' if success else '失败'} | "
            f"耗时: {execution_time:.2f}s | "
            f"质量: {quality_score:.2f}"
        )

    def get_best_strategy(
        self, task_type: str, complexity: ComplexityLevel
    ) -> StrategyType | None:
        """获取最佳策略"""
        candidates = []

        # 收集所有有数据的策略
        for key, perf in self._performance.items():
            if key[0] == task_type and key[1] == complexity:
                if perf.total_executions >= 3:  # 至少3次执行
                    candidates.append((perf, perf.success_rate))

        if not candidates:
            return None

        # 选择成功率最高的策略
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_perf = candidates[0][0]

        logger.debug(
            f"🏆 最佳策略: {best_perf.strategy.value} " f"(成功率: {best_perf.success_rate:.2%})"
        )

        return best_perf.strategy

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        total_records = len(self._performance)
        total_executions = sum(p.total_executions for p in self._performance.values())

        return {
            "total_records": total_records,
            "total_executions": total_executions,
            "strategies_tracked": len({p.strategy for p in self._performance.values()}),
        }
