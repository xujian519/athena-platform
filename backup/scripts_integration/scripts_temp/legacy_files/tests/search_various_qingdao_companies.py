#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索青岛地区可能相关的企业专利
Search Patents by Various Qingdao Companies
"""

import logging
import sys

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

import json

from database.db_config import get_patent_db_connection


def search_qingdao_companies():
    """搜索青岛地区可能制造紧固件、拉紧器的公司"""
    logger.info('🔍 搜索青岛地区可能相关的企业...')
    logger.info(str('='*60))

    conn = get_patent_db_connection()
    cursor = conn.cursor()

    # 青岛地区可能的公司名称模式
    company_patterns = [
        '青岛%',  # 所有青岛企业
        '青岛%锁具',
        '青岛%制锁',
        '青岛%五金',
        '青岛%紧固',
        '青岛%机械',
        '青岛%器械',
        '青岛%工具',
        '青岛%设备',
        # 可能的具体公司名
        '青岛双友',
        '青岛华天',
        '青岛崂山',
        '青岛机械厂',
        '青岛五金厂'
    ]

    found_companies = set()
    relevant_patents = []

    for pattern in company_patterns:
        cursor.execute("""
            SELECT DISTINCT applicant, COUNT(*) as patent_count
            FROM patents
            WHERE applicant LIKE %s
            GROUP BY applicant
            HAVING COUNT(*) > 0
            ORDER BY patent_count DESC
            LIMIT 10
        """, (pattern,))

        companies = cursor.fetchall()
        if companies:
            logger.info(f"\n🔎 搜索 '{pattern}': 找到 {len(companies)} 个公司")
            for company, count in companies:
                found_companies.add(company)
                logger.info(f"  - {company}: {count} 个专利")

    # 特别搜索"双友"相关（因为目标专利的申请人是"浙江双友"）
    logger.info("\n\n🔍 特别搜索'双友'相关企业...")
    cursor.execute("""
        SELECT patent_name, application_number, publication_number, applicant,
               ipc_main_class, abstract, application_date
        FROM patents
        WHERE applicant LIKE '%双友%'
        ORDER BY application_date DESC
        LIMIT 20
    """)

    shuangyou_patents = cursor.fetchall()
    logger.info(f"找到 {len(shuangyou_patents)} 个双友相关专利")

    for patent in shuangyou_patents:
        patent_info = {
            'patent_name': patent[0],
            'application_number': patent[1],
            'publication_number': patent[2],
            'applicant': patent[3],
            'ipc_main_class': patent[4],
            'abstract': patent[5][:300] + '...' if patent[5] and len(patent[5]) > 300 else (patent[5] or '无摘要'),
            'application_date': str(patent[6]) if patent[6] else '未知'
        }

        # 检查是否与拉紧器相关
        if any(keyword in patent_info['patent_name'].lower() for keyword in ['拉紧', '紧固', '捆绑', '张紧']):
            relevant_patents.append(patent_info)
            logger.info(f"\n✅ 找到双友相关拉紧器专利:")
            logger.info(f"   名称: {patent_info['patent_name']}")
            logger.info(f"   申请人: {patent_info['applicant']}")
            logger.info(f"   申请号: {patent_info['application_number']}")
            logger.info(f"   公开号: {patent_info['publication_number']}")

    # 搜索1990-2010年期间的拉紧器专利（与目标专利同期）
    logger.info("\n\n🔍 搜索1990-2010年期间的拉紧器专利...")
    cursor.execute("""
        SELECT patent_name, application_number, publication_number, applicant,
               ipc_main_class, abstract, application_date
        FROM patents
        WHERE (patent_name LIKE '%拉紧器%' OR patent_name LIKE '%张紧器%' OR patent_name LIKE '%紧固器%')
        AND application_date BETWEEN '1990-01-01' AND '2010-12-31'
        ORDER BY application_date DESC
        LIMIT 20
    """)

    early_patents = cursor.fetchall()
    logger.info(f"找到 {len(early_patents)} 个1990-2010年期间的拉紧器专利")

    for patent in early_patents:
        patent_info = {
            'patent_name': patent[0],
            'application_number': patent[1],
            'publication_number': patent[2],
            'applicant': patent[3],
            'ipc_main_class': patent[4],
            'abstract': patent[5][:300] + '...' if patent[5] and len(patent[5]) > 300 else (patent[5] or '无摘要'),
            'application_date': str(patent[6]) if patent[6] else '未知'
        }

        logger.info(f"\n📄 {patent_info['patent_name']}")
        logger.info(f"   申请人: {patent_info['applicant']}")
        logger.info(f"   申请号: {patent_info['application_number']}")
        logger.info(f"   公开号: {patent_info['publication_number']}")
        logger.info(f"   申请日: {patent_info['application_date']}")

        # 检查申请人是否包含"青岛"
        if '青岛' in patent_info['applicant']:
            logger.info('   ⭐ 这是青岛企业！')
            relevant_patents.append(patent_info)

    conn.close()

    # 保存结果
    output_file = 'qingdao_companies_patents.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'found_companies': list(found_companies),
            'shuangyou_patents': [dict(zip(['patent_name', 'application_number', 'publication_number', 'applicant', 'ipc_main_class', 'abstract', 'application_date'], p)) for p in shuangyou_patents],
            'early_patents': [dict(zip(['patent_name', 'application_number', 'publication_number', 'applicant', 'ipc_main_class', 'abstract', 'application_date'], p)) for p in early_patents],
            'relevant_patents': relevant_patents
        }, f, ensure_ascii=False, indent=2)

    logger.info(f"\n✅ 搜索结果已保存到 {output_file}")
    logger.info(f"📊 找到青岛相关企业: {len(found_companies)} 家")
    logger.info(f"📊 双友相关专利: {len(shuangyou_patents)} 个")
    logger.info(f"📊 早期拉紧器专利: {len(early_patents)} 个")
    logger.info(f"📊 青岛企业拉紧器专利: {len([p for p in relevant_patents if '青岛' in p['applicant']])} 个")

    return relevant_patents

def main():
    """主函数"""
    logger.info('🚀 青岛地区企业专利搜索')
    logger.info(str('='*60))
    logger.info('目标：查找青岛锁具厂或相关企业的拉紧器专利')
    logger.info(str('='*60))

    relevant_patents = search_qingdao_companies()

    if relevant_patents:
        logger.info("\n\n✅ 找到相关专利！")
        logger.info('最相关的专利：')
        for i, patent in enumerate(relevant_patents[:5], 1):
            logger.info(f"\n{i}. {patent['patent_name']}")
            logger.info(f"   申请人：{patent['applicant']}")
            logger.info(f"   申请号：{patent['application_number']}")
    else:
        logger.info("\n\n⚠️ 未能找到青岛锁具厂的拉紧器专利")
        logger.info("\n💡 可能的原因：")
        logger.info('1. 企业名称可能有变（如改制、更名）')
        logger.info('2. 可能以其他名称申请专利')
        logger.info('3. 数据库中可能没有收录该专利')
        logger.info('4. 时间范围可能需要调整')

if __name__ == '__main__':
    main()