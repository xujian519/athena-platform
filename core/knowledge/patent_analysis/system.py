#!/usr/bin/env python3
"""
专利分析系统
Patent Analysis System

完整的专利分析工作流集成

作者: Athena AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .analyzer import AnalysisResult, AnalysisType, PatentAnalyzer
from .evaluator import PatentEvaluationResult, PatentEvaluator
from .rewriter import PatentRewriter, RewriteMode, RewriteResult, RewriteTarget

logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """工作流阶段"""

    INITIALIZED = "initialized"
    ANALYZED = "analyzed"
    EVALUATED = "evaluated"
    REWRITTEN = "rewritten"
    COMPLETED = "completed"


class ProjectStatus(Enum):
    """项目状态"""

    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PatentProject:
    """专利项目"""

    project_id: str
    title: str
    description: str
    patent_data: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: ProjectStatus = ProjectStatus.CREATED
    current_stage: WorkflowStage = WorkflowStage.INITIALIZED

    # 分析结果
    analysis_results: list[AnalysisResult] = field(default_factory=list)
    evaluation_result: PatentEvaluationResult | None = None
    rewrite_results: list[RewriteResult] = field(default_factory=list)

    # 配置
    analysis_types: list[AnalysisType] = field(default_factory=list)
    rewrite_targets: list[RewriteTarget] = field(default_factory=list)
    rewrite_mode: RewriteMode = RewriteMode.STANDARD


@dataclass
class SystemConfiguration:
    """系统配置"""

    auto_save: bool = True
    save_directory: str = "./patent_projects"
    enable_notifications: bool = True
    default_analysis_types: list[AnalysisType] = field(
        default_factory=lambda: [
            AnalysisType.NOVELTY,
            AnalysisType.INVENTIVE,
            AnalysisType.PRACTICAL,
            AnalysisType.LEGAL,
        ]
    )
    default_rewrite_targets: list[RewriteTarget] = field(
        default_factory=lambda: [RewriteTarget.CLAIMS, RewriteTarget.SPECIFICATION]
    )
    max_concurrent_projects: int = 10
    quality_threshold: float = 70.0
    enable_ai_enhancement: bool = True


class PatentAnalysisSystem:
    """专利分析系统"""

    _instance: PatentAnalysisSystem | None = None

    def __init__(self, config: SystemConfiguration | None = None):
        self.config = config or SystemConfiguration()
        self.projects: dict[str, PatentProject] = {}
        self.analyzer: PatentAnalyzer | None = None
        self.evaluator: PatentEvaluator | None = None
        self.rewriter: PatentRewriter | None = None
        self._initialized = False

    @classmethod
    async def initialize(cls, config: SystemConfiguration | None = None):
        """初始化系统"""
        if cls._instance is None:
            cls._instance = cls(config)
            await cls._instance._initialize_components()
            cls._instance._initialized = True
            logger.info("✅ 专利分析系统初始化完成")
        return cls._instance

    @classmethod
    def get_instance(cls) -> PatentAnalysisSystem:
        """获取单例实例"""
        if cls._instance is None:
            raise RuntimeError("PatentAnalysisSystem未初始化,请先调用initialize()")
        return cls._instance

    async def _initialize_components(self):
        """初始化组件"""
        self.analyzer = await PatentAnalyzer.initialize()
        self.evaluator = await PatentEvaluator.initialize()
        self.rewriter = await PatentRewriter.initialize()

    async def create_project(
        self,
        title: str,
        description: str,
        patent_data: dict[str, Any],        analysis_types: list[AnalysisType] | None = None,
        rewrite_targets: list[RewriteTarget] | None = None,
    ) -> str:
        """
        创建专利项目

        Args:
            title: 项目标题
            description: 项目描述
            patent_data: 专利数据
            analysis_types: 分析类型列表
            rewrite_targets: 重写目标列表

        Returns:
            项目ID
        """
        project_id = f"patent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        project = PatentProject(
            project_id=project_id,
            title=title,
            description=description,
            patent_data=patent_data,
            analysis_types=analysis_types or self.config.default_analysis_types,
            rewrite_targets=rewrite_targets or self.config.default_rewrite_targets,
        )

        self.projects[project_id] = project

        if self.config.auto_save:
            await self._save_project(project)

        logger.info(f"✅ 创建专利项目: {project_id}")
        return project_id

    async def analyze_project(self, project_id: str) -> list[AnalysisResult]:
        """
        分析项目

        Args:
            project_id: 项目ID

        Returns:
            分析结果列表
        """
        project = self.projects.get(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        if project.status not in [ProjectStatus.CREATED, ProjectStatus.IN_PROGRESS]:
            raise ValueError(f"项目状态不允许分析: {project.status}")

        logger.info(f"🔍 开始分析项目: {project_id}")
        project.status = ProjectStatus.IN_PROGRESS
        project.current_stage = WorkflowStage.ANALYZED

        try:
            # 执行分析
            results = await self.analyzer.analyze_patent(
                project.patent_data, project.analysis_types
            )

            project.analysis_results = results
            project.updated_at = datetime.now()

            if self.config.auto_save:
                await self._save_project(project)

            logger.info(f"✅ 项目分析完成: {project_id}")
            return results

        except Exception as e:
            project.status = ProjectStatus.FAILED
            logger.error(f"❌ 项目分析失败: {project_id} - {e}")
            raise

    async def evaluate_project(self, project_id: str) -> PatentEvaluationResult:
        """
        评估项目

        Args:
            project_id: 项目ID

        Returns:
            评估结果
        """
        project = self.projects.get(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        if project.status not in [ProjectStatus.IN_PROGRESS]:
            raise ValueError(f"项目状态不允许评估: {project.status}")

        logger.info(f"📊 开始评估项目: {project_id}")
        project.current_stage = WorkflowStage.EVALUATED

        try:
            # 执行评估
            result = await self.evaluator.evaluate_patent(project.patent_data)

            project.evaluation_result = result
            project.updated_at = datetime.now()

            if self.config.auto_save:
                await self._save_project(project)

            logger.info(f"✅ 项目评估完成: {project_id}")
            return result

        except Exception as e:
            project.status = ProjectStatus.FAILED
            logger.error(f"❌ 项目评估失败: {project_id} - {e}")
            raise

    async def rewrite_project(
        self, project_id: str, rewrite_mode: RewriteMode | None = None
    ) -> list[RewriteResult]:
        """
        重写项目

        Args:
            project_id: 项目ID
            rewrite_mode: 重写模式

        Returns:
            重写结果列表
        """
        project = self.projects.get(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        if project.status not in [ProjectStatus.IN_PROGRESS]:
            raise ValueError(f"项目状态不允许重写: {project.status}")

        logger.info(f"✏️ 开始重写项目: {project_id}")
        project.current_stage = WorkflowStage.REWRITTEN

        mode = rewrite_mode or project.rewrite_mode

        try:
            # 执行重写
            results = await self.rewriter.batch_rewrite(
                [project.patent_data], project.rewrite_targets, mode
            )

            project.rewrite_results = results
            project.updated_at = datetime.now()

            if self.config.auto_save:
                await self._save_project(project)

            logger.info(f"✅ 项目重写完成: {project_id}")
            return results

        except Exception as e:
            project.status = ProjectStatus.FAILED
            logger.error(f"❌ 项目重写失败: {project_id} - {e}")
            raise

    async def run_full_workflow(
        self, project_id: str, rewrite_mode: RewriteMode | None = None
    ) -> dict[str, Any]:
        """
        运行完整工作流

        Args:
            project_id: 项目ID
            rewrite_mode: 重写模式

        Returns:
            工作流结果
        """
        project = self.projects.get(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        logger.info(f"🚀 开始完整工作流: {project_id}")

        workflow_results = {"project_id": project_id, "started_at": datetime.now(), "stages": {}}

        try:
            # 阶段1: 分析
            analysis_results = await self.analyze_project(project_id)
            workflow_results["stages"]["analysis"] = {
                "status": "completed",
                "results_count": len(analysis_results),
                "completed_at": datetime.now(),
            }

            # 阶段2: 评估
            evaluation_result = await self.evaluate_project(project_id)
            workflow_results["stages"]["evaluation"] = {
                "status": "completed",
                "overall_score": evaluation_result.overall_score,
                "overall_level": evaluation_result.overall_level.value,
                "completed_at": datetime.now(),
            }

            # 阶段3: 重写
            rewrite_results = await self.rewrite_project(project_id, rewrite_mode)
            workflow_results["stages"]["rewrite"] = {
                "status": "completed",
                "results_count": len(rewrite_results),
                "completed_at": datetime.now(),
            }

            # 完成项目
            project.status = ProjectStatus.COMPLETED
            project.current_stage = WorkflowStage.COMPLETED
            project.updated_at = datetime.now()

            workflow_results["status"] = "completed"
            workflow_results["completed_at"] = datetime.now()

            if self.config.auto_save:
                await self._save_project(project)

            logger.info(f"✅ 完整工作流完成: {project_id}")
            return workflow_results

        except Exception as e:
            project.status = ProjectStatus.FAILED
            workflow_results["status"] = "failed"
            workflow_results["error"] = str(e)
            workflow_results["failed_at"] = datetime.now()
            logger.error(f"❌ 工作流失败: {project_id} - {e}")
            raise

    async def get_project(self, project_id: str) -> PatentProject | None:
        """获取项目"""
        return self.projects.get(project_id)

    async def list_projects(self, status: ProjectStatus | None = None) -> list[PatentProject]:
        """列出项目"""
        projects = list(self.projects.values())
        if status:
            projects = [p for p in projects if p.status == status]
        return sorted(projects, key=lambda p: p.created_at, reverse=True)

    async def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        if project_id in self.projects:
            del self.projects[project_id]
            logger.info(f"✅ 删除项目: {project_id}")
            return True
        return False

    async def get_project_statistics(self) -> dict[str, Any]:
        """获取项目统计信息"""
        projects = list(self.projects.values())

        stats = {
            "total_projects": len(projects),
            "by_status": {},
            "by_stage": {},
            "average_score": 0.0,
            "recent_projects": 0,
        }

        # 按状态统计
        for status in ProjectStatus:
            count = len([p for p in projects if p.status == status])
            stats["by_status"][status.value] = count

        # 按阶段统计
        for stage in WorkflowStage:
            count = len([p for p in projects if p.current_stage == stage])
            stats["by_stage"][stage.value] = count

        # 平均分
        evaluated_projects = [p for p in projects if p.evaluation_result]
        if evaluated_projects:
            total_score = sum(p.evaluation_result.overall_score for p in evaluated_projects)
            stats["average_score"] = total_score / len(evaluated_projects)

        # 最近项目(24小时内)
        from datetime import timedelta

        yesterday = datetime.now() - timedelta(days=1)
        stats["recent_projects"] = len([p for p in projects if p.created_at > yesterday])

        return stats

    async def _save_project(self, project: PatentProject):
        """保存项目"""
        if not self.config.auto_save:
            return

        try:
            from pathlib import Path

            save_dir = Path(self.config.save_directory)
            save_dir.mkdir(parents=True, exist_ok=True)

            save_file = save_dir / f"{project.project_id}.json"

            # 序列化项目数据
            project_data = {
                "project_id": project.project_id,
                "title": project.title,
                "description": project.description,
                "patent_data": project.patent_data,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
                "status": project.status.value,
                "current_stage": project.current_stage.value,
                "analysis_types": [t.value for t in project.analysis_types],
                "rewrite_targets": [t.value for t in project.rewrite_targets],
                "rewrite_mode": project.rewrite_mode.value,
            }

            # 保存序列化数据
            with open(save_file, "w", encoding="utf-8") as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存项目失败: {e}")

    @classmethod
    async def shutdown(cls):
        """关闭系统"""
        if cls._instance:
            # 关闭组件
            if cls._instance.analyzer:
                await PatentAnalyzer.shutdown()
            if cls._instance.evaluator:
                await PatentEvaluator.shutdown()
            if cls._instance.rewriter:
                await PatentRewriter.shutdown()

            cls._instance = None
            logger.info("✅ 专利分析系统已关闭")
