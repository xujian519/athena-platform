#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出客户信息简化版
Export Customer Information - Simple Version
"""

import psycopg2
import json
import os

def export_customers():
    """导出所有客户信息"""
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

    # 查询所有客户（申请人）信息
    cursor.execute("""
        SELECT
            p.patent_name as 客户名称,
            p.contact_info as 联系信息,
            p.agency as 代理机构,
            a.client_name as 案源人,
            COUNT(*) as 专利数量,
            STRING_AGG(p.patent_number, ', ') as 申请号示例
        FROM patents p
        LEFT JOIN patent_agents a ON p.agent_id = a.id
        WHERE p.patent_name IS NOT NULL
        AND p.patent_name != ''
        AND p.patent_name != 'nan'
        GROUP BY p.patent_name, p.contact_info, p.agency, a.client_name
        ORDER BY 专利数量 DESC
    """)

    customers = cursor.fetchall()

    # 提取有联系信息的客户
    contact_customers = []
    for customer in customers:
        name = customer[0]
        contact = customer[1] or ""
        agency = customer[2] or ""
        agent = customer[3] or ""
        count = customer[4]
        examples = customer[5] or ""

        # 基本解析联系信息
        contact_data = {
            "客户名称": name,
            "联系信息": contact,
            "代理机构": agency,
            "案源人": agent,
            "专利数量": count,
            "申请号示例": examples
        }

        contact_customers.append(contact_data)

    # 保存到JSON
    with open("customers_extracted.json", "w", encoding="utf-8") as f:
        json.dump({
            "客户总数": len(contact_customers),
            "客户列表": contact_customers,
            "说明": "patent_name字段存储的是申请人（客户）名称"
        }, f, ensure_ascii=False, indent=2)

    # 保存到CSV
    with open("customers_extracted.csv", "w", encoding="utf-8") as f:
        f.write("客户名称,联系信息,代理机构,案源人,专利数量\n")
        for customer in contact_customers:
            f.write(f'"{customer["客户名称"]}","{customer["联系信息"]}","{customer["代理机构"]}",'
                  f'"{customer["案源人"]}",{customer["专利数量"]}\n')

    print(f"✅ 已导出 {len(contact_customers)} 个客户信息")
    print("- customers_extracted.json")
    print("- customers_extracted.csv")

    # 显示有电话号码的客户
    print("\n📞 有电话号码的客户示例：")
    print("-" * 80)
    phone_count = 0
    for i, customer in enumerate(contact_customers[:20]):
        if any(char.isdigit() for char in customer["联系信息"]):
            print(f"{i+1:2d}. {customer['客户名称']}")
            print(f"   联系信息: {customer['联系信息']}")
            print(f"   案源人: {customer['案源人']}")
            phone_count += 1

    print(f"\n统计：找到 {phone_count} 个客户有联系信息")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    export_customers()