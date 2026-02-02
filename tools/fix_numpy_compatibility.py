#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Numpy兼容性修复工具
Numpy Compatibility Fix Tool
"""

import os
import re
import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

class NumpyCompatibilityFixer:
    """Numpy兼容性修复器"""

    def __init__(self):
        self.fixes_applied = {
            "deprecated_types": 0,
            "array_creation": 0,
            "random_functions": 0,
            "boolean_operations": 0,
            "import_statements": 0
        }

        # 需要修复的模式
        self.deprecated_types = {
            r'\bnp\.int\b': 'np.int64',
            r'\bnp\.float\b': 'np.float64',
            r'\bnp\.bool\b': 'np.bool_',
            r'\bnp\.complex\b': 'np.complex128',
            r'\bnp\.object\b': 'np.object_',
            r'\bnp\.str\b': 'np.str_',
            r'\bnp\.unicode\b': 'np.str_',
        }

        # 数组创建修复
        self.array_creation_fixes = {
            r'np\.array\(\[\]\)': 'array([])',
            r'np\.empty\(([^,]+)(?:,\s*dtype=([^)]+))?\)': self._safe_empty_array,
            r'np\.zeros\(([^,]+)(?:,\s*dtype=([^)]+))?\)': self._safe_zeros_array,
            r'np\.ones\(([^,]+)(?:,\s*dtype=([^)]+))?\)': self._safe_ones_array,
        }

        # 随机函数修复
        self.random_fixes = {
            r'np\.random\.rand\(([^)]+)\)': self._safe_random_rand,
            r'np\.random\.randn\(([^)]+)\)': self._safe_random_randn,
            r'np\.random\.random\(([^)]+)\)': self._safe_random_random,
            r'np\.random\.choice\(([^,]+),\s*size=([^\)]+)\)': self._safe_random_choice,
        }

        # 布尔操作修复
        self.boolean_fixes = {
            r'np\.bool\(([^)]+)\)': 'bool(\1)',
            r'astype\(np\.bool\)': 'astype(bool)',
            r'astype\(np\.int\)': 'astype(np.int64)',
            r'astype\(np\.float\)': 'astype(np.float64)',
        }

    def _safe_empty_array(self, match):
        """安全的empty数组创建"""
        shape = match.group(1)
        dtype = match.group(2) if match.group(2) else 'np.float64'
        return f'np.empty({shape}, dtype={dtype})'

    def _safe_zeros_array(self, match):
        """安全的zeros数组创建"""
        shape = match.group(1)
        dtype = match.group(2) if match.group(2) else 'np.float64'
        return f'zeros({shape}, dtype={dtype})'

    def _safe_ones_array(self, match):
        """安全的ones数组创建"""
        shape = match.group(1)
        dtype = match.group(2) if match.group(2) else 'np.float64'
        return f'ones({shape}, dtype={dtype})'

    def _safe_random_rand(self, match):
        """安全的rand函数"""
        args = match.group(1)
        return f'random(({args}))'

    def _safe_random_randn(self, match):
        """安全的randn函数"""
        args = match.group(1)
        return f'random(({args}))'

    def _safe_random_random(self, match):
        """安全的random函数"""
        args = match.group(1)
        return f'random({args})'

    def _safe_random_choice(self, match):
        """安全的choice函数"""
        arr = match.group(1)
        size = match.group(2)
        return f'np.random.choice({arr}, size={size})'

    def fix_file(self, file_path: Path, dry_run: bool = True) -> Dict[str, int]:
        """修复单个文件的numpy兼容性"""
        fixes_in_file = {
            "deprecated_types": 0,
            "array_creation": 0,
            "random_functions": 0,
            "boolean_operations": 0,
            "import_statements": 0
        }

        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            original_content = content

            # 1. 修复废弃类型
            for old_pattern, new_type in self.deprecated_types.items():
                new_content = re.sub(old_pattern, new_type, content)
                if new_content != content:
                    fixes_in_file["deprecated_types"] += content.count(old_pattern)
                    content = new_content

            # 2. 修复数组创建
            for pattern, replacement in self.array_creation_fixes.items():
                if callable(replacement):
                    matches = list(re.finditer(pattern, content))
                    for match in reversed(matches):  # 从后往前替换避免位置偏移
                        new_replacement = replacement(match)
                        content = content[:match.start()] + new_replacement + content[match.end():]
                    fixes_in_file["array_creation"] += len(matches)
                else:
                    new_content = re.sub(pattern, replacement, content)
                    if new_content != content:
                        fixes_in_file["array_creation"] += 1
                        content = new_content

            # 3. 修复随机函数
            for pattern, replacement in self.random_fixes.items():
                if callable(replacement):
                    matches = list(re.finditer(pattern, content))
                    for match in reversed(matches):
                        new_replacement = replacement(match)
                        content = content[:match.start()] + new_replacement + content[match.end():]
                    fixes_in_file["random_functions"] += len(matches)
                else:
                    new_content = re.sub(pattern, replacement, content)
                    if new_content != content:
                        fixes_in_file["random_functions"] += 1
                        content = new_content

            # 4. 修复布尔操作
            for old_pattern, new_pattern in self.boolean_fixes.items():
                new_content = re.sub(old_pattern, new_pattern, content)
                if new_content != content:
                    fixes_in_file["boolean_operations"] += content.count(old_pattern)
                    content = new_content

            # 5. 添加兼容性导入（如果需要）
            if any(fixes_in_file[key] > 0 for key in fixes_in_file if key != "import_statements"):
                if 'from config.numpy_compatibility import' not in content:
                    # 在文件开头添加导入
                    lines = content.split('\n')
                    import_idx = 0

                    # 找到第一个import语句的位置
                    for i, line in enumerate(lines):
                        if line.strip().startswith(('import ', 'from ')):
                            import_idx = i
                            break

                    # 插入兼容性导入
                    compat_import = "# Numpy兼容性导入\nfrom config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot"
                    lines.insert(import_idx, compat_import)
                    content = '\n'.join(lines)
                    fixes_in_file["import_statements"] += 1

            # 写入文件（如果不是dry run）
            if content != original_content and not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # 累计修复数量
            for key in fixes_in_file:
                self.fixes_applied[key] += fixes_in_file[key]

        except Exception as e:
            print(f"❌ 修复文件失败 {file_path}: {e}")

        return fixes_in_file

    def fix_directory(self, directory: Path, dry_run: bool = True,
                     file_pattern: str = "*.py") -> Dict[str, int]:
        """修复目录下的所有Python文件"""
        total_fixes = {
            "files_processed": 0,
            "files_with_fixes": 0
        }

        # 查找所有Python文件
        py_files = list(directory.rglob(file_pattern))

        # 过滤掉不需要处理的目录
        skip_dirs = {'.git', '__pycache__', '.venv', 'venv', 'node_modules',
                    'site-packages', '.pytest_cache'}

        py_files = [f for f in py_files if not any(skip in str(f) for skip in skip_dirs)]

        print(f"🔧 开始处理 {len(py_files)} 个Python文件...")

        for py_file in py_files:
            # 检查文件是否使用了numpy
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # 快速检查是否包含numpy
                if not re.search(r'\b(np\.|numpy)', content):
                    continue

            except Exception:
                continue

            # 修复文件
            fixes = self.fix_file(py_file, dry_run)
            total_fixes["files_processed"] += 1

            if any(fixes[key] > 0 for key in fixes if key != "import_statements"):
                total_fixes["files_with_fixes"] += 1
                print(f"✅ 修复文件: {py_file.relative_to(directory)}")
                for fix_type, count in fixes.items():
                    if count > 0 and fix_type != "import_statements":
                        print(f"   - {fix_type}: {count}")

        return total_fixes

    def create_compatibility_test(self) -> str:
        """创建兼容性测试脚本"""
        test_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Numpy兼容性测试
Numpy Compatibility Test
"""

