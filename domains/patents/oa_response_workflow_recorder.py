#!/usr/bin/env python3
from __future__ import annotations

"""
审查意见答复工作流记录器
Office Action Response Workflow Recorder

用于记录OA答复的全过程，支持后续的模式提取和复用

功能:
1. 记录OA答复的完整流程
2. 跟踪每个步骤的执行状态
3. 收集性能指标和质量数据
4. 生成可复用的工作流模式

作者: 小诺·双鱼公主
创建时间: 2026-01-26
版本: v1.0.0
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging
from core.utils.error_handling import (
    ConfigurationError,
    WorkflowRecordError,
)

logger = setup_logging()


class OAStepType(Enum):
    """OA答复步骤类型"""

    # 分析阶段
    OA_ANALYSIS = "oa_analysis"  # 审查意见分析
    PATENT_UNDERSTANDING = "patent_understanding"  # 专利理解
    PRIOR_ART_SEARCH = "prior_art_search"  # 对比文件检索

    # 策略阶段
    STRATEGY_SELECTION = "strategy_selection"  # 策略选择
    SUCCESS_PREDICTION = "success_prediction"  # 成功率预测

    # 答复阶段
    ARGUMENT_GENERATION = "argument_generation"  # 论点生成
    CLAIM_AMENDMENT = "claim_amendment"  # 权利要求修改
    EVIDENCE_COLLECTION = "evidence_collection"  # 证据收集
    RESPONSE_DRAFTING = "response_drafting"  # 答复起草

    # 审核阶段
    QUALITY_CHECK = "quality_check"  # 质量检查
    FINAL_REVIEW = "final_review"  # 最终审核


class StepStatus(Enum):
    """步骤状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStepRecord:
    """工作流步骤记录"""

    step_id: str
    step_type: OAStepType
    name: str
    description: str

    # 执行信息
    status: StepStatus = StepStatus.PENDING
    start_time: str | None = None
    end_time: str | None = None
    duration: float = 0.0

    # 输入输出
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)

    # 结果评估
    success: bool = True
    error_message: str | None = None
    quality_score: float = 0.0  # 0-1

    # 依赖关系
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "step_id": self.step_id,
            "step_type": self.step_type.value,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "success": self.success,
            "error_message": self.error_message,
            "quality_score": self.quality_score,
            "dependencies": self.dependencies,
        }


@dataclass
class OAResponseTrajectory:
    """OA答复任务轨迹"""

    trajectory_id: str
    oa_id: str
    patent_id: str
    rejection_type: str

    # 任务信息
    task_name: str
    task_type: str = "OA_RESPONSE"
    domain: str = "PATENT"

    # 执行记录
    steps: list[WorkflowStepRecord] = field(default_factory=list)

    # 时间信息
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str | None = None
    total_duration: float = 0.0

    # 结果评估
    overall_success: bool = True
    final_outcome: str | None = None  # "allowed", "rejected", "partial"

    # 质量指标
    avg_quality_score: float = 0.0
    strategy_used: str | None = None
    success_probability: float = 0.0

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_step(self, step: WorkflowStepRecord):
        """添加步骤记录"""
        self.steps.append(step)

    def get_step_by_id(self, step_id: str) -> WorkflowStepRecord | None:
        """根据ID获取步骤"""
        return next((s for s in self.steps if s.step_id == step_id), None)

    def get_completed_steps(self) -> list[WorkflowStepRecord]:
        """获取已完成的步骤"""
        return [s for s in self.steps if s.status == StepStatus.COMPLETED]

    def get_failed_steps(self) -> list[WorkflowStepRecord]:
        """获取失败的步骤"""
        return [s for s in self.steps if s.status == StepStatus.FAILED]

    def calculate_metrics(self):
        """计算轨迹指标"""
        if not self.steps:
            return

        # 计算总时长
        completed_steps = self.get_completed_steps()
        if completed_steps:
            self.total_duration = sum(s.duration for s in completed_steps)

        # 计算平均质量分数
        quality_scores = [s.quality_score for s in completed_steps if s.quality_score > 0]
        if quality_scores:
            self.avg_quality_score = sum(quality_scores) / len(quality_scores)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        self.calculate_metrics()
        return {
            "trajectory_id": self.trajectory_id,
            "oa_id": self.oa_id,
            "patent_id": self.patent_id,
            "rejection_type": self.rejection_type,
            "task_name": self.task_name,
            "task_type": self.task_type,
            "domain": self.domain,
            "steps": [s.to_dict() for s in self.steps],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration": self.total_duration,
            "overall_success": self.overall_success,
            "final_outcome": self.final_outcome,
            "avg_quality_score": self.avg_quality_score,
            "strategy_used": self.strategy_used,
            "success_probability": self.success_probability,
            "created_at": self.created_at,
        }


