#!/usr/bin/env python3
from __future__ import annotations
"""
审查意见答复模式提取器
Office Action Response Pattern Extractor

从OA答复轨迹中提取可复用的工作流模式

功能:
1. 将OAResponseTrajectory转换为WorkflowPattern
2. 分析成功模式并提取关键步骤
3. 生成可复用的答复模板
4. 导出为Markdown格式

作者: 小诺·双鱼公主
创建时间: 2026-01-26
版本: v1.0.0
"""

from datetime import datetime
from typing import Any

from core.logging_config import setup_logging
from core.memory.cross_task_workflow_memory import CrossTaskWorkflowMemory
from core.memory.serializers.markdown_serializer import PatternMarkdownSerializer
from core.memory.workflow_pattern import (
    StepType,
    TaskDomain,
    WorkflowPattern,
    WorkflowStep,
)
from core.patent.oa_response_workflow_recorder import (
    OAResponseTrajectory,
    OAStepType,
    StepStatus,
)
from core.utils.error_handling import (
    ConfigurationError,
    KnowledgeGraphError,
    PatternExtractionError,
    timeout,
)

logger = setup_logging()


class OAResponsePatternExtractor:
    """
    OA答复模式提取器

    负责从完成的OA答复任务中提取可复用的工作流模式
    """

    def __init__(self):
        """初始化提取器"""
        try:
            self.memory = CrossTaskWorkflowMemory(
                storage_path="data/oa_responses/patterns",
                enable_markdown_export=True,
                enable_vector_search=True,
            )
            self.serializer = PatternMarkdownSerializer()
            logger.info("🔍 OA答复模式提取器初始化完成")
        except (OSError, PermissionError) as e:
            error = ConfigurationError(
                message="初始化模式存储失败",
                context={"storage_path": "data/oa_responses/patterns"}
            )
            logger.error(f"{error.message}: {e}")
            raise error from e
        except Exception as e:
            error = ConfigurationError(
                message="初始化模式提取器失败",
                context={"error_type": type(e).__name__}
            )
            logger.error(f"{error.message}: {e}")
            raise error from e

    def step_type_mapping(self, oa_step_type: OAStepType) -> StepType:
        """
        将OA步骤类型映射到通用工作流步骤类型

        Args:
            oa_step_type: OA步骤类型

        Returns:
            通用工作流步骤类型
        """
        mapping = {
            OAStepType.OA_ANALYSIS: StepType.REASONING,
            OAStepType.PATENT_UNDERSTANDING: StepType.REASONING,
            OAStepType.PRIOR_ART_SEARCH: StepType.TOOL_USE,
            OAStepType.STRATEGY_SELECTION: StepType.DECISION,
            OAStepType.SUCCESS_PREDICTION: StepType.REASONING,
            OAStepType.ARGUMENT_GENERATION: StepType.TOOL_USE,
            OAStepType.CLAIM_AMENDMENT: StepType.TOOL_USE,
            OAStepType.EVIDENCE_COLLECTION: StepType.TOOL_USE,
            OAStepType.RESPONSE_DRAFTING: StepType.TOOL_USE,
            OAStepType.QUALITY_CHECK: StepType.TOOL_USE,
            OAStepType.FINAL_REVIEW: StepType.REASONING,
        }

        return mapping.get(oa_step_type, StepType.TOOL_USE)

    def extract_pattern_from_trajectory(
        self,
        trajectory: OAResponseTrajectory,
    ) -> WorkflowPattern | None:
        """
        从轨迹中提取工作流模式

        Args:
            trajectory: OA答复轨迹

        Returns:
            工作流模式，如果提取失败返回None
        """
        if not trajectory.overall_success:
            logger.warning(f"⚠️ 轨迹 {trajectory.trajectory_id} 未成功，跳过模式提取")
            return None

        logger.info(f"🔍 开始从轨迹提取模式: {trajectory.trajectory_id}")

        # 生成模式ID和名称
        pattern_id = self._generate_pattern_id(trajectory)
        pattern_name = self._generate_pattern_name(trajectory)
        description = self._generate_pattern_description(trajectory)

        # 转换步骤
        workflow_steps = []
        for step_record in trajectory.steps:
            if step_record.status != StepStatus.COMPLETED:
                continue

            workflow_step = self._convert_step_to_workflow_step(step_record)
            if workflow_step:
                workflow_steps.append(workflow_step)

        if not workflow_steps:
            logger.warning(f"⚠️ 轨迹 {trajectory.trajectory_id} 没有有效步骤")
            return None

        # 计算成功率
        success_rate = 1.0 if trajectory.overall_success else 0.0

        # 获取领域
        domain = self._map_domain(trajectory.rejection_type)

        # 创建工作流模式
        pattern = WorkflowPattern(
            pattern_id=pattern_id,
            name=pattern_name,
            description=description,
            task_type="OA_RESPONSE",
            domain=domain,
            steps=workflow_steps,
            success_rate=success_rate,
            usage_count=1,
            total_executions=1,
            successful_executions=1 if trajectory.overall_success else 0,
            avg_execution_time=trajectory.total_duration,
            min_execution_time=trajectory.total_duration,
            max_execution_time=trajectory.total_duration,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        logger.info(f"✅ 成功提取模式: {pattern_id}")
        logger.info(f"  步骤数: {len(workflow_steps)}")
        logger.info(f"  成功率: {success_rate:.1%}")

        return pattern

    def _convert_step_to_workflow_step(
        self,
        step_record,
    ) -> WorkflowStep | None:
        """
        将轨迹步骤转换为工作流步骤

        Args:
            step_record: 轨迹步骤记录

        Returns:
            工作流步骤
        """
        step_type = self.step_type_mapping(step_record.step_type)

        # 提取输入输出schema
        input_schema = self._extract_schema_from_dict(step_record.inputs)
        output_schema = self._extract_schema_from_dict(step_record.outputs)

        return WorkflowStep(
            step_id=step_record.step_id,
            name=step_record.name,
            step_type=step_type,
            description=step_record.description,
            action=step_record.step_type.value,
            input_schema=input_schema,
            output_schema=output_schema,
            dependencies=step_record.dependencies,
        )

    def _extract_schema_from_dict(self, data: dict[str, Any]) -> dict[str, str]:
        """
        从字典中提取schema

        Args:
            data: 输入/输出数据

        Returns:
            Schema字典
        """
        if not data:
            return {}

        schema = {}
        for key, value in data.items():
            value_type = type(value).__name__
            schema[key] = value_type

        return schema

    def _generate_pattern_id(self, trajectory: OAResponseTrajectory) -> str:
        """生成模式ID"""
        rejection_code = trajectory.rejection_type.lower()
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"oa_response_{rejection_code}_{timestamp}"

    def _generate_pattern_name(self, trajectory: OAResponseTrajectory) -> str:
        """生成模式名称"""
        rejection_map = {
            "novelty": "新颖性驳回答复",
            "inventiveness": "创造性驳回答复",
            "utility": "实用性驳回答复",
            "clarity": "清晰度驳回答复",
            "support": "支持关系驳回答复",
            "unity": "单一性驳回答复",
        }

        base_name = rejection_map.get(
            trajectory.rejection_type.lower(),
            f"{trajectory.rejection_type}驳回答复",
        )

        return f"{base_name}模式"

    def _generate_pattern_description(self, trajectory: OAResponseTrajectory) -> str:
        """生成模式描述"""
        strategy = trajectory.strategy_used or "标准答复策略"
        steps_count = len(trajectory.get_completed_steps())

        return (
            f"针对{trajectory.rejection_type}驳回的完整答复流程，"
            f"采用{strategy}，包含{steps_count}个核心步骤，"
            f"平均质量分数{trajectory.avg_quality_score:.2f}"
        )

    def _map_domain(self, rejection_type: str) -> TaskDomain:
        """映射驳回类型到任务领域"""
        return TaskDomain.PATENT

    @timeout(seconds=30.0)
    async def extract_and_save_pattern(
        self,
        trajectory: OAResponseTrajectory,
    ) -> WorkflowPattern | None:
        """
        提取模式并保存 (超时30秒)

        Args:
            trajectory: OA答复轨迹

        Returns:
            保存的工作流模式
        """
        # 提取模式
        pattern = self.extract_pattern_from_trajectory(trajectory)
        if not pattern:
            return None

        # 添加到记忆系统（使用正确的API方法名）
        try:
            await self.memory.store_pattern(pattern)
        except Exception as e:
            error = PatternExtractionError(
                message=f"添加模式到记忆系统失败: {pattern.pattern_id}",
                context={"pattern_id": pattern.pattern_id}
            )
            logger.error(f"{error.message}: {e}")
            raise error from e

        # 保存Markdown
        md_path = f"data/oa_responses/patterns/{pattern.pattern_id}.md"
        try:
            await self.serializer.save_to_file(pattern, md_path)
        except OSError as e:
            error = PatternExtractionError(
                message=f"保存模式Markdown文件失败: {md_path}",
                context={"pattern_id": pattern.pattern_id, "md_path": md_path}
            )
            logger.error(f"{error.message}: {e}")
            raise error from e

        logger.info(f"💾 模式已保存: {md_path}")

        return pattern

    @timeout(seconds=10.0)
    async def find_similar_patterns(
        self,
        rejection_type: str,
        top_k: int = 3,
    ) -> list[Any]:
        """
        查找相似的历史模式 (超时10秒)

        Args:
            rejection_type: 驳回类型
            top_k: 返回数量

        Returns:
            相似模式列表 (从RetrievalResult中提取pattern对象)
        """
        # 构建查询任务对象
        task = {
            "id": f"query_{rejection_type}",
            "type": "OA_RESPONSE",
            "description": f"查找{rejection_type}驳回的答复模式",
            "domain": "patent",
        }

        try:
            # 使用正确的API: retrieve_similar_workflows
            retrieval_results = await self.memory.retrieve_similar_workflows(
                task=task,
                top_k=top_k,
            )

            # 从RetrievalResult中提取pattern对象
            similar_patterns = [result.pattern for result in retrieval_results]

            logger.info(f"🔍 找到 {len(similar_patterns)} 个相似模式")
            return similar_patterns

        except Exception as e:
            error = KnowledgeGraphError(
                message=f"检索相似模式失败: {rejection_type}",
                context={"rejection_type": rejection_type, "top_k": top_k}
            )
            logger.error(f"{error.message}: {e}")
            # 返回空列表而不是抛出异常，保持系统稳定性
            return []


# ===== 全局单例 =====

_extractor_instance: OAResponsePatternExtractor | None = None


def get_oa_pattern_extractor() -> OAResponsePatternExtractor:
    """获取OA模式提取器单例"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = OAResponsePatternExtractor()
    return _extractor_instance
