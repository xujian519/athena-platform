#!/usr/bin/env python3
"""测试侵权判定器"""
import asyncio
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台')

from core.patent.infringement.infringement_determiner import InfringementDeterminer
from core.patent.infringement.feature_comparator import FeatureComparison, FeatureMapping
from core.patent.infringement.claim_parser import ParsedClaim, ParsedFeature

async def test():
    determiner = InfringementDeterminer()

    # 创建测试数据
    claim = ParsedClaim(
        claim_number=1,
        claim_type="independent",
        preamble="一种图像识别方法",
        transition_word="其特征在于",
        body="包括输入层和卷积层",
        features=[
            ParsedFeature(
                id="f1",
                description="包括输入层和卷积层",
                feature_type="essential"
            )
        ]
    )

    comparison = FeatureComparison(
        claim_number=1,
        total_features=1,
        mapped_features=0,
        missing_features=1,
        different_features=0,
        mappings=[
            FeatureMapping(
                claim_feature_id="f1",
                claim_feature_text="包括输入层和卷积层",
                product_feature_id="",
                product_feature_text="未找到",
                correspondence_type="missing",
                confidence=0.0
            )
        ],
        coverage_ratio=0.0
    )

    # 测试
    result = determiner.determine(
        [comparison],
        "CN123456789A",
        "测试产品"
    )

    print(f"测试成功! 侵权: {result.overall_infringement}, 风险: {result.overall_risk}")

if __name__ == "__main__":
    asyncio.run(test())