class OAResponseWorkflowRecorder:
    """
    OA答复工作流记录器

    负责记录OA答复的完整过程，为后续模式提取提供数据
    """

    def __init__(self, storage_path: str = "data/oa_responses/workflows"):
        """初始化记录器"""
        try:
            self.storage_path = Path(storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self.current_trajectory: OAResponseTrajectory | None = None
            logger.info("📝 OA答复工作流记录器初始化完成")
        except (OSError, PermissionError) as e:
            error = ConfigurationError(
                message=f"创建存储路径失败: {storage_path}",
                context={"storage_path": storage_path}
            )
            logger.error(f"{error.message}: {e}")
            raise error from e

    def start_recording(
        self,
        oa_id: str,
        patent_id: str,
        rejection_type: str,
        task_name: str,
    ) -> OAResponseTrajectory:
        """
        开始记录新的答复任务

        Args:
            oa_id: 审查意见ID
            patent_id: 专利ID
            rejection_type: 驳回类型
            task_name: 任务名称

        Returns:
            任务轨迹对象
        """
        trajectory_id = f"{oa_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        trajectory = OAResponseTrajectory(
            trajectory_id=trajectory_id,
            oa_id=oa_id,
            patent_id=patent_id,
            rejection_type=rejection_type,
            task_name=task_name,
        )

        self.current_trajectory = trajectory

        logger.info(f"🎬 开始记录OA答复任务: {trajectory_id}")
        logger.info(f"  OA ID: {oa_id}")
        logger.info(f"  专利ID: {patent_id}")
        logger.info(f"  驳回类型: {rejection_type}")

        return trajectory

    def record_step_start(
        self,
        step_id: str,
        step_type: OAStepType,
        name: str,
        description: str,
        inputs: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
    ) -> WorkflowStepRecord:
        """
        记录步骤开始

        Args:
            step_id: 步骤ID
            step_type: 步骤类型
            name: 步骤名称
            description: 步骤描述
            inputs: 输入数据
            dependencies: 依赖的步骤ID

        Returns:
            步骤记录对象
        """
        if not self.current_trajectory:
            logger.warning("⚠️ 没有活跃的轨迹记录")
            return None

        step = WorkflowStepRecord(
            step_id=step_id,
            step_type=step_type,
            name=name,
            description=description,
            inputs=inputs or {},
            dependencies=dependencies or [],
            status=StepStatus.IN_PROGRESS,
            start_time=datetime.now().isoformat(),
        )

        self.current_trajectory.add_step(step)

        logger.info(f"▶️  步骤开始: {name} ({step_id})")

        return step

    def record_step_complete(
        self,
        step_id: str,
        outputs: dict[str, Any] | None = None,
        success: bool = True,
        error_message: str | None = None,
        quality_score: float = 0.0,
    ):
        """
        记录步骤完成

        Args:
            step_id: 步骤ID
            outputs: 输出数据
            success: 是否成功
            error_message: 错误信息
            quality_score: 质量分数 (0-1)
        """
        if not self.current_trajectory:
            return

        step = self.current_trajectory.get_step_by_id(step_id)
        if not step:
            logger.warning(f"⚠️ 未找到步骤: {step_id}")
            return

        step.status = StepStatus.COMPLETED if success else StepStatus.FAILED
        step.end_time = datetime.now().isoformat()
        step.outputs = outputs or {}
        step.success = success
        step.error_message = error_message
        step.quality_score = quality_score

        # 计算持续时间
        if step.start_time:
            start = datetime.fromisoformat(step.start_time)
            end = datetime.fromisoformat(step.end_time)
            step.duration = (end - start).total_seconds()

        status_icon = "✅" if success else "❌"
        logger.info(f"{status_icon} 步骤完成: {step.name} ({step.duration:.2f}s)")

    def finish_recording(
        self,
        overall_success: bool = True,
        final_outcome: str | None = None,
        strategy_used: str | None = None,
        success_probability: float = 0.0,
    ) -> OAResponseTrajectory:
        """
        完成记录

        Args:
            overall_success: 整体是否成功
            final_outcome: 最终结果
            strategy_used: 使用的策略
            success_probability: 成功概率

        Returns:
            完整的任务轨迹
        """
        if not self.current_trajectory:
            logger.warning("⚠️ 没有活跃的轨迹记录")
            return None

        trajectory = self.current_trajectory

        trajectory.end_time = datetime.now().isoformat()
        trajectory.overall_success = overall_success
        trajectory.final_outcome = final_outcome
        trajectory.strategy_used = strategy_used
        trajectory.success_probability = success_probability

        # 计算总时长
        trajectory.calculate_metrics()

        # 保存到文件
        self._save_trajectory(trajectory)

        logger.info(f"🏁 轨迹记录完成: {trajectory.trajectory_id}")
        logger.info(f"  总步骤数: {len(trajectory.steps)}")
        logger.info(f"  成功步骤: {len(trajectory.get_completed_steps())}")
        logger.info(f"  失败步骤: {len(trajectory.get_failed_steps())}")
        logger.info(f"  总时长: {trajectory.total_duration:.2f}s")
        logger.info(f"  平均质量: {trajectory.avg_quality_score:.2f}")

        self.current_trajectory = None

        return trajectory

    def _save_trajectory(self, trajectory: OAResponseTrajectory):
        """保存轨迹到文件"""
        filename = f"{trajectory.trajectory_id}.json"
        filepath = self.storage_path / filename

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(trajectory.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"💾 轨迹已保存: {filepath}")
        except OSError as e:
            error = WorkflowRecordError(
                message=f"保存轨迹文件失败: {filepath}",
                context={"trajectory_id": trajectory.trajectory_id, "filepath": str(filepath)}
            )
            logger.error(f"{error.message}: {e}")
            raise error from e
        except (TypeError, ValueError) as e:
            error = WorkflowRecordError(
                message=f"轨迹数据序列化失败: {trajectory.trajectory_id}",
                context={"trajectory_id": trajectory.trajectory_id}
            )
            logger.error(f"{error.message}: {e}")
            raise error from e

    def save_trajectory_markdown(self, trajectory: OAResponseTrajectory) -> str:
        """
        保存轨迹为Markdown格式

        Args:
            trajectory: 任务轨迹

        Returns:
            Markdown文件路径
        """
        filename = f"{trajectory.trajectory_id}.md"
        filepath = self.storage_path / filename

        md_lines = [
            f"# OA答复工作流: {trajectory.task_name}",
            "",
            "## 📋 基本信息",
            "",
            f"- **轨迹ID**: `{trajectory.trajectory_id}`",
            f"- **OA ID**: `{trajectory.oa_id}`",
            f"- **专利ID**: `{trajectory.patent_id}`",
            f"- **驳回类型**: `{trajectory.rejection_type}`",
            f"- **开始时间**: {trajectory.start_time}",
            f"- **结束时间**: {trajectory.end_time or '进行中'}",
            "",
            "## 📊 执行摘要",
            "",
            f"- **总步骤数**: {len(trajectory.steps)}",
            f"- **成功步骤**: {len(trajectory.get_completed_steps())}",
            f"- **失败步骤**: {len(trajectory.get_failed_steps())}",
            f"- **总时长**: {trajectory.total_duration:.2f}秒",
            f"- **平均质量**: {trajectory.avg_quality_score:.2f}",
            f"- **整体成功**: {'✅ 是' if trajectory.overall_success else '❌ 否'}",
            "",
            "## 🎯 答复结果",
            "",
            f"- **最终结果**: `{trajectory.final_outcome or '待定'}`",
            f"- **使用策略**: `{trajectory.strategy_used or '未指定'}`",
            f"- **成功概率**: {trajectory.success_probability:.1%}",
            "",
            "## 📝 执行步骤",
            "",
        ]

        for i, step in enumerate(trajectory.steps, 1):
            status_icon = {
                StepStatus.PENDING: "⏳",
                StepStatus.IN_PROGRESS: "🔄",
                StepStatus.COMPLETED: "✅",
                StepStatus.FAILED: "❌",
                StepStatus.SKIPPED: "⏭️",
            }.get(step.status, "❓")

            md_lines.extend([
                f"### {status_icon} 步骤 {i}: {step.name}",
                "",
                f"- **步骤ID**: `{step.step_id}`",
                f"- **类型**: `{step.step_type.value}`",
                f"- **状态**: `{step.status.value}`",
                f"- **描述**: {step.description}",
                "",
            ])

            if step.start_time:
                md_lines.append(f"- **开始时间**: {step.start_time}")
            if step.end_time:
                md_lines.append(f"- **结束时间**: {step.end_time}")
            if step.duration > 0:
                md_lines.append(f"- **耗时**: {step.duration:.2f}秒")

            if step.inputs:
                md_lines.extend([
                    "",
                    "**输入数据**:",
                    "```json",
                    json.dumps(step.inputs, ensure_ascii=False, indent=2),
                    "```",
                ])

            if step.outputs:
                md_lines.extend([
                    "",
                    "**输出数据**:",
                    "```json",
                    json.dumps(step.outputs, ensure_ascii=False, indent=2),
                    "```",
                ])

            if step.error_message:
                md_lines.extend([
                    "",
                    f"**错误信息**: {step.error_message}",
                ])

            if step.quality_score > 0:
                md_lines.append(f"**质量分数**: {step.quality_score:.2f}")

            md_lines.append("")

        # 写入文件
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(md_lines))
            logger.info(f"📄 Markdown轨迹已保存: {filepath}")
        except OSError as e:
            error = WorkflowRecordError(
                message=f"保存Markdown轨迹文件失败: {filepath}",
                context={"trajectory_id": trajectory.trajectory_id, "filepath": str(filepath)}
            )
            logger.error(f"{error.message}: {e}")
            raise error from e
        except Exception as e:
            error = WorkflowRecordError(
                message="生成Markdown轨迹时发生未知错误",
                context={"trajectory_id": trajectory.trajectory_id}
            )
            logger.error(f"{error.message}: {e}")
            raise error from e

        return str(filepath)


# ===== 全局单例 =====

_recorder_instance: OAResponseWorkflowRecorder | None = None


def get_oa_workflow_recorder() -> OAResponseWorkflowRecorder:
    """获取OA工作流记录器单例"""
    global _recorder_instance
    if _recorder_instance is None:
        _recorder_instance = OAResponseWorkflowRecorder()
    return _recorder_instance
