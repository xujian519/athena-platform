#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台统一备份管理器
Unified Backup Manager for Athena Work Platform

提供全面的数据备份、恢复和管理功能

使用方法:
python3 backup_manager.py --backup
python3 backup_manager.py --restore --date 20251208
python3 backup_manager.py --list
python3 backup_manager.py --cleanup

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import argparse
import gzip
import json
import logging
import os
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

class BackupManager:
    """统一备份管理器"""

    def __init__(self):
        self.project_root = project_root
        self.backup_dir = self.project_root / 'backups'
        self.data_dir = self.project_root / 'data'
        self.config_dir = self.project_root / 'config'
        self.logs_dir = self.project_root / 'logs'

        # 确保备份目录存在
        self.backup_dir.mkdir(exist_ok=True)

        # 日志配置
        self.setup_logging()

        # 备份配置
        self.backup_config = {
            'include_patterns': [
                'data/**/*.json',
                'data/**/*.db',
                'data/**/*.sqlite',
                'config/**/*.yaml',
                'config/**/*.json',
                'documentation/logs/**/*.log',
                'scripts/**/*.py',
                'core/**/*.py',
                'services/**/*.py'
            ],
            'exclude_patterns': [
                '**/__pycache__/**',
                '**/node_modules/**',
                '**/.git/**',
                '**/*.pyc',
                '**/tmp/**',
                '**/temp/**',
                '**/.DS_Store',
                '**/documentation/logs/**/tmp/**'
            ],
            'compression_level': 6,
            'retention_days': 30,
            'max_backup_size_gb': 10
        }

    def setup_logging(self):
        """设置日志"""
        log_file = self.logs_dir / 'backup_manager.log'
        log_file.parent.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def create_backup(self, backup_type: str = 'full') -> str:
        """创建备份"""
        self.logger.info(f"开始创建 {backup_type} 类型备份...")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"athena_backup_{backup_type}_{timestamp}"
        backup_file = self.backup_dir / f"{backup_name}.tar.gz"

        try:
            # 收集要备份的文件
            files_to_backup = self._collect_backup_files(backup_type)

            if not files_to_backup:
                self.logger.warning('没有找到需要备份的文件')
                return ''

            # 创建备份
            with tarfile.open(backup_file, 'w:gz') as tar:
                for file_path in files_to_backup:
                    try:
                        # 使用相对路径存储
                        arcname = file_path.relative_to(self.project_root)
                        tar.add(file_path, arcname=arcname)
                    except Exception as e:
                        self.logger.warning(f"跳过文件 {file_path}: {e}")

            # 验证备份
            backup_size = backup_file.stat().st_size
            self.logger.info(f"备份创建完成: {backup_file}")
            self.logger.info(f"备份大小: {self._format_size(backup_size)}")
            self.logger.info(f"包含文件数: {len(files_to_backup)}")

            # 创建备份元数据
            self._create_backup_metadata(backup_name, backup_type, files_to_backup)

            return str(backup_file)

        except Exception as e:
            self.logger.error(f"备份创建失败: {e}")
            # 清理失败的备份文件
            if backup_file.exists():
                backup_file.unlink()
            return ''

    def _collect_backup_files(self, backup_type: str) -> List[Path]:
        """收集要备份的文件"""
        files = []
        include_patterns = self.backup_config['include_patterns']
        exclude_patterns = self.backup_config['exclude_patterns']

        # 根据备份类型确定要包含的目录
        if backup_type == 'full':
            search_dirs = [self.data_dir, self.config_dir, self.logs_dir]
        elif backup_type == 'data':
            search_dirs = [self.data_dir]
        elif backup_type == 'config':
            search_dirs = [self.config_dir]
        elif backup_type == 'logs':
            search_dirs = [self.logs_dir]
        else:
            search_dirs = [self.project_root]

        # 收集文件
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # 递归查找所有文件，然后进行模式匹配
            for file_path in search_dir.rglob('*'):
                if not file_path.is_file():
                    continue

                # 检查是否应该排除
                should_exclude = False
                for exclude_pattern in exclude_patterns:
                    if file_path.match(exclude_pattern):
                        should_exclude = True
                        break

                if should_exclude:
                    continue

                # 检查文件扩展名是否匹配包含模式
                should_include = False
                file_ext = file_path.suffix.lower()

                for include_pattern in include_patterns:
                    if file_ext == '.json' and 'json' in include_pattern:
                        should_include = True
                        break
                    elif file_ext == '.db' and 'db' in include_pattern:
                        should_include = True
                        break
                    elif file_ext == '.sqlite' and 'sqlite' in include_pattern:
                        should_include = True
                        break
                    elif file_ext == '.yaml' and 'yaml' in include_pattern:
                        should_include = True
                        break
                    elif file_ext == '.log' and 'log' in include_pattern:
                        should_include = True
                        break
                    elif file_ext == '.py' and 'py' in include_pattern:
                        should_include = True
                        break

                if should_include:
                    files.append(file_path)

        return files

    def _create_backup_metadata(self, backup_name: str, backup_type: str, files: List[Path]):
        """创建备份元数据"""
        metadata = {
            'backup_name': backup_name,
            'backup_type': backup_type,
            'created_at': datetime.now().isoformat(),
            'created_by': 'Athena Backup Manager v1.0.0',
            'total_files': len(files),
            'total_size': sum(f.stat().st_size for f in files if f.exists()),
            'file_list': [str(f.relative_to(self.project_root)) for f in files],
            'config': self.backup_config
        }

        metadata_file = self.backup_dir / f"{backup_name}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        self.logger.info('列出所有备份...')

        backups = []

        for backup_file in self.backup_dir.glob('athena_backup_*.tar.gz'):
            metadata_file = backup_file.with_suffix('.json')

            backup_info = {
                'name': backup_file.name,
                'path': str(backup_file),
                'size': backup_file.stat().st_size,
                'created': datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                'metadata': None
            }

            # 读取元数据
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        backup_info['metadata'] = json.load(f)
                except Exception as e:
                    self.logger.warning(f"无法读取备份元数据 {metadata_file}: {e}")

            backups.append(backup_info)

        # 按创建时间排序
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups

    def restore_backup(self, backup_name: str, target_dir: str | None = None) -> bool:
        """恢复备份"""
        self.logger.info(f"开始恢复备份: {backup_name}")

        backup_file = self.backup_dir / backup_name
        if not backup_file.exists():
            backup_file = self.backup_dir / f"{backup_name}.tar.gz"

        if not backup_file.exists():
            self.logger.error(f"备份文件不存在: {backup_name}")
            return False

        try:
            # 确定恢复目录
            if target_dir:
                restore_dir = Path(target_dir)
            else:
                restore_dir = self.project_root

            restore_dir.mkdir(parents=True, exist_ok=True)

            # 解压备份
            with tarfile.open(backup_file, 'r:gz') as tar:
                tar.extractall(path=restore_dir)

            self.logger.info(f"备份恢复完成到: {restore_dir}")
            return True

        except Exception as e:
            self.logger.error(f"备份恢复失败: {e}")
            return False

    def cleanup_old_backups(self, days: int | None = None) -> int:
        """清理旧备份"""
        if days is None:
            days = self.backup_config['retention_days']

        self.logger.info(f"清理 {days} 天前的备份...")

        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for backup_file in self.backup_dir.glob('athena_backup_*.tar.gz'):
            if datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff_date:
                try:
                    backup_file.unlink()
                    # 同时删除元数据文件
                    metadata_file = backup_file.with_suffix('.json')
                    if metadata_file.exists():
                        metadata_file.unlink()
                    deleted_count += 1
                    self.logger.info(f"删除旧备份: {backup_file.name}")
                except Exception as e:
                    self.logger.warning(f"删除备份失败 {backup_file}: {e}")

        self.logger.info(f"清理完成，删除了 {deleted_count} 个旧备份")
        return deleted_count

    def verify_backup(self, backup_name: str) -> Dict[str, Any]:
        """验证备份完整性"""
        self.logger.info(f"验证备份完整性: {backup_name}")

        backup_file = self.backup_dir / backup_name
        if not backup_file.exists():
            backup_file = self.backup_dir / f"{backup_name}.tar.gz"

        if not backup_file.exists():
            return {'valid': False, 'error': '备份文件不存在'}

        verification_result = {
            'backup_name': backup_name,
            'valid': True,
            'file_exists': True,
            'file_size': backup_file.stat().st_size,
            'created': datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
            'metadata_valid': False,
            'file_count': 0,
            'issues': []
        }

        # 检查元数据
        metadata_file = backup_file.with_suffix('.json')
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                verification_result['metadata_valid'] = True
                verification_result['file_count'] = metadata.get('total_files', 0)

                # 验证文件列表
                file_list = metadata.get('file_list', [])
                missing_files = []
                for file_path_str in file_list:
                    file_path = self.project_root / file_path_str
                    if not file_path.exists():
                        missing_files.append(file_path_str)

                if missing_files:
                    verification_result['valid'] = False
                    verification_result['issues'].append(f"缺失文件: {len(missing_files)}个")

            except Exception as e:
                verification_result['issues'].append(f"元数据读取失败: {e}")
                verification_result['metadata_valid'] = False

        # 尝试验证压缩包完整性
        try:
            with tarfile.open(backup_file, 'r:gz') as tar:
                tar.getmembers()
        except Exception as e:
            verification_result['valid'] = False
            verification_result['issues'].append(f"压缩包损坏: {e}")

        return verification_result

    def get_backup_stats(self) -> Dict[str, Any]:
        """获取备份统计信息"""
        backups = self.list_backups()
        total_size = sum(b['size'] for b in backups)

        stats = {
            'total_backups': len(backups),
            'total_size': total_size,
            'total_size_gb': round(total_size / (1024**3), 2),
            'oldest_backup': None,
            'newest_backup': None,
            'backup_types': {}
        }

        if backups:
            stats['oldest_backup'] = min(b['created'] for b in backups)
            stats['newest_backup'] = max(b['created'] for b in backups)

            # 统计备份类型
            for backup in backups:
                if backup['metadata']:
                    backup_type = backup['metadata'].get('backup_type', 'unknown')
                    if backup_type not in stats['backup_types']:
                        stats['backup_types'][backup_type] = 0
                    stats['backup_types'][backup_type] += 1

        return stats

    def schedule_automatic_backup(self):
        """调度自动备份"""
        # 这里可以集成到系统的定时任务中
        # 例如使用 cron 或 systemd timer
        self.logger.info('建议设置定时任务执行自动备份')
        self.logger.info('示例 crontab:')
        self.logger.info('0 2 * * * cd /Users/xujian/Athena工作平台 && python3 scripts/system_operations/backup_manager.py --backup')

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def print_backup_list(self, backups: List[Dict[str, Any]]):
        """打印备份列表"""
        if not backups:
            logger.info('📭 没有找到备份文件')
            return

        logger.info(f"\n📋 Athena工作平台备份列表")
        logger.info(f"🕐 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📊 备份总数: {len(backups)}")

        logger.info(f"\n{'名称':<40} {'类型':<10} {'大小':<12} {'创建时间':<20}")
        logger.info(str('-' * 85))

        for backup in backups:
            name = backup['name'][:37] + '...' if len(backup['name']) > 40 else backup['name']
            metadata = backup.get('metadata') or {}
            backup_type = metadata.get('backup_type', 'unknown')
            size_str = self._format_size(backup['size'])
            created_time = backup['created'][:19]

            logger.info(f"{name:<40} {backup_type:<10} {size_str:<12} {created_time:<20}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Athena备份管理器')
    parser.add_argument('--backup', action='store_true', help='创建完整备份')
    parser.add_argument('--backup-type', choices=['full', 'data', 'config', 'logs'], default='full', help='备份类型')
    parser.add_argument('--restore', help='恢复指定备份')
    parser.add_argument('--list', action='store_true', help='列出所有备份')
    parser.add_argument('--verify', help='验证指定备份')
    parser.add_argument('--cleanup', type=int, nargs='?', const=None, help='清理旧备份')
    parser.add_argument('--stats', action='store_true', help='显示备份统计')
    parser.add_argument('--schedule', action='store_true', help='显示自动备份调度建议')

    args = parser.parse_args()

    manager = BackupManager()

    if args.backup or not any(vars(args).values()):
        # 默认执行备份
        backup_file = manager.create_backup(args.backup_type)
        if backup_file:
            logger.info(f"✅ 备份创建成功: {backup_file}")

    elif args.list:
        backups = manager.list_backups()
        manager.print_backup_list(backups)

    elif args.restore:
        success = manager.restore_backup(args.restore)
        if success:
            logger.info('✅ 备份恢复成功')

    elif args.verify:
        result = manager.verify_backup(args.verify)
        logger.info(f"✅ 备份验证结果:")
        logger.info(f"  备份名称: {result['backup_name']}")
        logger.info(f"  有效性: {'✅ 有效' if result['valid'] else '❌ 无效'}")
        logger.info(f"  文件大小: {manager._format_size(result['file_size'])}")
        logger.info(f"  文件数量: {result['file_count']}")
        if result['issues']:
            logger.info(f"  ⚠️ 问题: {'; '.join(result['issues'])}")

    elif args.cleanup is not None:
        days = args.cleanup if args.cleanup is not None else manager.backup_config['retention_days']
        deleted_count = manager.cleanup_old_backups(days)
        logger.info(f"✅ 清理完成，删除了 {deleted_count} 个旧备份")

    elif args.stats:
        stats = manager.get_backup_stats()
        logger.info(f"📊 备份统计信息:")
        logger.info(f"  备份总数: {stats['total_backups']}")
        logger.info(f"  总大小: {stats['total_size_gb']} GB")
        logger.info(f"  最新备份: {stats['newest_backup']}")
        logger.info(f"  最早备份: {stats['oldest_backup']}")
        logger.info(f"  备份类型:")
        for backup_type, count in stats['backup_types'].items():
            logger.info(f"    {backup_type}: {count} 个")

    elif args.schedule:
        manager.schedule_automatic_backup()

if __name__ == '__main__':
    main()