#!/usr/bin/env python3
"""
自动修复Python 3.10+类型注解到Python 3.9兼容格式
Auto-fix Python 3.10+ type annotations to Python 3.9 compatible format
"""

import re
from pathlib import Path
from typing import Set, Tuple, List
import shutil


def fix_type_annotations(content: str) -> Tuple[str, int]:
    """
    修复Python 3.10+类型注解为Python 3.9兼容格式

    Args:
        content: 文件内容

    Returns:
        (修复后的内容, 修复数量)
    """
    original_content = content
    fix_count = 0

    # 1. 修复简单类型注解: str | None -> Optional[str]
    simple_types = ['str', 'int', 'bool', 'float', 'bytes', 'dict', 'list', 'set', 'tuple']

    for type_name in simple_types:
        # 匹配: str | None 或 None | str
        pattern1 = rf'\b{type_name}\s*\|\s*None'
        pattern2 = rf'None\s*\|\s*{type_name}'

        if re.search(pattern1, content) or re.search(pattern2, content):
            # 检查是否已经导入了Optional
            if 'from typing import Optional' not in content:
                # 添加Optional导入
                import_match = re.search(r'from typing import (.+)', content)
                if import_match:
                    existing_imports = import_match.group(1)
                    if 'Optional' not in existing_imports:
                        content = content.replace(
                            f'from typing import {existing_imports}',
                            f'from typing import {existing_imports}, Optional'
                        )
                        fix_count += 1
                else:
                    # 添加新的导入语句
                    content = 'from typing import Optional\n' + content
                    fix_count += 1

            # 替换类型注解
            # str | None -> Optional[str]
            content = re.sub(rf'\b{type_name}\s*\|\s*None', f'Optional[{type_name}]', content)
            # None | str -> Optional[str]
            content = re.sub(rf'None\s*\|\s*{type_name}', f'Optional[{type_name}]', content)

            fix_count += len(re.findall(pattern1, original_content)) + len(re.findall(pattern2, original_content))

    # 2. 修复复杂类型注解: list[str] | None -> Optional[List[str]]
    # list[str] | None -> Optional[List[str]]
    complex_pattern = r'\b(list|dict|tuple|set)\[([^\]]+)\]\s*\|\s*None'
    if re.search(complex_pattern, content):
        # 确保导入了List, Dict, Tuple, Set
        needed_types = []
        if 'List[' not in content and 'list[' in content:
            needed_types.append('List')
        if 'Dict[' not in content and 'dict[' in content:
            needed_types.append('Dict')
        if 'Tuple[' not in content and 'tuple[' in content:
            needed_types.append('Tuple')
        if 'Set[' not in content and 'set[' in content:
            needed_types.append('Set')

        if needed_types:
            # 添加到typing导入
            import_match = re.search(r'from typing import (.+)', content)
            if import_match:
                existing_imports = import_match.group(1)
                for t in needed_types:
                    if t not in existing_imports:
                        content = content.replace(
                            f'from typing import {existing_imports}',
                            f'from typing import {existing_imports}, {t}'
                        )
                        fix_count += 1
            else:
                # 添加新的导入
                content = f'from typing import {", ".join(needed_types)}\n' + content
                fix_count += 1

        # 替换 list[str] | None -> Optional[List[str]]
        def replace_complex_type(match):
            container = match.group(1)  # list, dict, tuple, set
            inner = match.group(2)       # str, int, etc.
            container_cap = container.capitalize()
            return f'Optional[{container_cap}[{inner}]]'

        content = re.sub(complex_pattern, replace_complex_type, content)
        fix_count += len(re.findall(complex_pattern, original_content))

    # 3. 修复 dict[K, V] | None -> Optional[Dict[K, V]]
    dict_pattern = r'\bdict\[([^,]+),\s*([^\]]+)\]\s*\|\s*None'
    if re.search(dict_pattern, content):
        # 确保导入了Dict
        if 'from typing import' in content and 'Dict' not in content:
            import_match = re.search(r'from typing import (.+)', content)
            if import_match:
                content = content.replace(
                    f'from typing import {import_match.group(1)}',
                    f'from typing import {import_match.group(1)}, Dict'
                )

        content = re.sub(dict_pattern, r'Optional[Dict[\1, \2]]', content)
        fix_count += len(re.findall(dict_pattern, original_content))

    return content, fix_count


def fix_file(file_path: Path) -> bool:
    """
    修复单个文件

    Args:
        file_path: 文件路径

    Returns:
        是否成功修复
    """
    print(f"\n🔧 修复文件: {file_path.name}")
    print("   " + "-" * 60)

    try:
        # 读取原文件
        content = file_path.read_text()
        original_content = content

        # 备份原文件
        backup_path = file_path.with_suffix('.py.bak')
        shutil.copy(file_path, backup_path)
        print(f"   ✅ 已备份到: {backup_path.name}")

        # 修复类型注解
        fixed_content, fix_count = fix_type_annotations(content)

        if fix_count > 0:
            # 写入修复后的内容
            file_path.write_text(fixed_content)
            print(f"   ✅ 修复完成: {fix_count} 处类型注解")

            # 显示部分修复示例
            original_lines = original_content.split('\n')[:10]
            fixed_lines = fixed_content.split('\n')[:10]

            print("\n   修复示例 (前10行对比):")
            for i, (orig, fixed) in enumerate(zip(original_lines, fixed_lines), 1):
                if orig != fixed and '|' in orig:
                    print(f"   行 {i}:")
                    print(f"     修改前: {orig}")
                    print(f"     修改后: {fixed}")
                    break
            return True
        else:
            print(f"   ℹ️  无需修复: 文件已是Python 3.9兼容格式")
            # 删除备份文件
            backup_path.unlink()
            return True

    except Exception as e:
        print(f"   ❌ 修复失败: {e}")
        # 恢复备份
        if backup_path.exists():
            shutil.copy(backup_path, file_path)
            print(f"   ✅ 已从备份恢复")
        return False


def main():
    """主函数"""
    print("=" * 70)
    print("Python 3.10+ 类型注解自动修复工具")
    print("=" * 70)

    # 设置工作目录
    import os
    os.chdir('/Users/xujian/Athena工作平台')

    # 需要修复的文件
    files_to_fix = [
        "core/legal_world_model/scenario_identifier.py",
        "core/legal_world_model/scenario_rule_retriever_optimized.py",
        "core/legal_world_model/enhanced_scenario_identifier.py",
        "core/legal_world_model/scenario_identifier_optimized.py"
    ]

    print(f"\n将修复 {len(files_to_fix)} 个文件")
    print("=" * 70)

    results = {}
    for file_path_str in files_to_fix:
        file_path = Path(file_path_str)
        if file_path.exists():
            success = fix_file(file_path)
            results[file_path_str] = success
        else:
            print(f"\n⚠️  文件不存在: {file_path_str}")
            results[file_path_str] = False

    # 总结
    print("\n" + "=" * 70)
    print("修复总结")
    print("=" * 70)

    for file_path, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{status} - {file_path}")

    success_count = sum(1 for s in results.values() if s)
    print(f"\n总计: {success_count}/{len(results)} 个文件修复成功")

    if success_count == len(results):
        print("\n🎉 所有文件修复完成！")
        return 0
    else:
        print(f"\n⚠️  部分文件修复失败，请检查日志")
        return 1


if __name__ == "__main__":
    exit(main())
