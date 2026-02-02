#!/usr/bin/env python3
"""
分析2018-2020年专利数据CSV文件结构
"""

import csv
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_csv_structure(year):
    """分析CSV文件结构"""
    file_path = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"

    logger.info(f"\n=== 分析 {year} 年数据 ===")

    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)

            # 字段信息
            logger.info(f"字段数量: {len(reader.fieldnames)}")
            logger.info(f"字段列表: {reader.fieldnames}")

            # 读取前5行数据
            for i, row in enumerate(reader):
                if i >= 5:
                    break

                logger.info(f"\n第 {i+1} 行数据样例:")
                for field in reader.fieldnames[:10]:  # 只显示前10个字段
                    value = row.get(field, '')
                    if value:
                        value = value[:50] + '...' if len(value) > 50 else value
                        logger.info(f"  {field}: {value}")

                if len(reader.fieldnames) > 10:
                    logger.info(f"  ... 还有 {len(reader.fieldnames) - 10} 个字段")

            return reader.fieldnames

    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return None

def main():
    """主函数"""
    logger.info('=' * 80)
    logger.info('分析2018-2020年专利数据CSV文件结构')
    logger.info('=' * 80)

    years = [2018, 2019, 2020]
    structures = {}

    for year in years:
        fields = analyze_csv_structure(year)
        if fields:
            structures[year] = fields

    # 对比结构
    logger.info("\n=== 结构对比 ===")
    if structures:
        first_year = list(structures.keys())[0]
        base_fields = set(structures[first_year])

        for year, fields in structures.items():
            current_fields = set(fields)
            if year == first_year:
                logger.info(f"{year}年: {len(fields)} 个字段")
            else:
                common = base_fields & current_fields
                only_in_current = current_fields - base_fields
                only_in_base = base_fields - current_fields

                logger.info(f"\n与{first_year}年对比:")
                logger.info(f"  {year}年: {len(fields)} 个字段")
                logger.info(f"  共同字段: {len(common)} 个")
                if only_in_current:
                    logger.info(f"  {year}年独有: {only_in_current}")
                if only_in_base:
                    logger.info(f"  {first_year}年独有: {only_in_base}")

if __name__ == '__main__':
    main()