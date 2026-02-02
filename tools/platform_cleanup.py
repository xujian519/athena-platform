#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台文件清理工具
Platform File Cleanup Tool

扫描并识别冗余、过期和无用的文件
"""

import os
import logging

logger = logging.getLogger(__name__)
import re
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

class PlatformCleanupAnalyzer:
    """平台清理分析器"""

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.scan_results = {
            "redundant_files": [],
            "outdated_files": [],
            "test_files": [],
            "demo_files": [],
            "simple_files": [],
            "backup_files": [],
            "empty_directories": [],
            "duplicated_files": [],
            "large_files": [],
            "old_docs": []
        }

        # 文件大小阈值（MB）
        self.large_file_threshold = 50

        # 过期时间阈值（天）
        self.outdated_threshold = 180

        # 保留的目录
        self.protected_dirs = {
            ".git", "__pycache__", ".pytest_cache",
            ".idea", ".vscode", "node_modules"
        }

        # 需要保留的核心文件模式
        self.keep_patterns = {
            # 核心配置
            r"README\.md", r"requirements.*\.txt", r"pyproject\.toml",
            r"setup\.py", r"Pipfile", r".env.*",
            # 核心服务
            r"main\.py", r"app\.py", r"server\.py",
            # 数据库文件
            r".*\.sql", r".*\.db", r".*\.sqlite",
            # 重要文档
            r"COPYRIGHT", r"LICENSE", r"CHANGELOG",
        }

    def scan_platform(self) -> Dict:
        """扫描整个平台"""
        print("🔍 开始扫描平台文件...")

        # 1. 扫描文件
        print("  - 扫描文件...")
        self._scan_files()

        # 2. 分析测试文件
        print("  - 分析测试文件...")
        self._analyze_test_files()

        # 3. 分析demo文件
        print("  - 分析demo文件...")
        self._analyze_demo_files()

        # 4. 分析simple文件
        print("  - 分析simple文件...")
        self._analyze_simple_files()

        # 5. 查找备份文件
        print("  - 查找备份文件...")
        self._find_backup_files()

        # 6. 查找空目录
        print("  - 查找空目录...")
        self._find_empty_directories()

        # 7. 查找重复文件
        print("  - 查找重复文件...")
        self._find_duplicated_files()

        # 8. 查找大文件
        print("  - 查找大文件...")
        self._find_large_files()

        # 9. 分析过期文档
        print("  - 分析过期文档...")
        self._analyze_outdated_docs()

        print("✅ 扫描完成！")
        return self.scan_results

    def _scan_files(self):
        """扫描所有文件"""
        for file_path in self.root_path.rglob("*"):
            # 跳过受保护的目录
            if any(protected in str(file_path) for protected in self.protected_dirs):
                continue

            if file_path.is_file():
                # 检查文件修改时间
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                days_old = (datetime.now() - mtime).days

                if days_old > self.outdated_threshold:
                    self.scan_results["outdated_files"].append({
                        "path": str(file_path.relative_to(self.root_path)),
                        "size": file_path.stat().st_size,
                        "days_old": days_old,
                        "mtime": mtime.isoformat()
                    })

    def _analyze_test_files(self):
        """分析测试文件"""
        test_patterns = [
            r"test_.*\.py$",
            r".*_test\.py$",
            r"tests?.*/.*\.py$",
            r".*_spec\.py$",
            r"conftest\.py$"
        ]

        for pattern in test_patterns:
            for file_path in self.root_path.rglob(pattern):
                if file_path.is_file():
                    # 检查是否是真正的测试文件
                    content = file_path.read_text(errors='ignore')
                    if any(test_marker in content for test_marker in [
                        "import unittest", "import pytest",
                        "def test_", "class Test",
                        "@pytest", "@unittest"
                    ]):
                        self.scan_results["test_files"].append({
                            "path": str(file_path.relative_to(self.root_path)),
                            "size": file_path.stat().st_size,
                            "is_used": self._is_test_file_used(file_path)
                        })

    def _analyze_demo_files(self):
        """分析demo文件"""
        demo_patterns = [
            r".*demo.*\.py$",
            r".*Demo.*\.py$",
            r".*example.*\.py$",
            r".*Example.*\.py$",
            r"demo/.*",
            r"examples/.*"
        ]

        for pattern in demo_patterns:
            for file_path in self.root_path.rglob(pattern):
                if file_path.is_file():
                    self.scan_results["demo_files"].append({
                        "path": str(file_path.relative_to(self.root_path)),
                        "size": file_path.stat().st_size,
                        "is_redundant": self._is_demo_redundant(file_path)
                    })

    def _analyze_simple_files(self):
        """分析simple文件"""
        simple_patterns = [
            r".*simple.*\.py$",
            r".*Simple.*\.py$",
            r".*basic.*\.py$",
            r".*Basic.*\.py$",
            r".*tutorial.*\.py$"
        ]

        for pattern in simple_patterns:
            for file_path in self.root_path.rglob(pattern):
                if file_path.is_file():
                    self.scan_results["simple_files"].append({
                        "path": str(file_path.relative_to(self.root_path)),
                        "size": file_path.stat().st_size,
                        "is_tutorial": self._is_tutorial_file(file_path)
                    })

    def _find_backup_files(self):
        """查找备份文件"""
        backup_patterns = [
            r".*\.bak$",
            r".*\.backup$",
            r".*\.old$",
            r".*~$",
            r".*\.tmp$",
            r".*\.temp$",
            r".*_backup_.*",
            r".*_copy.*",
            r".*\.orig$"
        ]

        for pattern in backup_patterns:
            for file_path in self.root_path.rglob(pattern):
                if file_path.is_file():
                    self.scan_results["backup_files"].append({
                        "path": str(file_path.relative_to(self.root_path)),
                        "size": file_path.stat().st_size
                    })

    def _find_empty_directories(self):
        """查找空目录"""
        for dir_path in sorted(self.root_path.rglob("*"), reverse=True):
            if dir_path.is_dir():
                try:
                    # 尝试列出目录内容
                    contents = list(dir_path.iterdir())
                    if not contents or all(
                        f.name.startswith((".", "__")) for f in contents
                    ):
                        self.scan_results["empty_directories"].append({
                            "path": str(dir_path.relative_to(self.root_path))
                        })
                except PermissionError as e:                    # 记录异常但不中断流程
                    logger.debug(f"[platform_cleanup] PermissionError: {e}")

    def _find_duplicated_files(self):
        """查找重复文件（基于文件名）"""
        file_count = {}

        for file_path in self.root_path.rglob("*"):
            if file_path.is_file():
                filename = file_path.name
                if filename not in file_count:
                    file_count[filename] = []
                file_count[filename].append(file_path)

        # 找出有重复的文件
        for filename, files in file_count.items():
            if len(files) > 1 and not any(
                re.search(pattern, filename) for pattern in self.keep_patterns
            ):
                # 检查内容是否相同
                file_hashes = {}
                for file_path in files:
                    try:
                        file_hash = self._get_file_hash(file_path)
                        if file_hash not in file_hashes:
                            file_hashes[file_hash] = []
                        file_hashes[file_hash].append(file_path)
20except Exception as e:
20    # 记录异常但不中断流程
20    logger.debug(f"[platform_cleanup] Exception: {e}")

                for hash_value, duplicate_files in file_hashes.items():
                    if len(duplicate_files) > 1:
                        self.scan_results["duplicated_files"].append({
                            "filename": filename,
                            "hash": hash_value,
                            "files": [str(f.relative_to(self.root_path)) for f in duplicate_files]
                        })

    def _find_large_files(self):
        """查找大文件"""
        for file_path in self.root_path.rglob("*"):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                if size_mb > self.large_file_threshold:
                    # 检查是否是数据文件或模型文件
                    is_data_file = any(
                        ext in str(file_path).lower()
                        for ext in ['.pkl', '.pickle', '.h5', '.hdf5',
                                   '.model', '.bin', '.data', '.db',
                                   '.sqlite', '.parquet', '.csv']
                    )

                    self.scan_results["large_files"].append({
                        "path": str(file_path.relative_to(self.root_path)),
                        "size": file_path.stat().st_size,
                        "size_mb": round(size_mb, 2),
                        "is_data_file": is_data_file
                    })

    def _analyze_outdated_docs(self):
        """分析过期的文档"""
        doc_extensions = ['.md', '.rst', '.txt', '.html']

        for file_path in self.root_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in doc_extensions:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                days_old = (datetime.now() - mtime).days

                # 检查文档内容
                try:
                    content = file_path.read_text(errors='ignore')

                    # 查找可能过期的标记
                    outdated_markers = [
                        r"TBD", r"TODO", r"WIP", r"DRAFT",
                        r"版本[:：]\s*[0-9.]+",
                        r"更新日期[:：]\s*\d{4}[-/]\d{1,2}[-/]\d{1,2}",
                        r"deprecated", r"obsolete", r"legacy"
                    ]

                    has_markers = any(re.search(marker, content, re.IGNORECASE)
                                    for marker in outdated_markers)

                    if days_old > 90 and has_markers:
                        self.scan_results["old_docs"].append({
                            "path": str(file_path.relative_to(self.root_path)),
                            "days_old": days_old,
                            "has_markers": has_markers,
                            "size": file_path.stat().st_size
                        })
16except Exception as e:
16    # 记录异常但不中断流程
16    logger.debug(f"[platform_cleanup] Exception: {e}")

    def _is_test_file_used(self, file_path: Path) -> bool:
        """检查测试文件是否被使用"""
        # 检查是否有对应的源文件
        test_name = file_path.stem
        possible_sources = [
            f"{test_name.replace('test_', '')}.py",
            f"{test_name.replace('_test', '')}.py"
        ]

        for source in possible_sources:
            if (file_path.parent / source).exists():
                return True

        # 检查是否在配置中被引用
        try:
            config_files = [
                "pytest.ini", "setup.cfg", "pyproject.toml",
                "tox.ini", ".github/workflows"
            ]

            test_path = str(file_path.relative_to(self.root_path))
            for config in config_files:
                config_path = self.root_path / config
                if config_path.exists():
                    content = config_path.read_text(errors='ignore')
                    if test_path.replace('\\', '/') in content:
                        return True
8except Exception as e:
8    # 记录异常但不中断流程
8    logger.debug(f"[platform_cleanup] Exception: {e}")

        return False

    def _is_demo_redundant(self, file_path: Path) -> bool:
        """判断demo是否冗余"""
        try:
            content = file_path.read_text(errors='ignore')

            # 检查是否是简单的demo
            if len(content) < 1000:  # 小于1KB
                return True

            # 检查是否有过时的导入
            outdated_imports = [
                "from __future__ import",  # Python 2兼容代码
                "import tkinter",           # 可能是过时的UI demo
                "print('hello world')"     # 简单的示例
            ]

            if any(imp in content for imp in outdated_imports):
                return True
8except Exception as e:
8    # 记录异常但不中断流程
8    logger.debug(f"[platform_cleanup] Exception: {e}")

        return False

    def _is_tutorial_file(self, file_path: Path) -> bool:
        """判断是否是教程文件"""
        try:
            content = file_path.read_text(errors='ignore')

            tutorial_markers = [
                "# 教程", "# Tutorial", "# 示例", "# Example",
                "# 简单", "# Simple", "# 快速开始", "# Quick Start",
                "# 如何", "# How to"
            ]

            return any(marker in content for marker in tutorial_markers)
        except:
            return False

    def _get_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        import hashlib

        hasher = hashlib.md5(usedforsecurity=False)
        try:
            with open(file_path, 'rb') as f:
                # 只读取前1MB来计算哈希
                chunk = f.read(1024 * 1024)
                hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return ""

    def generate_cleanup_plan(self) -> Dict:
        """生成清理计划"""
        plan = {
            "safe_to_delete": [],
            "review_needed": [],
            "keep_files": [],
            "total_size_freed": 0,
            "actions": []
        }

        # 1. 安全删除的文件
        safe_patterns = {
            "backup_files": "备份文件",
            "empty_directories": "空目录"
        }

        for category, desc in safe_patterns.items():
            for item in self.scan_results.get(category, []):
                if "size" in item:
                    plan["total_size_freed"] += item["size"]
                plan["safe_to_delete"].append({
                    "path": item["path"],
                    "category": category,
                    "description": desc
                })

        # 2. 需要审查的文件
        review_categories = {
            "test_files": "测试文件",
            "demo_files": "Demo文件",
            "simple_files": "简单示例文件",
            "outdated_files": "过期文件",
            "duplicated_files": "重复文件",
            "old_docs": "过期文档"
        }

        for category, desc in review_categories.items():
            for item in self.scan_results.get(category, []):
                # 跳过正在使用的测试文件
                if category == "test_files" and item.get("is_used", False):
                    plan["keep_files"].append({
                        "path": item["path"],
                        "reason": "正在使用的测试文件"
                    })
                # 跳过非冗余的demo
                elif category == "demo_files" and not item.get("is_redundant", False):
                    plan["keep_files"].append({
                        "path": item["path"],
                        "reason": "非冗余的demo文件"
                    })
                else:
                    if "size" in item:
                        plan["total_size_freed"] += item["size"]
                    if isinstance(item, dict):
                        item["category"] = category
                        item["description"] = desc
                        plan["review_needed"].append(item)
                    else:
                        plan["review_needed"].append({
                            "path": item,
                            "category": category,
                            "description": desc
                        })

        # 3. 生成具体操作
        plan["actions"] = [
            f"1. 删除 {len(plan['safe_to_delete'])} 个安全删除的文件/目录",
            f"2. 审查 {len(plan['review_needed'])} 个需要确认的文件",
            f"3. 保留 {len(plan['keep_files'])} 个重要文件",
            f"4. 预计释放空间: {plan['total_size_freed'] / (1024*1024):.2f} MB"
        ]

        return plan

    def generate_report(self) -> str:
        """生成清理报告"""
        plan = self.generate_cleanup_plan()

        report = f"""# 平台文件清理报告

