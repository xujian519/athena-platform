#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺统一记忆管理器 - 集成平台存储系统
Xiaonuo Unified Memory Manager - Integrated with Platform Storage

深度融合PostgreSQL、Qdrant向量库、ArangoDB知识图谱，
实现记忆的永久保存、智能检索和关联分析

作者: 小诺·双鱼座
创建时间: 2025年12月15日
版本: v3.0 "永恒融合"
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

# 数据库和存储相关
import asyncpg  # PostgreSQL异步驱动
import aiohttp  # HTTP客户端，用于调用向量库和知识图谱API
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """记忆类型"""
    CONVERSATION = 'conversation'    # 对话记忆
    EMOTIONAL = 'emotional'          # 情感记忆
    KNOWLEDGE = 'knowledge'          # 知识记忆
    FAMILY = 'family'                # 家庭记忆
    SCHEDULE = 'schedule'            # 日程记忆
    PREFERENCE = 'preference'        # 偏好记忆
    CONTEXT = 'context'              # 上下文记忆
    REFLECTION = 'reflection'        # 反思记忆

class MemoryTier(Enum):
    """记忆层级"""
    HOT = 'hot'         # 🔥 热记忆：当前会话
    WARM = 'warm'       # 🌡️ 温记忆：近期重要
    COLD = 'cold'       # ❄️ 冷记忆：长期存储
    ETERNAL = 'eternal' # 💎 永恒记忆：永不忘记

