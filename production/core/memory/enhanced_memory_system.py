#!/usr/bin/env python3
from __future__ import annotations
"""
增强记忆系统
Enhanced Memory System

集成知识图谱的智能记忆系统
"""

import contextlib
import logging
from enum import Enum
from typing import Any

from .knowledge_graph_adapter import get_knowledge_adapter

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    SHORT_TERM = 'short_term'
    LONG_TERM = 'long_term'
    EPISODIC = 'episodic'
    SEMANTIC = 'semantic'
    KNOWLEDGE_GRAPH = 'knowledge_graph'

class EnhancedMemorySystem:
    """增强记忆系统 - 集成知识图谱"""

    def __init__(self, agent_id: str, config: dict | None = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False
        self.vector_memory = None
        self.knowledge_adapter = None

        # 配置参数
        self.enable_vector_memory = self.config.get('enable_vector_memory', True)
        self.enable_knowledge_graph = self.config.get('enable_knowledge_graph', True)
        self.auto_enhance_memories = self.config.get('auto_enhance_memories', True)
        self.knowledge_weight = self.config.get('knowledge_weight', 0.3)

    async def initialize(self):
        """初始化增强记忆系统"""
        logger.info(f"🧠 启动增强记忆系统: {self.agent_id}")

        try:
            # 初始化向量记忆系统
            if self.enable_vector_memory:
                from .vector_memory import get_vector_memory_instance
                self.vector_memory = await get_vector_memory_instance(
                    self.agent_id,
                    self.config.get('vector_memory', {})
                )
                logger.info(f"✅ 向量记忆系统集成完成: {self.agent_id}")

            # 初始化知识图谱适配器
            if self.enable_knowledge_graph:
                self.knowledge_adapter = await get_knowledge_adapter(
                    self.agent_id,
                    self.config.get('knowledge_graph', {})
                )
                logger.info(f"✅ 知识图谱适配器集成完成: {self.agent_id}")

        except Exception as e:
            logger.warning(f"⚠️ 增强功能初始化失败: {e}")

        self.initialized = True

    async def store_memory(self, content, memory_type, tags=None, embedding=None):
        """存储增强记忆"""
        if not self.initialized:
            raise RuntimeError('记忆系统未初始化')

        # 转换memory_type
        memory_category = self._convert_memory_type(memory_type)
        enhanced_content = content
        knowledge_entities = []

        try:
            # 如果启用自动增强，使用知识图谱增强内容
            if self.auto_enhance_memories and self.knowledge_adapter:
                enhancement = await self.knowledge_adapter.enhance_memory_with_knowledge(content)
                enhanced_content = enhancement['enhanced']
                knowledge_entities = enhancement.get('entities', [])

            # 如果有向量记忆系统，使用增强存储
            if self.vector_memory:
                metadata = {
                    'original_type': str(memory_type),
                    'tags': tags or [],
                    'source': 'enhanced_memory_system',
                    'knowledge_enhanced': bool(knowledge_entities)
                }

                # 添加知识图谱信息
                if knowledge_entities:
                    metadata['knowledge_entities'] = [
                        {
                            'entity_id': e['entity_id'],
                            'entity_type': e['entity_type'],
                            'name': e['name'],
                            'relevance': e.get('relevance_score', 0)
                        }
                        for e in knowledge_entities[:5]  # 只保留前5个
                    ]

                result = await self.vector_memory.store_memory(
                    content=enhanced_content,
                    category=memory_category,
                    embedding=embedding,
                    metadata=metadata
                )
                logger.debug(f"✅ 增强记忆存储成功: {result.get('vector_id')}")
                return result

        except Exception as e:
            logger.error(f"❌ 增强记忆存储失败: {e}")
            # 降级到基础存储
            return await self._basic_store_memory(content, memory_type, tags)

    async def retrieve_memory(self, query, memory_type=None, k=10, threshold=0.3):
        """检索增强记忆"""
        if not self.initialized:
            raise RuntimeError('记忆系统未初始化')

        # 转换memory_type
        memory_category = self._convert_memory_type(memory_type)

        try:
            # 向量记忆检索
            if self.vector_memory:
                result = await self.vector_memory.search_memories(
                    query=query,
                    category=memory_category,
                    k=k,
                    threshold=threshold
                )

                # 如果启用知识图谱，添加相关知识
                if self.knowledge_adapter and result.get('memories'):
                    enhanced_memories = []
                    for memory in result['memories']:
                        # 检索相关知识实体
                        related_entities = await self.knowledge_adapter.search_related_entities(
                            memory.get('content', ''),
                            entity_types=['concept', 'person', 'organization']
                        )

                        # 添加知识增强信息
                        if related_entities:
                            memory['knowledge_context'] = {
                                'related_entities': related_entities[:3],
                                'entity_count': len(related_entities)
                            }

                        enhanced_memories.append(memory)

                    result['memories'] = enhanced_memories

                return result

        except Exception as e:
            logger.error(f"❌ 增强记忆检索失败: {e}")

        # 降级到基础检索
        return await self._basic_retrieve_memory(query, memory_type, k, threshold)

    async def semantic_search(self, query, k=10, threshold=0.3):
        """语义搜索 - 兼容接口"""
        result = await self.retrieve_memory(query, k=k, threshold=threshold)

        # 转换返回格式
        memories = result.get('memories', [])
        for memory in memories:
            # 添加默认字段
            memory.setdefault('similarity', 0.5)
            memory.setdefault('category', 'general')

        return {
            'results': memories,
            'total_found': len(memories)
        }

    async def get_memory_stats(self):
        """获取记忆统计"""
        stats = {
            'agent_id': self.agent_id,
            'system_type': 'enhanced',
            'vector_memory_enabled': self.enable_vector_memory,
            'knowledge_graph_enabled': self.enable_knowledge_graph,
            'auto_enhance_enabled': self.auto_enhance_memories
        }

        # 向量记忆统计
        if self.vector_memory:
            try:
                vector_stats = await self.vector_memory.get_memory_stats()
                stats.update(vector_stats)
            except Exception:
                stats['vector_memory_error'] = True

        # 知识图谱统计
        if self.knowledge_adapter:
            try:
                # 获取知识图谱统计
                cursor = self.knowledge_adapter.connection.cursor()
                cursor.execute('SELECT COUNT(*) FROM entities')
                stats['knowledge_graph_entities'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM relations')
                stats['knowledge_graph_relations'] = cursor.fetchone()[0]
            except Exception:
                stats['knowledge_graph_error'] = True

        return stats

    async def search_knowledge_entities(self, query: str, entity_types: list[str] | None = None) -> list[dict]:
        """搜索知识图谱实体"""
        if not self.knowledge_adapter:
            return []

        return await self.knowledge_adapter.search_related_entities(query, entity_types)

    async def get_entity_context(self, entity_id: str) -> dict[str, Any]:
        """获取实体上下文"""
        if not self.knowledge_adapter:
            return {}

        return await self.knowledge_adapter.get_entity_context(entity_id)

    async def find_knowledge_paths(self, from_entity: str, to_entity: str, max_depth: int = 3) -> list[dict]:
        """查找知识路径"""
        if not self.knowledge_adapter:
            return []

        return await self.knowledge_adapter.find_knowledge_paths(from_entity, to_entity, max_depth)

    async def get_domain_knowledge(self, domain: str, limit: int = 10) -> list[dict]:
        """获取领域知识"""
        if not self.knowledge_adapter:
            return []

        return await self.knowledge_adapter.get_domain_knowledge(domain, limit)

    def _convert_memory_type(self, memory_type):
        """转换记忆类型"""
        if isinstance(memory_type, str):
            return memory_type
        elif hasattr(memory_type, 'value'):
            return memory_type.value
        else:
            return str(memory_type)

    async def _basic_store_memory(self, content, memory_type, tags=None):
        """基础记忆存储"""
        logger.warning('使用基础记忆存储功能')
        return {'status': 'stored', 'method': 'basic'}

    async def _basic_retrieve_memory(self, query, memory_type=None, k=10, threshold=0.3):
        """基础记忆检索"""
        logger.warning('使用基础记忆检索功能')
        return {'memories': [], 'total_found': 0, 'method': 'basic'}

    async def shutdown(self):
        """关闭记忆系统"""
        logger.info(f"🔄 关闭增强记忆系统: {self.agent_id}")

        if self.vector_memory:
            with contextlib.suppress(BaseException):
                await self.vector_memory.shutdown()

        if self.knowledge_adapter:
            with contextlib.suppress(BaseException):
                await self.knowledge_adapter.shutdown()

        self.initialized = False
