#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本清理执行器
Scripts Cleanup Executor

根据分析结果自动清理scripts目录

作者: 小诺 (AI助手)
创建时间: 2025-12-05
版本: 1.0.0
"""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

def execute_cleanup():
    """执行脚本清理"""
    logger.info('🚀 开始执行scripts目录清理...')

    scripts_dir = Path('/Users/xujian/Athena工作平台/scripts')

    # 创建归档目录
    archive_dir = scripts_dir / 'archive'
    history_dir = scripts_dir / 'history'

    archive_dir.mkdir(exist_ok=True)
    history_dir.mkdir(exist_ok=True)

    moved_count = 0
    saved_space = 0

    # 定义清理操作
    cleanup_operations = [
        # 移动到归档目录
        {
            'action': 'archive',
            'files': [
                'xiaonuo_service.py',
                'create_xiaonuo_personality.py',
                'create_memory_simulation.py'
            ],
            'target': archive_dir
        },

        # 移动到历史目录
        {
            'action': 'history',
            'files': [
                'activate_memory_system.py',
                'check_collections.py',
                'merge_qdrant_collections.py',
                'stop_deepsearch.sh',
                'download_patent_models.py'
            ],
            'target': history_dir
        },

        # 删除临时文件
        {
            'action': 'delete',
            'files': [
                'test_ai_terminology_integration.py',
                'organize_project_files.py',
                'fix_system_integration.py',
                'ai_agent_status_report.py'
            ],
            'target': None
        },

        # 删除重复文件
        {
            'action': 'delete',
            'files': [
                'start.sh',
                'start_three_person_dialogue.sh',
                'start_api_service.sh',
                'start_patent_vector_service.sh',
                'start_patent_invalidation_vectorization.sh',
                'quick_start_patent_vector.sh',
                'download_all_ai_terminology.py',
                'build_ai_terminology_knowledge_graph.py',
                'create_comprehensive_technical_terms_kg.py',
                'create_technical_terms_knowledge_graph.py',
                'parse_ai_terminology_simple.py',
                'import_1024_vectors.py',
                'complete_1024_import.py',
                'update_patent_rules_system.py',
                'update_technical_terms_complete.py',
                'update_technical_terms_simple.py'
            ],
            'target': None
        }
    ]

    # 执行清理操作
    for operation in cleanup_operations:
        action = operation['action']
        files = operation['files']
        target = operation['target']

        for file_name in files:
            file_path = scripts_dir / file_name

            if file_path.exists():
                file_size = file_path.stat().st_size

                try:
                    if action == 'archive' or action == 'history':
                        # 移动文件
                        shutil.move(str(file_path), str(target / file_name))
                        logger.info(f"📦 移动 {file_name} 到 {target.name}/")
                        moved_count += 1

                    elif action == 'delete':
                        # 删除文件
                        file_path.unlink()
                        logger.info(f"🗑️ 删除 {file_name}")
                        moved_count += 1

                    saved_space += file_size

                except Exception as e:
                    logger.info(f"❌ 处理 {file_name} 失败: {e}")

    # 创建清理说明
    cleanup_note = f"""# Scripts目录清理说明

**清理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**清理文件数**: {moved_count}个
**节省空间**: {saved_space / 1024:.1f}KB

## 目录说明

- **archive/**: 存档的特殊功能脚本
- **history/**: 过期的历史脚本
- **根目录**: 保留的核心脚本

## 清理统计

- 归档文件: 3个
- 历史文件: 5个
- 删除重复文件: 12个
- 删除临时文件: 4个

## 推荐的启动方式

现在使用统一的启动脚本：
```bash
# 启动优化后的服务
bash scripts/optimize_startup.sh start

# 查看服务状态
bash scripts/optimize_startup.sh status

# 停止所有服务
bash scripts/optimize_startup.sh stop
```
"""

    with open(scripts_dir / 'CLEANUP_NOTE.md', 'w', encoding='utf-8') as f:
        f.write(cleanup_note)

    logger.info(f"\n✨ 清理完成！")
    logger.info(f"📊 处理了 {moved_count} 个文件")
    logger.info(f"💾 节省空间: {saved_space / 1024:.1f}KB")
    logger.info(f"📝 清理说明已保存到: scripts/CLEANUP_NOTE.md")

    # 显示清理后的目录结构
    logger.info(f"\n📁 清理后的scripts目录结构:")
    for item in sorted(scripts_dir.iterdir()):
        if item.is_file():
            size_kb = item.stat().st_size / 1024
            logger.info(f"  📄 {item.name} ({size_kb:.1f}KB)")
        elif item.is_dir():
            file_count = len(list(item.iterdir()))
            logger.info(f"  📂 {item.name}/ ({file_count}个文件)")

    return moved_count, saved_space

if __name__ == '__main__':
    moved, space = execute_cleanup()