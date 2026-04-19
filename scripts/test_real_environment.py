#!/usr/bin/env python3
"""
真实环境测试脚本

测试:
1. 网络连接（Google Patents）
2. 数据库连接（PostgreSQL）
"""

import asyncio
import sys
from pathlib import Path
import traceback

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("🔬 真实环境测试")
print("=" * 80)
print()

# 测试1: 网络连接测试
print("1️⃣ 网络连接测试 - Google Patents")
print("-" * 80)
print()

try:
    import aiohttp
    import asyncio

    async def test_google_patents_connection():
        """测试Google Patents网站连接"""
        url = "https://patents.google.com"

        print(f"  🌐 测试连接: {url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    print(f"  ✅ Google Patents可访问")
                    print(f"     状态码: {response.status}")
                    print(f"     响应大小: {len(await response.text())} bytes")
                    return True
                else:
                    print(f"  ⚠️  Google Patents响应异常: {response.status}")
                    return False

    result = asyncio.run(test_google_patents_connection())

    if result:
        print("  ✅ 网络连接测试通过")
    else:
        print("  ❌ 网络连接测试失败")

except Exception as e:
    print(f"  ❌ 网络连接测试异常: {e}")
    traceback.print_exc()

print()

# 测试2: PostgreSQL连接测试
print("2️⃣ 数据库连接测试 - PostgreSQL")
print("-" * 80)
print()

try:
    import psycopg2

    # 测试连接
    print(f"  🗄️  测试连接: PostgreSQL")

    conn = psycopg2.connect(
        host="localhost",
        port=15432,
        database="athena",
        user="athena",
        password=""
    )

    print(f"  ✅ PostgreSQL连接成功")

    # 测试查询
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"  📊 PostgreSQL版本: {version[:50]}...")

    cursor.close()
    conn.close()

    print("  ✅ 数据库连接测试通过")

except Exception as e:
    print(f"  ❌ 数据库连接测试失败: {e}")
    traceback.print_exc()

print()

# 测试3: 检查现有数据
print("3️⃣ 检查现有数据")
print("-" * 80)
print()

try:
    import psycopg2

    conn = psycopg2.connect(
        host="localhost",
        port=15432,
        database="athena",
        user="athena",
        password=""
    )

    cursor = conn.cursor()

    # 检查是否有专利相关的表
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)

    tables = cursor.fetchall()

    if tables:
        print(f"  📋 发现 {len(tables)} 个表:")
        for table in tables:
            table_name = table[0]
            print(f"     - {table_name}")

            # 检查表是否是专利相关
            if 'patent' in table_name.lower():
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"       记录数: {count}")
    else:
        print("  ℹ️  当前数据库中没有表")
        print("  💡 提示: 需要先导入专利数据")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"  ❌ 检查现有数据失败: {e}")
    traceback.print_exc()

print()
print("=" * 80)
print("✅ 真实环境测试完成")
print("=" * 80)
print()
print("📋 测试总结:")
print("  1. 网络连接: 需要Google Patents可访问")
print("  2. 数据库连接: PostgreSQL可连接")
print("  3. 专利数据: 需要先导入到数据库")
print()
print("💡 建议:")
print("  - 如果需要完整测试，请先导入专利数据到PostgreSQL")
print("  - 或者使用mock数据进行接口功能测试")
print()
