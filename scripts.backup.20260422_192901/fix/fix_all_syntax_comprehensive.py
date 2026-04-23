#!/usr/bin/env python3
"""
全面修复Python类型注解语法错误
Comprehensive Python Type Annotation Syntax Fixer
"""

import re
from pathlib import Path
from typing import List, Tuple

def get_all_py_files(core_path: Path) -> List[Path]:
    """获取所有Python文件"""
    return list(core_path.rglob('*.py'))

def count_syntax_errors(files: List[Path]) -> int:
    """统计语法错误数量"""
    count = 0
    for f in files:
        try:
            compile(f.read_text(encoding='utf-8'), str(f), 'exec')
        except SyntaxError:
            count += 1
    return count

def fix_type_annotations(content: str) -> Tuple[str, int]:
    """修复类型注解语法错误，返回修复后的内容和修复数量"""
    original = content
    fixes = 0
    
    # 按优先级排序的修复模式
    patterns = [
        # 1. Optional[Type | None = None] -> Type | None = None
        (r'Optional\[([A-Z][a-zA-Z0-9_]*) \| None = None\]', r'\1 | None = None'),
        (r'Optional\[([a-z][a-zA-Z0-9_]*) \| None = None\]', r'\1 | None = None'),
        
        # 2. Optional[list[str] | None] -> Optional[list[str]] | None
        (r'Optional\[list\[str\] \| None\]', r'Optional[list[str]] | None'),
        (r'Optional\[dict\[str, Any\] \| None\]', r'Optional[dict[str, Any]] | None'),
        (r'Optional\[set\[str\] \| None\]', r'Optional[set[str]] | None'),
        
        # 3. list[str | None = None -> list[str] | None = None
        (r'list\[str \| None = None', r'list[str] | None = None'),
        (r'list\[int \| None = None', r'list[int] | None = None'),
        (r'List\[str \| None = None', r'List[str] | None = None'),
        (r'Set\[str \| None = None', r'Set[str] | None = None'),
        
        # 4. 修复带逗号的模式
        (r'list\[str \| None = None,\s*\*\*', r'list[str] | None = None, **'),
        (r'list\[str \| None = None,\s*\)', r'list[str] | None = None, )'),
        
        # 5. 修复未闭合的括号 dict[str, Any] | None = None]
        (r'dict\[str, Any\] \| None = None\]', r'dict[str, Any] | None = None'),
        (r'Dict\[str, Any\] \| None = None\]', r'Dict[str, Any] | None = None'),
        
        # 6. 修复Optional嵌套
        (r'Optional\[dict\[str, Any\]\s*\|\s*None\]', r'Optional[dict[str, Any]] | None'),
    ]
    
    for pattern, replacement in patterns:
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        if new_content != content:
            fixes += 1
            content = new_content
    
    return content, fixes

def fix_file(file_path: Path) -> bool:
    """修复单个文件"""
    try:
        content = file_path.read_text(encoding='utf-8')
        fixed, fix_count = fix_type_annotations(content)
        
        if fix_count > 0:
            file_path.write_text(fixed, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"⚠️ 处理文件失败 {file_path}: {e}")
        return False

def main():
    """主函数"""
    core_path = Path('/Users/xujian/Athena工作平台/core')
    
    print("=" * 60)
    print("🔍 开始全面修复Python语法错误")
    print("=" * 60)
    
    # 获取所有Python文件
    files = get_all_py_files(core_path)
    print(f"\n📁 找到 {len(files)} 个Python文件")
    
    # 统计初始错误数量
    print("\n📊 统计语法错误...")
    initial_errors = count_syntax_errors(files)
    print(f"   初始语法错误: {initial_errors} 个文件")
    
    # 第一轮修复
    print(f"\n🔧 第一轮修复...")
    fixed_count = 0
    for f in files:
        if fix_file(f):
            fixed_count += 1
    
    print(f"   修复文件: {fixed_count} 个")
    
    # 第二轮修复（处理需要多轮的模式）
    print(f"\n🔧 第二轮修复...")
    fixed_count_2 = 0
    for f in files:
        if fix_file(f):
            fixed_count_2 += 1
    
    print(f"   修复文件: {fixed_count_2} 个")
    
    # 统计最终错误数量
    print(f"\n📊 统计修复后语法错误...")
    final_errors = count_syntax_errors(files)
    print(f"   剩余语法错误: {final_errors} 个文件")
    
    print("\n" + "=" * 60)
    print(f"✅ 修复完成:")
    print(f"   - 修复前: {initial_errors} 个错误")
    print(f"   - 修复后: {final_errors} 个错误")
    print(f"   - 减少: {initial_errors - final_errors} 个")
    print("=" * 60)
    
    # 列出仍有错误的文件
    if final_errors > 0:
        print(f"\n⚠️ 仍有 {final_errors} 个文件存在语法错误:")
        error_files = []
        for f in files:
            try:
                compile(f.read_text(encoding='utf-8'), str(f), 'exec')
            except SyntaxError as e:
                error_files.append((str(f.relative_to(core_path.parent)), e.lineno, str(e.msg)[:50]))
        
        for file, line, error in error_files[:10]:
            print(f"   {file}:{line} - {error}")
        
        if len(error_files) > 10:
            print(f"   ... 还有 {len(error_files) - 10} 个文件")

if __name__ == "__main__":
    main()
