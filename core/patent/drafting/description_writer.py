#!/usr/bin/env python3
"""
说明书撰写器

撰写专利说明书的各个部分。
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional

from core.patent.data_structures import InventionUnderstanding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DescriptionWriter:
    """说明书撰写器"""

    def __init__(self):
        """初始化撰写器"""
        logger.info("✅ 说明书撰写器初始化成功")

    async def write_technical_field(
        self,
        understanding: InventionUnderstanding
    ) -> str:
        """
        撰写技术领域部分

        Args:
            understanding: 发明理解结果

        Returns:
            技术领域文本
        """
        logger.info("📝 撰写技术领域部分")

        if understanding.technical_field:
            return understanding.technical_field

        # 生成默认技术领域
        return f"本发明涉及{understanding.technical_field or '相关'}技术领域。"

    async def write_background_art(
        self,
        understanding: InventionUnderstanding,
        prior_art: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        撰写背景技术部分

        Args:
            understanding: 发明理解结果
            prior_art: 现有技术（可选）

        Returns:
            背景技术文本
        """
        logger.info("📝 撰写背景技术部分")

        background_parts = []

        # 1. 技术领域介绍
        if understanding.technical_field:
            background_parts.append(f"{understanding.technical_field}是当前研究的热点领域。")

        # 2. 现有技术描述
        if prior_art:
            background_parts.append("现有技术中，")
            for i, art in enumerate(prior_art[:3], 1):
                background_parts.append(f"{i}. {art.get('description', '')}")
        else:
            # 生成默认的现有技术描述
            background_parts.append("然而，现有技术存在一定的局限性。")

        # 3. 技术问题（过渡到发明内容）
        if understanding.technical_problem:
            background_parts.append(f"\n因此，{understanding.technical_problem}")

        return "\n".join(background_parts)

    async def write_summary(
        self,
        understanding: InventionUnderstanding,
        claims: List[str]
    ) -> str:
        """
        撰写发明内容部分

        Args:
            understanding: 发明理解结果
            claims: 权利要求列表

        Returns:
            发明内容文本
        """
        logger.info("📝 撰写发明内容部分")

        summary_parts = []

        # 1. 技术问题
        if understanding.technical_problem:
            summary_parts.append(f"【要解决的技术问题】\n{understanding.technical_problem}\n")

        # 2. 技术方案
        if understanding.technical_solution:
            summary_parts.append(f"【技术方案】\n{understanding.technical_solution}\n")

        # 3. 技术效果
        if understanding.technical_effects:
            summary_parts.append("【有益效果】\n")
            summary_parts.append("与现有技术相比，本发明具有以下优点：\n")
            for i, effect in enumerate(understanding.technical_effects, 1):
                summary_parts.append(f"{i}. {effect}")
            summary_parts.append("\n")

        return "\n".join(summary_parts)

    async def write_detailed_description(
        self,
        understanding: InventionUnderstanding,
        claims: List[str],
        embodiments: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        撰写具体实施方式部分

        Args:
            understanding: 发明理解结果
            claims: 权利要求列表
            embodiments: 实施例（可选）

        Returns:
            具体实施方式文本
        """
        logger.info("📝 撰写具体实施方式部分")

        description_parts = []

        # 1. 引言
        description_parts.append("下面结合附图和具体实施例对本发明作进一步详细说明。")

        # 2. 实施例1
        description_parts.append("\n【实施例1】\n")
        description_parts.append(f"如图1所示，本实施例提供一种{understanding.invention_title}，")

        # 描述核心组件/步骤
        if understanding.essential_features:
            for i, feature in enumerate(understanding.essential_features, 1):
                if feature.component:
                    description_parts.append(f"\n{i}. {feature.component}：")
                    if feature.function:
                        description_parts.append(f"   用于{feature.function}。")
                else:
                    description_parts.append(f"\n{i}. {feature.description}")

        # 3. 工作原理/工作过程
        description_parts.append("\n\n【工作原理】\n")
        if understanding.technical_effects:
            description_parts.append("本发明通过上述技术方案，能够：\n")
            for effect in understanding.technical_effects[:3]:
                description_parts.append(f"- {effect}")

        # 4. 其他实施例（如果有可选特征）
        if understanding.optional_features:
            description_parts.append("\n\n【实施例2】\n")
            description_parts.append("本实施例与实施例1的区别在于：\n")
            for feature in understanding.optional_features[:2]:
                description_parts.append(f"- {feature.description}")

        # 5. 结语
        description_parts.append("\n\n以上所述仅为本发明的优选实施例，并不用于限制本发明。")

        return "\n".join(description_parts)

    async def write_abstract(
        self,
        understanding: InventionUnderstanding
    ) -> str:
        """
        撰写摘要部分

        Args:
            understanding: 发明理解结果

        Returns:
            摘要文本
        """
        logger.info("📝 撰写摘要部分")

        abstract_parts = []

        # 1. 发明名称
        abstract_parts.append(f"本发明公开了{understanding.invention_title}。")

        # 2. 技术方案
        if understanding.technical_solution:
            # 取前150个字
            solution = understanding.technical_solution[:150]
            if len(understanding.technical_solution) > 150:
                solution += "..."
            abstract_parts.append(solution)

        # 3. 技术效果
        if understanding.technical_effects:
            abstract_parts.append(f"能够{understanding.technical_effects[0]}。")

        return "".join(abstract_parts)

    async def write_all_sections(
        self,
        understanding: InventionUnderstanding,
        claims: List[str],
        prior_art: Optional[List[Dict[str, Any]]] = None,
        embodiments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, str]:
        """
        撰写说明书所有部分

        Args:
            understanding: 发明理解结果
            claims: 权利要求列表
            prior_art: 现有技术
            embodiments: 实施例

        Returns:
            说明书各部分字典
        """
        logger.info("📝 开始撰写说明书所有部分")

        # 并发撰写各部分
        technical_field, background, summary, detailed, abstract = await asyncio.gather(
            self.write_technical_field(understanding),
            self.write_background_art(understanding, prior_art),
            self.write_summary(understanding, claims),
            self.write_detailed_description(understanding, claims, embodiments),
            self.write_abstract(understanding)
        )

        return {
            "technical_field": technical_field,
            "background_art": background,
            "summary": summary,
            "detailed_description": detailed,
            "abstract": abstract
        }


async def test_description_writer():
    """测试说明书撰写器"""
    from core.patent.data_structures import InventionUnderstanding, InventionType, TechnicalFeature, FeatureType

    writer = DescriptionWriter()

    print("\n" + "="*80)
    print("📝 说明书撰写器测试")
    print("="*80)

    # 构建测试用的发明理解
    understanding = InventionUnderstanding(
        invention_title="基于深度学习的图像识别方法",
        invention_type=InventionType.METHOD,
        technical_field="计算机视觉和人工智能技术领域",
        core_innovation="使用深度卷积神经网络提取图像特征",
        technical_problem="现有图像识别方法准确率低、鲁棒性差",
        technical_solution="采用深度卷积神经网络结构，包括输入层、卷积层、池化层和全连接层",
        technical_effects=[
            "提高识别准确率",
            "减少计算量",
            "增强鲁棒性",
            "自动提取特征"
        ],
        essential_features=[
            TechnicalFeature(
                id="FEAT_1",
                description="接收待识别图像",
                feature_type=FeatureType.ESSENTIAL,
                component="输入层",
                function="接收图像"
            ),
            TechnicalFeature(
                id="FEAT_2",
                description="提取图像特征",
                feature_type=FeatureType.ESSENTIAL,
                component="卷积层",
                function="提取特征"
            ),
        ],
        optional_features=[
            TechnicalFeature(
                id="FEAT_4",
                description="卷积核大小为3x3",
                feature_type=FeatureType.OPTIONAL,
                component="卷积核",
                function="3x3大小"
            ),
        ],
        confidence_score=0.9
    )

    # 测试权利要求
    claims = [
        "1. 一种基于深度学习的图像识别方法，其特征在于，包括：输入层，用于接收待识别图像；卷积层，用于提取图像特征。",
        "2. 根据权利要求1所述的基于深度学习的图像识别方法，其特征在于，所述卷积核大小为3x3。"
    ]

    # 撰写各部分
    sections = await writer.write_all_sections(understanding, claims)

    print(f"\n✅ 说明书各部分:\n")

    print("【技术领域】")
    print(sections["technical_field"])
    print("\n" + "-"*80 + "\n")

    print("【摘要】")
    print(sections["abstract"])
    print("\n" + "-"*80 + "\n")

    print("【发明内容】")
    print(sections["summary"][:300] + "...")
    print("\n" + "-"*80 + "\n")

    print("【具体实施方式】")
    print(sections["detailed_description"][:400] + "...")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_description_writer())
