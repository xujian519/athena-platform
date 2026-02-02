#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断专利处理缓慢问题
作者：小娜
日期：2025-12-07
"""

import logging
import os
import time
from pathlib import Path

import psutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def diagnose_performance():
    """诊断性能问题"""
    logger.info('=== 专利处理性能诊断 ===')

    # 1. CPU核心和进程数检查
    cpu_count = psutil.cpu_count()
    processes = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent', 'io_counters']):
        try:
            if proc.info['cmdline'] and 'process_all_patents_layered.py' in ' '.join(proc.info['cmdline']):
                processes.append(proc)
        except:
            continue

    logger.info(f"\n1. CPU和进程分析:")
    logger.info(f"   CPU核心数: {cpu_count}")
    logger.info(f"   专利处理进程数: {len(processes)}")
    logger.info(f"   理想进程数: {cpu_count - 1}")

    if len(processes) > cpu_count:
        logger.warning(f"   ⚠️  进程数超过CPU核心数，可能导致上下文切换开销")

    total_cpu = sum(p.cpu_percent() for p in processes)
    logger.info(f"   总CPU使用率: {total_cpu:.1f}%")
    logger.info(f"   平均每进程: {total_cpu/len(processes):.1f}%' if processes else '0")

    # 2. 内存使用分析
    logger.info(f"\n2. 内存使用分析:")
    total_memory = psutil.virtual_memory().total / 1024**3  # GB
    used_memory = psutil.virtual_memory().used / 1024**3  # GB

    logger.info(f"   总内存: {total_memory:.1f} GB")
    logger.info(f"   已使用: {used_memory:.1f} GB ({used_memory/total_memory*100:.1f}%)")

    proc_memory = sum(p.memory_info().rss / 1024**2 for p in processes)  # MB
    logger.info(f"   处理进程内存: {proc_memory:.1f} MB")
    if processes:
        logger.info(f"   每进程平均: {proc_memory/len(processes):.1f} MB")
    else:
        logger.info('   每进程平均: 0 MB')

    # 3. I/O分析（如果可用）
    logger.info(f"\n3. I/O分析:")
    io_processes = []
    for p in processes:
        try:
            io = p.io_counters()
            if io and (io.read_bytes > 0 or io.write_bytes > 0):
                io_processes.append({
                    'pid': p.pid,
                    'read_mb': io.read_bytes / 1024**2,
                    'write_mb': io.write_bytes / 1024**2
                })
        except:
            continue

    if io_processes:
        total_read = sum(p['read_mb'] for p in io_processes)
        total_write = sum(p['write_mb'] for p in io_processes)
        logger.info(f"   总读取: {total_read:.1f} MB")
        logger.info(f"   总写入: {total_write:.1f} MB")
    else:
        logger.warning('   无法获取I/O统计')

    # 4. 文件系统检查
    logger.info(f"\n4. 文件系统分析:")
    source_dir = Path('/Users/xujian/学习资料/专利')
    output_dir = Path('/Users/xujian/Athena工作平台/data/patent_knowledge_graph')

    # 统计文件
    doc_count = len(list(source_dir.rglob('*.doc')))
    docx_count = len(list(source_dir.rglob('*.docx')))
    output_count = 0

    if output_dir.exists():
        output_count = len(list(output_dir.rglob('*.json')))

    logger.info(f"   源文件数: {doc_count + docx_count:,} (.doc: {doc_count}, .docx: {docx_count})")
    logger.info(f"   输出文件数: {output_count:,}")
    logger.info(f"   处理进度: {(output_count / (doc_count + docx_count) * 100):.2f}%' if (doc_count + docx_count) > 0 else '0%")

    # 5. 建议
    logger.info(f"\n5. 性能优化建议:")

    # CPU相关
    if total_cpu < (cpu_count - 1) * 50:
        logger.info('   📈 CPU利用率不足，建议:')
        logger.info('      - 增加并行处理进程数')
        logger.info('      - 检查是否存在算法瓶颈')

    # 内存相关
    if proc_memory > used_memory * 0.7:
        logger.warning('   🔴 内存使用过高，建议:')
        logger.warning('      - 减少批处理大小')
        logger.warning('      - 增加系统交换空间')

    # 进程数相关
    if len(processes) < cpu_count // 2:
        logger.info('   🚀 建议增加并行度:')
        logger.info(f"      - 当前: {len(processes)} 个进程")
        logger.info(f"      - 建议: {cpu_count // 2} 个进程")

    # I/O相关
    if io_processes:
        avg_read = sum(p['read_mb'] for p in io_processes) / len(io_processes)
        if avg_read < 1:  # 每个进程读取小于1MB/s
            logger.warning('   ⚠️  I/O吞吐量可能过低，检查:')
            logger.warning('      - 磁盘是否为SSD')
            logger.warning('      - 是否有网络文件系统')
            logger.warning('      - 文件是否被其他程序锁定')

    # 6. 实时监控建议
    logger.info(f"\n6. 实时监控命令:")
    logger.info('   查看进程: ps aux | grep process_all_patents_layered')
    logger.info('   监控CPU: top -o cpu')
    logger.info('   监控内存: top -o mem')
    logger.info('   监控I/O: iotop (需安装)')

if __name__ == '__main__':
    diagnose_performance()