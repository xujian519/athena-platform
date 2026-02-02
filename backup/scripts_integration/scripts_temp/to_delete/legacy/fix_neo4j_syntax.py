#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复Neo4j约束语法错误
将旧版语法 ON ... ASSERT 改为新版语法 FOR ... REQUIRE
"""

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

def fix_neo4j_constraints_in_file(file_path):
    """修复单个文件中的Neo4j约束语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 统计修复数量
        original_content = content

        # 正则表达式匹配旧版约束语法
        # CREATE CONSTRAINT [IF NOT EXISTS] ON (label) ASSERT property IS [NOT] UNIQUE
        pattern = r'(CREATE CONSTRAINT\s+(IF NOT EXISTS\s+)?)(ON\s+)\(([^)]+)\)(\s+ASSERT\s+)([a-zA-Z_][a-zA-Z0-9_.]*)(\s+IS\s+)(NOT\s+)?UNIQUE'

        # 替换为新版语法
        def replacer(match):
            return f"{match.group(1)}FOR {match.group(4)} REQUIRE {match.group(6)} {match.group(8)}UNIQUE"

        new_content = re.sub(pattern, replacer, content, flags=re.IGNORECASE)

        # 如果内容有变化，写回文件
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True

        return False

    except Exception as e:
        logger.info(f"处理文件 {file_path} 时出错: {e}")
        return False

def fix_all_neo4j_files():
    """修复所有文件中的Neo4j语法"""
    base_dir = Path('/Users/xujian/Athena工作平台')

    # 文件扩展名模式
    patterns = ['*.py', '*.cypher', '*.cql']

    fixed_files = []

    logger.info('🔧 开始修复Neo4j约束语法...')

    for pattern in patterns:
        logger.info(f"\n📁 搜索 {pattern} 文件...")

        for file_path in base_dir.rglob(pattern):
            # 跳过某些目录
            if any(skip in str(file_path) for skip in ['.git', '__pycache__', 'venv', 'node_modules']):
                continue

            # 检查文件是否包含旧版语法
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if re.search(r'CREATE CONSTRAINT.*ON.*ASSERT', content, re.IGNORECASE):
                    logger.info(f"  修复: {file_path.relative_to(base_dir)}")
                    if fix_neo4j_constraints_in_file(file_path):
                        fixed_files.append(file_path)

            except Exception as e:
                logger.info(f"  ❌ 错误处理 {file_path}: {e}")

    logger.info(f"\n✅ 修复完成！")
    logger.info(f"   修复文件数: {len(fixed_files)}")

    if fixed_files:
        logger.info(f"\n📋 修复的文件列表:")
        for i, file_path in enumerate(fixed_files, 1):
            rel_path = str(file_path.relative_to(base_dir))
            logger.info(f"   {i:2d}. {rel_path}")

    return fixed_files

def main():
    """主函数"""
    logger.info(str('=' * 60))
    logger.info('Neo4j约束语法修复工具')
    logger.info('将旧版语法 ON ... ASSERT 改为新版语法 FOR ... REQUIRE')
    logger.info(str('=' * 60))

    fixed_files = fix_all_neo4j_files()

    logger.info(str("\n" + '=' * 60))
    logger.info('修复任务完成')
    logger.info(str('=' * 60))

if __name__ == '__main__':
    main()