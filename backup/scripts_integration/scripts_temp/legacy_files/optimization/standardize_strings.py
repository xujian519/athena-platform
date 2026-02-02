#!/usr/bin/env python3
"""
统一Python字符串格式为单引号
"""

import logging
import re
from pathlib import Path
from typing import List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_python_files(root_dir: Path) -> List[Path]:
    """查找所有Python文件"""
    python_files = []
    for py_file in root_dir.rglob('*.py'):
        # 跳过一些目录
        if any(part in py_file.parts for part in [
            '__pycache__', '.venv', 'venv', 'node_modules',
            '.git', 'dist', 'build', 'migrations'
        ]):
            continue
        python_files.append(py_file)
    return python_files


def standardize_strings_in_file(file_path: Path) -> int:
    """标准化文件中的字符串格式"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changed_count = 0

        # 将双引号字符串替换为单引号
        # 注意：不要处理以下情况：
        # 1. f-string（保留双引号或单引号原样）
        # 2. 文档字符串（"""..."""）
        # 3. 包含转义单引号的字符串
        # 4. SQL查询中的字符串（可能需要保留双引号）

        lines = content.split('\n')
        new_lines = []

        for line_num, line in enumerate(lines, 1):
            new_line = line

            # 跳过注释和文档字符串行
            if not line.strip().startswith('#') and '"""' not in line and "'''" not in line:
                # 查找并替换双引号字符串
                # 这个正则表达式匹配普通的双引号字符串
                # 避免匹配f-string和复杂字符串
                pattern = r'(?<!f)(?<!r)(?<!u)(?<!b)'([^'\\]*(\\.[^"\\]*)*)"'
                matches = list(re.finditer(pattern, new_line))

                # 从后往前替换，避免位置偏移
                for match in reversed(matches):
                    # 检查字符串内容是否包含单引号
                    text = match.group(1)
                    if "'" not in text and not ('\\' in text):
                        # 执行替换
                        start, end = match.span()
                        new_line = new_line[:start] + "'" + text + "'" + new_line[end:]
                        changed_count += 1

            new_lines.append(new_line)

        if changed_count > 0:
            content = '\n'.join(new_lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return changed_count

    except Exception as e:
        logger.error(f"标准化字符串失败 {file_path}: {str(e)}")
        return 0


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent.parent
    logger.info('开始标准化字符串格式...')

    # 查找所有Python文件
    python_files = find_python_files(project_root)
    logger.info(f"找到 {len(python_files)} 个Python文件")

    # 标准化字符串
    total_changes = 0
    processed_files = 0

    for i, file_path in enumerate(python_files, 1):
        if i % 50 == 0:
            logger.info(f"进度: {i}/{len(python_files)}")

        changes = standardize_strings_in_file(file_path)
        if changes > 0:
            total_changes += changes
            processed_files += 1

    logger.info(f"\n✅ 标准化完成！")
    logger.info(f"📊 处理了 {processed_files} 个文件")
    logger.info(f"🔄 总共修改了 {total_changes} 处字符串")


if __name__ == '__main__':
    main()