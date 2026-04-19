#!/usr/bin/env python3
from __future__ import annotations
"""
任务模板系统
Task Template System

提供常用任务的 Plan 模板，支持快速创建标准化的任务计划。

内置模板:
1. 专利检索任务
2. 专利分析任务
3. 专利撰写任务
4. 专利无效分析任务
5. 专利侵权分析任务

Author: Athena Team
Version: 1.0.0
Date: 2026-02-25
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ========== 模板类型 ==========


class TemplateType(Enum):
    """模板类型"""
    PATENT_SEARCH = "patent_search"  # 专利检索
    PATENT_ANALYSIS = "patent_analysis"  # 专利分析
    PATENT_DRAFTING = "patent_drafting"  # 专利撰写
    PATENT_INVALIDATION = "patent_invalidation"  # 专利无效分析
    PATENT_INFRINGEMENT = "patent_infringement"  # 专利侵权分析
    CUSTOM = "custom"  # 自定义


# ========== 模板数据结构 ==========


@dataclass
class StepTemplate:
    """步骤模板"""
    id: str
    name: str
    description: str
    agent: str
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    estimated_time: int = 60
    timeout: int = 300
    can_parallel: bool = False
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agent": self.agent,
            "action": self.action,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "estimated_time": self.estimated_time,
            "timeout": self.timeout,
            "can_parallel": self.can_parallel,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepTemplate":
        return cls(**data)


@dataclass
class TaskTemplate:
    """任务模板"""
    template_id: str
    name: str
    description: str
    template_type: TemplateType
    steps: list[StepTemplate]
    execution_mode: str = "sequential"  # sequential, parallel, hybrid
    category: str = "patent"  # patent, legal, general
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type.value,
            "steps": [s.to_dict() for s in self.steps],
            "execution_mode": self.execution_mode,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskTemplate":
        data = data.copy()
        data["template_type"] = TemplateType(data["template_type"])
        data["steps"] = [StepTemplate.from_dict(s) for s in data["steps"]]
        return cls(**data)


# ========== 内置模板 ==========


class BuiltInTemplates:
    """内置任务模板"""

    @staticmethod
    def patent_search_template() -> TaskTemplate:
        """专利检索任务模板"""
        return TaskTemplate(
            template_id="patent_search_v1",
            name="专利检索任务",
            description="从多个数据源检索相关专利信息",
            template_type=TemplateType.PATENT_SEARCH,
            category="patent",
            tags=["检索", "专利", "数据库"],
            steps=[
                StepTemplate(
                    id="step_1",
                    name="分析检索需求",
                    description="理解用户检索目标，确定检索关键词和策略",
                    agent="xiaonuo",
                    action="analyze_requirement",
                    dependencies=[],
                    estimated_time=30,
                    can_parallel=False,
                ),
                StepTemplate(
                    id="step_2a",
                    name="提取检索关键词",
                    description="分析检索关键词和技术领域",
                    agent="xiaonuo",
                    action="extract_keywords",
                    dependencies=["step_1"],
                    estimated_time=30,
                    can_parallel=False,
                ),
                StepTemplate(
                    id="step_2b",
                    name="检索中文专利数据库",
                    description="从中国专利数据库检索相关专利",
                    agent="xiaona",
                    action="search_cn_patents",
                    dependencies=["step_2a"],
                    estimated_time=60,
                    can_parallel=True,
                ),
                StepTemplate(
                    id="step_2c",
                    name="检索专利家族",
                    description="检索专利家族信息",
                    agent="xiaona",
                    action="search_patent_families",
                    dependencies=["step_2a"],
                    estimated_time=45,
                    can_parallel=True,
                ),
                StepTemplate(
                    id="step_3",
                    name="合并检索结果",
                    description="去重、排序、合并来自不同数据源的结果",
                    agent="xiaonuo",
                    action="merge_results",
                    dependencies=["step_2a", "step_2b", "step_2c"],
                    estimated_time=30,
                    can_parallel=False,
                ),
                StepTemplate(
                    id="step_4",
                    name="生成检索报告",
                    description="生成结构化的检索报告文档",
                    agent="xiaona",
                    action="generate_report",
                    dependencies=["step_3"],
                    estimated_time=60,
                    can_parallel=False,
                ),
            ],
            execution_mode="hybrid",
            metadata={
                "data_sources": ["CNIPA", "WIPO", "EPO"],
                "result_format": "JSON + Markdown",
                "typical_duration": "5-10分钟",
            },
        )

    @staticmethod
    def patent_analysis_template() -> TaskTemplate:
        """专利分析任务模板"""
        return TaskTemplate(
            template_id="patent_analysis_v1",
            name="专利分析任务",
            description="对专利进行深度分析，包括新颖性、创造性分析",
            template_type=TemplateType.PATENT_ANALYSIS,
            category="patent",
            tags=["分析", "专利", "法律"],
            steps=[
                StepTemplate(
                    id="step_1",
                    name="收集专利信息",
                    description="获取目标专利的完整信息和权利要求",
                    agent="xiaona",
                    action="fetch_patent_info",
                    estimated_time=30,
                ),
                StepTemplate(
                    id="step_2",
                    name="检索对比文献",
                    description="检索相关的现有技术文献（D1、D2等）",
                    agent="xiaona",
                    action="search_prior_art",
                    dependencies=["step_1"],
                    estimated_time=120,
                ),
                StepTemplate(
                    id="step_3",
                    name="分析权利要求",
                    description="逐项分析权利要求的保护范围",
                    agent="xiaona",
                    action="analyze_claims",
                    dependencies=["step_1"],
                    estimated_time=90,
                ),
                StepTemplate(
                    id="step_4",
                    name="新颖性分析",
                    description="评估专利的新颖性",
                    agent="xiaona",
                    action="novelty_analysis",
                    dependencies=["step_2", "step_3"],
                    estimated_time=120,
                ),
                StepTemplate(
                    id="step_5",
                    name="创造性分析",
                    description="评估专利的创造性/非显而易见性",
                    agent="xiaona",
                    action="inventive_step_analysis",
                    dependencies=["step_2", "step_3"],
                    estimated_time=120,
                ),
                StepTemplate(
                    id="step_6",
                    name="生成分析报告",
                    description="生成完整的专利分析报告",
                    agent="xiaona",
                    action="generate_analysis_report",
                    dependencies=["step_4", "step_5"],
                    estimated_time=90,
                ),
            ],
            execution_mode="hybrid",
            metadata={
                "analysis_types": ["novelty", "inventive_step", "industrial_applicability"],
                "output_format": "详细分析报告",
            },
        )

    @staticmethod
    def patent_drafting_template() -> TaskTemplate:
        """专利撰写任务模板"""
        return TaskTemplate(
            template_id="patent_drafting_v1",
            name="专利撰写任务",
            description="根据技术交底书撰写专利申请文件",
            template_type=TemplateType.PATENT_DRAFTING,
            category="patent",
            tags=["撰写", "专利", "文档"],
            steps=[
                StepTemplate(
                    id="step_1",
                    name="分析技术交底书",
                    description="理解发明内容和技术要点",
                    agent="xiaonuo",
                    action="analyze_disclosure",
                    estimated_time=60,
                ),
                StepTemplate(
                    id="step_2",
                    name="检索现有技术",
                    description="检索相关现有技术，评估授权前景",
                    agent="xiaona",
                    action="search_prior_art",
                    dependencies=["step_1"],
                    estimated_time=120,
                ),
                StepTemplate(
                    id="step_3",
                    name="确定保护范围",
                    description="确定独立权利要求的保护范围",
                    agent="xiaona",
                    action="define_scope",
                    dependencies=["step_1", "step_2"],
                    estimated_time=90,
                ),
                StepTemplate(
                    id="step_4",
                    name="撰写权利要求书",
                    description="撰写独立和从属权利要求",
                    agent="xiaona",
                    action="draft_claims",
                    dependencies=["step_3"],
                    estimated_time=180,
                ),
                StepTemplate(
                    id="step_5",
                    name="撰写说明书",
                    description="撰写技术领域、背景技术、发明内容等",
                    agent="xiaona",
                    action="draft_description",
                    dependencies=["step_3"],
                    estimated_time=180,
                    can_parallel=True,
                ),
                StepTemplate(
                    id="step_6",
                    name="撰写附图说明",
                    description="撰写附图说明和附图摘要",
                    agent="xiaona",
                    action="draft_drawings",
                    dependencies=["step_3"],
                    estimated_time=120,
                    can_parallel=True,
                ),
                StepTemplate(
                    id="step_7",
                    name="合并审查",
                    description="审查各部分的完整性和一致性",
                    agent="xiaonuo",
                    action="review_draft",
                    dependencies=["step_4", "step_5", "step_6"],
                    estimated_time=60,
                ),
                StepTemplate(
                    id="step_8",
                    name="生成最终文档",
                    description="生成完整的专利申请文件",
                    agent="xiaona",
                    action="generate_final_document",
                    dependencies=["step_7"],
                    estimated_time=60,
                ),
            ],
            execution_mode="hybrid",
            metadata={
                "document_type": "专利申请文件",
                "sections": ["权利要求书", "说明书", "附图说明", "摘要"],
                "estimated_duration": "1-2小时",
            },
        )

    @staticmethod
    def patent_invalidation_template() -> TaskTemplate:
        """专利无效分析任务模板"""
        return TaskTemplate(
            template_id="patent_invalidation_v1",
            name="专利无效分析任务",
            description="对目标专利进行无效可能性分析",
            template_type=TemplateType.PATENT_INVALIDATION,
            category="patent",
            tags=["无效", "分析", "法律"],
            steps=[
                StepTemplate(
                    id="step_1",
                    name="获取目标专利信息",
                    description="获取目标专利的详细信息",
                    agent="xiaona",
                    action="fetch_target_patent",
                    estimated_time=30,
                ),
                StepTemplate(
                    id="step_2",
                    name="检索对比文件",
                    description="检索可能用于无效的对比文件",
                    agent="xiaona",
                    action="search_invalidity_references",
                    dependencies=["step_1"],
                    estimated_time=180,
                ),
                StepTemplate(
                    id="step_3",
                    name="分析权利要求",
                    description="逐项分析权利要求的有效性",
                    agent="xiaona",
                    action="analyze_claim_validity",
                    dependencies=["step_1", "step_2"],
                    estimated_time=180,
                ),
                StepTemplate(
                    id="step_4",
                    name="评估无效理由",
                    description="确定可用的无效理由（新颖性、创造性等）",
                    agent="xiaona",
                    action="assess_invalidity_grounds",
                    dependencies=["step_2", "step_3"],
                    estimated_time=120,
                ),
                StepTemplate(
                    id="step_5",
                    name="生成无效分析报告",
                    description="生成完整的无效分析报告",
                    agent="xiaona",
                    action="generate_invalidation_report",
                    dependencies=["step_4"],
                    estimated_time=90,
                ),
            ],
            execution_mode="sequential",
            metadata={
                "invalidity_grounds": ["novelty", "inventive_step", "clarity", "support"],
            },
        )

    @staticmethod
    def patent_infringement_template() -> TaskTemplate:
        """专利侵权分析任务模板"""
        return TaskTemplate(
            template_id="patent_infringement_v1",
            name="专利侵权分析任务",
            description="分析产品/方法是否侵犯目标专利",
            template_type=TemplateType.PATENT_INFRINGEMENT,
            category="patent",
            tags=["侵权", "分析", "法律"],
            steps=[
                StepTemplate(
                    id="step_1",
                    name="获取目标专利信息",
                    description="获取目标专利的权利要求信息",
                    agent="xiaona",
                    action="fetch_claims",
                    estimated_time=30,
                ),
                StepTemplate(
                    id="step_2",
                    name="分析被控产品/方法",
                    description="获取并分析被控侵权产品或方法的技术特征",
                    agent="xiaona",
                    action="analyze_accused_product",
                    estimated_time=90,
                ),
                StepTemplate(
                    id="step_3",
                    name="特征比对",
                    description="将专利权利要求与产品特征进行逐项比对",
                    agent="xiaona",
                    action="compare_features",
                    dependencies=["step_1", "step_2"],
                    estimated_time=120,
                ),
                StepTemplate(
                    id="step_4",
                    name="确定保护范围",
                    description="解释权利要求的保护范围",
                    agent="xiaona",
                    action="interpret_claim_scope",
                    dependencies=["step_1"],
                    estimated_time=60,
                ),
                StepTemplate(
                    id="step_5",
                    name="侵权判定",
                    description="根据全面覆盖原则判定是否侵权",
                    agent="xiaona",
                    action="determine_infringement",
                    dependencies=["step_3", "step_4"],
                    estimated_time=90,
                ),
                StepTemplate(
                    id="step_6",
                    name="生成侵权分析报告",
                    description="生成完整的侵权分析报告",
                    agent="xiaona",
                    action="generate_infringement_report",
                    dependencies=["step_5"],
                    estimated_time=90,
                ),
            ],
            execution_mode="sequential",
            metadata={
                "infringement_test": "all_elements_rule",
                "jurisdiction": "CN",
            },
        )


# ========== 模板管理器 ==========


class TemplateManager:
    """任务模板管理器"""

    def __init__(self, template_dir: Path | None = None):
        self.template_dir = template_dir or Path("core/cognition/templates")
        self.template_dir.mkdir(parents=True, exist_ok=True)

        self.templates: dict[str, TaskTemplate] = {}
        self._load_builtin_templates()
        self._load_custom_templates()

        logger.info(f"📋 模板管理器初始化: {len(self.templates)} 个模板")

    def _load_builtin_templates(self) -> None:
        """加载内置模板"""
        builtin = BuiltInTemplates()

        self.templates["patent_search"] = builtin.patent_search_template()
        self.templates["patent_analysis"] = builtin.patent_analysis_template()
        self.templates["patent_drafting"] = builtin.patent_drafting_template()
        self.templates["patent_invalidation"] = builtin.patent_invalidation_template()
        self.templates["patent_infringement"] = builtin.patent_infringement_template()

        logger.info("   ✅ 内置模板加载完成")

    def _load_custom_templates(self) -> None:
        """加载自定义模板"""
        if not self.template_dir.exists():
            return

        for template_file in self.template_dir.glob("*.json"):
            try:
                with open(template_file, encoding="utf-8") as f:
                    data = json.load(f)

                template = TaskTemplate.from_dict(data)
                self.templates[template.template_id] = template

                logger.info(f"   ✅ 加载自定义模板: {template.template_id}")

            except Exception as e:
                logger.warning(f"   ⚠️ 加载模板失败 {template_file}: {e}")

    def get_template(self, template_id: str) -> TaskTemplate | None:
        """获取模板"""
        return self.templates.get(template_id)

    def list_templates(
        self,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> list[TaskTemplate]:
        """列出模板"""
        templates = list(self.templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        if tags:
            templates = [
                t for t in templates
                if any(tag in t.tags for tag in tags)
            ]

        return templates

    def create_task_from_template(
        self,
        template_id: str,
        task_id: str,
        title: str,
        description: str,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """从模板创建任务计划"""
        template = self.get_template(template_id)

        if not template:
            raise ValueError(f"模板不存在: {template_id}")

        # 转换步骤模板为实际步骤
        from core.cognition.dual_layer_planner_v2 import PlanStep

        steps = []
        for step_template in template.steps:
            # 应用参数替换
            step_params = step_template.parameters.copy()
            if parameters:
                for key, value in parameters.items():
                    if isinstance(value, str) and "{" in value:
                        # 简单的模板变量替换
                        step_params[key] = value.format(**parameters)

            step = PlanStep(
                id=step_template.id,
                name=step_template.name,
                description=step_template.description,
                agent=step_template.agent,
                action=step_template.action,
                parameters=step_params,
                dependencies=step_template.dependencies,
                estimated_time=step_template.estimated_time,
                timeout=step_template.timeout,
                can_parallel=step_template.can_parallel,
                max_retries=step_template.max_retries,
            )
            steps.append(step)

        return {
            "task_id": task_id,
            "title": title,
            "description": description,
            "steps": steps,
            "execution_mode": template.execution_mode,
            "metadata": {
                "template_id": template_id,
                "template_version": template.version,
                "parameters": parameters or {},
            },
        }

    def save_custom_template(self, template: TaskTemplate) -> str:
        """保存自定义模板"""
        self.templates[template.template_id] = template

        template_file = self.template_dir / f"{template.template_id}.json"

        with open(template_file, "w", encoding="utf-8") as f:
            json.dump(template.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"✅ 自定义模板已保存: {template.template_id}")
        return str(template_file)


# ========== 导出 ==========


__all__ = [
    "TemplateType",
    "StepTemplate",
    "TaskTemplate",
    "BuiltInTemplates",
    "TemplateManager",
]
