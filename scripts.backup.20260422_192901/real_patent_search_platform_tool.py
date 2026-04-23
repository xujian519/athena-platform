#!/usr/bin/env python3
"""
使用平台专利检索工具进行真实专利检索
检查本地patents表并检索相关专利
"""

import sys

sys.path.insert(0, "/Users/xujian/Athena工作平台")


import psycopg2

print("=" * 70)
print("🔍 使用平台专利检索工具 - 真实专利检索")
print("=" * 70)
print()

# 检查所有数据库中的patent相关表
print("📋 第一步: 检查本地数据库中的patent表")
print("-" * 70)

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="postgres",
    user="postgres",
    password="postgres",
    connect_timeout=10
)
conn.autocommit = True
cursor = conn.cursor()

# 检查所有表
cursor.execute("""
    SELECT table_name, table_schema
    FROM information_schema.tables
    WHERE table_name LIKE '%patent%'
    AND table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_name
""")

patent_tables = cursor.fetchall()

if patent_tables:
    print(f"找到 {len(patent_tables)} 个patent相关表:")
    for table in patent_tables:
        print(f"  • {table[1]}.{table[0]}")
else:
    print("未找到patent相关表")

print()

# 检查是否有patents表（平台专利检索工具使用的表）
has_patents_table = False
patents_schema = None

for table in patent_tables:
    if table[0] == "patents":
        has_patents_table = True
        patents_schema = table[1]
        break

if has_patents_table:
    print(f"✅ 找到patents表: {patents_schema}.patents")
    print()

    # 检查patents表结构
    print("📋 patents表结构:")
    print("-" * 70)

    cursor.execute(f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'patents'
        AND table_schema = '{patents_schema}'
        ORDER BY ordinal_position
    """)

    columns = cursor.fetchall()

    if columns:
        print("字段列表:")
        for col in columns:
            print(f"  • {col[0]}: {col[1]}")

    # 检查patents表中的记录数
    cursor.execute(f'SELECT COUNT(*) FROM "{patents_schema}".patents')
    count = cursor.fetchone()[0]
    print(f"\n总记录数: {count:,}")
    print()

    # 如果有数据，进行真实检索
    if count > 0:
        print("=" * 70)
        print("🔍 第二步: 真实专利检索")
        print("=" * 70)
        print()

        # 搜索关键词
        keywords = ["幼苗", "育苗", "保护罩", "植物保护", "农业"]

        for keyword in keywords:
            print(f"🔎 搜索关键词: {keyword}")
            print("-" * 70)

            cursor.execute(f"""
                SELECT
                    id,
                    patent_name,
                    abstract,
                    applicant,
                    ipc_main_class,
                    application_number,
                    application_date
                FROM "{patents_schema}".patents
                WHERE patent_name ILIKE %s
                   OR abstract ILIKE %s
                ORDER BY application_date DESC
                LIMIT 5
            """, (f'%{keyword}%', f'%{keyword}%'))

            results = cursor.fetchall()

            if results:
                print(f"✅ 找到 {len(results)} 条结果:")
                for r in results:
                    print(f"\n  📄 {r[1] or '未命名'}")
                    if r[5]:
                        print(f"     申请号: {r[5]}")
                    if r[3]:
                        print(f"     申请人: {r[3]}")
                    if r[4]:
                        print(f"     IPC分类: {r[4]}")
                    if r[2]:
                        abstract = r[2][:100] + '...' if len(r[2]) > 100 else r[2]
                        print(f"     摘要: {abstract}")
            else:
                print("  未找到匹配结果")
            print()

    else:
        print("⚠️ patents表为空，无法进行检索")

else:
    print("⚠️ 未找到patents表")
    print()
    print("说明: 平台的patents表可能不存在于postgres数据库中")
    print("     需要检查是否有独立的patent_db数据库")

# 检查是否有独立的patent_db数据库
print()
print("=" * 70)
print("📋 第三步: 检查是否有独立的patent_db数据库")
print("=" * 70)
print()

cursor.execute("""
    SELECT datname FROM pg_database
    WHERE datname LIKE '%patent%'
    ORDER BY datname
""")

patent_databases = cursor.fetchall()

if patent_databases:
    print(f"找到 {len(patent_databases)} 个patent相关数据库:")
    for db in patent_databases:
        print(f"  • {db[0]}")

    # 尝试连接patent_db数据库
    for db_info in patent_databases:
        db_name = db_info[0]
        print()
        print(f"尝试连接数据库: {db_name}")
        print("-" * 70)

        try:
            patent_conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database=db_name,
                user="postgres",
                password="postgres",
                connect_timeout=5
            )

            patent_cursor = patent_conn.cursor()

            # 检查表
            patent_cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                LIMIT 20
            """)

            tables = [t[0] for t in patent_cursor.fetchall()]

            if tables:
                print(f"表列表: {', '.join(tables[:10])}")

                # 如果有patents表，查询数据
                if 'patents' in tables:
                    patent_cursor.execute('SELECT COUNT(*) FROM patents')
                    patent_count = patent_cursor.fetchone()[0]
                    print(f"patents表记录数: {patent_count:,}")

                    if patent_count > 0:
                        print()
                        print("检索'幼苗'相关专利:")

                        patent_cursor.execute("""
                            SELECT
                                patent_name,
                                application_number,
                                abstract
                            FROM patents
                            WHERE patent_name ILIKE %s
                            LIMIT 3
                        """, ('%幼苗%',))

                        results = patent_cursor.fetchall()
                        for r in results:
                            print(f"  • {r[0] or '未命名'} ({r[1] or 'N/A'})")

            patent_cursor.close()
            patent_conn.close()

        except Exception as e:
            print(f"连接失败: {e}")

else:
    print("未找到独立的patent数据库")

print()

# 总结
print("=" * 70)
print("📊 检索结果总结")
print("=" * 70)
print()

print("本地数据库状态:")
print(f"  • patent相关表: {len(patent_tables)} 个")
print(f"  • patent相关数据库: {len(patent_databases)} 个")
print(f"  • patents表存在: {'是' if has_patents_table else '否'}")
print()

if not has_patents_table and len(patent_databases) == 0:
    print("⚠️ 结论:")
    print("  本地数据库中没有完整的专利文献数据")
    print("  建议使用以下平台进行真实专利检索:")
    print()
    print("  1. 中国专利公布公告网")
    print("     https://pss-system.cponline.cnipa.gov.cn/")
    print()
    print("  2. 国家知识产权局")
    print("     https://www.cnipa.gov.cn/")
    print()
    print("  3. Google Patents")
    print("     https://patents.google.com/")
    print()
    print("推荐检索策略:")
    print("  • IPC分类: A01G 9/00, A01G 13/00, A01G 9/14")
    print("  • 关键词: 幼苗保护罩、育苗装置、植物防护")
    print("  • 专利类型: 实用新型")

cursor.close()
conn.close()
