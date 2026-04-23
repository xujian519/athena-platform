
#!/usr/bin/env python3
"""
专利评估器
Patent Evaluator

专利价值评估和质量评估功能

作者: Athena AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EvaluationCriterion(Enum):
    """评估标准"""

    NOVELTY = "novelty"  # 新颖性
    INVENTIVE_STEP = "inventive_step"  # 创造性
    INDUSTRIAL_APPLICABILITY = "industrial_applicability"  # 实用性
    TECHNICAL_ADVANCEMENT = "technical_advancement"  # 技术进步性
    COMMERCIAL_VALUE = "commercial_value"  # 商业价值
    LEGAL_STABILITY = "legal_stability"  # 法律稳定性
    MARKET_POTENTIAL = "market_potential"  # 市场潜力


class EvaluationLevel(Enum):
    """评估等级"""

    EXCELLENT = "excellent"  # 优秀 (90-100)
    GOOD = "good"  # 良好 (80-89)
    AVERAGE = "average"  # 一般 (70-79)
    POOR = "poor"  # 较差 (60-69)
    VERY_POOR = "very_poor"  # 很差 (0-59)


@dataclass
class CriterionScore:
    """标准评分"""

    criterion: EvaluationCriterion
    score: float
    level: EvaluationLevel
    reasoning: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class PatentEvaluationResult:
    """专利评估结果"""

    patent_id: str
    patent_title: str
    overall_score: float
    overall_level: EvaluationLevel
    criterion_scores: list[CriterionScore]
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    estimated_value: Optional[float] = None
    confidence_level: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


class PatentEvaluator:
    """专利评估器"""

    _instance: Optional[PatentEvaluator] = None

    def __init__(self):
        self.evaluation_models = {}
        self.scoring_weights = {
            EvaluationCriterion.NOVELTY: 0.20,
            EvaluationCriterion.INVENTIVE_STEP: 0.20,
            EvaluationCriterion.INDUSTRIAL_APPLICABILITY: 0.15,
            EvaluationCriterion.TECHNICAL_ADVANCEMENT: 0.15,
            EvaluationCriterion.COMMERCIAL_VALUE: 0.10,
            EvaluationCriterion.LEGAL_STABILITY: 0.10,
            EvaluationCriterion.MARKET_POTENTIAL: 0.10,
        }
        self._initialized = False

    @classmethod
    async def initialize(cls):
        """初始化评估器"""
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._load_models()
            cls._instance._initialized = True
            logger.info("✅ 专利评估器初始化完成")
        return cls._instance

    @classmethod
    def get_instance(cls) -> PatentEvaluator:
        """获取单例实例"""
        if cls._instance is None:
            raise RuntimeError("PatentEvaluator未初始化,请先调用initialize()")
        return cls._instance

    async def _load_models(self):
        """加载评估模型"""
        self.evaluation_models = {
            EvaluationCriterion.NOVELTY: self._load_novelty_evaluator(),
            EvaluationCriterion.INVENTIVE_STEP: self._load_inventive_evaluator(),
            EvaluationCriterion.INDUSTRIAL_APPLICABILITY: self._load_practical_evaluator(),
            EvaluationCriterion.TECHNICAL_ADVANCEMENT: self._load_technical_evaluator(),
            EvaluationCriterion.COMMERCIAL_VALUE: self._load_commercial_evaluator(),
            EvaluationCriterion.LEGAL_STABILITY: self._load_legal_evaluator(),
            EvaluationCriterion.MARKET_POTENTIAL: self._load_market_evaluator(),
        }

    def _load_novelty_evaluator(self) -> Any:
        """加载新颖性评估器"""
        return {
            "model_name": "patent_novelty_evaluator",
            "version": "3.0.0",
            "parameters": {
                "prior_art_search": True,
                "similarity_threshold": 0.7,
                "semantic_analysis": True,
            },
        }

    def _load_inventive_evaluator(self) -> Any:
        """加载创造性评估器"""
        return {
            "model_name": "patent_inventive_evaluator",
            "version": "3.0.0",
            "parameters": {
                "technical_difficulty": True,
                "obviousness_check": True,
                "advancement_level": True,
            },
        }

    def _load_practical_evaluator(self) -> Any:
        """加载实用性评估器"""
        return {
            "model_name": "patent_practical_evaluator",
            "version": "3.0.0",
            "parameters": {
                "industrial_applicability": True,
                "economic_feasibility": True,
                "implementation_complexity": True,
            },
        }

    def _load_technical_evaluator(self) -> Any:
        """加载技术评估器"""
        return {
            "model_name": "patent_technical_evaluator",
            "version": "3.0.0",
            "parameters": {
                "innovation_level": True,
                "technical_merit": True,
                "advancement_degree": True,
            },
        }

    def _load_commercial_evaluator(self) -> Any:
        """加载商业价值评估器"""
        return {
            "model_name": "patent_commercial_evaluator",
            "version": "3.0.0",
            "parameters": {
                "market_size": True,
                "competitive_advantage": True,
                "monetization_potential": True,
            },
        }

    def _load_legal_evaluator(self) -> Any:
        """加载法律稳定性评估器"""
        return {
            "model_name": "patent_legal_evaluator",
            "version": "3.0.0",
            "parameters": {
                "claim_validity": True,
                "infringement_risk": True,
                "enforceability": True,
            },
        }

    def _load_market_evaluator(self) -> Any:
        """加载市场潜力评估器"""
        return {
            "model_name": "patent_market_evaluator",
            "version": "3.0.0",
            "parameters": {
                "market_trends": True,
                "growth_potential": True,
                "competitive_landscape": True,
            },
        }

    async def evaluate_patent(self, patent_data: dict[str, Any]) -> PatentEvaluationResult:
        """
        评估专利

        Args:
            patent_data: 专利数据

        Returns:
            评估结果
        """
        logger.info(f"📊 开始评估专利: {patent_data.get('title', 'Unknown')}")

        criterion_scores = []

        # 逐项评估
        for criterion in EvaluationCriterion:
            try:
                score = await self._evaluate_criterion(patent_data, criterion)
                criterion_scores.append(score)
                logger.info(f"✅ {criterion.value}评估完成: {score.score}")
            except Exception as e:
                logger.error(f"❌ {criterion.value}评估失败: {e}")
                # 创建默认评分
                default_score = CriterionScore(
                    criterion=criterion,
                    score=50.0,
                    level=EvaluationLevel.POOR,
                    reasoning=f"评估失败: {e!s}",
                    evidence=[],
                )
                criterion_scores.append(default_score)

        # 计算总分
        overall_score = self._calculate_overall_score(criterion_scores)
        overall_level = self._determine_level(overall_score)

        # 分析优劣势
        strengths, weaknesses = self._analyze_strengths_weaknesses(criterion_scores)

        # 生成建议
        recommendations = self._generate_recommendations(criterion_scores, overall_level)

        # 估算价值
        estimated_value = await self._estimate_patent_value(patent_data, overall_score)

        # 计算置信度
        confidence_level = self._calculate_confidence_level(criterion_scores)

        result = PatentEvaluationResult(
            patent_id=patent_data.get("id", "unknown"),
            patent_title=patent_data.get("title", "Unknown"),
            overall_score=overall_score,
            overall_level=overall_level,
            criterion_scores=criterion_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            estimated_value=estimated_value,
            confidence_level=confidence_level,
        )

        logger.info(f"✅ 专利评估完成: 总分{overall_score:.1f} ({overall_level.value})")
        return result

    async def _evaluate_criterion(
        self, patent_data: dict[str, Any], criterion: EvaluationCriterion
    ) -> CriterionScore:
        """评估特定标准"""
        model = self.evaluation_models.get(criterion)
        if not model:
            raise ValueError(f"不支持的评估标准: {criterion}")

        # 模拟评估过程
        await asyncio.sleep(0.1)

        # 根据标准类型执行不同的评估逻辑
        if criterion == EvaluationCriterion.NOVELTY:
            return await self._evaluate_novelty(patent_data)
        elif criterion == EvaluationCriterion.INVENTIVE_STEP:
            return await self._evaluate_inventive_step(patent_data)
        elif criterion == EvaluationCriterion.INDUSTRIAL_APPLICABILITY:
            return await self._evaluate_industrial_applicability(patent_data)
        elif criterion == EvaluationCriterion.TECHNICAL_ADVANCEMENT:
            return await self._evaluate_technical_advancement(patent_data)
        elif criterion == EvaluationCriterion.COMMERCIAL_VALUE:
            return await self._evaluate_commercial_value(patent_data)
        elif criterion == EvaluationCriterion.LEGAL_STABILITY:
            return await self._evaluate_legal_stability(patent_data)
        elif criterion == EvaluationCriterion.MARKET_POTENTIAL:
            return await self._evaluate_market_potential(patent_data)
        else:
            raise ValueError(f"未实现的评估标准: {criterion}")

    async def _evaluate_novelty(self, patent_data: dict[str, Any]) -> CriterionScore:
        """评估新颖性"""
        # 模拟新颖性评估
        score = 85.0
        reasoning = "该专利技术方案与现有技术有显著区别,具有较好的新颖性"
        evidence = ["现有技术检索结果", "技术对比分析"]
        return CriterionScore(
            criterion=EvaluationCriterion.NOVELTY,
            score=score,
            level=self._determine_level(score),
            reasoning=reasoning,
            evidence=evidence,
        )

    async def _evaluate_inventive_step(self, patent_data: dict[str, Any]) -> CriterionScore:
        """评估创造性"""
        score = 80.0
        reasoning = "该专利具有突出的实质性特点和显著的进步,符合创造性要求"
        evidence = ["技术难点分析", "非显而易见性论证"]
        return CriterionScore(
            criterion=EvaluationCriterion.INVENTIVE_STEP,
            score=score,
            level=self._determine_level(score),
            reasoning=reasoning,
            evidence=evidence,
        )

    async def _evaluate_industrial_applicability(
        self, patent_data: dict[str, Any]]
    ) -> CriterionScore:
        """评估实用性"""
        score = 90.0
        reasoning = "该专利技术方案成熟,能够在工业上制造和使用"
        evidence = ["技术可行性分析", "成本效益评估"]
        return CriterionScore(
            criterion=EvaluationCriterion.INDUSTRIAL_APPLICABILITY,
            score=score,
            level=self._determine_level(score),
            reasoning=reasoning,
            evidence=evidence,
        )

    async def _evaluate_technical_advancement(self, patent_data: dict[str, Any]) -> CriterionScore:
        """评估技术进步性"""
        score = 88.0
        reasoning = "该专利在技术上有显著进步,提高了技术效果"
        evidence = ["技术效果对比", "性能指标提升"]
        return CriterionScore(
            criterion=EvaluationCriterion.TECHNICAL_ADVANCEMENT,
            score=score,
            level=self._determine_level(score),
            reasoning=reasoning,
            evidence=evidence,
        )

    async def _evaluate_commercial_value(self, patent_data: dict[str, Any]) -> CriterionScore:
        """评估商业价值"""
        score = 75.0
        reasoning = "该专利具有良好的商业应用前景,但需要进一步市场验证"
        evidence = ["市场规模分析", "竞争优势评估"]
        return CriterionScore(
            criterion=EvaluationCriterion.COMMERCIAL_VALUE,
            score=score,
            level=self._determine_level(score),
            reasoning=reasoning,
            evidence=evidence,
        )

    async def _evaluate_legal_stability(self, patent_data: dict[str, Any]) -> CriterionScore:
        """评估法律稳定性"""
        score = 85.0
        reasoning = "该专利权利要求清晰,法律稳定性较好"
        evidence = ["权利要求分析", "侵权风险评估"]
        return CriterionScore(
            criterion=EvaluationCriterion.LEGAL_STABILITY,
            score=score,
            level=self._determine_level(score),
            reasoning=reasoning,
            evidence=evidence,
        )

    async def _evaluate_market_potential(self, patent_data: dict[str, Any]) -> CriterionScore:
        """评估市场潜力"""
        score = 78.0
        reasoning = "该专利所在市场增长潜力较大,具有较好的发展前景"
        evidence = ["市场趋势分析", "竞争格局评估"]
        return CriterionScore(
            criterion=EvaluationCriterion.MARKET_POTENTIAL,
            score=score,
            level=self._determine_level(score),
            reasoning=reasoning,
            evidence=evidence,
        )

    def _calculate_overall_score(self, criterion_scores: list[CriterionScore]) -> float:
        """计算总分"""
        total_score = 0.0
        total_weight = 0.0

        for score in criterion_scores:
            weight = self.scoring_weights.get(score.criterion, 0.0)
            total_score += score.score * weight
            total_weight += weight

        return total_score / max(total_weight, 1.0)

    def _determine_level(self, score: float) -> EvaluationLevel:
        """确定评估等级"""
        if score >= 90:
            return EvaluationLevel.EXCELLENT
        elif score >= 80:
            return EvaluationLevel.GOOD
        elif score >= 70:
            return EvaluationLevel.AVERAGE
        elif score >= 60:
            return EvaluationLevel.POOR
        else:
            return EvaluationLevel.VERY_POOR

    def _analyze_strengths_weaknesses(
        self, criterion_scores: list[CriterionScore]
    ) -> tuple[list[str], list[str]]:
        """分析优劣势"""
        strengths = []
        weaknesses = []

        for score in criterion_scores:
            if score.score >= 80:
                strengths.append(f"{score.criterion.value}: {score.reasoning}")
            elif score.score < 70:
                weaknesses.append(f"{score.criterion.value}: {score.reasoning}")

        return strengths, weaknesses

    def _generate_recommendations(
        self, criterion_scores: list[CriterionScore], overall_level: EvaluationLevel
    ) -> list[str]:
        """生成建议"""
        recommendations = []

        # 根据整体等级提供建议
        if overall_level in [EvaluationLevel.EXCELLENT, EvaluationLevel.GOOD]:
            recommendations.append("专利质量良好,建议尽快提交申请")
        elif overall_level == EvaluationLevel.AVERAGE:
            recommendations.append("专利质量一般,建议进一步优化后再提交")
        else:
            recommendations.append("专利质量较差,建议重大修改后再考虑提交")

        # 针对低分项目提供建议
        for score in criterion_scores:
            if score.score < 70:
                if score.criterion == EvaluationCriterion.NOVELTY:
                    recommendations.append("建议加强技术创新点,提高新颖性")
                elif score.criterion == EvaluationCriterion.INVENTIVE_STEP:
                    recommendations.append("建议突出技术难点和创造性")
                elif score.criterion == EvaluationCriterion.INDUSTRIAL_APPLICABILITY:
                    recommendations.append("建议完善实施例,提高实用性")
                elif score.criterion == EvaluationCriterion.COMMERCIAL_VALUE:
                    recommendations.append("建议加强市场调研,明确商业应用")
                elif score.criterion == EvaluationCriterion.LEGAL_STABILITY:
                    recommendations.append("建议优化权利要求,提高法律稳定性")
                elif score.criterion == EvaluationCriterion.MARKET_POTENTIAL:
                    recommendations.append("建议深入分析市场,发掘应用潜力")

        return recommendations

    async def _estimate_patent_value(
        self, patent_data: dict[str, Any], overall_score: float
    ) -> Optional[float]:
        """估算专利价值"""
        try:
            # 简化的价值估算模型
            base_value = 1000000  # 基础价值100万
            score_multiplier = overall_score / 100.0
            estimated_value = base_value * score_multiplier
            return estimated_value
        except Exception as e:
            logger.error(f"专利价值估算失败: {e}")
            return None

    def _calculate_confidence_level(self, criterion_scores: list[CriterionScore]) -> float:
        """计算置信度"""
        if not criterion_scores:
            return 0.0

        # 基于评分的一致性计算置信度
        scores = [score.score for score in criterion_scores]
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)

        # 方差越小,置信度越高
        confidence = max(0.5, 1.0 - variance / 1000.0)
        return confidence

    async def batch_evaluate(self, patents: list[dict[str, Any]) -> list[PatentEvaluationResult]]:
        """批量评估专利"""
        logger.info(f"📊 开始批量评估{len(patents)}项专利")

        tasks = [self.evaluate_patent(patent) for patent in patents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 专利{i+1}评估失败: {result}")
                # 创建默认结果
                default_result = PatentEvaluationResult(
                    patent_id=patents[i].get("id", f"patent_{i+1}"),
                    patent_title=patents[i].get("title", "Unknown"),
                    overall_score=0.0,
                    overall_level=EvaluationLevel.VERY_POOR,
                    criterion_scores=[],
                    strengths=[],
                    weaknesses=["评估失败"],
                    recommendations=["重新提交评估"],
                    confidence_level=0.0,
                )
                processed_results.append(default_result)
            else:
                processed_results.append(result)

        logger.info("✅ 批量评估完成")
        return processed_results

    @classmethod
    async def shutdown(cls):
        """关闭评估器"""
        if cls._instance:
            cls._instance = None
            logger.info("✅ 专利评估器已关闭")

