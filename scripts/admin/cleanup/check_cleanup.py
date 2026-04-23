#!/usr/bin/env python3
"""
检查实际清理情况
"""

import os


def check_cleanup_status() -> bool:
    base_path = "/Users/xujian/Athena工作平台"

    print("\n🔍 检查清理状态...")
    print("=" * 50)

    # 检查__pycache__
    pycache_count = 0
    pyc_count = 0
    ds_store_count = 0
    tmp_files = 0

    for _root, dirs, files in os.walk(base_path):
        # 检查__pycache__
        if "__pycache__" in dirs:
            pycache_count += 1

        # 检查.pyc文件
        for file in files:
            if file.endswith('.pyc'):
                pyc_count += 1
            elif file == '.DS_Store':
                ds_store_count += 1
            elif file.endswith('.tmp') or file.endswith('.temp'):
                tmp_files += 1

    print("\n📊 当前状态：")
    print(f"  __pycache__ 目录：{pycache_count} 个")
    print(f"  .pyc 文件：{pyc_count} 个")
    print(f"  .DS_Store 文件：{ds_store_count} 个")
    print(f"  临时文件：{tmp_files} 个")

    # 检查平台大小
    import subprocess
    result = subprocess.run(['du', '-sh', base_path], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"\n📏 平台总大小：{result.stdout.split()[0]}")

    # 检查大目录
    print("\n📁 主要目录大小：")
    subprocess.run(['du', '-sh', '--max-depth=1', base_path], capture_output=True, text=True)

if __name__ == "__main__":
    check_cleanup_status()
