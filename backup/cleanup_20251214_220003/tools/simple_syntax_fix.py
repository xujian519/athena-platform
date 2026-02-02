#!/usr/bin/env python3
"""
简单的Python语法错误修复工具
"""

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

def fix_file_syntax(file_path: str) -> bool:
    """修复单个文件的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # 1. 修复未闭合的括号
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'unmatched' in line or 'unexpected' in line:
                # 尝试简单修复
                if line.count('(') > line.count(')'):
                    lines[i] = line + ')' * (line.count('(') - line.count(')'))
                elif line.count('[') > line.count(']'):
                    lines[i] = line + ']' * (line.count('[') - line.count(']'))
        
        content = '\n'.join(lines)
        
        # 2. 修复简单的语法错误
        content = re.sub(r':\s*:\s*', ': ', content)  # 双冒号
        content = re.sub(r'\[\s*\]', '[]', content)   # 空列表
        content = re.sub(r'\{\s*\}', '{}', content)   # 空字典
        
        # 3. 修复缩进
        lines = content.split('\n')
        for i in range(1, len(lines)):
            if lines[i-1].strip().endswith(':') and not lines[i].startswith(' ') and not lines[i].startswith('\t'):
                lines[i] = '    ' + lines[i]
        
        content = '\n'.join(lines)
        
        # 如果有修改，保存文件
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"✅ 修复: {file_path}")
            return True
        else:
            logger.info(f"- 无需修复: {file_path}")
            return False
            
    except Exception as e:
        logger.info(f"❌ 修复失败 {file_path}: {e}")
        return False

# 错误文件列表
error_files = [
    '/Users/xujian/Athena工作平台/patent-guideline-system/src/models/graph_schema.py',
    '/Users/xujian/Athena工作平台/domains/legal-ai/services/hybrid_clause_search.py',
    '/Users/xujian/Athena工作平台/core/search/patent_query_processor.py',
    '/Users/xujian/Athena工作平台/core/autonomous_control/xiaonuo_executor.py',
    '/Users/xujian/Athena工作平台/core/authenticity/zero_simulation_data_enforcer.py',
    '/Users/xujian/Athena工作平台/patent-platform/workspace/src/knowledge_graph/neo4j_manager.py',
    '/Users/xujian/Athena工作平台/patent-platform/workspace/src/tools/patent_tools/__init__.py',
    '/Users/xujian/Athena工作平台/patent-platform/workspace/src/action/workflow_orchestrator.py',
    '/Users/xujian/Athena工作平台/patent-platform/workspace/src/perception/enhanced_vector_database.py',
    '/Users/xujian/Athena工作平台/utils/patent-search/use_boolean_patent_search.py'
]

logger.info('开始修复Python语法错误...')
fixed_count = 0
for file_path in error_files:
    if os.path.exists(file_path):
        if fix_file_syntax(file_path):
            fixed_count += 1

logger.info(f"\n修复完成: {fixed_count}/{len(error_files)} 个文件")