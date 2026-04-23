#!/usr/bin/env python3
"""
PostgreSQL数据库检查脚本
检查所有数据库并找出数据量大于8G的数据库
"""


import psycopg2

# 连接PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="postgres",
    user="postgres",
    password="postgres",
    connect_timeout=5
)

cursor = conn.cursor()

# 查询所有数据库
print("=" * 70)
print("📊 PostgreSQL数据库列表")
print("=" * 70)
print()

cursor.execute("""
    SELECT
        datname as database_name,
        pg_database_size(datname) as size_bytes,
        pg_size_pretty(pg_database_size(datname)) as size_pretty
    FROM pg_database
    WHERE datistemplate = false
    ORDER BY pg_database_size(datname) DESC
""")

databases = cursor.fetchall()

print(f"{'数据库名':<30} {'数据量':<15} {'大小(字节)':<15}")
print("-" * 70)

for db_name, size_bytes, size_pretty in databases:
    print(f"{db_name:<30} {size_pretty:<15} {size_bytes:15,}")

    # 标记大于8GB的数据库
    if size_bytes > 8 * 1024 * 1024 * 1024:
        print("  ⭐ 大于8GB!")

print()
print("=" * 70)
print("🔍 检查每个数据库的表数量")
print("=" * 70)
print()

for db_name, _, _ in databases[:5]:  # 只检查前5个
    try:
        # 切换到该数据库
        conn.autocommit = True
        cursor.execute(f'SET search_path TO "{db_name}"')

        # 查询表数量
        cursor.execute("""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        """)
        table_count = cursor.fetchone()[0]

        print(f"{db_name}: {table_count} 个表")

    except Exception as e:
        print(f"{db_name}: 无法访问 - {e}")

print()
print("=" * 70)
print("🔍 检查postgres数据库的详细信息")
print("=" * 70)
print()

# 检查postgres数据库的表
cursor.execute('SET search_path TO "postgres"')
cursor.execute("""
    SELECT
        schemaname,
        tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size
    FROM pg_tables
    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    LIMIT 20
""")

tables = cursor.fetchall()

print(f"{'Schema':<20} {'表名':<40} {'大小':<15}")
print("-" * 70)

for schema, table, size in tables:
    print(f"{schema:<20} {table:<40} {size:<15}")

cursor.close()
conn.close()
