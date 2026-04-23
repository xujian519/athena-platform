from __future__ import annotations
"""
上下文压缩机制 - 限制对话历史长度
用于提升AI模型处理效率,减少token消耗
"""

import re
import time
from dataclasses import dataclass


@dataclass
class Message:
    """消息数据结构"""

    role: str  # user, assistant, system
    content: str
    timestamp: float
    message_id: str
    importance: float = 1.0  # 重要性评分 0-1
    keywords: list[str] = None
    summary: str = ""
    token_count: int = 0


@dataclass
class ContextSummary:
    """上下文摘要"""

    original_messages: list[dict]
    compressed_messages: list[dict]
    summary_text: str
    compression_ratio: float
    original_tokens: int
    compressed_tokens: int
    created_at: float


class ContextCompressor:
    """上下文压缩器"""

    def __init__(
        self,
        max_history_length: int = 10,
        max_tokens: int = 4000,
        compression_strategy: str = "smart",
    ):
        """
        初始化上下文压缩器

        Args:
            max_history_length: 最大历史消息数量
            max_tokens: 最大token数量
            compression_strategy: 压缩策略 (smart, recent, importance, summary)
        """
        self.max_history_length = max_history_length
        self.max_tokens = max_tokens
        self.compression_strategy = compression_strategy

        # 重要关键词列表(用于评估消息重要性)
        self.important_keywords = {
            "technical": ["专利", "发明", "申请", "技术", "创新", "设计", "方法", "系统"],
            "business": ["客户", "项目", "费用", "报价", "合同", "合作", "需求", "目标"],
            "action": ["请", "需要", "要求", "希望", "建议", "计划", "执行", "完成"],
            "question": ["什么", "如何", "为什么", "哪里", "什么时候", "谁"],
            "priority": ["紧急", "重要", "关键", "核心", "主要", "首要"],
        }

        # 压缩统计
        self.compression_stats = {
            "total_compressions": 0,
            "original_tokens_sum": 0,
            "compressed_tokens_sum": 0,
            "average_compression_ratio": 0,
            "last_compression_time": None,
        }

    def compress_context(
        self, messages: list[dict], force_compress: bool = False
    ) -> ContextSummary:
        """
        压缩上下文

        Args:
            messages: 原始消息列表
            force_compress: 是否强制压缩

        Returns:
            压缩结果
        """
        if not messages:
            return ContextSummary([], [], "", 1.0, 0, 0, time.time())

        start_time = time.time()

        # 计算原始token数量
        original_tokens = self._estimate_tokens(messages)

        # 检查是否需要压缩
        if not force_compress and self._should_compress(messages, original_tokens):
            compressed_messages = self._apply_compression_strategy(messages)
        else:
            compressed_messages = messages

        # 计算压缩后的token数量
        compressed_tokens = self._estimate_tokens(compressed_messages)

        # 生成摘要
        summary_text = self._generate_summary(messages, compressed_messages)

        # 计算压缩比
        compression_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

        # 更新统计信息
        self._update_stats(original_tokens, compressed_tokens, time.time() - start_time)

        return ContextSummary(
            original_messages=messages,
            compressed_messages=compressed_messages,
            summary_text=summary_text,
            compression_ratio=compression_ratio,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            created_at=time.time(),
        )

    def _should_compress(self, messages: list[dict], token_count: int) -> bool:
        """判断是否需要压缩"""
        # 检查消息数量
        if len(messages) > self.max_history_length:
            return True

        # 检查token数量
        if token_count > self.max_tokens:
            return True

        # 检查时间范围(保留最近2小时的消息)
        current_time = time.time()
        two_hours_ago = current_time - 2 * 3600

        old_messages = [msg for msg in messages if msg.get("timestamp", 0) < two_hours_ago]

        if len(old_messages) > len(messages) * 0.3:  # 超过30%的消息超过2小时
            return True

        return False

    def _apply_compression_strategy(self, messages: list[dict]) -> list[dict]:
        """应用压缩策略"""
        if self.compression_strategy == "smart":
            return self._smart_compress(messages)
        elif self.compression_strategy == "recent":
            return self._recent_compress(messages)
        elif self.compression_strategy == "importance":
            return self._importance_compress(messages)
        elif self.compression_strategy == "summary":
            return self._summary_compress(messages)
        else:
            return self._smart_compress(messages)

    def _smart_compress(self, messages: list[dict]) -> list[dict]:
        """智能压缩策略"""
        # 转换为Message对象
        message_objects = []
        for i, msg in enumerate(messages):
            message_obj = Message(
                role=msg.get("role", "unknown"),
                content=msg.get("content", ""),
                timestamp=msg.get("timestamp", time.time()),
                message_id=msg.get("message_id", f"msg_{i}"),
                importance=self._calculate_importance(msg),
                keywords=self._extract_keywords(msg.get("content", "")),
                token_count=self._estimate_tokens([msg]),
            )
            message_objects.append(message_obj)

        # 分层压缩策略
        current_time = time.time()
        one_hour_ago = current_time - 3600
        half_hour_ago = current_time - 1800

        # 最近30分钟:保留完整消息
        recent_messages = [msg for msg in message_objects if msg.timestamp >= half_hour_ago]

        # 30分钟-1小时:保留重要消息
        medium_messages = [
            msg
            for msg in message_objects
            if half_hour_ago <= msg.timestamp < one_hour_ago and msg.importance >= 0.6
        ]

        # 1小时以上:只保留高重要性消息和摘要
        old_messages = [
            msg
            for msg in message_objects
            if msg.timestamp >= one_hour_ago and msg.importance >= 0.8
        ]

        # 按重要性排序,限制数量
        old_messages.sort(key=lambda x: x.importance, reverse=True)
        old_messages = old_messages[: self.max_history_length // 2]

        # 合并所有消息
        all_messages = recent_messages + medium_messages + old_messages

        # 限制总数量
        if len(all_messages) > self.max_history_length:
            all_messages = all_messages[-self.max_history_length :]

        # 转换回字典格式
        return [self._message_to_dict(msg) for msg in all_messages]

    def _recent_compress(self, messages: list[dict]) -> list[dict]:
        """最近消息压缩策略"""
        # 按时间排序,保留最近的消息
        sorted_messages = sorted(messages, key=lambda x: x.get("timestamp", 0), reverse=True)
        return sorted_messages[: self.max_history_length]

    def _importance_compress(self, messages: list[dict]) -> list[dict]:
        """重要性压缩策略"""
        # 计算重要性评分
        scored_messages = []
        for i, msg in enumerate(messages):
            importance = self._calculate_importance(msg)
            scored_messages.append((importance, i, msg))

        # 按重要性排序
        scored_messages.sort(key=lambda x: x[0], reverse=True)

        # 选择最重要的消息
        selected_messages = scored_messages[: self.max_history_length]

        # 按原始时间顺序排序
        selected_messages.sort(key=lambda x: x[1])

        return [msg[2] for msg in selected_messages]

    def _summary_compress(self, messages: list[dict]) -> list[dict]:
        """摘要压缩策略"""
        if len(messages) <= self.max_history_length:
            return messages

        # 分为三部分:开头、中间、结尾
        if len(messages) <= self.max_history_length:
            return messages

        keep_start = self.max_history_length // 4
        keep_end = self.max_history_length // 2

        # 保留开头的消息
        start_messages = messages[:keep_start]

        # 保留结尾的消息
        end_messages = messages[-keep_end:]

        # 中间消息生成摘要
        middle_messages = messages[keep_start:-keep_end]
        if middle_messages:
            summary_content = self._create_middle_summary(middle_messages)
            summary_message = {
                "role": "system",
                "content": f"[中间对话摘要]: {summary_content}",
                "timestamp": time.time(),
                "message_id": f"summary_{int(time.time())}",
                "is_summary": True,
            }
            return [*start_messages, summary_message, *end_messages]
        else:
            return start_messages + end_messages

    def _calculate_importance(self, message: dict) -> float:
        """计算消息重要性"""
        content = message.get("content", "").lower()
        role = message.get("role", "")
        importance = 0.5  # 基础分数

        # 根据角色调整
        if role == "user":
            importance += 0.2
        elif role == "system":
            importance += 0.1

        # 根据关键词调整
        for category, keywords in self.important_keywords.items():
            found_keywords = [kw for kw in keywords if kw in content]
            if found_keywords:
                if category == "priority":
                    importance += 0.3
                elif category == "action":
                    importance += 0.2
                elif category == "question":
                    importance += 0.15
                elif category in ["technical", "business"]:
                    importance += 0.1

        # 根据消息长度调整
        content_length = len(content)
        if content_length > 200:
            importance += 0.1
        elif content_length < 20:
            importance -= 0.1

        # 根据时间调整(越新的消息越重要)
        timestamp = message.get("timestamp", time.time())
        age_hours = (time.time() - timestamp) / 3600
        if age_hours < 1:
            importance += 0.1
        elif age_hours > 24:
            importance -= 0.1

        return min(1.0, max(0.0, importance))

    def _extract_keywords(self, content: str) -> list[str]:
        """提取关键词"""
        content = content.lower()
        keywords = []

        for category, keyword_list in self.important_keywords.items():
            for keyword in keyword_list:
                if keyword in content:
                    keywords.append(f"{category}:{keyword}")

        return keywords

    def _create_middle_summary(self, messages: list[dict]) -> str:
        """创建中间消息摘要"""
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]

        summary_parts = []

        if user_messages:
            user_topics = []
            for msg in user_messages:
                content = msg.get("content", "")
                # 提取主要话题
                if len(content) > 50:
                    user_topics.append(content[:50] + "...")
                else:
                    user_topics.append(content)
            summary_parts.append(
                f"用户询问了{len(user_messages)}个问题,涉及: {', '.join(user_topics)}"
            )

        if assistant_messages:
            summary_parts.append(f"助手进行了{len(assistant_messages)}次回复")

        return "; ".join(summary_parts)

    def _generate_summary(self, original: list[dict], compressed: list[dict]) -> str:
        """生成压缩摘要"""
        if len(original) == len(compressed):
            return "未进行压缩"

        original_count = len(original)
        compressed_count = len(compressed)
        removed_count = original_count - compressed_count

        summary_parts = [
            f"从{original_count}条消息压缩到{compressed_count}条",
            f"删除了{removed_count}条消息",
            f"压缩率: {(compressed_count/original_count)*100:.1f}%",
        ]

        return "; ".join(summary_parts)

    def _estimate_tokens(self, messages: list[dict]) -> int:
        """估算token数量"""
        total_tokens = 0
        for message in messages:
            content = message.get("content", "")
            # 简单估算:中文每个字符约1.3个token,英文每个单词约1个token
            chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", content))
            english_words = len(re.findall(r"\b\w+\b", content))
            total_tokens += int(chinese_chars * 1.3 + english_words)

            # 加上一些开销
            total_tokens += 10

        return total_tokens

    def _message_to_dict(self, message: Message) -> dict:
        """将Message对象转换为字典"""
        return {
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp,
            "message_id": message.message_id,
            "importance": message.importance,
            "keywords": message.keywords,
            "summary": message.summary,
            "token_count": message.token_count,
        }

    def _update_stats(
        self, original_tokens: int, compressed_tokens: int, compression_time: float
    ) -> None:
        """更新压缩统计"""
        self.compression_stats["total_compressions"] += 1
        self.compression_stats["original_tokens_sum"] += original_tokens
        self.compression_stats["compressed_tokens_sum"] += compressed_tokens
        self.compression_stats["last_compression_time"] = compression_time

        # 计算平均压缩比
        if self.compression_stats["total_compressions"] > 0:
            self.compression_stats["average_compression_ratio"] = (
                self.compression_stats["compressed_tokens_sum"]
                / self.compression_stats["original_tokens_sum"]
            )

    def get_stats(self) -> dict:
        """获取压缩统计信息"""
        return self.compression_stats.copy()

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.compression_stats = {
            "total_compressions": 0,
            "original_tokens_sum": 0,
            "compressed_tokens_sum": 0,
            "average_compression_ratio": 0,
            "last_compression_time": None,
        }

    def set_strategy(self, strategy: str) -> None:
        """设置压缩策略"""
        valid_strategies = ["smart", "recent", "importance", "summary"]
        if strategy in valid_strategies:
            self.compression_strategy = strategy
            print(f"压缩策略已设置为: {strategy}")
        else:
            print(f"无效的压缩策略: {strategy}")

    def set_limits(self, max_history: Optional[int] = None, max_tokens: Optional[int] = None) -> None:
        """设置压缩限制"""
        if max_history is not None:
            self.max_history_length = max_history
        if max_tokens is not None:
            self.max_tokens = max_tokens


