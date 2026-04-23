#!/usr/bin/env python3
"""
技术特征提取器

从技术交底书中提取技术特征和三元组关系。
"""
import asyncio
import logging
import re

from core.patents.data_structures import FeatureType, ProblemFeatureEffect, TechnicalFeature

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechnicalFeatureExtractor:
    """技术特征提取器"""

    def __init__(self):
        """初始化提取器"""
        logger.info("✅ 技术特征提取器初始化成功")

    async def extract_features(
        self,
        disclosure_text: str,
        sections: dict[str, str] | None = None
    ) -> list[TechnicalFeature]:
        """
        从技术交底书提取技术特征

        Args:
            disclosure_text: 技术交底书全文
            sections: 章节内容（如果已解析）

        Returns:
            技术特征列表
        """
        logger.info("🔍 开始提取技术特征")

        try:
            features = []

            # 1. 从技术方案中提取特征
            if sections and "技术方案" in sections:
                solution_text = sections["技术方案"]
            else:
                solution_text = self._extract_solution_section(disclosure_text)

            # 2. 提取组件特征
            component_features = self._extract_component_features(solution_text)
            features.extend(component_features)

            # 3. 提取步骤特征（如果是方法）
            step_features = self._extract_step_features(solution_text)
            features.extend(step_features)

            # 4. 提取参数特征
            param_features = self._extract_parameter_features(solution_text)
            features.extend(param_features)

            # 5. 分类特征类型
            features = self._classify_features(features)

            logger.info(f"✅ 提取到 {len(features)} 个技术特征")
            return features

        except Exception as e:
            logger.error(f"❌ 提取技术特征失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def extract_problem_feature_effects(
        self,
        disclosure_text: str,
        sections: dict[str, str] | None = None,
        features: list[TechnicalFeature] | None = None
    ) -> list[ProblemFeatureEffect]:
        """
        提取问题-特征-效果三元组

        Args:
            disclosure_text: 技术交底书全文
            sections: 章节内容
            features: 技术特征列表

        Returns:
            三元组列表
        """
        logger.info("🔗 开始提取问题-特征-效果三元组")

        try:
            pfe_tuples = []

            # 1. 提取技术问题
            if sections and "技术问题" in sections:
                problem = sections["技术问题"]
            else:
                problem = self._extract_problem_section(disclosure_text)

            # 2. 提取技术效果
            if sections and "技术效果" in sections:
                effects_text = sections["技术效果"]
            else:
                effects_text = self._extract_effects_section(disclosure_text)

            effects = self._parse_effects(effects_text)

            # 3. 关联技术特征
            if features:
                related_features = [f for f in features if f.feature_type == FeatureType.ESSENTIAL]
            else:
                related_features = []

            # 4. 构建三元组
            if problem and related_features:
                pfe = ProblemFeatureEffect(
                    id=f"PFE_{len(pfe_tuples) + 1}",
                    technical_problem=problem,
                    technical_features=related_features,
                    technical_effects=effects
                )
                pfe_tuples.append(pfe)

            logger.info(f"✅ 提取到 {len(pfe_tuples)} 个三元组")
            return pfe_tuples

        except Exception as e:
            logger.error(f"❌ 提取三元组失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_solution_section(self, text: str) -> str:
        """提取技术方案部分"""
        patterns = [
            r'技术方案[：:](.+?)(?=\n技术效果|\n具体实施方式|$)',
            r'采用[^\n]*?(?=\n技术效果|\n具体实施方式|$)',
            r'包括[^\n]*?(?=\n技术效果|\n具体实施方式|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_problem_section(self, text: str) -> str:
        """提取技术问题部分"""
        patterns = [
            r'技术问题[：:](.+?)(?=\n技术方案|$)',
            r'所要解决的技术问题[：:](.+?)(?=\n技术方案|$)',
            r'为了解决(.+?)(?=\n技术方案|，|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_effects_section(self, text: str) -> str:
        """提取技术效果部分"""
        patterns = [
            r'技术效果[：:](.+?)(?=\n具体实施方式|$)',
            r'有益效果[：:](.+?)(?=\n具体实施方式|$)',
            r'优点[：:](.+?)(?=\n具体实施方式|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_component_features(self, solution_text: str) -> list[TechnicalFeature]:
        """提取组件特征"""
        features = []

        # 匹配"XX层"、"XX模块"、"XX单元"等组件
        patterns = [
            r'([^\s，。]{2,8})(?:层|模块|单元|部件|装置|器件)',
            r'([^\s，。]{2,8})(?:器|机|设备)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, solution_text)
            for _i, match in enumerate(matches):
                feature = TechnicalFeature(
                    id=f"COMP_{len(features) + 1}",
                    description=match,
                    feature_type=FeatureType.ESSENTIAL,  # 默认为核心特征
                    component=match,
                    function=self._infer_function(match, solution_text)
                )
                features.append(feature)

        return features

    def _extract_step_features(self, solution_text: str) -> list[TechnicalFeature]:
        """提取步骤特征"""
        features = []

        # 匹配"步骤1"、"第一步骤"、"包括：XX"等
        patterns = [
            r'步骤[一二三四五六七八九十\d]+[：:]\s*([^\n，。]+)',
            r'第[一二三四五六七八九十\d]+步[：:]\s*([^\n，。]+)',
            r'包括[：:]\s*([^\n；；]+?)(?:；|，|。)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, solution_text)
            for _i, match in enumerate(matches):
                feature = TechnicalFeature(
                    id=f"STEP_{len(features) + 1}",
                    description=match.strip(),
                    feature_type=FeatureType.ESSENTIAL,
                    function=match.strip()
                )
                features.append(feature)

        return features

    def _extract_parameter_features(self, solution_text: str) -> list[TechnicalFeature]:
        """提取参数特征"""
        features = []

        # 匹配参数设置，如"卷积核大小为3x3"
        patterns = [
            r'([^\s，。]{2,10})(?:大小|数量|长度|宽度|厚度|重量)[：:]\s*([^\n，。]+)',
            r'([^\s，。]{2,10})为\s*([^\n，。]+?)(?:，|。|$)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, solution_text)
            for param_name, param_value in matches:
                feature = TechnicalFeature(
                    id=f"PARAM_{len(features) + 1}",
                    description=f"{param_name}为{param_value}",
                    feature_type=FeatureType.OPTIONAL,  # 参数通常是可选特征
                    component=param_name,
                    function=param_value
                )
                features.append(feature)

        return features

    def _classify_features(
        self,
        features: list[TechnicalFeature]
    ) -> list[TechnicalFeature]:
        """分类特征类型"""
        # 简单的分类逻辑
        # 核心特征：主要组件、关键步骤
        # 可选特征：参数、辅助功能

        for feature in features:
            # 如果特征描述包含"可选"、"可以"、"优选"等词，标记为可选
            if any(keyword in feature.description for keyword in ["可选", "可以", "优选", "例如"]):
                feature.feature_type = FeatureType.OPTIONAL
            else:
                feature.feature_type = FeatureType.ESSENTIAL

        return features

    def _infer_function(self, component: str, context: str) -> str:
        """推断组件功能"""
        # 查找组件所在句子
        pattern = rf'{component}[^\n]*?[，。；]'
        matches = re.findall(pattern, context)

        if matches:
            return matches[0].strip()

        return ""

    def _parse_effects(self, effects_text: str) -> list[str]:
        """解析技术效果"""
        effects = []

        # 按句子分割
        sentences = re.split(r'[，。；；]', effects_text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 5:  # 过滤太短的句子
                effects.append(sentence)

        return effects


async def test_feature_extractor():
    """测试技术特征提取器"""
    extractor = TechnicalFeatureExtractor()

    print("\n" + "="*80)
    print("🔍 技术特征提取器测试")
    print("="*80)

    # 测试文本
    test_disclosure = """
    发明名称：一种基于深度学习的图像识别方法

    技术领域：本发明涉及计算机视觉技术领域。

    背景技术：现有图像识别方法准确率低。

    技术问题：本发明要解决如何提高图像识别准确率的技术问题。

    技术方案：本发明提供一种图像识别方法，包括：输入层，用于接收图像；
    卷积层，用于提取特征；池化层，用于降维；全连接层，用于分类；
    输出层，输出结果。其中卷积核大小为3x3，池化窗口为2x2。

    技术效果：本发明能够提高识别准确率，具有良好的鲁棒性，可以减少计算量。

    具体实施方式：如图1所示...
    """

    # 提取技术特征
    features = await extractor.extract_features(test_disclosure)

    print(f"\n✅ 提取到 {len(features)} 个技术特征:")
    for i, feature in enumerate(features, 1):
        print(f"\n{i}. [{feature.feature_type.value}] {feature.description}")
        if feature.component:
            print(f"   组件: {feature.component}")
        if feature.function:
            print(f"   功能: {feature.function}")

    # 提取三元组
    pfe_tuples = await extractor.extract_problem_feature_effects(
        test_disclosure,
        features=features
    )

    print(f"\n\n✅ 提取到 {len(pfe_tuples)} 个问题-特征-效果三元组:")
    for i, pfe in enumerate(pfe_tuples, 1):
        print(f"\n{i}. 问题: {pfe.technical_problem}")
        print(f"   特征数: {len(pfe.technical_features)}")
        print(f"   效果数: {len(pfe.technical_effects)}")
        if pfe.technical_effects:
            print(f"   效果: {'; '.join(pfe.technical_effects[:3])}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_feature_extractor())
