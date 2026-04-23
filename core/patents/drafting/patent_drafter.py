#!/usr/bin/env python3
"""
专利撰写主控制器

整合所有模块，提供完整的专利撰写流程。
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    # 相对导入（作为模块使用时）
    from .disclosure_parser import DisclosureDocumentParser, DisclosureDocument
    from .technical_feature_extractor import TechnicalFeatureExtractor
    from .invention_understanding import InventionUnderstandingBuilder
    from .claim_generator import ClaimGenerator, ClaimGenerationOptions
    from .description_writer import DescriptionWriter
except ImportError:
    # 绝对导入（直接运行时）
    from core.patents.drafting.disclosure_parser import DisclosureDocumentParser, DisclosureDocument
    from core.patents.drafting.technical_feature_extractor import TechnicalFeatureExtractor
    from core.patents.drafting.invention_understanding import InventionUnderstandingBuilder
    from core.patents.drafting.claim_generator import ClaimGenerator, ClaimGenerationOptions
    from core.patents.drafting.description_writer import DescriptionWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DraftingOptions:
    """撰写选项"""
    claim_count: int = 3  # 权利要求数量
    include_background: bool = True  # 是否包含背景技术
    include_detailed_description: bool = True  # 是否包含具体实施方式
    writing_style: str = "formal"  # formal, concise, detailed
    use_llm: bool = False  # 是否使用LLM增强（预留）


@dataclass
class PatentApplication:
    """专利申请文件"""
    application_number: str = ""  # 申请号（生成时为空）
    filing_date: str = ""  # 申请日期
    title: str = ""  # 发明名称
    abstract: str = ""  # 摘要
    claims: list[str] = field(default_factory=list)  # 权利要求书
    technical_field: str = ""  # 技术领域
    background_art: str = ""  # 背景技术
    summary: str = ""  # 发明内容
    detailed_description: str = ""  # 具体实施方式
    drawings_description: list[str] = field(default_factory=list)  # 附图说明
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "application_number": self.application_number,
            "filing_date": self.filing_date,
            "title": self.title,
            "abstract": self.abstract,
            "claims": self.claims,
            "technical_field": self.technical_field,
            "background_art": self.background_art,
            "summary": self.summary,
            "detailed_description": self.detailed_description,
            "drawings_description": self.drawings_description,
            "metadata": self.metadata
        }

    def save_to_file(self, file_path: str) -> None:
        """保存到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {self.title}\n\n")
            f.write(f"## 摘要\n{self.abstract}\n\n")
            f.write(f"## 权利要求书\n")
            for claim in self.claims:
                f.write(f"{claim}\n")
            f.write(f"\n## 说明书\n\n")
            f.write(f"### 技术领域\n{self.technical_field}\n\n")
            f.write(f"### 背景技术\n{self.background_art}\n\n")
            f.write(f"### 发明内容\n{self.summary}\n\n")
            f.write(f"### 具体实施方式\n{self.detailed_description}\n")


