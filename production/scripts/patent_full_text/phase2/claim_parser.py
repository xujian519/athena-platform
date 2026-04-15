#!/usr/bin/env python3
"""
权利要求解析器
解析专利权利要求书，结构化提取权利要求信息

作者: Athena平台团队
创建时间: 2025-12-24
"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from enum import Enum

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClaimType(Enum):
    """权利要求类型"""
    INDEPENDENT = "independent"  # 独立权利要求
    DEPENDENT = "dependent"      # 从属权利要求


@dataclass
class Claim:
    """单条权利要求"""
    claim_number: int
    claim_type: ClaimType
    text: str
    depends_on: int | None = None  # 从属的权利要求号
    category: str = ""  # 类别（产品、方法、用途等）

    def __str__(self) -> str:
        return f"权利要求{self.claim_number}: {self.text[:50]}..."


@dataclass
class ParsedClaims:
    """解析后的权利要求书"""
    raw_text: str
    claims: list[Claim] = field(default_factory=list)
    independent_count: int = 0
    dependent_count: int = 0
    language: str = "unknown"

    def get_independent_claims(self) -> list[Claim]:
        """获取所有独立权利要求"""
        return [c for c in self.claims if c.claim_type == ClaimType.INDEPENDENT]

    def get_dependent_claims(self) -> list[Claim]:
        """获取所有从属权利要求"""
        return [c for c in self.claims if c.claim_type == ClaimType.DEPENDENT]

    def get_claim_by_number(self, number: int) -> Claim | None:
        """根据编号获取权利要求"""
        for claim in self.claims:
            if claim.claim_number == number:
                return claim
        return None


class ClaimParser:
    """权利要求解析器"""

    def __init__(self):
        """初始化解析器"""
        # 中文权利要求正则
        self.zh_claim_pattern = re.compile(r'(\d+)\.?\s*(.+?)(?=\n\s*\d+\.|$)', re.DOTALL)
        self.zh_dependent_pattern = re.compile(
            r'根据权利要求(\d+)所述的|如权利要求(\d+)所述|按照权利要求(\d+)',
            re.IGNORECASE
        )

        # 英文权利要求正则
        self.en_claim_pattern = re.compile(r'(\d+)\.\s*(.+?)(?=\n\s*\d+\.|$)', re.DOTALL)
        self.en_dependent_pattern = re.compile(
            r'(?:The|A|An)\s+\w+\s+(?:of\s+)?claim\s+(\d+)|according\s+to\s+claim\s+(\d+)',
            re.IGNORECASE
        )

    def parse(self, claims_text: str) -> ParsedClaims:
        """
        解析权利要求书

        Args:
            claims_text: 权利要求书文本

        Returns:
            ParsedClaims: 解析结果
        """
        if not claims_text or not claims_text.strip():
            return ParsedClaims(raw_text=claims_text, claims=[])

        # 检测语言
        language = self._detect_language(claims_text)

        # 解析权利要求
        claims = self._parse_claims(claims_text, language)

        # 统计
        independent_count = sum(1 for c in claims if c.claim_type == ClaimType.INDEPENDENT)
        dependent_count = sum(1 for c in claims if c.claim_type == ClaimType.DEPENDENT)

        result = ParsedClaims(
            raw_text=claims_text,
            claims=claims,
            independent_count=independent_count,
            dependent_count=dependent_count,
            language=language
        )

        logger.info(f"✅ 解析完成: {len(claims)}条权利要求 "
                   f"(独立{independent_count}条, 从属{dependent_count}条)")

        return result

    def _detect_language(self, text: str) -> str:
        """检测语言"""
        # 检查中文特征
        if '权利要求' in text or re.search(r'[\u4e00-\u9fff]{10,}', text):
            return "zh"
        # 检查英文特征
        if 'claim' in text.lower() or re.search(r'[a-z_a-Z]{50,}', text):
            return "en"
        return "unknown"

    def _parse_claims(self, text: str, language: str) -> list[Claim]:
        """解析权利要求列表"""
        if language == "zh":
            return self._parse_chinese_claims(text)
        elif language == "en":
            return self._parse_english_claims(text)
        else:
            # 尝试两种方式
            claims = self._parse_chinese_claims(text)
            if not claims:
                claims = self._parse_english_claims(text)
            return claims

    def _parse_chinese_claims(self, text: str) -> list[Claim]:
        """解析中文权利要求"""
        claims = []

        # 预处理：移除空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)

        # 使用正则匹配权利要求
        matches = self.zh_claim_pattern.finditer(text)

        for match in matches:
            claim_num = int(match.group(1))
            claim_text = match.group(2).strip()

            # 清理文本
            claim_text = self._clean_claim_text(claim_text)

            # 判断类型
            claim_type = ClaimType.INDEPENDENT
            depends_on = None

            # 检查是否从属
            dep_match = self.zh_dependent_pattern.search(claim_text)
            if dep_match:
                claim_type = ClaimType.DEPENDENT
                # 获取从属的权利要求号
                for group in dep_match.groups()[1:]:
                    if group:
                        depends_on = int(group)
                        break

            # 判断类别
            category = self._determine_category_zh(claim_text)

            claim = Claim(
                claim_number=claim_num,
                claim_type=claim_type,
                text=claim_text,
                depends_on=depends_on,
                category=category
            )
            claims.append(claim)

        return claims

    def _parse_english_claims(self, text: str) -> list[Claim]:
        """解析英文权利要求"""
        claims = []

        # 预处理
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)

        # 使用正则匹配
        matches = self.en_claim_pattern.finditer(text)

        for match in matches:
            claim_num = int(match.group(1))
            claim_text = match.group(2).strip()

            # 清理文本
            claim_text = self._clean_claim_text(claim_text)

            # 判断类型
            claim_type = ClaimType.INDEPENDENT
            depends_on = None

            # 检查是否从属
            dep_match = self.en_dependent_pattern.search(claim_text)
            if dep_match:
                claim_type = ClaimType.DEPENDENT
                for group in dep_match.groups():
                    if group:
                        depends_on = int(group)
                        break

            # 判断类别
            category = self._determine_category_en(claim_text)

            claim = Claim(
                claim_number=claim_num,
                claim_type=claim_type,
                text=claim_text,
                depends_on=depends_on,
                category=category
            )
            claims.append(claim)

        return claims

    def _clean_claim_text(self, text: str) -> str:
        """清理权利要求文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = text.strip()
        return text

    def _determine_category_zh(self, text: str) -> str:
        """判断中文权利要求类别"""
        if re.search(r'其特征在于|包括|包含|设有', text):
            return "产品"
        elif re.search(r'方法|步骤|工艺', text):
            return "方法"
        elif re.search(r'用途|应用|用于', text):
            return "用途"
        else:
            return "其他"

    def _determine_category_en(self, text: str) -> str:
        """判断英文权利要求类别"""
        text_lower = text.lower()
        if re.search(r'\bcomprising\b|\bwherein\b|\bcharacterized by\b', text_lower):
            return "product"
        elif re.search(r'\bmethod\b|\bstep\b', text_lower):
            return "method"
        elif re.search(r'\buse\b|\busing\b|\bapplication\b', text_lower):
            return "use"
        else:
            return "other"

    def extract_keywords(self, parsed_claims: ParsedClaims) -> dict[str, list[str]]:
        """
        从权利要求中提取关键词

        Args:
            parsed_claims: 解析后的权利要求

        Returns:
            Dict[str, List[str]]: 分类关键词字典
        """
        keywords = {
            "technical_features": [],
            "materials": [],
            "functions": [],
            "parameters": []
        }

        # 技术特征提取（简化版）
        for claim in parsed_claims.get_independent_claims():
            # 中文技术特征
            if parsed_claims.language == "zh":
                # 提取"包括"后面的内容
                including_match = re.search(r'包括[：:](.+?)(?:；|，|。|$)', claim.text)
                if including_match:
                    features = including_match.group(1).split('、')
                    keywords["technical_features"].extend([f.strip() for f in features[:5]])

                # 提取"所述"引用的特征
                mentioned = re.findall(r'所述([^，。；]{2,10})', claim.text)
                keywords["technical_features"].extend(mentioned[:5])

            # 英文技术特征
            else:
                # 提取comprising后面的内容
                comprising_match = re.search(r'comprising\s*[:\.]?\s*(.+?)(?:;|,|\.$)', claim.text, re.IGNORECASE)
                if comprising_match:
                    features = re.split(r',\s*(?:and\s+)?', comprising_match.group(1))
                    keywords["technical_features"].extend([f.strip() for f in features[:5]])

        # 去重并限制数量
        for key in keywords:
            keywords[key] = list(set(keywords[key]))[:20]

        return keywords


