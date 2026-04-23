#!/usr/bin/env python3
"""
简单的Python类型注解修复工具
"""
import re
import sys
from pathlib import Path


def fix_file(file_path: Path) -> bool:
    """修复单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # 修复1: Optional[list[str] = None -> Optional[list[str]] = None
        content = re.sub(
            r'Optional\[list\[str\] = None',
            r'Optional[list[str]] = None',
            content
        )

        # 修复2: Optional[dict[str, Any] = None -> Optional[dict[str, Any]] = None
        content = re.sub(
            r'Optional\[dict\[str, Any\] = None',
            r'Optional[dict[str, Any]] = None',
            content
        )

        # 修复3: list[dict[str, Any] = None -> list[dict[str, Any]] = None
        content = re.sub(
            r'list\[dict\[str, Any\] = None',
            r'list[dict[str, Any]] = None',
            content
        )

        # 修复4: ]]] = -> ]] = (三重括号)
        content = re.sub(r'\]\]\] =', r']] =', content)

        # 修复5: ]]] -> ]] (三重括号在行尾)
        content = re.sub(r'\]\]\]\s*$', r']]', content, flags=re.MULTILINE)

        # 如果没有修改，直接返回
        if content == original:
            return False

        # 验证语法
        import py_compile
        try:
            # 创建临时文件验证
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tf:
                tf.write(content)
                tf_path = tf.name

            py_compile.compile(tf_path, doraise=True)

            # 验证通过，写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"❌ {file_path}: 修复后语法错误 - {e}")
            return False

    except Exception as e:
        print(f"❌ {file_path}: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("用法: python3 simple_fix_syntax.py <目录>")
        sys.exit(1)

    base_dir = Path(sys.argv[1])

    # 查找所有需要修复的文件
    files_to_fix = []
    for py_file in base_dir.rglob('*.py'):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
                if 'Optional[list[str] = None' in content or \
                   'Optional[dict[str, Any] = None' in content or \
                   'list[dict[str, Any] = None' in content:
                    files_to_fix.append(py_file)
        except:
            pass

    print(f"找到 {len(files_to_fix)} 个需要修复的文件")

    fixed_count = 0
    for file_path in files_to_fix:
        if fix_file(file_path):
            print(f"✅ {file_path}")
            fixed_count += 1

    print(f"\n修复完成: {fixed_count}/{len(files_to_fix)}")


if __name__ == '__main__':
    main()
