#!/usr/bin/env python3
"""
审查意见答复主控制器

整合所有模块，提供完整的审查意见答复流程。
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

try:
    from .prior_art_analyzer import PriorArtAnalysis, PriorArtAnalyzer
    from .response_strategy_generator import ResponseStrategy, ResponseStrategyGenerator
    from .response_writer import ResponseWriter
except ImportError:
    from core.patents.oa_response.prior_art_analyzer import PriorArtAnalyzer
    from core.patents.oa_response.response_strategy_generator import (
        ResponseStrategyGenerator,
    )
    from core.patents.oa_response.response_writer import ResponseWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExaminationOpinion:
    """审查意见"""
    oa_number: str  # 审查意见通知书编号
    oa_date: str  # 审查意见日期
    rejection_type: str  # 驳回类型
    cited_claims: list[int]  # 被引用的权利要求
    prior_art_references: list[str]  # 对比文件引用
    examiner_arguments: list[str]  # 审查员论点
    legal_basis: list[str]  # 法律依据
    raw_text: str = ""  # 原始文本

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "oa_number": self.oa_number,
            "oa_date": self.oa_date,
            "rejection_type": self.rejection_type,
            "cited_claims": self.cited_claims,
            "prior_art_references": self.prior_art_references,
            "examiner_arguments": self.examiner_arguments,
            "legal_basis": self.legal_basis,
            "raw_text": self.raw_text
        }


@dataclass
class ResponseOptions:
    """答复选项"""
    include_amendments: bool = True  # 是否包含修改建议
    auto_generate_amendments: bool = True  # 是否自动生成修改
    writing_style: str = "formal"  # formal, concise, detailed


@dataclass
class OAResponse:
    """审查意见答复"""
    oa_number: str  # 审查意见通知书编号
    response_date: str  # 答复日期
    response_arguments: str  # 答复理由陈述
    amended_claims: list[str]  # 修改后的权利要求
    amended_description: str = ""  # 修改后的说明书
    strategy: dict[str, Any] = field(default_factory=dict)  # 答复策略
    amendments: list[dict[str, Any] = field(default_factory=list)  # 修改建议
    prior_art_analysis: dict[str, Any] = field(default_factory=dict)  # 对比文件分析
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "oa_number": self.oa_number,
            "response_date": self.response_date,
            "response_arguments": self.response_arguments,
            "amended_claims": self.amended_claims,
            "amended_description": self.amended_description,
            "strategy": self.strategy,
            "amendments": self.amendments,
            "prior_art_analysis": self.prior_art_analysis,
            "metadata": self.metadata
        }

    def save_to_file(self, file_path: str) -> None:
        """保存到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {self.oa_number} 答复意见书\n\n")
            f.write(f"## 答复日期\n{self.response_date}\n\n")
            f.write("## 答复策略\n")
            f.write(f"策略类型: {self.strategy.get('strategy_type', 'N/A')}\n")
            f.write(f"成功概率: {self.strategy.get('success_probability', 0):.2%}\n\n")
            f.write(f"## 答复理由陈述\n{self.response_arguments}\n\n")
            if self.amended_claims:
                f.write("## 修改后的权利要求\n")
                for claim in self.amended_claims:
                    f.write(f"{claim}\n")
            if self.amendments:
                f.write("\n## 修改建议\n")
                for i, amendment in enumerate(self.amendments, 1):
                    f.write(f"{i}. {amendment.get('reason', '')}\n")


