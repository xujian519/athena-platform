#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版系统清理工具
Enhanced System Cleaner Tool

深度扫描和清理各种冗余文件，包括重复文件、无用文档、过期备份等
"""

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
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

class EnhancedCleaner:
    """增强版系统清理器"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.cleaned_files = []
        self.cleaned_size = 0
        self.report = {
            'scan_time': datetime.now(),
            'cleaned_files': {},
            'found_issues': [],
            'recommendations': []
        }

        # 需要保护的目录和文件
        self.protected_paths = {
            'core', 'scripts', 'services', 'domains', 'models', 'data', 'storage',
            '.git', 'node_modules', 'venv', 'env', '.env'
        }

        # 清理规则配置
        self.cleaning_rules = {
            'cache_files': {
                'patterns': ['**/*.pyc', '**/*.pyo', '**/__pycache__', '**/.DS_Store', '**/Thumbs.db'],
                'description': '缓存文件',
                'safe': True
            },
            'temp_files': {
                'patterns': ['**/*.tmp', '**/*.temp', '**/*.swp', '**/*.swo', '**/*.bak', '**/*.orig'],
                'description': '临时文件',
                'safe': True
            },
            'logs': {
                'patterns': ['**/*.log', '**/*.out', '**/*.err'],
                'description': '日志文件（超过7天）',
                'safe': True,
                'age_days': 7
            },
            'build_artifacts': {
                'patterns': ['**/build/**', '**/dist/**', '**/*.egg-info/**'],
                'description': '构建产物',
                'safe': True
            },
            'backup_files': {
                'patterns': ['**/*.backup', '**/*.old', '**/*.save', '**/*~'],
                'description': '备份文件',
                'safe': False
            },
            'useless_docs': {
                'patterns': [],
                'description': '无用文档',
                'safe': False
            },
            'duplicate_files': {
                'patterns': [],
                'description': '重复文件',
                'safe': False
            }
        }

    def find_large_unused_files(self, min_size_mb: int = 50, unused_days: int = 90) -> List[Dict]:
        """查找大且长期未使用的文件"""
        logger.info(f"🔍 查找大于 {min_size_mb}MB 且 {unused_days} 天未使用的文件...")

        large_unused = []
        min_size_bytes = min_size_mb * 1024 * 1024
        cutoff_time = time.time() - (unused_days * 24 * 60 * 60)

        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and self._is_cleanable(file_path):
                try:
                    stat = file_path.stat()

                    if stat.st_size > min_size_bytes:
                        access_time = stat.st_atime
                        modify_time = stat.st_mtime

                        # 检查是否长期未访问
                        if access_time < cutoff_time and modify_time < cutoff_time:
                            large_unused.append({
                                'path': file_path.relative_to(self.project_root),
                                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                                'size_gb': round(stat.st_size / (1024 * 1024 * 1024), 2),
                                'last_access': datetime.fromtimestamp(access_time),
                                'last_modified': datetime.fromtimestamp(modify_time),
                                'days_unused': (time.time() - access_time) / (24 * 60 * 60)
                            })

                except (OSError, PermissionError):
                    continue

        large_unused.sort(key=lambda x: x['size_mb'], reverse=True)
        logger.info(f"✅ 发现 {len(large_unused)} 个大且长期未使用的文件")

        return large_unused

    def find_duplicate_files(self) -> Dict[str, List[Dict]]:
        """查找重复文件"""
        logger.info('🔍 查找重复文件...')

        file_hashes = {}
        duplicates = {}

        # 只扫描大于1KB的文件
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and self._is_cleanable(file_path):
                try:
                    if file_path.stat().st_size > 1024:
                        file_hash = self._calculate_file_hash(file_path)
                        if file_hash:
                            file_info = {
                                'path': file_path.relative_to(self.project_root),
                                'size_mb': round(file_path.stat().st_size / (1024 * 1024), 2),
                                'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                            }

                            if file_hash in file_hashes:
                                if file_hash not in duplicates:
                                    duplicates[file_hash] = [file_hashes[file_hash]]
                                duplicates[file_hash].append(file_info)
                            else:
                                file_hashes[file_hash] = file_info

                except (OSError, PermissionError):
                    continue

        # 过滤出真正的重复文件组
        real_duplicates = {h: files for h, files in duplicates.items() if len(files) > 1}

        total_duplicate_size = sum(
            sum(f['size_mb'] for f in files[1:])  # 保留第一个，计算其他重复文件大小
            for files in real_duplicates.values()
        )

        logger.info(f"✅ 发现 {len(real_duplicates)} 组重复文件，可释放 {total_duplicate_size:.2f} MB")

        return real_duplicates

    def find_useless_docs(self) -> List[Dict]:
        """查找无用的文档文件"""
        logger.info('🔍 查找无用的文档文件...')

        useless_docs = []
        doc_patterns = ['**/*.md', '**/*.txt', '**/*.rst', '**/*.doc', '**/*.docx', '**/*.pdf']

        # 无用文档的特征
        useless_keywords = [
            'copy', '副本', '备份', 'temp', 'tmp', 'test', 'demo', 'example',
            'old', '废弃', 'obsolete', 'draft', '草稿', 'todo', 'fixme'
        ]

        for pattern in doc_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and self._is_cleanable(file_path):
                    try:
                        # 检查文件名是否包含无用关键词
                        filename_lower = file_path.name.lower()
                        if any(keyword in filename_lower for keyword in useless_keywords):
                            stat = file_path.stat()
                            file_age = (time.time() - stat.st_mtime) / (24 * 60 * 60)

                            useless_docs.append({
                                'path': file_path.relative_to(self.project_root),
                                'size_kb': round(stat.st_size / 1024, 2),
                                'age_days': round(file_age, 0),
                                'reason': '文件名包含无用关键词'
                            })

                        # 检查是否为空文档或极小文档
                        elif stat.st_size < 1024:  # 小于1KB
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read().strip()
                                if len(content) < 100:  # 内容少于100字符
                                    useless_docs.append({
                                        'path': file_path.relative_to(self.project_root),
                                        'size_kb': round(stat.st_size / 1024, 2),
                                        'age_days': round((time.time() - stat.st_mtime) / (24 * 60 * 60), 0),
                                        'reason': '文档内容极少或为空'
                                    })

                    except (OSError, PermissionError, UnicodeDecodeError):
                        continue

        logger.info(f"✅ 发现 {len(useless_docs)} 个可能无用的文档")

        return useless_docs

    def find_empty_directories(self) -> List[Path]:
        """查找空目录"""
        logger.info('🔍 查找空目录...')

        empty_dirs = []

        # 多次扫描，因为删除内层空目录后，外层可能也变空
        for _ in range(3):
            current_empty = []
            for dir_path in sorted(self.project_root.rglob('*'), reverse=True):
                if dir_path.is_dir() and self._is_cleanable(dir_path):
                    try:
                        if not any(dir_path.iterdir()):
                            if dir_path not in empty_dirs:
                                current_empty.append(dir_path)
                    except (OSError, PermissionError):
                        continue

            if current_empty:
                empty_dirs.extend(current_empty)

        logger.info(f"✅ 发现 {len(empty_dirs)} 个空目录")

        return empty_dirs

    def find_orphaned_files(self) -> List[Dict]:
        """查找孤立文件（没有引用的文件）"""
        logger.info('🔍 查找孤立文件...')

        orphaned = []

        # 查找配置文件
        config_patterns = ['**/*.json', '**/*.yaml', '**/*.yml', '**/*.ini', '**/*.cfg', '**/*.conf']
        found_configs = set()

        for pattern in config_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and self._is_cleanable(file_path):
                    found_configs.add(file_path.name)

        # 查找可能的临时配置文件
        temp_patterns = ['**/*.tmp.json', '**/*.temp.yaml', '**/*_backup.*']
        for pattern in temp_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and self._is_cleanable(file_path):
                    try:
                        stat = file_path.stat()
                        file_age = (time.time() - stat.st_mtime) / (24 * 60 * 60)

                        if file_age > 7:  # 超过7天
                            orphaned.append({
                                'path': file_path.relative_to(self.project_root),
                                'size_kb': round(stat.st_size / 1024, 2),
                                'age_days': round(file_age, 0),
                                'type': '临时配置文件'
                            })
                    except (OSError, PermissionError):
                        continue

        logger.info(f"✅ 发现 {len(orphaned)} 个孤立文件")

        return orphaned

    def find_deprecated_code(self) -> List[Dict]:
        """查找废弃的代码文件"""
        logger.info('🔍 查找废弃的代码文件...')

        deprecated = []
        deprecated_patterns = ['**/deprecated/**', '**/old/**', '**/legacy/**', '**/obsolete/**']

        # 废弃代码的关键词
        deprecated_keywords = [
            'deprecated', 'obsolete', 'legacy', 'old_', 'TODO: remove',
            '# DEPRECATED', '# OBSOLETE', 'def deprecated_'
        ]

        for pattern in deprecated_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and file_path.suffix in ['.py', '.js', '.java', '.cpp', '.c']:
                    try:
                        stat = file_path.stat()
                        deprecated.append({
                            'path': file_path.relative_to(self.project_root),
                            'size_kb': round(stat.st_size / 1024, 2),
                            'age_days': round((time.time() - stat.st_mtime) / (24 * 60 * 60), 0),
                            'reason': '位于废弃目录'
                        })
                    except (OSError, PermissionError):
                        continue

        # 扫描包含废弃关键词的文件
        for file_path in self.project_root.rglob('*.py'):
            if file_path.is_file() and self._is_cleanable(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        if any(keyword.lower() in content for keyword in deprecated_keywords):
                            stat = file_path.stat()
                            deprecated.append({
                                'path': file_path.relative_to(self.project_root),
                                'size_kb': round(stat.st_size / 1024, 2),
                                'age_days': round((time.time() - stat.st_mtime) / (24 * 60 * 60), 0),
                                'reason': '包含废弃关键词'
                            })
                except (OSError, PermissionError, UnicodeDecodeError):
                    continue

        logger.info(f"✅ 发现 {len(deprecated)} 个可能废弃的代码文件")

        return deprecated

    def _is_cleanable(self, path: Path) -> bool:
        """判断文件/目录是否可以清理"""
        path_str = str(path)

        # 跳过隐藏文件
        if path.name.startswith('.'):
            return False

        # 跳过受保护的路径
        for protected in self.protected_paths:
            if protected in path_str:
                return False

        # 跳过重要文件
        important_files = {
            'README.md', 'LICENSE', 'setup.py', 'requirements.txt',
            'package.json', 'Dockerfile', 'docker-compose.yml',
            '.gitignore', 'Makefile', 'pyproject.toml'
        }

        if path.name in important_files:
            return False

        return True

    def _calculate_file_hash(self, file_path: Path, block_size: int = 65536) -> str | None:
        """计算文件哈希值"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for block in iter(lambda: f.read(block_size), b''):
                    hasher.update(block)
            return hasher.hexdigest()
        except (OSError, PermissionError):
            return None

    def scan_all(self) -> Dict[str, any]:
        """执行全面扫描"""
        logger.info('🚀 开始全面扫描...')

        scan_results = {
            'cache_files': self._scan_pattern_files(self.cleaning_rules['cache_files']['patterns']),
            'temp_files': self._scan_pattern_files(self.cleaning_rules['temp_files']['patterns']),
            'log_files': self._scan_pattern_files(self.cleaning_rules['logs']['patterns']),
            'build_artifacts': self._scan_pattern_files(self.cleaning_rules['build_artifacts']['patterns']),
            'backup_files': self._scan_pattern_files(self.cleaning_rules['backup_files']['patterns']),
            'large_unused': self.find_large_unused_files(),
            'duplicate_files': self.find_duplicate_files(),
            'useless_docs': self.find_useless_docs(),
            'empty_dirs': self.find_empty_directories(),
            'orphaned_files': self.find_orphaned_files(),
            'deprecated_code': self.find_deprecated_code()
        }

        # 计算总的可清理空间
        total_cleanable_mb = 0
        for category, items in scan_results.items():
            if isinstance(items, list) and items:
                if category == 'duplicate_files':
                    # 重复文件只计算重复的部分
                    for file_list in items.values():
                        total_cleanable_mb += sum(f['size_mb'] for f in file_list[1:])
                elif 'size_mb' in items[0]:
                    total_cleanable_mb += sum(item.get('size_mb', 0) for item in items)
                elif 'size_kb' in items[0]:
                    total_cleanable_mb += sum(item.get('size_kb', 0) / 1024 for item in items)
                elif 'size_gb' in items[0]:
                    total_cleanable_mb += sum(item.get('size_gb', 0) * 1024 for item in items)

        scan_results['total_cleanable_mb'] = round(total_cleanable_mb, 2)
        scan_results['total_cleanable_gb'] = round(total_cleanable_mb / 1024, 2)

        return scan_results

    def _scan_pattern_files(self, patterns: List[str]) -> List[Dict]:
        """根据模式扫描文件"""
        files = []
        for pattern in patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and self._is_cleanable(file_path):
                    try:
                        stat = file_path.stat()
                        files.append({
                            'path': file_path.relative_to(self.project_root),
                            'size_mb': round(stat.st_size / (1024 * 1024), 2),
                            'age_days': round((time.time() - stat.st_mtime) / (24 * 60 * 60), 0)
                        })
                    except (OSError, PermissionError):
                        continue
        return files

    def generate_detailed_report(self, scan_results: Dict[str, any]) -> str:
        """生成详细的清理报告"""
        report = f"""# 系统深度清理报告

## 📊 扫描概览
- **扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **项目路径**: {self.project_root}
- **可清理空间**: {scan_results.get('total_cleanable_mb', 0):.2f} MB ({scan_results.get('total_cleanable_gb', 0):.2f} GB)

## 🧹 清理项目详情

### 1. 缓存文件 (安全清理)
- **数量**: {len(scan_results.get('cache_files', []))}
- **大小**: {sum(f['size_mb'] for f in scan_results.get('cache_files', [])):.2f} MB
- **类型**: Python缓存、系统缓存

### 2. 临时文件 (安全清理)
- **数量**: {len(scan_results.get('temp_files', []))}
- **大小**: {sum(f['size_mb'] for f in scan_results.get('temp_files', [])):.2f} MB

### 3. 日志文件 (超过7天)
- **数量**: {len(scan_results.get('log_files', []))}
- **大小**: {sum(f['size_mb'] for f in scan_results.get('log_files', [])):.2f} MB

### 4. 构建产物
- **数量**: {len(scan_results.get('build_artifacts', []))}
- **大小**: {sum(f['size_mb'] for f in scan_results.get('build_artifacts', [])):.2f} MB

### 5. 备份文件 (需要确认)
- **数量**: {len(scan_results.get('backup_files', []))}
- **大小**: {sum(f['size_mb'] for f in scan_results.get('backup_files', [])):.2f} MB

### 6. 大且长期未使用的文件 (需要确认)
"""

        # 大文件详情
        large_files = scan_results.get('large_unused', [])
        if large_files:
            report += f"""
- **数量**: {len(large_files)}
- **总大小**: {sum(f['size_mb'] for f in large_files):.2f} MB

**Top 10 大文件:**
| 文件路径 | 大小 | 未使用天数 |
|---------|------|------------|
{chr(10).join([f"| {f['path']} | {f['size_mb']:.2f} MB | {f['days_unused']:.0f} 天 |" for f in large_files[:10]])}
"""

        # 重复文件详情
        duplicates = scan_results.get('duplicate_files', {})
        if duplicates:
            duplicate_size = sum(sum(f['size_mb'] for f in files[1:]) for files in duplicates.values())
            report += f"""
### 7. 重复文件 (需要确认)
- **组数**: {len(duplicates)}
- **可释放大小**: {duplicate_size:.2f} MB

**重复文件组 (Top 5):**
"""
"""

        # 无用文档详情
        useless_docs = scan_results.get('useless_docs', [])
        if useless_docs:
            useless_docs_size_mb = sum(f['size_kb'] for f in useless_docs) / 1024
            report += f"""
### 8. 无用文档 (需要确认)
- **数量**: {len(useless_docs)}
- **总大小**: {useless_docs_size_mb:.2f} MB

**示例:**
{chr(10).join([f"- {f['path']} ({f['reason']})" for f in useless_docs[:10]])}
"""

        # 其他项目
        report += f"""
### 9. 其他清理项目
- **空目录**: {len(scan_results.get('empty_dirs', []))} 个
- **孤立文件**: {len(scan_results.get('orphaned_files', []))} 个
- **废弃代码**: {len(scan_results.get('deprecated_code', []))} 个

## 💡 清理建议

### 🔒 安全清理 (可立即执行)
1. **缓存文件**: 释放 {sum(f['size_mb'] for f in scan_results.get('cache_files', [])):.2f} MB
2. **临时文件**: 释放 {sum(f['size_mb'] for f in scan_results.get('temp_files', [])):.2f} MB
3. **日志文件**: 释放 {sum(f['size_mb'] for f in scan_results.get('log_files', [])):.2f} MB
4. **构建产物**: 释放 {sum(f['size_mb'] for f in scan_results.get('build_artifacts', [])):.2f} MB
5. **空目录**: 清理 {len(scan_results.get('empty_dirs', []))} 个

**安全清理可释放空间**: {
    sum(f['size_mb'] for f in scan_results.get('cache_files', [])) +
    sum(f['size_mb'] for f in scan_results.get('temp_files', [])) +
    sum(f['size_mb'] for f in scan_results.get('log_files', [])) +
    sum(f['size_mb'] for f in scan_results.get('build_artifacts', []))
:.2f} MB

### ⚠️ 需要确认的清理
1. **大文件**: 手动检查 {len(large_files)} 个大文件
2. **重复文件**: 可释放 {duplicate_size if duplicates else 0:.2f} MB
3. **备份文件**: 检查 {len(scan_results.get('backup_files', []))} 个备份文件
4. **无用文档**: 检查 {len(useless_docs)} 个文档

### 📋 执行步骤
1. 执行安全清理：`python3 scripts/enhanced_cleaner.py --safe-clean`
2. 手动检查需要确认的项目
3. 执行深度清理：`python3 scripts/enhanced_cleaner.py --deep-clean`

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        return report

    def execute_safe_clean(self) -> Dict[str, any]:
        """执行安全清理"""
        logger.info('🧹 执行安全清理...')

        results = {
            'cache_files': 0,
            'temp_files': 0,
            'log_files': 0,
            'build_artifacts': 0,
            'empty_dirs': 0,
            'total_freed_mb': 0
        }

        # 清理缓存文件
        for file_path in self.project_root.glob('**/*.pyc'):
            if self._is_cleanable(file_path):
                try:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    results['cache_files'] += 1
                    results['total_freed_mb'] += size / (1024 * 1024)
                except (OSError, PermissionError):
                    continue

        # 清理__pycache__目录
        for dir_path in self.project_root.glob('**/__pycache__'):
            if self._is_cleanable(dir_path):
                try:
                    size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                    shutil.rmtree(dir_path)
                    results['cache_files'] += 1
                    results['total_freed_mb'] += size / (1024 * 1024)
                except (OSError, PermissionError):
                    continue

        # 清理.DS_Store文件
        for file_path in self.project_root.glob('**/.DS_Store'):
            if self._is_cleanable(file_path):
                try:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    results['cache_files'] += 1
                    results['total_freed_mb'] += size / (1024 * 1024)
                except (OSError, PermissionError):
                    continue

        # 清理空目录
        for _ in range(3):  # 多轮清理
            current_empty = []
            for dir_path in sorted(self.project_root.rglob('*'), reverse=True):
                if dir_path.is_dir() and self._is_cleanable(dir_path):
                    try:
                        if not any(dir_path.iterdir()):
                            current_empty.append(dir_path)
                    except (OSError, PermissionError):
                        continue

            for dir_path in current_empty:
                try:
                    dir_path.rmdir()
                    results['empty_dirs'] += 1
                except (OSError, PermissionError):
                    continue

        results['total_freed_mb'] = round(results['total_freed_mb'], 2)
        results['total_freed_gb'] = round(results['total_freed_mb'] / 1024, 2)

        logger.info(f"✅ 安全清理完成，释放空间: {results['total_freed_mb']:.2f} MB")
        return results

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='增强版系统清理工具')
    parser.add_argument('--project-root', default='.', help='项目根目录')
    parser.add_argument('--scan', action='store_true', help='执行全面扫描')
    parser.add_argument('--safe-clean', action='store_true', help='执行安全清理')
    parser.add_argument('--deep-clean', action='store_true', help='执行深度清理（需要确认）')
    parser.add_argument('--min-size-mb', type=int, default=50, help='大文件最小大小（MB）')
    parser.add_argument('--unused-days', type=int, default=90, help='长期未使用的天数')

    args = parser.parse_args()

    cleaner = EnhancedCleaner(args.project_root)

    try:
        if args.safe_clean:
            results = cleaner.execute_safe_clean()
            logger.info(f"\n🎉 安全清理完成！")
            logger.info(f"💾 释放空间: {results['total_freed_gb']:.2f} GB")
            logger.info(f"📁 清理项目:")
            logger.info(f"  - 缓存文件: {results['cache_files']} 个")
            logger.info(f"  - 空目录: {results['empty_dirs']} 个")

        else:
            # 扫描模式
            scan_results = cleaner.scan_all()
            report = cleaner.generate_detailed_report(scan_results)

            # 保存报告
            report_file = Path('ENHANCED_CLEANUP_REPORT.md')
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)

            logger.info('📋 深度清理报告已生成')
            logger.info(f"📄 报告文件: {report_file.absolute()}")
            logger.info(f"\n📊 发现可清理空间: {scan_results['total_cleanable_gb']:.2f} GB")
            logger.info(f"\n使用 --safe-clean 执行安全清理")

    except Exception as e:
        logger.error(f"❌ 清理过程中出现错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()