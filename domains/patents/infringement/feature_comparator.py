#!/usr/bin/env python3
"""
特征对比器

对比权利要求特征与产品特征，建立对应关系。
"""
import logging
from dataclasses import dataclass, field
from typing import Any

try:
    from .claim_parser import ParsedClaim, ParsedFeature
    from .product_analyzer import AnalyzedProduct, ProductFeature
except ImportError:
    from core.patents.infringement.claim_parser import ParsedClaim, ParsedFeature
    from core.patents.infringement.product_analyzer import AnalyzedProduct, ProductFeature

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FeatureMapping:
    """特征映射关系"""
    claim_feature_id: str
    claim_feature_text: str
    product_feature_id: str
    product_feature_text: str
    correspondence_type: str  # exact, equivalent, missing, different
    confidence: float  # 映射置信度
    reasoning: str = ""  # 映射理由

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "claim_feature_id": self.claim_feature_id,
            "claim_feature_text": self.claim_feature_text,
            "product_feature_id": self.product_feature_id,
            "product_feature_text": self.product_feature_text,
            "correspondence_type": self.correspondence_type,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }


@dataclass
class FeatureComparison:
    """特征对比结果"""
    claim_number: int
    total_features: int
    mapped_features: int
    missing_features: int
    different_features: int
    mappings: list[FeatureMapping]
    coverage_ratio: float  # 覆盖率
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "claim_number": self.claim_number,
            "total_features": self.total_features,
            "mapped_features": self.mapped_features,
            "missing_features": self.missing_features,
            "different_features": self.different_features,
            "mappings": [m.to_dict() for m in self.mappings],
            "coverage_ratio": self.coverage_ratio,
            "metadata": self.metadata
        }


