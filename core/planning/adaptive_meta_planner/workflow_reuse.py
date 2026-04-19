#!/usr/bin/env python3
from __future__ import annotations
"""
自适应元规划器 - 工作流复用管理器
Adaptive Meta Planner - Workflow Reuse Manager

作者: Athena平台团队
创建时间: 2026-01-20
重构时间: 2026-01-26
版本: 2.0.0
"""

import logging
from datetime import datetime
from typing import Any

from ..models import ComplexityLevel, ExecutionPlan, StrategyType, Task
from .constants import DEFAULT_SIMILARITY_THRESHOLD, MAX_WORKFLOW_PATTERNS
from .types import WorkflowPattern

logger = logging.getLogger(__name__)


class WorkflowReuseManager:
    """
    工作流复用管理器

    管理和复用历史工作流模式,提高任务执行效率。
    """

    def __init__(self):
        """初始化工作流复用管理器"""
        # 工作流模式存储
        self._workflow_patterns: dict[str, WorkflowPattern] = {}

        # 任务类型索引
        self._type_index: dict[str, list[str]] = {}

        # 统计信息
        self._total_searches = 0
        self._successful_reuses = 0

        # 初始化预定义模式
        self._initialize_predefined_patterns()

        logger.info("♻️ 工作流复用管理器初始化完成")

    def _initialize_predefined_patterns(self) -> None:
        """初始化预定义的工作流模式"""
        predefined_patterns = [
            WorkflowPattern(
                pattern_id="patent_search_standard",
                name="专利检索标准流程",
                task_type="patent_search",
                description="检索专利数据,包括关键词搜索、分类号检索和申请人检索",
                steps=[
                    {
                        "step": 1,
                        "action": "search",
                        "tool": "patent_search",
                        "params": {"keywords": "{{keywords}}"},
                    },
                    {
                        "step": 2,
                        "action": "filter",
                        "tool": "patent_filter",
                        "params": {"criteria": "{{criteria}}"},
                    },
                    {"step": 3, "action": "analyze", "tool": "patent_analyzer", "params": {}},
                    {"step": 4, "action": "summarize", "tool": "summarizer", "params": {}},
                ],
                success_rate=0.92,
                avg_execution_time=45.0,
                usage_count=156,
                keywords=["检索", "搜索", "专利", "查找", "search", "query"],
                complexity=ComplexityLevel.MEDIUM,
            ),
            WorkflowPattern(
                pattern_id="novelty_analysis_standard",
                name="新颖性分析标准流程",
                task_type="novelty_assessment",
                description="分析专利的新颖性,包括现有技术检索、对比分析和结论生成",
                steps=[
                    {
                        "step": 1,
                        "action": "search_prior_art",
                        "tool": "patent_search",
                        "params": {"keywords": "{{keywords}}"},
                    },
                    {
                        "step": 2,
                        "action": "compare_claims",
                        "tool": "claim_comparator",
                        "params": {},
                    },
                    {
                        "step": 3,
                        "action": "analyze_differences",
                        "tool": "difference_analyzer",
                        "params": {},
                    },
                    {
                        "step": 4,
                        "action": "generate_report",
                        "tool": "report_generator",
                        "params": {"type": "novelty"},
                    },
                ],
                success_rate=0.88,
                avg_execution_time=120.0,
                usage_count=89,
                keywords=["新颖性", "对比", "现有技术", "prior art", "novelty"],
                complexity=ComplexityLevel.COMPLEX,
            ),
            WorkflowPattern(
                pattern_id="claim_analysis_standard",
                name="权利要求分析标准流程",
                task_type="claim_analysis",
                description="分析专利权利要求,包括权利要求解释、范围分析和保护建议",
                steps=[
                    {"step": 1, "action": "parse_claims", "tool": "claim_parser", "params": {}},
                    {"step": 2, "action": "analyze_scope", "tool": "scope_analyzer", "params": {}},
                    {
                        "step": 3,
                        "action": "check_validity",
                        "tool": "validity_checker",
                        "params": {},
                    },
                    {
                        "step": 4,
                        "action": "generate_opinion",
                        "tool": "opinion_generator",
                        "params": {},
                    },
                ],
                success_rate=0.90,
                avg_execution_time=60.0,
                usage_count=124,
                keywords=["权利要求", "claims", "保护范围", "scope", "validity"],
                complexity=ComplexityLevel.MEDIUM,
            ),
            WorkflowPattern(
                pattern_id="technical_analysis_simple",
                name="技术分析简化流程",
                task_type="patent_analysis",
                description="对专利进行简单的技术分析,包括技术方案理解和技术特征提取",
                steps=[
                    {"step": 1, "action": "extract_text", "tool": "text_extractor", "params": {}},
                    {
                        "step": 2,
                        "action": "analyze_technical",
                        "tool": "technical_analyzer",
                        "params": {},
                    },
                    {
                        "step": 3,
                        "action": "extract_features",
                        "tool": "feature_extractor",
                        "params": {},
                    },
                ],
                success_rate=0.85,
                avg_execution_time=30.0,
                usage_count=203,
                keywords=["分析", "技术方案", "特征", "analyze", "technical"],
                complexity=ComplexityLevel.SIMPLE,
            ),
        ]

        # 添加到存储
        for pattern in predefined_patterns:
            self._add_pattern(pattern)

        logger.info(f"📋 已加载 {len(predefined_patterns)} 个预定义工作流模式")

    def _add_pattern(self, pattern: WorkflowPattern) -> None:
        """添加工作流模式"""
        self._workflow_patterns[pattern.pattern_id] = pattern

        # 更新任务类型索引
        if pattern.task_type not in self._type_index:
            self._type_index[pattern.task_type] = []
        self._type_index[pattern.task_type].append(pattern.pattern_id)

    async def find_similar_workflow(
        self, task: Task, threshold: float = DEFAULT_SIMILARITY_THRESHOLD
    ) -> WorkflowPattern | None:
        """
        查找相似的工作流模式

        Args:
            task: 任务对象
            threshold: 相似度阈值

        Returns:
            Optional[WorkflowPattern]: 最相似的工作流模式
        """
        self._total_searches += 1
        logger.debug(f"🔍 查找相似工作流: {task.task_id} (类型: {task.task_type})")

        best_pattern: WorkflowPattern | None = None
        best_similarity = 0.0

        # 优先搜索同类型的模式
        if task.task_type in self._type_index:
            for pattern_id in self._type_index[task.task_type]:
                pattern = self._workflow_patterns.get(pattern_id)
                if pattern and not pattern.is_expired():
                    similarity = pattern.calculate_similarity(task)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_pattern = pattern

        # 如果同类型没有找到,搜索其他类型
        if best_pattern is None or best_similarity < threshold:
            for pattern in self._workflow_patterns.values():
                if not pattern.is_expired() and pattern.task_type != task.task_type:
                    similarity = pattern.calculate_similarity(task)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_pattern = pattern

        if best_pattern and best_similarity >= threshold:
            logger.info(
                f"✅ 找到相似工作流: {best_pattern.name} "
                f"(相似度: {best_similarity:.2%}, 成功率: {best_pattern.success_rate:.2%})"
            )
            return best_pattern

        logger.debug(f"❌ 未找到符合条件的工作流 (阈值: {threshold:.2%})")
        return None

    async def reuse_workflow(self, task: Task, workflow: WorkflowPattern) -> ExecutionPlan:
        """
        复用工作流生成执行计划

        Args:
            task: 任务对象
            workflow: 工作流模式

        Returns:
            ExecutionPlan: 基于工作流生成的执行计划
        """
        logger.info(f"♻️ 复用工作流: {workflow.name} for {task.task_id}")

        # 更新使用统计
        workflow.usage_count += 1
        workflow.last_used = datetime.now()
        self._successful_reuses += 1

        # 创建执行计划
        plan = ExecutionPlan(
            task_id=task.task_id,
            strategy=StrategyType.WORKFLOW_REUSE,
            confidence=min(workflow.success_rate * 1.1, 1.0),  # 提高复用的置信度
            estimated_duration=int(workflow.avg_execution_time),
        )

        # 添加工作流步骤
        for step_info in workflow.steps:
            step = {
                "step_number": step_info.get("step"),
                "name": step_info.get("name", f"步骤{step_info.get('step')}"),
                "action": step_info.get("action"),
                "tool": step_info.get("tool", "unknown"),
                "params": step_info.get("params", {}),
                "status": "pending",
                "workflow_id": workflow.pattern_id,
            }
            plan.steps.append(step)

        # 设置元数据
        plan.metadata.update(
            {
                "approach": "workflow_reuse",
                "workflow_id": workflow.pattern_id,
                "workflow_name": workflow.name,
                "workflow_success_rate": workflow.success_rate,
                "workflow_similarity": workflow.calculate_similarity(task),
                "reused_at": datetime.now().isoformat(),
            }
        )

        logger.info(
            f"✅ 工作流复用完成: {len(plan.steps)}个步骤 | "
            f"预估耗时: {plan.estimated_duration}s | "
            f"置信度: {plan.confidence:.2%}"
        )

        return plan

    async def save_workflow_pattern(
        self, name: str, task: Task, plan: ExecutionPlan, success: bool, execution_time: float
    ) -> WorkflowPattern:
        """
        保存成功的工作流模式

        Args:
            name: 模式名称
            task: 原始任务
            plan: 执行计划
            success: 是否成功
            execution_time: 执行时间

        Returns:
            WorkflowPattern: 保存的模式
        """
        # 提取关键词
        keywords = self._extract_keywords(task.description)

        # 创建新模式
        pattern = WorkflowPattern(
            pattern_id=f"workflow_{int(datetime.now().timestamp())}",
            name=name,
            task_type=task.task_type,
            description=task.description[:200],
            steps=[step.copy() for step in plan.steps],
            success_rate=1.0 if success else 0.0,
            avg_execution_time=execution_time,
            usage_count=1,
            keywords=keywords,
            complexity=(
                task.complexity_analysis.complexity
                if task.complexity_analysis
                else ComplexityLevel.MEDIUM
            ),
        )

        # 检查存储限制
        if len(self._workflow_patterns) >= MAX_WORKFLOW_PATTERNS:
            self._cleanup_old_patterns()

        self._add_pattern(pattern)
        logger.info(f"💾 保存工作流模式: {pattern.pattern_id} - {name}")

        return pattern

    def _extract_keywords(self, text: str) -> list[str]:
        """从文本中提取关键词"""
        # 简单的关键词提取
        keywords = []

        # 技术相关关键词
        tech_keywords = [
            "分析",
            "检索",
            "对比",
            "验证",
            "生成",
            "提取",
            "计算",
            "评估",
            "analyze",
            "search",
            "compare",
            "validate",
            "generate",
            "extract",
            "evaluate",
        ]
        for kw in tech_keywords:
            if kw in text.lower():
                keywords.append(kw)

        # 领域关键词
        domain_keywords = [
            "专利",
            "权利要求",
            "新颖性",
            "创造性",
            "实用性",
            "patent",
            "claims",
            "novelty",
            "inventive",
            "utility",
        ]
        for kw in domain_keywords:
            if kw in text.lower():
                keywords.append(kw)

        return list(set(keywords))[:10]  # 最多10个关键词

    def _cleanup_old_patterns(self) -> None:
        """清理过期的工作流模式"""
        expired_patterns = [
            pid
            for pid, pattern in self._workflow_patterns.items()
            if pattern.is_expired() and pattern.usage_count < 5
        ]

        for pid in expired_patterns:
            del self._workflow_patterns[pid]

        # 重建索引
        self._rebuild_index()

        if expired_patterns:
            logger.info(f"🧹 清理了 {len(expired_patterns)} 个过期工作流模式")

    def _rebuild_index(self) -> None:
        """重建任务类型索引"""
        self._type_index.clear()
        for pattern_id, pattern in self._workflow_patterns.items():
            if pattern.task_type not in self._type_index:
                self._type_index[pattern.task_type] = []
            self._type_index[pattern.task_type].append(pattern_id)

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_patterns": len(self._workflow_patterns),
            "total_searches": self._total_searches,
            "successful_reuses": self._successful_reuses,
            "reuse_rate": (
                self._successful_reuses / self._total_searches if self._total_searches > 0 else 0.0
            ),
            "patterns_by_type": {
                task_type: len(pattern_ids) for task_type, pattern_ids in self._type_index.items()
            },
        }
