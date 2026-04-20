#!/usr/bin/env python3
"""
专利分析与评估系统 (CAP02)
Patent Analysis and Evaluation System

提供完整的专利分析评估功能：
1. 新颖性分析 (Novelty Analysis)
2. 创造性评估 (Inventive Step Assessment)
3. 实用性评估 (Utility Assessment)
4. 权利要求分析 (Claims Analysis)
5. 综合评估报告 (Comprehensive Report)

Author: Athena平台团队
Created: 2026-04-20
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AssessmentLevel(Enum):
    """评估等级"""
    EXCELLENT = "优秀"  # 90-100分
    GOOD = "良好"      # 75-89分
    MEDIUM = "中等"    # 60-74分
    LOW = "较低"       # 45-59分
    VERY_LOW = "很低"  # <45分


@dataclass
class TechnicalFeature:
    """技术特征"""
    name: str
    description: str
    category: str  # 技术类别
    keywords: List[str] = field(default_factory=list)


@dataclass
class NoveltyAnalysisResult:
    """新颖性分析结果"""
    patent_id: str
    novelty_score: float  # 0-100
    novelty_level: AssessmentLevel
    prior_art_found: bool
    similar_patents: List[Dict[str, Any]] = field(default_factory=list)
    novel_features: List[str] = field(default_factory=list)
    analysis_details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class CreativityAssessmentResult:
    """创造性评估结果"""
    patent_id: str
    creativity_score: float  # 0-100
    creativity_level: AssessmentLevel
    technical_contribution: str
    innovation_type: List[str] = field(default_factory=list)
    unexpected_effects: List[str] = field(default_factory=list)
    analysis_details: Dict[str, Any] = field(default_factory=dict)
    improvement_suggestions: List[str] = field(default_factory=list)


@dataclass
class UtilityAssessmentResult:
    """实用性评估结果"""
    patent_id: str
    utility_score: float  # 0-100
    utility_level: AssessmentLevel
    industrial_applicability: bool
    implementation_feasibility: str
    commercial_potential: str
    analysis_details: Dict[str, Any] = field(default_factory=dict)
    application_suggestions: List[str] = field(default_factory=list)


@dataclass
class ClaimsAnalysisResult:
    """权利要求分析结果"""
    patent_id: str
    claims_count: int
    clarity_score: float  # 0-100
    coverage_score: float  # 0-100
    breadth_assessment: str
    independent_claims: List[Dict[str, Any]] = field(default_factory=list)
    dependent_claims: List[Dict[str, Any]] = field(default_factory=list)
    analysis_details: Dict[str, Any] = field(default_factory=dict)
    drafting_suggestions: List[str] = field(default_factory=list)


@dataclass
class ComprehensiveEvaluationReport:
    """综合评估报告"""
    patent_id: str
    title: str
    evaluation_date: str

    # 四大评估结果
    novelty: NoveltyAnalysisResult
    creativity: CreativityAssessmentResult
    utility: UtilityAssessmentResult
    claims: ClaimsAnalysisResult

    # 综合评分
    overall_score: float
    overall_level: AssessmentLevel
    patentability_recommendation: str  # 可专利性建议

    # 关键发现
    key_strengths: List[str]
    key_weaknesses: List[str]
    risk_factors: List[str]

    # 行动建议
    recommended_actions: List[str]


class PatentEvaluationSystem:
    """专利分析与评估系统"""

    def __init__(self):
        """初始化评估系统"""
        self.patent_retriever = None
        logger.info("✅ 专利评估系统初始化成功")

    async def evaluate_patent(
        self,
        patent_id: str,
        title: str,
        abstract: str,
        claims: List[str],
        description: Optional[str] = None,
        applicant: Optional[str] = None,
        inventor: Optional[str] = None,
        ipc_codes: Optional[str] = None
    ) -> ComprehensiveEvaluationReport:
        """
        综合评估专利

        Args:
            patent_id: 专利号
            title: 专利标题
            abstract: 摘要
            claims: 权利要求列表
            description: 说明书
            applicant: 申请人
            inventor: 发明人
            ipc_codes: IPC分类号

        Returns:
            综合评估报告
        """
        logger.info(f"🔬 开始综合评估专利: {patent_id}")

        # 并行执行四大评估
        novelty_task = self._analyze_novelty(
            patent_id, title, abstract, claims, description
        )
        creativity_task = self._assess_creativity(
            patent_id, title, abstract, claims, description
        )
        utility_task = self._assess_utility(
            patent_id, title, abstract, claims, description, applicant
        )
        claims_task = self._analyze_claims(
            patent_id, title, claims
        )

        # 并发执行
        novelty, creativity, utility, claims_analysis = await asyncio.gather(
            novelty_task,
            creativity_task,
            utility_task,
            claims_task,
            return_exceptions=True
        )

        # 处理异常
        if isinstance(novelty, Exception):
            logger.error(f"新颖性分析失败: {novelty}")
            novelty = self._get_default_novelty_result(patent_id, title)

        if isinstance(creativity, Exception):
            logger.error(f"创造性评估失败: {creativity}")
            creativity = self._get_default_creativity_result(patent_id, title)

        if isinstance(utility, Exception):
            logger.error(f"实用性评估失败: {utility}")
            utility = self._get_default_utility_result(patent_id, title)

        if isinstance(claims_analysis, Exception):
            logger.error(f"权利要求分析失败: {claims_analysis}")
            claims_analysis = self._get_default_claims_result(patent_id, title, claims)

        # 计算综合评分
        overall_score = self._calculate_overall_score(
            novelty.novelty_score,
            creativity.creativity_score,
            utility.utility_score,
            claims_analysis.clarity_score
        )

        overall_level = self._get_assessment_level(overall_score)

        # 生成可专利性建议
        patentability_recommendation = self._generate_patentability_recommendation(
            overall_score, novelty, creativity, utility, claims_analysis
        )

        # 识别关键优势和劣势
        key_strengths, key_weaknesses, risk_factors = self._identify_key_factors(
            novelty, creativity, utility, claims_analysis
        )

        # 生成行动建议
        recommended_actions = self._generate_recommendations(
            novelty, creativity, utility, claims_analysis
        )

        # 构建综合报告
        report = ComprehensiveEvaluationReport(
            patent_id=patent_id,
            title=title,
            evaluation_date=datetime.now().strftime("%Y-%m-%d"),
            novelty=novelty,
            creativity=creativity,
            utility=utility,
            claims=claims_analysis,
            overall_score=overall_score,
            overall_level=overall_level,
            patentability_recommendation=patentability_recommendation,
            key_strengths=key_strengths,
            key_weaknesses=key_weaknesses,
            risk_factors=risk_factors,
            recommended_actions=recommended_actions
        )

        logger.info(f"✅ 综合评估完成: {patent_id} - 总分: {overall_score:.2f}")

        return report

    async def _analyze_novelty(
        self,
        patent_id: str,
        title: str,
        abstract: str,
        claims: List[str],
        description: Optional[str]
    ) -> NoveltyAnalysisResult:
        """新颖性分析"""
        logger.info(f"🔍 执行新颖性分析: {patent_id}")

        # 构建查询文本
        query_text = f"{title} {abstract}"
        if claims:
            query_text += " " + " ".join(claims[:3])  # 使用前3条权利要求

        # 执行检索
        similar_patents = []
        try:
            # 使用本地数据库检索
            from advanced_patent_search import AdvancedPatentRetriever, SearchFilter

            retriever = AdvancedPatentRetriever()
            results = await retriever.search(query_text, top_k=10)

            for result in results:
                similar_patents.append({
                    "patent_id": result.patent_id,
                    "title": result.title,
                    "similarity": result.score,
                    "abstract": result.abstract[:200] if result.abstract else ""
                })

            retriever.close()

        except Exception as e:
            logger.warning(f"⚠️ 检索现有技术失败: {e}")

        # 分析新颖性特征
        novel_features = self._extract_novel_features(title, abstract, claims)

        # 计算新颖性评分
        novelty_score = self._calculate_novelty_score(
            similar_patents, novel_features, abstract
        )

        novelty_level = self._get_assessment_level(novelty_score)

        return NoveltyAnalysisResult(
            patent_id=patent_id,
            novelty_score=novelty_score,
            novelty_level=novelty_level,
            similar_patents=similar_patents,
            novel_features=novel_features,
            prior_art_found=len(similar_patents) > 0,
            analysis_details={
                "similar_count": len(similar_patents),
                "novel_feature_count": len(novel_features)
            },
            recommendations=self._generate_novelty_recommendations(novelty_score, similar_patents)
        )

    async def _assess_creativity(
        self,
        patent_id: str,
        title: str,
        abstract: str,
        claims: List[str],
        description: Optional[str]
    ) -> CreativityAssessmentResult:
        """创造性评估"""
        logger.info(f"💡 执行创造性评估: {patent_id}")

        # 提取技术特征
        technical_features = self._extract_technical_features(title, abstract, claims)

        # 识别创新类型
        innovation_types = self._identify_innovation_types(title, abstract, claims)

        # 识别预料不到的技术效果
        unexpected_effects = self._identify_unexpected_effects(abstract, claims)

        # 计算创造性评分
        creativity_score = self._calculate_creativity_score(
            technical_features, innovation_types, unexpected_effects, abstract
        )

        creativity_level = self._get_assessment_level(creativity_score)

        # 确定技术贡献度
        technical_contribution = self._determine_technical_contribution(creativity_score, innovation_types)

        return CreativityAssessmentResult(
            patent_id=patent_id,
            creativity_score=creativity_score,
            creativity_level=creativity_level,
            technical_contribution=technical_contribution,
            innovation_type=innovation_types,
            unexpected_effects=unexpected_effects,
            analysis_details={
                "feature_count": len(technical_features),
                "innovation_types": innovation_types
            },
            improvement_suggestions=self._generate_creativity_improvements(creativity_score)
        )

    async def _assess_utility(
        self,
        patent_id: str,
        title: str,
        abstract: str,
        claims: List[str],
        description: Optional[str],
        applicant: Optional[str]
    ) -> UtilityAssessmentResult:
        """实用性评估"""
        logger.info(f"⚙️ 执行实用性评估: {patent_id}")

        # 评估工业实用性
        industrial_applicability = self._assess_industrial_applicability(title, abstract, claims)

        # 评估实施可行性
        implementation_feasibility = self._assess_implementation_feasibility(title, abstract, claims)

        # 评估商业潜力
        commercial_potential = self._assess_commercial_potential(title, abstract, applicant)

        # 计算实用性评分
        utility_score = self._calculate_utility_score(
            industrial_applicability, implementation_feasibility, commercial_potential
        )

        utility_level = self._get_assessment_level(utility_score)

        return UtilityAssessmentResult(
            patent_id=patent_id,
            utility_score=utility_score,
            utility_level=utility_level,
            industrial_applicability=industrial_applicability,
            implementation_feasibility=implementation_feasibility,
            commercial_potential=commercial_potential,
            analysis_details={
                "industrial": industrial_applicability,
                "feasibility": implementation_feasibility,
                "commercial": commercial_potential
            },
            application_suggestions=self._generate_utility_suggestions(utility_score)
        )

    async def _analyze_claims(
        self,
        patent_id: str,
        title: str,
        claims: List[str]
    ) -> ClaimsAnalysisResult:
        """权利要求分析"""
        logger.info(f"⚖️ 执行权利要求分析: {patent_id}")

        # 解析权利要求结构
        independent_claims = []
        dependent_claims = []

        for i, claim in enumerate(claims):
            # 识别独立权利要求（通常以"1.一种"开头）
            if re.match(r'^1\.', claim):
                independent_claims.append({
                    "claim_number": i + 1,
                    "text": claim,
                    "type": "independent",
                    "scope": self._analyze_claim_scope(claim)
                })
            else:
                dependent_claims.append({
                    "claim_number": i + 1,
                    "text": claim,
                    "type": "dependent",
                    "scope": self._analyze_claim_scope(claim)
                })

        claims_count = len(claims)

        # 评估清晰度
        clarity_score = self._assess_claims_clarity(claims)

        # 评估保护范围
        coverage_score, breadth_assessment = self._assess_claims_coverage(claims)

        return ClaimsAnalysisResult(
            patent_id=patent_id,
            claims_count=claims_count,
            clarity_score=clarity_score,
            coverage_score=coverage_score,
            breadth_assessment=breadth_assessment,
            independent_claims=independent_claims,
            dependent_claims=dependent_claims,
            analysis_details={
                "independent_count": len(independent_claims),
                "dependent_count": len(dependent_claims)
            },
            drafting_suggestions=self._generate_claims_suggestions(
                clarity_score, coverage_score, breadth_assessment
            )
        )

    # ==================== 辅助方法 ====================

    def _extract_novel_features(self, title: str, abstract: str, claims: List[str]) -> List[str]:
        """提取新颖性特征"""
        novel_features = []

        # 关键词提取
        text = f"{title} {abstract}"
        keywords = re.findall(r'([^，。；：]+)(?:方法|系统|装置|设备|模块)', text)
        novel_features.extend(keywords[:5])

        # 技术术语
        tech_terms = re.findall(r'([A-Z][a-z]+(?:神经网络|算法|模型|技术))', abstract)
        novel_features.extend(tech_terms[:3])

        return list(set(novel_features))

    def _calculate_novelty_score(self, similar_patents: List, novel_features: List, abstract: str) -> float:
        """计算新颖性评分"""
        score = 100.0

        # 根据相似专利数量扣分
        if len(similar_patents) > 0:
            score -= min(len(similar_patents) * 10, 50)

        # 根据新颖特征数量加分
        score += min(len(novel_features) * 3, 20)

        # 根据摘要长度和复杂度调整
        if len(abstract) > 200:
            score += 5

        return max(0, min(100, score))

    def _extract_technical_features(self, title: str, abstract: str, claims: List[str]) -> List[TechnicalFeature]:
        """提取技术特征"""
        features = []

        # 从标题提取
        title_features = re.findall(r'([^，。]+)(?:方法|系统|装置)', title)
        for feature in title_features:
            features.append(TechnicalFeature(
                name=feature.strip(),
                description=f"标题提及: {feature}",
                category="primary"
            ))

        # 从摘要提取
        abstract_features = re.findall(r'(?:采用|使用|基于|应用)([^，。]+)', abstract)
        for feature in abstract_features[:5]:
            features.append(TechnicalFeature(
                name=feature.strip(),
                description=f"摘要提及: {feature}",
                category="secondary"
            ))

        return features

    def _identify_innovation_types(self, title: str, abstract: str, claims: List[str]) -> List[str]:
        """识别创新类型"""
        innovation_types = []

        full_text = f"{title} {abstract}"

        if re.search(r'新|创新|首次|首创', full_text):
            innovation_types.append("原始创新")

        if re.search(r'改进|优化|增强|提升', full_text):
            innovation_types.append("改进型创新")

        if re.search(r'组合|集成|融合|混合', full_text):
            innovation_types.append("组合创新")

        if re.search(r'应用|用于|适配', full_text):
            innovation_types.append("应用创新")

        if not innovation_types:
            innovation_types.append("常规技术")

        return innovation_types

    def _identify_unexpected_effects(self, abstract: str, claims: List[str]) -> List[str]:
        """识别预料不到的技术效果"""
        effects = []

        full_text = f"{abstract} {' '.join(claims)}"

        # 查找效果描述
        effect_patterns = [
            r'(?:提高|提升|增强|改善)([^，。]+)',
            r'(?:实现|达到)([^，。]+)(?:效果|目标)',
            r'(?:显著|大幅|明显)([^，。]+)'
        ]

        for pattern in effect_patterns:
            matches = re.findall(pattern, full_text)
            effects.extend(matches[:3])

        return list(set(effects))

    def _calculate_creativity_score(self, features: List, innovation_types: List,
                                   unexpected_effects: List, abstract: str) -> float:
        """计算创造性评分"""
        score = 50.0  # 基础分

        # 根据技术特征数量
        score += min(len(features) * 5, 20)

        # 根据创新类型
        if "原始创新" in innovation_types:
            score += 20
        elif "组合创新" in innovation_types:
            score += 15
        elif "改进型创新" in innovation_types:
            score += 10

        # 根据预料不到的效果
        score += min(len(unexpected_effects) * 5, 15)

        return max(0, min(100, score))

    def _determine_technical_contribution(self, score: float, innovation_types: List[str]) -> str:
        """确定技术贡献度"""
        if score >= 80:
            return "重大技术贡献"
        elif score >= 60:
            return "显著技术进步"
        elif score >= 40:
            return "一般性改进"
        else:
            return "微小改进"

    def _assess_industrial_applicability(self, title: str, abstract: str, claims: List[str]) -> bool:
        """评估工业实用性"""
        # 检查是否包含具体的实施方式
        full_text = f"{title} {abstract} {' '.join(claims)}"

        # 包含具体实施方式的指标
        has_implementation = (
            re.search(r'包括|包含|设有|配置', full_text) and
            re.search(r'模块|单元|部件|装置', full_text)
        )

        # 技术术语的丰富度
        tech_terms = len(re.findall(r'[A-Z][a-z]+(?:算法|模型|系统)', full_text))

        return has_implementation or tech_terms >= 3

    def _assess_implementation_feasibility(self, title: str, abstract: str, claims: List[str]) -> str:
        """评估实施可行性"""
        full_text = f"{title} {abstract} {' '.join(claims)}"

        # 检查技术复杂度
        complex_indicators = ['算法', '模型', '系统', '多']
        complexity = sum(1 for ind in complex_indicators if ind in full_text)

        if complexity >= 3:
            return "高复杂度，需要专业团队"
        elif complexity >= 1:
            return "中等复杂度，可实现"
        else:
            return "低复杂度，易于实现"

    def _assess_commercial_potential(self, title: str, abstract: str, applicant: Optional[str]) -> str:
        """评估商业潜力"""
        # 热门技术领域
        hot_fields = [
            '人工智能', '机器学习', '深度学习', '大数据',
            '区块链', '云计算', '物联网', '自动驾驶',
            '新能源', '生物技术'
        ]

        text = f"{title} {abstract}"
        hot_field_hits = sum(1 for field in hot_fields if field in text)

        if hot_field_hits >= 2:
            return "高商业潜力"
        elif hot_field_hits >= 1:
            return "中等商业潜力"
        else:
            return "商业潜力待评估"

    def _calculate_utility_score(self, industrial: bool, feasibility: str, commercial: str) -> float:
        """计算实用性评分"""
        score = 50.0

        if industrial:
            score += 20

        if "易于实现" in feasibility:
            score += 15
        elif "可实现" in feasibility:
            score += 10

        if "高商业潜力" in commercial:
            score += 15
        elif "中等商业潜力" in commercial:
            score += 10

        return max(0, min(100, score))

    def _analyze_claim_scope(self, claim: str) -> str:
        """分析权利要求范围"""
        # 简单的宽度分析
        if re.search(r'所述.*?其特征在于', claim):
            return "中等范围"
        elif re.search(r'包括.*?(?:等|、)', claim):
            return "较宽范围"
        else:
            return "标准范围"

    def _assess_claims_clarity(self, claims: List[str]) -> float:
        """评估权利要求清晰度"""
        if not claims:
            return 0.0

        score = 70.0

        # 检查权利要求结构
        has_numbering = any(re.match(r'^\d+\.', claim) for claim in claims)
        if has_numbering:
            score += 15

        # 检查是否有"其特征在于"等表述
        has_characterization = any("其特征在于" in claim for claim in claims)
        if has_characterization:
            score += 10

        # 检查是否有具体技术参数
        has_params = any(re.search(r'\d+', claim) for claim in claims)
        if has_params:
            score += 5

        return max(0, min(100, score))

    def _assess_claims_coverage(self, claims: List[str]) -> tuple:
        """评估权利要求保护范围"""
        coverage_score = 70.0

        # 检查独立权利要求数量
        independent_count = sum(1 for claim in claims if re.match(r'^1\.', claim))

        if independent_count >= 2:
            coverage_score += 15
        elif independent_count == 1:
            coverage_score += 10

        # 检查从属权利要求
        dependent_count = len(claims) - independent_count
        if dependent_count >= 3:
            coverage_score += 10
        elif dependent_count >= 1:
            coverage_score + 5

        coverage_score = max(0, min(100, coverage_score))

        # 宽度评估
        if coverage_score >= 85:
            breadth = "较宽保护范围"
        elif coverage_score >= 60:
            breadth = "适中保护范围"
        else:
            breadth = "较窄保护范围"

        return coverage_score, breadth

    def _calculate_overall_score(self, novelty: float, creativity: float,
                               utility: float, claims: float) -> float:
        """计算综合评分"""
        # 权重分配
        weights = {
            "novelty": 0.30,
            "creativity": 0.35,
            "utility": 0.25,
            "claims": 0.10
        }

        overall_score = (
            novelty * weights["novelty"] +
            creativity * weights["creativity"] +
            utility * weights["utility"] +
            claims * weights["claims"]
        )

        return round(overall_score, 2)

    def _get_assessment_level(self, score: float) -> AssessmentLevel:
        """获取评估等级"""
        if score >= 90:
            return AssessmentLevel.EXCELLENT
        elif score >= 75:
            return AssessmentLevel.GOOD
        elif score >= 60:
            return AssessmentLevel.MEDIUM
        elif score >= 45:
            return AssessmentLevel.LOW
        else:
            return AssessmentLevel.VERY_LOW

    def _generate_patentability_recommendation(self, overall_score: float,
                                                  novelty: NoveltyAnalysisResult,
                                                  creativity: CreativityAssessmentResult,
                                                  utility: UtilityAssessmentResult,
                                                  claims: ClaimsAnalysisResult) -> str:
        """生成可专利性建议"""
        if overall_score >= 75:
            return "建议申请专利，具有较好的专利性"
        elif overall_score >= 60:
            return "可以考虑申请，建议优化权利要求"
        elif overall_score >= 45:
            return "专利性一般，建议进行现有技术检索后决定"
        else:
            return "专利性较低，不建议申请或需要重大改进"

    def _identify_key_factors(self, novelty: NoveltyAnalysisResult,
                             creativity: CreativityAssessmentResult,
                             utility: UtilityAssessmentResult,
                             claims: ClaimsAnalysisResult) -> tuple:
        """识别关键因素"""
        strengths = []
        weaknesses = []
        risks = []

        # 新颖性方面
        if novelty.novelty_score >= 70:
            strengths.append("新颖性较好")
        elif novelty.novelty_score < 50:
            weaknesses.append("新颖性不足")
            risks.append("现有技术较多")

        # 创造性方面
        if creativity.creativity_score >= 70:
            strengths.append("技术方案创新")
        elif creativity.creativity_score < 50:
            weaknesses.append("创新程度有限")
            risks.append("创造性可能受到质疑")

        # 实用性方面
        if utility.utility_score >= 70:
            strengths.append("实用性强")
        elif utility.utility_score < 50:
            weaknesses.append("实用性待提升")

        # 权利要求方面
        if claims.claims_count == 0:
            weaknesses.append("缺少权利要求")
            risks.append("无法确定保护范围")
        elif claims.clarity_score < 60:
            weaknesses.append("权利要求清晰度不足")
            risks.append("保护范围可能不明确")

        return strengths, weaknesses, risks

    def _generate_recommendations(self, novelty: NoveltyAnalysisResult,
                                creativity: CreativityAssessmentResult,
                                utility: UtilityAssessmentResult,
                                claims: ClaimsAnalysisResult) -> List[str]:
        """生成行动建议"""
        recommendations = []

        # 新颖性建议
        if novelty.novelty_score < 60:
            recommendations.append("建议进行更深入的现有技术检索，以增强新颖性")

        # 创造性建议
        if creativity.creativity_score < 60:
            recommendations.append("建议加强技术方案的创新性，突出与现有技术的区别")

        # 实用性建议
        if utility.utility_score < 60:
            recommendations.append("建议补充具体的实施方式，增强实用性")

        # 权利要求建议
        if claims.claims_count < 2:
            recommendations.append("建议增加从属权利要求，形成多层次保护")

        return recommendations

    def _generate_novelty_recommendations(self, score: float,
                                        similar_patents: List) -> List[str]:
        """生成新颖性改进建议"""
        recommendations = []

        if len(similar_patents) > 3:
            recommendations.append("现有技术较多，建议突出技术差异点")

        if score < 60:
            recommendations.append("新颖性较低，建议调整技术方案")

        return recommendations

    def _generate_creativity_improvements(self, score: float) -> List[str]:
        """生成创造性改进建议"""
        recommendations = []

        if score < 70:
            recommendations.append("建议增加技术方案的创新点")

        if score < 50:
            recommendations.append("建议强调预料不到的技术效果")

        return recommendations

    def _generate_utility_suggestions(self, score: float) -> List[str]:
        """生成实用性改进建议"""
        recommendations = []

        if score < 70:
            recommendations.append("建议补充具体的实施例")

        return recommendations

    def _generate_claims_suggestions(self, clarity_score: float,
                                   coverage_score: float,
                                   breadth: str) -> List[str]:
        """生成权利要求撰写建议"""
        suggestions = []

        if clarity_score < 70:
            suggestions.append("建议提高权利要求的表述清晰度")

        if coverage_score < 70:
            suggestions.append("建议增加从属权利要求")

        if breadth == "较窄保护范围":
            suggestions.append("建议适当扩大保护范围")

        return suggestions

    # ==================== 默认结果 ====================

    def _get_default_novelty_result(self, patent_id: str, title: str) -> NoveltyAnalysisResult:
        """获取默认新颖性分析结果"""
        return NoveltyAnalysisResult(
            patent_id=patent_id,
            novelty_score=60.0,
            novelty_level=AssessmentLevel.MEDIUM,
            similar_patents=[],
            novel_features=[],
            prior_art_found=False,
            analysis_details={"note": "使用默认评估"},
            recommendations=["建议进行现有技术检索"]
        )

    def _get_default_creativity_result(self, patent_id: str, title: str) -> CreativityAssessmentResult:
        """获取默认创造性评估结果"""
        return CreativityAssessmentResult(
            patent_id=patent_id,
            creativity_score=60.0,
            creativity_level=AssessmentLevel.MEDIUM,
            technical_contribution="待评估",
            innovation_type=["待分析"],
            unexpected_effects=[],
            analysis_details={"note": "使用默认评估"},
            improvement_suggestions=["建议补充技术细节"]
        )

    def _get_default_utility_result(self, patent_id: str, title: str) -> UtilityAssessmentResult:
        """获取默认实用性评估结果"""
        return UtilityAssessmentResult(
            patent_id=patent_id,
            utility_score=60.0,
            utility_level=AssessmentLevel.MEDIUM,
            industrial_applicability=True,
            implementation_feasibility="待评估",
            commercial_potential="待评估",
            analysis_details={"note": "使用默认评估"},
            application_suggestions=["建议补充实施方式"]
        )

    def _get_default_claims_result(self, patent_id: str, title: str,
                                 claims: List[str]) -> ClaimsAnalysisResult:
        """获取默认权利要求分析结果"""
        return ClaimsAnalysisResult(
            patent_id=patent_id,
            claims_count=len(claims),
            clarity_score=70.0,
            coverage_score=70.0,
            breadth_assessment="待评估",
            independent_claims=[],
            dependent_claims=[],
            analysis_details={"note": "使用默认评估"},
            drafting_suggestions=["建议完善权利要求结构"]
        )


async def test_evaluation_system():
    """测试专利评估系统"""
    system = PatentEvaluationSystem()

    print("\n" + "="*80)
    print("🔬 专利分析与评估系统测试")
    print("="*80)

    # 测试专利数据
    test_patent = {
        "patent_id": "CN123456789A",
        "title": "一种基于深度学习的图像识别方法",
        "abstract": "本发明公开了一种基于深度卷积神经网络的图像识别方法，包括特征提取层、卷积层、池化层和全连接层。该方法通过多尺度特征融合技术，提高了图像识别的准确率和鲁棒性。可应用于人脸识别、物体检测、场景分类等领域。",
        "claims": [
            "1. 一种基于深度学习的图像识别方法，其特征在于，包括：输入层，用于接收待识别图像；卷积层，用于提取图像特征；池化层，用于降维和特征选择；全连接层，用于分类识别；输出层，输出识别结果。",
            "2. 根据权利要求1所述的方法，其特征在于，所述卷积层采用多尺度卷积核。",
            "3. 根据权利要求1所述的方法，其特征在于，还包括数据增强层，用于扩充训练样本。"
        ],
        "description": "本发明属于计算机视觉技术领域，具体涉及一种利用深度学习进行图像识别的方法。",
        "applicant": "北京大学",
        "inventor": "张三;李四;王五",
        "ipc_codes": "G06K;G06N"
    }

    print(f"\n📋 评估专利: {test_patent['patent_id']}")
    print(f"标题: {test_patent['title']}")
    print(f"申请人: {test_patent['applicant']}")
    print()

    # 执行综合评估
    report = await system.evaluate_patent(**test_patent)

    # 输出评估结果
    print("="*80)
    print("📊 综合评估报告")
    print("="*80)

    print(f"\n专利号: {report.patent_id}")
    print(f"标题: {report.title}")
    print(f"评估日期: {report.evaluation_date}")
    print(f"综合评分: {report.overall_score:.2f} 分")
    print(f"评估等级: {report.overall_level.value}")

    print(f"\n可专利性建议: {report.patentability_recommendation}")

    print("\n" + "-"*80)
    print("1️⃣ 新颖性分析")
    print("-"*80)
    print(f"新颖性评分: {report.novelty.novelty_score:.2f} 分")
    print(f"新颖性等级: {report.novelty.novelty_level.value}")
    print(f"新颖特征数量: {len(report.novelty.novel_features)}")
    print(f"发现相似专利: {len(report.novelty.similar_patents)} 件")
    if report.novelty.similar_patents:
        print(f"示例: [{report.novelty.similar_patents[0]['patent_id']}] {report.novelty.similar_patents[0]['title'][:50]}...")

    print("\n" + "-"*80)
    print("2️⃣ 创造性评估")
    print("-"*80)
    print(f"创造性评分: {report.creativity.creativity_score:.2f} 分")
    print(f"创造性等级: {report.creativity.creativity_level.value}")
    print(f"技术贡献: {report.creativity.technical_contribution}")
    print(f"创新类型: {', '.join(report.creativity.innovation_type)}")
    print(f"预料不到的效果: {len(report.creativity.unexpected_effects)} 项")

    print("\n" + "-"*80)
    print("3️⃣ 实用性评估")
    print("-"*80)
    print(f"实用性评分: {report.utility.utility_score:.2f} 分")
    print(f"实用性等级: {report.utility.utility_level.value}")
    print(f"工业实用性: {'是' if report.utility.industrial_applicability else '否'}")
    print(f"实施可行性: {report.utility.implementation_feasibility}")
    print(f"商业潜力: {report.utility.commercial_potential}")

    print("\n" + "-"*80)
    print("4️⃣ 权利要求分析")
    print("-"*80)
    print(f"权利要求数量: {report.claims.claims_count} 条")
    print(f"清晰度评分: {report.claims.clarity_score:.2f} 分")
    print(f"保护范围评分: {report.claims.coverage_score:.2f} 分")
    print(f"保护范围: {report.claims.breadth_assessment}")

    print("\n" + "="*80)
    print("✅ 关键优势")
    print("="*80)
    for i, strength in enumerate(report.key_strengths, 1):
        print(f"{i}. {strength}")

    if report.key_weaknesses:
        print("\n" + "="*80)
        print("⚠️  关键劣势")
        print("="*80)
        for i, weakness in enumerate(report.key_weaknesses, 1):
            print(f"{i}. {weakness}")

    if report.risk_factors:
        print("\n" + "="*80)
        print("⚠️  风险因素")
        print("="*80)
        for i, risk in enumerate(report.risk_factors, 1):
            print(f"{i}. {risk}")

    print("\n" + "="*80)
    print("💡 行动建议")
    print("="*80)
    for i, recommendation in enumerate(report.recommended_actions, 1):
        print(f"{i}. {recommendation}")

    print("\n" + "="*80)
    print("✅ 评估完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_evaluation_system())
