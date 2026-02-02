#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超级快速专利处理器
作者：小娜
日期：2025-12-07
"""

import gc
import hashlib
import json
import logging
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'documentation/logs/super_fast_patent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全局配置
SOURCE_DIR = '/Users/xujian/学习资料/专利'
OUTPUT_DIR = '/Users/xujian/Athena工作平台/data/patent_kg_superfast'
BATCH_SIZE = 500  # 每批500个文件
MAX_WORKERS = min(mp.cpu_count(), 24)  # 最多24个进程

def process_single_file(file_path):
    """处理单个文件（超快速版本）"""
    try:
        # 生成唯一ID
        file_hash = hashlib.md5(str(file_path, usedforsecurity=False).encode()).hexdigest()[:16]

        # 极简的专利信息提取
        patent_data = {
            'id': f"patent_{file_hash}",
            'source_file': str(file_path),
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'processed_time': datetime.now().isoformat()
        }

        # 从文件名提取基本信息
        filename = file_path.stem

        # 提取专利号（简化版）
        import re
        patent_numbers = re.findall(r'\d{13,}', filename)
        if patent_numbers:
            patent_data['patent_number'] = patent_numbers[0]

        # 提取类型
        if '无效' in filename:
            patent_data['type'] = 'invalidation'
        elif '复审' in filename:
            patent_data['type'] = 'reexamination'
        else:
            patent_data['type'] = 'unknown'

        # 生成简单的三元组
        triples = [
            {
                'subject': patent_data['id'],
                'predicate': 'has_type',
                'object': patent_data['type']
            },
            {
                'subject': patent_data['id'],
                'predicate': 'from_source',
                'object': str(file_path)
            }
        ]

        if 'patent_number' in patent_data:
            triples.append({
                'subject': patent_data['id'],
                'predicate': 'patent_number',
                'object': patent_data['patent_number']
            })

        return {
            'patent': patent_data,
            'triples': triples,
            'status': 'success'
        }

    except Exception as e:
        logger.error(f"处理失败 {file_path}: {e}")
        return {
            'patent': None,
            'triples': [],
            'status': 'error',
            'error': str(e)
        }

def process_batch(batch_files, batch_id):
    """处理一批文件"""
    start_time = time.time()
    results = {
        'batch_id': batch_id,
        'files_count': len(batch_files),
        'success_count': 0,
        'patents': [],
        'all_triples': [],
        'errors': []
    }

    logger.info(f"批次 {batch_id}: 开始处理 {len(batch_files)} 个文件")

    # 使用线程池处理I/O密集型任务
    with ThreadPoolExecutor(max_workers=min(100, len(batch_files))) as executor:
        futures = [executor.submit(process_single_file, f) for f in batch_files]

        for future in futures:
            try:
                result = future.result(timeout=30)
                if result['status'] == 'success':
                    results['success_count'] += 1
                    results['patents'].append(result['patent'])
                    results['all_triples'].extend(result['triples'])
                else:
                    results['errors'].append(result.get('error', 'Unknown error'))
            except Exception as e:
                results['errors'].append(str(e))

    # 保存批次结果
    output_file = Path(OUTPUT_DIR) / f"batch_{batch_id:04d}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    logger.info(f"批次 {batch_id} 完成: {results['success_count']}/{results['files_count']} 成功, "
              f"耗时 {elapsed:.2f}s, 速度 {results['files_count']/elapsed:.1f} 文件/秒")

    return results

def super_fast_processing():
    """超级快速处理主函数"""
    logger.info('启动超级快速专利处理器')
    logger.info(f"输出目录: {OUTPUT_DIR}")
    logger.info(f"源目录: {SOURCE_DIR}")

    # 查找所有文件
    all_files = []
    for ext in ['*.doc', '*.docx']:
        all_files.extend(Path(SOURCE_DIR).rglob(ext))

    total_files = len(all_files)
    logger.info(f"找到 {total_files:,} 个专利文档")

    if not all_files:
        logger.error('未找到专利文件')
        return

    # 预处理：创建内存映射（如果文件数量很多）
    logger.info('开始预处理文件列表...')

    # 分批
    batches = []
    for i in range(0, total_files, BATCH_SIZE):
        batch = all_files[i:i + BATCH_SIZE]
        batches.append((batch, i // BATCH_SIZE))

    total_batches = len(batches)
    logger.info(f"分成 {total_batches} 个批次，每批 {BATCH_SIZE} 个文件")
    logger.info(f"使用 {MAX_WORKERS} 个并行进程")

    # 创建输出目录
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # 主处理循环
    start_time = time.time()
    processed_files = 0
    total_patents = 0
    total_triples = 0

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有批次
        future_to_batch = {
            executor.submit(process_batch, batch, batch_id): batch_id
            for batch, batch_id in batches
        }

        # 处理完成的批次
        completed = 0
        for future in future_to_batch:
            batch_id = future_to_batch[future]
            try:
                result = future.result(timeout=300)  # 5分钟超时

                processed_files += result.get('success_count', 0)
                total_patents += len(result.get('patents', []))
                total_triples += len(result.get('all_triples', []))
                completed += 1

                # 进度报告
                progress = (completed / total_batches) * 100
                elapsed = time.time() - start_time
                speed = processed_files / elapsed if elapsed > 0 else 0
                eta = (total_files - processed_files) / speed if speed > 0 else 0

                logger.info(f"进度: {progress:.1f}% | "
                          f"已完成: {completed}/{total_batches} 批次 | "
                          f"速度: {speed:.1f} 文件/秒 | "
                          f"ETA: {eta/3600:.1f}小时")

                # 内存清理
                gc.collect()

            except Exception as e:
                logger.error(f"批次 {batch_id} 失败: {e}")

    # 最终统计
    total_time = time.time() - start_time

    logger.info('=' * 60)
    logger.info('超级快速处理完成！')
    logger.info(f"总耗时: {total_time/3600:.2f} 小时")
    logger.info(f"处理文件数: {processed_files:,}")
    logger.info(f"成功专利: {total_patents:,}")
    logger.info(f"三元组数: {total_triples:,}")
    logger.info(f"平均速度: {processed_files/total_time:.1f} 文件/秒")
    logger.info(f"输出目录: {OUTPUT_DIR}")
    logger.info('=' * 60)

    # 生成汇总报告
    summary = {
        'timestamp': datetime.now().isoformat(),
        'statistics': {
            'total_files': total_files,
            'processed_files': processed_files,
            'success_rate': f"{(processed_files/total_files*100):.2f}%",
            'total_patents': total_patents,
            'total_triples': total_triples,
            'processing_time': f"{total_time/3600:.2f} hours",
            'average_speed': f"{processed_files/total_time:.1f} files/sec"
        },
        'output_files': total_batches
    }

    with open(Path(OUTPUT_DIR) / 'summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary

if __name__ == '__main__':
    # 设置优化参数
    os.environ['PYTHONHASHSEED'] = '0'  # 确保哈希一致性
    os.environ['OMP_NUM_THREADS'] = '1'  # 避免OpenMP过度使用

    # 运行超级快速处理
    super_fast_processing()