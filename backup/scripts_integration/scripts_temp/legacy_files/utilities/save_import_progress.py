#!/usr/bin/env python3
"""
专利数据导入进度保存和恢复脚本
在重启前保存当前进度，重启后可以继续导入
"""

import json
import logging
import os
import subprocess
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

# 进度保存文件
PROGRESS_FILE = 'data/import_progress.json'

def log(message):
    """输出日志信息"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{timestamp}] {message}")

def save_progress():
    """保存当前导入进度"""
    log('💾 保存当前导入进度...')

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 获取各年份的导入进度
        progress_data = {
            'timestamp': datetime.now().isoformat(),
            'total_patents': 0,
            'years': {},
            'next_import_tasks': []
        }

        years = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]
        target_counts = {
            2010: 1000000, 2011: 1000000, 2012: 1000000, 2013: 1000000, 2014: 1000000,
            2015: 3000000, 2016: 3000000, 2017: 3000000, 2018: 3000000, 2019: 3000000, 2020: 3000000
        }

        for year in years:
            cursor.execute('SELECT COUNT(*) FROM patents WHERE source_year = %s', (year,))
            count = cursor.fetchone()[0]
            progress_data['years'][year] = {
                'imported': count,
                'target': target_counts[year],
                'percentage': (count / target_counts[year] * 100) if target_counts[year] > 0 else 0,
                'remaining': max(0, target_counts[year] - count)
            }
            progress_data['total_patents'] += count

        # 生成下一步导入任务
        for year in years:
            year_data = progress_data['years'][year]
            if year_data['remaining'] > 0:
                # 根据剩余数量确定导入策略
                if year_data['remaining'] > 2000000:
                    chunks = 100
                    batch_size = 1000
                    workers = 4
                elif year_data['remaining'] > 1000000:
                    chunks = 80
                    batch_size = 800
                    workers = 3
                else:
                    chunks = 50
                    batch_size = 600
                    workers = 2

                progress_data['next_import_tasks'].append({
                    'year': year,
                    'priority': 'high' if year in [2016, 2017, 2019] else 'medium',
                    'remaining': year_data['remaining'],
                    'chunks': chunks,
                    'batch_size': batch_size,
                    'workers': workers,
                    'command': f'python3 scripts/import_large_patent_file.py --year {year} --chunks {chunks} --batch-size {batch_size} --workers {workers}'
                })

        # 按优先级和剩余数量排序任务
        progress_data['next_import_tasks'].sort(key=lambda x: (
            0 if x['priority'] == 'high' else 1,
            -x['remaining']
        ))

        cursor.close()
        conn.close()

        # 确保目录存在
        os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)

        # 保存进度到文件
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)

        log(f"✅ 进度已保存到: {PROGRESS_FILE}")

        # 显示保存的进度摘要
        log("\n📊 导入进度摘要:")
        total_target = sum(target_counts.values())
        total_imported = progress_data['total_patents']
        total_percentage = (total_imported / total_target * 100) if total_target > 0 else 0

        log(f"  总进度: {total_imported:,} / {total_target:,} ({total_percentage:.1f}%)")

        for year in years:
            if year in progress_data['years']:
                year_data = progress_data['years'][year]
                status = '✅ 已完成' if year_data['percentage'] >= 100 else \
                        '🔄 进行中' if year_data['percentage'] > 0 else '⏳ 未开始'
                log(f"  {year}年: {year_data['imported']:,} 条 ({year_data['percentage']:.1f}%) - {status}")

        log(f"\n🎯 下一步导入任务 ({len(progress_data['next_import_tasks'])} 个):")
        for i, task in enumerate(progress_data['next_import_tasks'][:5], 1):  # 只显示前5个任务
            log(f"  {i}. {task['year']}年 - 剩余{task['remaining']:,}条 ({task['priority']}优先级)")

        return progress_data

    except Exception as e:
        log(f"❌ 保存进度失败: {e}")
        return None

def stop_all_imports():
    """停止所有导入进程"""
    log('🛑 停止所有导入进程...')

    try:
        # 查找所有导入相关进程
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')

        stopped_count = 0
        for line in lines:
            if any(keyword in line for keyword in [
                'import_large_patent_file.py',
                'import_patents_to_postgres.py',
                'migrate_simple_to_full.py',
                'optimized_patent_importer.py',
                'batch_migrate_patents.py',
                'emergency_import_fix.py'
            ]) and 'grep' not in line and 'save_import_progress.py' not in line:
                parts = line.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    try:
                        os.kill(int(pid), 15)  # SIGTERM
                        stopped_count += 1
                        time.sleep(1)
                    except:
                        pass

        log(f"✅ 已停止 {stopped_count} 个导入进程")

    except Exception as e:
        log(f"❌ 停止进程时出错: {e}")

def create_restart_script():
    """创建重启脚本"""
    restart_script = """#!/bin/bash
