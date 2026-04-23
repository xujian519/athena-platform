#!/usr/bin/env python3
"""
全面的Python类型注解修复工具
处理所有常见的括号不匹配错误
"""
import re
import sys
from pathlib import Path


# 定义所有需要修复的模式
FIX_PATTERNS = [
    # 格式: (模式, 替换, 说明)
    (r'Optional\[dict\[str, Any\](?=\s*=\s*None)', r'Optional[dict[str, Any]]', 'Optional[dict[str, Any]'),
    (r'Optional\[list\[str\](?=\s*=\s*None)', r'Optional[list[str]]', 'Optional[list[str]'),
    (r'list\[dict\[str, Any\](?=\s*=\s*None)', r'list[dict[str, Any]]', 'list[dict[str, Any]'),
    (r'dict\[str, dict\[str, Any\](?=\s*=\s*None)', r'dict[str, dict[str, Any]]', 'dict[str, dict[str, Any]]'),
    (r'Optional\[List\[str\](?=\s*=\s*None)', r'Optional[List[str]]', 'Optional[List[str]]'),
    (r'Optional\[list\[float\](?=\s*=\s*None)', r'Optional[list[float]]', 'Optional[list[float]]'),
    (r'dict\[str, list\[str\](?=\s*=\s*None)', r'dict[str, list[str]]', 'dict[str, list[str]]'),
    (r'Optional\[dict\[str, str\](?=\s*=\s*None)', r'Optional[dict[str, str]]', 'Optional[dict[str, str]]'),
    (r'Optional\[list\[dict\[str, Any\]\](?=\s*=\s*None)', r'Optional[list[dict[str, Any]]]', 'Optional[list[dict[str, Any]]]'),
    (r'dict\[str, set\[str\](?=\s*=\s*None)', r'dict[str, set[str]]', 'dict[str, set[str]]'),
    (r'list\[str\](?=\s*=\s*None)', r'list[str]]', 'list[str]'),
    (r'Optional\[str\](?=\s*=\s*None)', r'Optional[str]]', 'Optional[str]'),
    (r'dict\[str, Any\](?=\s*=\s*None)', r'dict[str, Any]]', 'dict[str, Any]'),
    (r'dict\[str, list\[float\](?=\s*=\s*None)', r'dict[str, list[float]]', 'dict[str, list[float]]'),
    (r'Optional\[Optional\[dict\[str, Any\]\](?=\s*=\s*None)', r'Optional[Optional[dict[str, Any]]]', 'Optional[Optional[dict[str, Any]]]'),
    (r'Optional\[list\[dict\](?=\s*=\s*None)', r'Optional[list[dict]]', 'Optional[list[dict]]'),
    (r'list\[dict\[str, str\](?=\s*=\s*None)', r'list[dict[str, str]]', 'list[dict[str, str]]'),
    (r'Final\[list\](?=\s*=\s*None)', r'Final[list]]', 'Final[list]'),
    (r'OrderedDict\[str, tuple\[Any, float\](?=\s*=\s*None)', r'OrderedDict[str, tuple[Any, float]]', 'OrderedDict[str, tuple[Any, float]]'),
]


def fix_file(file_path: Path) -> dict:
    """修复单个文件"""
    result = {
        'file': str(file_path),
        'success': False,
        'fixes': [],
        'error': None
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content
        fixes_applied = []

        # 应用所有修复模式
        for pattern, replacement, description in FIX_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                fixes_applied.append(f"{description}: {len(matches)}处")

        # 修复多余的三重括号
        content = re.sub(r'\]\]\] =', r']] =', content)
        content = re.sub(r'\]\]\]\s*$', r']]', content, flags=re.MULTILINE)

        # 如果没有修改，直接返回
        if content == original:
            result['success'] = True  # 没有错误也是成功
            return result

        # 验证语法
        import py_compile
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tf:
            tf.write(content)
            tf_path = tf.name

        try:
            py_compile.compile(tf_path, doraise=True)

            # 验证通过，写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            result['success'] = True
            result['fixes'] = fixes_applied

        except py_compile.PyCompileError as e:
            result['error'] = f"语法错误: {e}"

        except Exception as e:
            result['error'] = f"验证错误: {e}"

    except Exception as e:
        result['error'] = str(e)

    return result


def main():
    if len(sys.argv) < 2:
        print("用法: python3 comprehensive_fix.py <目录>")
        sys.exit(1)

    base_dir = Path(sys.argv[1])

    # 查找所有Python文件
    py_files = list(base_dir.rglob('*.py'))
    print(f"找到 {len(py_files)} 个Python文件")

    # 修复文件
    results = []
    success_count = 0
    fix_count = 0

    for file_path in py_files:
        result = fix_file(file_path)
        results.append(result)

        if result['success']:
            if result['fixes']:
                success_count += 1
                fix_count += len(result['fixes'])
                print(f"✅ {file_path}")
                for fix in result['fixes']:
                    print(f"   - {fix}")
        elif result['error']:
            print(f"❌ {file_path}: {result['error']}")

    # 总结
    print("\n" + "=" * 60)
    print(f"修复完成:")
    print(f"  成功: {success_count}/{len(py_files)}")
    print(f"  总修复数: {fix_count}")


if __name__ == '__main__':
    main()
