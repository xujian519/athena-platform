#!/usr/bin/env python3
"""
补充清理脚本
清理.DS_Store文件和其他冗余文件
"""

import os
import shutil
import subprocess

def cleanup_ds_store():
    """清理.DS_Store文件"""
    print("\n🧹 清理.DS_Store文件...")

    base_path = "/Users/xujian/Athena工作平台"
    count = 0

    for root, dirs, files in os.walk(base_path):
        if ".DS_Store" in files:
            ds_store_path = os.path.join(root, ".DS_Store")
            try:
                os.remove(ds_store_path)
                count += 1
                print(f"  ✅ 删除 {ds_store_path}")
            except Exception as e:
                print(f"  ❌ 无法删除 {ds_store_path}: {e}")

    print(f"\n📊 删除了 {count} 个.DS_Store文件")

def cleanup_backup_dirs():
    """清理备份目录"""
    print("\n🧹 检查备份目录...")

    base_path = "/Users/xujian/Athena工作平台"
    backup_dirs = ["_backup", "_temp"]

    total_size = 0

    for backup_dir in backup_dirs:
        backup_path = os.path.join(base_path, backup_dir)
        if os.path.exists(backup_path):
            try:
                # 计算大小
                size = 0
                for dirpath, dirnames, filenames in os.walk(backup_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            size += os.path.getsize(filepath)
                        except:
                            pass

                total_size += size
                print(f"  📁 {backup_dir}: {size/1024/1024:.2f}MB")
                print(f"     路径: {backup_path}")
            except Exception as e:
                print(f"  ❌ 无法处理 {backup_path}: {e}")

    print(f"\n💾 备份目录总大小: {total_size/1024/1024:.2f}MB")

def cleanup_pycache_remaining():
    """清理剩余的__pycache__"""
    print("\n🧹 检查剩余的__pycache__...")

    base_path = "/Users/xujian/Athena工作平台"
    count = 0

    for root, dirs, files in os.walk(base_path):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                count += 1
                print(f"  ✅ 删除 {pycache_path}")
                dirs.remove("__pycache__")
            except Exception as e:
                print(f"  ❌ 无法删除 {pycache_path}: {e}")

    if count == 0:
        print("  ✅ 没有找到剩余的__pycache__目录")
    else:
        print(f"\n📊 删除了 {count} 个剩余的__pycache__目录")

def cleanup_log_files():
    """清理旧日志文件"""
    print("\n🧹 检查日志文件...")

    import datetime

    base_path = "/Users/xujian/Athena工作平台"
    old_logs = []

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.log'):
                file_path = os.path.join(root, file)
                try:
                    mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    # 超过30天的日志
                    if (datetime.datetime.now() - mod_time).days > 30:
                        old_logs.append(file_path)
                        size = os.path.getsize(file_path)
                        os.remove(file_path)
                        print(f"  ✅ 删除 {file_path} ({size/1024:.2f}KB, {mod_time.strftime('%Y-%m-%d')})")
                except Exception as e:
                    print(f"  ❌ 无法处理 {file_path}: {e")

    if not old_logs:
        print("  ✅ 没有找到超过30天的日志文件")

def show_space_usage():
    """显示磁盘空间使用情况"""
    print("\n💽 磁盘空间使用情况：")

    # 获取目录大小
    base_path = "/Users/xujian/Athena工作平台"

    subprocess.run([
        'du', '-sh', base_path
    ])

def generate_cleanup_summary():
    """生成清理总结"""
    print("\n📋 清理总结：")
    print("=" * 50)
    print("✅ 已清理：")
    print("  1. Python缓存文件 (__pycache__ 和 .pyc)")
    print("  2. .DS_Store 文件")
    print("  3. 超过30天的日志文件")
    print("\n📁 检查了以下目录：")
    print("  - _backup (备份文件)")
    print("  - _temp (临时文件)")
    print("\n💡 建议：")
    print("  1. 定期运行清理脚本（建议每周）")
    print("  2. 在.gitignore中添加：")
    print("     __pycache__/")
    print("     *.pyc")
    print("     .DS_Store")
    print("  3. 考虑清理_node_modules（如果存在）")

def main():
    """主函数"""
    print("🚀 Athena工作平台补充清理")
    print("=" * 60)

    # 执行清理
    cleanup_ds_store()
    cleanup_pycache_remaining()
    cleanup_log_files()
    cleanup_backup_dirs()

    # 显示信息
    show_space_usage()
    generate_cleanup_summary()

    print("\n✨ 补充清理完成！")

if __name__ == "__main__":
    main()