class OAResponder:
    """审查意见答复主控制器"""

    def __init__(self):
        """初始化答复器"""
        self.prior_art_analyzer = PriorArtAnalyzer()
        self.strategy_generator = ResponseStrategyGenerator()
        self.response_writer = ResponseWriter()
        logger.info("✅ 审查意见答复主控制器初始化成功")

    async def create_response(
        self,
        oa: ExaminationOpinion,
        current_claims: list[str],
        options: ResponseOptions | None = None
    ) -> OAResponse:
        """
        创建审查意见答复

        Args:
            oa: 审查意见
            current_claims: 当前权利要求
            options: 答复选项

        Returns:
            OAResponse对象
        """
        logger.info(f"🚀 开始创建审查意见答复: {oa.oa_number}")

        if options is None:
            options = ResponseOptions()

        try:
            # 1. 分析对比文件
            logger.info("🔍 步骤1: 分析对比文件")
            prior_art_analysis = await self.prior_art_analyzer.analyze_prior_art(
                current_claims,
                oa.prior_art_references
            )

            # 2. 生成答复策略
            logger.info("🎯 步骤2: 生成答复策略")
            strategy = await self.strategy_generator.generate_strategy(
                oa.rejection_type,
                oa.cited_claims,
                oa.examiner_arguments,
                prior_art_analysis
            )

            # 3. 撰写答复理由
            logger.info("📝 步骤3: 撰写答复理由")
            response_arguments = await self.response_writer.write_response_arguments(
                oa.oa_number,
                strategy,
                prior_art_analysis
            )

            # 4. 生成修改建议
            amended_claims = current_claims
            amendments = []

            if options.include_amendments and options.auto_generate_amendments:
                logger.info("✏️ 步骤4: 生成修改建议")
                amendments = await self.response_writer.generate_amendment_suggestions(
                    current_claims,
                    strategy,
                    prior_art_analysis
                )

                # 应用修改
                if amendments:
                    amended_claims = await self.response_writer.write_amended_claims(
                        current_claims,
                        amendments
                    )

            # 5. 组装完整答复
            logger.info("📦 步骤5: 组装完整答复")
            response = OAResponse(
                oa_number=oa.oa_number,
                response_date=datetime.now().strftime("%Y-%m-%d"),
                response_arguments=response_arguments,
                amended_claims=amended_claims,
                strategy=strategy.to_dict() if hasattr(strategy, 'to_dict') else {},
                amendments=[a.to_dict() if hasattr(a, 'to_dict') else a for a in amendments],
                prior_art_analysis=prior_art_analysis.to_dict() if hasattr(prior_art_analysis, 'to_dict') else {},
                metadata={
                    "rejection_type": oa.rejection_type,
                    "cited_claims": oa.cited_claims,
                    "examiner_arguments_count": len(oa.examiner_arguments),
                    "success_probability": strategy.success_probability if hasattr(strategy, 'success_probability') else 0.5,
                    "claims_amended": len(amended_claims) != len(current_claims) or amended_claims != current_claims
                }
            )

            logger.info("✅ 审查意见答复创建完成!")
            logger.info(f"   策略类型: {response.strategy.get('strategy_type', 'N/A')}")
            logger.info(f"   成功概率: {response.metadata.get('success_probability', 0):.2%}")
            logger.info(f"   修改权利要求: {response.metadata.get('claims_amended', False)}")

            return response

        except Exception as e:
            logger.error(f"❌ 创建审查意见答复失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def batch_create_responses(
        self,
        oa_list: list[ExaminationOpinion],
        claims_dict: dict[str, list[str],
        options: ResponseOptions | None = None
    ) -> list[OAResponse]:
        """
        批量创建答复

        Args:
            oa_list: 审查意见列表
            claims_dict: 权利要求字典（key为OA编号）
            options: 答复选项

        Returns:
            答复列表
        """
        logger.info(f"🚀 开始批量创建答复: {len(oa_list)} 个审查意见")

        # 并发处理
        tasks = [
            self.create_response(oa, claims_dict.get(oa.oa_number, []), options)
            for oa in oa_list
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ OA {oa_list[i].oa_number} 答复失败: {result}")
            else:
                responses.append(result)

        logger.info(f"✅ 批量答复完成: {len(responses)}/{len(oa_list)} 成功")
        return responses


async def test_oa_responder():
    """测试审查意见答复主控制器"""
    responder = OAResponder()

    print("\n" + "="*80)
    print("🚀 审查意见答复主控制器测试")
    print("="*80)

    # 创建测试审查意见
    oa = ExaminationOpinion(
        oa_number="OA202312001",
        oa_date="2023-12-01",
        rejection_type="novelty",
        cited_claims=[1, 2],
        prior_art_references=["CN123456789A", "US9876543B2"],
        examiner_arguments=[
            "对比文件D1公开了相同的图像识别方法",
            "权利要求1相对于D1不具备新颖性"
        ],
        legal_basis=["专利法第22条第2款"],
        raw_text=""
    )

    # 当前权利要求
    current_claims = [
        "1. 一种基于深度学习的图像识别方法，其特征在于，包括：输入层，用于接收待识别图像；卷积层，用于提取图像特征，所述卷积层采用多尺度卷积核；池化层，用于降维和特征选择。",
        "2. 根据权利要求1所述的方法，其特征在于，所述卷积核大小为3x3。"
    ]

    # 配置选项
    options = ResponseOptions(
        include_amendments=True,
        auto_generate_amendments=True,
        writing_style="formal"
    )

    # 创建答复
    response = await responder.create_response(oa, current_claims, options)

    # 输出结果
    print("\n✅ 审查意见答复创建完成:\n")
    print(f"OA编号: {response.oa_number}")
    print(f"答复日期: {response.response_date}")
    print(f"策略类型: {response.strategy.get('strategy_type', 'N/A')}")
    print(f"成功概率: {response.metadata.get('success_probability', 0):.2%}")
    print("\n答复理由（前500字）:")
    print(response.response_arguments[:500] + "...")

    if response.amended_claims and response.amended_claims != current_claims:
        print("\n修改后的权利要求（第1条）:")
        print(response.amended_claims[0])

    # 保存到文件
    import tempfile
    output_file = tempfile.mktemp(suffix='_oa_response.txt')
    response.save_to_file(output_file)
    print(f"\n💾 答复文件已保存到: {output_file}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_oa_responder())
