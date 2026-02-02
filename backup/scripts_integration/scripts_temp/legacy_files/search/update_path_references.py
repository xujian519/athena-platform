#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径引用更新脚本
Update Path References Script

用于在目录整合后更新所有文件中的路径引用
"""

import glob
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class PathReferenceUpdater:
    """路径引用更新器"""

    def __init__(self, base_dir: str = '/Users/xujian/Athena工作平台'):
        self.base_dir = Path(base_dir)

        # 路径映射表：旧路径 -> 新路径
        self.path_mappings = {
            # 专利相关目录映射
            'patent_retrieval_system': 'patent-platform/core',
            'patent_agent': 'patent-platform/agent',
            'patent_workspace': 'patent-platform/workspace',
            'patents_downloads': 'patent-platform/data',

            # 部署相关目录映射
            'deploy/': 'deployment/',
            'deployment/': 'deployment/',  # 避免重复替换
            'deployments/': 'deployment/',
            'docker/': 'deployment/docker/',
            'nginx/': 'deployment/nginx/',

            # 文档相关目录映射
            'docs/': 'documentation/',
            "docs\\": "documentation\\",  # Windows路径
            'logs/': 'documentation/logs/',
        }

        # 需要更新的文件类型
        self.file_patterns = [
            '**/*.py',
            '**/*.sh',
            '**/*.yaml',
            '**/*.yml',
            '**/*.json',
            '**/*.conf',
            '**/*.cfg',
            '**/*.ini',
            '**/*.md'
        ]

    def find_files_to_update(self) -> List[Path]:
        """查找需要更新的文件"""
        files_to_update = []

        for pattern in self.file_patterns:
            for file_path in self.base_dir.glob(pattern):
                # 跳过新整合目录中的文件（避免循环更新）
                if self._should_skip_file(file_path):
                    continue

                # 检查文件是否包含旧路径
                if self._file_contains_old_paths(file_path):
                    files_to_update.append(file_path)

        return files_to_update

    def _should_skip_file(self, file_path: Path) -> bool:
        """判断是否应该跳过文件"""
        skip_patterns = [
            'deployment/',
            'patent-platform/',
            'documentation/',
            'ai-projects/',
            'dev-tools/',
            'monitoring/',
            '__pycache__/',
            '.git/',
            'node_modules/'
        ]

        file_str = str(file_path.relative_to(self.base_dir))
        return any(pattern in file_str for pattern in skip_patterns)

    def _file_contains_old_paths(self, file_path: Path) -> bool:
        """检查文件是否包含旧路径"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return any(old_path in content for old_path in self.path_mappings.keys())
        except Exception as e:
            logger.info(f"⚠️ 无法读取文件 {file_path}: {e}")
            return False

    def update_file(self, file_path: Path) -> Tuple[bool, int]:
        """更新单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            updated_content = original_content
            update_count = 0

            # 应用路径映射
            for old_path, new_path in self.path_mappings.items():
                # 使用正则表达式进行路径替换
                pattern = re.compile(re.escape(old_path))
                matches = pattern.findall(updated_content)
                if matches:
                    updated_content = pattern.sub(new_path, updated_content)
                    update_count += len(matches)

            # 如果有更新，写入文件
            if updated_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                return True, update_count

            return False, 0

        except Exception as e:
            logger.info(f"❌ 更新文件失败 {file_path}: {e}")
            return False, 0

    def update_all_files(self, dry_run: bool = True) -> Dict:
        """更新所有文件"""
        logger.info(f"🔍 搜索需要更新的文件...")
        files_to_update = self.find_files_to_update()

        logger.info(f"📝 找到 {len(files_to_update)} 个文件需要更新")

        if dry_run:
            logger.info('🔍 这是一个预览模式，不会实际修改文件')
            for file_path in files_to_update:
                logger.info(f"  - {file_path.relative_to(self.base_dir)}")
            return {'preview': True, 'files': files_to_update}

        # 实际更新
        logger.info(f"🔄 开始更新文件...")
        updated_files = []
        total_updates = 0

        for file_path in files_to_update:
            updated, count = self.update_file(file_path)
            if updated:
                updated_files.append(file_path)
                total_updates += count
                logger.info(f"  ✅ {file_path.relative_to(self.base_dir)} ({count} 处更新)")

        return {
            'preview': False,
            'updated_files': updated_files,
            'total_files': len(updated_files),
            'total_updates': total_updates
        }

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='更新路径引用')
    parser.add_argument('--execute', action='store_true', help='实际执行更新（默认为预览模式）')
    parser.add_argument('--base-dir', default='/Users/xujian/Athena工作平台', help='基础目录')

    args = parser.parse_args()

    updater = PathReferenceUpdater(args.base_dir)
    result = updater.update_all_files(dry_run=not args.execute)

    if result['preview']:
        logger.info(f"\n💡 使用 --execute 参数来实际执行更新")
    else:
        logger.info(f"\n✅ 更新完成")
        logger.info(f"   更新文件数: {result['total_files']}")
        logger.info(f"   总更新处数: {result['total_updates']}")

if __name__ == '__main__':
    main()