#!/usr/bin python3
from __future__ import annotations
"""
会话搜索系统 - 语义搜索 + 关键词搜索

基于 Hermes Agent 的设计理念，实现跨会话搜索和历史记录恢复。
支持语义搜索、关键词搜索和混合搜索模式。

核心特性:
1. 语义搜索 - 基于向量相似度
2. 关键词搜索 - 精确匹配
3. 跨会话引用
4. 历史记录恢复

作者: Athena平台团队
创建时间: 2026-03-19
版本: v1.0.0
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 默认存储路径
DEFAULT_SEARCH_DIR = Path(__file__).parent / "data" / "sessions"


@dataclass
class SessionMessage:
    """会话消息"""

    message_id: str
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "metadata": self.metadata,
        }


@dataclass
class Session:
    """会话"""

    session_id: str
    name: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    messages: list[SessionMessage] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": len(self.messages),
            "metadata": self.metadata,
        }


@dataclass
class SearchResult:
    """搜索结果"""

    message: SessionMessage
    relevance_score: float
    match_type: str  # semantic, keyword, hybrid
    matched_terms: list[str] = field(default_factory=list)
    context: str = ""  # 前后文上下文

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message.message_id,
            "role": self.message.role,
            "content_preview": self.message.content[:200] + "...",
            "relevance_score": self.relevance_score,
            "match_type": self.match_type,
            "matched_terms": self.matched_terms,
            "context": self.context,
            "timestamp": self.message.timestamp.isoformat(),
            "session_id": self.message.session_id,
        }


class SessionSearchEngine:
    """
    会话搜索引擎

    支持多种搜索模式和历史记录恢复。
    """

    def __init__(self, storage_dir: Path | None = None):
        """
        初始化搜索引擎

        Args:
            storage_dir: 存储目录
        """
        self.storage_dir = storage_dir or DEFAULT_SEARCH_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.sessions: dict[str, Session] = {}
        self._load_sessions()

        logger.info(f"🔍 SessionSearchEngine 初始化完成 (已加载 {len(self.sessions)} 个会话)")

    def _load_sessions(self) -> None:
        """加载会话数据"""
        for session_file in self.storage_dir.glob("session_*.json"):
            try:
                with open(session_file, encoding="utf-8") as f:
                    data = json.load(f)

                messages = []
                for msg_data in data.get("messages", []):
                    msg = SessionMessage(
                        message_id=msg_data["message_id"],
                        role=msg_data["role"],
                        content=msg_data["content"],
                        timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                        session_id=msg_data.get("session_id", ""),
                        metadata=msg_data.get("metadata", {}),
                    )
                    messages.append(msg)

                session = Session(
                    session_id=data["session_id"],
                    name=data.get("name", ""),
                    created_at=datetime.from_isoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"]),
                    messages=messages,
                    metadata=data.get("metadata", {}),
                )
                self.sessions[session.session_id] = session

            except Exception as e:
                logger.warning(f"⚠️ 加载会话失败: {session_file} - {e}")

    def _save_session(self, session: Session) -> None:
        """保存会话数据"""
        session_file = self.storage_dir / f"session_{session.session_id}.json"
        try:
            data = {
                "session_id": session.session_id,
                "name": session.name,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "messages": [m.to_dict() for m in session.messages],
                "metadata": session.metadata,
            }
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存会话失败: {e}")

    def create_session(self, name: str = "") -> Session:
        """
        创建新会话

        Args:
            name: 会话名称

        Returns:
            Session: 新创建的会话
        """
        import uuid

        session_id = f"session_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        session = Session(
            session_id=session_id,
            name=name,
        )
        self.sessions[session_id] = session
        self._save_session(session)

        logger.info(f"📝 创建新会话: {session_id}")
        return session

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> SessionMessage | None:
        """
        添加消息到会话

        Args:
            session_id: 会话ID
            role: 角色 (user/assistant/system)
            content: 消息内容
            metadata: 元数据

        Returns:
            SessionMessage | None: 添加的消息
        """
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"⚠️ 会话不存在: {session_id}")
            return None

        import uuid

        message_id = f"msg_{uuid.uuid4().hex[:8]}"

        message = SessionMessage(
            message_id=message_id,
            role=role,
            content=content,
            session_id=session_id,
            metadata=metadata or {},
        )

        session.messages.append(message)
        session.updated_at = datetime.now()
        self._save_session(session)

        logger.debug(f"📝 添加消息: {message_id} 到会话 {session_id}")
        return message

    def search(
        self,
        query: str,
        mode: str = "hybrid",
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """
        搜索会话内容

        Args:
            query: 搜索查询
            mode: 搜索模式 (semantic/keyword/hybrid)
            session_id: 限定会话ID (None表示搜索全部)
            limit: 返回结果数量限制

        Returns:
            list[SearchResult]: 搜索结果
        """
        results: list[SearchResult] = []

        # 获取要搜索的会话
        sessions_to_search = (
            [self.sessions[session_id]]
            if session_id and session_id in self.sessions
            else list(self.sessions.values())
        )

        for session in sessions_to_search:
            for message in session.messages:
                score = 0.0
                match_type = ""
                matched_terms: list[str] = []

                if mode in ("keyword", "hybrid"):
                    kw_score, kw_terms = self._keyword_search(message.content, query)
                    if kw_score > 0:
                        score += kw_score
                        matched_terms.extend(kw_terms)
                        match_type = "keyword"

                if mode in ("semantic", "hybrid"):
                    sem_score, sem_terms = self._semantic_search(message.content, query)
                    if sem_score > 0:
                        score += sem_score
                        matched_terms.extend(sem_terms)
                        if not match_type:
                            match_type = "semantic"
                        elif match_type == "keyword":
                            match_type = "hybrid"

                if score > 0:
                    # 提取上下文
                    context = self._extract_context(message.content, query)

                    result = SearchResult(
                        message=message,
                        relevance_score=score,
                        match_type=match_type,
                        matched_terms=list(set(matched_terms)),
                        context=context,
                    )
                    results.append(result)

        # 按相关度排序
        results.sort(key=lambda x: -x.relevance_score)

        # 返回前N个结果
        return results[:limit]

    def _keyword_search(self, content: str, query: str) -> tuple[float, list[str]]:
        """
        关键词搜索

        Args:
            content: 消息内容
            query: 搜索查询

        Returns:
            tuple[float, list[str]]: (相关度分数, 匹配的关键词)
        """
        # 分词
        query_terms = set(re.findall(r"\w+", query.lower()))
        content_lower = content.lower()
        matched_terms = []

        for term in query_terms:
            if len(term) >= 2 and term in content_lower:
                matched_terms.append(term)

        if not matched_terms:
            return 0.0, []

        # 计算相关度
        score = len(matched_terms) / max(len(query_terms), 1)
        return min(1.0, score), matched_terms

    def _semantic_search(self, content: str, query: str) -> tuple[float, list[str]]:
        """
        语义搜索 (简化实现)

        实际项目应使用向量嵌入。

        Args:
            content: 消息内容
            query: 搜索查询

        Returns:
            tuple[float, list[str]]: (相关度分数, 匹配的语义概念)
        """
        # 简化的语义匹配 (基于关键词扩展)
        semantic_patterns = {
            "专利": ["发明", "实用新型", "外观设计", "申请", "授权"],
            "法律": ["法规", "条文", "诉讼", "合同", "协议"],
            "分析": ["评估", "研究", "调查", "检查"],
            "检索": ["搜索", "查找", "查询", "寻找"],
        }

        content_lower = content.lower()
        query_lower = query.lower()
        matched_concepts = []

        for key, synonyms in semantic_patterns.items():
            if key in query_lower:
                for syn in synonyms:
                    if syn in content_lower:
                        matched_concepts.append(syn)

        if not matched_concepts:
            return 0.0, []

        score = min(1.0, len(matched_concepts) * 0.2)
        return score, matched_concepts

    def _extract_context(self, content: str, query: str, context_size: int = 100) -> str:
        """
        提取上下文

        Args:
            content: 消息内容
            query: 搜索查询
            context_size: 上下文大小 (字符)

        Returns:
            str: 提取的上下文
        """
        # 找到查询词在内容中的位置
        query_lower = query.lower()
        content_lower = content.lower()
        pos = content_lower.find(query_lower)

        if pos == -1:
            # 查找任何查询词
            for term in query_lower.split():
                pos = content_lower.find(term)
                if pos != -1:
                    break

        if pos == -1:
            return content[: context_size * 2]

        # 提取上下文
        start = max(0, pos - context_size)
        end = min(len(content), pos + len(query) + context_size)

        context = content[start:end]
        if start > 0:
            context = "..." + context
        if end < len(content):
            context = context + "..."

        return context

    def get_session(self, session_id: str) -> Session | None:
        """获取会话"""
        return self.sessions.get(session_id)

    def get_all_sessions(self, limit: int = 50) -> list[dict[str, Any]]:
        """获取所有会话列表"""
        sessions = sorted(
            self.sessions.values(),
            key=lambda s: s.updated_at,
            reverse=True,
        )
        return [s.to_dict() for s in sessions[:limit]]

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            session_file = self.storage_dir / f"session_{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            logger.info(f"🗑️ 删除会话: {session_id}")
            return True
        return False

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        total_messages = sum(len(s.messages) for s in self.sessions.values())

        return {
            "total_sessions": len(self.sessions),
            "total_messages": total_messages,
            "avg_messages_per_session": (
                total_messages / len(self.sessions) if self.sessions else 0
            ),
            "sessions": self.get_all_sessions(limit=10),
        }


# ========================================
# 全局搜索引擎实例
# ========================================
_global_search_engine: SessionSearchEngine | None = None


def get_session_search_engine(storage_dir: Path | None = None) -> SessionSearchEngine:
    """获取全局会话搜索引擎"""
    global _global_search_engine
    if _global_search_engine is None:
        _global_search_engine = SessionSearchEngine(storage_dir)
    return _global_search_engine


__all__ = [
    "SearchResult",
    "Session",
    "SessionMessage",
    "SessionSearchEngine",
    "get_session_search_engine",
]