# 上下文管理器
class ContextManager:
    """上下文管理器"""

    def __init__(self, compressor: ContextCompressor = None):
        self.compressor = compressor or ContextCompressor()
        self.conversation_contexts: dict[str, list[dict]] = {}
        self.context_summaries: dict[str, list[ContextSummary]] = {}

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_id: Optional[str] = None,
        importance: Optional[float] = None,
    ) -> None:
        """添加消息到上下文"""
        if conversation_id not in self.conversation_contexts:
            self.conversation_contexts[conversation_id] = []

        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "message_id": message_id or f"msg_{int(time.time())}",
            "importance": importance,
        }

        self.conversation_contexts[conversation_id].append(message)

    def get_compressed_context(self, conversation_id: str) -> list[dict]:
        """获取压缩后的上下文"""
        if conversation_id not in self.conversation_contexts:
            return []

        messages = self.conversation_contexts[conversation_id]
        compressed_result = self.compressor.compress_context(messages)

        # 保存摘要
        if conversation_id not in self.context_summaries:
            self.context_summaries[conversation_id] = []

        self.context_summaries[conversation_id].append(compressed_result)

        # 保留最近10个摘要
        if len(self.context_summaries[conversation_id]) > 10:
            self.context_summaries[conversation_id] = self.context_summaries[conversation_id][-10:]

        return compressed_result.compressed_messages

    def get_context_summary(self, conversation_id: str) -> dict | None:
        """获取上下文摘要"""
        if conversation_id not in self.context_summaries:
            return None

        summaries = self.context_summaries[conversation_id]
        if not summaries:
            return None

        latest_summary = summaries[-1]
        return {
            "compression_ratio": latest_summary.compression_ratio,
            "original_tokens": latest_summary.original_tokens,
            "compressed_tokens": latest_summary.compressed_tokens,
            "summary_text": latest_summary.summary_text,
            "message_count": len(latest_summary.original_messages),
        }

    def clear_context(self, conversation_id: str) -> None:
        """清空指定对话的上下文"""
        if conversation_id in self.conversation_contexts:
            del self.conversation_contexts[conversation_id]
        if conversation_id in self.context_summaries:
            del self.context_summaries[conversation_id]

    def get_all_conversations(self) -> list[str]:
        """获取所有对话ID"""
        return list(self.conversation_contexts.keys())


