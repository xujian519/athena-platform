#!/usr/bin/env python3
"""
审查意见答复输入验证模型
Office Action Response Input Validation Models

使用Pydantic增强输入验证，确保数据质量和系统稳定性

功能:
1. 请求模型验证
2. 参数类型检查
3. 数据约束验证
4. 自动类型转换

作者: 小诺·双鱼公主
创建时间: 2026-01-26
版本: v1.0.0
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from core.utils.error_handling import ConfigurationError


class RejectionType(str, Enum):
    """驳回类型枚举"""

    NOVELTY = "novelty"
    INVENTIVENESS = "inventiveness"
    UTILITY = "utility"
    CLARITY = "clarity"
    SUPPORT = "support"
    UNITY = "unity"


class StepType(str, Enum):
    """步骤类型枚举"""

    OA_ANALYSIS = "oa_analysis"
    PATENT_UNDERSTANDING = "patent_understanding"
    PRIOR_ART_SEARCH = "prior_art_search"
    STRATEGY_SELECTION = "strategy_selection"
    SUCCESS_PREDICTION = "success_prediction"
    ARGUMENT_GENERATION = "argument_generation"
    CLAIM_AMENDMENT = "claim_amendment"
    EVIDENCE_COLLECTION = "evidence_collection"
    RESPONSE_DRAFTING = "response_drafting"
    QUALITY_CHECK = "quality_check"
    FINAL_REVIEW = "final_review"


class RecordingStartRequest(BaseModel):
    """开始记录请求模型"""

    oa_id: str = Field(..., min_length=1, max_length=100, description="审查意见ID")
    patent_id: str = Field(..., min_length=1, max_length=100, description="专利ID")
    rejection_type: RejectionType = Field(..., description="驳回类型")
    task_name: str = Field(..., min_length=1, max_length=500, description="任务名称")

    @field_validator("oa_id", "patent_id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """验证ID格式"""
        # 移除前后空格
        v = v.strip()
        if not v:
            raise ValueError("ID不能为空")
        # 检查是否包含非法字符
        invalid_chars = ["<", ">", ":", "\"", "|", "?", "*", "\0"]
        if any(char in v for char in invalid_chars):
            raise ValueError(f"ID包含非法字符: {invalid_chars}")
        return v

    @field_validator("task_name")
    @classmethod
    def validate_task_name(cls, v: str) -> str:
        """验证任务名称"""
        v = v.strip()
        if not v:
            raise ValueError("任务名称不能为空")
        return v


class StepStartRequest(BaseModel):
    """步骤开始请求模型"""

    step_id: str = Field(..., min_length=1, max_length=100, description="步骤ID")
    step_type: StepType = Field(..., description="步骤类型")
    name: str = Field(..., min_length=1, max_length=200, description="步骤名称")
    description: str = Field(..., min_length=0, max_length=1000, description="步骤描述")
    inputs: dict[str, Any] = Field(default_factory=dict, description="输入数据")
    dependencies: list[str] = Field(default_factory=list, description="依赖的步骤ID")

    @field_validator("step_id")
    @classmethod
    def validate_step_id(cls, v: str) -> str:
        """验证步骤ID"""
        v = v.strip()
        if not v:
            raise ValueError("步骤ID不能为空")
        return v

    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(cls, v: list[str]) -> list[str]:
        """验证依赖关系"""
        # 确保依赖列表中没有重复
        if len(v) != len(set(v)):
            raise ValueError("依赖列表中存在重复的步骤ID")
        return v


class StepCompleteRequest(BaseModel):
    """步骤完成请求模型"""

    step_id: str = Field(..., min_length=1, max_length=100, description="步骤ID")
    outputs: dict[str, Any] = Field(default_factory=dict, description="输出数据")
    success: bool = Field(default=True, description="是否成功")
    error_message: str = Field(None, max_length=1000, description="错误信息")
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="质量分数")

    @field_validator("step_id")
    @classmethod
    def validate_step_id(cls, v: str) -> str:
        """验证步骤ID"""
        v = v.strip()
        if not v:
            raise ValueError("步骤ID不能为空")
        return v

    @field_validator("error_message")
    @classmethod
    def validate_error_message(cls, v: str | None) -> str | None:
        """验证错误信息"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    @model_validator(mode="after")
    def validate_consistency(self) -> "StepCompleteRequest":
        """验证数据一致性"""
        # 如果步骤失败，应该有错误信息
        if not self.success and not self.error_message:
            raise ValueError("失败的步骤必须提供错误信息")
        # 如果步骤成功且质量分数为0，给出警告但不阻止
        if self.success and self.quality_score == 0.0:
            pass  # 可以记录警告日志
        return self


