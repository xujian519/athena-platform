#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询当前正在处理的实际客户（申请人）
Check Currently Active Real Customers (Applicants)
"""

import psycopg2
import os
from datetime import datetime, timedelta

# PostgreSQL配置
db_config = {
    "host": "localhost",
    "port": 5432,
    "database": "patent_archive",
    "user": "xujian",
    "password": ""
}

# 检查PostgreSQL路径
postgres_path = "/opt/homebrew/opt/postgresql@17/bin"
if postgres_path not in os.environ.get("PATH", ""):
    os.environ["PATH"] = postgres_path + ":" + os.environ.get("PATH", "")

conn = psycopg2.connect(**db_config)
cursor = conn.cursor()

print("="*80)
print("👥 当前正在处理的客户（申请人）查询")
print("="*80)

# 1. 查找2024-2025年的专利申请对应的客户（申请人）
print("\n1. 📅 2024-2025年申请专利的客户（近期活跃）：")
print("-" * 80)

cursor.execute("""
    SELECT
        p.patent_name as 客户名称,
        COUNT(*) as 专利数量,
        COUNT(CASE WHEN legal_status = '有效' THEN 1 END) as 有效专利,
        COUNT(CASE WHEN legal_status = '已拿证' THEN 1 END) as 已授权,
        COUNT(CASE WHEN legal_status IN ('审查中', '实审') THEN 1 END) as 审查中,
        STRING_AGG(DISTINCT a.client_name, ', ') as 案源人,
        MAX(application_date) as 最新申请日期
    FROM patents p
    LEFT JOIN patent_agents a ON p.agent_id = a.id
    WHERE p.patent_name IS NOT NULL
    AND p.patent_name != ''
    AND p.patent_name != 'nan'
    AND p.patent_name NOT LIKE '一种%'
    AND p.patent_name NOT LIKE '基于%'
    AND p.patent_name NOT LIKE '%（%'
    AND EXTRACT(YEAR FROM application_date) IN (2024, 2025)
    GROUP BY p.patent_name
    HAVING COUNT(*) >= 1
    ORDER BY 专利数量 DESC, 最新申请日期 DESC
    LIMIT 20
""")

results = cursor.fetchall()
if results:
    print(f"{'客户名称':<40} {'专利数':<6} {'有效':<6} {'授权':<6} {'审查中':<8} {'案源人':<20} {'最新申请':<12}")
    print("-" * 130)
    for row in results:
        customer = row[0][:38] if len(row[0]) > 38 else row[0]
        agents = row[5][:18] if row[5] else "无"
        latest_date = row[6].strftime('%Y-%m-%d') if row[6] else "无"
        print(f"{customer:<40} {row[1]:>6} {row[2]:>6} {row[3]:>6} {row[4]:>8} {agents:<20} {latest_date:<12}")
else:
    print("   未找到符合条件的企业客户")

# 2. 查找真正的企业客户（包含公司、学院、研究所等关键词）
print("\n2. 🏢 企业及机构客户（专利数排序）：")
print("-" * 80)

cursor.execute("""
    SELECT
        p.patent_name as 客户名称,
        COUNT(*) as 专利总数,
        COUNT(CASE WHEN legal_status = '有效' THEN 1 END) as 有效专利,
        COUNT(CASE WHEN legal_status = '已拿证' THEN 1 END) as 已授权,
        COUNT(CASE WHEN p.agent_id IS NOT NULL THEN 1 END) as 有案源人,
        STRING_AGG(DISTINCT a.client_name, ', ') as 案源人,
        MIN(EXTRACT(YEAR FROM application_date)) as 最早年份,
        MAX(EXTRACT(YEAR FROM application_date)) as 最新年份
    FROM patents p
    LEFT JOIN patent_agents a ON p.agent_id = a.id
    WHERE p.patent_name IS NOT NULL
    AND p.patent_name != ''
    AND p.patent_name != 'nan'
    AND (
        p.patent_name LIKE '%公司%' OR
        p.patent_name LIKE '%学院%' OR
        p.patent_name LIKE '%大学%' OR
        p.patent_name LIKE '%研究所%' OR
        p.patent_name LIKE '%研究院%' OR
        p.patent_name LIKE '%医院%' OR
        p.patent_name LIKE '%中心%' OR
        p.patent_name LIKE '%集团%' OR
        p.patent_name LIKE '%企业%' OR
        p.patent_name LIKE '%学校%' OR
        p.patent_name LIKE '%有限%'
    )
    GROUP BY p.patent_name
    HAVING COUNT(*) > 0
    ORDER BY 专利总数 DESC
    LIMIT 25