**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**扫描路径**: {self.root_path}

## 📊 扫描统计

| 类别 | 数量 | 大小 |
|------|------|------|
| 测试文件 | {len(self.scan_results['test_files'])} | {sum(f['size'] for f in self.scan_results['test_files']) / (1024*1024):.2f} MB |
| Demo文件 | {len(self.scan_results['demo_files'])} | {sum(f['size'] for f in self.scan_results['demo_files']) / (1024*1024):.2f} MB |
| Simple文件 | {len(self.scan_results['simple_files'])} | {sum(f['size'] for f in self.scan_results['simple_files']) / (1024*1024):.2f} MB |
| 备份文件 | {len(self.scan_results['backup_files'])} | {sum(f['size'] for f in self.scan_results['backup_files']) / (1024*1024):.2f} MB |
| 过期文件 | {len(self.scan_results['outdated_files'])} | {sum(f['size'] for f in self.scan_results['outdated_files']) / (1024*1024):.2f} MB |
| 空目录 | {len(self.scan_results['empty_directories'])} | - |
| 重复文件 | {len(self.scan_results['duplicated_files'])} | {sum(f['size'] for group in self.scan_results['duplicated_files'] for f in group['files']) / (1024*1024):.2f} MB |
| 大文件 | {len(self.scan_results['large_files'])} | {sum(f['size'] for f in self.scan_results['large_files']) / (1024*1024):.2f} MB |
| 过期文档 | {len(self.scan_results['old_docs'])} | {sum(f['size'] for f in self.scan_results['old_docs']) / (1024*1024):.2f} MB |

