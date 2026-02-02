#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试人机协作决策模型
Test Human-in-the-Loop Decision Model
"""

import sys
import os
sys.path.append(os.path.expanduser("~/Athena工作平台"))

import asyncio
from datetime import datetime
from typing import Dict, Any

async def test_human_in_loop_decision():
    """测试人机协作决策模型"""
    print("🤝 测试人机协作决策模型")
    print("=" * 60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # 导入模型
        from core.agent.human_in_the_loop_decision_model import HumanInTheLoopDecisionModel

        # 创建决策模型（模拟环境）
        decision_model = HumanInTheLoopDecisionModel(
            evaluation_engine=None,  # 模拟
            learning_engine=None,    # 模拟
            memory_system=None       # 模拟
        )

        print("✅ 人机协作决策模型创建成功\n")

        # 测试场景1: 技术选型决策
        await test_tech_selection(decision_model)

        # 测试场景2: 资源分配决策
        await test_resource_allocation(decision_model)

        # 测试场景3: 战略规划决策
        await test_strategic_planning(decision_model)

        # 获取决策洞察
        await get_decision_insights(decision_model)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_tech_selection(decision_model):
    """测试技术选型决策"""
    print("📊 测试场景1: 技术选型决策")
    print("-" * 50)

    problem = "为项目选择后端框架"

    options = [
        {
            'name': 'Spring Boot',
            'description': 'Java企业级框架',
            'pros': ['成熟稳定', '生态完善', '企业级支持'],
            'cons': ['学习曲线', '资源消耗大'],
            'risk_level': 0.2,
            'expected_value': 0.85,
            'implementation_plan': {
                'timeline': '3个月',
                'team_size': 5,
                'budget': '中等'
            }
        },
        {
            'name': 'FastAPI',
            'description': 'Python现代Web框架',
            'pros': ['高性能', '易于学习', '开发效率高'],
            'cons': ['生态相对新', '企业级案例少'],
            'risk_level': 0.4,
            'expected_value': 0.75,
            'implementation_plan': {
                'timeline': '2个月',
                'team_size': 3,
                'budget': '低'
            }
        },
        {
            'name': 'Node.js + Express',
            'description': 'JavaScript全栈方案',
            'pros': ['统一技术栈', '社区活跃', '灵活性强'],
            'cons': ['单线程限制', '内存使用高'],
            'risk_level': 0.5,
            'expected_value': 0.7,
            'implementation_plan': {
                'timeline': '2.5个月',
                'team_size': 4,
                'budget': '中低'
            }
        }
    ]

    context = {
        'project_type': '企业级应用',
        'timeline': '3个月内',
        'team_experience': 'Java为主',
        'performance_requirement': '高并发'
    }

    # 执行协作决策
    result = await decision_model.collaborative_decision_process(
        problem=problem,
        options_data=options,
        context=context
    )

    if result['success']:
        print(f"✅ 决策成功!")
        print(f"   选中方案: {result['result']['selected_option'].name}")
        print(f"   置信度: {result['result']['confidence']:.2f}")
        print(f"   人类参与: {'是' if result['result']['human_incorporated'] else '否'}")
    else:
        print(f"⚠️ 决策部分成功: {result.get('error', '')}")

    print()

async def test_resource_allocation(decision_model):
    """测试资源分配决策"""
    print("📊 测试场景2: 资源分配决策")
    print("-" * 50)

    problem = "分配项目开发资源"

    options = [
        {
            'name': '优先核心功能',
            'description': '集中资源开发核心功能',
            'pros': ['保证核心质量', '快速MVP', '风险可控'],
            'cons': ['功能受限', '后期扩展'],
            'risk_level': 0.3,
            'expected_value': 0.8
        },
        {
            'name': '并行开发',
            'description': '多个功能同时开发',
            'pros': ['功能完整', '时间节省'],
            'cons': ['资源分散', '协调困难'],
            'risk_level': 0.6,
            'expected_value': 0.65
        },
        {
            'name': '分阶段实施',
            'description': '分阶段逐步实施',
            'pros': ['风险低', '反馈及时', '灵活调整'],
            'cons': ['周期长', '交付晚'],
            'risk_level': 0.2,
            'expected_value': 0.75
        }
    ]

    context = {
        'budget': '100万',
        'timeline': '6个月',
        'team_size': 8,
        'stakeholder_expectation': '高'
    }

    result = await decision_model.collaborative_decision_process(
        problem=problem,
        options_data=options,
        context=context
    )

    print(f"✅ 资源分配决策完成")
    print()

async def test_strategic_planning(decision_model):
    """测试战略规划决策"""
    print("📊 测试场景3: 战略规划决策")
    print("-" * 50)

    problem = "制定产品发展策略"

    options = [
        {
            'name': '市场领先策略',
            'description': '快速占领市场份额',
            'pros': ['先发优势', '品牌效应', '规模经济'],
            'cons': ['投入大', '风险高', '竞争激烈'],
            'risk_level': 0.7,
            'expected_value': 0.9
        },
        {
            'name': '差异化策略',
            'description': '专注细分市场',
            'pros': ['竞争小', '利润率高', '客户忠诚'],
            'cons': ['市场小', '增长限制'],
            'risk_level': 0.4,
            'expected_value': 0.7
        },
        {
            'name': '成本领先策略',
            'description': '降低成本竞争',
            'pros': ['价格优势', '需求稳定'],
            'cons': ['利润低', '品牌影响弱'],
            'risk_level': 0.5,
            'expected_value': 0.6
        }
    ]

    context = {
        'industry': '科技',
        'company_size': '中型',
        'capital': '充足',
        'competitor_count': '多'
    }

    result = await decision_model.collaborative_decision_process(
        problem=problem,
        options_data=options,
        context=context
    )

    print(f"✅ 战略规划决策完成")
    print()

async def get_decision_insights(decision_model):
    """获取决策洞察"""
    print("📈 获取决策洞察")
    print("-" * 50)

    insights = await decision_model.get_decision_insights()

    if 'message' in insights:
        print(insights['message'])
    else:
        print(f"📊 决策统计:")
        print(f"  • 总决策数: {insights['total_decisions']}")
        print(f"  • 最近决策数: {insights['recent_decisions']}")
        print(f"  • 平均置信度: {insights['average_confidence']:.2f}")
        print(f"  • 人类参与率: {insights['human_participation_rate']:.2%}")

        print(f"\n💡 爸爸偏好:")
        prefs = insights['dad_preferences']
        print(f"  • 风险承受度: {prefs['risk_tolerance']:.2f}")
        print(f"  • 决策风格: {prefs['decision_style']}")
        print(f"  • 关注因素: {', '.join(prefs['preferred_factors'])}")

        if insights['recommendations']:
            print(f"\n📋 改进建议:")
            for rec in insights['recommendations']:
                print(f"  • {rec}")

    print("\n🎉 人机协作决策模型测试完成！")
    print("=" * 60)
    print("\n💡 关键特性:")
    print("  ✅ 多阶段决策流程（初始化→审核→协作→决策→执行）")
    print("  ✅ 人类在环（Human-in-the-Loop）设计")
    print("  ✅ 动态学习和偏好适应")
    print("  ✅ 详细的决策报告和理由说明")
    print("  ✅ 决策历史记录和洞察分析")

if __name__ == "__main__":
    asyncio.run(test_human_in_loop_decision())