#!/usr/bin/env python3
"""
快速测试脚本 - 验证修复后的功能
"""

from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "phase2"))

print("=" * 70)
print("快速功能验证测试")
print("=" * 70)

# 测试1: Qdrant连接和集合创建
print("\n[1/4] Qdrant连接测试")
try:
    import requests

    # 使用Session解决502问题
    session = requests.Session()
    session.trust_env = False
    response = session.get("http://127.0.0.1:6333/collections", timeout=10)
    if response.status_code == 200:
        collections = response.json().get("result", {}).get("collections", [])
        print("✅ Qdrant连接成功")
        print(f"   现有集合: {len(collections)} 个")
        for c in collections:
            print(f"   - {c['name']}")
    else:
        print(f"❌ Qdrant响应异常: {response.status_code}")
except Exception as e:
    print(f"❌ Qdrant连接失败: {e}")

# 测试2: BGE模型加载
print("\n[2/4] BGE模型加载测试")
try:
    from phase2.vector_processor import BGEVectorizer

    vectorizer = BGEVectorizer()

    if vectorizer.model:
        print("✅ BGE模型加载成功")
        print(f"   模型路径: {vectorizer.model_path}")
        print(f"   向量维度: {vectorizer.vector_dimension}")
        print(f"   设备: {vectorizer.model.device}")
    else:
        print("⚠️  BGE模型未加载")
except Exception as e:
    print(f"❌ BGE模型加载失败: {e}")
    import traceback
    traceback.print_exc()

# 测试3: NebulaGraph连接
print("\n[3/4] NebulaGraph连接测试")
try:
    from nebula3.Config import Config
    from nebula3.gclient.net import ConnectionPool

    config = Config()
    config.max_connection_pool_size = 2

    pool = ConnectionPool()
    pool.init([('127.0.0.1', 9669)], config)

    session = pool.get_session('root', 'xiaonuo@Athena')
    result = session.execute('SHOW SPACES;')

    spaces = [row.values[0] for row in result.rows()]
    print("✅ NebulaGraph连接成功")
    print(f"   现有空间: {len(spaces)} 个")
    for s in spaces:
        print(f"   - {s}")

    session.release()
    pool.close()
except Exception as e:
    print(f"❌ NebulaGraph连接失败: {e}")

# 测试4: PostgreSQL连接
print("\n[4/4] PostgreSQL连接测试")
try:
    import psycopg2

    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="patent_db",
        user="xujian",
        password=config.get('POSTGRES_USER', 'apps/apps/xiaonuo')
    )

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM patents;")
    count = cursor.fetchone()[0]

    print("✅ PostgreSQL连接成功")
    print(f"   专利记录数: {count}")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ PostgreSQL连接失败: {e}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
