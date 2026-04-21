#!/usr/bin/env python3
"""
侵权分析主控制器

整合所有模块，提供完整的侵权分析流程。
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from .claim_parser import ClaimParser, ParsedClaim
    from .product_analyzer import ProductAnalyzer, AnalyzedProduct
    from .feature_comparator import FeatureComparator, FeatureComparison
    from .infringement_determiner import InfringementDeterminer, InfringementResult
    from .opinion_writer import OpinionWriter
except ImportError:
    from core.patents.infringement.claim_parser import ClaimParser, ParsedClaim
    from core.patents.infringement.product_analyzer import ProductAnalyzer, AnalyzedProduct
    from core.patents.infringement.feature_comparator import FeatureComparator, FeatureComparison
    from core.patents.infringement.infringement_determiner import InfringementDeterminer, InfringementResult
    from core.patents.infringement.opinion_writer import OpinionWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class InfringementAnalysisOptions:
    """侵权分析选项"""
    include_comparison_table: bool = True  # 是否生成对比表
    include_detailed_reasoning: bool = True  # 是否包含详细推理
    writing_style: str = "formal"  # formal, concise, detailed


@dataclass
class InfringementAnalysisResult:
    """侵权分析结果"""
    patent_id: str
    product_name: str
    parsed_claims: List[Dict[str, Any]]
    analyzed_product: Dict[str, Any]
    feature_comparisons: List[Dict[str, Any]]
    infringement_result: Dict[str, Any]
    legal_opinion: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "product_name": self.product_name,
            "parsed_claims": self.parsed_claims,
            "analyzed_product": self.analyzed_product,
            "feature_comparisons": self.feature_comparisons,
            "infringement_result": self.infringement_result,
            "legal_opinion": self.legal_opinion,
            "metadata": self.metadata
        }

    def save_to_file(self, file_path: str) -> None:
        """保存到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.legal_opinion)


