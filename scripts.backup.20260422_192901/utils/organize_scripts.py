#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整理scripts目录，按功能分类脚本文件
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

def organize_scripts() -> Any:
    """整理scripts目录"""
    scripts_dir = Path('/Users/xujian/Athena工作平台/scripts')

    # 定义分类目录
    categories = {
        'patent_processing': {
            'description': '专利处理相关脚本',
            'patterns': [
                '*patent*', '*Patent*', 'patent_knowledge_graph_builder.py'
            ]
        },
        'neo4j_operations': {
            'description': 'Neo4j数据库操作脚本',
            'patterns': [
                '*neo4j*', '*Neo4j*', 'batch_import_to_neo4j.py',
                'bulk_import_to_neo4j.py', 'patent_kg_to_neo4j.py',
                'simple_patent_kg_import.py', 'check_neo4j_status.py'
            ]
        },
        'knowledge_graph': {
            'description': '知识图谱构建脚本',
            'patterns': [
                '*knowledge_graph*', '*kg*', '*KG*',
                'build_ai_terminology_complete_kg.py',
                'build_production_legal_kg.py'
            ]
        },
        'cleanup_maintenance': {
            'description': '清理和维护脚本',
            'patterns': [
                '*clean*', 'cleanup_*.py', 'auto_clean_redundant_files.py',
                'clean_backup_files.py', 'clean_duplicate_batches.py',
                'clean_redundant_files.py', 'monthly_cleanup.sh',
                'setup_monthly_cleanup.sh'
            ]
        },
        'optimization': {
            'description': '优化工具脚本',
            'patterns': [
                '*optim*', '*boost*', 'boost_patent_processing.py'
            ]
        },
        'monitoring': {
            'description': '监控工具脚本',
            'patterns': [
                '*monitor*', '*progress*', 'monitor_patent_progress.py'
            ]
        },
        'startup': {
            'description': '系统启动脚本',
            'patterns': [
                'start_*.sh', 'startup_*.sh', 'auto_patent_pipeline.sh'
            ]
        },
        'utilities': {
            'description': '通用工具脚本',
            'patterns': [
                'fix_*.py', 'organize_scripts.py', 'diagnose_*.py'
            ]
        },
        'migration': {
            'description': '数据迁移脚本',
            'patterns': [
                '*migrate*', '*migration*'
            ]
        }
    }

    # 创建分类目录
    for category_name, category_info in categories.items():
        category_dir = scripts_dir / category_name
        category_dir.mkdir(exist_ok=True)

        # 创建README文件
        readme_path = category_dir / 'README.md'
        if not readme_path.exists():
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"# {category_info['description']}\n\n")
                f.write(f"分类: {category_name}\n")
                f.write(f"说明: {category_info['description']}\n\n")

    # 遍历所有文件，进行分类
    moved_files = []
    skipped_files = []

    for file_path in scripts_dir.glob('*'):
        if file_path.is_file() and file_path.name not in ['organize_scripts.py']:
            file_name = file_path.name

            # 检查是否属于某个分类
            moved = False
            for category_name, category_info in categories.items():
                if any(file_name.startswith(p.replace('*', '')) or
                      file_name.endswith(p.replace('*', '')) or
                       file_name == p for p in category_info['patterns']):
                    # 移动文件
                    target_dir = scripts_dir / category_name
                    target_path = target_dir / file_name

                    # 如果目标文件已存在，跳过
                    if target_path.exists():
                        skipped_files.append((file_name, category_name, '目标文件已存在'))
                        moved = True
                        break

                    shutil.move(str(file_path), str(target_path))
                    moved_files.append((file_name, category_name))
                    moved = True
                    break

            if not moved:
                skipped_files.append((file_name, '未分类', '未匹配到任何分类'))

    # 输出报告
    logger.info('Scripts目录整理完成！')
    logger.info(f"✅ 成功移动文件数: {len(moved_files)}")
    logger.info(f"⚠️  跳过文件数: {len(skipped_files)}")

    if moved_files:
        logger.info("\n📁 移动的文件:")
        for file_name, category in moved_files:
            logger.info(f"  - {file_name} → {category}/")

    if skipped_files:
        logger.info("\n⚠️  跳过的文件:")
        for file_name, category, reason in skipped_files:
            logger.info(f"  - {file_name} ({reason})")

    # 创建总览文件
    overview_path = scripts_dir / 'SCRIPTS_OVERVIEW.md'
    with open(overview_path, 'w', encoding='utf-8') as f:
        f.write("# Scripts目录总览\n\n")
        f.write(f"整理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for category_name, category_info in categories.items():
            f.write(f"## {category_name}\n")
            f.write(f"- 说明: {category_info['description']}\n")

            category_dir = scripts_dir / category_name
            if category_dir.exists():
                files = [f.name for f in category_dir.glob('*.py') or category_dir.glob('*.sh')]
                if files:
                    f.write(f"- 文件数: {len(files)}\n")
                    f.write("- 文件列表:\n")
                    for file in sorted(files):
                        f.write(f"  - `{file}`\n")
            f.write("\n")

if __name__ == '__main__':
    from datetime import datetime
    organize_scripts()