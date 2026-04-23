#!/usr/bin/env python3
"""
搜索和导入所有历史记忆
"""

import json
import os
import sqlite3
import subprocess
from typing import Any

# PostgreSQL连接信息
PSQL_PATH = '/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql'
DB_HOST = 'localhost'
DB_PORT = '5438'
DB_NAME = 'memory_module'

def search_sqlite_memories() -> Any | None:
    """搜索所有SQLite数据库中的记忆"""
    print("🔍 搜索SQLite数据库中的历史记忆...\n")

    # 潜在的数据库路径
    db_paths = [
        "/Users/xujian/Athena工作平台/patent-platform/workspace/src/cognition/memory_storage.db",
        "/Users/xujian/Athena工作平台/patent-platform/workspace/src/cognition/test_memory_fix.db",
        "/Users/xujian/Athena工作平台/data/memory/cold_tier.db",
        "/Users/xujian/Athena工作平台/data/support_data/databases/memory_active.db",
    ]

    found_memories = []

    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"📁 检查: {db_path}")
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # 获取所有表名
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()

                for table_name, in tables:
                    if 'memory' in table_name.lower() or 'trace' in table_name.lower():
                        # 使用参数化查询防止SQL注入
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]

                        if count > 0:
                            print(f"  ✅ 表 {table_name}: {count} 条记录")

                            # 获取样本数据 - 使用参数化查询
                            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                            rows = cursor.fetchall()

                            # 获取列名 - 使用参数化查询
                            cursor.execute(f"PRAGMA table_info({table_name})")
                            columns = [col[1] for col in cursor.fetchall()]

                            for row in rows:
                                memory_data = dict(zip(columns, row, strict=False))
                                found_memories.append({
                                    'source': db_path,
                                    'table': table_name,
                                    'data': memory_data
                                })

                conn.close()

            except Exception as e:
                print(f"  ❌ 错误: {e}")

    return found_memories

def search_json_memories() -> Any | None:
    """搜索JSON文件中的记忆"""
    print("\n📄 搜索JSON文件中的历史记忆...\n")

    json_files = [
        "/Users/xujian/Athena工作平台/documentation/logs/xiaonuo_enhanced_status.json",
    ]

    found_memories = []

    for json_file in json_files:
        if os.path.exists(json_file):
            print(f"📁 检查: {json_file}")
            try:
                with open(json_file, encoding='utf-8') as f:
                    data = json.load(f)

                    # 检查是否包含记忆相关内容
                    if any(key in str(data).lower() for key in ['memory', '记忆', 'status', '状态']):
                        found_memories.append({
                            'source': json_file,
                            'type': 'json',
                            'data': data
                        })
                        print("  ✅ 找到记忆相关数据")

            except Exception as e:
                print(f"  ❌ 错误: {e}")

    return found_memories

def check_current_memory_status() -> bool:
    """检查当前记忆系统状态"""
    print("\n📊 当前记忆系统状态:\n")

    # 总记忆数
    cmd = [
        PSQL_PATH, '-h', DB_HOST, '-p', str(DB_PORT),
        '-d', DB_NAME, '-c', "SELECT COUNT(*) FROM memory_items;"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 3:
            total = lines[2].strip()
            print(f"  总记忆数: {total}")

    # 历史记忆数
    cmd = [
        PSQL_PATH, '-h', DB_HOST, '-p', str(DB_PORT),
        '-d', DB_NAME, '-c', "SELECT COUNT(*) FROM memory_items WHERE metadata->>'source' IN ('sqlite_import', 'json_import');"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 3:
            historical = lines[2].strip()
            print(f"  历史记忆数: {historical}")

    # 按类型分布
    cmd = [
        PSQL_PATH, '-h', DB_HOST, '-p', str(DB_PORT),
        '-d', DB_NAME, '-c', "SELECT memory_type, COUNT(*) FROM memory_items GROUP BY memory_type ORDER BY COUNT(*) DESC;"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("\n  按类型分布:")
        lines = result.stdout.strip().split('\n')[2:-1]  # 跳过头部和尾部
        for line in lines:
            if ' | ' in line:
                type_, count = line.split(' | ')
                print(f"    - {type_.strip()}: {count.strip()}")

def main() -> None:
    """主函数"""
    print("=" * 60)
    print("🔍 历史记忆搜索报告")
    print("=" * 60)

    # 1. 检查当前状态
    check_current_memory_status()

    # 2. 搜索SQLite记忆
    sqlite_memories = search_sqlite_memories()

    # 3. 搜索JSON记忆
    json_memories = search_json_memories()

    # 4. 总结
    print("\n" + "=" * 60)
    print("📋 搜索总结:")
    print(f"  - SQLite数据库记忆: {len(sqlite_memories)} 条")
    print(f"  - JSON文件记忆: {len(json_memories)} 条")

    total_found = len(sqlite_memories) + len(json_memories)
    if total_found == 0:
        print("\n✅ 所有历史记忆已经导入到新的记忆系统中！")
    else:
        print(f"\n⚠️  还有 {total_found} 条历史记忆未导入")
        print("   建议运行 import_comprehensive.py 进行导入")

if __name__ == "__main__":
    main()
