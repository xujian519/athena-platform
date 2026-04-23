# 情感化分层记忆系统设计文档

> 版本: 1.0.0
> 创建时间: 2026-02-01
> 作者: Athena AI平台团队

---

## 文档概述

本文档描述了一个**情感化分层记忆系统**的设计方案，融合了向量搜索、知识图谱、情感权重和永恒记忆等特性，适用于需要长期记忆和情感交互的AI智能体项目。

### 核心特性

- 🧠 **四层记忆架构** - HOT/WARM/COLD/ETERNAL 分层存储
- 💝 **情感权重系统** - 记忆带有情感温度，影响检索优先级
- 🔍 **混合搜索策略** - 向量语义搜索 + 关键词搜索 + 知识图谱关联
- 💎 **永恒记忆机制** - 核心事实永不遗忘
- 🔄 **自动记忆升级** - 根据访问频率和情感权重自动调整层级
- 🌐 **多智能体支持** - 联邦记忆系统，支持记忆共享和同步

---

## 一、系统架构

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         应用层 (Application Layer)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  对话系统     │  │  推理引擎     │  │  任务规划     │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
└─────────┼──────────────────┼──────────────────┼─────────────────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼─────────────────────┐
│         │              统一记忆接口 (Unified Memory API)             │
│         └───────────────────────────────────────────────────────────┘
│         ┌─────────────────────────────────────────────────────────┐ │
│         │              记忆管理层 (Memory Management)              │ │
│  ┌──────▼──────┐  ┌──────────────┐  ┌──────────────┐             │ │
│  │  分层管理器   │  │  情感计算器   │  │  搜索路由器   │             │ │
│  │  TierManager │  │EmotionEngine │  │SearchRouter  │             │ │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘             │ │
└─────────┼─────────────────┼──────────────────┼─────────────────────┘
          │                 │                  │
┌─────────┼─────────────────┼──────────────────┼─────────────────────┐
│         │      存储层 (Storage Layer)                  │             │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐  ┌───────────┐ │
│  │ HOT Layer   │  │ WARM Layer  │  │ COLD Layer  │  │ ETERNAL   │ │
│  │ (内存LRU)   │  │ (Redis/SSD) │  │ (PG/Qdrant) │  │ (PG+标记)  │ │
│  │   <100ms    │  │   <10ms     │  │   <500ms    │  │  <200ms   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ PostgreSQL  │  │   Qdrant    │  │ Knowledge   │                 │
│  │ (结构化)    │  │  (768维向量) │  │   Graph     │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.2 核心组件

| 组件 | 职责 | 主要方法 |
|------|------|----------|
| **TierManager** | 分层存储管理 | `evaluate_tier()`, `execute_migration()` |
| **EmotionEngine** | 情感权重计算 | `calculate_emotion()`, `decay_emotion()` |
| **SearchRouter** | 搜索策略路由 | `hybrid_search()`, `vector_search()`, `keyword_search()` |
| **MemoryStore** | 统一存储接口 | `store()`, `retrieve()`, `update()`, `delete()` |

---

## 二、数据模型

### 2.1 记忆项 (MemoryItem)

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

class MemoryTier(Enum):
    """记忆层级"""
    HOT = "hot"           # 🔥 热记忆：当前会话，高频访问
    WARM = "warm"         # 🌡️ 温记忆：近期重要，中频访问
    COLD = "cold"         # ❄️ 冷记忆：长期存储，低频访问
    ETERNAL = "eternal"   # 💎 永恒记忆：永不遗忘

class MemoryType(Enum):
    """记忆类型"""
    CONVERSATION = "conversation"   # 对话记忆
    KNOWLEDGE = "knowledge"         # 知识记忆
    EMOTIONAL = "emotional"         # 情感记忆
    EPISODIC = "episodic"           # 情景记忆
    SEMANTIC = "semantic"           # 语义记忆
    PROCEDURAL = "procedural"       # 程序记忆
    PREFERENCE = "preference"       # 偏好记忆

