#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原始目录清理脚本
Original Directory Cleanup Script

用于安全清理已整合到新目录的原始分散目录
"""

import argparse
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class OriginalDirectoryCleanup:
    """原始目录清理器"""

    def __init__(self, base_dir: str = '/Users/xujian/Athena工作平台'):
        self.base_dir = Path(base_dir)

        # 原始目录到新目录的映射
        self.directory_mappings = {
            # 部署相关目录
            'deploy': 'deployment',
            'deployments': 'deployment',
            'docker': 'deployment/docker',
            'nginx': 'deployment/nginx',

            # 专利相关目录
            'patent_retrieval_system': 'patent-platform/core',
            'patent_agent': 'patent-platform/agent',
            'patent_workspace': 'patent-platform/workspace',
            'patents_downloads': 'patent-platform/data',

            # 文档相关目录（部分已经移动）
            # 注意：logs 目录需要特别小心，因为可能包含正在使用的日志
        }

        # 保护目录：永远不要删除
        self.protected_directories = {
            '论文',  # 用户特别指定的保护目录
            '工作',  # 用户特别指定的保护目录
            'scripts',  # 核心脚本目录
            'core',    # 核心功能目录
            'services', # 服务目录
            'config',  # 配置目录
            'data',    # 数据目录
            'deployment',  # 新的整合目录
            'patent-platform',  # 新的整合目录
            'documentation',  # 新的整合目录
            'ai-projects',  # 新的整合目录
            'dev-tools',  # 新的整合目录
            'monitoring',  # 新的整合目录
        }

    def check_directory_safety(self, dir_path: Path) -> Tuple[bool, str]:
        """检查目录是否可以安全删除"""
        dir_name = dir_path.name

        # 检查是否为保护目录
        if dir_name in self.protected_directories:
            return False, f"保护目录，不允许删除: {dir_name}"

        # 检查目录是否为空
        if not dir_path.exists():
            return True, '目录不存在，可以跳过'

        # 检查目录内容
        try:
            items = list(dir_path.iterdir())
            if not items:
                return True, '空目录，可以安全删除'
        except PermissionError:
            return False, f"权限不足，无法访问: {dir_path}"

        # 检查是否有重要文件
        important_patterns = [
            '*.py',
            '*.sh',
            '*.yaml',
            '*.yml',
            '*.json',
            '*.conf',
            'README*',
            '*.md'
        ]

        important_files = []
        for item in items:
            if item.is_file() and any(item.match(pattern) for pattern in important_patterns):
                important_files.append(item.name)

        if important_files:
            return False, f"包含重要文件，需要仔细检查: {important_files[:5]}"

        return True, '可以安全删除'

    def get_cleanup_candidates(self) -> List[Tuple[Path, str, str]]:
        """获取可以清理的目录列表"""
        candidates = []

        for old_dir_name, new_dir_path in self.directory_mappings.items():
            old_dir_path = self.base_dir / old_dir_name

            if not old_dir_path.exists():
                continue

            is_safe, reason = self.check_directory_safety(old_dir_path)
            if is_safe:
                candidates.append((old_dir_path, new_dir_path, reason))
            else:
                logger.info(f"⚠️ 跳过 {old_dir_name}: {reason}")

        return candidates

    def cleanup_directory(self, dir_path: Path, dry_run: bool = True) -> bool:
        """清理单个目录"""
        try:
            if not dir_path.exists():
                return True

            if dry_run:
                logger.info(f"🔍 将删除目录: {dir_path.relative_to(self.base_dir)}")
                return True

            # 实际删除
            if dir_path.is_dir():
                shutil.rmtree(dir_path)
                logger.info(f"✅ 已删除目录: {dir_path.relative_to(self.base_dir)}")
                return True
            elif dir_path.is_file():
                dir_path.unlink()
                logger.info(f"✅ 已删除文件: {dir_path.relative_to(self.base_dir)}")
                return True

        except Exception as e:
            logger.info(f"❌ 删除失败 {dir_path}: {e}")
            return False

        return False

    def cleanup_all(self, dry_run: bool = True, force: bool = False) -> Dict:
        """清理所有原始目录"""
        logger.info('🔍 检查可以清理的目录...')
        candidates = self.get_cleanup_candidates()

        if not candidates:
            logger.info('✅ 没有找到可以清理的目录')
            return {'success': True, 'cleaned': 0, 'candidates': 0}

        logger.info(f"📝 找到 {len(candidates)} 个可以清理的目录:")

        for dir_path, new_dir_path, reason in candidates:
            rel_path = dir_path.relative_to(self.base_dir)
            logger.info(f"  - {rel_path} -> {new_dir_path} ({reason})")

        if not force and not dry_run:
            logger.info("\n⚠️ 这是一个破坏性操作！")
            response = input('确定要继续吗？(yes/no): ')
            if response.lower() != 'yes':
                logger.info('操作已取消')
                return {'success': False, 'cleaned': 0, 'candidates': len(candidates)}

        if dry_run:
            logger.info("\n💡 这是预览模式，使用 --execute 参数来实际执行清理")
            return {'success': True, 'cleaned': 0, 'candidates': len(candidates), 'dry_run': True}

        logger.info(f"\n🧹 开始清理原始目录...")
        cleaned_count = 0

        for dir_path, new_dir_path, reason in candidates:
            if self.cleanup_directory(dir_path, dry_run=False):
                cleaned_count += 1

        return {
            'success': True,
            'cleaned': cleaned_count,
            'candidates': len(candidates),
            'dry_run': False
        }

    def analyze_remaining_directories(self):
        """分析剩余的目录结构"""
        logger.info("\n📊 当前目录结构分析:")

        # 统计各类目录
        categories = {
            '核心目录': ['scripts', 'core', 'services', 'config', 'data'],
            '整合目录': ['deployment', 'patent-platform', 'documentation', 'ai-projects', 'dev-tools', 'monitoring'],
            '项目目录': ['projects', 'prototypes', 'apps'],
            '保留目录': ['论文', '工作'],
            '其他目录': []
        }

        category_counts = {cat: 0 for cat in categories.keys()}

        for item in self.base_dir.iterdir():
            if not item.is_dir() or item.name.startswith('.'):
                continue

            categorized = False
            for category, dirs in categories.items():
                if item.name in dirs:
                    category_counts[category] += 1
                    categorized = True
                    break

            if not categorized:
                categories['其他目录'].append(item.name)
                category_counts['其他目录'] += 1

        for category, count in category_counts.items():
            if category == '其他目录':
                logger.info(f"  {category}: {count} 个")
                for dir_name in categories[category][:10]:  # 只显示前10个
                    logger.info(f"    - {dir_name}")
                if len(categories[category]) > 10:
                    logger.info(f"    ... 还有 {len(categories[category]) - 10} 个")
            else:
                logger.info(f"  {category}: {count} 个")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='清理原始目录')
    parser.add_argument('--execute', action='store_true', help='实际执行清理（默认为预览模式）')
    parser.add_argument('--force', action='store_true', help='强制执行，不询问确认')
    parser.add_argument('--base-dir', default='/Users/xujian/Athena工作平台', help='基础目录')
    parser.add_argument('--analyze', action='store_true', help='分析当前目录结构')

    args = parser.parse_args()

    cleanup = OriginalDirectoryCleanup(args.base_dir)

    if args.analyze:
        cleanup.analyze_remaining_directories()
        return

    result = cleanup.cleanup_all(dry_run=not args.execute, force=args.force)

    if result['dry_run']:
        logger.info(f"\n💡 使用 --execute 参数来实际执行清理")
    elif result['success']:
        logger.info(f"\n✅ 清理完成")
        logger.info(f"   清理目录数: {result['cleaned']}/{result['candidates']}")
    else:
        logger.info(f"\n❌ 清理未完成")

if __name__ == '__main__':
    main()