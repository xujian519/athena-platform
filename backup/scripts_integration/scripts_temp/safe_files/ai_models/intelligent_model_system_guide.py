#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能模型系统使用指南
Intelligent Model System Usage Guide
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from athena_xiaonuo_cloud_integration import AthenaXiaoNuoCloudIntegration
from simple_model_manager import SimpleModelManager

logger = logging.getLogger(__name__)

class IntelligentModelSystem:
    """智能模型系统 - 展示全部能力"""

    def __init__(self):
        self.integration = AthenaXiaoNuoCloudIntegration()
        self.model_manager = SimpleModelManager()

    async def demonstrate_all_capabilities(self):
        """演示所有功能"""
        logger.info(str("\n" + '='*80))
        logger.info('🌟 智能模型系统 - 全功能展示')
        logger.info(str('='*80))

        # 1. 智能路由自动选择最优模型
        logger.info(str("\n" + '📍 1. 智能路由展示'.center(50)))
        logger.info(str('='*50))
        await self._demonstrate_smart_routing()

        # 2. Athena深度推理能力
        logger.info(str("\n" + '🧠 2. Athena深度推理'.center(50)))
        logger.info(str('='*50))
        await self._demonstrate_athena_reasoning()

        # 3. 小诺情感互动
        logger.info(str("\n" + '💝 3. 小诺情感互动'.center(50)))
        logger.info(str('='*50))
        await self._demonstrate_xiaonuo_interaction()

        # 4. 协作模式
        logger.info(str("\n" + '🤝 4. 协作模式'.center(50)))
        logger.info(str('='*50))
        await self._demonstrate_collaborative_mode()

        # 5. 高级功能
        logger.info(str("\n" + '⚡ 5. 高级功能'.center(50)))
        logger.info(str('='*50))
        await self._demonstrate_advanced_features()

    async def _demonstrate_smart_routing(self):
        """演示智能路由"""
        logger.info("\n📋 测试用例：")
        test_cases = [
            {
                'input': '你好，请用中文回复',
                'expected_model': 'GLM-4.6 (中文优化+免费)',
                'reason': '中文对话自动选择GLM-4.6'
            },
            {
                'input': '证明哥德巴赫猜想',
                'expected_model': 'DeepSeek-V3 (数学推理最强)',
                'reason': '复杂推理自动选择DeepSeek'
            },
            {
                'input': '实现一个区块链节点',
                'expected_model': 'DeepSeek-Coder (代码专业)',
                'reason': '编程任务自动选择Code模型'
            },
            {
                'input': '解释量子纠缠',
                'expected_model': 'Qwen-2.5 (知识库丰富)',
                'reason': '知识问答自动选择Qwen'
            }
        ]

        for i, case in enumerate(test_cases, 1):
            logger.info(f"\n{i}. {case['input'][:30]}...")
            logger.info(f"   预期模型: {case['expected_model']}")
            logger.info(f"   路由原因: {case['reason']}")

            # 执行请求
            result = self.model_manager.chat(case['input'], 'smart_routing')

            if result['success']:
                model_used = result['model_used']
                logger.info(f"   ✅ 实际使用: {model_used}")
                logger.info(f"   响应: {result['response'][:80]}...")
            else:
                logger.info(f"   ❌ 错误: {result['error']}")

    async def _demonstrate_athena_reasoning(self):
        """演示Athena推理"""
        logger.info("\n🧠 Athena推理展示：")
        reasoning_tasks = [
            {
                'task': '设计一个高性能的微服务架构',
                'complexity': 'deep',
                'description': '需要系统架构设计'
            },
            {
                'task': '如何平衡创新与稳定？',
                'complexity': 'standard',
                'description': '哲学层面思考'
            },
            {
                'task': '分析技术债务的成因',
                'complexity': 'deep',
                'description': '深层原因分析'
            }
        ]

        for i, task in enumerate(reasoning_tasks, 1):
            logger.info(f"\n{i}. {task['task']}")
            logger.info(f"   复杂度: {task['complexity']}")
            logger.info(f"   描述: {task['description']}")

            result = await self.integration.athena_reasoning(task['task'], task['complexity'])

            if result['status'] == 'success':
                logger.info(f"   ✅ 推理深度: {result['confidence']:.1f}/1.0")
                logger.info(f"   推理要点:")
                # 提取推理要点
                reasoning_lines = result['reasoning'].split('\n')
                for line in reasoning_lines[:3]:
                    if line.strip():
                        logger.info(f"     • {line.strip()}")

    async def _demonstrate_xiaonuo_interaction(self):
        """演示小诺互动"""
        logger.info("\n💝 小诺互动展示：")
        interaction_scenarios = [
            {
                'user_input': '我今天考试没考好，好难过',
                'emotion': 'sad',
                'xiaonuo_style': '温暖安慰'
            },
            {
                'user_input': '我终于学会了Python！',
                'emotion': 'excited',
                'xiaonuo_style': '兴奋庆祝'
            },
            {
                'user_input': '这个概念太难了，不理解',
                'emotion': 'confused',
                'xiaonuo_style': '耐心解释'
            }
        ]

        for i, scenario in enumerate(interaction_scenarios, 1):
            logger.info(f"\n{i}. 用户: '{scenario['user_input']}'")
            logger.info(f"   情感: {scenario['emotion']}")
            logger.info(f"   小诺风格: {scenario['xiaonuo_style']}")

            result = await self.integration.xiaonuo_empathetic_chat(
                scenario['user_input'],
                scenario['emotion']
            )

            if result['status'] == 'success':
                logger.info(f"   ✅ {result['xiaonuo_emoji']} {result['response'][:100]}...")
            else:
                logger.info(f"   ❌ 错误: {result['error']}")

    async def _demonstrate_collaborative_mode(self):
        """演示协作模式"""
        logger.info("\n🤝 协作模式展示：")
        logger.info("\n📝 复杂场景：用户遇到技术难题，同时需要情感支持和专业解决")

        scenario = {
            'problem': '我的React项目性能很差，用户抱怨加载慢，我不知道怎么办...',
            'user_mood': 'anxious',
            'needs': ['情感支持', '技术分析', '具体方案']
        }

        logger.info(f"\n用户问题：{scenario['problem']}")
        logger.info(f"用户心情：{scenario['user_mood']}")
        logger.info(f"需求：{', '.join(scenario['needs'])}")

        result = await self.integration.collaborative_solve(
            scenario['problem'],
            scenario['user_mood']
        )

        if result['status'] == 'success' and result['mode'] == 'collaborative':
            logger.info(f"\n✨ 小诺的温暖支持:")
            support = result['xiaonuo_support']['emotional']
            logger.info(str(support[:150] + '...'))

            logger.info(f"\n🧠 Athena的专业分析:")
            analysis = result['athena_analysis']['reasoning']
            logger.info(str(analysis[:150] + '...'))

            logger.info(f"\n💡 综合建议:")
            suggestions = result['combined_response'].split('\n\n')
            for suggestion in suggestions[:3]:
                if suggestion.strip():
                    logger.info(f"• {suggestion.strip()[:80]}...")
        else:
            logger.info(f"\n❌ 状态: {result.get('status', 'unknown')}")

    async def _demonstrate_advanced_features(self):
        """演示高级功能"""
        logger.info("\n⚡ 高级功能展示：")

        # 1. 成本优化
        logger.info("\n1️⃣ 成本优化策略")
        logger.info('   • GLM-4.6优先使用（包月免费）')
        logger.info('   • 简单任务用小模型')
        logger.info('   • 复杂任务才用大模型')
        logger.info('   • 实时成本监控')

        # 2. 性能监控
        logger.info("\n2️⃣ 性能监控")
        logger.info('   • 请求成功率：>95%')
        logger.info('   • 平均响应时间：<2秒')
        logger.info('   • 模型使用统计')

        # 3. 自定义路由
        logger.info("\n3️⃣ 自定义路由规则")
        logger.info('   • 可根据任务类型定制')
        logger.info('   • 支持用户偏好设置')
        logger.info('   • 实时调整路由策略')

        # 4. 批量处理
        logger.info("\n4️⃣ 批量处理能力")
        logger.info('   • 支持并行请求')
        logger.info('   • 任务队列管理')
        logger.info('   • 负载均衡')

        # 获取实际统计
        stats = self.integration.get_performance_metrics()
        logger.info("\n📊 实时统计：")
        logger.info(f"   • 总请求数：{stats['total_interactions']}")
        logger.info(f"   • 成功率：{stats['success_rate']:.1f}%")
        logger.info(f"   • 常用模型：")
        for model, count in stats['favorite_models'].items():
            logger.info(f"     - {model}: {count} 次")

    def get_usage_tips(self) -> Dict[str, List[str]]:
        """获取使用技巧"""
        return {
            '高效使用': [
                '简单问题用GLM-4.6（免费）',
                "需要深度分析时指定'深度推理'",
                "编程任务直接指定'coding'",
                "超长文档用'long_text'模式"
            ],
            '节省成本': [
                'GLM-4.6优先（已包月）',
                '批量处理时合并请求',
                '使用缓存减少重复调用',
                '避免不必要的大模型调用'
            ],
            '获得最佳结果': [
                '描述问题时尽可能详细',
                '提供上下文信息',
                '指定输出格式要求',
                '明确任务目标'
            ]
        }

    def print_quick_start_guide(self):
        """打印快速开始指南"""
        logger.info(str("\n" + '='*80))
        logger.info('🎯 快速开始指南')
        logger.info(str('='*80))

        guide = """
1. 直接对话模式：
   manager = SimpleModelManager()
   response = manager.chat('你好，请介绍一下自己')

2. 情感感知模式：
   integration = AthenaXiaoNuoCloudIntegration()
   response = await integration.xiaonuo_empathetic_chat('我需要帮助', 'sad')

3. 深度推理模式：
   response = await integration.athena_reasoning('复杂问题分析', 'deep')

4. 协作模式（推荐）：
   response = await integration.collaborative_solve('问题', 'neutral')

5. 获取使用统计：
   stats = integration.get_performance_metrics()

🚀 立即开始使用，享受智能模型的强大能力！
        """
        logger.info(str(guide))

# 使用示例
async def main():
    """主函数"""
    system = IntelligentModelSystem()

    logger.info('🌟 欢迎使用智能模型系统！')

    # 打印快速开始指南
    system.print_quick_start_guide()

    # 获取使用技巧
    tips = system.get_usage_tips()

    logger.info("\n💡 使用技巧：")
    for category, tip_list in tips.items():
        logger.info(f"\n{category}:")
        for tip in tip_list:
            logger.info(f"   • {tip}")

    # 演示所有功能
    logger.info(str("\n" + '='*60))
    logger.info('🚀 开始功能演示...')
    logger.info(str('='*60))

    await system.demonstrate_all_capabilities()

if __name__ == '__main__':
    asyncio.run(main())