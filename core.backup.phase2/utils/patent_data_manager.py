#!/usr/bin/env python3
from __future__ import annotations
"""
专利数据管理工具
用于管理源数据、索引数据和缓存
"""

import json
import logging
import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

class PatentDataManager:
    """专利数据管理器"""

    def __init__(self):
        self.base_path = Path('/Users/xujian/Athena工作平台/data/patents')
        self.raw_path = self.base_path / 'raw'
        self.processed_path = self.base_path / 'processed'
        self.backup_path = self.base_path / 'backup'
        self.cache_path = self.base_path / 'cache'

        # 确保目录存在
        self.backup_path.mkdir(parents=True, exist_ok=True)

    def check_storage_usage(self) -> bool:
        """检查存储使用情况"""
        logger.info(str('='*60))
        logger.info('📊 专利数据存储使用情况')
        logger.info(str('='*60))

        total_size = 0
        usage_info = {}

        # 检查各目录
        directories = [
            ('源数据', self.raw_path),
            ('索引数据', self.processed_path),
            ('缓存数据', self.cache_path),
            ('备份数据', self.backup_path)
        ]

        for name, path in directories:
            if path.exists():
                size = self._get_dir_size(path)
                usage_info[name] = {
                    'path': str(path),
                    'size': size,
                    'size_gb': size / (1024**3)
                }
                total_size += size
                logger.info(f"\n{name}: {path}")
                logger.info(f"  大小: {size / (1024**3):.2f} GB")
                logger.info(f"  文件数: {self._count_files(path)}")

        logger.info(f"\n总计: {total_size / (1024**3):.2f} GB")

        # 磁盘空间检查
        disk_usage = shutil.disk_usage(self.base_path)
        free_space = disk_usage.free
        total_space = disk_usage.total

        logger.info("\n💾 磁盘空间:")
        logger.info(f"  总容量: {total_space / (1024**3):.1f} GB")
        logger.info(f"  已使用: {(total_space - free_space) / (1024**3):.1f} GB")
        logger.info(f"  剩余空间: {free_space / (1024**3):.1f} GB")
        logger.info(f"  使用率: {(1 - free_space/total_space)*100:.1f}%")

        return usage_info, total_size, free_space

    def archive_raw_data(self) -> Any:
        """归档源数据"""
        logger.info("\n📦 开始归档源数据...")

        # 查找源数据文件
        raw_files = list(self.raw_path.glob('*.csv'))
        if not raw_files:
            logger.info('⚠️  未找到源数据文件')
            return

        for csv_file in raw_files:
            # 创建归档文件名
            timestamp = datetime.now().strftime('%Y%m%d')
            archive_name = f"{csv_file.stem}_{timestamp}.tar.gz"
            archive_path = self.backup_path / archive_name

            # 如果归档已存在，跳过
            if archive_path.exists():
                logger.info(f"⏭️  归档已存在: {archive_name}")
                continue

            logger.info(f"🔒 归档: {csv_file.name}")

            # 创建tar.gz归档
            import tarfile
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(csv_file, arcname=csv_file.name)

            logger.info(f"✅ 归档完成: {archive_path}")
            logger.info(f"   大小: {archive_path.stat().st_size / (1024**3):.2f} GB")

    def clean_cache(self, older_than_days: int = 7) -> Any:
        """清理旧缓存"""
        logger.info(f"\n🧹 清理{older_than_days}天前的缓存...")

        cache_files = list(self.cache_path.rglob('*'))
        cleaned_count = 0
        cleaned_size = 0

        cutoff_time = time.time() - (older_than_days * 24 * 3600)

        for file_path in cache_files:
            if file_path.is_file():
                file_mtime = file_path.stat().st_mtime
                if file_mtime < cutoff_time:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    cleaned_count += 1
                    cleaned_size += file_size
                    logger.info(f"  删除: {file_path.name}")

        if cleaned_count > 0:
            logger.info("\n✅ 清理完成:")
            logger.info(f"  文件数: {cleaned_count}")
            logger.info(f"  释放空间: {cleaned_size / (1024**2):.1f} MB")
        else:
            logger.info('✅ 没有需要清理的缓存')

    def verify_integrity(self) -> bool:
        """验证数据完整性"""
        logger.info("\n🔍 验证数据完整性...")

        # 1. 检查索引数据库
        db_path = self.processed_path / 'indexed_patents.db'
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 检查专利数量
            cursor.execute('SELECT COUNT(*) FROM patents')
            patent_count = cursor.fetchone()[0]
            logger.info(f"✅ 索引专利数量: {patent_count:,}")

            # 检查索引状态
            cursor.execute('SELECT COUNT(*) FROM patents_fts')
            fts_count = cursor.fetchone()[0]
            logger.info(f"✅ 全文索引条数: {fts_count:,}")

            conn.close()
        else:
            logger.info('⚠️  索引数据库不存在')

        # 2. 检查源数据完整性
        csv_files = list(self.raw_path.glob('*.csv'))
        for csv_file in csv_files:
            try:
                # 快速检查文件是否可读
                pd.read_csv(csv_file, nrows=1)
                logger.info(f"✅ {csv_file.name}: 可正常读取")
            except Exception as e:
                logger.info(f"❌ {csv_file.name}: 读取失败 - {e}")

    def compress_old_backups(self, days_threshold: int = 30) -> Any:
        """压缩旧备份"""
        logger.info(f"\n🗜️ 压缩{days_threshold}天前的备份...")

        # 找到旧的备份文件（非压缩的）
        for backup_file in self.backup_path.glob('*.csv'):
            file_age = (datetime.now() - datetime.fromtimestamp(
                backup_file.stat().st_mtime)).days

            if file_age > days_threshold:
                # 压缩为.gz
                compressed_name = backup_file.with_suffix('.csv.gz')
                if not compressed_name.exists():
                    logger.info(f"🔒 压缩: {backup_file.name}")

                    # 使用gzip压缩
                    import gzip
                    with open(backup_file, 'rb') as f_in:
                        with gzip.open(compressed_name, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    # 删除原文件
                    backup_file.unlink()
                    logger.info(f"   压缩率: {compressed_name.stat().st_size / backup_file.stat().st_size * 100:.1f}%")

    def generate_report(self) -> Any:
        """生成数据管理报告"""
        logger.info("\n📊 生成数据管理报告...")

        report = {
            'timestamp': datetime.now().isoformat(),
            'storage_usage': {},
            'recommendations': []
        }

        # 检查存储使用
        usage_info, total_size, free_space = self.check_storage_usage()
        report['storage_usage'] = {
            name: {
                'path': info['path'],
                'size_gb': info['size_gb'],
                'file_count': self._count_files(Path(info['path']))
            }
            for name, info in usage_info.items()
        }

        # 生成建议
        free_space_gb = free_space / (1024**3)
        raw_size_gb = usage_info.get('源数据', {}).get('size_gb', 0)

        if free_space_gb < 20:
            report['recommendations'].append('磁盘空间不足，建议清理缓存或归档源数据')

        if raw_size_gb > 50:
            report['recommendations'].append('源数据较大，建议归档后删除')

        # 保存报告
        report_file = self.base_path / f"data_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"\n✅ 报告已保存: {report_file}")
        return report

    def _get_dir_size(self, path: Path) -> int:
        """获取目录大小"""
        total_size = 0
        for entry in path.rglob('*'):
            if entry.is_file():
                total_size += entry.stat().st_size
        return total_size

    def _count_files(self, path: Path) -> int:
        """计算文件数量"""
        return len(list(path.rglob('*')))

    def interactive_menu(self) -> Any:
        """交互式菜单"""
        while True:
            logger.info(str("\n" + '='*60))
            logger.info('🔧 专利数据管理工具')
            logger.info(str('='*60))
            logger.info('1. 检查存储使用情况')
            logger.info('2. 归档源数据')
            logger.info('3. 清理缓存')
            logger.info('4. 验证数据完整性')
            logger.info('5. 压缩旧备份')
            logger.info('6. 生成管理报告')
            logger.info('0. 退出')
            logger.info(str('='*60))

            choice = input("\n请选择操作 (0-6): ").strip()

            if choice == '0':
                logger.info("\n👋 再见！")
                break
            elif choice == '1':
                self.check_storage_usage()
            elif choice == '2':
                self.archive_raw_data()
            elif choice == '3':
                days = input('清理多少天前的缓存？(默认7): ').strip()
                days = int(days) if days else 7
                self.clean_cache(days)
            elif choice == '4':
                self.verify_integrity()
            elif choice == '5':
                days = input('压缩多少天前的备份？(默认30): ').strip()
                days = int(days) if days else 30
                self.compress_old_backups(days)
            elif choice == '6':
                self.generate_report()
            else:
                logger.info("\n❌ 无效选择，请重试")

            input("\n按回车继续...")


# 使用示例
if __name__ == '__main__':
    manager = PatentDataManager()
    manager.interactive_menu()
