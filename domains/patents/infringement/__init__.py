#!/usr/bin/env python3
"""
侵权分析系统

提供专利侵权分析的完整功能：
1. 权利要求解析
2. 涉案产品分析
3. 特征对比
4. 侵权判定
5. 法律意见书撰写
"""

from .claim_parser import ClaimParser, ParsedClaim
from .feature_comparator import FeatureComparator, FeatureComparison
from .infringement_analyzer import InfringementAnalysisOptions, InfringementAnalyzer
from .infringement_determiner import InfringementDeterminer, InfringementResult
from .opinion_writer import OpinionWriter
from .product_analyzer import AnalyzedProduct, ProductAnalyzer

__all__ = [
    "ClaimParser",
    "ParsedClaim",
    "ProductAnalyzer",
    "AnalyzedProduct",
    "FeatureComparator",
    "FeatureComparison",
    "InfringementDeterminer",
    "InfringementResult",
    "OpinionWriter",
    "InfringementAnalyzer",
    "InfringementAnalysisOptions",
]