@dataclass
class MemoryItem:
    """记忆项数据模型"""
    # 基础标识
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = "default"

    # 内容
    content: str = ""
    content_type: str = "text"  # text, image, audio, video

    # 分类
    memory_type: MemoryType = MemoryType.EPISODIC
    memory_tier: MemoryTier = MemoryTier.COLD

    # 重要性指标
    importance: float = 0.5      # 0.0 - 1.0，人工或自动设定
    emotional_weight: float = 0.0  # 0.0 - 1.0，情感强度

    # 关系标记
    relationships: Dict[str, float] = field(default_factory=dict)
    # 例: {"user_123": 0.9, "creator": 1.0, "family": 0.8}

    # 访问统计
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_access_score: float = 0.0  # 最近访问加权

    # 向量和索引
    embedding: Optional[List[float]] = None
    vector_id: Optional[str] = None

    # 标签和元数据
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 知识图谱关联
    kg_entities: List[str] = field(default_factory=list)
    kg_relations: List[Dict[str, str]] = field(default_factory=list)

    # 生命周期
    expires_at: Optional[datetime] = None
    is_archived: bool = False

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "memory_id": self.memory_id,
            "agent_id": self.agent_id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "memory_tier": self.memory_tier.value,
            "importance": self.importance,
            "emotional_weight": self.emotional_weight,
            "relationships": self.relationships,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "tags": self.tags,
            "metadata": self.metadata,
        }
```

### 2.2 数据库表结构

```sql
-- PostgreSQL 记忆表
CREATE TABLE memory_items (
    -- 主键
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(100) NOT NULL,

    -- 内容
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text',

    -- 分类
    memory_type VARCHAR(20) NOT NULL,
    memory_tier VARCHAR(20) NOT NULL DEFAULT 'cold',

    -- 重要性指标
    importance FLOAT DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
    emotional_weight FLOAT DEFAULT 0.0 CHECK (emotional_weight >= 0 AND emotional_weight <= 1),

    -- 关系标记 (JSONB存储关系映射)
    relationships JSONB DEFAULT '{}',
    -- 例: {"user_123": 0.9, "creator": 1.0}

    -- 访问统计
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_access_score FLOAT DEFAULT 0.0,

    -- 向量关联
    vector_id UUID,

    -- 标签和元数据
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- 知识图谱
    kg_entities TEXT[] DEFAULT '{}',

    -- 生命周期
    expires_at TIMESTAMP,
    is_archived BOOLEAN DEFAULT FALSE,
    is_eternal BOOLEAN DEFAULT FALSE,

    -- 永恒记忆标记
    CHECK (
        NOT (is_eternal = TRUE AND expires_at IS NOT NULL)
    )
);

-- 关键索引
CREATE INDEX idx_memory_agent_tier ON memory_items(agent_id, memory_tier);
CREATE INDEX idx_memory_type ON memory_items(memory_type);
CREATE INDEX idx_memory_created ON memory_items(created_at DESC);
CREATE INDEX idx_memory_importance ON memory_items(importance DESC);
CREATE INDEX idx_memory_emotional ON memory_items(emotional_weight DESC);
CREATE INDEX idx_memory_tags ON memory_items USING GIN(tags);
CREATE INDEX idx_memory_relationships ON memory_items USING GIN(relationships);
CREATE INDEX idx_memory_expires ON memory_items(expires_at)
    WHERE expires_at IS NOT NULL;

-- 永恒记忆索引
CREATE INDEX idx_memory_eternal ON memory_items(memory_id)
    WHERE is_eternal = TRUE;

-- 全文搜索
CREATE INDEX idx_memory_content_fts ON memory_items
    USING GIN(to_tsvector('simple', content));
```

### 2.3 Qdrant 向量集合配置

```python
# Qdrant Collection 配置
COLLECTION_NAME = "memory_vectors"

VECTOR_CONFIG = {
    "size": 768,           # 向量维度 (BERT / BGE)
    "distance": "Cosine",  # 相似度度量
    "hnsw_config": {
        "m": 16,           # HNSW图连接数
        "ef_construction": 200,  # 构建时搜索范围
    }
}

