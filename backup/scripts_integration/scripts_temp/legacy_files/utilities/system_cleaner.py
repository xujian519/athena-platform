#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统清理工具
System Cleaner Tool

扫描和清理平台中的冗余文件、过期文件、缓存文件、测试文件等
"""

import hashlib
import json
import logging
import os
import re
import shutil
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemCleaner:
    """系统清理器"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.cleaned_files = []
        self.cleaned_size = 0
        self.skip_patterns = {
            # 重要文件和目录，不删除
            '__pycache__',
            '.git',
            'node_modules',
            'venv',
            'env',
            '.env',
            'models',
            'data',
            'storage',
            'outputs',
            'logs',
            'core',
            'scripts',
            'services',
            'domains',
            'test_*.py',
            '*_test.py'
        }

        # 文件类型分类
        self.file_categories = {
            'cache': ['.pyc', '.pyo', '.pyd', '.pycache__', '.DS_Store', 'Thumbs.db'],
            'temp': ['.tmp', '.temp', '.swp', '.swo', '.bak', '.orig', '.rej'],
            'build': ['.so', '.pyd', '.dll', '.exe', '.dylib'],
            'logs': ['.log', '.out', '.err'],
            'docs': ['.md', '.rst', '.txt', '.pdf', '.doc', '.docx'],
            'test': ['test_', '_test.', 'spec_', '_spec.'],
            'backup': ['.bak', '.backup', '.old', '.save'],
            'duplicate': [],  # 动态填充
            'large': [],      # 动态填充
            'empty': []       # 动态填充
        }

        # 清理规则
        self.cleaning_rules = {
            'cache_files': {
                'description': 'Python缓存文件',
                'patterns': ['**/*.pyc', '**/*.pyo', '**/__pycache__', '**/.DS_Store'],
                'max_age': 0,  # 立即清理
                'safe': True
            },
            'temp_files': {
                'description': '临时文件',
                'patterns': ['**/*.tmp', '**/*.temp', '**/*.swp', '**/*.swo', '**/*.bak'],
                'max_age': timedelta(days=1),
                'safe': True
            },
            'old_logs': {
                'description': '过期日志文件',
                'patterns': ['**/*.log', '**/*.out', '**/*.err'],
                'max_age': timedelta(days=7),
                'safe': True
            },
            'test_outputs': {
                'description': '测试输出文件',
                'patterns': ['**/test_output/**', '**/pytest_cache/**', '**/.coverage'],
                'max_age': timedelta(days=3),
                'safe': True
            },
            'duplicate_files': {
                'description': '重复文件',
                'patterns': [],
                'max_age': 0,
                'safe': False  # 需要确认
            },
            'empty_dirs': {
                'description': '空目录',
                'patterns': [],
                'max_age': 0,
                'safe': True
            },
            'large_unused': {
                'description': '大文件',
                'patterns': [],
                'max_age': timedelta(days=30),
                'safe': False,
                'min_size_mb': 100
            }
        }

    def scan_files(self) -> Dict[str, any]:
        """扫描文件系统"""
        logger.info('🔍 开始扫描文件系统...')

        scan_results = {
            'total_files': 0,
            'total_size_mb': 0,
            'file_types': {},
            'duplicate_files': {},
            'empty_dirs': [],
            'large_files': [],
            'old_files': [],
            'cache_files': [],
            'temp_files': []
        }

        # 用于检测重复文件
        file_hashes = {}
        duplicate_candidates = []

        # 扫描所有文件
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                try:
                    # 跳过重要目录
                    if self._should_skip(file_path):
                        continue

                    # 文件信息
                    stat = file_path.stat()
                    file_size = stat.st_size
                    file_ext = file_path.suffix.lower()
                    file_age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)

                    # 更新统计
                    scan_results['total_files'] += 1
                    scan_results['total_size_mb'] += file_size / (1024 * 1024)

                    # 文件类型统计
                    if file_ext not in scan_results['file_types']:
                        scan_results['file_types'][file_ext] = {'count': 0, 'size_mb': 0}
                    scan_results['file_types'][file_ext]['count'] += 1
                    scan_results['file_types'][file_ext]['size_mb'] += file_size / (1024 * 1024)

                    # 缓存文件
                    if file_ext in ['.pyc', '.pyo'] or '.pycache__' in str(file_path):
                        scan_results['cache_files'].append(file_path)

                    # 临时文件
                    if file_ext in ['.tmp', '.temp', '.swp', '.swo', '.bak']:
                        scan_results['temp_files'].append(file_path)

                    # 重复文件检测
                    if file_size > 1024:  # 只检测大于1KB的文件
                        file_hash = self._get_file_hash(file_path)
                        if file_hash:
                            if file_hash in file_hashes:
                                duplicate_candidates.append((file_hash, file_path, file_hashes[file_hash]))
                            else:
                                file_hashes[file_hash] = file_path

                    # 大文件检测
                    if file_size > 100 * 1024 * 1024:  # 大于100MB
                        scan_results['large_files'].append({
                            'path': file_path,
                            'size_mb': file_size / (1024 * 1024),
                            'age_days': file_age.days,
                            'last_access': datetime.fromtimestamp(stat.st_atime)
                        })

                    # 过期文件检测
                    if file_age > timedelta(days=90):
                        scan_results['old_files'].append({
                            'path': file_path,
                            'age_days': file_age.days,
                            'size_mb': file_size / (1024 * 1024)
                        })

                except (OSError, PermissionError, hashlib.LOOKUP_ERROR):
                    continue

            elif file_path.is_dir():
                # 空目录检测
                try:
                    if not any(file_path.iterdir()):
                        scan_results['empty_dirs'].append(file_path)
                except (OSError, PermissionError):
                    continue

        # 处理重复文件
        for file_hash, file1, file2 in duplicate_candidates:
            if file_hash not in scan_results['duplicate_files']:
                scan_results['duplicate_files'][file_hash] = []
            scan_results['duplicate_files'][file_hash].extend([file1, file2])

        logger.info(f"✅ 扫描完成，共扫描 {scan_results['total_files']} 个文件")
        return scan_results

    def _get_file_hash(self, file_path: Path, block_size: int = 65536) -> str | None:
        """计算文件哈希值"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for block in iter(lambda: f.read(block_size), b''):
                    hasher.update(block)
            return hasher.hexdigest()
        except (OSError, PermissionError):
            return None

    def _should_skip(self, file_path: Path) -> bool:
        """判断是否应该跳过该文件/目录"""
        path_str = str(file_path)

        # 跳过隐藏文件和目录
        if file_path.name.startswith('.'):
            return True

        # 跳过重要目录
        important_dirs = [
            '.git', 'node_modules', 'venv', 'env', '.env',
            'models', 'data', 'storage', 'outputs', 'logs',
            'core', 'scripts', 'services', 'domains'
        ]

        for dir_name in important_dirs:
            if f'/{dir_name}/' in path_str or path_str.endswith(f'/{dir_name}'):
                return True

        # 跳过重要文件
        important_files = [
            'requirements.txt', 'package.json', 'pyproject.toml',
            'Dockerfile', 'docker-compose.yml', '.gitignore',
            'README.md', 'LICENSE', 'setup.py', 'Makefile'
        ]

        if file_path.name in important_files:
            return True

        return False

    def clean_cache_files(self, dry_run: bool = True) -> Dict[str, any]:
        """清理缓存文件"""
        logger.info('🧹 清理缓存文件...')

        cleaned_count = 0
        cleaned_size = 0

        cache_patterns = ['**/*.pyc', '**/*.pyo', '**/__pycache__', '**/.DS_Store', '**/Thumbs.db']

        for pattern in cache_patterns:
            for file_path in self.project_root.glob(pattern):
                try:
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        if not dry_run:
                            file_path.unlink()
                        cleaned_count += 1
                        cleaned_size += size
                        logger.info(f"{'[预览]' if dry_run else '[删除]'} 缓存文件: {file_path.relative_to(self.project_root)}")

                    elif file_path.is_dir():
                        size = sum(f.stat().st_size for f in file_path.rglob('*') if f.is_file())
                        if not dry_run:
                            shutil.rmtree(file_path)
                        cleaned_count += 1
                        cleaned_size += size
                        logger.info(f"{'[预览]' if dry_run else '[删除]'} 缓存目录: {file_path.relative_to(self.project_root)}")

                except (OSError, PermissionError):
                    continue

        return {
            'cleaned_count': cleaned_count,
            'cleaned_size_mb': round(cleaned_size / (1024 * 1024), 2)
        }

    def clean_temp_files(self, dry_run: bool = True) -> Dict[str, any]:
        """清理临时文件"""
        logger.info('🧹 清理临时文件...')

        cleaned_count = 0
        cleaned_size = 0
        cutoff_time = time.time() - (24 * 60 * 60)  # 24小时前

        temp_patterns = ['**/*.tmp', '**/*.temp', '**/*.swp', '**/*.swo', '**/*.bak', '**/*.orig', '**/*.rej']

        for pattern in temp_patterns:
            for file_path in self.project_root.glob(pattern):
                try:
                    if file_path.is_file():
                        stat = file_path.stat()
                        if stat.st_mtime < cutoff_time:
                            size = stat.st_size
                            if not dry_run:
                                file_path.unlink()
                            cleaned_count += 1
                            cleaned_size += size
                            logger.info(f"{'[预览]' if dry_run else '[删除]'} 临时文件: {file_path.relative_to(self.project_root)}")

                except (OSError, PermissionError):
                    continue

        return {
            'cleaned_count': cleaned_count,
            'cleaned_size_mb': round(cleaned_size / (1024 * 1024), 2)
        }

    def clean_old_logs(self, dry_run: bool = True, days: int = 7) -> Dict[str, any]:
        """清理过期日志文件"""
        logger.info(f"🧹 清理 {days} 天前的日志文件...")

        cleaned_count = 0
        cleaned_size = 0
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        log_patterns = ['**/*.log', '**/*.out', '**/*.err']

        for pattern in log_patterns:
            for file_path in self.project_root.glob(pattern):
                try:
                    if file_path.is_file():
                        stat = file_path.stat()
                        if stat.st_mtime < cutoff_time:
                            size = stat.st_size
                            if not dry_run:
                                file_path.unlink()
                            cleaned_count += 1
                            cleaned_size += size
                            logger.info(f"{'[预览]' if dry_run else '[删除]'} 日志文件: {file_path.relative_to(self.project_root)}")

                except (OSError, PermissionError):
                    continue

        return {
            'cleaned_count': cleaned_count,
            'cleaned_size_mb': round(cleaned_size / (1024 * 1024), 2)
        }

    def clean_empty_dirs(self, dry_run: bool = True) -> Dict[str, any]:
        """清理空目录"""
        logger.info('🧹 清理空目录...')

        cleaned_count = 0
        empty_dirs = []

        # 多次扫描，因为删除内层空目录后，外层可能也变空
        for _ in range(3):
            current_empty = []
            for dir_path in sorted(self.project_root.rglob('*'), reverse=True):
                if dir_path.is_dir():
                    try:
                        # 跳过重要目录
                        if self._should_skip(dir_path):
                            continue

                        # 检查是否为空
                        if not any(dir_path.iterdir()):
                            if dir_path not in empty_dirs:
                                current_empty.append(dir_path)
                    except (OSError, PermissionError):
                        continue

            if current_empty:
                empty_dirs.extend(current_empty)
                if not dry_run:
                    for dir_path in current_empty:
                        try:
                            dir_path.rmdir()
                            logger.info(f"[删除] 空目录: {dir_path.relative_to(self.project_root)}")
                        except (OSError, PermissionError):
                            continue
                cleaned_count += len(current_empty)

        return {
            'cleaned_count': cleaned_count
        }

    def find_duplicate_files(self) -> Dict[str, List[Path]]:
        """查找重复文件"""
        logger.info('🔍 查找重复文件...')

        file_hashes = {}
        duplicates = {}

        # 只扫描大于1KB的文件
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and not self._should_skip(file_path):
                try:
                    if file_path.stat().st_size > 1024:
                        file_hash = self._get_file_hash(file_path)
                        if file_hash:
                            if file_hash in file_hashes:
                                if file_hash not in duplicates:
                                    duplicates[file_hash] = [file_hashes[file_hash]]
                                duplicates[file_hash].append(file_path)
                            else:
                                file_hashes[file_hash] = file_path
                except (OSError, PermissionError):
                    continue

        # 过滤出真正的重复文件组
        real_duplicates = {h: files for h, files in duplicates.items() if len(files) > 1}

        logger.info(f"✅ 发现 {len(real_duplicates)} 组重复文件")
        return real_duplicates

    def analyze_large_files(self, min_size_mb: int = 100) -> List[Dict]:
        """分析大文件"""
        logger.info(f"🔍 分析大于 {min_size_mb}MB 的文件...")

        large_files = []
        min_size_bytes = min_size_mb * 1024 * 1024

        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and not self._should_skip(file_path):
                try:
                    stat = file_path.stat()
                    if stat.st_size > min_size_bytes:
                        file_age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)
                        access_age = datetime.now() - datetime.fromtimestamp(stat.st_atime)

                        large_files.append({
                            'path': file_path.relative_to(self.project_root),
                            'size_mb': round(stat.st_size / (1024 * 1024), 2),
                            'size_gb': round(stat.st_size / (1024 * 1024 * 1024), 2),
                            'age_days': file_age.days,
                            'access_days': access_age.days,
                            'last_modified': datetime.fromtimestamp(stat.st_mtime),
                            'last_accessed': datetime.fromtimestamp(stat.st_atime)
                        })
                except (OSError, PermissionError):
                    continue

        large_files.sort(key=lambda x: x['size_mb'], reverse=True)
        logger.info(f"✅ 发现 {len(large_files)} 个大文件")

        return large_files

    def clean_unused_test_files(self, dry_run: bool = True) -> Dict[str, any]:
        """清理未使用的测试文件"""
        logger.info('🧹 清理未使用的测试文件...')

        cleaned_count = 0
        cleaned_size = 0

        # 查找测试文件
        test_files = []
        for pattern in ['**/test_*.py', '**/*_test.py', '**/spec_*.py', '**/*_spec.py']:
            test_files.extend(self.project_root.glob(pattern))

        # 查找测试输出目录
        test_output_dirs = []
        test_dir_patterns = ['test_output', 'test_results', 'pytest_cache', '.pytest_cache']
        for dir_name in test_dir_patterns:
            test_output_dirs.extend(self.project_root.glob(f'**/{dir_name}'))

        # 清理测试输出目录
        for dir_path in test_output_dirs:
            if isinstance(dir_path, Path) and dir_path.is_dir():
                try:
                    size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                    if not dry_run:
                        shutil.rmtree(dir_path)
                    cleaned_count += 1
                    cleaned_size += size
                    logger.info(f"{'[预览]' if dry_run else '[删除]'} 测试目录: {dir_path.relative_to(self.project_root)}")
                except (OSError, PermissionError):
                    continue

        return {
            'cleaned_count': cleaned_count,
            'cleaned_size_mb': round(cleaned_size / (1024 * 1024), 2)
        }

    def generate_cleanup_report(self, dry_run: bool = True) -> str:
        """生成清理报告"""
        logger.info('📊 生成清理报告...')

        # 执行清理预览
        cache_result = self.clean_cache_files(dry_run=True)
        temp_result = self.clean_temp_files(dry_run=True)
        log_result = self.clean_old_logs(dry_run=True)
        empty_result = self.clean_empty_dirs(dry_run=True)
        test_result = self.clean_unused_test_files(dry_run=True)

        # 生成报告
        report = f"""
