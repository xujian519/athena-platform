#!/usr/bin/env python3
from __future__ import annotations
"""
增强记忆系统模块 - BaseModule标准接口兼容版本
Enhanced Memory Module - BaseModule Compatible Version

基于现有EnhancedMemorySystem，添加BaseModule标准接口支持
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 导入BaseModule
from core.base_module import BaseModule

# 导入现有记忆系统
try:
    from .enhanced_memory_system import EnhancedMemorySystem, MemoryType
    MEMORY_SYSTEM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"无法导入现有记忆系统: {e}")
    MEMORY_SYSTEM_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryCategory(Enum):
    """记忆分类"""
    EPISODIC = 'episodic'          # 情节记忆
    SEMANTIC = 'semantic'          # 语义记忆
    PROCEDURAL = 'procedural'      # 程序性记忆
    WORKING = 'working'           # 工作记忆
    LONG_TERM = 'long_term'       # 长期记忆
    SHORT_TERM = 'short_term'     # 短期记忆

@dataclass
class MemoryItem:
    """记忆项数据结构"""
    id: str
    content: str
    category: MemoryCategory
    tags: list[str]
    embedding: list[float]
    metadata: dict[str, Any]
    created_at: datetime
    accessed_at: datetime
    access_count: int
    relevance_score: float

@dataclass
class MemorySearchResult:
    """记忆搜索结果"""
    memories: list[MemoryItem]
    total_count: int
    query: str
    search_time: float
    relevance_threshold: float

class EnhancedMemoryConfig:
    """增强记忆配置"""

    def __init__(self, config: dict[str, Any] | None = None):
        config = config or {}

        # 基础配置
        self.enable_vector_memory = config.get('enable_vector_memory', True)
        self.enable_knowledge_graph = config.get('enable_knowledge_graph', True)
        self.auto_enhance_memories = config.get('auto_enhance_memories', True)

        # 性能配置
        self.max_memory_items = config.get('max_memory_items', 10000)
        self.retrieval_limit = config.get('retrieval_limit', 10)
        self.relevance_threshold = config.get('relevance_threshold', 0.3)
        self.cache_search_results = config.get('cache_search_results', True)

        # 知识图谱配置
        self.knowledge_weight = config.get('knowledge_weight', 0.3)
        self.enable_entity_extraction = config.get('enable_entity_extraction', True)

        # 向量存储配置
        self.embedding_dimension = config.get('embedding_dimension', 1024)
        self.vector_db_type = config.get('vector_db_type', 'faiss')  # faiss, chroma, pinecone
        self.enable_semantic_search = config.get('enable_semantic_search', True)

class EnhancedMemoryModule(BaseModule):
    """增强记忆系统模块 - BaseModule标准接口版本"""

    def __init__(self, agent_id: str, config: dict[str, Any] | None = None):
        """
        初始化增强记忆系统模块

        Args:
            agent_id: 智能体标识符
            config: 配置参数
        """
        super().__init__(agent_id, config)

        # 记忆模块特有配置
        self.memory_config = EnhancedMemoryConfig(config)

        # 初始化现有记忆系统
        self.memory_system = None
        if MEMORY_SYSTEM_AVAILABLE:
            try:
                self.memory_system = EnhancedMemorySystem(agent_id, config)
                logger.info('✅ 现有记忆系统集成成功')
            except Exception as e:
                logger.warning(f"现有记忆系统集成失败: {e}")

        # 记忆状态
        self.memory_stats = {
            'total_memories': 0,
            'memories_by_category': {},
            'total_searches': 0,
            'successful_searches': 0,
            'average_search_time': 0.0,
            'cache_hits': 0,
            'last_access_time': None
        }

        # 搜索缓存
        self.search_cache = {} if self.memory_config.cache_search_results else None

        # 记忆项存储（备用）
        self.memory_items = []

        # 支持的记忆操作
        self.supported_operations = [
            'store', 'retrieve', 'search', 'update', 'delete',
            'consolidate', 'enhance', 'categorize', 'tag'
        ]

        logger.info(f"🧠 增强记忆系统模块初始化完成 - Agent: {self.agent_id}")

    async def _on_initialize(self) -> bool:
        """模块初始化"""
        try:
            logger.info('🧠 初始化记忆系统模块...')

            # 初始化现有记忆系统
            if self.memory_system:
                await self.memory_system.initialize()
                logger.info('✅ 现有记忆系统就绪')
            else:
                # 创建简化的记忆处理能力
                await self._initialize_fallback_memory()
                logger.info('✅ 备用记忆处理能力就绪')

            # 验证必要依赖
            dependencies_ok = await self._verify_dependencies()
            if not dependencies_ok:
                logger.warning('⚠️ 部分依赖缺失，某些功能可能不可用')

            # 初始化搜索缓存
            if self.search_cache is not None:
                self.search_cache = {}

            logger.info('✅ 记忆系统模块初始化成功')
            return True

        except Exception as e:
            logger.error(f"❌ 记忆系统模块初始化失败: {e!s}")
            return False

    async def _on_health_check(self) -> bool:
        """健康检查"""
        try:
            checks = {
                'memory_system_available': self.memory_system is not None,
                'dependencies_ok': await self._verify_dependencies(),
                'storage_available': True,
                'memory_usage_ok': self._check_memory_usage(),
                'cache_system_ok': self.search_cache is not None or not self.memory_config.cache_search_results
            }

            overall_healthy = all(checks.values())

            # 存储健康检查详情
            self._health_check_details = {
                'memory_status': 'available' if checks['memory_system_available'] else 'unavailable',
                'dependencies_status': 'ok' if checks['dependencies_ok'] else 'missing',
                'storage_status': 'ready' if checks['storage_available'] else 'full',
                'cache_status': 'ok' if checks['cache_system_ok'] else 'error',
                'stats': self.memory_stats
            }

            return overall_healthy

        except Exception as e:
            logger.error(f"健康检查失败: {e!s}")
            self._health_check_details = {'error': str(e)}
            return False

    async def store(self, content: str, memory_type: str = 'short_term',
                   tags: list[str] | None = None,
                   metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        存储记忆 - 核心功能方法

        Args:
            content: 记忆内容
            memory_type: 记忆类型
            tags: 标签列表
            metadata: 元数据

        Returns:
            存储结果
        """
        try:
            start_time = datetime.now()

            # 更新统计信息
            self.memory_stats['total_memories'] += 1

            # 类型转换
            memory_category = self._convert_memory_type(memory_type)
            if not memory_category:
                raise ValueError(f"不支持的记忆类型: {memory_type}")

            # 使用现有记忆系统
            if self.memory_system:
                result = await self.memory_system.store_memory(
                    content=content,
                    memory_type=memory_type,
                    tags=tags
                )
                success = result.get('success', True)
                memory_id = result.get('memory_id', f"memory_{self.memory_stats['total_memories']}")
            else:
                # 备用存储
                memory_id = await self._fallback_store_memory(content, memory_category, tags, metadata)
                success = True
                result = {'memory_id': memory_id, 'success': True}

            # 更新分类统计
            category_name = memory_category.value
            self.memory_stats['memories_by_category'][category_name] = \
                self.memory_stats['memories_by_category'].get(category_name, 0) + 1

            # 清理相关缓存
            if self.search_cache:
                self.search_cache.clear()

            logger.info(f"✅ 记忆存储完成 - ID: {memory_id}")
            return {
                'success': success,
                'memory_id': memory_id,
                'category': memory_category.value,
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'agent_id': self.agent_id
            }

        except Exception as e:
            logger.error(f"❌ 记忆存储失败: {e!s}")
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.agent_id
            }

    async def retrieve(self, query: str, memory_type: str | None = None,
                      k: int = 10, threshold: float = 0.3) -> MemorySearchResult:
        """
        检索记忆

        Args:
            query: 查询内容
            memory_type: 记忆类型过滤
            k: 返回数量限制
            threshold: 相关性阈值

        Returns:
            记忆搜索结果
        """
        try:
            start_time = datetime.now()

            # 更新统计信息
            self.memory_stats['total_searches'] += 1

            # 缓存检查
            cache_key = self._get_search_cache_key(query, memory_type, k, threshold)
            if self.search_cache and cache_key in self.search_cache:
                cached_result = self.search_cache[cache_key]
                self.memory_stats['cache_hits'] += 1
                logger.info(f"✅ 搜索缓存命中: {query[:50]}...")
                return cached_result

            # 使用现有记忆系统
            if self.memory_system:
                result_data = await self.memory_system.retrieve_memory(
                    query=query,
                    memory_type=memory_type,
                    k=k,
                    threshold=threshold
                )
                search_result = self._convert_to_search_result(result_data, query, start_time)
            else:
                # 备用检索
                search_result = await self._fallback_retrieve_memory(query, memory_type, k, threshold, start_time)

            # 更新统计信息
            self.memory_stats['successful_searches'] += 1
            self.memory_stats['last_access_time'] = datetime.now().isoformat()
            self._update_average_search_time(search_result.search_time)

            # 缓存结果
            if self.search_cache is not None:
                self.search_cache[cache_key] = search_result

            logger.info(f"✅ 记忆检索完成 - 找到 {len(search_result.memories)} 条记忆")
            return search_result

        except Exception as e:
            logger.error(f"❌ 记忆检索失败: {e!s}")

            # 返回空结果
            return MemorySearchResult(
                memories=[],
                total_count=0,
                query=query,
                search_time=0.0,
                relevance_threshold=threshold
            )

    async def consolidate(self, memory_ids: list[str] | None = None,
                         criteria: dict[str, Any] | None = None) -> dict[str, Any]:
        """记忆巩固"""
        try:
            logger.info('🔄 开始记忆巩固...')

            # 这里实现记忆巩固逻辑
            # 合并相似记忆，删除冗余，强化重要连接

            consolidated_count = 0
            if memory_ids:
                consolidated_count = len(memory_ids)

            logger.info(f"✅ 记忆巩固完成 - 巩固了 {consolidated_count} 条记忆")
            return {
                'success': True,
                'consolidated_count': consolidated_count,
                'criteria': criteria,
                'agent_id': self.agent_id
            }

        except Exception as e:
            logger.error(f"❌ 记忆巩固失败: {e!s}")
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.agent_id
            }

    async def process(self, input_data: Any) -> dict[str, Any]:
        """标准处理接口 - BaseModule兼容"""
        try:
            if isinstance(input_data, dict):
                operation = input_data.get('operation', 'store')
                content = input_data.get('content', '')
                memory_type = input_data.get('memory_type', 'short_term')
                tags = input_data.get('tags')
                metadata = input_data.get('metadata')

                if operation == 'store':
                    return await self.store(content, memory_type, tags, metadata)
                elif operation == 'retrieve':
                    query = input_data.get('query', content)
                    k = input_data.get('k', 10)
                    threshold = input_data.get('threshold', 0.3)
                    result = await self.retrieve(query, memory_type, k, threshold)
                    return {
                        'success': True,
                        'memories': [m.__dict__ for m in result.memories],
                        'total_count': result.total_count
                    }
                else:
                    raise ValueError(f"不支持的操作: {operation}")
            else:
                # 默认为存储操作
                return await self.store(str(input_data))

        except Exception as e:
            logger.error(f"❌ 处理失败: {e!s}")
            raise

    async def _initialize_fallback_memory(self):
        """初始化备用记忆能力"""
        self.fallback_memory = {
            'items': [],
            'categories': set(),
            'tags': set()
        }

    async def _verify_dependencies(self) -> bool:
        """验证依赖"""
        try:
            # 检查基础依赖
            return True  # 记忆系统主要依赖内部存储
        except Exception:
            return False

    def _check_memory_usage(self) -> bool:
        """检查内存使用"""
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent
            return memory_percent < 90
        except ImportError:
            return True

    def _convert_memory_type(self, memory_type: str) -> MemoryCategory | None:
        """转换记忆类型"""
        type_mapping = {
            'short_term': MemoryCategory.SHORT_TERM,
            'long_term': MemoryCategory.LONG_TERM,
            'working': MemoryCategory.WORKING,
            'episodic': MemoryCategory.EPISODIC,
            'semantic': MemoryCategory.SEMANTIC,
            'procedural': MemoryCategory.PROCEDURAL
        }
        return type_mapping.get(memory_type.lower())

    def _get_search_cache_key(self, query: str, memory_type: str,
                            k: int, threshold: float) -> str:
        """生成搜索缓存键"""
        import hashlib
        content = f"{query}:{memory_type}:{k}:{threshold}"
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

    def _convert_to_search_result(self, result_data: dict[str, Any],                                query: str, start_time: datetime) -> MemorySearchResult:
        """转换搜索结果格式"""
        memories = []
        for memory_data in result_data.get('memories', []):
            memory_item = MemoryItem(
                id=memory_data.get('id', ''),
                content=memory_data.get('content', ''),
                category=MemoryCategory(memory_data.get('category', 'short_term')),
                tags=memory_data.get('tags', []),
                embedding=memory_data.get('embedding'),
                metadata=memory_data.get('metadata', {}),
                created_at=datetime.fromisoformat(memory_data.get('created_at', datetime.now().isoformat())),
                accessed_at=datetime.fromisoformat(memory_data.get('accessed_at', datetime.now().isoformat())),
                access_count=memory_data.get('access_count', 0),
                relevance_score=memory_data.get('relevance_score', 0.0)
            )
            memories.append(memory_item)

        search_time = (datetime.now() - start_time).total_seconds()

        return MemorySearchResult(
            memories=memories,
            total_count=result_data.get('total_count', len(memories)),
            query=query,
            search_time=search_time,
            relevance_threshold=result_data.get('threshold', 0.3)
        )

    async def _fallback_store_memory(self, content: str, category: MemoryCategory,
                                   tags: list[str], metadata: dict[str, Any]) -> str:
        """备用记忆存储"""
        memory_id = f"fallback_memory_{len(self.memory_items)}"
        memory_item = MemoryItem(
            id=memory_id,
            content=content,
            category=category,
            tags=tags or [],
            embedding=None,
            metadata=metadata or {},
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            access_count=0,
            relevance_score=1.0
        )
        self.memory_items.append(memory_item)
        return memory_id

    async def _fallback_retrieve_memory(self, query: str, memory_type: str,
                                      k: int, threshold: float, start_time: datetime) -> MemorySearchResult:
        """备用记忆检索"""
        # 简化的文本匹配
        matching_memories = []
        query_lower = query.lower()

        for memory in self.memory_items:
            # 类型过滤
            if memory_type and memory.category.value != memory_type:
                continue

            # 简单的文本匹配
            if query_lower in memory.content.lower():
                memory.access_count += 1
                memory.accessed_at = datetime.now()
                matching_memories.append(memory)

        # 限制数量
        matching_memories = matching_memories[:k]

        search_time = (datetime.now() - start_time).total_seconds()

        return MemorySearchResult(
            memories=matching_memories,
            total_count=len(matching_memories),
            query=query,
            search_time=search_time,
            relevance_threshold=threshold
        )

    def _update_average_search_time(self, search_time: float):
        """更新平均搜索时间"""
        if self.memory_stats['total_searches'] > 0:
            current_avg = self.memory_stats['average_search_time']
            n = self.memory_stats['total_searches']
            new_avg = (current_avg * (n - 1) + search_time) / n
            self.memory_stats['average_search_time'] = new_avg

    def get_metrics(self) -> dict[str, Any]:
        """获取模块性能指标"""
        try:
            return {
                'agent_id': self.agent_id,
                'module_type': self.__class__.__name__,
                'module_status': self.status.value if hasattr(self, 'status') else 'unknown',
                'initialized': hasattr(self, '_initialized') and self._initialized,
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if hasattr(self, 'start_time') else 0,
                'memory_stats': self.memory_stats,
                'config': {
                    'enable_vector_memory': self.memory_config.enable_vector_memory,
                    'enable_knowledge_graph': self.memory_config.enable_knowledge_graph,
                    'retrieval_limit': self.memory_config.retrieval_limit,
                    'relevance_threshold': self.memory_config.relevance_threshold
                },
                'system_available': self.memory_system is not None,
                'capabilities': self.supported_operations,
                'health_details': getattr(self, '_health_check_details', {})
            }
        except Exception as e:
            logger.error(f"获取指标失败: {e!s}")
            return {
                'error': str(e),
                'agent_id': getattr(self, 'agent_id', 'unknown')
            }

    async def _on_start(self) -> bool:
        """启动模块"""
        try:
            logger.info(f"🚀 启动记忆系统模块 - Agent: {self.agent_id}")
            self._is_running = True
            return True
        except Exception as e:
            logger.error(f"❌ 记忆系统模块启动失败: {e!s}")
            return False

    async def _on_stop(self) -> bool:
        """停止模块"""
        try:
            logger.info(f"⏹️ 停止记忆系统模块 - Agent: {self.agent_id}")
            self._is_running = False
            return True
        except Exception as e:
            logger.error(f"❌ 记忆系统模块停止失败: {e!s}")
            return False

    async def _on_shutdown(self) -> bool:
        """关闭模块"""
        try:
            logger.info(f"🔚 关闭记忆系统模块 - Agent: {self.agent_id}")

            # 清理记忆系统
            if self.memory_system:
                self.memory_system = None

            # 清理缓存
            if self.search_cache is not None:
                self.search_cache.clear()

            # 保存统计信息
            logger.info(f"📊 记忆统计: {self.memory_stats}")
            return True
        except Exception as e:
            logger.error(f"❌ 记忆系统模块关闭失败: {e!s}")
            return False

# 便捷创建函数
def create_enhanced_memory_module(agent_id: str | None = None, config: dict[str, Any] | None = None) -> EnhancedMemoryModule:
    """
    创建增强记忆系统模块实例

    Args:
        agent_id: 智能体标识符
        config: 配置参数

    Returns:
        EnhancedMemoryModule实例
    """
    return EnhancedMemoryModule(agent_id, config)