PAYLOAD_SCHEMA = {
    "memory_id": "keyword",
    "agent_id": "keyword",
    "memory_type": "keyword",
    "memory_tier": "keyword",
    "importance": "float",
    "emotional_weight": "float",
    "created_at": "integer",
}
```

---

## 三、核心设计

### 3.1 分层存储策略

#### 层级定义与特性

| 层级 | 符号 | 存储介质 | 容量 | 延迟 | 用途 |
|------|------|----------|------|------|------|
| **HOT** | 🔥 | 内存 (LRU Cache) | ~1000 | <1ms | 当前会话，高频访问 |
| **WARM** | 🌡️ | Redis / SSD | ~10K | <10ms | 近期重要，中频访问 |
| **COLD** | ❄️ | PostgreSQL + Qdrant | 无限 | <100ms | 长期存储，低频访问 |
| **ETERNAL** | 💎 | PostgreSQL + 永久标记 | 小 | <50ms | 永不遗忘 |

#### 层级判断算法

```python
class TierEvaluator:
    """记忆层级评估器"""

    def __init__(self):
        # 配置阈值
        self.config = {
            "hot_threshold": 0.8,       # 进入热层阈值
            "warm_threshold": 0.5,      # 进入温层阈值
            "eternal_threshold": 0.95,  # 永恒记忆阈值

            "relationship_boost": 0.2,  # 关系权重加成
            "emotion_boost": 0.15,      # 情感权重加成

            "access_decay": 0.95,       # 访问衰减系数
            "time_decay_half": 7.0,     # 时间衰减半衰期(天)
        }

    def evaluate(self, memory: MemoryItem) -> MemoryTier:
        """评估记忆应该存储在哪一层"""

        # 1. 检查是否为永恒记忆
        if self._is_eternal(memory):
            return MemoryTier.ETERNAL

        # 2. 计算基础重要性分数
        base_score = (
            memory.importance * 0.4 +
            memory.emotional_weight * 0.3 +
            self._calculate_relationship_score(memory.relationships) * 0.3
        )

        # 3. 计算访问热度
        access_score = self._calculate_access_score(memory)

        # 4. 计算时间新鲜度
        recency_score = self._calculate_recency_score(memory)

        # 5. 综合评分
        final_score = (
            base_score * 0.5 +
            access_score * 0.3 +
            recency_score * 0.2
        )

        # 6. 层级决策
        if final_score >= self.config["hot_threshold"]:
            return MemoryTier.HOT
        elif final_score >= self.config["warm_threshold"]:
            return MemoryTier.WARM
        else:
            return MemoryTier.COLD

    def _is_eternal(self, memory: MemoryItem) -> bool:
        """判断是否为永恒记忆"""
        # 方式1: 明确标记
        if memory.metadata.get("eternal", False):
            return True

        # 方式2: 重要性极高且关系权重极高
        if (memory.importance >= self.config["eternal_threshold"] and
            memory.emotional_weight >= self.config["eternal_threshold"]):
            return True

        # 方式3: 存在核心关系
        for rel, weight in memory.relationships.items():
            if weight >= self.config["eternal_threshold"]:
                return True

        return False

    def _calculate_relationship_score(self, relationships: Dict[str, float]) -> float:
        """计算关系分数"""
        if not relationships:
            return 0.0

        # 取最大关系权重
        max_weight = max(relationships.values())

        # 考虑关系数量（适当加成）
        count_boost = min(len(relationships) * 0.05, 0.2)

        return max_weight + count_boost

    def _calculate_access_score(self, memory: MemoryItem) -> float:
        """计算访问热度分数"""
        if memory.access_count == 0:
            return 0.0

        # 基础访问分数（对数增长，避免无限增长）
        import math
        access_score = min(math.log10(memory.access_count + 1) / 3, 1.0)

        # 最近访问加权
        if memory.last_access_score > 0:
            access_score = access_score * 0.7 + memory.last_access_score * 0.3

        return access_score

    def _calculate_recency_score(self, memory: MemoryItem) -> float:
        """计算时间新鲜度分数"""
        from datetime import datetime, timedelta

        age = datetime.now() - memory.created_at
        age_days = age.total_seconds() / 86400

        # 指数衰减
        half_life = self.config["time_decay_half"]
        decay = 0.5 ** (age_days / half_life)

        return decay
