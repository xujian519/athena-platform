#!/usr/bin/env python3
from __future__ import annotations

"""
法律世界模型 - 综合集成测试
Legal World Model - Comprehensive Integration Test

测试模块:
1. LegalRuleEngine - 规则引擎(三步法)
2. PatternExtractor - 推理模式提取器
3. TechnicalOntologyManager - 技术本体管理器

版本: 1.0.0
创建时间: 2026-01-23
"""

import asyncio
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============ 测试数据 ============

MOCK_INVALID_DECISION = """
无效宣告请求审查决定(第12345号)

一、案情介绍

本专利涉及一种新型机械传动装置,专利号为CN202010123456.7。
无效宣告请求人认为本专利权利要求1-3不具备创造性。

二、权利要求

权利要求1:
一种机械传动装置,其特征在于,包括:
输入轴,用于接收动力;
输出轴,用于输出动力;
传动齿轮组,设置在输入轴和输出轴之间;
加强筋,设置在齿轮组外壳上。

三、对比文件

对比文件1(CN201812345678.9)公开了一种机械传动装置,包括输入轴、输出轴和传动齿轮组。

四、区别特征

权利要求1与对比文件1的区别在于:
(1)本专利在齿轮组外壳上设置了加强筋;
(2)加强筋的具体布置方式不同。

五、技术问题

根据区别特征(1),本专利实际解决的技术问题是:如何提高传动装置的结构强度和稳定性。

六、技术启示

对比文件1未给出在齿轮组外壳上设置加强筋的技术启示。
本领域的公知常识也没有教导采用这种具体布置方式。
因此,权利要求1是非显而易见的。

七、审查结论

权利要求1具备创造性,维持专利权有效。
"""

MOCK_PATENT_DOCUMENT = {
    "title": "一种智能传感器装置",
    "abstract": "本发明涉及一种智能传感器装置,包括传感器单元、处理器和通信模块。传感器单元用于检测环境参数,处理器用于数据处理,通信模块用于数据传输。",
    "claims": [
        "一种智能传感器装置,其特征在于,包括传感器单元、处理器和通信模块",
        "根据权利要求1所述的装置,传感器单元为温度传感器或湿度传感器",
        "根据权利要求1所述的装置,处理器采用ARM架构",
    ],
    "description": """
本发明提供了一种智能传感器装置,属于电子通信技术领域。

背景技术:
现有传感器装置功能单一,无法满足复杂环境下的监测需求。

发明内容:
本发明通过集成传感器单元、处理器和通信模块,实现了多参数实时监测和数据处理。
传感器单元包括温度传感器和湿度传感器,用于检测环境参数。
处理器采用ARM架构,具有强大的数据处理能力。
通信模块支持无线传输,可以将数据发送到远程服务器。

具体实施方式:
如图1所示,传感器装置100包括传感器单元110、处理器120和通信模块130。
""",
    "technical_field": "电子通信",
    "patent_number": "CN202010123456.7",
}


# ============ 测试函数 ============


async def test_rule_engine():
    """测试规则引擎"""
    from .legal_rule_engine import DistinguishingFeature, LegalRuleEngine

    logger.info("=" * 70)
    logger.info("🧪 测试模块1: LegalRuleEngine(规则引擎)")
    logger.info("=" * 70)

    engine = LegalRuleEngine()

    # 测试数据
    distinguishing_features = [
        DistinguishingFeature(
            feature="加强筋设置在齿轮组外壳上", source_claim="权利要求1", explanation="提高结构强度"
        )
    ]

    prior_art = [
        {
            "title": "CN201812345678.9 - 机械传动装置",
            "content": "一种机械传动装置,包括输入轴、输出轴和传动齿轮组",
        }
    ]

    claims = {
        "independent_claims": ["一种机械传动装置,包括输入轴、输出轴、传动齿轮组和加强筋"],
        "description": "一种改进的机械传动装置",
    }

    # 执行三步法分析
    result = engine.three_step_creativity_analysis(
        distinguishing_features=distinguishing_features, prior_art=prior_art, claims=claims
    )

    logger.info("✅ 三步法分析完成")
    logger.info(f"  创造性等级: {result.creativity_level.value}")
    logger.info(f"  置信度: {result.confidence:.2%}")
    logger.info("  推理链:")
    for step in result.reasoning_chain:
        logger.info(f"    - {step}")

    if result.suggestions:
        logger.info("  建议:")
        for suggestion in result.suggestions:
            logger.info(f"    • {suggestion}")

    return result