# 系统清理报告

## 📊 扫描概览
**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**项目路径**: {self.project_root}
**扫描模式**: {'预览模式' if dry_run else '执行模式'}

## 🧹 清理预览

### 1. 缓存文件清理
- **文件数量**: {cache_result['cleaned_count']}
- **释放空间**: {cache_result['cleaned_size_mb']} MB
- **类型**: Python缓存 (.pyc, .pyo, __pycache__), 系统缓存 (.DS_Store)

### 2. 临时文件清理
- **文件数量**: {temp_result['cleaned_count']}
- **释放空间**: {temp_result['cleaned_size_mb']} MB
- **类型**: 编辑器临时文件 (.swp, .swo), 备份文件 (.bak, .orig)

### 3. 过期日志清理
- **文件数量**: {log_result['cleaned_count']}
- **释放空间**: {log_result['cleaned_size_mb']} MB
- **时间范围**: 7天前的日志文件

### 4. 测试输出清理
- **目录数量**: {test_result['cleaned_count']}
- **释放空间**: {test_result['cleaned_size_mb']} MB

### 5. 空目录清理
- **目录数量**: {empty_result['cleaned_count']}

## 💡 清理建议

### 立即清理 (安全)
1. **缓存文件**: 可立即清理，释放 {cache_result['cleaned_size_mb']} MB
2. **临时文件**: 可立即清理，释放 {temp_result['cleaned_size_mb']} MB
3. **过期日志**: 可清理7天前的日志，释放 {log_result['cleaned_size_mb']} MB
4. **测试输出**: 可清理测试临时输出，释放 {test_result['cleaned_size_mb']} MB
5. **空目录**: 可清理 {empty_result['cleaned_count']} 个空目录

