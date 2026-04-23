#!/usr/bin/env python3

"""
失败恢复处理器 - Minitap式智能重规划
Failure Recovery Handler - Minitap-Style Intelligent Replanning

当步骤失败时，自动回退并重新规划剩余任务

Author: Athena Team
Version: 1.0.0
Date: 2026-02-26
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from core.cognition.checkpoint import CheckpointManager, get_checkpoint_manager
from core.cognition.xiaonuo_planner_engine import (
    ExecutionPlan,
    ExecutionStep,
)

logger = logging.getLogger(__name__)


# ========== 失败处理策略 ==========


class FailureStrategy(Enum):
    """失败处理策略"""
    RETRY = "retry"  # 重试当前步骤
    SKIP = "skip"  # 跳过当前步骤
    ROLLBACK = "rollback"  # 回退到上一个检查点
    REPLAN = "replan"  # 重新规划
    ABORT = "abort"  # 中止执行


@dataclass
class FailureAnalysis:
    """失败分析结果"""
    failed_step_id: str
    error_type: str  # 错误类型
    error_message: str
    suggested_strategy: FailureStrategy
    retry_count: int = 0
    max_retries: int = 3
    can_skip: bool = False  # 是否可以跳过此步骤
    alternative_actions: list[str] = field(default_factory=list)  # 替代操作


# ========== 失败分析器 ==========


class FailureAnalyzer:
    """
    失败分析器

    分析失败原因并建议处理策略
    """

    def __init__(self, llm_manager=None):
        """
        初始化失败分析器

        Args:
            llm_manager: LLM管理器（用于智能分析）
        """
        self.llm_manager = llm_manager

        # 错误模式匹配规则
        self.error_patterns = {
            # 网络错误
            "network": [
                "connection refused",
                "timeout",
                "network unreachable",
                "ConnectionError",
                "TimeoutError",
            ],
            # 数据错误
            "data": [
                "invalid data",
                "parsing error",
                "ValueError",
                "KeyError",
            ],
            # 权限错误
            "permission": [
                "permission denied",
                "AccessDenied",
                "Unauthorized",
            ],
            # 资源不足
            "resource": [
                "out of memory",
                "disk full",
                "OutOfMemoryError",
            ],
        }

    async def analyze_failure(
        self,
        step: ExecutionStep,
        error: Exception,
        retry_count: int = 0,
    ) -> FailureAnalysis:
        """
        分析失败原因

        Args:
            step: 失败的步骤
            error: 错误信息
            retry_count: 当前重试次数

        Returns:
            FailureAnalysis: 失败分析结果
        """
        error_message = str(error)
        error_type = self._classify_error(error_message)

        logger.info(f"🔍 分析失败: {step.id}")
        logger.info(f"   错误类型: {error_type}")
        logger.info(f"   错误信息: {error_message[:100]}")

        # 根据错误类型确定策略
        strategy = self._determine_strategy(error_type, step, retry_count)

        # 检查是否可以跳过
        can_skip = self._can_skip_step(step)

        # 建议替代操作
        alternative_actions = self._suggest_alternatives(step, error_type)

        analysis = FailureAnalysis(
            failed_step_id=step.id,
            error_type=error_type,
            error_message=error_message,
            suggested_strategy=strategy,
            retry_count=retry_count,
            can_skip=can_skip,
            alternative_actions=alternative_actions,
        )

        logger.info(f"   建议策略: {strategy.value}")
        logger.info(f"   可以跳过: {can_skip}")

        return analysis

    def _classify_error(self, error_message: str) -> str:
        """分类错误类型"""
        error_lower = error_message.lower()

        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern.lower() in error_lower:
                    return error_type

        return "unknown"

    def _determine_strategy(
        self,
        error_type: str,
        step: ExecutionStep,
        retry_count: int,
    ) -> FailureStrategy:
        """确定处理策略"""
        # 网络错误：重试
        if error_type == "network":
            if retry_count < 3:
                return FailureStrategy.RETRY
            else:
                return FailureStrategy.REPLAN

        # 数据错误：跳过或重规划
        if error_type == "data":
            if step.fallback_strategy:
                return FailureStrategy.SKIP
            else:
                return FailureStrategy.REPLAN

        # 权限错误：中止
        if error_type == "permission":
            return FailureStrategy.ABORT

        # 资源不足：重规划
        if error_type == "resource":
            return FailureStrategy.REPLAN

        # 默认：重试
        if retry_count < 1:
            return FailureStrategy.RETRY

        return FailureStrategy.ABORT

    def _can_skip_step(self, step: ExecutionStep) -> bool:
        """检查是否可以跳过步骤"""
        # 如果没有依赖此步骤，可以跳过
        return not step.dependencies

    def _suggest_alternatives(
        self,
        step: ExecutionStep,
        error_type: str,
    ) -> list[str]:
        """建议替代操作"""
        alternatives = []

        # 根据错误类型建议替代方案
        if error_type == "network":
            alternatives = [
                f"{step.action}_fallback",
                f"{step.action}_retry",
            ]
        elif error_type == "data":
            alternatives = [
                f"{step.action}_simplified",
                f"{step.action}_with_defaults",
            ]
        else:
            alternatives = [
                f"{step.action}_alternative",
            ]

        return alternatives


# ========== 失败恢复处理器 ==========


class FailureRecoveryHandler:
    """
    失败恢复处理器

    处理步骤失败，执行回退、重规划等操作
    """

    def __init__(
        self,
        checkpoint_manager: Optional[CheckpointManager] = None,
        failure_analyzer: Optional[FailureAnalyzer] = None,
    ):
        """
        初始化失败恢复处理器

        Args:
            checkpoint_manager: 检查点管理器
            failure_analyzer: 失败分析器
        """
        self.checkpoint_manager = checkpoint_manager or get_checkpoint_manager()
        self.failure_analyzer = failure_analyzer or FailureAnalyzer()

        logger.info("🔄 失败恢复处理器初始化")

    async def handle_failure(
        self,
        step: ExecutionStep,
        error: Exception,
        execution_plan: ExecutionPlan,
        task_id: str,
        completed_steps: list[str],
        retry_count: int = 0,
    ) -> dict[str, Any]:
        """
        处理步骤失败

        Args:
            step: 失败的步骤
            error: 错误
            execution_plan: 执行方案
            task_id: 任务ID
            completed_steps: 已完成的步骤列表
            retry_count: 当前重试次数

        Returns:
            Dict: 处理结果
        """
        logger.info(f"🔧 处理步骤失败: {step.id}")

        # 分析失败
        analysis = await self.failure_analyzer.analyze_failure(
            step,
            error,
            retry_count,
        )

        # 根据策略处理
        strategy = analysis.suggested_strategy

        if strategy == FailureStrategy.RETRY:
            return await self._handle_retry(step, analysis, retry_count)

        elif strategy == FailureStrategy.SKIP:
            return await self._handle_skip(step, analysis)

        elif strategy == FailureStrategy.ROLLBACK:
            return await self._handle_rollback(
                task_id,
                analysis,
            )

        elif strategy == FailureStrategy.REPLAN:
            return await self._handle_replan(
                execution_plan,
                task_id,
                completed_steps,
                analysis,
            )

        else:  # ABORT
            return await self._handle_abort(analysis)

    async def _handle_retry(
        self,
        step: ExecutionStep,
        analysis: FailureAnalysis,
        retry_count: int,
    ) -> dict[str, Any]:
        """处理重试策略"""
        logger.info(f"   🔄 重试步骤: {step.id} (第 {retry_count + 1} 次)")

        if retry_count >= analysis.max_retries:
            logger.error(f"   ❌ 达到最大重试次数: {analysis.max_retries}")
            return {
                "action": "abort",
                "reason": "max_retries_exceeded",
            }

        return {
            "action": "retry",
            "retry_count": retry_count + 1,
            "message": f"重试第 {retry_count + 1} 次",
        }

    async def _handle_skip(
        self,
        step: ExecutionStep,
        analysis: FailureAnalysis,
    ) -> dict[str, Any]:
        """处理跳过策略"""
        logger.info(f"   ⏭️ 跳过步骤: {step.id}")

        return {
            "action": "skip",
            "skipped_step": step.id,
            "message": f"跳过失败步骤: {step.description}",
        }

    async def _handle_rollback(
        self,
        task_id: str,
        analysis: FailureAnalysis,
    ) -> dict[str, Any]:
        """处理回退策略"""
        logger.info(f"   ⏪ 回退到上一个检查点: {task_id}")

        # 加载最新检查点
        checkpoint = self.checkpoint_manager.get_latest_checkpoint(task_id)

        if checkpoint:
            logger.info(
                f"   📂 找到检查点: {checkpoint.checkpoint_id}"
            )
            logger.info(
                f"   可从步骤 {checkpoint.current_step} 继续执行"
            )

            return {
                "action": "rollback",
                "checkpoint_id": checkpoint.checkpoint_id,
                "checkpoint": checkpoint,
                "message": f"回退到检查点 {checkpoint.checkpoint_id}",
            }
        else:
            logger.warning("   ⚠️ 未找到检查点，无法回退")
            return {
                "action": "abort",
                "reason": "no_checkpoint",
            }

    async def _handle_replan(
        self,
        execution_plan: ExecutionPlan,
        task_id: str,
        completed_steps: list[str],
        analysis: FailureAnalysis,
    ) -> dict[str, Any]:
        """处理重新规划策略"""
        logger.info("   📋 重新规划剩余任务...")

        # 这里可以调用LLM进行智能重规划
        # 当前实现：简化版本

        # 找出未完成的步骤
        remaining_steps = [
            step for step in execution_plan.steps
            if step.id not in completed_steps
        ]

        logger.info(f"   📊 剩余 {len(remaining_steps)} 个步骤")

        # 生成新的执行计划
        new_plan_id = f"replan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return {
            "action": "replan",
            "new_plan_id": new_plan_id,
            "remaining_steps": [s.id for s in remaining_steps],
            "message": f"重新规划 {len(remaining_steps)} 个剩余步骤",
        }

    async def _handle_abort(
        self,
        analysis: FailureAnalysis,
    ) -> dict[str, Any]:
        """处理中止策略"""
        logger.error(f"   🛑 中止执行: {analysis.failed_step_id}")

        return {
            "action": "abort",
            "reason": "user_abort",
            "error": analysis.error_message,
        }


# ========== 导出 ==========


__all__ = [
    "FailureStrategy",
    "FailureAnalysis",
    "FailureAnalyzer",
    "FailureRecoveryHandler",
]

