#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速平台清理扫描工具
Quick Platform Cleanup Scanner
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def scan_platform():
    """扫描平台并返回可删除的文件列表"""
    root = Path(".")

    # 要查找的文件类型
    patterns = {
        "备份文件": [
            r".*\.bak$",
            r".*\.backup$",
            r".*\.old$",
            r".*~$",
            r".*\.tmp$",
            r".*\.temp$"
        ],
        "测试文件": [
            r"test_.*\.py$",
            r".*_test\.py$",
            r"conftest\.py$"
        ],
        "Demo文件": [
            r".*demo.*\.py$",
            r".*Demo.*\.py$",
            r".*example.*\.py$"
        ],
        "简单示例": [
            r".*simple.*\.py$",
            r".*Simple.*\.py$",
            r".*basic.*\.py$"
        ]
    }

    # 跳过的目录
    skip_dirs = {
        ".git", "__pycache__", ".pytest_cache",
        ".idea", ".vscode", "node_modules", "venv"
    }

    found_files = defaultdict(list)
    total_size = 0

    print("🔍 扫描平台文件...")

    for pattern_name, pattern_list in patterns.items():
        for pattern in pattern_list:
            for file_path in root.rglob(pattern):
                # 跳过目录和特殊目录
                if not file_path.is_file():
                    continue

                if any(skip in str(file_path) for skip in skip_dirs):
                    continue

                # 获取文件信息
                size = file_path.stat().st_size
                relative_path = str(file_path.relative_to(root))

                found_files[pattern_name].append({
                    "path": relative_path,
                    "size": size
                })
                total_size += size

    # 查找空目录
    empty_dirs = []
    for dir_path in sorted(root.rglob("*"), reverse=True):
        if dir_path.is_dir() and dir_path.name not in skip_dirs:
            try:
                contents = list(dir_path.iterdir())
                if not contents or all(f.name.startswith((".", "__")) for f in contents):
                    empty_dirs.append(str(dir_path.relative_to(root)))
            except Exception as e:

                # 记录异常但不中断流程

                logger.debug(f"[quick_cleanup_scan] Exception: {e}")
    # 查找重复文件
    file_counts = defaultdict(list)
    for file_path in root.rglob("*.py"):
        if file_path.is_file() and "backup" not in str(file_path):
            filename = file_path.name
            file_counts[filename].append(file_path)

    duplicates = []
    for filename, files in file_counts.items():
        if len(files) > 1:
            duplicates.append({
                "name": filename,
                "count": len(files),
                "paths": [str(f.relative_to(root)) for f in files]
            })

    # 输出结果
    print("\n📊 扫描结果:")
    print("=" * 60)

    for category, files in found_files.items():
        if files:
            total_size_mb = sum(f["size"] for f in files) / (1024 * 1024)
            print(f"\n{category} ({len(files)} 个文件, {total_size_mb:.2f} MB):")

            for f in files[:10]:  # 只显示前10个
                print(f"  - {f['path']}")

            if len(files) > 10:
                print(f"  ... 还有 {len(files) - 10} 个文件")

    if empty_dirs:
        print(f"\n空目录 ({len(empty_dirs)} 个):")
        for d in empty_dirs[:5]:
            print(f"  - {d}")
        if len(empty_dirs) > 5:
            print(f"  ... 还有 {len(empty_dirs) - 5} 个空目录")

    if duplicates:
        print(f"\n重复的Python文件 ({len(duplicates)} 组):")
        for dup in duplicates[:5]:
            print(f"  - {dup['name']} (x{dup['count']})")
        if len(duplicates) > 5:
            print(f"  ... 还有 {len(duplicates) - 5} 组重复文件")

    # 生成清理建议
    print("\n🎯 清理建议:")
    print("=" * 60)

    safe_delete = []
    safe_delete.extend(found_files["备份文件"])
    safe_delete.extend([{"path": d, "size": 0} for d in empty_dirs])

    review_needed = []
    review_needed.extend(found_files["测试文件"])
    review_needed.extend(found_files["Demo文件"])
    review_needed.extend(found_files["简单示例"])

    safe_size = sum(f["size"] for f in safe_delete) / (1024 * 1024)
    review_size = sum(f["size"] for f in review_needed) / (1024 * 1024)

    print(f"\n✅ 可以安全删除的文件:")
    print(f"   - 文件数: {len(safe_delete)}")
    print(f"   - 空间: {safe_size:.2f} MB")
    print(f"   包括: 所有备份文件和空目录")

    print(f"\n⚠️ 需要审查的文件:")
    print(f"   - 文件数: {len(review_needed)}")
    print(f"   - 空间: {review_size:.2f} MB")
    print(f"   包括: 测试文件、Demo和示例文件")

    # 生成删除命令
    print("\n📋 删除命令:")
    print("=" * 60)

    print("\n# 1. 删除备份文件（安全）")
    for f in found_files["备份文件"]:
        print(f"rm -f '{f['path']}'")

    print("\n# 2. 删除空目录（安全）")
    for d in empty_dirs:
        print(f"rmdir '{d}' 2>/dev/null || rm -rf '{d}'")

    print("\n# 3. 测试文件（需要审查）")
    for f in found_files["测试文件"][:5]:
        print(f"# rm -f '{f['path']}'  # 请审查后删除")

    # 保存详细报告
    with open("quick_cleanup_report.txt", "w", encoding="utf-8") as f:
        f.write("快速清理扫描报告\n")
        f.write("=" * 40 + "\n\n")

        f.write(f"备份文件 ({len(found_files['备份文件'])}):\n")
        for f in found_files["备份文件"]:
            f.write(f"  {f['path']}\n")

        f.write(f"\n测试文件 ({len(found_files['测试文件'])}):\n")
        for f in found_files["测试文件"]:
            f.write(f"  {f['path']}\n")

        f.write(f"\nDemo文件 ({len(found_files['Demo文件'])}):\n")
        for f in found_files["Demo文件"]:
            f.write(f"  {f['path']}\n")

        f.write(f"\n简单示例 ({len(found_files['简单示例'])}):\n")
        for f in found_files["简单示例"]:
            f.write(f"  {f['path']}\n")

        f.write(f"\n空目录 ({len(empty_dirs)}):\n")
        for d in empty_dirs:
            f.write(f"  {d}\n")

        f.write(f"\n重复文件 ({len(duplicates)}):\n")
        for dup in duplicates:
            f.write(f"  {dup['name']} (x{dup['count']}):\n")
            for p in dup['paths']:
                f.write(f"    {p}\n")

    print(f"\n📄 详细报告已保存到: quick_cleanup_report.txt")

    return {
        "backup_files": found_files["备份文件"],
        "test_files": found_files["测试文件"],
        "demo_files": found_files["Demo文件"],
        "simple_files": found_files["简单示例"],
        "empty_dirs": empty_dirs,
        "duplicates": duplicates
    }

if __name__ == "__main__":
    results = scan_platform()