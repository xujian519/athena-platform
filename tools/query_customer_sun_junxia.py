#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询客户孙俊霞的信息
Query Customer Sun Junxia's Information
"""

import psycopg2
import os
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


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
print("👤 客户信息查询 - 孙俊霞")
print("="*80)

# 1. 查找patents表中是否包含孙俊霞
print("\n1. 📋 专利记录查询：")
print("-" * 80)

cursor.execute("""
    SELECT
        patent_number,
        patent_name,
        patent_type,
        application_date,
        legal_status,
        contact_info,
        agency,
        archive_location,
        a.client_name as 案源人
    FROM patents p
    LEFT JOIN patent_agents a ON p.agent_id = a.id
    WHERE
        patent_name LIKE '%孙俊霞%' OR
        contact_info LIKE '%孙俊霞%' OR
        agency LIKE '%孙俊霞%'
    ORDER BY application_date DESC
""")

patent_results = cursor.fetchall()

if patent_results:
    print(f"{'申请号':<20} {'专利名称':<40} {'类型':<10} {'申请日':<12} {'状态':<10} {'案源人':<15}")
    print("-" * 130)
    for row in patent_results:
        patent_num = row[0] or "无"
        patent_name = row[1][:38] if row[1] else "无"
        patent_type = row[2] or "无"
        app_date = row[4].strftime('%Y-%m-%d') if row[4] else "无"
        status = row[5] or "无"
        agent = row[8] or "无"
        print(f"{patent_num:<20} {patent_name:<40} {patent_type:<10} {app_date:<12} {status:<10} {agent:<15}")
else:
    print("   未在专利表中找到孙俊霞相关记录")

# 2. 查找缴费记录
print("\n\n2. 💰 缴费记录查询：")
print("-" * 80)

cursor.execute("""
    SELECT DISTINCT
        p.patent_name,
        pp.payment_amount,
        pp.payment_date,
        pp.payment_type,
        pp.source_file
    FROM patent_payments pp
    JOIN patents p ON pp.patent_id = p.id
    WHERE p.patent_name LIKE '%孙俊霞%'
    ORDER BY pp.payment_date DESC
""")

payment_results = cursor.fetchall()

if payment_results:
    print(f"{'客户名称':<30} {'缴费金额':<10} {'缴费日期':<12} {'缴费类型':<15}")
    print("-" * 80)
    for row in payment_results:
        name = row[0][:28] if row[0] else "无"
        amount = f"¥{row[1]:.2f}" if row[1] else "无"
        pay_date = row[2].strftime('%Y-%m-%d') if row[2] else "无"
        pay_type = row[3] or "无"
        print(f"{name:<30} {amount:<10} {pay_date:<12} {pay_type:<15}")
else:
    print("   未找到孙俊霞的缴费记录")

# 3. 查找客户档案
print("\n\n3. 📁 客户档案查询：")
print("-" * 80)

# 查找可能的客户档案文件
customer_files = []
for root, dirs, files in os.walk("/Users/xujian/Athena工作平台"):
    for file in files:
        if "孙俊霞" in file:
            if file.endswith('.json'):
                customer_files.append(os.path.join(root, file))

if customer_files:
    print(f"找到 {len(customer_files)} 个客户档案文件：")
    for file_path in customer_files:
        print(f"\n📄 文件：{os.path.basename(file_path)}")

        # 尝试读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # 查找关键信息
                if isinstance(data, dict):
                    if 'customer_info' in data:
                        info = data['customer_info']
                        print(f"   客户姓名：{info.get('customer_name', '未知')}")
                        print(f"   联系电话：{info.get('contact_phone', '未知')}")
                        print(f"   地 址：{info.get('address', '未知')}")

                    if 'batch_info' in data:
                        batch = data['batch_info']
                        print(f"   专利类型：{batch.get('batch_type', '未知')}")
                        print(f"   专利数量：{batch.get('total_patents', 0)}件")
                        print(f"   缴费状态：{batch.get('payment_status', '未知')}")
                        print(f"   总费用：¥{batch.get('total_fee', 0)}")

                    if 'patent_cases' in data:
                        cases = data['patent_cases']
                        print(f"\n   专利名称：")
                        for i, case in enumerate(cases, 1):
                            title = case.get('title', '未知')
                            status = case.get('application_status', {}).get('current_stage', '未知')
                            print(f"   {i}. {title}")
                            print(f"      状态：{status}")

                            # 查看是否已确定名称
                            if 'title' in case and case['title'] != 'TBD':
                                print(f"      ✅ 专利名称已确定")
                            else:
                                print(f"      ⚠️ 专利名称待确定")

        except Exception as e:
            print(f"   ❌ 读取文件失败：{str(e)}")
else:
    print("   未找到孙俊霞的客户档案文件")

# 4. 查找任务列表
print("\n\n4. 📋 任务列表查询：")
print("-" * 80)

# 读取任务列表
task_files = [
    "/Users/xujian/Athena工作平台/data/tasks/tasks.json",
    "/Users/xujian/Athena工作平台/data/tasks/task_孙俊霞*.json"
]

found_tasks = []
for pattern in task_files:
    if '*' in pattern:
        from glob import glob
        files = glob(pattern)
        found_tasks.extend(files)
    else:
        if os.path.exists(pattern):
            found_tasks.append(pattern)

for task_file in found_tasks[:5]:  # 只查看前5个
    try:
        with open(task_file, 'r', encoding='utf-8') as f:
            tasks = json.load(f)

            # 检查是否包含孙俊霞的任务
            if isinstance(tasks, dict):
                for task_id, task in tasks.items():
                    title = task.get('title', '') or task.get('description', '')
                    if '孙俊霞' in title:
                        print(f"\n📝 任务ID：{task_id}")
                        print(f"   任务标题：{title}")
                        print(f"   状态：{task.get('status', '未知')}")
                        print(f"   优先级：{task.get('priority', '未知')}")
                        if task.get('due_at'):
                            print(f"   截止时间：{task['due_at'][:10]}")

                        # 查看任务详情
                        tags = task.get('tags', [])
                        if tags:
                            print(f"   标签：{', '.join(tags)}")
    except Exception as e:

        # 记录异常但不中断流程

        logger.debug(f"[query_customer_sun_junxia] Exception: {e}")
# 5. 统计查询结果
print("\n\n5. 📊 查询结果汇总：")
print("-" * 80)

print(f"📋 专利记录：{len(patent_results)} 条")
print(f"💰 缴费记录：{len(payment_results)} 条")
print(f"📁 客户档案：{len(customer_files)} 个文件")

if len(patent_results) == 0 and len(customer_files) == 0:
    print("\n⚠️ 未在系统中找到孙俊霞的相关信息")
    print("\n💡 建议：")
    print("1. 检查姓名是否正确（可能是孙俊霞、孙俊侠等）")
    print("2. 确认是否为近期新增客户")
    print("3. 检查是否在其他系统中记录")
else:
    print("\n✅ 找到孙俊霞的相关记录")

cursor.close()
conn.close()

print("\n" + "="*80)
print("✅ 查询完成")
print("="*80)