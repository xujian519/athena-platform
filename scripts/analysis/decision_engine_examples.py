#!/usr/bin/env python3
"""
decision_engine工具使用示例

展示如何在实际业务场景中使用decision_engine工具。

作者: Athena平台
日期: 2026-04-20
"""

import asyncio
import json
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tools.production_tool_implementations import decision_engine_handler


async def example_patent_solution_selection():
    """示例1: 专利技术方案选择"""
    print("\n" + "=" * 60)
    print("示例1: 专利技术方案选择")
    print("=" * 60)

    params = {
        "context": "自动驾驶掉头路段脱困技术方案选择",
        "options": [
            "方案A: 纯规则引擎",
            "方案B: 深度强化学习",
            "方案C: 混合方案(规则+AI)",
            "方案D: 传统机器学习",
        ],
        "criteria": {
            "创新性": 0.25,  # 专利创造性核心
            "技术可行性": 0.20,
            "实施成本": 0.15,
            "开发周期": 0.15,
            "技术风险": 0.15,
            "产业化前景": 0.10,
        },
        "scores": {
            "方案A: 纯规则引擎": {
                "创新性": 0.40,  # 低创新
                "技术可行性": 0.95,  # 高可行性
                "实施成本": 0.90,  # 低成本
                "开发周期": 0.95,  # 快速
                "技术风险": 0.90,  # 低风险
                "产业化前景": 0.60,  # 一般
            },
            "方案B: 深度强化学习": {
                "创新性": 0.95,  # 高创新
                "技术可行性": 0.60,  # 中等可行性
                "实施成本": 0.50,  # 高成本
                "开发周期": 0.55,  # 周期长
                "技术风险": 0.45,  # 高风险
                "产业化前景": 0.90,  # 好
            },
            "方案C: 混合方案(规则+AI)": {
                "创新性": 0.85,  # 较高创新
                "技术可行性": 0.85,  # 高可行性
                "实施成本": 0.70,  # 中等成本
                "开发周期": 0.75,  # 中等周期
                "技术风险": 0.75,  # 中等风险
                "产业化前景": 0.85,  # 较好
            },
            "方案D: 传统机器学习": {
                "创新性": 0.60,  # 中等创新
                "技术可行性": 0.90,  # 高可行性
                "实施成本": 0.75,  # 中等成本
                "开发周期": 0.85,  # 较快
                "技术风险": 0.80,  # 较低风险
                "产业化前景": 0.70,  # 中等
            },
        },
    }

    result = await decision_engine_handler(params, {})

    print(f"\n决策背景: {result['context']}")
    print(f"\n评估标准: {result['analysis']['criteria_used']}")
    print(f"\n决策排名:")

    for rank in result["ranking"]:
        print(f"\n  第{rank['rank']}名: {rank['option']}")
        print(f"  总分: {rank['score']:.3f}")

    print(f"\n推荐方案: {result['best_option']}")

    print(f"\n决策分析:")
    print(f"  方案数量: {result['analysis']['total_options']}")
    print(f"  分数范围: {result['analysis']['score_range']}")
    print(f"  置信度: {result['analysis']['confidence']}")

    return result


async def example_investment_decision():
    """示例2: 投资标的决策"""
    print("\n" + "=" * 60)
    print("示例2: 投资标的决策")
    print("=" * 60)

    params = {
        "context": "科技股投资选择",
        "options": ["股票A: 芯片制造", "股票B: 云计算", "股票C: 新能源"],
        "criteria": {"预期收益": 0.4, "风险水平": 0.3, "流动性": 0.2, "估值": 0.1},
        "scores": {
            "股票A: 芯片制造": {"预期收益": 0.85, "风险水平": 0.70, "流动性": 0.80, "估值": 0.60},
            "股票B: 云计算": {"预期收益": 0.75, "风险水平": 0.80, "流动性": 0.90, "估值": 0.70},
            "股票C: 新能源": {"预期收益": 0.90, "风险水平": 0.50, "流动性": 0.60, "估值": 0.50},
        },
    }

    result = await decision_engine_handler(params, {})

    print(f"\n投资决策排名:")
    for rank in result["ranking"]:
        print(f"  {rank['rank']}. {rank['option']}: {rank['score']:.3f}")

    print(f"\n推荐投资: {result['best_option']}")
    print(f"风险提示: 投资有风险，决策需谨慎")

    return result


