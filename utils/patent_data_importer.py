#!/usr/bin/env python3
"""
专利数据导入工具
用于将大型CSV专利数据导入到Athena平台
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import os
import shutil
import sqlite3
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

def import_patent_data(source_path: str, target_dir: str = None) -> Any:
    """
    导入专利数据到Athena平台
    Args:
        source_path: 源文件路径
        target_dir: 目标目录
    """
    if target_dir is None:
        target_dir = '/Users/xujian/Athena工作平台/data/patents/raw'

    # 创建目标目录
    Path(target_dir).mkdir(parents=True, exist_ok=True)

    # 检查源文件
    source = Path(source_path)
    if not source.exists():
        logger.info(f"❌ 源文件不存在: {source_path}")
        return False

    # 获取文件信息
    file_size = source.stat().st_size
    file_size_gb = file_size / (1024**3)

    logger.info(f"📁 源文件: {source_path}")
    logger.info(f"📊 文件大小: {file_size_gb:.2f} GB")

    # 如果文件太大，询问是否继续
    if file_size_gb > 50:
        logger.info("\n⚠️  文件较大，导入可能需要一些时间...")
        response = input('是否继续？(y/n): ')
        if response.lower() != 'y':
            return False

    # 复制文件
    target_path = Path(target_dir) / source.name
    logger.info(f"\n📥 复制到: {target_path}")

    try:
        # 使用shutil复制大文件
        shutil.copy2(source, target_path)
        logger.info(f"✅ 复制完成")

        # 预览文件结构
        logger.info(f"\n📋 预览文件结构...")
        preview_csv_structure(target_path)

        return True

    except Exception as e:
        logger.info(f"❌ 复制失败: {e}")
        return False

def preview_csv_structure(csv_path: str, sample_rows: int = 5) -> Any:
    """预览CSV结构"""
    try:
        # 尝试不同编码
        for encoding in ['utf-8', 'gbk', 'gb18030']:
            try:
                # 读取前几行
                df = pd.read_csv(csv_path, encoding=encoding, nrows=sample_rows)
                logger.info(f"✅ 编码: {encoding}")
                logger.info(f"📊 总列数: {len(df.columns)}")
                logger.info(f"📊 预计总行数: {_estimate_row_count(csv_path)}")
                logger.info(f"\n列名:")
                for i, col in enumerate(df.columns, 1):
                    logger.info(f"  {i}. {col}")

                logger.info(f"\n数据示例:")
                logger.info(str(df.head(sample_rows)).to_string())
                break
            except:
                continue
    except Exception as e:
        logger.info(f"❌ 无法预览: {e}")

def _estimate_row_count(csv_path: str) -> int:
    """估算CSV行数"""
    try:
        # 计算文件大小和单行大小比例
        with open(csv_path, 'rb') as f:
            # 读取第一行确定行大小
            first_line = f.readline()
            if first_line:
                file_size = os.path.getsize(csv_path)
                avg_row_size = len(first_line)
                estimated_rows = int(file_size / avg_row_size)
                return estimated_rows
    except:
        return 0

def main() -> None:
    """主函数"""
    logger.info(str('='*60))
    logger.info('📦 专利数据导入工具')
    logger.info(str('='*60))

    # 用户输入路径
    source_path = input("\n请输入专利CSV文件路径: ").strip()

    # 移除引号
    if source_path.startswith('"') and source_path.endswith('"'):
        source_path = source_path[1:-1]

    # 标准化路径
    if not source_path.startswith('/'):
        # 相对路径，转换为绝对路径
        source_path = os.path.abspath(os.path.expanduser(source_path))

    logger.info(f"\n🔍 查找文件: {source_path}")

    # 导入数据
    success = import_patent_data(source_path)

    if success:
        logger.info("\n✅ 导入成功！")
        logger.info("\n下一步:")
        logger.info('1. 运行以下命令建立索引:')
        logger.info('   python3 /Users/xujian/Athena工作平台/services/enhanced_patent_search.py')
        logger.info('2. 数据将自动导入到SQLite索引数据库')
        logger.info('3. 之后可以使用本地检索功能')
    else:
        logger.info("\n❌ 导入失败")
        logger.info("\n请检查:")
        logger.info('1. 文件路径是否正确')
        logger.info('2. 文件是否有读取权限')
        logger.info('3. 磁盘空间是否充足')

if __name__ == '__main__':
    main()