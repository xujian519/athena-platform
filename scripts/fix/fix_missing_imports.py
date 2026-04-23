#!/usr/bin/env python3
"""
自动修复缺失的导入语句

用法:
    python3 scripts/fix_missing_imports.py --dry-run     # 预览修复
    python3 scripts/fix_missing_imports.py --execute     # 执行修复
    python3 scripts/fix_missing_imports.py --verify      # 验证修复
"""

import argparse
import re
import sys
from pathlib import Path

# 导入映射表：检测变量名到应添加的导入语句
IMPORT_MAPPING = {
    'np': ('import numpy as np', 'numpy'),
    'numpy': ('import numpy', 'numpy'),
    'st': ('import streamlit as st', 'streamlit'),
    'streamlit': ('import streamlit', 'streamlit'),
    'nx': ('import networkx as nx', 'networkx'),
    'networkx': ('import networkx', 'networkx'),
    'pd': ('import pandas as pd', 'pandas'),
    'pandas': ('import pandas', 'pandas'),
    'plt': ('import matplotlib.pyplot as plt', 'matplotlib'),
    'sns': ('import seaborn as sns', 'seaborn'),
    'torch': ('import torch', 'torch'),
    'tf': ('import tensorflow as tf', 'tensorflow'),
    'sp': ('import spacy', 'spacy'),
    'PIL': ('from PIL import Image', 'PIL'),
    'cv2': ('import cv2', 'opencv-python'),
    'requests': ('import requests', 'requests'),
    'httpx': ('import httpx', 'httpx'),
    'aiohttp': ('import aiohttp', 'aiohttp'),
}

# typing导入映射
TYPING_IMPORTS = {
    'Dict': 'from typing import Dict',
    'List': 'from typing import List',
    'Set': 'from typing import Set',
    'Tuple': 'from typing import Tuple',
    'Optional': 'from typing import Optional',
    'Union': 'from typing import Union',
    'Any': 'from typing import Any',
    'Callable': 'from typing import Callable',
    'Type': 'from typing import Type',
    'TypeVar': 'from typing import TypeVar',
    'Generic': 'from typing import Generic',
    'Protocol': 'from typing import Protocol',
    'Literal': 'from typing import Literal',
    'Final': 'from typing import Final',
}

# 标准库映射
STDLIB_IMPORTS = {
    'os': 'import os',
    'sys': 'import sys',
    'json': 'import json',
    're': 'import re',
    'datetime': 'import datetime',
    'time': 'import time',
    'logging': 'import logging',
    'pathlib': 'from pathlib import Path',
    'collections': 'import collections',
    'itertools': 'import itertools',
    'functools': 'import functools',
    'copy': 'import copy',
    'random': 'import random',
    'math': 'import math',
    'hashlib': 'import hashlib',
    'base64': 'import base64',
    'uuid': 'import uuid',
}


