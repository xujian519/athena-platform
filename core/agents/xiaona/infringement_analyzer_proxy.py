"""
侵权分析智能体

专注于专利侵权分析，提供全面的侵权风险评估。
"""

from typing import Any, Dict, List, Optional
import logging
from core.agents.xiaona.base_component import BaseXiaonaComponent

logger = logging.getLogger(__name__)


class InfringementAnalyzerProxy(BaseXiaonaComponent):
    """
    侵权分析智能体

    核心能力：
    - 权利要求解释
    - 特征比对（全面原则、等同原则）
    - 侵权判定（直接侵权、间接侵权）
    - 风险评估和规避建议
    """

    def _initialize(self) -> None:
        """初始化侵权分析智能体"""
        self._register_capabilities([
            {
                "name": "claim_interpretation",
                "description": "权利要求解释",
                "input_types": ["专利文件"],
                "output_types": ["权利要求解释"],
                "estimated_time": 15.0,
            },
            {
                "name": "feature_comparison",
                "description": "特征比对",
                "input_types": ["权利要求", "产品描述"],
                "output_types": ["比对结果"],
                "estimated_time": 20.0,
            },
            {
                "name": "infringement_determination",
                "description": "侵权判定",
                "input_types": ["比对结果"],
                "output_types": ["侵权结论"],
                "estimated_time": 25.0,
            },
            {
                "name": "risk_assessment",
                "description": "风险评估",
                "input_types": ["侵权结果"],
                "output_types": ["风险报告"],
                "estimated_time": 10.0,
            },
        ])

    async def analyze_infringement(
        self,
        patent_data: Dict[str, Any],
        product_data: Dict[str, Any],
        analysis_mode: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        完整侵权分析流程

        Args:
            patent_data: 目标专利数据
            product_data: 被诉产品/方法数据
            analysis_mode: 分析模式（comprehensive/quick）

        Returns:
            完整侵权分析报告
        """
        # 1. 解释权利要求
        claims = await self.interpret_claims(patent_data)

        # 2. 特征比对
        comparisons = await self.compare_features(
            claims.get("claims", []),
            product_data
        )

        # 3. 侵权判定
        infringement = await self.determine_infringement(
            comparisons.get("comparisons", [])
        )

        # 4. 风险评估
        risk = await self.assess_risk(
            infringement,
            patent_data.get("estimated_value", 0)
        )

        # 5. 生成报告
        return {
            "patent_id": patent_data.get("patent_id", "未知"),
            "product": product_data.get("product_name", "未知"),
            "analysis_mode": analysis_mode,
            "claims_analysis": claims,
            "feature_comparison": comparisons,
            "infringement_conclusion": infringement,
            "risk_assessment": risk,
            "generated_at": self._get_timestamp(),
        }

    async def interpret_claims(
        self,
        patent_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解释权利要求，确定保护范围

        Args:
            patent_data: 专利数据

        Returns:
            权利要求解释结果
        """
        patent_id = patent_data.get("patent_id", "未知")
        claims_text = patent_data.get("claims", "")

        # 提取权利要求（简化版）
        claims_list = self._parse_claims(claims_text)

        # 分析每个权利要求
        interpreted_claims = []
        for claim in claims_list:
            interpreted = {
                "claim_number": claim.get("number", 0),
                "type": claim.get("type", "independent"),
                "text": claim.get("text", ""),
                "essential_features": self._extract_essential_features(
                    claim.get("text", "")
                ),
                "protection_scope": self._determine_protection_scope(
                    claim.get("text", "")
                ),
            }
            interpreted_claims.append(interpreted)

        return {
            "patent_id": patent_id,
            "total_claims": len(interpreted_claims),
            "independent_claims": len([c for c in interpreted_claims if c["type"] == "independent"]),
            "dependent_claims": len([c for c in interpreted_claims if c["type"] == "dependent"]),
            "claims": interpreted_claims,
        }

    async def compare_features(
        self,
        claims: List[Dict[str, Any]],
        product_description: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        将产品/方法与权利要求比对

        Args:
            claims: 权利要求列表
            product_description: 产品描述

        Returns:
            特征比对结果
        """
        product_features = product_description.get("features", {})
        product_name = product_description.get("product_name", "未知产品")

        comparisons = []
        for claim in claims:
            claim_number = claim["claim_number"]
            essential_features = claim.get("essential_features", [])

            # 全面原则比对（字面侵权）
            covered_features = []
            missing_features = []

            for feature in essential_features:
                if self._feature_covered(feature, product_features):
                    covered_features.append(feature)
                else:
                    missing_features.append(feature)

            # 等同原则比对
            equivalent_features = self._find_equivalent_features(
                missing_features,
                product_features
            )

            # 判定侵权类型
            if len(missing_features) == 0:
                infringement_type = "literal_infringement"
            elif len(equivalent_features) > 0:
                infringement_type = "equivalent_infringement"
            else:
                infringement_type = "no_infringement"

            comparison = {
                "claim_number": claim_number,
                "covered_features": covered_features,
                "missing_features": missing_features,
                "equivalent_features": equivalent_features,
                "infringement_type": infringement_type,
                "coverage_ratio": len(covered_features) / len(essential_features) if essential_features else 0,
            }
            comparisons.append(comparison)

        return {
            "product": product_name,
            "comparisons": comparisons,
            "summary": self._generate_comparison_summary(comparisons),
        }

    async def determine_infringement(
        self,
        comparisons: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        判定是否侵权（全面原则、等同原则）

        Args:
            comparisons: 特征比对结果

        Returns:
            侵权判定结论
        """
        # 统计侵权情况
        literal_infringed = []
        equivalent_infringed = []
        non_infringed = []

        for comp in comparisons:
            claim_number = comp["claim_number"]
            infringement_type = comp["infringement_type"]

            if infringement_type == "literal_infringement":
                literal_infringed.append(claim_number)
            elif infringement_type == "equivalent_infringement":
                equivalent_infringed.append(claim_number)
            else:
                non_infringed.append(claim_number)

        # 判定侵权结论
        total_infringed = len(literal_infringed) + len(equivalent_infringed)
        total_claims = len(comparisons)

        if total_infringed == 0:
            conclusion = "不构成侵权"
            confidence = 0.9
        elif len(literal_infringed) > 0:
            conclusion = "构成字面侵权"
            confidence = 0.85 + (0.1 * len(literal_infringed) / total_claims)
        else:
            conclusion = "构成等同侵权"
            confidence = 0.7 + (0.1 * len(equivalent_infringed) / total_claims)

        # 限制置信度范围
        confidence = min(max(confidence, 0.5), 0.95)

        return {
            "infringement_conclusion": conclusion,
            "infringed_claims": {
                "literal": literal_infringed,
                "equivalent": equivalent_infringed,
                "total": total_infringed,
            },
            "non_infringed_claims": non_infringed,
            "legal_basis": self._get_legal_basis(literal_infringed, equivalent_infringed),
            "confidence": confidence,
            "reasoning": self._generate_infringement_reasoning(comparisons),
        }

    async def assess_risk(
        self,
        infringement_result: Dict[str, Any],
        claim_value: float
    ) -> Dict[str, Any]:
        """
        评估侵权风险和赔偿

        Args:
            infringement_result: 侵权判定结果
            claim_value: 专利价值/索赔金额

        Returns:
            风险评估报告
        """
        conclusion = infringement_result.get("infringement_conclusion", "")
        confidence = infringement_result.get("confidence", 0)
        total_infringed = infringement_result.get("infringed_claims", {}).get("total", 0)

        # 风险等级判定
        if "不构成侵权" in conclusion:
            risk_level = "low"
            estimated_damages = 0
            injunctive_relief_risk = 0.1
        elif "字面侵权" in conclusion and confidence > 0.8:
            risk_level = "high"
            estimated_damages = claim_value * 0.5  # 估算为专利价值的50%
            injunctive_relief_risk = 0.9
        elif "等同侵权" in conclusion:
            risk_level = "medium"
            estimated_damages = claim_value * 0.3  # 估算为专利价值的30%
            injunctive_relief_risk = 0.6
        else:
            risk_level = "medium"
            estimated_damages = claim_value * 0.2
            injunctive_relief_risk = 0.5

        # 规避设计建议
        design_around_suggestions = []
        if risk_level in ["high", "medium"]:
            design_around_suggestions = [
                "修改被控侵权产品的技术特征，使其不完全落入权利要求保护范围",
                "通过技术改进，实现与专利不同的技术方案",
                "寻求专利无效宣告或专利权评价",
                "评估许可谈判的可行性",
            ]

        return {
            "risk_level": risk_level,
            "estimated_damages": int(estimated_damages),
            "injunctive_relief_risk": injunctive_relief_risk,
            "litigation_risk": "high" if risk_level == "high" else "medium",
            "design_around_suggestions": design_around_suggestions,
            "recommended_actions": self._generate_action_recommendations(risk_level),
        }

    # 辅助方法

    def _parse_claims(self, claims_text: str) -> List[Dict[str, Any]]:
        """解析权利要求文本"""
        # 简化版解析，实际应该使用更复杂的NLP
        claims = []
        lines = claims_text.split("\n")

        current_claim = None
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            if line.startswith(str(len(claims) + 1)) + "." or line.startswith("权利要求" + str(len(claims) + 1)):
                # 新权利要求
                if current_claim:
                    claims.append(current_claim)

                current_claim = {
                    "number": len(claims) + 1,
                    "type": "independent" if len(claims) == 0 else "dependent",
                    "text": line,
                }
            elif current_claim:
                current_claim["text"] += " " + line

        if current_claim:
            claims.append(current_claim)

        return claims if claims else [
            {"number": 1, "type": "independent", "text": claims_text}
        ]

    def _extract_essential_features(
        self,
        claim_text: str
    ) -> List[str]:
        """提取必要技术特征"""
        # 简化版特征提取
        features = []

        # 查找常见特征关键词
        keywords = ["包括", "包含", "具有", "设置", "配置"]
        for keyword in keywords:
            if keyword in claim_text:
                # 提取包含关键词的句子
                sentences = claim_text.split("，")
                for sentence in sentences:
                    if keyword in sentence:
                        features.append(sentence.strip())

        return features if features else ["特征1", "特征2", "特征3"]

    def _determine_protection_scope(self, claim_text: str) -> str:
        """确定保护范围"""
        # 简化版保护范围判定
        if "所述" in claim_text or "其特征在于" in claim_text:
            return "中等"
        elif len(claim_text) > 200:
            return "较宽"
        else:
            return "较窄"

    def _feature_covered(
        self,
        feature: str,
        product_features: Dict[str, Any]
    ) -> bool:
        """判断特征是否被覆盖"""
        # 简化版判断
        feature_lower = feature.lower()

        # 检查产品特征中是否包含
        for key, value in product_features.items():
            if isinstance(value, str):
                if feature_lower in value.lower():
                    return True
            elif isinstance(value, list):
                for item in value:
                    if feature_lower in str(item).lower():
                        return True

        return False

    def _find_equivalent_features(
        self,
        missing_features: List[str],
        product_features: Dict[str, Any]
    ) -> List[str]:
        """查找等同特征"""
        # 简化版等同特征判定
        equivalent = []

        for feature in missing_features:
            # 检查是否有相似的特征
            for key, value in product_features.items():
                if isinstance(value, str) and self._is_equivalent(feature, value):
                    equivalent.append(f"{feature} ≈ {value}")
                    break

        return equivalent

    def _is_equivalent(self, feature1: str, feature2: str) -> bool:
        """判断两个特征是否等同"""
        # 简化版等同判定
        # 实际应该使用语义相似度
        synonyms_map = {
            "包括": "包含",
            "设置": "配置",
            "连接": "联接",
        }

        for word, synonym in synonyms_map.items():
            if word in feature1 and synonym in feature2:
                return True
            if synonym in feature1 and word in feature2:
                return True

        return False

    def _generate_comparison_summary(
        self,
        comparisons: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成比对摘要"""
        total = len(comparisons)
        literal = len([c for c in comparisons if c["infringement_type"] == "literal_infringement"])
        equivalent = len([c for c in comparisons if c["infringement_type"] == "equivalent_infringement"])
        no_infringement = len([c for c in comparisons if c["infringement_type"] == "no_infringement"])

        avg_coverage = sum(c["coverage_ratio"] for c in comparisons) / total if total > 0 else 0

        return {
            "total_claims_compared": total,
            "literal_infringement": literal,
            "equivalent_infringement": equivalent,
            "no_infringement": no_infringement,
            "average_coverage_ratio": avg_coverage,
        }

    def _get_legal_basis(
        self,
        literal_claims: List[int],
        equivalent_claims: List[int]
    ) -> str:
        """获取法律依据"""
        if literal_claims and equivalent_claims:
            return "专利法第11条（全面原则、等同原则）"
        elif literal_claims:
            return "专利法第11条（全面原则）"
        elif equivalent_claims:
            return "专利法第11条（等同原则）"
        else:
            return "不适用"

    def _generate_infringement_reasoning(
        self,
        comparisons: List[Dict[str, Any]]
    ) -> str:
        """生成侵权判定推理"""
        reasoning_parts = []

        for comp in comparisons:
            claim_num = comp["claim_number"]
            infringement_type = comp["infringement_type"]
            covered = len(comp["covered_features"])
            total = covered + len(comp["missing_features"])

            if infringement_type == "literal_infringement":
                reasoning_parts.append(
                    f"权利要求{claim_num}：{covered}/{total}个特征被覆盖，构成字面侵权"
                )
            elif infringement_type == "equivalent_infringement":
                reasoning_parts.append(
                    f"权利要求{claim_num}：部分特征等同，构成等同侵权"
                )
            else:
                reasoning_parts.append(
                    f"权利要求{claim_num}：特征不匹配，不构成侵权"
                )

        return "；".join(reasoning_parts)

    def _generate_action_recommendations(
        self,
        risk_level: str
    ) -> List[str]:
        """生成行动建议"""
        if risk_level == "high":
            return [
                "立即停止涉嫌侵权行为",
                "寻求专业律师意见",
                "考虑与专利权人协商许可",
                "评估无效宣告的可能性",
            ]
        elif risk_level == "medium":
            return [
                "继续监控市场动态",
                "准备规避设计方案",
                "收集不侵权证据",
                "评估许可谈判的可行性",
            ]
        else:
            return [
                "继续现有业务",
                "定期更新技术方案",
                "关注专利法律动态",
            ]

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
