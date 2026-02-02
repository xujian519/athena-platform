#!/usr/bin/env python3
"""
详细检查2016-2017年CSV文件结构
"""

import codecs
import csv
import logging
import sys

logger = logging.getLogger(__name__)

def analyze_csv_structure(year):
    """分析CSV文件结构"""
    file_path = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"

    logger.info(f"\n分析 {year} 年CSV文件: {file_path}")
    logger.info(str('=' * 80))

    try:
        # 尝试不同编码
        encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # 读取前几行
                    lines = []
                    for i, line in enumerate(f):
                        lines.append(line)
                        if i >= 2:  # 只读取前3行
                            break

                    logger.info(f"\n使用编码: {encoding}")
                    logger.info(str('-' * 40))

                    # 分析第一行（标题行）
                    header_line = lines[0]
                    logger.info(f"标题行原始内容: {repr(header_line[:200])}")

                    # 使用csv模块解析
                    f.seek(0)
                    reader = csv.reader(f)
                    headers = next(reader)
                    logger.info(f"\n解析出的字段数量: {len(headers)}")
                    logger.info(f"字段列表:")
                    for i, header in enumerate(headers):
                        logger.info(f"  {i+1:2d}. {repr(header)}")

                    # 分析数据行
                    data_row = next(reader, None)
                    if data_row:
                        logger.info(f"\n第一行数据字段数量: {len(data_row)}")
                        logger.info(f"数据列表:")
                        for i, value in enumerate(data_row):
                            logger.info(f"  {i+1:2d}. {repr(value[:50])}")

                    # 检查是否有空字段
                    logger.info(f"\n字段分析:")
                    for i, header in enumerate(headers):
                        if not header or header.strip() == '':
                            logger.info(f"  警告: 第{i+1}个字段为空")

                    if data_row:
                        for i, value in enumerate(data_row):
                            if i < len(headers) and not headers[i]:
                                logger.info(f"  警告: 第{i+1}个数据字段对应的标题为空")

                    return True

            except UnicodeDecodeError:
                logger.info(f"编码 {encoding} 失败")
                continue
            except Exception as e:
                logger.info(f"使用编码 {encoding} 时出错: {e}")
                continue

        logger.info(f"\n所有编码尝试失败")
        return False

    except Exception as e:
        logger.info(f"分析文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    years = [2016, 2017]

    for year in years:
        analyze_csv_structure(year)
        logger.info(str("\n" + '=' * 80))
        logger.info("\n")

if __name__ == '__main__':
    main()