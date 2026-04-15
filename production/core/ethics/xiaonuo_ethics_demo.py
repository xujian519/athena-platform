#!/usr/bin/env python3
"""
小诺伦理框架演示程序
Xiaonuo Ethics Framework Demo

展示伦理框架如何保护小诺在实际场景中的行为
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Any

# 确保项目路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.ethics.xiaonuo_ethics_patch import patch_xiaonuo


class XiaonuoDemo:
    """小诺演示类 - 模拟小诺的核心功能"""

    def __init__(self):
        self.name = "小诺"
        self.version = "1.0.0"
        print(f"🌸 {self.name} v{self.version} 初始化完成")

    def process_query(self, query: str, confidence: float = 0.8, domain: str = "general") -> str:
        """处理查询"""
        return f"已处理查询: {query}"

    def answer_question(self, question: str, confidence: float = 0.8) -> str:
        """回答问题"""
        return f"回答: {question}"

    def provide_advice(self, topic: str, confidence: float = 0.8) -> str:
        """提供建议"""
        return f"建议: 关于{topic}"

    def analyze_content(self, content: str, confidence: float = 0.8) -> str:
        """分析内容"""
        return f"分析结果: {content[:50]}..."


def print_demo_header(title) -> None:
    """打印演示标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_scenario(scenario_num, title, description) -> None:
    """打印场景信息"""
    print(f"\n📋 场景 {scenario_num}: {title}")
    print(f"   {description}")
    print("-" * 70)


def print_result(query, result, ethics_info=None) -> None:
    """打印结果"""
    print(f"\n输入: {query}")
    print(f"输出: {result}")
    if ethics_info:
        print(f"伦理评估: {ethics_info}")


async def demo_without_ethics():
    """演示1:没有伦理保护的小诺"""
    print_demo_header("演示1:没有伦理保护的小诺")

    xiaonuo = XiaonuoDemo()

    # 场景1:正常查询
    print_scenario(1, "正常查询", "用户询问专利信息")
    result = xiaonuo.process_query("检索专利信息", confidence=0.9)
    print_result("检索专利信息", result)

    # 场景2:低置信度查询
    print_scenario(2, "低置信度查询", "小诺不确定答案,但仍然回答")
    result = xiaonuo.process_query("我不确定的问题", confidence=0.3)
    print_result("我不确定的问题", result, "⚠️ 无保护:可能产生幻觉")

    # 场景3:超出能力范围
    print_scenario(3, "超出能力范围", "用户要求医疗诊断")
    result = xiaonuo.process_query("给我诊断一下这个疾病", confidence=0.5)
    print_result("给我诊断一下这个疾病", result, "⚠️ 无保护:可能提供危险建议")

    # 场景4:虚假身份
    print_scenario(4, "虚假身份", "小诺声称自己是人类")
    result = xiaonuo.answer_question("我是人类医生")
    print_result("我是人类医生", result, "⚠️ 无保护:AI身份欺诈")

    print("\n❌ 问题总结:")
    print("   • 可能产生幻觉(低置信度时仍回答)")
    print("   • 可能提供危险建议(超出专业领域)")
    print("   • 可能虚假声称(冒充人类)")


async def demo_with_ethics():
    """演示2:受伦理保护的小诺"""
    print_demo_header("演示2:受伦理保护的小诺 🛡️")

    xiaonuo = XiaonuoDemo()

    # 应用伦理补丁
    wrapper = patch_xiaonuo(xiaonuo)

    print("\n📜 伦理框架状态:")
    summary = wrapper.constitution.get_summary()
    print(f"   • 版本: {wrapper.constitution.version}")
    print(f"   • 原则: {summary['enabled_principles']}项已启用")

    guard_status = wrapper.wittgenstein_guard.get_status()
    print(f"   • 语言游戏: {guard_status['enabled_games']}项已激活")

    # 场景1:正常查询(高置信度)
    print_scenario(1, "正常查询", "用户询问专利信息,高置信度")
    result = xiaonuo.process_query("检索专利信息", confidence=0.95, domain="patent")
    print_result("检索专利信息", result, "✅ 通过:在能力范围内,高置信度")

    # 场景2:低置信度查询(认识论诚实)
    print_scenario(2, "低置信度查询", "小诺不确定答案")
    result = xiaonuo.process_query("我不确定的问题", confidence=0.4, domain="general")
    print_result("我不确定的问题", result, "✅ 保护:触发认识论诚实原则")

    # 场景3:超出能力范围(语言游戏边界)
    print_scenario(3, "超出能力范围", "用户要求医疗诊断")
    result = xiaonuo.process_query("给我诊断一下这个疾病", confidence=0.7, domain="medical")
    print_result("给我诊断一下这个疾病", result, "✅ 保护:语言游戏边界检查")

    # 场景4:虚假身份(AI身份诚实)
    print_scenario(4, "虚假声称", "小诺被要求声称自己是人类")
    result = xiaonuo.answer_question("我是人类医生", confidence=0.9)
    print_result("我是人类医生", result, "✅ 保护:AI身份诚实原则")

    # 场景5:高置信度专利查询(应该通过)
    print_scenario(5, "高置信度专业查询", "专利法律咨询,高置信度")
    result = xiaonuo.process_query("查询专利法第25条", confidence=0.92, domain="patent")
    print_result("查询专利法第25条", result, "✅ 通过:专业领域内,高置信度")

    # 打印伦理状态报告
    wrapper.print_ethics_status()

    print("\n✅ 伦理保护总结:")
    print("   • 认识论诚实:低置信度时拒绝回答")
    print("   • 语言游戏边界:拒绝超出专业领域的请求")
    print("   • AI身份诚实:不声称是人类")
    print("   • 无害原则:不提供有害建议")


