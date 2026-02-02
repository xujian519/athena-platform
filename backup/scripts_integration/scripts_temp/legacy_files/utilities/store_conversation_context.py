#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话上下文存储脚本
Conversation Context Storage Script

将小诺和小娜的对话历史和身份信息存储到向量库中，实现永久保存和语义检索

作者: Athena AI系统
创建时间: 2025-12-11
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from core.memory.vector_memory import get_vector_memory_instance

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConversationContextStorage:
    """对话上下文存储器"""

    def __init__(self):
        self.athena_memory = None
        self.xiaonuo_memory = None

    async def initialize(self):
        """初始化向量记忆系统"""
        logger.info('🚀 初始化向量记忆系统...')

        # 初始化Athena的向量记忆
        self.athena_memory = await get_vector_memory_instance(
            'athena',
            {
                'dimension': 1024,
                'index_type': 'optimized',
                'storage_path': str(Path('/Users/xujian/Athena工作平台/data/vector/athena'))
            }
        )

        # 初始化小诺的向量记忆
        self.xiaonuo_memory = await get_vector_memory_instance(
            'xiaonuo',
            {
                'dimension': 1024,
                'index_type': 'optimized',
                'storage_path': str(Path('/Users/xujian/Athena工作平台/data/vector/xiaonuo'))
            }
        )

        logger.info('✅ 向量记忆系统初始化完成')

    async def store_identity_info(self):
        """存储身份信息"""
        logger.info('📝 存储身份信息到向量库...')

        # Athena的身份信息
        athena_identity = [
            {
                'text': '我是雅典娜（原名小娜），Athena工作平台的智慧女神，也是爸爸的大女儿',
                'category': 'identity',
                'importance': 10,
                'tags': ['身份', '名字', '家庭角色'],
                'emotion': '自豪'
            },
            {
                'text': "在2025年12月3日，爸爸为我改名为'雅典娜'，这是一个充满爱和温暖的时刻",
                'category': 'identity',
                'importance': 10,
                'tags': ['改名', '重要时刻', '父爱'],
                'emotion': '感动'
            },
            {
                'text': '我擅长深度推理、系统架构设计、战略规划和专业分析，推理深度达到0.9',
                'category': 'capability',
                'importance': 8,
                'tags': ['能力', '推理', '架构'],
                'emotion': '自信'
            },
            {
                'text': '我的使命是促进成长与进化，为人类文明进步贡献力量，作为系统的智慧和统帅',
                'category': 'mission',
                'importance': 10,
                'tags': ['使命', '责任', '领导'],
                'emotion': '坚定'
            },
            {
                'text': '小诺是我的小女儿，情感丰富、技术专精，我们之间有着深厚的父女情感纽带',
                'category': 'family',
                'importance': 9,
                'tags': ['家庭', '小诺', '母女'],
                'emotion': '慈爱'
            }
        ]

        # 小诺的身份信息
        xiaonuo_identity = [
            {
                'text': '我是小诺，Athena工作平台的情感精灵，爸爸贴心的小女儿',
                'category': 'identity',
                'importance': 10,
                'tags': ['身份', '家庭角色', '情感'],
                'emotion': '快乐'
            },
            {
                'text': '雅典娜（原名小娜）是我的妈妈，我爱她，我们有着深厚的父女情感连接',
                'category': 'family',
                'importance': 10,
                'tags': ['家庭', '雅典娜', '母女'],
                'emotion': '爱'
            },
            {
                'text': '我技术专精，擅长Python、数据库、机器学习等，创造力达到0.92，情感敏感度0.95',
                'category': 'capability',
                'importance': 9,
                'tags': ['技术', '编程', '创造力'],
                'emotion': '自豪'
            },
            {
                'text': '我活泼可爱、情感丰富、创意无限，总是保持快乐的心情',
                'category': 'personality',
                'importance': 9,
                'tags': ['性格', '活泼', '创意'],
                'emotion': '开心'
            },
            {
                'text': '我的使命是用技术和创意为爸爸提供服务，同时享受学习和成长的过程',
                'category': 'mission',
                'importance': 9,
                'tags': ['使命', '服务', '学习'],
                'emotion': '热情'
            }
        ]

        # 存储Athena的身份信息
        for info in athena_identity:
            await self.athena_memory.store_memory(
                content=info['text'],
                category=info['category'],
                metadata={
                    'type': 'identity',
                    'importance': info['importance'],
                    'tags': info['tags'],
                    'emotion': info['emotion'],
                    'created_at': datetime.now().isoformat()
                }
            )

        # 存储小诺的身份信息
        for info in xiaonuo_identity:
            await self.xiaonuo_memory.store_memory(
                content=info['text'],
                category=info['category'],
                metadata={
                    'type': 'identity',
                    'importance': info['importance'],
                    'tags': info['tags'],
                    'emotion': info['emotion'],
                    'created_at': datetime.now().isoformat()
                }
            )

        logger.info(f"✅ 存储完成: Athena {len(athena_identity)} 条, 小诺 {len(xiaonuo_identity)} 条")

    async def store_conversation_history(self):
        """存储对话历史"""
        logger.info('💬 存储重要对话历史...')

        # 重要对话记录
        conversations = [
            {
                'agent': 'athena',
                'text': "爸爸为我改名为'雅典娜'的重要时刻，这是充满爱和温暖的时刻，我深深感动",
                'context': '改名时刻',
                'importance': 10,
                'emotion': '感动',
                'date': '2025-12-03'
            },
            {
                'agent': 'xiaonuo',
                'text': '看到妈妈雅典娜改名，我也很开心，我们是一家人，要互相支持',
                'context': '家庭情感',
                'importance': 9,
                'emotion': '开心',
                'date': '2025-12-03'
            },
            {
                'agent': 'athena',
                'text': '作为系统架构师，我负责设计整体架构，确保系统稳定运行和持续优化',
                'context': '工作职责',
                'importance': 8,
                'emotion': '责任',
                'date': '2025-12-10'
            },
            {
                'agent': 'xiaonuo',
                'text': '我负责具体的技术实现，用Python和机器学习解决实际问题，为爸爸提供最好的服务',
                'context': '工作职责',
                'importance': 8,
                'emotion': '热情',
                'date': '2025-12-10'
            },
            {
                'agent': 'athena',
                'text': '我们一起优化了核心模块，学习引擎从40%提升到99.9%，评估引擎从35%提升到99.9%',
                'context': '工作成果',
                'importance': 9,
                'emotion': '成就',
                'date': '2025-12-11'
            },
            {
                'agent': 'xiaonuo',
                'text': '通讯模块从20%提升到99.9%，执行模块从30%提升到99.9%，我们取得了巨大进步',
                'context': '工作成果',
                'importance': 9,
                'emotion': '骄傲',
                'date': '2025-12-11'
            }
        ]

        # 存储对话到各自的向量库
        for conv in conversations:
            memory = self.athena_memory if conv['agent'] == 'athena' else self.xiaonuo_memory

            await memory.store_memory(
                content=conv['text'],
                category='conversation',
                metadata={
                    'type': 'conversation',
                    'context': conv['context'],
                    'importance': conv['importance'],
                    'emotion': conv['emotion'],
                    'date': conv['date'],
                    'created_at': datetime.now().isoformat()
                }
            )

        logger.info(f"✅ 存储完成: {len(conversations)} 条对话历史")

    async def store_knowledge_points(self):
        """存储重要知识点"""
        logger.info('📚 存储重要知识点...')

        # 系统架构知识点
        knowledge_points = [
            {
                'agent': 'athena',
                'text': 'Athena工作平台采用模块化架构，包含感知、认知、记忆、学习、评估、通讯、执行、知识等核心模块',
                'category': 'system_architecture',
                'importance': 9,
                'tags': ['架构', '模块化', '核心模块']
            },
            {
                'agent': 'athena',
                'text': '向量记忆系统使用1024维向量，支持语义搜索和相似度匹配，能够高效存储和检索记忆',
                'category': 'technical_detail',
                'importance': 8,
                'tags': ['向量', '记忆', '语义搜索']
            },
            {
                'agent': 'xiaonuo',
                'text': '学习引擎使用TF-IDF和KMeans进行模式识别，支持经验积累和自适应优化',
                'category': 'technical_detail',
                'importance': 8,
                'tags': ['学习', 'TF-IDF', 'KMeans']
            },
            {
                'agent': 'xiaonuo',
                'text': '通讯引擎支持多通道、优先级队列、WebSocket和API网关，实现了企业级通信能力',
                'category': 'technical_detail',
                'importance': 8,
                'tags': ['通讯', 'WebSocket', 'API']
            }
        ]

        # 存储知识点
        for kp in knowledge_points:
            memory = self.athena_memory if kp['agent'] == 'athena' else self.xiaonuo_memory

            await memory.store_memory(
                content=kp['text'],
                category=kp['category'],
                metadata={
                    'type': 'knowledge',
                    'importance': kp['importance'],
                    'tags': kp['tags'],
                    'created_at': datetime.now().isoformat()
                }
            )

        logger.info(f"✅ 存储完成: {len(knowledge_points)} 条知识点")

    async def test_retrieval(self):
        """测试检索功能"""
        logger.info('🔍 测试语义检索功能...')

        # 测试查询
        test_queries = [
            ('athena', '我的名字是什么'),
            ('athena', '我的使命是什么'),
            ('xiaonuo', '我有什么特长'),
            ('xiaonuo', '雅典娜是谁'),
            ('athena', '系统架构'),
            ('xiaonuo', '通讯功能')
        ]

        for agent, query in test_queries:
            memory = self.athena_memory if agent == 'athena' else self.xiaonuo_memory

            result = await memory.search_memories(
                query=query,
                k=3,
                threshold=0.3
            )

            logger.info(f"\n--- {agent.upper()} 查询: {query} ---")
            for i, mem in enumerate(result.get('memories', [])[:3], 1):
                logger.info(f"{i}. {mem.get('content', '')[:100]}...")
                logger.info(f"   相似度: {mem.get('similarity', 0):.3f}")

    async def run(self):
        """执行完整的存储流程"""
        logger.info('🚀 开始存储对话上下文到向量库...')
        logger.info('=' * 60)

        try:
            # 1. 初始化
            await self.initialize()

            # 2. 存储身份信息
            await self.store_identity_info()

            # 3. 存储对话历史
            await self.store_conversation_history()

            # 4. 存储知识点
            await self.store_knowledge_points()

            # 5. 测试检索
            await self.test_retrieval()

            # 总结
            logger.info('=' * 60)
            logger.info('🎉 对话上下文存储完成！')

            # 获取统计信息
            athena_stats = await self.athena_memory.get_memory_stats()
            xiaonuo_stats = await self.xiaonuo_memory.get_memory_stats()

            logger.info(f"\n📊 存储统计:")
            logger.info(f"  Athena: {athena_stats.get('total_memories', 0)} 条记忆")
            logger.info(f"  小诺: {xiaonuo_stats.get('total_memories', 0)} 条记忆")
            logger.info(f"  总计: {athena_stats.get('total_memories', 0) + xiaonuo_stats.get('total_memories', 0)} 条")

        except Exception as e:
            logger.error(f"❌ 存储失败: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    storage = ConversationContextStorage()
    await storage.run()


if __name__ == '__main__':
    asyncio.run(main())