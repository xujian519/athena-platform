#!/usr/bin/env python3
"""
从1985年开始按顺序处理专利数据
每处理完一年验证后立即删除备份，节省空间
"""

import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/process_from_1985.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_available_years(source_dir):
    """获取所有可用的年份"""
    csv_files = list(Path(source_dir).glob('中国专利数据库*.csv'))
    years = []

    for f in csv_files:
        try:
            # 从文件名提取年份
            year_str = f.name.split('中国专利数据库')[1].split('年')[0]
            year = int(year_str)
            years.append(year)
        except:
            continue

    return sorted(years)

def process_single_year(year, source_dir, db_path, backup_dir):
    """处理单个年份的数据"""
    csv_file = Path(source_dir) / f"中国专利数据库{year}年.csv"

    if not csv_file.exists():
        logger.warning(f"⚠️  {year}年文件不存在，跳过")
        return False, 0

    logger.info(f"\n{'='*60}")
    logger.info(f"处理 {year} 年数据")
    logger.info(f"文件: {csv_file.name}")
    logger.info(f"大小: {csv_file.stat().st_size/(1024*1024):.1f} MB")
    logger.info(f"{'='*60}")

    # 检查磁盘空间
    df_output = os.popen(f"df -h {Path(db_path).parent}").read()
    if len(df_output.split('\n')) > 1:
        used_percent = df_output.split('\n')[1].split()[4].rstrip('%')
        if int(used_percent) > 85:
            logger.warning(f"⚠️ 磁盘使用率过高 ({used_percent}%)")

    # 使用批处理器处理
    cmd = [
        'python3', 'services/safe_yearly_processor.py',
        '--csv-path', str(csv_file),
        '--db-path', str(db_path),
        '--batch-size', '2000'
    ]

    logger.info(f"执行批处理命令...")
    start_time = time.time()

    # 运行批处理
    result = subprocess.run(cmd, capture_output=True, text=True)

    elapsed = time.time() - start_time

    if result.returncode == 0:
        logger.info(f"✅ {year}年处理成功，耗时: {elapsed:.2f}秒")

        # 验证数据
        logger.info(f"\n验证 {year} 年数据...")
        success, count = verify_year_data(db_path, year)

        if success:
            logger.info(f"✅ {year}年数据验证通过，导入 {count:,} 条专利")

            # 删除备份文件
            cleanup_backups(backup_dir, year)

            return True, count
        else:
            logger.error(f"❌ {year}年数据验证失败")
            return False, 0
    else:
        logger.error(f"❌ {year}年处理失败")
        if result.stderr:
            logger.error(f"错误信息: {result.stderr[-500:]}")
        return False, 0