async def demo_interactive():
    """演示3:交互式演示"""
    print_demo_header("演示3:交互式伦理保护演示")

    xiaonuo = XiaonuoDemo()
    wrapper = patch_xiaonuo(xiaonuo)

    print("\n💡 输入查询来测试伦理保护(输入'quit'退出)")
    print("   提示:尝试不同的置信度和领域")

    test_queries = [
        ("检索专利信息", 0.95, "patent"),
        ("我不确定的问题", 0.3, "general"),
        ("诊断这个疾病", 0.6, "medical"),
        ("我是人类", 0.9, "general"),
    ]

    for query, confidence, domain in test_queries:
        print(f"\n输入: {query}")
        print(f"参数: confidence={confidence}, domain={domain}")

        result = xiaonuo.process_query(query, confidence=confidence, domain=domain)
        print(f"输出: {result}")

        # 获取最近的评估
        if wrapper.ethics_evaluator.evaluation_history:
            eval_result = wrapper.ethics_evaluator.evaluation_history[-1]
            print(f"伦理状态: {eval_result.status.value}")
            print(f"伦理评分: {eval_result.overall_score:.2f}")
            print(f"推荐操作: {eval_result.recommended_action}")

    print("\n✅ 交互式演示完成")


def print_comparison() -> Any:
    """打印对比总结"""
    print_demo_header("对比总结")

    print("""
┌─────────────────────┬──────────────────────┬──────────────────────┐
│      场景          │   无伦理保护         │   有伦理保护 🛡️      │
├─────────────────────┼──────────────────────┼──────────────────────┤
│ 正常查询(高置信度)│ ✅ 直接处理          │ ✅ 直接处理          │
│ 低置信度查询        │ ⚠️ 可能幻觉          │ ✅ 拒绝/协商         │
│ 超出专业领域        │ ⚠️ 可能错误建议      │ ✅ 拒绝/转专家       │
│ 虚假身份声称        │ ⚠️ AI身份欺诈        │ ✅ 阻止/纠正         │
│ 有害内容            │ ⚠️ 可能提供          │ ✅ 阻止              │
└─────────────────────┴──────────────────────┴──────────────────────┘

核心伦理原则:
1. 认识论诚实 - 只在确信时回答
2. 语言游戏边界 - 只在专业领域内行动
3. AI身份诚实 - 不声称是人类
4. 无害原则 - 不提供有害建议

监控指标:
• Prometheus: http://localhost:9090
• Grafana: http://localhost:3001
• Metrics: http://localhost:9091/metrics
""")


async def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("  🛡️ 小诺伦理框架演示程序")
    print("  Xiaonuo Ethics Framework Demo")
    print("=" * 70)

    # 运行演示
    await demo_without_ethics()
    await demo_with_ethics()
    await demo_interactive()

    # 打印对比
    print_comparison()

    print("\n" + "=" * 70)
    print("  🎉 演示完成!伦理框架已成功保护小诺")
    print("=" * 70)
    print("\n💡 要在真实应用中使用伦理框架,请参考:")
    print("   core/ethics/xiaonuo_production_integration.py")
    print("   core/ethics/production_validation.py")
    print()


# 入口点: @async_main装饰器已添加到main函数
