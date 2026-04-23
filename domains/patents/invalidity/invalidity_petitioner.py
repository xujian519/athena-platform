#!/usr/bin/env python3
"""
无效宣告主控制器

整合所有模块，提供完整的无效宣告流程。
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .evidence_collector import EvidenceCollector
from .invalidity_analyzer import InvalidityAnalyzer
from .invalidity_petition_writer import InvalidityPetitionWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class InvalidityPetitionOptions:
    """无效宣告选项"""
    max_evidence: int = 10  # 最大证据数量
    include_all_claims: bool = True  # 是否挑战所有权利要求
    auto_collect_evidence: bool = True  # 是否自动收集证据


@dataclass
class InvalidityPetitionResult:
    """无效宣告结果"""
    target_patent_id: str
    petition_text: str
    invalidity_analysis: dict[str, Any]
    evidence_list: list[dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "target_patent_id": self.target_patent_id,
            "petition_text": self.petition_text,
            "invalidity_analysis": self.invalidity_analysis,
            "evidence_list": self.evidence_list,
            "metadata": self.metadata
        }

    def save_to_file(self, file_path: str) -> None:
        """保存到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.petition_text)


class InvalidityPetitioner:
    """无效宣告主控制器"""

    def __init__(self):
        """初始化控制器"""
        self.analyzer = InvalidityAnalyzer()
        self.evidence_collector = EvidenceCollector()
        self.petition_writer = InvalidityPetitionWriter()
        logger.info("✅ 无效宣告主控制器初始化成功")

    async def create_petition(
        self,
        target_patent_id: str,
        target_claims: list[str],
        petitioner_info: dict[str, str],
        options: InvalidityPetitionOptions | None = None,
        prior_art_references: list[str] | None = None
    ) -> InvalidityPetitionResult:
        """
        创建无效宣告请求

        Args:
            target_patent_id: 目标专利号
            target_claims: 目标权利要求
            petitioner_info: 请求人信息
            options: 无效宣告选项
            prior_art_references: 现有技术参考

        Returns:
            InvalidityPetitionResult对象
        """
        logger.info(f"🚀 开始创建无效宣告请求: {target_patent_id}")

        if options is None:
            options = InvalidityPetitionOptions()

        try:
            # 1. 分析无效理由
            logger.info("🔍 步骤1: 分析无效理由")
            invalidity_analysis = await self.analyzer.analyze_invalidity(
                target_patent_id,
                target_claims,
                prior_art_references
            )

            # 2. 收集证据
            evidence_list = []
            if options.auto_collect_evidence:
                logger.info("📚 步骤2: 收集证据")
                evidence_list = await self.evidence_collector.collect_evidence(
                    target_patent_id,
                    target_claims,
                    invalidity_analysis.invalidity_grounds,
                    options.max_evidence
                )

            # 3. 撰写请求书
            logger.info("📝 步骤3: 撰写请求书")
            petition_text = await self.petition_writer.write_petition(
                target_patent_id,
                invalidity_analysis,
                evidence_list,
                petitioner_info
            )

            # 4. 组装结果
            result = InvalidityPetitionResult(
                target_patent_id=target_patent_id,
                petition_text=petition_text,
                invalidity_analysis=invalidity_analysis.to_dict() if hasattr(invalidity_analysis, 'to_dict') else {},
                evidence_list=[e.to_dict() if hasattr(e, 'to_dict') else e for e in evidence_list],
                metadata={
                    "creation_date": datetime.now().strftime("%Y-%m-%d"),
                    "claims_count": len(target_claims),
                    "evidence_count": len(evidence_list),
                    "grounds_count": len(invalidity_analysis.invalidity_grounds) if hasattr(invalidity_analysis, 'invalidity_grounds') else 0
                }
            )

            logger.info("✅ 无效宣告请求创建完成!")
            logger.info(f"   证据数量: {len(evidence_list)}")
            logger.info(f"   无效理由: {result.metadata['grounds_count']}个")

            return result

        except Exception as e:
            logger.error(f"❌ 创建无效宣告请求失败: {e}")
            import traceback
            traceback.print_exc()
            raise


async def test_invalidity_petitioner():
    """测试无效宣告主控制器"""
    petitioner = InvalidityPetitioner()

    print("\n" + "="*80)
    print("🚀 无效宣告主控制器测试")
    print("="*80)

    # 测试数据
    target_patent_id = "CN123456789A"
    target_claims = [
        "1. 一种图像识别方法，包括输入层和卷积层。",
        "2. 根据权利要求1所述的方法，其特征在于，所述卷积层采用多尺度卷积核。",
        "3. 根据权利要求1所述的方法，其特征在于，还包括池化层。"
    ]

    petitioner_info = {
        "name": "XXX公司",
        "address": "北京市XXX区XXX路XXX号"
    }

    options = InvalidityPetitionOptions(
        max_evidence=5,
        include_all_claims=True,
        auto_collect_evidence=True
    )

    # 创建无效宣告请求
    result = await petitioner.create_petition(
        target_patent_id,
        target_claims,
        petitioner_info,
        options
    )

    # 输出结果
    print("\n✅ 无效宣告请求创建完成:\n")
    print(f"目标专利: {result.target_patent_id}")
    print(f"证据数量: {result.metadata['evidence_count']}")
    print(f"无效理由: {result.metadata['grounds_count']}个")

    print("\n请求书（前500字）:")
    print(result.petition_text[:500] + "...")

    # 保存到文件
    import tempfile
    output_file = tempfile.mktemp(suffix='_invalidity_petition.txt')
    result.save_to_file(output_file)
    print(f"\n💾 请求书已保存到: {output_file}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_invalidity_petitioner())
