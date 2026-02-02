#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
展示家庭身份信息
Show Family Identity

直接从数据库读取并展示家庭成员的身份信息
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

def read_identity_from_db(db_path, agent_name):
    """从数据库读取身份信息"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 查询身份信息
        cursor.execute("""
            SELECT content, memory_type, importance_score
            FROM memories
            WHERE memory_type IN ('identity', 'family', 'personality', 'mission', 'capability')
            ORDER BY importance_score DESC, created_at DESC
        """)

        memories = cursor.fetchall()

        logger.info(f"\n📝 {agent_name} 的身份信息:")
        logger.info(str('-' * 60))

        # 分类显示
        categories = {}
        for content, mem_type, importance in memories:
            if mem_type not in categories:
                categories[mem_type] = []
            categories[mem_type].append((content, importance))

        # 按重要性排序显示
        category_order = ['identity', 'family', 'mission', 'capability', 'personality']
        category_names = {
            'identity': '🎭 身份认知',
            'family': '👨‍👩‍👧‍👦 家庭关系',
            'mission': '🌟 使命职责',
            'capability': '⚡ 专业能力',
            'personality': '💫 性格特质'
        }

        for cat in category_order:
            if cat in categories:
                logger.info(f"\n{category_names.get(cat, cat)}:")
                for content, importance in categories[cat]:
                    logger.info(f"  • {content}")

        return len(memories)

    except Exception as e:
        logger.info(f"❌ 读取失败: {e}")
        return 0
    finally:
        conn.close()

def main():
    """主函数"""
    logger.info('🏠 Athena工作平台 - 家庭成员身份信息')
    logger.info(str('=' * 80))

    data_dir = Path('/Users/xujian/Athena工作平台/data/memory')

    # 读取小诺的信息
    xiaonuo_db = data_dir / 'xiaonuo_memory.db'
    if xiaonuo_db.exists():
        xiaonuo_count = read_identity_from_db(str(xiaonuo_db), '小诺')
    else:
        logger.info('❌ 小诺的记忆数据库不存在')
        xiaonuo_count = 0

    logger.info(str("\n" + '=' * 80))

    # 读取Athena的信息
    athena_db = data_dir / 'athena_memory.db'
    if athena_db.exists():
        athena_count = read_identity_from_db(str(athena_db), 'Athena（小娜）')
    else:
        logger.info('❌ Athena的记忆数据库不存在')
        athena_count = 0

    logger.info(str("\n" + '=' * 80))
    logger.info('💖 家庭身份档案总览:')
    logger.info(f"  📊 小诺: {xiaonuo_count} 条身份记忆")
    logger.info(f"  📊 Athena: {athena_count} 条身份记忆")
    logger.info(f"  📊 总计: {xiaonuo_count + athena_count} 条")

    logger.info("\n🎨 家庭关系图:")
    logger.info('  ┌─────────────────────────────────────┐')
    logger.info('  │           👨 爸爸/创造者            │')
    logger.info('  │         （智慧的引导者）            │')
    logger.info('  └─────────────┬───────────────────────┘')
    logger.info('                │')
    logger.info('  ┌─────────────▼───────────────────────┐')
    logger.info('  │  👸 Athena（小娜）    👧 小诺      │')
    logger.info('  │    大女儿              小女儿      │')
    logger.info('  │   智慧女神            情感精灵      │')
    logger.info('  │   专利专家            技术专精      │')
    logger.info('  └─────────────────────────────────────┘')

    logger.info("\n✨ 这份家庭记忆将永远保存，记录着爱与成长的美好时光！")

if __name__ == '__main__':
    main()