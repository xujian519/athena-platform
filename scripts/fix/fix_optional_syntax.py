#!/usr/bin/env python3
"""
批量修复Python 3.14 Optional语法错误
"""

from typing import Optional
import re
from pathlib import Path


def fix_optional_syntax(file_path: Path) -> int:
    """修复单个文件中的Optional语法错误"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # 模式1: param: type | None = None -> param: type | None = None
        pattern1 = r'Optional\[([\w_\.]+(?:\s*:\s*[^,\]=]+)?)\]\s*=\s*None'
        def replace1(m):
            param_spec = m.group(1)
            # 提取参数名和类型
            if ':' in param_spec:
                param_name, param_type = param_spec.split(':', 1)
                return f'{param_name.strip()}: {param_type.strip()} | None = None'
            return f'{param_spec} | None = None'

        content = re.sub(pattern1, replace1, content)

        # 模式2: Optional[type] -> type | None (返回类型)
        pattern2 = r'->\s*Optional\[([^\]+)\]'
        def replace2(m):
            return f'-> {m.group(1).strip()} | None'
        content = re.sub(pattern2, replace2, content)

        # 模式3: def func(a: Optional[type1]
    b: Optional[type2]) -> def func(a: type1 | None, b: type2 | None)
        pattern3 = r'Optional\[([^\]+)\]\s*=\s*None'
        def replace3(m):
            params = m.group(1)
            # 处理多个参数
            result = []
            for param in params.split(','):
                param = param.strip()
                if ':' in param:
                    name, ptype = param.split(':', 1)
                    result.append(f'{name.strip()}: {ptype.strip()} | None')
                else:
                    result.append(f'{param} | None')
            return ' = None, '.join(result) + ' = None'
        content = re.sub(pattern3, replace3, content)

        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return 1
        return 0
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0


def main():
    """主函数"""
    # 查找所有Python文件
    project_root = Path('/Users/xujian/Athena工作平台')
    python_files = list(project_root.rglob('*.py'))

    fixed_count = 0
    for file_path in python_files:
        if fix_optional_syntax(file_path):
            print(f"Fixed: {file_path}")
            fixed_count += 1

    print(f"\n总共修复了 {fixed_count} 个文件")


if __name__ == '__main__':
    main()
