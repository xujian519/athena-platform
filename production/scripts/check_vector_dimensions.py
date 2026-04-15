#!/usr/bin/env python3
"""
快速验证向量维度
Quick Vector Dimension Verification

检查当前记忆系统的向量维度配置
"""

from __future__ import annotations
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncpg


async def check_vector_dimensions():
    """检查数据库中的向量维度"""

    print("="*80)
    print("🔍 向量维度检查工具")
    print("="*80)
    print()

    # 连接数据库
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        database='athena_memory',
        user='postgres'
    )

    try:
        # 检查表结构
        print("📋 数据库表结构:")
        print("-" * 80)

        columns = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'agent_memories'
            AND column_name LIKE '%vector%'
            ORDER BY ordinal_position
        """)

        if columns:
            for col in columns:
                print(f"   {col['column_name']}: {col['data_type']}")
        else:
            print("   ⚠️ 未找到向量相关列")

        print()

        # 检查向量数据
        print("📊 向量数据统计:")
        print("-" * 80)

        stats = await conn.fetchrow("""
            SELECT
                COUNT(*) as total,
                COUNT(vector_embedding) as with_vectors,
                COUNT(*) - COUNT(vector_embedding) as without_vectors
            FROM agent_memories
        """)

        print(f"   总记忆数: {stats['total']}")
        print(f"   有向量: {stats['with_vectors']}")
        print(f"   无向量: {stats['without_vectors']}")

        print()

        # 检查向量维度
        if stats['with_vectors'] > 0:
            print("🔢 向量维度检查:")
            print("-" * 80)

            result = await conn.fetchrow("""
                SELECT memory_id, array_length(vector_embedding, 1) as dimension
                FROM agent_memories
                WHERE vector_embedding IS NOT NULL
                LIMIT 1
            """)

            if result:
                dimension = result['dimension']
                print(f"   检测到的向量维度: {dimension}")

                if dimension == 1024:
                    print("   ✅ 向量维度正确：1024维 (bge-m3)")
                elif dimension == 768:
                    print("   ⚠️ 向量维度为1024维（BGE-M3），需要迁移到1024维")
                    print("   💡 运行迁移脚本: bash production/scripts/run_vector_migration.sh")
                else:
                    print(f"   ⚠️ 未知的向量维度: {dimension}")

                # 显示示例向量
                sample = await conn.fetchrow("""
                    SELECT vector_embedding
                    FROM agent_memories
                    WHERE vector_embedding IS NOT NULL
                    LIMIT 1
                """)

                if sample:
                    vector = sample['vector_embedding']
                    print(f"   向量示例 (前10维): {vector[:10]}")
            else:
                print("   ⚠️ 无法获取向量维度")

        print()

        # 按智能体统计
        print("👥 按智能体统计:")
        print("-" * 80)

        by_agent = await conn.fetch("""
            SELECT
                agent_id,
                COUNT(*) as total,
                COUNT(vector_embedding) as with_vectors,
                array_length(vector_embedding, 1) as dimension
            FROM agent_memories
            GROUP BY agent_id
            ORDER BY with_vectors DESC
        """)

        for row in by_agent:
            dim_str = f"{row['dimension']}维" if row['dimension'] else "未知"
            print(f"   {row['agent_id']}: {row['with_vectors']}/{row['total']} 条向量 ({dim_str})")

        print()
        print("="*80)
        print("✅ 检查完成")
        print("="*80)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_vector_dimensions())
