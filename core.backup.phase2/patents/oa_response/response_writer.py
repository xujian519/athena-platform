#!/usr/bin/env python3
"""
答复文书撰写器

撰写审查意见答复书。
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AmendmentSuggestion:
    """修改建议"""
    claim_number: int  # 权利要求编号
    original_text: str  # 原文
    amended_text: str  # 修改后文本
    reason: str  # 修改理由

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "claim_number": self.claim_number,
            "original_text": self.original_text,
            "amended_text": self.amended_text,
            "reason": self.reason
        }


class ResponseWriter:
    """答复文书撰写器"""

    def __init__(self):
        """初始化撰写器"""
        logger.info("✅ 答复文书撰写器初始化成功")

    async def write_response_arguments(
        self,
        oa_number: str,
        strategy: Any,
        prior_art_analysis: Optional[Any] = None
    ) -> str:
        """
        撰写答复理由陈述

        Args:
            oa_number: 审查意见通知书编号
            strategy: 答复策略
            prior_art_analysis: 对比文件分析

        Returns:
            答复理由文本
        """
        logger.info("📝 开始撰写答复理由陈述")

        try:
            response_parts = []

            # 1. 开头部分
            response_parts.append(self._write_header(oa_number))

            # 2. 总体陈述
            response_parts.append(self._write_opening_statement(strategy))

            # 3. 具体论点
            response_parts.append(self._write_arguments(strategy, prior_art_analysis))

            # 4. 结尾部分
            response_parts.append(self._write_closing())

            return "\n".join(response_parts)

        except Exception as e:
            logger.error(f"❌ 撰写答复理由失败: {e}")
            import traceback
            traceback.print_exc()
            return "答复理由撰写失败"

    def _write_header(self, oa_number: str) -> str:
        """撰写开头"""
        return f"""
关于{oa_number}的审查意见答复

申请人：

收到的{oa_number}审查意见通知书，现作如下答复：
"""

    def _write_opening_statement(self, strategy: Any) -> str:
        """撰写总体陈述"""
        return """
一、总体说明

申请人仔细研究了审查意见，认为审查员指出的问题可以通过修改和陈述予以克服。
"""

    def _write_arguments(
        self,
        strategy: Any,
        prior_art_analysis: Optional[Any]
    ) -> str:
        """撰写具体论点"""
        arguments_parts = []

        arguments_parts.append("\n二、具体答复意见\n")

        # 策略论点
        if hasattr(strategy, 'arguments') and strategy.arguments:
            for i, arg in enumerate(strategy.arguments, 1):
                arguments_parts.append(f"\n{i}. {arg}\n")

        # 法律依据
        if hasattr(strategy, 'legal_basis') and strategy.legal_basis:
            arguments_parts.append("\n【法律依据】\n")
            for basis in strategy.legal_basis:
                arguments_parts.append(f"- {basis}\n")

        # 案例参考
        if hasattr(strategy, 'case_references') and strategy.case_references:
            arguments_parts.append("\n【案例参考】\n")
            for case_ref in strategy.case_references:
                arguments_parts.append(f"- {case_ref}\n")

        return "".join(arguments_parts)

    def _write_closing(self) -> str:
        """撰写结尾"""
        return """
三、结语

综上所述，申请人认为本申请符合专利法及审查指南的相关规定，恳请审查员给予早日授权。

此致
敬礼！

