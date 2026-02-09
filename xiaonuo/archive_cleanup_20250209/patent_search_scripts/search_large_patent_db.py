#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索大型专利数据库 - CN221192368U
Search Large Patent Database

连接到200G大型专利数据库搜索指定专利

作者: 小娜·天秤女神
创建时间: 2025-12-17
版本: v1.0.0 "大型数据库搜索"
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import psycopg2
from psycopg2.extras import DictCursor

def search_large_patent_db():
    """在大型专利数据库中搜索"""
    print("🔍 连接200G大型专利数据库")
    print("=" * 60)

    # 大型专利数据库配置
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'patents_original',  # 这是200G的大型专利数据库
        'user': 'postgres',
        'password': 'postgres',
        'options': '-c client_encoding=UTF8'
    }

    patent_number = 'CN221192368U'

    try:
        conn = psycopg2.connect(**db_config, cursor_factory=DictCursor)
        cursor = conn.cursor()
        print("✅ 成功连接到200G专利数据库")

        # 检查数据库大小和基本信息
        cursor.execute("""
            SELECT
                pg_size_pretty(pg_database_size(current_database())) as db_size,
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size
            FROM pg_tables
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10;
        """)

        db_info = cursor.fetchall()
        print(f"\n📊 数据库信息:")
        print(f"   数据库总大小: {db_info[0]['db_size'] if db_info else 'Unknown'}")
        print(f"   主要表结构:")
        for info in db_info[:5]:
            print(f"     - {info['schemaname']}.{info['tablename']}: {info['table_size']}")

        # 首先检查所有表结构
        cursor.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND (column_name ILIKE '%patent%' OR column_name ILIKE '%number%' OR column_name ILIKE '%publication%')
            ORDER BY table_name, ordinal_position;
        """)

        columns_info = cursor.fetchall()
        print(f"\n📋 专利相关字段:")
        current_table = None
        for col in columns_info:
            if col['table_name'] != current_table:
                current_table = col['table_name']
                print(f"\n   表: {current_table}")
            print(f"     - {col['column_name']}: {col['data_type']}")

        # 查看所有表
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        print(f"\n📋 数据库中的所有表:")
        for table in tables:
            print(f"   - {table['table_name']}")

        # 尝试多种搜索策略
        search_strategies = [
            # 策略1: 直接匹配公开号
            {
                'name': '直接匹配公开号',
                'sql': f"SELECT * FROM patents WHERE publication_number = '{patent_number}' LIMIT 1;"
            },
            # 策略2: 模糊匹配
            {
                'name': '模糊匹配公开号',
                'sql': f"SELECT * FROM patents WHERE publication_number LIKE '%221192368%' LIMIT 5;"
            },
            # 策略3: 查找包含专利号的所有记录
            {
                'name': '包含专利号片段',
                'sql': f"SELECT * FROM patents WHERE publication_number LIKE '%221192368%' OR application_number LIKE '%221192368%' LIMIT 10;"
            }
        ]

        print(f"\n🔍 开始搜索专利: {patent_number}")

        found_patent = None

        for strategy in search_strategies:
            print(f"\n📝 策略: {strategy['name']}")
            try:
                cursor.execute(strategy['sql'])
                results = cursor.fetchall()

                if results:
                    print(f"✅ 找到 {len(results)} 条记录!")

                    for i, result in enumerate(results[:3], 1):  # 只显示前3条
                        print(f"\n📄 专利记录 [{i}]:")

                        # 显示所有字段
                        for key, value in result.items():
                            if value is not None:
                                if key in ['abstract', 'claims', 'description']:
                                    # 长文本字段截断显示
                                    print(f"   {key}: {str(value)[:150]}...")
                                else:
                                    print(f"   {key}: {value}")
                            else:
                                print(f"   {key}: NULL")

                        if i == 1:  # 保存第一条作为主要结果
                            found_patent = result

                        # 检查是否包含苏东霞
                        if result.get('inventor') and '苏东霞' in str(result['inventor']):
                            print(f"   🎯 找到苏东霞相关的专利!")
                        elif result.get('applicant') and '苏东霞' in str(result['applicant']):
                            print(f"   🎯 申请人是苏东霞!")

                else:
                    print(f"❌ 未找到记录")

            except Exception as e:
                print(f"⚠️ 搜索出错: {e}")

        # 如果还没找到，尝试查看其他可能的表
        if not found_patent:
            print(f"\n🔍 尝试在其他表中搜索...")

            # 查找可能包含专利信息的其他表
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND (table_name ILIKE '%patent%' OR table_name ILIKE '%application%' OR table_name ILIKE '%publication%')
                ORDER BY table_name;
            """)

            patent_tables = cursor.fetchall()

            for table_info in patent_tables:
                table_name = table_info['table_name']
                print(f"\n📋 搜索表: {table_name}")

                try:
                    # 获取表结构
                    cursor.execute(f"""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = '{table_name}'
                        AND table_schema = 'public'
                        ORDER BY ordinal_position;
                    """)
                    columns = [col[0] for col in cursor.fetchall()]

                    # 尝试在有相关字段的表中搜索
                    if any('number' in col.lower() or 'patent' in col.lower() for col in columns):
                        # 构建搜索SQL
                        search_conditions = []
                        for col in columns:
                            if 'number' in col.lower():
                                search_conditions.append(f"{col} LIKE '%221192368%'")

                        if search_conditions:
                            sql = f"SELECT * FROM {table_name} WHERE {' OR '.join(search_conditions)} LIMIT 3;"
                            cursor.execute(sql)
                            results = cursor.fetchall()

                            if results:
                                print(f"✅ 在表 {table_name} 中找到 {len(results)} 条记录!")
                                for result in results:
                                    print(f"   记录: {dict(result)}")

                except Exception as e:
                    print(f"   ⚠️ 搜索表 {table_name} 出错: {e}")

        # 最终结果报告
        print(f"\n📊 搜索结果总结:")
        print(f"   🔍 搜索专利号: {patent_number}")
        print(f"   🗄️ 数据库: patents_original (200G)")

        if found_patent:
            print(f"   ✅ 搜索成功!")
            print(f"   📄 专利标题: {found_patent.get('title', found_patent.get('patent_name', 'Unknown'))}")
            print(f"   🏢 申请人: {found_patent.get('applicant', 'Unknown')}")
            print(f"   👤 发明人: {found_patent.get('inventor', 'Unknown')}")

            # 分析是否与苏东霞相关
            inventor = found_patent.get('inventor', '')
            applicant = found_patent.get('applicant', '')

            if '苏东霞' in str(inventor):
                print(f"   🎯 发明人确实是苏东霞!")
            elif '苏东霞' in str(applicant):
                print(f"   🎯 申请人是苏东霞!")
            else:
                print(f"   ⚠️ 未发现与苏东霞的直接关联")
        else:
            print(f"   ❌ 在200G数据库中未找到该专利")
            print(f"   💡 可能原因:")
            print(f"      1. 该专利可能不在此数据库中")
            print(f"      2. 专利号格式可能不同")
            print(f"      3. 数据可能存储在不同的表中")

        conn.close()

    except Exception as e:
        print(f"❌ 连接或搜索失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    search_large_patent_db()