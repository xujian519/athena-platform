#!/usr/bin/env python3
"""
专利数据导入紧急修复脚本
清理卡住进程并重启优化的数据导入
"""

import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime

import psycopg2

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'patent_db'
}

def log(message):
    """输出日志信息"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{timestamp}] {message}")

def get_patent_progress():
    """获取当前专利数据导入进度"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 检查各年份导入进度
        years = [2016, 2017, 2018, 2019, 2020]
        progress = {}

        for year in years:
            cursor.execute('SELECT COUNT(*) FROM patents WHERE source_year = %s', (year,))
            count = cursor.fetchone()[0]
            progress[year] = count

        cursor.close()
        conn.close()
        return progress

    except Exception as e:
        log(f"❌ 获取进度失败: {e}")
        return {}

def kill_stuck_processes():
    """清理卡住的导入进程"""
    log('🔍 查找卡住的导入进程...')

    stuck_processes = []

    # 查找相关进程
    try:
        result = subprocess.run([
            'ps', 'aux'
        ], capture_output=True, text=True)

        lines = result.stdout.split('\n')
        for line in lines:
            if any(keyword in line for keyword in [
                'import_large_patent_file.py',
                'import_patents_to_postgres.py',
                'migrate_simple_to_full.py',
                'optimized_patent_importer.py',
                'batch_migrate_patents.py'
            ]) and 'grep' not in line:
                parts = line.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    cmd = ' '.join(parts[10:])
                    stuck_processes.append((pid, cmd))

    except Exception as e:
        log(f"❌ 查找进程失败: {e}")

    if not stuck_processes:
        log('✅ 没有发现卡住的进程')
        return

    log(f"🔧 发现 {len(stuck_processes)} 个卡住的进程:")
    for pid, cmd in stuck_processes:
        log(f"  PID {pid}: {cmd[:80]}...")

    # 终止进程
    for pid, cmd in stuck_processes:
        try:
            log(f"🛑 终止进程 PID {pid}")
            os.kill(int(pid), signal.SIGTERM)
            time.sleep(2)

            # 如果还在运行，强制终止
            try:
                os.kill(int(pid), 0)  # 检查进程是否还存在
                log(f"💥 强制终止进程 PID {pid}")
                os.kill(int(pid), signal.SIGKILL)
            except OSError:
                pass  # 进程已经不存在

        except Exception as e:
            log(f"❌ 终止进程失败 {pid}: {e}")

def restart_optimized_import():
    """重启优化的数据导入"""
    log('🚀 启动优化的数据导入...')

    progress = get_patent_progress()

    # 根据当前进度决定导入策略
    if progress.get(2016, 0) < 3000000:
        log('▶️ 启动2016年数据导入 (还需约300万条)')
        subprocess.Popen([
            'python3', 'scripts/import_large_patent_file.py',
            '--year', '2016',
            '--chunks', '60',
            '--batch-size', '800',
            '--workers', '4'
        ])

    if progress.get(2017, 0) < 3000000:
        time.sleep(30)  # 错开启动时间
        log('▶️ 启动2017年数据导入 (还需约300万条)')
        subprocess.Popen([
            'python3', 'scripts/import_large_patent_file.py',
            '--year', '2017',
            '--chunks', '80',
            '--batch-size', '1000',
            '--workers', '4'
        ])

    if progress.get(2019, 0) < 100000:  # 2019年几乎还没开始
        time.sleep(60)  # 错开启动时间
        log('▶️ 启动2019年数据导入 (全新开始)')
        subprocess.Popen([
            'python3', 'scripts/import_large_patent_file.py',
            '--year', '2019',
            '--chunks', '100',
            '--batch-size', '600',
            '--workers', '3'
        ])

def monitor_progress():
    """监控导入进度"""
    log('📊 启动进度监控...')

    while True:
        try:
            progress = get_patent_progress()
            total = sum(progress.values())

            # 计算最近5分钟的变化
            time.sleep(300)  # 5分钟检查一次

            new_progress = get_patent_progress()
            new_total = sum(new_progress.values())

            if new_total > total:
                increase = new_total - total
                log(f"✅ 最近5分钟新增: {increase:,} 条专利")

                # 显示各年份进度
                for year in sorted(new_progress.keys()):
                    count = new_progress[year]
                    percentage = (count / 3000000) * 100
                    log(f"  {year}年: {count:,} 条 ({percentage:.1f}%)")
            else:
                log('⚠️ 最近5分钟无新数据，可能需要再次检查')

        except KeyboardInterrupt:
            log('🛑 停止监控')
            break
        except Exception as e:
            log(f"❌ 监控出错: {e}")
            time.sleep(60)  # 出错后等待1分钟再试

def main():
    """主函数"""
    log('=' * 60)
    log('🔧 专利数据导入紧急修复脚本')
    log('=' * 60)

    # 1. 显示当前状态
    log("\n📊 当前导入状态:")
    progress = get_patent_progress()
    total = sum(progress.values())

    for year in sorted(progress.keys()):
        count = progress[year]
        percentage = (count / 3000000) * 100
        status = '✅ 已完成' if percentage >= 100 else '🔄 进行中' if percentage > 0 else '⏳ 未开始'
        log(f"  {year}年: {count:,} 条 ({percentage:.1f}%) - {status}")

    log(f"\n📈 总计: {total:,} 条专利")

    # 2. 清理卡住进程
    log("\n🔧 第一步: 清理卡住的进程...")
    kill_stuck_processes()

    # 等待一段时间让系统稳定
    log('⏱️ 等待系统稳定...')
    time.sleep(10)

    # 3. 重启优化的导入
    log("\n🚀 第二步: 重启优化的数据导入...")
    restart_optimized_import()

    # 4. 监控进度
    log("\n📊 第三步: 开始监控进度...")
    log('💡 提示: 按 Ctrl+C 可以停止监控')

    try:
        monitor_progress()
    except KeyboardInterrupt:
        log("\n🛑 监控已停止")

    log('✅ 紧急修复脚本执行完成')

if __name__ == '__main__':
    main()