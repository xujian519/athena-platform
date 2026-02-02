#!/usr/bin/env python3
"""
专利数据年度处理器
支持命令行参数，使用已验证的安全批处理逻辑
"""

import argparse
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from services.safe_yearly_processor import SafeYearlyProcessor


def main():
    parser = argparse.ArgumentParser(description='处理指定年份的专利数据')
    parser.add_argument('--year', type=int, required=True, help='处理年份')
    parser.add_argument('--input', type=str, required=True, help='输入CSV文件路径')
    parser.add_argument('--output', type=str, default='data/patents/processed/china_patents_enhanced.db', help='输出数据库路径')
    parser.add_argument('--batch-size', type=int, default=2000, help='批处理大小')

    args = parser.parse_args()

    # 验证输入文件
    if not os.path.exists(args.input):
        logger.info(f"❌ 输入文件不存在: {args.input}")
        sys.exit(1)

    # 创建处理器
    processor = SafeYearlyProcessor()

    # 处理数据
    logger.info(f"\n{'='*60}")
    logger.info(f"开始处理 {args.year} 年专利数据")
    logger.info(f"输入文件: {args.input}")
    logger.info(f"输出数据库: {args.output}")
    logger.info(f"批处理大小: {args.batch_size}")
    logger.info(f"{'='*60}\n")

    # 备份现有数据库
    if os.path.exists(args.output):
        processor.backup_database(args.output)

    # 处理文件
    success, count = processor.process_year_file_safe(
        csv_path=args.input,
        db_path=args.output,
        batch_size=args.batch_size
    )

    if success:
        logger.info(f"\n✅ {args.year}年数据处理成功! 共处理 {count:,} 条专利")

        # 验证数据
        logger.info("\n验证处理结果...")
        is_valid = processor.verify_database(args.output, str(args.year))

        if is_valid:
            logger.info(f"✅ {args.year}年数据验证通过")

            # 显示统计信息
            processor.show_year_stats(args.output, args.year)
        else:
            logger.info(f"⚠️  {args.year}年数据验证失败，但处理已完成")
    else:
        logger.info(f"\n❌ {args.year}年数据处理失败")
        sys.exit(1)

if __name__ == '__main__':
    main()