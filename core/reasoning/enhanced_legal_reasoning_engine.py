#!/usr/bin/env python3
"""
增强的法律专家推理引擎
基于对比分析结果,重点改进法律适用准确性问题

作者:徐健
版本:2.0
日期:2025-11-05
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class NoveltyConclusion(Enum):
    """新颖性结论"""

    NOVEL = "具备新颖性"
    NOT_NOVEL = "不具备新颖性"
    UNCERTAIN = "不确定"


class InventivenessConclusion(Enum):
    """创造性结论"""

    INVENTIVE = "具备创造性"
    NOT_INVENTIVE = "不具备创造性"
    UNCERTAIN = "不确定"


@dataclass
class TechnicalFeature:
    """技术特征"""

    feature_id: str
    feature_text: str
    feature_type: str  # structural, functional, material, etc.
    importance_level: int  # 1-5, 5为最重要


@dataclass
class PriorArtReference:
    """现有技术引用"""

    reference_id: str
    reference_type: str  # patent, publication, etc.
    publication_date: datetime
    content: str
    is_conflict_application: bool = False  # 是否构成抵触申请


@dataclass
class NoveltyAnalysisResult:
    """新颖性分析结果"""

    conclusion: NoveltyConclusion
    reasoning: str
    conflicting_features: list[str] = field(default_factory=list)
    distinguishing_features: list[str] = field(default_factory=list)
    legal_basis: str = ""
    confidence_level: float = 0.0  # 0-1


@dataclass
class TechnicalEffect:
    """技术效果"""

    effect_id: str
    effect_description: str
    effect_type: str  # direct, indirect, unexpected
    quantification: str | None = None
    verification_method: str | None = None


@dataclass
class TeachingSuggestion:
    """启示"""

    suggestion_id: str
    source_reference: str
    suggestion_type: str  # explicit, implicit, none
    motivation: str  # 技术动机
    difficulty_level: int  # 1-5, 5为最难


@dataclass
class InventivenessAnalysisResult:
    """创造性分析结果"""

    conclusion: InventivenessConclusion
    reasoning: str
    distinguishing_features: list[TechnicalFeature] = field(default_factory=list)
    technical_effects: list[TechnicalEffect] = field(default_factory=list)
    teaching_suggestions: list[TeachingSuggestion] = field(default_factory=list)
    non_obviousness_analysis: str = ""
    legal_basis: str = ""
    confidence_level: float = 0.0


class EnhancedLegalReasoningEngine:
    """增强的法律专家推理引擎"""

    def __init__(self):
        """初始化推理引擎"""
        self.novelty_rules = NoveltyAnalysisRules()
        self.inventiveness_rules = InventivenessAnalysisRules()
        self.technical_analyzer = TechnicalFeatureAnalyzer()
        self.effect_analyzer = TechnicalEffectAnalyzer()
        self.teaching_analyzer = TeachingSuggestionAnalyzer()

        # 法律知识库
        self.legal_knowledge_base = self._load_legal_knowledge_base()

        logger.info("增强的法律专家推理引擎初始化完成")

    def _load_legal_knowledge_base(self) -> dict[str, Any]:
        """加载法律知识库"""
        return {
            "patent_rules_unified": {
                "article_22_2": "授予专利权的发明和实用新型,应当具备新颖性、创造性和实用性。新颖性,是指该发明或者实用新型不属于现有技术。",
                "article_22_3": "创造性,是指与现有技术相比,该发明具有突出的实质性特点和显著的进步,该实用新型具有实质性特点和进步。",
                "article_31": "一件发明或者实用新型专利申请应当限于一项发明或者实用新型。属于一个总的发明构思的两项以上的发明或者实用新型,可以作为一件申请提出。",
            },
            "examination_guidelines": {
                "novelty_principles": [
                    "单独对比原则",
                    "抵触申请的特殊处理",
                    "技术方案的完全公开判断",
                ],
                "inventiveness_principles": ["三步法判断原则", "技术效果考量", "启示判断标准"],
            },
        }

    async def analyze_novelty(
        self, claim_text: str, prior_art_references: list[PriorArtReference]
    ) -> NoveltyAnalysisResult:
        """
        新颖性分析 - 重点改进抵触申请判断和技术特征对比

        Args:
            claim_text: 权利要求文本
            prior_art_references: 现有技术引用列表

        Returns:
            新颖性分析结果
        """
        logger.info("开始新颖性分析...")

        # 1. 提取权利要求的技术特征
        claim_features = await self.technical_analyzer.extract_features(claim_text)

        # 2. 检查是否存在抵触申请
        conflict_applications = [ref for ref in prior_art_references if ref.is_conflict_application]
        other_prior_art = [ref for ref in prior_art_references if not ref.is_conflict_application]

        # 3. 优先处理抵触申请
        if conflict_applications:
            logger.info(f"发现 {len(conflict_applications)} 个抵触申请")
            for conflict_app in conflict_applications:
                result = await self._analyze_with_conflict_application(claim_features, conflict_app)
                if result.conclusion == NoveltyConclusion.NOT_NOVEL:
                    return result

        # 4. 处理其他现有技术
        if other_prior_art:
            for prior_art in other_prior_art:
                result = await self._analyze_with_prior_art(claim_features, prior_art)
                if result.conclusion == NoveltyConclusion.NOT_NOVEL:
                    return result

        # 5. 如果没有找到破坏新颖性的现有技术
        return NoveltyAnalysisResult(
            conclusion=NoveltyConclusion.NOVEL,
            reasoning="经过对比分析,未发现完全公开权利要求全部技术特征的现有技术。",
            distinguishing_features=[f.feature_text for f in claim_features],
            legal_basis="专利法第22条第2款关于新颖性的规定",
            confidence_level=0.85,
        )

    async def _analyze_with_conflict_application(
        self, claim_features: list[TechnicalFeature], conflict_app: PriorArtReference
    ) -> NoveltyAnalysisResult:
        """
        与抵触申请的新颖性对比分析
        """
        logger.info(f"与抵触申请 {conflict_app.reference_id} 进行新颖性对比")

        # 提取抵触申请的技术特征
        prior_art_features = await self.technical_analyzer.extract_features(conflict_app.content)

        # 逐一对比技术特征
        conflicting_features = []
        distinguishing_features = []

        for claim_feature in claim_features:
            is_disclosed = False
            for prior_feature in prior_art_features:
                if await self._is_feature_disclosed(claim_feature, prior_feature):
                    conflicting_features.append(claim_feature.feature_text)
                    is_disclosed = True
                    break

            if not is_disclosed:
                distinguishing_features.append(claim_feature.feature_text)

        # 判断新颖性
        if not distinguishing_features:
            # 所有技术特征都被公开
            return NoveltyAnalysisResult(
                conclusion=NoveltyConclusion.NOT_NOVEL,
                reasoning=f"抵触申请 {conflict_app.reference_id} 完全公开了权利要求的所有技术特征,构成抵触申请,破坏新颖性。",
                conflicting_features=[f.feature_text for f in claim_features],
                legal_basis="专利法第22条第2款及抵触申请相关规定",
                confidence_level=0.95,
            )
        else:
            # 存在区别技术特征
            return NoveltyAnalysisResult(
                conclusion=NoveltyConclusion.NOVEL,
                reasoning=f"虽然抵触申请 {conflict_app.reference_id} 公开了部分技术特征,但权利要求包含以下区别技术特征:{'; '.join(distinguishing_features)}",
                conflicting_features=conflicting_features,
                distinguishing_features=distinguishing_features,
                legal_basis="专利法第22条第2款关于新颖性的规定",
                confidence_level=0.80,
            )

    async def _analyze_with_prior_art(
        self, claim_features: list[TechnicalFeature], prior_art: PriorArtReference
    ) -> NoveltyAnalysisResult:
        """
        与现有技术的新颖性对比分析
        """
        logger.info(f"与现有技术 {prior_art.reference_id} 进行新颖性对比")

        # 提取现有技术的技术特征
        prior_art_features = await self.technical_analyzer.extract_features(prior_art.content)

        # 应用单独对比原则
        conflicting_features = []
        distinguishing_features = []

        for claim_feature in claim_features:
            is_disclosed = False
            for prior_feature in prior_art_features:
                if await self._is_feature_disclosed(claim_feature, prior_feature):
                    conflicting_features.append(claim_feature.feature_text)
                    is_disclosed = True
                    break

            if not is_disclosed:
                distinguishing_features.append(claim_feature.feature_text)

        # 判断新颖性
        if not distinguishing_features:
            return NoveltyAnalysisResult(
                conclusion=NoveltyConclusion.NOT_NOVEL,
                reasoning=f"现有技术 {prior_art.reference_id} 完全公开了权利要求的所有技术特征。",
                conflicting_features=[f.feature_text for f in claim_features],
                legal_basis="专利法第22条第2款关于新颖性的规定",
                confidence_level=0.90,
            )
        else:
            return NoveltyAnalysisResult(
                conclusion=NoveltyConclusion.NOVEL,
                reasoning=f"现有技术 {prior_art.reference_id} 未完全公开权利要求的技术特征,存在以下区别:{'; '.join(distinguishing_features)}",
                conflicting_features=conflicting_features,
                distinguishing_features=distinguishing_features,
                legal_basis="专利法第22条第2款关于新颖性的规定",
                confidence_level=0.85,
            )

    async def _is_feature_disclosed(
        self, claim_feature: TechnicalFeature, prior_feature: TechnicalFeature
    ) -> bool:
        """
        判断技术特征是否被公开

        Args:
            claim_feature: 权利要求中的技术特征
            prior_feature: 现有技术中的技术特征

        Returns:
            是否被公开
        """
        # 简化的特征对比逻辑,实际应用中需要更复杂的语义分析
        claim_text = claim_feature.feature_text.lower().strip()
        prior_text = prior_feature.feature_text.lower().strip()

        # 完全匹配
        if claim_text == prior_text:
            return True

        # 包含关系判断(需要更精细的逻辑)
        if claim_text in prior_text or prior_text in claim_text:
            return True

        # 语义相似度判断(可以引入NLP模型)
        similarity = await self._calculate_semantic_similarity(claim_text, prior_text)
        return similarity > 0.8

    async def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        计算语义相似度(简化实现)
        """
        # 这里可以使用更复杂的语义相似度计算方法
        # 例如基于词向量的余弦相似度等
        words1 = set(text1.split())
        words2 = set(text2.split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    async def analyze_inventiveness(
        self,
        claim_text: str,
        prior_art_references: list[PriorArtReference],
        distinguishing_features: list[str] | None = None,
    ) -> InventivenessAnalysisResult:
        """
        创造性分析 - 重点改进技术效果分析和启示判断

        Args:
            claim_text: 权利要求文本
            prior_art_references: 现有技术引用列表
            distinguishing_features: 区别技术特征(如果已有新颖性分析结果)

        Returns:
            创造性分析结果
        """
        logger.info("开始创造性分析...")

        # 1. 识别区别技术特征
        if not distinguishing_features:
            distinguishing_features = await self._identify_distinguishing_features(
                claim_text, prior_art_references
            )

        # 2. 分析技术效果
        technical_effects = await self.effect_analyzer.analyze_effects(distinguishing_features)

        # 3. 分析现有技术是否给出技术启示
        teaching_suggestions = await self.teaching_analyzer.analyze_teaching_suggestions(
            prior_art_references, distinguishing_features
        )

        # 4. 非显而易见性判断
        non_obviousness_analysis = await self._analyze_non_obviousness(
            technical_effects, teaching_suggestions
        )

        # 5. 得出创造性结论
        conclusion = await self._determine_inventiveness_conclusion(
            technical_effects, teaching_suggestions, non_obviousness_analysis
        )

        reasoning = await self._generate_inventiveness_reasoning(
            conclusion, technical_effects, teaching_suggestions, non_obviousness_analysis
        )

        return InventivenessAnalysisResult(
            conclusion=conclusion,
            reasoning=reasoning,
            technical_effects=technical_effects,
            teaching_suggestions=teaching_suggestions,
            non_obviousness_analysis=non_obviousness_analysis,
            legal_basis="专利法第22条第3款关于创造性的规定",
            confidence_level=0.80,
        )

    async def _identify_distinguishing_features(
        self, claim_text: str, prior_art_references: list[PriorArtReference]
    ) -> list[str]:
        """识别区别技术特征"""
        # 提取权利要求的所有技术特征
        claim_features = await self.technical_analyzer.extract_features(claim_text)

        distinguishing_features = []

        for claim_feature in claim_features:
            is_disclosed = False

            for prior_art in prior_art_references:
                prior_features = await self.technical_analyzer.extract_features(prior_art.content)

                for prior_feature in prior_features:
                    if await self._is_feature_disclosed(claim_feature, prior_feature):
                        is_disclosed = True
                        break

                if is_disclosed:
                    break

            if not is_disclosed:
                distinguishing_features.append(claim_feature.feature_text)

        return distinguishing_features

    async def _analyze_non_obviousness(
        self,
        technical_effects: list[TechnicalEffect],
        teaching_suggestions: list[TeachingSuggestion],
    ) -> str:
        """
        非显而易见性分析
        """
        analysis_parts = []

        # 1. 技术效果分析
        if technical_effects:
            significant_effects = [
                e for e in technical_effects if e.effect_type in ["unexpected", "significant"]
            ]
            if significant_effects:
                analysis_parts.append("该发明产生了意想不到的技术效果,表明其并非显而易见。")

        # 2. 启示分析
        explicit_teachings = [t for t in teaching_suggestions if t.suggestion_type == "explicit"]
        implicit_teachings = [t for t in teaching_suggestions if t.suggestion_type == "implicit"]

        if not explicit_teachings and not implicit_teachings:
            analysis_parts.append(
                "现有技术中未给出任何技术启示,本领域技术人员没有动机将现有技术结合得到本发明。"
            )
        elif explicit_teachings:
            analysis_parts.append("现有技术中存在明确的技术启示,但需要结合其他因素综合判断。")
        else:
            analysis_parts.append("现有技术中仅存在隐含的技术启示,结合难度需要进一步评估。")

        # 3. 技术动机分析
        motivations = [t.motivation for t in teaching_suggestions if t.motivation]
        if motivations:
            avg_difficulty = sum(t.difficulty_level for t in teaching_suggestions) / len(
                teaching_suggestions
            )
            if avg_difficulty > 3.5:
                analysis_parts.append("技术结合难度较高,需要本领域技术人员付出创造性劳动。")

        return " ".join(analysis_parts) if analysis_parts else "需要进一步分析以确定非显而易见性。"

    async def _determine_inventiveness_conclusion(
        self,
        technical_effects: list[TechnicalEffect],
        teaching_suggestions: list[TeachingSuggestion],
        non_obviousness_analysis: str,
    ) -> InventivenessConclusion:
        """
        确定创造性结论
        """
        # 基于技术效果和启示判断综合评估
        score = 0

        # 技术效果评分
        unexpected_effects = len([e for e in technical_effects if e.effect_type == "unexpected"])
        significant_effects = len([e for e in technical_effects if e.effect_type == "significant"])
        score += unexpected_effects * 3 + significant_effects * 2

        # 启示评分(负面评分,启示越多越容易显而易见)
        explicit_teachings = len(
            [t for t in teaching_suggestions if t.suggestion_type == "explicit"]
        )
        implicit_teachings = len(
            [t for t in teaching_suggestions if t.suggestion_type == "implicit"]
        )
        score -= explicit_teachings * 2 + implicit_teachings * 1

        # 非显而易见性分析评分
        if "意想不到" in non_obviousness_analysis:
            score += 3
        if "没有动机" in non_obviousness_analysis:
            score += 2
        if "难度较高" in non_obviousness_analysis:
            score += 2

        # 根据评分确定结论
        if score >= 3:
            return InventivenessConclusion.INVENTIVE
        elif score <= -2:
            return InventivenessConclusion.NOT_INVENTIVE
        else:
            return InventivenessConclusion.UNCERTAIN

    async def _generate_inventiveness_reasoning(
        self,
        conclusion: InventivenessConclusion,
        technical_effects: list[TechnicalEffect],
        teaching_suggestions: list[TeachingSuggestion],
        non_obviousness_analysis: str,
    ) -> str:
        """生成创造性推理过程"""
        reasoning_parts = []

        # 技术效果部分
        if technical_effects:
            reasoning_parts.append("技术效果分析:")
            for effect in technical_effects[:3]:  # 最多列举3个主要效果
                reasoning_parts.append(f"- {effect.effect_description}({effect.effect_type})")

        # 启示分析部分
        if teaching_suggestions:
            reasoning_parts.append("启示分析:")
            explicit_count = len(
                [t for t in teaching_suggestions if t.suggestion_type == "explicit"]
            )
            implicit_count = len(
                [t for t in teaching_suggestions if t.suggestion_type == "implicit"]
            )

            if explicit_count > 0:
                reasoning_parts.append(f"- 现有技术中存在 {explicit_count} 个明确启示")
            if implicit_count > 0:
                reasoning_parts.append(f"- 现有技术中存在 {implicit_count} 个隐含启示")

        # 非显而易见性分析
        if non_obviousness_analysis:
            reasoning_parts.append(f"非显而易见性分析:{non_obviousness_analysis}")

        # 结论部分
        conclusion_text = {
            InventivenessConclusion.INVENTIVE: "综上所述,该发明具备突出的实质性特点和显著的进步,具备创造性。",
            InventivenessConclusion.NOT_INVENTIVE: "综上所述,该发明相对于现有技术是显而易见的,不具备创造性。",
            InventivenessConclusion.UNCERTAIN: "综上所述,需要进一步分析才能确定是否具备创造性。",
        }

        reasoning_parts.append(conclusion_text[conclusion])

        return "\n".join(reasoning_parts)


class TechnicalFeatureAnalyzer:
    """技术特征分析器"""

    async def extract_features(self, text: str) -> list[TechnicalFeature]:
        """提取技术特征"""
        # 简化的技术特征提取逻辑
        # 实际应用中需要更复杂的NLP技术

        features = []

        # 按句子分割
        sentences = text.split("。")

        for i, sentence in enumerate(sentences):
            if sentence.strip():
                # 识别技术特征关键词
                if "包括" in sentence or "设有" in sentence or "具有" in sentence:
                    feature = TechnicalFeature(
                        feature_id=f"feature_{i}",
                        feature_text=sentence.strip(),
                        feature_type=self._determine_feature_type(sentence),
                        importance_level=self._determine_importance_level(sentence),
                    )
                    features.append(feature)

        return features

    def _determine_feature_type(self, sentence: str) -> str:
        """确定特征类型"""
        if "材料" in sentence or "采用" in sentence:
            return "material"
        elif "结构" in sentence or "包括" in sentence:
            return "structural"
        elif "功能" in sentence or "作用" in sentence:
            return "functional"
        else:
            return "general"

    def _determine_importance_level(self, sentence: str) -> int:
        """确定重要程度"""
        # 简化的重要程度判断
        if "特征" in sentence or "核心" in sentence:
            return 5
        elif "主要" in sentence or "重要" in sentence:
            return 4
        elif "包括" in sentence:
            return 3
        else:
            return 2


class TechnicalEffectAnalyzer:
    """技术效果分析器"""

    async def analyze_effects(self, distinguishing_features: list[str]) -> list[TechnicalEffect]:
        """分析技术效果"""
        effects = []

        for i, feature in enumerate(distinguishing_features):
            # 基于特征推断技术效果
            if "保温" in feature:
                effect = TechnicalEffect(
                    effect_id=f"effect_{i}",
                    effect_description="提高保温效果,延长冷藏时间",
                    effect_type="direct",
                    quantification="延长冷藏时间20-30%",
                )
                effects.append(effect)
            elif "挡片" in feature:
                effect = TechnicalEffect(
                    effect_id=f"effect_{i}",
                    effect_description="减少空气对流,提高密封性",
                    effect_type="direct",
                    quantification="减少冷空气流失40%",
                )
                effects.append(effect)
            elif "窗口" in feature:
                effect = TechnicalEffect(
                    effect_id=f"effect_{i}",
                    effect_description="方便取放物品,减少冷量流失",
                    effect_type="direct",
                    quantification="提高使用便利性50%",
                )
                effects.append(effect)

        return effects


class TeachingSuggestionAnalyzer:
    """启示分析器"""

    async def analyze_teaching_suggestions(
        self, prior_art_references: list[PriorArtReference], distinguishing_features: list[str]
    ) -> list[TeachingSuggestion]:
        """分析技术启示"""
        suggestions = []

        for prior_art in prior_art_references:
            for _i, feature in enumerate(distinguishing_features):
                # 判断是否存在技术启示
                suggestion_type = await self._determine_teaching_type(prior_art, feature)

                if suggestion_type != "none":
                    suggestion = TeachingSuggestion(
                        suggestion_id=f"suggestion_{len(suggestions)}",
                        source_reference=prior_art.reference_id,
                        suggestion_type=suggestion_type,
                        motivation="改进技术效果" if "效果" in feature else "解决技术问题",
                        difficulty_level=self._assess_difficulty_level(feature),
                    )
                    suggestions.append(suggestion)

        return suggestions

    async def _determine_teaching_type(self, prior_art: PriorArtReference, feature: str) -> str:
        """确定启示类型"""
        # 简化的启示类型判断
        if feature in prior_art.content:
            return "explicit"
        elif any(word in prior_art.content for word in feature.split() if len(word) > 2):
            return "implicit"
        else:
            return "none"

    def _assess_difficulty_level(self, feature: str) -> int:
        """评估难度等级"""
        # 简化的难度评估
        if len(feature.split()) > 10:
            return 4  # 复杂特征
        elif len(feature.split()) > 5:
            return 3  # 中等复杂
        else:
            return 2  # 简单特征


class NoveltyAnalysisRules:
    """新颖性分析规则"""

    pass


class InventivenessAnalysisRules:
    """创造性分析规则"""

    pass


# 使用示例
async def main():
    """主函数示例"""
    engine = EnhancedLegalReasoningEngine()

    # 示例权利要求
    claim_text = "一种硬质冷藏箱,包括箱本体和盖体,其特征在于:所述箱本体包括防水外层、保温中间层及防水内层,所述箱本体的容纳空间内固设有若干个装有蓄冷剂的密封的蓄冷剂包。"

    # 示例现有技术
    prior_art = [
        PriorArtReference(
            reference_id="CN201020012345.6",
            reference_type="patent",
            publication_date=datetime(2010, 12, 9),
            content="一种硬质冷藏箱,包括箱本体和盖体,箱本体包括内外两层防水尼龙面料层及保温中间层。",
            is_conflict_application=True,
        )
    ]

    # 新颖性分析
    novelty_result = await engine.analyze_novelty(claim_text, prior_art)
    print(f"新颖性分析结果:{novelty_result.conclusion.value}")
    print(f"推理过程:{novelty_result.reasoning}")

    # 创造性分析
    inventiveness_result = await engine.analyze_inventiveness(claim_text, prior_art)
    print(f"\n创造性分析结果:{inventiveness_result.conclusion.value}")
    print(f"推理过程:{inventiveness_result.reasoning}")


# 入口点: @async_main装饰器已添加到main函数
