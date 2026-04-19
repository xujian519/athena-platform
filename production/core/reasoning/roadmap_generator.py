#!/usr/bin/env python3
"""
技术路线图自动生成系统
Technology Roadmap Auto-Generation System

基于专利数据和技术趋势分析,自动生成智能技术路线图
作者: 小诺·双鱼座
创建时间: 2025-12-21
版本: v1.0.0 "智能路线图"
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .llm_enhanced_judgment import JudgmentContext, LLMEnhancedJudgment
from .prior_art_analyzer import PriorArtAnalyzer, TechEvolution

logger = logging.getLogger(__name__)


class RoadmapType(Enum):
    """路线图类型"""

    TECHNOLOGY_EVOLUTION = "technology_evolution"  # 技术演进路线图
    PRODUCT_DEVELOPMENT = "product_development"  # 产品开发路线图
    MARKET_ENTRY = "market_entry"  # 市场进入路线图
    COMPETITIVE_STRATEGY = "competitive_strategy"  # 竞争策略路线图
    INNOVATION_PATH = "innovation_path"  # 创新路径路线图


class MilestoneType(Enum):
    """里程碑类型"""

    TECHNICAL_BREAKTHROUGH = "technical_breakthrough"  # 技术突破
    PRODUCT_LAUNCH = "product_launch"  # 产品发布
    MARKET_MILESTONE = "market_milestone"  # 市场里程碑
    REGULATORY_APPROVAL = "regulatory_approval"  # 监管批准
    PARTNERSHIP = "partnership"  # 合作伙伴
    INVESTMENT = "investment"  # 投资


class RiskLevel(Enum):
    """风险级别"""

    LOW = (0.0, 0.3)
    MEDIUM = (0.3, 0.7)
    HIGH = (0.7, 1.0)


@dataclass
class RoadmapMilestone:
    """路线图里程碑"""

    milestone_id: str
    title: str
    description: str
    milestone_type: MilestoneType
    target_date: datetime
    dependencies: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    resources_required: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8


@dataclass
class DevelopmentPhase:
    """开发阶段"""

    phase_id: str
    phase_name: str
    duration_months: int
    objectives: list[str]
    key_activities: list[str]
    milestones: list[str] = field(default_factory=list)
    deliverables: list[str] = field(default_factory=list)
    budget_estimate: float | None = None
    team_requirements: dict[str, int] = field(default_factory=dict)


@dataclass
class MarketOpportunity:
    """市场机会"""

    opportunity_id: str
    market_segment: str
    market_size: float
    growth_rate: float
    entry_strategy: str
    competitive_advantage: str
    timeline: str
    revenue_potential: float


@dataclass
class CompetitiveIntelligence:
    """竞争情报"""

    competitor_id: str
    competitor_name: str
    technology_focus: list[str]
    patent_portfolio: int
    market_position: str
    recent_activities: list[str]
    threat_level: str


@dataclass
class TechnologyRoadmap:
    """技术路线图"""

    roadmap_id: str
    roadmap_name: str
    roadmap_type: RoadmapType
    focus_technology: str
    time_horizon_months: int
    development_phases: list[DevelopmentPhase]
    milestones: list[RoadmapMilestone]
    market_opportunities: list[MarketOpportunity]
    competitive_intelligence: list[CompetitiveIntelligence]
    risk_assessment: dict[str, Any]
    success_metrics: list[str]
    investment_requirements: dict[str, float]
    created_at: datetime = field(default_factory=datetime.now)


class RoadmapGenerator:
    """技术路线图生成器"""

    def __init__(self):
        self.name = "技术路线图自动生成系统"
        self.version = "1.0.0"
        self._initialized = False
        self.logger = logging.getLogger(self.name)

        # 核心组件
        self.prior_art_analyzer: PriorArtAnalyzer | None = None
        self.llm_judgment: LLMEnhancedJudgment | None = None

        # 模板库
        self.roadmap_templates: dict[RoadmapType, dict[str, Any]] = {}

        # 生成缓存
        self.generation_cache: dict[str, TechnologyRoadmap] = {}

        # 配置参数
        self.config = {
            "max_time_horizon_months": 60,  # 最大5年
            "default_phase_duration": 6,  # 默认阶段6个月
            "min_milestones_per_phase": 2,
            "max_risk_level": 0.7,
            "cache_ttl": 7200,
            "enable_llm_enhancement": True,
            "include_market_analysis": True,
            "include_competitive_intel": True,
        }

        # 统计信息
        self.stats = {
            "roadmaps_generated": 0,
            "milestones_created": 0,
            "phases_planned": 0,
            "cache_hits": 0,
            "generation_time_total": 0.0,
        }

    async def initialize(self):
        """初始化路线图生成器"""
        try:
            # 初始化核心组件
            self.prior_art_analyzer = PriorArtAnalyzer()
            await self.prior_art_analyzer.initialize()

            self.llm_judgment = LLMEnhancedJudgment()
            await self.llm_judgment.initialize()

            # 加载路线图模板
            await self._load_roadmap_templates()

            self._initialized = True
            self.logger.info("✅ RoadmapGenerator 初始化完成")
            return True

        except Exception:
            return False

    async def _load_roadmap_templates(self):
        """加载路线图模板"""
        try:
            # 技术演进路线图模板
            self.roadmap_templates[RoadmapType.TECHNOLOGY_EVOLUTION] = {
                "phases": [
                    {"name": "基础研究", "duration": 12, "objectives": ["理论验证", "概念验证"]},
                    {"name": "技术开发", "duration": 18, "objectives": ["原型开发", "技术验证"]},
                    {"name": "应用优化", "duration": 12, "objectives": ["性能优化", "应用测试"]},
                    {"name": "产业化", "duration": 18, "objectives": ["规模化生产", "市场推广"]},
                ],
                "milestone_types": [
                    MilestoneType.TECHNICAL_BREAKTHROUGH,
                    MilestoneType.PRODUCT_LAUNCH,
                    MilestoneType.MARKET_MILESTONE,
                ],
            }

            # 产品开发路线图模板
            self.roadmap_templates[RoadmapType.PRODUCT_DEVELOPMENT] = {
                "phases": [
                    {"name": "需求分析", "duration": 3, "objectives": ["市场调研", "需求定义"]},
                    {"name": "设计阶段", "duration": 6, "objectives": ["概念设计", "详细设计"]},
                    {"name": "开发阶段", "duration": 12, "objectives": ["功能开发", "集成测试"]},
                    {"name": "测试验证", "duration": 6, "objectives": ["系统测试", "用户验收"]},
                    {"name": "产品发布", "duration": 3, "objectives": ["市场准备", "正式发布"]},
                ],
                "milestone_types": [
                    MilestoneType.PRODUCT_LAUNCH,
                    MilestoneType.REGULATORY_APPROVAL,
                ],
            }

            self.logger.info("✅ 路线图模板加载完成")

        except Exception as e:
            self.logger.error(f"路线图模板加载失败: {e}")

    async def generate_roadmap(
        self,
        focus_technology: str,
        roadmap_type: RoadmapType,
        time_horizon_months: int | None = None,
        context: dict[str, Any] | None = None,
        patent_data: dict[str, Any] | None = None,
    ) -> TechnologyRoadmap:
        """
        生成技术路线图

        Args:
            focus_technology: 重点关注的技术
            roadmap_type: 路线图类型
            time_horizon_months: 时间跨度(月)
            context: 上下文信息
            patent_data: 专利数据

        Returns:
            TechnologyRoadmap: 技术路线图
        """
        if not self._initialized:
            raise RuntimeError("RoadmapGenerator未初始化")

        start_time = datetime.now()
        self.stats["roadmaps_generated"] += 1

        try:
            # 设置默认时间跨度
            if time_horizon_months is None:
                time_horizon_months = min(self.config.get("max_time_horizon_months"), 36)

            # 生成路线图ID
            roadmap_id = (
                f"{roadmap_type.value}_{focus_technology}_{start_time.strftime('%Y%m%d_%H%M%S')}"
            )

            # 分析技术演进
            tech_evolution = await self.prior_art_analyzer.analyze_technology_evolution(
                focus_technology
            )

            # 生成开发阶段
            development_phases = await self._generate_development_phases(
                roadmap_type, tech_evolution, time_horizon_months
            )

            # 生成里程碑
            milestones = await self._generate_milestones(
                development_phases, tech_evolution, roadmap_type
            )

            # 分析市场机会
            market_opportunities = []
            if self.config.get("include_market_analysis"):
                market_opportunities = await self._analyze_market_opportunities(
                    focus_technology, tech_evolution
                )

            # 收集竞争情报
            competitive_intelligence = []
            if self.config.get("include_competitive_intel"):
                competitive_intelligence = await self._gather_competitive_intelligence(
                    focus_technology
                )

            # 风险评估
            risk_assessment = await self._assess_risks(
                focus_technology, development_phases, tech_evolution
            )

            # 成功指标
            success_metrics = await self._define_success_metrics(roadmap_type, focus_technology)

            # 投资需求
            investment_requirements = await self._estimate_investment_requirements(
                development_phases, roadmap_type
            )

            # LLM增强分析
            if self.config.get("enable_llm_enhancement") and patent_data:
                await self._llm_enhance_roadmap(
                    focus_technology, patent_data, development_phases, milestones
                )

            # 创建路线图
            roadmap = TechnologyRoadmap(
                roadmap_id=roadmap_id,
                roadmap_name=f"{focus_technology}技术路线图",
                roadmap_type=roadmap_type,
                focus_technology=focus_technology,
                time_horizon_months=time_horizon_months,
                development_phases=development_phases,
                milestones=milestones,
                market_opportunities=market_opportunities,
                competitive_intelligence=competitive_intelligence,
                risk_assessment=risk_assessment,
                success_metrics=success_metrics,
                investment_requirements=investment_requirements,
            )

            # 更新统计
            self.stats["milestones_created"] += len(milestones)
            self.stats["phases_planned"] += len(development_phases)

            # 记录生成时间
            generation_time = (datetime.now() - start_time).total_seconds()
            self.stats["generation_time_total"] += generation_time

            self.logger.info(f"✅ 技术路线图生成完成: {roadmap_id}, 耗时: {generation_time:.2f}秒")
            return roadmap

        except Exception:
            raise

    async def _generate_development_phases(
        self, roadmap_type: RoadmapType, tech_evolution: TechEvolution, time_horizon_months: int
    ) -> list[DevelopmentPhase]:
        """生成开发阶段"""
        phases = []

        try:
            # 获取模板
            template = self.roadmap_templates.get(roadmap_type, {})
            template_phases = template.get("phases", [])

            if not template_phases:
                # 使用默认阶段
                template_phases = [
                    {"name": "规划阶段", "duration": 6, "objectives": ["需求分析", "目标设定"]},
                    {"name": "开发阶段", "duration": 12, "objectives": ["技术开发", "功能实现"]},
                    {"name": "测试阶段", "duration": 6, "objectives": ["系统测试", "性能优化"]},
                    {"name": "部署阶段", "duration": 6, "objectives": ["系统部署", "市场推广"]},
                ]

            # 调整阶段时长以适应总时间跨度
            total_template_duration = sum(p["duration"] for p in template_phases)
            scaling_factor = (
                time_horizon_months / total_template_duration
                if total_template_duration > 0
                else 1.0
            )

            current_date = datetime.now()

            for i, template_phase in enumerate(template_phases):
                # 计算阶段时长
                actual_duration = int(template_phase["duration"] * scaling_factor)
                if actual_duration < 3:  # 最短3个月
                    actual_duration = 3

                # 计算阶段时间范围
                phase_end = current_date + timedelta(days=actual_duration * 30)

                # 生成阶段ID
                phase_id = f"phase_{i+1}_{template_phase['name']}"

                # 基于技术演进调整目标
                enhanced_objectives = await self._enhance_phase_objectives(
                    template_phase["objectives"], tech_evolution, i
                )

                # 生成关键活动
                key_activities = await self._generate_key_activities(
                    template_phase["name"], enhanced_objectives
                )

                # 估算预算
                budget_estimate = await self._estimate_phase_budget(
                    template_phase["name"], actual_duration
                )

                # 估算团队需求
                team_requirements = await self._estimate_team_requirements(
                    template_phase["name"], enhanced_objectives
                )

                phase = DevelopmentPhase(
                    phase_id=phase_id,
                    phase_name=template_phase["name"],
                    duration_months=actual_duration,
                    objectives=enhanced_objectives,
                    key_activities=key_activities,
                    deliverables=await self._define_phase_deliverables(template_phase["name"]),
                    budget_estimate=budget_estimate,
                    team_requirements=team_requirements,
                )

                phases.append(phase)
                current_date = phase_end

        except Exception as e:
            self.logger.error(f"阶段生成失败: {e}")

        return phases

    async def _enhance_phase_objectives(
        self, base_objectives: list[str], tech_evolution: TechEvolution, phase_index: int
    ) -> list[str]:
        """基于技术演进增强阶段目标"""
        enhanced_objectives = base_objectives.copy()

        try:
            # 根据技术演进特点调整目标
            if phase_index == 0:  # 第一阶段
                enhanced_objectives.append("建立技术基础和理论框架")
            elif phase_index == len(base_objectives) - 1:  # 最后阶段
                enhanced_objectives.append("实现技术商业化和产业化")

            # 添加技术演进相关目标
            if tech_evolution.future_trends:
                enhanced_objectives.append(
                    f"关注未来趋势: {', '.join(tech_evolution.future_trends[:2])}"
                )

        except Exception as e:
            self.logger.warning(f"阶段目标增强失败: {e}")

        return enhanced_objectives

    async def _generate_key_activities(self, phase_name: str, objectives: list[str]) -> list[str]:
        """生成关键活动"""
        activities = []

        try:
            # 基于阶段名称生成活动
            activity_mapping = {
                "基础研究": ["文献调研", "理论建模", "实验验证", "技术评估"],
                "技术开发": ["需求分析", "架构设计", "原型开发", "功能实现"],
                "应用优化": ["性能测试", "用户体验优化", "安全加固", "兼容性测试"],
                "产业化": ["生产准备", "质量控制", "市场推广", "客户支持"],
                "需求分析": ["市场调研", "用户访谈", "竞品分析", "需求文档"],
                "设计阶段": ["概念设计", "详细设计", "原型设计", "评审确认"],
                "开发阶段": ["编码实现", "单元测试", "集成测试", "代码审查"],
                "测试验证": ["系统测试", "性能测试", "安全测试", "用户验收"],
                "产品发布": ["发布准备", "市场宣传", "销售培训", "客户培训"],
            }

            for key, acts in activity_mapping.items():
                if key in phase_name:
                    activities.extend(acts)
                    break

            # 基于目标生成额外活动
            for objective in objectives:
                if "专利" in objective:
                    activities.append("专利申请和布局")
                elif "标准" in objective:
                    activities.append("标准制定和参与")
                elif "合作" in objective:
                    activities.append("合作伙伴开发")

        except Exception as e:
            self.logger.warning(f"活动生成失败: {e}")

        return list(set(activities))  # 去重

    async def _define_phase_deliverables(self, phase_name: str) -> list[str]:
        """定义阶段交付物"""
        deliverables = []

        try:
            deliverable_mapping = {
                "基础研究": ["研究报告", "理论模型", "实验数据", "技术白皮书"],
                "技术开发": ["技术规格", "原型系统", "测试报告", "设计文档"],
                "应用优化": ["优化方案", "性能报告", "用户手册", "测试用例"],
                "产业化": ["产品规格书", "生产流程", "质量标准", "市场材料"],
                "需求分析": ["需求文档", "市场报告", "用户画像", "竞品分析报告"],
                "设计阶段": ["设计文档", "原型设计", "接口规范", "技术方案"],
                "开发阶段": ["源代码", "测试报告", "部署文档", "用户手册"],
                "测试验证": ["测试报告", "缺陷报告", "性能报告", "验收文档"],
                "产品发布": ["发布版本", "用户文档", "营销材料", "培训材料"],
            }

            for key, delivs in deliverable_mapping.items():
                if key in phase_name:
                    deliverables.extend(delivs)
                    break

        except Exception as e:
            self.logger.warning(f"交付物定义失败: {e}")

        return deliverables

    async def _estimate_phase_budget(self, phase_name: str, duration_months: int) -> float:
        """估算阶段预算"""
        try:
            # 基础预算(万元/月)
            base_budget_per_month = {
                "基础研究": 5.0,
                "技术开发": 8.0,
                "应用优化": 6.0,
                "产业化": 10.0,
                "需求分析": 3.0,
                "设计阶段": 4.0,
                "开发阶段": 7.0,
                "测试验证": 5.0,
                "产品发布": 6.0,
            }

            base_budget = base_budget_per_month.get(phase_name, 5.0)
            total_budget = base_budget * duration_months

            # 根据时长调整(有规模效应)
            if duration_months > 12:
                total_budget *= 0.9  # 长期项目有折扣

            return total_budget

        except Exception:
            return 0.0

    async def _estimate_team_requirements(
        self, phase_name: str, objectives: list[str]
    ) -> dict[str, int]:
        """估算团队需求"""
        team_requirements = {}

        try:
            # 基础团队配置
            base_team = {
                "基础研究": {"researcher": 3, "engineer": 2, "analyst": 1},
                "技术开发": {"developer": 5, "architect": 2, "tester": 2},
                "应用优化": {"optimizer": 3, "tester": 2, "ux_designer": 1},
                "产业化": {"manager": 2, "engineer": 3, "marketing": 2},
                "需求分析": {"analyst": 3, "designer": 1, "researcher": 1},
                "设计阶段": {"designer": 3, "architect": 2, "analyst": 1},
                "开发阶段": {"developer": 6, "tester": 3, "tech_lead": 1},
                "测试验证": {"tester": 4, "qa_engineer": 2, "analyst": 1},
                "产品发布": {"manager": 2, "marketing": 3, "support": 2},
            }

            for key, team in base_team.items():
                if key in phase_name:
                    team_requirements = team.copy()
                    break

            # 根据目标调整
            for objective in objectives:
                if "专利" in objective:
                    team_requirements["ip_specialist"] = 1
                elif "标准" in objective:
                    team_requirements["standard_expert"] = 1
                elif "国际" in objective:
                    team_requirements["international_specialist"] = 1

        except Exception as e:
            self.logger.warning(f"团队需求估算失败: {e}")

        return team_requirements

    async def _generate_milestones(
        self,
        development_phases: list[DevelopmentPhase],
        tech_evolution: TechEvolution,
        roadmap_type: RoadmapType,
    ) -> list[RoadmapMilestone]:
        """生成里程碑"""
        milestones = []
        current_date = datetime.now()

        try:
            # 为每个阶段生成里程碑
            for i, phase in enumerate(development_phases):
                # 基于阶段类型生成里程碑
                phase_milestones = await self._generate_phase_milestones(phase, i, current_date)
                milestones.extend(phase_milestones)

                # 更新当前时间
                current_date += timedelta(days=phase.duration_months * 30)

            # 添加全局里程碑
            global_milestones = await self._generate_global_milestones(
                tech_evolution, roadmap_type, development_phases
            )
            milestones.extend(global_milestones)

            # 按时间排序
            milestones.sort(key=lambda m: m.target_date)

        except Exception as e:
            self.logger.warning(f"里程碑生成失败: {e}")

        return milestones

    async def _generate_phase_milestones(
        self, phase: DevelopmentPhase, phase_index: int, start_date: datetime
    ) -> list[RoadmapMilestone]:
        """生成阶段里程碑"""
        phase_milestones = []

        try:
            # 阶段开始里程碑
            start_milestone = RoadmapMilestone(
                milestone_id=f"phase_{phase.phase_id}_start",
                title=f"{phase.phase_name}开始",
                description=f"正式开始{phase.phase_name}阶段的工作",
                milestone_type=(
                    MilestoneType.PRODUCT_LAUNCH
                    if phase_index == 0
                    else MilestoneType.TECHNICAL_BREAKTHROUGH
                ),
                target_date=start_date,
                success_criteria=[f"{phase.phase_name}团队组建完成", "项目计划确认"],
                confidence=0.9,
            )
            phase_milestones.append(start_milestone)

            # 阶段中期里程碑(如果阶段较长)
            if phase.duration_months > 6:
                mid_date = start_date + timedelta(days=phase.duration_months * 15)
                mid_milestone = RoadmapMilestone(
                    milestone_id=f"phase_{phase.phase_id}_mid",
                    title=f"{phase.phase_name}中期评估",
                    description=f"评估{phase.phase_name}阶段进展和调整计划",
                    milestone_type=MilestoneType.MARKET_MILESTONE,
                    target_date=mid_date,
                    success_criteria=["阶段性目标达成", "风险评估完成"],
                    confidence=0.8,
                )
                phase_milestones.append(mid_milestone)

            # 阶段结束里程碑
            end_date = start_date + timedelta(days=phase.duration_months * 30)
            end_milestone = RoadmapMilestone(
                milestone_id=f"phase_{phase.phase_id}_end",
                title=f"{phase.phase_name}完成",
                description=f"成功完成{phase.phase_name}阶段所有目标",
                milestone_type=(
                    MilestoneType.PRODUCT_LAUNCH
                    if phase_index == len(phase_milestones) - 1
                    else MilestoneType.TECHNICAL_BREAKTHROUGH
                ),
                target_date=end_date,
                success_criteria=phase.deliverables,
                risks=["进度延期风险", "质量问题风险"],
                confidence=0.7,
            )
            phase_milestones.append(end_milestone)

        except Exception as e:
            self.logger.warning(f"阶段里程碑生成失败: {e}")

        return phase_milestones

    async def _generate_global_milestones(
        self,
        tech_evolution: TechEvolution,
        roadmap_type: RoadmapType,
        development_phases: list[DevelopmentPhase],
    ) -> list[RoadmapMilestone]:
        """生成全局里程碑"""
        global_milestones = []

        try:
            current_date = datetime.now()

            # 专利申请里程碑
            patent_milestone = RoadmapMilestone(
                milestone_id="patent_filing",
                title="核心专利申请",
                description="提交核心技术专利申请",
                milestone_type=MilestoneType.REGULATORY_APPROVAL,
                target_date=current_date + timedelta(days=180),
                success_criteria=["专利技术交底完成", "专利申请提交"],
                resources_required={"legal_budget": 50.0},
                confidence=0.8,
            )
            global_milestones.append(patent_milestone)

            # 投资里程碑
            investment_milestone = RoadmapMilestone(
                milestone_id="first_round_funding",
                title="首轮融资",
                description="完成第一轮融资",
                milestone_type=MilestoneType.INVESTMENT,
                target_date=current_date + timedelta(days=365),
                success_criteria=["商业计划完成", "投资者意向达成"],
                resources_required={"funding_amount": 1000.0},
                confidence=0.6,
            )
            global_milestones.append(investment_milestone)

        except Exception as e:
            self.logger.warning(f"全局里程碑生成失败: {e}")

        return global_milestones

    async def _analyze_market_opportunities(
        self, focus_technology: str, tech_evolution: TechEvolution
    ) -> list[MarketOpportunity]:
        """分析市场机会"""
        opportunities = []

        try:
            # 基于技术演进趋势生成机会
            for trend in tech_evolution.future_trends[:3]:
                opportunity = MarketOpportunity(
                    opportunity_id=f"market_{hash(trend) % 10000}",
                    market_segment=trend,
                    market_size=1000.0,  # 模拟数据
                    growth_rate=0.15,
                    entry_strategy="技术领先策略",
                    competitive_advantage=f"{trend}技术创新优势",
                    timeline="2-3年",
                    revenue_potential=500.0,
                )
                opportunities.append(opportunity)

        except Exception as e:
            self.logger.warning(f"市场机会分析失败: {e}")

        return opportunities

    async def _gather_competitive_intelligence(
        self, focus_technology: str
    ) -> list[CompetitiveIntelligence]:
        """收集竞争情报"""
        intelligence = []

        try:
            # 模拟竞争情报
            competitors = [
                {
                    "name": "科技公司A",
                    "focus": [focus_technology],
                    "apps/apps/patents": 150,
                    "position": "领导者",
                },  # TODO: 确保除数不为零
                {
                    "name": "创新公司B",
                    "focus": [focus_technology],
                    "apps/apps/patents": 80,
                    "position": "挑战者",
                },  # TODO: 确保除数不为零
                {
                    "name": "传统企业C",
                    "focus": [focus_technology],
                    "apps/apps/patents": 50,
                    "position": "跟随者",
                },  # TODO: 确保除数不为零
            ]

            for i, comp in enumerate(competitors):
                intel = CompetitiveIntelligence(
                    competitor_id=f"competitor_{i+1}",
                    competitor_name=comp["name"],
                    technology_focus=comp["focus"],
                    patent_portfolio=comp["apps/apps/patents"],  # TODO: 确保除数不为零
                    market_position=comp["position"],
                    recent_activities=["技术更新", "专利申请"],
                    threat_level="high" if comp["position"] == "领导者" else "medium",
                )
                intelligence.append(intel)

        except Exception as e:
            self.logger.warning(f"竞争情报收集失败: {e}")

        return intelligence

    async def _assess_risks(
        self,
        focus_technology: str,
        development_phases: list[DevelopmentPhase],
        tech_evolution: TechEvolution,
    ) -> dict[str, Any]:
        """风险评估"""
        risk_assessment = {
            "overall_risk_level": "medium",
            "technical_risks": [],
            "market_risks": [],
            "operational_risks": [],
            "financial_risks": [],
            "mitigation_strategies": [],
        }

        try:
            # 技术风险
            risk_assessment["technical_risks"] = [
                "技术实现难度高",
                "技术演进速度快",
                "依赖关键技术突破",
            ]

            # 市场风险
            risk_assessment["market_risks"] = ["市场需求变化", "竞争加剧", "替代技术威胁"]

            # 运营风险
            risk_assessment["operational_risks"] = ["人才短缺", "项目管理复杂", "供应链不稳定"]

            # 财务风险
            risk_assessment["financial_risks"] = ["研发投入超预算", "融资困难", "现金流风险"]

            # 缓解策略
            risk_assessment["mitigation_strategies"] = [
                "分阶段投资降低风险",
                "建立技术储备",
                "多元化市场策略",
                "加强人才培养",
            ]

        except Exception as e:
            self.logger.warning(f"风险评估失败: {e}")

        return risk_assessment

    async def _define_success_metrics(
        self, roadmap_type: RoadmapType, focus_technology: str
    ) -> list[str]:
        """定义成功指标"""
        metrics = []

        try:
            # 基础指标
            base_metrics = [
                "技术目标达成率 > 90%",
                "项目按时完成率 > 85%",
                "预算控制在计划范围内",
                "团队满意度 > 80%",
            ]
            metrics.extend(base_metrics)

            # 基于路线图类型的指标
            type_metrics = {
                RoadmapType.TECHNOLOGY_EVOLUTION: [
                    "技术专利数量 > 10",
                    "技术创新度评估 > 80%",
                    "技术影响力指数 > 70%",
                ],
                RoadmapType.PRODUCT_DEVELOPMENT: [
                    "产品质量合格率 > 95%",
                    "用户满意度 > 85%",
                    "市场份额目标达成",
                ],
                RoadmapType.MARKET_ENTRY: [
                    "市场进入时间 < 6个月",
                    "初期客户获取 > 100",
                    "品牌知名度提升 > 50%",
                ],
            }

            if roadmap_type in type_metrics:
                metrics.extend(type_metrics[roadmap_type])

        except Exception as e:
            self.logger.warning(f"成功指标定义失败: {e}")

        return metrics

    async def _estimate_investment_requirements(
        self, development_phases: list[DevelopmentPhase], roadmap_type: RoadmapType
    ) -> dict[str, float]:
        """估算投资需求"""
        investment_requirements = {}

        try:
            # 计算总预算
            total_budget = sum(phase.budget_estimate or 0 for phase in development_phases)
            investment_requirements["total_budget"] = total_budget

            # 按年分解
            investment_requirements["year_1"] = total_budget * 0.4
            investment_requirements["year_2"] = total_budget * 0.35
            investment_requirements["year_3"] = total_budget * 0.25

            # 其他投资需求
            investment_requirements["contingency"] = total_budget * 0.2  # 应急资金
            investment_requirements["operating"] = total_budget * 0.3  # 运营资金

        except Exception as e:
            self.logger.warning(f"投资需求估算失败: {e}")

        return investment_requirements

    async def _llm_enhance_roadmap(
        self,
        focus_technology: str,
        patent_data: dict[str, Any],        development_phases: list[DevelopmentPhase],
        milestones: list[RoadmapMilestone],
    ):
        """LLM增强路线图"""
        try:
            # 创建判断上下文
            context = JudgmentContext(
                patent_id=patent_data.get("patent_id", "unknown"),
                technology_field=focus_technology,
                market_context={},
                legal_framework="相关专利法规",
                business_objectives=["技术创新", "商业化"],
                stakeholder_interests=["投资者", "用户", "团队"],
            )

            # 执行LLM判断
            judgment = await self.llm_judgment.judge_patentability(patent_data, context)

            # 基于LLM判断调整路线图
            if judgment.confidence_score > 0.7:
                # 高置信度时可以更积极
                for phase in development_phases:
                    if phase.budget_estimate:
                        phase.budget_estimate *= 1.1  # 增加10%预算

            # 添加LLM建议作为里程碑
            llm_milestone = RoadmapMilestone(
                milestone_id="llm_validation",
                title="专家验证节点",
                description="基于AI专家系统验证的关键节点",
                milestone_type=MilestoneType.TECHNICAL_BREAKTHROUGH,
                target_date=datetime.now() + timedelta(days=90),
                success_criteria=judgment.recommendations[:3],
                confidence=judgment.confidence_score,
            )
            milestones.append(llm_milestone)

        except Exception as e:
            self.logger.warning(f"LLM路线图增强失败: {e}")

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        avg_generation_time = (
            self.stats["generation_time_total"] / self.stats["roadmaps_generated"]
            if self.stats["roadmaps_generated"] > 0
            else 0.0
        )

        return {
            **self.stats,
            "cache_size": len(self.generation_cache),
            "average_generation_time": avg_generation_time,
        }

    async def close(self):
        """关闭路线图生成器"""
        if self.prior_art_analyzer:
            await self.prior_art_analyzer.close()
        if self.llm_judgment:
            await self.llm_judgment.close()

        self.generation_cache.clear()
        self._initialized = False
        self.logger.info("✅ RoadmapGenerator 已关闭")


# 便捷函数
async def get_roadmap_generator() -> RoadmapGenerator:
    """获取路线图生成器实例"""
    generator = RoadmapGenerator()
    await generator.initialize()
    return generator


async def generate_technology_roadmap(
    technology: str, roadmap_type: RoadmapType = RoadmapType.TECHNOLOGY_EVOLUTION, years: int = 3
) -> TechnologyRoadmap:
    """便捷函数:生成技术路线图"""
    generator = await get_roadmap_generator()
    return await generator.generate_roadmap(technology, roadmap_type, years * 12)


if __name__ == "__main__":
    print("技术路线图自动生成系统模块已加载")
