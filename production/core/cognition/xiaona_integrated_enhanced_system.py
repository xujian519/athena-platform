
# pyright: ignore
# !/usr/bin/env python3
"""
小娜集成增强系统
Xiaona Integrated Enhanced System

整合人机协作、反思引擎和学习系统的完整解决方案
为小娜专利法律专家提供全面的智能增强能力

作者: 徐健 (xujian519@gmail.com)
创建时间: 2025-12-17
版本: v2.0.0 Integrated
"""

from __future__ import annotations
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ..collaboration.human_ai_collaboration_framework import (
    CollaborationSession,
    HumanInTheLoopEngine,
    TaskType,
)
from ..learning.xiaona_adaptive_learning_system import LearningEvent, XiaonaAdaptiveLearningSystem
from .xiaona_enhanced_reflection_engine import LegalReflectionResult, XiaonaEnhancedReflectionEngine

logger = logging.getLogger(__name__)


@dataclass
class EnhancementConfig:
    """增强配置"""

    enable_reflection: bool = True
    enable_collaboration: bool = True
    enable_learning: bool = True
    reflection_threshold: float = 0.80
    collaboration_threshold: float = 0.70
    learning_threshold: float = 0.75
    auto_refine: bool = True
    auto_collaborate: bool = True


@dataclass
class ProcessingResult:
    """处理结果"""

    task_id: str
    original_input: str
    initial_output: str
    enhanced_output: str | None = None
    reflection_result: LegalReflectionResult | None = None
    collaboration_session: CollaborationSession | None = None
    learning_events: list[LearningEvent] = field(default_factory=list)
    processing_time: float = 0.0
    enhancement_applied: list[str] = field(default_factory=list)
    final_confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class XiaonaIntegratedEnhancedSystem:
    """小娜集成增强系统"""

    def __init__(
        self,
        llm_client=None,  # type: ignore
        notification_service=None,  # type: ignore
        config: EnhancementConfig | None = None,
        storage_path: str = "/tmp/xiaona_enhanced",  # TODO: 确保除数不为零
    ):
        self.llm_client = llm_client
        self.notification_service = notification_service
        self.config = config or EnhancementConfig()
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 初始化各个子系统
        self.reflection_engine = XiaonaEnhancedReflectionEngine(llm_client=llm_client)

        self.collaboration_engine = (
            HumanInTheLoopEngine(llm_client=llm_client, notification_service=notification_service)
            if self.config.enable_collaboration
            else None
        )

        self.learning_system = (
            XiaonaAdaptiveLearningSystem(storage_path=str(self.storage_path / "learning"))
            if self.config.enable_learning
            else None
        )

        # 处理统计
        self.processing_stats = {
            "total_processed": 0,
            "reflection_applied": 0,
            "collaboration_triggered": 0,
            "learning_events": 0,
            "average_processing_time": 0.0,
            "success_rate": 0.0,
        }

        logger.info("小娜集成增强系统初始化完成")

    async def process_legal_task(
        self,
        task_id: str,
        task_input: str,
        task_type: str = "patent_analysis",
        context: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> ProcessingResult:
        """处理法律任务 - 主入口"""

        start_time = datetime.now()
        logger.info(f"开始处理法律任务: {task_id}")

        context = context or {}
        result = ProcessingResult(
            task_id=task_id,
            original_input=task_input,
            initial_output="",  # 这里应该调用小娜的分析引擎生成初始输出
            metadata={
                "task_type": task_type,
                "user_id": user_id,
                "processing_start": start_time.isoformat(),
            },
        )

        try:
            # 步骤1: 生成初始分析结果
            result.initial_output = await self._generate_initial_analysis(
                task_input, task_type, context
            )

            # 步骤2: 反思引擎评估
            if self.config.enable_reflection:
                result.reflection_result = await self._apply_reflection(
                    result.task_id, result.original_input, result.initial_output, task_type, context
                )
                result.enhancement_applied.append("reflection")

            # 步骤3: 根据反思结果决定是否需要协作
            if self.config.enable_collaboration and self._should_collaborate(
                result.reflection_result
            ):
                result.collaboration_session = await self._initiate_collaboration(
                    result.task_id,
                    task_type,
                    result.original_input,
                    result.initial_output,
                    result.reflection_result,
                    context,
                )
                result.enhancement_applied.append("collaboration")

                # 等待协作完成或超时
                await self._wait_for_collaboration(result)
            else:
                # 步骤4: 自动优化
                if (
                    self.config.auto_refine
                    and result.reflection_result
                    and result.reflection_result.should_refine
                ):
                    result.enhanced_output = await self._auto_refine_output(
                        result.initial_output, result.reflection_result, context
                    )
                    result.enhancement_applied.append("auto_refine")

            # 步骤5: 学习系统处理
            if self.config.enable_learning:
                await self._process_learning(result)
                result.enhancement_applied.append("learning")

            # 确定最终输出和置信度
            result.final_output = result.enhanced_output or result.initial_output
            result.final_confidence = self._calculate_final_confidence(result)

            # 计算处理时间
            result.processing_time = (datetime.now() - start_time).total_seconds()

            # 更新统计信息
            self._update_processing_stats(result)

            logger.info(f"法律任务处理完成: {task_id}, 耗时: {result.processing_time:.2f}s")

        except Exception as e:
            logger.error(f"法律任务处理失败: {task_id}, 错误: {e}")
            result.metadata["error"] = str(e)

        return result

    async def _generate_initial_analysis(
        self, task_input: str, task_type: str, context: dict[str, Any]
    ) -> str:
        """生成初始分析结果"""

        # 这里应该调用小娜的核心分析引擎
        # 为了演示,返回一个模拟的分析结果
        analysis_templates = {
            "patent_analysis": f"""
专利分析报告:

1. 技术方案理解:
   - 输入:{task_input}
   - 初步分析:这是一个技术相关专利

2. 法律评估:
   - 适用法律:专利法及其实施细则
   - 初步结论:需要进一步检索现有技术

3. 建议措施:
   - 进行详细的现有技术检索
   - 分析技术方案的创造性
   - 评估专利授权前景
            """,
            "legal_research": f"""
法律研究结果:

1. 问题分析:
   - 研究内容:{task_input}
   - 法律领域:知识产权法

2. 相关法规:
   - 主要依据:专利法、商标法、著作权法
   - 参考案例:需要具体分析

3. 初步结论:
   - 需要更多背景信息
   - 建议咨询专业律师
            """,
        }

        template = analysis_templates.get(task_type, analysis_templates["patent_analysis"])
        return template.format(task_input=task_input)

    async def _apply_reflection(
        self,
        task_id: str,
        original_input: str,
        initial_output: str,
        task_type: str,
        context: dict[str, Any],    ) -> LegalReflectionResult:
        """应用反思引擎"""

        logger.info(f"应用反思引擎: {task_id}")

        reflection_result = await self.reflection_engine.reflect_on_legal_analysis(
            task_id=task_id,
            original_prompt=original_input,
            legal_output=initial_output,
            task_type=task_type,
            context=context,
        )

        self.processing_stats["reflection_applied"] += 1
        return reflection_result

    def _should_collaborate(self, reflection_result: LegalReflectionResult,) -> bool:
        """判断是否需要协作"""

        if not self.config.enable_collaboration or not reflection_result:
            return False

        # 基于反思结果判断
        conditions = [
            reflection_result.human_review_required,
            reflection_result.refinement_priority >= 4,  # 高优先级
            reflection_result.overall_score < self.config.collaboration_threshold,
        ]

        return any(conditions)

    async def _initiate_collaboration(
        self,
        task_id: str,
        task_type: str,
        original_input: str,
        initial_output: str,
        reflection_result: LegalReflectionResult,
        context: dict[str, Any],    ) -> CollaborationSession:
        """启动协作流程"""

        if not self.collaboration_engine:
            raise ValueError("协作引擎未启用")

        logger.info(f"启动协作流程: {task_id}")

        # 创建协作任务
        collaboration_task_type = (
            TaskType.PATENT_ANALYSIS if "patent" in task_type else TaskType.LEGAL_RESEARCH
        )

        task = await self.collaboration_engine.create_collaboration_task(
            task_type=collaboration_task_type,
            title=f"法律分析协作 - {task_id}",
            description=f"评分: {reflection_result.overall_score:.2f}, 建议: {', '.join(reflection_result.recommendations[:3])}",
            context={
                "task_id": task_id,
                "original_input": original_input,
                "initial_output": initial_output,
                "reflection_result": reflection_result.__dict__,
                **context,
            },
            ai_output=initial_output,
            ai_confidence=reflection_result.confidence_level,
            priority=reflection_result.refinement_priority,
        )

        # 启动协作会话
        session = await self.collaboration_engine.start_collaboration_session(task)
        self.processing_stats["collaboration_triggered"] += 1

        return session

    async def _wait_for_collaboration(self, result: ProcessingResult, timeout: int = 300):
        """等待协作完成"""

        if not result.collaboration_session:
            return

        session_id = result.collaboration_session.session_id
        logger.info(f"等待协作完成: {session_id}, 超时: {timeout}秒")

        # 在实际应用中,这里应该等待专家响应
        # 为了演示,我们模拟一个等待过程
        await asyncio.sleep(2)  # 模拟等待时间

        # 检查协作状态
        if self.collaboration_engine:
            if session_id in self.collaboration_engine.active_sessions:
                session = self.collaboration_engine.active_sessions[session_id]
                if session.consensus_reached and session.final_output:
                    result.enhanced_output = session.final_output
                    logger.info(f"协作完成,获得优化输出: {session_id}")

    async def _auto_refine_output(
        self, initial_output: str, reflection_result: LegalReflectionResult, context: dict[str, Any]
    ) -> str:
        """自动优化输出"""

        logger.info("执行自动优化")

        # 基于反思结果优化输出
        refined_output = initial_output

        # 添加改进建议
        if reflection_result.recommendations:
            refinement_section = "\n\n[AI自动优化建议]\n"
            for i, recommendation in enumerate(reflection_result.recommendations[:3], 1):
                refinement_section += f"{i}. {recommendation}\n"

            refined_output += refinement_section

        # 强化薄弱环节
        for weakness in reflection_result.weaknesses:
            if "完整性" in weakness:
                refined_output += "\n\n注意:本分析可能需要更多信息以确保完整性。"
            elif "准确性" in weakness:
                refined_output += "\n\n注意:建议验证关键事实和数据的准确性。"

        return refined_output

    async def _process_learning(self, result: ProcessingResult):
        """处理学习"""

        if not self.learning_system:
            return

        logger.info(f"执行学习处理: {result.task_id}")

        # 处理反思结果的学习
        if result.reflection_result:
            await self.learning_system.process_reflection_result(result.reflection_result)

        # 处理协作会话的学习
        if result.collaboration_session:
            await self.learning_system.process_human_feedback(
                session=result.collaboration_session,
                human_feedback="专家协作反馈",  # 简化处理
                feedback_quality="constructive",
            )

        self.processing_stats["learning_events"] += 1

    def _calculate_final_confidence(self, result: ProcessingResult) -> float:
        """计算最终置信度"""

        base_confidence = 0.8  # 基础置信度

        # 基于反思结果调整
        if result.reflection_result:
            base_confidence = result.reflection_result.confidence_level

        # 如果有协作完成,提高置信度
        if result.collaboration_session and result.collaboration_session.consensus_reached:
            base_confidence = min(base_confidence * 1.2, 1.0)

        # 如果应用了自动优化,略微提高置信度
        if "auto_refine" in result.enhancement_applied:
            base_confidence *= 1.05

        return min(base_confidence, 1.0)

    def _update_processing_stats(self, result: ProcessingResult) -> Any:
        """更新处理统计"""

        self.processing_stats["total_processed"] += 1

        # 更新平均处理时间
        total_time = self.processing_stats["average_processing_time"] * (
            self.processing_stats["total_processed"] - 1
        )
        total_time += result.processing_time
        self.processing_stats["average_processing_time"] = (
            total_time / self.processing_stats["total_processed"]
        )

        # 更新成功率
        if result.final_confidence >= 0.8:
            success_count = self.processing_stats["success_rate"] * (
                self.processing_stats["total_processed"] - 1
            )
            success_count += 1
            self.processing_stats["success_rate"] = (
                success_count / self.processing_stats["total_processed"]
            )

    def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""

        status = {
            "system_name": "小娜集成增强系统",
            "version": "v2.0.0",
            "enabled_modules": {
                "reflection_engine": self.config.enable_reflection,
                "collaboration_engine": self.config.enable_collaboration,
                "learning_system": self.config.enable_learning,
            },
            "processing_statistics": self.processing_stats,
            "configuration": {
                "reflection_threshold": self.config.reflection_threshold,
                "collaboration_threshold": self.config.collaboration_threshold,
                "auto_refine": self.config.auto_refine,
                "auto_collaborate": self.config.auto_collaborate,
            },
        }

        # 添加子系统状态
        if self.config.enable_reflection:
            reflection_stats = self.reflection_engine.get_reflection_statistics()
            status["reflection_engine"] = {
                "total_reflections": reflection_stats["total_reflections"],
                "average_score": reflection_stats["average_score"],
                "improvement_rate": reflection_stats["improvement_rate"],
            }

        if self.config.enable_collaboration and self.collaboration_engine:
            collaboration_stats = self.collaboration_engine.get_collaboration_statistics()
            status["collaboration_engine"] = {
                "active_sessions": collaboration_stats["active_sessions"],
                "completed_sessions": collaboration_stats["completed_sessions"],
                "registered_experts": collaboration_stats["registered_experts"],
            }

        if self.config.enable_learning:
            learning_summary = self.learning_system.get_learning_summary()  # type: ignore
            status["learning_system"] = {
                "knowledge_items": learning_summary["knowledge_base"]["total_items"],
                "learning_events": learning_summary["agent_profile"]["total_events"],
                "performance_metrics": learning_summary["performance_metrics"],
            }

        return status

    async def shutdown(self):
        """关闭系统"""

        logger.info("正在关闭小娜集成增强系统...")

        # 保存学习数据
        if self.learning_system:
            self.learning_system._save_learning_data()  # type: ignore

        # 保存处理统计
        stats_file = self.storage_path / "processing_stats.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(self.processing_stats, f, ensure_ascii=False, indent=2)

        logger.info("小娜集成增强系统已关闭")


# 示例使用
async def demo_integrated_system():
    """演示集成系统"""

    # 创建集成系统
    config = EnhancementConfig(
        enable_reflection=True,
        enable_collaboration=True,
        enable_learning=True,
        reflection_threshold=0.80,
        collaboration_threshold=0.70,
    )

    enhanced_system = XiaonaIntegratedEnhancedSystem(config=config)

    try:
        # 处理法律任务
        result = await enhanced_system.process_legal_task(
            task_id="demo_001",
            task_input="请分析专利CN123456789A的新颖性和创造性",
            task_type="patent_analysis",
            context={
                "patent_number": "CN123456789A",
                "client_requirements": ["快速分析", "准确判断"],
            },
            user_id="demo_user",
        )

        print("处理结果:")
        print(f"任务ID: {result.task_id}")
        print(f"应用增强: {', '.join(result.enhancement_applied)}")
        print(f"处理时间: {result.processing_time:.2f}秒")
        print(f"最终置信度: {result.final_confidence:.2f}")
        print(f"\n初始输出:\n{result.initial_output[:200]}...")

        if result.enhanced_output:
            print(f"\n增强输出:\n{result.enhanced_output[:200]}...")

        if result.reflection_result:
            print("\n反思结果:")
            print(f"总分: {result.reflection_result.overall_score:.2f}")
            print(f"需要改进: {result.reflection_result.should_refine}")

        # 获取系统状态
        status = enhanced_system.get_system_status()
        print("\n系统状态:")
        print(json.dumps(status, ensure_ascii=False, indent=2))

    finally:
        # 关闭系统
        await enhanced_system.shutdown()


if __name__ == "__main__":
    asyncio.run(demo_integrated_system())