## 🎯 清理建议

### 安全删除（建议立即执行）
"""

        for item in plan["safe_to_delete"]:
            report += f"- `{item['path']}` - {item['description']}\n"

        report += f"""
### 需要审查（建议手动确认）
"""

        for item in plan["review_needed"][:20]:  # 只显示前20个
            report += f"- `{item['path'] if isinstance(item, dict) else item}` - {item['description']}\n"

        if len(plan["review_needed"]) > 20:
            report += f"- ... 还有 {len(plan['review_needed']) - 20} 个文件需要审查\n"

        report += f"""
## 📋 执行计划
"""

        for action in plan["actions"]:
            report += f"- {action}\n"

        report += f"""
## 🔧 执行命令

```bash
# 1. 生成详细的删除脚本
python3 tools/platform_cleanup.py --generate-delete-script

# 2. 执行清理（先dry-run）
python3 tools/platform_cleanup.py --execute --dry-run

# 3. 实际执行清理
python3 tools/platform_cleanup.py --execute
```

---
*报告由 platform_cleanup.py 生成*
"""

        return report

def main():
    """主函数"""
    import argparse
    import shutil

    parser = argparse.ArgumentParser(description="平台文件清理工具")
    parser.add_argument("--root", default=".", help="扫描根目录")
    parser.add_argument("--generate-delete-script", action="store_true",
                      help="生成删除脚本")
    parser.add_argument("--execute", action="store_true",
                      help="执行清理操作")
    parser.add_argument("--dry-run", action="store_true",
                      help="预览模式（不实际删除）")
    parser.add_argument("--report", help="保存报告到文件")

    args = parser.parse_args()

    analyzer = PlatformCleanupAnalyzer(args.root)

    # 执行扫描
    results = analyzer.scan_platform()

    # 生成报告
    report = analyzer.generate_report()

    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 报告已保存到: {args.report}")
    else:
        print(report)

    # 生成删除脚本
    if args.generate_delete_script:
        plan = analyzer.generate_cleanup_plan()

        delete_script = """#!/bin/bash