class InfringementAnalyzer:
    """侵权分析主控制器"""

    def __init__(self):
        """初始化控制器"""
        self.claim_parser = ClaimParser()
        self.product_analyzer = ProductAnalyzer()
        self.feature_comparator = FeatureComparator()
        self.infringement_determiner = InfringementDeterminer()
        self.opinion_writer = OpinionWriter()
        logger.info("✅ 侵权分析主控制器初始化成功")

    async def analyze_infringement(
        self,
        patent_id: str,
        claims: List[str],
        product_description: str,
        product_name: str = "涉案产品",
        options: Optional[InfringementAnalysisOptions] = None
    ) -> InfringementAnalysisResult:
        """
        执行完整的侵权分析流程

        Args:
            patent_id: 专利号
            claims: 权利要求列表
            product_description: 产品描述
            product_name: 产品名称
            options: 分析选项

        Returns:
            InfringementAnalysisResult对象
        """
        logger.info(f"🚀 开始侵权分析: 专利={patent_id}, 产品={product_name}")

        if options is None:
            options = InfringementAnalysisOptions()

        try:
            # 步骤1: 解析权利要求
            logger.info("📜 步骤1: 解析权利要求")
            parsed_claims = self.claim_parser.parse_multiple_claims(claims)

            # 步骤2: 分析产品
            logger.info("📦 步骤2: 分析涉案产品")
            analyzed_product = self.product_analyzer.analyze_from_description(
                product_description,
                product_name
            )

            # 步骤3: 特征对比
            logger.info("🔍 步骤3: 特征对比分析")
            comparisons = self.feature_comparator.compare_multiple_claims(
                parsed_claims,
                analyzed_product
            )

            # 步骤4: 侵权判定
            logger.info("⚖️ 步骤4: 侵权判定")
            infringement_result = self.infringement_determiner.determine(
                comparisons,
                patent_id,
                product_name
            )

            # 步骤5: 撰写法律意见书
            logger.info("📝 步骤5: 撰写法律意见书")
            legal_opinion = self.opinion_writer.write_opinion(
                infringement_result,
                comparisons,
                attorney="Athena专利代理系统"
            )

            # 组装结果
            result = InfringementAnalysisResult(
                patent_id=patent_id,
                product_name=product_name,
                parsed_claims=[c.to_dict() for c in parsed_claims],
                analyzed_product=analyzed_product.to_dict(),
                feature_comparisons=[c.to_dict() for c in comparisons],
                infringement_result=infringement_result.to_dict(),
                legal_opinion=legal_opinion,
                metadata={
                    "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                    "claims_analyzed": len(parsed_claims),
                    "product_features": len(analyzed_product.features),
                    "overall_infringement": infringement_result.overall_infringement,
                    "overall_risk": infringement_result.overall_risk
                }
            )

            logger.info("✅ 侵权分析完成!")
            logger.info(f"   分析权利要求: {len(parsed_claims)} 条")
            logger.info(f"   产品特征数: {len(analyzed_product.features)} 个")
            logger.info(f"   总体侵权: {'是' if infringement_result.overall_infringement else '否'}")
            logger.info(f"   风险等级: {infringement_result.overall_risk}")

            return result

        except Exception as e:
            logger.error(f"❌ 侵权分析失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def analyze_from_files(
        self,
        patent_id: str,
        claims_file: str,
        product_file: str,
        options: Optional[InfringementAnalysisOptions] = None
    ) -> InfringementAnalysisResult:
        """
        从文件执行侵权分析

        Args:
            patent_id: 专利号
            claims_file: 权利要求文件路径
            product_file: 产品说明文件路径
            options: 分析选项

        Returns:
            InfringementAnalysisResult对象
        """
        logger.info(f"🚀 从文件执行侵权分析")

        # 读取权利要求
        with open(claims_file, 'r', encoding='utf-8') as f:
            claims_text = f.read()
        claims = [line.strip() for line in claims_text.split('\n') if line.strip()]

        # 分析产品
        product_analyzer = ProductAnalyzer()
        analyzed_product = await product_analyzer.analyze_from_file(product_file)

        # 执行分析
        result = await self.analyze_infringement(
            patent_id,
            claims,
            analyzed_product.description,
            analyzed_product.product_name,
            options
        )

        return result


async def test_infringement_analyzer():
    """测试侵权分析主控制器"""
    analyzer = InfringementAnalyzer()

    print("\n" + "="*80)
    print("🚀 侵权分析主控制器测试")
    print("="*80)

    # 测试数据
    patent_id = "CN123456789A"
    claims = [
        "1. 一种图像识别方法，包括输入层和卷积层，其特征在于，所述卷积层采用多尺度卷积核。",
        "2. 根据权利要求1所述的方法，其特征在于，还包括池化层。"
    ]

    product_description = """
    本产品是一种智能图像识别系统，用于人脸识别应用。
    系统包括数据输入模块，用于接收图像数据。
    系统还包括卷积神经网络模块，该模块使用3x3和5x5两种尺寸的卷积核进行特征提取。
    系统还包括池化层，用于降低特征维度。
    系统输出识别结果到显示模块。
    """

    # 执行分析
    result = await analyzer.analyze_infringement(
        patent_id,
        claims,
        product_description,
        "智能图像识别系统"
    )

    # 输出结果
    print(f"\n✅ 侵权分析完成:\n")
    print(f"专利号: {result.patent_id}")
    print(f"产品名: {result.product_name}")
    print(f"总体侵权: {result.metadata['overall_infringement']}")
    print(f"风险等级: {result.metadata['overall_risk']}")

    print(f"\n法律意见书（前500字）:")
    print(result.legal_opinion[:500] + "...")

    # 保存到文件
    import tempfile
    output_file = tempfile.mktemp(suffix='_infringement_opinion.md')
    result.save_to_file(output_file)
    print(f"\n💾 法律意见书已保存到: {output_file}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_infringement_analyzer())
