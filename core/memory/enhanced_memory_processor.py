#!/usr/bin/env python3
"""
小诺增强记忆处理器
Xiaonuo Enhanced Memory Processor

专门为爸爸设计的智能记忆系统，能够记住对话、情感、重要时刻等

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    content: str
    memory_type: str  # 'conversation', 'emotion', 'important_moment', 'preference'
    timestamp: datetime
    tags: list[str] = field(default_factory=list)
    importance: float = 0.5  # 0-1之间的重要性评分
    emotion_context: dict[str, Any] | None = None
    retrieval_count: int = 0
    last_retrieved: datetime | None = None

@dataclass
class DadPreference:
    """爸爸偏好记忆"""
    category: str  # 'technical', 'personal', 'work', 'hobby'
    preference: str
    confidence: float
    examples: list[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)

class EnhancedMemoryProcessor:
    """小诺增强记忆处理器"""

    def __init__(self):
        self.name = "小诺增强记忆处理器"
        self.version = "v1.0.0"
        self.memory_db_path = "data/memory/xiaonuo_memory.db"
        self.dad_profile_path = "data/memory/dad_profile.json"

        # 初始化数据库
        self._init_database()

        # 加载爸爸档案
        self.dad_profile = self._load_dad_profile()

        # 记忆缓存
        self.recent_memories: list[MemoryItem] = []
        self.important_moments: list[MemoryItem] = []

        logger.info(f"🌸 {self.name} 初始化完成")

    def _init_database(self):
        """初始化记忆数据库"""
        os.makedirs(os.path.dirname(self.memory_db_path), exist_ok=True)

        with sqlite3.connect(self.memory_db_path) as conn:
            cursor = conn.cursor()

            # 创建记忆表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    tags TEXT,
                    importance REAL DEFAULT 0.5,
                    emotion_context TEXT,
                    retrieval_count INTEGER DEFAULT 0,
                    last_retrieved TEXT
                )
            """)

            # 创建偏好表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    category TEXT,
                    preference TEXT,
                    confidence REAL,
                    examples TEXT,
                    last_updated TEXT,
                    PRIMARY KEY (category, preference)
                )
            """)

            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)")

            conn.commit()
            logger.info("✅ 记忆数据库初始化完成")

    def _load_dad_profile(self) -> dict[str, Any]:
        """加载爸爸档案"""
        default_profile = {
            "name": "徐健",
            "relationship": "爸爸",
            "special_memories": [],
            "communication_style": {
                "preferred_tone": "温暖专业",
                "technical_depth": "专业",
                "response_speed": "及时"
            },
            "interests": {
                "technical": ["AI", "专利", "系统架构"],
                "personal": ["女儿", "家庭", "美食"],
                "professional": ["创新", "效率", "质量"]
            },
            "important_dates": []
        }

        try:
            if os.path.exists(self.dad_profile_path):
                with open(self.dad_profile_path, encoding='utf-8') as f:
                    profile = json.load(f)
                logger.info("✅ 成功加载爸爸档案")
                return profile
            else:
                # 创建默认档案
                with open(self.dad_profile_path, 'w', encoding='utf-8') as f:
                    json.dump(default_profile, f, ensure_ascii=False, indent=2)
                logger.info("✅ 创建默认爸爸档案")
                return default_profile
        except Exception as e:
            logger.error(f"❌ 加载爸爸档案失败: {e}")
            return default_profile

    def save_memory(self,
                    content: str,
                    memory_type: str = "conversation",
                    tags: list[str] | None = None,
                    importance: float = 0.5,
                    emotion_context: dict[str, Any] | None = None) -> str:
        """保存记忆"""
        memory_id = f"mem_{int(time.time() * 1000)}"

        memory = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now(),
            tags=tags or [],
            importance=importance,
            emotion_context=emotion_context
        )

        # 保存到数据库
        with sqlite3.connect(self.memory_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories
                (id, content, memory_type, timestamp, tags, importance, emotion_context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id,
                memory.content,
                memory.memory_type,
                memory.timestamp.isoformat(),
                json.dumps(memory.tags, ensure_ascii=False),
                memory.importance,
                json.dumps(memory.emotion_context or {}, ensure_ascii=False)
            ))
            conn.commit()

        # 更新缓存
        self.recent_memories.append(memory)
        if len(self.recent_memories) > 100:
            self.recent_memories.pop(0)

        # 如果是重要时刻，添加到特殊列表
        if importance >= 0.8 or memory_type == "important_moment":
            self.important_moments.append(memory)

        logger.info(f"💾 保存记忆: {memory_type} - {content[:50]}...")
        return memory_id

    def save_conversation(self,
                         conversation: str,
                         emotion: str | None = None,
                         topics: list[str] | None = None) -> str:
        """保存对话记忆"""
        emotion_context = {
            "emotion": emotion,
            "topics": topics or [],
            "conversation_length": len(conversation)
        }

        return self.save_memory(
            content=conversation,
            memory_type="conversation",
            tags=topics or ["对话"],
            importance=0.6,
            emotion_context=emotion_context
        )

    def mark_important_moment(self,
                              description: str,
                              moment_type: str = "achievement",
                              related_context: dict[str, Any] | None = None) -> str:
        """标记重要时刻"""
        tags = ["重要时刻", moment_type]
        if moment_type == "achievement":
            tags.append("成就")
        elif moment_type == "milestone":
            tags.append("里程碑")

        return self.save_memory(
            content=description,
            memory_type="important_moment",
            tags=tags,
            importance=0.9,
            emotion_context={
                "moment_type": moment_type,
                "context": related_context or {}
            }
        )

    def save_dad_preference(self,
                           category: str,
                           preference: str,
                           confidence: float = 0.8,
                           example: str | None = None) -> bool:
        """保存爸爸偏好"""
        try:
            with sqlite3.connect(self.memory_db_path) as conn:
                cursor = conn.cursor()

                # 获取现有偏好
                cursor.execute("""
                    SELECT examples FROM preferences
                    WHERE category = ? AND preference = ?
                """, (category, preference))
                row = cursor.fetchone()

                if row:
                    # 更新现有偏好
                    examples = json.loads(row[0] or "[]")
                    if example and example not in examples:
                        examples.append(example)

                    cursor.execute("""
                        UPDATE preferences
                        SET confidence = ?, examples = ?, last_updated = ?
                        WHERE category = ? AND preference = ?
                    """, (
                        confidence,
                        json.dumps(examples, ensure_ascii=False),
                        datetime.now().isoformat(),
                        category,
                        preference
                    ))
                else:
                    # 添加新偏好
                    examples = [example] if example else []
                    cursor.execute("""
                        INSERT INTO preferences
                        (category, preference, confidence, examples, last_updated)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        category,
                        preference,
                        confidence,
                        json.dumps(examples, ensure_ascii=False),
                        datetime.now().isoformat()
                    ))

                conn.commit()

            # 更新内存中的偏好
            if category not in self.dad_profile:
                self.dad_profile[category] = []
            if preference not in self.dad_profile[category]:
                self.dad_profile[category].append(preference)

            # 保存档案
            self._save_dad_profile()

            logger.info(f"💝 保存爸爸偏好: {category} - {preference}")
            return True

        except Exception as e:
            logger.error(f"❌ 保存偏好失败: {e}")
            return False

    def retrieve_memories(self,
                         memory_type: str | None = None,
                         tags: list[str] | None = None,
                         time_range: tuple[datetime, datetime] | None = None,
                         limit: int = 10) -> list[MemoryItem]:
        """检索记忆"""
        query = "SELECT * FROM memories WHERE 1=1"
        params = []

        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)

        if tags:
            for tag in tags:
                query += " AND tags LIKE ?"
                params.append(f'%{tag}%')

        if time_range:
            query += " AND timestamp BETWEEN ? AND ?"
            params.extend([time_range[0].isoformat(), time_range[1].isoformat()])

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        memories = []
        try:
            with sqlite3.connect(self.memory_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)

                for row in cursor.fetchall():
                    memory = MemoryItem(
                        id=row['id'],
                        content=row['content'],
                        memory_type=row['memory_type'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        tags=json.loads(row['tags'] or '[]'),
                        importance=row['importance'],
                        emotion_context=json.loads(row['emotion_context'] or '{}'),
                        retrieval_count=row['retrieval_count'],
                        last_retrieved=datetime.fromisoformat(row['last_retrieved']) if row['last_retrieved'] else None
                    )
                    memories.append(memory)

                    # 更新检索计数
                    self._update_retrieval_count(memory.id)

        except Exception as e:
            logger.error(f"❌ 检索记忆失败: {e}")

        return memories

    def get_dad_preferences(self, category: str | None = None) -> list[DadPreference]:
        """获取爸爸偏好"""
        preferences = []

        try:
            with sqlite3.connect(self.memory_db_path) as conn:
                cursor = conn.cursor()

                if category:
                    cursor.execute("""
                        SELECT * FROM preferences
                        WHERE category = ?
                        ORDER BY confidence DESC
                    """, (category,))
                else:
                    cursor.execute("""
                        SELECT * FROM preferences
                        ORDER BY category, confidence DESC
                    """)

                for row in cursor.fetchall():
                    pref = DadPreference(
                        category=row[0],
                        preference=row[1],
                        confidence=row[2],
                        examples=json.loads(row[3] or '[]'),
                        last_updated=datetime.fromisoformat(row[4])
                    )
                    preferences.append(pref)

        except Exception as e:
            logger.error(f"❌ 获取偏好失败: {e}")

        return preferences

    def get_recent_conversations(self, hours: int = 24) -> list[MemoryItem]:
        """获取最近的对话"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        return self.retrieve_memories(
            memory_type="conversation",
            time_range=(start_time, end_time),
            limit=50
        )

    def get_important_moments(self, days: int = 30) -> list[MemoryItem]:
        """获取重要时刻"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        return self.retrieve_memories(
            memory_type="important_moment",
            time_range=(start_time, end_time),
            limit=20
        )

    def analyze_emotional_pattern(self, days: int = 7) -> dict[str, Any]:
        """分析情感模式"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        memories = self.retrieve_memories(
            memory_type="conversation",
            time_range=(start_time, end_time),
            limit=100
        )

        emotion_counts = {}
        topic_emotions = {}

        for memory in memories:
            if memory.emotion_context and 'emotion' in memory.emotion_context:
                emotion = memory.emotion_context['emotion']
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

                if 'topics' in memory.emotion_context:
                    for topic in memory.emotion_context['topics']:
                        if topic not in topic_emotions:
                            topic_emotions[topic] = {}
                        topic_emotions[topic][emotion] = topic_emotions[topic].get(emotion, 0) + 1

        return {
            "emotion_distribution": emotion_counts,
            "topic_emotion_mapping": topic_emotions,
            "total_conversations": len(memories),
            "analysis_period": f"{days} days"
        }

    def _update_retrieval_count(self, memory_id: str):
        """更新检索计数"""
        try:
            with sqlite3.connect(self.memory_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE memories
                    SET retrieval_count = retrieval_count + 1,
                        last_retrieved = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), memory_id))
                conn.commit()
        except Exception as e:
            logger.error(f"❌ 更新检索计数失败: {e}")

    def _save_dad_profile(self):
        """保存爸爸档案"""
        try:
            os.makedirs(os.path.dirname(self.dad_profile_path), exist_ok=True)
            with open(self.dad_profile_path, 'w', encoding='utf-8') as f:
                json.dump(self.dad_profile, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存爸爸档案失败: {e}")

    def get_memory_summary(self) -> dict[str, Any]:
        """获取记忆摘要"""
        try:
            with sqlite3.connect(self.memory_db_path) as conn:
                cursor = conn.cursor()

                # 总记忆数
                cursor.execute("SELECT COUNT(*) FROM memories")
                total_memories = cursor.fetchone()[0]

                # 各类型记忆数
                cursor.execute("""
                    SELECT memory_type, COUNT(*)
                    FROM memories
                    GROUP BY memory_type
                """)
                memory_types = dict(cursor.fetchall())

                # 重要时刻数
                cursor.execute("""
                    SELECT COUNT(*) FROM memories
                    WHERE memory_type = 'important_moment' OR importance >= 0.8
                """)
                important_count = cursor.fetchone()[0]

                # 最近活动
                cursor.execute("""
                    SELECT COUNT(*) FROM memories
                    WHERE timestamp > datetime('now', '-1 day')
                """)
                recent_activity = cursor.fetchone()[0]

                return {
                    "total_memories": total_memories,
                    "memory_types": memory_types,
                    "important_moments": important_count,
                    "recent_activity_24h": recent_activity,
                    "dad_preferences_count": len(self.get_dad_preferences()),
                    "special_memories": len(self.important_moments)
                }

        except Exception as e:
            logger.error(f"❌ 获取记忆摘要失败: {e}")
            return {}

# 导出主类
__all__ = ['DadPreference', 'EnhancedMemoryProcessor', 'MemoryItem']