# 自动生成的文件删除脚本
# 执行前请仔细检查！

set -e

echo "⚠️  准备删除文件..."
echo "按 Ctrl+C 取消，按 Enter 继续..."
read

"""

        # 添加删除命令
        for item in plan["safe_to_delete"]:
            delete_script += f'echo "删除: {item["path"]}"\n'
            delete_script += f'rm -rf "{item["path"]}"\n'

        delete_script += """
echo "✅ 清理完成！"
"""

        script_path = "cleanup_files.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(delete_script)

        os.chmod(script_path, 0o755)
        print(f"\n✅ 删除脚本已生成: {script_path}")
        print("⚠️  执行前请检查脚本内容！")

    # 执行清理
    if args.execute:
        plan = analyzer.generate_cleanup_plan()

        if args.dry_run:
            print("\n🔍 Dry-run模式 - 以下文件将被删除:")
            for item in plan["safe_to_delete"]:
                print(f"  - {item['path']}")
        else:
            # 实际删除
            print("\n🗑️  开始清理...")
            deleted_count = 0
            freed_space = 0

            for item in plan["safe_to_delete"]:
                try:
                    path = Path(args.root) / item["path"]
                    if path.exists():
                        size = path.stat().st_size if path.is_file() else 0
                        if path.is_file():
                            path.unlink()
                        else:
                            shutil.rmtree(path)
                        deleted_count += 1
                        freed_space += size
                        print(f"  ✅ 已删除: {item['path']}")
                except Exception as e:
                    print(f"  ❌ 删除失败: {item['path']} - {e}")

            print(f"\n✅ 清理完成!")
            print(f"  删除文件/目录: {deleted_count}")
            print(f"  释放空间: {freed_space / (1024*1024):.2f} MB")

if __name__ == "__main__":
    main()