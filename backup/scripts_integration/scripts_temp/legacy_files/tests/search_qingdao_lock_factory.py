#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检索青岛锁具厂的专利
Search Patents by Applicant: Qingdao Lock Factory
"""

import logging
import sys

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

import json

from database.db_config import get_patent_db_connection


def search_by_applicant():
    """根据申请人名称检索专利"""
    logger.info("🔍 检索申请人'青岛锁具厂'的专利...")
    logger.info(str('='*60))

    conn = get_patent_db_connection()
    cursor = conn.cursor()

    # 搜索青岛锁具厂的专利
    search_patterns = [
        '青岛锁具厂',
        '青岛制锁厂',
        '青岛锁厂',
        '青岛市锁具厂'
    ]

    all_patents = []

    for pattern in search_patterns:
        logger.info(f"\n🔎 搜索模式: {pattern}")

        cursor.execute("""
            SELECT patent_name, application_number, publication_number, applicant,
                   ipc_main_class, abstract, application_date, publication_date
            FROM patents
            WHERE applicant LIKE %s
            ORDER BY application_date DESC
            LIMIT 20
        """, (f"%{pattern}%",))

        patents = cursor.fetchall()
        logger.info(f"  找到 {len(patents)} 条记录")

        for row in patents:
            patent_info = {
                'patent_name': row[0],
                'application_number': row[1],
                'publication_number': row[2],
                'applicant': row[3],
                'ipc_main_class': row[4],
                'abstract': row[5][:300] + '...' if row[5] and len(row[5]) > 300 else (row[5] or '无摘要'),
                'application_date': str(row[6]) if row[6] else '未知',
                'publication_date': str(row[7]) if row[7] else '未知'
            }

            # 检查是否已存在
            if patent_info not in all_patents:
                all_patents.append(patent_info)
                logger.info(f"    ✓ {patent_info['patent_name'][:40]}...")

    conn.close()

    # 查找与拉紧器相关的专利
    logger.info("\n\n📋 筛选与'拉紧器'相关的专利：")
    logger.info(str('='*60))

    relevant_patents = []
    for patent in all_patents:
        patent_name = patent.get('patent_name', '').lower()
        abstract = patent.get('abstract', '').lower()

        # 检查是否包含相关关键词
        keywords = ['拉紧', '紧固', '捆绑', '锁紧', '张紧', '固定']
        if any(keyword in patent_name or keyword in abstract for keyword in keywords):
            relevant_patents.append(patent)
            logger.info(f"\n✅ 相关专利:")
            logger.info(f"   名称: {patent['patent_name']}")
            logger.info(f"   申请号: {patent['application_number']}")
            logger.info(f"   公开号: {patent['publication_number']}")
            logger.info(f"   IPC分类: {patent['ipc_main_class']}")
            logger.info(f"   申请日: {patent['application_date']}")
            logger.info(f"   摘要: {patent['abstract'][:150]}...")

    # 保存结果
    output_file = 'qingdao_lock_factory_patents.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'all_patents': all_patents,
            'relevant_patents': relevant_patents
        }, f, ensure_ascii=False, indent=2)

    logger.info(f"\n✅ 检索结果已保存到 {output_file}")
    logger.info(f"📊 总计找到 {len(all_patents)} 个专利")
    logger.info(f"📊 其中相关专利 {len(relevant_patents)} 个")

    return all_patents, relevant_patents

def search_similar_locking_devices():
    """搜索类似的锁定装置专利"""
    logger.info("\n\n🔍 搜索类似锁定装置的专利（可能与目标专利相关）...")
    logger.info(str('='*60))

    conn = get_patent_db_connection()
    cursor = conn.cursor()

    # 扩大搜索范围，查找可能的相似专利
    cursor.execute("""
        SELECT patent_name, application_number, publication_number, applicant,
               ipc_main_class, abstract, application_date
        FROM patents
        WHERE (
            (applicant LIKE '%青岛%' AND (patent_name LIKE '%紧固%' OR patent_name LIKE '%锁%' OR patent_name LIKE '%夹%'))
            OR (patent_name LIKE '%双钩%' OR patent_name LIKE '%拉紧%')
            OR (ipc_main_class LIKE 'E05B%' OR ipc_main_class LIKE 'F16B%' OR ipc_main_class LIKE 'B65B%')
            AND (patent_name LIKE '%装置%' OR patent_name LIKE '%器%')
        )
        AND application_date BETWEEN '2000-01-01' AND '2012-12-31'
        ORDER BY application_date DESC
        LIMIT 30
    """)

    patents = cursor.fetchall()
    logger.info(f"找到 {len(patents)} 条可能相关的记录")

    similar_devices = []
    for row in patents:
        patent_info = {
            'patent_name': row[0],
            'application_number': row[1],
            'publication_number': row[2],
            'applicant': row[3],
            'ipc_main_class': row[4],
            'abstract': row[5][:300] + '...' if row[5] and len(row[5]) > 300 else (row[5] or '无摘要'),
            'application_date': str(row[6]) if row[6] else '未知'
        }

        # 评估相关性
        relevance_score = 0
        name = patent_info['patent_name'].lower()
        abstract = patent_info['abstract'].lower()

        if '青岛' in patent_info['applicant']:
            relevance_score += 20
        if any(word in name for word in ['拉紧', '紧固', '夹紧', '锁定']):
            relevance_score += 30
        if any(word in abstract for word in ['螺纹', '旋转', '手柄', '调节']):
            relevance_score += 25
        if '2009' in patent_info['application_date'] or '2010' in patent_info['application_date']:
            relevance_score += 15

        patent_info['relevance_score'] = relevance_score
        similar_devices.append(patent_info)

    # 按相关性排序
    similar_devices.sort(key=lambda x: x['relevance_score'], reverse=True)

    # 显示最相关的专利
    logger.info("\n最相关的专利（按相关性排序）：")
    for i, patent in enumerate(similar_devices[:10], 1):
        logger.info(f"\n{i}. 【专利名称】{patent['patent_name']}")
        logger.info(f"   【申请人】{patent['applicant']}")
        logger.info(f"   【申请号】{patent['application_number']}")
        logger.info(f"   【公开号】{patent['publication_number']}")
        logger.info(f"   【相关性评分】{patent['relevance_score']}/100")
        logger.info(f"   【申请日】{patent['application_date']}")
        if patent['relevance_score'] > 30:
            logger.info(f"   【摘要】{patent['abstract'][:150]}...")

    conn.close()

    # 保存结果
    output_file = 'similar_locking_devices.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(similar_devices[:20], f, ensure_ascii=False, indent=2)

    logger.info(f"\n✅ 类似锁定装置专利已保存到 {output_file}")

    return similar_devices

def main():
    """主函数"""
    logger.info('🚀 青岛锁具厂专利检索系统')
    logger.info(str('='*60))

    # 1. 搜索青岛锁具厂的专利
    all_patents, relevant_patents = search_by_applicant()

    # 2. 搜索类似的锁定装置
    similar_devices = search_similar_locking_devices()

    # 3. 总结
    logger.info("\n\n📊 检索总结：")
    logger.info(str('='*60))
    logger.info(f"1. 青岛锁具厂相关专利：{len(all_patents)} 个")
    logger.info(f"2. 与拉紧器相关的专利：{len(relevant_patents)} 个")
    logger.info(f"3. 类似锁定装置专利：{len(similar_devices)} 个")

    if relevant_patents:
        logger.info("\n✅ 找到与拉紧器相关的青岛锁具厂专利！")
    else:
        logger.info("\n⚠️ 未能找到青岛锁具厂的拉紧器相关专利")
        logger.info('💡 建议：')
        logger.info("   - 尝试其他申请人名称变体（如'青岛制锁总厂'等）")
        logger.info('   - 扩大搜索时间范围')
        logger.info('   - 检查是否有名称变更或企业改制')

if __name__ == '__main__':
    main()