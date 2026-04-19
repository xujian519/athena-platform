#!/usr/bin/env python3
"""
查询客户王玉荣的信息
Query Customer Wang Yurong's Information
"""

import logging
import os

import psycopg2

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
print("👤 客户信息查询 - 王玉荣")
print("="*80)

# 1. 查找patents表中是否包含王玉荣
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
        CASE
            WHEN patent_name LIKE '%王玉荣%' THEN '在客户名称中'
            WHEN contact_info LIKE '%王玉荣%' THEN '在联系信息中'
            ELSE '其他'
        END as 匹配位置
    FROM patents
    WHERE
        patent_name LIKE '%王玉荣%' OR
        contact_info LIKE '%王玉荣%' OR
        agency LIKE '%王玉荣%'
    ORDER BY application_date DESC
""")

patent_results = cursor.fetchall()

if patent_results:
    print(f"{'申请号':<20} {'专利名称':<40} {'类型':<10} {'申请日':<12} {'状态':<10} {'匹配位置':<15}")
    print("-" * 130)
    for row in patent_results:
        patent_num = row[0] or "无"
        patent_name = row[1][:38] if row[1] else "无"
        patent_type = row[2] or "无"
        app_date = row[4].strftime('%Y-%m-%d') if row[4] else "无"
        status = row[5] or "无"
        match_pos = row[8]
        print(f"{patent_num:<20} {patent_name:<40} {patent_type:<10} {app_date:<12} {status:<10} {match_pos:<15}")
else:
    print("   未在专利表中找到王玉荣相关记录")

# 2. 查找patent_agents表中是否有王玉荣（作为案源人）
print("\n\n2. 👨‍💼 案源人记录查询：")
print("-" * 80)

cursor.execute("""
    SELECT
        a.client_name,
        STRING_AGG(p.contact_info, '; ') as 联系信息,
        COUNT(p.id) as 服务专利数,
        STRING_AGG(DISTINCT p.patent_name, ', ') as 服务客户示例
    FROM patent_agents a
    LEFT JOIN patents p ON a.id = p.agent_id
    WHERE a.client_name LIKE '%王玉荣%'
    GROUP BY a.id, a.client_name
""")

agent_results = cursor.fetchall()

if agent_results:
    for row in agent_results:
        print(f"案源人：{row[0]}")
        print(f"联系信息：{row[1] or '无'}")
        print(f"服务专利数：{row[2]}件")
        if row[3]:
            print(f"服务客户示例：{row[3][:100]}...")
else:
    print("   未在案源人中找到王玉荣")

# 3. 查找客户档案中是否有记录
print("\n\n3. 📁 客户档案查询：")
print("-" * 80)

# 查找可能的客户档案文件
customer_files = []
for root, _dirs, files in os.walk("/Users/xujian/Athena工作平台"):
    for file in files:
        if "王玉荣" in file or "客户档案" in file:
            if file.endswith('.json'):
                customer_files.append(os.path.join(root, file))

if customer_files:
    print(f"找到 {len(customer_files)} 个可能相关的客户档案文件：")
    for file_path in customer_files[:5]:  # 只显示前5个
        print(f"  - {os.path.basename(file_path)}")

        # 尝试读取文件内容查找王玉荣
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
                if '王玉荣' in content:
                    print("    ✅ 该文件包含王玉荣信息")
        except Exception as e:

            # 记录异常但不中断流程

            logger.debug(f"[query_customer_wang_yurong] Exception: {e}")
else:
    print("   未找到包含'王玉荣'的客户档案文件")

# 4. 模糊搜索可能的相关记录（相似姓名）
print("\n\n4. 🔍 相似姓名查询：")
print("-" * 80)

# 搜索包含"王"姓的客户
cursor.execute("""
    SELECT DISTINCT
        patent_name,
        COUNT(*) as 专利数量,
        STRING_AGG(DISTINCT legal_status, ', ') as 专利状态,
        STRING_AGG(DISTINCT a.client_name, ', ') as 案源人
    FROM patents p
    LEFT JOIN patent_agents a ON p.agent_id = a.id
    WHERE
        patent_name LIKE '%王%' AND
        patent_name NOT LIKE '%一种%' AND
        patent_name NOT LIKE '%基于%' AND
        patent_name NOT LIKE '%具有%'
        AND patent_name != ''
        AND patent_name != 'nan'
    GROUP BY patent_name
    HAVING COUNT(*) > 0
    ORDER BY 专利数量 DESC
    LIMIT 10
""")

similar_results = cursor.fetchall()

if similar_results:
    print("姓'王'的客户列表（可能相关）：")
    print(f"{'客户名称':<40} {'专利数':<6} {'专利状态':<20} {'案源人':<15}")
    print("-" * 90)
    for row in similar_results:
        customer = row[0][:38] if len(row[0]) > 38 else row[0]
        status = row[2][:18] if row[2] else "无"
        agents = row[3][:13] if row[3] else "无"
        print(f"{customer:<40} {row[1]:>6} {status:<20} {agents:<15}")
else:
    print("   未找到姓'王'的客户")

# 5. 统计查询结果
print("\n\n5. 📊 查询结果汇总：")
print("-" * 80)

total_patents = len(patent_results)
total_agents = len(agent_results)

print(f"📋 专利记录：{total_patents} 条")
print(f"👨‍💼 案源人记录：{total_agents} 条")
print(f"📁 客户档案：{len(customer_files)} 个文件")

if total_patents == 0 and total_agents == 0:
    print("\n⚠️ 未找到王玉荣的相关信息")
    print("\n💡 建议：")
    print("1. 检查姓名是否正确（可能存在同音字或别名）")
    print("2. 确认是否为近期的客户（可能尚未录入系统）")
    print("3. 尝试搜索其他可能的关键词（如公司名、联系方式等）")

    # 提供一些搜索建议
    print("\n🔍 您可以尝试搜索：")
    print("- 公司名称（如果王玉荣是某公司的联系人）")
    print("- 电话号码或其他联系方式")
    print("- 申请号或专利名称的关键词")

cursor.close()
conn.close()

print("\n" + "="*80)
print("✅ 查询完成")
print("="*80)
