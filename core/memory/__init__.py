#!/usr/bin/env python3
from __future__ import annotations
"""
记忆模块
Memory Module
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    SHORT_TERM = 'short_term'
    LONG_TERM = 'long_term'
    EPISODIC = 'episodic'
    SEMANTIC = 'semantic'

class MemorySystem:
    """记忆系统 - 集成向量记忆能力"""

    def __init__(self, agent_id: str, config: dict = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False
        self.vector_memory = None
        self.enable_vector_memory = self.config.get('enable_vector_memory', True)

    async def initialize(self):
        """初始化记忆系统"""
        logger.info(f"🧠 启动记忆系统: {self.agent_id}")

        try:
            # 初始化向量记忆系统
            if self.enable_vector_memory:
                from .vector_memory import get_vector_memory_instance
                self.vector_memory = await get_vector_memory_instance(
                    self.agent_id,
                    self.config.get('vector_memory', {})
                )
                logger.info(f"✅ 向量记忆系统集成完成: {self.agent_id}")
            else:
                logger.info(f"📝 向量记忆功能已禁用: {self.agent_id}")

        except Exception as e:
            logger.warning(f"⚠️ 向量记忆系统初始化失败，使用基础记忆功能: {e}")
            self.vector_memory = None

        self.initialized = True

    async def store_memory(self, content, memory_type, tags=None, embedding=None):
        """存储记忆"""
        if not self.initialized:
            raise RuntimeError('记忆系统未初始化')

        # 转换memory_type
        memory_category = self._convert_memory_type(memory_type)

        try:
            # 如果有向量记忆系统，使用增强存储
            if self.vector_memory:
                result = await self.vector_memory.store_memory(
                    content=content,
                    category=memory_category,
                    embedding=embedding,
                    metadata={
                        'original_type': str(memory_type),
                        'tags': tags or [],
                        'source': 'enhanced_memory_system'
                    }
                )
                logger.debug(f"✅ 向量记忆存储成功: {result.get('vector_id')}")
                return result
            else:
                # 基础存储
                return await self._basic_store_memory(content, memory_type, tags)

        except Exception as e:
            logger.error(f"❌ 记忆存储失败: {e}")
            # 降级到基础存储
            return await self._basic_store_memory(content, memory_type, tags)

    async def store(self, key, content, memory_type='general', tags=None, embedding=None):
        """存储记忆 - 兼容测试接口"""
        # 将key作为内容的一部分
        if isinstance(content, dict):
            content['key'] = key
            content_str = str(content)
        else:
            content_str = f"{key}: {content}"

        return await self.store_memory(content_str, memory_type, tags, embedding)

    async def retrieve_memory(self, query, memory_type=None, k=10, threshold=0.3):
        """检索记忆"""
        if not self.initialized:
            raise RuntimeError('记忆系统未初始化')

        try:
            # 如果有向量记忆系统，使用语义搜索
            if self.vector_memory:
                memory_category = self._convert_memory_type(memory_type) if memory_type else None
                result = await self.vector_memory.search_memories(
                    query=str(query),
                    category=memory_category,
                    k=k,
                    threshold=threshold
                )

                # 转换为兼容格式
                return {
                    'results': result.get('memories', []),
                    'total_found': result.get('total_found', 0),
                    'search_type': 'vector_search',
                    'query': str(query)[:100],
                    'agent_id': self.agent_id
                }
            else:
                # 基础检索
                return await self._basic_retrieve_memory(query, memory_type)

        except Exception as e:
            logger.error(f"❌ 记忆检索失败: {e}")
            # 降级到基础检索
            return await self._basic_retrieve_memory(query, memory_type)

    async def retrieve(self, key):
        """检索记忆 - 兼容测试接口"""
        # 使用key作为查询
        result = await self.retrieve_memory(key)

        # 如果有结果，返回第一个
        if result.get('results'):
            return result['results'][0]
        else:
            return None

    async def semantic_search(self, query, category=None, k=5, threshold=0.4):
        """语义搜索 - 新增方法"""
        if not self.vector_memory:
            return {
                'success': False,
                'error': '向量记忆系统未启用',
                'results': []
            }

        try:
            result = await self.vector_memory.search_memories(
                query=query,
                category=category,
                k=k,
                threshold=threshold
            )

            return {
                'success': True,
                'query': query,
                'category': category,
                'results': result.get('memories', []),
                'total_found': result.get('total_found', 0),
                'search_stats': result.get('search_stats', {})
            }

        except Exception as e:
            logger.error(f"❌ 语义搜索失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }

    async def get_memory_stats(self):
        """获取记忆统计信息"""
        if not self.initialized:
            raise RuntimeError('记忆系统未初始化')

        if self.vector_memory:
            return await self.vector_memory.get_memory_stats()
        else:
            return {
                'agent_id': self.agent_id,
                'total_memories': 0,
                'memory_type': 'basic_only',
                'vector_enabled': False
            }

    async def delete_memory(self, memory_id):
        """删除记忆"""
        if not self.initialized:
            raise RuntimeError('记忆系统未初始化')

        if self.vector_memory:
            return await self.vector_memory.delete_memory(memory_id)
        else:
            return {
                'success': False,
                'error': '基础记忆系统不支持删除操作',
                'agent_id': self.agent_id
            }

    async def clear_memories(self, memory_type=None):
        """清空记忆"""
        if not self.initialized:
            raise RuntimeError('记忆系统未初始化')

        if self.vector_memory:
            category = self._convert_memory_type(memory_type) if memory_type else None
            return await self.vector_memory.clear_memories(category)
        else:
            return {
                'success': False,
                'error': '基础记忆系统不支持清空操作',
                'agent_id': self.agent_id
            }

    def _convert_memory_type(self, memory_type) -> str:
        """转换记忆类型"""
        if isinstance(memory_type, str):
            memory_type = memory_type.lower()
            mapping = {
                'short_term': 'working',
                'long_term': 'semantic',
                'episodic': 'episodic',
                'semantic': 'semantic'
            }
            return mapping.get(memory_type, 'episodic')
        elif memory_type and hasattr(memory_type, 'value'):
            return self._convert_memory_type(memory_type.value)
        else:
            return 'episodic'

    async def _basic_store_memory(self, content, memory_type, tags):
        """基础记忆存储（降级方案）"""
        # 简单的内存存储实现
        if not hasattr(self, '_basic_memories'):
            self._basic_memories = []

        memory_record = {
            'content': str(content)[:200],  # 限制长度
            'type': str(memory_type),
            'tags': tags or [],
            'timestamp': datetime.now().isoformat(),
            'agent_id': self.agent_id
        }

        self._basic_memories.append(memory_record)
        return {'status': 'stored', 'type': 'basic'}

    async def _basic_retrieve_memory(self, query, memory_type):
        """基础记忆检索（降级方案）"""
        if not hasattr(self, '_basic_memories'):
            self._basic_memories = []

        query_str = str(query).lower()
        results = []

        for memory in self._basic_memories:
            if memory_type and memory['type'] != str(memory_type):
                continue

            # 简单的关键词匹配
            if any(word in memory['content'].lower() for word in query_str.split()):
                results.append(memory)

        return {
            'results': results[:10],  # 限制结果数量
            'total_found': len(results),
            'search_type': 'basic_keyword',
            'agent_id': self.agent_id
        }

    def register_callback(self, event_type: str, callback) -> None:
        """注册回调函数"""
        if not hasattr(self, '_callbacks'):
            self._callbacks = {}
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    async def shutdown(self):
        logger.info(f"🔄 关闭记忆系统: {self.agent_id}")
        self.initialized = False

    @classmethod
    async def initialize_global(cls):
        if not hasattr(cls, 'global_instance'):
            cls.global_instance = cls('global', {})
            await cls.global_instance.initialize()
        return cls.global_instance

    @classmethod
    async def shutdown_global(cls):
        if hasattr(cls, 'global_instance') and cls.global_instance:
            await cls.global_instance.shutdown()
            del cls.global_instance

__all__ = ['MemorySystem', 'MemoryType']
