#!/usr/bin/env python3
"""
权利要求解析器 V2
Claim Parser V2

支持分条款解析、权利要求编号识别、引用关系解析

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ClaimType(Enum):
    """权利要求类型"""
    INDEPENDENT = "independent"  # 独立权利要求
    DEPENDENT = "dependent"      # 从属权利要求


@dataclass
class ClaimData:
    """权利要求数据"""
    claim_number: int           # 权利要求编号 (1, 2, 3...)
    claim_type: ClaimType       # 独立/从属
    claim_text: str             # 权利要求完整文本
    claim_body: str             # 权利要求主体（去除前缀）

    # 引用关系（从属权利要求专用）
    referenced_claims: list[int] = field(default_factory=list)  # 引用的权利要求编号

    # 结构化信息
    preamble: str = ""          # 前序部分（一种...，其特征在于...）
    characterizing: str = ""    # 特征部分
    features: list[str] = field(default_factory=list)  # 特征列表

    # 统计信息
    word_count: int = 0
    char_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "claim_number": self.claim_number,
            "claim_type": self.claim_type.value,
            "claim_text": self.claim_text,
            "claim_body": self.claim_body,
            "referenced_claims": self.referenced_claims,
            "preamble": self.preamble,
            "characterizing": self.characterizing,
            "features": self.features,
            "word_count": self.word_count,
            "char_count": self.char_count
        }


@dataclass
class ParsedClaims:
    """解析结果"""
    patent_number: str
    success: bool

    # 解析的权利要求
    independent_claims: list[ClaimData] = field(default_factory=list)
    dependent_claims: list[ClaimData] = field(default_factory=list)

    # 统计信息
    total_claim_count: int = 0
    processing_time: float = 0.0
    error_message: str | None = None

    @property
    def all_claims(self) -> list[ClaimData]:
        """获取所有权利要求"""
        return self.independent_claims + self.dependent_claims

    def get_claim(self, claim_number: int) -> ClaimData | None:
        """根据编号获取权利要求"""
        for claim in self.all_claims:
            if claim.claim_number == claim_number:
                return claim
        return None

    def get_summary(self) -> dict[str, Any]:
        """获取解析摘要"""
        return {
            "patent_number": self.patent_number,
            "success": self.success,
            "total_claims": self.total_claim_count,
            "independent_count": len(self.independent_claims),
            "dependent_count": len(self.dependent_claims),
            "processing_time": self.processing_time
        }


class ClaimParserV2:
    """
    权利要求解析器V2

    支持功能:
    1. 分条款解析（独立/从属）
    2. 权利要求编号识别
    3. 引用关系解析
    4. 前序部分/特征部分提取
    5. 特征列表提取
    """

    # 权利要求前缀正则
    CLAIM_PREFIX_PATTERN = re.compile(
        r'^(\d+)\.?\s*',  # 匹配 "1." 或 "1." 开头
        re.MULTILINE
    )

    # 从属权利要求引用模式
    REFERENCE_PATTERN = re.compile(
        r'根据权利要求(\d+(?:\s*[,，、]\s*\d+)*)',  # 匹配 "根据权利要求1、2、3"
        re.IGNORECASE
    )

    # 特征部分分隔符
    CHARACTERIZING_PATTERN = re.compile(
        r'(?:其特征在于|特征在于)(?:，|：|:|，|。)',
        re.IGNORECASE
    )

    # 特征分隔符（用于分号、句号分割）
    FEATURE_SEPARATOR_PATTERN = re.compile(
        r'[；;]\s*(?=[^\d]+|$)'  # 分号后跟非数字
    )

    def __init__(self, enable_structure_parsing: bool = True):
        """
        初始化解析器

        Args:
            enable_structure_parsing: 是否启用结构化解析（前序/特征部分）
        """
        self.enable_structure_parsing = enable_structure_parsing

    def parse(self, patent_number: str, claims_text: str) -> ParsedClaims:
        """
        解析权利要求书

        Args:
            patent_number: 专利号
            claims_text: 权利要求书全文

        Returns:
            ParsedClaims 解析结果
        """
        import time
        start_time = time.time()

        try:
            # 1. 分割权利要求
            claims = self._split_claims(claims_text)

            # 2. 解析每个权利要求
            independent = []
            dependent = []

            for claim_text in claims:
                claim_data = self._parse_single_claim(claim_text)

                if claim_data.claim_type == ClaimType.INDEPENDENT:
                    independent.append(claim_data)
                else:
                    dependent.append(claim_data)

            # 3. 构建结果
            result = ParsedClaims(
                patent_number=patent_number,
                success=True,
                independent_claims=independent,
                dependent_claims=dependent,
                total_claim_count=len(independent) + len(dependent),
                processing_time=time.time() - start_time
            )

            logger.info(f"✅ 解析完成: {result.total_claim_count}条权利要求 "
                       f"({len(independent)}独立 + {len(dependent)}从属)")

            return result

        except Exception as e:
            logger.error(f"❌ 解析失败: {e}")
            return ParsedClaims(
                patent_number=patent_number,
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )

    def _split_claims(self, claims_text: str) -> list[str]:
        """
        分割权利要求

        支持:
        1. "1." 开头的格式
        2. 换行分隔
        """
        # 清理文本
        claims_text = claims_text.strip()
        if not claims_text:
            return []

        # 方法1: 使用正则分割
        matches = list(self.CLAIM_PREFIX_PATTERN.finditer(claims_text))

        if len(matches) > 1:
            # 找到多个权利要求
            claims = []
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(claims_text)
                claim_text = claims_text[start:end].strip()
                if claim_text:
                    claims.append(claim_text)
            return claims

        # 方法2: 按换行符分割
        lines = claims_text.split('\n')
        claims = []
        current_claim = []

        for line in lines:
            line = line.strip()
            if not line:
                if current_claim:
                    claims.append('\n'.join(current_claim))
                    current_claim = []
                continue

            # 检查是否是新权利要求开始
            if self.CLAIM_PREFIX_PATTERN.match(line) and current_claim:
                claims.append('\n'.join(current_claim))
                current_claim = [line]
            else:
                current_claim.append(line)

        if current_claim:
            claims.append('\n'.join(current_claim))

        return claims

    def _parse_single_claim(self, claim_text: str) -> ClaimData:
        """
        解析单个权利要求

        Args:
            claim_text: 权利要求文本

        Returns:
            ClaimData
        """
        # 1. 提取权利要求编号
        claim_number = self._extract_claim_number(claim_text)

        # 2. 判断权利要求类型
        claim_type, referenced_claims = self._determine_claim_type(claim_text)

        # 3. 去除编号前缀
        claim_body = self.CLAIM_PREFIX_PATTERN.sub('', claim_text).strip()

        # 4. 结构化解析（可选）
        preamble = ""
        characterizing = ""
        features = []

        if self.enable_structure_parsing:
            preamble, characterizing = self._extract_preamble_characterizing(claim_body)
            features = self._extract_features(claim_body)

        # 5. 统计信息
        word_count = len(claim_body)
        char_count = len(claim_body.replace(' ', ''))

        return ClaimData(
            claim_number=claim_number,
            claim_type=claim_type,
            claim_text=claim_text,
            claim_body=claim_body,
            referenced_claims=referenced_claims,
            preamble=preamble,
            characterizing=characterizing,
            features=features,
            word_count=word_count,
            char_count=char_count
        )

    def _extract_claim_number(self, claim_text: str) -> int:
        """提取权利要求编号"""
        match = self.CLAIM_PREFIX_PATTERN.match(claim_text)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass
        return 0

    def _determine_claim_type(self, claim_text: str) -> tuple:
        """
        判断权利要求类型并提取引用

        Returns:
            (ClaimType, referenced_claims_list)
        """
        # 查找引用模式
        match = self.REFERENCE_PATTERN.search(claim_text)

        if match:
            # 从属权利要求
            ref_str = match.group(1)
            # 解析引用的权利要求编号（支持逗号、顿号分隔）
            referenced = []
            for num_str in re.split(r'[,，、]\s*', ref_str):
                try:
                    referenced.append(int(num_str.strip()))
                except ValueError:
                    continue

            return ClaimType.DEPENDENT, referenced

        # 独立权利要求
        return ClaimType.INDEPENDENT, []

    def _extract_preamble_characterizing(self, claim_body: str) -> tuple:
        """
        提取前序部分和特征部分

        Returns:
            (preamble, characterizing)
        """
        match = self.CHARACTERIZING_PATTERN.search(claim_body)

        if match:
            split_pos = match.end()
            preamble = claim_body[:match.start()].strip()
            characterizing = claim_body[split_pos:].strip()
            return preamble, characterizing

        # 没有找到"其特征在于"，整体作为前序部分
        return claim_body, ""

    def _extract_features(self, claim_body: str) -> list[str]:
        """
        提取特征列表

        简单实现: 按分号分割
        """
        features = []

        # 尝试从特征部分提取
        match = self.CHARACTERIZING_PATTERN.search(claim_body)
        if match:
            characterizing_part = claim_body[match.end():]
            # 按分号分割
            raw_features = self.FEATURE_SEPARATOR_PATTERN.split(characterizing_part)
            features = [f.strip().rstrip('。；;') for f in raw_features if f.strip()]
        else:
            # 整体作为单个特征
            features = [claim_body.rstrip('。；;')]

        return features


# ========== 便捷函数 ==========

def parse_claims(patent_number: str, claims_text: str, **kwargs) -> ParsedClaims:
    """
    解析权利要求书

    Args:
        patent_number: 专利号
        claims_text: 权利要求书全文
        **kwargs: 传递给ClaimParserV2的参数

    Returns:
        ParsedClaims 解析结果
    """
    parser = ClaimParserV2(**kwargs)
    return parser.parse(patent_number, claims_text)


# ========== 示例使用 ==========

def main() -> None:
    """示例使用"""
    print("=" * 70)
    print("权利要求解析器V2 示例")
    print("=" * 70)

    # 示例权利要求书
    sample_claims = """
