#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整目录迁移脚本
Complete Directory Migration Script

完成剩余的目录迁移工作，将原始目录内容移动到新的整合目录中
"""

import argparse
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)

class CompleteDirectoryMigration:
    """完整目录迁移器"""

    def __init__(self, base_dir: str = '/Users/xujian/Athena工作平台'):
        self.base_dir = Path(base_dir)

        # 完整的迁移映射
        self.migration_plan = {
            # 专利相关目录迁移
            'patent_retrieval_system': {
                'target': 'patent-platform/core',
                'action': 'move',
                'description': '专利检索系统 -> patent-platform核心'
            },
            'patent_agent': {
                'target': 'patent-platform/agent',
                'action': 'move',
                'description': '专利代理 -> patent-platform代理'
            },
            'patent_workspace': {
                'target': 'patent-platform/workspace',
                'action': 'merge',
                'description': '专利工作空间 -> 合并到patent-platform工作空间'
            },

            # 部署相关目录迁移（剩余内容）
            'docker': {
                'target': 'deployment/docker',
                'action': 'merge',
                'description': 'Docker配置 -> 合并到deployment/docker'
            },

            # 文档相关目录迁移
            'docs': {
                'target': 'documentation',
                'action': 'merge',
                'description': '文档 -> 合并到documentation'
            },
            'logs': {
                'target': 'documentation/logs',
                'action': 'move',
                'description': '日志 -> documentation/logs'
            }
        }

        # 保护目录：不要迁移
        self.protected_directories = {
            '论文', '工作', 'scripts', 'core', 'services', 'config', 'data',
            'deployment', 'patent-platform', 'documentation', 'ai-projects',
            'dev-tools', 'monitoring', '.git', '.claude', '.github', '.system',
            '.workspace', 'models', 'database', 'storage', 'projects'
        }

    def check_migration_feasibility(self) -> Dict:
        """检查迁移可行性"""
        logger.info('🔍 检查迁移可行性...')

        analysis = {
            'ready_to_migrate': [],
            'needs_manual_review': [],
            'conflicts': [],
            'missing_targets': []
        }

        for source_dir, config in self.migration_plan.items():
            source_path = self.base_dir / source_dir
            target_path = self.base_dir / config['target']

            # 检查源目录
            if not source_path.exists():
                analysis['missing_targets'].append(f"源目录不存在: {source_dir}")
                continue

            # 检查目标目录
            if not target_path.exists():
                analysis['missing_targets'].append(f"目标目录不存在: {config['target']}")
                continue

            # 检查文件冲突
            source_files = set(f.name for f in source_path.rglob('*') if f.is_file())
            target_files = set(f.name for f in target_path.rglob('*') if f.is_file())

            conflicts = source_files & target_files
            if conflicts:
                analysis['conflicts'].append({
                    'source': source_dir,
                    'target': config['target'],
                    'conflicts': list(conflicts)[:5]  # 只显示前5个
                })

            # 根据文件数量决定是否需要人工审查
            source_file_count = len(source_files)
            if source_file_count > 100:
                analysis['needs_manual_review'].append({
                    'dir': source_dir,
                    'file_count': source_file_count,
                    'reason': '文件过多，需要仔细检查'
                })
            elif conflicts:
                analysis['needs_manual_review'].append({
                    'dir': source_dir,
                    'file_count': source_file_count,
                    'reason': f"存在{len(conflicts)}个文件冲突"
                })
            else:
                analysis['ready_to_migrate'].append(source_dir)

        return analysis

    def migrate_directory(self, source_dir: str, config: Dict, dry_run: bool = True) -> bool:
        """迁移单个目录"""
        source_path = self.base_dir / source_dir
        target_path = self.base_dir / config['target']

        try:
            if dry_run:
                logger.info(f"🔍 [{config['action'].upper()}] {source_dir} -> {config['target']}")
                return True

            if not source_path.exists():
                logger.info(f"⚠️ 源目录不存在: {source_dir}")
                return False

            logger.info(f"🔄 [{config['action'].upper()}] {source_dir} -> {config['target']}")

            if config['action'] == 'move':
                # 移动整个目录
                if target_path.exists():
                    # 合并到目标目录
                    for item in source_path.iterdir():
                        target_item = target_path / item.name
                        if target_item.exists():
                            logger.info(f"  ⚠️ 跳过已存在: {item.name}")
                            continue

                        if item.is_file():
                            shutil.copy2(item, target_item)
                        elif item.is_dir():
                            shutil.copytree(item, target_item)
                    logger.info(f"  ✅ 已合并内容，保留原目录结构")
                else:
                    shutil.move(str(source_path), str(target_path))
                    logger.info(f"  ✅ 已移动整个目录")

            elif config['action'] == 'merge':
                # 合并内容
                for item in source_path.iterdir():
                    target_item = target_path / item.name

                    if target_item.exists():
                        if item.is_file() and target_item.is_file():
                            # 文件冲突，检查内容是否相同
                            if item.stat().st_size == target_item.stat().st_size:
                                logger.info(f"  ⚠️ 跳过相同大小文件: {item.name}")
                                continue
                            else:
                                # 重命名
                                counter = 1
                                while target_item.exists():
                                    stem = item.stem
                                    suffix = item.suffix
                                    new_name = f"{stem}_conflict_{counter}{suffix}"
                                    target_item = target_path / new_name
                                    counter += 1
                                logger.info(f"  ⚠️ 重命名冲突文件: {item.name} -> {new_name}")

                        if item.is_file():
                            shutil.copy2(item, target_item)
                        elif item.is_dir():
                            if not target_item.exists():
                                shutil.copytree(item, target_item)
                            else:
                                # 递归合并子目录
                                self._merge_directories(item, target_item)

                logger.info(f"  ✅ 已合并内容")

            return True

        except Exception as e:
            logger.info(f"  ❌ 迁移失败: {e}")
            return False

    def _merge_directories(self, source: Path, target: Path):
        """递归合并目录"""
        for item in source.iterdir():
            target_item = target / item.name

            if item.is_file():
                shutil.copy2(item, target_item)
            elif item.is_dir():
                if not target_item.exists():
                    shutil.copytree(item, target_item)
                else:
                    self._merge_directories(item, target_item)

    def cleanup_empty_directory(self, dir_path: Path):
        """清理空目录"""
        try:
            if dir_path.exists() and dir_path.is_dir():
                # 检查是否为空
                items = list(dir_path.iterdir())
                if not items:
                    dir_path.rmdir()
                    logger.info(f"  🗑️ 已删除空目录: {dir_path.name}")
                    return True
        except Exception as e:
            logger.info(f"  ⚠️ 无法删除目录 {dir_path}: {e}")
        return False

    def complete_migration(self, dry_run: bool = True, force: bool = False) -> Dict:
        """完成迁移"""
        logger.info('🚀 开始完整目录迁移...')

        # 首先检查可行性
        analysis = self.check_migration_feasibility()

        logger.info(f"\n📊 迁移分析结果:")
        logger.info(f"  可以直接迁移: {len(analysis['ready_to_migrate'])} 个目录")
        logger.info(f"  需要人工审查: {len(analysis['needs_manual_review'])} 个目录")
        logger.info(f"  存在文件冲突: {len(analysis['conflicts'])} 个目录")
        logger.info(f"  目标不存在: {len(analysis['missing_targets'])} 个问题")

        if analysis['conflicts']:
            logger.info(f"\n⚠️ 文件冲突详情:")
            for conflict in analysis['conflicts']:
                logger.info(f"  {conflict['source']} -> {conflict['target']}: {conflict['conflicts']}")

        if analysis['needs_manual_review']:
            logger.info(f"\n🔍 需要人工审查的目录:")
            for review in analysis['needs_manual_review']:
                logger.info(f"  {review['dir']}: {review['file_count']} 个文件 ({review['reason']})")

        if dry_run:
            logger.info(f"\n💡 这是预览模式，使用 --execute 来实际执行迁移")
            return {'status': 'preview', 'analysis': analysis}

        if not force:
            logger.info(f"\n⚠️ 这将移动/合并目录内容！")
            response = input('确定要继续吗？(yes/no): ')
            if response.lower() != 'yes':
                logger.info('操作已取消')
                return {'status': 'cancelled'}

        # 执行迁移
        logger.info(f"\n🔄 执行迁移...")
        migrated_count = 0
        failed_migrations = []

        for source_dir, config in self.migration_plan.items():
            if self.migrate_directory(source_dir, config, dry_run=False):
                migrated_count += 1

                # 尝试清理空目录
                source_path = self.base_dir / source_dir
                if self.cleanup_empty_directory(source_path):
                    logger.info(f"  ✅ {source_dir} 迁移并清理完成")
                else:
                    logger.info(f"  ✅ {source_dir} 迁移完成（保留原目录）")
            else:
                failed_migrations.append(source_dir)

        return {
            'status': 'completed',
            'migrated': migrated_count,
            'failed': failed_migrations,
            'total': len(self.migration_plan)
        }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='完成目录迁移')
    parser.add_argument('--execute', action='store_true', help='实际执行迁移（默认为预览模式）')
    parser.add_argument('--force', action='store_true', help='强制执行，不询问确认')
    parser.add_argument('--base-dir', default='/Users/xujian/Athena工作平台', help='基础目录')

    args = parser.parse_args()

    migration = CompleteDirectoryMigration(args.base_dir)
    result = migration.complete_migration(dry_run=not args.execute, force=args.force)

    if result['status'] == 'preview':
        logger.info(f"\n💡 使用 --execute 参数来实际执行迁移")
    elif result['status'] == 'completed':
        logger.info(f"\n✅ 迁移完成")
        logger.info(f"   成功迁移: {result['migrated']}/{result['total']} 个目录")
        if result['failed']:
            logger.info(f"   失败: {result['failed']}")
    elif result['status'] == 'cancelled':
        logger.info(f"\n❌ 迁移已取消")

if __name__ == '__main__':
    main()