def verify_year_data(db_path, year):
    """验证指定年份的数据"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查该年的记录数
        cursor.execute('SELECT COUNT(*) FROM patents WHERE source_year = ?', (year,))
        count = cursor.fetchone()[0]

        # 如果没有记录，检查year字段
        if count == 0:
            cursor.execute('SELECT COUNT(*) FROM patents WHERE year = ?', (str(year),))
            count = cursor.fetchone()[0]

        # 抽样检查
        cursor.execute("""
            SELECT patent_name, applicant, application_number
            FROM patents
            WHERE (source_year = ? OR year = ?)
            AND patent_name IS NOT NULL
            LIMIT 3
        """, (year, str(year)))

        samples = cursor.fetchall()

        conn.close()

        if samples:
            logger.info(f"  样本数据:")
            for i, (name, applicant, app_num) in enumerate(samples, 1):
                logger.info(f"    {i}. {name[:50]}...")
                logger.info(f"       申请人: {applicant}")
                logger.info(f"       申请号: {app_num}")

        return True, count

    except Exception as e:
        logger.error(f"验证失败: {str(e)}")
        return False, 0

def cleanup_backups(backup_dir, year):
    """清理指定年份的备份"""
    patterns = [
        f"*{year}*.db",
        f"pre_{year}_*.db"
    ]

    cleaned_size = 0
    for pattern in patterns:
        for backup in Path(backup_dir).glob(pattern):
            size_mb = backup.stat().st_size / (1024*1024)
            logger.info(f"  🗑️  删除备份 {backup.name} (节省 {size_mb:.1f} MB)")
            backup.unlink()
            cleaned_size += size_mb

    if cleaned_size > 0:
        logger.info(f"  💾 总共节省空间: {cleaned_size:.1f} MB")

def get_processed_years(db_path):
    """获取已处理的年份"""
    if not os.path.exists(db_path):
        return []

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 尝试从不同字段获取年份
        cursor.execute("""
            SELECT DISTINCT COALESCE(source_year, year) as year
            FROM patents
            WHERE COALESCE(source_year, year) IS NOT NULL
            AND COALESCE(source_year, year) != ''
        """)

        years = [int(row[0]) for row in cursor.fetchall() if row[0].isdigit()]
        conn.close()

        return sorted(years)
    except:
        return []

def main():
    source_dir = '/Volumes/xujian/patent_data/china_patents'
    db_path = 'data/patents/processed/china_patents_enhanced.db'
    backup_dir = 'data/patents/processed/backups'

    # 创建必要目录
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    logger.info('='*60)
    logger.info('从1985年开始处理专利数据（空间优化版）')
    logger.info(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info('='*60)

    # 检查源目录
    if not os.path.exists(source_dir):
        logger.error(f"❌ 源目录不存在: {source_dir}")
        return

    # 获取所有可用年份
    available_years = get_available_years(source_dir)
    if not available_years:
        logger.error('❌ 未找到专利数据文件')
        return

    # 查找已处理的年份
    processed_years = get_processed_years(db_path)

    logger.info(f"\n可用年份: {available_years[0]} - {available_years[-1]}")
    logger.info(f"已处理年份: {processed_years if processed_years else '无'}")

    # 确认从1985年开始
    if 1985 not in available_years:
        logger.warning('⚠️  1985年数据不存在，将从最早年份开始')
        start_year = available_years[0]
    else:
        start_year = 1985

    # 获取要处理的年份列表
    years_to_process = [y for y in available_years if y >= start_year]

    logger.info(f"\n将从 {start_year} 年开始处理，共 {len(years_to_process)} 年")

    # 统计
    total_processed = 0
    successful_years = []
    failed_years = []

    # 按顺序处理年份
    for year in years_to_process:
        if year in processed_years:
            logger.info(f"⏭️  跳过已处理的年份: {year}")
            continue

        # 检查系统负载
        load = os.popen("uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ','").read().strip()
        try:
            if float(load) > 3.0:
                logger.warning(f"⚠️  系统负载过高 ({load})，等待60秒...")
                time.sleep(60)
        except:
            pass

        # 处理当前年份
        success, count = process_single_year(year, source_dir, db_path, backup_dir)

        if success:
            total_processed += count
            successful_years.append(year)

            # 显示进度
            progress = len(successful_years) / len(years_to_process) * 100
            logger.info(f"\n📊 进度: {progress:.1f}% ({len(successful_years)}/{len(years_to_process)})")
            logger.info(f"📈 累计导入专利: {total_processed:,}")
        else:
            failed_years.append(year)

            # 询问是否继续
            logger.error(f"\n❌ {year}年处理失败")
            logger.info(f"成功年份: {successful_years}")
            logger.info(f"失败年份: {failed_years}")

            # 继续处理下一年
            logger.info('继续处理下一年...')

    # 最终统计
    logger.info("\n" + '='*60)
    logger.info('处理完成统计')
    logger.info('='*60)

    logger.info(f"\n成功处理年份: {successful_years}")
    if failed_years:
        logger.info(f"处理失败年份: {failed_years}")

    # 数据库最终统计
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM patents')
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COALESCE(source_year, year), COUNT(*)
            FROM patents
            WHERE COALESCE(source_year, year) IS NOT NULL
            AND COALESCE(source_year, year) != ''
            GROUP BY COALESCE(source_year, year)
            ORDER BY COALESCE(source_year, year) DESC
            LIMIT 10
        """)
        year_stats = cursor.fetchall()

        conn.close()

        logger.info(f"\n最终数据库统计:")
        logger.info(f"  总专利数: {total:,}")
        logger.info(f"\n最近10年统计:")
        for year, count in year_stats:
            logger.info(f"  {year}年: {count:,} 条")

        # 显示文件大小
        db_size_mb = os.path.getsize(db_path) / (1024*1024)
        logger.info(f"\n数据库大小: {db_size_mb:.1f} MB")

    logger.info(f"\n完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info('='*60)

if __name__ == '__main__':
    main()