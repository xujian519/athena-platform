#!/usr/bin/env python3
from __future__ import annotations
"""
记忆数据迁移脚本
将旧的agent_memory表数据迁移到新的agent_memories统一结构
"""

import asyncio
import logging
import sys
import uuid
from pathlib import Path

import asyncpg

from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO)
logger = setup_logging()


async def migrate_agent_memory():
    """迁移agent_memory表数据到agent_memories表"""

    # 数据库连接配置
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "athena_memory",
        "user": "postgres",
        "password": "",
    }

    logger.info("🔄 开始记忆数据迁移...")

    try:
        conn = await asyncpg.connect(**db_config)
        logger.info("✅ 数据库连接成功")

        # 检查源数据
        source_count = await conn.fetchval("SELECT COUNT(*) FROM agent_memory")
        logger.info(f"📊 源表(agent_memory)记录数: {source_count}")

        if source_count == 0:
            logger.info("⚠️ 源表无数据,无需迁移")
            await conn.close()
            return

        # 检查目标数据
        target_count = await conn.fetchval("SELECT COUNT(*) FROM agent_memories")
        logger.info(f"📊 目标表(agent_memories)现有记录数: {target_count}")

        # 查询源数据
        rows = await conn.fetch("""
            SELECT
                id,
                agent_id,
                context_type,
                content,
                importance_score,
                access_count,
                last_accessed,
                metadata,
                created_at
            FROM agent_memory
            ORDER BY created_at
        """)

        logger.info(f"📦 准备迁移 {len(rows)} 条记录")

        # 迁移数据
        migrated = 0
        skipped = 0
        errors = 0

        for row in rows:
            try:
                agent_type = "xiaonuo"  # 默认类型
                if "xiaona" in row["agent_id"].lower():
                    agent_type = "xiaona"
                elif "athena" in row["agent_id"].lower():
                    agent_type = "athena"

                # 确定记忆类型和层级
                memory_type = "conversation"
                if row["context_type"] in ["knowledge", "professional"]:
                    memory_type = "knowledge"
                elif row["context_type"] in ["family", "emotional"]:
                    memory_type = "family"

                memory_tier = "cold"
                if row["access_count"] > 10 or row["importance_score"] >= 8:
                    memory_tier = "warm"
                if row["importance_score"] >= 9:
                    memory_tier = "eternal"

                # 插入数据
                await conn.execute(
                    """
                    INSERT INTO agent_memories (
                        memory_id,
                        agent_id,
                        agent_type,
                        content,
                        memory_type,
                        memory_tier,
                        importance,
                        access_count,
                        last_accessed,
                        metadata,
                        created_at,
                        family_related,
                        work_related,
                        tags
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    ON CONFLICT (memory_id) DO NOTHING
                """,
                    str(uuid.uuid4()),  # 生成新UUID
                    row["agent_id"],
                    agent_type,
                    row["content"],
                    memory_type,
                    memory_tier,
                    row["importance_score"] / 10.0,  # 转换为0-1范围
                    row["access_count"],
                    row["last_accessed"],
                    row["metadata"],
                    row["created_at"],
                    memory_type == "family",
                    memory_type in ["knowledge", "professional"],
                    [row["context_type"]],
                )

                migrated += 1
                if migrated % 10 == 0:
                    logger.info(f"✅ 已迁移 {migrated}/{len(rows)} 条记录")

            except Exception:
                raise

        # 统计结果
        new_target_count = await conn.fetchval("SELECT COUNT(*) FROM agent_memories")
        new_records = new_target_count - target_count

        logger.info("═══════════════════════════════════")
        logger.info("📊 迁移统计:")
        logger.info(f"  源表记录数: {source_count}")
        logger.info(f"  成功迁移: {migrated}")
        logger.info(f"  跳过记录: {skipped}")
        logger.info(f"  错误记录: {errors}")
        logger.info(f"  目标表新增: {new_records}")
        logger.info(f"  目标表总计: {new_target_count}")
        logger.info("═══════════════════════════════════")

        # 验证迁移结果
        verification = await conn.fetchrow("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT agent_id) as agents,
                COUNT(CASE WHEN memory_tier = 'eternal' THEN 1 END) as eternal,
                COUNT(CASE WHEN family_related = TRUE THEN 1 END) as family,
                AVG(importance) as avg_importance
            FROM agent_memories
        """)

        logger.info("📈 迁移后数据验证:")
        logger.info(f"  总记录数: {verification['total']}")
        logger.info(f"  智能体数: {verification['agents']}")
        logger.info(f"  永恒记忆: {verification['eternal']}")
        logger.info(f"  家庭记忆: {verification['family']}")
        logger.info(f"  平均重要性: {verification['avg_importance']:.2f}")

        await conn.close()
        logger.info("✅ 迁移完成!")

    except Exception:
        raise


if __name__ == "__main__":
    asyncio.run(migrate_agent_memory())