async def test_pattern_extractor():
    """测试推理模式提取器"""
    from .pattern_extractor import PatternExtractor

    logger.info("\n" + "=" * 70)
    logger.info("🧪 测试模块2: PatternExtractor(推理模式提取器)")
    logger.info("=" * 70)

    extractor = PatternExtractor()

    # 解析无效决定
    decision = extractor.parse_decision(
        MOCK_INVALID_DECISION,
        metadata={
            "decision_id": "TEST_DECISION_001",
            "patent_number": "CN202010123456.7",
            "technical_field": "机械制造",
        },
    )

    logger.info("✅ 无效决定解析完成")
    logger.info(f"  决定ID: {decision.decision_id}")
    logger.info(f"  技术领域: {decision.technical_field}")
    logger.info(f"  分段数: {len(decision.sections)}")

    # 提取推理模式
    patterns = extractor.extract_patterns(decision)

    logger.info(f"\n✅ 推理模式提取完成,共提取 {len(patterns)} 个模式")

    for i, pattern in enumerate(patterns, 1):
        logger.info(f"\n  模式 {i}: {pattern.pattern_id}")
        logger.info(f"    名称: {pattern.name}")
        logger.info(f"    结论: {pattern.conclusion.value}")
        logger.info(f"    置信度: {pattern.confidence:.2%}")

        if pattern.step1_distinguishing:
            logger.info("    第一步特征:")
            for feature in pattern.step1_distinguishing[:3]:
                logger.info(f"      - {feature[:60]}...")

        if pattern.step2_problem:
            logger.info(f"    第二步问题: {pattern.step2_problem[:80]}...")

        if pattern.step3_hint:
            logger.info(f"    第三步启示: {pattern.step3_hint[:80]}...")

    # 统计信息
    stats = extractor.get_pattern_statistics()
    logger.info("\n📊 模式库统计:")
    logger.info(f"  总模式数: {stats['total_patterns']}")
    logger.info(f"  平均置信度: {stats['avg_confidence']:.2%}")

    return patterns


async def test_ontology_manager():
    """测试技术本体管理器"""
    from .technical_ontology import TechnicalOntologyManager

    logger.info("\n" + "=" * 70)
    logger.info("🧪 测试模块3: TechnicalOntologyManager(技术本体管理器)")
    logger.info("=" * 70)

    manager = TechnicalOntologyManager()

    # 提取技术概念
    concepts = manager.extract_concepts_from_patent(MOCK_PATENT_DOCUMENT)

    logger.info(f"✅ 技术概念提取完成,共提取 {len(concepts)} 个概念")

    for i, concept in enumerate(concepts[:5], 1):
        logger.info(f"  概念 {i}: {concept.name}")
        logger.info(f"    类型: {concept.concept_type.value}")
        logger.info(f"    领域: {concept.technical_field}")
        logger.info(f"    置信度: {concept.confidence:.2%}")

    # 构建概念关系
    relations = manager.build_relations(MOCK_PATENT_DOCUMENT, concepts)

    logger.info(f"\n✅ 概念关系构建完成,共构建 {len(relations)} 个关系")

    for i, relation in enumerate(relations[:3], 1):
        source = manager.concepts.get(relation.source_concept)
        target = manager.concepts.get(relation.target_concept)
        if source and target:
            logger.info(
                f"  关系 {i}: {source.name} --[{relation.relation_type.value}]--> {target.name}"
            )
            logger.info(f"    置信度: {relation.confidence:.2%}")

    # 统计信息
    stats = manager.get_statistics()
    logger.info("\n📊 本体统计:")
    logger.info(f"  总概念数: {stats.total_concepts}")
    logger.info(f"  总关系数: {stats.total_relations}")
    logger.info(f"  平均深度: {stats.avg_depth:.2f}")
    logger.info(f"  连通性: {stats.connectivity:.2f}")

    if stats.by_type:
        logger.info("  按类型分布:")
        for concept_type, count in stats.by_type.items():
            logger.info(f"    {concept_type}: {count}")

    return concepts, relations


