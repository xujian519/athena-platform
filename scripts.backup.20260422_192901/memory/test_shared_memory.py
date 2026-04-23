#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试共享记忆查询逻辑
"""

import subprocess
from typing import Any, Dict, List, Optional, Tuple, Callable, Union

# PostgreSQL连接信息
PSQL_PATH = '/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql'
DB_HOST = 'localhost'
DB_PORT = '5438'
DB_NAME = 'memory_module'

def test_shared_memory_query() -> Any:
    """测试共享记忆查询"""
    print("🔍 测试共享记忆查询逻辑...\n")

    # 1. 首先创建一个明确的共享记忆
    print("1. 创建共享记忆...")
    create_sql = """
    INSERT INTO memory_items (
        agent_id, agent_type, content, memory_type, memory_tier,
        importance, emotional_weight, family_related, work_related,
        tags, metadata, related_agents, created_at, updated_at
    ) VALUES (
        'test_shared_source',
        'athena',
        '【共享记忆】这是一个跨智能体测试记忆',
        'knowledge',
        'eternal',
        1.0,
        0.8,
        false,
        true,
        ARRAY['共享', '测试'],
        '{"shared": true, "test": true}'::jsonb,
        ARRAY['athena', 'xiaona', 'yunxi', 'xiaochen', 'xiaonuo'],
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
        '-c', create_sql
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        shared_id = result.stdout.strip().split('\n')[-1]  # 获取最后一行（UUID）
        print(f"✅ 共享记忆创建成功，ID: {shared_id}")
    else:
        print(f"❌ 创建失败: {result.stderr}")
        return

    # 2. 测试每个智能体的查询
    agents = ['athena', 'xiaona', 'yunxi', 'xiaochen', 'xiaonuo']

    print("\n2. 测试各智能体查询权限...")

    for agent in agents:
        print(f"\n  🤖 测试智能体: {agent}")

        # 使用更精确的查询
        search_sql = f"""
        SELECT content, agent_type, related_agents
        FROM memory_items
        WHERE content = '【共享记忆】这是一个跨智能体测试记忆'
        AND ('{agent}' = ANY(related_agents)
             OR agent_type = '{agent}'
             OR agent_id LIKE '%{agent}%');
        """

        cmd = [
            PSQL_PATH,
            '-h', DB_HOST,
            '-p', str(DB_PORT),
            '-d', DB_NAME,
            '-c', search_sql
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            # 解析输出
            lines = result.stdout.strip().split('\n')
            if len(lines) > 2:  # 有数据
                print(f"    ✅ 可以访问")
                # 显示内容
                content_line = lines[2] if len(lines) > 2 else ""
                if "【共享记忆】" in content_line:
                    print(f"    📝 找到共享记忆")
            else:
                print(f"    ❌ 无法访问")
        else:
            print(f"    ❌ 查询失败: {result.stderr[:100]}...")

    # 3. 验证related_agents字段
    print("\n3. 验证related_agents字段...")
    verify_sql = """
    SELECT related_agents
    FROM memory_items
    WHERE content = '【共享记忆】这是一个跨智能体测试记忆';
    """

    cmd = [
        PSQL_PATH,
        '-h', DB_HOST,
        '-p', str(DB_PORT),
        '-d', DB_NAME,
        '-c', verify_sql
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"  📋 related_agents: {result.stdout}")

if __name__ == "__main__":
    test_shared_memory_query()