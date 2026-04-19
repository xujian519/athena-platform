#!/usr/bin/env python3
"""
测试专利申请号格式转换
Test Patent Number Format Conversion
"""

import os

import psycopg2

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

def convert_patent_number_format(payment_number):
    """转换缴费表格中的申请号格式到数据库格式"""
    print(f"\n原始号码: {payment_number}")

    # 缴费表格式：YYYY(4) + 类型码(1) + 序号(7) + 校验码(1) = 13位
    # 数据库格式：YYYY(4) + 序号(7) + 校验码(1) = 12位（可能包含小数点）

    if len(payment_number) == 13:
        # 提取各部分
        year = payment_number[:4]
        type_code = payment_number[4:5]
        serial = payment_number[5:12]
        check = payment_number[12:13]

        print(f"  年份: {year}")
        print(f"  类型码: {type_code}")
        print(f"  序号: {serial}")
        print(f"  校验码: {check}")

        # 数据库中的格式：年份 + 序号 + 校验码
        db_format1 = f"{year}{serial}.{check}"
        db_format2 = f"{year}{serial}{check}"
        db_format3 = f"{year}{serial[:6]}.{check}"  # 有时序号少一位

        print("\n尝试的格式:")
        print(f"  1. {db_format1}")
        print(f"  2. {db_format2}")
        print(f"  3. {db_format3}")

        # 检查这些格式是否存在
        for i, fmt in enumerate([db_format1, db_format2, db_format3], 1):
            cursor.execute("""
                SELECT patent_number, patent_name
                FROM patents
                WHERE patent_number = %s
            """, (fmt,))

            result = cursor.fetchone()
            if result:
                print(f"  ✅ 格式{i}匹配: {result[0]} - {result[1][:50]}...")
                return fmt
            else:
                print(f"  ❌ 格式{i}未匹配")

    return None

# 测试几个典型的缴费申请号
test_numbers = [
    "2025226088686",  # 实用新型
    "2025230055081",  # 发明
    "2022330145163",  # 外观设计
]

print("="*80)
print("🔧 测试专利申请号格式转换")
print("="*80)

for num in test_numbers:
    convert_patent_number_format(num)

# 查看数据库中实际的格式样本
print("\n\n数据库中的申请号样本:")
cursor.execute(r"""
    SELECT patent_number, patent_name
    FROM patents
    WHERE patent_number IS NOT NULL
    AND patent_number NOT LIKE '%:%'
    AND patent_number ~ '^\d{10,13}(\.\d)?$'
    ORDER BY patent_number DESC
    LIMIT 10
""")

results = cursor.fetchall()
for r in results:
    print(f"  {r[0]} - {r[1][:50]}...")

cursor.close()
conn.close()
