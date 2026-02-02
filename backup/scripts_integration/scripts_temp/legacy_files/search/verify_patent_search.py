#!/usr/bin/env python3
"""
验证专利数据检索功能
"""

import json
import logging
import sys
from datetime import datetime

import psycopg2
import requests

logger = logging.getLogger(__name__)

# API配置
API_BASE_URL = 'http://localhost:8030'

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'patent_db',
    'user': 'postgres',
    'password': 'postgres'
}

def test_api_search(year, query='人工智能', limit=5):
    """测试API搜索功能"""
    logger.info(f"\n=== 测试 {year} 年数据检索 ===")

    # 查询简化表
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 统计该年份的数据量
        cursor.execute(
            'SELECT COUNT(*) FROM patents_simple WHERE source_year = %s',
            (year,)
        )
        count = cursor.fetchone()[0]
        logger.info(f"✓ 数据库中 {year} 年有 {count:,} 条记录")

        # 获取一些样例数据
        cursor.execute(
            'SELECT patent_name, applicant, abstract FROM patents_simple '
            'WHERE source_year = %s AND patent_name IS NOT NULL LIMIT 3',
            (year,)
        )
        samples = cursor.fetchall()

        if samples:
            logger.info(f"✓ 样例数据:")
            for i, (name, applicant, abstract) in enumerate(samples, 1):
                logger.info(f"  {i}. 专利名称: {name[:50]}...")
                logger.info(f"     申请人: {applicant}")
                if abstract:
                    logger.info(f"     摘要: {abstract[:100]}...")
        else:
            logger.info(f"⚠️  没有找到 {year} 年的数据")
            return False

        cursor.close()
        conn.close()
    except Exception as e:
        logger.info(f"✗ 数据库连接失败: {str(e)}")
        return False

    # 测试API搜索
    try:
        # 测试搜索接口
        search_url = f"{API_BASE_URL}/api/v1/search"
        params = {
            'query': query,
            'year': year,
            'limit': limit
        }

        response = requests.get(search_url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            total = data.get('total', 0)

            logger.info(f"\n✓ API搜索 '{query}' ({year}年):")
            logger.info(f"  总命中: {total:,} 条")
            logger.info(f"  返回 {len(results)} 条结果")

            if results:
                logger.info("\n  前3条结果:")
                for i, patent in enumerate(results[:3], 1):
                    logger.info(f"    {i}. {patent.get('patent_name', 'N/A')}")
                    logger.info(f"       申请人: {patent.get('applicant', 'N/A')}")
                    logger.info(f"       申请号: {patent.get('application_number', 'N/A')}")
        else:
            logger.info(f"✗ API搜索失败 (状态码: {response.status_code})")
            logger.info(f"  响应: {response.text[:200]}")
            return False

    except Exception as e:
        logger.info(f"✗ API请求失败: {str(e)}")
        return False

    return True

def main():
    """主函数"""
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1:]]
    else:
        # 默认验证已导入的年份
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT DISTINCT source_year FROM patents_simple ORDER BY source_year'
            )
            years = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
        except:
            logger.info('无法获取已导入的年份列表')
            return

    logger.info(f"验证年份: {years}")
    logger.info(str('='*60))

    success_years = []
    failed_years = []

    for year in years:
        if test_api_search(year):
            success_years.append(year)
        else:
            failed_years.append(year)

    # 总结
    logger.info(str("\n" + '='*60))
    logger.info('验证结果总结:')
    logger.info(f"✓ 成功年份: {success_years}")
    if failed_years:
        logger.info(f"✗ 失败年份: {failed_years}")

    if len(success_years) == len(years):
        logger.info("\n🎉 所有年份验证通过！")
    else:
        logger.info(f"\n⚠️  {len(failed_years)} 个年份验证失败")

if __name__ == '__main__':
    main()