def detect_undefined_variables(file_path: Path) -> set[str]:
    """检测文件中使用的未定义变量"""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        return set()

    undefined_vars = set()

    # 检测常见的未定义变量模式
    # 例如: np.array, st.title, nx.Graph
    patterns = [
        r'\bnp\.\w+',  # numpy
        r'\bst\.\w+',  # streamlit
        r'\bnx\.\w+',  # networkx
        r'\bpd\.\w+',  # pandas
        r'\bplt\.\w+', # matplotlib
        r'\bsns\.\w+', # seaborn
        r'\btorch\.\w+', # pytorch
        r'\btf\.\w+',  # tensorflow
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            var_name = match.split('.')[0]
            if var_name in IMPORT_MAPPING:
                undefined_vars.add(var_name)

    # 检测typing注解
    typing_patterns = [
        r':\s*Dict\[', r':\s*List\[', r':\s*Set\[', r':\s*Tuple\[',
        r':\s*Optional\[', r':\s*Union\[', r':\s*Any', r':\s*Callable\[',
        r':\s*Type\[', r':\s*TypeVar', r':\s*Generic', r':\s*Protocol',
    ]

    for pattern in typing_patterns:
        if re.search(pattern, content):
            # 提取类型名
            type_match = re.search(r':\s*(Dict|List|Set|Tuple|Optional|Union|Any|Callable|Type|TypeVar|Generic|Protocol|Literal|Final)(?=\[|\s|$)', content)
            if type_match:
                undefined_vars.add(type_match.group(1))

    # 检测标准库使用
    for lib_name in STDLIB_IMPORTS.keys():
        if re.search(rf'\b{lib_name}\.\w+', content):
            # 检查是否已经导入
            import_pattern = rf'import\s+{lib_name}'
            if not re.search(import_pattern, content):
                undefined_vars.add(lib_name)

    return undefined_vars


def has_existing_import(content: str, import_statement: str) -> bool:
    """检查是否已存在导入语句"""
    # 提取导入的模块名
    module_match = re.search(r'import\s+(\w+)|from\s+(\w+)', import_statement)
    if module_match:
        module_name = module_match.group(1) or module_match.group(2)
        # 检查是否已导入
        return bool(re.search(rf'\b{module_name}\b', content))
    return False


def add_import_to_file(file_path: Path, imports: set[str], dry_run: bool = False) -> bool:
    """向文件添加缺失的导入语句"""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"❌ 无法读取文件 {file_path}: {e}")
        return False

    lines = content.split('\n')

    # 找到文档字符串结束的位置
    docstring_end = 0
    in_docstring = False
    docstring_char = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 检测文档字符串开始
        if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
            in_docstring = True
            docstring_char = stripped[:3]
            if len(stripped) > 3:  # 单行文档字符串
                in_docstring = False
                docstring_end = i
            continue

        # 检测文档字符串结束
        if in_docstring and (stripped.endswith(docstring_char) or stripped == docstring_char):
            in_docstring = False
            docstring_end = i + 1
            continue

        # 找到第一个非空非注释行
        if not in_docstring and stripped and not stripped.startswith('#'):
            if docstring_end == 0:
                docstring_end = i
            break

    # 准备要添加的导入语句
    typing_imports = []
    stdlib_imports = []
    thirdparty_imports = []

    for var_name in sorted(imports):
        if var_name in TYPING_IMPORTS:
            typing_imports.append(TYPING_IMPORTS[var_name])
        elif var_name in STDLIB_IMPORTS:
            stdlib_imports.append(STDLIB_IMPORTS[var_name])
        elif var_name in IMPORT_MAPPING:
            import_stmt, _ = IMPORT_MAPPING[var_name]
            thirdparty_imports.append(import_stmt)

    # 组合导入（按PEP8顺序：标准库 -> 第三方 -> typing）
    all_imports = []
    if stdlib_imports:
        all_imports.extend(sorted(stdlib_imports))
    if thirdparty_imports:
        all_imports.extend(sorted(thirdparty_imports))
    if typing_imports:
        all_imports.append('')  # 空行分隔
        all_imports.extend(sorted(typing_imports))

    if not all_imports:
        return False

    # 检查是否已存在这些导入
    existing_imports = set()
    for line in lines[:docstring_end+20]:
        for imp in all_imports:
            # 安全地提取导入的模块名
            parts = imp.split()
            if len(parts) >= 2:
                module_name = parts[1]  # "import X as Y" 中的 X
                if module_name in line or imp in line:
                    existing_imports.add(imp)
            elif imp in line:
                existing_imports.add(imp)

    new_imports = [imp for imp in all_imports if imp not in existing_imports]
    if not new_imports:
        return False

    # 插入导入语句
    insert_pos = docstring_end

    # 如果文档字符串后没有空行，添加一个
    if insert_pos < len(lines) and lines[insert_pos].strip():
        new_imports.insert(0, '')

    # 构建新内容
    new_lines = lines[:insert_pos] + new_imports + lines[insert_pos:]
    new_content = '\n'.join(new_lines)

    if dry_run:
        print(f"📄 {file_path}")
        for imp in new_imports:
            print(f"  + {imp}")
        return True

    try:
        file_path.write_text(new_content, encoding='utf-8')
        print(f"✅ 已修复: {file_path}")
        return True
    except Exception as e:
        print(f"❌ 无法写入文件 {file_path}: {e}")
        return False


def scan_and_fix(directory: Path, dry_run: bool = False) -> dict[str, int]:
    """扫描并修复目录中的所有Python文件"""
    stats = {
        'scanned': 0,
        'fixed': 0,
        'numpy_imports': 0,
        'streamlit_imports': 0,
        'networkx_imports': 0,
        'typing_imports': 0,
        'stdlib_imports': 0,
        'total_imports_added': 0,
    }

    python_files = list(directory.rglob('*.py'))

    print(f"🔍 扫描 {len(python_files)} 个Python文件...")

    for file_path in python_files:
        stats['scanned'] += 1

        # 跳过虚拟环境和构建目录
        if 'venv' in str(file_path) or '__pycache__' in str(file_path):
            continue

        # 检测未定义变量
        undefined_vars = detect_undefined_variables(file_path)

        if undefined_vars:
            if add_import_to_file(file_path, undefined_vars, dry_run):
                stats['fixed'] += 1

                # 统计导入类型
                for var_name in undefined_vars:
                    stats['total_imports_added'] += 1
                    if var_name in ['np', 'numpy']:
                        stats['numpy_imports'] += 1
                    elif var_name in ['st', 'streamlit']:
                        stats['streamlit_imports'] += 1
                    elif var_name in ['nx', 'networkx']:
                        stats['networkx_imports'] += 1
                    elif var_name in TYPING_IMPORTS:
                        stats['typing_imports'] += 1
                    elif var_name in STDLIB_IMPORTS:
                        stats['stdlib_imports'] += 1

    return stats


