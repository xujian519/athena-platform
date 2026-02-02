#!/usr/bin/env python3
"""
使用enhanced_patent_processor处理专利数据
基于成功的处理经验
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

import time

from services.enhanced_patent_processor import EnhancedPatentProcessor


def main():
    source_dir = '/Volumes/xujian/patent_data/china_patents'
    db_path = 'data/patents/processed/china_patents_enhanced.db'
    backup_dir = 'data/patents/processed/backups'

    # 创建必要目录
    os.makedirs(backup_dir, exist_ok=True)

    logger.info(str('='*60))
    logger.info('使用增强版处理器处理专利数据')
    logger.info(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(str('='*60))

    # 获取所有年份
    years = []
    for f in Path(source_dir).glob('中国专利数据库*.csv'):
        try:
            year = int(f.name.split('中国专利数据库')[1].split('年')[0])
            years.append(year)
        except:
            continue

    years = sorted(years)
    logger.info(f"\n找到 {len(years)} 年的数据: {years[0]} - {years[-1]}")

    # 处理每一年的数据
    for year in years:
        csv_file = Path(source_dir) / f"中国专利数据库{year}年.csv"

        if not csv_file.exists():
            logger.info(f"\n⚠️  {year}年文件不存在，跳过")
            continue

        logger.info(f"\n{'='*60}")
        logger.info(f"处理 {year} 年数据")
        logger.info(f"文件: {csv_file.name}")
        logger.info(f"大小: {csv_file.stat().st_size/(1024*1024):.1f} MB")
        logger.info(f"{'='*60}")

        # 创建处理器实例
        processor = EnhancedPatentProcessor()

        # 处理数据
        success, count = processor.process_patent_file(
            csv_path=str(csv_file),
            db_path=db_path,
            batch_size=2000
        )

        if success:
            logger.info(f"✅ {year}年处理成功，导入 {count:,} 条专利")

            # 删除备份文件（节省空间）
            for backup in Path(backup_dir).glob(f"*{year}*.db"):
                size_mb = backup.stat().st_size / (1024*1024)
                logger.info(f"  🗑️  删除备份 {backup.name} (节省 {size_mb:.1f} MB)")
                backup.unlink()
        else:
            logger.info(f"❌ {year}年处理失败")

if __name__ == '__main__':
    main()