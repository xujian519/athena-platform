#!/usr/bin/env python3
from __future__ import annotations
"""
小诺多轮对话参数澄清机制
实现智能参数缺失检测、提问生成和多轮对话管理

功能特性:
1. 参数缺失检测算法
2. 智能提问生成
3. 参数确认流程
4. 对话状态管理
5. 用户体验优化
6. 参数修正和补充

作者: 小诺AI团队
日期: 2025-12-18
"""

import os
import re

# 导入NER参数提取器
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

from core.logging_config import setup_logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from xiaonuo_ner_parameter_extractor import NERModelConfig, XiaonuoNERParameterExtractor

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class DialogueState(Enum):
    """对话状态"""

    INIT = "init"  # 初始状态
    COLLECTING = "collecting"  # 参数收集中
    CLARIFYING = "clarifying"  # 参数澄清中
    CONFIRMING = "confirming"  # 确认中
    COMPLETED = "completed"  # 完成
    ERROR = "error"  # 错误状态


class QuestionType(Enum):
    """问题类型"""

    MISSING_PARAM = "missing_param"  # 缺失参数
    AMBIGUOUS_PARAM = "ambiguous_param"  # 模糊参数
    INVALID_PARAM = "invalid_param"  # 无效参数
    CONFIRM_PARAM = "confirm_param"  # 确认参数
    CORRECTION_PARAM = "correction_param"  # 纠正参数


class ParameterPriority(Enum):
    """参数优先级"""

    CRITICAL = 3  # 关键参数
    IMPORTANT = 2  # 重要参数
    OPTIONAL = 1  # 可选参数


@dataclass
class ParameterTemplate:
    """参数模板"""

    name: str  # 参数名
    type: str  # 参数类型
    required: bool  # 是否必需
    priority: ParameterPriority  # 优先级
    description: str  # 描述
    validation_rules: list[str]  # 验证规则
    default_value: Any = None  # 默认值
    examples: list[str] = field(default_factory=list)  # 示例


@dataclass
class ClarificationQuestion:
    """澄清问题"""

    question_id: str  # 问题ID
    question_type: QuestionType  # 问题类型
    content: str  # 问题内容
    parameter_name: str  # 相关参数名
    expected_type: str  # 期望类型
    examples: list[str] = field(default_factory=list)  # 示例
    suggestions: list[str] = field(default_factory=list)  # 建议
    priority: int = 1  # 优先级


@dataclass
class DialogueTurn:
    """对话轮次"""

    turn_id: str  # 轮次ID
    timestamp: datetime  # 时间戳
    user_input: str  # 用户输入
    system_response: str  # 系统响应
    extracted_params: dict[str, Any]  # 提取参数
    questions_asked: list[str]  # 提出的问题
    state: DialogueState  # 状态
    confidence: float  # 置信度


@dataclass
class DialogueSession:
    """对话会话"""

    session_id: str  # 会话ID
    user_id: str  # 用户ID
    intent: str  # 意图
    start_time: datetime  # 开始时间
    current_state: DialogueState  # 当前状态
    turns: list[DialogueTurn] = field(default_factory=list)  # 对话轮次
    collected_params: dict[str, Any] = field(default_factory=dict)  # 已收集参数
    missing_params: list[str] = field(default_factory=list)  # 缺失参数
    clarification_history: list[str] = field(default_factory=list)  # 澄清历史


@dataclass
class ClarificationConfig:
    """澄清系统配置"""

    max_turns: int = 5  # 最大对话轮次
    confidence_threshold: float = 0.8  # 置信度阈值
    question_templates_path: str = "config/clarification_templates.json"
    parameter_schemas_path: str = "config/parameter_schemas.json"
    session_timeout: int = 1800  # 会话超时(秒)