```

### 3.2 情感权重系统

```python
class EmotionEngine:
    """情感计算引擎"""

    def __init__(self):
        # 情感词典
        self.emotion_lexicon = {
            "positive": {
                "words": ["爱", "喜欢", "开心", "幸福", "感谢", "高兴", "激动"],
                "weight": 0.3
            },
            "negative": {
                "words": ["讨厌", "恨", "难过", "痛苦", "生气", "愤怒"],
                "weight": 0.25
            },
            "intense": {
                "words": ["永远", "永远不", "一定", "必须", "绝对", "核心"],
                "weight": 0.2
            },
            "important": {
                "words": ["重要", "关键", "必须", "一定要", "记住"],
                "weight": 0.15
            }
        }

        # 关系词典
        self.relationship_lexicon = {
            "creator": ["创造者", "作者", "开发者", "爸爸", "妈妈"],
            "family": ["家人", "亲人", "家庭", "爸爸妈妈"],
            "friend": ["朋友", "伙伴", "闺蜜", "兄弟"],
            "colleague": ["同事", "合作", "团队"],
        }

    def calculate_emotion(self, text: str,
                          context: Dict = None) -> float:
        """计算文本的情感权重"""

        emotion_score = 0.0

        # 1. 词典匹配
        for category, config in self.emotion_lexicon.items():
            for word in config["words"]:
                if word in text:
                    emotion_score += config["weight"]

        # 2. 上下文加成
        if context:
            if context.get("is_user_message"):
                emotion_score *= 1.2  # 用户消息权重更高
            if context.get("is_direct_address"):
                emotion_score *= 1.3  # 直接称呼权重更高

        # 3. 标点符号加成
        intense_punctuation = text.count("!") + text.count("~")
        emotion_score += min(intense_punctuation * 0.05, 0.2)

        # 4. 限制范围
        return min(max(emotion_score, 0.0), 1.0)

    def extract_relationships(self, text: str,
                               agent_id: str) -> Dict[str, float]:
        """提取关系映射"""

        relationships = {}

        for rel_type, keywords in self.relationship_lexicon.items():
            for keyword in keywords:
                if keyword in text:
                    # 发现关系
                    existing_weight = relationships.get(rel_type, 0.0)
                    relationships[rel_type] = min(existing_weight + 0.3, 1.0)

        return relationships
