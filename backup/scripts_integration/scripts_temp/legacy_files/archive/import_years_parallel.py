#!/usr/bin/env python3
"""
并行导入多年份专利数据到简化表
使用多进程加速导入
"""

import logging
import multiprocessing as mp
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_year(year, result_queue):
    """导入单年数据到简化表"""
    try:
        cmd = [sys.executable, 'scripts/simple_import_2013_plus.py', str(year)]

        start_time = datetime.now()
        logger.info(f"[{year}] 开始导入...")

        # 运行导入脚本
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200  # 2小时超时
        )

        elapsed = datetime.now() - start_time

        if result.returncode == 0:
            # 解析输出获取导入数量
            count = 0
            for line in result.stdout.split('\n'):
                if '成功导入:' in line:
                    try:
                        count = int(line.split('成功导入:')[1].split(',')[0].replace(',', '').strip())
                    except:
                        pass

            result_queue.put({
                'year': year,
                'status': 'success',
                'count': count,
                'elapsed': str(elapsed),
                'output': result.stdout[-500:] if result.stdout else ''
            })
            logger.info(f"[{year}] ✅ 导入完成: {count:,} 条记录 (耗时: {elapsed})")
        else:
            result_queue.put({
                'year': year,
                'status': 'error',
                'error': result.stderr[-500:] if result.stderr else '未知错误',
                'elapsed': str(elapsed)
            })
            logger.error(f"[{year}] ❌ 导入失败: {result.stderr[:200] if result.stderr else '未知错误'}")

    except subprocess.TimeoutExpired:
        result_queue.put({
            'year': year,
            'status': 'timeout',
            'error': '导入超时',
            'elapsed': str(datetime.now() - start_time)
        })
        logger.error(f"[{year}] ⏰ 导入超时")

    except Exception as e:
        result_queue.put({
            'year': year,
            'status': 'exception',
            'error': str(e),
            'elapsed': str(datetime.now() - start_time)
        })
        logger.error(f"[{year}] 💥 异常: {str(e)}")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='并行导入多年份专利数据')
    parser.add_argument('--years', type=str, default='2013-2025',
                       help='年份范围，格式: 2013-2025 或 2013,2014,2015')
    parser.add_argument('--max-workers', type=int, default=3,
                       help='最大并行数 (默认: 3)')

    args = parser.parse_args()

    # 解析年份
    if '-' in args.years:
        start, end = map(int, args.years.split('-'))
        years = list(range(start, end + 1))
    else:
        years = [int(y.strip()) for y in args.years.split(',')]

    # 过滤已存在的年份
    existing_years = []
    pending_years = []

    for year in years:
        # 检查文件是否存在
        csv_file = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"
        if not Path(csv_file).exists():
            logger.warning(f"⚠️  {year}年文件不存在: {csv_file}")
            continue

        # 检查是否已导入
        result = subprocess.run(
            ['psql', '-h', 'localhost', '-U', 'postgres', '-d', 'patent_db', '-c',
             f"SELECT COUNT(*) FROM patents_simple WHERE source_year = {year}"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            try:
                count = int(result.stdout.strip())
                if count > 0:
                    existing_years.append((year, count))
                    logger.info(f"✅ {year}年已存在 {count:,} 条记录，跳过")
                    continue
            except:
                pass

        pending_years.append(year)

    logger.info(f"\n准备导入 {len(pending_years)} 年的数据: {pending_years}")
    logger.info(f"最大并行数: {args.max_workers}")

    if not pending_years:
        logger.info("\n没有需要导入的年份")
        return

    # 使用进度管理器控制并发数
    total_success = 0
    total_count = 0

    # 分批处理
    for i in range(0, len(pending_years), args.max_workers):
        batch = pending_years[i:i + args.max_workers]
        logger.info(f"\n开始处理批次: {batch}")

        # 创建进程池
        result_queue = mp.Queue()
        processes = []

        # 启动进程
        for year in batch:
            p = mp.Process(target=import_year, args=(year, result_queue))
            p.start()
            processes.append(p)

        # 收集结果
        results = []
        for _ in batch:
            results.append(result_queue.get())

        # 等待所有进程结束
        for p in processes:
            p.join()

        # 处理结果
        for result in results:
            if result['status'] == 'success':
                total_success += 1
                total_count += result['count']
                logger.info(f"✅ {result['year']}年: {result['count']:,} 条记录")
            else:
                logger.error(f"❌ {result['year']}年: {result['status']} - {result.get('error', '')}")

    # 显示最终结果
    logger.info(f"\n{'='*60}")
    logger.info(f"并行导入完成!")
    logger.info(f"  成功年份: {total_success}/{len(pending_years)}")
    logger.info(f"  总导入量: {total_count:,} 条记录")

    # 更新的统计
    logger.info(f"\n更新后的统计:")
    result = subprocess.run(
        ['psql', '-h', 'localhost', '-U', 'postgres', '-d', 'patent_db', '-c',
         'SELECT source_year, COUNT(*) as count FROM patents_simple GROUP BY source_year ORDER BY source_year'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')[2:-1]  # 跳过标题和分隔线
        for line in lines:
            if '|' in line:
                year, count = line.split('|')
                logger.info(f"  {year.strip()}: {int(count.strip()):,} 条记录")

    logger.info(f"{'='*60}")

if __name__ == '__main__':
    main()