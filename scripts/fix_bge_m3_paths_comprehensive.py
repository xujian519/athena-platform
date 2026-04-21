#!/usr/bin/env python3
"""
BGE-M3硬编码路径全面修复脚本
Comprehensive fix for all BGE-M3 hardcoded paths

作者: Claude Code
日期: 2026-04-21
"""

import os
import re
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")

# BGE-M3 API服务URL
BGE_M3_API_URL = "http://127.0.0.1:8766/v1/embeddings"

def fix_file_comprehensive(file_path: Path) -> int:
    """全面修复单个文件中的所有硬编码路径"""
    if not file_path.exists():
        print(f"  ⚠️  文件不存在: {file_path}")
        return 0

    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # 检查是否包含bge-m3路径的任何形式
        if "bge-m3" not in content.lower():
            return 0

        # 多种替换模式
        replacements = [
            # 模式1: 完整的硬编码路径
            (r'["\']/?Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3/?["\']',
             BGE_M3_API_URL),

            # 模式2: project_root / "models/converted/BAAI/bge-m3"
            (r'str\(project_root\s*/\s*["\']models/converted/BAAI/bge-m3["\']\)',
             '"' + BGE_M3_API_URL + '"'),

            # 模式3: PROJECT_ROOT / "models/converted/BAAI/bge-m3"
            (r'str\(PROJECT_ROOT\s*/\s*["\']models/converted/BAAI/bge-m3["\']\)',
             '"' + BGE_M3_API_URL + '"'),

            # 模式4: project_root / "models/converted/BAAI/bge-m3" (无str())
            (r'project_root\s*/\s*["\']models/converted/BAAI/bge-m3["\']',
             '"' + BGE_M3_API_URL + '"'),

            # 模式5: PROJECT_ROOT / "models/converted/BAAI/bge-m3" (无str())
            (r'PROJECT_ROOT\s*/\s*["\']models/converted/BAAI/bge-m3["\']',
             '"' + BGE_M3_API_URL + '"'),
        ]

        changes = 0
        for pattern, replacement in replacements:
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                content = new_content
                changes += count
                print(f"    模式匹配: {pattern[:50]}... → {count}处")

        # 如果有更改，写回文件
        if changes > 0 and content != original_content:
            file_path.write_text(content, encoding='utf-8')
            print(f"  ✅ {file_path.relative_to(PROJECT_ROOT)}: {changes} 处修改")
            return changes

        return 0

    except Exception as e:
        print(f"  ❌ {file_path.relative_to(PROJECT_ROOT)}: 错误 - {e}")
        return 0

def scan_and_fix_core():
    """扫描并修复core/目录下的所有Python文件"""
    print("🔍 扫描core/目录:")
    print("")

    total_changes = 0
    fixed_files = 0

    # 递归扫描core/目录
    for py_file in PROJECT_ROOT.glob("core/**/*.py"):
        changes = fix_file_comprehensive(py_file)
        if changes > 0:
            fixed_files += 1
            total_changes += changes

    return fixed_files, total_changes

def main():
    """主函数"""
    print("🔧 BGE-M3硬编码路径全面修复")
    print("=" * 60)
    print("")
    print("📋 修复方案:")
    print(f"  所有形式的bge-m3路径 → {BGE_M3_API_URL}")
    print("")

    fixed_files, total_changes = scan_and_fix_core()

    print("")
    print("📊 修复统计:")
    print(f"  修复文件数: {fixed_files}")
    print(f"  总修改数: {total_changes}")
    print("")

    if total_changes > 0:
        print("✅ 硬编码路径修复完成！")
        print("")
        print("📝 后续步骤:")
        print("  1. 验证代码语法正确性")
        print("  2. 测试embedding功能是否正常")
        print("  3. 确认BGE-M3 API服务运行在8766端口")
        print("  4. 提交修复后的代码")
    else:
        print("ℹ️  未发现需要修复的硬编码路径")

if __name__ == "__main__":
    main()
