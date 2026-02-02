#!/usr/bin/env python3
"""
专利数据导入进度监控脚本
实时显示2016-2020年数据导入进度
"""

import logging
import sys
import time
from datetime import datetime

import psycopg2

logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'patent_db'
}

def get_connection():
    """创建数据库连接"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.info(f"数据库连接失败: {e}")
        return None

def clear_screen():
    """清屏"""
    import os
    os.system('clear' if os.name == 'posix' else 'cls')

def monitor_progress():
    """监控导入进度"""
    years = [2016, 2017, 2018, 2019, 2020]
    last_counts = {year: 0 for year in years}

    while True:
        conn = get_connection()
        if not conn:
            logger.info('无法连接到数据库，等待5秒后重试...')
            time.sleep(5)
            continue

        cursor = conn.cursor()

        # 清屏并显示标题
        clear_screen()
        logger.info(str('=' * 80))
        logger.info(f"专利数据导入进度监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(str('=' * 80))

        # 检查各年份进度
        logger.info("\n📊 各年份导入进度:")
        logger.info(str('-' * 80))
        total_processed = 0
        total_estimated = 0

        for year in years:
            # 获取当前数量
            cursor.execute('SELECT COUNT(*) FROM patents WHERE source_year = %s', (year,))
            current_count = cursor.fetchone()[0]

            # 计算增量
            increment = current_count - last_counts[year]

            # 计算百分比（假设每年约300万条）
            estimated = 3000000
            percentage = (current_count / estimated * 100) if estimated > 0 else 0

            # 状态图标
            if percentage >= 100:
                status = '✅ 已完成'
                color = "\033[92m"  # 绿色
            elif percentage >= 80:
                status = '🔄 即将完成'
                color = "\033[93m"  # 黄色
            elif percentage >= 50:
                status = '🔄 过半'
                color = "\033[94m"  # 蓝色
            elif percentage >= 20:
                status = '🔄 进行中'
                color = "\033[96m"  # 青色
            elif percentage > 0:
                status = '🔄 刚开始'
                color = "\033[95m"  # 紫色
            else:
                status = '⏳ 未开始'
                color = "\033[90m"  # 灰色

            # 显示进度条
            bar_length = 30
            filled_length = int(bar_length * min(percentage / 100, 1))
            bar = '█' * filled_length + '░' * (bar_length - filled_length)

            # 输出进度信息
            logger.info(f"{color}{year}年: {current_count:>7,} / {estimated:,} ({percentage:>5.1f}%) [{bar}]\033[0m {status}")

            if increment > 0:
                logger.info(f"     +{increment:,} 条 (上次检查后新增)")

            total_processed += current_count
            total_estimated += estimated
            last_counts[year] = current_count

        # 总体进度
        total_percentage = (total_processed / (total_estimated) * 100) if total_estimated > 0 else 0
        logger.info(str('-' * 80))
        logger.info(f"\n📈 总体进度: {total_processed:,} / {total_estimated:,} ({total_percentage:.1f}%)")

        # 检查最近1小时的导入量
        logger.info("\n⏱️  最近1小时导入量:")
        logger.info(str('-' * 80))
        recent_total = 0
        for year in years:
            cursor.execute('''
                SELECT COUNT(*) FROM patents
                WHERE source_year = %s AND created_at > NOW() - INTERVAL '1 hour'
            ''', (year,))
            recent = cursor.fetchone()[0]
            if recent > 0:
                logger.info(f"{year}年: +{recent:,} 条")
                recent_total += recent

        if recent_total == 0:
            logger.info('❌ 最近1小时无新数据导入')
        else:
            logger.info(f"总计: +{recent_total:,} 条")

        # 检查正在运行的导入进程
        logger.info("\n🔄 正在运行的导入进程:")
        logger.info(str('-' * 80))
        import subprocess

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = []
            for line in result.stdout.split('\n'):
                if 'python3' in line and any(year in line for year in ['2016', '2017', '2018', '2019', '2020']):
                    if 'import_' in line:
                        parts = line.split()
                        pid = parts[1]
                        cpu = parts[2]
                        mem = parts[3]
                        cmd = ' '.join(parts[10:])
                        processes.append((pid, cpu, mem, cmd))

            if processes:
                for pid, cpu, mem, cmd in processes:
                    logger.info(f"PID {pid:>6} | CPU {cpu:>5}% | MEM {mem:>5}% | {cmd[:60]}...")
            else:
                logger.info('❌ 没有发现正在运行的导入进程')
        except:
            logger.info('⚠️ 无法获取进程信息')

        # 预计完成时间
        if recent_total > 0:
            remaining = total_estimated - total_processed
            hours_needed = remaining / recent_total
            logger.info(f"\n⏰ 预计完成时间: {hours_needed:.1f} 小时后")

        cursor.close()
        conn.close()

        # 等待30秒后再次检查
        logger.info(str("\n" + '=' * 80))
        logger.info('等待30秒后再次检查...')
        time.sleep(30)

if __name__ == '__main__':
    try:
        monitor_progress()
    except KeyboardInterrupt:
        logger.info("\n\n监控已停止")
        sys.exit(0)