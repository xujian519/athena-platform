#!/usr/bin/env python3
from __future__ import annotations
"""
工作流模式数据结构

定义WorkflowPattern和WorkflowStep的数据模型。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TaskDomain(str, Enum):
    """任务领域"""
    PATENT = "patent"
    LEGAL = "legal"
    TRADEMARK = "trademark"
    COPYRIGHT = "copyright"
    GENERAL = "general"


class StepType(str, Enum):
    """步骤类型"""
    REASONING = "reasoning"  # 推理步骤
    TOOL_USE = "tool_use"    # 工具调用
    DECISION = "decision"    # 决策点


class WorkflowStep(BaseModel):
    """
    工作流步骤

    表示workflow中的一个原子操作或决策点。
    """
    step_id: str = Field(description="步骤唯一标识")
    name: str = Field(description="步骤名称")
    step_type: StepType = Field(description="步骤类型")
    description: str = Field(description="步骤描述")

    # 工具调用相关
    action: Optional[str] = Field(default=None, description="工具名称或动作")
    input_schema: dict[str, Any] = Field(default_factory=dict, description="输入schema")
    output_schema: dict[str, Any] = Field(default_factory=dict, description="输出schema")

    # 依赖关系
    dependencies: list[str] = Field(default_factory=list, description="依赖的步骤ID列表")

    # 元数据
    metadata: dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WorkflowPattern(BaseModel):
    """
    工作流模式

    从历史任务中提取的可复用workflow模式。
    包含完整的步骤序列、成功统计和使用记录。
    """
    # 基本信息
    pattern_id: str = Field(description="模式唯一标识")
    name: str = Field(description="模式名称")
    description: str = Field(description="模式描述")
    task_type: str = Field(description="任务类型")
    domain: TaskDomain = Field(description="任务领域")

    # Workflow步骤
    steps: list[WorkflowStep] = Field(description="工作流步骤列表")

    # 统计信息
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="成功率")
    usage_count: int = Field(default=0, ge=0, description="使用次数")
    total_executions: int = Field(default=0, ge=0, description="总执行次数")
    successful_executions: int = Field(default=0, ge=0, description="成功执行次数")

    # 性能指标
    avg_execution_time: float = Field(default=0.0, ge=0.0, description="平均执行时间(秒)")
    min_execution_time: float = Field(default=float('inf'), ge=0.0, description="最小执行时间")
    max_execution_time: float = Field(default=0.0, ge=0.0, description="最大执行时间")

    # 向量表示 (用于相似度检索)
    embedding: np.ndarray | None = Field(default=None, description="模式向量表示")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    last_used_at: datetime | None = Field(default=None, description="最后使用时间")

    # 变体和适应
    variations: dict[str, Any] = Field(default_factory=dict, description="模式变体")
    adaptation_rules: list[dict[str, Any]] = Field(default_factory=list, description="适应规则")

    # 成功标准
    success_criteria: dict[str, Any] = Field(default_factory=dict, description="成功标准")

    class Config:
        """Pydantic配置"""
        use_enum_values = True
        arbitrary_types_allowed = True  # 允许np.ndarray类型
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            np.ndarray: lambda v: v.tolist() if v is not None else None
        }

    def record_execution(
        self,
        success: bool,
        execution_time: float,
        timestamp: datetime | None = None
    ):
        """
        记录一次执行

        Args:
            success: 是否成功
            execution_time: 执行时间(秒)
            timestamp: 执行时间戳
        """
        self.total_executions += 1
        if success:
            self.successful_executions += 1

        # 更新成功率
        self.success_rate = self.successful_executions / self.total_executions

        # 更新执行时间统计
        if execution_time > 0:
            self.avg_execution_time = (
                (self.avg_execution_time * (self.total_executions - 1) + execution_time)
                / self.total_executions
            )
            self.min_execution_time = min(self.min_execution_time, execution_time)
            self.max_execution_time = max(self.max_execution_time, execution_time)

        # 更新时间戳
        self.last_used_at = timestamp or datetime.now()
        self.updated_at = datetime.now()

    def get_confidence(self) -> float:
        """
        计算模式的置信度

        置信度综合考虑:
        - 成功率 (50%)
        - 使用次数 (30%)
        - 最近使用情况 (20%)

        Returns:
            置信度分数 (0-1)
        """
        # 成功率得分
        success_score = self.success_rate

        # 使用次数得分 (对数缩放,避免无限增长)
        usage_score = min(1.0, np.log10(self.usage_count + 1) / 3.0)

        # 最近使用得分 (30天内衰减)
        if self.last_used_at:
            days_since_last_use = (datetime.now() - self.last_used_at).days
            recency_score = max(0.0, 1.0 - days_since_last_use / 30.0)
        else:
            recency_score = 0.0

        # 加权组合
        confidence = (
            0.5 * success_score +
            0.3 * usage_score +
            0.2 * recency_score
        )

        return confidence

    def can_adapt_to_task(
        self,
        task_description: str,
        threshold: float = 0.7,
        task_embedding: np.ndarray | None = None
    ) -> bool:
        """
        判断是否能适应到指定任务

        Args:
            task_description: 任务描述
            threshold: 相似度阈值
            task_embedding: 任务向量（可选，如果提供则使用向量相似度）

        Returns:
            是否可以适应
        """
        # 如果提供了task_embedding和pattern的embedding，使用余弦相似度
        if task_embedding is not None and self.embedding is not None:
            similarity = self._cosine_similarity(task_embedding, self.embedding)
            logger.debug(
                f"🎯 向量相似度: {similarity:.3f} "
                f"(阈值: {threshold})"
            )
            return similarity >= threshold

        # 否则，使用置信度作为近似
        confidence = self.get_confidence()
        logger.debug(
            f"📊 使用置信度评估: {confidence:.3f} "
            f"(阈值: {threshold})"
        )
        return confidence >= threshold

    def _cosine_similarity(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray
    ) -> float:
        """
        计算两个向量的余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            余弦相似度 (0-1之间)
        """
        try:
            # 确保向量是numpy数组
            vec1 = np.asarray(vec1, dtype=np.float32)
            vec2 = np.asarray(vec2, dtype=np.float32)

            # 计算余弦相似度
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)

            # 确保在[0, 1]范围内
            return float(max(0.0, min(1.0, similarity)))

        except Exception as e:
            logger.warning(f"⚠️ 计算余弦相似度失败: {e}")
            return 0.0

    def adapt_to_task(self, task_params: dict[str, Any]) -> WorkflowPattern:
        """
        适应当前任务参数

        Args:
            task_params: 任务参数

        Returns:
            适应后的新模式
        """
        # 创建模式的副本
        adapted = WorkflowPattern(**self.model_dump())

        # 应用适应规则
        for rule in self.adaptation_rules:
            if self._should_apply_rule(rule, task_params):
                adapted = self._apply_rule(adapted, rule, task_params)

        return adapted

    def _should_apply_rule(self, rule: dict, task_params: dict[str, Any]) -> bool:
        """判断是否应该应用适应规则"""
        condition = rule.get("condition", {})
        return all(task_params.get(key) == value for key, value in condition.items())

    def _apply_rule(
        self,
        pattern: WorkflowPattern,
        rule: dict[str, Any],        task_params: dict[str, Any]
    ) -> WorkflowPattern:
        """应用适应规则"""
        modifications = rule.get("modifications", {})

        for key, value in modifications.items():
            if hasattr(pattern, key):
                setattr(pattern, key, value)

        return pattern


class TaskTrajectory(BaseModel):
    """
    任务轨迹

    记录任务执行的完整轨迹,包括所有步骤、决策和结果。
    """
    task_id: str = Field(description="任务ID")
    task_description: str = Field(description="任务描述")
    task_type: str = Field(description="任务类型")
    domain: TaskDomain = Field(description="任务领域")

    # 执行步骤
    steps: list[WorkflowStep] = Field(description="执行的步骤列表")

    # 中间结果
    intermediate_results: dict[str, Any] = Field(
        default_factory=dict,
        description="中间结果"
    )

    # 最终结果
    final_result: Optional[dict[str, Any]] = Field(default=None, description="最终结果")

    # 执行统计
    start_time: datetime = Field(description="开始时间")
    end_time: datetime | None = Field(default=None, description="结束时间")
    total_steps: int = Field(default=0, description="总步数")
    execution_time: float = Field(default=0.0, description="执行时间(秒)")

    # 成功标志
    success: bool = Field(default=False, description="是否成功")
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="质量分数")

    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


__all__ = [
    'StepType',
    'TaskDomain',
    'TaskTrajectory',
    'WorkflowPattern',
    'WorkflowStep'
]