class RecordingFinishRequest(BaseModel):
    """完成记录请求模型"""

    overall_success: bool = Field(default=True, description="整体是否成功")
    final_outcome: str = Field(
        None,
        description="最终结果 (allowed/rejected/partial)"
    )
    strategy_used: str = Field(None, max_length=100, description="使用的策略")
    success_probability: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="成功概率"
    )

    @field_validator("final_outcome")
    @classmethod
    def validate_final_outcome(cls, v: str | None) -> str | None:
        """验证最终结果"""
        if v is not None:
            v = v.strip().lower()
            valid_outcomes = ["allowed", "rejected", "partial"]
            if v not in valid_outcomes:
                raise ValueError(f"最终结果必须是以下之一: {valid_outcomes}")
        return v

    @field_validator("strategy_used")
    @classmethod
    def validate_strategy(cls, v: str | None) -> str | None:
        """验证策略名称"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class PatternSearchRequest(BaseModel):
    """模式搜索请求模型"""

    rejection_type: RejectionType = Field(..., description="驳回类型")
    top_k: int = Field(default=3, ge=1, le=10, description="返回数量")

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        """验证返回数量"""
        if v < 1:
            raise ValueError("返回数量必须大于0")
        if v > 10:
            raise ValueError("返回数量不能超过10")
        return v


class TrajectoryInfo(BaseModel):
    """轨迹信息模型"""

    trajectory_id: str
    oa_id: str
    patent_id: str
    rejection_type: str
    task_name: str
    steps_count: int = Field(ge=0, description="步骤数量")
    total_duration: float = Field(ge=0, description="总时长")
    avg_quality_score: float = Field(ge=0.0, le=1.0, description="平均质量分数")
    overall_success: bool
    final_outcome: str

    class Config:
        """Pydantic配置"""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


# ===== 验证辅助函数 =====


def validate_recording_start(**kwargs) -> RecordingStartRequest:
    """
    验证开始记录请求

    Args:
        **kwargs: 请求参数

    Returns:
        验证后的请求模型

    Raises:
        ConfigurationError: 验证失败
    """
    try:
        return RecordingStartRequest(**kwargs)
    except Exception as e:
        raise ConfigurationError(
            message=f"开始记录请求验证失败: {e}",
            context={"kwargs": kwargs}
        ) from e


def validate_step_start(**kwargs) -> StepStartRequest:
    """
    验证步骤开始请求

    Args:
        **kwargs: 请求参数

    Returns:
        验证后的请求模型

    Raises:
        ConfigurationError: 验证失败
    """
    try:
        return StepStartRequest(**kwargs)
    except Exception as e:
        raise ConfigurationError(
            message=f"步骤开始请求验证失败: {e}",
            context={"kwargs": kwargs}
        ) from e


def validate_step_complete(**kwargs) -> StepCompleteRequest:
    """
    验证步骤完成请求

    Args:
        **kwargs: 请求参数

    Returns:
        验证后的请求模型

    Raises:
        ConfigurationError: 验证失败
    """
    try:
        return StepCompleteRequest(**kwargs)
    except Exception as e:
        raise ConfigurationError(
            message=f"步骤完成请求验证失败: {e}",
            context={"kwargs": kwargs}
        ) from e


def validate_recording_finish(**kwargs) -> RecordingFinishRequest:
    """
    验证完成记录请求

    Args:
        **kwargs: 请求参数

    Returns:
        验证后的请求模型

    Raises:
        ConfigurationError: 验证失败
    """
    try:
        return RecordingFinishRequest(**kwargs)
    except Exception as e:
        raise ConfigurationError(
            message=f"完成记录请求验证失败: {e}",
            context={"kwargs": kwargs}
        ) from e


def validate_pattern_search(**kwargs) -> PatternSearchRequest:
    """
    验证模式搜索请求

    Args:
        **kwargs: 请求参数

    Returns:
        验证后的请求模型

    Raises:
        ConfigurationError: 验证失败
    """
    try:
        return PatternSearchRequest(**kwargs)
    except Exception as e:
        raise ConfigurationError(
            message=f"模式搜索请求验证失败: {e}",
            context={"kwargs": kwargs}
        ) from e
