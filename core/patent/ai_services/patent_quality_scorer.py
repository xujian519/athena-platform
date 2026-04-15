from __future__ import annotations
"""
增强版专利质量评分器 - 综合质量评估和风险预警

基于论文#20《Predicting Patent Quality》
- Random Forest: AUC=0.78
- NPE专利坏专利比例55%
- 软件/商业方法专利风险最高

扩展现有quality_assessor.py，添加:
- NPE专利风险预警
- 软件/商业方法专利风险
- 审查历史分析
- 综合质量报告

作者: 小娜·天秤女神
创建时间: 2026-03-20
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class RiskCategory(Enum):
    """风险类别"""
    NPE_RISK = "npe_risk"  # NPE专利风险
    SOFTWARE_PATENT_RISK = "software_patent_risk"  # 软件专利风险
    SCOPE_RISK = "scope_risk"  # 范围风险
    SUPPORT_RISK = "support_risk"  # 支持性风险
    EXAMINATION_RISK = "examination_risk"  # 审查风险


@dataclass
class NPERiskAssessment:
    """NPE风险评估"""
    risk_level: str  # low/medium/high
    risk_score: float  # 0-1
    claim_risk_indicators: list[str] = field(default_factory=list)
    technology_risk_factors: list[str] = field(default_factory=list)
    mitigation_suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "claim_risk_indicators": self.claim_risk_indicators,
            "technology_risk_factors": self.technology_risk_factors,
            "mitigation_suggestions": self.mitigation_suggestions,
        }


@dataclass
class SoftwarePatentRiskAssessment:
    """软件专利风险评估"""
    is_software_patent: bool
    risk_level: str
    risk_score: float
    technical_feature_score: float  # 技术特征评分
    abstract_idea_risk: float  # 抽象概念风险
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_software_patent": self.is_software_patent,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "technical_feature_score": self.technical_feature_score,
            "abstract_idea_risk": self.abstract_idea_risk,
            "suggestions": self.suggestions,
        }


@dataclass
class ComprehensiveQualityReport:
    """综合质量报告"""

    # 基础信息
    patent_no: str
    assessment_scope: str  # full/quick/claims_only

    # 综合评分
    overall_score: float  # 0-100
    quality_level: str  # 优秀/良好/中等/较差/差

    # 基础六维评估
    base_quality: dict = field(default_factory=dict)

    # 风险评估
    npe_risk: NPERiskAssessment | None = None
    software_risk: SoftwarePatentRiskAssessment | None = None
    examination_analysis: dict | None = None

    # 综合建议
    recommendations: list[str] = field(default_factory=list)
    priority_actions: list[dict] = field(default_factory=list)

    # 元数据
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "patent_no": self.patent_no,
            "overall_score": self.overall_score,
            "quality_level": self.quality_level,
            "base_quality": self.base_quality,
            "npe_risk": self.npe_risk.to_dict() if self.npe_risk else None,
            "software_risk": self.software_risk.to_dict() if self.software_risk else None,
            "examination_analysis": self.examination_analysis,
            "recommendations": self.recommendations,
            "priority_actions": self.priority_actions,
            "processing_time_ms": self.processing_time_ms,
        }


class NPERiskDetector:
    """
    NPE专利风险检测器

    基于论文#20: NPE专利中55%是"坏专利"

    高风险特征:
    - 宽泛的权利要求
    - 模糊的技术特征
    - 软件/商业方法相关
    - 高引用密度但低质量
    """

    # NPE高风险关键词
    NPE_INDICATORS = [
        "计算机实现的方法",
        "系统",
        "计算机程序产品",
        "存储介质",
        "网络",
        "数据处理",
        "一种方法",
        "一种系统",
    ]

    # NPE专利常见问题模式
    NPE_CLAIM_PATTERNS = [
        "一种...方法，包括:",
        "一种...系统，包括:",
        "一种计算机程序产品",
        "一种存储介质",
    ]

    def __init__(self):
        self.name = "NPE风险检测器"
        self.logger = logging.getLogger(self.name)

    async def detect(
        self,
        claims: list[str],
        assignee_type: str = "unknown",
    ) -> NPERiskAssessment:
        """
        检测NPE专利风险

        Args:
            claims: 权利要求列表
            assignee_type: 权利人类型

        Returns:
            NPERiskAssessment: 风险评估结果
        """
        # 1. 检查权利要求特征
        claim_risk = self._analyze_claim_risk(claims)

        # 2. 检查技术领域
        tech_risk = self._analyze_technology_risk(claims)

        # 3. 综合评估
        overall_risk = self._calculate_npe_risk(
            claim_risk,
            tech_risk,
            assignee_type,
        )

        # 4. 生成缓解建议
        suggestions = self._generate_mitigation_suggestions(
            claim_risk,
            tech_risk,
        )

        return NPERiskAssessment(
            risk_level=overall_risk["level"],
            risk_score=overall_risk["score"],
            claim_risk_indicators=claim_risk["indicators"],
            technology_risk_factors=tech_risk["factors"],
            mitigation_suggestions=suggestions,
        )

    def _analyze_claim_risk(self, claims: list[str]) -> dict:
        """分析权利要求风险"""
        indicators = []
        risk_score = 0.0

        claim_text = " ".join(claims).lower()

        for pattern in self.NPE_CLAIM_PATTERNS:
            if pattern in claim_text:
                indicators.append(f"发现NPE典型模式: {pattern[:20]}...")
                risk_score += 0.15

        # 检查权利要求宽度
        for claim in claims:
            if self._is_broad_claim(claim):
                indicators.append("权利要求可能过于宽泛")
                risk_score += 0.10
                break

        # 检查技术特征
        if self._has_vague_technical_features(claim_text):
            indicators.append("技术特征描述模糊")
            risk_score += 0.10

        return {
            "indicators": indicators[:5],
            "score": min(1.0, risk_score),
        }

    def _analyze_technology_risk(self, claims: list[str]) -> dict:
        """分析技术领域风险"""
        factors = []
        risk_score = 0.0

        claim_text = " ".join(claims).lower()

        # 软件相关
        software_keywords = ["计算机", "程序", "软件", "算法", "数据处理"]
        if any(kw in claim_text for kw in software_keywords):
            factors.append("涉及软件技术")
            risk_score += 0.20

        # 商业方法
        business_keywords = ["商业", "交易", "支付", "管理方法"]
        if any(kw in claim_text for kw in business_keywords):
            factors.append("涉及商业方法")
            risk_score += 0.25

        # 通信/网络
        network_keywords = ["网络", "通信", "传输", "协议"]
        if any(kw in claim_text for kw in network_keywords):
            factors.append("涉及网络通信")
            risk_score += 0.15

        return {
            "factors": factors,
            "score": min(1.0, risk_score),
        }

    def _calculate_npe_risk(
        self,
        claim_risk: dict,
        tech_risk: dict,
        assignee_type: str,
    ) -> dict:
        """计算综合NPE风险"""
        base_score = (claim_risk["score"] + tech_risk["score"]) / 2

        # NPE权利人加权
        if assignee_type.lower() in ["npe", "non-practicing", "patent_troll"]:
            base_score = min(1.0, base_score * 1.5)

        if base_score >= 0.7:
            level = "high"
        elif base_score >= 0.4:
            level = "medium"
        else:
            level = "low"

        return {"level": level, "score": base_score}

    def _is_broad_claim(self, claim: str) -> bool:
        """判断权利要求是否过宽"""
        # 简单规则: 长度短且限定词少
        words = claim.split()
        qualifiers = ["其中", "所述", "包括", "特别是"]

        if len(words) < 50:
            qualifier_count = sum(1 for q in qualifiers if q in claim)
            if qualifier_count < 2:
                return True
        return False

    def _has_vague_technical_features(self, text: str) -> bool:
        """判断技术特征是否模糊"""
        vague_terms = ["适当的", "合适的", "等等", "例如", "如", "等"]
        return any(term in text for term in vague_terms)

    def _generate_mitigation_suggestions(
        self,
        claim_risk: dict,
        tech_risk: dict,
    ) -> list[str]:
        """生成缓解建议"""
        suggestions = []

        if claim_risk["score"] > 0.3:
            suggestions.append("增加具体技术特征限定")
            suggestions.append("避免使用模糊的概括性语言")

        if tech_risk["score"] > 0.3:
            suggestions.append("强调技术实现的具体细节")
            suggestions.append("说明技术效果和技术进步")

        if not suggestions:
            suggestions.append("保持当前权利要求的清晰度和完整性")

        return suggestions[:5]


class SoftwarePatentRiskAnalyzer:
    """
    软件专利风险分析器

    基于论文#20: 软件专利无效风险45%

    分析要点:
    - 技术特征是否充分
    - 是否落入抽象概念
    - 是否有技术效果
    """

    # 抽象概念关键词
    ABSTRACT_IDEA_PATTERNS = [
        "收集数据",
        "分析数据",
        "显示结果",
        "存储信息",
        "计算",
        "比较",
    ]

    # 技术三要素
    TECHNICAL_ELEMENTS = {
        "technical_problem": ["技术问题", "解决的技术问题"],
        "technical_solution": ["技术方案", "技术特征", "技术手段"],
        "technical_effect": ["技术效果", "有益效果", "技术进步"],
    }

    def __init__(self):
        self.name = "软件专利风险分析器"
        self.logger = logging.getLogger(self.name)

    async def analyze(
        self,
        claims: list[str],
        cpc_code: str = "",
    ) -> SoftwarePatentRiskAssessment:
        """
        分析软件专利风险

        Args:
            claims: 权利要求列表
            cpc_code: CPC分类代码

        Returns:
            SoftwarePatentRiskAssessment: 风险评估结果
        """
        claim_text = " ".join(claims)

        # 1. 判断是否软件专利
        is_software = self._is_software_patent(claim_text, cpc_code)

        if not is_software:
            return SoftwarePatentRiskAssessment(
                is_software_patent=False,
                risk_level="low",
                risk_score=0.0,
                technical_feature_score=10.0,
                abstract_idea_risk=0.0,
                suggestions=["非软件专利，按常规专利评估"],
            )

        # 2. 评估技术特征
        tech_score = self._evaluate_technical_features(claim_text)

        # 3. 评估抽象概念风险
        abstract_risk = self._evaluate_abstract_idea_risk(claim_text)

        # 4. 计算综合风险
        overall_risk = self._calculate_software_risk(tech_score, abstract_risk)

        # 5. 生成建议
        suggestions = self._generate_software_suggestions(tech_score, abstract_risk)

        return SoftwarePatentRiskAssessment(
            is_software_patent=True,
            risk_level=overall_risk["level"],
            risk_score=overall_risk["score"],
            technical_feature_score=tech_score,
            abstract_idea_risk=abstract_risk,
            suggestions=suggestions,
        )

    def _is_software_patent(self, claim_text: str, cpc_code: str) -> bool:
        """判断是否软件专利"""
        # CPC分类判断
        software_cpc = ["G06F", "G06Q", "G06N"]
        if any(cpc_code.startswith(code) for code in software_cpc):
            return True

        # 关键词判断
        software_keywords = [
            "计算机", "程序", "软件", "算法", "代码",
            "处理器", "存储器", "指令", "模块",
        ]
        claim_lower = claim_text.lower()
        return any(kw in claim_lower for kw in software_keywords)

    def _evaluate_technical_features(self, claim_text: str) -> float:
        """评估技术特征充分性 (0-10)"""
        score = 5.0  # 基础分

        # 检查技术三要素
        for _element, keywords in self.TECHNICAL_ELEMENTS.items():
            if any(kw in claim_text for kw in keywords):
                score += 1.0

        # 检查具体技术实现
        implementation_keywords = [
            "电路", "架构", "协议", "接口", "硬件",
            "寄存器", "总线", "中断",
        ]
        if any(kw in claim_text for kw in implementation_keywords):
            score += 1.5

        # 检查数据处理流程
        if "步骤" in claim_text or "流程" in claim_text:
            score += 0.5

        return min(10.0, score)

    def _evaluate_abstract_idea_risk(self, claim_text: str) -> float:
        """评估抽象概念风险 (0-1)"""
        risk = 0.0

        for pattern in self.ABSTRACT_IDEA_PATTERNS:
            if pattern in claim_text:
                risk += 0.1

        # 检查是否只是商业方法泛化
        if "商业" in claim_text and "计算机" in claim_text:
            if "具体" not in claim_text and "特定" not in claim_text:
                risk += 0.2

        return min(1.0, risk)

    def _calculate_software_risk(self, tech_score: float, abstract_risk: float) -> dict:
        """计算综合软件专利风险"""
        # 技术特征越充分，风险越低
        tech_factor = (10.0 - tech_score) / 10.0

        overall_risk = tech_factor * 0.5 + abstract_risk * 0.5

        if overall_risk >= 0.7:
            level = "high"
        elif overall_risk >= 0.4:
            level = "medium"
        else:
            level = "low"

        return {"level": level, "score": overall_risk}

    def _generate_software_suggestions(self, tech_score: float, abstract_risk: float) -> list[str]:
        """生成软件专利改进建议"""
        suggestions = []

        if tech_score < 7.0:
            suggestions.append("增加具体的技术实现细节")
            suggestions.append("明确说明技术方案如何解决技术问题")

        if abstract_risk > 0.3:
            suggestions.append("避免仅描述通用的数据处理步骤")
            suggestions.append("强调技术方案的创新性和非显而易见性")

        if tech_score >= 7.0 and abstract_risk <= 0.3:
            suggestions.append("技术特征描述充分，保持当前质量")

        return suggestions[:4]


class EnhancedPatentQualityScorer:
    """
    增强版专利质量评分器

    扩展现有quality_assessor.py，添加:
    - NPE专利风险预警 (论文#20: 55%坏专利)
    - 软件/商业方法专利风险 (论文#20: 45%无效风险)
    - 审查历史分析
    - 综合质量报告

    评分体系:
    - 基础六维评分 (60%)
    - NPE风险评分 (20%)
    - 软件专利风险 (10%)
    - 审查历史评分 (10%)
    """

    # 质量等级定义
    QUALITY_LEVELS = {
        "优秀": (85, 100),
        "良好": (70, 85),
        "中等": (55, 70),
        "较差": (40, 55),
        "差": (0, 40),
    }

    def __init__(
        self,
        base_assessor=None,
        llm_manager=None,
    ):
        """
        初始化增强版质量评分器

        Args:
            base_assessor: 基础评估器 (ClaimQualityAssessor)
            llm_manager: LLM管理器
        """
        self.name = "增强版专利质量评分器"
        self.version = "1.0.0"
        self.logger = logging.getLogger(self.name)

        # 核心组件
        self._base_assessor = base_assessor
        self._llm_manager = llm_manager

        # 风险检测器
        self._npe_detector = NPERiskDetector()
        self._software_analyzer = SoftwarePatentRiskAnalyzer()

        # 统计
        self.stats = {
            "total_assessments": 0,
            "avg_score": 0.0,
            "risk_distribution": {"high": 0, "medium": 0, "low": 0},
        }

    @property
    def base_assessor(self):
        """延迟加载基础评估器"""
        if self._base_assessor is None:
            try:
                from core.patent.quality_assessor import ClaimQualityAssessor
                self._base_assessor = ClaimQualityAssessor()
            except ImportError:
                self.logger.warning("基础评估器未找到，使用简化模式")
        return self._base_assessor

    @property
    def llm_manager(self):
        """延迟加载LLM管理器"""
        if self._llm_manager is None:
            try:
                from core.llm.unified_llm_manager import get_unified_llm_manager
                self._llm_manager = get_unified_llm_manager()
            except ImportError:
                pass
        return self._llm_manager

    async def comprehensive_quality_assessment(
        self,
        patent_data: dict,
        assessment_scope: str = "full",
    ) -> ComprehensiveQualityReport:
        """
        全面质量评估

        Args:
            patent_data: 专利数据
                - patent_no: 专利号
                - claims: 权利要求列表
                - description: 说明书
                - prior_art: 现有技术
                - cpc_code: CPC分类代码
                - examination_history: 审查历史 (可选)
                - assignee_type: 权利人类型 (可选)
            assessment_scope: 评估范围 (full/quick/claims_only)

        Returns:
            ComprehensiveQualityReport: 综合质量报告
        """
        start_time = datetime.now()
        self.stats["total_assessments"] += 1

        patent_no = patent_data.get("patent_no", "unknown")
        claims = patent_data.get("claims", [])

        try:
            # 1. 基础六维评估 (复用现有)
            base_quality = await self._assess_base_quality(patent_data, assessment_scope)

            # 2. NPE风险检测
            npe_risk = None
            if assessment_scope in ["full", "quick"]:
                npe_risk = await self._npe_detector.detect(
                    claims,
                    patent_data.get("assignee_type", "unknown"),
                )

            # 3. 软件/商业方法专利风险
            software_risk = None
            if assessment_scope in ["full", "quick"]:
                software_risk = await self._software_analyzer.analyze(
                    claims,
                    patent_data.get("cpc_code", ""),
                )

            # 4. 审查历史分析
            exam_analysis = None
            if assessment_scope == "full" and "examination_history" in patent_data:
                exam_analysis = self._analyze_examination_history(
                    patent_data["examination_history"]
                )

            # 5. 综合评分计算
            overall_score = self._calculate_overall_score(
                base_quality,
                npe_risk,
                software_risk,
                exam_analysis,
            )

            # 6. 确定质量等级
            quality_level = self._determine_quality_level(overall_score)

            # 7. 生成建议
            recommendations = self._generate_recommendations(
                base_quality,
                npe_risk,
                software_risk,
                exam_analysis,
            )

            # 8. 确定优先行动
            priority_actions = self._determine_priority_actions(
                base_quality,
                npe_risk,
                software_risk,
            )

            # 更新统计
            self._update_stats(overall_score, npe_risk, software_risk)

            return ComprehensiveQualityReport(
                patent_no=patent_no,
                assessment_scope=assessment_scope,
                overall_score=overall_score,
                quality_level=quality_level,
                base_quality=base_quality,
                npe_risk=npe_risk,
                software_risk=software_risk,
                examination_analysis=exam_analysis,
                recommendations=recommendations,
                priority_actions=priority_actions,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

        except Exception as e:
            self.logger.error(f"质量评估失败: {e}")
            return ComprehensiveQualityReport(
                patent_no=patent_no,
                assessment_scope=assessment_scope,
                overall_score=0.0,
                quality_level="差",
                recommendations=[f"评估失败: {str(e)}"],
            )

    async def _assess_base_quality(self, patent_data: dict, scope: str) -> dict:
        """基础六维质量评估"""
        if self.base_assessor is None:
            return self._simplified_base_assessment(patent_data)

        try:
            assessment = self.base_assessor.assess(
                claim_text="\n".join(patent_data.get("claims", [])),
                description=patent_data.get("description", ""),
                prior_art=patent_data.get("prior_art"),
                cpc_code=patent_data.get("cpc_code"),
            )

            return {
                "overall_score": assessment.overall_score * 10,  # 转换为百分制
                "quality_level": assessment.quality_level,
                "dimension_scores": {
                    dim.value: score.score
                    for dim, score in assessment.dimension_scores.items()
                },
                "critical_issues": [
                    {"dimension": issue.dimension.value, "description": issue.description}
                    for issue in assessment.critical_issues[:5]
                ],
            }
        except Exception as e:
            self.logger.error(f"基础评估失败: {e}")
            return self._simplified_base_assessment(patent_data)

    def _simplified_base_assessment(self, patent_data: dict) -> dict:
        """简化基础评估 (降级方案)"""
        claims = patent_data.get("claims", [])

        # 简单规则评分
        score = 50.0

        # 权利要求数量
        if len(claims) >= 10:
            score += 10
        elif len(claims) >= 5:
            score += 5

        # 平均长度
        avg_length = sum(len(c) for c in claims) / len(claims) if claims else 0
        if avg_length >= 200:
            score += 10
        elif avg_length >= 100:
            score += 5

        return {
            "overall_score": min(100, score),
            "quality_level": "中等",
            "dimension_scores": {},
            "critical_issues": [],
        }

    def _analyze_examination_history(self, history: dict) -> dict:
        """分析审查历史"""
        analysis = {
            "office_actions": history.get("office_actions", 0),
            "rejections": history.get("rejections", 0),
            "amendments": history.get("claim_amendments", 0),
            "prosecution_days": history.get("prosecution_days", 0),
            "risk_factors": [],
            "positive_factors": [],
        }

        # 风险因素
        if analysis["office_actions"] > 3:
            analysis["risk_factors"].append("审查意见次数较多")

        if analysis["rejections"] > 1:
            analysis["risk_factors"].append("多次被驳回")

        if analysis["prosecution_days"] > 1825:  # 5年
            analysis["risk_factors"].append("审查周期过长")

        # 积极因素
        if analysis["amendments"] > 0 and analysis["rejections"] == 0:
            analysis["positive_factors"].append("主动修改，无驳回")

        return analysis

    def _calculate_overall_score(
        self,
        base_quality: dict,
        npe_risk: NPERiskAssessment | None,
        software_risk: SoftwarePatentRiskAssessment | None,
        exam_analysis: dict | None,
    ) -> float:
        """计算综合评分 (0-100)"""
        # 基础评分 (60%)
        base_score = base_quality.get("overall_score", 50) * 0.6

        # NPE风险扣分 (最多扣20分)
        npe_deduction = 0
        if npe_risk:
            if npe_risk.risk_level == "high":
                npe_deduction = 20
            elif npe_risk.risk_level == "medium":
                npe_deduction = 10

        # 软件专利风险扣分 (最多扣10分)
        software_deduction = 0
        if software_risk and software_risk.is_software_patent:
            if software_risk.risk_level == "high":
                software_deduction = 10
            elif software_risk.risk_level == "medium":
                software_deduction = 5

        # 审查历史扣分 (最多扣10分)
        exam_deduction = 0
        if exam_analysis:
            risk_count = len(exam_analysis.get("risk_factors", []))
            exam_deduction = min(10, risk_count * 3)

        overall = base_score - npe_deduction - software_deduction - exam_deduction
        return max(0, min(100, overall))

    def _determine_quality_level(self, score: float) -> str:
        """确定质量等级"""
        for level, (low, high) in self.QUALITY_LEVELS.items():
            if low <= score < high:
                return level
        return "差"

    def _generate_recommendations(
        self,
        base_quality: dict,
        npe_risk: NPERiskAssessment | None,
        software_risk: SoftwarePatentRiskAssessment | None,
        exam_analysis: dict | None,
    ) -> list[str]:
        """生成综合建议"""
        recommendations = []

        # 基于基础评估的建议
        for issue in base_quality.get("critical_issues", [])[:3]:
            recommendations.append(f"[{issue['dimension']}] {issue['description']}")

        # NPE风险建议
        if npe_risk and npe_risk.risk_level in ["medium", "high"]:
            recommendations.extend(npe_risk.mitigation_suggestions[:2])

        # 软件专利建议
        if software_risk and software_risk.is_software_patent:
            recommendations.extend(software_risk.suggestions[:2])

        # 审查历史建议
        if exam_analysis and exam_analysis.get("risk_factors"):
            recommendations.append("关注审查历史中的问题点，确保已完全解决")

        return recommendations[:10]

    def _determine_priority_actions(
        self,
        base_quality: dict,
        npe_risk: NPERiskAssessment | None,
        software_risk: SoftwarePatentRiskAssessment | None,
    ) -> list[dict]:
        """确定优先行动"""
        actions = []

        # 高风险NPE
        if npe_risk and npe_risk.risk_level == "high":
            actions.append({
                "priority": "P0",
                "action": "降低NPE专利风险",
                "details": "增加具体技术特征，避免宽泛的权利要求",
            })

        # 高风险软件专利
        if software_risk and software_risk.risk_level == "high":
            actions.append({
                "priority": "P0",
                "action": "增强软件专利技术特征",
                "details": "确保技术方案有具体的技术实现细节",
            })

        # 基础质量问题
        critical_issues = base_quality.get("critical_issues", [])
        if critical_issues:
            actions.append({
                "priority": "P1",
                "action": "解决关键质量问题",
                "details": critical_issues[0]["description"] if critical_issues else "",
            })

        return actions[:5]

    def _update_stats(
        self,
        score: float,
        npe_risk: NPERiskAssessment | None,
        software_risk: SoftwarePatentRiskAssessment | None,
    ):
        """更新统计信息"""
        n = self.stats["total_assessments"]
        old_avg = self.stats["avg_score"]
        self.stats["avg_score"] = old_avg + (score - old_avg) / n

        # 风险分布
        overall_risk = "low"
        if npe_risk and npe_risk.risk_level == "high":
            overall_risk = "high"
        elif software_risk and software_risk.risk_level == "high":
            overall_risk = "high"
        elif (npe_risk and npe_risk.risk_level == "medium") or \
             (software_risk and software_risk.risk_level == "medium"):
            overall_risk = "medium"

        self.stats["risk_distribution"][overall_risk] += 1

    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.stats


# 便捷函数
def get_enhanced_quality_scorer() -> EnhancedPatentQualityScorer:
    """获取增强版质量评分器实例"""
    return EnhancedPatentQualityScorer()
