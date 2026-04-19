#!/usr/bin/env python3
"""
法律规则引擎 - Legal Rule Engine
Legal Rule Engine for Patent Law

将形式化的法律规则转换为可执行推理

⚠️ 重点:创造性评估(三步法)
📋 功能:
1. ✅ 创造性"三步法"推理(主要功能)
2. 🔄 从无效决定提取推理模式(进行中)
3. ⏳ 新颖性评估规则(暂缓实现)
4. ⏳ 审查决策树(计划中)
5. ⏳ 法律规则形式化(计划中)

版本: 1.0.0
创建时间: 2026-01-23
更新时间: 2026-01-23
"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ============ 数据模型 ============


class NoveltyLevel(Enum):
    """新颖性等级"""

    NOVELTY_NONE = "无新颖性"  # 与现有技术完全相同
    NOVELTY_LOW = "低新颖性"  # 仅简单替换或组合
    NOVELTY_MEDIUM = "中等新颖性"  # 部分区别特征
    NOVELTY_HIGH = "高新颖性"  # 实质性区别特征


class CreativityLevel(Enum):
    """创造性等级"""

    CREATIVITY_NONE = "无创造性"  # 显而易见
    CREATIVITY_LOW = "低创造性"  # 有限创造性
    CREATIVITY_MEDIUM = "中等创造性"  # 有实质性特点
    CREATIVITY_HIGH = "高创造性"  # 突出实质性特点


@dataclass
class DistinguishingFeature:
    """区别技术特征"""

    feature: str
    source_claim: str
    prior_art_references: list[str] = field(default_factory=list)
    explanation: str = ""


@dataclass
class TechnicalProblem:
    """技术问题"""

    problem: str
    distinguishing_features: list[DistinguishingFeature] = field(default_factory=list)
    explanation: str = ""


@dataclass
class TechnicalHint:
    """技术启示"""

    has_hint: bool
    hint_sources: list[str] = field(default_factory=list)
    explanation: str = ""
    confidence: float = 0.0


@dataclass
class NoveltyReport:
    """新颖性评估报告"""

    novelty_level: NoveltyLevel
    confidence: float
    identical_features: list[str] = field(default_factory=list)
    equivalent_features: list[str] = field(default_factory=list)
    distinguishing_features: list[DistinguishingFeature] = field(default_factory=list)
    problematic_features: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class CreativityAssessment:
    """创造性评估报告"""

    creativity_level: CreativityLevel
    confidence: float
    step1_distinguishing: list[DistinguishingFeature]
    step2_problem: TechnicalProblem | None
    step3_hint: TechnicalHint | None
    reasoning_chain: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


# ============ 核心引擎 ============


class LegalRuleEngine:
    """
    法律规则引擎

    将形式化的法律规则转换为可执行推理
    """

    # 专利法第22条:新颖性判断规则
    NOVELTY_RULES = {
        "identical_prohibition": "新颖性,是指该发明或者实用新型不属于现有技术",
        "prior_art_definition": "现有技术是指申请日以前在国内外为公众所知的技术",
        "identical_judgment": "权利要求与现有技术完全相同的,不具备新颖性",
    }

    # 创造性判断规则(审查指南第二部分第四章 6.3)
    CREATIVITY_RULES = {
        "three_step_method": "三步法:确定区别技术特征→确定技术问题→判断技术启示",
        "obviousness": "对于本领域技术人员来说,是显而易见的",
        "technical_hint": "现有技术中是否给出结合启示",
    }

    def __init__(self):
        """初始化规则引擎"""
        logger.info("✅ 法律规则引擎初始化成功")

    def evaluate_novelty(
        self, claims: dict[str, Any], prior_art: list[dict[str, Any]]
    ) -> NoveltyReport:
        """
        新颖性评估

        基于专利法第22条和审查指南第二部分第三章

        Args:
            claims: 权利要求信息
                {
                    "independent_claims": ["..."],
                    "dependent_claims": ["..."],
                    "technical_field": "...",
                    "description": "..."
                }
            prior_art: 现有技术列表

        Returns:
            NoveltyReport: 新颖性评估报告
        """
        logger.info("=" * 60)
        logger.info("🔍 开始新颖性评估")
        logger.info("=" * 60)

        # 步骤1:完全相同要素对比
        identical_features = self._find_identical_features(claims, prior_art)
        logger.info(f"📌 相同特征数量: {len(identical_features)}")

        # 步骤2:等同特征判断
        equivalent_features = self._find_equivalent_features(claims, prior_art)
        logger.info(f"📌 等同特征数量: {len(equivalent_features)}")

        # 步骤3:技术方案整体对比
        overall_similarity = self._compare_overall_solution(claims, prior_art)
        logger.info(f"📌 整体相似度: {overall_similarity:.2%}")

        # 步骤4:识别区别特征
        distinguishing_features = self._identify_distinguishing_features(
            claims, prior_art, identical_features, equivalent_features
        )
        logger.info(f"📌 区别特征数量: {len(distinguishing_features)}")

        # 生成新颖性报告
        report = self._generate_novelty_report(
            identical_features, equivalent_features, distinguishing_features, overall_similarity
        )

        logger.info("=" * 60)
        logger.info(f"🎯 新颖性评估完成: {report.novelty_level.value}")
        logger.info(f"📊 置信度: {report.confidence:.2%}")
        logger.info("=" * 60)

        return report

    def three_step_creativity_analysis(
        self,
        distinguishing_features: list[DistinguishingFeature],
        prior_art: list[dict[str, Any]],        claims: dict[str, Any],    ) -> CreativityAssessment:
        """
        三步法创造性分析

        基于审查指南第二部分第四章 6.3

        Args:
            distinguishing_features: 区别技术特征列表
            prior_art: 现有技术
            claims: 权利要求信息

        Returns:
            CreativityAssessment: 创造性评估报告
        """
        logger.info("=" * 60)
        logger.info("🔍 开始三步法创造性分析")
        logger.info("=" * 60)

        reasoning_chain = []

        # 第一步:确定区别技术特征
        logger.info("📌 第一步:确定区别技术特征")
        step1_result = self._step1_identify_distinguishing(distinguishing_features, prior_art)
        reasoning_chain.append(f"第一步:识别出{len(step1_result)}个区别特征")

        # 第二步:确定实际解决的技术问题
        logger.info("📌 第二步:确定技术问题")
        step2_result = self._step2_derive_problem(step1_result, claims)
        reasoning_chain.append(f"第二步:确定技术问题 - {step2_result.problem}")

        # 第三步:判断现有技术是否给出技术启示
        logger.info("📌 第三步:判断技术启示")
        step3_result = self._step3_evaluate_hint(step2_result, prior_art)
        reasoning_chain.append(
            f"第三步:技术启示判断 - {'有技术启示' if step3_result.has_hint else '无技术启示'}"
        )

        # 综合评估创造性
        creativity_level = self._calculate_creativity(step1_result, step2_result, step3_result)

        # 生成建议
        suggestions = self._generate_creativity_suggestions(
            step1_result, step2_result, step3_result
        )

        logger.info("=" * 60)
        logger.info(f"🎯 创造性评估完成: {creativity_level.value}")
        logger.info("=" * 60)

        return CreativityAssessment(
            creativity_level=creativity_level,
            confidence=self._calculate_confidence(step1_result, step2_result, step3_result),
            step1_distinguishing=step1_result,
            step2_problem=step2_result,
            step3_hint=step3_result,
            reasoning_chain=reasoning_chain,
            suggestions=suggestions,
        )

    # ============ 私有方法:新颖性评估 ============

    def _find_identical_features(
        self, claims: dict[str, Any], prior_art: list[dict[str, Any]]
    ) -> list[str]:
        """查找完全相同的特征"""
        identical = []

        # 提取权利要求中的技术特征关键词
        claim_features = self._extract_feature_keywords(claims)

        # 从现有技术中提取特征
        for pa in prior_art:
            pa_features = self._extract_feature_keywords(
                {
                    "description": pa.get("content", pa.get("description", "")),
                    "title": pa.get("title", ""),
                }
            )

            # 查找完全匹配
            for claim_feature in claim_features:
                for pa_feature in pa_features:
                    if self._is_identical_feature(claim_feature, pa_feature):
                        identical.append(f"{claim_feature} (来自:{pa.get('title', '未知')})")

        return list(set(identical))

    def _find_equivalent_features(
        self, claims: dict[str, Any], prior_art: list[dict[str, Any]]
    ) -> list[str]:
        """查找等同特征"""
        equivalent = []

        # 等同特征映射表(示例)
        equivalences = {
            "连接": ["联接", "固定", "安装"],
            "设置": ["配置", "布置", "安置"],
            "包括": ["包含", "具有", "设有"],
            "为": ["是", "构成"],
        }

        claim_features = self._extract_feature_keywords(claims)

        for pa in prior_art:
            pa_features = self._extract_feature_keywords(
                {
                    "description": pa.get("content", pa.get("description", "")),
                    "title": pa.get("title", ""),
                }
            )

            # 查找等同特征
            for claim_feature in claim_features:
                for pa_feature in pa_features:
                    if self._is_equivalent_feature(claim_feature, pa_feature, equivalences):
                        equivalent.append(
                            f"{claim_feature} ≈ {pa_feature} (来自:{pa.get('title', '未知')})"
                        )

        return list(set(equivalent))

    def _compare_overall_solution(
        self, claims: dict[str, Any], prior_art: list[dict[str, Any]]
    ) -> float:
        """技术方案整体对比"""
        # 简化实现:使用向量相似度
        # 实际应该有更复杂的整体方案对比逻辑

        similarities = []
        claim_text = claims.get("description", "")
        if not claim_text:
            claim_text = " ".join(claims.get("independent_claims", []))

        for pa in prior_art:
            pa_text = pa.get("content", pa.get("description", ""))
            if pa_text:
                # 简单的文本相似度计算
                similarity = self._text_similarity(claim_text, pa_text)
                similarities.append(similarity)

        return max(similarities) if similarities else 0.0

    def _identify_distinguishing_features(
        self,
        claims: dict[str, Any],        prior_art: list[dict[str, Any]],        identical: list[str],
        equivalent: list[str],
    ) -> list[DistinguishingFeature]:
        """识别区别技术特征"""
        # 提取权利要求中的所有技术特征
        claim_features = self._extract_feature_keywords(claims)

        # 移除相同和等同特征
        distinguishing = [
            feat
            for feat in claim_features
            if not any(
                self._is_feature_mentioned(feat, known) or self._is_feature_mentioned(known, feat)
                for known in identical + equivalent
            )
        ]

        return [
            DistinguishingFeature(
                feature=feat, source_claim="权利要求", explanation="该特征在现有技术中未发现"
            )
            for feat in distinguishing
        ]

    def _generate_novelty_report(
        self,
        identical: list[str],
        equivalent: list[str],
        distinguishing: list[DistinguishingFeature],
        similarity: float,
    ) -> NoveltyReport:
        """生成新颖性报告"""
        # 决策树
        if len(identical) > 0:
            return NoveltyReport(
                novelty_level=NoveltyLevel.NOVELTY_NONE,
                confidence=0.95,
                identical_features=identical,
                reason=f"权利要求与现有技术存在{len(identical)}个完全相同特征",
            )

        if len(equivalent) > 3:
            return NoveltyReport(
                novelty_level=NoveltyLevel.NOVELTY_LOW,
                confidence=0.85,
                equivalent_features=equivalent,
                reason=f"权利要求与现有技术存在{len(equivalent)}个等同特征,属于简单替换",
            )

        if similarity > 0.8:
            return NoveltyReport(
                novelty_level=NoveltyLevel.NOVELTY_LOW,
                confidence=0.80,
                reason=f"技术方案整体与现有技术相似度{similarity:.1%}",
            )

        if len(distinguishing) == 0:
            return NoveltyReport(
                novelty_level=NoveltyLevel.NOVELTY_LOW,
                confidence=0.60,
                reason="未发现明显的区别特征",
            )

        if len(distinguishing) >= 3:
            return NoveltyReport(
                novelty_level=NoveltyLevel.NOVELTY_HIGH,
                confidence=0.80,
                distinguishing_features=distinguishing,
                reason=f"存在{len(distinguishing)}个实质性区别特征",
            )

        return NoveltyReport(
            novelty_level=NoveltyLevel.NOVELTY_MEDIUM,
            confidence=0.70,
            distinguishing_features=distinguishing,
            reason=f"存在{len(distinguishing)}个区别特征,需要进一步分析",
        )

    # ============ 私有方法:创造性评估(三步法)===========

    def _step1_identify_distinguishing(
        self, distinguishing: list[DistinguishingFeature], prior_art: list[dict[str, Any]]
    ) -> list[DistinguishingFeature]:
        """第一步:确定区别技术特征"""
        # 分析每个区别特征的显著性
        significant_features = []

        for feature in distinguishing:
            # 判断特征是否显著
            if self._is_significant_feature(feature):
                significant_features.append(feature)

        return significant_features

    def _step2_derive_problem(
        self, distinguishing: list[DistinguishingFeature], claims: dict[str, Any]
    ) -> TechnicalProblem:
        """第二步:确定技术问题"""
        if not distinguishing:
            return TechnicalProblem(problem="无法确定技术问题:无明显区别特征")

        # 从区别特征中推导技术问题
        # 简化实现:使用规则模板

        # 智能推导技术问题
        problem = self._derive_problem_from_features(distinguishing)

        return TechnicalProblem(
            problem=problem,
            distinguishing_features=distinguishing,
            explanation=f"基于区别特征推导:{problem}",
        )

    def _step3_evaluate_hint(
        self, problem: TechnicalProblem, prior_art: list[dict[str, Any]]
    ) -> TechnicalHint:
        """第三步:判断技术启示"""
        # 查找是否现有技术给出技术启示
        hint_sources = []

        # 在现有技术中搜索相似的技术问题
        for pa in prior_art:
            if self._has_similar_problem(problem, pa):
                hint_sources.append(pa.get("title", "未知"))

        has_hint = len(hint_sources) > 0

        return TechnicalHint(
            has_hint=has_hint,
            hint_sources=hint_sources,
            explanation=(
                f"在{len(hint_sources)}份现有技术中发现相似技术问题"
                if has_hint
                else "现有技术未给出技术启示"
            ),
            confidence=0.7 if has_hint else 0.6,
        )

    # ============ 辅助方法 ============

    def _extract_feature_keywords(self, document: dict[str, Any]) -> list[str]:
        """提取技术特征关键词"""
        text = document.get("description", "")
        if not text:
            text = document.get("title", "")

        # 技术特征模式(示例)
        patterns = [
            r"包括([^。]{2,20})",
            r"设置([^。]{2,20})",
            r"连接([^。]{2,20})",
            r"配置([^。]{2,20})",
            r"([^。]{2,10})层",
            r"([^。]{2,10})模块",
        ]

        features = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            features.extend(matches)

        return list(set(features))

    def _is_identical_feature(self, feat1: str, feat2: str) -> bool:
        """判断是否为相同特征"""
        return feat1.strip() == feat2.strip()

    def _is_equivalent_feature(
        self, feat1: str, feat2: str, equivalences: dict[str, list[str]]
    ) -> bool:
        """判断是否为等同特征"""
        feat1 = feat1.strip()
        feat2 = feat2.strip()

        for key, values in equivalences.items():
            if feat1 == key and feat2 in values:
                return True
            if feat2 == key and feat1 in values:
                return True

        return False

    def _is_feature_mentioned(self, feature: str, known_item: str) -> bool:
        """判断特征是否在已知项中被提及"""
        return feature.lower() in known_item.lower() or known_item.lower() in feature.lower()

    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        # 简化实现:使用简单的词汇重叠度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _is_significant_feature(self, feature: DistinguishingFeature) -> bool:
        """判断特征是否显著"""
        # 简化实现:特征长度大于3个字符即为显著
        return len(feature.feature) > 3

    def _derive_problem_from_features(self, features: list[DistinguishingFeature]) -> str:
        """从区别特征推导技术问题"""
        # 智能推导:根据特征类型生成问题
        if not features:
            return "无明显技术问题"

        # 使用第一个区别特征生成问题
        primary_feature = features[0].feature
        return f"如何改进或优化{primary_feature}所涉及的技术方案"

    def _has_similar_problem(self, problem: TechnicalProblem, prior_art: dict) -> bool:
        """判断现有技术是否有相似技术问题"""
        # 简化实现:检查问题关键词是否在现有技术中出现
        problem_keywords = set(problem.problem.lower().split())

        pa_text = prior_art.get("content", prior_art.get("description", "")).lower()
        pa_words = set(pa_text.split())

        overlap = problem_keywords & pa_words
        return len(overlap) >= 2

    def _calculate_creativity(
        self, step1: list[DistinguishingFeature], step2: TechnicalProblem, step3: TechnicalHint
    ) -> CreativityLevel:
        """综合评估创造性"""
        score = 0

        # 第一步:区别特征数量(最多3分)
        score += min(len(step1) * 1.0, 3.0)

        # 第二步:技术问题明确性(最多2分)
        if step2 and step2.problem:
            score += 2.0

        # 第三步:无技术启示(最多5分)
        if step3 and not step3.has_hint:
            score += 5.0

        # 根据得分确定创造性等级
        if score >= 8:
            return CreativityLevel.CREATIVITY_HIGH
        elif score >= 5:
            return CreativityLevel.CREATIVITY_MEDIUM
        elif score >= 3:
            return CreativityLevel.CREATIVITY_LOW
        else:
            return CreativityLevel.CREATIVITY_NONE

    def _calculate_confidence(
        self, step1: list[DistinguishingFeature], step2: TechnicalProblem, step3: TechnicalHint
    ) -> float:
        """计算评估置信度"""
        confidence = 0.6  # 基础置信度

        # 根据区别特征数量调整
        if len(step1) >= 3:
            confidence += 0.1

        # 根据技术问题明确性调整
        if step2 and step2.problem:
            confidence += 0.1

        # 根据技术启示判断调整
        if step3:
            confidence += 0.2

        return min(confidence, 0.95)

    def _generate_creativity_suggestions(
        self, step1: list[DistinguishingFeature], step2: TechnicalProblem, step3: TechnicalHint
    ) -> list[str]:
        """生成创造性建议"""
        suggestions = []

        if not step1:
            suggestions.append("建议:进一步分析权利要求,识别更具体的区别技术特征")

        if step3 and step3.has_hint:
            suggestions.append("警告:现有技术可能给出技术启示,创造性可能不足")
            suggestions.append("建议:考虑引入额外的技术特征以增强创造性")

        if len(step1) > 0:
            suggestions.append(
                f"建议:强调以下区别特征的技术贡献:{', '.join([f.feature for f in step1[:3]])}"
            )

        suggestions.append("建议:结合具体技术领域分析技术启示的合理性")

        return suggestions


# ============ 主函数 ============


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="法律规则引擎测试")
    parser.add_argument("--test", action="store_true", help="运行测试")

    args = parser.parse_args()

    if args.test:
        test_rule_engine()


def test_rule_engine():
    """测试规则引擎"""
    print("🧪 测试法律规则引擎")

    engine = LegalRuleEngine()

    # 测试案例1:新颖性评估
    print("\n" + "=" * 60)
    print("测试案例1:新颖性评估")
    print("=" * 60)

    claims = {
        "independent_claims": ["一种数据处理方法,包括步骤A和步骤B", "其中步骤A包括数据预处理"],
        "description": "一种改进的数据处理方法,通过优化算法提高效率",
        "technical_field": "计算机技术",
    }

    prior_art = [
        {
            "title": "CN123456789A - 数据处理装置",
            "content": "一种数据处理装置,包括数据预处理单元和计算单元",
            "description": "用于提高数据处理效率",
        }
    ]

    novelty_report = engine.evaluate_novelty(claims, prior_art)
    print(f"新颖性等级: {novelty_report.novelty_level.value}")
    print(f"置信度: {novelty_report.confidence:.2%}")
    print(f"理由: {novelty_report.reason}")

    # 测试案例2:创造性评估
    print("\n" + "=" * 60)
    print("测试案例2:创造性评估")
    print("=" * 60)

    distinguishing = [DistinguishingFeature(feature="优化算法", source_claim="权利要求1")]

    creativity_assessment = engine.three_step_creativity_analysis(distinguishing, prior_art, claims)
    print(f"创造性等级: {creativity_assessment.creativity_level.value}")
    print(f"推理链: {' -> '.join(creativity_assessment.reasoning_chain)}")

    if creativity_assessment.suggestions:
        print("\n建议:")
        for suggestion in creativity_assessment.suggestions:
            print(f"  - {suggestion}")


if __name__ == "__main__":
    main()
