#!/usr/bin/env python3
"""
管理并行导入多年份专利数据
"""

import logging
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

class ImportManager:
    """导入管理器"""

    def __init__(self):
        self.processes = {}
        self.log_dir = Path('documentation/logs/parallel_imports')
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def start_import(self, year):
        """启动指定年份的导入"""
        if year in self.processes:
            logger.warning(f"{year}年导入已在运行中")
            return False

        # 创建日志文件
        log_file = self.log_dir / f"import_{year}.log"

        # 启动导入进程
        cmd = [
            sys.executable,
            'scripts/batch_import_years.py',
            '--year', str(year)
        ]

        logger.info(f"启动 {year} 年导入...")
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=Path.cwd(),
                universal_newlines=True
            )

        self.processes[year] = {
            'process': process,
            'start_time': datetime.now(),
            'log_file': log_file
        }

        logger.info(f"✅ {year} 年导入已启动 (PID: {process.pid})")
        return True

    def start_parallel_imports(self, years, max_concurrent=3):
        """并行导入多个年份"""
        # 按文件大小排序，先导入小文件
        years_with_size = []
        for year in years:
            csv_file = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"
            if Path(csv_file).exists():
                size = Path(csv_file).stat().st_size
                years_with_size.append((year, size))

        years_with_size.sort(key=lambda x: x[1])
        sorted_years = [y for y, _ in years_with_size]

        logger.info(f"导入顺序（按文件大小）: {sorted_years}")

        # 并行导入
        for i, year in enumerate(sorted_years):
            # 等待有空闲槽位
            while len(self.processes) >= max_concurrent:
                self.check_processes()
                if len(self.processes) >= max_concurrent:
                    time.sleep(5)

            # 启动导入
            self.start_import(year)
            time.sleep(2)  # 避免同时启动太多进程

        # 等待所有导入完成
        while self.processes:
            self.check_processes()
            if self.processes:
                time.sleep(10)

    def check_processes(self):
        """检查并清理已完成的进程"""
        completed = []

        for year, info in self.processes.items():
            process = info['process']

            if process.poll() is not None:
                # 进程已结束
                return_code = process.returncode
                elapsed = datetime.now() - info['start_time']

                if return_code == 0:
                    logger.info(f"✅ {year} 年导入成功完成 (耗时: {elapsed})")
                else:
                    logger.error(f"❌ {year} 年导入失败 (返回码: {return_code})")
                    # 显示最后几行日志
                    self.show_last_log_lines(year, 5)

                completed.append(year)

        # 清理已完成的进程
        for year in completed:
            del self.processes[year]

    def show_last_log_lines(self, year, n=10):
        """显示最后的日志行"""
        if year in self.processes:
            log_file = self.processes[year]['log_file']
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for line in lines[-n:]:
                            logger.error(f"    {line.strip()}")
                except Exception as e:
                    logger.error(f"    读取日志失败: {str(e)}")

    def stop_all(self):
        """停止所有导入进程"""
        logger.info('正在停止所有导入进程...')
        for year, info in self.processes.items():
            try:
                info['process'].terminate()
                logger.info(f"已发送停止信号给 {year} 年导入进程")
            except Exception as e:
                logger.error(f"停止 {year} 年导入进程失败: {str(e)}")

        # 等待进程结束
        time.sleep(5)

        # 强制杀死仍在运行的进程
        for year, info in self.processes.items():
            try:
                if info['process'].poll() is None:
                    info['process'].kill()
                    logger.info(f"已强制终止 {year} 年导入进程")
            except Exception as e:
                logger.error(f"强制终止 {year} 年导入进程失败: {str(e)}")

    def get_status(self):
        """获取当前状态"""
        if not self.processes:
            logger.info('当前没有正在运行的导入任务')
            return

        logger.info(f"\n当前有 {len(self.processes)} 个导入任务正在运行:")
        for year, info in self.processes.items():
            elapsed = datetime.now() - info['start_time']
            status = '运行中' if info['process'].poll() is None else '已结束'
            logger.info(f"  {year}年: {status} (PID: {info['process'].pid}, 耗时: {elapsed})")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='管理并行专利数据导入')
    parser.add_argument('--years', type=str, default='2013-2025',
                       help='年份范围，格式: 2013-2025 或 2013,2014,2015')
    parser.add_argument('--max-concurrent', type=int, default=3,
                       help='最大并行数 (默认: 3)')
    parser.add_argument('--status', action='store_true',
                       help='查看当前状态')
    parser.add_argument('--stop', action='store_true',
                       help='停止所有导入任务')

    args = parser.parse_args()

    manager = ImportManager()

    # 注册退出处理器
    def signal_handler(signum, frame):
        logger.info("\n正在停止所有导入任务...")
        manager.stop_all()
        sys.exit(0)

    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.status:
        manager.get_status()
        return

    if args.stop:
        manager.stop_all()
        return

    # 解析年份
    if '-' in args.years:
        start, end = map(int, args.years.split('-'))
        years = list(range(start, end + 1))
    else:
        years = [int(y.strip()) for y in args.years.split(',')]

    logger.info(f"准备导入年份: {years}")
    logger.info(f"最大并行数: {args.max_concurrent}")

    # 开始并行导入
    manager.start_parallel_imports(years, args.max_concurrent)

    # 显示最终状态
    manager.get_status()
    logger.info("\n所有导入任务已完成!")

if __name__ == '__main__':
    main()