#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆处理器
Memory Processor

提供完整的记忆管理功能，包括短期记忆、长期记忆、工作记忆和元认知记忆

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import hashlib
import heapq
import json
import logging
import pickle
import sqlite3
import threading
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """记忆类型"""
    EPISODIC = 'episodic'       # 情景记忆
    SEMANTIC = 'semantic'       # 语义记忆
    PROCEDURAL = 'procedural'   # 程序性记忆
    WORKING = 'working'         # 工作记忆
    METACOGNITIVE = 'metacognitive'  # 元认知记忆

class MemoryStatus(Enum):
    """记忆状态"""
    ACTIVE = 'active'           # 活跃
    DORMANT = 'dormant'         # 休眠
    ARCHIVED = 'archived'       # 已归档
    FORGOTTEN = 'forgotten'     # 已遗忘

class ConsolidationLevel(Enum):
    """巩固级别"""
    TRANSIENT = 'transient'     # 瞬时
    SHORT_TERM = 'short_term'   # 短期
    LONG_TERM = 'long_term'     # 长期
    PERMANENT = 'permanent'     # 永久

@dataclass
class MemoryTrace:
    """记忆痕迹"""
    trace_id: str
    memory_type: MemoryType
    content: Dict[str, Any]
    tags: List[str]
    importance: float  # 0-1
    emotional_valence: float  # -1 to 1
    retrieval_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    creation_time: datetime = field(default_factory=datetime.now)
    consolidation_level: ConsolidationLevel = ConsolidationLevel.TRANSIENT
    status: MemoryStatus = MemoryStatus.ACTIVE
    associated_traces: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RetrievalCue:
    """检索线索"""
    cue_id: str
    query: str
    memory_types: List[MemoryType]
    tags: List[str]
    time_range: Optional[Tuple[datetime, datetime] = None
    importance_threshold: float = 0.0
    max_results: int = 10

@dataclass
class RetrievalResult:
    """检索结果"""
    cue: RetrievalCue
    matched_traces: List[MemoryTrace]
    relevance_scores: List[float]
    retrieval_time: float
    total_matches: int

class MemoryConsolidation:
    """记忆巩固机制"""

    def __init__(self):
        self.consolidation_thresholds = {
            ConsolidationLevel.TRANSIENT: 1.0,      # 1小时
            ConsolidationLevel.SHORT_TERM: 24.0,   # 24小时
            ConsolidationLevel.LONG_TERM: 168.0,    # 7天
            ConsolidationLevel.PERMANENT: float('inf')  # 永久
        }
        self.importance_weights = {
            'retrieval_frequency': 0.3,
            'recent_access': 0.2,
            'importance_score': 0.3,
            'emotional_impact': 0.2
        }

    def should_consolidate(self, trace: MemoryTrace) -> ConsolidationLevel | None:
        """判断是否需要巩固"""
        current_level = trace.consolidation_level
        if current_level == ConsolidationLevel.PERMANENT:
            return None

        # 计算记忆强度
        memory_strength = self._calculate_memory_strength(trace)

        # 计算当前年龄
        age_hours = (datetime.now() - trace.creation_time).total_seconds() / 3600

        # 根据当前级别和记忆强度决定是否巩固
        next_level = self._get_next_consolidation_level(current_level)
        if next_level:
            threshold = self.consolidation_thresholds[next_level]

            # 重要记忆或强记忆可以提前巩固
            if (trace.importance > 0.7 or memory_strength > 0.8) and age_hours > threshold * 0.5:
                return next_level
            elif age_hours > threshold:
                return next_level

        return None

    def _calculate_memory_strength(self, trace: MemoryTrace) -> float:
        """计算记忆强度"""
        # 检索频率分数
        retrieval_score = min(trace.retrieval_count / 10.0, 1.0)

        # 最近访问分数
        days_since_access = (datetime.now() - trace.last_accessed).days
        recent_score = max(0, 1 - days_since_access / 30.0)

        # 重要性分数
        importance_score = trace.importance

        # 情感影响分数
        emotional_score = abs(trace.emotional_valence)

        # 加权计算
        memory_strength = (
            retrieval_score * self.importance_weights['retrieval_frequency'] +
            recent_score * self.importance_weights['recent_access'] +
            importance_score * self.importance_weights['importance_score'] +
            emotional_score * self.importance_weights['emotional_impact']
        )

        return memory_strength

    def _get_next_consolidation_level(self, current: ConsolidationLevel) -> ConsolidationLevel | None:
        """获取下一个巩固级别"""
        level_order = [
            ConsolidationLevel.TRANSIENT,
            ConsolidationLevel.SHORT_TERM,
            ConsolidationLevel.LONG_TERM,
            ConsolidationLevel.PERMANENT
        ]

        try:
            current_index = level_order.index(current)
            if current_index < len(level_order) - 1:
                return level_order[current_index + 1]
        except ValueError:
            pass

        return None

class MemoryIndex:
    """记忆索引"""

    def __init__(self):
        self.content_index: Dict[str, List[str] = defaultdict(list)  # 内容关键词索引
        self.tag_index: Dict[str, List[str] = defaultdict(list)      # 标签索引
        self.type_index: Dict[MemoryType, List[str] = defaultdict(list)  # 类型索引
        self.temporal_index: List[Tuple[datetime, str] = []          # 时间索引
        self.importance_index: List[Tuple[float, str] = []           # 重要性索引

    def add_trace(self, trace: MemoryTrace):
        """添加记忆痕迹到索引"""
        trace_id = trace.trace_id

        # 内容索引
        content_text = json.dumps(trace.content, ensure_ascii=False).lower()
        keywords = self._extract_keywords(content_text)
        for keyword in keywords:
            self.content_index[keyword].append(trace_id)

        # 标签索引
        for tag in trace.tags:
            self.tag_index[tag].append(trace_id)

        # 类型索引
        self.type_index[trace.memory_type].append(trace_id)

        # 时间索引
        heapq.heappush(self.temporal_index, (trace.creation_time, trace_id))

        # 重要性索引
        heapq.heappush(self.importance_index, (-trace.importance, trace_id))

    def remove_trace(self, trace_id: str):
        """从索引中移除记忆痕迹"""
        # 这里需要实现完整的索引清理逻辑
        # 简化版本：不做处理，实际应用中需要清理所有索引
        pass

    def search(self, cue: RetrievalCue) -> List[str]:
        """根据线索搜索"""
        candidate_ids = set()

        # 根据查询内容搜索
        if cue.query:
            query_keywords = self._extract_keywords(cue.query.lower())
            for keyword in query_keywords:
                if keyword in self.content_index:
                    candidate_ids.update(self.content_index[keyword])

        # 根据标签搜索
        for tag in cue.tags:
            if tag in self.tag_index:
                candidate_ids.update(self.tag_index[tag])

        # 根据记忆类型搜索
        for memory_type in cue.memory_types:
            if memory_type in self.type_index:
                candidate_ids.update(self.type_index[memory_type])

        # 如果没有候选结果，返回空列表
        if not candidate_ids:
            return []

        return list(candidate_ids)

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简化的关键词提取
        import re
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
        # 过滤停用词和短词
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '如果', 'the', 'is', 'at', 'which', 'on'}
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        return keywords[:20]  # 限制关键词数量

class MemoryProcessor:
    """记忆处理器"""

    def __init__(self, agent_id: str = 'default', storage_path: str = 'memory_storage.db'):
        self.agent_id = agent_id
        self.storage_path = storage_path
        self.initialized = False
        self.consolidation = MemoryConsolidation()
        self.index = MemoryIndex()

        # 内存存储
        self.working_memory: deque = deque(maxlen=100)  # 工作记忆
        self.short_term_memory: Dict[str, MemoryTrace] = {}  # 短期记忆
        self.long_term_memory: Dict[str, MemoryTrace] = {}   # 长期记忆

        # 性能指标
        self.metrics = {
            'total_stored': 0,
            'total_retrieved': 0,
            'consolidated_count': 0,
            'forgotten_count': 0,
            'average_retrieval_time': 0.0,
            'hit_rate': 0.0
        }

        # 配置
        self.working_memory_capacity = 100
        self.short_term_capacity = 1000
        self.consolidation_interval = 3600  # 1小时
        self.forgetting_threshold = 0.1

        # 后台任务
        self.consolidation_task: asyncio.Task | None = None
        self.forgetting_task: asyncio.Task | None = None

        # 延迟初始化数据库
        self.conn = None

        logger.info(f"🧠 记忆处理器创建完成: {agent_id}")

    async def initialize(self):
        """初始化记忆处理器"""
        if self.initialized:
            return

        try:
            # 初始化数据库
            self._init_database()

            # 加载现有记忆
            await self._load_memories()

            # 启动后台任务
            self._start_background_tasks()

            self.initialized = True
            logger.info(f"✅ 记忆处理器初始化完成: {self.agent_id}")

        except Exception as e:
            logger.error(f"❌ 记忆处理器初始化失败: {e}")
            raise

    async def _load_memories(self):
        """加载现有记忆"""
        try:
            # 加载短期记忆
            cursor = self.conn.execute(
                'SELECT * FROM memory_traces WHERE consolidation_level = ?',
                ('short_term',)
            )
            for row in cursor.fetchall():
                trace = self._row_to_memory_trace(row)
                self.short_term_memory[trace.trace_id] = trace

            # 加载长期记忆
            cursor = self.conn.execute(
                'SELECT * FROM memory_traces WHERE consolidation_level = ?',
                ('long_term',)
            )
            for row in cursor.fetchall():
                trace = self._row_to_memory_trace(row)
                self.long_term_memory[trace.trace_id] = trace

            total_loaded = len(self.short_term_memory) + len(self.long_term_memory)
            logger.info(f"📚 已加载 {len(self.short_term_memory)} 条短期记忆, {len(self.long_term_memory)} 条长期记忆")

        except Exception as e:
            logger.warning(f"⚠️ 加载现有记忆失败: {e}")

    def _row_to_memory_trace(self, row) -> MemoryTrace:
        """将数据库行转换为MemoryTrace对象"""
        content = json.loads(row['content'])
        tags = json.loads(row['tags'])
        context = json.loads(row['context'])
        associated_traces = json.loads(row['associated_traces'])

        return MemoryTrace(
            trace_id=row['trace_id'],
            memory_type=MemoryType(row['memory_type']),
            content=content,
            tags=tags,
            importance=row['importance'],
            emotional_valence=row['emotional_valence'],
            retrieval_count=row['retrieval_count'],
            last_accessed=datetime.fromisoformat(row['last_accessed']),
            creation_time=datetime.fromisoformat(row['creation_time']),
            consolidation_level=ConsolidationLevel(row['consolidation_level']),
            status=MemoryStatus(row['status']),
            associated_traces=associated_traces,
            context=context
        )

    def _start_background_tasks(self):
        """启动后台任务"""
        # 这里可以启动记忆巩固和遗忘的后台任务
        # 为了简化，暂时不启动
        pass

    def _init_database(self):
        """初始化数据库"""
        # 创建数据目录
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)

        # 连接数据库
        self.conn = sqlite3.connect(self.storage_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # 创建表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_traces (
                trace_id TEXT PRIMARY KEY,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL,
                importance REAL NOT NULL,
                emotional_valence REAL NOT NULL,
                retrieval_count INTEGER DEFAULT 0,
                last_accessed TEXT NOT NULL,
                creation_time TEXT NOT NULL,
                consolidation_level TEXT NOT NULL,
                status TEXT NOT NULL,
                associated_traces TEXT NOT NULL,
                context TEXT NOT NULL
            )
        """)

        # 创建索引
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_traces(memory_type)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_creation_time ON memory_traces(creation_time)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_importance ON memory_traces(importance)')

        # 加载现有记忆
        self._load_existing_memories()

        logger.info('✅ 数据库初始化完成')

    def _load_existing_memories(self):
        """加载现有记忆"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM memory_traces')

        for row in cursor.fetchall():
            trace = MemoryTrace(
                trace_id=row['trace_id'],
                memory_type=MemoryType(row['memory_type']),
                content=json.loads(row['content']),
                tags=json.loads(row['tags']),
                importance=row['importance'],
                emotional_valence=row['emotional_valence'],
                retrieval_count=row['retrieval_count'],
                last_accessed=datetime.fromisoformat(row['last_accessed']),
                creation_time=datetime.fromisoformat(row['creation_time']),
                consolidation_level=ConsolidationLevel(row['consolidation_level']),
                status=MemoryStatus(row['status']),
                associated_traces=json.loads(row['associated_traces']),
                context=json.loads(row['context'])
            )

            # 根据巩固级别分类存储
            if trace.consolidation_level == ConsolidationLevel.TRANSIENT:
                self.short_term_memory[trace.trace_id] = trace
            else:
                self.long_term_memory[trace.trace_id] = trace

            # 添加到索引
            self.index.add_trace(trace)

        logger.info(f"📚 已加载 {len(self.short_term_memory)} 条短期记忆, {len(self.long_term_memory)} 条长期记忆")

    async def start_background_tasks(self):
        """启动后台任务"""
        # 启动记忆巩固任务
        self.consolidation_task = asyncio.create_task(self._consolidation_loop())

        # 启动记忆遗忘任务
        self.forgetting_task = asyncio.create_task(self._forgetting_loop())

        logger.info('🚀 后台任务已启动')

    async def stop_background_tasks(self):
        """停止后台任务"""
        if self.consolidation_task:
            self.consolidation_task.cancel()
        if self.forgetting_task:
            self.forgetting_task.cancel()

        logger.info('🛑 后台任务已停止')

    async def process_memory(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理记忆数据（兼容性接口）"""
        try:
            # 解析记忆数据
            content = memory_data.get('content', '')
            memory_type_str = memory_data.get('type', 'episodic')
            tags = memory_data.get('tags', [])
            importance = memory_data.get('importance', 0.5)
            emotional_valence = memory_data.get('emotional_valence', 0.0)
            context = memory_data.get('context', {})

            # 转换记忆类型
            if isinstance(memory_type_str, str):
                try:
                    memory_type = MemoryType(memory_type_str)
                except ValueError:
                    memory_type = MemoryType.EPISODIC
            else:
                memory_type = MemoryType.EPISODIC

            # 存储记忆
            trace_id = await self.store_memory(
                content={'text': content, **context},
                memory_type=memory_type,
                tags=tags,
                importance=importance,
                emotional_valence=emotional_valence,
                context=context
            )

            return {
                'success': True,
                'trace_id': trace_id,
                'memory_type': memory_type.value,
                'agent_id': self.agent_id
            }

        except Exception as e:
            logger.error(f"处理记忆失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.agent_id
            }

    async def store_memory(self,
                          content: Dict[str, Any],
                          memory_type: MemoryType,
                          tags: Optional[List[str] = None,
                          importance: float = 0.5,
                          emotional_valence: float = 0.0,
                          context: Optional[Dict[str, Any] = None) -> str:
        """存储记忆"""
        trace_id = str(uuid.uuid4())
        tags = tags or []
        context = context or {}

        # 创建记忆痕迹
        trace = MemoryTrace(
            trace_id=trace_id,
            memory_type=memory_type,
            content=content,
            tags=tags,
            importance=min(1.0, max(0.0, importance)),
            emotional_valence=min(1.0, max(-1.0, emotional_valence)),
            context=context
        )

        # 根据记忆类型和重要性决定存储位置
        if memory_type == MemoryType.WORKING:
            # 工作记忆直接存储在内存中
            self.working_memory.append(trace)
        elif trace.consolidation_level in [ConsolidationLevel.TRANSIENT, ConsolidationLevel.SHORT_TERM]:
            # 短期记忆
            if len(self.short_term_memory) >= self.short_term_capacity:
                # 移除最旧的记忆
                oldest_id = min(self.short_term_memory.keys(),
                               key=lambda k: self.short_term_memory[k].creation_time)
                await self._archive_memory(oldest_id)

            self.short_term_memory[trace_id] = trace
        else:
            # 长期记忆
            self.long_term_memory[trace_id] = trace

        # 添加到索引
        self.index.add_trace(trace)

        # 持久化到数据库
        self._persist_trace(trace)

        # 更新指标
        self.metrics['total_stored'] += 1

        logger.debug(f"💾 存储记忆: {trace_id}, 类型: {memory_type.value}")
        return trace_id

    async def retrieve_memory(self, cue: RetrievalCue) -> RetrievalResult:
        """检索记忆"""
        start_time = datetime.now()

        # 从索引中搜索候选记忆
        candidate_ids = self.index.search(cue)

        # 根据线索过滤和排序
        matched_traces = []
        relevance_scores = []

        for trace_id in candidate_ids:
            trace = self._get_trace_by_id(trace_id)
            if trace and self._matches_cue(trace, cue):
                # 计算相关性分数
                relevance = self._calculate_relevance(trace, cue)
                if relevance > 0.1:  # 相关性阈值
                    matched_traces.append(trace)
                    relevance_scores.append(relevance)

        # 排序并限制结果数量
        sorted_results = sorted(zip(matched_traces, relevance_scores),
                               key=lambda x: x[1],
                               reverse=True)[:cue.max_results]

        # 更新访问统计
        for trace, _ in sorted_results:
            trace.retrieval_count += 1
            trace.last_accessed = datetime.now()
            self._persist_trace(trace)  # 更新数据库

        # 计算检索时间
        retrieval_time = (datetime.now() - start_time).total_seconds()

        # 更新指标
        self.metrics['total_retrieved'] += len(sorted_results)
        self._update_retrieval_metrics(retrieval_time)

        logger.debug(f"🔍 检索记忆: 找到 {len(sorted_results)} 条匹配")
        return RetrievalResult(
            cue=cue,
            matched_traces=[trace for trace, _ in sorted_results],
            relevance_scores=[score for _, score in sorted_results],
            retrieval_time=retrieval_time,
            total_matches=len(matched_traces)
        )

    def _get_trace_by_id(self, trace_id: str) -> MemoryTrace | None:
        """根据ID获取记忆痕迹"""
        # 工作记忆
        for trace in self.working_memory:
            if trace.trace_id == trace_id:
                return trace

        # 短期记忆
        if trace_id in self.short_term_memory:
            return self.short_term_memory[trace_id]

        # 长期记忆
        if trace_id in self.long_term_memory:
            return self.long_term_memory[trace_id]

        return None

    def _matches_cue(self, trace: MemoryTrace, cue: RetrievalCue) -> bool:
        """检查记忆是否匹配线索"""
        # 记忆类型匹配
        if cue.memory_types and trace.memory_type not in cue.memory_types:
            return False

        # 重要性阈值
        if trace.importance < cue.importance_threshold:
            return False

        # 时间范围
        if cue.time_range:
            start_time, end_time = cue.time_range
            if not (start_time <= trace.creation_time <= end_time):
                return False

        # 标签匹配
        if cue.tags and not any(tag in trace.tags for tag in cue.tags):
            return False

        return True

    def _calculate_relevance(self, trace: MemoryTrace, cue: RetrievalCue) -> float:
        """计算相关性分数"""
        score = 0.0

        # 查询内容匹配
        if cue.query:
            content_text = json.dumps(trace.content, ensure_ascii=False).lower()
            query_keywords = self.index._extract_keywords(cue.query.lower())
            content_keywords = self.index._extract_keywords(content_text)

            # 计算关键词重叠度
            overlap = len(set(query_keywords) & set(content_keywords))
            score += overlap / max(len(query_keywords), 1) * 0.4

        # 标签匹配
        if cue.tags:
            tag_matches = len(set(cue.tags) & set(trace.tags))
            score += tag_matches / max(len(cue.tags), 1) * 0.3

        # 重要性加权
        score += trace.importance * 0.2

        # 时间新近度
        days_old = (datetime.now() - trace.last_accessed).days
        recency_score = max(0, 1 - days_old / 30.0)
        score += recency_score * 0.1

        return min(score, 1.0)

    def _persist_trace(self, trace: MemoryTrace):
        """持久化记忆痕迹"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO memory_traces
            (trace_id, memory_type, content, tags, importance, emotional_valence,
             retrieval_count, last_accessed, creation_time, consolidation_level,
             status, associated_traces, context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trace.trace_id,
            trace.memory_type.value,
            json.dumps(trace.content, ensure_ascii=False),
            json.dumps(trace.tags, ensure_ascii=False),
            trace.importance,
            trace.emotional_valence,
            trace.retrieval_count,
            trace.last_accessed.isoformat(),
            trace.creation_time.isoformat(),
            trace.consolidation_level.value,
            trace.status.value,
            json.dumps(trace.associated_traces, ensure_ascii=False),
            json.dumps(trace.context, ensure_ascii=False)
        ))
        self.conn.commit()

    async def _consolidation_loop(self):
        """记忆巩固循环"""
        while True:
            try:
                await asyncio.sleep(self.consolidation_interval)
                await self._perform_consolidation()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 记忆巩固异常: {e}")

    async def _perform_consolidation(self):
        """执行记忆巩固"""
        logger.info('🔄 开始记忆巩固...')
        consolidated_count = 0

        # 检查短期记忆中的痕迹
        for trace_id, trace in list(self.short_term_memory.items()):
            next_level = self.consolidation.should_consolidate(trace)
            if next_level:
                trace.consolidation_level = next_level

                # 移动到长期记忆
                if next_level in [ConsolidationLevel.LONG_TERM, ConsolidationLevel.PERMANENT]:
                    self.long_term_memory[trace_id] = trace
                    del self.short_term_memory[trace_id]

                # 持久化更新
                self._persist_trace(trace)
                consolidated_count += 1

        self.metrics['consolidated_count'] += consolidated_count
        logger.info(f"✅ 记忆巩固完成，处理 {consolidated_count} 条记忆")

    async def _forgetting_loop(self):
        """记忆遗忘循环"""
        while True:
            try:
                await asyncio.sleep(86400)  # 24小时
                await self._perform_forgetting()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 记忆遗忘异常: {e}")

    async def _perform_forgetting(self):
        """执行记忆遗忘"""
        logger.info('🗑️ 开始记忆遗忘...')
        forgotten_count = 0

        # 检查所有记忆的强度
        all_traces = list(self.short_term_memory.values()) + list(self.long_term_memory.values())

        for trace in all_traces:
            memory_strength = self.consolidation._calculate_memory_strength(trace)

            # 强度低于阈值的记忆被遗忘
            if memory_strength < self.forgetting_threshold and trace.consolidation_level != ConsolidationLevel.PERMANENT:
                await self._forget_memory(trace.trace_id)
                forgotten_count += 1

        self.metrics['forgotten_count'] += forgotten_count
        logger.info(f"✅ 记忆遗忘完成，遗忘 {forgotten_count} 条记忆")

    async def _forget_memory(self, trace_id: str):
        """遗忘记忆"""
        # 从内存中移除
        if trace_id in self.short_term_memory:
            del self.short_term_memory[trace_id]
        elif trace_id in self.long_term_memory:
            del self.long_term_memory[trace_id]

        # 从索引中移除
        self.index.remove_trace(trace_id)

        # 从数据库中标记为已遗忘
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE memory_traces SET status = ? WHERE trace_id = ?',
            (MemoryStatus.FORGOTTEN.value, trace_id)
        )
        self.conn.commit()

    async def _archive_memory(self, trace_id: str):
        """归档记忆"""
        if trace_id in self.short_term_memory:
            trace = self.short_term_memory[trace_id]
            trace.status = MemoryStatus.ARCHIVED

            # 如果重要，转移到长期记忆
            if trace.importance > 0.5:
                self.long_term_memory[trace_id] = trace
                del self.short_term_memory[trace_id]
            else:
                # 否则删除
                await self._forget_memory(trace_id)

    def _update_retrieval_metrics(self, retrieval_time: float):
        """更新检索指标"""
        total_retrievals = self.metrics['total_retrieved']
        if total_retrievals > 0:
            current_avg = self.metrics['average_retrieval_time']
            self.metrics['average_retrieval_time'] = (
                (current_avg * (total_retrievals - 1) + retrieval_time) / total_retrievals
            )

    def get_memory_statistics(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        stats = {
            'working_memory': {
                'count': len(self.working_memory),
                'capacity': self.working_memory_capacity
            },
            'short_term_memory': {
                'count': len(self.short_term_memory),
                'capacity': self.short_term_capacity
            },
            'long_term_memory': {
                'count': len(self.long_term_memory),
                'unlimited': True
            },
            'consolidation_levels': defaultdict(int),
            'memory_types': defaultdict(int),
            'metrics': self.metrics.copy()
        }

        # 统计巩固级别
        all_traces = list(self.short_term_memory.values()) + list(self.long_term_memory.values())
        for trace in all_traces:
            stats['consolidation_levels'][trace.consolidation_level.value] += 1
            stats['memory_types'][trace.memory_type.value] += 1

        return stats

    def export_memories(self, file_path: str, memory_type: MemoryType | None = None):
        """导出记忆"""
        traces_to_export = []

        # 工作记忆
        for trace in self.working_memory:
            if not memory_type or trace.memory_type == memory_type:
                traces_to_export.append(asdict(trace))

        # 短期和长期记忆
        all_traces = list(self.short_term_memory.values()) + list(self.long_term_memory.values())
        for trace in all_traces:
            if not memory_type or trace.memory_type == memory_type:
                traces_to_export.append(asdict(trace))

        # 序列化日期时间对象
        for trace_dict in traces_to_export:
            for key, value in trace_dict.items():
                if isinstance(value, datetime):
                    trace_dict[key] = value.isoformat()
                elif isinstance(value, (MemoryType, ConsolidationLevel, MemoryStatus)):
                    trace_dict[key] = value.value

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(traces_to_export, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 记忆已导出到: {file_path}, 共 {len(traces_to_export)} 条")

    async def shutdown(self):
        """关闭记忆处理器"""
        try:
            # 停止后台任务
            if self.consolidation_task and not self.consolidation_task.done():
                self.consolidation_task.cancel()
            if self.forgetting_task and not self.forgetting_task.done():
                self.forgetting_task.cancel()

            # 持久化内存中的记忆
            await self._persist_memories()

            # 关闭数据库连接
            if self.conn:
                self.conn.close()

            self.initialized = False
            logger.info(f"✅ 记忆处理器已关闭: {self.agent_id}")

        except Exception as e:
            logger.error(f"❌ 关闭记忆处理器失败: {e}")

    async def _persist_memories(self):
        """持久化内存中的记忆"""
        if not self.conn:
            return

        try:
            # 持久化短期记忆
            for trace in self.short_term_memory.values():
                await self._save_memory_trace(trace, 'short_term')

            # 持久化长期记忆
            for trace in self.long_term_memory.values():
                await self._save_memory_trace(trace, 'long_term')

            self.conn.commit()
            logger.debug(f"💾 持久化了 {len(self.short_term_memory) + len(self.long_term_memory)} 条记忆")

        except Exception as e:
            logger.error(f"❌ 持久化记忆失败: {e}")

    def close(self):
        """关闭记忆处理器（同步版本，用于向后兼容）"""
        # 关闭数据库连接
        if hasattr(self, 'conn'):
            self.conn.close()

        logger.info('✅ 记忆处理器已关闭')

# 测试用例
async def main():
    """主函数"""
    logger.info('🧠 记忆处理器测试')
    logger.info(str('='*50))

    # 创建记忆处理器
    processor = MemoryProcessor('test_memory.db')

    # 启动后台任务
    await processor.start_background_tasks()

    # 存储测试记忆
    logger.info("\n💾 存储测试记忆...")
    memory_ids = []

    # 情景记忆
    episodic_id = await processor.store_memory(
        content={
            'event': '专利审查会议',
            'participants': ['审查员', '申请人', '代理人'],
            'outcome': '需要补充技术细节'
        },
        memory_type=MemoryType.EPISODIC,
        tags=['会议', '专利', '审查'],
        importance=0.8,
        emotional_valence=0.3
    )
    memory_ids.append(episodic_id)

    # 语义记忆
    semantic_id = await processor.store_memory(
        content={
            'concept': '专利新颖性',
            'definition': '指该发明或者实用新型不属于现有技术',
            'criteria': ['绝对新颖性', '相对新颖性']
        },
        memory_type=MemoryType.SEMANTIC,
        tags=['专利', '法律', '新颖性'],
        importance=0.9
    )
    memory_ids.append(semantic_id)

    # 工作记忆
    working_id = await processor.store_memory(
        content={
            'current_task': '分析专利申请',
            'focus_area': '技术方案的创新点',
            'progress': '正在进行中'
        },
        memory_type=MemoryType.WORKING,
        tags=['任务', '分析', '进行中'],
        importance=0.6
    )
    memory_ids.append(working_id)

    logger.info(f"✅ 已存储 {len(memory_ids)} 条记忆")

    # 检索测试
    logger.info("\n🔍 检索测试...")
    retrieval_cue = RetrievalCue(
        cue_id='cue1',
        query='专利新颖性定义',
        memory_types=[MemoryType.SEMANTIC],
        tags=['专利'],
        max_results=5
    )

    result = await processor.retrieve_memory(retrieval_cue)
    logger.info(f"找到 {len(result.matched_traces)} 条匹配记忆")
    for i, (trace, score) in enumerate(zip(result.matched_traces, result.relevance_scores), 1):
        logger.info(f"\n记忆 {i}:")
        logger.info(f"  ID: {trace.trace_id}")
        logger.info(f"  类型: {trace.memory_type.value}")
        logger.info(f"  相关性: {score:.2f}")
        logger.info(f"  内容: {json.dumps(trace.content, ensure_ascii=False, indent=4)}")

    # 获取统计信息
    logger.info("\n📊 记忆统计:")
    stats = processor.get_memory_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    # 导出记忆
    processor.export_memories('exported_memories.json')
    logger.info("\n📄 记忆已导出")

    # 停止后台任务
    await processor.stop_background_tasks()

    # 关闭处理器
    processor.close()

    logger.info("\n✅ 测试完成！")

if __name__ == '__main__':
    asyncio.run(main())