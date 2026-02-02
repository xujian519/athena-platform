#!/usr/bin/env python3
"""
按时间顺序逐年处理专利数据，验证后立即删除备份节省空间
"""

import logging
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)

def main():
    source_dir = '/Volumes/xujian/patent_data/china_patents'
    db_path = 'data/patents/processed/china_patents_enhanced.db'
    backup_dir = 'data/patents/processed/backups'

    # 创建目录
    os.makedirs(backup_dir, exist_ok=True)

    logger.info(str('='*60))
    logger.info('专利数据按时间顺序处理（空间优化版）')
    logger.info(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(str('='*60))

    # 检查源目录
    if not os.path.exists(source_dir):
        logger.info(f"❌ 源目录不存在: {source_dir}")
        return

    # 获取所有CSV文件并排序
    csv_files = sorted(Path(source_dir).glob('中国专利数据库*.csv'))
    if not csv_files:
        logger.info('❌ 未找到专利数据文件')
        return

    logger.info(f"\n找到 {len(csv_files)} 个文件，将按时间顺序处理:")

    # 显示处理计划
    for f in csv_files[:5]:  # 只显示前5个
        year = f.name.split('中国专利数据库')[1].split('年')[0]
        size_mb = f.stat().st_size / (1024*1024)
        logger.info(f"  - {year}年: {size_mb:.1f} MB")
    if len(csv_files) > 5:
        logger.info(f"  ... 还有 {len(csv_files)-5} 个文件")

    # 确认是否继续
    logger.info(f"\n总计需要处理 {len(csv_files)} 年的数据")
    response = input('是否继续? (y/n): ')
    if response.lower() != 'y':
        return

    # 逐年处理
    for i, csv_file in enumerate(csv_files, 1):
        year = csv_file.name.split('中国专利数据库')[1].split('年')[0]

        logger.info(str("\n" + '='*60))
        logger.info(f"[{i}/{len(csv_files)}] 处理 {year} 年数据")
        logger.info(f"文件: {csv_file.name}")
        logger.info(f"大小: {csv_file.stat().st_size/(1024*1024):.1f} MB")
        logger.info(str('='*60))

        # 使用批处理命令
        cmd = f"""python3 scripts/process_patent_year.py \
            --year {year} \
            --input {csv_file} \
            --output {db_path} \
            --batch-size 2000"""

        logger.info(f"\n执行命令:")
        logger.info(str(cmd))

        # 执行处理
        exit_code = os.system(cmd)

        if exit_code == 0:
            logger.info(f"✅ {year}年处理成功")

            # 删除该年的备份文件（节省空间）
            for backup in Path(backup_dir).glob(f"*{year}*.db"):
                size_mb = backup.stat().st_size / (1024*1024)
                logger.info(f"删除备份 {backup.name} (节省 {size_mb:.1f} MB)")
                backup.unlink()

        else:
            logger.info(f"❌ {year}年处理失败 (退出码: {exit_code})")

            # 询问是否继续
            cont = input('是否继续处理下一年? (y/n): ')
            if cont.lower() != 'y':
                break

    # 最终统计
    logger.info(str("\n" + '='*60))
    logger.info('处理完成统计')
    logger.info(str('='*60))

    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM patents')
        total = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT year) FROM patents')
        years = cursor.fetchone()[0]

        cursor.execute('SELECT year, COUNT(*) FROM patents GROUP BY year ORDER BY year DESC LIMIT 5')
        recent = cursor.fetchall()

        logger.info(f"总专利数: {total:,}")
        logger.info(f"涉及年数: {years}")
        logger.info("\n最近5年统计:")
        for year, count in recent:
            logger.info(f"  {year}年: {count:,} 条")

        conn.close()

        # 显示文件大小
        db_size_mb = os.path.getsize(db_path) / (1024*1024)
        logger.info(f"\n数据库大小: {db_size_mb:.1f} MB")

    logger.info(f"\n完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()