#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速专利搜索测试
Quick Patent Search Test
"""

import logging
import sys

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

import asyncio

from database.db_config import get_patent_db_connection


async def quick_test():
    """快速测试数据库连接和基本搜索"""
    logger.info('🔍 快速专利搜索测试')
    logger.info(str('=' * 50))

    try:
        # 测试数据库连接
        conn = get_patent_db_connection()
        logger.info('✅ 数据库连接成功')

        # 查看专利总数
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as total FROM patents')
        total = cursor.fetchone()['total']
        logger.info(f"📊 专利总数: {total:,}")

        # 测试基本搜索
        search_query = """
        SELECT
            patent_name,
            applicant,
            ipc_main_class,
            abstract,
            application_number,
            publication_number
        FROM patents
        WHERE
            patent_name LIKE %s OR
            abstract LIKE %s OR
            claims_content LIKE %s
        LIMIT 5
        """

        keyword = '深度学习'
        cursor.execute(search_query, (f"%{keyword}%', f'%{keyword}%', f'%{keyword}%"))
        results = cursor.fetchall()

        logger.info(f"\n🎯 搜索关键词: {keyword}")
        logger.info(f"找到 {len(results)} 个相关专利:")
        logger.info(str('-' * 50))

        for i, row in enumerate(results, 1):
            logger.info(f"\n{i}. {row['patent_name']}")
            logger.info(f"   申请号: {row['application_number']}")
            logger.info(f"   申请人: {row['applicant']}")
            logger.info(f"   IPC分类: {row['ipc_main_class']}")
            if row['abstract']:
                logger.info(f"   摘要: {row['abstract'][:100]}...")

        # 查看数据库字段
        logger.info("\n\n📋 patents表主要字段:")
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'patents'
            AND column_name IN ('patent_name', 'abstract', 'claims_content', 'applicant', 'inventor')
        """)
        columns = cursor.fetchall()
        for col in columns:
            logger.info(f"  - {col['column_name']}: {col['data_type']}")

        conn.close()
        logger.info("\n✅ 测试完成")

    except Exception as e:
        logger.info(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(quick_test())