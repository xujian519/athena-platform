#!/usr/bin/env python3
"""
统一记忆系统向量维度迁移脚本
Vector Dimension Migration Script for Unified Memory System

将历史数据从1024维向量（BGE-M3）迁移到1024维向量
Migrate historical data from 1024-dim (BGE-M3) vectors to 1024-dim vectors

作者: Athena平台团队
创建时间: 2026-01-14
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

import aiohttp
import asyncpg
from sentence_transformers import SentenceTransformer

# 配置日志
log_dir = project_root / "production" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(log_dir / "vector_migration.log"),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class VectorDimensionMigrator:
    """向量维度迁移器"""

    def __init__(self):
        self.bge_model = None
        self.pg_pool = None
        self.qdrant_client = None

        # 数据库配置
        self.db_config = {
            'postgresql': {
                'host': 'localhost',
                'port': 5432,
                'database': 'athena_memory',
                'user': 'postgres',
                'password': ''
            },
            'qdrant': {
                'host': 'localhost',
                'port': 6333
            }
        }

        # 统计信息
        self.stats = {
            'total_memories': 0,
            'migrated_memories': 0,
            'skipped_memories': 0,
            'failed_memories': 0,
            'old_dimension': 768,
            'new_dimension': 1024
        }

    async def initialize(self):
        """初始化迁移器"""
        logger.info("🚀 初始化向量维度迁移器...")

        # 加载BGE-M3模型
        await self._load_bge_model()

        # 初始化PostgreSQL连接
        await self._init_postgresql()

        # 初始化Qdrant客户端
        await self._init_qdrant()

        logger.info("✅ 迁移器初始化完成")

    async def _load_bge_model(self):
        """加载BGE-M3模型"""
        try:
            logger.info("🔤 加载BGE-M3模型...")

            model_path = project_root / "models" / "converted" / "BAAI" / "bge-m3"

            self.bge_model = SentenceTransformer(
                str(model_path),
                device="mps"  # 使用Apple Silicon加速
            )

            logger.info("✅ BGE-M3模型加载成功，向量维度: 1024")

        except Exception as e:
            logger.error(f"❌ BGE-M3模型加载失败: {e}")
            raise

    async def _init_postgresql(self):
        """初始化PostgreSQL连接"""
        config = self.db_config['postgresql']

        self.pg_pool = await asyncpg.create_pool(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            min_size=5,
            max_size=20
        )

        logger.info("✅ PostgreSQL连接池已建立")

    async def _init_qdrant(self):
        """初始化Qdrant客户端"""
        self.qdrant_client = aiohttp.ClientSession(
            base_url=f"http://{self.db_config['qdrant']['host']}:{self.db_config['qdrant']['port']}",
            timeout=aiohttp.ClientTimeout(total=30)
        )

        logger.info("✅ Qdrant客户端已初始化")

    async def check_database_schema(self) -> bool:
        """检查数据库表结构"""
        logger.info("🔍 检查数据库表结构...")

        async with self.pg_pool.acquire() as conn:
            # 检查vector_embedding列的维度
            result = await conn.fetchval("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'agent_memories'
                AND column_name = 'vector_embedding'
            """)

            if result == 0:
                logger.warning("⚠️ vector_embedding列不存在，无需迁移")
                return False

        logger.info("✅ 数据库表结构检查完成")
        return True

    async def get_memory_statistics(self) -> dict[str, Any]:
        """获取记忆数据统计信息"""
        logger.info("📊 获取记忆数据统计...")

        async with self.pg_pool.acquire() as conn:
            # 总记忆数
            total = await conn.fetchval("SELECT COUNT(*) FROM agent_memories")

            # 有向量嵌入的记忆数
            with_vectors = await conn.fetchval(
                "SELECT COUNT(*) FROM agent_memories WHERE vector_embedding IS NOT NULL"
            )

            # 按智能体分组统计
            by_agent = await conn.fetch("""
                SELECT
                    agent_id,
                    COUNT(*) as count,
                    COUNT(vector_embedding) as with_vectors
                FROM agent_memories
                GROUP BY agent_id
                ORDER BY count DESC
            """)

        stats = {
            'total_memories': total,
            'memories_with_vectors': with_vectors,
            'memories_without_vectors': total - with_vectors,
            'by_agent': {row['agent_id']: {
                'total': row['count'],
                'with_vectors': row['with_vectors']
            } for row in by_agent}
        }

        logger.info(f"📊 总记忆数: {stats['total_memories']}")
        logger.info(f"📊 有向量: {stats['memories_with_vectors']}")
        logger.info(f"📊 无向量: {stats['memories_without_vectors']}")

        return stats

    async def recreate_qdrant_collections(self):
        """重建Qdrant集合（从1024维（BGE-M3）改为1024维）"""
        logger.info("🔄 重建Qdrant集合...")

        collections = [
            "athena", "xiaona", "yunxi", "xiaochen", "xiaonuo",
            "athena_conversations", "xiaona_conversations",
            "yunxi_conversations", "xiaochen_conversations", "xiaonuo_conversations"
        ]

        for collection_name in collections:
            try:
                # 删除旧集合
                logger.info(f"   删除集合: {collection_name}")
                async with self.qdrant_client.delete(
                    f"/collections/{collection_name}"
                ) as resp:
                    if resp.status not in [200, 404]:
                        logger.warning(f"   ⚠️ 删除失败: {await resp.text()}")

                # 创建新集合（1024维）
                logger.info(f"   创建集合: {collection_name} (1024维)")

                payload = {
                    "vectors": {
                        "size": 1024,
                        "distance": "Cosine"
                    }
                }

                async with self.qdrant_client.put(
                    f"/collections/{collection_name}",
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"   ✅ {collection_name} 创建成功")
                    else:
                        logger.error(f"   ❌ {collection_name} 创建失败: {await resp.text()}")

            except Exception as e:
                logger.error(f"❌ 处理集合 {collection_name} 失败: {e}")

        logger.info("✅ Qdrant集合重建完成")

    async def migrate_memory_vectors(self, batch_size: int = 100):
        """迁移记忆向量"""
        logger.info("🔄 开始迁移记忆向量...")
        logger.info(f"   批处理大小: {batch_size}")

        self.stats['total_memories'] = 0

        async with self.pg_pool.acquire() as conn:
            # 获取所有需要迁移的记忆
            rows = await conn.fetch("""
                SELECT memory_id, agent_id, content
                FROM agent_memories
                WHERE content IS NOT NULL
                ORDER BY created_at DESC
            """)

            self.stats['total_memories'] = len(rows)
            logger.info(f"📊 需要处理的记忆总数: {self.stats['total_memories']}")

            # 批量处理
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                logger.info(f"🔄 处理批次 {i//batch_size + 1}/{(len(rows)-1)//batch_size + 1} ({len(batch)}条)")

                await self._process_batch(conn, batch)

    async def _process_batch(self, conn, batch: list):
        """处理一个批次的记忆"""
        # 生成1024维向量
        texts = [row['content'] for row in batch]

        try:
            # 批量编码
            embeddings = self.bge_model.encode(
                texts,
                normalize_embeddings=True,
                batch_size=32,
                show_progress_bar=False
            )

            # 更新数据库
            for row, embedding in zip(batch, embeddings, strict=False):
                try:
                    # 将numpy数组转换为列表
                    vector_list = embedding.tolist()

                    # 更新PostgreSQL中的向量
                    await conn.execute("""
                        UPDATE agent_memories
                        SET vector_embedding = $1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE memory_id = $2
                    """, vector_list, row['memory_id'])

                    self.stats['migrated_memories'] += 1

                except Exception as e:
                    logger.error(f"❌ 更新记忆 {row['memory_id']} 失败: {e}")
                    self.stats['failed_memories'] += 1

        except Exception as e:
            logger.error(f"❌ 批量编码失败: {e}")
            # 失败的批次标记为跳过
            self.stats['skipped_memories'] += len(batch)

    async def update_qdrant_collections(self):
        """更新Qdrant集合数据"""
        logger.info("🔄 更新Qdrant集合数据...")

        async with self.pg_pool.acquire() as conn:
            # 获取所有有向量的记忆
            rows = await conn.fetch("""
                SELECT memory_id, agent_id, agent_type, vector_embedding,
                       memory_type, memory_tier, importance, tags,
                       EXTRACT(EPOCH FROM created_at)::bigint as created_at
                FROM agent_memories
                WHERE vector_embedding IS NOT NULL
                LIMIT 1000
            """)

            logger.info(f"📊 需要同步到Qdrant的记忆数: {len(rows)}")

            # 按智能体分组
            memories_by_agent = {}
            for row in rows:
                agent_id = row['agent_id']
                if agent_id not in memories_by_agent:
                    memories_by_agent[agent_id] = []
                memories_by_agent[agent_id].append(row)

            # 为每个智能体更新Qdrant
            for agent_id, memories in memories_by_agent.items():
                await self._update_agent_qdrant_collection(agent_id, memories)

        logger.info("✅ Qdrant集合更新完成")

    async def _update_agent_qdrant_collection(self, agent_id: str, memories: list):
        """更新智能体的Qdrant集合"""
        collection_name = f"{agent_id}_memories"

        # 准备批量插入数据
        points = []
        for memory in memories:
            points.append({
                "id": hash(memory['memory_id']) % 1000000000,  # 简单的ID映射
                "vector": memory['vector_embedding'],
                "payload": {
                    "memory_id": memory['memory_id'],
                    "agent_id": memory['agent_id'],
                    "agent_type": memory['agent_type'],
                    "memory_type": memory['memory_type'],
                    "memory_tier": memory['memory_tier'],
                    "importance": memory['importance'],
                    "created_at": memory['created_at']
                }
            })

        # 批量插入
        try:
            async with self.qdrant_client.put(
                f"/collections/{collection_name}/points",
                json={"points": points}
            ) as resp:
                if resp.status == 200:
                    logger.info(f"   ✅ {agent_id}: {len(points)}条记忆已同步")
                else:
                    logger.error(f"   ❌ {agent_id} 同步失败: {await resp.text()}")
        except Exception as e:
            logger.error(f"❌ 同步 {agent_id} 到Qdrant失败: {e}")

    async def verify_migration(self):
        """验证迁移结果"""
        logger.info("🔍 验证迁移结果...")

        async with self.pg_pool.acquire() as conn:
            # 检查向量维度
            sample = await conn.fetchrow("""
                SELECT memory_id, array_length(vector_embedding, 1) as dimension
                FROM agent_memories
                WHERE vector_embedding IS NOT NULL
                LIMIT 1
            """)

            if sample:
                dimension = sample['dimension']
                logger.info(f"✅ 向量维度: {dimension}")

                if dimension == 1024:
                    logger.info("✅ 向量维度正确：1024维")
                else:
                    logger.warning(f"⚠️ 向量维度不正确：期望1024，实际{dimension}")
            else:
                logger.warning("⚠️ 没有找到向量数据")

            # 统计迁移结果
            stats = await self.get_memory_statistics()

        logger.info("📊 迁移统计:")
        logger.info(f"   总记忆数: {self.stats['total_memories']}")
        logger.info(f"   已迁移: {self.stats['migrated_memories']}")
        logger.info(f"   跳过: {self.stats['skipped_memories']}")
        logger.info(f"   失败: {self.stats['failed_memories']}")

    async def close(self):
        """关闭连接"""
        if self.pg_pool:
            await self.pg_pool.close()
            logger.info("✅ PostgreSQL连接已关闭")

        if self.qdrant_client:
            await self.qdrant_client.close()
            logger.info("✅ Qdrant客户端已关闭")


async def main():
    """主函数"""
    logger.info("="*80)
    logger.info("🚀 统一记忆系统向量维度迁移 (1024维（BGE-M3） → 1024维)")
    logger.info("="*80)
    logger.info(f"开始时间: {datetime.now()}")
    logger.info("")

    migrator = VectorDimensionMigrator()

    try:
        # 初始化
        await migrator.initialize()

        # 检查数据库结构
        schema_ok = await migrator.check_database_schema()
        if not schema_ok:
            logger.warning("⚠️ 数据库结构检查失败，终止迁移")
            return

        # 获取统计信息
        await migrator.get_memory_statistics()

        # 重建Qdrant集合
        await migrator.recreate_qdrant_collections()

        # 迁移记忆向量
        await migrator.migrate_memory_vectors(batch_size=100)

        # 更新Qdrant
        await migrator.update_qdrant_collections()

        # 验证迁移
        await migrator.verify_migration()

        logger.info("")
        logger.info("="*80)
        logger.info("🎉 迁移完成！")
        logger.info(f"结束时间: {datetime.now()}")
        logger.info("="*80)

    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await migrator.close()


if __name__ == "__main__":
    asyncio.run(main())
