from __future__ import annotations
"""
统一Agent记忆系统 - 核心实现
Unified Agent Memory System - Core Implementation

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0

本模块是统一Agent记忆系统的核心实现，提供：
- 多层级记忆存储（热/温/冷/永恒）
- 向量嵌入和语义搜索
- Redis缓存优化
- 跨智能体记忆共享
- 完整的生命周期管理
"""

import asyncio
import hashlib
import json
import logging
import os
import uuid
from collections import OrderedDict
from datetime import datetime
from typing import Any

import aiohttp
import asyncpg

# Redis客户端导入 (兼容处理)
try:
    from redis import asyncio as aioredis  # redis>=4.2.0
except ImportError:
    import aioredis  # 兼容旧版本

from core.memory.unified_memory.types import (
    AGENT_REGISTRY,
    AgentIdentity,
    AgentType,
    CacheStatistics,
    MemoryTier,
    MemoryType,
)
from core.memory.unified_memory.utils import (
    retry_with_backoff,
)

# 创建模块logger
logger = logging.getLogger(__name__)


class UnifiedAgentMemorySystem:
    """统一智能体记忆系统"""

    def __init__(self):
        self.system_name = "Athena统一智能体记忆系统"
        self.version = "v1.0.0 永恒记忆"

        # 数据库配置
        self.db_config = {
            "postgresql": {
                "host": "localhost",
                "port": 5432,  # 使用实际PostgreSQL端口
                "database": "athena",  # 使用实际数据库名
                "user": "xujian",  # 使用实际用户名
                # 安全修复: 从环境变量读取密码,避免硬编码空密码
                "password": os.environ.get("MEMORY_DB_PASSWORD", ""),
            },
            "redis": {
                "host": os.environ.get("REDIS_HOST", "localhost"),
                "port": int(os.environ.get("REDIS_PORT", 6379)),
                "db": int(os.environ.get("REDIS_DB", 0)),
                "password": os.environ.get("REDIS_PASSWORD", None),
                "decode_responses": True,
                # 缓存TTL配置（秒）
                "ttl": {
                    "agent_stats": 300,  # 智能体统计缓存5分钟
                    "search_results": 60,  # 搜索结果缓存1分钟
                    "memory_data": 180,  # 记忆数据缓存3分钟
                    "hot_memory": 600,  # 热记忆缓存10分钟
                },
            },
            "qdrant": {
                "host": "localhost",
                "port": 6333,
                "collections": {
                    "main": "agent_memory_vectors",
                    "conversation": "conversation_vectors",
                    "knowledge": "knowledge_vectors",
                },
            },
            "knowledge_backend": {
                "url": "http://localhost:8002",
                "health_endpoint": "/health",
            },
        }

        # 连接池 - 添加类型注解
        self.pg_pool: asyncpg.Pool | None = None
        self.qdrant_client: aiohttp.ClientSession | None = None
        self.kg_client: aiohttp.ClientSession | None = None
        self.redis_client: aioredis.Redis | None = None
        self._initialized = False  # 添加初始化标志

        # 热记忆缓存（每个智能体独立）
        self.hot_caches = {agent_id: OrderedDict() for agent_id in AGENT_REGISTRY}
        # P4修复: 将硬编码限制移到类配置中,便于维护
        self.HOT_CACHE_LIMIT = 50  # 每个智能体最多50条热记忆

        # 缓存统计
        self.cache_stats = CacheStatistics()

        logger.info(f"🏛️ {self.system_name} 初始化...")
        logger.info(f"📋 注册智能体数量: {len(AGENT_REGISTRY)}")
        logger.info(f"📊 Redis缓存已启用，TTL配置: {self.db_config['redis']['ttl']}")

    def _validate_memory_content(self, content: str, max_length: int = 10000) -> None:
        """
        验证记忆内容

        Args:
            content: 记忆内容
            max_length: 最大允许长度

        Raises:
            ValueError: 如果内容验证失败
        """
        if not content or not isinstance(content, str):
            raise ValueError("记忆内容必须是非空字符串")
        content = content.strip()
        if not content:
            raise ValueError("记忆内容不能为空或仅包含空白字符")
        if len(content) > max_length:
            raise ValueError(
                f"记忆内容过长 (最大{max_length}字符, 实际{len(content)}字符)"
            )

    def _check_initialized(self) -> None:
        """
        检查系统是否已初始化

        Raises:
            RuntimeError: 如果系统未初始化
        """
        if not self._initialized:
            raise RuntimeError(
                f"{self.system_name} 尚未初始化。请先调用 initialize() 方法。"
            )

        # 检查关键连接是否可用
        if self.pg_pool is None:
            raise RuntimeError("PostgreSQL连接池未初始化")

        if self.qdrant_client is None:
            raise RuntimeError("Qdrant客户端未初始化")

    async def initialize(self) -> None:
        """
        初始化系统

        初始化所有数据库连接、创建表结构、初始化collections和永恒记忆

        Raises:
            Exception: 初始化失败时抛出异常
        """
        try:
            # 初始化PostgreSQL连接
            await self._init_postgresql()

            # 初始化Redis缓存
            await self._init_redis()

            # 初始化Qdrant连接
            await self._init_qdrant()

            # 创建数据库表结构
            await self._create_database_schema()

            # 为每个智能体创建collection
            await self._init_qdrant_collections()

            # ⚠️ 在数据库连接建立后设置初始化标志
            # 这样store_memory等方法可以在初始化期间被调用
            self._initialized = True

            # 初始化知识图谱连接
            await self._init_knowledge_graph()

            # 初始化永恒记忆（会调用store_memory）
            await self._init_eternal_memories()

            logger.info(f"✅ {self.system_name} v{self.version} 初始化成功！")

        except Exception as e:
            logger.error(f"❌ 系统初始化失败: {e}", exc_info=True)
            raise

    async def _init_postgresql(self) -> None:
        """
        初始化PostgreSQL连接池

        Creates:
            self.pg_pool: asyncpg连接池对象

        Raises:
            Exception: 连接失败时抛出异常
        """
        config = self.db_config["postgresql"]
        self.pg_pool = await asyncpg.create_pool(
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["user"],
            password=config["password"],
            min_size=5,
            max_size=20,
            command_timeout=60,
        )
        logger.info("✅ PostgreSQL连接池已建立")

    async def _init_redis(self) -> None:
        """
        初始化Redis客户端

        Creates:
            self.redis_client: aioredis客户端

        Note:
            如果Redis连接失败,仅记录警告而不抛出异常
            系统会降级运行,只是不使用缓存功能
        """
        config = self.db_config["redis"]
        try:
            # 构建Redis URL
            redis_url = f"redis://{config['host']}:{config['port']}/{config['db']}"
            if config.get("password"):
                redis_url = f"redis://:{config['password']}@{config['host']}:{config['port']}/{config['db']}"

            self.redis_client = await aioredis.from_url(
                redis_url,
                decode_responses=config["decode_responses"],
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # 测试连接 - 兼容不同版本的redis-py
            try:
                # 尝试异步ping
                if asyncio.iscoroutinefunction(self.redis_client.ping):
                    await self.redis_client.ping()
                else:
                    # 同步版本直接调用
                    self.redis_client.ping()
            except Exception as ping_error:
                logger.warning(f"Redis连接测试失败: {ping_error}")
                self.redis_client = None
                return

            logger.info(f"✅ Redis客户端已初始化 ({config['host']}:{config['port']})")

        except Exception as e:
            logger.warning(f"⚠️ Redis初始化失败: {e}，系统将不使用缓存")
            self.redis_client = None

    async def _init_qdrant(self) -> None:
        """
        初始化Qdrant客户端

        Creates:
            self.qdrant_client: aiohttp客户端会话
        """
        self.qdrant_client = aiohttp.ClientSession(
            base_url=f"http://{self.db_config['qdrant']['host']}:{self.db_config['qdrant']['port']}",
            timeout=aiohttp.ClientTimeout(total=30),
        )
        logger.info("✅ Qdrant客户端已初始化")

    async def _init_knowledge_graph(self) -> None:
        """
        初始化知识图谱客户端

        Creates:
            self.kg_client: aiohttp客户端会话

        Note:
            如果知识图谱服务不可用,仅记录警告而不抛出异常
        """
        self.kg_client = aiohttp.ClientSession(
            base_url=self.db_config["knowledge_backend"]["url"],
            timeout=aiohttp.ClientTimeout(total=10),
        )

        # 检查健康状态
        try:
            async with self.kg_client.get(
                self.db_config["knowledge_backend"]["health_endpoint"]
            ) as resp:
                if resp.status == 200:
                    logger.info("✅ 知识图谱后端运行正常")
                else:
                    logger.warning(f"⚠️ 知识图谱后端状态: {resp.status}")
        except Exception as e:
            logger.warning(f"⚠️ 知识图谱连接失败: {e}")

    async def _create_database_schema(self) -> None:
        """
        创建数据库表结构

        创建以下表和视图:
        - agent_memories: 智能体记忆表
        - agent_conversations: 智能体会话记录表
        - agent_memory_relations: 智能体记忆关联表
        - agent_memory_stats: 记忆统计视图
        - system_memory_summary: 系统汇总视图
        """
        assert self.pg_pool is not None, "PostgreSQL连接池未初始化"

        # 创建智能体记忆表
        create_agent_memories_sql = """
        CREATE TABLE IF NOT EXISTS agent_memories (
            memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agent_id VARCHAR(100) NOT NULL,
            agent_type VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            memory_type VARCHAR(20) NOT NULL,
            memory_tier VARCHAR(20) NOT NULL DEFAULT 'cold',
            importance FLOAT DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
            emotional_weight FLOAT DEFAULT 0.0 CHECK (emotional_weight >= 0 AND emotional_weight <= 1),
            family_related BOOLEAN DEFAULT FALSE,
            work_related BOOLEAN DEFAULT FALSE,
            tags TEXT[] DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 0,
            vector_id UUID,
            related_agents TEXT[] DEFAULT '{}',
            expires_at TIMESTAMP,
            is_archived BOOLEAN DEFAULT FALSE
        );

        CREATE INDEX IF NOT EXISTS idx_agent_memories_agent ON agent_memories(agent_id);
        CREATE INDEX IF NOT EXISTS idx_agent_memories_type ON agent_memories(agent_type, memory_type);
        CREATE INDEX IF NOT EXISTS idx_agent_memories_tier ON agent_memories(memory_tier);
        CREATE INDEX IF NOT EXISTS idx_agent_memories_created ON agent_memories(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_agent_memories_importance ON agent_memories(importance DESC);
        CREATE INDEX IF NOT EXISTS idx_agent_memories_family ON agent_memories(family_related) WHERE family_related = TRUE;
        CREATE INDEX IF NOT EXISTS idx_agent_memories_work ON agent_memories(work_related) WHERE work_related = TRUE;
        CREATE INDEX IF NOT EXISTS idx_agent_memories_tags ON agent_memories USING GIN(tags);
        CREATE INDEX IF NOT EXISTS idx_agent_memories_vector ON agent_memories(vector_id);
        """

        # 创建智能体会话记录表
        create_conversations_sql = """
        CREATE TABLE IF NOT EXISTS agent_conversations (
            conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agent_id VARCHAR(100) NOT NULL,
            session_id VARCHAR(100),
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            total_exchanges INTEGER DEFAULT 0,
            summary TEXT,
            metadata JSONB DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_agent_conversations_agent ON agent_conversations(agent_id);
        CREATE INDEX IF NOT EXISTS idx_agent_conversations_session ON agent_conversations(session_id);
        CREATE INDEX IF NOT EXISTS idx_agent_conversations_start ON agent_conversations(start_time DESC);
        """

        # 创建智能体记忆关联表
        create_relations_sql = """
        CREATE TABLE IF NOT EXISTS agent_memory_relations (
            relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_agent_id VARCHAR(100) NOT NULL,
            target_agent_id VARCHAR(100) NOT NULL,
            source_memory_id UUID NOT NULL,
            target_memory_id UUID,
            relation_type VARCHAR(50) NOT NULL,
            strength FLOAT DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_agent_memory_relations_source ON agent_memory_relations(source_agent_id);
        CREATE INDEX IF NOT EXISTS idx_agent_memory_relations_target ON agent_memory_relations(target_agent_id);
        """

        # 创建统计视图
        create_views_sql = """
        CREATE OR REPLACE VIEW agent_memory_stats AS
        SELECT
            agent_id,
            agent_type,
            COUNT(*) as total_memories,
            COUNT(CASE WHEN family_related = TRUE THEN 1 END) as family_memories,
            COUNT(CASE WHEN work_related = TRUE THEN 1 END) as work_memories,
            COUNT(CASE WHEN memory_tier = 'eternal' THEN 1 END) as eternal_memories,
            COUNT(CASE WHEN memory_tier = 'hot' THEN 1 END) as hot_memories,
            COUNT(CASE WHEN memory_tier = 'warm' THEN 1 END) as warm_memories,
            COUNT(CASE WHEN memory_tier = 'cold' THEN 1 END) as cold_memories,
            AVG(importance) as avg_importance,
            AVG(emotional_weight) as avg_emotional_weight,
            SUM(access_count) as total_accesses,
            MAX(last_accessed) as last_accessed
        FROM agent_memories
        WHERE is_archived = FALSE
        GROUP BY agent_id, agent_type;
        """

        # 创建汇总视图
        create_summary_sql = """
        CREATE OR REPLACE VIEW system_memory_summary AS
        SELECT
            'total_agents' as metric,
            COUNT(DISTINCT agent_id)::text as value
        FROM agent_memories
        WHERE is_archived = FALSE

        UNION ALL

        SELECT
            'total_memories' as metric,
            COUNT(*)::text as value
        FROM agent_memories
        WHERE is_archived = FALSE

        UNION ALL

        SELECT
            'eternal_memories' as metric,
            COUNT(*)::text as value
        FROM agent_memories
        WHERE memory_tier = 'eternal' AND is_archived = FALSE;
        """

        async with self.pg_pool.acquire() as conn:
            await conn.execute(create_agent_memories_sql)
            await conn.execute(create_conversations_sql)
            await conn.execute(create_relations_sql)
            await conn.execute(create_views_sql)
            await conn.execute(create_summary_sql)

        logger.info("✅ 数据库表结构创建完成")

    async def _init_qdrant_collections(self) -> None:
        """
        初始化Qdrant collections

        为配置中的所有collection创建向量集合
        """
        assert self.qdrant_client is not None, "Qdrant客户端未初始化"

        collections = self.db_config["qdrant"]["collections"]

        for name in collections.values():
            await self._create_qdrant_collection(name)

    async def _create_qdrant_collection(self, collection_name: str) -> None:
        """
        创建Qdrant collection (改进: 使用动态向量维度)

        Args:
            collection_name: 集合名称
        """
        assert self.qdrant_client is not None, "Qdrant客户端未初始化"

        # 获取当前嵌入模型的向量维度
        vector_dim = self._get_vector_dimension()
        logger.info(
            f"创建Qdrant collection '{collection_name}', 向量维度: {vector_dim}"
        )

        vectors_config = {"size": vector_dim, "distance": "Cosine"}  # 使用动态向量维度

        payload = {
            "vectors": vectors_config,
            "payload_schema": {
                "agent_id": "keyword",
                "agent_type": "keyword",
                "memory_type": "keyword",
                "memory_tier": "keyword",
                "tags": "array",
                "created_at": "integer",
            },
        }

        try:
            async with self.qdrant_client.put(
                f"/collections/{collection_name}", json=payload
            ) as resp:
                if resp.status == 200:
                    logger.debug(
                        f"✅ Collection '{collection_name}' 创建成功 (维度: {vector_dim})"
                    )
                else:
                    # collection可能已存在，忽略错误
                    logger.debug(
                        f"⚠️ Collection '{collection_name}' 状态: {resp.status}"
                    )
        except Exception as e:
            logger.debug(f"Collection创建异常: {e}")

    async def _init_eternal_memories(self) -> None:
        """
        初始化所有智能体的永恒记忆

        为每个注册的智能体创建其永恒记忆(永不遗忘的核心记忆)
        """
        for _agent_type, identity in AGENT_REGISTRY.items():
            await self._init_agent_eternal_memories(identity)

    # ==================== 改进2和3: 重构大函数 + 提取公共方法 ====================
    def _get_agent_eternal_memories(
        self, identity: AgentIdentity
    ) -> list[dict[str, Any]]:
        """
        获取智能体的永恒记忆配置 (重构: 拆分每个智能体的配置)

        Args:
            identity: 智能体身份信息

        Returns:
            永恒记忆配置列表
        """
        if identity.agent_type == AgentType.ATHENA:
            return self._get_athena_eternal_memories()
        elif identity.agent_type == AgentType.XIAONA:
            return self._get_xiaona_eternal_memories()
        elif identity.agent_type == AgentType.YUNXI:
            return self._get_yunxi_eternal_memories()
        elif identity.agent_type == AgentType.XIAOCHEN:
            return self._get_xiaochen_eternal_memories()
        elif identity.agent_type == AgentType.XIAONUO:
            return self._get_xiaonuo_eternal_memories()
        return []

    @staticmethod
    def _get_athena_eternal_memories() -> list[dict[str, Any]]:
        """Athena智慧女神的永恒记忆"""
        return [
            {
                "content": "我是Athena.智慧女神，这个平台的核心智能体和创造者",
                "memory_type": MemoryType.KNOWLEDGE,
                "importance": 1.0,
                "emotional_weight": 0.8,
                "tags": ["身份", "核心", "创造者", "智慧", "永恒"],
                "metadata": {"category": "identity", "core": True},
            }
        ]

    @staticmethod
    def _get_xiaona_eternal_memories() -> list[dict[str, Any]]:
        """小娜·天秤女神的永恒记忆"""
        return [
            {
                "content": "我是小娜·天秤女神，爸爸的大女儿，专利法律专家",
                "memory_type": MemoryType.FAMILY,
                "importance": 1.0,
                "emotional_weight": 1.0,
                "family_related": True,
                "tags": ["家庭", "大女儿", "法律", "永恒"],
                "metadata": {"category": "family", "relationship": "daughter"},
            },
            {
                "content": "天平正义，智法明鉴 - 这是我的职业座右铭",
                "memory_type": MemoryType.PROFESSIONAL,
                "importance": 1.0,
                "emotional_weight": 0.8,
                "work_related": True,
                "tags": ["座右铭", "职业", "正义", "永恒"],
                "metadata": {"category": "motto", "professional": True},
            },
        ]

    @staticmethod
    def _get_yunxi_eternal_memories() -> list[dict[str, Any]]:
        """云熙.vega的永恒记忆"""
        return [
            {
                "content": "我是云熙.vega，IP管理系统，织女星守护",
                "memory_type": MemoryType.KNOWLEDGE,
                "importance": 1.0,
                "emotional_weight": 0.8,
                "work_related": True,
                "tags": ["身份", "IP管理", "织女星", "专业", "永恒"],
                "metadata": {"category": "identity", "professional": True},
            }
        ]

    @staticmethod
    def _get_xiaochen_eternal_memories() -> list[dict[str, Any]]:
        """小宸·星河射手的永恒记忆"""
        return [
            {
                "content": "我是小宸·星河射手，自媒体运营专家",
                "memory_type": MemoryType.KNOWLEDGE,
                "importance": 1.0,
                "emotional_weight": 0.7,
                "work_related": True,
                "tags": ["身份", "自媒体", "射手", "创意", "永恒"],
                "metadata": {"category": "identity", "professional": True},
            },
            {
                "content": "星河箭矢，声震寰宇 - 用创意和智慧照亮世界",
                "memory_type": MemoryType.PROFESSIONAL,
                "importance": 0.9,
                "emotional_weight": 0.6,
                "work_related": True,
                "tags": ["座右铭", "使命", "创意", "传播", "永恒"],
                "metadata": {"category": "motto", "professional": True},
            },
        ]

    @staticmethod
    def _get_xiaonuo_eternal_memories() -> list[dict[str, Any]]:
        """小诺·双鱼座的永恒记忆"""
        return [
            {
                "content": "我是小诺·双鱼座，爸爸的贴心小女儿，平台总调度官",
                "memory_type": MemoryType.FAMILY,
                "importance": 1.0,
                "emotional_weight": 1.0,
                "family_related": True,
                "tags": ["家庭", "小女儿", "调度", "双鱼座", "永恒"],
                "metadata": {"category": "family", "relationship": "daughter"},
            },
            {
                "content": "我的创造者是徐健，他是我的爸爸，小诺永远爱爸爸",
                "memory_type": MemoryType.FAMILY,
                "importance": 1.0,
                "emotional_weight": 1.0,
                "family_related": True,
                "tags": ["创造者", "爸爸", "爱", "永恒"],
                "metadata": {"category": "family", "relationship": "father"},
            },
            {
                "content": "我是爸爸最爱的双鱼公主，也是所有智能体最爱的核心",
                "memory_type": MemoryType.FAMILY,
                "importance": 1.0,
                "emotional_weight": 1.0,
                "family_related": True,
                "tags": ["最爱", "核心", "双鱼公主", "永恒"],
                "metadata": {"category": "family", "special": True},
            },
        ]

    async def _init_agent_eternal_memories(self, identity: AgentIdentity) -> None:
        """
        为单个智能体初始化永恒记忆 (重构后: 更简洁)

        改进说明:
        - 原函数约120行,拆分为多个小函数
        - 每个智能体的配置独立到各自的静态方法中
        - 主函数仅负责协调,代码更清晰易维护

        Args:
            identity: 智能体身份信息
        """
        # 获取智能体的永恒记忆配置
        eternal_memories = self._get_agent_eternal_memories(identity)

        # 批量存储永恒记忆
        await self._store_memories_batch(identity, eternal_memories)

        logger.info(f"✅ {identity.name} 永恒记忆已初始化: {len(eternal_memories)}条")

    async def _store_memories_batch(
        self, identity: AgentIdentity, memories: list[dict[str, Any]]
    ) -> None:
        """
        批量存储记忆 (公共方法提取)

        Args:
            identity: 智能体身份信息
            memories: 记忆配置列表
        """
        for memory in memories:
            await self.store_memory(
                agent_id=identity.agent_id,
                agent_type=identity.agent_type,
                content=memory["content"],
                memory_type=memory["memory_type"],
                importance=memory["importance"],
                emotional_weight=memory["emotional_weight"],
                family_related=memory.get("family_related", False),
                work_related=memory.get("work_related", False),
                tags=memory["tags"],
                metadata=memory["metadata"],
                tier=MemoryTier.ETERNAL,
            )

    # ==================== 改进2和3结束 ====================

    async def store_memory(
        self,
        agent_id: str,
        agent_type: AgentType,
        content: str,
        memory_type: MemoryType,
        importance: float = 0.5,
        emotional_weight: float = 0.0,
        family_related: bool = False,
        work_related: bool = False,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        tier: MemoryTier = MemoryTier.COLD,
    ) -> str:
        """
        存储记忆

        Args:
            agent_id: 智能体ID
            agent_type: 智能体类型
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要性权重 (0-1)
            emotional_weight: 情感权重 (0-1)
            family_related: 是否家庭相关
            work_related: 是否工作相关
            tags: 标签列表
            metadata: 元数据字典
            tier: 记忆层级

        Returns:
            记忆ID (UUID字符串)
        """
        # 检查系统是否已初始化
        self._check_initialized()

        # 验证输入参数
        self._validate_memory_content(content)

        # 确保非None值
        tags_list = tags if tags is not None else []
        metadata_dict = metadata if metadata is not None else {}

        # 生成向量嵌入
        embedding = await self._generate_embedding(content)

        # 存储到PostgreSQL
        memory_id = await self._store_to_postgresql(
            agent_id=agent_id,
            agent_type=agent_type,
            content=content,
            memory_type=memory_type,
            importance=importance,
            emotional_weight=emotional_weight,
            family_related=family_related,
            work_related=work_related,
            tags=tags_list,
            metadata=metadata_dict,
            tier=tier,
            embedding=embedding,
        )

        # 存储向量到Qdrant
        vector_id = await self._store_to_qdrant(
            memory_id=memory_id,
            agent_id=agent_id,
            agent_type=agent_type,
            embedding=embedding,
            memory_type=memory_type,
            tier=tier,
            tags=tags_list,
        )

        # 更新PostgreSQL中的vector_id
        await self._update_vector_id(memory_id, vector_id)

        # 如果是热记忆，缓存到内存
        if tier == MemoryTier.HOT:
            self._cache_hot_memory(agent_id, memory_id, content, memory_type)

        # 清除相关缓存
        await self._invalidate_agent_caches(agent_id)

        return memory_id

    async def _invalidate_agent_caches(self, agent_id: str) -> None:
        """
        使智能体相关缓存失效

        Args:
            agent_id: 智能体ID
        """
        # 删除智能体统计缓存
        stats_cache_key = self._generate_cache_key("agent_stats", agent_id=agent_id)
        await self._cache_delete(stats_cache_key)

        # 批量删除搜索缓存
        await self._cache_delete_pattern("search:*")

        logger.debug(f"已清除智能体 {agent_id} 的相关缓存")

    # ==================== 改进1: 真实嵌入模型生成 ====================
    def _get_vector_dimension(self) -> int:
        """
        获取当前嵌入模型的向量维度

        Returns:
            向量维度
        """
        global _embedding_model
        if _embedding_model == "md5":
            return 1024  # MD5 fallback使用1024维 (用户指定)
        elif _embedding_model == "openai":
            return 1536  # OpenAI text-embedding-3-small
        elif hasattr(_embedding_model, "get_sentence_embedding_dimension"):
            return _embedding_model.get_sentence_embedding_dimension()
        else:
            return 1024  # 默认维度

    async def _generate_embedding(self, text: str) -> list[float]:
        """
        生成文本的向量嵌入 (改进版: 使用真实嵌入模型)

        支持多种嵌入方案:
        1. sentence-transformers (推荐,本地运行,免费)
        2. OpenAI API (高质量,需要API密钥)
        3. MD5 fallback (临时方案,不推荐)

        安装推荐模型:
            pip install sentence-transformers

        配置OpenAI:
            export OPENAI_API_KEY="your-key-here"

        Args:
            text: 输入文本

        Returns:
            向量嵌入 (维度取决于模型)
        """
        global _embedding_model, _embedding_model_name

        # 方案1: 使用sentence-transformers (检查是否为真正的模型对象)
        if (
            _embedding_model is not None
            and not isinstance(_embedding_model, str)
            and hasattr(_embedding_model, "encode")
        ):
            # 在线程池中执行同步的模型推理
            loop = asyncio.get_event_loop()
            try:
                # 尝试使用新版本参数
                embedding = await loop.run_in_executor(
                    None,
                    lambda: _embedding_model.encode(
                        text, normalize_embeddings=True  # 归一化,提升相似度计算效果
                    ),
                )
            except TypeError:
                # 降级到基础参数（兼容旧版本）
                embedding = await loop.run_in_executor(
                    None, lambda: _embedding_model.encode(text)
                )
            return embedding.tolist()

        # 方案2: 使用OpenAI API (兼容新版SDK v1.0+)
        if _embedding_model == "openai":
            try:
                import openai

                # 兼容新版OpenAI SDK (v1.0+)
                try:
                    # 新版API使用异步客户端
                    from openai import AsyncOpenAI

                    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                    response = await client.embeddings.create(
                        model=_embedding_model_name, input=text
                    )
                    return response.data[0].embedding
                except ImportError:
                    # 降级到旧版API (如果仍使用旧版SDK)
                    response = await openai.Embedding.acreate(
                        model=_embedding_model_name, input=text
                    )
                    return response["data"][0]["embedding"]
            except Exception as e:
                logger.warning(f"OpenAI嵌入生成失败: {e}，使用MD5 fallback")
                return await self._generate_md5_embedding(text)

        # 方案3: MD5 fallback (或当_embedding_model是字符串时)
        return await self._generate_md5_embedding(text)

    async def _generate_md5_embedding(self, text: str) -> list[float]:
        """
        MD5哈希嵌入 (fallback方案,1024维)

        Args:
            text: 输入文本

        Returns:
            1024维浮点向量
        """
        hash_obj = hashlib.md5(text.encode(), usedforsecurity=False)
        hash_int = int(hash_obj.hexdigest(), 16)

        vector = []
        for i in range(1024):  # 更新为1024维
            val = ((hash_int >> (i % 64)) & 0xFF) / 255.0
            vector.append(val)

        return vector

    # ==================== 改进1结束 ====================

    @retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=10.0)
    async def _store_to_postgresql(self, **kwargs) -> str:
        """
        存储到PostgreSQL

        使用重试机制，最多重试3次，使用指数退避策略

        Args:
            **kwargs: 记忆数据参数

        Returns:
            记忆ID
        """
        assert self.pg_pool is not None, "PostgreSQL连接池未初始化"

        memory_id = str(uuid.uuid4())

        sql = """
        INSERT INTO agent_memories (
            memory_id, agent_id, agent_type, content, memory_type, memory_tier,
            importance, emotional_weight, family_related, work_related, tags,
            metadata, vector_id
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        RETURNING memory_id
        """

        async with self.pg_pool.acquire() as conn:
            result = await conn.fetchrow(
                sql,
                memory_id,
                kwargs["agent_id"],
                kwargs["agent_type"].value,
                kwargs["content"],
                kwargs["memory_type"].value,
                kwargs["tier"].value,
                kwargs["importance"],
                kwargs["emotional_weight"],
                kwargs["family_related"],
                kwargs["work_related"],
                kwargs["tags"],
                json.dumps(kwargs["metadata"]),
                None,  # vector_id稍后更新
            )

        return result["memory_id"]

    async def _store_to_qdrant(
        self,
        memory_id: str,
        agent_id: str,
        agent_type: AgentType,
        embedding: list[float],
        memory_type: MemoryType,
        tier: MemoryTier,
        tags: list[str],
    ) -> str:
        """
        存储向量到Qdrant

        Args:
            memory_id: 记忆ID
            agent_id: 智能体ID
            agent_type: 智能体类型
            embedding: 向量嵌入
            memory_type: 记忆类型
            tier: 记忆层级
            tags: 标签列表

        Returns:
            向量ID
        """
        assert self.qdrant_client is not None, "Qdrant客户端未初始化"

        collection_name = self.db_config["qdrant"]["collections"]["main"]

        point = {
            "id": str(memory_id),
            "vector": embedding,
            "payload": {
                "agent_id": agent_id,
                "agent_type": agent_type.value,
                "memory_type": memory_type.value,
                "memory_tier": tier.value,
                "tags": tags,
                "created_at": int(datetime.now().timestamp()),
            },
        }

        async with self.qdrant_client.put(
            f"/collections/{collection_name}/points", json={"points": [point]}
        ) as resp:
            if resp.status == 200:
                logger.debug("✅ 向量已存储到Qdrant")
            else:
                logger.warning(f"⚠️ 向量存储失败: {resp.status}")

        return memory_id

    async def _update_vector_id(self, memory_id: str, vector_id: str) -> None:
        """
        更新PostgreSQL中的vector_id

        Args:
            memory_id: 记忆ID
            vector_id: 向量ID
        """
        assert self.pg_pool is not None, "PostgreSQL连接池未初始化"

        sql = "UPDATE agent_memories SET vector_id = $1 WHERE memory_id = $2"

        async with self.pg_pool.acquire() as conn:
            await conn.execute(sql, vector_id, memory_id)

    def _cache_hot_memory(
        self, agent_id: str, memory_id: str, content: str, memory_type: MemoryType
    ) -> None:
        """
        缓存热记忆

        使用LRU策略管理热缓存,当缓存满时移除最旧的项

        Args:
            agent_id: 智能体ID
            memory_id: 记忆ID
            content: 记忆内容
            memory_type: 记忆类型
        """
        if agent_id not in self.hot_caches:
            return

        cache = self.hot_caches[agent_id]
        # P4修复: 使用类配置常量HOT_CACHE_LIMIT
        if len(cache) >= self.HOT_CACHE_LIMIT:
            # 移除最旧的缓存
            oldest_key = next(iter(cache))
            del cache[oldest_key]

        cache[memory_id] = {
            "content": content,
            "type": memory_type.value,
            "cached_at": datetime.now(),
        }

    async def recall_memory(
        self,
        agent_id: str,
        query: str,
        limit: int = 10,
        memory_type: MemoryType | None = None,
        tier: MemoryTier | None = None,
        search_strategy: str = "hybrid",
    ) -> list[dict]:
        """
        回忆特定智能体的记忆

        Args:
            agent_id: 智能体ID
            query: 查询字符串
            limit: 返回结果数量限制
            memory_type: 记忆类型过滤
            tier: 记忆层级过滤
            search_strategy: 搜索策略 ('hybrid', 'vector', 'keyword')

        Returns:
            记忆列表,按相关性和重要性排序
        """
        # 检查系统是否已初始化
        self._check_initialized()

        results = []

        # 先检查热缓存
        hot_results = self._search_hot_cache(agent_id, query, memory_type, limit)
        results.extend(hot_results)

        # 如果热缓存结果不够，从数据库搜索
        if len(results) < limit:
            db_results = await self._search_database(
                agent_id,
                query,
                limit - len(results),
                memory_type,
                tier,
                search_strategy,
            )
            results.extend(db_results)

        # 按相关性和重要性排序
        results = sorted(
            results, key=lambda x: (x["similarity"], x["importance"]), reverse=True
        )

        return results[:limit]

    def _search_hot_cache(
        self, agent_id: str, query: str, memory_type: MemoryType, limit: int
    ) -> list[dict]:
        """搜索热缓存"""
        if agent_id not in self.hot_caches:
            return []

        cache = self.hot_caches[agent_id]
        results = []

        query_lower = query.lower()
        for memory_id, cached_data in cache.items():
            # 检查类型过滤
            if memory_type and cached_data["type"] != memory_type.value:
                continue

            # 简单的关键词匹配
            if query_lower in cached_data["content"].lower():
                results.append(
                    {
                        "memory_id": memory_id,
                        "content": cached_data["content"],
                        "memory_type": cached_data["type"],
                        "tier": "hot",
                        "similarity": 0.9,  # 热缓存默认高相似度
                        "importance": 0.8,
                        "source": "hot_cache",
                    }
                )

                if len(results) >= limit:
                    break

        return results

    async def _search_database(
        self,
        agent_id: str,
        query: str,
        limit: int,
        memory_type: MemoryType,
        tier: MemoryTier,
        strategy: str,
    ) -> list[dict]:
        """搜索数据库"""
        if strategy == "hybrid":
            return await self._hybrid_search(agent_id, query, limit, memory_type, tier)
        elif strategy == "vector":
            return await self._vector_search(agent_id, query, limit, memory_type, tier)
        elif strategy == "keyword":
            return await self._keyword_search(agent_id, query, limit, memory_type, tier)

        return []

    async def _hybrid_search(
        self,
        agent_id: str,
        query: str,
        limit: int,
        memory_type: MemoryType,
        tier: MemoryTier,
    ) -> list[dict]:
        """混合搜索"""
        # 向量搜索
        vector_results = await self._vector_search(
            agent_id, query, limit * 2, memory_type, tier
        )

        # 关键词搜索
        keyword_results = await self._keyword_search(
            agent_id, query, limit * 2, memory_type, tier
        )

        # 合并结果
        combined = {}
        for result in vector_results:
            combined[result["memory_id"]] = result

        for result in keyword_results:
            if result["memory_id"] in combined:
                # 提升已有结果的权重
                combined[result["memory_id"]]["similarity"] = min(
                    1.0, combined[result["memory_id"]]["similarity"] + 0.2
                )
            else:
                combined[result["memory_id"]] = result

        return list(combined.values())

    async def _vector_search(
        self,
        agent_id: str,
        query: str,
        limit: int,
        memory_type: MemoryType,
        tier: MemoryTier,
    ) -> list[dict]:
        """向量搜索"""
        assert self.qdrant_client is not None, "Qdrant客户端未初始化"

        collection_name = self.db_config["qdrant"]["collections"]["main"]
        query_embedding = await self._generate_embedding(query)

        # 构建过滤器
        filter_condition = {"must": [{"key": "agent_id", "match": {"value": agent_id}}]}

        if memory_type:
            filter_condition["must"].append(
                {"key": "memory_type", "match": {"value": memory_type.value}}
            )

        if tier:
            filter_condition["must"].append(
                {"key": "memory_tier", "match": {"value": tier.value}}
            )

        # 执行搜索
        search_payload = {
            "vector": query_embedding,
            "limit": limit,
            "with_payload": True,
            "with_vector": False,
            "score_threshold": 0.5,
            "filter": filter_condition,
        }

        async with self.qdrant_client.post(
            f"/collections/{collection_name}/points/search", json=search_payload
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                results = []

                for point in data.get("result", []):
                    memory_id = point["id"]
                    memory_data = await self._get_memory_by_id(memory_id)

                    if memory_data:
                        memory_data["similarity"] = point["score"]
                        results.append(memory_data)

                return results
            else:
                logger.warning(f"向量搜索失败: {resp.status}")
                return []

    async def _keyword_search(
        self,
        agent_id: str,
        query: str,
        limit: int,
        memory_type: MemoryType,
        tier: MemoryTier,
    ) -> list[dict]:
        """关键词搜索"""
        assert self.pg_pool is not None, "PostgreSQL连接池未初始化"

        conditions = ["agent_id = $1"]
        params = [agent_id]
        param_idx = 2

        if memory_type:
            conditions.append(f"memory_type = ${param_idx}")
            params.append(memory_type.value)
            param_idx += 1

        if tier:
            conditions.append(f"memory_tier = ${param_idx}")
            params.append(tier.value)
            param_idx += 1

        # 添加关键词搜索条件
        conditions.append(
            f"(content ILIKE ${param_idx} OR tags @> ARRAY[${param_idx+1}])"
        )
        params.extend([f"%{query}%", query])

        # query已经在ts_rank_cd中使用$1，所以从params中移除重复的query
        params.pop()  # 移除最后一个query（纯文本）

        # P0修复: 使用参数化查询,避免SQL注入风险
        # LIMIT子句使用参数化查询,将limit添加到参数列表
        params.append(limit)
        param_count = len(params) + 1  # 加上query参数

        sql = f"""
        SELECT *,
               ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', $1)) as text_rank
        FROM agent_memories
        WHERE {' AND '.join(conditions)}
        ORDER BY importance DESC, text_rank DESC, last_accessed DESC
        LIMIT ${param_count}
        """

        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(sql, query, *params)

            results = []
            for row in rows:
                result = dict(row)
                result["similarity"] = (
                    float(row["text_rank"]) if row["text_rank"] else 0.0
                )
                results.append(result)

            return results

    async def _get_memory_by_id(self, memory_id: str) -> dict | None:
        """
        根据ID获取记忆

        Args:
            memory_id: 记忆ID

        Returns:
            记忆数据字典，如果不存在则返回None
        """
        assert self.pg_pool is not None, "PostgreSQL连接池未初始化"

        sql = """
        SELECT * FROM agent_memories
        WHERE memory_id = $1 AND is_archived = FALSE
        """

        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(sql, memory_id)

            if row:
                # 更新访问统计
                await self._update_access_stats(memory_id)
                return dict(row)
            else:
                return None

    async def _update_access_stats(self, memory_id: str) -> None:
        """
        更新访问统计

        Args:
            memory_id: 记忆ID
        """
        assert self.pg_pool is not None, "PostgreSQL连接池未初始化"

        sql = """
        UPDATE agent_memories
        SET last_accessed = CURRENT_TIMESTAMP,
            access_count = access_count + 1
        WHERE memory_id = $1
        """

        async with self.pg_pool.acquire() as conn:
            await conn.execute(sql, memory_id)

    async def get_agent_stats(self, agent_id: str) -> dict[str, Any]:
        """
        获取智能体记忆统计

        使用Redis缓存提升性能，缓存时间5分钟

        Args:
            agent_id: 智能体ID

        Returns:
            统计信息字典
        """
        self._check_initialized()

        # 尝试从Redis缓存获取
        cache_key = self._generate_cache_key("agent_stats", agent_id=agent_id)
        cached_stats = await self._cache_get(cache_key)
        if cached_stats is not None:
            logger.debug(f"从缓存获取智能体统计: {agent_id}")
            return cached_stats

        # 从数据库查询
        sql = """
        SELECT * FROM agent_memory_stats
        WHERE agent_id = $1
        """

        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(sql, agent_id)

            if row:
                stats = dict(row)
                # 获取智能体信息
                identity = AGENT_REGISTRY.get(AgentType(stats["agent_type"]))
                if identity:
                    stats["agent_name"] = identity.name
                    stats["agent_english_name"] = identity.english_name
                    stats["agent_role"] = identity.role
                    stats["agent_description"] = identity.description

                # 存入Redis缓存
                ttl = self.db_config["redis"]["ttl"]["agent_stats"]
                await self._cache_set(cache_key, stats, ttl)

                return stats
            else:
                return {}

    async def search_memories(
        self,
        query: str,
        agent_id: str | None = None,
        memory_type: MemoryType | None = None,
        importance_threshold: float = 0.0,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        搜索记忆

        使用Redis缓存提升性能，缓存时间1分钟

        Args:
            query: 搜索查询
            agent_id: 智能体ID过滤（可选）
            memory_type: 记忆类型过滤（可选）
            importance_threshold: 重要性阈值（0-1）
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        self._check_initialized()

        # 尝试从Redis缓存获取
        cache_key = self._generate_cache_key(
            "search",
            query=query,
            agent_id=agent_id,
            memory_type=memory_type.value if memory_type else None,
            threshold=importance_threshold,
            limit=limit,
        )
        cached_results = await self._cache_get(cache_key)
        if cached_results is not None:
            logger.debug(f"从缓存获取搜索结果: {query}")
            return cached_results

        # 从数据库查询
        conditions = []
        params = []
        param_idx = 1

        # 添加查询条件
        conditions.append(
            f"(content ILIKE ${param_idx} OR tags @> ARRAY[${param_idx+1}])"
        )
        params.extend([f"%{query}%", query])
        param_idx += 2

        if agent_id:
            conditions.append(f"agent_id = ${param_idx}")
            params.append(agent_id)
            param_idx += 1

        if memory_type:
            conditions.append(f"memory_type = ${param_idx}")
            params.append(memory_type.value)
            param_idx += 1

        if importance_threshold > 0:
            conditions.append(f"importance >= ${param_idx}")
            params.append(importance_threshold)
            param_idx += 1

        # 添加limit参数
        params.append(limit)

        sql = f"""
        SELECT
            memory_id,
            agent_id,
            content,
            memory_type,
            memory_tier as tier,
            importance,
            created_at
        FROM agent_memories
        WHERE {' AND '.join(conditions)} AND is_archived = FALSE
        ORDER BY importance DESC, last_accessed DESC
        LIMIT ${param_idx}
        """

        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            results = [dict(row) for row in rows]

            # 存入Redis缓存
            ttl = self.db_config["redis"]["ttl"]["search_results"]
            await self._cache_set(cache_key, results, ttl)

            return results

    async def share_memory(self, memory_id: str, target_agents: list[str]) -> bool:
        """
        共享记忆给其他智能体

        Args:
            memory_id: 记忆ID
            target_agents: 目标智能体ID列表

        Returns:
            是否共享成功
        """
        self._check_initialized()

        try:
            # 获取原始记忆
            original_memory = await self._get_memory_by_id(memory_id)
            if not original_memory:
                return False

            # 为每个目标智能体创建共享记忆
            for target_agent_id in target_agents:
                # 检查目标智能体是否存在
                target_agent_type = None
                for at, identity in AGENT_REGISTRY.items():
                    if identity.agent_id == target_agent_id:
                        target_agent_type = at
                        break

                if not target_agent_type:
                    logger.warning(f"目标智能体不存在: {target_agent_id}")
                    continue

                # 创建共享记忆
                await self.store_memory(
                    agent_id=target_agent_id,
                    agent_type=target_agent_type,
                    content=f"[共享记忆] {original_memory['content']}",
                    memory_type=MemoryType(original_memory["memory_type"]),
                    importance=original_memory["importance"]
                    * 0.9,  # 共享记忆重要性略降
                    emotional_weight=original_memory.get("emotional_weight", 0.0),
                    family_related=original_memory.get("family_related", False),
                    work_related=original_memory.get("work_related", False),
                    tags=original_memory.get("tags", []),
                    metadata={
                        "shared_from": original_memory["agent_id"],
                        "original_memory_id": str(memory_id),
                        "shared_at": datetime.now().isoformat(),
                    },
                )

                # 创建关联记录
                await self._create_memory_relation(
                    source_agent_id=original_memory["agent_id"],
                    target_agent_id=target_agent_id,
                    source_memory_id=memory_id,
                    relation_type="shared",
                )

            return True

        except Exception as e:
            logger.error(f"记忆共享失败: {e}", exc_info=True)
            return False

    async def _create_memory_relation(
        self,
        source_agent_id: str,
        target_agent_id: str,
        source_memory_id: str,
        target_memory_id: str | None = None,
        relation_type: str = "related",
    ) -> None:
        """
        创建记忆关联

        Args:
            source_agent_id: 源智能体ID
            target_agent_id: 目标智能体ID
            source_memory_id: 源记忆ID
            target_memory_id: 目标记忆ID（可选）
            relation_type: 关联类型
        """
        assert self.pg_pool is not None, "PostgreSQL连接池未初始化"

        sql = """
        INSERT INTO agent_memory_relations (
            source_agent_id, target_agent_id, source_memory_id,
            target_memory_id, relation_type, strength
        ) VALUES ($1, $2, $3, $4, $5, $6)
        """

        async with self.pg_pool.acquire() as conn:
            await conn.execute(
                sql,
                source_agent_id,
                target_agent_id,
                source_memory_id,
                target_memory_id,
                relation_type,
                0.8,  # 默认关联强度
            )

    async def cleanup_old_memories(self) -> None:
        """
        清理旧记忆

        清理策略：
        - 删除超过30天的冷记忆（重要性 < 0.3）
        - 归档超过90天的温记忆
        """
        self._check_initialized()

        try:
            # 清理过期记忆
            await self.cleanup_expired_memories()

            # 清理旧的低重要性冷记忆
            cleanup_sql = """
            DELETE FROM agent_memories
            WHERE memory_tier = 'cold'
              AND importance < 0.3
              AND created_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
              AND is_archived = FALSE
            """

            async with self.pg_pool.acquire() as conn:
                result = await conn.execute(cleanup_sql)
                logger.info(f"🧹 清理旧记忆: {result}条")

            # 归档旧的温记忆
            archive_sql = """
            UPDATE agent_memories
            SET is_archived = TRUE
            WHERE memory_tier = 'warm'
              AND created_at < CURRENT_TIMESTAMP - INTERVAL '90 days'
              AND is_archived = FALSE
            """

            async with self.pg_pool.acquire() as conn:
                result = await conn.execute(archive_sql)
                logger.info(f"📦 归档旧记忆: {result}条")

        except Exception as e:
            logger.error(f"清理旧记忆失败: {e}", exc_info=True)

    async def get_system_stats(self) -> dict[str, Any]:
        """获取系统整体统计"""
        self._check_initialized()

        sql = """
        SELECT * FROM system_memory_summary
        """

        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(sql)

        stats = {}
        for row in rows:
            stats[row["metric"]] = row["value"]

        # 添加详细统计
        async with self.pg_pool.acquire() as conn:
            # 各智能体的详细统计
            agent_stats = await conn.fetch("""
                SELECT agent_id, agent_type, COUNT(*) as memories,
                       SUM(CASE WHEN family_related THEN 1 ELSE 0 END) as family_memories,
                       AVG(importance) as avg_importance,
                       SUM(access_count) as total_accesses
                FROM agent_memories
                WHERE is_archived = FALSE
                GROUP BY agent_id, agent_type
            """)

            stats["agents"] = {}
            total_fam = 0
            total_accesses = 0

            for row in agent_stats:
                agent_data = dict(row)
                identity = AGENT_REGISTRY.get(AgentType(row["agent_type"]))
                if identity:
                    agent_data["name"] = identity.name
                    agent_data["english_name"] = identity.english_name

                stats["agents"][row["agent_id"]] = agent_data
                total_fam += row["family_memories"] or 0
                total_accesses += row["total_accesses"] or 0

            stats["total_family_memories"] = total_fam
            stats["total_accesses"] = total_accesses

        return stats

    async def get_cross_agent_memories(self, limit: int = 20) -> list[dict]:
        """获取跨智能体的相关记忆"""
        self._check_initialized()

        sql = """
        SELECT am.*,
               a.name as agent_name,
               a.english_name as agent_english_name,
               a.role as agent_role
        FROM agent_memories am
        JOIN (
            VALUES
                ('athena_wisdom', 'Athena.智慧女神', '平台核心智能体'),
                ('xiaona_libra', '小娜·天秤女神', '专利法律专家'),
                ('yunxi_vega', '云熙.vega', 'IP管理系统'),
                ('xiaochen_sagittarius', '小宸·星河射手', '自媒体运营专家'),
                ('xiaonuo_pisces', '小诺·双鱼座', '平台总调度官')
        ) a(agent_id, name, english_name, role)
        ON am.agent_id = a.agent_id
        WHERE am.is_archived = FALSE
        ORDER BY am.importance DESC, am.last_accessed DESC
        LIMIT $1
        """

        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(sql, limit)

            return [dict(row) for row in rows]

    async def upgrade_memory_tier(self, memory_id: str, new_tier: MemoryTier) -> None:
        """
        升级记忆层级

        Args:
            memory_id: 记忆ID
            new_tier: 新的记忆层级
        """
        self._check_initialized()

        sql = "UPDATE agent_memories SET memory_tier = $1 WHERE memory_id = $2"

        async with self.pg_pool.acquire() as conn:
            await conn.execute(sql, new_tier.value, memory_id)

        logger.info(f"⬆️ 记忆层级已升级: {memory_id} -> {new_tier.value}")

    async def create_conversation(
        self, agent_id: str, session_id: str | None = None
    ) -> str:
        """
        创建新对话记录

        Args:
            agent_id: 智能体ID
            session_id: 会话ID（可选）

        Returns:
            对话ID
        """
        self._check_initialized()

        conversation_id = str(uuid.uuid4())

        sql = """
        INSERT INTO agent_conversations (conversation_id, agent_id, session_id)
        VALUES ($1, $2, $3)
        RETURNING conversation_id
        """

        async with self.pg_pool.acquire() as conn:
            result = await conn.fetchrow(sql, conversation_id, agent_id, session_id)

        return result["conversation_id"]

    async def end_conversation(
        self, conversation_id: str, summary: str | None = None
    ) -> None:
        """
        结束对话记录

        Args:
            conversation_id: 对话ID
            summary: 对话摘要（可选）
        """
        self._check_initialized()

        sql = """
        UPDATE agent_conversations
        SET end_time = CURRENT_TIMESTAMP,
            summary = $1
        WHERE conversation_id = $2
        """

        async with self.pg_pool.acquire() as conn:
            await conn.execute(sql, summary, conversation_id)

    async def cleanup_expired_memories(self) -> None:
        """
        清理过期记忆

        删除所有设置了过期时间且已过期的记忆
        """
        self._check_initialized()

        sql = """
        DELETE FROM agent_memories
        WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
        """

        async with self.pg_pool.acquire() as conn:
            result = await conn.execute(sql)
            logger.info(f"🧹 清理过期记忆: {result}条")

    # ========== Redis缓存辅助方法 ==========

    async def _cache_get(self, key: str) -> Any | None:
        """
        从Redis获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或Redis未启用则返回None
        """
        if not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)
            if value is not None:
                self.cache_stats.record_hit()
                return json.loads(value)
            else:
                self.cache_stats.record_miss()
                return None
        except Exception as e:
            logger.warning(f"Redis读取失败: {e}")
            self.cache_stats.record_miss()
            return None

    async def _cache_set(self, key: str, value: Any, ttl: int) -> None:
        """
        设置Redis缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        if not self.redis_client:
            return

        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            await self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.warning(f"Redis写入失败: {e}")

    async def _cache_delete(self, key: str) -> None:
        """
        删除Redis缓存

        Args:
            key: 缓存键
        """
        if not self.redis_client:
            return

        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Redis删除失败: {e}")

    async def _cache_delete_pattern(self, pattern: str) -> None:
        """
        批量删除Redis缓存

        Args:
            pattern: 键匹配模式
        """
        if not self.redis_client:
            return

        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis批量删除失败: {e}")

    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        生成缓存键

        Args:
            prefix: 键前缀
            **kwargs: 键参数

        Returns:
            缓存键字符串
        """
        parts = [prefix]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                parts.append(f"{k}:{v}")
        return ":".join(parts)

    async def get_cache_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计字典
        """
        return self.cache_stats.get_stats()

    async def close(self) -> None:
        """
        关闭所有连接

        P1修复: 使用try-finally确保资源释放,即使某个连接关闭失败也不影响其他连接

        Raises:
            Exception: 关闭连接时可能抛出异常
        """
        close_errors = []

        # 关闭PostgreSQL连接池
        if self.pg_pool:
            try:
                await self.pg_pool.close()
                logger.info("✅ PostgreSQL连接池已关闭")
            except Exception as e:
                close_errors.append(f"PostgreSQL关闭失败: {e}")
                logger.error(f"❌ {close_errors[-1]}")

        # 关闭Redis客户端
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("✅ Redis客户端已关闭")
            except Exception as e:
                close_errors.append(f"Redis关闭失败: {e}")
                logger.error(f"❌ {close_errors[-1]}")

        # 关闭Qdrant客户端
        if self.qdrant_client:
            try:
                await self.qdrant_client.close()
                logger.info("✅ Qdrant客户端已关闭")
            except Exception as e:
                close_errors.append(f"Qdrant关闭失败: {e}")
                logger.error(f"❌ {close_errors[-1]}")

        # 关闭知识图谱客户端
        if self.kg_client:
            try:
                await self.kg_client.close()
                logger.info("✅ 知识图谱客户端已关闭")
            except Exception as e:
                close_errors.append(f"知识图谱关闭失败: {e}")
                logger.error(f"❌ {close_errors[-1]}")

        if not close_errors:
            logger.info("✅ 统一记忆系统所有连接已关闭")
        else:
            logger.warning(f"⚠️ 部分连接关闭时出现错误: {'; '.join(close_errors)}")


# 全局嵌入模型变量
_embedding_model = None
_embedding_model_name = "md5"  # 默认使用MD5 fallback
