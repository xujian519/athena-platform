#!/usr/bin/env python3
from __future__ import annotations
"""
小诺知识库管理器
Xiaonuo Knowledge Manager

智能管理爸爸关心的知识领域,支持动态更新和智能检索

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class KnowledgeType(Enum):
    """知识类型"""

    TECHNICAL = "technical"  # 技术知识
    LEGAL = "legal"  # 法律知识
    BUSINESS = "business"  # 商业知识
    PERSONAL = "personal"  # 个人知识
    PATENT = "patent"  # 专利知识
    AI_ML = "ai_ml"  # AI/机器学习


class KnowledgePriority(Enum):
    """知识优先级"""

    CRITICAL = 3  # 关键
    HIGH = 2  # 高
    NORMAL = 1  # 普通
    LOW = 0  # 低


@dataclass
class KnowledgeItem:
    """知识项"""

    id: str
    title: str
    content: str
    knowledge_type: KnowledgeType
    priority: KnowledgePriority
    tags: list[str] = field(default_factory=list)
    source: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime | None = None
    confidence: float = 1.0  # 可信度
    related_items: set[str] = field(default_factory=set)


@dataclass
class SearchResult:
    """搜索结果"""

    item: KnowledgeItem
    relevance_score: float
    match_type: str  # exact, partial, semantic
    match_details: dict[str, Any] = field(default_factory=dict)


class XiaonuoKnowledgeManager:
    """小诺知识库管理器"""

    def __init__(self):
        self.name = "小诺知识库管理器"
        self.version = "v1.0.0"

        # 数据库路径
        self.db_path = (
            "data/modules/knowledge/knowledge/modules/knowledge/knowledge/xiaonuo_knowledge.db"
        )
        self.index_path = (
            "data/modules/knowledge/knowledge/modules/knowledge/knowledge/knowledge_index.json"
        )

        # 知识领域配置
        self.domain_configs = {
            KnowledgeType.TECHNICAL: {
                "keywords": ["Python", "AI", "机器学习", "深度学习", "算法", "架构", "系统"],
                "importance": 0.9,
                "update_frequency": "daily",
            },
            KnowledgeType.PATENT: {
                "keywords": ["专利", "发明", "申请", "审查", "权利要求", "说明书"],
                "importance": 0.95,
                "update_frequency": "weekly",
            },
            KnowledgeType.LEGAL: {
                "keywords": ["法律", "法规", "条款", "知识产权", "版权", "商标"],
                "importance": 0.85,
                "update_frequency": "monthly",
            },
            KnowledgeType.BUSINESS: {
                "keywords": ["商业", "市场", "策略", "管理", "运营", "产品"],
                "importance": 0.8,
                "update_frequency": "weekly",
            },
            KnowledgeType.PERSONAL: {
                "keywords": ["爸爸", "家庭", "生活", "健康", "兴趣", "爱好"],
                "importance": 1.0,
                "update_frequency": "realtime",
            },
        }

        # 初始化数据库
        self._init_database()

        # 加载知识索引
        self._load_knowledge_index()

        # 缓存
        self._cache = {}
        self._cache_ttl = 3600  # 1小时

        print(f"🌸 {self.name} 初始化完成")

    def _init_database(self) -> Any:
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 创建知识表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    knowledge_type TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    tags TEXT,
                    source TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    confidence REAL DEFAULT 1.0
                )
            """)

            # 创建关联表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_relations (
                    item_id1 TEXT,
                    item_id2 TEXT,
                    relation_type TEXT,
                    strength REAL,
                    PRIMARY KEY (item_id1, item_id2)
                )
            """)

            # 创建搜索索引表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_index (
                    keyword TEXT,
                    item_id TEXT,
                    frequency INTEGER,
                    PRIMARY KEY (keyword, item_id)
                )
            """)

            # 创建索引
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_items(knowledge_type)"
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_priority ON knowledge_items(priority)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_created_at ON knowledge_items(created_at)"
            )

            conn.commit()
            print("✅ 知识库数据库初始化完成")

    def _load_knowledge_index(self) -> Any:
        """加载知识索引"""
        try:
            if os.path.exists(self.index_path):
                with open(self.index_path, encoding="utf-8") as f:
                    self._cache = json.load(f)
                print("✅ 成功加载知识索引")
        except Exception as e:
            print(f"❌ 加载知识索引失败: {e}")
            self._cache = {}

    def add_knowledge(
        self,
        title: str,
        content: str,
        knowledge_type: KnowledgeType,
        priority: KnowledgePriority = KnowledgePriority.NORMAL,
        tags: list[str] = None,
        source: str = "",
    ) -> str:
        """添加知识"""
        knowledge_id = self._generate_id(title + content)

        knowledge = KnowledgeItem(
            id=knowledge_id,
            title=title,
            content=content,
            knowledge_type=knowledge_type,
            priority=priority,
            tags=tags or [],
            source=source,
        )

        # 保存到数据库
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO knowledge_items
                (id, title, content, knowledge_type, priority, tags, source,
                 created_at, updated_at, access_count, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    knowledge.id,
                    knowledge.title,
                    knowledge.content,
                    knowledge.knowledge_type.value,
                    knowledge.priority.value,
                    json.dumps(knowledge.tags, ensure_ascii=False),
                    knowledge.source,
                    knowledge.created_at.isoformat(),
                    knowledge.updated_at.isoformat(),
                    knowledge.access_count,
                    knowledge.confidence,
                ),
            )
            conn.commit()

        # 更新搜索索引
        self._update_search_index(knowledge)

        # 清除缓存
        self._invalidate_cache()

        print(f"📚 添加知识: {title}")
        return knowledge_id

    def search_knowledge(
        self,
        query: str,
        knowledge_type: KnowledgeType | None = None,
        limit: int = 10,
        min_relevance: float = 0.3,
    ) -> list[SearchResult]:
        """搜索知识"""
        cache_key = f"search:{hash(query)}:{knowledge_type}:{limit}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        results = []

        # 分词
        keywords = self._extract_keywords(query)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 构建查询
            query_conditions = []
            params = []

            if keywords:
                # 精确匹配
                exact_match = " OR ".join(["title LIKE ? OR content LIKE ?"] * len(keywords))
                for keyword in keywords:
                    params.extend([f"%{keyword}%", f"%{keyword}%"])
                query_conditions.append(f"({exact_match})")

            if knowledge_type:
                query_conditions.append("knowledge_type = ?")
                params.append(knowledge_type.value)

            if query_conditions:
                base_query = f"SELECT * FROM knowledge_items WHERE {' AND '.join(query_conditions)}"
            else:
                base_query = "SELECT * FROM knowledge_items"

            base_query += " ORDER BY priority DESC, access_count DESC LIMIT ?"
            params.append(limit)

            cursor.execute(base_query, params)

            for row in cursor.fetchall():
                # 重建KnowledgeItem
                knowledge = KnowledgeItem(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    knowledge_type=KnowledgeType(row[3]),
                    priority=KnowledgePriority(row[4]),
                    tags=json.loads(row[5] or "[]"),
                    source=row[6],
                    created_at=datetime.fromisoformat(row[7]),
                    updated_at=datetime.fromisoformat(row[8]),
                    access_count=row[9],
                    last_accessed=datetime.fromisoformat(row[10]) if row[10] else None,
                    confidence=row[11],
                )

                # 计算相关性分数
                relevance = self._calculate_relevance(query, knowledge, keywords)

                if relevance >= min_relevance:
                    results.append(
                        SearchResult(
                            item=knowledge,
                            relevance_score=relevance,
                            match_type=self._determine_match_type(query, knowledge),
                        )
                    )

                    # 更新访问计数
                    self._update_access_count(knowledge.id)

        # 缓存结果
        self._set_cache(cache_key, results, ttl=1800)

        return results

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 简单的关键词提取
        import re

        # 提取中文词汇(2-4个字)
        chinese_words = re.findall(r"[\u4e00-\u9fff]{2,4}", text)
        # 提取英文单词
        english_words = re.findall(r"[a-z_a-Z]{3,}", text)

        # 过滤停用词
        stop_words = {
            "的",
            "是",
            "在",
            "有",
            "和",
            "与",
            "或",
            "但",
            "如果",
            "那么",
            "the",
            "is",
            "at",
            "which",
            "on",
        }

        keywords = []
        for word in chinese_words + english_words:
            if word.lower() not in stop_words and len(word) >= 2:
                keywords.append(word)

        # 去重并返回前10个
        return list(set(keywords))[:10]

    def _calculate_relevance(
        self, query: str, knowledge: KnowledgeItem, keywords: list[str]
    ) -> float:
        """计算相关性分数"""
        score = 0.0

        # 标题匹配权重更高
        for keyword in keywords:
            if keyword in knowledge.title:
                score += 0.3
            if keyword in knowledge.content:
                score += 0.1

        # 知识类型重要性
        type_importance = self.domain_configs.get(knowledge.knowledge_type, {}).get(
            "importance", 0.5
        )
        score += type_importance * 0.2

        # 优先级
        score += knowledge.priority.value * 0.1

        # 访问热度
        if knowledge.access_count > 0:
            score += min(0.2, knowledge.access_count / 100)

        return min(1.0, score)

    def _determine_match_type(self, query: str, knowledge: KnowledgeItem) -> str:
        """确定匹配类型"""
        if query.lower() == knowledge.title.lower():
            return "exact"
        elif any(word in knowledge.title for word in query.split()):
            return "title_partial"
        elif any(word in knowledge.content for word in query.split()):
            return "content_partial"
        else:
            return "semantic"

    def _update_search_index(self, knowledge: KnowledgeItem) -> Any:
        """更新搜索索引"""
        # 从标题和内容提取关键词
        all_text = knowledge.title + " " + knowledge.content
        keywords = self._extract_keywords(all_text)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 删除旧的索引
            cursor.execute("DELETE FROM search_index WHERE item_id = ?", (knowledge.id,))

            # 添加新索引
            for keyword in keywords:
                # 检查是否已存在
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO search_index
                    (keyword, item_id, frequency)
                    VALUES (?, ?, ?)
                """,
                    (keyword, knowledge.id, 1),
                )

            conn.commit()

    def _update_access_count(self, knowledge_id: str) -> int:
        """更新访问计数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE knowledge_items
                SET access_count = access_count + 1,
                    last_accessed = ?
                WHERE id = ?
            """,
                (datetime.now().isoformat(), knowledge_id),
            )
            conn.commit()

    def get_knowledge_by_type(
        self, knowledge_type: KnowledgeType, limit: int = 20
    ) -> list[KnowledgeItem]:
        """根据类型获取知识"""
        cache_key = f"by_type:{knowledge_type.value}:{limit}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        items = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM knowledge_items
                WHERE knowledge_type = ?
                ORDER BY priority DESC, updated_at DESC
                LIMIT ?
            """,
                (knowledge_type.value, limit),
            )

            for row in cursor.fetchall():
                items.append(
                    KnowledgeItem(
                        id=row[0],
                        title=row[1],
                        content=row[2],
                        knowledge_type=KnowledgeType(row[3]),
                        priority=KnowledgeType(row[4]),
                        tags=json.loads(row[5] or "[]"),
                        source=row[6],
                        created_at=datetime.fromisoformat(row[7]),
                        updated_at=datetime.fromisoformat(row[8]),
                        access_count=row[9],
                        last_accessed=datetime.fromisoformat(row[10]) if row[10] else None,
                        confidence=row[11],
                    )
                )

        self._set_cache(cache_key, items)
        return items

    def get_related_knowledge(self, knowledge_id: str, limit: int = 5) -> list[KnowledgeItem]:
        """获取相关知识"""
        # 获取当前知识
        current = self.get_knowledge_by_id(knowledge_id)
        if not current:
            return []

        # 提取关键词
        keywords = self._extract_keywords(current.title + " " + current.content)

        # 搜索相关知识
        related = self.search_knowledge(
            " ".join(keywords[:3]), limit=limit + 1  # 使用前3个关键词  # 多取一个,排除自己
        )

        # 排除自己
        return [r.item for r in related if r.item.id != knowledge_id][:limit]

    def get_knowledge_by_id(self, knowledge_id: str) -> KnowledgeItem | None:
        """根据ID获取知识"""
        cache_key = f"by_id:{knowledge_id}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge_items WHERE id = ?", (knowledge_id,))
            row = cursor.fetchone()

            if row:
                knowledge = KnowledgeItem(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    knowledge_type=KnowledgeType(row[3]),
                    priority=KnowledgeType(row[4]),
                    tags=json.loads(row[5] or "[]"),
                    source=row[6],
                    created_at=datetime.fromisoformat(row[7]),
                    updated_at=datetime.fromisoformat(row[8]),
                    access_count=row[9],
                    last_accessed=datetime.fromisoformat(row[10]) if row[10] else None,
                    confidence=row[11],
                )
                self._set_cache(cache_key, knowledge)
                return knowledge

        return None

    def get_statistics(self) -> dict[str, Any]:
        """获取知识库统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 总知识数
            cursor.execute("SELECT COUNT(*) FROM knowledge_items")
            total_items = cursor.fetchone()[0]

            # 各类型知识数
            cursor.execute("""
                SELECT knowledge_type, COUNT(*)
                FROM knowledge_items
                GROUP BY knowledge_type
            """)
            type_counts = dict(cursor.fetchall())

            # 最受欢迎的知识
            cursor.execute("""
                SELECT title, access_count
                FROM knowledge_items
                ORDER BY access_count DESC
                LIMIT 5
            """)
            popular = cursor.fetchall()

            # 最近更新的知识
            cursor.execute("""
                SELECT title, updated_at
                FROM knowledge_items
                ORDER BY updated_at DESC
                LIMIT 5
            """)
            recent = cursor.fetchall()

            return {
                "total_items": total_items,
                "items_by_type": type_counts,
                "most_accessed": popular,
                "recently_updated": recent,
                "cache_size": len(self._cache),
                "domain_configs": {k.value: v for k, v in self.domain_configs.items()},
            }

    def _generate_id(self, content: str) -> str:
        """生成唯一ID"""
        return hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:16]

    def _get_from_cache(self, key: str) -> Any:
        """从缓存获取"""
        if key in self._cache:
            item = self._cache[key]
            if "timestamp" in item and time.time() - item["timestamp"] < self._cache_ttl:
                return item["data"]
        return None

    def _set_cache(self, key: str, data, ttl: int | None = None) -> None:
        """设置缓存"""
        self._cache[key] = {
            "data": data,
            "timestamp": time.time(),
            "ttl": ttl or self._cache_ttl,
        }

    def _invalidate_cache(self) -> Any:
        """清除缓存"""
        self._cache = {}

    def save_knowledge_index(self) -> None:
        """保存知识索引"""
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存知识索引失败: {e}")


# 导出主类
__all__ = [
    "KnowledgeItem",
    "KnowledgePriority",
    "KnowledgeType",
    "SearchResult",
    "XiaonuoKnowledgeManager",
]
