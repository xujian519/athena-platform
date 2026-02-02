#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询当前正在处理的客户
Check Currently Active Customers
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
print("👥 当前正在处理的客户查询")
print("="*80)

# 1. 查找2024-2025年的专利申请（最近的）
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
    AND EXTRACT(YEAR FROM application_date) IN (2024, 2025)
    GROUP BY p.patent_name
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
    print("   未找到2024-2025年的专利申请")

# 2. 查找有缴费记录的客户（表示专利仍在维护中）
print("\n2. 💰 有近期缴费记录的客户（专利维护中）：")
print("-" * 80)

cursor.execute("""
    SELECT DISTINCT
        p.patent_name as 客户名称,
        COUNT(p.id) as 专利总数,
        COUNT(pp.id) as 缴费记录数,
        SUM(pp.payment_amount) as 总缴费金额,
        MAX(pp.created_at) as 最后缴费时间,
        STRING_AGG(DISTINCT a.client_name, ', ') as 案源人
    FROM patents p
    LEFT JOIN patent_payments pp ON p.id = pp.patent_id
    LEFT JOIN patent_agents a ON p.agent_id = a.id
    WHERE p.patent_name IS NOT NULL
    AND p.patent_name != ''
    AND p.patent_name != 'nan'
    AND pp.id IS NOT NULL
    GROUP BY p.patent_name
    ORDER BY 最后缴费时间 DESC
    LIMIT 15
""")

results = cursor.fetchall()
if results:
    print(f"{'客户名称':<40} {'专利数':<6} {'缴费次':<6} {'总金额':<10} {'最后缴费':<20} {'案源人':<20}")
    print("-" * 130)
    for row in results:
        customer = row[0][:38] if len(row[0]) > 38 else row[0]
        last_payment = row[4].strftime('%Y-%m-%d %H:%M') if row[4] else "无"
        agents = row[5][:18] if row[5] else "无"
        print(f"{customer:<40} {row[1]:>6} {row[2]:>6} {row[3]:>10.2f} {last_payment:<20} {agents:<20}")
else:
    print("   未找到近期缴费记录")

# 3. 查找法律状态为"审查中"的专利
print("\n3. 🔍 审查中的专利客户（等待授权）：")
print("-" * 80)

cursor.execute("""
    SELECT
        p.patent_name as 客户名称,
        COUNT(*) as 审查中专利数,
        STRING_AGG(p.patent_number, ', ') as 申请号示例,
        STRING_AGG(DISTINCT a.client_name, ', ') as 案源人,
        MIN(application_date) as 最早申请,
        MAX(application_date) as 最新申请
    FROM patents p
    LEFT JOIN patent_agents a ON p.agent_id = a.id
    WHERE p.patent_name IS NOT NULL
    AND p.patent_name != ''
    AND p.patent_name != 'nan'
    AND p.legal_status IN ('审查中', '实审', '公开')
    GROUP BY p.patent_name
    HAVING COUNT(*) > 0
    ORDER BY 审查中专利数 DESC
    LIMIT 15
""")

results = cursor.fetchall()
if results:
    print(f"{'客户名称':<40} {'审查数':<6} {'申请号示例':<40} {'案源人':<15} {'申请期间':<20}")
    print("-" * 130)
    for row in results:
        customer = row[0][:38] if len(row[0]) > 38 else row[0]
        examples = row[2][:38] if row[2] else "无"
        agents = row[3][:13] if row[3] else "无"
        earliest = row[4].strftime('%Y-%m') if row[4] else ""
        latest = row[5].strftime('%Y-%m') if row[5] else ""
        period = f"{earliest}~{latest}" if earliest and latest else "无"
        print(f"{customer:<40} {row[1]:>6} {examples:<40} {agents:<15} {period:<20}")
else:
    print("   未找到审查中的专利")

# 4. 查找案源人近期活跃情况
print("\n4. 📊 案源人近期工作情况：")
print("-" * 80)

cursor.execute("""
    SELECT
        a.client_name as 案源人,
        COUNT(p.id) as 服务专利总数,
        COUNT(CASE WHEN EXTRACT(YEAR FROM p.application_date) = 2025 THEN 1 END) as new_2025,
        COUNT(CASE WHEN p.legal_status = '有效' THEN 1 END) as 有效专利数,
        COUNT(DISTINCT p.patent_name) as 服务客户数,
        MAX(p.application_date) as 最后服务日期
    FROM patent_agents a
    LEFT JOIN patents p ON a.id = p.agent_id
    GROUP BY a.id, a.client_name
    HAVING COUNT(p.id) > 0
    ORDER BY new_2025 DESC, 服务专利总数 DESC
    LIMIT 10
""")

results = cursor.fetchall()
if results:
    print(f"{'案源人':<15} {'总专利':<8} {'2025年':<8} {'有效':<8} {'客户数':<8} {'最后服务':<12}")
    print("-" * 70)
    for row in results:
        last_date = row[5].strftime('%Y-%m-%d') if row[5] else "无"
        print(f"{row[0]:<15} {row[1]:>8} {row[2]:>8} {row[3]:>8} {row[4]:>8} {last_date:<12}")
else:
    print("   未找到案源人工作记录")

# 5. 重点客户监控（专利数量>10的）
print("\n5. 🏆 重点客户（专利数量较多的）：")
print("-" * 80)

cursor.execute("""
    SELECT
        p.patent_name as 客户名称,
        COUNT(*) as 专利总数,
        COUNT(CASE WHEN legal_status = '有效' THEN 1 END) as 有效专利,
        COUNT(CASE WHEN legal_status = '已拿证' THEN 1 END) as 已授权,
        COUNT(CASE WHEN legal_status = '审查中' THEN 1 END) as 审查中,
        COUNT(CASE WHEN legal_status = '驳回' THEN 1 END) AS 驳回,
        STRING_AGG(DISTINCT a.client_name, ', ') as 案源人
    FROM patents p
    LEFT JOIN patent_agents a ON p.agent_id = a.id
    WHERE p.patent_name IS NOT NULL
    AND p.patent_name != ''
    AND p.patent_name != 'nan'
    GROUP BY p.patent_name
    HAVING COUNT(*) >= 10
    ORDER BY 专利总数 DESC
    LIMIT 15
""")

results = cursor.fetchall()
if results:
    print(f"{'客户名称':<40} {'总数':<6} {'有效':<6} {'授权':<6} {'审查':<6} {'驳回':<6} {'案源人':<20}")
    print("-" * 110)
    for row in results:
        customer = row[0][:38] if len(row[0]) > 38 else row[0]
        agents = row[6][:18] if row[6] else "无"
        print(f"{customer:<40} {row[1]:>6} {row[2]:>6} {row[3]:>6} {row[4]:>6} {row[5]:>6} {agents:<20}")
else:
    print("   未找到专利数量超过10的客户")

cursor.close()
conn.close()

print("\n" + "="*80)
print("✅ 查询完成！")
print("="*80)

print("\n💡 处理建议：")
print("1. 重点关注2024-2025年的新申请客户，这些是当前最活跃的客户")
print("2. 有缴费记录的客户表示专利仍在维护期，需要持续跟进")
print("3. 审查中的专利需要密切关注授权进度")
print("4. 案源人工作情况反映了当前的业务活跃程度")
print("5. 重点客户需要特别关注，保持良好的客户关系")