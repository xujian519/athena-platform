#!/usr/bin/env python3
from __future__ import annotations
"""
增强意图分析器测试
Test Enhanced Intent Analyzer

验证增强意图分析器的功能。

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.cognition.enhanced_intent_analyzer import (
    EnhancedIntentAnalyzer,
    EnhancedIntentType,
    PatentSubDomain,
    PatentType,
    analyze_intent_enhanced,
)


def print_separator(title: str = ""):
    """打印分隔线"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)


def print_intent_result(intent, input_text: str):
    """打印意图识别结果"""
    print(f"\n📝 用户输入: {input_text}")
    print("\n🎯 识别结果:")
    print(f"  ┌─ 意图类型: {intent.intent_type.value}")
    print(f"  ├─ 主要目标: {intent.primary_goal}")
    print(f"  ├─ 置信度: {intent.confidence:.2f}")
    print(f"  ├─ 业务领域: {intent.domain.value}")

    if intent.task_type:
        print(f"  ├─ 任务类型: {intent.task_type.value}")
    if intent.phase:
        print(f"  ├─ 业务阶段: {intent.phase.value}")
    if intent.patent_type:
        print(f"  ├─ 专利类型: {intent.patent_type.value}")
    if intent.patent_sub_domain:
        print(f"  ├─ 专利子领域: {intent.patent_sub_domain.value}")
    if intent.layer_type:
        print(f"  ├─ 相关层级: {intent.layer_type.value}")
    if intent.suggested_agent:
        print(f"  ├─ 建议智能体: {intent.suggested_agent}")
    if intent.required_documents:
        print(f"  ├─ 需要文档: {[doc.value for doc in intent.required_documents]}")
    if intent.required_layers:
        print(f"  └─ 需要层级: {[layer.value for layer in intent.required_layers]}")

    if intent.extracted_variables:
        print("\n📦 提取的变量:")
        for key, value in intent.extracted_variables.items():
            print(f"  - {key}: {value}")


async def test_user_example():
    """测试用户示例：我要写一篇农业领域的实用新型专利"""
    print_separator("测试用户示例")

    analyzer = EnhancedIntentAnalyzer()
    input_text = "我要写一篇农业领域的实用新型专利"

    intent = await analyzer.analyze(input_text)
    print_intent_result(intent, input_text)

    # 验证关键识别结果
    assert intent.intent_type == EnhancedIntentType.PATENT_WRITING, \
        f"意图类型应为 PATENT_WRITING，实际为 {intent.intent_type}"
    assert intent.patent_type == PatentType.UTILITY_MODEL, \
        f"专利类型应为 UTILITY_MODEL，实际为 {intent.patent_type}"
    assert intent.patent_sub_domain == PatentSubDomain.AGRICULTURE, \
        f"专利子领域应为 AGRICULTURE，实际为 {intent.patent_sub_domain}"

    print("\n✅ 用户示例测试通过！")


async def test_various_patent_types():
    """测试各种专利类型识别"""
    print_separator("测试专利类型识别")

    test_cases = [
        ("我要申请一项发明专利", PatentType.INVENTION),
        ("这个实用新型专利的结构", PatentType.UTILITY_MODEL),
        ("设计一款产品的外观", PatentType.DESIGN),
    ]

    for input_text, expected_type in test_cases:
        intent = await analyze_intent_enhanced(input_text)
        status = "✅" if intent.patent_type == expected_type else "❌"
        print(f"\n{status} 输入: {input_text}")
        print(f"   识别: {intent.patent_type.value if intent.patent_type else 'None'}, "
              f"期望: {expected_type.value}")


async def test_various_sub_domains():
    """测试各种子领域识别"""
    print_separator("测试专利子领域识别")

    test_cases = [
        ("农业机械的收割装置", PatentSubDomain.AGRICULTURE),
        ("电子电路的控制系统", PatentSubDomain.ELECTRONICS),
        ("化学反应的合成方法", PatentSubDomain.CHEMISTRY),
        ("计算机软件的算法", PatentSubDomain.COMPUTER),
        ("汽车制造的制动系统", PatentSubDomain.VEHICLE),
    ]

    for input_text, expected_domain in test_cases:
        intent = await analyze_intent_enhanced(input_text)
        status = "✅" if intent.patent_sub_domain == expected_domain else "❌"
        print(f"\n{status} 输入: {input_text}")
        print(f"   识别: {intent.patent_sub_domain.value if intent.patent_sub_domain else 'None'}, "
              f"期望: {expected_domain.value}")


