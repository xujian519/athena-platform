#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在大型CSV文件中搜索特定公司的专利数据
Search patents for a specific company in large CSV file
"""

import logging
import os
import sys
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

def search_company_patents(csv_file, company_name, max_results=100):
    """
    在CSV文件中搜索特定公司的专利

    Args:
        csv_file: CSV文件路径
        company_name: 公司名称
        max_results: 最大返回结果数
    """

    logger.info(f"🔍 搜索公司: {company_name}")
    logger.info(f"📁 文件: {csv_file}")
    logger.info(f"⏰ 开始时间: {datetime.now()}")
    print()

    # 读取CSV文件 - 使用chunksize避免内存溢出
    chunk_size = 100000  # 每次处理10万条
    found_patents = []
    total_processed = 0
    chunk_count = 0

    try:
        # 使用迭代器读取大文件
        reader = pd.read_csv(
            csv_file,
            encoding='utf-8',
            chunksize=chunk_size,
            dtype=str,
            low_memory=False
        )

        logger.info('📊 开始逐块处理数据...')

        for chunk in reader:
            chunk_count += 1
            total_processed += len(chunk)

            # 在多个字段中搜索公司名称
            # 检查申请人、当前权利人等字段
            mask = (
                chunk['申请人'].str.contains(company_name, na=False) |
                chunk['当前权利人'].str.contains(company_name, na=False)
            )

            # 找到匹配的记录
            matched = chunk[mask]

            if not matched.empty:
                for _, row in matched.iterrows():
                    patent_info = {
                        '专利名称': row.get('专利名称', ''),
                        '专利类型': row.get('专利类型', ''),
                        '申请人': row.get('申请人', ''),
                        '申请号': row.get('申请号', ''),
                        '申请日': row.get('申请日', ''),
                        '公开公告号': row.get('公开公告号', ''),
                        '公开公告日': row.get('公开公告日', ''),
                        '授权公告号': row.get('授权公告号', ''),
                        '授权公告日': row.get('授权公告日', ''),
                        '发明人': row.get('发明人', ''),
                        '摘要文本': row.get('摘要文本', '')[:100] + '...' if len(str(row.get('摘要文本', ''))) > 100 else row.get('摘要文本', ''),
                        'IPC分类号': row.get('IPC分类号', ''),
                        '引证次数': row.get('引证次数', 0),
                        '被引证次数': row.get('被引证次数', 0)
                    }
                    found_patents.append(patent_info)

                    # 限制结果数量
                    if len(found_patents) >= max_results:
                        logger.info(f"\n⚠️  已达到最大显示数量 {max_results} 条，但可能还有更多")
                        break

            # 显示进度
            if chunk_count % 10 == 0:
                logger.info(f"  已处理: {total_processed:,} 条记录，找到 {len(found_patents)} 条匹配专利")

            # 如果已经找到足够的专利，可以提前退出
            if len(found_patents) >= max_results:
                break

    except Exception as e:
        logger.info(f"❌ 错误: {e}")
        return

    # 显示结果
    logger.info(f"\n✅ 搜索完成！")
    logger.info(f"📊 总共处理: {total_processed:,} 条记录")
    logger.info(f"🔍 找到 {company_name} 的专利: {len(found_patents)} 条")
    print()

    if found_patents:
        logger.info("\n📋 专利列表:")
        logger.info(str('=' * 120))

        for i, patent in enumerate(found_patents, 1):
            logger.info(f"\n【专利 {i}】")
            logger.info(f"  专利名称: {patent['专利名称']}")
            logger.info(f"  专利类型: {patent['专利类型']}")
            logger.info(f"  申请人: {patent['申请人']}")
            logger.info(f"  申请号: {patent['申请号']}")
            logger.info(f"  申请日: {patent['申请日']}")
            logger.info(f"  公开号: {patent['公开公告号']}")
            logger.info(f"  公开日: {patent['公开公告日']}")
            logger.info(f"  授权号: {patent['授权公告号']}")
            logger.info(f"  授权日: {patent['授权公告日']}")
            logger.info(f"  发明人: {patent['发明人']}")
            logger.info(f"  IPC分类号: {patent['IPC分类号']}")
            logger.info(f"  引证次数: {patent['引证次数']}")
            logger.info(f"  被引证次数: {patent['被引证次数']}")
            logger.info(f"  摘要: {patent['摘要文本']}")
            logger.info(str('-' * 120))

        # 统计信息
        patents_by_type = {}
        for patent in found_patents:
            ptype = patent['专利类型']
            patents_by_type[ptype] = patents_by_type.get(ptype, 0) + 1

        logger.info(f"\n📈 专利类型统计:")
        for ptype, count in patents_by_type.items():
            logger.info(f"  {ptype}: {count} 条")

        # 申请年份统计
        years = []
        for patent in found_patents:
            year = patent['申请日'][:4] if len(patent['申请日']) >= 4 else ''
            if year.isdigit():
                years.append(int(year))

        if years:
            logger.info(f"\n📅 申请年份分布:")
            logger.info(f"  最早申请: {min(years)} 年")
            logger.info(f"  最晚申请: {max(years)} 年")
            logger.info(f"  平均年份: {sum(years)/len(years):.0f} 年")

        # 导出结果到文件
        output_file = f'/tmp/{company_name}_patents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv'
        df = pd.DataFrame(found_patents)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"\n💾 结果已保存到: {output_file}")

    else:
        logger.info(f"\n❌ 未找到 {company_name} 的专利记录")

        # 建议相似的公司名称
        logger.info("\n💡 建议:")
        logger.info('  1. 检查公司名称是否准确')
        logger.info('  2. 尝试使用简称或不同名称')
        logger.info('  3. 检查是否可能有其他关联公司名称')

def main():
    """主函数"""
    if len(sys.argv) < 3:
        logger.info('用法: python3 search_company_patents.py <csv_file> <company_name>')
        logger.info("示例: python3 search_company_patents.py /path/to/patents.csv '青岛锁具厂'")
        return

    csv_file = sys.argv[1]
    company_name = sys.argv[2]

    # 检查文件是否存在
    if not os.path.exists(csv_file):
        logger.info(f"❌ 文件不存在: {csv_file}")
        return

    # 执行搜索
    search_company_patents(csv_file, company_name)

if __name__ == '__main__':
    main()