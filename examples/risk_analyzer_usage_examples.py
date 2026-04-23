#!/usr/bin/env python3
"""
Risk Analyzer工具使用示例

演示如何使用risk_analyzer工具进行风险分析
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tools.production_tool_implementations import risk_analyzer_handler


async def example_1_patent_application():
    """示例1: 专利申请风险分析"""
    print("=" * 80)
    print("示例1: 专利申请风险分析")
    print("=" * 80)
    print()

    params = {
        "scenario": "申请人工智能自动驾驶相关专利，涉及复杂算法和大量数据",
        "risk_factors": [
            {
                "name": "技术风险",
                "description": "算法新颖性不足，创造性可能被质疑"
            },
            {
                "name": "时间风险",
                "description": "专利审查周期长，可能影响产品上市"
            },
            {
                "name": "竞争风险",
                "description": "竞争对手已有类似专利"
            }
        ]
    }

    result = await risk_analyzer_handler(params, {})

    print(f"场景: {params['scenario']}")
    print(f"整体风险等级: {result['overall_risk_level']}")
    print(f"整体风险评分: {result['overall_score']}")
    print()

    print("风险详情:")
    for i, risk in enumerate(result['risks'], 1):
        print(f"{i}. {risk['name']}")
        print(f"   - 等级: {risk['risk_level']}")
        print(f"   - 概率: {risk['probability']}")
        print(f"   - 影响: {risk['impact']}")
        print(f"   - 评分: {risk['score']}")
        print(f"   - 缓解: {risk['mitigation']}")
        print()

    print("重点关注:")
    for strategy in result['mitigation_strategies']:
        print(f"  - {strategy}")

    print()


async def example_2_software_development():
    """示例2: 软件开发风险分析"""
    print("=" * 80)
    print("示例2: 软件开发风险分析")
    print("=" * 80)
    print()

    params = {
        "scenario": "开发一个复杂的分布式系统，涉及微服务架构和大量并发处理",
        "risk_factors": [
            {
                "name": "技术风险",
                "description": "系统复杂度高，架构设计难度大"
            },
            {
                "name": "时间风险",
                "description": "开发周期紧张，可能延期"
            },
            {
                "name": "资源风险",
                "description": "高级开发人员不足"
            },
            {
                "name": "集成风险",
                "description": "微服务之间集成复杂"
            }
        ]
    }

    result = await risk_analyzer_handler(params, {})

    print(f"场景: {params['scenario']}")
    print(f"风险数量: {result['total_risks']}")
    print(f"整体风险等级: {result['overall_risk_level']} ({result['risk_color']})")
    print()

    # 风险矩阵
    print("风险矩阵:")
    print(f"{'风险名称':<15} {'等级':<8} {'概率':<15} {'影响':<12} {'评分':<6}")
    print("-" * 80)
    for risk in result['risks']:
        print(f"{risk['name']:<15} {risk['risk_level']:<8} {risk['probability']:<15} "
              f"{risk['impact']:<12} {risk['score']:<6}")

    print()


async def example_3_business_investment():
    """示例3: 商业投资风险分析"""
    print("=" * 80)
    print("示例3: 商业投资风险分析")
    print("=" * 80)
    print()

    params = {
        "scenario": "投资一家新兴科技公司，涉及大额资金和长期回报预期",
        "risk_factors": [
            {
                "name": "市场风险",
                "description": "市场需求变化，竞争加剧"
            },
            {
                "name": "财务风险",
                "description": "资金链断裂，回报不及预期"
            },
            {
                "name": "政策风险",
                "description": "监管政策变化"
            }
        ]
    }

    result = await risk_analyzer_handler(params, {})

    print(f"场景: {params['scenario']}")
    print(f"整体风险等级: {result['overall_risk_level']}")
    print(f"整体风险评分: {result['overall_score']}")
    print()

    # 按风险评分排序
    sorted_risks = sorted(result['risks'], key=lambda x: x['score'], reverse=True)

    print("风险排序（从高到低）:")
    for i, risk in enumerate(sorted_risks, 1):
        print(f"{i}. {risk['name']} - 评分: {risk['score']} - {risk['mitigation']}")

    print()


async def example_4_custom_risks():
    """示例4: 自定义风险因子"""
    print("=" * 80)
    print("示例4: 自定义风险因子")
    print("=" * 80)
    print()

    params = {
        "scenario": "组织一场大型技术会议",
        "risk_factors": [
            {
                "name": "场地风险",
                "description": "场地容量不足或设施故障"
            },
            {
                "name": "嘉宾风险",
                "description": "重要嘉宾临时无法出席"
            },
            {
                "name": "天气风险",
                "description": "恶劣天气影响活动进行"
            },
            {
                "name": "技术风险",
                "description": "音视频设备故障"
            }
        ]
    }

    result = await risk_analyzer_handler(params, {})

    print(f"场景: {params['scenario']}")
    print(f"整体风险等级: {result['overall_risk_level']}")
    print()

    print("风险详情:")
    for risk in result['risks']:
        print(f"  {risk['name']}: {risk['risk_level']} - {risk['mitigation']}")

    print()


async def example_5_default_risks():
    """示例5: 使用默认风险因子"""
    print("=" * 80)
    print("示例5: 使用默认风险因子（空输入）")
    print("=" * 80)
    print()

    # 不提供任何风险因子，使用默认的5个风险类型
    params = {
        "scenario": "启动一个新的创业项目",
        "risk_factors": []  # 空列表，将使用默认风险因子
    }

    result = await risk_analyzer_handler(params, {})

    print(f"场景: {params['scenario']}")
    print(f"使用默认风险因子数量: {result['total_risks']}")
    print(f"整体风险等级: {result['overall_risk_level']}")
    print()

    print("默认风险类型:")
    for risk in result['risks']:
        print(f"  - {risk['name']}: {risk['description']}")

    print()


async def example_6_risk_comparison():
    """示例6: 多个方案风险对比"""
    print("=" * 80)
    print("示例6: 多个方案风险对比")
    print("=" * 80)
    print()

    scenarios = [
        {
            "name": "方案A: 自主研发",
            "scenario": "完全自主研发，拥有完整知识产权",
            "risk_factors": [
                {"name": "技术风险", "description": "技术难度大，可能失败"},
                {"name": "时间风险", "description": "研发周期长"},
                {"name": "资源风险", "description": "需要大量资金和人才"}
            ]
        },
        {
            "name": "方案B: 合作开发",
            "scenario": "与其他公司合作开发，共享技术和风险",
            "risk_factors": [
                {"name": "合作风险", "description": "合作伙伴可能违约"},
                {"name": "技术风险", "description": "技术整合难度"},
                {"name": "知识产权风险", "description": "知识产权归属不清"}
            ]
        },
        {
            "name": "方案C: 直接购买",
            "scenario": "购买成熟技术方案，快速上线",
            "risk_factors": [
                {"name": "成本风险", "description": "购买成本高"},
                {"name": "依赖风险", "description": "依赖供应商"},
                {"name": "适配风险", "description": "技术适配可能有问题"}
            ]
        }
    ]

    results = []
    for scenario in scenarios:
        result = await risk_analyzer_handler({
            "scenario": scenario['scenario'],
            "risk_factors": scenario['risk_factors']
        }, {})
        results.append({
            "name": scenario['name'],
            "overall_score": result['overall_score'],
            "overall_risk_level": result['overall_risk_level']
        })

    # 按风险评分排序
    results.sort(key=lambda x: x['overall_score'])

    print("方案风险对比（从低到高）:")
    print(f"{'方案':<20} {'风险等级':<12} {'风险评分':<10}")
    print("-" * 80)
    for result in results:
        print(f"{result['name']:<20} {result['overall_risk_level']:<12} "
              f"{result['overall_score']:<10.2f}")

    print()


async def main():
    """运行所有示例"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Risk Analyzer工具使用示例" + " " * 34 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    await example_1_patent_application()
    await example_2_software_development()
    await example_3_business_investment()
    await example_4_custom_risks()
    await example_5_default_risks()
    await example_6_risk_comparison()

    print("=" * 80)
    print("所有示例运行完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
