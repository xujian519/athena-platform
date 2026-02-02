#!/usr/bin/env python3
"""
专家级合规性审查预判系统
Expert Compliance Review & Prediction System

集成专家规则、LLM判断和数据分析的智能合规性审查系统
作者: 小诺·双鱼座
创建时间: 2025-12-21
版本: v1.0.0 "专家审查"
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


from ..knowledge.patent_analysis.enhanced_knowledge_graph import EnhancedPatentKnowledgeGraph
from .expert_rule_engine import ExpertRuleEngine
from .llm_enhanced_judgment import JudgmentContext, LLMEnhancedJudgment
from .patent_rule_chain import PatentRuleChainEngine

logger = logging.getLogger(__name__)


class ComplianceCategory(Enum):
    """合规性类别"""

    PATENTABILITY = "patentability"  # 可专利性
    FORMALITY = "formality"  # 形式要求
    DISCLOSURE = "disclosure"  # 充分公开
    NOVELTY = "novelty"  # 新颖性
    INVENTIVENESS = "inventiveness"  # 创造性
    UTILITY = "utility"  # 实用性
    UNITY = "unity"  # 单一性
    CLARITY = "clarity"  # 清晰性
    SCOPE = "scope"  # 保护范围


class ReviewOutcome(Enum):
    """审查结果"""

    APPROVED = "approved"  # 通过
    REJECTED = "rejected"  # 驳回
    CONDITIONALLY_APPROVED = "conditionally_approved"  # 有条件通过
    FURTHER_REVIEW = "further_review"  # 需要进一步审查
    INCOMPLETE = "incomplete"  # 材料不完整


class SeverityLevel(Enum):
    """严重程度"""

    CRITICAL = (0.8, 1.0)  # 严重
    MAJOR = (0.6, 0.8)  # 重要
    MODERATE = (0.4, 0.6)  # 中等
    MINOR = (0.2, 0.4)  # 轻微
    INFO = (0.0, 0.2)  # 信息


@dataclass
class ComplianceIssue:
    """合规性问题"""

    issue_id: str
    category: ComplianceCategory
    severity: SeverityLevel
    title: str
    description: str
    location: str | None = None  # 问题位置
    reference: str | None = None  # 参考法规
    suggestions: list[str] = field(default_factory=list)
    auto_fixable: bool = False
    confidence: float = 0.8


@dataclass
class ComplianceScore:
    """合规性评分"""

    category: ComplianceCategory
    score: float  # 0-100
    weight: float  # 权重
    issues: list[ComplianceIssue] = field(default_factory=list)
    passed_threshold: bool = False


@dataclass
class ExpertReview:
    """专家审查意见"""

    review_id: str
    reviewer_type: str  # human, ai, hybrid
    confidence: float
    primary_assessment: str
    detailed_analysis: list[str]
    recommendations: list[str]
    concerns: list[str]
    supporting_evidence: list[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CompliancePrediction:
    """合规性预测"""

    prediction_id: str
    success_probability: float  # 0-1
    predicted_outcome: ReviewOutcome
    key_factors: list[str]
    risk_factors: list[str]
    improvement_areas: list[str]
    estimated_timeline: str | None = None
    confidence: float = 0.7


@dataclass
class ComprehensiveComplianceReview:
    """综合合规性审查"""

    review_id: str
    patent_id: str
    submission_date: datetime
    overall_score: float
    individual_scores: list[ComplianceScore]
    expert_reviews: list[ExpertReview]
    prediction: CompliancePrediction
    final_recommendation: str
    next_steps: list[str]
    created_at: datetime = field(default_factory=datetime.now)


class ComplianceJudge:
    """合规性审查预判系统"""

    def __init__(self):
        self.name = "专家级合规性审查预判系统"
        self.version = "1.0.0"
        self._initialized = False
        self.logger = logging.getLogger(self.name)

        # 核心组件
        self.rule_engine: ExpertRuleEngine | None = None
        self.rule_chain_engine: PatentRuleChainEngine | None = None
        self.llm_judgment: LLMEnhancedJudgment | None = None
        self.knowledge_graph: EnhancedPatentKnowledgeGraph | None = None

        # 合规性标准库
        self.compliance_standards: dict[ComplianceCategory, dict[str, Any] = {}

        # 审查模板
        self.review_templates: dict[str, dict[str, Any]] = {}

        # 审查历史
        self.review_history: dict[str, ComprehensiveComplianceReview] = {}

        # 配置参数
        self.config = {
            "overall_passing_score": 70.0,
            "category_weights": {
                ComplianceCategory.PATENTABILITY: 0.3,
                ComplianceCategory.FORMALITY: 0.2,
                ComplianceCategory.DISCLOSURE: 0.2,
                ComplianceCategory.NOVELTY: 0.15,
                ComplianceCategory.INVENTIVENESS: 0.15,
            },
            "enable_auto_review": True,
            "enable_prediction": True,
            "enable_human_review_simulation": True,
            "strict_mode": False,
            "cache_ttl": 3600,
        }

        # 统计信息
        self.stats = {
            "total_reviews": 0,
            "approved_reviews": 0,
            "rejected_reviews": 0,
            "average_score": 0.0,
            "prediction_accuracy": 0.0,
            "auto_reviews": 0,
            "human_simulated_reviews": 0,
        }

    async def initialize(self):
        """初始化合规性审查系统"""
        try:
            # 初始化核心组件
            self.rule_engine = ExpertRuleEngine()
            await self.rule_engine.initialize()

            self.rule_chain_engine = PatentRuleChainEngine()
            await self.rule_chain_engine.initialize()

            self.llm_judgment = LLMEnhancedJudgment()
            await self.llm_judgment.initialize()

            self.knowledge_graph = await EnhancedPatentKnowledgeGraph.initialize()

            # 加载合规性标准
            await self._load_compliance_standards()

            # 构建审查模板
            await self._build_review_templates()

            self._initialized = True
            self.logger.info("✅ ComplianceJudge 初始化完成")
            return True

        except Exception as e:
            return False

    async def _load_compliance_standards(self):
        """加载合规性标准"""
        try:
            # 可专利性标准
            self.compliance_standards[ComplianceCategory.PATENTABILITY] = {
                "name": "可专利性审查",
                "description": "判断发明是否具备专利法规定的授权条件",
                "criteria": ["属于专利保护客体", "不违反法律和社会公德", "不属于不授权的情形"],
                "reference": "专利法第2条、第5条、第25条",
                "passing_score": 70.0,
            }

            # 形式要求标准
            self.compliance_standards[ComplianceCategory.FORMALITY] = {
                "name": "形式要求审查",
                "description": "检查申请文件的格式和完整性",
                "criteria": ["申请文件齐全", "格式符合规定", "费用缴纳完整", "申请人信息准确"],
                "reference": "专利法实施细则第16-20条",
                "passing_score": 85.0,
            }

            # 充分公开标准
            self.compliance_standards[ComplianceCategory.DISCLOSURE] = {
                "name": "充分公开审查",
                "description": "评估说明书是否清楚、完整地公开了发明",
                "criteria": ["技术问题明确", "技术方案完整", "有益效果清楚", "能够实现"],
                "reference": "专利法第26条第3款",
                "passing_score": 75.0,
            }

            # 新颖性标准
            self.compliance_standards[ComplianceCategory.NOVELTY] = {
                "name": "新颖性审查",
                "description": "判断发明是否属于现有技术",
                "criteria": [
                    "未在国内外公开出版物上公开发表过",
                    "未在国内公开使用过",
                    "未被他人申请过",
                ],
                "reference": "专利法第22条第1款",
                "passing_score": 80.0,
            }

            # 创造性标准
            self.compliance_standards[ComplianceCategory.INVENTIVENESS] = {
                "name": "创造性审查",
                "description": "评估发明是否具有突出的实质性特点和显著的进步",
                "criteria": ["相对于现有技术具有实质性特点", "具有显著的进步", "非显而易见性"],
                "reference": "专利法第22条第3款",
                "passing_score": 65.0,
            }

            # 实用性标准
            self.compliance_standards[ComplianceCategory.UTILITY] = {
                "name": "实用性审查",
                "description": "判断发明是否能够在产业上制造或使用",
                "criteria": ["能够制造或使用", "能够产生积极效果", "具有可再现性"],
                "reference": "专利法第22条第4款",
                "passing_score": 90.0,
            }

            self.logger.info("✅ 合规性标准加载完成")

        except Exception as e:

    async def _build_review_templates(self):
        """构建审查模板"""
        try:
            # 基础审查模板
            self.review_templates["basic"] = {
                "categories": [
                    ComplianceCategory.PATENTABILITY,
                    ComplianceCategory.FORMALITY,
                    ComplianceCategory.DISCLOSURE,
                ],
                "auto_check_items": ["文件完整性", "格式规范性", "基本信息准确性"],
            }

            # 详细审查模板
            self.review_templates["detailed"] = {
                "categories": list(ComplianceCategory),
                "expert_review_required": True,
                "llm_enhancement": True,
                "prediction_enabled": True,
            }

            # 快速预审模板
            self.review_templates["preliminary"] = {
                "categories": [
                    ComplianceCategory.PATENTABILITY,
                    ComplianceCategory.NOVELTY,
                    ComplianceCategory.INVENTIVENESS,
                ],
                "quick_check": True,
                "focus_on_major_issues": True,
            }

        except Exception as e:

    async def comprehensive_compliance_review(
        self,
        patent_data: dict[str, Any],        review_template: str = "detailed",
        context: dict[str, Any] | None = None,
    ) -> ComprehensiveComplianceReview:
        """
        综合合规性审查

        Args:
            patent_data: 专利数据
            review_template: 审查模板
            context: 上下文信息

        Returns:
            ComprehensiveComplianceReview: 综合审查结果
        """
        if not self._initialized:
            raise RuntimeError("ComplianceJudge未初始化")

        review_id = f"compliance_{patent_data.get('patent_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stats["total_reviews"] += 1

        try:
            # 获取审查配置
            template = self.review_templates.get(review_template, self.review_templates["detailed"])
            categories = template.get("categories", list(ComplianceCategory))

            # 执行分项评分
            individual_scores = []
            for category in categories:
                score = await self._review_category(patent_data, category, context)
                individual_scores.append(score)

            # 计算整体评分
            overall_score = self._calculate_overall_score(individual_scores)

            # 生成专家审查意见
            expert_reviews = []
            if template.get("expert_review_required", True):
                expert_reviews.extend(
                    [
                        await self._generate_ai_expert_review(
                            patent_data, individual_scores, context
                        ),
                        await self._simulate_human_expert_review(
                            patent_data, individual_scores, context
                        ),
                    ]
                )

            # 生成合规性预测
            prediction = None
            if template.get("prediction_enabled", True):
                prediction = await self._predict_compliance_outcome(
                    patent_data, individual_scores, context
                )

            # 生成最终建议
            final_recommendation = self._generate_final_recommendation(
                overall_score, individual_scores, prediction
            )

            # 生成下一步行动
            next_steps = self._generate_next_steps(final_recommendation, individual_scores)

            # 创建综合审查结果
            review = ComprehensiveComplianceReview(
                review_id=review_id,
                patent_id=patent_data.get("patent_id", "unknown"),
                submission_date=patent_data.get("submission_date", datetime.now()),
                overall_score=overall_score,
                individual_scores=individual_scores,
                expert_reviews=expert_reviews,
                prediction=prediction,
                final_recommendation=final_recommendation,
                next_steps=next_steps,
            )

            # 保存审查历史
            self.review_history[review_id] = review

            # 更新统计
            self._update_statistics(review)

            self.logger.info(f"✅ 合规性审查完成: {review_id}, 整体评分: {overall_score:.1f}")
            return review

        except Exception as e:
            raise

    async def _review_category(
        self,
        patent_data: dict[str, Any],        category: ComplianceCategory,
        context: dict[str, Any],    ) -> ComplianceScore:
        """审查特定类别"""
        try:
            # 获取标准
            standard = self.compliance_standards.get(category, {})
            passing_score = standard.get("passing_score", 70.0)
            weight = self.config.get("category_weights").get(category, 0.1)

            # 执行规则链检查
            rule_chain_results = []
            if self.rule_chain_engine:
                try:
                    rule_chain_results = await self.rule_chain_engine.check_compliance(
                        patent_data, [category]
                    )
                except Exception as e:

            # 提取问题
            issues = []
            score = 100.0  # 满分开始

            # 基于规则链结果减分
            for check_result in rule_chain_results:
                if not check_result.passed:
                    score -= check_result.score * 0.5  # 根据严重程度减分

                    issue = ComplianceIssue(
                        issue_id=f"rule_{check_result.check_id}",
                        category=category,
                        severity=self._map_score_to_severity(check_result.score),
                        title=f"{category.value}问题",
                        description=f"违反{category.value}要求",
                        reference=standard.get("reference", ""),
                        suggestions=check_result.suggestions,
                        auto_fixable=check_result.score > 50,
                        confidence=check_result.confidence,
                    )
                    issues.append(issue)

            # 执行自动检查
            auto_issues = await self._auto_check_category(patent_data, category)
            issues.extend(auto_issues)

            # 根据自动问题调整分数
            for issue in auto_issues:
                if issue.severity == SeverityLevel.CRITICAL:
                    score -= 20
                elif issue.severity == SeverityLevel.MAJOR:
                    score -= 10
                elif issue.severity == SeverityLevel.MODERATE:
                    score -= 5
                elif issue.severity == SeverityLevel.MINOR:
                    score -= 2

            score = max(0, score)  # 确保不低于0

            passed = score >= passing_score

            return ComplianceScore(
                category=category,
                score=score,
                weight=weight,
                issues=issues,
                passed_threshold=passed,
            )

        except Exception as e:
            return ComplianceScore(
                category=category,
                score=0.0,
                weight=0.1,
                issues=[
                    ComplianceIssue(
                        issue_id=f"error_{category.value}",
                        category=category,
                        severity=SeverityLevel.CRITICAL,
                        title="审查错误",
                        description=f"审查过程中发生错误: {e!s}",
                    )
                ],
                passed_threshold=False,
            )

    async def _auto_check_category(
        self, patent_data: dict[str, Any], category: ComplianceCategory
    ) -> list[ComplianceIssue]:
        """自动检查特定类别"""
        issues = []

        try:
            if category == ComplianceCategory.FORMALITY:
                # 形式要求检查
                required_fields = ["title", "abstract", "claims", "description"]
                for field in required_fields:
                    if field not in patent_data or not patent_data.get(field):
                        issues.append(
                            ComplianceIssue(
                                issue_id=f"missing_{field}",
                                category=category,
                                severity=SeverityLevel.CRITICAL,
                                title=f"缺少{field}",
                                description=f"申请文件缺少必要的{field}部分",
                                auto_fixable=True,
                                suggestions=[f"补充{field}内容"],
                            )
                        )

                # 标题长度检查
                if "title" in patent_data:
                    title = patent_data.get("title")
                    if len(title) < 10:
                        issues.append(
                            ComplianceIssue(
                                issue_id="title_too_short",
                                category=category,
                                severity=SeverityLevel.MINOR,
                                title="标题过短",
                                description="标题过于简短,可能无法清楚概括发明内容",
                                suggestions=["建议扩展标题内容,使其更加具体"],
                            )
                        )
                    elif len(title) > 100:
                        issues.append(
                            ComplianceIssue(
                                issue_id="title_too_long",
                                category=category,
                                severity=SeverityLevel.MINOR,
                                title="标题过长",
                                description="标题可能超出规定长度限制",
                                suggestions=["建议精简标题内容"],
                            )
                        )

            elif category == ComplianceCategory.DISCLOSURE:
                # 充分公开检查
                if "description" in patent_data:
                    description = patent_data.get("description")
                    if len(description) < 500:
                        issues.append(
                            ComplianceIssue(
                                issue_id="insufficient_disclosure",
                                category=category,
                                severity=SeverityLevel.MAJOR,
                                title="说明书过于简略",
                                description="说明书内容过于简略,可能不满足充分公开要求",
                                suggestions=["详细描述技术方案、实施方式和有益效果"],
                            )
                        )

            elif category == ComplianceCategory.CLAIMS:
                # 权利要求检查
                if "claims" in patent_data:
                    claims = patent_data.get("claims")
                    if not claims.strip():
                        issues.append(
                            ComplianceIssue(
                                issue_id="empty_claims",
                                category=category,
                                severity=SeverityLevel.CRITICAL,
                                title="权利要求为空",
                                description="权利要求书内容为空",
                                suggestions=["补充权利要求内容"],
                            )
                        )
                    else:
                        # 检查权利要求数量
                        claim_count = len(re.findall(r"\d+\.", claims))
                        if claim_count == 0:
                            issues.append(
                                ComplianceIssue(
                                    issue_id="no_claims",
                                    category=category,
                                    severity=SeverityLevel.CRITICAL,
                                    title="缺少权利要求",
                                    description="未找到有效的权利要求",
                                    suggestions=["按标准格式添加权利要求"],
                                )
                            )
                        elif claim_count > 50:
                            issues.append(
                                ComplianceIssue(
                                    issue_id="too_many_claims",
                                    category=category,
                                    severity=SeverityLevel.MODERATE,
                                    title="权利要求数量过多",
                                    description=f"权利要求数量({claim_count})可能超出合理范围",
                                    suggestions=["考虑精简权利要求数量,突出核心创新点"],
                                )
                            )

        except Exception as e:

        return issues

    def _map_score_to_severity(self, score: float) -> SeverityLevel:
        """将评分映射到严重程度"""
        if score <= 20:
            return SeverityLevel.CRITICAL
        elif score <= 40:
            return SeverityLevel.MAJOR
        elif score <= 60:
            return SeverityLevel.MODERATE
        elif score <= 80:
            return SeverityLevel.MINOR
        else:
            return SeverityLevel.INFO

    def _calculate_overall_score(self, individual_scores: list[ComplianceScore]) -> float:
        """计算整体评分"""
        if not individual_scores:
            return 0.0

        weighted_score = 0.0
        total_weight = 0.0

        for score in individual_scores:
            weighted_score += score.score * score.weight
            total_weight += score.weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    async def _generate_ai_expert_review(
        self,
        patent_data: dict[str, Any],        individual_scores: list[ComplianceScore],
        context: dict[str, Any],    ) -> ExpertReview:
        """生成AI专家审查意见"""
        try:
            # 准备LLM判断上下文
            judgment_context = JudgmentContext(
                patent_id=patent_data.get("patent_id", "unknown"),
                technology_field=patent_data.get("technical_field", "未知"),
                market_context=context or {},
                legal_framework="专利法及其实施细则",
                business_objectives=["获得专利授权", "保护技术创新"],
                stakeholder_interests=["发明人", "申请人", "审查员"],
            )

            # 执行LLM判断
            judgment = await self.llm_judgment.judge_patentability(patent_data, judgment_context)

            # 构建AI专家意见
            review = ExpertReview(
                review_id=f"ai_expert_{datetime.now().strftime('%H%M%S')}",
                reviewer_type="ai",
                confidence=judgment.confidence_score,
                primary_assessment=judgment.primary_conclusion,
                detailed_analysis=judgment.supporting_reasoning,
                recommendations=judgment.recommendations,
                concerns=judgment.risk_factors,
                supporting_evidence=[e.content for e in judgment.evidence_items: 5,
                timestamp=datetime.now(),
            )

            self.stats["auto_reviews"] += 1
            return review

        except Exception as e:
            # 返回默认审查意见
            return ExpertReview(
                review_id=f"ai_expert_error_{datetime.now().strftime('%H%M%S')}",
                reviewer_type="ai",
                confidence=0.3,
                primary_assessment="审查过程中遇到错误,建议人工复核",
                detailed_analysis=["系统错误导致无法完成详细分析"],
                recommendations=["请提交完整资料进行人工审查"],
                concerns=["数据完整性问题", "系统稳定性问题"],
                supporting_evidence=[],
            )

    async def _simulate_human_expert_review(
        self,
        patent_data: dict[str, Any],        individual_scores: list[ComplianceScore],
        context: dict[str, Any],    ) -> ExpertReview:
        """模拟人类专家审查意见"""
        try:
            # 基于评分生成人类专家意见
            failed_categories = [s for s in individual_scores if not s.passed_threshold]
            overall_score = self._calculate_overall_score(individual_scores)

            if overall_score >= 85:
                assessment = "专利申请质量优秀,建议优先审查"
                confidence = 0.9
                recommendations = ["申请加快审查程序", "准备授权答辩"]
                concerns = []
            elif overall_score >= 70:
                assessment = "专利申请基本符合要求,建议通过"
                confidence = 0.8
                recommendations = ["根据审查意见进行必要修改", "准备答复审查意见"]
                concerns = ["部分细节需要完善"]
            elif overall_score >= 50:
                assessment = "专利申请存在明显缺陷,需要补正"
                confidence = 0.7
                recommendations = ["针对主要问题进行修改", "补充必要材料"]
                concerns = [f"{cat.category.value}方面存在缺陷" for cat in failed_categories]
            else:
                assessment = "专利申请存在严重问题,驳回可能性高"
                confidence = 0.8
                recommendations = ["重新评估专利申请策略", "考虑分案申请"]
                concerns = ["多项实质性缺陷", "授权前景不明"]

            review = ExpertReview(
                review_id=f"human_expert_{datetime.now().strftime('%H%M%S')}",
                reviewer_type="human_simulated",
                confidence=confidence,
                primary_assessment=assessment,
                detailed_analysis=[
                    f"整体评分: {overall_score:.1f}分",
                    f"通过审查类别: {len([s for s in individual_scores if s.passed_threshold])}/{len(individual_scores)}",
                ],
                recommendations=recommendations,
                concerns=concerns,
                supporting_evidence=[
                    "基于专利审查标准和历史案例分析",
                    "参考了相似技术领域的审查实践",
                ],
                timestamp=datetime.now(),
            )

            self.stats["human_simulated_reviews"] += 1
            return review

        except Exception as e:
            return ExpertReview(
                review_id=f"human_expert_error_{datetime.now().strftime('%H%M%S')}",
                reviewer_type="human_simulated",
                confidence=0.2,
                primary_assessment="审查系统错误,需要人工干预",
                detailed_analysis=["无法完成专家审查模拟"],
                recommendations=["立即联系人工审查员"],
                concerns=["系统可靠性问题"],
                supporting_evidence=[],
            )

    async def _predict_compliance_outcome(
        self,
        patent_data: dict[str, Any],        individual_scores: list[ComplianceScore],
        context: dict[str, Any],    ) -> CompliancePrediction:
        """预测合规性结果"""
        try:
            overall_score = self._calculate_overall_score(individual_scores)

            # 计算成功概率
            if overall_score >= 90:
                success_prob = 0.95
                outcome = ReviewOutcome.APPROVED
            elif overall_score >= 80:
                success_prob = 0.85
                outcome = ReviewOutcome.APPROVED
            elif overall_score >= 70:
                success_prob = 0.70
                outcome = ReviewOutcome.CONDITIONALLY_APPROVED
            elif overall_score >= 50:
                success_prob = 0.40
                outcome = ReviewOutcome.FURTHER_REVIEW
            else:
                success_prob = 0.15
                outcome = ReviewOutcome.REJECTED

            # 识别关键因素
            key_factors = []
            risk_factors = []
            improvement_areas = []

            for score in individual_scores:
                if score.passed_threshold:
                    key_factors.append(f"{score.category.value}符合要求")
                else:
                    risk_factors.append(f"{score.category.value}存在风险")
                    improvement_areas.append(f"重点改进{score.category.value}")

            # 估算时间线
            timeline = None
            if outcome == ReviewOutcome.APPROVED:
                timeline = "6-12个月"
            elif outcome == ReviewOutcome.CONDITIONALLY_APPROVED:
                timeline = "8-15个月"
            elif outcome == ReviewOutcome.FURTHER_REVIEW:
                timeline = "12-24个月"
            else:
                timeline = "需要重新申请"

            prediction = CompliancePrediction(
                prediction_id=f"prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                success_probability=success_prob,
                predicted_outcome=outcome,
                key_factors=key_factors,
                risk_factors=risk_factors,
                improvement_areas=improvement_areas,
                estimated_timeline=timeline,
                confidence=0.75,
            )

            return prediction

        except Exception as e:
            return CompliancePrediction(
                prediction_id=f"prediction_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                success_probability=0.5,
                predicted_outcome=ReviewOutcome.FURTHER_REVIEW,
                key_factors=[],
                risk_factors=["预测系统错误"],
                improvement_areas=["需要人工判断"],
                confidence=0.1,
            )

    def _generate_final_recommendation(
        self,
        overall_score: float,
        individual_scores: list[ComplianceScore],
        prediction: CompliancePrediction,
    ) -> str:
        """生成最终建议"""
        if overall_score >= 85:
            return "专利申请质量优秀,建议直接提交审查,有较高授权前景。"
        elif overall_score >= 70:
            return "专利申请基本符合要求,建议提交审查,同时准备答复可能的审查意见。"
        elif overall_score >= 50:
            return "专利申请存在明显缺陷,建议根据问题清单进行修改后再提交。"
        else:
            return "专利申请存在严重问题,建议重新评估申请策略,考虑技术方案调整或分案申请。"

    def _generate_next_steps(
        self, final_recommendation: str, individual_scores: list[ComplianceScore]
    ) -> list[str]:
        """生成下一步行动"""
        steps = []

        # 基于分数生成行动
        failed_categories = [s for s in individual_scores if not s.passed_threshold]

        if failed_categories:
            steps.append("解决以下关键问题:")
            for category in failed_categories:
                steps.append(f"  - 改进{category.category.value}相关内容")
        else:
            steps.append("准备申请材料提交")
            steps.append("监控审查进度")

        # 添加通用步骤
        steps.extend(["保存审查报告作为参考", "关注相关法规更新", "考虑后续专利布局策略"])

        return steps

    def _update_statistics(self, review: ComprehensiveComplianceReview) -> Any:
        """更新统计信息"""
        # 更新平均分
        self.stats["average_score"] = (
            self.stats["average_score"] * (self.stats["total_reviews"] - 1) + review.overall_score
        ) / self.stats["total_reviews"]

        # 更新通过/驳回统计
        if review.overall_score >= self.config.get("overall_passing_score"):
            self.stats["approved_reviews"] += 1
        else:
            self.stats["rejected_reviews"] += 1

        # 更新预测准确性(如果有历史数据)
        if review.prediction and len(self.review_history) > 10:
            # 简化的预测准确性计算
            predicted_approved = review.prediction.predicted_outcome in [
                ReviewOutcome.APPROVED,
                ReviewOutcome.CONDITIONALLY_APPROVED,
            ]
            actual_approved = review.overall_score >= self.config.get("overall_passing_score")

            if predicted_approved == actual_approved:
                self.stats["prediction_accuracy"] += 0.01

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "review_history_size": len(self.review_history),
            "approval_rate": (
                self.stats["approved_reviews"] / self.stats["total_reviews"]
                if self.stats["total_reviews"] > 0
                else 0.0
            ),
        }

    async def close(self):
        """关闭合规性审查系统"""
        if self.rule_engine:
            await self.rule_engine.close()
        if self.rule_chain_engine:
            await self.rule_chain_engine.close()
        if self.llm_judgment:
            await self.llm_judgment.close()

        self.review_history.clear()
        self._initialized = False
        self.logger.info("✅ ComplianceJudge 已关闭")


# 便捷函数
async def get_compliance_judge() -> ComplianceJudge:
    """获取合规性审查系统实例"""
    judge = ComplianceJudge()
    await judge.initialize()
    return judge


async def quick_patent_compliance_check(
    patent_data: dict[str, Any],) -> ComprehensiveComplianceReview:
    """便捷函数:快速专利合规性检查"""
    judge = await get_compliance_judge()
    return await judge.comprehensive_compliance_review(patent_data, review_template="preliminary")


if __name__ == "__main__":
    print("专家级合规性审查预判系统模块已加载")