# 全局上下文管理器实例
_global_context_manager: ContextManager | None = None


def get_context_manager() -> ContextManager:
    """获取全局上下文管理器实例"""
    global _global_context_manager
    if _global_context_manager is None:
        _global_context_manager = ContextManager()
    return _global_context_manager


# 示例使用
if __name__ == "__main__":
    # 创建压缩器
    compressor = ContextCompressor(max_history_length=5, compression_strategy="smart")

    # 创建测试消息
    test_messages = [
        {"role": "user", "content": "什么是专利申请?", "timestamp": time.time() - 3600},
        {
            "role": "assistant",
            "content": "专利申请是向专利局提交专利申请的法律程序",
            "timestamp": time.time() - 3500,
        },
        {"role": "user", "content": "申请专利需要什么材料?", "timestamp": time.time() - 3400},
        {
            "role": "assistant",
            "content": "需要申请书、说明书、权利要求书等",
            "timestamp": time.time() - 3300,
        },
        {
            "role": "user",
            "content": "紧急!我需要申请一个发明专利",
            "timestamp": time.time() - 1800,
        },
        {
            "role": "assistant",
            "content": "好的,我来帮您准备发明专利申请材料",
            "timestamp": time.time() - 1700,
        },
        {"role": "user", "content": "请问费用是多少?", "timestamp": time.time() - 100},
        {
            "role": "assistant",
            "content": "发明专利申请费用包括代理费和官费",
            "timestamp": time.time() - 50,
        },
    ]

    # 压缩上下文
    result = compressor.compress_context(test_messages)

    print(f"原始消息数: {len(result.original_messages)}")
    print(f"压缩后消息数: {len(result.compressed_messages)}")
    print(f"压缩比: {result.compression_ratio:.2f}")
    print(f"原始tokens: {result.original_tokens}")
    print(f"压缩后tokens: {result.compressed_tokens}")
    print(f"摘要: {result.summary_text}")

    # 查看统计信息
    stats = compressor.get_stats()
    print(f"\\n压缩统计: {stats}")