async def example_vendor_selection():
    """示例3: 供应商选择"""
    print("\n" + "=" * 60)
    print("示例3: 供应商选择")
    print("=" * 60)

    params = {
        "context": "专利代理机构选择",
        "options": ["代理机构A", "代理机构B", "代理机构C"],
        "criteria": {
            "专业能力": 0.30,
            "服务费用": 0.25,
            "响应速度": 0.20,
            "成功案例": 0.15,
            "服务质量": 0.10,
        },
        "scores": {
            "代理机构A": {
                "专业能力": 0.90,
                "服务费用": 0.60,
                "响应速度": 0.85,
                "成功案例": 0.95,
                "服务质量": 0.90,
            },
            "代理机构B": {
                "专业能力": 0.75,
                "服务费用": 0.85,
                "响应速度": 0.70,
                "成功案例": 0.70,
                "服务质量": 0.75,
            },
            "代理机构C": {
                "专业能力": 0.80,
                "服务费用": 0.75,
                "响应速度": 0.90,
                "成功案例": 0.80,
                "服务质量": 0.85,
            },
        },
    }

    result = await decision_engine_handler(params, {})

    print(f"\n供应商评估:")
    for rank in result["ranking"]:
        print(f"  {rank['rank']}. {rank['option']}: {rank['score']:.3f}")

    print(f"\n推荐供应商: {result['best_option']}")

    return result


async def example_auto_scoring():
    """示例4: 自动评分（快速原型）"""
    print("\n" + "=" * 60)
    print("示例4: 自动评分模式")
    print("=" * 60)

    params = {
        "context": "快速技术选型",
        "options": ["技术方案X", "技术方案Y", "技术方案Z"],
        # 不提供criteria和scores，使用默认值
    }

    result = await decision_engine_handler(params, {})

    print(f"\n默认评估标准: {result['analysis']['criteria_used']}")
    print(f"\n自动评分结果:")
    for rank in result["ranking"]:
        print(f"  {rank['rank']}. {rank['option']}: {rank['score']:.3f}")

    print(f"\n注意: 这是随机生成的分数，仅用于原型验证")

    return result


async def example_weight_normalization():
    """示例5: 权重自动归一化"""
    print("\n" + "=" * 60)
    print("示例5: 权重自动归一化")
    print("=" * 60)

    # 提供非标准权重
    params = {
        "context": "测试权重归一化",
        "options": ["A", "B"],
        "criteria": {"质量": 0.5, "价格": 0.8, "服务": 0.7},  # 总和=2.0
        "scores": {
            "A": {"质量": 0.9, "价格": 0.6, "服务": 0.8},
            "B": {"质量": 0.7, "价格": 0.9, "服务": 0.7},
        },
    }

    result = await decision_engine_handler(params, {})

    print(f"\n原始权重: 质量=0.5, 价格=0.8, 服务=0.7 (总和=2.0)")
    print(f"归一化后: 质量=0.25, 价格=0.40, 服务=0.35 (总和=1.0)")

    print(f"\n归一化评分:")
    for rank in result["ranking"]:
        print(f"  {rank['option']}: {rank['score']:.3f}")

    print(f"\n✓ 权重已自动归一化")

    return result


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("decision_engine工具使用示例")
    print("=" * 60)
    print("\n将演示6个实际业务场景...")

    examples = [
        ("专利技术方案选择", example_patent_solution_selection),
        ("投资标的决策", example_investment_decision),
        ("供应商选择", example_vendor_selection),
        ("自动评分模式", example_auto_scoring),
        ("权重归一化", example_weight_normalization),
    ]

    results = []

    for name, example_func in examples:
        try:
            result = await example_func()
            results.append((name, True, result))
        except Exception as e:
            print(f"\n❌ 示例执行失败: {e}")
            results.append((name, False, None))

    # 摘要
    print("\n" + "=" * 60)
    print("示例执行摘要")
    print("=" * 60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    print(f"\n总示例数: {total}")
    print(f"成功: {passed} ✅")
    print(f"失败: {total - passed} ❌")

    print("\n详细结果:")
    for name, success, _ in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")

    if passed == total:
        print("\n🎉 所有示例执行成功!")
        print("\n使用建议:")
        print("  1. 根据业务场景调整评估标准权重")
        print("  2. 评分需要基于实际数据和专家判断")
        print("  3. 复杂决策可结合多种方法（SAW/AHP/TOPSIS）")
        print("  4. 定期回顾决策结果，优化权重配置")
    else:
        print(f"\n⚠️  {total - passed}个示例失败")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
