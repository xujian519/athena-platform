#!/usr/bin/env python3
"""
处理最近几年的专利数据（非交互式）
验证后立即删除备份节省空间
"""

import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)

def process_single_year(year, source_dir, db_path, backup_dir):
    """处理单个年份"""
    csv_file = Path(source_dir) / f"中国专利数据库{year}年.csv"

    if not csv_file.exists():
        logger.info(f"⚠️  {year}年文件不存在，跳过")
        return False

    logger.info(f"\n{'='*60}")
    logger.info(f"处理 {year} 年数据")
    logger.info(f"文件: {csv_file.name}")
    logger.info(f"大小: {csv_file.stat().st_size/(1024*1024):.1f} MB")
    logger.info(f"{'='*60}")

    # 执行处理命令
    cmd = [
        'python3', 'scripts/process_patent_year.py',
        '--year', str(year),
        '--input', str(csv_file),
        '--output', db_path,
        '--batch-size', '2000'
    ]

    logger.info(f"执行: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        logger.info(f"✅ {year}年处理成功")

        # 验证数据
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM patents WHERE year = ?', (year,))
        count = cursor.fetchone()[0]
        conn.close()

        logger.info(f"  - 导入专利数: {count:,}")

        # 删除该年的备份（节省空间）
        for backup in Path(backup_dir).glob(f"*{year}*.db"):
            size_mb = backup.stat().st_size / (1024*1024)
            logger.info(f"  - 删除备份 {backup.name} (节省 {size_mb:.1f} MB)")
            backup.unlink()

        return True
    else:
        logger.info(f"❌ {year}年处理失败")
        logger.info(f"错误输出: {result.stderr[-500:]}")
        return False

def main():
    source_dir = '/Volumes/xujian/patent_data/china_patents'
    db_path = 'data/patents/processed/china_patents_enhanced.db'
    backup_dir = 'data/patents/processed/backups'

    # 创建目录
    os.makedirs(backup_dir, exist_ok=True)

    # 定义要处理的年份（从最近的开始）
    years = [2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016]

    logger.info(str('='*60))
    logger.info('处理最近几年的专利数据（空间优化版）')
    logger.info(f"处理年份: {years}")
    logger.info(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(str('='*60))

    successful_years = []
    failed_years = []

    for year in years:
        if process_single_year(year, source_dir, db_path, backup_dir):
            successful_years.append(year)
        else:
            failed_years.append(year)

    # 最终统计
    logger.info(str("\n" + '='*60))
    logger.info('处理完成统计')
    logger.info(str('='*60))

    if successful_years:
        logger.info(f"\n✅ 成功处理的年份: {successful_years}")

    if failed_years:
        logger.info(f"\n❌ 处理失败的年份: {failed_years}")

    # 数据库统计
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM patents')
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT year, COUNT(*)
            FROM patents
            WHERE year IN ({})
            GROUP BY year
            ORDER BY year DESC
        """.format(','.join(map(str, years))))
        year_stats = cursor.fetchall()

        logger.info(f"\n数据库总专利数: {total:,}")
        logger.info(f"\n处理年份统计:")
        for year, count in year_stats:
            logger.info(f"  {year}年: {count:,} 条")

        conn.close()

        # 显示文件大小
        db_size_mb = os.path.getsize(db_path) / (1024*1024)
        logger.info(f"\n数据库大小: {db_size_mb:.1f} MB")

    logger.info(f"\n完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()