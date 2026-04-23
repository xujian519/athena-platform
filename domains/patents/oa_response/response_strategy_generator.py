#!/usr/bin/env python3
"""
答复策略生成器

生成审查意见答复的策略和论点。
"""
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.patents.qualitative_rules import get_qualitative_rule_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResponseStrategyType(Enum):
    """答复策略类型"""
    ARGUE = "argue"  # 争辩（认为审查员错误）
    AMEND = "amend"  # 修改（修改权利要求）
    COMBINE = "combine"  # 组合（争辩+修改）


@dataclass
class ResponseStrategy:
    """答复策略"""
    strategy_type: ResponseStrategyType
    success_probability: float  # 成功概率
    arguments: list[str]  # 争辩论点
    amendment_suggestions: list[str]  # 修改建议
    legal_basis: list[str]  # 法律依据
    case_references: list[str]  # 案例参考
    reasoning: str  # 策略推理

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "strategy_type": self.strategy_type.value,
            "success_probability": self.success_probability,
            "arguments": self.arguments,
            "amendment_suggestions": self.amendment_suggestions,
            "legal_basis": self.legal_basis,
            "case_references": self.case_references,
            "reasoning": self.reasoning
        }


class ResponseStrategyGenerator:
    """答复策略生成器"""

    def __init__(self):
        """初始化生成器"""
        try:
            self.rule_engine = get_qualitative_rule_engine()
            logger.info("✅ 定性规则引擎已加载")
        except Exception as e:
            logger.warning(f"⚠️ 规则引擎加载失败: {e}")
            self.rule_engine = None

        logger.info("✅ 答复策略生成器初始化成功")

    async def generate_strategy(
        self,
        rejection_type: str,
        cited_claims: list[int],
        examiner_arguments: list[str],
        prior_art_analysis: Any | None = None
    ) -> ResponseStrategy:
        """
        生成答复策略

        Args:
            rejection_type: 驳回类型（novelty, inventiveness, clarity等）
            cited_claims: 被引用的权利要求
            examiner_arguments: 审查员论点
            prior_art_analysis: 对比文件分析结果

        Returns:
            ResponseStrategy对象
        """
        logger.info(f"🎯 开始生成答复策略: {rejection_type}")

        try:
            # 1. 分析驳回类型
            strategy_type = await self._determine_strategy_type(
                rejection_type,
                prior_art_analysis
            )

            # 2. 生成争辩论点
            arguments = await self._generate_arguments(
                rejection_type,
                examiner_arguments,
                prior_art_analysis
            )

            # 3. 生成修改建议
            amendment_suggestions = await self._generate_amendments(
                strategy_type,
                cited_claims,
                prior_art_analysis
            )

            # 4. 确定法律依据
            legal_basis = await self._determine_legal_basis(rejection_type)

            # 5. 计算成功概率
            success_probability = await self._calculate_success_probability(
                strategy_type,
                prior_art_analysis
            )

            # 6. 生成策略推理
            reasoning = self._generate_reasoning(
                strategy_type,
                rejection_type,
                prior_art_analysis
            )

            # 7. 查找案例参考
            case_references = await self._find_case_references(rejection_type)

            logger.info(f"✅ 答复策略生成完成: {strategy_type.value}")

            return ResponseStrategy(
                strategy_type=strategy_type,
                success_probability=success_probability,
                arguments=arguments,
                amendment_suggestions=amendment_suggestions,
                legal_basis=legal_basis,
                case_references=case_references,
                reasoning=reasoning
            )

        except Exception as e:
            logger.error(f"❌ 生成答复策略失败: {e}")
            import traceback
            traceback.print_exc()

            # 返回默认策略
            return ResponseStrategy(
                strategy_type=ResponseStrategyType.COMBINE,
                success_probability=0.5,
                arguments=["暂无具体论点"],
                amendment_suggestions=["暂无修改建议"],
                legal_basis=[],
                case_references=[],
                reasoning="策略生成失败，使用默认策略"
            )

    async def _determine_strategy_type(
        self,
        rejection_type: str,
        prior_art_analysis: Any | None
    ) -> ResponseStrategyType:
        """确定答复策略类型"""
        # 根据驳回类型和对比文件分析确定策略

        if prior_art_analysis and hasattr(prior_art_analysis, 'undisclosed_features'):
            # 如果有未公开特征，优先争辩
            if len(prior_art_analysis.undisclosed_features) >= 2:
                return ResponseStrategyType.ARGUE

            # 如果有少量未公开特征，考虑组合策略
            if len(prior_art_analysis.undisclosed_features) >= 1:
                return ResponseStrategyType.COMBINE

        # 根据驳回类型
        if rejection_type in ["novelty", "inventiveness"]:
            # 新颖性或创造性驳回，通常需要修改
            return ResponseStrategyType.COMBINE
        elif rejection_type in ["clarity", "support"]:
            # 清晰度或支持问题，通常可以修改解决
            return ResponseStrategyType.AMEND
        else:
            # 其他情况，默认组合策略
            return ResponseStrategyType.COMBINE

    async def _generate_arguments(
        self,
        rejection_type: str,
        examiner_arguments: list[str],
        prior_art_analysis: Any | None
    ) -> list[str]:
        """生成争辩论点"""
        arguments = []

        # 基于驳回类型生成论点
        if rejection_type == "novelty":
            arguments.append("对比文件未公开本申请的所有技术特征")
            if prior_art_analysis and hasattr(prior_art_analysis, 'undisclosed_features'):
                for feature in prior_art_analysis.undisclosed_features[:3]:
                    arguments.append(f"对比文件未公开{feature}")

        elif rejection_type == "inventiveness":
            arguments.append("本申请相对于对比文件具有突出的实质性特点和显著的进步")
            arguments.append("对比文件未给出技术启示")

        # 基于审查员论点生成反驳
        for arg in examiner_arguments[:2]:
            arguments.append(f"关于审查员指出的'{arg[:30]}...'，本申请存在区别")

        return arguments

    async def _generate_amendments(
        self,
        strategy_type: ResponseStrategyType,
        cited_claims: list[int],
        prior_art_analysis: Any | None
    ) -> list[str]:
        """生成修改建议"""
        amendments = []

        if strategy_type in [ResponseStrategyType.AMEND, ResponseStrategyType.COMBINE]:
            # 建议修改权利要求
            for claim_num in cited_claims[:3]:
                amendments.append(f"建议修改权利要求{claim_num}，进一步限定技术特征")

            if prior_art_analysis and hasattr(prior_art_analysis, 'undisclosed_features'):
                for feature in prior_art_analysis.undisclosed_features[:2]:
                    amendments.append(f"建议将'{feature}'补入权利要求")

        return amendments

    async def _determine_legal_basis(self, rejection_type: str) -> list[str]:
        """确定法律依据"""
        legal_basis = []

        # 专利法相关条款
        if rejection_type == "novelty":
            legal_basis.append("《专利法》第22条第2款：新颖性")
        elif rejection_type == "inventiveness":
            legal_basis.append("《专利法》第22条第3款：创造性")
        elif rejection_type == "clarity":
            legal_basis.append("《专利法》第26条第4款：清楚简要")
        elif rejection_type == "support":
            legal_basis.append("《专利法》第26条第4款：说明书支持")

        # 审查指南相关条款
        legal_basis.append("《专利审查指南》相关规定")

        return legal_basis

    async def _calculate_success_probability(
        self,
        strategy_type: ResponseStrategyType,
        prior_art_analysis: Any | None
    ) -> float:
        """计算成功概率"""
        base_probability = 0.5

        # 根据策略类型调整
        if strategy_type == ResponseStrategyType.ARGUE:
            base_probability = 0.6
        elif strategy_type == ResponseStrategyType.COMBINE:
            base_probability = 0.75
        elif strategy_type == ResponseStrategyType.AMEND:
            base_probability = 0.8

        # 根据对比文件分析调整
        if prior_art_analysis and hasattr(prior_art_analysis, 'undisclosed_features'):
            # 未公开特征越多，成功概率越高
            base_probability += len(prior_art_analysis.undisclosed_features) * 0.05

        return min(base_probability, 0.95)

    def _generate_reasoning(
        self,
        strategy_type: ResponseStrategyType,
        rejection_type: str,
        prior_art_analysis: Any | None
    ) -> str:
        """生成策略推理"""
        reasoning_parts = []

        reasoning_parts.append(f"针对{rejection_type}驳回，")

        if strategy_type == ResponseStrategyType.ARGUE:
            reasoning_parts.append("建议采用争辩策略。")
            if prior_art_analysis and hasattr(prior_art_analysis, 'undisclosed_features'):
                reasoning_parts.append(
                    f"理由：对比文件未公开{len(prior_art_analysis.undisclosed_features)}个特征，"
                    f"具备争辩空间。"
                )
        elif strategy_type == ResponseStrategyType.AMEND:
            reasoning_parts.append("建议采用修改策略。")
            reasoning_parts.append("理由：通过修改权利要求可以克服驳回问题。")
        elif strategy_type == ResponseStrategyType.COMBINE:
            reasoning_parts.append("建议采用组合策略。")
            reasoning_parts.append("理由：同时进行争辩和修改，可以提高答复成功率。")

        return "".join(reasoning_parts)

    async def _find_case_references(self, rejection_type: str) -> list[str]:
        """查找案例参考"""
        # 这里可以连接到案例数据库
        # 暂时返回模拟案例
        case_references = []

        if rejection_type == "novelty":
            case_references.append("案例1：相似技术特征不同，认定具备新颖性")
        elif rejection_type == "inventiveness":
            case_references.append("案例2：预料不到的技术效果，认定具备创造性")

        return case_references


async def test_strategy_generator():
    """测试答复策略生成器"""
    generator = ResponseStrategyGenerator()

    print("\n" + "="*80)
    print("🎯 答复策略生成器测试")
    print("="*80)

    # 测试数据
    strategy = await generator.generate_strategy(
        rejection_type="novelty",
        cited_claims=[1, 2],
        examiner_arguments=[
            "对比文件D1公开了相同的技术方案",
            "权利要求1不具备新颖性"
        ],
        prior_art_analysis=None
    )

    # 输出结果
    print("\n✅ 策略生成完成:\n")
    print(f"策略类型: {strategy.strategy_type.value}")
    print(f"成功概率: {strategy.success_probability:.2%}")
    print("\n争辩论点:")
    for i, arg in enumerate(strategy.arguments, 1):
        print(f"  {i}. {arg}")
    print("\n修改建议:")
    for i, sug in enumerate(strategy.amendment_suggestions, 1):
        print(f"  {i}. {sug}")
    print("\n法律依据:")
    for basis in strategy.legal_basis:
        print(f"  - {basis}")
    print(f"\n策略推理: {strategy.reasoning}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_strategy_generator())
