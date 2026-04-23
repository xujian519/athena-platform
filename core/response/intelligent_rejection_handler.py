#!/usr/bin/env python3
from __future__ import annotations
"""
智能拒绝处理器
Intelligent Rejection Handler

为智能体提供友好、合理的拒绝响应:
1. 拒绝原因分析
2. 友好提示生成
3. 替代方案建议
4. 其他智能体推荐
5. 拒绝历史追踪
6. 拒绝策略优化

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "智能拒绝"
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RejectionReason(Enum):
    """拒绝原因"""

    OUT_OF_SCOPE = "out_of_scope"  # 超出专业范围
    LACKING_CAPABILITY = "lacking_capability"  # 能力不足
    INVALID_INPUT = "invalid_input"  # 输入无效
    RESOURCE_UNAVAILABLE = "resource_unavailable"  # 资源不可用
    SECURITY_CONCERN = "security_concern"  # 安全顾虑
    DEPENDENCY_MISSING = "dependency_missing"  # 缺少依赖
    PERMISSION_DENIED = "permission_denied"  # 权限不足
    TEMPORARY_ISSUE = "temporary_issue"  # 临时问题
    UNKNOWN = "unknown"


@dataclass
class RejectionResponse:
    """拒绝响应"""

    rejected: bool
    reason: str
    explanation: str
    suggestions: list[str]
    alternative_agents: list[str]
    can_retry: bool
    retry_after: Optional[float] = None  # 秒
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RejectionHistory:
    """拒绝历史"""

    reason: RejectionReason
    count: int = 0
    last_occurrence: datetime | None = None
    user_satisfaction: float = 0.5  # 0-1


class IntelligentRejectionHandler:
    """
    智能拒绝处理器

    核心功能:
    1. 拒绝原因分析
    2. 友好响应生成
    3. 替代方案推荐
    4. 历史学习优化
    5. 跨智能体推荐
    """

    def __init__(self, agent_id: str, agent_capabilities: list[str]):
        self.agent_id = agent_id
        self.agent_capabilities = agent_capabilities

        # 拒绝历史
        self.rejection_history: dict[RejectionReason, RejectionHistory] = {}

        # 其他智能体能力映射
        self.agent_capabilities_map: dict[str, list[str]] = {}

        # 拒绝模板
        self.rejection_templates = self._initialize_templates()

        # 统计信息
        self.metrics = {
            "total_rejections": 0,
            "reasonable_rejections": 0,
            "unreasonable_rejections": 0,
            "user_satisfaction": 0.5,
        }

        logger.info(f"🤝 智能拒绝处理器初始化完成: {agent_id}")

    def _initialize_templates(self) -> dict[RejectionReason, dict[str, Any]]:
        """初始化拒绝模板"""
        return {
            RejectionReason.OUT_OF_SCOPE: {
                "title": "超出专业范围",
                "explanation_template": (
                    "这个请求超出了我的专业领域。我主要擅长{capabilities},"
                    "而您的问题涉及{topic},这需要其他专业支持。"
                ),
                "suggestions_template": [
                    "建议咨询{alt_agents},他们在这个领域更专业",
                    "可以尝试将问题拆分,我可以协助处理其中部分内容",
                ],
            },
            RejectionReason.LACKING_CAPABILITY: {
                "title": "能力限制",
                "explanation_template": (
                    "抱歉,我目前还不具备完成这个任务的能力。"
                    "这需要{required_capability},我正在持续学习中。"
                ),
                "suggestions_template": [
                    "您可以尝试{alt_agents},他们可能支持这个功能",
                    "或者稍后再试,我可能会学会这个技能",
                ],
            },
            RejectionReason.INVALID_INPUT: {
                "title": "输入格式问题",
                "explanation_template": (
                    "您提供的输入信息有些问题:{input_issue}。"
                    "这可能是因为缺少必要参数或格式不正确。"
                ),
                "suggestions_template": [
                    "请检查{missing_params}是否完整",
                    "参考正确的输入格式:{format_example}",
                ],
            },
            RejectionReason.RESOURCE_UNAVAILABLE: {
                "title": "资源暂时不可用",
                "explanation_template": (
                    "完成这个任务需要的{resource_type}当前不可用。"
                    "这可能是由于维护、限流或其他临时原因。"
                ),
                "suggestions_template": [
                    "请稍后再试,预计{retry_after}分钟后恢复",
                    "或者联系管理员获取帮助",
                ],
                "can_retry": True,
            },
            RejectionReason.SECURITY_CONCERN: {
                "title": "安全限制",
                "explanation_template": (
                    "抱歉,出于安全考虑,我无法执行这个操作。"
                    "这涉及{security_issue},需要特殊权限或验证。"
                ),
                "suggestions_template": ["请联系管理员获取相应权限", "或者使用其他经过验证的方式"],
                "can_retry": False,
            },
            RejectionReason.DEPENDENCY_MISSING: {
                "title": "缺少依赖",
                "explanation_template": (
                    "完成这个任务需要先完成{dependencies}。" "这些前置条件目前还不满足。"
                ),
                "suggestions_template": [
                    "请先完成{dependencies}",
                    "或者我可以协助您完成这些前置任务",
                ],
                "can_retry": True,
            },
            RejectionReason.PERMISSION_DENIED: {
                "title": "权限不足",
                "explanation_template": ("您没有权限执行此操作。这需要{required_permission}权限。"),
                "suggestions_template": ["请联系管理员申请相应权限", "或者使用其他有权限的账户"],
                "can_retry": False,
            },
            RejectionReason.TEMPORARY_ISSUE: {
                "title": "临时问题",
                "explanation_template": ("遇到了临时性问题:{issue_description}。" "请稍后再试。"),
                "suggestions_template": [
                    "预计{retry_after}分钟后恢复",
                    "如果问题持续,请联系技术支持",
                ],
                "can_retry": True,
            },
        }

    def register_agent_capabilities(self, agent_id: str, capabilities: list[str]) -> Any:
        """注册其他智能体的能力"""
        self.agent_capabilities_map[agent_id] = capabilities
        logger.debug(f"📝 已注册智能体能力: {agent_id}")

    async def analyze_rejection(
        self,
        user_request: str,
        error: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> RejectionReason:
        """
        分析拒绝原因

        Args:
            user_request: 用户请求
            error: 错误信息
            context: 上下文

        Returns:
            RejectionReason: 拒绝原因
        """
        # 1. 检查是否超出范围
        if not await self._check_capability_match(user_request):
            return RejectionReason.OUT_OF_SCOPE

        # 2. 检查输入有效性
        if await self._check_invalid_input(user_request, context):
            return RejectionReason.INVALID_INPUT

        # 3. 检查资源可用性
        if await self._check_resource_availability(context):
            return RejectionReason.RESOURCE_UNAVAILABLE

        # 4. 检查安全问题
        if await self._check_security_concerns(user_request):
            return RejectionReason.SECURITY_CONCERN

        # 5. 检查依赖
        if await self._check_dependencies(context):
            return RejectionReason.DEPENDENCY_MISSING

        # 6. 检查权限
        if await self._check_permissions(context):
            return RejectionReason.PERMISSION_DENIED

        # 默认:能力不足
        return RejectionReason.LACKING_CAPABILITY

    async def generate_rejection_response(
        self, user_request: str, reason: RejectionReason, context: Optional[dict[str, Any]] = None
    ) -> RejectionResponse:
        """
        生成拒绝响应

        Args:
            user_request: 用户请求
            reason: 拒绝原因
            context: 上下文

        Returns:
            RejectionResponse: 拒绝响应
        """
        context = context or {}

        # 获取模板
        template = self.rejection_templates.get(reason)
        if not template:
            template = self.rejection_templates[RejectionReason.UNKNOWN]

        # 生成解释
        explanation = await self._generate_explanation(user_request, reason, template, context)

        # 生成建议
        suggestions = await self._generate_suggestions(user_request, reason, template, context)

        # 推荐替代智能体
        alternative_agents = await self._recommend_alternative_agents(user_request, reason)

        # 判断是否可以重试
        can_retry = template.get("can_retry", False)
        retry_after = context.get("retry_after")

        # 更新历史
        await self._update_rejection_history(reason)

        # 更新统计
        self.metrics["total_rejections"] += 1
        if await self._is_reasonable_rejection(reason, context):
            self.metrics["reasonable_rejections"] += 1
        else:
            self.metrics["unreasonable_rejections"] += 1

        return RejectionResponse(
            rejected=True,
            reason=template["title"],
            explanation=explanation,
            suggestions=suggestions,
            alternative_agents=alternative_agents,
            can_retry=can_retry,
            retry_after=retry_after,
        )

    async def _check_capability_match(self, user_request: str) -> bool:
        """检查能力匹配"""
        # 简化实现:关键词匹配
        for capability in self.agent_capabilities:
            if capability.lower() in user_request.lower():
                return True
        return False

    async def _check_invalid_input(
        self, user_request: str, context: dict[str, Any]
    ) -> bool:
        """检查输入是否无效"""
        # 简化实现:检查长度
        if len(user_request) < 3:
            return True

        # 检查是否包含无效字符
        return bool(any(char in user_request for char in ["\x00", "\x01", "\x02"]))

    async def _check_resource_availability(self, context: dict[str, Any]) -> bool:
        """检查资源可用性"""
        if not context:
            return False

        # 检查上下文中的资源状态
        return context.get("resource_unavailable", False)

    async def _check_security_concerns(self, user_request: str) -> bool:
        """检查安全问题"""
        # 危险操作关键词
        dangerous_keywords = ["删除所有", "drop database", "rm -rf", "format c:"]

        user_request_lower = user_request.lower()
        return any(keyword in user_request_lower for keyword in dangerous_keywords)

    async def _check_dependencies(self, context: dict[str, Any]) -> bool:
        """检查依赖"""
        if not context:
            return False

        return context.get("missing_dependencies", False)

    async def _check_permissions(self, context: dict[str, Any]) -> bool:
        """检查权限"""
        if not context:
            return False

        return context.get("permission_denied", False)

    async def _generate_explanation(
        self,
        user_request: str,
        reason: RejectionReason,
        template: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """生成解释说明"""
        explanation_template = template["explanation_template"]

        # 确保context不为None
        context = context or {}

        # 准备模板变量
        variables = {
            "capabilities": ", ".join(self.agent_capabilities[:3]),
            "topic": context.get("topic", "相关领域"),
            "required_capability": context.get("required_capability", "特定能力"),
            "input_issue": context.get("input_issue", "格式不正确"),
            "missing_params": context.get("missing_params", "必要参数"),
            "format_example": context.get("format_example", "标准格式"),
            "resource_type": context.get("resource_type", "所需资源"),
            "retry_after": context.get("retry_after", 5),
            "security_issue": context.get("security_issue", "安全问题"),
            "dependencies": context.get("dependencies", "前置条件"),
            "required_permission": context.get("required_permission", "特定权限"),
            "issue_description": context.get("issue_description", "未知问题"),
        }

        # 填充模板
        try:
            explanation = explanation_template.format(**variables)
        except KeyError as e:
            logger.warning(f"模板变量缺失: {e}")
            explanation = explanation_template

        return explanation

    async def _generate_suggestions(
        self,
        user_request: str,
        reason: RejectionReason,
        template: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> list[str]:
        """生成建议"""
        suggestions_template = template.get("suggestions_template", [])

        # 确保context不为None
        context = context or {}

        suggestions = []
        for suggestion_template in suggestions_template:
            # 准备变量
            variables = {
                "alt_agents": ", ".join(self.agent_capabilities_map.keys())[:3],
                "missing_params": context.get("missing_params", "必要参数"),
                "format_example": context.get("format_example", ""),
                "retry_after": context.get("retry_after", 5),
                "dependencies": context.get("dependencies", "前置条件"),
            }

            # 填充模板
            try:
                suggestion = suggestion_template.format(**variables)
                suggestions.append(suggestion)
            except KeyError:
                suggestions.append(suggestion_template)

        return suggestions[:3]  # 最多返回3条建议

    async def _recommend_alternative_agents(
        self, user_request: str, reason: RejectionReason
    ) -> list[str]:
        """推荐替代智能体"""
        alternatives = []

        # 根据请求内容匹配其他智能体的能力
        for agent_id, capabilities in self.agent_capabilities_map.items():
            if agent_id == self.agent_id:
                continue

            # 检查能力匹配
            for capability in capabilities:
                if capability.lower() in user_request.lower():
                    alternatives.append(agent_id)
                    break

        return alternatives[:3]

    async def _update_rejection_history(self, reason: RejectionReason):
        """更新拒绝历史"""
        if reason not in self.rejection_history:
            self.rejection_history[reason] = RejectionHistory(reason=reason)

        history = self.rejection_history[reason]
        history.count += 1
        history.last_occurrence = datetime.now()

    async def _is_reasonable_rejection(
        self, reason: RejectionReason, context: dict[str, Any]
    ) -> bool:
        """判断拒绝是否合理"""
        # 不合理的拒绝:应该是能处理但拒绝了
        unreasonable_reasons = [RejectionReason.LACKING_CAPABILITY, RejectionReason.TEMPORARY_ISSUE]

        # 检查是否是这些原因但在用户能力范围内
        if reason in unreasonable_reasons:
            # 如果用户请求实际在能力范围内,则是不合理拒绝
            user_request = context.get("user_request", "")
            if await self._check_capability_match(user_request):
                return False

        return True

    async def get_rejection_metrics(self) -> dict[str, Any]:
        """获取拒绝统计"""
        total = self.metrics["total_rejections"]

        return {
            "total_rejections": total,
            "reasonable_rate": (self.metrics["reasonable_rejections"] / max(total, 1)),
            "unreasonable_rate": (self.metrics["unreasonable_rejections"] / max(total, 1)),
            "by_reason": {
                reason.value: history.count for reason, history in self.rejection_history.items()
            },
            "user_satisfaction": self.metrics["user_satisfaction"],
        }


# 导出便捷函数
_handlers: dict[str, IntelligentRejectionHandler] = {}


def get_rejection_handler(
    agent_id: str, agent_capabilities: list[str]
) -> IntelligentRejectionHandler:
    """获取拒绝处理器"""
    if agent_id not in _handlers:
        _handlers[agent_id] = IntelligentRejectionHandler(
            agent_id=agent_id, agent_capabilities=agent_capabilities
        )
    return _handlers[agent_id]