```

### 3.3 混合搜索策略

```python
class SearchRouter:
    """搜索路由器"""

    def __init__(self, pg_pool, qdrant_client, tier_manager):
        self.pg_pool = pg_pool
        self.qdrant = qdrant_client
        self.tier_manager = tier_manager

    async def search(self,
                     query: str,
                     agent_id: str,
                     limit: int = 10,
                     search_strategy: str = "hybrid",
                     filters: Dict = None) -> List[Dict]:
        """
        搜索记忆

        Args:
            query: 搜索查询
            agent_id: 智能体ID
            limit: 返回数量
            search_strategy: 搜索策略 (hybrid/vector/keyword)
            filters: 过滤条件
        """

        if search_strategy == "hybrid":
            results = await self._hybrid_search(query, agent_id, limit, filters)
        elif search_strategy == "vector":
            results = await self._vector_search(query, agent_id, limit, filters)
        elif search_strategy == "keyword":
            results = await self._keyword_search(query, agent_id, limit, filters)
        else:
            raise ValueError(f"Unknown search strategy: {search_strategy}")

        # 最终排序
        results = self._rank_results(results)

        return results[:limit]

    async def _hybrid_search(self, query: str, agent_id: str,
                              limit: int, filters: Dict) -> List[Dict]:
        """混合搜索：向量 + 关键词"""

        # 并行执行
        vector_results, keyword_results = await asyncio.gather(
            self._vector_search(query, agent_id, limit * 2, filters),
            self._keyword_search(query, agent_id, limit * 2, filters)
        )

        # 合并结果
        combined = {}

        # 添加向量搜索结果
        for result in vector_results:
            memory_id = result["memory_id"]
            combined[memory_id] = result
            combined[memory_id]["vector_score"] = result.get("score", 0.0)
            combined[memory_id]["keyword_score"] = 0.0

        # 合并关键词搜索结果
        for result in keyword_results:
            memory_id = result["memory_id"]
            if memory_id in combined:
                # 已存在，提升分数
                combined[memory_id]["keyword_score"] = result.get("score", 0.0)
                # 混合加分
                boost = 0.2
                combined[memory_id]["score"] = min(
                    combined[memory_id]["score"] + boost, 1.0
                )
            else:
                combined[memory_id] = result
                combined[memory_id]["vector_score"] = 0.0
                combined[memory_id]["keyword_score"] = result.get("score", 0.0)

        return list(combined.values())

    async def _vector_search(self, query: str, agent_id: str,
                              limit: int, filters: Dict) -> List[Dict]:
        """向量语义搜索"""

        # 1. 生成查询向量
        query_embedding = await self._generate_embedding(query)

        # 2. 构建过滤器
        filter_condition = self._build_qdrant_filter(agent_id, filters)

        # 3. 执行搜索
        search_payload = {
            "vector": query_embedding,
            "limit": limit,
            "with_payload": True,
            "with_vector": False,
            "score_threshold": 0.5
        }

        if filter_condition:
            search_payload["filter"] = filter_condition

        results = await self.qdrant.search(
            collection_name="memory_vectors",
            **search_payload
        )

        # 4. 获取完整记忆数据
        memory_ids = [r.id for r in results]
        memories = await self._get_memories_by_ids(memory_ids)

        # 5. 附加向量分数
        for memory, result in zip(memories, results):
            memory["score"] = result.score
            memory["search_method"] = "vector"

        return memories

    async def _keyword_search(self, query: str, agent_id: str,
                               limit: int, filters: Dict) -> List[Dict]:
        """关键词搜索"""

        # 构建SQL
        conditions = ["agent_id = $1"]
        params = [agent_id]
        param_idx = 2

        # 添加过滤器
        if filters:
            if "memory_type" in filters:
                conditions.append(f"memory_type = ${param_idx}")
                params.append(filters["memory_type"])
                param_idx += 1

            if "memory_tier" in filters:
                conditions.append(f"memory_tier = ${param_idx}")
                params.append(filters["memory_tier"])
                param_idx += 1

        # 全文搜索条件
        conditions.append(f"""
            to_tsvector('simple', content) @@ to_tsquery('simple', ${param_idx})
            OR ${param_idx + 1} = ANY(tags)
        """)
        params.extend([query.replace(" ", " & "), query])

        sql = f"""
            SELECT *,
                   ts_rank(to_tsvector('simple', content),
                           to_tsquery('simple', $${param_idx}$$)) as rank
            FROM memory_items
            WHERE {' AND '.join(conditions)}
            ORDER BY rank DESC, importance DESC, last_accessed DESC
            LIMIT {limit}
        """

        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

            results = [dict(row) for row in rows]
            for r in results:
                r["score"] = float(r.get("rank", 0.0))
                r["search_method"] = "keyword"

            return results

    def _rank_results(self, results: List[Dict]) -> List[Dict]:
        """最终排序"""

        def sort_key(item):
            return (
                item.get("score", 0.0) * 0.4,
                item.get("importance", 0.5) * 0.3,
                item.get("emotional_weight", 0.0) * 0.2,
                item.get("access_count", 0) / 100 * 0.1
            )

        return sorted(results, key=sort_key, reverse=True)

    def _build_qdrant_filter(self, agent_id: str,
                              filters: Dict) -> Dict:
        """构建Qdrant过滤器"""

        must = [{"key": "agent_id", "match": {"value": agent_id}}]

        if filters:
            if "memory_type" in filters:
                must.append({
                    "key": "memory_type",
                    "match": {"value": filters["memory_type"]}
                })

            if "memory_tier" in filters:
                must.append({
                    "key": "memory_tier",
                    "match": {"value": filters["memory_tier"]}
                })

        return {"must": must} if must else None