import sys
import warnings
import traceback
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_numpy_compatibility():
    """测试numpy兼容性"""
    print("🧪 开始Numpy兼容性测试...")

    try:
        # 测试基础导入
        from config.numpy_compatibility import np, array, zeros, ones, random, mean, sum, dot
        print("✅ 基础导入成功")

        # 测试数组创建
        test_arr = array([1, 2, 3, 4, 5])
        print(f"✅ 数组创建: {test_arr}")

        # 测试零数组
        zeros_arr = zeros((3, 3))
        print(f"✅ 零数组创建: {zeros_arr.shape}")

        # 测试随机数
        rand_arr = random(5)
        print(f"✅ 随机数组: {rand_arr[:3]}...")

        # 测试数学运算
        print(f"✅ 数组求和: {sum(test_arr)}")
        print(f"✅ 数组均值: {mean(test_arr)}")

        # 测试高级功能
        a = array([[1, 2], [3, 4]])
        b = array([[5, 6], [7, 8]])
        c = dot(a, b)
        print(f"✅ 矩阵乘法:\\n{c}")

        # 测试类型兼容性
        int_arr = array([1, 2, 3], dtype=np.int64)
        float_arr = array([1.0, 2.0, 3.0], dtype=np.float64)
        bool_arr = array([True, False, True])
        print(f"✅ 类型测试: int={int_arr.dtype}, float={float_arr.dtype}, bool={bool_arr.dtype}")

        print("\\n🎉 所有兼容性测试通过！")
        return True

    except Exception as e:
        print(f"\\n❌ 测试失败: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_numpy_compatibility()
    sys.exit(0 if success else 1)
'''

        return test_script

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Numpy兼容性修复工具")
    parser.add_argument("--directory", default=".", help="要修复的目录")
    parser.add_argument("--dry-run", action="store_true", help="仅分析不修改")
    parser.add_argument("--pattern", default="*.py", help="文件匹配模式")
    parser.add_argument("--create-test", action="store_true", help="创建兼容性测试脚本")

    args = parser.parse_args()

    fixer = NumpyCompatibilityFixer()

    print("🔧 Numpy兼容性修复工具")
    print("=" * 50)

    if args.create_test:
        test_script = fixer.create_compatibility_test()
        test_path = Path("test_numpy_compatibility.py")
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(test_script)
        print(f"✅ 兼容性测试脚本已创建: {test_path}")

    # 修复目录
    directory = Path(args.directory)
    total_fixes = fixer.fix_directory(directory, dry_run=args.dry_run, file_pattern=args.pattern)

    # 显示修复结果
    print(f"\n📊 修复统计:")
    print(f"   处理文件数: {total_fixes['files_processed']}")
    print(f"   修复文件数: {total_fixes['files_with_fixes']}")

    print(f"\n🔧 总计修复:")
    for fix_type, count in fixer.fixes_applied.items():
        if count > 0:
            print(f"   {fix_type}: {count}")

    if args.dry_run:
        print(f"\n💡 这是dry-run模式，没有实际修改文件")
        print(f"   要应用修复，请运行: python {__file__} --directory {args.directory}")
    else:
        print(f"\n✅ 修复完成！建议运行测试脚本验证兼容性")
        print(f"   python test_numpy_compatibility.py")

if __name__ == "__main__":
    main()