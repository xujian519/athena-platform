#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接导入历史记忆
Direct Import Historical Memories

使用直接SQL插入方式

作者: Athena平台团队
创建时间: 2025年12月15日
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import json
import sys
from datetime import datetime
import subprocess

def export_from_sqlite() -> Any:
    """从SQLite导出"""
    print("📂 从SQLite导出历史记忆...")

    db_path = "/Users/xujian/Athena工作平台/patent-platform/workspace/src/cognition/memory_storage.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查询记忆数据
        cursor.execute("SELECT * FROM memory_traces")
        rows = cursor.fetchall()
        conn.close()

        print(f"✅ 找到 {len(rows)} 条记忆")

        return rows

    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return []

def create_insert_sql(rows) -> Any:
    """创建INSERT SQL语句"""
    print("\n📝 生成PostgreSQL插入语句...")

    sql_statements = []

    for row in rows:
        # 解析内容
        content = row[2] if len(row) > 2 else ""
        if isinstance(content, str):
            try:
                content_dict = json.loads(content)
                text = content_dict.get('text', content)
            except:
                text = content
        else:
            text = str(content)

        # 转义单引号
        text = text.replace("'", "''")

        # 确定类型
        text_lower = text.lower()
        if '爸爸' in text_lower or '爱' in text_lower:
            memory_type = 'family'
            agent_type = 'xiaonuo'
        elif '语义' in str(row[1]):
            memory_type = 'knowledge'
            agent_type = 'athena'
        else:
            memory_type = 'conversation'
            agent_type = 'athena'

        # 创建INSERT语句
        sql = f"""
INSERT INTO memory_items (
    agent_id, agent_type, content, memory_type, memory_tier,
    importance, emotional_weight, family_related, work_related,
    tags, metadata, created_at, updated_at
) VALUES (
    'historical_{agent_type}',
    '{agent_type}',
    '{text}',
    '{memory_type}',
    'warm',
    {float(row[4]) if len(row) > 4 else 0.5},
    0.5,
    {'true' if 'family' in text_lower else 'false'},
    true,
    ARRAY['历史导入', 'sqlite'],
    '{{"source": "sqlite_import", "import_date": "{datetime.now().isoformat()}"}}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
);
"""
        sql_statements.append(sql)

    return sql_statements

def save_sql_file(sql_statements) -> None:
    """保存SQL到文件"""
    print("💾 保存SQL文件...")

    with open('import_historical_memories.sql', 'w', encoding='utf-8') as f:
        f.write("-- 历史记忆导入SQL\n")
        f.write(f"-- 生成时间: {datetime.now().isoformat()}\n")
        f.write(f"-- 总记忆数: {len(sql_statements)}\n\n")

        for i, sql in enumerate(sql_statements, 1):
            f.write(f"-- 记忆 #{i}\n")
            f.write(sql)
            f.write("\n")

    print(f"✅ 已保存 {len(sql_statements)} 条SQL语句到 import_historical_memories.sql")

def execute_sql_file() -> Any:
    """执行SQL文件"""
    print("\n🚀 执行SQL导入...")

    # 使用psql执行
    cmd = [
        '/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql',
        '-h', 'localhost',
        '-p', '5438',
        '-d', 'memory_module',
        '-f', 'import_historical_memories.sql'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ SQL执行成功")
            print(result.stdout)
        else:
            print("⚠️ SQL执行有警告:")
            print(result.stderr)

    except Exception as e:
        print(f"❌ 执行失败: {e}")

def verify_import() -> bool:
    """验证导入"""
    print("\n🔍 验证导入结果...")

    try:
        cmd = [
            '/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql',
            '-h', 'localhost',
            '-p', '5438',
            '-d', 'memory_module',
            '-c', "SELECT COUNT(*) FROM memory_items WHERE metadata->>'source' = 'sqlite_import';"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            count = result.stdout.strip()
            print(f"✅ 验证成功: 找到 {count} 条导入的记忆")

            # 查询样本
            cmd_sample = [
                '/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql',
                '-h', 'localhost',
                '-p', '5438',
                '-d', 'memory_module',
                '-c', "SELECT content, memory_type, agent_type FROM memory_items WHERE metadata->>'source' = 'sqlite_import' LIMIT 1;"
            ]

            result_sample = subprocess.run(cmd_sample, capture_output=True, text=True)

            if result_sample.returncode == 0:
                lines = result_sample.stdout.strip().split('\n')
                if len(lines) > 2:
                    print("\n📝 记忆样本:")
                    print(lines[2] if len(lines[2]) > 0 else "无数据")

    except Exception as e:
        print(f"⚠️ 验证失败: {e}")

def main() -> None:
    """主函数"""
    print("🚀 历史记忆导入工具（直接SQL方式）")
    print("=" * 60)

    # 1. 从SQLite导出
    rows = export_from_sqlite()

    if not rows:
        print("\n⚠️ 没有找到历史记忆数据")
        return

    # 2. 生成SQL
    sql_statements = create_insert_sql(rows)

    # 3. 保存SQL文件
    save_sql_file(sql_statements)

    # 4. 执行导入
    execute_sql_file()

    # 5. 验证导入
    verify_import()

    # 6. 总结
    print("\n" + "=" * 60)
    print("🎉 历史记忆导入完成！")
    print("\n📁 生成的文件:")
    print("  - import_historical_memories.sql (SQL导入脚本)")
    print("\n📊 导入统计:")
    print(f"  - 总记忆数: {len(sql_statements)}")
    print(f"  - 目标系统: PostgreSQL(memory_module@localhost:5438)")
    print(f"  - 导入时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()