# 专利数据导入重启脚本
# 重启系统后运行此脚本继续导入

echo '🔄 重启专利数据导入...'
echo '上次保存时间: $(date)'

# 检查进度文件是否存在
if [ ! -f 'data/import_progress.json' ]; then
    echo '❌ 未找到进度文件，请先运行 python3 scripts/save_import_progress.py'
    exit 1
fi

# 等待数据库启动
echo '⏱️ 等待数据库启动...'
sleep 10

# 检查数据库连接
python3 -c "
import psycopg2

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query
try:
    conn = psycopg2.connect(host='localhost', port=5432, user='postgres', password='postgres', database='patent_db')
    conn.close()
    logger.info('✅ 数据库连接正常')
except Exception as e:
    logger.info(f"❌ 数据库连接失败: {e}")
    exit(1)
"

if [ $? -ne 0 ]; then
    echo '❌ 数据库连接失败，请先启动PostgreSQL'
    exit 1
fi

# 启动导入任务
echo '🚀 启动导入任务...'

# 高优先级任务（2016、2017、2019年）
python3 scripts/import_large_patent_file.py --year 2016 --chunks 60 --batch-size 800 --workers 4 &
sleep 30

python3 scripts/import_large_patent_file.py --year 2017 --chunks 80 --batch-size 1000 --workers 4 &
sleep 30

python3 scripts/import_large_patent_file.py --year 2019 --chunks 100 --batch-size 600 --workers 3 &

echo '✅ 重启脚本执行完成，导入任务已在后台运行'
echo '💡 使用以下命令监控进度:'
echo '   python3 scripts/monitor_import_progress.py'
"""

    with open('restart_import.sh', 'w', encoding='utf-8') as f:
        f.write(restart_script)

    os.chmod('restart_import.sh', 0o755)
    log('✅ 重启脚本已创建: restart_import.sh')

def main():
    """主函数"""
    log('=' * 60)
    log('💾 专利数据导入进度保存脚本')
    log('=' * 60)

    # 1. 保存进度
    progress = save_progress()
    if not progress:
        log('❌ 无法保存进度，退出')
        sys.exit(1)

    # 2. 停止所有导入进程
    log("\n🛑 停止当前导入进程...")
    stop_all_imports()

    # 3. 创建重启脚本
    log("\n📝 创建重启脚本...")
    create_restart_script()

    # 4. 生成重启说明
    log("\n" + '=' * 60)
    log('📋 重启说明')
    log('=' * 60)
    log('1. 重启电脑')
    log('2. 启动PostgreSQL数据库')
    log('3. 进入Athena工作平台目录:')
    log('   cd /Users/xujian/Athena工作平台')
    log('4. 运行重启脚本:')
    log('   ./restart_import.sh')
    log('5. 监控导入进度:')
    log('   python3 scripts/monitor_import_progress.py')
    log('')
    log('💡 当前进度已保存到: data/import_progress.json')
    log('💡 重启脚本已创建: restart_import.sh')

    log("\n✅ 进度保存完成，可以安全重启系统了")

if __name__ == '__main__':
    main()