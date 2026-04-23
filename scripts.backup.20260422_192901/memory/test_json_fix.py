#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JSON格式修复
"""

import subprocess

# PostgreSQL连接信息
PSQL_PATH = '/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql'
DB_HOST = 'localhost'
DB_PORT = '5438'
DB_NAME = 'memory_module'

# 测试不同的JSON格式
json_formats = [
    # 格式1: 简单JSON
    """
    '{"test": true}'::jsonb
    """,

    # 格式2: 带时间戳的JSON
    """
    jsonb_build_object('test', true, 'timestamp', CURRENT_TIMESTAMP)
    """,

    # 格式3: 使用字符串拼接
    """
    ('{"test": true, "timestamp": "' || to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS') || '"}')::jsonb
    """,

    # 格式4: 使用jsonb_build_object
    """
    jsonb_build_object(
        'test', true,
        'timestamp', to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')
    )
    """
]

print("🧪 测试不同的JSON格式...\n")

for i, json_format in enumerate(json_formats, 1):
    print(f"测试格式 {i}:")
    sql = f"""
    INSERT INTO memory_items (
        agent_id, agent_type, content, memory_type, memory_tier,
        importance, emotional_weight, family_related, work_related,
        tags, metadata, created_at, updated_at
    ) VALUES (
        'test_json_{i}',
        'athena',
        'JSON格式测试 {i}',
        'test',
        'hot',
        0.5,
        0.5,
        false,
        true,
        ARRAY['JSON测试'],
        {json_format},
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
    RETURNING id;
    """

    cmd = [
        PSQL_PATH,
        '-h', DB_HOST,
        '-p', str(DB_PORT),
        '-d', DB_NAME,
        '-c', sql
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"  ✅ 成功")
        print(f"  📝 返回ID: {result.stdout.strip()[:50]}...")
    else:
        print(f"  ❌ 失败")
        print(f"  🚨 错误: {result.stderr.strip()[:100]}...")

    print()

print("🏁 测试完成")