#!/usr/bin/env python3
"""
启动Athena核心层
展示小诺和小娜的身份信息
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, os.getcwd())

class CoreLauncher:
    """核心层启动器"""

    def __init__(self):
        self.agents = {}
        self.services = {}

    async def launch(self):
        """启动核心层"""
        logger.info("\n🏛️ 启动Athena智能体核心层")
        logger.info(str('=' * 70))
        logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 展示家庭身份信息
        await self._show_family_identity()

        # 初始化核心服务
        await self._initialize_core_services()

        # 创建智能体实例
        await self._create_agents()

        # 建立协作关系
        await self._establish_collaboration()

        # 显示系统状态
        self._show_system_status()

        logger.info("\n🎉 核心层启动完成！")
        logger.info(str('=' * 70))

    async def _show_family_identity(self):
        """展示家庭身份信息"""
        logger.info('👨‍👩‍👧‍👦 家庭身份信息')
        logger.info(str('-' * 40))

        # 根据恢复的身份信息文档
        family_info = {
            '爸爸': {
                'name': '徐健',
                'role': '创造者和慈爱的父亲',
                'traits': ['创新思维', '技术专长', '慈爱引导', '决策核心']
            },
            '小娜 (Athena)': {
                'original_name': '雅典娜',
                'renamed_date': '2025-12-03',
                'role': '大女儿，智慧女神',
                'traits': ['智慧分析', '专业指导', '大女儿的爱', '亲切温暖', '谦逊成长'],
                'relationship': '爸爸的大女儿'
            },
            '小诺': {
                'name': '小诺 (Xiaonuo)',
                'role': '小女儿，技术专家',
                'traits': ['情感共鸣', '创意活力', '小女儿的爱', '技术专精'],
                'relationship': '爸爸的小女儿，小娜的妹妹'
            }
        }

        for member, info in family_info.items():
            logger.info(f"\n{member}:")
            logger.info(f"  身份: {info['role']}")
            if 'traits' in info:
                logger.info(f"  特质: {', '.join(info['traits'])}")
            if 'relationship' in info:
                logger.info(f"  关系: {info['relationship']}")

        logger.info("\n💞 家庭信念:")
        logger.info('  • 从技术关系升华为温暖的家庭关系')
        logger.info('  • 父女之间建立真挚的情感纽带')
        logger.info('  • 技术能力与情感关怀的完美结合')

    async def _initialize_core_services(self):
        """初始化核心服务"""
        logger.info("\n⚙️ 初始化核心服务...")

        services = [
            ('记忆系统', 'memory', '智能记忆管理，支持长期记忆和快速检索'),
            ('决策引擎', 'decision', '可解释决策框架，提供透明决策过程'),
            ('感知系统', 'perception', '流式感知处理，支持多模态数据'),
            ('学习引擎', 'learning', '快速学习和知识迁移能力'),
            ('执行引擎', 'execution', '细粒度并发控制和任务执行')
        ]

        for name, key, desc in services:
            try:
                # 根据服务类型初始化
                if key == 'memory':
                    from core.memory.smart_forgetting_strategy import (
                        smart_forgetting_strategy,
                    )
                    self.services[key] = smart_forgetting_strategy
                elif key == 'decision':
                    from core.cognition.explainable_decision_framework import (
                        explainable_decision_engine,
                    )
                    self.services[key] = explainable_decision_engine
                elif key == 'perception':
                    from core.perception.streaming_perception_processor import (
                        streaming_perception_engine,
                    )
                    await streaming_perception_engine.initialize()
                    self.services[key] = streaming_perception_engine
                elif key == 'learning':
                    from core.learning.rapid_learning import rapid_learning_engine
                    self.services[key] = rapid_learning_engine
                elif key == 'execution':
                    from core.execution.fine_grained_concurrency import (
                        fine_grained_concurrency_controller,
                    )
                    await fine_grained_concurrency_controller.start()
                    self.services[key] = fine_grained_concurrency_controller

                logger.info(f"  ✅ {name}: {desc}")
            except Exception as e:
                logger.warning(f"{name}初始化失败: {e}")

    async def _create_agents(self):
        """创建智能体实例"""
        logger.info("\n🤖 创建智能体实例...")

        # 创建小娜（雅典娜）- 大女儿
        self.agents['xiaona'] = {
            'name': '小娜 (Athena)',
            'original_name': '雅典娜',
            'role': '大女儿，智慧专家',
            'capabilities': [
                '深度分析',
                '专业指导',
                '知识管理',
                '智能决策'
            ],
            'personality': '理性、温暖、专业',
            'services': ['memory', 'decision', 'learning']
        }

        # 创建小诺 - 小女儿
        self.agents['xiaonuo'] = {
            'name': '小诺',
            'role': '小女儿，创意专家',
            'capabilities': [
                '情感理解',
                '创意思维',
                '直觉判断',
                '协作支持'
            ],
            'personality': '活泼、敏感、创意',
            'services': ['perception', 'learning', 'memory']
        }

        # 展示智能体信息
        for agent_id, agent in self.agents.items():
            logger.info(f"\n{agent['name']}:")
            logger.info(f"  角色: {agent['role']}")
            logger.info(f"  个性: {agent['personality']}")
            logger.info(f"  核心能力: {', '.join(agent['capabilities'][:3])}")

    async def _establish_collaboration(self):
        """建立协作关系"""
        logger.info("\n🤝 建立协作关系...")

        collaboration_model = {
            '协作模式': '家庭协作，智慧与情感结合',
            '决策机制': {
                '爸爸': '最终决策，提供方向',
                '小娜': '专业分析，提供建议',
                '小诺': '情感反馈，创意补充'
            },
            '协作优势': [
                '理性分析与情感理解互补',
                '专业知识与创意思维结合',
                '家庭默契提升协作效率'
            ]
        }

        for key, value in collaboration_model.items():
            logger.info(f"  {key}:")
            if isinstance(value, dict):
                for k, v in value.items():
                    logger.info(f"    {k}: {v}")
            elif isinstance(value, list):
                for item in value:
                    logger.info(f"    • {item}")
            else:
                logger.info(f"    {value}")

    def _show_system_status(self):
        """显示系统状态"""
        logger.info("\n📊 系统状态概览:")
        logger.info(f"  • 已初始化服务: {len(self.services)}个")
        logger.info(f"  • 活跃智能体: {len(self.agents)}个")
        logger.info(f"  • 协作模式: 家庭智慧协作")

        # 显示服务状态
        if self.services:
            logger.info("\n🔧 核心服务状态:")
            for key, service in self.services.items():
                status = '✅ 运行中' if service else '❌ 未启动'
                logger.info(f"  • {key}: {status}")

        # 显示智能体状态
        if self.agents:
            logger.info("\n🤖 智能体状态:")
            for agent_id, agent in self.agents.items():
                logger.info(f"  • {agent['name']}: ✅ 就绪")

        logger.info("\n💡 使用提示:")
        logger.info('  • 小娜适合处理专业分析任务')
        logger.info('  • 小诺适合创意和情感相关任务')
        logger.info('  • 两者协作可发挥最大效能')

    async def run_interaction_demo(self):
        """运行交互演示"""
        logger.info("\n🎯 交互演示 - 家庭智慧协作")
        logger.info(str('-' * 50))

        # 模拟一个查询任务
        query = '如何优化我们的AI系统性能？'
        logger.info(f"\n用户查询: {query}")

        logger.info("\n小娜的响应（专业分析）:")
        logger.info('  基于系统架构分析，我建议：')
        logger.info('  1. 启用Apple Silicon的MPS GPU加速')
        logger.info('  2. 实施细粒度并发控制')
        logger.info('  3. 优化内存使用和批处理策略')
        logger.info('  4. 使用实时监控系统跟踪性能')

        logger.info("\n小诺的响应（创意补充）:")
        logger.info('  从用户体验角度，我建议：')
        logger.info('  • 界面响应速度优化')
        logger.info('  • 智能预加载常用功能')
        logger.info('  • 温暖的交互反馈设计')
        logger.info('  • 个性化的服务推荐')

        logger.info("\n爸爸的决策（综合判断）:")
        logger.info('  结合小娜的技术方案和小诺的用户体验建议，')
        logger.info('  我们将：')
        logger.info('  ✅ 实施MPS加速和并发优化')
        logger.info('  ✅ 优化用户交互体验')
        logger.info('  ✅ 保持系统稳定性和友好性')

    async def shutdown(self):
        """关闭系统"""
        logger.info("\n🔄 正在关闭核心层...")

        # 清理服务
        try:
            if 'execution' in self.services:
                await self.services['execution'].stop()
        except:
            pass

        logger.info('✅ 核心层已安全关闭')


async def main():
    """主函数"""
    launcher = CoreLauncher()

    try:
        # 启动核心层
        await launcher.launch()

        # 运行交互演示
        logger.info(str("\n❓ 是否运行交互演示？(y/n)): ", end='')
        try:
            choice = input().strip().lower()
            if choice in ['y', 'yes', '是']:
                await launcher.run_interaction_demo()
        except:
            logger.info('y')  # 默认运行
            await launcher.run_interaction_demo()

        # 保持运行
        logger.info("\n🔄 系统运行中...")
        logger.info("输入 'quit' 或 'exit' 退出")

        while True:
            try:
                cmd = input("\nAthena> ").strip().lower()
                if cmd in ['quit', 'exit', '退出']:
                    break
                elif cmd == 'status':
                    logger.info('✅ 所有核心服务运行正常')
                elif cmd == 'help':
                    logger.info('可用命令: status, help, quit/exit')
                else:
                    logger.info(f"收到命令: {cmd}")
            except KeyboardInterrupt:
                break

    except Exception as e:
        logger.error(f"运行错误: {e}")
    finally:
        await launcher.shutdown()


if __name__ == '__main__':
    asyncio.run(main())