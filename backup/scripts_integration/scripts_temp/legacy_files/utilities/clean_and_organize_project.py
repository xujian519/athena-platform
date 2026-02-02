#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台项目清理和整理工具
Project Cleanup and Organization Tool for Athena Platform

功能:
1. 清理冗余文件和临时文件
2. 删除冲突文件和备份文件
3. 整理根目录散落文件到合适文件夹
4. 生成清理报告

作者: 小诺 (AI助手)
创建时间: 2025-12-11
"""

import json
import logging
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProjectCleaner:
    """项目清理器"""

    def __init__(self, project_root='/Users/xujian/Athena工作平台'):
        self.project_root = Path(project_root)
        self.cleanup_stats = {
            'timestamp': datetime.now().isoformat(),
            'files_deleted': [],
            'files_moved': [],
            'directories_cleaned': [],
            'errors': [],
            'total_deleted_size': 0,
            'total_moved_size': 0
        }

    def analyze_project_structure(self):
        """分析项目结构"""
        logger.info('🔍 开始分析项目结构...')

        analysis = {
            'root_files': [],
            'conflict_files': [],
            'log_files': [],
            'temp_files': [],
            'backup_files': [],
            'duplicate_files': [],
            'recommendations': []
        }

        # 分析根目录文件
        for file_path in self.project_root.iterdir():
            if file_path.is_file() and not self._should_ignore_file(file_path):
                analysis['root_files'].append(str(file_path))
                file_name = file_path.name.lower()

                # 分类文件
                if 'conflict' in file_name or '_conflict_' in file_name:
                    analysis['conflict_files'].append(str(file_path))
                elif file_name.endswith(('.log', '.pid')):
                    analysis['log_files'].append(str(file_path))
                elif file_name.endswith(('.tmp', '.temp')):
                    analysis['temp_files'].append(str(file_path))
                elif 'backup' in file_name or 'bak' in file_name:
                    analysis['backup_files'].append(str(file_path))
                elif 'duplicate' in file_name:
                    analysis['duplicate_files'].append(str(file_path))

        # 生成建议
        if analysis['conflict_files']:
            analysis['recommendations'].append('删除冲突文件')
        if analysis['root_files']:
            analysis['recommendations'].append('整理根目录文件到合适文件夹')
        if analysis['log_files']:
            analysis['recommendations'].append('移动日志文件到logs目录')
        if analysis['temp_files']:
            analysis['recommendations'].append('删除临时文件')

        logger.info(f"✅ 项目结构分析完成")
        return analysis

    def _should_ignore_file(self, file_path):
        """判断文件是否应该忽略"""
        ignore_patterns = [
            '.git',
            'node_modules',
            '.DS_Store',
            '__pycache__',
            '.vscode',
            '.idea'
        ]

        file_str = str(file_path)
        return any(pattern in file_str for pattern in ignore_patterns)

    def cleanup_root_directory(self):
        """清理根目录"""
        logger.info('🧹 开始清理根目录...')

        # 确保目标目录存在
        dirs_to_create = [
            'logs',
            'temp',
            'backup',
            'reports'
        ]

        for dir_name in dirs_to_create:
            dir_path = self.project_root / dir_name
            dir_path.mkdir(exist_ok=True)

        # 处理根目录文件
        for file_path in self.project_root.iterdir():
            if not file_path.is_file() or self._should_ignore_file(file_path):
                continue

            file_name = file_path.name
            file_lower = file_name.lower()

            try:
                # 处理冲突文件
                if 'conflict' in file_lower or '_conflict_' in file_lower:
                    self._delete_file(file_path, 'conflict file')

                # 处理日志文件
                elif file_lower.endswith(('.log', '.pid')):
                    self._move_file(file_path, 'logs', 'log file')

                # 处理JSON性能日志
                elif file_lower.endswith('_performance_log.json'):
                    self._move_file(file_path, 'logs', 'performance log')

                # 处理临时文件
                elif file_lower.endswith(('.tmp', '.temp')):
                    self._delete_file(file_path, 'temporary file')

                # 处理备份文件
                elif 'backup' in file_lower or 'bak' in file_lower:
                    self._move_file(file_path, 'backup', 'backup file')

                # 处理其他散落文件
                else:
                    # 根据文件类型移动到合适位置
                    if file_lower.endswith(('.md', '.txt')):
                        self._move_file(file_path, 'docs', 'documentation file')
                    elif file_lower.endswith(('.json', '.yaml', '.yml')):
                        if 'config' in file_lower:
                            self._move_file(file_path, 'config', 'config file')
                        else:
                            self._move_file(file_path, 'data', 'data file')

            except Exception as e:
                logger.error(f"❌ 处理文件失败 {file_path}: {e}")
                self.cleanup_stats['errors'].append(f"处理文件失败: {file_path} - {str(e)}")

        logger.info(f"✅ 根目录清理完成")

    def cleanup_conflict_files(self):
        """清理冲突文件"""
        logger.info('🔧 开始清理冲突文件...')

        conflict_files = list(self.project_root.rglob('*conflict*'))

        for file_path in conflict_files:
            if file_path.is_file():
                self._delete_file(file_path, 'conflict file')

        logger.info(f"✅ 冲突文件清理完成，处理了 {len(conflict_files)} 个文件")

    def cleanup_temp_files(self):
        """清理临时文件"""
        logger.info('🗑️ 开始清理临时文件...')

        temp_patterns = [
            '*.tmp',
            '*.temp',
            '*~',
            '.DS_Store',
            '.pytest_cache',
            '__pycache__'
        ]

        deleted_count = 0
        for pattern in temp_patterns:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file():
                    self._delete_file(file_path, 'temporary file')
                    deleted_count += 1
                elif file_path.is_dir():
                    self._delete_directory(file_path, 'temporary directory')
                    deleted_count += 1

        logger.info(f"✅ 临时文件清理完成，处理了 {deleted_count} 个文件/目录")

    def organize_directories(self):
        """整理目录结构"""
        logger.info('📁 开始整理目录结构...')

        # 整理子目录中的散落文件
        self._organize_directory_contents(self.project_root / 'scripts')
        self._organize_directory_contents(self.project_root / 'services')
        self._organize_directory_contents(self.project_root / 'domains')
        self._organize_directory_contents(self.project_root / 'utils')

        logger.info('✅ 目录结构整理完成')

    def _organize_directory_contents(self, dir_path):
        """整理目录内容"""
        if not dir_path.exists():
            return

        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.log', '.pid', '.tmp']:
                try:
                    # 移动到logs目录
                    target_path = self.project_root / 'logs' / file_path.name
                    if target_path.exists():
                        target_path = target_path.parent / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_path.suffix}"

                    shutil.move(str(file_path), str(target_path))
                    self.cleanup_stats['files_moved'].append({
                        'source': str(file_path),
                        'target': str(target_path),
                        'type': 'log file from subdir'
                    })
                except Exception as e:
                    logger.warning(f"⚠️ 移动文件失败 {file_path}: {e}")

    def _delete_file(self, file_path, file_type):
        """删除文件"""
        try:
            file_size = file_path.stat().st_size
            file_path.unlink()
            self.cleanup_stats['files_deleted'].append({
                'path': str(file_path),
                'type': file_type,
                'size': file_size
            })
            self.cleanup_stats['total_deleted_size'] += file_size
            logger.debug(f"🗑️ 删除文件: {file_path}")
        except Exception as e:
            logger.error(f"❌ 删除文件失败 {file_path}: {e}")

    def _delete_directory(self, dir_path, dir_type):
        """删除目录"""
        try:
            shutil.rmtree(dir_path)
            self.cleanup_stats['files_deleted'].append({
                'path': str(dir_path),
                'type': dir_type,
                'size': 0
            })
            logger.debug(f"🗑️ 删除目录: {dir_path}")
        except Exception as e:
            logger.error(f"❌ 删除目录失败 {dir_path}: {e}")

    def _move_file(self, file_path, target_dir, file_type):
        """移动文件"""
        try:
            target_path = self.project_root / target_dir / file_path.name

            # 避免文件名冲突
            counter = 1
            original_target = target_path
            while target_path.exists():
                name_parts = file_path.stem.split('_')
                if len(name_parts) > 1 and name_parts[-1].isdigit():
                    name_parts[-1] = str(counter)
                else:
                    name_parts.append(str(counter))
                target_path = original_target.parent / f"_{'_'.join(name_parts)}{file_path.suffix}"
                counter += 1

            file_size = file_path.stat().st_size
            shutil.move(str(file_path), str(target_path))

            self.cleanup_stats['files_moved'].append({
                'source': str(file_path),
                'target': str(target_path),
                'type': file_type,
                'size': file_size
            })
            self.cleanup_stats['total_moved_size'] += file_size
            logger.debug(f"📁 移动文件: {file_path} -> {target_path}")
        except Exception as e:
            logger.error(f"❌ 移动文件失败 {file_path}: {e}")

    def generate_cleanup_report(self):
        """生成清理报告"""
        logger.info('📋 生成清理报告...')

        report = self.cleanup_stats.copy()
        report['summary'] = {
            'total_files_deleted': len(report['files_deleted']),
            'total_files_moved': len(report['files_moved']),
            'total_size_saved': report['total_deleted_size'] + report['total_moved_size'],
            'errors_count': len(report['errors']),
            'cleanup_status': 'completed' if not report['errors'] else 'completed_with_errors'
        }

        # 保存报告
        report_path = self.project_root / '.runtime' / 'project_cleanup_report.json'
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 清理报告已保存到: {report_path}")
        return report

def main():
    """主函数"""
    logger.info('🧹 Athena工作平台项目清理和整理工具')
    logger.info(str('='*60))

    cleaner = ProjectCleaner()

    # 1. 分析项目结构
    analysis = cleaner.analyze_project_structure()
    logger.info(f"\n📊 项目结构分析:")
    logger.info(f"  根目录文件: {len(analysis['root_files'])}")
    logger.info(f"  冲突文件: {len(analysis['conflict_files'])}")
    logger.info(f"  日志文件: {len(analysis['log_files'])}")
    logger.info(f"  临时文件: {len(analysis['temp_files'])}")
    logger.info(f"  备份文件: {len(analysis['backup_files'])}")

    # 2. 清理根目录
    logger.info(f"\n🧹 清理根目录...")
    cleaner.cleanup_root_directory()

    # 3. 清理冲突文件
    logger.info(f"\n🔧 清理冲突文件...")
    cleaner.cleanup_conflict_files()

    # 4. 清理临时文件
    logger.info(f"\n🗑️ 清理临时文件...")
    cleaner.cleanup_temp_files()

    # 5. 整理目录结构
    logger.info(f"\n📁 整理目录结构...")
    cleaner.organize_directories()

    # 6. 生成报告
    logger.info(f"\n📋 生成清理报告...")
    report = cleaner.generate_cleanup_report()

    # 显示总结
    logger.info(str(f"\n' + '="*60))
    logger.info(f"🎉 项目清理和整理完成!")
    logger.info(str(f"="*60))
    logger.info(f"📊 清理统计:")
    logger.info(f"  删除文件数: {report['summary']['total_files_deleted']}")
    logger.info(f"  移动文件数: {report['summary']['total_files_moved']}")
    logger.info(f"  节省空间: {report['summary']['total_size_saved'] / 1024 / 1024:.2f} MB")
    logger.info(f"  错误数量: {report['summary']['errors_count']}")
    logger.info(f"  清理状态: {report['summary']['cleanup_status']}")

    if report['summary']['errors_count'] == 0:
        logger.info(f"\n🎊 项目清理完美完成!")
    else:
        logger.info(f"\n⚠️ 清理完成，但有 {report['summary']['errors_count']} 个错误")
        logger.info(f"请检查日志了解详情")

    return report

if __name__ == '__main__':
    main()