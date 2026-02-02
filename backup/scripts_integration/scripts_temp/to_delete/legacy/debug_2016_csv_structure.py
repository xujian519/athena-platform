#!/usr/bin/env python3
"""
调试2016年CSV文件结构
"""

import csv
import logging
import sys

logger = logging.getLogger(__name__)

def analyze_csv_structure(file_path):
    """分析CSV文件结构"""
    logger.info(f"分析文件: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            logger.info(f"\nCSV文件列数: {len(header)}")
            logger.info("\n列名列表:")
            for i, col in enumerate(header):
                logger.info(f"  {i+1:2d}. {col}")

            # 读取前5行数据，查看数据格式
            logger.info("\n\n前5行数据示例:")
            f.seek(0)
            next(reader)  # 跳过表头
            for row_idx, row in enumerate(reader, 1):
                if row_idx > 5:
                    break
                logger.info(f"\n第{row_idx}行 (共{len(row)}列):")
                for i, value in enumerate(row[:10]):  # 只显示前10列
                    if i < len(header):
                        logger.info(f"  {header[i]}: {value[:50]}")
                    else:
                        logger.info(f"  列{i+1}: {value[:50]}")

    except Exception as e:
        logger.info(f"错误: {e}")

def main():
    # 分析2016年文件
    file_2016 = '/Volumes/xujian/patent_data/china_patents/中国专利数据库2016年.csv'
    analyze_csv_structure(file_2016)

    logger.info(str("\n" + '='*80 + "\n"))

    # 分析2017年文件
    file_2017 = '/Volumes/xujian/patent_data/china_patents/中国专利数据库2017年.csv'
    analyze_csv_structure(file_2017)

if __name__ == '__main__':
    main()