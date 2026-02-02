#!/usr/bin/env python3
"""
分析2013年专利数据的格式
"""

import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def analyze_format(year):
    """分析指定年份的数据格式"""
    csv_file = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"

    if not Path(csv_file).exists():
        logger.info(f"文件不存在: {csv_file}")
        return

    logger.info(f"\n分析 {year} 年数据格式:")
    logger.info(str('='*60))

    try:
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)

            # 读取标题行
            header = next(reader)
            logger.info(f"总列数: {len(header)}")
            logger.info("\n标题列:")
            for i, col in enumerate(header, 1):
                logger.info(f"  {i:2d}. {col}")

            # 读取前10行数据，统计每行的列数
            logger.info("\n数据行分析 (前10行):")
            line_counts = {}
            for row_num, row in enumerate(reader, start=2):
                if row_num > 11:  # 只分析前10行
                    break
                col_count = len(row)
                line_counts[col_count] = line_counts.get(col_count, 0) + 1
                logger.info(f"  第{row_num:4d}行: {col_count} 列")

                # 如果列数不正常，显示前几个字段
                if col_count < 35:
                    logger.info(f"    前5个字段: {row[:5]}")

            # 统计列数分布
            if line_counts:
                logger.info("\n列数分布:")
                for count, freq in sorted(line_counts.items()):
                    logger.info(f"  {count} 列: {freq} 行")

            # 检查申请号位置（通常在第8列，索引7）
            f.seek(0)
            next(reader)  # 跳过标题

            logger.info("\n申请号字段分析 (前5行):")
            for row_num, row in enumerate(reader, start=2):
                if row_num > 6:
                    break

                logger.info(f"\n第{row_num}行:")
                logger.info(f"  总列数: {len(row)}")

                # 尝试不同的申请号位置
                for pos in [7, 8, 9, 10]:  # 尝试几个可能的申请号位置
                    if pos < len(row):
                        val = row[pos]
                        if val and 'CN' in val:
                            logger.info(f"  位置{pos}(第{pos+1}列): {val}")
                            break

    except Exception as e:
        logger.info(f"分析失败: {str(e)}")

if __name__ == '__main__':
    # 对比2012年和2013年的格式
    analyze_format(2012)
    analyze_format(2013)