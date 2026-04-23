from __future__ import annotations
"""
多轮对话上下文管理器

实现跨多轮对话的上下文保持和引用解析功能:
1. 对话历史管理
2. 指代消解 (Coreference Resolution)
3. 上下文相关性评分
4. 上下文窗口管理
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ContextStatus(Enum):
    """上下文状态"""

    ACTIVE = "active"  # 活跃状态
    ARCHIVED = "archived"  # 已归档
    EXPIRED = "expired"  # 已过期


@dataclass
class DialogueTurn:
    """对话轮次"""

    turn_id: str  # 轮次ID
    timestamp: float  # 时间戳
    user_message: str  # 用户消息
    bot_response: str  # 机器人响应
    intent: str  # 意图
    entities: dict[str, Any] = field(default_factory=dict)  # 实体
    confidence: float = 0.0  # 置信度
    context_snapshot: dict[str, Any] = field(default_factory=dict)  # 上下文快照


@dataclass
class ContextWindow:
    """上下文窗口"""

    window_id: str  # 窗口ID
    session_id: str  # 会话ID
    turns: list[DialogueTurn] = field(default_factory=list)  # 对话轮次
    current_topic: Optional[str] = None  # 当前话题
    accumulated_entities: dict[str, Any] = field(default_factory=dict)  # 累积实体
    status: ContextStatus = ContextStatus.ACTIVE  # 状态
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    last_updated: float = field(default_factory=lambda: datetime.now().timestamp())
    max_turns: int = 10  # 最大轮次


class ContextRelevanceScorer:
    """上下文相关性评分器"""

    # 指代词模式
    REFERENCE_PATTERNS = {
        "它": ["它", "它们", "这个", "这些", "那个", "那些"],
        "他": ["他", "她", "他们", "她们"],
        "这个": ["这个", "这一", "该"],
        "那个": ["那个", "那一个"],
        "前者": ["前者", "上一个", "刚才提到的"],
        "后者": ["后者", "下一个"],
        "第X个": ["第(\\d+)个", "第(\\d+)项", "第(\\d+)条"],
    }

    # 话题转换关键词
    TOPIC_SWITCH_KEYWORDS = ["等等", "不对", "换个话题", "另外", "先不谈", "暂且", "重新开始"]

    @classmethod
    def calculate_relevance(
        cls, current_message: str, previous_turn: DialogueTurn, current_entities: dict[str, Any]
    ) -> float:
        """
        计算当前消息与历史轮次的相关性

        Args:
            current_message: 当前消息
            previous_turn: 历史轮次
            current_entities: 当前实体

        Returns:
            相关性分数 (0-1)
        """
        score = 0.0

        # 1. 话题连续性 (0.3)
        if previous_turn.intent:
            # 简化版:检查是否属于同一意图类别
            score += 0.3

        # 2. 实体引用 (0.4)
        if cls._has_entity_reference(current_message, previous_turn):
            score += 0.4

        # 3. 时间连续性 (0.2)
        time_diff = datetime.now().timestamp() - previous_turn.timestamp
        if time_diff < 300:  # 5分钟内
            score += 0.2 * (1 - time_diff / 300)

        # 4. 指代词检测 (0.1)
        if cls._has_reference_pronouns(current_message):
            score += 0.1

        return min(score, 1.0)

    @classmethod
    def _has_entity_reference(cls, message: str, turn: DialogueTurn) -> bool:
        """检查是否引用了历史实体"""
        if not turn.entities:
            return False

        # 检查消息中是否包含历史实体
        for entity_value in turn.entities.values():
            if isinstance(entity_value, str) and entity_value in message:
                return True

        return False

    @classmethod
    def _has_reference_pronouns(cls, message: str) -> bool:
        """检测指代词"""
        for pronouns in cls.REFERENCE_PATTERNS.values():
            for pronoun in pronouns:
                if pronoun in message:
                    return True
        return False

    @classmethod
    def detect_topic_switch(cls, message: str, previous_intent: str) -> bool:
        """
        检测话题转换

        Args:
            message: 当前消息
            previous_intent: 前一个意图

        Returns:
            是否切换话题
        """
        # 检查话题转换关键词
        return any(keyword in message for keyword in cls.TOPIC_SWITCH_KEYWORDS)


class CoreferenceResolver:
    """指代消解器"""

    # 指代词与其可能的指代对象
    REFERENCE_MAPPING = {
        # 指代词 -> 实体类型
        "它": ["patent", "document", "result"],
        "他": ["person", "inventor", "applicant"],
        "她": ["person", "inventor", "applicant"],
        "这个": ["patent", "concept", "idea"],
        "那个": ["patent", "concept", "idea"],
    }

    def resolve(self, message: str, context_window: ContextWindow) -> tuple[str, dict[str, Any]]:
        """
        解析消息中的指代词

        Args:
            message: 当前消息
            context_window: 上下文窗口

        Returns:
            (消解后的消息, 提取的实体)
        """
        resolved_message = message
        extracted_entities = {}

        # 遍历历史轮次(从最近到最远)
        for turn in reversed(context_window.turns):
            if not turn.entities:
                continue

            # 检查每种指代词
            for reference, entity_types in self.REFERENCE_MAPPING.items():
                if reference not in message:
                    continue

                # 在历史实体中查找匹配的实体
                for entity_type in entity_types:
                    if entity_type in turn.entities:
                        # 替换指代词为实际实体
                        entity_value = turn.entities[entity_type]
                        if isinstance(entity_value, str):
                            resolved_message = resolved_message.replace(reference, entity_value)
                            extracted_entities[entity_type] = entity_value
                            logger.info(f"指代消解: {reference} -> {entity_value}")
                            break

        return resolved_message, extracted_entities

    def resolve_ordinal_reference(
        self, message: str, context_window: ContextWindow
    ) -> Optional[dict[str, Any]]:
        """
        解析序数引用(如"第3个")

        Args:
            message: 当前消息
            context_window: 上下文窗口

        Returns:
            引用的实体信息
        """
        # 匹配 "第X个" 模式
        match = re.search(r"第(\d+)个", message)
        if not match:
            return None

        index = int(match.group(1)) - 1  # 转换为0-based索引

        # 查找对应的结果
        # 这里简化处理,实际应该从结果缓存中获取
        if 0 <= index < len(context_window.turns):
            return {
                "type": "ordinal_reference",
                "index": index,
                "referenced_turn": context_window.turns[index].turn_id,
            }

        return None


class MultiTurnContextManager:
    """
    多轮对话上下文管理器

    核心功能:
    1. 管理对话历史
    2. 指代消解
    3. 上下文相关性评分
    4. 话题转换检测
    """

    def __init__(
        self,
        max_turns: int = 10,
        context_ttl: int = 3600,  # 上下文过期时间(秒)
        enable_coreference: bool = True,
    ):
        """
        初始化多轮对话上下文管理器

        Args:
            max_turns: 最大保存轮次
            context_ttl: 上下文过期时间
            enable_coreference: 是否启用指代消解
        """
        self.max_turns = max_turns
        self.context_ttl = context_ttl
        self.enable_coreference = enable_coreference

        # 上下文窗口存储 {session_id: ContextWindow}
        self.context_windows: dict[str, ContextWindow] = {}

        # 评分器
        self.scorer = ContextRelevanceScorer()

        # 指代消解器
        self.resolver = CoreferenceResolver() if enable_coreference else None

        logger.info("✅ 多轮对话上下文管理器初始化完成")
        logger.info(f"   最大轮次: {max_turns}")
        logger.info(f"   上下文TTL: {context_ttl}秒")
        logger.info(f"   指代消解: {'启用' if enable_coreference else '禁用'}")

    def create_context(
        self, session_id: str, initial_context: Optional[dict[str, Any]] = None
    ) -> ContextWindow:
        """
        创建新的上下文窗口

        Args:
            session_id: 会话ID
            initial_context: 初始上下文

        Returns:
            上下文窗口
        """
        context = ContextWindow(
            window_id=f"ctx_{session_id}_{datetime.now().timestamp()}",
            session_id=session_id,
            max_turns=self.max_turns,
            status=ContextStatus.ACTIVE,
        )

        if initial_context:
            context.accumulated_entities.update(initial_context)

        self.context_windows[session_id] = context
        logger.info(f"📝 创建上下文窗口: {context.window_id}")

        return context

    def add_turn(
        self,
        session_id: str,
        user_message: str,
        bot_response: str,
        intent: str,
        entities: dict[str, Any],        confidence: float = 0.0,
    ) -> DialogueTurn:
        """
        添加对话轮次

        Args:
            session_id: 会话ID
            user_message: 用户消息
            bot_response: 机器人响应
            intent: 意图
            entities: 实体
            confidence: 置信度

        Returns:
            对话轮次
        """
        context = self.get_context(session_id)
        if not context:
            context = self.create_context(session_id)

        # 创建对话轮次
        turn = DialogueTurn(
            turn_id=f"turn_{session_id}_{len(context.turns)}",
            timestamp=datetime.now().timestamp(),
            user_message=user_message,
            bot_response=bot_response,
            intent=intent,
            entities=entities,
            confidence=confidence,
            context_snapshot=self._capture_context_snapshot(context),
        )

        # 添加到上下文窗口
        context.turns.append(turn)
        context.last_updated = datetime.now().timestamp()

        # 累积实体
        context.accumulated_entities.update(entities)

        # 更新当前话题
        context.current_topic = intent

        # 管理窗口大小
        if len(context.turns) > context.max_turns:
            # 移除最老的轮次
            removed_turn = context.turns.pop(0)
            logger.info(f"🔄 移除过期轮次: {removed_turn.turn_id}")

        logger.info(f"➕ 添加对话轮次: {turn.turn_id} (意图: {intent})")

        return turn

    def get_context(self, session_id: str) -> ContextWindow | None:
        """
        获取上下文窗口

        Args:
            session_id: 会话ID

        Returns:
            上下文窗口或None
        """
        context = self.context_windows.get(session_id)

        if context:
            # 检查是否过期
            if self._is_context_expired(context):
                logger.info(f"⏰ 上下文已过期: {session_id}")
                context.status = ContextStatus.EXPIRED
                return None

        return context

    def resolve_coreference(self, session_id: str, message: str) -> tuple[str, dict[str, Any]]:
        """
        解析指代词

        Args:
            session_id: 会话ID
            message: 当前消息

        Returns:
            (消解后的消息, 提取的实体)
        """
        if not self.enable_coreference or not self.resolver:
            return message, {}

        context = self.get_context(session_id)
        if not context or not context.turns:
            return message, {}

        # 执行指代消解
        resolved_message, extracted_entities = self.resolver.resolve(message, context)

        # 检查序数引用
        ordinal_ref = self.resolver.resolve_ordinal_reference(message, context)
        if ordinal_ref:
            extracted_entities["ordinal_reference"] = ordinal_ref

        return resolved_message, extracted_entities

    def detect_topic_switch(self, session_id: str, message: str, current_intent: str) -> bool:
        """
        检测话题转换

        Args:
            session_id: 会话ID
            message: 当前消息
            current_intent: 当前意图

        Returns:
            是否切换话题
        """
        context = self.get_context(session_id)
        if not context or not context.turns:
            return False

        previous_intent = context.turns[-1].intent

        return self.scorer.detect_topic_switch(message, previous_intent)

    def calculate_context_relevance(
        self, session_id: str, message: str, current_entities: dict[str, Any]
    ) -> list[tuple[int, float]]:
        """
        计算与历史轮次的相关性

        Args:
            session_id: 会话ID
            message: 当前消息
            current_entities: 当前实体

        Returns:
            [(轮次索引, 相关性分数)] 列表,按相关性降序排序
        """
        context = self.get_context(session_id)
        if not context or not context.turns:
            return []

        relevance_scores = []

        for idx, turn in enumerate(context.turns):
            score = self.scorer.calculate_relevance(message, turn, current_entities)
            relevance_scores.append((idx, score))

        # 按相关性降序排序
        relevance_scores.sort(key=lambda x: x[1], reverse=True)

        return relevance_scores

    def get_conversation_history(
        self, session_id: str, max_turns: Optional[int] = None
    ) -> list[DialogueTurn]:
        """
        获取对话历史

        Args:
            session_id: 会话ID
            max_turns: 最大返回轮次

        Returns:
            对话轮次列表
        """
        context = self.get_context(session_id)
        if not context:
            return []

        turns = context.turns

        if max_turns:
            turns = turns[-max_turns:]

        return turns

    def clear_context(self, session_id: str) -> bool:
        """
        清除上下文

        Args:
            session_id: 会话ID

        Returns:
            是否成功
        """
        if session_id in self.context_windows:
            del self.context_windows[session_id]
            logger.info(f"🗑️ 清除上下文: {session_id}")
            return True

        return False

    def get_context_summary(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        获取上下文摘要

        Args:
            session_id: 会话ID

        Returns:
            上下文摘要
        """
        context = self.get_context(session_id)
        if not context:
            return None

        return {
            "window_id": context.window_id,
            "session_id": context.session_id,
            "turns_count": len(context.turns),
            "current_topic": context.current_topic,
            "accumulated_entities": context.accumulated_entities,
            "status": context.status.value,
            "created_at": context.created_at,
            "last_updated": context.last_updated,
            "recent_intents": [t.intent for t in context.turns[-5:]],
        }

    def _capture_context_snapshot(self, context: ContextWindow) -> dict[str, Any]:
        """捕获上下文快照"""
        return {
            "current_topic": context.current_topic,
            "accumulated_entities": context.accumulated_entities.copy(),
            "turns_count": len(context.turns),
        }

    def _is_context_expired(self, context: ContextWindow) -> bool:
        """检查上下文是否过期"""
        now = datetime.now().timestamp()
        return (now - context.last_updated) > self.context_ttl

    def cleanup_expired_contexts(self) -> int:
        """
        清理过期上下文

        Returns:
            清理的上下文数量
        """
        expired_sessions = []

        for session_id, context in self.context_windows.items():
            if self._is_context_expired(context):
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.context_windows[session_id]

        if expired_sessions:
            logger.info(f"🧹 清理过期上下文: {len(expired_sessions)}个")

        return len(expired_sessions)


# 单例模式
_context_manager: MultiTurnContextManager | None = None


def get_multi_turn_context_manager() -> MultiTurnContextManager:
    """获取多轮对话上下文管理器单例"""
    global _context_manager
    if _context_manager is None:
        _context_manager = MultiTurnContextManager()
    return _context_manager
