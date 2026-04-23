#!/usr/bin/env python3
"""
简单直接的修复 - 只修复特定模式
"""
import re
from pathlib import Path

def simple_fix(content):
    """只修复明确的问题模式"""
    lines = content.split('\n')
    fixed = []

    for line in lines:
        # 模式1: Optional[Type = None, -> Optional[Type] = None,
        if re.search(r'Optional\[[^\[\]]+ = None,', line):
            line = re.sub(r'(Optional\[[^\[\]]+)( = None,)', r'\1]\2', line)

        # 模式2: Optional[Type = field( -> Optional[Type] = field(
        if re.search(r'Optional\[[^\[\]]+ = field\(', line):
            line = re.sub(r'(Optional\[[^\[\]]+)( = field\()', r'\1]\2', line)

        # 模式3: var: Type[ = value  -> var: Type] = value
        if re.search(r': (list|dict)\[[^\[\]]+ = [\[{}\[]', line):
            line = re.sub(r': (list|dict)(\[[^\[\]]+)( = [\[{}\[])', r': \1\2]\3', line)

        # 模式4: 修复 ]] -> ]
        line = line.replace(']]', ']')

        fixed.append(line)

    return '\n'.join(fixed)

base = Path('/Users/xujian/Athena工作平台/core/framework/agents')

for py_file in base.rglob('*.py'):
    try:
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()

        fixed = simple_fix(content)
        if fixed != content:
            with open(py_file, 'w', encoding='utf-8') as f:
                f.write(fixed)
            print(f"Fixed: {py_file.relative_to(base)}")
    except:
        pass

print("\nDone!")