""")

results = cursor.fetchall()
if results:
    print(f"{'客户名称':<40} {'专利数':<6} {'有效':<6} {'授权':<6} {'有案源':<6} {'案源人':<20} {'申请年份':<12}")
    print("-" * 130)
    for row in results:
        customer = row[0][:38] if len(row[0]) > 38 else row[0]
        agents = row[5][:18] if row[5] else "无"
        years = f"{int(row[6])}~{int(row[7])}" if row[6] and row[7] else "无"
        print(f"{customer:<40} {row[1]:>6} {row[2]:>6} {row[3]:>6} {row[4]:>6} {agents:<20} {years:<12}")
else:
    print("   未找到企业客户")

# 3. 查找2024-2025年的专利但尚未授权的客户
print("\n3. ⏳ 2024-2025年申请但尚未授权的客户：")
print("-" * 80)

cursor.execute("""
    SELECT
        p.patent_name as 客户名称,
        COUNT(*) as 申请专利数,
        STRING_AGG(p.patent_number, ', ') as 申请号示例,
        STRING_AGG(DISTINCT p.patent_type, ', ') as 专利类型,
        STRING_AGG(DISTINCT a.client_name, ', ') as 案源人
    FROM patents p
    LEFT JOIN patent_agents a ON p.agent_id = a.id
    WHERE p.patent_name IS NOT NULL
    AND p.patent_name != ''
    AND p.patent_name != 'nan'
    AND p.patent_name NOT LIKE '一种%'
    AND EXTRACT(YEAR FROM application_date) IN (2024, 2025)
    AND p.legal_status NOT IN ('已拿证', '有效')
    GROUP BY p.patent_name
    HAVING COUNT(*) > 0
    ORDER BY 申请专利数 DESC
    LIMIT 15
""")

results = cursor.fetchall()
if results:
    print(f"{'客户名称':<40} {'申请数':<6} {'申请号示例':<40} {'专利类型':<15} {'案源人':<20}")
    print("-" * 120)
    for row in results:
        customer = row[0][:38] if len(row[0]) > 38 else row[0]
        examples = (row[2][:37] + '...') if len(row[2]) > 40 else row[2]
        types = row[3][:13] if row[3] else "无"
        agents = row[4][:18] if row[4] else "无"
        print(f"{customer:<40} {row[1]:>6} {examples:<40} {types:<15} {agents:<20}")
else:
    print("   未找到符合条件的待授权客户")

# 4. 统计各类型客户分布
print("\n4. 📊 客户类型分布统计：")
print("-" * 80)

# 企业客户
cursor.execute("""
    SELECT COUNT(DISTINCT patent_name) as count FROM patents
    WHERE patent_name LIKE '%公司%' OR patent_name LIKE '%集团%' OR patent_name LIKE '%企业%'
    OR patent_name LIKE '%有限%'
""")
company_count = cursor.fetchone()[0]

# 学校客户
cursor.execute("""
    SELECT COUNT(DISTINCT patent_name) as count FROM patents
    WHERE patent_name LIKE '%大学%' OR patent_name LIKE '%学院%' OR patent_name LIKE '%学校%'
""")
school_count = cursor.fetchone()[0]

# 研究机构
cursor.execute("""
    SELECT COUNT(DISTINCT patent_name) as count FROM patents
    WHERE patent_name LIKE '%研究所%' OR patent_name LIKE '%研究院%'
""")
research_count = cursor.fetchone()[0]

# 医院
cursor.execute("""
    SELECT COUNT(DISTINCT patent_name) as count FROM patents
    WHERE patent_name LIKE '%医院%'
""")
hospital_count = cursor.fetchone()[0]

print(f"   🏢 企业类客户: {company_count} 个")
print(f"   🎓 学校类客户: {school_count} 个")
print(f"   🔬 研究机构: {research_count} 个")
print(f"   🏥 医疗机构: {hospital_count} 个")

# 5. 查找有缴费记录的实际客户
print("\n5. 💰 有近期缴费记录的客户：")
print("-" * 80)

cursor.execute("""
    SELECT DISTINCT
        p.patent_name as 客户名称,
        COUNT(p.id) as 专利总数,
        COUNT(pp.id) as 缴费记录数,
        SUM(pp.payment_amount) as 总缴费金额,
        MAX(pp.created_at) as 最后缴费时间
    FROM patents p
    LEFT JOIN patent_payments pp ON p.id = pp.patent_id
    WHERE p.patent_name IS NOT NULL
    AND p.patent_name != ''
    AND p.patent_name != 'nan'
    AND p.patent_name NOT LIKE '一种%'
    AND pp.id IS NOT NULL
    GROUP BY p.patent_name
    ORDER BY 总缴费金额 DESC
    LIMIT 10
""")

results = cursor.fetchall()
if results:
    print(f"{'客户名称':<40} {'专利数':<6} {'缴费次':<6} {'总金额':<10} {'最后缴费':<20}")
    print("-" * 90)
    for row in results:
        customer = row[0][:38] if len(row[0]) > 38 else row[0]
        last_payment = row[4].strftime('%Y-%m-%d %H:%M') if row[4] else "无"
        print(f"{customer:<40} {row[1]:>6} {row[2]:>6} {row[3]:>10.2f} {last_payment:<20}")
else:
    print("   未找到企业客户的缴费记录")

cursor.close()
conn.close()

print("\n" + "="*80)
print("✅ 查询完成！")
print("="*80)

print("\n💡 处理建议：")
print("1. 重点维护专利数量多的企业客户关系")
print("2. 关注2024-2025年新申请的客户，提供及时的进度反馈")
print("3. 对有缴费记录的客户要继续做好年费提醒服务")
print("4. 未授权的客户需要密切关注审查进度")
print("5. 不同类型客户（企业/学校/研究机构）的服务策略应有所区别")