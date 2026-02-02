#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终清理脚本
Final Cleanup Script

清理迁移后剩余的原始目录和重复文件
"""

import argparse
import logging
import os
import shutil
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

class FinalCleanup:
    """最终清理器"""

    def __init__(self, base_dir: str = '/Users/xujian/Athena工作平台'):
        self.base_dir = Path(base_dir)

        # 可以安全删除的目录（主要内容已迁移）
        self.safe_to_remove = [
            'patent_retrieval_system',
            'patent_agent',
            'patent_workspace',
            'docker',
            'docs',
            'logs'
        ]

        # 保护目录
        self.protected = {
            '论文', '工作', 'scripts', 'core', 'services', 'config', 'data',
            'deployment', 'patent-platform', 'documentation', 'ai-projects',
            'dev-tools', 'monitoring', '.git', '.claude', '.github', '.system',
            '.workspace', 'models', 'database', 'storage', 'projects',
            'academic_retrieval_system', 'ai_drawing_deployment', 'apps',
            'binaries', 'domains', 'examples', 'init-scripts', 'production',
            'prototypes', 'reports', 'requirements', 'tools', 'utils',
            'workflows', 'workspace'
        }

    def analyze_remaining_structure(self):
        """分析剩余的目录结构"""
        logger.info('🔍 分析当前目录结构...')

        all_dirs = [d for d in self.base_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]

        categories = {
            '整合目录': [],
            '原始目录(可清理)': [],
            '项目目录': [],
            '保留目录': [],
            '其他目录': []
        }

        for dir_path in all_dirs:
            dir_name = dir_path.name

            if dir_name in {'deployment', 'patent-platform', 'documentation', 'ai-projects', 'dev-tools', 'monitoring'}:
                categories['整合目录'].append(dir_name)
            elif dir_name in self.safe_to_remove:
                categories['原始目录(可清理)'].append(dir_name)
            elif dir_name in {'projects', 'prototypes', 'apps', 'academic_retrieval_system', 'ai_drawing_deployment'}:
                categories['项目目录'].append(dir_name)
            elif dir_name in {'论文', '工作'}:
                categories['保留目录'].append(dir_name)
            elif dir_name in self.protected:
                categories['保留目录'].append(dir_name)
            else:
                categories['其他目录'].append(dir_name)

        logger.info(f"\n📊 目录统计:")
        for category, dirs in categories.items():
            logger.info(f"  {category}: {len(dirs)} 个")
            for dir_name in dirs:
                size = self._get_directory_size(self.base_dir / dir_name)
                logger.info(f"    - {dir_name} ({size})")

        return categories

    def _get_directory_size(self, dir_path: Path) -> str:
        """获取目录大小"""
        try:
            total_size = 0
            for item in dir_path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
            return self._format_size(total_size)
        except:
            return '未知大小'

    def _format_size(self, size_bytes: int) -> str:
        """格式化大小"""
        if size_bytes == 0:
            return '0B'
        size_names = ['B', 'KB', 'MB', 'GB']
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f}{size_names[i]}"

    def check_duplicate_files(self) -> List[Tuple[str, str, str]]:
        """检查重复文件"""
        logger.info("\n🔍 检查重复文件...")

        duplicates = []

        # 检查conflict文件
        for conflict_file in self.base_dir.rglob('*conflict_*'):
            if conflict_file.is_file():
                original_name = conflict_file.name.replace('_conflict_1', '')
                original_path = conflict_file.parent / original_name
                if original_path.exists():
                    size_diff = conflict_file.stat().st_size - original_path.stat().st_size
                    duplicates.append((
                        str(conflict_file.relative_to(self.base_dir)),
                        str(original_path.relative_to(self.base_dir)),
                        f"大小差: {self._format_size(abs(size_diff))}"
                    ))

        return duplicates

    def safe_remove_directory(self, dir_path: Path, dry_run: bool = True) -> bool:
        """安全删除目录"""
        try:
            if not dir_path.exists():
                return True

            if dry_run:
                size = self._get_directory_size(dir_path)
                logger.info(f"🔍 将删除: {dir_path.name} ({size})")
                return True

            # 实际删除
            shutil.rmtree(dir_path)
            logger.info(f"✅ 已删除: {dir_path.name}")
            return True

        except Exception as e:
            logger.info(f"❌ 删除失败 {dir_path.name}: {e}")
            return False

    def execute_cleanup(self, dry_run: bool = True, force: bool = False) -> dict:
        """执行清理"""
        logger.info('🧹 开始最终清理...')

        # 分析结构
        categories = self.analyze_remaining_structure()

        # 检查重复文件
        duplicates = self.check_duplicate_files()
        if duplicates:
            logger.info(f"\n⚠️ 发现 {len(duplicates)} 个可能的重复文件:")
            for dup in duplicates[:5]:  # 只显示前5个
                logger.info(f"  {dup[0]} <-> {dup[1]} ({dup[2]})")

        # 准备删除的目录
        to_remove = []
        total_size = 0
        for dir_name in categories['原始目录(可清理)']:
            dir_path = self.base_dir / dir_name
            if dir_path.exists():
                to_remove.append(dir_path)
                total_size += self._get_directory_size_bytes(dir_path)

        if not to_remove:
            logger.info("\n✅ 没有需要清理的目录")
            return {'status': 'completed', 'removed': 0, 'size_freed': '0B'}

        logger.info(f"\n📝 准备清理 {len(to_remove)} 个目录:")
        logger.info(f"   预计释放空间: {self._format_size(total_size)}")

        if dry_run:
            logger.info(f"\n💡 这是预览模式，使用 --execute 来实际执行清理")
            return {'status': 'preview', 'to_remove': len(to_remove), 'size': self._format_size(total_size)}

        if not force:
            logger.info(f"\n⚠️ 这将永久删除目录和文件！")
            response = input('确定要继续吗？(yes/no): ')
            if response.lower() != 'yes':
                logger.info('操作已取消')
                return {'status': 'cancelled'}

        # 执行删除
        logger.info(f"\n🗑️ 执行清理...")
        removed_count = 0
        for dir_path in to_remove:
            if self.safe_remove_directory(dir_path, dry_run=False):
                removed_count += 1

        return {
            'status': 'completed',
            'removed': removed_count,
            'total': len(to_remove),
            'size_freed': self._format_size(total_size)
        }

    def _get_directory_size_bytes(self, dir_path: Path) -> int:
        """获取目录字节大小"""
        try:
            total_size = 0
            for item in dir_path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
            return total_size
        except:
            return 0

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='最终清理')
    parser.add_argument('--execute', action='store_true', help='实际执行清理（默认为预览模式）')
    parser.add_argument('--force', action='store_true', help='强制执行，不询问确认')
    parser.add_argument('--base-dir', default='/Users/xujian/Athena工作平台', help='基础目录')
    parser.add_argument('--analyze', action='store_true', help='只分析结构，不清理')

    args = parser.parse_args()

    cleanup = FinalCleanup(args.base_dir)

    if args.analyze:
        cleanup.analyze_remaining_structure()
        return

    result = cleanup.execute_cleanup(dry_run=not args.execute, force=args.force)

    if result['status'] == 'preview':
        logger.info(f"\n💡 使用 --execute 参数来实际执行清理")
    elif result['status'] == 'completed':
        logger.info(f"\n✅ 清理完成")
        logger.info(f"   删除目录: {result['removed']}/{result['total']}")
        logger.info(f"   释放空间: {result['size_freed']}")
    elif result['status'] == 'cancelled':
        logger.info(f"\n❌ 清理已取消")

if __name__ == '__main__':
    main()