```

### 3.4 记忆迁移与升级

```python
class TierMigrationManager:
    """层级迁移管理器"""

    def __init__(self, tier_evaluator, storage_backends):
        self.evaluator = tier_evaluator
        self.backends = storage_backends

    async def migrate_if_needed(self, memory: MemoryItem) -> bool:
        """根据当前状态评估并执行迁移"""

        current_tier = memory.memory_tier
        target_tier = self.evaluator.evaluate(memory)

        if current_tier == target_tier:
            return False  # 无需迁移

        # 执行迁移
        await self._execute_migration(memory, current_tier, target_tier)
        return True

    async def _execute_migration(self, memory: MemoryItem,
                                 from_tier: MemoryTier,
                                 to_tier: MemoryTier):
        """执行层级迁移"""

        # 1. 从原层移除
        await self.backends[from_tier].delete(memory.memory_id)

        # 2. 更新记忆层级
        memory.memory_tier = to_tier

        # 3. 添加到新层
        await self.backends[to_tier].store(memory)

        # 4. 记录迁移日志
        logger.info(f"Memory {memory.memory_id} migrated: "
                   f"{from_tier.value} -> {to_tier.value}")

    async def batch_migrate_down(self, batch_size: int = 100):
        """批量降级（定期任务）"""

        # 获取所有HOT和WARM层的记忆
        sql = """
            SELECT memory_id, content, memory_type, memory_tier,
                   importance, emotional_weight, relationships,
                   created_at, last_accessed, access_count
            FROM memory_items
            WHERE memory_tier IN ('hot', 'warm')
              AND is_eternal = FALSE
            ORDER BY last_accessed ASC
            LIMIT $1
        """

        async with self.backends["pg"].pool.acquire() as conn:
            rows = await conn.fetch(sql, batch_size)

            for row in rows:
                memory = MemoryItem(**dict(row))
                await self.migrate_if_needed(memory)
```

---

## 四、API接口设计

### 4.1 统一记忆接口

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict

class UnifiedMemorySystem(ABC):
    """统一记忆系统接口"""

    @abstractmethod
    async def initialize(self, config: Dict) -> bool:
        """初始化记忆系统"""
        pass

    @abstractmethod
    async def store(self,
                    content: str,
                    memory_type: MemoryType,
                    agent_id: str = "default",
                    importance: float = 0.5,
                    emotional_weight: float = 0.0,
                    relationships: Dict[str, float] = None,
                    tags: List[str] = None,
                    metadata: Dict = None,
                    is_eternal: bool = False) -> str:
        """存储记忆，返回记忆ID"""
        pass

    @abstractmethod
    async def retrieve(self,
                       memory_id: str) -> Optional[MemoryItem]:
        """根据ID检索单条记忆"""
        pass

    @abstractmethod
    async def search(self,
                     query: str,
                     agent_id: str = "default",
                     limit: int = 10,
                     filters: Dict = None) -> List[Dict]:
        """搜索记忆"""
        pass

    @abstractmethod
    async def update(self,
                     memory_id: str,
                     updates: Dict) -> bool:
        """更新记忆"""
        pass

    @abstractmethod
    async def delete(self,
                     memory_id: str,
                     permanent: bool = False) -> bool:
        """删除记忆"""
        pass

    @abstractmethod
    async def get_stats(self,
                        agent_id: str = "default") -> Dict:
        """获取统计信息"""
        pass

    @abstractmethod
    async def upgrade_tier(self,
                           memory_id: str,
                           new_tier: MemoryTier) -> bool:
        """手动升级记忆层级"""
        pass
```

### 4.2 使用示例