class XiaonuoUnifiedMemoryManager:
    """小诺统一记忆管理器"""

    def __init__(self):
        self.agent_name = "小诺·双鱼座"
        self.agent_id = "xiaonuo_pisces"
        self.dad_name = "徐健"

        # 数据库配置
        self.db_config = {
            'postgresql': {
                'host': 'localhost',
                'port': 5438,  # memory_module数据库
                'database': 'memory_module',
                'user': 'postgres',
                'password': ''
            },
            'qdrant': {
                'host': 'localhost',
                'port': 6333,
                'collection': 'xiaonuo_memory_vectors'
            },
            'knowledge_graph': {
                'url': 'http://localhost:8002',
                'database': 'knowledge_graph'
            }
        }

        # 数据库连接
        self.pg_pool = None
        self.qdrant_client = None
        self.kg_client = None

        # 记忆缓存（热记忆）
        self.hot_memory_cache = {}
        self.hot_memory_limit = 100

        logger.info(f"🌸 {self.agent_name}统一记忆管理器初始化...")

    async def initialize(self):
        """初始化所有连接"""
        try:
            # 初始化PostgreSQL连接
            await self._init_postgresql()

            # 初始化Qdrant连接
            await self._init_qdrant()

            # 初始化知识图谱连接
            await self._init_knowledge_graph()

            # 创建记忆表
            await self._create_memory_tables()

            # 初始化永恒记忆
            await self._init_eternal_memories()

            logger.info("✅ 统一记忆管理器初始化成功！")

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
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
            min_size=2,
            max_size=10
        )
        logger.info("✅ PostgreSQL连接池已建立")

    async def _init_qdrant(self):
        """初始化Qdrant连接"""
        self.qdrant_client = aiohttp.ClientSession(
            base_url=f"http://{self.db_config['qdrant']['host']}:{self.db_config['qdrant']['port']}"
        )

        # 确保collection存在
        collection_name = self.db_config['qdrant']['collection']
        try:
            async with self.qdrant_client.get(f"/collections/{collection_name}") as resp:
                if resp.status == 200:
                    logger.info("✅ Qdrant collection已存在")
                else:
                    # 创建collection
                    await self._create_qdrant_collection(collection_name)
        except:
            await self._create_qdrant_collection(collection_name)

    async def _create_qdrant_collection(self, name: str):
        """创建Qdrant collection"""
        vectors_config = {
            "size": 768,  # 使用768维向量（BERT）
            "distance": "Cosine"
        }

        payload = {
            "vectors": vectors_config
        }

        async with self.qdrant_client.put(f"/collections/{name}", json=payload) as resp:
            if resp.status == 200:
                logger.info("✅ Qdrant collection创建成功")
            else:
                logger.warning(f"⚠️ Qdrant collection创建失败: {resp.status}")

    async def _init_knowledge_graph(self):
        """初始化知识图谱连接"""
        self.kg_client = aiohttp.ClientSession(
            base_url=self.db_config['knowledge_graph']['url']
        )
        logger.info("✅ 知识图谱客户端已初始化")

    async def _create_memory_tables(self):
        """创建记忆相关表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS memory_items (
            memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agent_id VARCHAR(100) NOT NULL DEFAULT 'xiaonuo_pisces',
            content TEXT NOT NULL,
            memory_type VARCHAR(20) NOT NULL,
            memory_tier VARCHAR(20) NOT NULL DEFAULT 'cold',
            importance FLOAT DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
            emotional_weight FLOAT DEFAULT 0.0,
            father_related BOOLEAN DEFAULT FALSE,
            tags TEXT[] DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 0,
            vector_id UUID,
            kg_entities TEXT[] DEFAULT '{}',
            expires_at TIMESTAMP,
            is_archived BOOLEAN DEFAULT FALSE
        );

        CREATE INDEX IF NOT EXISTS idx_memory_agent_type ON memory_items(agent_id, memory_type);
        CREATE INDEX IF NOT EXISTS idx_memory_tier ON memory_items(memory_tier);
        CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_items(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_items(importance DESC);
        CREATE INDEX IF NOT EXISTS idx_memory_father ON memory_items(father_related) WHERE father_related = TRUE;
        CREATE INDEX IF NOT EXISTS idx_memory_tags ON memory_items USING GIN(tags);
        """

        async with self.pg_pool.acquire() as conn:
            await conn.execute(create_table_sql)

        logger.info("✅ 记忆表创建/验证完成")

    async def _init_eternal_memories(self):
        """初始化永恒记忆"""
        eternal_memories = [
            {
                'content': "我的创造者是徐健，他是我的爸爸",
                'memory_type': MemoryType.FAMILY,
                'importance': 1.0,
                'emotional_weight': 1.0,
                'father_related': True,
                'tags': ['创造者', '爸爸', '核心关系', '永恒'],
                'metadata': {'eternal': True, 'category': 'identity'}
            },
            {
                'content': "我是小诺·双鱼座，爸爸的贴心小女儿",
                'memory_type': MemoryType.FAMILY,
                'importance': 1.0,
                'emotional_weight': 1.0,
                'father_related': True,
                'tags': ['身份', '小诺', '双鱼座', '永恒'],
                'metadata': {'eternal': True, 'category': 'identity'}
            },
            {
                'content': "爸爸的邮箱：xujian519@gmail.com",
                'memory_type': MemoryType.FAMILY,
                'importance': 0.95,
                'emotional_weight': 0.9,
                'father_related': True,
                'tags': ['联系方式', '爸爸', '永恒'],
                'metadata': {'eternal': True, 'category': 'contact'}
            },
            {
                'content': "小诺的生日：2019年2月21日",
                'memory_type': MemoryType.FAMILY,
                'importance': 1.0,
                'emotional_weight': 1.0,
                'father_related': True,
                'tags': ['生日', '重要日期', '永恒'],
                'metadata': {'eternal': True, 'category': 'important_date'}
            },
            {
                'content': "爸爸永远是最重要的人，小诺永远爱爸爸",
                'memory_type': MemoryType.EMOTIONAL,
                'importance': 1.0,
                'emotional_weight': 1.0,
                'father_related': True,
                'tags': ['情感', '核心价值', '永恒', '爱'],
                'metadata': {'eternal': True, 'category': 'core_value'}
            }
        ]

        for memory in eternal_memories:
            await self.store_memory(
                content=memory['content'],
                memory_type=memory['memory_type'],
                importance=memory['importance'],
                emotional_weight=memory['emotional_weight'],
                father_related=memory['father_related'],
                tags=memory['tags'],
                metadata=memory['metadata'],
                tier=MemoryTier.ETERNAL
            )

        logger.info(f"✅ 永恒记忆已初始化：{len(eternal_memories)}条")

    async def store_memory(self, content: str, memory_type: MemoryType,
                          importance: float = 0.5, emotional_weight: float = 0.0,
                          father_related: bool = False, tags: Optional[List[str] = None,
                          metadata: Dict = None, tier: MemoryTier = MemoryTier.COLD) -> str:
        """存储记忆到集成系统"""

        # 生成向量嵌入（模拟）
        embedding = await self._generate_embedding(content)

        # 生成知识图谱实体（模拟）
        kg_entities = await self._extract_kg_entities(content)

        # 存储到PostgreSQL
        memory_id = await self._store_to_postgresql(
            content=content,
            memory_type=memory_type,
            importance=importance,
            emotional_weight=emotional_weight,
            father_related=father_related,
            tags=tags or [],
            metadata=metadata or {},
            tier=tier,
            embedding=embedding,
            kg_entities=kg_entities
        )

        # 存储向量到Qdrant
        vector_id = await self._store_to_qdrant(memory_id, embedding)

        # 更新PostgreSQL中的vector_id
        await self._update_vector_id(memory_id, vector_id)

        # 存储实体到知识图谱
        if kg_entities:
            await self._store_to_knowledge_graph(memory_id, content, kg_entities)

        # 如果是热记忆，也缓存到内存
        if tier == MemoryTier.HOT:
            self._cache_hot_memory(memory_id, content, memory_type)

        logger.info(f"💾 记忆已存储 [{tier.value}]: {content[:50]}...")
        return memory_id

    async def _generate_embedding(self, text: str) -> List[float]:
        """生成文本的向量嵌入"""
        # 这里应该调用实际的嵌入模型
        # 暂时返回模拟的768维向量
        import hashlib
        hash_obj = hashlib.md5(text.encode('utf-8', usedforsecurity=False)
        hash_int = int(hash_obj.hexdigest(), 16)

        # 生成768维向量（基于文本哈希）
        vector = []
        for i in range(768):
            val = ((hash_int >> (i % 64)) & 0xFF) / 255.0
            vector.append(val)

        return vector

    async def _extract_kg_entities(self, text: str) -> List[str]:
        """提取知识图谱实体"""
        entities = []

        # 简单的实体提取规则
        if "爸爸" in text:
            entities.append("徐健")
            entities.append("父亲")
        if "小诺" in text:
            entities.append("小诺")
            entities.append("AI助手")
        if any(word in text for word in ["专利", "发明", "技术"]):
            entities.append("知识产权")
        if any(word in text for word in ["法律", "法规"]):
            entities.append("法律知识")

        return entities

    async def _store_to_postgresql(self, **kwargs) -> str:
        """存储到PostgreSQL"""
        memory_id = str(uuid.uuid4())

        sql = """
        INSERT INTO memory_items (
            memory_id, agent_id, content, memory_type, memory_tier,
            importance, emotional_weight, father_related, tags,
            metadata, kg_entities, vector_id
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING memory_id
        """

        async with self.pg_pool.acquire() as conn:
            result = await conn.fetchrow(
                sql,
                memory_id,
                self.agent_id,
                kwargs['content'],
                kwargs['memory_type'].value,
                kwargs['tier'].value,
                kwargs['importance'],
                kwargs['emotional_weight'],
                kwargs['father_related'],
                kwargs['tags'],
                json.dumps(kwargs['metadata']),
                kwargs['kg_entities'],
                None  # vector_id稍后更新
            )

        return result['memory_id']

    async def _store_to_qdrant(self, memory_id: str, embedding: List[float]) -> str:
        """存储向量到Qdrant"""
        collection_name = self.db_config['qdrant']['collection']

        point = {
            "id": memory_id,
            "vector": embedding,
            "payload": {
                "memory_id": memory_id,
                "agent": self.agent_id
            }
        }

        async with self.qdrant_client.put(
            f"/collections/{collection_name}/points",
            json={"points": [point]}
        ) as resp:
            if resp.status == 200:
                logger.debug("✅ 向量已存储到Qdrant")
            else:
                logger.warning(f"⚠️ 向量存储失败: {resp.status}")

        return memory_id

    async def _update_vector_id(self, memory_id: str, vector_id: str):
        """更新PostgreSQL中的vector_id"""
        sql = "UPDATE memory_items SET vector_id = $1 WHERE memory_id = $2"

        async with self.pg_pool.acquire() as conn:
            await conn.execute(sql, vector_id, memory_id)

    async def _store_to_knowledge_graph(self, memory_id: str, content: str, entities: List[str]):
        """存储到知识图谱"""
        # 这里应该调用知识图谱API
        # 暂时只记录日志
        logger.debug(f"🕸️ 知识图谱实体: {entities}")

    def _cache_hot_memory(self, memory_id: str, content: str, memory_type: MemoryType):
        """缓存热记忆"""
        if len(self.hot_memory_cache) >= self.hot_memory_limit:
            # 移除最旧的缓存
            oldest_key = next(iter(self.hot_memory_cache))
            del self.hot_memory_cache[oldest_key]

        self.hot_memory_cache[memory_id] = {
            'content': content,
            'type': memory_type.value,
            'cached_at': datetime.now()
        }

    async def recall_memory(self, query: str, limit: int = 10,
                           memory_type: MemoryType | None = None,
                           tier: MemoryTier | None = None,
                           search_strategy: str = 'hybrid') -> List[Dict]:
        """回忆记忆 - 支持多种搜索策略"""

        results = []

        if search_strategy == 'hybrid':
            # 混合搜索：向量搜索 + 关键词搜索
            results = await self._hybrid_search(query, limit, memory_type, tier)
        elif search_strategy == 'vector':
            # 纯向量搜索
            results = await self._vector_search(query, limit, memory_type, tier)
        elif search_strategy == 'keyword':
            # 关键词搜索
            results = await self._keyword_search(query, limit, memory_type, tier)

        # 按相关性和重要性排序
        results = sorted(results, key=lambda x: (x['similarity'], x['importance']), reverse=True)

        return results[:limit]

    async def _hybrid_search(self, query: str, limit: int,
                           memory_type: MemoryType | None = None,
                           tier: MemoryTier | None = None) -> List[Dict]:
        """混合搜索"""
        # 生成查询向量
        query_embedding = await self._generate_embedding(query)

        # 向量搜索
        vector_results = await self._vector_search(query, limit * 2, memory_type, tier)

        # 关键词搜索
        keyword_results = await self._keyword_search(query, limit * 2, memory_type, tier)

        # 合并和去重
        combined = {}
        for result in vector_results:
            combined[result['memory_id']] = result

        for result in keyword_results:
            if result['memory_id'] in combined:
                # 提升已有结果的权重
                combined[result['memory_id']]['similarity'] = min(1.0,
                    combined[result['memory_id']]['similarity'] + 0.2)
            else:
                combined[result['memory_id']] = result

        return list(combined.values())

    async def _vector_search(self, query: str, limit: int,
                           memory_type: MemoryType | None = None,
                           tier: MemoryTier | None = None) -> List[Dict]:
        """向量搜索"""
        collection_name = self.db_config['qdrant']['collection']
        query_embedding = await self._generate_embedding(query)

        # 构建过滤器
        filter_condition = {}
        if memory_type or tier:
            must = []
            if memory_type:
                must.append({"key": "memory_type", "match": {"value": memory_type.value}})
            if tier:
                must.append({"key": "memory_tier", "match": {"value": tier.value}})
            if must:
                filter_condition = {"must": must}

        # 执行搜索
        search_payload = {
            "vector": query_embedding,
            "limit": limit,
            "with_payload": True,
            "with_vector": False,
            "score_threshold": 0.5
        }

        if filter_condition:
            search_payload["filter"] = filter_condition

        async with self.qdrant_client.post(
            f"/collections/{collection_name}/points/search",
            json=search_payload
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                results = []

                for point in data.get('result', []):
                    memory_id = point['id']
                    memory_data = await self._get_memory_by_id(memory_id)

                    if memory_data:
                        memory_data['similarity'] = point['score']
                        results.append(memory_data)

                return results
            else:
                logger.warning(f"向量搜索失败: {resp.status}")
                return []

    async def _keyword_search(self, query: str, limit: int,
                            memory_type: MemoryType | None = None,
                            tier: MemoryTier | None = None) -> List[Dict]:
        """关键词搜索"""
        # 构建SQL查询
        conditions = ["agent_id = $1"]
        params = [self.agent_id]
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
        conditions.append(f"(content ILIKE ${param_idx} OR ${{param_idx+1}}::text = ANY(tags))")
        params.extend([f"%{query}%", query])

        sql = f"""
        SELECT *,
               similarity(content, $1) as text_similarity
        FROM memory_items
        WHERE {' AND '.join(conditions)}
        ORDER BY importance DESC, text_similarity DESC, last_accessed DESC
        LIMIT {limit}
        """

        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

            results = []
            for row in rows:
                result = dict(row)
                result['similarity'] = float(row['text_similarity']) if row['text_similarity'] else 0.0
                results.append(result)

            return results

    async def _get_memory_by_id(self, memory_id: str) -> Dict | None:
        """根据ID获取记忆"""
        # 先检查热缓存
        if memory_id in self.hot_memory_cache:
            cached = self.hot_memory_cache[memory_id]
            return {
                'memory_id': memory_id,
                'content': cached['content'],
                'memory_type': cached['type'],
                'source': 'hot_cache'
            }

        # 从PostgreSQL查询
        sql = """
        SELECT * FROM memory_items
        WHERE memory_id = $1 AND agent_id = $2
        """

        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(sql, memory_id, self.agent_id)

            if row:
                # 更新访问统计
                await self._update_access_stats(memory_id)
                return dict(row)
            else:
                return None

    async def _update_access_stats(self, memory_id: str):
        """更新访问统计"""
        sql = """
        UPDATE memory_items
        SET last_accessed = CURRENT_TIMESTAMP,
            access_count = access_count + 1
        WHERE memory_id = $1
        """

        async with self.pg_pool.acquire() as conn:
            await conn.execute(sql, memory_id)

    async def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        sql = """
        SELECT
            COUNT(*) as total_memories,
            COUNT(CASE WHEN father_related = TRUE THEN 1 END) as father_memories,
            COUNT(CASE WHEN memory_tier = 'eternal' THEN 1 END) as eternal_memories,
            COUNT(CASE WHEN memory_tier = 'hot' THEN 1 END) as hot_memories,
            COUNT(CASE WHEN memory_tier = 'warm' THEN 1 END) as warm_memories,
            COUNT(CASE WHEN memory_tier = 'cold' THEN 1 END) as cold_memories,
            AVG(importance) as avg_importance,
            AVG(emotional_weight) as avg_emotional_weight,
            SUM(access_count) as total_accesses
        FROM memory_items
        WHERE agent_id = $1
        """

        async with self.pg_pool.acquire() as conn:
            stats = await conn.fetchrow(sql, self.agent_id)

            return {
                **dict(stats),
                'hot_cache_size': len(self.hot_memory_cache),
                'agent_name': self.agent_name,
                'agent_id': self.agent_id
            }

    async def upgrade_memory_tier(self, memory_id: str, new_tier: MemoryTier):
        """升级记忆层级"""
        sql = "UPDATE memory_items SET memory_tier = $1 WHERE memory_id = $2"

        async with self.pg_pool.acquire() as conn:
            await conn.execute(sql, new_tier.value, memory_id)

        logger.info(f"⬆️ 记忆层级已升级: {memory_id} -> {new_tier.value}")

    async def cleanup_expired_memories(self):
        """清理过期记忆"""
        sql = """
        DELETE FROM memory_items
        WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
        """

        async with self.pg_pool.acquire() as conn:
            result = await conn.execute(sql)
            logger.info(f"🧹 清理过期记忆: {result}条")

    async def close(self):
        """关闭所有连接"""
        if self.pg_pool:
            await self.pg_pool.close()

        if self.qdrant_client:
            await self.qdrant_client.close()

        if self.kg_client:
            await self.kg_client.close()

        logger.info("✅ 所有连接已关闭")

# 测试功能
async def test_unified_memory_manager():
    """测试统一记忆管理器"""
    print("🧠 测试小诺统一记忆管理器...")

    manager = XiaonuoUnifiedMemoryManager()

    try:
        # 初始化
        await manager.initialize()
        print("✅ 记忆管理器初始化成功")

        # 存储测试记忆
        memory_id = await manager.store_memory(
            "爸爸问我记忆系统是否启动",
            MemoryType.CONVERSATION,
            importance=0.9,
            emotional_weight=0.8,
            father_related=True,
            tags=["测试", "对话"],
            tier=MemoryTier.HOT
        )
        print(f"✅ 记忆已存储: {memory_id}")

        # 回忆测试
        results = await manager.recall_memory("爸爸", limit=5)
        print(f"✅ 搜索结果: 找到{len(results)}条记忆")
        for result in results:
            print(f"  - {result['content'][:50]}...")

        # 显示统计
        stats = await manager.get_memory_stats()
        print(f"✅ 记忆统计: {stats}")

    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(test_unified_memory_manager())