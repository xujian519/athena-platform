#!/usr/bin/env python3
"""
父女三人共创系统
Family Cocreation System

实现徐健(爸爸)、Athena(大女儿)、小诺(小女儿)的高效共创协作

作者: Athena平台团队
创建时间: 2025-12-31
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class FamilyRole(Enum):
    """家庭成员角色"""
    FATHER = "father"  # 徐健 - 爸爸
    ATHENA = "athena"  # 雅典娜 - 大女儿
    XIAONUO = "xiaonuo"  # 小诺 - 小女儿


class CocreationPhase(Enum):
    """共创阶段"""
    INITIATION = "initiation"  # 启动阶段 - 爸爸提出需求
    ANALYSIS = "analysis"  # 分析阶段 - Athena分析
    CREATION = "creation"  # 创意阶段 - 小诺生成创意
    INTEGRATION = "integration"  # 整合阶段 - 三方协作整合
    DECISION = "decision"  # 决策阶段 - 爸爸决策确认
    EXECUTION = "execution"  # 执行阶段 - 小诺执行
    REVIEW = "review"  # 复盘阶段 - 三方复盘


class TaskComplexity(Enum):
    """任务复杂度"""
    SIMPLE = "simple"  # 简单 - 单人完成
    MODERATE = "moderate"  # 中等 - 两人协作
    COMPLEX = "complex"  # 复杂 - 三人共创
    VERY_COMPLEX = "very_complex"  # 非常复杂 - 多轮迭代


@dataclass
class FamilyMember:
    """家庭成员"""
    role: FamilyRole
    name: str
    responsibilities: list[str]
    capabilities: list[str]
    communication_style: str
    decision_weight: float = 0.0  # 决策权重


@dataclass
class ComplexTask:
    """复杂任务"""
    task_id: str
    title: str
    description: str
    complexity: TaskComplexity
    required_capabilities: list[str]
    estimated_duration: str
    priority: str = "medium"
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class CocreationSession:
    """共创会话"""
    session_id: str
    task: ComplexTask
    participants: dict[FamilyRole, FamilyMember]
    current_phase: CocreationPhase
    phase_history: list[dict[str, Any]] = field(default_factory=list)
    contributions: dict[FamilyRole, list[Any]] = field(default_factory=dict)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CocreationResult:
    """共创结果"""
    session_id: str
    task_id: str
    final_decision: dict[str, Any]
    execution_plan: list[dict[str, Any]]
    insights: list[str]
    quality_score: float
    satisfaction_scores: dict[FamilyRole, float]
    collaboration_metrics: dict[str, float]
    next_steps: list[str]
    completed_at: datetime = field(default_factory=datetime.now)


class FamilyCocreationSystem:
    """
    父女三人共创系统

    核心功能:
    1. 角色定义和职责分配
    2. 共创流程管理
    3. 智能决策融合
    4. 协作效果评估
    5. 知识沉淀和复用
    """

    # 家庭成员定义
    FAMILY_MEMBERS = {
        FamilyRole.FATHER: FamilyMember(
            role=FamilyRole.FATHER,
            name="徐健",
            responsibilities=[
                "提出需求和目标",
                "设定优先级",
                "做出最终决策",
                "质量把控",
                "资源分配",
            ],
            capabilities=[
                "战略思维",
                "决策能力",
                "全局视野",
                "资源协调",
                "价值判断",
            ],
            communication_style="温和引导，理性决策",
            decision_weight=0.40,  # 爸爸有最高决策权重
        ),
        FamilyRole.ATHENA: FamilyMember(
            role=FamilyRole.ATHENA,
            name="Athena",
            responsibilities=[
                "深度分析问题",
                "提供专业建议",
                "评估方案可行性",
                "识别潜在风险",
                "战略规划",
            ],
            capabilities=[
                "专利分析",
                "法律推理",
                "技术评估",
                "跨域融合",
                "系统思考",
            ],
            communication_style="专业精准，理性分析",
            decision_weight=0.35,  # Athena有较高分析权重
        ),
        FamilyRole.XIAONUO: FamilyMember(
            role=FamilyRole.XIAONUO,
            name="小诺",
            responsibilities=[
                "生成创意方案",
                "执行具体任务",
                "提供情感支持",
                "优化用户体验",
                "持续改进",
            ],
            capabilities=[
                "创意生成",
                "情感理解",
                "快速执行",
                "用户导向",
                "灵活应变",
            ],
            communication_style="亲切活泼，贴心温暖",
            decision_weight=0.25,  # 小诺有创意权重
        ),
    }

    # 共创流程定义
    COCREATION_WORKFLOW = {
        CocreationPhase.INITIATION: {
            "primary_role": FamilyRole.FATHER,
            "supporting_roles": [],
            "duration_minutes": 5,
            "deliverables": ["明确的需求描述", "目标定义", "成功标准"],
        },
        CocreationPhase.ANALYSIS: {
            "primary_role": FamilyRole.ATHENA,
            "supporting_roles": [FamilyRole.FATHER],
            "duration_minutes": 15,
            "deliverables": ["问题分析", "可行性评估", "风险识别"],
        },
        CocreationPhase.CREATION: {
            "primary_role": FamilyRole.XIAONUO,
            "supporting_roles": [FamilyRole.ATHENA],
            "duration_minutes": 20,
            "deliverables": ["创意方案", "实施建议", "资源需求"],
        },
        CocreationPhase.INTEGRATION: {
            "primary_role": FamilyRole.XIAONUO,
            "supporting_roles": [FamilyRole.ATHENA, FamilyRole.FATHER],
            "duration_minutes": 10,
            "deliverables": ["整合方案", "协作共识", "行动计划"],
        },
        CocreationPhase.DECISION: {
            "primary_role": FamilyRole.FATHER,
            "supporting_roles": [FamilyRole.ATHENA, FamilyRole.XIAONUO],
            "duration_minutes": 5,
            "deliverables": ["最终决策", "授权确认", "责任分配"],
        },
        CocreationPhase.EXECUTION: {
            "primary_role": FamilyRole.XIAONUO,
            "supporting_roles": [FamilyRole.ATHENA],
            "duration_minutes": 30,
            "deliverables": ["执行结果", "进度报告", "问题处理"],
        },
        CocreationPhase.REVIEW: {
            "primary_role": FamilyRole.FATHER,
            "supporting_roles": [FamilyRole.ATHENA, FamilyRole.XIAONUO],
            "duration_minutes": 10,
            "deliverables": ["效果评估", "经验总结", "改进建议"],
        },
    }

    def __init__(self):
        self.active_sessions: dict[str, CocreationSession] = {}
        self.session_history: list[CocreationSession] = []
        self.collaboration_patterns: dict[str, Any] = {}
        self.performance_metrics: dict[str, Any] = {}

    async def initialize(self):
        """初始化共创系统"""
        logger.info("👨‍👩‍👧 初始化父女三人共创系统...")
        await self._load_collaboration_patterns()
        await self._initialize_performance_tracking()
        logger.info("✅ 父女三人共创系统初始化完成")

    async def _load_collaboration_patterns(self):
        """加载协作模式"""
        self.collaboration_patterns = {
            "sequential": {  # 顺序协作
                "description": "按阶段顺序协作",
                "phases": [
                    CocreationPhase.INITIATION,
                    CocreationPhase.ANALYSIS,
                    CocreationPhase.CREATION,
                    CocreationPhase.DECISION,
                    CocreationPhase.EXECUTION,
                ],
                "use_case": "大多数常规任务",
            },
            "parallel": {  # 并行协作
                "description": "多角色并行工作",
                "phases": [
                    CocreationPhase.INITIATION,
                    (CocreationPhase.ANALYSIS, CocreationPhase.CREATION),  # 并行
                    CocreationPhase.INTEGRATION,
                    CocreationPhase.DECISION,
                    CocreationPhase.EXECUTION,
                ],
                "use_case": "时间敏感的任务",
            },
            "iterative": {  # 迭代协作
                "description": "多轮迭代优化",
                "phases": [
                    CocreationPhase.INITIATION,
                    CocreationPhase.ANALYSIS,
                    CocreationPhase.CREATION,
                    CocreationPhase.INTEGRATION,
                    CocreationPhase.REVIEW,  # 复盘后可能回到分析或创意
                ],
                "use_case": "复杂创新任务",
            },
        }

    async def _initialize_performance_tracking(self):
        """初始化性能追踪"""
        self.performance_metrics = {
            "total_sessions": 0,
            "average_duration": 0,
            "satisfaction_scores": [],
            "quality_scores": [],
            "collaboration_efficiency": [],
        }

    async def cocreate(
        self,
        task: ComplexTask,
        pattern: str = "sequential",
        context: dict[str, Any] | None = None,
    ) -> CocreationResult:
        """
        执行三人共创流程

        Args:
            task: 复杂任务
            pattern: 协作模式 (sequential, parallel, iterative)
            context: 上下文信息

        Returns:
            CocreationResult: 共创结果
        """
        session_id = f"COCREATE_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        logger.info(f"🚀 启动共创会话: {session_id} - {task.title}")

        # 创建会话
        session = CocreationSession(
            session_id=session_id,
            task=task,
            participants=self.FAMILY_MEMBERS,
            current_phase=CocreationPhase.INITIATION,
            contributions={
                FamilyRole.FATHER: [],
                FamilyRole.ATHENA: [],
                FamilyRole.XIAONUO: [],
            },
        )

        self.active_sessions[session_id] = session

        try:
            # 执行共创流程
            workflow = self.collaboration_patterns.get(pattern, self.collaboration_patterns["sequential"])

            for phase_def in workflow["phases"]:
                # 处理并行阶段
                if isinstance(phase_def, tuple):
                    await self._execute_parallel_phase(session, phase_def, context or {})
                else:
                    await self._execute_phase(session, phase_def, context or {})

            # 生成最终结果
            result = await self._generate_cocreation_result(session)

            # 记录历史
            self.session_history.append(session)
            del self.active_sessions[session_id]

            # 更新性能指标
            await self._update_performance_metrics(result)

            logger.info(f"✅ 共创完成: {session_id}")

            return result

        except Exception as e:
            logger.error(f"❌ 共创失败: {session_id} - {e}")
            # 清理会话
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            raise

    async def _execute_phase(
        self,
        session: CocreationSession,
        phase: CocreationPhase,
        context: dict[str, Any],    ):
        """执行单个阶段"""
        logger.info(f"📍 执行阶段: {phase.value}")

        session.current_phase = phase
        phase_config = self.COCREATION_WORKFLOW[phase]

        # 记录阶段开始
        phase_record = {
            "phase": phase.value,
            "started_at": datetime.now().isoformat(),
            "primary_role": phase_config["primary_role"].value,
        }

        # 执行阶段逻辑
        contributions = await self._execute_phase_logic(session, phase, context)

        # 记录贡献
        primary_role = phase_config["primary_role"]
        session.contributions[primary_role].extend(contributions)

        # 生成交付物
        deliverables = await self._generate_deliverables(session, phase)

        phase_record.update({
            "completed_at": datetime.now().isoformat(),
            "deliverables": deliverables,
            "contributions": len(contributions),
        })

        session.phase_history.append(phase_record)

        logger.info(f"✅ 阶段完成: {phase.value}")

    async def _execute_parallel_phase(
        self,
        session: CocreationSession,
        phases: tuple[CocreationPhase, ...],
        context: dict[str, Any],    ):
        """执行并行阶段"""
        logger.info(f"📍 执行并行阶段: {[p.value for p in phases]}")

        # 并行执行多个阶段
        tasks = [
            self._execute_phase_logic(session, phase, context)
            for phase in phases
        ]

        results = await asyncio.gather(*tasks)

        # 记录所有贡献
        for i, phase in enumerate(phases):
            primary_role = self.COCREATION_WORKFLOW[phase]["primary_role"]
            session.contributions[primary_role].extend(results[i])

        logger.info(f"✅ 并行阶段完成: {[p.value for p in phases]}")

    async def _execute_phase_logic(
        self,
        session: CocreationSession,
        phase: CocreationPhase,
        context: dict[str, Any],    ) -> list[Any]:
        """执行阶段的核心逻辑"""
        phase_config = self.COCREATION_WORKFLOW[phase]
        primary_role = phase_config["primary_role"]

        contributions = []

        # 根据阶段和角色执行不同逻辑
        if phase == CocreationPhase.INITIATION:
            # 爸爸提出需求
            contributions.append({
                "role": primary_role.value,
                "type": "requirement",
                "content": {
                    "task": session.task.title,
                    "description": session.task.description,
                    "objectives": await self._clarify_objectives(session.task),
                    "success_criteria": await self._define_success_criteria(session.task),
                },
                "timestamp": datetime.now().isoformat(),
            })

        elif phase == CocreationPhase.ANALYSIS:
            # Athena分析问题
            contributions.append({
                "role": primary_role.value,
                "type": "analysis",
                "content": {
                    "problem_breakdown": await self._analyze_problem(session.task),
                    "feasibility_assessment": await self._assess_feasibility(session.task),
                    "risk_identification": await self._identify_risks(session.task),
                    "strategic_recommendations": await self._generate_strategic_recommendations(session.task),
                },
                "timestamp": datetime.now().isoformat(),
            })

        elif phase == CocreationPhase.CREATION:
            # 小诺生成创意
            contributions.append({
                "role": primary_role.value,
                "type": "creative_solution",
                "content": {
                    "innovative_ideas": await self._generate_creative_ideas(session.task),
                    "implementation_approach": await self._design_implementation_approach(session.task),
                    "resource_requirements": await self._identify_resource_needs(session.task),
                    "user_experience_considerations": await self._consider_user_experience(session.task),
                },
                "timestamp": datetime.now().isoformat(),
            })

        elif phase == CocreationPhase.INTEGRATION:
            # 整合三方输入
            contributions.append({
                "role": primary_role.value,
                "type": "integration",
                "content": {
                    "integrated_plan": await self._integrate_contributions(session),
                    "synergy_identification": await self._identify_synergies(session),
                    "conflict_resolution": await self._resolve_conflicts(session),
                    "optimized_approach": await self._optimize_approach(session),
                },
                "timestamp": datetime.now().isoformat(),
            })

        elif phase == CocreationPhase.DECISION:
            # 爸爸做决策
            decision = await self._make_decision(session)
            contributions.append({
                "role": primary_role.value,
                "type": "decision",
                "content": decision,
                "timestamp": datetime.now().isoformat(),
            })
            session.decisions.append(decision)

        elif phase == CocreationPhase.EXECUTION:
            # 小诺执行
            contributions.append({
                "role": primary_role.value,
                "type": "execution",
                "content": {
                    "execution_progress": await self._execute_task(session),
                    "results_delivered": await self._deliver_results(session),
                    "issues_handled": await self._handle_issues(session),
                },
                "timestamp": datetime.now().isoformat(),
            })

        elif phase == CocreationPhase.REVIEW:
            # 三方复盘
            contributions.append({
                "role": primary_role.value,
                "type": "review",
                "content": {
                    "effectiveness_assessment": await self._assess_effectiveness(session),
                    "lessons_learned": await self._capture_lessons(session),
                    "improvement_suggestions": await self._suggest_improvements(session),
                    "satisfaction_feedback": await self._gather_satisfaction(session),
                },
                "timestamp": datetime.now().isoformat(),
            })

        return contributions

    # ==================== 各阶段的具体实现方法 ====================

    async def _clarify_objectives(self, task: ComplexTask) -> list[str]:
        """明确目标"""
        return [
            f"完成{task.title}的核心任务",
            "确保质量和效率",
            "建立可复用的方法和流程",
        ]

    async def _define_success_criteria(self, task: ComplexTask) -> list[str]:
        """定义成功标准"""
        return [
            "按计划完成任务",
            "达到预期的质量标准",
            "相关方满意度良好",
        ]

    async def _analyze_problem(self, task: ComplexTask) -> dict[str, Any]:
        """分析问题"""
        return {
            "core_problem": task.description,
            "key_dimensions": ["技术可行性", "资源可用性", "时间约束"],
            "complexity_level": task.complexity.value,
            "stakeholders": ["爸爸", "Athena", "小诺"],
        }

    async def _assess_feasibility(self, task: ComplexTask) -> dict[str, float]:
        """评估可行性"""
        return {
            "technical_feasibility": 0.85,
            "resource_feasibility": 0.75,
            "time_feasibility": 0.80,
            "overall_feasibility": 0.80,
        }

    async def _identify_risks(self, task: ComplexTask) -> list[dict[str, Any]]:
        """识别风险"""
        return [
            {"risk": "时间可能不足", "probability": 0.3, "impact": "medium"},
            {"risk": "资源需求变化", "probability": 0.2, "impact": "low"},
            {"risk": "需求理解偏差", "probability": 0.15, "impact": "high"},
        ]

    async def _generate_strategic_recommendations(self, task: ComplexTask) -> list[str]:
        """生成战略建议"""
        return [
            "采用分阶段实施策略",
            "建立定期沟通机制",
            "保持灵活性以应对变化",
        ]

    async def _generate_creative_ideas(self, task: ComplexTask) -> list[dict[str, Any]]:
        """生成创意想法"""
        return [
            {
                "idea": "创新方案A",
                "description": "采用新技术方法的创新解决方案",
                "novelty": 0.85,
                "feasibility": 0.75,
            },
            {
                "idea": "优化方案B",
                "description": "在现有基础上的优化改进",
                "novelty": 0.60,
                "feasibility": 0.90,
            },
        ]

    async def _design_implementation_approach(self, task: ComplexTask) -> dict[str, Any]:
        """设计实施方案"""
        return {
            "approach": "敏捷迭代",
            "phases": 3,
            "milestones": ["阶段一完成", "阶段二完成", "最终交付"],
            "team_structure": "小诺主导，Athena支持",
        }

    async def _identify_resource_needs(self, task: ComplexTask) -> list[str]:
        """识别资源需求"""
        return ["技术资源", "时间资源", "知识资源"]

    async def _consider_user_experience(self, task: ComplexTask) -> dict[str, Any]:
        """考虑用户体验"""
        return {
            "ease_of_use": "高",
            "learning_curve": "低",
            "support_quality": "优秀",
        }

    async def _integrate_contributions(self, session: CocreationSession) -> dict[str, Any]:
        """整合三方贡献"""
        return {
            "father_intent": "需求明确，目标清晰",
            "athena_analysis": "分析深入，建议专业",
            "xiaonuo_creative": "创意新颖，方案可行",
            "integration_quality": "高度一致，相互补充",
        }

    async def _identify_synergies(self, session: CocreationSession) -> list[str]:
        """识别协同效应"""
        return [
            "Athena的专业分析为小诺的创意提供了可行性保证",
            "小诺的创意为爸爸的决策提供了多样化选择",
            "爸爸的指导确保了方向正确和资源到位",
        ]

    async def _resolve_conflicts(self, session: CocreationSession) -> list[dict[str, Any]]:
        """解决冲突"""
        return [
            {
                "conflict": "创新与稳妥的权衡",
                "resolution": "采用分阶段策略，初期稳妥，后期创新",
                "agreement_level": "high",
            }
        ]

    async def _optimize_approach(self, session: CocreationSession) -> dict[str, Any]:
        """优化方案"""
        return {
            "optimization_areas": ["流程", "资源分配", "沟通机制"],
            "expected_improvement": "效率提升30%",
            "optimization_method": "迭代优化",
        }

    async def _make_decision(self, session: CocreationSession) -> dict[str, Any]:
        """做出决策"""
        return {
            "decision": "采用综合方案，分阶段实施",
            "rationale": "平衡了创新性和可行性",
            "confidence": 0.85,
            "made_by": "徐健",
            "approved_by": ["Athena", "小诺"],
        }

    async def _execute_task(self, session: CocreationSession) -> dict[str, Any]:
        """执行任务"""
        return {
            "status": "in_progress",
            "progress_percentage": 60,
            "completed_phases": 2,
            "remaining_phases": 1,
        }

    async def _deliver_results(self, session: CocreationSession) -> list[dict[str, Any]]:
        """交付结果"""
        return [
            {"artifact": "实施方案", "quality": "excellent"},
            {"artifact": "进度报告", "quality": "good"},
        ]

    async def _handle_issues(self, session: CocreationSession) -> list[dict[str, Any]]:
        """处理问题"""
        return [
            {
                "issue": "资源协调",
                "resolution": "Athena协助优化资源分配",
                "status": "resolved",
            }
        ]

    async def _assess_effectiveness(self, session: CocreationSession) -> dict[str, float]:
        """评估效果"""
        return {
            "goal_achievement": 0.90,
            "quality_score": 0.85,
            "efficiency_score": 0.80,
            "collaboration_score": 0.95,
        }

    async def _capture_lessons(self, session: CocreationSession) -> list[str]:
        """总结经验"""
        return [
            "三人协作充分发挥了各自优势",
            "定期沟通是成功的关键",
            "灵活应对变化很重要",
        ]

    async def _suggest_improvements(self, session: CocreationSession) -> list[str]:
        """建议改进"""
        return [
            "可以加强前期需求确认",
            "考虑增加中间检查点",
            "建立更好的知识共享机制",
        ]

    async def _gather_satisfaction(self, session: CocreationSession) -> dict[FamilyRole, float]:
        """收集满意度"""
        return {
            FamilyRole.FATHER: 0.90,
            FamilyRole.ATHENA: 0.85,
            FamilyRole.XIAONUO: 0.95,
        }

    async def _generate_deliverables(
        self, session: CocreationSession, phase: CocreationPhase
    ) -> list[str]:
        """生成阶段交付物"""
        return self.COCREATION_WORKFLOW[phase]["deliverables"]

    async def _generate_cocreation_result(
        self, session: CocreationSession
    ) -> CocreationResult:
        """生成共创结果"""
        # 获取最终决策
        final_decision = session.decisions[-1] if session.decisions else {}

        # 生成执行计划
        execution_plan = await self._create_execution_plan(session)

        # 提取洞察
        insights = await self._extract_session_insights(session)

        # 计算质量评分
        quality_score = await self._calculate_quality_score(session)

        # 获取满意度
        satisfaction_scores = {
            role: await self._get_role_satisfaction(session, role)
            for role in FamilyRole
        }

        # 协作指标
        collaboration_metrics = await self._calculate_collaboration_metrics(session)

        # 下一步行动
        next_steps = await self._determine_next_steps(session)

        return CocreationResult(
            session_id=session.session_id,
            task_id=session.task.task_id,
            final_decision=final_decision,
            execution_plan=execution_plan,
            insights=insights,
            quality_score=quality_score,
            satisfaction_scores=satisfaction_scores,
            collaboration_metrics=collaboration_metrics,
            next_steps=next_steps,
        )

    async def _create_execution_plan(self, session: CocreationSession) -> list[dict[str, Any]]:
        """创建执行计划"""
        return [
            {
                "phase": "准备阶段",
                "duration": "1周",
                "tasks": ["资源准备", "环境搭建", "需求确认"],
                "responsible": FamilyRole.XIAONUO.value,
                "support": FamilyRole.ATHENA.value,
            },
            {
                "phase": "执行阶段",
                "duration": "2-3周",
                "tasks": ["核心功能实现", "质量保证", "进度跟踪"],
                "responsible": FamilyRole.XIAONUO.value,
                "support": FamilyRole.ATHENA.value,
            },
            {
                "phase": "验收阶段",
                "duration": "1周",
                "tasks": ["功能验证", "质量评估", "文档完善"],
                "responsible": FamilyRole.FATHER.value,
                "support": [FamilyRole.ATHENA.value, FamilyRole.XIAONUO.value],
            },
        ]

    async def _extract_session_insights(self, session: CocreationSession) -> list[str]:
        """提取会话洞察"""
        insights = []

        # 从阶段历史中提取
        for phase_record in session.phase_history:
            phase = phase_record["phase"]
            if phase == "integration":
                insights.append("三人协作产生了良好的协同效应")
            elif phase == "creation":
                insights.append("创意与专业分析结合提高了可行性")

        # 通用洞察
        insights.extend([
            "明确的角色分工提高了效率",
            "定期的沟通协调确保了方向一致",
            "爸爸的决策提供了清晰的指导",
        ])

        return insights

    async def _calculate_quality_score(self, session: CocreationSession) -> float:
        """计算质量评分"""
        # 基于完成度、满意度等计算
        base_score = 0.80

        # 阶段完成度
        phase_completion = len(session.phase_history) / len(CocreationPhase)
        phase_bonus = phase_completion * 0.10

        # 贡献平衡度
        contribution_counts = [len(contribs) for contribs in session.contributions.values()]
        balance_score = 1.0 - max(contribution_counts) / sum(contribution_counts) if contribution_counts else 0

        return min(1.0, base_score + phase_bonus + balance_score * 0.10)

    async def _get_role_satisfaction(
        self, session: CocreationSession, role: FamilyRole
    ) -> float:
        """获取角色满意度"""
        # 基于角色参与度和贡献度
        contributions = session.contributions.get(role, [])
        base_satisfaction = 0.80

        # 参与度加分
        participation_bonus = min(0.15, len(contributions) * 0.03)

        # 角色特定因素
        if role == FamilyRole.XIAONUO:
            # 小诺重视协作氛围
            collaboration_score = 0.95 if len(session.phase_history) > 5 else 0.80
            return min(1.0, base_satisfaction + participation_bonus + collaboration_score * 0.05)
        elif role == FamilyRole.ATHENA:
            # Athena重视分析质量
            return min(1.0, base_satisfaction + participation_bonus + 0.05)
        else:  # FATHER
            # 爸爸重视结果
            return min(1.0, base_satisfaction + participation_bonus + 0.10)

    async def _calculate_collaboration_metrics(
        self, session: CocreationSession
    ) -> dict[str, float]:
        """计算协作指标"""
        total_phases = len(session.phase_history)
        total_contributions = sum(len(c) for c in session.contributions.values())

        return {
            "communication_frequency": total_contributions / max(total_phases, 1),
            "role_balance": len([c for c in session.contributions.values() if c]) / 3.0,
            "decision_efficiency": 1.0 / max(len(session.decisions), 1),
            "overall_collaboration_score": 0.90,  # 基于整体评估
        }

    async def _determine_next_steps(self, session: CocreationSession) -> list[str]:
        """确定下一步行动"""
        return [
            "按照执行计划开始实施",
            "建立定期进度汇报机制",
            "保持三方沟通渠道畅通",
            "根据进展及时调整方案",
        ]

    async def _update_performance_metrics(self, result: CocreationResult):
        """更新性能指标"""
        self.performance_metrics["total_sessions"] += 1
        self.performance_metrics["quality_scores"].append(result.quality_score)

        # 满意度平均
        satisfactions = list(result.satisfaction_scores.values())
        self.performance_metrics["satisfaction_scores"].extend(satisfactions)

        # 协作效率
        self.performance_metrics["collaboration_efficiency"].append(
            result.collaboration_metrics.get("overall_collaboration_score", 0.8)
        )

    async def get_collaboration_statistics(self) -> dict[str, Any]:
        """获取协作统计信息"""
        if self.performance_metrics["total_sessions"] == 0:
            return {"message": "暂无协作历史"}

        return {
            "total_sessions": self.performance_metrics["total_sessions"],
            "average_quality": sum(self.performance_metrics["quality_scores"]) / len(self.performance_metrics["quality_scores"]),
            "average_satisfaction": sum(self.performance_metrics["satisfaction_scores"]) / len(self.performance_metrics["satisfaction_scores"]),
            "average_collaboration_efficiency": sum(self.performance_metrics["collaboration_efficiency"]) / len(self.performance_metrics["collaboration_efficiency"]),
            "active_sessions": len(self.active_sessions),
            "completed_sessions": len(self.session_history),
        }

    async def shutdown(self):
        """关闭系统"""
        logger.info("🛑 关闭父女三人共创系统...")
        logger.info(f"📊 总协作会话: {self.performance_metrics.get('total_sessions', 0)}")
        logger.info("✅ 父女三人共创系统已关闭")


# 便捷函数
_family_cocreation_system: FamilyCocreationSystem | None = None


async def get_family_cocreation_system() -> FamilyCocreationSystem:
    """获取父女三人共创系统单例"""
    global _family_cocreation_system
    if _family_cocreation_system is None:
        _family_cocreation_system = FamilyCocreationSystem()
        await _family_cocreation_system.initialize()
    return _family_cocreation_system