def verify_fixes(directory: Path) -> dict[str, int]:
    """验证修复结果"""
    print("\n🔍 验证修复结果...")

    # 运行ruff检查
    import subprocess

    result = subprocess.run(
        ['ruff', 'check', str(directory), '--select', 'F821', '--statistics'],
        capture_output=True,
        text=True
    )

    output = result.stdout

    # 统计未定义变量
    undefined_count = 0
    if 'F821' in output:
        for line in output.split('\n'):
            if 'F821' in line:
                undefined_count += 1

    # 统计各类未定义变量
    result = subprocess.run(
        ['ruff', 'check', str(directory), '--select', 'F821'],
        capture_output=True,
        text=True
    )

    var_counts = {}
    for line in result.stdout.split('\n'):
        if 'F821' in line and '`' in line:
            # 提取变量名
            match = re.search(r'`([^`]+)`', line)
            if match:
                var_name = match.group(1)
                var_counts[var_name] = var_counts.get(var_name, 0) + 1

    return {
        'total_undefined': undefined_count,
        'by_variable': var_counts,
    }


def main():
    parser = argparse.ArgumentParser(description='自动修复缺失的导入语句')
    parser.add_argument('--dry-run', action='store_true', help='预览修复，不实际修改文件')
    parser.add_argument('--execute', action='store_true', help='执行修复')
    parser.add_argument('--verify', action='store_true', help='验证修复结果')
    parser.add_argument('--directory', type=str, default='core/', help='要扫描的目录')

    args = parser.parse_args()

    directory = Path(args.directory)

    if not directory.exists():
        print(f"❌ 目录不存在: {directory}")
        sys.exit(1)

    if args.dry_run:
        print("=" * 80)
        print("🔍 P1级问题修复 - 预览模式")
        print("=" * 80)
        stats = scan_and_fix(directory, dry_run=True)

        print("\n" + "=" * 80)
        print("📊 预览统计")
        print("=" * 80)
        print(f"扫描文件数: {stats['scanned']}")
        print(f"需要修复的文件: {stats['fixed']}")
        print(f"预计添加的导入数: {stats['total_imports_added']}")
        print(f"  - numpy导入: {stats['numpy_imports']}")
        print(f"  - streamlit导入: {stats['streamlit_imports']}")
        print(f"  - networkx导入: {stats['networkx_imports']}")
        print(f"  - typing导入: {stats['typing_imports']}")
        print(f"  - 标准库导入: {stats['stdlib_imports']}")
        print("\n使用 --execute 执行实际修复")

    elif args.execute:
        print("=" * 80)
        print("🔧 P1级问题修复 - 执行模式")
        print("=" * 80)
        stats = scan_and_fix(directory, dry_run=False)

        print("\n" + "=" * 80)
        print("📊 修复统计")
        print("=" * 80)
        print(f"扫描文件数: {stats['scanned']}")
        print(f"已修复文件数: {stats['fixed']}")
        print(f"添加的导入数: {stats['total_imports_added']}")
        print(f"  - numpy导入: {stats['numpy_imports']}")
        print(f"  - streamlit导入: {stats['streamlit_imports']}")
        print(f"  - networkx导入: {stats['networkx_imports']}")
        print(f"  - typing导入: {stats['typing_imports']}")
        print(f"  - 标准库导入: {stats['stdlib_imports']}")

        print("\n✅ 修复完成！运行 --verify 查看验证结果")

    elif args.verify:
        print("=" * 80)
        print("✅ P1级问题修复 - 验证模式")
        print("=" * 80)
        stats = verify_fixes(directory)

        print("\n📊 验证结果")
        print("-" * 80)
        print(f"剩余未定义变量: {stats['total_undefined']} 个")

        if stats['by_variable']:
            print("\nTop 未定义变量:")
            for var_name, count in sorted(stats['by_variable'].items(), key=lambda x: -x[1])[:10]:
                print(f"  - {var_name}: {count} 处")

        improvement = 725 - stats['total_undefined']
        improvement_pct = (improvement / 725) * 100

        print(f"\n改进: {improvement} 个 ({improvement_pct:.1f}%)")

        if stats['total_undefined'] < 50:
            print("\n✅ 修复效果显著！剩余问题可手动处理。")
        else:
            print("\n⚠️  仍有较多问题，建议运行第二轮修复或手动检查。")


if __name__ == '__main__':
    main()
