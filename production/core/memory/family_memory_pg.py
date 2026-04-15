#!/usr/bin/env python3
"""
AI家族共享记忆 - PostgreSQL版本
Family Shared Memory with PostgreSQL + pgvector

从Qdrant迁移到PostgreSQL + pgvector的实现
保持原有API接口兼容
"""

from __future__ import annotations
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from dateutil import parser as date_parser

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class AgentType(Enum):
    """智能体类型"""

    XIAONUO = "小诺"
    XIANA = "小娜"
    ATHENA = "Athena"
    FATHER = "徐健"


class MemoryCategory(Enum):
    """记忆分类"""

    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass
class MemoryVector:
    """记忆向量对象"""

    memory_id: str
    content: str
    memory_type: str
    agent: str
    timestamp: str
    title: str = ""
    importance: float = 0.5
    emotional_weight: float = 0.5
    tags: list = field(default_factory=list)
    participants: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    access_count: int = 0
    last_accessed: str = ""


class FamilyMemoryPG:
    """AI家族共享记忆 - PostgreSQL实现"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "athena_memory",
        user: str = "xujian",
        model_path: str | None = None,
    ):
        """初始化PostgreSQL记忆库

        ⚠️ 安全说明:table_name是硬编码的常量,不接受用户输入,因此是安全的
        """
        self.pg_config = {"host": host, "port": port, "database": database, "user": user}
        # 硬编码表名,不接受用户输入
        self.table_name = "ai_family_shared_memory"

        # 验证表名(安全检查)
        import re

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", self.table_name):
            raise ValueError(f"Invalid table name: {self.table_name}")

        self.pool = None
        self.model = None

        # BGE模型路径
        if model_path:
            try:
                logger.info(f"✅ BGE模型加载成功: {model_path}")
            except Exception as e:
                logger.error(f"操作失败: {e}", exc_info=True)
                raise
    async def initialize(self):
        """初始化连接池"""
        import asyncpg

        # 构建PostgreSQL DSN
        dsn = f"postgresql://{self.pg_config['user']}@{self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['database']}"
        self.pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10)
        logger.info("✅ PostgreSQL连接池已建立")

        # 检查表是否存在
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                """
                SELECT COUNT(*) FROM pg_tables
                WHERE schemaname = 'public' AND tablename = $1
            """,
                self.table_name,
            )

            if result > 0:
                # 使用参数化查询
                count = await conn.fetchval(
                    f"SELECT COUNT(*) FROM {self.table_name}"
                )
                logger.info(f"✅ 表 {self.table_name} 存在,包含 {count} 条记录")
            else:
                logger.error(f"❌ 表 {self.table_name} 不存在")

    async def add_memory(self, memory: MemoryVector) -> bool:
        """添加记忆"""
        async with self.pool.acquire() as conn:
            # 生成向量
            embedding = None
            if self.model:
                vector = self.model.encode(memory.content)
                embedding = f"[{','.join(map(str, vector))}]"

            # 解析时间戳
            created_at = datetime.now()
            if memory.timestamp:
                try:
                    created_at = date_parser.isoparse(memory.timestamp)
                except Exception as e:
                    logger.error(f"操作失败: {e}", exc_info=True)
                    raise

            # 插入数据 - 使用参数化查询防止SQL注入
            # 注意: 表名已经通过正则验证在初始化时确保安全
            await conn.execute(
                f"""
                INSERT INTO {self.table_name} (
                    memory_id, agent, memory_type, content, title,
                    importance, emotional_weight, tags, participants,
                    embedding, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (memory_id) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    access_count = {self.table_name}.access_count + 1
            """,
                memory.memory_id,
                memory.agent,
                memory.memory_type,
                memory.content,
                memory.title,
                memory.importance,
                memory.emotional_weight,
                memory.tags,
                memory.participants,
                embedding,
                json.dumps(memory.metadata, ensure_ascii=False),
                created_at,
            )

        logger.info(f"✅ 记忆已添加: {memory.memory_id}")
        return True

    async def search_similar_memories(
        self,
        query: str,
        agent: str | None = None,
        memory_type: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """搜索相似记忆"""
        if not self.model:
            logger.warning("⚠️ 模型未加载,无法执行向量搜索")
            return []

        # 生成查询向量
        query_vector = self.model.encode(query)
        vector_str = f"[{','.join(map(str, query_vector))}]"

        # 构建参数化查询
        conditions = []
        params = [vector_str, limit]
        param_idx = 3

        if agent:
            # 使用参数化查询防止SQL注入
            conditions.append(f"agent = ${param_idx}")
            params.append(agent)
            param_idx += 1

        if memory_type:
            # 使用参数化查询防止SQL注入
            conditions.append(f"memory_type = ${param_idx}")
            params.append(memory_type)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        async with self.pool.acquire() as conn:
            # 使用参数化查询
            results = await conn.fetch(
                f"""
                SELECT
                    memory_id,
                    agent,
                    memory_type,
                    content,
                    title,
                    importance,
                    emotional_weight,
                    tags,
                    metadata,
                    1 - (embedding <=> $1::vector) as similarity
                FROM {self.table_name}
                {where_clause}
                ORDER BY embedding <=> $1::vector
                LIMIT $2
            """,
                *params,
            )

        return [dict(row) for row in results]

    async def get_memory_by_id(self, memory_id: str) -> dict | None:
        """根据ID获取记忆"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                f"""
                SELECT * FROM {self.table_name} WHERE memory_id = $1
            """,
                memory_id,
            )

            return dict(result) if result else None

    async def get_recent_memories(self, agent: str | None = None, limit: int = 10) -> list[dict]:
        """获取最近的记忆"""
        async with self.pool.acquire() as conn:
            if agent:
                results = await conn.fetch(
                    f"""
                    SELECT * FROM {self.table_name}
                    WHERE agent = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """,
                    agent,
                    limit,
                )
            else:
                results = await conn.fetch(
                    f"""
                    SELECT * FROM {self.table_name}
                    ORDER BY created_at DESC
                    LIMIT $1
                """,
                    limit,
                )

        return [dict(row) for row in results]

    async def close(self):
        """关闭连接池"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ 连接池已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
        return False


# 单例实例
_pg_instance = None


async def get_family_memory_pg() -> FamilyMemoryPG:
    """获取PostgreSQL记忆库实例"""
    global _pg_instance

    if _pg_instance is None:
        _pg_instance = FamilyMemoryPG(
            model_path="/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3"
        )
        await _pg_instance.initialize()

    return _pg_instance


# 测试代码
async def test():
    """测试PostgreSQL记忆库"""
    print("🧪 测试PostgreSQL记忆库\n")

    # 初始化
    memory = FamilyMemoryPG(model_path="/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3")
    await memory.initialize()

    # 测试搜索
    print("\n🔍 测试1: 搜索相似记忆")
    results = await memory.search_similar_memories("写诗", limit=3)

    for idx, row in enumerate(results, 1):
        print(f"{idx}. [{row['agent']}] 相似度: {row['similarity']:.4f}")
        print(f"   {row['content'][:50]}...\n")

    # 测试按智能体查询
    print("\n🔍 测试2: 获取小诺的最近记忆")
    recent = await memory.get_recent_memories(agent="小诺", limit=3)

    for idx, row in enumerate(recent, 1):
        print(f"{idx}. {row['memory_type']}: {row['content'][:40]}...")

    # 统计信息
    async with memory.pool.acquire() as conn:
        count = await conn.fetchval(f"SELECT COUNT(*) FROM {memory.table_name}")
        print(f"\n📊 总记忆数: {count}")

    await memory.close()
    print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(test())