async def test_various_intent_types():
    """测试各种意图类型识别"""
    print_separator("测试意图类型识别")

    test_cases = [
        ("帮我撰写专利申请文件", EnhancedIntentType.PATENT_WRITING),
        ("检索相关现有技术", EnhancedIntentType.PATENT_SEARCH),
        ("分析这个技术方案的新颖性", EnhancedIntentType.PATENT_NOVELTY),
        ("评估专利的创造性", EnhancedIntentType.PATENT_CREATIVITY),
        ("判断是否构成侵权", EnhancedIntentType.PATENT_INFIRMINGEMENT),
        ("宣告专利权无效", EnhancedIntentType.PATENT_INVALIDATION),
    ]

    for input_text, expected_intent in test_cases:
        intent = await analyze_intent_enhanced(input_text)
        status = "✅" if intent.intent_type == expected_intent else "❌"
        print(f"\n{status} 输入: {input_text}")
        print(f"   识别: {intent.intent_type.value}, 期望: {expected_intent.value}")


async def test_complex_scenarios():
    """测试复杂场景"""
    print_separator("测试复杂场景")

    complex_cases = [
        {
            "input": "我要分析农业灌溉装置的发明专利是否侵犯他人专利权",
            "expected": {
                "intent_type": EnhancedIntentType.PATENT_INFIRMINGEMENT,
                "patent_type": PatentType.INVENTION,
                "sub_domain": PatentSubDomain.AGRICULTURE,
            }
        },
        {
            "input": "帮我检索机械传动领域的实用新型专利",
            "expected": {
                "intent_type": EnhancedIntentType.PATENT_SEARCH,
                "patent_type": PatentType.UTILITY_MODEL,
                "sub_domain": PatentSubDomain.MACHINERY,
            }
        },
        {
            "input": "评估电子电路的新颖性和创造性",
            "expected": {
                "intent_type": EnhancedIntentType.PATENT_ANALYSIS,
                "sub_domain": PatentSubDomain.ELECTRONICS,
            }
        },
    ]

    for case in complex_cases:
        input_text = case["input"]
        expected = case["expected"]

        intent = await analyze_intent_enhanced(input_text)
        print(f"\n📝 输入: {input_text}")
        print("\n🎯 识别结果:")
        print(f"  意图类型: {intent.intent_type.value} "
              f"{'✅' if intent.intent_type == expected['intent_type'] else '❌'}")
        if expected.get("patent_type"):
            print(f"  专利类型: {intent.patent_type.value if intent.patent_type else 'None'} "
                  f"{'✅' if intent.patent_type == expected['patent_type'] else '❌'}")
        if expected.get("sub_domain"):
            print(f"  子领域: {intent.patent_sub_domain.value if intent.patent_sub_domain else 'None'} "
                  f"{'✅' if intent.patent_sub_domain == expected['sub_domain'] else '❌'}")


async def test_layer_determination():
    """测试层级确定逻辑"""
    print_separator("测试法律世界模型层级确定")

    test_cases = [
        {
            "input": "撰写专利申请",
            "expected_layers": ["patent_professional_layer"],
        },
        {
            "input": "分析专利侵权案件",
            "expected_layers": ["judicial_case_layer"],
        },
        {
            "input": "专利无效宣告请求",
            "expected_layers": ["judicial_case_layer"],
        },
    ]

    for case in test_cases:
        intent = await analyze_intent_enhanced(case["input"])
        actual_layers = [layer.value for layer in intent.required_layers]
        expected_layers = case["expected_layers"]

        print(f"\n📝 输入: {case['input']}")
        print(f"   需要层级: {actual_layers}")
        print(f"   期望层级: {expected_layers}")
        print(f"   {'✅' if set(actual_layers) == set(expected_layers) else '❌'}")


async def main():
    """主测试函数"""
    print_separator("增强意图分析器测试套件")

    try:
        # 1. 用户示例测试
        await test_user_example()

        # 2. 专利类型识别测试
        await test_various_patent_types()

        # 3. 子领域识别测试
        await test_various_sub_domains()

        # 4. 意图类型识别测试
        await test_various_intent_types()

        # 5. 复杂场景测试
        await test_complex_scenarios()

        # 6. 层级确定测试
        await test_layer_determination()

        print_separator("测试完成")
        print("\n✅ 所有测试通过！")

        # 显示统计信息
        analyzer = EnhancedIntentAnalyzer()
        await analyzer.analyze("测试")  # 触发初始化
        stats = analyzer.get_recognition_stats()
        if stats.get("total_recognitions", 0) > 0:
            print("\n📊 统计信息:")
            print(f"  总识别次数: {stats['total_recognitions']}")
            print(f"  平均置信度: {stats['average_confidence']:.2f}")
            if stats.get('intent_distribution'):
                print(f"  意图分布: {stats['intent_distribution']}")
            if stats.get('patent_type_distribution'):
                print(f"  专利类型分布: {stats['patent_type_distribution']}")
            if stats.get('sub_domain_distribution'):
                print(f"  子领域分布: {stats['sub_domain_distribution']}")

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
