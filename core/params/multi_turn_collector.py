#!/usr/bin/env python3
"""
多轮对话参数收集器
Multi-turn Dialogue Parameter Collector

智能地在多轮对话中收集和补全参数,通过上下文理解和主动提问
实现高完成率的参数收集功能
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


logger = logging.getLogger(__name__)


class ParameterStatus(Enum):
    """参数状态枚举"""

    MISSING = "missing"  # 缺失
    PARTIAL = "partial"  # 部分收集
    COLLECTED = "collected"  # 已收集
    CONFIRMED = "confirmed"  # 已确认
    INVALID = "invalid"  # 无效


class QuestionType(Enum):
    """问题类型枚举"""

    DIRECT = "direct"  # 直接询问
    CONFIRMATION = "confirmation"  # 确认问题
    CLARIFICATION = "clarification"  # 澄清问题
    SUGGESTION = "suggestion"  # 建议问题


@dataclass
class ParameterRequirement:
    """参数需求定义"""

    name: str  # 参数名称
    param_type: str  # 参数类型
    required: bool = True  # 是否必需
    default_value: Any = None  # 默认值
    validation_pattern: str | None = None  # 验证正则
    description: str = ""  # 参数描述
    examples: list[str] = field(default_factory=list)  # 示例值
    dependencies: list[str] = field(default_factory=list)  # 依赖的其他参数


@dataclass
class ParameterState:
    """参数状态"""

    requirement: ParameterRequirement
    status: ParameterStatus = ParameterStatus.MISSING
    value: Any = None
    confidence: float = 0.0  # 置信度
    source: str = ""  # 来源(用户输入/推断/默认)
    validation_errors: list[str] = field(default_factory=list)
    extraction_time: datetime | None = None


@dataclass
class CollectionQuestion:
    """收集问题"""

    question_type: QuestionType
    question_text: str
    parameter_name: str
    priority: int = 1  # 优先级(1-10)
    options: list[str] | None = None  # 选项
    hints: list[str] = field(default_factory=list)  # 提示信息


@dataclass
class CollectionResult:
    """收集结果"""

    parameters: dict[str, Any]  # 收集到的参数
    completion_rate: float  # 完成率(0-1)
    missing_required: list[str]  # 缺失的必需参数
    questions: list[CollectionQuestion]  # 需要问的问题
    collection_round: int  # 当前收集轮次
    is_complete: bool  # 是否完成
    needs_clarification: bool  # 是否需要澄清
    confidence_score: float  # 整体置信度


class MultiTurnParameterCollector:
    """
    多轮对话参数收集器

    核心功能:
    1. 上下文感知的参数提取
    2. 智能问题生成
    3. 参数验证和确认
    4. 多轮对话状态管理
    """

    def __init__(self):
        """初始化收集器"""
        self.name = "多轮对话参数收集器 v1.0"
        self.version = "1.0.0"

        # 参数需求定义
        self.parameter_requirements: dict[str, ParameterRequirement] = {}

        # 当前参数状态
        self.parameter_states: dict[str, ParameterState] = {}

        # 对话历史
        self.conversation_history: list[dict[str, Any]] = []

        # 收集轮次
        self.collection_round = 0

        # 统计信息
        self.stats = {
            "total_collections": 0,
            "completed_collections": 0,
            "total_questions_asked": 0,
            "avg_rounds_to_complete": 0.0,
            "parameter_hit_rates": {},
        }

        # 意图-参数映射
        self.intent_parameter_map: dict[str, list[str]] = {}

        # 初始化默认参数需求
        self._initialize_default_requirements()

    def _initialize_default_requirements(self) -> Any:
        """初始化默认参数需求定义"""
        # 专利分析相关参数
        self.register_parameter(
            ParameterRequirement(
                name="patent_number",
                param_type="string",
                required=True,
                validation_pattern=r"^(CN|US|EP|JP|WO|KR)[A-Z0-9]+$",
                description="专利号",
                examples=["CN123456789A", "US2023001234"],
            )
        )

        self.register_parameter(
            ParameterRequirement(
                name="analysis_depth",
                param_type="string",
                required=False,
                default_value="standard",
                description="分析深度",
                examples=["quick", "standard", "detailed"],
            )
        )

        # 编程助手相关参数
        self.register_parameter(
            ParameterRequirement(
                name="language",
                param_type="string",
                required=True,
                description="编程语言",
                examples=["Python", "JavaScript", "Java", "Go"],
            )
        )

        self.register_parameter(
            ParameterRequirement(
                name="requirements", param_type="string", required=True, description="功能需求"
            )
        )

        # 法律咨询相关参数
        self.register_parameter(
            ParameterRequirement(
                name="query", param_type="string", required=True, description="法律问题"
            )
        )

        self.register_parameter(
            ParameterRequirement(
                name="domain",
                param_type="string",
                required=False,
                description="法律领域",
                examples=["合同法", "知识产权", "劳动法"],
            )
        )

    def register_parameter(self, requirement: ParameterRequirement) -> Any:
        """
        注册参数需求

        Args:
            requirement: 参数需求定义
        """
        self.parameter_requirements[requirement.name] = requirement
        self.parameter_states[requirement.name] = ParameterState(requirement=requirement)
        logger.debug(f"注册参数需求: {requirement.name}")

    def register_intent_parameters(self, intent: str, parameters: list[str]) -> Any:
        """
        注册意图-参数映射

        Args:
            intent: 意图名称
            parameters: 参数列表
        """
        self.intent_parameter_map[intent] = parameters
        logger.debug(f"注册意图参数映射: {intent} -> {parameters}")

    async def collect_parameters(
        self, intent: str, user_input: str, context: dict[str, Any] | None = None
    ) -> CollectionResult:
        """
        收集参数

        Args:
            intent: 用户意图
            user_input: 用户输入
            context: 上下文信息

        Returns:
            CollectionResult: 收集结果
        """
        context = context or {}
        self.collection_round += 1

        # 添加到对话历史
        self.conversation_history.append(
            {
                "round": self.collection_round,
                "intent": intent,
                "input": user_input,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # 获取需要的参数
        required_params = self.intent_parameter_map.get(intent, [])
        if not required_params:
            # 如果没有映射,尝试从所有必需参数中推断
            required_params = [
                name for name, req in self.parameter_requirements.items() if req.required
            ]

        # 从用户输入中提取参数
        extracted = await self._extract_parameters_from_input(user_input, intent, context)

        # 更新参数状态
        for param_name, value in extracted.items():
            if param_name in self.parameter_states:
                state = self.parameter_states[param_name]
                state.value = value
                state.status = ParameterStatus.COLLECTED
                state.confidence = value.get("confidence", 0.8) if isinstance(value, dict) else 0.8
                state.source = "user_input"
                state.extraction_time = datetime.now()

        # 验证参数
        await self._validate_parameters(required_params)

        # 计算完成率
        result = self._calculate_collection_result(required_params)

        # 更新统计
        self.stats["total_collections"] += 1
        self.stats["total_questions_asked"] += len(result.questions)

        if result.is_complete:
            self.stats["completed_collections"] += 1

        return result

    async def _extract_parameters_from_input(
        self, user_input: str, intent: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        从用户输入中提取参数

        Args:
            user_input: 用户输入文本
            intent: 意图
            context: 上下文

        Returns:
            提取的参数字典
        """
        extracted = {}

        # 1. 基于规则的提取
        rule_based = self._extract_by_rules(user_input, intent)
        extracted.update(rule_based)

        # 2. 基于上下文的推断
        context_based = self._extract_from_context(user_input, context)
        extracted.update(context_based)

        # 3. 从历史对话中提取
        history_based = await self._extract_from_history(user_input)
        extracted.update(history_based)

        return extracted

    def _extract_by_rules(self, user_input: str, intent: str) -> dict[str, Any]:
        """基于规则提取参数"""
        extracted = {}
        text = user_input.lower()

        # 专利号提取
        patent_pattern = r"(?:专利号?|patent\s*(?:no\.?|number))?\s*[:::]?\s*([A-Z]{2}\d+[A-Z]?)"
        patent_match = re.search(patent_pattern, user_input, re.IGNORECASE)
        if patent_match:
            extracted["patent_number"] = patent_match.group(1).upper()

        # 编程语言提取
        language_keywords = {
            "python": "Python",
            "javascript": "JavaScript",
            "java": "Java",
            "go": "Go",
            "rust": "Rust",
            r"c\+\+": "C++",
            "c#": "C#",
            "typescript": "TypeScript",
        }

        for keyword, language in language_keywords.items():
            if keyword in text:
                extracted["language"] = language
                break

        # 分析深度提取
        depth_keywords = {
            "快速": "quick",
            "简单": "quick",
            "详细": "detailed",
            "深入": "detailed",
            "全面": "detailed",
        }
        for keyword, depth in depth_keywords.items():
            if keyword in text:
                extracted["analysis_depth"] = depth
                break

        return extracted

    def _extract_from_context(self, user_input: str, context: dict[str, Any]) -> dict[str, Any]:
        """从上下文中提取参数"""
        extracted = {}

        # 从之前的参数中引用
        if "previous_parameters" in context:
            prev_params = context["previous_parameters"]
            # 检查是否有代词引用
            if any(word in user_input for word in ["它", "这个", "该", "此"]):
                # 可能引用之前的参数
                if "patent_number" in prev_params:
                    extracted["patent_number"] = prev_params["patent_number"]

        # 从会话状态中提取
        if "session_state" in context:
            session_state = context["session_state"]
            if "current_patent" in session_state:
                extracted["patent_number"] = session_state["current_patent"]

        return extracted

    async def _extract_from_history(self, user_input: str) -> dict[str, Any]:
        """从历史对话中提取参数"""
        extracted = {}

        # 查找最近的参数提及
        for entry in reversed(self.conversation_history[-5:]):
            if "parameters" in entry:
                for param_name, param_value in entry["parameters"].items():
                    if param_value and param_name not in extracted:
                        extracted[param_name] = param_value

        return extracted

    async def _validate_parameters(self, required_params: list[str]):
        """验证参数"""
        for param_name in required_params:
            if param_name not in self.parameter_states:
                continue

            state = self.parameter_states[param_name]
            requirement = state.requirement

            # 检查是否缺失
            if state.value is None:
                state.status = ParameterStatus.MISSING
                continue

            # 检查类型
            if requirement.validation_pattern:
                pattern = requirement.validation_pattern
                value_str = str(state.value)
                if not re.match(pattern, value_str):
                    state.validation_errors.append(f"值 '{state.value}' 不符合格式要求")
                    state.status = ParameterStatus.INVALID
                    continue

            # 验证通过
            if state.status == ParameterStatus.COLLECTED:
                state.status = ParameterStatus.CONFIRMED

    def _calculate_collection_result(self, required_params: list[str]) -> CollectionResult:
        """计算收集结果"""
        # 统计参数状态
        collected_count = 0
        missing_required = []
        total_confidence = 0.0

        for param_name in required_params:
            if param_name not in self.parameter_states:
                missing_required.append(param_name)
                continue

            state = self.parameter_states[param_name]

            if state.status in [ParameterStatus.COLLECTED, ParameterStatus.CONFIRMED]:
                collected_count += 1
                total_confidence += state.confidence
            elif state.requirement.required and state.status == ParameterStatus.MISSING:
                missing_required.append(param_name)

        # 计算完成率
        total_required = len(required_params)
        completion_rate = collected_count / total_required if total_required > 0 else 0

        # 生成需要问的问题
        questions = self._generate_questions(missing_required)

        # 计算整体置信度
        confidence_score = total_confidence / collected_count if collected_count > 0 else 0

        return CollectionResult(
            parameters={
                name: state.value
                for name, state in self.parameter_states.items()
                if state.value is not None
            },
            completion_rate=completion_rate,
            missing_required=missing_required,
            questions=questions,
            collection_round=self.collection_round,
            is_complete=len(missing_required) == 0 and completion_rate >= 0.85,
            needs_clarification=len(
                [q for q in questions if q.question_type == QuestionType.CLARIFICATION]
            )
            > 0,
            confidence_score=confidence_score,
        )

    def _generate_questions(self, missing_params: list[str]) -> list[CollectionQuestion]:
        """生成收集问题"""
        questions = []

        for param_name in missing_params:
            if param_name not in self.parameter_requirements:
                continue

            requirement = self.parameter_requirements[param_name]

            # 生成问题文本
            if requirement.examples:
                question_text = f"请提供{requirement.description}({requirement.name})。例如:{', '.join(requirement.examples[:3])})"
            else:
                question_text = f"请提供{requirement.description}({requirement.name})"

            question = CollectionQuestion(
                question_type=QuestionType.DIRECT,
                question_text=question_text,
                parameter_name=param_name,
                priority=10 if requirement.required else 5,
                options=requirement.examples if len(requirement.examples) <= 5 else None,
            )

            questions.append(question)

        # 按优先级排序
        questions.sort(key=lambda q: q.priority, reverse=True)

        return questions

    async def confirm_parameters(
        self, intent: str, parameters: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """
        确认参数

        Args:
            intent: 意图
            parameters: 参数字典

        Returns:
            (是否需要确认, 确认问题列表)
        """
        required_params = self.intent_parameter_map.get(intent, [])
        questions = []

        # 检查低置信度参数
        for param_name in required_params:
            if param_name not in self.parameter_states:
                continue

            state = self.parameter_states[param_name]

            if state.confidence < 0.7 and state.value:
                question = CollectionQuestion(
                    question_type=QuestionType.CONFIRMATION,
                    question_text=f"我理解{state.requirement.description}是'{state.value}',对吗?",
                    parameter_name=param_name,
                    priority=8,
                )
                questions.append(question)

        return len(questions) > 0, questions

    def get_collection_stats(self) -> dict[str, Any]:
        """获取收集统计"""
        total = self.stats["total_collections"]
        completed = self.stats["completed_collections"]

        return {
            "total_collections": total,
            "completed_collections": completed,
            "success_rate": completed / total if total > 0 else 0,
            "total_questions_asked": self.stats["total_questions_asked"],
            "avg_questions_per_collection": (
                self.stats["total_questions_asked"] / total if total > 0 else 0
            ),
            "avg_rounds_to_complete": self.stats["avg_rounds_to_complete"],
            "parameter_hit_rates": self.stats["parameter_hit_rates"],
        }

    def reset_conversation(self) -> Any:
        """重置对话状态"""
        self.collection_round = 0
        self.conversation_history.clear()
        for state in self.parameter_states.values():
            state.status = ParameterStatus.MISSING
            state.value = None
            state.confidence = 0.0
            state.validation_errors.clear()
        logger.debug("对话状态已重置")


# 单例实例
_collector_instance: MultiTurnParameterCollector | None = None


async def get_multi_turn_collector() -> MultiTurnParameterCollector:
    """获取多轮对话参数收集器单例(异步版本)"""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = MultiTurnParameterCollector()
        logger.info("多轮对话参数收集器已初始化")
    return _collector_instance


def get_multi_turn_collector_sync() -> MultiTurnParameterCollector:
    """获取多轮对话参数收集器单例(同步版本,用于向后兼容)"""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = MultiTurnParameterCollector()
        logger.info("多轮对话参数收集器已初始化")
    return _collector_instance


async def main():
    """测试主函数"""
    collector = get_multi_turn_collector()

    # 注册意图参数
    collector.register_intent_parameters("patent_analysis", ["patent_number", "analysis_depth"])

    # 测试多轮收集
    print("=== 多轮对话参数收集测试 ===\n")

    # 第1轮
    print("用户: 帮我查一下专利")
    result1 = await collector.collect_parameters(
        intent="patent_analysis", user_input="帮我查一下专利"
    )
    print(f"完成率: {result1.completion_rate:.1%}")
    print(f"缺失参数: {result1.missing_required}")
    if result1.questions:
        print(f"需要询问: {result1.questions[0].question_text}")

    print("\n用户: 专利号是CN123456789A")
    result2 = await collector.collect_parameters(
        intent="patent_analysis",
        user_input="专利号是CN123456789A",
        context={"previous_parameters": result1.parameters},
    )
    print(f"完成率: {result2.completion_rate:.1%}")
    print(f"收集到的参数: {result2.parameters}")
    print(f"是否完成: {result2.is_complete}")

    # 显示统计
    stats = collector.get_collection_stats()
    print("\n=== 统计信息 ===")
    print(f"总收集次数: {stats['total_collections']}")
    print(f"成功率: {stats['success_rate']:.1%}")


# 入口点: @async_main装饰器已添加到main函数