class XiaonuoParameterClarification:
    """小诺参数澄清系统"""

    def __init__(self, config: ClarificationConfig = None):
        self.config = config or ClarificationConfig()
        self.ner_extractor = XiaonuoNERParameterExtractor(NERModelConfig())

        # 对话会话管理
        self.active_sessions: dict[str, DialogueSession] = {}

        # 参数模板
        self.parameter_templates: dict[str, ParameterTemplate] = {}

        # 问题模板
        self.question_templates: dict[str, list[str]] = {}

        # 意图参数映射
        self.intent_param_mapping: dict[str, list[str]] = {}

        # 加载配置
        self._load_configuration()

        logger.info("💬 小诺参数澄清系统初始化完成")
        logger.info(f"📋 支持意图数: {len(self.intent_param_mapping)}")
        logger.info(f"📝 参数模板数: {len(self.parameter_templates)}")

    def _load_configuration(self) -> Any:
        """加载配置文件"""
        try:
            # 加载参数模板
            self._init_parameter_templates()

            # 加载问题模板
            self._init_question_templates()

            # 初始化意图参数映射
            self._init_intent_param_mapping()

        except Exception as e:
            logger.warning(f"⚠️ 配置加载失败,使用默认配置: {e}")
            self._load_default_configuration()

    def _init_parameter_templates(self) -> Any:
        """初始化参数模板"""
        templates = {
            "url": ParameterTemplate(
                name="url",
                type="string",
                required=True,
                priority=ParameterPriority.CRITICAL,
                description="要访问的网址",
                validation_rules=["url_format", "not_empty"],
                examples=["https://www.example.com", "http://api.test.com"],
            ),
            "email": ParameterTemplate(
                name="email",
                type="string",
                required=True,
                priority=ParameterPriority.IMPORTANT,
                description="邮箱地址",
                validation_rules=["email_format", "not_empty"],
                examples=["user@example.com", "test@domain.org"],
            ),
            "phone": ParameterTemplate(
                name="phone",
                type="string",
                required=True,
                priority=ParameterPriority.IMPORTANT,
                description="电话号码",
                validation_rules=["phone_format"],
                examples=["13812345678", "010-12345678"],
            ),
            "date": ParameterTemplate(
                name="date",
                type="date",
                required=True,
                priority=ParameterPriority.IMPORTANT,
                description="日期",
                validation_rules=["date_format", "future_date"],
                examples=["2025-12-25", "明天", "下周三"],
            ),
            "time": ParameterTemplate(
                name="time",
                type="time",
                required=True,
                priority=ParameterPriority.IMPORTANT,
                description="时间",
                validation_rules=["time_format"],
                examples=["10:30", "下午2点", "14:00"],
            ),
            "port": ParameterTemplate(
                name="port",
                type="integer",
                required=False,
                priority=ParameterPriority.OPTIONAL,
                description="端口号",
                validation_rules=["port_range"],
                default_value=80,
                examples=["80", "443", "3000"],
            ),
            "file": ParameterTemplate(
                name="file",
                type="string",
                required=True,
                priority=ParameterPriority.CRITICAL,
                description="文件名或路径",
                validation_rules=["file_exists", "file_extension"],
                examples=["example.py", "/path/to/file.txt"],
            ),
            "host": ParameterTemplate(
                name="host",
                type="string",
                required=True,
                priority=ParameterPriority.CRITICAL,
                description="主机地址",
                validation_rules=["ip_format", "domain_format"],
                examples=["192.168.1.100", "example.com"],
            ),
        }

        self.parameter_templates = templates

    def _init_question_templates(self) -> Any:
        """初始化问题模板"""
        templates = {
            QuestionType.MISSING_PARAM: [
                "请提供{parameter_name}({description})",
                "我需要知道{parameter_name}才能继续,{parameter_name}是{description}",
                "请告诉我{parameter_name}{examples},这样我就能帮您{intent}",
            ],
            QuestionType.AMBIGUOUS_PARAM: [
                "关于{parameter_name},您是指{options}中的哪一个?",
                "您提到的{parameter_name}不够明确,请选择:{options}",
                "请澄清{parameter_name},可用的选项是:{options}",
            ],
            QuestionType.INVALID_PARAM: [
                "{parameter_name}的值{value}无效,请提供有效的{parameter_name}",
                "您提供的{parameter_name}不正确,正确的{parameter_name}应该是{examples}",
                "{value}不是有效的{parameter_name},请重新输入",
            ],
            QuestionType.CONFIRM_PARAM: [
                "请确认{parameter_name}: {value}是否正确?",
                "您提供的{parameter_name}是{value},对吗?",
                "确认{parameter_name}为{value}?",
            ],
            QuestionType.CORRECTION_PARAM: [
                "请更正{parameter_name}的值",
                "请提供正确的{parameter_name}",
                "请修改{parameter_name}",
            ],
        }

        for qtype, questions in templates.items():
            self.question_templates[qtype.value] = questions

    def _init_intent_param_mapping(self) -> Any:
        """初始化意图参数映射"""
        mapping = {
            "code_analysis": ["file", "language"],
            "api_test": ["url", "method", "port"],
            "email": ["email", "subject", "content"],
            "call": ["phone"],
            "appointment": ["date", "time", "location"],
            "infrastructure/infrastructure/deployment": ["host", "port", "environment"],
            "search": ["keyword", "category"],
            "appointment": ["date", "time", "participants", "location"],
            "payment": ["amount", "recipient", "method"],
            "booking": ["date", "time", "number_of_people", "location"],
        }

        self.intent_param_mapping = mapping

    def _load_default_configuration(self) -> Any:
        """加载默认配置"""
        logger.info("📝 使用默认配置")

    def start_clarification_session(
        self, user_id: str, intent: str, initial_input: str
    ) -> DialogueSession:
        """
        开始澄清会话

        Args:
            user_id: 用户ID
            intent: 用户意图
            initial_input: 初始输入

        Returns:
            DialogueSession: 对话会话
        """
        session_id = f"{user_id}_{int(datetime.now().timestamp())}"

        # 创建会话
        session = DialogueSession(
            session_id=session_id,
            user_id=user_id,
            intent=intent,
            start_time=datetime.now(),
            current_state=DialogueState.INIT,
            collected_params={},
        )

        # 提取初始参数
        extraction = self.ner_extractor.extract_parameters(initial_input, intent)
        session.collected_params = extraction.parameters

        # 检测缺失参数
        session.missing_params = self._detect_missing_parameters(session)

        # 添加第一轮对话
        turn = DialogueTurn(
            turn_id=f"{session_id}_turn_1",
            timestamp=datetime.now(),
            user_input=initial_input,
            system_response="",
            extracted_params=extraction.parameters,
            questions_asked=[],
            state=DialogueState.COLLECTING,
            confidence=extraction.confidence,
        )
        session.turns.append(turn)

        # 更新会话状态
        if session.missing_params:
            session.current_state = DialogueState.CLARIFYING
        else:
            session.current_state = DialogueState.CONFIRMING

        # 保存会话
        self.active_sessions[session_id] = session

        logger.info(
            f"🚀 开始澄清会话: {session_id}, 意图: {intent}, 缺失参数: {len(session.missing_params)}"
        )

        return session

    def continue_clarification(self, session_id: str, user_input: str) -> tuple[str, DialogueState]:
        """
        继续澄清对话

        Args:
            session_id: 会话ID
            user_input: 用户输入

        Returns:
            tuple[str, DialogueState]: (系统响应, 新状态)
        """
        if session_id not in self.active_sessions:
            return "会话已过期,请重新开始", DialogueState.ERROR

        session = self.active_sessions[session_id]

        # 检查超时
        if (datetime.now() - session.turns[-1].timestamp).seconds > self.config.session_timeout:
            del self.active_sessions[session_id]
            return "会话已超时,请重新开始", DialogueState.ERROR

        # 检查最大轮次
        if len(session.turns) >= self.config.max_turns:
            return "对话轮次过多,请重新开始", DialogueState.ERROR

        # 提取新参数
        extraction = self.ner_extractor.extract_parameters(user_input, session.intent)

        # 更新会话参数
        for param_name, param_value in extraction.parameters.items():
            if not param_name.startswith("_"):
                session.collected_params[param_name] = param_value

        # 检测参数有效性
        validation_errors = self._validate_parameters(session.collected_params, session.intent)

        # 添加新对话轮次
        turn = DialogueTurn(
            turn_id=f"{session_id}_turn_{len(session.turns) + 1}",
            timestamp=datetime.now(),
            user_input=user_input,
            system_response="",
            extracted_params=extraction.parameters,
            questions_asked=[],
            state=session.current_state,
            confidence=extraction.confidence,
        )
        session.turns.append(turn)

        # 生成系统响应
        response, new_state = self._generate_response(session, validation_errors)
        session.current_state = new_state

        logger.info(f"💬 澄清对话继续: {session_id}, 状态: {new_state.value}")

        return response, new_state

    def _detect_missing_parameters(self, session: DialogueSession) -> list[str]:
        """检测缺失参数"""
        missing = []
        required_params = self.intent_param_mapping.get(session.intent, [])

        for param_name in required_params:
            if param_name not in session.collected_params:
                template = self.parameter_templates.get(param_name)
                if template and template.required:
                    missing.append(param_name)

        # 按优先级排序
        def priority_score(param_name) -> None:
            template = self.parameter_templates.get(param_name)
            return template.priority.value if template else 1

        missing.sort(key=priority_score, reverse=True)

        return missing

    def _validate_parameters(self, parameters: dict[str, Any], intent: str) -> list[str]:
        """验证参数"""
        errors = []

        for param_name, param_value in parameters.items():
            if param_name.startswith("_"):
                continue

            template = self.parameter_templates.get(param_name)
            if not template:
                continue

            # 验证规则检查
            for rule in template.validation_rules:
                if not self._apply_validation_rule(rule, param_value):
                    errors.append(f"参数 {param_name} 验证失败: {rule}")

        return errors

    def _apply_validation_rule(self, rule: str, value: Any) -> bool:
        """应用验证规则"""
        try:
            if rule == "not_empty":
                return value is not None and str(value).strip() != ""
            elif rule == "url_format":
                url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
                return bool(url_pattern.match(str(value)))
            elif rule == "email_format":
                email_pattern = re.compile(r"^[a-z_a-Z0-9._%+-]+@[a-z_a-Z0-9.-]+\.[a-z_a-Z]{2,}$")
                return bool(email_pattern.match(str(value)))
            elif rule == "phone_format":
                phone_pattern = re.compile(r"1[3-9]\d{9}|\d{3,4}-\d{7,8}")
                return bool(phone_pattern.match(str(value)))
            elif rule == "port_range":
                port = int(str(value))
                return 1 <= port <= 65535
            elif rule == "date_format":
                # 简化日期验证
                return True
            elif rule == "time_format":
                # 简化时间验证
                return True
            elif rule == "ip_format":
                ip_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
                if ip_pattern.match(str(value)):
                    parts = str(value).split(".")
                    return all(0 <= int(part) <= 255 for part in parts)
                return False
            else:
                return True
        except Exception:
            return False

    def _generate_response(
        self, session: DialogueSession, validation_errors: list[str]
    ) -> tuple[str, DialogueState]:
        """生成系统响应"""
        if validation_errors:
            # 有验证错误
            for error in validation_errors:
                param_name = error.split(" ")[1]
                question = self._generate_clarification_question(
                    session, param_name, QuestionType.INVALID_PARAM
                )
                return question, DialogueState.CLARIFYING

        if session.current_state == DialogueState.CONFIRMING:
            # 确认阶段
            return self._generate_confirmation_response(session)

        if not session.missing_params:
            # 所有参数已收集
            return self._generate_completion_response(session), DialogueState.COMPLETED

        # 询问缺失参数
        next_param = session.missing_params[0]
        question = self._generate_clarification_question(
            session, next_param, QuestionType.MISSING_PARAM
        )

        return question, DialogueState.CLARIFYING

    def _generate_clarification_question(
        self, session: DialogueSession, param_name: str, question_type: QuestionType
    ) -> str:
        """生成澄清问题"""
        template = self.parameter_templates.get(param_name)
        if not template:
            return f"请提供{param_name}"

        templates = self.question_templates.get(question_type.value, [])
        if not templates:
            return f"请提供{param_name}"

        # 随机选择模板
        import random

        selected_template = random.choice(templates)

        # 准备模板变量
        variables = {
            "parameter_name": param_name,
            "description": template.description,
            "dev/examples": self._format_examples(template.examples),
            "intent": session.intent,
            "options": "",  # TODO: 实现选项生成
            "value": session.collected_params.get(param_name, ""),
        }

        # 填充模板
        try:
            question = selected_template.format(**variables)
        except KeyError:
            question = f"请提供{param_name}({template.description})"

        # 记录问题
        session.turns[-1].questions_asked.append(question)

        return question

    def _format_examples(self, examples: list[str]) -> str:
        """格式化示例"""
        if not examples:
            return ""

        if len(examples) == 1:
            return f",例如:{examples[0]}"
        else:
            return f",例如:{', '.join(examples[:-1])}或{examples[-1]}"

    def _generate_confirmation_response(
        self, session: DialogueSession
    ) -> tuple[str, DialogueState]:
        """生成确认响应"""
        params_list = []
        for param_name, param_value in session.collected_params.items():
            if not param_name.startswith("_"):
                params_list.append(f"{param_name}: {param_value}")

        if params_list:
            confirmation = (
                "请确认以下信息:\n"
                + "\n".join(params_list)
                + "\n\n确认无误请回复'是',需要修改请说明具体参数。"
            )
            return confirmation, DialogueState.CONFIRMING
        else:
            return "参数收集完成", DialogueState.COMPLETED

    def _generate_completion_response(self, session: DialogueSession) -> str:
        """生成完成响应"""
        duration = (datetime.now() - session.start_time).total_seconds()
        return f"参数收集完成!共收集{len(session.collected_params)}个参数,耗时{duration:.1f}秒。"

    def get_session_status(self, session_id: str) -> DialogueSession | None:
        """获取会话状态"""
        return self.active_sessions.get(session_id)

    def end_session(self, session_id: str) -> DialogueSession | None:
        """结束会话"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.current_state = DialogueState.COMPLETED
            del self.active_sessions[session_id]
            return session
        return None

    def get_session_summary(self, session_id: str) -> dict[str, Any]:
        """获取会话摘要"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {}

        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "intent": session.intent,
            "duration": (datetime.now() - session.start_time).total_seconds(),
            "turns": len(session.turns),
            "collected_params": session.collected_params,
            "state": session.current_state.value,
            "confidence": np.mean([turn.confidence for turn in session.turns]),
        }


