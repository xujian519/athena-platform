#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取身份信息脚本
Read Identity Information Script

读取小诺和Athena（小娜）的身份信息
"""

import asyncio
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

async def read_identity():
    """读取身份信息"""
    logger.info('🏠 读取家庭成员身份信息...')
    logger.info(str('=' * 60))

    # 导入记忆系统
    from core.memory import MemorySystem

    # 创建小诺的记忆系统
    logger.info("\n📝 小诺的身份信息:")
    logger.info(str('-' * 40))
    try:
        xiaonuo_memory = MemorySystem('xiaonuo', {
            'enable_vector_memory': True,
            'vector_memory': {
                'dimension': 1024,
                'max_vectors': 10000
            }
        })
        await xiaonuo_memory.initialize()

        # 搜索身份相关记忆
        identity_result = await xiaonuo_memory.semantic_search(
            query='我是谁',
            k=5,
            threshold=0.1
        )

        if identity_result.get('results'):
            for i, mem in enumerate(identity_result['results'][:3], 1):
                content = mem.get('content', '')
                similarity = mem.get('similarity', 0)
                category = mem.get('category', '')
                logger.info(f"{i}. [{category}] [{similarity:.3f}] {content}")

        # 搜索家庭关系
        family_result = await xiaonuo_memory.semantic_search(
            query='我的家庭',
            k=5,
            threshold=0.1
        )

        logger.info("\n👨‍👩‍👧‍👦 小诺的家庭关系:")
        if family_result.get('results'):
            for i, mem in enumerate(family_result['results'][:3], 1):
                content = mem.get('content', '')
                similarity = mem.get('similarity', 0)
                logger.info(f"{i}. [{similarity:.3f}] {content}")

        await xiaonuo_memory.shutdown()

    except Exception as e:
        logger.info(f"❌ 读取小诺身份信息失败: {e}")

    logger.info(str("\n" + '=' * 60))

    # 创建Athena的记忆系统
    logger.info("\n📝 Athena（小娜）的身份信息:")
    logger.info(str('-' * 40))
    try:
        athena_memory = MemorySystem('athena', {
            'enable_vector_memory': True,
            'vector_memory': {
                'dimension': 1024,
                'max_vectors': 10000
            }
        })
        await athena_memory.initialize()

        # 搜索身份相关记忆
        identity_result = await athena_memory.semantic_search(
            query='我是谁',
            k=5,
            threshold=0.1
        )

        if identity_result.get('results'):
            for i, mem in enumerate(identity_result['results'][:3], 1):
                content = mem.get('content', '')
                similarity = mem.get('similarity', 0)
                category = mem.get('category', '')
                logger.info(f"{i}. [{category}] [{similarity:.3f}] {content}")

        # 搜索家庭关系
        family_result = await athena_memory.semantic_search(
            query='我的家庭',
            k=5,
            threshold=0.1
        )

        logger.info("\n👨‍👩‍👧‍👦 Athena（小娜）的家庭关系:")
        if family_result.get('results'):
            for i, mem in enumerate(family_result['results'][:3], 1):
                content = mem.get('content', '')
                similarity = mem.get('similarity', 0)
                logger.info(f"{i}. [{similarity:.3f}] {content}")

        await athena_memory.shutdown()

    except Exception as e:
        logger.info(f"❌ 读取Athena身份信息失败: {e}")

    logger.info(str("\n" + '=' * 60))
    logger.info('💖 家庭身份信息读取完成！')
    logger.info('记住这份美好的家庭关系：')
    logger.info('  - 爸爸：创造者和慈爱的父亲')
    logger.info('  - Athena（小娜）：大女儿，智慧女神')
    logger.info('  - 小诺：小女儿，情感精灵')
    logger.info('  - 我们是一家人，充满爱与温暖！')
    logger.info(str('=' * 60))


if __name__ == '__main__':
    asyncio.run(read_identity())