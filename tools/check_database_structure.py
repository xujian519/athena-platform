#!/usr/bin/env python3
"""
检查专利档案数据库结构
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# 导入安全配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "core"))
from security.env_config import get_env_var, get_database_url, get_jwt_secret

def check_database():
    """检查数据库结构"""
    try:
        # 连接数据库
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="athena_business",
            user="postgres",
            password="xj781102"
        )

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        print("🔍 检查数据库表结构...\n")

        # 获取所有表
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        tables = [row['table_name'] for row in cursor.fetchall()]
        print(f"数据库中的表: {tables}\n")

        # 检查相关的表
        relevant_tables = ['clients', 'cases', 'patents', 'projects']

        for table in relevant_tables:
            if table in tables:
                print(f"\n📋 表 '{table}' 的结构:")
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table}'
                    ORDER BY ordinal_position
                """)

                columns = cursor.fetchall()
                for col in columns:
                    print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")

                # 查看示例数据
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"  记录数: {count}")

                if count > 0:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    samples = cursor.fetchall()
                    print("  示例数据:")
                    for sample in samples:
                        print(f"    {dict(sample)}")

        conn.close()

    except Exception as e:
        print(f"❌ 检查数据库失败: {str(e)}")

if __name__ == "__main__":
    check_database()