# ==================== 示例使用 ====================

def main() -> None:
    """示例使用"""
    parser = ClaimParser()

    # 示例1: 中文权利要求
    zh_claims_text = """
    1. 一种基于人工智能的图像识别方法，其特征在于，包括：
    获取待识别图像；
    使用预训练的深度学习模型对图像进行特征提取；
    根据提取的特征进行分类识别。

    2. 根据权利要求1所述的方法，其特征在于，所述深度学习模型为卷积神经网络。

    3. 根据权利要求1所述的方法，其特征在于，还包括：对图像进行预处理。
    """

    print("=" * 70)
    print("中文权利要求解析示例")
    print("=" * 70)

    parsed = parser.parse(zh_claims_text)

    print("\n📋 基本信息:")
    print(f"   权利要求数量: {len(parsed.claims)}")
    print(f"   独立权利要求: {parsed.independent_count}")
    print(f"   从属权利要求: {parsed.dependent_count}")
    print(f"   语言: {parsed.language}")

    print("\n📝 权利要求列表:")
    for claim in parsed.claims:
        print(f"\n   {claim}")
        print(f"      类型: {claim.claim_type.value}")
        if claim.depends_on:
            print(f"      从属于: 权利要求{claim.depends_on}")
        print(f"      类别: {claim.category}")

    # 提取关键词
    keywords = parser.extract_keywords(parsed)
    print("\n🔑 提取的关键词:")
    for key, values in keywords.items():
        if values:
            print(f"   {key}: {', '.join(values[:3])}...")

    # 示例2: 英文权利要求
    en_claims_text = """
    1. A method for image recognition using artificial intelligence, comprising:
    obtaining an image to be recognized;
    extracting features from the image using a pre-trained deep learning model;
    classifying the image based on the extracted features.

    2. The method of claim 1, wherein the deep learning model is a convolutional neural network.

    3. The method of claim 1, further comprising: preprocessing the image.
    """

    print("\n" + "=" * 70)
    print("英文权利要求解析示例")
    print("=" * 70)

    parsed_en = parser.parse(en_claims_text)

    print("\n📋 基本信息:")
    print(f"   权利要求数量: {len(parsed_en.claims)}")
    print(f"   独立权利要求: {parsed_en.independent_count}")
    print(f"   从属权利要求: {parsed_en.dependent_count}")
    print(f"   语言: {parsed_en.language}")


if __name__ == "__main__":
    main()
