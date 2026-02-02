#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索专利 CN2278112Y
"""

import logging
import sys

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

from database.db_config import get_patent_db_connection


def search_patent_CN2278112Y():
    """搜索专利 CN2278112Y"""
    logger.info('🔍 搜索专利 CN2278112Y')
    logger.info(str('='*60))

    conn = get_patent_db_connection()
    cursor = conn.cursor()

    # 1. 按公开号搜索
    logger.info("\n1. 按公开号搜索:")
    cursor.execute("""
        SELECT patent_name, application_number, publication_number, authorization_number,
               applicant, ipc_main_class, patent_type, source_year, abstract
        FROM patents
        WHERE publication_number = 'CN2278112Y'
    """)
    results = cursor.fetchall()
    logger.info(f"   找到 {len(results)} 条记录")

    if results:
        for row in results:
            logger.info(f"   - 专利名称: {row[0]}")
            logger.info(f"     申请号: {row[1]}")
            logger.info(f"     公开号: {row[2]}")
            logger.info(f"     授权公告号: {row[3]}")
            logger.info(f"     申请人: {row[4]}")
            logger.info(f"     IPC分类: {row[5]}")
            logger.info(f"     专利类型: {row[6]}")
            logger.info(f"     年份: {row[7]}")
            logger.info(f"     摘要: {row[8][:100] if row[8] else '无'}...")

    # 2. 模糊搜索
    logger.info("\n2. 模糊搜索 (包含 2278112):")
    cursor.execute("""
        SELECT patent_name, application_number, publication_number, authorization_number,
               applicant, ipc_main_class, patent_type, source_year
        FROM patents
        WHERE publication_number LIKE '%2278112%'
        OR authorization_number LIKE '%2278112%'
    """)
    results = cursor.fetchall()
    logger.info(f"   找到 {len(results)} 条记录")

    for row in results:
        logger.info(f"   - {row[0]} ({row[2]})")

    # 3. 按申请人搜索
    logger.info("\n3. 按申请人 '青岛索具厂' 搜索:")
    cursor.execute("""
        SELECT patent_name, application_number, publication_number, authorization_number,
               ipc_main_class, patent_type, source_year
        FROM patents
        WHERE applicant LIKE '%青岛索具厂%'
        ORDER BY source_year
    """)
    results = cursor.fetchall()
    logger.info(f"   找到 {len(results)} 条记录")

    for row in results:
        logger.info(f"   - {row[0]}")
        logger.info(f"     公开号: {row[2]}")
        logger.info(f"     年份: {row[6]}")
        logger.info(f"     IPC: {row[4]}")

    # 4. 按IPC分类号搜索
    logger.info("\n4. 按 IPC 分类号 'F16G11/00' 搜索:")
    cursor.execute("""
        SELECT patent_name, application_number, publication_number, applicant,
               patent_type, source_year
        FROM patents
        WHERE ipc_main_class = 'F16G11/00'
        OR ipc_main_class LIKE 'F16G11/%'
        ORDER BY source_year DESC
        LIMIT 20
    """)
    results = cursor.fetchall()
    logger.info(f"   找到 {len(results)} 条记录 (最近20条)")

    for row in results:
        logger.info(f"   - {row[0]} ({row[5]})")
        logger.info(f"     公开号: {row[2]}")
        logger.info(f"     申请人: {row[3]}")

    # 5. 搜索1998年的相关专利
    logger.info("\n5. 搜索1998年包含'索具'的专利:")
    cursor.execute("""
        SELECT patent_name, application_number, publication_number, applicant,
               ipc_main_class, patent_type
        FROM patents
        WHERE source_year = 1998
        AND (patent_name LIKE '%索具%' OR applicant LIKE '%索具%')
    """)
    results = cursor.fetchall()
    logger.info(f"   找到 {len(results)} 条记录")

    for row in results:
        logger.info(f"   - {row[0]}")
        logger.info(f"     公开号: {row[2]}")
        logger.info(f"     申请人: {row[3]}")
        logger.info(f"     IPC: {row[4]}")

    conn.close()

if __name__ == '__main__':
    search_patent_CN2278112Y()