class FeatureComparator:
    """特征对比器"""

    def __init__(self):
        """初始化对比器"""
        logger.info("✅ 特征对比器初始化成功")

    def compare(
        self,
        claim: ParsedClaim,
        product: AnalyzedProduct
    ) -> FeatureComparison:
        """
        对比权利要求与产品特征

        Args:
            claim: 解析的权利要求
            product: 分析的产品

        Returns:
            FeatureComparison对象
        """
        logger.info(f"🔍 对比权利要求 {claim.claim_number} 与产品 {product.product_name}")

        mappings = []

        # 逐个特征对比
        for claim_feature in claim.features:
            mapping = self._find_best_match(claim_feature, product.features)
            mappings.append(mapping)

        # 统计结果
        total = len(mappings)
        mapped = sum(1 for m in mappings if m.correspondence_type in ['exact', 'equivalent'])
        missing = sum(1 for m in mappings if m.correspondence_type == 'missing')
        different = sum(1 for m in mappings if m.correspondence_type == 'different')

        coverage_ratio = mapped / total if total > 0 else 0.0

        comparison = FeatureComparison(
            claim_number=claim.claim_number,
            total_features=total,
            mapped_features=mapped,
            missing_features=missing,
            different_features=different,
            mappings=mappings,
            coverage_ratio=coverage_ratio
        )

        logger.info("✅ 特征对比完成")
        logger.info(f"   总特征数: {total}")
        logger.info(f"   已覆盖: {mapped} ({coverage_ratio:.1%})")
        logger.info(f"   缺失: {missing}")
        logger.info(f"   差异: {different}")

        return comparison

    def compare_multiple_claims(
        self,
        claims: list[ParsedClaim],
        product: AnalyzedProduct
    ) -> list[FeatureComparison]:
        """
        对比多条权利要求与产品

        Args:
            claims: 权利要求列表
            product: 产品

        Returns:
            FeatureComparison列表
        """
        logger.info(f"🔍 批量对比 {len(claims)} 条权利要求")

        comparisons = []
        for claim in claims:
            try:
                comparison = self.compare(claim, product)
                comparisons.append(comparison)
            except Exception as e:
                logger.error(f"❌ 对比权利要求 {claim.claim_number} 失败: {e}")
                continue

        return comparisons

    def _find_best_match(
        self,
        claim_feature: ParsedFeature,
        product_features: list[ProductFeature]
    ) -> FeatureMapping:
        """
        为权利要求特征找到最佳匹配的产品特征

        Args:
            claim_feature: 权利要求特征
            product_features: 产品特征列表

        Returns:
            FeatureMapping对象
        """
        best_match = None
        best_score = 0.0

        for product_feature in product_features:
            score = self._calculate_similarity(claim_feature, product_feature)

            if score > best_score:
                best_score = score
                best_match = product_feature

        # 判定对应关系类型
        if best_score >= 0.9:
            correspondence_type = "exact"
            confidence = best_score
            reasoning = "特征完全一致"
        elif best_score >= 0.7:
            correspondence_type = "equivalent"
            confidence = best_score
            reasoning = "特征等同（功能、手段、效果基本相同）"
        elif best_score >= 0.5:
            correspondence_type = "different"
            confidence = best_score
            reasoning = "特征存在差异"
        else:
            correspondence_type = "missing"
            confidence = best_score
            best_match = None
            reasoning = "产品未包含该特征"

        mapping = FeatureMapping(
            claim_feature_id=claim_feature.id,
            claim_feature_text=claim_feature.description,
            product_feature_id=best_match.id if best_match else "",
            product_feature_text=best_match.description if best_match else "未找到",
            correspondence_type=correspondence_type,
            confidence=confidence,
            reasoning=reasoning
        )

        return mapping

    def _calculate_similarity(
        self,
        claim_feature: ParsedFeature,
        product_feature: ProductFeature
    ) -> float:
        """
        计算特征相似度

        Args:
            claim_feature: 权利要求特征
            product_feature: 产品特征

        Returns:
            相似度分数 (0-1)
        """
        # 简单的基于关键词重叠的相似度计算
        claim_text = claim_feature.description.lower()
        product_text = product_feature.description.lower()

        # 分词
        claim_words = set(claim_text)
        product_words = set(product_text)

        # 计算交集
        intersection = claim_words & product_words
        union = claim_words | product_words

        if not union:
            return 0.0

        # Jaccard相似度
        jaccard = len(intersection) / len(union)

        # 检查关键组件是否相同
        component_bonus = 0.0
        if claim_feature.component and claim_feature.component in product_text:
            component_bonus = 0.3

        # 综合相似度
        similarity = jaccard * 0.7 + component_bonus

        return min(similarity, 1.0)

    def generate_comparison_table(
        self,
        comparisons: list[FeatureComparison]
    ) -> str:
        """
        生成特征对比表（Markdown格式）

        Args:
            comparisons: 对比结果列表

        Returns:
            Markdown格式的对比表
        """
        lines = []
        lines.append("# 权利要求与产品特征对比表\n")

        for comparison in comparisons:
            lines.append(f"## 权利要求 {comparison.claim_number}\n")
            lines.append(f"- 总特征数: {comparison.total_features}")
            lines.append(f"- 已覆盖: {comparison.mapped_features} ({comparison.coverage_ratio:.1%})")
            lines.append(f"- 缺失: {comparison.missing_features}")
            lines.append(f"- 差异: {comparison.different_features}\n")

            lines.append("| 权利要求特征 | 产品特征 | 对应关系 | 置信度 |")
            lines.append("|-------------|---------|---------|--------|")

            for mapping in comparison.mappings:
                claim_short = mapping.claim_feature_text[:40] + "..." if len(mapping.claim_feature_text) > 40 else mapping.claim_feature_text
                product_short = mapping.product_feature_text[:40] + "..." if len(mapping.product_feature_text) > 40 else mapping.product_feature_text

                # 对应关系符号
                if mapping.correspondence_type == "exact":
                    symbol = "✓ 完全一致"
                elif mapping.correspondence_type == "equivalent":
                    symbol = "≈ 等同"
                elif mapping.correspondence_type == "different":
                    symbol = "× 差异"
                else:
                    symbol = "✗ 缺失"

                lines.append(f"| {claim_short} | {product_short} | {symbol} | {mapping.confidence:.2%} |")

            lines.append("\n")

        return "\n".join(lines)
