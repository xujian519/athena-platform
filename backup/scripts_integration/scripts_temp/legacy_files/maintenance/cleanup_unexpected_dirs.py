#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理未预期的顶级目录
Cleanup Unexpected Directories
"""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class DirectoryCleanup:
    """目录清理工具"""

    def __init__(self):
        self.base_dir = Path('/Users/xujian/Athena工作平台')

        # 保护的目录（不删除）
        self.protected_dirs = {
            'config', 'docs', 'docker', 'scripts', 'services', 'core',
            'apps', 'utils', 'database', 'deployment', 'monitoring',
            'domains', 'logs', 'tools', '工作', '论文', '.git',
            '.claude', '.pids', 'documentation', 'storage'
        }

        # 需要移动到archive的目录
        self.to_archive = {
            'examples', 'prototypes', 'ai-projects', 'projects', 'reports',
            'academic_retrieval_system', 'patent-platform', 'workspace',
            'init-scripts', 'requirements', 'dev-tools', 'workflows',
            'binaries', 'models', 'data', 'production', 'ai_drawing_deployment'
        }

        # 归档目录
        self.archive_dir = self.base_dir / 'archive'

    def analyze_directories(self):
        """分析当前目录结构"""
        logger.info('📁 分析当前目录结构...')

        actual_dirs = set()
        for item in self.base_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                actual_dirs.add(item.name)

        logger.info(f"发现 {len(actual_dirs)} 个顶级目录")

        unexpected = actual_dirs - self.protected_dirs
        logger.info(f"未预期的目录: {len(unexpected)} 个")

        return actual_dirs, unexpected

    def create_archive_directory(self):
        """创建归档目录"""
        if not self.archive_dir.exists():
            self.archive_dir.mkdir(exist_ok=True)
            logger.info(f"创建归档目录: {self.archive_dir}")

    def archive_directories(self, dirs_to_move):
        """归档目录"""
        logger.info("\n📦 归档未使用目录...")

        archived_count = 0
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        for dir_name in dirs_to_move:
            if dir_name in self.to_archive:
                source_path = self.base_dir / dir_name

                if source_path.exists():
                    # 检查是否为空目录
                    if not any(source_path.iterdir()):
                        logger.info(f"  🗂️ 删除空目录: {dir_name}")
                        source_path.rmdir()
                        archived_count += 1
                    else:
                        # 移动到归档
                        archive_path = self.archive_dir / f"{dir_name}_{timestamp}"
                        logger.info(f"  📦 归档: {dir_name} -> archive/{dir_name}_{timestamp}")
                        shutil.move(str(source_path), str(archive_path))
                        archived_count += 1

        logger.info(f"\n✅ 已归档 {archived_count} 个目录")
        return archived_count

    def create_index(self):
        """创建归档索引"""
        index_file = self.archive_dir / 'archive_index.md'

        with open(index_file, 'w', encoding='utf-8') as f:
            f.write("# 归档目录索引\n\n")
            f.write(f"创建时间: {datetime.now().isoformat()}\n\n")

            for item in self.archive_dir.iterdir():
                if item.is_dir() and item.name != 'archive_index.md':
                    f.write(f"- **{item.name}**\n")

        logger.info(f"📝 创建归档索引: {index_file}")

    def cleanup_empty_dirs(self):
        """清理空目录"""
        logger.info("\n🧹 清理空目录...")

        empty_count = 0
        for root, dirs, files in os.walk(self.base_dir, topdown=False):
            # 跳过归档目录和受保护目录
            if 'archive' in root:
                continue
            if any(protected in root for protected in self.protected_dirs):
                continue

            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not any(dir_path.iterdir()):
                        logger.info(f"  🗑️ 删除空目录: {dir_path.relative_to(self.base_dir)}")
                        dir_path.rmdir()
                        empty_count += 1
                except:
                    pass

        logger.info(f"✅ 删除了 {empty_count} 个空目录")
        return empty_count

    def run_cleanup(self):
        """执行清理"""
        logger.info('🚀 开始目录清理...')

        # 分析当前结构
        actual_dirs, unexpected = self.analyze_directories()

        if not unexpected:
            logger.info('✅ 没有需要清理的目录')
            return

        # 创建归档目录
        self.create_archive_directory()

        # 归档目录
        archived_count = self.archive_directories(unexpected)

        # 清理空目录
        empty_count = self.cleanup_empty_dirs()

        # 创建索引
        self.create_index()

        logger.info(f"\n🎉 清理完成!")
        logger.info(f"  - 归档目录: {archived_count} 个")
        logger.info(f"  - 删除空目录: {empty_count} 个")
        logger.info(f"  - 归档位置: {self.archive_dir}")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='清理未预期的顶级目录')
    parser.add_argument('--dry-run', action='store_true', help='仅显示将要清理的目录，不执行实际操作')

    args = parser.parse_args()

    cleanup = DirectoryCleanup()

    if args.dry_run:
        logger.info('🔍 预览模式 - 仅显示将要清理的目录')
        actual_dirs, unexpected = cleanup.analyze_directories()
        logger.info(f"\n将要归档的目录:")
        for dir_name in sorted(unexpected):
            logger.info(f"  - {dir_name}")
    else:
        cleanup.run_cleanup()

if __name__ == '__main__':
    main()