#!/usr/bin/env python3
"""
涉案产品分析器

分析涉案产品/方法，提取技术特征。
"""
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any

try:
    from core.tools.enhanced_document_parser import EnhancedDocumentParser
    DOCUMENT_PARSER_AVAILABLE = True
except ImportError:
    DOCUMENT_PARSER_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProductFeature:
    """产品技术特征"""
    id: str
    description: str
    feature_type: str  # component, step, parameter, function
    details: str = ""  # 详细描述
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyzedProduct:
    """分析的产品"""
    product_name: str
    product_type: str  # product, method
    description: str
    features: List[ProductFeature]
    source: str = ""  # 信息来源
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "product_name": self.product_name,
            "product_type": self.product_type,
            "description": self.description,
            "features": [f.__dict__ for f in self.features],
            "source": self.source,
            "metadata": self.metadata
        }


class ProductAnalyzer:
    """涉案产品分析器"""

    def __init__(self):
        """初始化分析器"""
        self.parser = None
        if DOCUMENT_PARSER_AVAILABLE:
            try:
                self.parser = EnhancedDocumentParser()
                logger.info("✅ 文档解析器已加载")
            except Exception as e:
                logger.warning(f"文档解析器加载失败: {e}")

        logger.info("✅ 涉案产品分析器初始化成功")

    async def analyze_from_file(
        self,
        file_path: str,
        product_name: str = ""
    ) -> AnalyzedProduct:
        """
        从文件分析产品

        Args:
            file_path: 产品说明文件路径
            product_name: 产品名称（可选）

        Returns:
            AnalyzedProduct对象
        """
        logger.info(f"📦 从文件分析产品: {file_path}")

        # 解析文档
        if self.parser:
            try:
                parse_result = await self.parser.parse_document_async(
                    file_path,
                    use_ocr=True
                )
                description = parse_result.get("raw_text", "")
            except Exception as e:
                logger.error(f"文档解析失败: {e}")
                description = Path(file_path).read_text(encoding='utf-8')
        else:
            description = Path(file_path).read_text(encoding='utf-8')

        # 提取产品信息
        if not product_name:
            product_name = Path(file_path).stem

        # 分析产品类型
        product_type = self._determine_product_type(description)

        # 提取技术特征
        features = self._extract_product_features(description)

        analyzed_product = AnalyzedProduct(
            product_name=product_name,
            product_type=product_type,
            description=description[:500],  # 限制长度
            features=features,
            source=file_path
        )

        logger.info(f"✅ 产品分析完成: {product_name}")
        logger.info(f"   产品类型: {product_type}")
        logger.info(f"   特征数: {len(features)}")

        return analyzed_product

    def analyze_from_description(
        self,
        description: str,
        product_name: str = "涉案产品"
    ) -> AnalyzedProduct:
        """
        从描述文本分析产品

        Args:
            description: 产品描述文本
            product_name: 产品名称

        Returns:
            AnalyzedProduct对象
        """
        logger.info(f"📦 从描述分析产品: {product_name}")

        # 分析产品类型
        product_type = self._determine_product_type(description)

        # 提取技术特征
        features = self._extract_product_features(description)

        analyzed_product = AnalyzedProduct(
            product_name=product_name,
            product_type=product_type,
            description=description[:500],
            features=features,
            source="user_input"
        )

        logger.info(f"✅ 产品分析完成")
        logger.info(f"   产品类型: {product_type}")
        logger.info(f"   特征数: {len(features)}")

        return analyzed_product

    def _determine_product_type(self, description: str) -> str:
        """
        判断产品类型（产品/方法）

        Args:
            description: 产品描述

        Returns:
            "product" 或 "method"
        """
        # 方法类关键词
        method_keywords = ['方法', '工艺', '步骤', '流程', '过程', '方法包括']

        # 检查是否包含方法类关键词
        for keyword in method_keywords:
            if keyword in description:
                return "method"

        # 默认为产品类
        return "product"

    def _extract_product_features(self, description: str) -> List[ProductFeature]:
        """
        从描述中提取技术特征

        Args:
            description: 产品描述

        Returns:
            技术特征列表
        """
        features = []

        # 按句号或分号分割
        sentences = re.split(r'[。；;]', description)

        for idx, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 5:  # 过滤太短的句子
                continue

            # 识别特征类型
            feature_type = self._classify_feature(sentence)

            # 提取参数（数字、尺寸等）
            parameters = self._extract_parameters(sentence)

            feature = ProductFeature(
                id=f"product_feature_{idx+1}",
                description=sentence,
                feature_type=feature_type,
                parameters=parameters
            )

            features.append(feature)

        logger.info(f"   提取到 {len(features)} 个技术特征")

        return features

    def _classify_feature(self, sentence: str) -> str:
        """
        分类特征类型

        Args:
            sentence: 特征描述

        Returns:
            特征类型
        """
        # 组件类关键词
        component_keywords = ['包括', '包含', '设有', '设置', '具有', '安装']

        # 步骤类关键词
        step_keywords = ['步骤', '然后', '接着', '之后', '首先', '其次', '最后']

        # 参数类关键词
        parameter_keywords = ['为', '等于', '范围', '大小', '尺寸']

        # 功能类关键词
        function_keywords = ['用于', '配置为', '实现', '能够', '可以']

        # 检查特征类型
        if any(kw in sentence for kw in step_keywords):
            return "step"
        elif any(kw in sentence for kw in function_keywords):
            return "function"
        elif any(kw in sentence for kw in parameter_keywords):
            return "parameter"
        else:
            return "component"

    def _extract_parameters(self, sentence: str) -> Dict[str, Any]:
        """
        提取参数信息

        Args:
            sentence: 特征描述

        Returns:
            参数字典
        """
        parameters = {}

        # 提取数字
        numbers = re.findall(r'\d+\.?\d*', sentence)
        if numbers:
            parameters['numbers'] = [float(n) for n in numbers]

        # 提取尺寸信息
        size_pattern = r'(\d+\.?\d*)\s*(mm|cm|m|μm|nm)'
        sizes = re.findall(size_pattern, sentence)
        if sizes:
            parameters['sizes'] = [{'value': float(s[0]), 'unit': s[1]} for s in sizes]

        # 提取范围
        range_pattern = r'(\d+\.?\d*)\s*[-~至到]\s*(\d+\.?\d*)'
        ranges = re.findall(range_pattern, sentence)
        if ranges:
            parameters['ranges'] = [{'min': float(r[0]), 'max': float(r[1])} for r in ranges]

        return parameters
