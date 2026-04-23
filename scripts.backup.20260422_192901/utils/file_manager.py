#!/usr/bin/env python3
"""
文件管理工具
提供文件操作、备份、同步等功能
"""

import os
import shutil
import hashlib
import gzip
import json
import time
from typing import List, Optional, Dict, Tuple, Generator
from pathlib import Path
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

from core.config import config
from utils.logger import ScriptLogger
from utils.progress_tracker import ProgressTracker


@dataclass
class FileInfo:
    """文件信息"""
    path: str
    size: int
    modified_time: datetime
    hash: str
    is_directory: bool = False


class FileManager:
    """文件管理器"""

    def __init__(self):
        self.logger = ScriptLogger("FileManager")

    def get_file_info(self, path: str) -> FileInfo:
        """获取文件信息"""
        try:
            stat = os.stat(path)
            is_dir = os.path.isdir(path)

            info = FileInfo(
                path=path,
                size=stat.st_size if not is_dir else 0,
                modified_time=datetime.fromtimestamp(stat.st_mtime),
                hash=self._calculate_hash(path) if not is_dir else "",
                is_directory=is_dir
            )

            return info

        except Exception as e:
            self.logger.error(f"获取文件信息失败 {path}: {e}")
            return None

    def _calculate_hash(self, path: str) -> str:
        """计算文件哈希值"""
        try:
            hash_md5 = hashlib.md5()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return ""

    def find_files(self, root_path: str, pattern: str = "*",
                   include_dirs: bool = False,
                   max_depth: int = None) -> Generator[str, None, None]:
        """查找文件"""
        try:
            root_path = Path(root_path).resolve()

            for item in root_path.glob(pattern):
                if item.is_file() or (include_dirs and item.is_dir()):
                    # 检查深度
                    if max_depth is not None:
                        depth = len(item.relative_to(root_path).parts)
                        if depth > max_depth:
                            continue

                    yield str(item)

        except Exception as e:
            self.logger.error(f"查找文件失败: {e}")

    def get_directory_size(self, path: str) -> int:
        """获取目录大小"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except:
                        pass
        except Exception as e:
            self.logger.error(f"计算目录大小失败 {path}: {e}")

        return total_size

    def get_directory_stats(self, path: str) -> Dict[str, int]:
        """获取目录统计信息"""
        stats = {
            'files': 0,
            'directories': 0,
            'size': 0,
            'largest_file': '',
            'largest_size': 0
        }

        try:
            for dirpath, dirnames, filenames in os.walk(path):
                stats['directories'] += len(dirnames)
                stats['files'] += len(filenames)

                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        size = os.path.getsize(filepath)
                        stats['size'] += size

                        if size > stats['largest_size']:
                            stats['largest_size'] = size
                            stats['largest_file'] = filepath
                    except:
                        pass

        except Exception as e:
            self.logger.error(f"获取目录统计失败 {path}: {e}")

        return stats

    def backup_file(self, source_path: str, backup_dir: str,
                   compress: bool = True,
                   keep_versions: int = 5) -> str | None:
        """备份文件"""
        try:
            source_path = Path(source_path)
            backup_dir = Path(backup_dir)
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"

            if compress:
                backup_name += '.gz'

            backup_path = backup_dir / backup_name

            # 执行备份
            if compress:
                with open(source_path, 'rb') as f_in:
                    with gzip.open(backup_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(source_path, backup_path)

            # 清理旧版本
            self._cleanup_old_backups(
                backup_dir,
                source_path.stem,
                keep_versions
            )

            self.logger.info(f"文件备份成功: {backup_path}")
            return str(backup_path)

        except Exception as e:
            self.logger.error(f"备份文件失败 {source_path}: {e}")
            return None

    def _cleanup_old_backups(self, backup_dir: Path, file_prefix: str,
                           keep_versions: int):
        """清理旧备份"""
        try:
            # 查找所有备份
            backups = []
            for file in backup_dir.glob(f"{file_prefix}_*"):
                if file.is_file():
                    backups.append((file.stat().st_mtime, file))

            # 按时间排序
            backups.sort(key=lambda x: x[0], reverse=True)

            # 删除多余的备份
            for _, backup_file in backups[keep_versions:]:
                backup_file.unlink()
                self.logger.debug(f"删除旧备份: {backup_file}")

        except Exception as e:
            self.logger.error(f"清理旧备份失败: {e}")

    def restore_file(self, backup_path: str, target_path: str) -> bool:
        """恢复文件"""
        try:
            backup_path = Path(backup_path)
            target_path = Path(target_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 检查是否是压缩文件
            if backup_path.suffix == '.gz':
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(target_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(backup_path, target_path)

            self.logger.info(f"文件恢复成功: {target_path}")
            return True

        except Exception as e:
            self.logger.error(f"恢复文件失败: {e}")
            return False

    def sync_directories(self, source: str, target: str,
                        exclude_patterns: Optional[List[str] = None,
                        delete_extra: bool = False) -> bool:
        """同步目录"""
        try:
            source = Path(source).resolve()
            target = Path(target).resolve()
            exclude_patterns = exclude_patterns or []

            # 确保目标目录存在
            target.mkdir(parents=True, exist_ok=True)

            tracker = ProgressTracker(100, "目录同步")

            # 1. 扫描源目录
            source_files = set()
            for item in source.rglob('*'):
                if item.is_file():
                    rel_path = item.relative_to(source)
                    if not self._should_exclude(rel_path, exclude_patterns):
                        source_files.add(rel_path)

            tracker.update(20, "源目录扫描完成")

            # 2. 同步文件
            synced = 0
            total_files = len(source_files)

            for rel_path in source_files:
                source_file = source / rel_path
                target_file = target / rel_path

                # 确保目标目录存在
                target_file.parent.mkdir(parents=True, exist_ok=True)

                # 检查是否需要更新
                need_update = (
                    not target_file.exists() or
                    source_file.stat().st_mtime > target_file.stat().st_mtime or
                    self._calculate_hash(str(source_file)) != self._calculate_hash(str(target_file))
                )

                if need_update:
                    shutil.copy2(source_file, target_file)

                synced += 1
                if total_files > 0:
                    tracker.update(70 * synced // total_files)

            tracker.update(90, "文件同步完成")

            # 3. 删除多余文件（如果启用）
            if delete_extra:
                target_files = set()
                for item in target.rglob('*'):
                    if item.is_file():
                        rel_path = item.relative_to(target)
                        if not self._should_exclude(rel_path, exclude_patterns):
                            target_files.add(rel_path)

                # 删除源目录中不存在的文件
                for rel_path in target_files:
                    if rel_path not in source_files:
                        (target / rel_path).unlink()
                        self.logger.debug(f"删除多余文件: {rel_path}")

            tracker.complete()
            self.logger.info(f"目录同步完成: {source} -> {target}")
            return True

        except Exception as e:
            self.logger.error(f"同步目录失败: {e}")
            return False

    def _should_exclude(self, path: Path, patterns: List[str]) -> bool:
        """检查是否应该排除"""
        path_str = str(path)

        for pattern in patterns:
            if pattern in path_str:
                return True

        return False

    def clean_directory(self, directory: str, days_old: int = 30,
                       dry_run: bool = False) -> Dict[str, int]:
        """清理目录中的旧文件"""
        try:
            directory = Path(directory)
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)

            stats = {
                'files_deleted': 0,
                'dirs_deleted': 0,
                'space_freed': 0
            }

            # 首先删除文件
            for item in directory.rglob('*'):
                if item.is_file() and item.stat().st_mtime < cutoff_time:
                    size = item.stat().st_size
                    if not dry_run:
                        item.unlink()
                    stats['files_deleted'] += 1
                    stats['space_freed'] += size

            # 然后删除空目录
            dirs = sorted(directory.rglob('*'), key=lambda x: len(x.parts), reverse=True)
            for item in dirs:
                if item.is_dir() and not any(item.iterdir()):
                    if not dry_run:
                        item.rmdir()
                    stats['dirs_deleted'] += 1

            return stats

        except Exception as e:
            self.logger.error(f"清理目录失败 {directory}: {e}")
            return {'files_deleted': 0, 'dirs_deleted': 0, 'space_freed': 0}

    def archive_directory(self, source: str, archive_path: str,
                         format: str = 'tar.gz') -> bool:
        """归档目录"""
        try:
            source = Path(source)
            archive_path = Path(archive_path)
            archive_path.parent.mkdir(parents=True, exist_ok=True)

            if format == 'tar.gz':
                shutil.make_archive(
                    str(archive_path.with_suffix('')),
                    'gztar',
                    str(source.parent),
                    source.name
                )
            elif format == 'zip':
                shutil.make_archive(
                    str(archive_path.with_suffix('')),
                    'zip',
                    str(source.parent),
                    source.name
                )
            else:
                raise ValueError(f"不支持的归档格式: {format}")

            self.logger.info(f"目录归档成功: {archive_path}")
            return True

        except Exception as e:
            self.logger.error(f"归档目录失败: {e}")
            return False


# 全局实例
file_manager = FileManager()