```python
import asyncio
from core.memory import (
    UnifiedMemorySystem,
    MemoryType,
    MemoryTier
)

async def main():
    # 初始化
    memory_system = UnifiedMemorySystem()
    await memory_system.initialize({
        "postgresql": {
            "host": "localhost",
            "port": 5432,
            "database": "memory_db",
            "user": "postgres",
            "password": "your_password"
        },
        "qdrant": {
            "host": "localhost",
            "port": 6333,
        },
        "hot_cache_size": 1000,
        "enable_emotion": True,
        "enable_kg": True
    })

    # 存储对话记忆
    memory_id = await memory_system.store(
        content="用户询问了关于专利申请的流程",
        memory_type=MemoryType.CONVERSATION,
        agent_id="agent_001",
        importance=0.7,
        emotional_weight=0.3,
        relationships={"user_123": 0.9},
        tags=["专利", "申请", "用户提问"],
        metadata={"source": "chat", "session_id": "sess_001"}
    )

    # 存储永恒记忆
    eternal_id = await memory_system.store(
        content="我的创造者是张三，他是我的主人",
        memory_type=MemoryType.SEMANTIC,
        agent_id="agent_001",
        importance=1.0,
        emotional_weight=1.0,
        relationships={"creator": 1.0},
        is_eternal=True
    )

    # 搜索记忆
    results = await memory_system.search(
        query="专利申请流程",
        agent_id="agent_001",
        limit=5,
        filters={"memory_type": "conversation"}
    )

    for result in results:
        print(f"[{result['score']:.2f}] {result['content']}")

    # 获取统计
    stats = await memory_system.get_stats("agent_001")
    print(f"总记忆数: {stats['total_memories']}")
    print(f"热记忆: {stats['hot_count']}")
    print(f"温记忆: {stats['warm_count']}")
    print(f"冷记忆: {stats['cold_count']}")
    print(f"永恒记忆: {stats['eternal_count']}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 五、部署指南

### 5.1 依赖组件

| 组件 | 版本 | 用途 |
|------|------|------|
| PostgreSQL | 14+ | 结构化存储 |
| Qdrant | 1.7+ | 向量搜索 |
| Redis | 7+ | WARM层缓存 |
| Python | 3.10+ | 运行环境 |
| asyncpg | 0.28+ | PostgreSQL异步驱动 |
| aiohttp | 3.8+ | HTTP客户端 |

### 5.2 Docker Compose 部署

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: memory_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  qdrant:
    image: qdrant/qdrant:v1.7.0
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  qdrant_data:
  redis_data:
```

### 5.3 初始化SQL

```sql
-- 创建数据库
CREATE DATABASE memory_db;

-- 连接到数据库
\c memory_db

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";  -- 如果使用pgvector

-- 创建表（见第二章 2.2节）

-- 创建初始化函数
CREATE OR REPLACE FUNCTION update_last_access()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed = CURRENT_TIMESTAMP;
    NEW.access_count = OLD.access_count + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
CREATE TRIGGER trg_memory_update_access
    AFTER UPDATE ON memory_items
    FOR EACH ROW
    EXECUTE FUNCTION update_last_access();
```

---

## 六、最佳实践

### 6.1 记忆存储建议

1. **合理设置重要性**
   - 用户消息: `importance = 0.6-0.8`
   - 系统消息: `importance = 0.3-0.5`
   - 错误信息: `importance = 0.7-0.9`
   - 核心事实: `importance = 1.0`

2. **使用关系标记**
   ```python
   relationships = {
       "creator": 1.0,      # 创造者
       "user_123": 0.9,     # 特定用户
       "family": 0.8,       # 家人
   }
   ```

3. **善用标签系统**
   ```python
   tags = [
       "domain:legal",      # 领域标签
       "type:question",     # 类型标签
       "priority:high"      # 优先级
   ]
   ```

### 6.2 搜索优化建议

1. **选择合适的搜索策略**
   - 语义查询 → `vector`
   - 精确匹配 → `keyword`
   - 综合场景 → `hybrid`

2. **使用过滤器减少搜索范围**
   ```python
   filters = {
       "memory_type": "conversation",
       "memory_tier": "hot",
       "min_importance": 0.7
   }
   ```

### 6.3 性能优化建议