class PatentDrafter:
    """专利撰写主控制器"""

    def __init__(self):
        """初始化撰写器"""
        self.parser = DisclosureDocumentParser()
        self.feature_extractor = TechnicalFeatureExtractor()
        self.understanding_builder = InventionUnderstandingBuilder()
        self.claim_generator = ClaimGenerator()
        self.description_writer = DescriptionWriter()
        logger.info("✅ 专利撰写主控制器初始化成功")

    async def draft_patent_application(
        self,
        disclosure_file: str,
        options: Optional[DraftingOptions] = None
    ) -> PatentApplication:
        """
        完整专利申请文件撰写流程

        Args:
            disclosure_file: 技术交底书文件路径
            options: 撰写选项

        Returns:
            PatentApplication对象
        """
        logger.info(f"🚀 开始专利撰写流程: {disclosure_file}")

        if options is None:
            options = DraftingOptions()

        try:
            # 1. 解析技术交底书
            logger.info("📄 步骤1: 解析技术交底书")
            disclosure = await self.parser.parse_disclosure(disclosure_file)

            if disclosure.confidence < 0.3:
                logger.warning(f"⚠️ 技术交底书解析置信度较低: {disclosure.confidence:.2f}")

            # 2. 提取技术特征
            logger.info("🔍 步骤2: 提取技术特征")
            features = await self.feature_extractor.extract_features(
                disclosure.raw_text,
                disclosure.sections
            )

            if not features:
                logger.warning("⚠️ 未提取到技术特征")

            # 3. 提取三元组
            logger.info("🔗 步骤3: 提取问题-特征-效果三元组")
            pfe_tuples = await self.feature_extractor.extract_problem_feature_effects(
                disclosure.raw_text,
                disclosure.sections,
                features
            )

            # 4. 构建发明理解
            logger.info("🧠 步骤4: 构建发明理解")
            understanding = await self.understanding_builder.build_understanding(
                {
                    "raw_text": disclosure.raw_text,
                    "sections": disclosure.sections,
                    "metadata": disclosure.metadata,
                    "confidence": disclosure.confidence
                },
                features,
                pfe_tuples
            )

            if understanding.confidence_score < 0.3:
                logger.warning(f"⚠️ 发明理解置信度较低: {understanding.confidence_score:.2f}")

            # 5. 生成权利要求书
            logger.info("📝 步骤5: 生成权利要求书")
            claim_options = ClaimGenerationOptions(
                claim_count=options.claim_count,
                writing_style=options.writing_style
            )
            claims = await self.claim_generator.generate_all_claims(
                understanding,
                claim_options
            )

            if not claims:
                logger.error("❌ 权利要求生成失败")
                raise ValueError("无法生成权利要求")

            # 6. 撰写说明书各部分
            logger.info("📝 步骤6: 撰写说明书")
            description_sections = await self.description_writer.write_all_sections(
                understanding,
                claims,
                embodiments=None  # 可以后续添加实施例
            )

            # 7. 组装完整申请文件
            logger.info("📦 步骤7: 组装申请文件")
            application = PatentApplication(
                title=understanding.invention_title,
                abstract=description_sections["abstract"],
                claims=claims,
                technical_field=description_sections["technical_field"],
                background_art=description_sections["background_art"] if options.include_background else "",
                summary=description_sections["summary"],
                detailed_description=description_sections["detailed_description"] if options.include_detailed_description else "",
                metadata={
                    "filing_date": datetime.now().strftime("%Y-%m-%d"),
                    "disclosure_file": disclosure_file,
                    "disclosure_confidence": disclosure.confidence,
                    "understanding_confidence": understanding.confidence_score,
                    "features_count": len(features),
                    "claims_count": len(claims)
                }
            )

            logger.info("✅ 专利撰写完成!")
            logger.info(f"   标题: {application.title}")
            logger.info(f"   权利要求数: {len(application.claims)}")
            logger.info(f"   摘要长度: {len(application.abstract)}")

            return application

        except Exception as e:
            logger.error(f"❌ 专利撰写失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def batch_draft(
        self,
        disclosure_files: list[str],
        options: Optional[DraftingOptions] = None
    ) -> list[PatentApplication]:
        """
        批量撰写专利申请

        Args:
            disclosure_files: 技术交底书文件列表
            options: 撰写选项

        Returns:
            专利申请列表
        """
        logger.info(f"🚀 开始批量专利撰写: {len(disclosure_files)} 个文件")

        # 并发处理
        tasks = [
            self.draft_patent_application(file, options)
            for file in disclosure_files
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常
        applications = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 文件 {disclosure_files[i]} 撰写失败: {result}")
            else:
                applications.append(result)

        logger.info(f"✅ 批量撰写完成: {len(applications)}/{len(disclosure_files)} 成功")
        return applications


async def test_patent_drafter():
    """测试专利撰写主控制器"""
    import sys
    from pathlib import Path

    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    from core.patents.drafting.patent_drafter import PatentDrafter, DraftingOptions

    drafter = PatentDrafter()

    print("\n" + "="*80)
    print("🚀 专利撰写主控制器测试")
    print("="*80)

    # 创建测试技术交底书
    test_disclosure = """
发明名称：一种基于深度学习的图像识别方法

技术领域：
本发明涉及计算机视觉和人工智能技术领域，具体涉及一种基于深度卷积神经网络的图像识别方法。

背景技术：
图像识别是计算机视觉领域的核心任务之一。传统的图像识别方法主要基于手工设计的特征，如SIFT、HOG等，结合机器学习分类器如SVM、随机森林等。这些方法需要大量领域知识来设计特征提取器，且对于复杂的图像识别任务效果有限。近年来，深度学习技术在图像识别领域取得了显著进展，但仍存在计算量大、对小样本数据鲁棒性差等问题。

技术问题：
本发明要解决的技术问题是：如何提高图像识别的准确率和鲁棒性，减少对手工特征工程的依赖，同时降低计算复杂度。

技术方案：
本发明提供一种基于深度学习的图像识别方法，包括：
输入层，用于接收待识别的图像数据；
卷积层，用于提取图像的多尺度特征，采用多尺度卷积核；
池化层，用于降维和特征选择，减少参数数量；
全连接层，用于基于提取的特征进行分类识别；
输出层，输出识别结果。

其中，卷积层采用3x3的卷积核，池化层采用2x2的池化窗口。

技术效果：
本发明能够自动提取图像特征，提高识别准确率15%以上；
通过多尺度特征融合，增强对不同尺度目标的识别能力；
采用优化的网络结构，减少计算量约30%；
具有良好的泛化能力，在小样本数据上也能保持较高的识别准确率。

具体实施方式：
如图1所示，本发明的图像识别方法采用深度卷积神经网络结构。
首先，输入层接收待识别图像，图像尺寸为224x224像素。
然后，卷积层提取图像特征，包括3个卷积层，每层使用64个3x3卷积核。
接着，池化层进行降维，池化窗口为2x2，步长为2。
全连接层接收池化层输出的特征向量，包含1024个神经元。
最后，输出层使用softmax激活函数输出各类别的概率。

本实施例在ImageNet数据集上进行测试，top-1准确率达到75.3%，top-5准确率达到92.2%。
"""

    # 保存测试文件
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_disclosure)
        temp_file = f.name

    try:
        # 执行撰写
        options = DraftingOptions(
            claim_count=3,
            include_background=True,
            include_detailed_description=True,
            writing_style="formal"
        )

        application = await drafter.draft_patent_application(temp_file, options)

        # 输出结果
        print(f"\n✅ 专利申请文件撰写完成:\n")
        print(f"【发明名称】{application.title}\n")
        print(f"【摘要】\n{application.abstract}\n")
        print(f"【权利要求书】({len(application.claims)}条)\n")
        for i, claim in enumerate(application.claims, 1):
            print(f"{claim}")

        print(f"\n【技术领域】\n{application.technical_field}\n")

        print(f"\n【元数据】")
        for key, value in application.metadata.items():
            print(f"  {key}: {value}")

        # 保存到文件
        output_file = tempfile.mktemp(suffix='_patent_application.txt')
        application.save_to_file(output_file)
        print(f"\n💾 申请文件已保存到: {output_file}")

        print("\n" + "="*80)
        print("✅ 测试完成")
        print("="*80)

    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == "__main__":
    # 设置路径
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    # 运行测试
    asyncio.run(test_patent_drafter())
