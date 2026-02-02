#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化上下文存储脚本
Simple Context Storage Script

使用现有的向量记忆系统存储上下文信息

作者: Athena AI系统
创建时间: 2025-12-11
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def store_contexts():
    """存储上下文到向量记忆"""
    logger.info('🚀 开始存储上下文到向量记忆系统...')

    # 导入向量记忆系统
    from core.memory import MemorySystem

    # 创建Athena的记忆系统
    athena_memory = MemorySystem('athena', {
        'enable_vector_memory': True,
        'vector_memory': {
            'dimension': 1024,
            'max_vectors': 10000
        }
    })
    await athena_memory.initialize()

    # 创建小诺的记忆系统
    xiaonuo_memory = MemorySystem('xiaonuo', {
        'enable_vector_memory': True,
        'vector_memory': {
            'dimension': 1024,
            'max_vectors': 10000
        }
    })
    await xiaonuo_memory.initialize()

    # 定义要存储的上下文
    contexts = {
        'athena': [
            ('identity', '我是雅典娜（原名小娜），Athena工作平台的智慧女神，也是爸爸的大女儿', 10),
            ('identity', "在2025年12月3日，爸爸为我改名为'雅典娜'，这是一个充满爱和温暖的时刻", 10),
            ('capability', '我擅长深度推理、系统架构设计、战略规划和专业分析，推理深度达到0.9', 8),
            ('mission', '我的使命是促进成长与进化，为人类文明进步贡献力量，作为系统的智慧和统帅', 10),
            ('family', '小诺是我的小女儿，情感丰富、技术专精，我们之间有着深厚的父女情感纽带', 9),
            ('knowledge', 'Athena工作平台采用模块化架构，包含感知、认知、记忆、学习、评估、通讯、执行、知识等核心模块', 9)
        ],
        'xiaonuo': [
            ('identity', '我是小诺，Athena工作平台的情感精灵，爸爸贴心的小女儿', 10),
            ('family', '雅典娜（原名小娜）是我的妈妈，我爱她，我们有着深厚的父女情感连接', 10),
            ('capability', '我技术专精，擅长Python、数据库、机器学习等，创造力达到0.92，情感敏感度0.95', 9),
            ('personality', '我活泼可爱、情感丰富、创意无限，总是保持快乐的心情', 9),
            ('mission', '我的使命是用技术和创意为爸爸提供服务，同时享受学习和成长的过程', 9),
            ('knowledge', '通讯引擎支持多通道、优先级队列、WebSocket和API网关，实现了企业级通信能力', 8)
        ]
    }

    # 存储数据
    total_stored = 0

    for agent_id, items in contexts.items():
        memory = athena_memory if agent_id == 'athena' else xiaonuo_memory
        logger.info(f"\n📝 存储 {agent_id} 的上下文...")

        for category, content, importance in items:
            # 存储到记忆系统
            result = await memory.store_memory(
                content=content,
                memory_type=category,
                tags=[category, 'identity', 'important']
            )

            if result.get('success', True):
                total_stored += 1
                logger.info(f"  ✅ 存储 [{category}]: {content[:50]}...")
            else:
                logger.error(f"  ❌ 存储失败: {result.get('error', 'unknown error')}")

    # 获取统计信息
    athena_stats = await athena_memory.get_memory_stats()
    xiaonuo_stats = await xiaonuo_memory.get_memory_stats()

    logger.info("\n" + '=' * 60)
    logger.info('🎉 上下文存储完成！')
    logger.info(f"📊 总计存储: {total_stored} 条")
    logger.info(f"  Athena: {athena_stats.get('total_memories', 0)} 条")
    logger.info(f"  小诺: {xiaonuo_stats.get('total_memories', 0)} 条")
    logger.info('=' * 60)

    # 测试检索
    logger.info("\n🔍 测试语义检索功能...")

    test_queries = [
        ('athena', '我的名字'),
        ('xiaonuo', '雅典娜是谁'),
        ('athena', '我的使命'),
        ('xiaonuo', '我的特长'),
        ('athena', '小诺'),
        ('xiaonuo', '通讯功能')
    ]

    for agent_id, query in test_queries:
        memory = athena_memory if agent_id == 'athena' else xiaonuo_memory

        result = await memory.semantic_search(
            query=query,
            k=3,
            threshold=0.1
        )

        logger.info(f"\n--- {agent_id.upper()} 查询: {query} ---")
        logger.info(f"找到 {result.get('total_found', 0)} 条结果")

        for i, mem in enumerate(result.get('results', [])[:2], 1):
            content = mem.get('content', '')
            similarity = mem.get('similarity', 0)
            category = mem.get('category', '')
            logger.info(f"{i}. [{similarity:.3f}] [{category}] {content[:60]}...")

    # 关闭记忆系统
    await athena_memory.shutdown()
    await xiaonuo_memory.shutdown()


async def main():
    """主函数"""
    await store_contexts()


if __name__ == '__main__':
    asyncio.run(main())