申请人：[申请人名称]
日期：""" + datetime.now().strftime("%Y年%m月%d日")

    async def generate_amendment_suggestions(
        self,
        current_claims: List[str],
        strategy: Any,
        prior_art_analysis: Optional[Any] = None
    ) -> List[AmendmentSuggestion]:
        """
        生成修改建议

        Args:
            current_claims: 当前权利要求
            strategy: 答复策略
            prior_art_analysis: 对比文件分析

        Returns:
            修改建议列表
        """
        logger.info("✏️ 开始生成修改建议")

        amendments = []

        # 根据策略生成修改建议
        if hasattr(strategy, 'amendment_suggestions'):
            for i, suggestion in enumerate(strategy.amendment_suggestions):
                # 简单解析建议文本
                if "权利要求" in suggestion and "修改" in suggestion:
                    # 提取权利要求编号
                    import re
                    match = re.search(r'权利要求(\d+)', suggestion)
                    if match:
                        claim_num = int(match.group(1))
                        if claim_num <= len(current_claims):
                            amendments.append(AmendmentSuggestion(
                                claim_number=claim_num,
                                original_text=current_claims[claim_num - 1],
                                amended_text=f"[修改后]{current_claims[claim_num - 1]}",
                                reason=suggestion
                            ))

        logger.info(f"✅ 生成 {len(amendments)} 条修改建议")
        return amendments

    async def write_amended_claims(
        self,
        current_claims: List[str],
        amendments: List[AmendmentSuggestion]
    ) -> List[str]:
        """
        撰写修改后的权利要求

        Args:
            current_claims: 当前权利要求
            amendments: 修改建议列表

        Returns:
            修改后的权利要求列表
        """
        logger.info("📝 开始撰写修改后的权利要求")

        amended_claims = current_claims.copy()

        # 应用修改建议
        for amendment in amendments:
            if amendment.claim_number <= len(amended_claims):
                amended_claims[amendment.claim_number - 1] = amendment.amended_text

        logger.info(f"✅ 修改完成，共 {len(amended_claims)} 条权利要求")
        return amended_claims

    async def write_full_response(
        self,
        oa_number: str,
        current_claims: List[str],
        strategy: Any,
        prior_art_analysis: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        撰写完整答复意见书

        Args:
            oa_number: 审查意见通知书编号
            current_claims: 当前权利要求
            strategy: 答复策略
            prior_art_analysis: 对比文件分析

        Returns:
            完整答复意见书字典
        """
        logger.info("📝 开始撰写完整答复意见书")

        # 1. 撰写答复理由
        response_arguments = await self.write_response_arguments(
            oa_number,
            strategy,
            prior_art_analysis
        )

        # 2. 生成修改建议
        amendments = await self.generate_amendment_suggestions(
            current_claims,
            strategy,
            prior_art_analysis
        )

        # 3. 撰写修改后的权利要求
        if amendments:
            amended_claims = await self.write_amended_claims(
                current_claims,
                amendments
            )
        else:
            amended_claims = current_claims

        # 4. 组装完整答复
        full_response = {
            "oa_number": oa_number,
            "response_arguments": response_arguments,
            "amendments": [a.to_dict() for a in amendments],
            "amended_claims": amended_claims,
            "strategy": strategy.to_dict() if hasattr(strategy, 'to_dict') else {},
            "metadata": {
                "generation_date": datetime.now().strftime("%Y-%m-%d"),
                "claims_count": len(amended_claims),
                "amendments_count": len(amendments)
            }
        }

        logger.info("✅ 完整答复意见书撰写完成")
        return full_response


async def test_response_writer():
    """测试答复文书撰写器"""
    writer = ResponseWriter()

    print("\n" + "="*80)
    print("📝 答复文书撰写器测试")
    print("="*80)

    # 创建测试策略
    try:
        from response_strategy_generator import ResponseStrategy, ResponseStrategyType
    except ImportError:
        from core.patents.oa_response.response_strategy_generator import ResponseStrategy, ResponseStrategyType

    test_strategy = ResponseStrategy(
        strategy_type=ResponseStrategyType.COMBINE,
        success_probability=0.75,
        arguments=[
            "对比文件D1未公开本申请的多尺度特征融合技术",
            "本申请具有预料不到的技术效果"
        ],
        amendment_suggestions=[
            "建议修改权利要求1，补入'多尺度特征融合'特征",
            "建议修改权利要求2，进一步限定卷积核参数"
        ],
        legal_basis=[
            "《专利法》第22条第2款：新颖性",
            "《专利法》第22条第3款：创造性"
        ],
        case_references=[
            "案例1：相似技术特征不同，认定具备新颖性"
        ],
        reasoning="采用组合策略，同时进行争辩和修改"
    )

    # 当前权利要求
    current_claims = [
        "1. 一种图像识别方法，包括输入层和卷积层。",
        "2. 根据权利要求1所述的方法，其特征在于，所述卷积层用于提取特征。"
    ]

    # 撰写答复理由
    response_arguments = await writer.write_response_arguments(
        "OA202312001",
        test_strategy
    )

    print(f"\n✅ 答复理由:\n")
    print(response_arguments[:500] + "...\n")

    # 生成修改建议
    amendments = await writer.generate_amendment_suggestions(
        current_claims,
        test_strategy
    )

    print(f"\n✅ 修改建议: {len(amendments)}条\n")
    for i, amendment in enumerate(amendments, 1):
        print(f"{i}. 权利要求{amendment.claim_number}: {amendment.reason}")

    # 撰写完整答复
    full_response = await writer.write_full_response(
        "OA202312001",
        current_claims,
        test_strategy
    )

    print(f"\n✅ 完整答复意见书元数据:")
    for key, value in full_response["metadata"].items():
        print(f"  {key}: {value}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_response_writer())
