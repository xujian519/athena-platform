#!/usr/bin/env python3
"""
AI家族统一记忆接口
Unified Family Memory Interface

提供统一的记忆访问接口,自动在Qdrant和PostgreSQL之间切换
默认使用PostgreSQL + pgvector,Qdrant作为备用

作者: 小诺·双鱼公主
创建时间: 2025-12-29
版本: v1.0.0 "统一记忆"
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class MemoryBackend(Enum):
    """记忆后端类型"""

    POSTGRESQL = "postgresql"  # PostgreSQL + pgvector (默认)
    QDRANT = "qdrant"  # Qdrant (备用)


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
    related_memories: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    access_count: int = 0
    last_accessed: str = ""


class UnifiedFamilyMemory:
    """统一家族记忆接口"""

    def __init__(
        self, backend: MemoryBackend = MemoryBackend.POSTGRESQL, fallback_enabled: bool = True
    ):
        """
        初始化统一记忆接口

        Args:
            backend: 首选后端 (默认PostgreSQL)
            fallback_enabled: 是否启用备用后端
        """
        self.backend = backend
        self.fallback_enabled = fallback_enabled
        self.primary_client = None
        self.fallback_client = None
        self.model = None

        logger.info("🧠 统一家族记忆接口初始化")
        logger.info(f"   主后端: {backend.value}")
        logger.info(f"   备用后端: {'已启用' if fallback_enabled else '未启用'}")

    async def initialize(self):
        """初始化记忆系统"""
        try:
            if self.backend == MemoryBackend.POSTGRESQL:
                await self._init_postgresql()
            else:
                await self._init_qdrant()

            # 初始化备用后端
            if self.fallback_enabled and self.backend != MemoryBackend.QDRANT:
                try:
                    pass
                except Exception as e:
                    logger.error(f"操作失败: {e}", exc_info=True)
                    raise
            logger.info("✅ 统一家族记忆接口初始化完成")
            return True

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def _init_postgresql(self):
        """初始化PostgreSQL后端"""
        # 动态导入避免循环依赖
        import importlib

        module = importlib.import_module(".family_memory_pg", package="core.memory")
        FamilyMemoryPG = module.FamilyMemoryPG

        self.primary_client = FamilyMemoryPG(
            host="localhost",
            port=5432,
            database="athena_memory",
            user="xujian",
            model_path="/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3",
        )
        await self.primary_client.initialize()
        logger.info("✅ PostgreSQL后端已就绪")

    async def _init_qdrant(self):
        """初始化Qdrant后端"""
        # 动态导入
        import importlib

        module = importlib.import_module(".family_memory_vector_db", package="core.memory")
        FamilyMemoryVectorDB = module.FamilyMemoryVectorDB

        client = FamilyMemoryVectorDB(qdrant_host="localhost", qdrant_port=6333)
        await client.initialize()

        if self.backend == MemoryBackend.QDRANT:
            self.primary_client = client
        else:
            self.fallback_client = client

        logger.info("✅ Qdrant后端已就绪")

    async def add_memory(self, memory: MemoryVector) -> bool:
        """添加记忆"""
        try:
            return await self._add_to_primary(memory)
        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise
        except Exception as e:

            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def _add_to_primary(self, memory: MemoryVector) -> bool:
        """写入主后端"""
        if self.backend == MemoryBackend.POSTGRESQL:
            return await self.primary_client.add_memory(memory)
        else:
            # Qdrant需要embedding
            if not self.model:
                from sentence_transformers import SentenceTransformer

                self.model = SentenceTransformer(
                    "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3"
                )
            embedding = self.model.encode(memory.content).tolist()
            return await self.primary_client.add_memory(memory, embedding)

    async def _add_to_fallback(self, memory: MemoryVector) -> bool:
        """写入备用后端"""
        # 动态导入
        import importlib

        module = importlib.import_module(".family_memory_vector_db", package="core.memory")
        FamilyMemoryVectorDB = module.FamilyMemoryVectorDB

        if isinstance(self.fallback_client, FamilyMemoryVectorDB):
            if not self.model:
                from sentence_transformers import SentenceTransformer

                self.model = SentenceTransformer(
                    "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3"
                )
            embedding = self.model.encode(memory.content).tolist()
            return await self.fallback_client.add_memory(memory, embedding)
        else:
            return await self.fallback_client.add_memory(memory)

    async def search_similar_memories(
        self,
        query: str,
        agent: str | None = None,
        memory_type: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """搜索相似记忆"""
        try:
            if self.backend == MemoryBackend.POSTGRESQL:
                return await self.primary_client.search_similar_memories(
                    query, agent, memory_type, limit
                )
            else:
                # Qdrant需要embedding
                if not self.model:
                    from sentence_transformers import SentenceTransformer

                    self.model = SentenceTransformer(
                        "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3"
                    )

                embedding = self.model.encode(query).tolist()
                results = await self.primary_client.search_memories(
                    query_vector=embedding, limit=limit, score_threshold=0.0
                )

                # 转换结果格式
                return [
                    {
                        "memory_id": r.payload.get("memory_id", ""),
                        "agent": r.payload.get("agent", ""),
                        "memory_type": r.payload.get("memory_type", ""),
                        "content": r.payload.get("content", ""),
                        "similarity": 1 - r.score,  # 转换距离为相似度
                    }
                    for r in results
                ]

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def get_recent_memories(self, agent: str | None = None, limit: int = 10) -> list[dict]:
        """获取最近的记忆"""
        try:
            return await self.primary_client.get_recent_memories(agent, limit)
        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def get_memory_by_id(self, memory_id: str) -> dict | None:
        """根据ID获取记忆"""
        try:
            return await self.primary_client.get_memory_by_id(memory_id)
        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def close(self):
        """关闭连接"""
        if self.primary_client and hasattr(self.primary_client, "close"):
            await self.primary_client.close()
        if self.fallback_client and hasattr(self.fallback_client, "close"):
            await self.fallback_client.close()
        logger.info("✅ 统一家族记忆接口已关闭")


# 单例实例
_unified_memory_instance = None


async def get_unified_memory() -> UnifiedFamilyMemory:
    """获取统一记忆实例(单例)"""
    global _unified_memory_instance

    if _unified_memory_instance is None:
        _unified_memory_instance = UnifiedFamilyMemory(
            backend=MemoryBackend.POSTGRESQL, fallback_enabled=True
        )
        await _unified_memory_instance.initialize()

    return _unified_memory_instance


# 便捷函数
async def add_family_memory(
    content: str,
    agent: str,
    memory_type: str = "episodic",
    importance: float = 0.5,
    emotional_weight: float = 0.5,
) -> bool:
    """添加家族记忆(便捷函数)"""
    memory = MemoryVector(
        memory_id=f"{memory_type}_{uuid.uuid4().hex[:12]}",
        content=content,
        memory_type=memory_type,
        agent=agent,
        timestamp=datetime.now().isoformat(),
        importance=importance,
        emotional_weight=emotional_weight,
    )

    unified_memory = await get_unified_memory()
    return await unified_memory.add_memory(memory)


async def search_family_memories(
    query: str | None = None, agent: str | None = None, limit: int = 5
) -> list[dict]:
    """搜索家族记忆(便捷函数)"""
    unified_memory = await get_unified_memory()
    return await unified_memory.search_similar_memories(query, agent, limit=limit)