def main() -> None:
    """测试函数"""
    # 初始化澄清系统
    clarification = XiaonuoParameterClarification()

    # 测试场景
    test_scenarios = [
        {
            "user_id": "test_user_1",
            "intent": "code_analysis",
            "initial_input": "帮我分析代码",
            "conversation": [
                "example.py",
                "是",
            ],
        },
        {
            "user_id": "test_user_2",
            "intent": "appointment",
            "initial_input": "明天开会",
            "conversation": [
                "上午10点",
                "在会议室A",
                "是",
            ],
        },
        {
            "user_id": "test_user_3",
            "intent": "infrastructure/infrastructure/deployment",
            "initial_input": "部署应用",
            "conversation": [
                "192.168.1.100",
                "3000",
                "生产环境",
                "是",
            ],
        },
    ]

    logger.info("🧪 开始参数澄清测试")

    for i, scenario in enumerate(test_scenarios, 1):
        logger.info(f"\n📝 测试场景 {i}: {scenario['intent']}")

        # 开始澄清会话
        session = clarification.start_clarification_session(
            scenario["user_id"], scenario["intent"], scenario["initial_input"]
        )

        logger.info(f"🚀 会话开始: {session.session_id}")
        logger.info(f"📋 初始参数: {session.collected_params}")
        logger.info(f"❓ 缺失参数: {session.missing_params}")

        # 模拟多轮对话
        current_state = session.current_state
        for j, user_input in enumerate(scenario["conversation"], 1):
            if current_state == DialogueState.COMPLETED:
                break

            logger.info(f"\n💬 第{j}轮对话")
            logger.info(f"用户: {user_input}")

            response, current_state = clarification.continue_clarification(
                session.session_id, user_input
            )

            logger.info(f"系统: {response}")
            logger.info(f"状态: {current_state.value}")

            # 获取当前状态
            current_session = clarification.get_session_status(session.session_id)
            logger.info(f"当前参数: {current_session.collected_params}")

        # 获取会话摘要
        summary = clarification.get_session_summary(session.session_id)
        logger.info("\n📊 会话摘要:")
        for key, value in summary.items():
            logger.info(f"  {key}: {value}")

        # 结束会话
        clarification.end_session(session.session_id)

    logger.info("\n✅ 参数澄清测试完成")


if __name__ == "__main__":
    main()
