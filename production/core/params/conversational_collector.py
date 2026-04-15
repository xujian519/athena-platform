"""
对话式参数收集器

通过多轮对话收集缺失的参数,提升参数填充有效性。
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .parameter_validator import ParameterValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class CollectionState:
    """参数收集状态"""

    session_id: str  # 会话ID
    intent: str  # 当前意图
    collected_params: dict[str, Any]  # 已收集的参数
    current_question: str | None  # 当前问题
    question_count: int  # 已提问次数
    start_time: datetime  # 开始时间
    last_activity: datetime  # 最后活动时间
    completed: bool = False  # 是否完成

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "intent": self.intent,
            "collected_params": self.collected_params,
            "current_question": self.current_question,
            "question_count": self.question_count,
            "start_time": self.start_time.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CollectionState":
        """从字典创建"""
        return cls(
            session_id=data["session_id"],
            intent=data["intent"],
            collected_params=data["collected_params"],
            current_question=data.get("current_question"),
            question_count=data.get("question_count", 0),
            start_time=datetime.fromisoformat(data["start_time"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            completed=data.get("completed", False),
        )


@dataclass
class CollectionContext:
    """收集上下文"""

    max_questions: int = 5  # 最大提问次数
    timeout_seconds: int = 300  # 超时时间(秒)
    friendly_mode: bool = True  # 友好模式
    show_examples: bool = True  # 显示示例


class ConversationalCollector:
    """
    对话式参数收集器

    通过多轮对话自然地收集缺失的参数,而不是直接拒绝请求。
    """

    def __init__(self, validator: ParameterValidator):
        """
        初始化收集器

        Args:
            validator: 参数验证器
        """
        self.validator = validator
        self.active_sessions: dict[str, CollectionState] = {}
        self.context = CollectionContext()

    def start_collection(
        self,
        session_id: str,
        intent: str,
        initial_params: dict[str, Any],
        context: CollectionContext | None = None,
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        开始参数收集

        Args:
            session_id: 会话ID
            intent: 意图类型
            initial_params: 初始参数
            context: 收集上下文

        Returns:
            (complete, response, params)
            - complete: 是否已完成收集
            - response: 响应文本(问题或确认信息)
            - params: 当前参数集合
        """
        if context:
            self.context = context

        # 验证初始参数
        validation_result = self.validator.validate(intent, initial_params)

        if validation_result.valid:
            # 参数完整,直接返回
            return True, "✅ 参数完整,开始处理。", initial_params

        # 创建收集状态
        state = CollectionState(
            session_id=session_id,
            intent=intent,
            collected_params=initial_params.copy(),
            current_question=None,
            question_count=0,
            start_time=datetime.now(),
            last_activity=datetime.now(),
            completed=False,
        )

        self.active_sessions[session_id] = state

        # 生成第一个问题
        response = self._generate_next_question(state, validation_result)

        return False, response, state.collected_params

    def continue_collection(
        self, session_id: str, user_message: str
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        继续参数收集

        Args:
            session_id: 会话ID
            user_message: 用户回复

        Returns:
            (complete, response, params)
        """
        # 获取会话状态
        state = self.active_sessions.get(session_id)
        if not state:
            # 没有活跃的收集会话,直接返回
            return True, user_message, {}

        # 检查超时
        if self._is_timeout(state):
            logger.info(f"会话 {session_id} 超时")
            del self.active_sessions[session_id]
            return True, user_message, {}

        # 检查提问次数限制
        if state.question_count >= self.context.max_questions:
            logger.info(f"会话 {session_id} 达到最大提问次数")
            del self.active_sessions[session_id]
            return True, "📝 已收集部分信息,我将使用现有参数继续处理。", state.collected_params

        # 解析用户回复,提取参数
        extracted_params = self._extract_params_from_message(state.intent, user_message)

        # 更新已收集的参数
        state.collected_params.update(extracted_params)
        state.last_activity = datetime.now()

        # 重新验证
        validation_result = self.validator.validate(state.intent, state.collected_params)

        if validation_result.valid:
            # 收集完成
            state.completed = True
            del self.active_sessions[session_id]

            # 生成确认信息
            confirmation = self._generate_confirmation(state)
            return True, confirmation, state.collected_params

        # 继续提问
        state.question_count += 1
        response = self._generate_next_question(state, validation_result)
        state.current_question = response

        return False, response, state.collected_params

    def cancel_collection(self, session_id: str) -> bool:
        """
        取消参数收集

        Args:
            session_id: 会话ID

        Returns:
            是否成功取消
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False

    def get_session_state(self, session_id: str) -> CollectionState | None:
        """获取会话状态"""
        return self.active_sessions.get(session_id)

    def _generate_next_question(
        self, state: CollectionState, validation_result: ValidationResult
    ) -> str:
        """生成下一个问题"""
        # 获取缺失的参数
        missing = validation_result.missing_params

        if not missing:
            # 没有缺失参数但有无效参数
            if validation_result.invalid_params:
                invalid_list = ", ".join(validation_result.invalid_params)
                return f"⚠️ 以下参数格式不正确:{invalid_list}。\n" + self._get_first_suggestion(
                    validation_result
                )

        # 生成友好问题
        first_missing = missing[0]
        param_desc = self.validator.get_param_description(state.intent, first_missing)

        if self.context.friendly_mode:
            return self._friendly_question(first_missing, param_desc)
        else:
            return f"请提供{param_desc}。"

    def _friendly_question(self, param_name: str, param_desc: str) -> str:
        """生成友好的问题"""
        questions = {
            "patent_number": "📋 请问您要分析的专利号是多少?(例如:CN202310123456)",
            "invention_title": "💡 请问您的发明名称是什么?",
            "technical_field": "🔬 请问这项发明属于哪个技术领域?",
            "oa_number": "📨 请问审查意见通知书的编号是多少?",
            "rejection_reasons": "📝 请问审查员的主要驳回理由是什么?",
            "keywords": "🔍 请问您想搜索哪些关键词?",
            "question": "❓ 请问您具体想咨询什么法律问题?",
            "task": "🎯 请问您想完成什么任务?",
        }

        return questions.get(param_name, f"请提供{param_desc}。")

    def _generate_confirmation(self, state: CollectionState) -> str:
        """生成参数收集完成的确认信息"""
        params_text = ", ".join([f"{k}={v}" for k, v in state.collected_params.items()])

        return (
            f"✅ 信息收集完成!\n" f"📋 已收集参数: {params_text}\n" f"🚀 现在开始处理您的请求..."
        )

    def _extract_params_from_message(self, intent: str, message: str) -> dict[str, Any]:
        """
        从用户消息中提取参数

        这是一个简化实现,实际可以使用LLM来提取。
        """
        import re

        params = {}

        # 根据意图类型和参数定义提取
        param_defs = self.validator.intent_params.get(intent, [])

        for param_def in param_defs:
            # 简单的提取逻辑
            if param_def.validation_pattern:
                # 尝试匹配正则表达式
                match = re.search(param_def.validation_pattern, message)
                if match:
                    params[param_def.name] = match.group(0)

        # 如果是简单字符串参数,尝试提取引号内容
        quoted_pattern = r'["\']([^"\']+)["\']'
        quoted_matches = re.findall(quoted_pattern, message)
        if quoted_matches:
            # 将引号内容分配给缺失的参数
            for param_def in param_defs:
                if param_def.name not in params and quoted_matches:
                    params[param_def.name] = quoted_matches.pop(0)

        return params

    def _get_first_suggestion(self, validation_result: ValidationResult) -> str:
        """获取第一条建议"""
        if validation_result.suggestions:
            first_key = next(iter(validation_result.suggestions))
            return validation_result.suggestions[first_key]
        return ""

    def _is_timeout(self, state: CollectionState) -> bool:
        """检查是否超时"""
        elapsed = (datetime.now() - state.last_activity).total_seconds()
        return elapsed > self.context.timeout_seconds

    def cleanup_expired_sessions(self) -> Any:
        """清理过期的会话"""
        expired = [sid for sid, state in self.active_sessions.items() if self._is_timeout(state)]

        for sid in expired:
            logger.info(f"清理过期会话: {sid}")
            del self.active_sessions[sid]

        return len(expired)
