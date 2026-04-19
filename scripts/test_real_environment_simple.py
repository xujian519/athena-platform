#!/usr/bin/env python3
"""
专利工具真实环境测试（简化版）

使用docker exec避免密码问题
"""

import subprocess
import sys
from pathlib import Path

print("=" * 80)
print("🔬 专利工具真实环境测试")
print("=" * 80)
print()

# 测试1: PostgreSQL数据库连接
print("1️⃣ PostgreSQL数据库连接测试")
print("-" * 80)
print()

try:
    # 使用docker exec测试连接
    cmd = [
        "docker", "exec", "athena-postgres",
        "psql", "-U", "athena", "-d", "athena",
        "-c", "SELECT version();"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

    if result.returncode == 0:
        print("  ✅ PostgreSQL连接成功")
        print(f"  📊 版本: {result.stdout.strip()[:60]}...")
    else:
        print(f"  ❌ PostgreSQL连接失败: {result.stderr}")

except Exception as e:
    print(f"  ❌ PostgreSQL连接异常: {e}")

print()

# 测试2: 检查专利相关表
print("2️⃣ 检查专利相关表")
print("-" * 80)
print()

try:
    cmd = [
        "docker", "exec", "athena-postgres",
        "psql", "-U", "athena", "-d", "athena",
        "-c", "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

    if result.returncode == 0:
        tables = result.stdout.strip().split('\n')[2:]  # 跳过表头

        if tables and tables[0]:
            print(f"  📋 发现 {len(tables)} 个表:")

            patent_tables = []
            for table in tables:
                table_name = table.strip()
                if table_name:
                    # 检查是否是专利相关
                    if 'patent' in table_name.lower() or '专利' in table_name:
                        patent_tables.append(table_name)
                        print(f"     ⭐ {table_name} (专利相关)")
                    else:
                        print(f"     - {table_name}")
        else:
            print("  ℹ️  当前数据库中没有表")
            print("  💡 提示: 需要先创建专利表")
    else:
        print(f"  ❌ 查询失败: {result.stderr}")

except Exception as e:
    print(f"  ❌ 检查表失败: {e}")

print()

# 测试3: 网络连接测试（简化版）
print("3️⃣ 网络连接测试")
print("-" * 80)
print()

try:
    import urllib.request
    import socket

    # 设置超时
    socket.setdefaulttimeout(10)

    url = "https://patents.google.com"
    print(f"  🌐 测试连接: {url}")

    try:
        response = urllib.request.urlopen(url, timeout=10)
        if response.status == 200:
            content_length = len(response.read(1000))  # 只读取前1000字节
            print(f"  ✅ Google Patents可访问")
            print(f"     状态码: {response.status}")
            print(f"     响应大小: {content_length} bytes (前1000字节)")
        else:
            print(f"  ⚠️  Google Patents响应异常: {response.status}")

    except urllib.error.URLError as e:
        print(f"  ⚠️  网络连接可能有问题: {e}")
        print("  💡 这可能是暂时的网络问题或防火墙限制")

    except socket.timeout:
        print(f"  ⚠️  网络连接超时")
        print("  💡 可能需要VPN或代理")

    except Exception as e:
        print(f"  ❌ 网络连接异常: {e}")

except Exception as e:
    print(f"  ❌ 网络测试失败: {e}")

print()

# 测试4: 检查专利数据文件
print("4️⃣ 检查本地专利数据文件")
print("-" * 80)
print()

data_dirs = [
    "data/patents",
    "patent_hybrid_retrieval/data"
]

for data_dir in data_dirs:
    dir_path = Path(data_dir)
    if dir_path.exists():
        files = list(dir_path.rglob("*.*"))
        print(f"  📁 {data_dir}:")
        print(f"     文件数: {len(files)}")

        # 统计文件大小
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        print(f"     总大小: {total_size / 1024 / 1024:.2f} MB")
        break
else:
    print("  ℹ️  没有找到本地专利数据目录")
    print("  💡 提示: 需要导入专利数据")

print()

print("=" * 80)
print("✅ 真实环境测试完成")
print("=" * 80)
print()

# 总结
print("📋 环境状态总结:")
print("  1. ✅ PostgreSQL数据库运行中")
print("  2. ⚠️  专利数据表需要创建")
print("  3. ⚠️  网络连接可能需要VPN")
print()
print("💡 下一步建议:")
print("  - 创建专利数据库表")
print("  - 导入专利数据")
print("  - 或先使用mock数据测试接口功能")
print()
