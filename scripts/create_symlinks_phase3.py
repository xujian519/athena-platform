#!/usr/bin/env python3
"""
创建符号链接 - Phase 3专利目录整合
Create Symbolic Links - Phase 3 Patent Directory Unification

为向后兼容性创建符号链接，使旧的导入路径仍然可以工作

执行方式:
    python3 scripts/create_symlinks_phase3.py

清理方式:
    python3 scripts/create_symlinks_phase3.py --remove
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# 配置
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")

# 符号链接映射：旧路径 -> 新路径
SYMLINK_MAPPINGS = [
    # core/patent -> patents/core
    {
        'old': PROJECT_ROOT / 'core' / 'patent',
        'new': PROJECT_ROOT / 'patents' / 'core',
        'description': 'core/patent -> patents/core'
    },
    # 如果后续有更多映射，在这里添加
]


def remove_symlink(symlink_path: Path) -> bool:
    """删除符号链接（如果是符号链接）"""
    try:
        if symlink_path.is_symlink():
            symlink_path.unlink()
            print(f"  ✓ 已删除符号链接: {symlink_path}")
            return True
        elif symlink_path.exists():
            print(f"  ⚠️  路径存在但不是符号链接: {symlink_path}")
            print(f"     类型: {'目录' if symlink_path.is_dir() else '文件'}")
            return False
        else:
            print(f"  ℹ️  路径不存在: {symlink_path}")
            return True
    except Exception as e:
        print(f"  ❌ 删除失败: {e}")
        return False


def create_symlink(old_path: Path, new_path: Path) -> bool:
    """创建符号链接"""
    try:
        # 如果旧路径已存在，需要处理
        if old_path.exists():
            if old_path.is_symlink():
                # 已经是符号链接，删除它
                old_path.unlink()
                print(f"  ✓ 删除旧符号链接: {old_path}")
            else:
                # 是真实目录/文件，需要重命名
                backup_path = old_path.with_suffix(old_path.suffix + '.bak')
                if backup_path.exists():
                    backup_path = old_path.with_suffix(
                        old_path.suffix + f'.bak_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                    )
                shutil.move(old_path, backup_path)
                print(f"  ⚠️  已备份原有目录: {old_path}")
                print(f"     → {backup_path}")

        # 创建相对路径符号链接（更便携）
        relative_path = os.path.relpath(new_path, old_path.parent)
        old_path.symlink_to(relative_path)

        print(f"  ✓ 创建符号链接: {old_path} -> {new_path}")
        print(f"     (相对路径: {relative_path})")

        # 验证符号链接
        if old_path.is_symlink():
            target = os.readlink(old_path)
            print(f"  ✓ 验证成功: {target}")
            return True
        else:
            print(f"  ❌ 验证失败: 符号链接未创建")
            return False

    except Exception as e:
        print(f"  ❌ 创建符号链接失败: {e}")
        return False


def main():
    """主函数"""
    # 检查命令行参数
    remove_mode = '--remove' in sys.argv or '--cleanup' in sys.argv

    print("=" * 70)
    print("符号链接管理 - Phase 3专利目录整合")
    print("=" * 70)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"模式: {'删除符号链接' if remove_mode else '创建符号链接'}")
    print()

    if remove_mode:
        print("🗑️  删除符号链接...")
    else:
        print("🔗 创建符号链接...")
    print()

    success_count = 0
    fail_count = 0

    for mapping in SYMLINK_MAPPINGS:
        old_path = mapping['old']
        new_path = mapping['new']
        description = mapping['description']

        print(f"处理: {description}")
        print(f"  旧路径: {old_path}")
        print(f"  新路径: {new_path}")

        # 验证新路径存在
        if not remove_mode and not new_path.exists():
            print(f"  ⚠️  警告: 目标路径不存在: {new_path}")
            fail_count += 1
            print()
            continue

        if remove_mode:
            # 删除模式
            if remove_symlink(old_path):
                success_count += 1
            else:
                fail_count += 1
        else:
            # 创建模式
            if create_symlink(old_path, new_path):
                success_count += 1
            else:
                fail_count += 1

        print()

    # 打印统计信息
    print("=" * 70)
    print("📊 统计信息")
    print("=" * 70)
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print()

    if not remove_mode:
        print("✅ 符号链接创建完成！")
        print()
        print("向后兼容性:")
        print("  ✓ 旧代码 `from core.patent.xxx` 仍然可以工作")
        print("  ✓ 新代码 `from patents.core.xxx` 也可以使用")
        print()
        print("下一步:")
        print("  1. 运行测试验证功能")
        print("  2. 如果出现问题，删除符号链接: python3 scripts/create_symlinks_phase3.py --remove")
        print("  3. 如果一切正常，稍后可以逐步迁移到新导入路径")
    else:
        print("✅ 符号链接删除完成！")
        print()
        print("注意:")
        print("  - 删除符号链接后，旧导入路径将不再工作")
        print("  - 确保所有代码都已更新为新导入路径")

    print()
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
