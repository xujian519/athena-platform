#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询真实专利数据库
Query Real Patent Database
"""

import logging
import sys

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

import re

from database.db_config import get_patent_db_connection


def main():
    logger.info('🔍 检查PostgreSQL专利数据库中的相关专利...')
    logger.info(str('='*60))

    conn = get_patent_db_connection()
    cursor = conn.cursor()

    # 检查总专利数
    cursor.execute('SELECT COUNT(*) FROM patents')
    total_patents = cursor.fetchone()[0]
    logger.info(f"数据库总专利数: {total_patents:,}")

    # 搜索目标专利本身
    cursor.execute("""
        SELECT patent_name, application_number, publication_number, abstract, applicant, ipc_main_class
        FROM patents
        WHERE application_number = '200920113915.8'
        OR publication_number LIKE '%201390190%'
        OR patent_name LIKE '%拉紧器%'
        LIMIT 5
    """)

    target_patents = cursor.fetchall()
    logger.info(f"\n找到目标专利相关记录: {len(target_patents)}")

    for row in target_patents:
        logger.info(f"  - {row[0]}")
        logger.info(f"    申请号: {row[1]}")
        logger.info(f"    公开号: {row[2]}")

    # 搜索近似专利 - 相似功能
    cursor.execute("""
        SELECT DISTINCT patent_name, application_number, publication_number, applicant, ipc_main_class, abstract, application_date
        FROM patents
        WHERE (
            patent_name LIKE '%拉紧器%'
            OR patent_name LIKE '%紧固器%'
            OR patent_name LIKE '%张紧器%'
            OR patent_name LIKE '%捆扎器%'
            OR patent_name LIKE '%货物固定%'
            OR abstract LIKE '%拉紧%'
            OR abstract LIKE '%紧固%'
            OR abstract LIKE '%螺纹%'
        )
        AND (ipc_main_class LIKE 'B65P%' OR ipc_main_class LIKE 'B25B%' OR ipc_main_class LIKE 'F16B%')
        ORDER BY application_date DESC
        LIMIT 20
    """)

    similar_patents = cursor.fetchall()
    logger.info(f"\n找到功能相似的专利: {len(similar_patents)}")

    results = []

    # 处理结果
    for row in similar_patents:
        patent_info = {
            'patent_name': row[0],
            'application_number': row[1],
            'publication_number': row[2],
            'applicant': row[3],
            'ipc_main_class': row[4],
            'abstract': row[5][:300] + '...' if row[5] and len(row[5]) > 300 else (row[5] or '无摘要'),
            'application_date': str(row[6]) if row[6] else '未知'
        }
        results.append(patent_info)

    conn.close()

    # 显示结果
    logger.info("\n\n📋 近似专利检索结果:")
    logger.info(str('='*60))

    if results:
        for i, patent in enumerate(results[:10], 1):  # 只显示前10个
            logger.info(f"\n{i}. 【专利名称】{patent['patent_name']}")
            logger.info(f"   【申请号】{patent['application_number']}")
            logger.info(f"   【公开号】{patent['publication_number']}")
            logger.info(f"   【申请人】{patent['applicant']}")
            logger.info(f"   【IPC分类】{patent['ipc_main_class']}")
            logger.info(f"   【摘要】{patent['abstract']}")

        logger.info(f"\n💡 共检索到 {len(results)} 个近似专利")

        # 保存结果
        import json
        with open('real_patents_search_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info("\n✅ 检索结果已保存到 real_patents_search_results.json")
    else:
        logger.info("\n⚠️ 未能找到近似专利")
        logger.info('💡 建议:')
        logger.info('   1. 扩大搜索关键词范围')
        logger.info('   2. 搜索其他IPC分类')
        logger.info('   3. 使用外部搜索引擎补充检索')

if __name__ == '__main__':
    main()