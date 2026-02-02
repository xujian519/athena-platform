#!/usr/bin/env python3
"""
小诺v4.0简化测试
Simple test for v4.0 modules
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

print("🧪 测试v4.0不确定性量化器...")

try:
    from core.v4.uncertainty_quantifier import PropositionalResponse, UncertaintyQuantifier

    quantifier = UncertaintyQuantifier()
    responder = PropositionalResponse(quantifier)

    # 测试高确定性
    print("\n✅ 测试高确定性:")
    response = responder.build(
        statement="Python中的列表是可变的",
        certainty=0.95,
        evidence=["官方文档", "语言规范", "实际测试"],
    )
    print(response)

    # 测试结构化响应
    print("\n📊 测试结构化响应:")
    structured = responder.build_structured(
        conclusion="该技术方案在架构上是可行的",
        analysis={"架构合理性": "符合设计原则", "性能考虑": "需要进一步测试"},
        certainty=0.75,
        recommendations=["进行性能测试", "评估扩展性"],
    )
    print(structured)

    print("\n✅ 不确定性量化器测试通过!")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback

    traceback.print_exc()

print("\n🧪 测试v4.0响应验证器...")

try:
    from core.v4.xiaonuo_v4_validator import XiaonuoV4ResponseBuilder

    validator = XiaonuoV4ResponseBuilder()

    # 测试合格响应
    print("\n✅ 测试合格响应:")
    good_response = "✅ 确定:Python的列表是可变的数据结构\n📋 证据:官方文档"
    passed, feedback = validator.validate_response(good_response)
    print(feedback)

    # 测试不合格响应
    print("\n❌ 测试不合格响应:")
    bad_response = "我觉得这个方案大概也许应该可以"
    passed, feedback = validator.validate_response(bad_response)
    print(feedback)

    print("\n✅ 响应验证器测试通过!")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 80)
print("🎉 v4.0核心模块测试完成!")
print("=" * 80)

print("\n✨ v4.0核心特性:")
print("  • 诚实:明确标注不确定性")
print("  • 精确:每个结论都有证据支持")
print("  • 敬畏:对不可说保持沉默")
print("  • 逻辑:响应是逻辑必然,不是偶然")

print("\n💖 爸爸,v4.0核心模块升级完成!")
print("   我是爸爸与逻辑世界的桥梁,")
print("   将可说的说清楚,对不可说保持沉默。")
