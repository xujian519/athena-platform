#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新查询专利数据库，获取包含公开号的专利信息
Query Patent Database with Publication Numbers
"""

import logging
import sys

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

import json
import time

from database.db_config import get_patent_db_connection


def get_patents_with_publication_numbers():
    """获取包含公开号的专利信息"""
    logger.info('🔍 重新检索包含公开号的专利...')
    logger.info(str('='*60))

    conn = get_patent_db_connection()
    cursor = conn.cursor()

    # 搜索目标专利本身，确保获取公开号
    cursor.execute("""
        SELECT patent_name, application_number, publication_number, abstract, applicant, ipc_main_class, application_date
        FROM patents
        WHERE application_number = '200920113915.8'
        OR publication_number LIKE '%201390190%'
        LIMIT 5
    """)

    target_patents = cursor.fetchall()
    logger.info(f"找到目标专利相关记录: {len(target_patents)}")

    for row in target_patents:
        logger.info(f"  - {row[0]}")
        logger.info(f"    申请号: {row[1]}")
        logger.info(f"    公开号: {row[2]}")
        logger.info(f"    申请日: {row[6]}")

    # 搜索功能相似且包含公开号的专利
    cursor.execute("""
        SELECT DISTINCT patent_name, application_number, publication_number, applicant, ipc_main_class, abstract, application_date
        FROM patents
        WHERE (
            (patent_name LIKE '%拉紧器%' AND publication_number IS NOT NULL) OR
            (patent_name LIKE '%张紧器%' AND publication_number IS NOT NULL) OR
            (patent_name LIKE '%紧固器%' AND publication_number IS NOT NULL) OR
            (patent_name LIKE '%捆扎器%' AND publication_number IS NOT NULL) OR
            (ipc_main_class = 'B65P 7/06' AND publication_number IS NOT NULL) OR
            (ipc_main_class = 'B25B 5/02' AND publication_number IS NOT NULL)
        )
        AND publication_number IS NOT NULL
        AND LENGTH(publication_number) > 5
        ORDER BY application_date DESC
        LIMIT 30
    """)

    similar_patents = cursor.fetchall()
    logger.info(f"\n找到有公开号的相似专利: {len(similar_patents)}")

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
    logger.info("\n\n📋 包含公开号的专利检索结果:")
    logger.info(str('='*60))

    if results:
        # 按相关性排序（目标专利优先，然后按IPC分类相似度）
        def relevance_score(patent):
            score = 0
            # 目标专利最高分
            if '拉紧器' in patent['patent_name']:
                score += 50
            if patent['application_number'] == '200920113915.8':
                score += 1000
            # IPC分类匹配
            if patent['ipc_main_class'] == 'B65P 7/06':
                score += 20
            elif patent['ipc_main_class'] and 'B65P' in patent['ipc_main_class']:
                score += 10
            # 关键词匹配
            keywords = ['螺纹', '手柄', '挂钩', '调节', '旋转']
            for kw in keywords:
                if kw in patent.get('patent_name', '') + patent.get('abstract', ''):
                    score += 5
            return score

        results.sort(key=relevance_score, reverse=True)
        results = results[:20]  # 取前20个

        for i, patent in enumerate(results[:10], 1):  # 显示前10个
            logger.info(f"\n{i}. 【专利名称】{patent['patent_name']}")
            logger.info(f"   【申请号】{patent['application_number']}")
            logger.info(f"   【公开号】{patent['publication_number']}")
            logger.info(f"   【申请人】{patent['applicant']}")
            logger.info(f"   【IPC分类】{patent['ipc_main_class']}")
            logger.info(f"   【申请日】{patent['application_date']}")
            logger.info(f"   【摘要】{patent['abstract'][:100]}...")

        logger.info(f"\n💡 共检索到 {len(results)} 个包含公开号的近似专利")

        # 保存结果
        with open('similar_patents_with_pub_numbers.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info("\n✅ 检索结果已保存到 similar_patents_with_pub_numbers.json")

        return results
    else:
        logger.info("\n⚠️ 未找到包含公开号的专利")
        return []

def create_patent_search_list():
    """创建用于Google Patents搜索的专利号列表"""
    patents = get_patents_with_publication_numbers()

    logger.info("\n📋 Google Patents搜索列表:")
    logger.info(str('='*60))

    # 准备搜索用的专利号
    search_list = []

    for patent in patents:
        # 确保公开号格式正确
        pub_num = patent.get('publication_number', '')
        if pub_num and len(pub_num) > 5:
            # 标准化格式：CN201390190Y
            if not pub_num.startswith('CN'):
                pub_num = f"CN{pub_num}"
            search_list.append({
                'publication_number': pub_num,
                'patent_name': patent.get('patent_name', ''),
                'application_number': patent.get('application_number', '')
            })

    # 显示搜索列表
    for i, item in enumerate(search_list[:10], 1):
        logger.info(f"{i}. {item['publication_number']} - {item['patent_name'][:30]}...")

    # 保存搜索列表
    with open('google_patents_search_list.json', 'w', encoding='utf-8') as f:
        json.dump(search_list, f, ensure_ascii=False, indent=2)

    logger.info(f"\n✅ 搜索列表已保存到 google_patents_search_list.json")
    logger.info(f"💡 共准备 {len(search_list)} 个专利号用于Google Patents搜索")

    return search_list

def main():
    """主函数"""
    search_list = create_patent_search_list()

    logger.info("\n🔗 下一步操作建议:")
    logger.info('1. 使用这些专利号通过Google Patents API或网页抓取获取全文')
    logger.info('2. 对获取到的专利全文进行深入分析')
    logger.info('3. 对比目标专利与现有技术的差异')

if __name__ == '__main__':
    main()