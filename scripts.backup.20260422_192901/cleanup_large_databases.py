#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理大型数据库脚本
Cleanup Large Databases Script

处理剩余的大型数据库文件，进一步优化系统性能

作者: 小诺
创建时间: 2025-12-17
版本: v1.0.0
"""

import os
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

def check_large_databases() -> bool:
    """检查大型数据库"""
    base_path = Path("/Users/xujian/Athena工作平台")

    large_dbs = []

    # 检查特定的大型数据库
    large_db_paths = [
        base_path / "data/knowledge_graph_sqlite/databases/patent_knowledge_graph.db",
        base_path / "data/support_data/databases/legal_laws_database.db",
        base_path / "backup/migration_backup_20251212_132121/legal_laws.db"
    ]

    for db_path in large_db_paths:
        if db_path.exists():
            size = db_path.stat().st_size
            size_mb = size / (1024 * 1024)

            # 检查数据库内容
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()

                # 获取表的数量
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
                table_count = cursor.fetchone()[0]

                # 获取记录数
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5;")
                tables = cursor.fetchall()

                total_records = 0
                for (table_name,) in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                        records = cursor.fetchone()[0]
                        total_records += records
                    except:
                        pass

                conn.close()

                large_dbs.append({
                    'path': db_path,
                    'relative_path': db_path.relative_to(base_path),
                    'size_mb': size_mb,
                    'table_count': table_count,
                    'total_records': total_records,
                    'is_backup': 'backup' in str(db_path)
                })

            except Exception as e:
                print(f"⚠️ 检查数据库时出错 {db_path}: {e}")
                large_dbs.append({
                    'path': db_path,
                    'relative_path': db_path.relative_to(base_path),
                    'size_mb': size_mb,
                    'table_count': 'unknown',
                    'total_records': 'unknown',
                    'is_backup': 'backup' in str(db_path),
                    'error': str(e)
                })

    return large_dbs

def cleanup_large_databases() -> Any:
    """清理大型数据库"""
    print("🔍 检查剩余的大型数据库...")

    large_dbs = check_large_databases()

    if not large_dbs:
        print("✅ 没有发现大型数据库需要处理")
        return

    print(f"\n📊 发现 {len(large_dbs)} 个大型数据库:")

    for i, db in enumerate(large_dbs, 1):
        print(f"\n{i}. {db['relative_path']}")
        print(f"   大小: {db['size_mb']:.1f} MB")
        print(f"   类型: {'备份文件' if db['is_backup'] else '活跃文件'}")

        if 'table_count' in db:
            print(f"   表数: {db['table_count']}")
            print(f"   记录数: {db['total_records']}")

        if 'error' in db:
            print(f"   ⚠️ 错误: {db['error']}")

    print("\n💡 建议操作:")

    # 处理建议
    for db in large_dbs:
        print(f"\n📁 {db['relative_path']}:")

        if db['is_backup']:
            print("   ✅ 这是备份文件，建议删除")

            # 删除备份文件
            try:
                db['path'].unlink()
                print(f"   ✅ 已删除备份文件，释放 {db['size_mb']:.1f} MB 空间")
            except Exception as e:
                print(f"   ❌ 删除失败: {e}")

        elif db['size_mb'] > 100:  # 大于100MB的文件
            print(f"   ⚠️ 这是一个非常大的活跃数据库 ({db['size_mb']:.1f} MB)")

            if 'table_count' in db and db['table_count'] > 0:
                print(f"   📊 包含 {db['table_count']} 个表，{db['total_records']} 条记录")
                print("   💡 建议保留但需要优化")

                # 提供压缩选项
                print("   🔧 执行数据库压缩...")
                try:
                    conn = sqlite3.connect(str(db['path']))
                    conn.execute("VACUUM;")
                    conn.close()

                    # 检查压缩后的大小
                    new_size = db['path'].stat().st_size / (1024 * 1024)
                    saved = db['size_mb'] - new_size
                    print(f"   ✅ 压缩完成，节省 {saved:.1f} MB 空间")

                except Exception as e:
                    print(f"   ❌ 压缩失败: {e}")
            else:
                print("   💡 看起来是空数据库或损坏，建议删除")

                # 询问是否删除
                response = input("   🗑️ 是否删除这个数据库? (y/N): ")
                if response.lower() == 'y':
                    try:
                        db['path'].unlink()
                        print(f"   ✅ 已删除，释放 {db['size_mb']:.1f} MB 空间")
                    except Exception as e:
                        print(f"   ❌ 删除失败: {e}")

def main() -> None:
    """主函数"""
    print("🧹 大型数据库清理工具")
    print("=" * 40)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    cleanup_large_databases()

    print("\n✅ 清理完成！")

if __name__ == "__main__":
    main()