1. 一种基于人工智能的图像识别方法，其特征在于，包括以下步骤：
    获取待识别图像；
    使用深度学习模型提取图像特征；
    根据所述图像特征进行分类识别，得到识别结果。

2. 根据权利要求1所述的图像识别方法，其特征在于，
    所述深度学习模型为卷积神经网络模型，包括：
    特征提取层，用于提取图像的多层特征；
    注意力机制模块，用于加权融合所述多层特征；
    分类输出层，用于输出分类结果。

3. 根据权利要求1或2所述的图像识别方法，其特征在于，
    所述待识别图像为医学影像图像。
    """

    # 解析
    result = parse_claims("CN112233445A", sample_claims)

    print("\n📋 解析结果:")
    summary = result.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print(f"\n📄 独立权利要求 ({len(result.independent_claims)}条):")
    for claim in result.independent_claims:
        print(f"  权利要求{claim.claim_number}: {claim.claim_body[:50]}...")
        if claim.features:
            print(f"    特征数: {len(claim.features)}")

    print(f"\n📄 从属权利要求 ({len(result.dependent_claims)}条):")
    for claim in result.dependent_claims:
        print(f"  权利要求{claim.claim_number}: 引用{claim.referenced_claims}")
        print(f"    {claim.claim_body[:50]}...")


if __name__ == "__main__":
    main()
