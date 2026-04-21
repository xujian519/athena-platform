#!/usr/bin/env python3
"""
权利要求解析器

解析权利要求文本，提取保护范围和技术特征。
"""
import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ParsedFeature:
    """解析的技术特征"""
    id: str
    description: str
    feature_type: str  # essential, optional, functional
    component: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedClaim:
    """解析的权利要求"""
    claim_number: int
    claim_type: str  # independent, dependent
    preamble: str  # 前序部分
    transition_word: str  # 过渡词（"包括"、"包含"、"其特征在于"等）
    body: str  # 主体部分
    features: List[ParsedFeature]  # 技术特征列表
    dependent_from: int = 0  # 引用的权利要求（从属权利要求）
    full_text: str = ""  # 完整文本

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "claim_number": self.claim_number,
            "claim_type": self.claim_type,
            "preamble": self.preamble,
            "transition_word": self.transition_word,
            "body": self.body,
            "features": [f.__dict__ for f in self.features],
            "dependent_from": self.dependent_from,
            "full_text": self.full_text
        }


class ClaimParser:
    """权利要求解析器"""

    # 过渡词模式
    TRANSITION_PATTERNS = [
        r'其特征在于[：:,]?\s*',
        r'包括[：:,]?\s*',
        r'包含[：:,]?\s*',
        r'具有[：:,]?\s*',
        r'其中[：:,]?\s*',
    ]

    # 从属权利要求引用模式
    DEPENDENT_PATTERN = r'根据权利要求(\d+)[所述之]'

    def __init__(self):
        """初始化解析器"""
        self.transition_regex = re.compile('|'.join(self.TRANSITION_PATTERNS))
        self.dependent_regex = re.compile(self.DEPENDENT_PATTERN)
        logger.info("✅ 权利要求解析器初始化成功")

    def parse_claim(self, claim_text: str, claim_number: int) -> ParsedClaim:
        """
        解析单条权利要求

        Args:
            claim_text: 权利要求文本
            claim_number: 权利要求编号

        Returns:
            ParsedClaim对象
        """
        logger.info(f"📜 解析权利要求 {claim_number}")

        # 清理文本
        claim_text = claim_text.strip()
        if claim_text.startswith(f"{claim_number}"):
            claim_text = claim_text[len(str(claim_number)):].strip()
        if claim_text.startswith("."):
            claim_text = claim_text[1:].strip()

        # 判断是否为从属权利要求
        dependent_match = self.dependent_regex.search(claim_text)
        if dependent_match:
            claim_type = "dependent"
            dependent_from = int(dependent_match.group(1))
        else:
            claim_type = "independent"
            dependent_from = 0

        # 提取前序部分和过渡词
        preamble, transition, body = self._split_claim_sections(claim_text)

        # 提取技术特征
        features = self._extract_features(body)

        # 构建解析结果
        parsed_claim = ParsedClaim(
            claim_number=claim_number,
            claim_type=claim_type,
            preamble=preamble,
            transition_word=transition,
            body=body,
            features=features,
            dependent_from=dependent_from,
            full_text=claim_text
        )

        logger.info(f"✅ 权利要求 {claim_number} 解析完成")
        logger.info(f"   类型: {claim_type}")
        logger.info(f"   特征数: {len(features)}")

        return parsed_claim

    def parse_multiple_claims(self, claims_text: List[str]) -> List[ParsedClaim]:
        """
        解析多条权利要求

        Args:
            claims_text: 权利要求文本列表

        Returns:
            ParsedClaim列表
        """
        logger.info(f"📜 批量解析 {len(claims_text)} 条权利要求")

        parsed_claims = []
        for idx, claim_text in enumerate(claims_text, start=1):
            try:
                parsed_claim = self.parse_claim(claim_text, idx)
                parsed_claims.append(parsed_claim)
            except Exception as e:
                logger.error(f"❌ 解析权利要求 {idx} 失败: {e}")
                continue

        logger.info(f"✅ 成功解析 {len(parsed_claims)}/{len(claims_text)} 条权利要求")

        return parsed_claims

    def _split_claim_sections(self, claim_text: str) -> tuple[str, str, str]:
        """
        分割权利要求为前序部分、过渡词、主体部分

        Args:
            claim_text: 权利要求文本

        Returns:
            (前序部分, 过渡词, 主体部分)
        """
        # 查找过渡词位置
        transition_match = self.transition_regex.search(claim_text)

        if transition_match:
            # 找到过渡词
            transition_start = transition_match.start()
            transition_end = transition_match.end()

            preamble = claim_text[:transition_start].strip()
            transition = transition_match.group().strip()
            body = claim_text[transition_end:].strip()

            # 如果前序部分为空，可能是从属权利要求，需要重新处理
            if not preamble:
                # 检查是否为从属权利要求
                dependent_match = self.dependent_regex.search(claim_text)
                if dependent_match:
                    # 从属权利要求，前序部分包含引用部分
                    ref_end = dependent_match.end()
                    preamble = claim_text[:ref_end].strip()
                    body = claim_text[ref_end:].strip()
                    # 查找后续的过渡词
                    remaining_match = self.transition_regex.search(body)
                    if remaining_match:
                        transition = remaining_match.group().strip()
                        body = body[remaining_match.end():].strip()

        else:
            # 没有找到过渡词，整段作为主体
            preamble = ""
            transition = ""
            body = claim_text

        return preamble, transition, body

    def _extract_features(self, body: str) -> List[ParsedFeature]:
        """
        从主体部分提取技术特征

        Args:
            body: 主体部分文本

        Returns:
            技术特征列表
        """
        features = []

        # 按分号或句号分割特征
        feature_texts = re.split(r'[；;。]', body)

        for idx, feature_text in enumerate(feature_texts):
            feature_text = feature_text.strip()
            if not feature_text:
                continue

            # 识别特征类型
            if '所述' in feature_text or '该' in feature_text:
                feature_type = "essential"
            elif '可选' in feature_text or '可以' in feature_text:
                feature_type = "optional"
            elif '用于' in feature_text or '配置为' in feature_text:
                feature_type = "functional"
            else:
                feature_type = "essential"

            # 提取组件名称（简单规则）
            component_match = re.search(r'(\w+层|\w+模块|\w+单元|\w+装置|\w+系统|\w+部件)', feature_text)
            component = component_match.group(1) if component_match else ""

            feature = ParsedFeature(
                id=f"feature_{idx+1}",
                description=feature_text,
                feature_type=feature_type,
                component=component
            )

            features.append(feature)

        return features
