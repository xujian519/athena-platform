#!/usr/bin/env python3
"""
发明理解模块

构建对发明的完整理解，包括发明类型、技术领域、核心创新点等。
"""
import asyncio
import logging
from typing import Any

from core.patents.data_structures import (
    FeatureType,
    InventionType,
    InventionUnderstanding,
    ProblemFeatureEffect,
    TechnicalFeature,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InventionUnderstandingBuilder:
    """发明理解构建器"""

    def __init__(self):
        """初始化构建器"""
        logger.info("✅ 发明理解构建器初始化成功")

    async def build_understanding(
        self,
        disclosure_data: dict[str, Any],
        features: list[TechnicalFeature],
        pfe_tuples: list[ProblemFeatureEffect]
    ) -> InventionUnderstanding:
        """
        构建发明理解结果

        Args:
            disclosure_data: 技术交底书数据
            features: 技术特征列表
            pfe_tuples: 三元组列表

        Returns:
            InventionUnderstanding对象
        """
        logger.info("🧠 开始构建发明理解")

        try:
            sections = disclosure_data.get("sections", {})
            raw_text = disclosure_data.get("raw_text", "")

            # 1. 确定发明类型
            invention_type = self._determine_invention_type(raw_text, features)

            # 2. 提取发明名称
            invention_title = self._extract_title(sections)

            # 3. 提取技术领域
            technical_field = self._extract_technical_field(sections)

            # 4. 总结核心创新点
            core_innovation = self._extract_core_innovation(sections, features)

            # 5. 提取技术问题
            technical_problem = self._extract_technical_problem(sections, pfe_tuples)

            # 6. 提取技术方案
            technical_solution = self._extract_technical_solution(sections, features)

            # 7. 提取技术效果
            technical_effects = self._extract_technical_effects(sections, pfe_tuples)

            # 8. 分类特征
            essential_features = [f for f in features if f.feature_type == FeatureType.ESSENTIAL]
            optional_features = [f for f in features if f.feature_type == FeatureType.OPTIONAL]

            # 9. 计算置信度
            confidence_score = self._calculate_confidence(
                sections, features, pfe_tuples
            )

            logger.info(f"✅ 发明理解构建完成，置信度: {confidence_score:.2f}")

            return InventionUnderstanding(
                invention_title=invention_title,
                invention_type=invention_type,
                technical_field=technical_field,
                core_innovation=core_innovation,
                technical_problem=technical_problem,
                technical_solution=technical_solution,
                technical_effects=technical_effects,
                essential_features=essential_features,
                optional_features=optional_features,
                confidence_score=confidence_score
            )

        except Exception as e:
            logger.error(f"❌ 构建发明理解失败: {e}")
            import traceback
            traceback.print_exc()

            # 返回默认的发明理解
            return InventionUnderstanding(
                invention_title="未知发明",
                invention_type=InventionType.PRODUCT,
                technical_field="",
                core_innovation="",
                technical_problem="",
                technical_solution="",
                technical_effects=[],
                essential_features=[],
                optional_features=[],
                confidence_score=0.0
            )

    def _determine_invention_type(
        self,
        text: str,
        features: list[TechnicalFeature]
    ) -> InventionType:
        """
        确定发明类型

        Args:
            text: 技术交底书文本
            features: 技术特征列表

        Returns:
            InventionType枚举值
        """

        # 检查是否包含方法关键词
        method_keywords = ["方法", "工艺", "步骤", "流程", "算法", "处理方法"]
        is_method = any(keyword in text for keyword in method_keywords)

        # 检查是否包含产品关键词
        product_keywords = ["装置", "设备", "器件", "系统", "部件", "组件", "单元"]
        is_product = any(keyword in text for keyword in product_keywords)

        # 检查是否包含用途关键词
        use_keywords = ["用途", "应用", "用于", "应用于"]
        is_use = any(keyword in text for keyword in use_keywords)

        # 优先级判断
        if is_use and not is_method:
            return InventionType.USE
        elif is_method and not is_product:
            return InventionType.METHOD
        elif is_product:
            return InventionType.PRODUCT
        else:
            # 默认为产品
            return InventionType.PRODUCT

    def _extract_title(self, sections: dict[str, str]) -> str:
        """提取发明名称"""
        # 从"发明名称"章节提取
        if "发明名称" in sections and sections["发明名称"]:
            return sections["发明名称"].strip()

        # 从文本开头提取
        return "未命名发明"

    def _extract_technical_field(self, sections: dict[str, str]) -> str:
        """提取技术领域"""
        if "技术领域" in sections and sections["技术领域"]:
            return sections["技术领域"].strip()

        return ""

    def _extract_core_innovation(
        self,
        sections: dict[str, str],
        features: list[TechnicalFeature]
    ) -> str:
        """提取核心创新点"""
        # 从技术方案提取
        if "技术方案" in sections and sections["技术方案"]:
            solution = sections["技术方案"]
            # 取前200个字作为核心创新点
            return solution[:200] + "..." if len(solution) > 200 else solution

        # 从特征列表提取
        if features:
            essential_names = [f.description for f in features if f.feature_type == FeatureType.ESSENTIAL]
            return "、".join(essential_names[:5])

        return ""

    def _extract_technical_problem(
        self,
        sections: dict[str, str],
        pfe_tuples: list[ProblemFeatureEffect]
    ) -> str:
        """提取技术问题"""
        # 优先从三元组提取
        if pfe_tuples:
            return pfe_tuples[0].technical_problem

        # 从章节提取
        if "技术问题" in sections and sections["技术问题"]:
            return sections["技术问题"].strip()

        return ""

    def _extract_technical_solution(
        self,
        sections: dict[str, str],
        features: list[TechnicalFeature]
    ) -> str:
        """提取技术方案"""
        # 从章节提取
        if "技术方案" in sections and sections["技术方案"]:
            return sections["技术方案"].strip()

        # 从特征构建
        if features:
            essential_descriptions = [f.description for f in features if f.feature_type == FeatureType.ESSENTIAL]
            return "、".join(essential_descriptions)

        return ""

    def _extract_technical_effects(
        self,
        sections: dict[str, str],
        pfe_tuples: list[ProblemFeatureEffect]
    ) -> list[str]:
        """提取技术效果"""
        effects = []

        # 从三元组提取
        for pfe in pfe_tuples:
            effects.extend(pfe.technical_effects)

        # 从章节提取
        if "技术效果" in sections and sections["技术效果"]:
            effects_text = sections["技术效果"]
            # 分割效果
            import re
            effect_sentences = re.split(r'[，。；；]', effects_text)
            effects.extend([e.strip() for e in effect_sentences if len(e.strip()) > 5])

        # 去重
        return list(set(effects))

    def _calculate_confidence(
        self,
        sections: dict[str, str],
        features: list[TechnicalFeature],
        pfe_tuples: list[ProblemFeatureEffect]
    ) -> float:
        """计算置信度"""
        confidence = 0.0

        # 关键章节存在性 (0.5分)
        key_sections = ["技术领域", "技术问题", "技术方案", "技术效果"]
        for section in key_sections:
            if section in sections and sections[section]:
                confidence += 0.125

        # 特征数量 (0.3分)
        if len(features) >= 3:
            confidence += 0.3
        elif len(features) >= 1:
            confidence += 0.1

        # 三元组完整性 (0.2分)
        if pfe_tuples and pfe_tuples[0].technical_problem:
            confidence += 0.1
        if pfe_tuples and pfe_tuples[0].technical_effects:
            confidence += 0.1

        return min(confidence, 1.0)


async def test_invention_understanding():
    """测试发明理解模块"""
    from .disclosure_parser import DisclosureDocumentParser
    from .technical_feature_extractor import TechnicalFeatureExtractor

    builder = InventionUnderstandingBuilder()
    DisclosureDocumentParser()
    extractor = TechnicalFeatureExtractor()

    print("\n" + "="*80)
    print("🧠 发明理解模块测试")
    print("="*80)

    # 测试数据
    test_disclosure = """
    发明名称：一种基于深度学习的图像识别方法

    技术领域：本发明涉及计算机视觉和人工智能技术领域。

    技术问题：本发明要解决如何提高图像识别准确率的技术问题。

    技术方案：本发明提供一种图像识别方法，包括：输入层，用于接收图像；
    卷积层，用于提取特征；池化层，用于降维；全连接层，用于分类；
    输出层，输出结果。

    技术效果：本发明能够提高识别准确率，具有良好的鲁棒性，可以减少计算量。

    具体实施方式：如图1所示...
    """

    # 解析文档
    disclosure_data = {
        "raw_text": test_disclosure,
        "sections": {
            "发明名称": "一种基于深度学习的图像识别方法",
            "技术领域": "本发明涉及计算机视觉和人工智能技术领域。",
            "技术问题": "本发明要解决如何提高图像识别准确率的技术问题。",
            "技术方案": "本发明提供一种图像识别方法，包括：输入层，用于接收图像；卷积层，用于提取特征；池化层，用于降维；全连接层，用于分类；输出层，输出结果。",
            "技术效果": "本发明能够提高识别准确率，具有良好的鲁棒性，可以减少计算量。",
        },
        "metadata": {},
        "confidence": 0.9
    }

    # 提取特征
    features = await extractor.extract_features(test_disclosure)

    # 提取三元组
    pfe_tuples = await extractor.extract_problem_feature_effects(
        test_disclosure,
        disclosure_data["sections"],
        features
    )

    # 构建发明理解
    understanding = await builder.build_understanding(
        disclosure_data,
        features,
        pfe_tuples
    )

    # 输出结果
    print("\n📋 发明理解结果:")
    print(f"  发明名称: {understanding.invention_title}")
    print(f"  发明类型: {understanding.invention_type.value}")
    print(f"  技术领域: {understanding.technical_field}")
    print(f"  核心创新点: {understanding.core_innovation[:100]}...")
    print(f"  技术问题: {understanding.technical_problem}")
    print(f"  技术方案: {understanding.technical_solution[:100]}...")
    print(f"  技术效果数量: {len(understanding.technical_effects)}")
    print(f"  核心特征数量: {len(understanding.essential_features)}")
    print(f"  可选特征数量: {len(understanding.optional_features)}")
    print(f"  置信度: {understanding.confidence_score:.2f}")

    if understanding.technical_effects:
        print("\n✨ 技术效果:")
        for i, effect in enumerate(understanding.technical_effects[:3], 1):
            print(f"  {i}. {effect}")

    if understanding.essential_features:
        print("\n🔧 核心特征:")
        for i, feature in enumerate(understanding.essential_features[:5], 1):
            print(f"  {i}. {feature.description}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_invention_understanding())