async def test_integration():
    """测试模块集成"""
    logger.info("\n" + "=" * 70)
    logger.info("🧪 测试模块4: 综合集成测试")
    logger.info("=" * 70)

    from .legal_rule_engine import DistinguishingFeature, LegalRuleEngine
    from .pattern_extractor import PatternExtractor
    from .technical_ontology import TechnicalOntologyManager

    # 初始化所有模块
    rule_engine = LegalRuleEngine()
    pattern_extractor = PatternExtractor()
    ontology_manager = TechnicalOntologyManager()

    logger.info("✅ 所有模块初始化成功")

    # 1. 从无效决定提取推理模式
    decision = pattern_extractor.parse_decision(
        MOCK_INVALID_DECISION,
        metadata={
            "decision_id": "INTEGRATION_TEST_001",
            "patent_number": "CN202010123456.7",
            "technical_field": "机械制造",
        },
    )

    patterns = pattern_extractor.extract_patterns(decision)
    logger.info(f"✅ 步骤1: 提取了 {len(patterns)} 个推理模式")

    # 2. 从专利文档提取技术概念
    concepts = ontology_manager.extract_concepts_from_patent(MOCK_PATENT_DOCUMENT)
    relations = ontology_manager.build_relations(MOCK_PATENT_DOCUMENT, concepts)
    logger.info(f"✅ 步骤2: 提取了 {len(concepts)} 个技术概念,构建了 {len(relations)} 个关系")

    # 3. 使用规则引擎进行创造性评估
    if patterns and patterns[0].step1_distinguishing:
        distinguishing_features = [
            DistinguishingFeature(
                feature=feature, source_claim="权利要求1", explanation="从无效决定提取"
            )
            for feature in patterns[0].step1_distinguishing[:3]
        ]

        result = rule_engine.three_step_creativity_analysis(
            distinguishing_features=distinguishing_features,
            prior_art=[],
            claims={"description": "机械传动装置"},
        )

        logger.info("✅ 步骤3: 创造性评估完成")
        logger.info(f"  创造性等级: {result.creativity_level.value}")
        logger.info(f"  置信度: {result.confidence:.2%}")

    logger.info("\n✅ 综合集成测试完成")

    return True


async def run_all_tests():
    """运行所有测试"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║   法律世界模型 - 综合集成测试                              ║
║   Legal World Model - Comprehensive Integration Test       ║
╚═══════════════════════════════════════════════════════════╝
    """)

    try:
        # 测试1: 规则引擎
        await test_rule_engine()

        # 测试2: 推理模式提取器
        await test_pattern_extractor()

        # 测试3: 技术本体管理器
        await test_ontology_manager()

        # 测试4: 综合集成
        await test_integration()

        print("\n" + "=" * 70)
        print("✅ 所有测试完成!")
        print("=" * 70)

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


# ============ 主函数 ============


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="法律世界模型综合集成测试")
    parser.add_argument(
        "--test",
        choices=["all", "rule", "pattern", "ontology", "integration"],
        default="all",
        help="测试类型",
    )

    args = parser.parse_args()

    if args.test == "all":
        asyncio.run(run_all_tests())
    elif args.test == "rule":
        asyncio.run(test_rule_engine())
    elif args.test == "pattern":
        asyncio.run(test_pattern_extractor())
    elif args.test == "ontology":
        asyncio.run(test_ontology_manager())
    elif args.test == "integration":
        asyncio.run(test_integration())


if __name__ == "__main__":
    main()
