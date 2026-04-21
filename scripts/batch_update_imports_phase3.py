#!/usr/bin/env python3
"""
批量更新导入路径 - Phase 3专利目录整合
Batch Update Import Paths - Phase 3 Patent Directory Unification

将所有 `from patents.core.*` 和 `import patents.core.*` 更新为 `from patents.core.*`

执行方式:
    python3 scripts/batch_update_imports_phase3.py

回滚方式:
    git checkout . -- revert all changes
"""

import os
import re
from pathlib import Path
from datetime import datetime

# 配置
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
DRY_RUN = False  # 设为True只显示会修改什么，不实际修改

# 需要更新的导入路径模式
IMPORT_PATTERNS = [
    # from patents.core.xxx -> from patents.core.xxx
    (r'from core\.patent\.', 'from patents.core.'),
    # import patents.core.xxx -> import patents.core.xxx
    (r'import core\.patent\.', 'import patents.core.'),
]

# 排除的目录
EXCLUDE_DIRS = {
    '.git',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    'node_modules',
    'venv',
    '.venv',
    'dist',
    'build',
    '*.egg-info',
    # 排除旧目录（稍后删除）
    'core/patent',  # 旧目录
}

# 需要处理的文件扩展名
INCLUDE_EXTENSIONS = {'.py'}


def should_process_file(file_path: Path) -> bool:
    """判断文件是否需要处理"""
    # 检查文件扩展名
    if file_path.suffix not in INCLUDE_EXTENSIONS:
        return False

    # 检查是否在排除目录中
    for part in file_path.parts:
        if part in EXCLUDE_DIRS:
            return False

    return True


def update_imports_in_file(file_path: Path) -> dict:
    """更新单个文件的导入路径"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        changes = []

        # 应用所有替换模式
        for pattern, replacement in IMPORT_PATTERNS:
            matches = list(re.finditer(pattern, content))
            if matches:
                content = re.sub(pattern, replacement, content)
                changes.extend([
                    {
                        'line': content[:match.start()].count('\n') + 1,
                        'old': match.group(0),
                        'new': re.sub(pattern, replacement, match.group(0))
                    }
                    for match in matches
                ])

        if content != original_content:
            if not DRY_RUN:
                file_path.write_text(content, encoding='utf-8')
            return {
                'file': str(file_path.relative_to(PROJECT_ROOT)),
                'changes': len(changes),
                'details': changes
            }

    except Exception as e:
        print(f"❌ 错误处理文件 {file_path}: {e}")

    return None


def main():
    """主函数"""
    print("=" * 70)
    print("批量更新导入路径 - Phase 3专利目录整合")
    print("=" * 70)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"模式: {'模拟运行（不实际修改）' if DRY_RUN else '实际修改文件'}")
    print()

    # 统计信息
    total_files = 0
    modified_files = 0
    total_changes = 0

    # 遍历所有Python文件
    print("🔍 扫描Python文件...")
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # 过滤掉排除的目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            file_path = Path(root) / file

            if should_process_file(file_path):
                total_files += 1
                result = update_imports_in_file(file_path)

                if result:
                    modified_files += 1
                    total_changes += result['changes']

                    print(f"✓ {result['file']}")
                    print(f"  修改: {result['changes']}处")

                    # 显示详细修改
                    for change in result['details'][:3]:  # 最多显示3处
                        print(f"  第{change['line']}行: {change['old']} → {change['new']}")
                    if len(result['details']) > 3:
                        print(f"  ... 还有{len(result['details']) - 3}处修改")
                    print()

    # 打印统计信息
    print("=" * 70)
    print("📊 统计信息")
    print("=" * 70)
    print(f"扫描文件数: {total_files}")
    print(f"修改文件数: {modified_files}")
    print(f"总修改数: {total_changes}")
    print()

    if DRY_RUN:
        print("⚠️  这是模拟运行，没有实际修改文件")
        print("   要实际修改，请设置 DRY_RUN = False")
    else:
        print("✅ 导入路径更新完成！")
        print()
        print("下一步:")
        print("1. 运行测试验证功能")
        print("2. 如果出现问题，使用 git checkout . 回滚")
        print("3. 如果一切正常，提交更改")

    print()
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
