#!/usr/bin/env python3
from __future__ import annotations
"""
Athena工作平台清理脚本
清理冗余和过期文件
"""

import glob
import os
import shutil
import time
from datetime import datetime, timedelta
from typing import Any


def cleanup_python_cache() -> Any:
    """清理Python缓存文件"""
    print("\n🧹 清理Python缓存文件...")

    base_path = "/Users/xujian/Athena工作平台"

    # 统计
    pyc_count = 0
    pycache_count = 0
    total_size = 0

    # 删除__pycache__目录
    for root, dirs, _files in os.walk(base_path):
        # 删除__pycache__目录
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                size = sum(os.path.getsize(os.path.join(dirpath, filename))
                          for dirpath, dirnames, filenames in os.walk(pycache_path)
                          for filename in filenames)
                shutil.rmtree(pycache_path)
                pycache_count += 1
                total_size += size
                print(f"  ✅ 删除 {pycache_path} ({size/1024/1024:.2f}MB)")
            except Exception as e:
                print(f"  ❌ 无法删除 {pycache_path}: {e}")

            # 从dirs列表中移除，避免进入该目录
            dirs.remove("__pycache__")

    # 删除.pyc和.pyo文件
    for pattern in ["*.pyc", "*.pyo"]:
        for file_path in glob.glob(os.path.join(base_path, "**", pattern), recursive=True):
            try:
                size = os.path.getsize(file_path)
                os.remove(file_path)
                pyc_count += 1
                total_size += size
                print(f"  ✅ 删除 {file_path} ({size/1024:.2f}KB)")
            except Exception as e:
                print(f"  ❌ 无法删除 {file_path}: {e}")

    print("\n📊 Python缓存清理完成：")
    print(f"  - 删除了 {pycache_count} 个 __pycache__ 目录")
    print(f"  - 删除了 {pyc_count} 个 .pyc/.pyo 文件")
    print(f"  - 释放空间：{total_size/1024/1024/1024:.2f}GB")

def cleanup_temp_files() -> Any:
    """清理临时文件"""
    print("\n🧹 清理临时文件...")

    base_path = "/Users/xujian/Athena工作平台"
    temp_dirs = ["_temp", "tmp", "temp"]

    total_size = 0

    for temp_dir in temp_dirs:
        temp_path = os.path.join(base_path, temp_dir)
        if os.path.exists(temp_path):
            try:
                # 获取大小
                size = sum(os.path.getsize(os.path.join(dirpath, filename))
                          for dirpath, dirnames, filenames in os.walk(temp_path)
                          for filename in filenames)
                total_size += size

                # 删除
                shutil.rmtree(temp_path)
                print(f"  ✅ 删除 {temp_path} ({size/1024:.2f}KB)")
            except Exception as e:
                print(f"  ❌ 无法删除 {temp_path}: {e}")

    print(f"\n📊 临时文件清理完成，释放空间：{total_size/1024:.2f}KB")

def cleanup_old_logs(days=7) -> Any:
    """清理过期日志文件"""
    print(f"\n🧹 清理超过{days}天的日志文件...")

    base_path = "/Users/xujian/Athena工作平台"
    cutoff_time = datetime.now() - timedelta(days=days)

    for root, _dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.log'):
                file_path = os.path.join(root, file)
                try:
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if mod_time < cutoff_time:
                        os.path.getsize(file_path)
                        os.remove(file_path)
                        print(f"  ✅ 删除 {file_path} ({mod_time.strftime('%Y-%m-%d')})")
                except Exception as e:
                    print(f"  ❌ 无法处理 {file_path}: {e}")

def cleanup_empty_dirs() -> Any:
    """清理空目录（保留重要的空目录）"""
    print("\n🧹 检查空目录...")

    base_path = "/Users/xujian/Athena工作平台"
    protected_dirs = {
        "__pycache__", "venv", "env", ".git", "node_modules",
        "logs", "data", "cache", "tmp", "temp"
    }

    empty_dirs = []

    for root, dirs, _files in os.walk(base_path, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                if not os.listdir(dir_path) and dir_name not in protected_dirs:
                    empty_dirs.append(dir_path)
            except Exception:
                pass

    # 不自动删除空目录，只报告
    if empty_dirs:
        print(f"\n📊 发现 {len(empty_dirs)} 个空目录（建议手动检查）：")
        for dir_path in empty_dirs[-10:]:  # 只显示最后10个
            print(f"  📁 {dir_path}")
        if len(empty_dirs) > 10:
            print(f"  ... 还有 {len(empty_dirs)-10} 个")

def generate_cleanup_report() -> Any:
    """生成清理报告"""
    print("\n📋 生成清理报告...")

    report = f"""
# Athena工作平台清理报告
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 已执行的操作
1. ✅ 清理Python缓存文件（__pycache__目录和.pyc/.pyo文件）
2. ✅ 清理临时文件（_temp, tmp, temp目录）
3. ✅ 清理过期日志文件（超过7天）
4. ✅ 检查空目录

## 建议保留的文件
- 所有.bak备份文件
- 当前日志文件（7天内）
- 项目中的测试文件
- 空目录（用于未来扩展）

## 后续建议
1. 定期运行清理脚本（建议每周一次）
2. 设置git ignore文件，避免提交缓存文件
3. 监控磁盘空间使用情况
"""

    report_path = "/Users/xujian/Athena工作平台/cleanup_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"  ✅ 报告已保存到：{report_path}")

def main() -> None:
    """主函数"""
    print("🚀 Athena工作平台清理工具")
    print("=" * 60)

    start_time = time.time()

    # 执行清理
    cleanup_python_cache()
    cleanup_temp_files()
    cleanup_old_logs(days=7)
    cleanup_empty_dirs()
    generate_cleanup_report()

    # 计算耗时
    elapsed = time.time() - start_time

    print("\n" + "="*60)
    print("✨ 清理完成！")
    print(f"⏱️  总耗时：{elapsed:.2f}秒")
    print("\n💡 建议：")
    print("1. 重启相关服务以确保清理生效")
    print("2. 检查重要功能是否正常运行")
    print("3. 定期运行此清理脚本")

if __name__ == "__main__":
    main()
