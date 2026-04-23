#!/usr/bin/env python3

"""
增强执行步骤 - 添加验证支持
Enhanced Execution Step - With Verification Support

扩展 ExecutionStep 添加验证相关字段

Author: Athena Team
Version: 1.0.0
Date: 2026-02-26
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from core.cognition.xiaonuo_planner_engine import ExecutionStep


@dataclass
class VerificationConfig:
    """验证配置"""
    enabled: bool = True  # 是否启用验证
    required: bool = True  # 验证是否必须通过（False时警告不中断）
    verifier_type: Optional[str] = None  # 指定验证器类型
    custom_criteria: Optional[dict[str, Any]] = None  # 自定义验证标准
    timeout_seconds: int = 30  # 验证超时时间


@dataclass
class EnhancedExecutionStep(ExecutionStep):
    """
    增强执行步骤 - 支持验证

    继承自 ExecutionStep，添加验证相关字段
    """
    verification: VerificationConfig = field(default_factory=VerificationConfig)
    expected_output_schema: Optional[dict[str, Any]] = None  # 期望的输出格式
    success_conditions: list[str] = field(default_factory=list)  # 成功条件
    retry_on_failure: bool = False  # 验证失败时是否重试
    max_retries: int = 0  # 最大重试次数

    @classmethod
    def from_step(
        cls,
        step: ExecutionStep,
        verification: Optional[VerificationConfig] = None,
    ) -> EnhancedExecutionStep:
        """
        从普通 ExecutionStep 创建增强步骤

        Args:
            step: 原始执行步骤
            verification: 验证配置

        Returns:
            EnhancedExecutionStep: 增强执行步骤
        """
        return cls(
            id=step.id,
            description=step.description,
            agent=step.agent,
            action=step.action,
            parameters=step.parameters,
            dependencies=step.dependencies,
            estimated_time=step.estimated_time,
            required_resources=step.required_resources,
            fallback_strategy=step.fallback_strategy,
            verification=verification or VerificationConfig(),
        )


def enhance_step_with_verification(
    step: ExecutionStep,
    action_type: str,
) -> EnhancedExecutionStep:
    """
    根据操作类型自动添加验证配置

    Args:
        step: 原始执行步骤
        action_type: 操作类型（用于选择验证器）

    Returns:
        EnhancedExecutionStep: 增强执行步骤
    """
    # 根据操作类型确定验证配置
    verification_config = VerificationConfig(
        enabled=True,
        required=False,  # 默认不阻塞（警告不中断）
        verifier_type=action_type,
    )

    # 为不同操作类型设置特定配置
    if action_type in ["patent_search", "patent_analyze"]:
        verification_config.required = True
        verification_config.timeout_seconds = 30
    elif action_type in ["claim_draft", "claim_drafting"]:
        verification_config.required = True
        verification_config.timeout_seconds = 60

    return EnhancedExecutionStep.from_step(step, verification_config)


# ========== 导出 ==========


__all__ = [
    "VerificationConfig",
    "EnhancedExecutionStep",
    "enhance_step_with_verification",
]