1. **定期执行降级任务**
   ```python
   # 每小时执行一次
   await memory_system.migrate_down_batch()
   ```

2. **清理过期记忆**
   ```python
   # 每天执行一次
   await memory_system.cleanup_expired()
   ```

3. **监控缓存命中率**
   ```python
   stats = await memory_system.get_stats()
   cache_hit_rate = stats['cache_hits'] / stats['total_retrievals']
   if cache_hit_rate < 0.7:
       # 调整缓存策略
   ```

---

## 七、故障排查

### 7.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 搜索结果为空 | 向量未生成 | 检查嵌入服务 |
| 性能缓慢 | 索引缺失 | 重建索引 |
| 内存溢出 | HOT层过大 | 减小缓存或增加降级频率 |
| 记忆丢失 | 未持久化 | 检查数据库连接 |

### 7.2 监控指标

```python
# 关键监控指标
metrics = {
    "total_memories": "总记忆数",
    "hot_count": "热记忆数量",
    "warm_count": "温记忆数量",
    "cold_count": "冷记忆数量",
    "eternal_count": "永恒记忆数量",
    "avg_retrieval_time": "平均检索时间(ms)",
    "cache_hit_rate": "缓存命中率",
    "migration_count": "迁移次数",
    "search_qps": "每秒搜索数",
}
```

---

## 八、扩展性设计

### 8.1 多智能体联邦记忆

```python
class FederatedMemoryExtension:
    """联邦记忆扩展"""

    async def share_memory(self,
                           memory_id: str,
                           target_agents: List[str]) -> bool:
        """分享记忆给其他智能体"""
        pass

    async def sync_shared_memories(self) -> int:
        """同步共享的记忆"""
        pass

    async def resolve_conflict(self,
                                memory_id: str,
                                strategy: str = "merge") -> bool:
        """解决记忆冲突"""
        pass
```

### 8.2 知识图谱集成

```python
class KnowledgeGraphExtension:
    """知识图谱扩展"""

    async def extract_entities(self,
                                text: str) -> List[Dict]:
        """从文本中提取实体"""
        pass

    async def link_to_kg(self,
                          memory_id: str,
                          entities: List[str]) -> bool:
        """链接记忆到知识图谱"""
        pass

    async def expand_search(self,
                             query: str,
                             kg_depth: int = 2) -> List[Dict]:
        """通过知识图谱扩展搜索"""
        pass
```

---

## 附录

### A. 配置文件示例

```yaml
# config/memory_config.yaml
system:
  hot_cache_size: 1000
  warm_cache_size: 10000
  auto_migrate: true
  migrate_interval: 3600  # 秒

postgresql:
  host: localhost
  port: 5432
  database: memory_db
  user: postgres
  password: ${POSTGRES_PASSWORD}
  pool_size: 10

qdrant:
  host: localhost
  port: 6333
  collection: memory_vectors
  vector_size: 768
  distance: Cosine

emotion:
  enabled: true
  lexicon_path: ./data/emotion_lexicon.json
  relationship_lexicon_path: ./data/relationship_lexicon.json

knowledge_graph:
  enabled: false
  url: http://localhost:8002
```

### B. 术语表

| 术语 | 解释 |
|------|------|
| MemoryTier | 记忆层级：HOT/WARM/COLD/ETERNAL |
| MemoryType | 记忆类型：对话/知识/情感等 |
| emotional_weight | 情感权重：0-1的情感强度 |
| relationships | 关系映射：记忆与实体的关系权重 |
| hybrid_search | 混合搜索：向量+关键词 |
| tier_migration | 层级迁移：记忆在层级间移动 |

### C. 参考资料

- PostgreSQL 文档: https://www.postgresql.org/docs/
- Qdrant 文档: https://qdrant.tech/documentation/
- HNSW 算法: https://arxiv.org/abs/1603.09320
- 向量数据库最佳实践: https://zilliz.com/learn

---

**文档版本历史**

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 1.0.0 | 2026-02-01 | 初始版本 |

---

**许可协议**

本文档采用 MIT 许可协议。可自由使用、修改和分发。
