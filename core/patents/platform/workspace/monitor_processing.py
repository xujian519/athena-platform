#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利处理监控脚本
Patent Processing Monitor Script

实时监控专利文档处理进度
Real-time monitoring of patent document processing progress

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

def print_status(message, status='INFO'):
    """打印状态信息"""
    icons = {
        'INFO': 'ℹ️',
        'SUCCESS': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'PROGRESS': '🔄',
        'MILESTONE': '🎯'
    }
    timestamp = datetime.now().strftime('%H:%M:%S')
    logger.info(f"[{timestamp}] {icons.get(status, 'ℹ️')} {message}")

def find_processing_log():
    """查找处理日志文件"""
    log_files = list(Path('/Users/xujian/Athena工作平台/patent_workspace').glob('patent_full_processing_*.log'))
    if log_files:
        return sorted(log_files, key=lambda x: x.stat().st_mtime)[-1]  # 最新的日志文件
    return None

def monitor_processing():
    """监控处理进度"""
    logger.info('🔍 专利文档处理监控器')
    logger.info(str('='*50))
    logger.info('📝 监控目标: 57,218个专利文档处理进度')
    logger.info('⏰ 预计完成时间: 5-8小时')
    logger.info(str('='*50))

    log_file = find_processing_log()
    if not log_file:
        print_status('未找到处理日志文件', 'WARNING')
        return

    print_status(f"监控日志文件: {log_file.name}', 'INFO")

    # 读取日志的文件位置
    last_position = 0

    while True:
        try:
            # 检查进程是否还在运行
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if 'process_all_patents.py' not in result.stdout:
                print_status('处理进程已结束', 'INFO')
                break

            # 读取新的日志内容
            with open(log_file, 'r', encoding='utf-8') as f:
                f.seek(last_position)
                new_lines = f.readlines()
                last_position = f.tell()

            # 显示新的日志内容
            for line in new_lines:
                line = line.strip()
                if line:
                    # 特别处理进度信息
                    if '进度:' in line or 'MILESTONE' in line or 'SUCCESS' in line or 'ERROR' in line:
                        print_status(line, 'PROGRESS' if '进度:' in line else 'INFO')
                    else:
                        logger.info(f"  {line}")

            # 等待一段时间再检查
            time.sleep(10)

        except KeyboardInterrupt:
            print_status('监控被用户中断', 'INFO')
            break
        except Exception as e:
            print_status(f"监控异常: {str(e)}', 'ERROR")
            time.sleep(5)

def show_processing_summary():
    """显示处理摘要"""
    logger.info(f"\n📊 处理摘要")
    logger.info(str('='*50))

    # 检查输出目录
    output_dir = Path('/tmp/patent_full_output')
    if output_dir.exists():
        files = list(output_dir.glob('*'))
        logger.info(f"输出目录: {output_dir}")
        logger.info(f"文件数量: {len(files)}")

        for file in sorted(files):
            size = file.stat().st_size
            size_mb = size / (1024 * 1024)
            logger.info(f"  📄 {file.name}: {size_mb:.1f}MB")

    # 检查Neo4j状态
    try:
        import requests
        response = requests.get('http://localhost:7474', timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ Neo4j Web界面可访问: http://localhost:7474")
    except:
        logger.info(f"⚠️ Neo4j Web界面不可访问")

    logger.info(f"\n💡 有用的查询:")
    logger.info(f"1. 查看节点总数: MATCH (n) RETURN count(n)")
    logger.info(f"2. 查看节点类型: MATCH (n) RETURN labels(n)[0], count(n)")
    logger.info(f"3. 查看关系总数: MATCH ()-[r]->() RETURN count(r)")

def main():
    """主函数"""
    monitor_processing()
    show_processing_summary()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 监控被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.info(f"❌ 监控异常: {e}")
        sys.exit(1)