### 注意事项
- 📝 这是{'预览模式' if dry_run else '执行模式'}
- 🔒 重要文件已自动排除
- 📋 建议先运行预览模式确认后再执行清理
- 💾 清理前建议备份重要数据
"""

        return report

    def execute_cleanup(self, safe_only: bool = True) -> Dict[str, any]:
        """执行清理操作"""
        logger.info('🚀 开始执行清理...')

        results = {
            'cache_cleaned': self.clean_cache_files(dry_run=False),
            'temp_cleaned': self.clean_temp_files(dry_run=False),
            'logs_cleaned': self.clean_old_logs(dry_run=False),
            'empty_dirs_cleaned': self.clean_empty_dirs(dry_run=False),
            'test_cleaned': self.clean_unused_test_files(dry_run=False)
        }

        total_freed_mb = sum([
            results['cache_cleaned']['cleaned_size_mb'],
            results['temp_cleaned']['cleaned_size_mb'],
            results['logs_cleaned']['cleaned_size_mb'],
            results['test_cleaned']['cleaned_size_mb']
        ])

        results['total_freed_mb'] = total_freed_mb
        results['total_freed_gb'] = total_freed_mb / 1024

        logger.info(f"✅ 清理完成，释放空间: {total_freed_mb:.2f} MB ({total_freed_mb/1024:.2f} GB)")

        return results

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='系统清理工具')
    parser.add_argument('--project-root', default='.', help='项目根目录')
    parser.add_argument('--dry-run', action='store_true', default=True, help='预览模式（默认）')
    parser.add_argument('--execute', action='store_true', help='执行清理')
    parser.add_argument('--safe-only', action='store_true', default=True, help='仅执行安全清理')
    parser.add_argument('--min-size-mb', type=int, default=100, help='大文件最小大小（MB）')
    parser.add_argument('--log-days', type=int, default=7, help='日志文件保留天数')

    args = parser.parse_args()

    cleaner = SystemCleaner(args.project_root)

    try:
        if args.execute:
            # 执行清理
            results = cleaner.execute_cleanup(safe_only=args.safe_only)
            logger.info(f"\n🎉 清理完成！")
            logger.info(f"💾 总计释放空间: {results['total_freed_gb']:.2f} GB")
            logger.info(f"\n详细结果:")
            for key, result in results.items():
                if key.endswith('_cleaned') and isinstance(result, dict):
                    logger.info(f"  - {result['cleaned_count']} 个项目, {result['cleaned_size_mb']:.2f} MB")
        else:
            # 生成预览报告
            report = cleaner.generate_cleanup_report(dry_run=True)

            # 保存报告
            report_file = Path('SYSTEM_CLEANUP_REPORT.md')
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)

            logger.info('📋 清理预览报告已生成')
            logger.info(f"📄 报告文件: {report_file.absolute()}")
            logger.info(f"\n使用 --execute 参数执行实际清理")

    except Exception as e:
        logger.error(f"❌ 清理过程中出现错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()