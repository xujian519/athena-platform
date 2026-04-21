#!/usr/bin/env python3
"""
诉讼策略分析器

分析专利诉讼案件，制定诉讼策略，评估胜诉概率和风险等级。
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LitigationType(Enum):
    """诉讼类型"""
    INFRINGEMENT = "patent_infringement"  # 侵权诉讼
    INVALIDATION = "patent_invalidation"  # 无效诉讼
    OWNERSHIP = "patent_ownership"  # 权属诉讼
    CONTRACT = "license_contract"  # 合同诉讼
    OTHER = "other"  # 其他诉讼


class LitigationRole(Enum):
    """诉讼角色"""
    PLAINTIFF = "plaintiff"  # 原告
    DEFENDANT = "defendant"  # 被告
    THIRD_PARTY = "third_party"  # 第三人


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"  # 低风险
    MEDIUM = "medium"  # 中等风险
    HIGH = "high"  # 高风险
    EXTREME = "extreme"  # 极高风险


@dataclass
class CaseAnalysis:
    """案件分析结果"""
    litigation_type: LitigationType
    litigation_role: LitigationRole
    case_strength: float  # 案件强度 (0-1)
    win_probability: float  # 胜诉概率 (0-1)
    risk_level: RiskLevel
    key_issues: List[str]  # 关键争议点
    strengths: List[str]  # 己方优势
    weaknesses: List[str]  # 己方劣势
    recommended_strategy: str  # 推荐策略
    estimated_duration: str  # 预计持续时间
    estimated_cost_range: tuple[float, float]  # 预计费用范围（万元）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "litigation_type": self.litigation_type.value,
            "litigation_role": self.litigation_role.value,
            "case_strength": self.case_strength,
            "win_probability": self.win_probability,
            "risk_level": self.risk_level.value,
            "key_issues": self.key_issues,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommended_strategy": self.recommended_strategy,
            "estimated_duration": self.estimated_duration,
            "estimated_cost_range": {
                "min": self.estimated_cost_range[0],
                "max": self.estimated_cost_range[1]
            }
        }


class LitigationStrategyAnalyzer:
    """诉讼策略分析器"""

    def __init__(self):
        """初始化分析器"""
        self.litigation_knowledge = self._load_litigation_knowledge()
        logger.info("✅ 诉讼策略分析器初始化成功")

    def _load_litigation_knowledge(self) -> Dict[str, Any]:
        """加载诉讼知识库"""
        return {
            "infringement": {
                "avg_duration": "12-24个月",
                "avg_cost": (50, 200),
                "key_factors": [
                    "专利有效性",
                    "侵权行为认定",
                    "损害赔偿计算",
                    "抗辩理由有效性"
                ]
            },
            "invalidation": {
                "avg_duration": "6-12个月",
                "avg_cost": (30, 100),
                "key_factors": [
                    "新颖性证据",
                    "创造性判断",
                    "说明书公开充分性",
                    "权利要求清楚性"
                ]
            },
            "ownership": {
                "avg_duration": "6-18个月",
                "avg_cost": (20, 80),
                "key_factors": [
                    "发明人资格",
                    "职务发明认定",
                    "合同约定",
                    "权属证据"
                ]
            },
            "contract": {
                "avg_duration": "6-12个月",
                "avg_cost": (20, 60),
                "key_factors": [
                    "合同有效性",
                    "违约事实",
                    "损失计算",
                    "合同解释"
                ]
            }
        }

    def analyze_case(
        self,
        patent_id: str,
        litigation_type: LitigationType,
        litigation_role: LitigationRole,
        case_info: Dict[str, Any],
        patent_info: Optional[Dict[str, Any]] = None
    ) -> CaseAnalysis:
        """
        分析诉讼案件

        Args:
            patent_id: 专利号
            litigation_type: 诉讼类型
            litigation_role: 诉讼角色
            case_info: 案件信息
            patent_info: 专利信息（可选）

        Returns:
            CaseAnalysis对象
        """
        logger.info(f"⚖️ 分析诉讼案件: {patent_id}, 类型={litigation_type.value}, 角色={litigation_role.value}")

        # 步骤1: 评估案件强度
        case_strength = self._assess_case_strength(
            litigation_type,
            litigation_role,
            case_info,
            patent_info
        )

        # 步骤2: 计算胜诉概率
        win_probability = self._calculate_win_probability(
            litigation_type,
            litigation_role,
            case_strength,
            case_info
        )

        # 步骤3: 确定风险等级
        risk_level = self._assess_risk_level(win_probability, case_info)

        # 步骤4: 识别关键争议点
        key_issues = self._identify_key_issues(
            litigation_type,
            case_info,
            patent_info
        )

        # 步骤5: 分析优势劣势
        strengths, weaknesses = self._analyze_strengths_weaknesses(
            litigation_type,
            litigation_role,
            case_info,
            patent_info
        )

        # 步骤6: 制定推荐策略
        recommended_strategy = self._generate_strategy(
            litigation_type,
            litigation_role,
            win_probability,
            key_issues
        )

        # 步骤7: 估算持续时间和费用
        estimated_duration = self.litigation_knowledge.get(
            litigation_type.value, {}
        ).get("avg_duration", "12-18个月")

        base_cost = self.litigation_knowledge.get(
            litigation_type.value, {}
        ).get("avg_cost", (30, 100))

        # 根据案件复杂度调整费用
        complexity_factor = case_info.get("complexity", 1.0)
        estimated_cost_range = (
            base_cost[0] * complexity_factor,
            base_cost[1] * complexity_factor
        )

        return CaseAnalysis(
            litigation_type=litigation_type,
            litigation_role=litigation_role,
            case_strength=case_strength,
            win_probability=win_probability,
            risk_level=risk_level,
            key_issues=key_issues,
            strengths=strengths,
            weaknesses=weaknesses,
            recommended_strategy=recommended_strategy,
            estimated_duration=estimated_duration,
            estimated_cost_range=estimated_cost_range
        )

    def _assess_case_strength(
        self,
        litigation_type: LitigationType,
        litigation_role: LitigationRole,
        case_info: Dict[str, Any],
        patent_info: Optional[Dict[str, Any]]
    ) -> float:
        """评估案件强度"""
        base_strength = 0.5

        # 根据诉讼角色调整
        if litigation_role == LitigationRole.PLAINTIFF:
            base_strength += 0.1  # 原告通常有举证优势
        elif litigation_role == LitigationRole.DEFENDANT:
            base_strength -= 0.05  # 被告需要抗辩

        # 根据证据质量调整
        evidence_quality = case_info.get("evidence_quality", 0.5)
        base_strength += (evidence_quality - 0.5) * 0.3

        # 根据专利稳定性调整（如果有专利信息）
        if patent_info:
            patent_validity = patent_info.get("validity_score", 0.5)
            if litigation_type == LitigationType.INFRINGEMENT:
                base_strength += (patent_validity - 0.5) * 0.2

        # 限制在0-1范围
        return max(0.0, min(1.0, base_strength))

    def _calculate_win_probability(
        self,
        litigation_type: LitigationType,
        litigation_role: LitigationRole,
        case_strength: float,
        case_info: Dict[str, Any]
    ) -> float:
        """计算胜诉概率"""
        base_probability = case_strength

        # 根据诉讼类型调整
        if litigation_type == LitigationType.INFRINGEMENT:
            # 侵权诉讼胜诉率通常较低
            base_probability *= 0.85
        elif litigation_type == LitigationType.INVALIDATION:
            # 无效诉讼成功率取决于证据
            evidence_strength = case_info.get("invalidation_evidence", 0.5)
            base_probability = (base_probability + evidence_strength) / 2

        # 根据复杂度调整
        complexity = case_info.get("complexity", 1.0)
        if complexity > 1.2:
            base_probability *= 0.9  # 复杂案件胜诉率降低

        return max(0.1, min(0.95, base_probability))

    def _assess_risk_level(
        self,
        win_probability: float,
        case_info: Dict[str, Any]
    ) -> RiskLevel:
        """评估风险等级"""
        if win_probability >= 0.7:
            return RiskLevel.LOW
        elif win_probability >= 0.5:
            return RiskLevel.MEDIUM
        elif win_probability >= 0.3:
            return RiskLevel.HIGH
        else:
            return RiskLevel.EXTREME

    def _identify_key_issues(
        self,
        litigation_type: LitigationType,
        case_info: Dict[str, Any],
        patent_info: Optional[Dict[str, Any]]
    ) -> List[str]:
        """识别关键争议点"""
        knowledge = self.litigation_knowledge.get(litigation_type.value, {})
        base_issues = knowledge.get("key_factors", [])

        # 根据案件信息定制
        custom_issues = []

        if litigation_type == LitigationType.INFRINGEMENT:
            if case_info.get("dispute_infringement", False):
                custom_issues.append("是否构成侵权")
            if case_info.get("dispute_validity", False):
                custom_issues.append("专利有效性争议")
            if case_info.get("dispute_damages", False):
                custom_issues.append("损害赔偿计算")

        elif litigation_type == LitigationType.INVALIDATION:
            if case_info.get("prior_art_found", False):
                custom_issues.append("现有技术对比")
            if case_info.get("lack_of_clarity", False):
                custom_issues.append("权利要求清楚性")

        return base_issues + custom_issues

    def _analyze_strengths_weaknesses(
        self,
        litigation_type: LitigationType,
        litigation_role: LitigationRole,
        case_info: Dict[str, Any],
        patent_info: Optional[Dict[str, Any]]
    ) -> tuple[List[str], List[str]]:
        """分析优势劣势"""
        strengths = []
        weaknesses = []

        if litigation_role == LitigationRole.PLAINTIFF:
            strengths.append("主动发起诉讼，掌握主动权")
            if case_info.get("strong_evidence", False):
                strengths.append("证据充分，证明力强")

            weaknesses.append("举证责任重")
            weaknesses.append("诉讼成本高")
        else:  # DEFENDANT
            strengths.append("可以提出无效宣告抗辩")
            strengths.append("可以主张现有技术抗辩")

            weaknesses.append("处于被动地位")
            weaknesses.append("需要应对原告诉请")

        # 根据专利信息调整
        if patent_info:
            if patent_info.get("validity_score", 0.5) > 0.7:
                strengths.append("专利稳定性高")
            elif patent_info.get("validity_score", 0.5) < 0.3:
                weaknesses.append("专利稳定性差")

        return strengths, weaknesses

    def _generate_strategy(
        self,
        litigation_type: LitigationType,
        litigation_role: LitigationRole,
        win_probability: float,
        key_issues: List[str]
    ) -> str:
        """生成推荐策略"""
        strategy_parts = []

        # 基础策略
        if win_probability >= 0.7:
            strategy_parts.append("建议积极应诉，争取胜诉")
        elif win_probability >= 0.5:
            strategy_parts.append("建议稳健推进，寻求和解可能")
        else:
            strategy_parts.append("建议考虑和解，减少损失")

        # 根据诉讼角色补充
        if litigation_role == LitigationRole.PLAINTIFF:
            strategy_parts.append("作为原告，应充分准备证据，合理确定诉讼请求")
        else:
            strategy_parts.append("作为被告，应积极收集抗辩证据，考虑提起无效宣告")

        # 根据关键争议点补充
        if key_issues:
            strategy_parts.append(f"重点争议: {', '.join(key_issues[:3])}")

        return "; ".join(strategy_parts)


async def test_litigation_strategy_analyzer():
    """测试诉讼策略分析器"""
    analyzer = LitigationStrategyAnalyzer()

    print("\n" + "="*80)
    print("⚖️ 诉讼策略分析器测试")
    print("="*80)

    # 测试案例1: 侵权诉讼-原告
    result1 = analyzer.analyze_case(
        patent_id="CN123456789A",
        litigation_type=LitigationType.INFRINGEMENT,
        litigation_role=LitigationRole.PLAINTIFF,
        case_info={
            "evidence_quality": 0.7,
            "complexity": 1.2,
            "dispute_infringement": True,
            "dispute_damages": True
        },
        patent_info={
            "validity_score": 0.8,
            "patent_type": "invention"
        }
    )

    print(f"\n📋 案例分析结果:")
    print(f"   诉讼类型: {result1.litigation_type.value}")
    print(f"   诉讼角色: {result1.litigation_role.value}")
    print(f"   案件强度: {result1.case_strength:.2f}")
    print(f"   胜诉概率: {result1.win_probability:.1%}")
    print(f"   风险等级: {result1.risk_level.value}")
    print(f"   预计持续时间: {result1.estimated_duration}")
    print(f"   预计费用: {result1.estimated_cost_range[0]:.0f}-{result1.estimated_cost_range[1]:.0f}万元")
    print(f"\n   关键争议点:")
    for issue in result1.key_issues[:3]:
        print(f"      - {issue}")
    print(f"\n   己方优势:")
    for strength in result1.strengths[:2]:
        print(f"      - {strength}")
    print(f"\n   己方劣势:")
    for weakness in result1.weaknesses[:2]:
        print(f"      - {weakness}")
    print(f"\n   推荐策略: {result1.recommended_strategy}")

    # 测试案例2: 无效诉讼-被告
    result2 = analyzer.analyze_case(
        patent_id="CN987654321A",
        litigation_type=LitigationType.INVALIDATION,
        litigation_role=LitigationRole.DEFENDANT,
        case_info={
            "evidence_quality": 0.4,
            "complexity": 1.0,
            "prior_art_found": True
        }
    )

    print(f"\n📋 案例分析结果2:")
    print(f"   诉讼类型: {result2.litigation_type.value}")
    print(f"   胜诉概率: {result2.win_probability:.1%}")
    print(f"   风险等级: {result2.risk_level.value}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_litigation_strategy_analyzer())
