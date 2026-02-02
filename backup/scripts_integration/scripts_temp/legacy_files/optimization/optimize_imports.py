#!/usr/bin/env python3
"""
优化Python文件导入语句
"""

import logging
import os
import subprocess
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


def optimize_imports_with_isort(file_path: Path) -> bool:
    """使用isort优化导入"""
    try:
        result = subprocess.run(
            ['python3', '-m', 'isort', str(file_path), '--profile', 'black', '--quiet'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return True
        else:
            logger.error(f"isort失败 {file_path}: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"优化导入失败 {file_path}: {str(e)}")
        return False


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent.parent
    logger.info(f"开始优化导入语句...")

    # 查找所有Python文件
    python_files = find_python_files(project_root)
    logger.info(f"找到 {len(python_files)} 个Python文件")

    # 优化导入
    optimized_count = 0
    for i, file_path in enumerate(python_files, 1):
        if i % 50 == 0:
            logger.info(f"进度: {i}/{len(python_files)}")

        if optimize_imports_with_isort(file_path):
            optimized_count += 1

    logger.info(f"\n✅ 优化完成！")
    logger.info(f"📊 优化了 {optimized_count} 个文件的导入语句")


if __name__ == '__main__':
    main()