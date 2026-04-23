#!/usr/bin/env python3
"""
权利要求生成器

生成独立权利要求和从属权利要求。
"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from core.patents.data_structures import (
    InventionUnderstanding,
    TechnicalFeature,
    FeatureType,
    InventionType
)
from core.llm.unified_llm_manager import UnifiedLLMManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ClaimGenerationOptions:
    """权利要求生成选项"""
    claim_count: int = 3  # 总权利要求数量
    include_method_claims: bool = True  # 是否包含方法权利要求（如果是产品发明）
    detailed_features: bool = True  # 是否详细描述特征
    writing_style: str = "formal"  # formal, concise, detailed


class ClaimGenerator:
    """权利要求生成器"""

    def __init__(self):
        """初始化生成器"""
        self.llm_manager = UnifiedLLMManager()
        logger.info("✅ 权利要求生成器初始化成功")

    async def generate_independent_claim(
        self,
        understanding: InventionUnderstanding,
        options: Optional[ClaimGenerationOptions] = None
    ) -> str:
        """
        生成独立权利要求

        Args:
            understanding: 发明理解结果
            options: 生成选项

        Returns:
            独立权利要求文本
        """
        logger.info("📝 开始生成独立权利要求")

        try:
            if options is None:
                options = ClaimGenerationOptions()

            # 1. 构建前序部分
            preamble = self._build_preamble(understanding)

            # 2. 构建特征部分
            features_clause = await self._build_features_clause(
                understanding,
                options
            )

            # 3. 组装独立权利要求
            claim = f"1. {preamble}{features_clause}。"

            logger.info("✅ 独立权利要求生成完成")
            return claim

        except Exception as e:
            logger.error(f"❌ 生成独立权利要求失败: {e}")
            import traceback
            traceback.print_exc()
            return "1. 一种未定义的发明，其特征在于，包括基础组件。"

    async def generate_dependent_claims(
        self,
        understanding: InventionUnderstanding,
        independent_claim: str,
        options: Optional[ClaimGenerationOptions] = None
    ) -> List[str]:
        """
        生成从属权利要求

        Args:
            understanding: 发明理解结果
            independent_claim: 独立权利要求
            options: 生成选项

        Returns:
            从属权利要求列表
        """
        logger.info("📝 开始生成从属权利要求")

        try:
            if options is None:
                options = ClaimGenerationOptions()

            dependent_claims = []

            # 获取可选特征
            optional_features = understanding.optional_features
            if not optional_features:
                # 如果没有可选特征，将部分核心特征细化为从属权利要求
                essential_features = understanding.essential_features
                optional_features = essential_features[1:]  # 从第二个开始

            # 为每个可选特征生成从属权利要求
            for i, feature in enumerate(optional_features[:options.claim_count - 1], 2):
                claim = await self._generate_dependent_claim(
                    i,
                    feature,
                    understanding,
                    options
                )
                dependent_claims.append(claim)

            logger.info(f"✅ 生成 {len(dependent_claims)} 条从属权利要求")
            return dependent_claims

        except Exception as e:
            logger.error(f"❌ 生成从属权利要求失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _build_preamble(self, understanding: InventionUnderstanding) -> str:
        """
        构建前序部分

        Args:
            understanding: 发明理解结果

        Returns:
            前序部分文本
        """
        # 根据发明类型构建前序
        if understanding.invention_type == InventionType.METHOD:
            return f"一种{understanding.invention_title}"
        elif understanding.invention_type == InventionType.USE:
            return f"{understanding.invention_title}的用途"
        else:  # PRODUCT
            return f"一种{understanding.invention_title}"

    async def _build_features_clause(
        self,
        understanding: InventionUnderstanding,
        options: ClaimGenerationOptions
    ) -> str:
        """
        构建特征部分

        Args:
            understanding: 发明理解结果
            options: 生成选项

        Returns:
            特征部分文本
        """
        # 获取核心特征
        essential_features = understanding.essential_features

        if not essential_features:
            return "，包括基础组件"

        # 组织特征
        if understanding.invention_type == InventionType.METHOD:
            # 方法发明：按步骤组织
            features_text = self._organize_step_features(essential_features)
        else:
            # 产品发明：按组件组织
            features_text = self._organize_component_features(essential_features)

        return features_text

    def _organize_component_features(self, features: List[TechnicalFeature]) -> str:
        """组织组件特征"""
        feature_descriptions = []

        for feature in features:
            if feature.component:
                desc = feature.component
                if feature.function and len(feature.function) > 5:
                    desc += f"，用于{feature.function}"
                feature_descriptions.append(desc)
            else:
                feature_descriptions.append(feature.description)

        if len(feature_descriptions) == 1:
            return f"，其特征在于，包括{feature_descriptions[0]}"
        else:
            return f"，其特征在于，包括{'；'.join(feature_descriptions[:-1])}；以及{feature_descriptions[-1]}"

    def _organize_step_features(self, features: List[TechnicalFeature]) -> str:
        """组织步骤特征"""
        feature_descriptions = []

        for feature in features:
            if feature.description:
                feature_descriptions.append(feature.description)

        if len(feature_descriptions) == 1:
            return f"，其特征在于，包括{feature_descriptions[0]}"
        else:
            return f"，其特征在于，包括以下步骤：{'；'.join(feature_descriptions)}"

    async def _generate_dependent_claim(
        self,
        claim_number: int,
        feature: TechnicalFeature,
        understanding: InventionUnderstanding,
        options: ClaimGenerationOptions
    ) -> str:
        """
        生成单条从属权利要求

        Args:
            claim_number: 权利要求编号
            feature: 技术特征
            understanding: 发明理解结果
            options: 生成选项

        Returns:
            从属权利要求文本
        """
        # 引用在先权利要求
        reference = f"根据权利要求{claim_number - 1}"

        # 构建特征限定
        if feature.component:
            limitation = f"所述{feature.component}"
            if feature.function and len(feature.function) > 5:
                limitation += f"{feature.function}"
            else:
                limitation += f"的具体配置为{feature.description}"
        else:
            limitation = f"其特征在于{feature.description}"

        return f"{claim_number}. {reference}所述的{understanding.invention_title}，{limitation}。"

    async def generate_all_claims(
        self,
        understanding: InventionUnderstanding,
        options: Optional[ClaimGenerationOptions] = None
    ) -> List[str]:
        """
        生成所有权利要求

        Args:
            understanding: 发明理解结果
            options: 生成选项

        Returns:
            权利要求列表
        """
        logger.info("📝 开始生成所有权利要求")

        # 1. 生成独立权利要求
        independent_claim = await self.generate_independent_claim(
            understanding,
            options
        )

        # 2. 生成从属权利要求
        dependent_claims = await self.generate_dependent_claims(
            understanding,
            independent_claim,
            options
        )

        # 3. 组装所有权利要求
        all_claims = [independent_claim] + dependent_claims

        logger.info(f"✅ 共生成 {len(all_claims)} 条权利要求")
        return all_claims


async def test_claim_generator():
    """测试权利要求生成器"""
    from core.patents.data_structures import InventionUnderstanding, InventionType, TechnicalFeature, FeatureType

    generator = ClaimGenerator()

    print("\n" + "="*80)
    print("📝 权利要求生成器测试")
    print("="*80)

    # 构建测试用的发明理解
    understanding = InventionUnderstanding(
        invention_title="基于深度学习的图像识别方法",
        invention_type=InventionType.METHOD,
        technical_field="计算机视觉技术领域",
        core_innovation="使用深度卷积神经网络提取图像特征",
        technical_problem="现有图像识别方法准确率低",
        technical_solution="采用深度卷积神经网络结构",
        technical_effects=["提高识别准确率", "减少计算量", "增强鲁棒性"],
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
            TechnicalFeature(
                id="FEAT_3",
                description="降维处理",
                feature_type=FeatureType.ESSENTIAL,
                component="池化层",
                function="降维"
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
            TechnicalFeature(
                id="FEAT_5",
                description="池化窗口为2x2",
                feature_type=FeatureType.OPTIONAL,
                component="池化窗口",
                function="2x2大小"
            ),
        ],
        confidence_score=0.9
    )

    # 生成权利要求
    options = ClaimGenerationOptions(claim_count=3)
    claims = await generator.generate_all_claims(understanding, options)

    print(f"\n✅ 生成 {len(claims)} 条权利要求:\n")
    for i, claim in enumerate(claims, 1):
        print(f"{claim}\n")

    print("="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_claim_generator())
