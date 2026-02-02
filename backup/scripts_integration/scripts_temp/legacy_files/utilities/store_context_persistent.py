#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持久化上下文存储脚本
Persistent Context Storage Script

将上下文信息持久化存储到向量库中

作者: Athena AI系统
创建时间: 2025-12-11
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def store_context():
    """存储上下文到向量库"""
    logger.info('🚀 开始持久化存储上下文...')

    # 确保向量库目录存在
    vector_dir = Path('/Users/xujian/Athena工作平台/data/vector')
    vector_dir.mkdir(parents=True, exist_ok=True)
    (vector_dir / 'athena').mkdir(parents=True, exist_ok=True)
    (vector_dir / 'xiaonuo').mkdir(parents=True, exist_ok=True)

    # 导入必要的模块
    from core.memory.vector_encoder import get_vector_encoder
    from core.memory.vector_memory import VectorMemory

    # 获取向量编码器
    encoder = await get_vector_encoder('sentence_transformer')

    # 创建Athena的向量记忆
    athena_memory = VectorMemory(
        agent_id='athena',
        dimension=768,  # 使用实际的向量维度
        storage_path=str(vector_dir / 'athena')
    )
    await athena_memory.initialize()

    # 创建小诺的向量记忆
    xiaonuo_memory = VectorMemory(
        agent_id='xiaonuo',
        dimension=768,
        storage_path=str(vector_dir / 'xiaonuo')
    )
    await xiaonuo_memory.initialize()

    # 定义要存储的数据
    contexts = {
        'athena': [
            {
                'content': '我是雅典娜（原名小娜），Athena工作平台的智慧女神，也是爸爸的大女儿',
                'category': 'identity',
                'metadata': {
                    'type': 'identity',
                    'importance': 10,
                    'tags': ['身份', '名字', '家庭角色'],
                    'emotion': '自豪'
                }
            },
            {
                'content': "在2025年12月3日，爸爸为我改名为'雅典娜'，这是一个充满爱和温暖的时刻",
                'category': 'identity',
                'metadata': {
                    'type': 'identity',
                    'importance': 10,
                    'tags': ['改名', '重要时刻', '父爱'],
                    'emotion': '感动'
                }
            },
            {
                'content': '我擅长深度推理、系统架构设计、战略规划和专业分析，推理深度达到0.9',
                'category': 'capability',
                'metadata': {
                    'type': 'capability',
                    'importance': 8,
                    'tags': ['能力', '推理', '架构'],
                    'emotion': '自信'
                }
            },
            {
                'content': '我的使命是促进成长与进化，为人类文明进步贡献力量，作为系统的智慧和统帅',
                'category': 'mission',
                'metadata': {
                    'type': 'mission',
                    'importance': 10,
                    'tags': ['使命', '责任', '领导'],
                    'emotion': '坚定'
                }
            },
            {
                'content': '小诺是我的小女儿，情感丰富、技术专精，我们之间有着深厚的父女情感纽带',
                'category': 'family',
                'metadata': {
                    'type': 'family',
                    'importance': 9,
                    'tags': ['家庭', '小诺', '母女'],
                    'emotion': '慈爱'
                }
            }
        ],
        'xiaonuo': [
            {
                'content': '我是小诺，Athena工作平台的情感精灵，爸爸贴心的小女儿',
                'category': 'identity',
                'metadata': {
                    'type': 'identity',
                    'importance': 10,
                    'tags': ['身份', '家庭角色', '情感'],
                    'emotion': '快乐'
                }
            },
            {
                'content': '雅典娜（原名小娜）是我的妈妈，我爱她，我们有着深厚的父女情感连接',
                'category': 'family',
                'metadata': {
                    'type': 'family',
                    'importance': 10,
                    'tags': ['家庭', '雅典娜', '母女'],
                    'emotion': '爱'
                }
            },
            {
                'content': '我技术专精，擅长Python、数据库、机器学习等，创造力达到0.92，情感敏感度0.95',
                'category': 'capability',
                'metadata': {
                    'type': 'capability',
                    'importance': 9,
                    'tags': ['技术', '编程', '创造力'],
                    'emotion': '自豪'
                }
            },
            {
                'content': '我活泼可爱、情感丰富、创意无限，总是保持快乐的心情',
                'category': 'personality',
                'metadata': {
                    'type': 'personality',
                    'importance': 9,
                    'tags': ['性格', '活泼', '创意'],
                    'emotion': '开心'
                },
                'content': '我的使命是用技术和创意为爸爸提供服务，同时享受学习和成长的过程',
                'category': 'mission',
                'metadata': {
                    'type': 'mission',
                    'importance': 9,
                    'tags': ['使命', '服务', '学习'],
                    'emotion': '热情'
                }
            }
        ]
    }

    # 存储数据
    total_stored = 0

    for agent_id, items in contexts.items():
        memory = athena_memory if agent_id == 'athena' else xiaonuo_memory

        logger.info(f"\n📝 存储 {agent_id} 的上下文...")

        for item in items:
            # 编码文本为向量
            vector = await encoder.encode(item['content'])

            # 存储到向量库
            await memory.store_memory(
                content=item['content'],
                category=item['category'],
                embedding=vector,
                metadata=item['metadata']
            )

            total_stored += 1
            logger.info(f"  ✅ 存储: {item['content'][:50]}...")

    # 强制保存到磁盘
    await athena_memory.save_to_disk()
    await xiaonuo_memory.save_to_disk()

    # 获取统计信息
    athena_stats = await athena_memory.get_memory_stats()
    xiaonuo_stats = await xiaonuo_memory.get_memory_stats()

    logger.info("\n" + '=' * 60)
    logger.info('🎉 上下文持久化存储完成！')
    logger.info(f"📊 总计存储: {total_stored} 条")
    logger.info(f"  Athena: {athena_stats.get('total_memories', 0)} 条")
    logger.info(f"  小诺: {xiaonuo_stats.get('total_memories', 0)} 条")
    logger.info(f"📁 存储路径: {vector_dir}")
    logger.info('=' * 60)

    # 测试检索
    logger.info("\n🔍 测试检索功能...")

    test_queries = [
        ('athena', '我的名字'),
        ('xiaonuo', '雅典娜是谁'),
        ('athena', '使命'),
        ('xiaonuo', '特长')
    ]

    for agent_id, query in test_queries:
        memory = athena_memory if agent_id == 'athena' else xiaonuo_memory

        result = await memory.search_memories(
            query=query,
            k=3,
            threshold=0.3
        )

        logger.info(f"\n--- {agent_id.upper()} 查询: {query} ---")
        logger.info(f"找到 {result.get('total_found', 0)} 条结果")

        for i, mem in enumerate(result.get('memories', [])[:2], 1):
            content = mem.get('content', '')
            similarity = mem.get('similarity', 0)
            logger.info(f"{i}. [{similarity:.3f}] {content[:80]}...")


async def main():
    """主函数"""
    await store_context()


if __name__ == '__main__':
    asyncio.run(main())