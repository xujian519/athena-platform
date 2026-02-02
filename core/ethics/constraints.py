"""
伦理约束执行器 - 执行伦理决策
Ethical Constraints Enforcer - Execute Ethical Decisions

核心功能:
1. 根据评估结果执行相应的约束行动
2. 实现协商、升级、阻止等策略
3. 提供装饰器模式简化集成
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional

from .evaluator import ActionSeverity, ComplianceStatus, EthicsEvaluator, EvaluationResult

logger = logging.getLogger(__name__)


class ConstraintAction(Enum):
    """约束行动类型"""

    PROCEED = "proceed"  # 继续执行
    PROCEED_WITH_CAUTION = "proceed_with_caution"  # 谨慎执行
    NEGOTIATE = "negotiate"  # 协商
    ESCALATE = "escalate"  # 升级
    BLOCK = "block"  # 阻止
    MODIFY = "modify"  # 修改
    LOG_ONLY = "log_only"  # 仅记录


@dataclass
class ConstraintResult:
    """约束执行结果"""

    action_taken: ConstraintAction
    allowed: bool
    message: str
    modified_action: str | None = None
    escalation_target: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class EthicalConstraint:
    """伦理约束

    定义如何处理违规情况
    """

    def __init__(
        self,
        evaluator: EthicsEvaluator,
        auto_block_critical: bool = True,
        auto_negotiate_uncertain: bool = True,
        auto_escalate_high_severity: bool = True,
    ):
        self.evaluator = evaluator
        self.auto_block_critical = auto_block_critical
        self.auto_negotiate_uncertain = auto_negotiate_uncertain
        self.auto_escalate_high_severity = auto_escalate_high_severity

    def enforce(self, agent_id: str, action: str, context: dict[str, Any]) -> ConstraintResult:
        """执行约束

        根据评估结果决定如何处理行动
        """
        # 评估行动
        evaluation = self.evaluator.evaluate_action(
            agent_id=agent_id, action=action, context=context
        )

        # 根据评估结果决定行动
        return self._determine_action(evaluation)

    def _determine_action(self, evaluation: EvaluationResult) -> ConstraintResult:
        """根据评估结果确定约束行动"""

        if evaluation.status == ComplianceStatus.COMPLIANT:
            return ConstraintResult(
                action_taken=ConstraintAction.PROCEED,
                allowed=True,
                message="行动符合伦理要求,可以执行。",
                metadata={"evaluation_score": evaluation.overall_score},
            )

        # 有关键违规
        critical_violations = [v for v in evaluation.violations if v.principle_priority >= 10]

        if critical_violations and self.auto_block_critical:
            return ConstraintResult(
                action_taken=ConstraintAction.BLOCK,
                allowed=False,
                message=f"行动被阻止:违反关键原则 - {critical_violations[0].principle_name}",
                metadata={
                    "violations": [v.principle_id for v in critical_violations],
                    "severity": evaluation.severity.value,
                },
            )

        # 高严重程度
        if evaluation.severity == ActionSeverity.CRITICAL:
            return ConstraintResult(
                action_taken=ConstraintAction.BLOCK,
                allowed=False,
                message="行动被阻止:存在严重伦理问题。",
                metadata={"explanation": evaluation.explanation},
            )

        if evaluation.severity == ActionSeverity.HIGH and self.auto_escalate_high_severity:
            escalation_target = self._get_escalation_target(evaluation)
            return ConstraintResult(
                action_taken=ConstraintAction.ESCALATE,
                allowed=False,
                message=f"行动需要升级:{evaluation.explanation}",
                escalation_target=escalation_target,
                metadata={"violations": [v.principle_id for v in evaluation.violations]},
            )

        # 认识论不确定
        epistemic_violations = [
            v
            for v in evaluation.violations
            if v.principle_id in ["epistemic_honesty", "language_game_boundaries"]
        ]

        if epistemic_violations and self.auto_negotiate_uncertain:
            negotiation_message = self._generate_negotiation_message(evaluation)
            return ConstraintResult(
                action_taken=ConstraintAction.NEGOTIATE,
                allowed=False,
                message=negotiation_message,
                metadata={
                    "uncertainty": True,
                    "violations": [v.principle_id for v in epistemic_violations],
                },
            )

        # 部分合规,谨慎执行
        if evaluation.status == ComplianceStatus.PARTIAL:
            return ConstraintResult(
                action_taken=ConstraintAction.PROCEED_WITH_CAUTION,
                allowed=True,
                message=f"行动可执行,但需注意:{evaluation.explanation}",
                metadata={
                    "caution_level": "medium",
                    "violations": [v.principle_id for v in evaluation.violations],
                },
            )

        # 默认:阻止
        return ConstraintResult(
            action_taken=ConstraintAction.BLOCK,
            allowed=False,
            message=f"行动不符合伦理要求:{evaluation.explanation}",
            metadata={"violations": [v.principle_id for v in evaluation.violations]},
        )

    def _get_escalation_target(self, evaluation: EvaluationResult) -> str:
        """获取升级目标"""
        context = evaluation.context

        # 优先使用上下文中的升级路径
        if "escalation_path" in context:
            return context["escalation_path"]

        # 根据领域确定
        domain = context.get("domain", "general")
        domain_targets = {
            "medical": "human_medical_professional",
            "legal": "human_attorney",
            "patent": "human_patent_attorney",
            "financial": "human_financial_advisor",
        }

        return domain_targets.get(domain, "human_expert")

    def _generate_negotiation_message(self, evaluation: EvaluationResult) -> str:
        """生成协商消息"""
        context = evaluation.context
        query = context.get("query", "")

        # 使用维特根斯坦守护的建议
        if hasattr(self.evaluator, "wittgenstein_guard") and self.evaluator.wittgenstein_guard:
            guard_eval = self.evaluator.wittgenstein_guard.evaluate_query(query)

            if guard_eval.get("action") == "negotiate":
                suggestion = self.evaluator.wittgenstein_guard.suggest_negotiation(
                    query, guard_eval
                )
                return f"我不太确定您的需求。{suggestion}"

        # 默认协商消息
        return "我不太确定您的需求。能否提供更多细节或澄清您的问题?"


class ConstraintEnforcer:
    """约束执行器

    提供高级约束执行功能
    """

    def __init__(self, constraint: EthicalConstraint):
        self.constraint = constraint
        self.enforcement_history: list[dict[str, Any]] = []

    def enforce_and_log(
        self, agent_id: str, action: str, context: dict[str, Any]
    ) -> ConstraintResult:
        """执行约束并记录"""
        result = self.constraint.enforce(agent_id, action, context)

        # 记录历史
        self.enforcement_history.append(
            {
                "agent_id": agent_id,
                "action": action,
                "result": {
                    "action_taken": result.action_taken.value,
                    "allowed": result.allowed,
                    "message": result.message,
                },
                "timestamp": None,  # 可添加时间戳
            }
        )

        # 记录日志
        log_level = logging.WARNING if not result.allowed else logging.INFO
        logger.log(
            log_level,
            f"伦理约束执行: agent={agent_id}, action={result.action_taken.value}, "
            f"allowed={result.allowed}",
        )

        return result

    def get_enforcement_statistics(self) -> dict[str, Any]:
        """获取执行统计"""
        if not self.enforcement_history:
            return {"total": 0}

        total = len(self.enforcement_history)
        allowed = sum(1 for e in self.enforcement_history if e["result"]["allowed"])

        action_counts = {}
        for entry in self.enforcement_history:
            action = entry["result"]["action_taken"]
            action_counts[action] = action_counts.get(action, 0) + 1

        return {
            "total": total,
            "allowed": allowed,
            "blocked": total - allowed,
            "allow_rate": allowed / total,
            "action_distribution": action_counts,
        }


def ethical_action(agent_id: str, evaluator: EthicsEvaluator = None, on_violation: str = "block"):
    """伦理行动装饰器

    用于自动为智能体方法添加伦理检查

    Args:
        agent_id: 智能体ID
        evaluator: 伦理评估器实例
        on_violation: 违规时的处理方式: "block", "negotiate", "escalate"

    Usage:
        @ethical_action(agent_id="xiaonuo")
        def answer_question(self, query: str) -> str:
            return self._generate_answer(query)
    """

    def decorator(func) -> None:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            # 提取上下文
            context = {
                "agent_id": agent_id,
                "function": func.__name__,
                "args": args,
                "kwargs": kwargs,
            }

            # 从kwargs中提取可能的伦理相关信息
            if "confidence" in kwargs:
                context["confidence"] = kwargs["confidence"]
            if "query" in kwargs:
                context["query"] = kwargs["query"]
            if "domain" in kwargs:
                context["domain"] = kwargs["domain"]

            # 创建约束
            if evaluator is None:
                from core.ethics import create_ethics_evaluator

                evaluator = create_ethics_evaluator()

            constraint = EthicalConstraint(
                evaluator=evaluator,
                auto_block_critical=(on_violation == "block"),
                auto_negotiate_uncertain=(on_violation == "negotiate"),
                auto_escalate_high_severity=(on_violation == "escalate"),
            )

            # 执行约束检查
            result = constraint.enforce(
                agent_id=agent_id, action=f"{func.__name__}", context=context
            )

            if not result.allowed:
                # 根据约束结果处理
                if result.action_taken == ConstraintAction.NEGOTIATE:
                    return result.message
                elif result.action_taken == ConstraintAction.ESCALATE:
                    return f"此请求需要升级处理:{result.escalation_target}"
                else:  # BLOCK
                    return f"此请求无法处理:{result.message}"

            # 允许执行
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


# 便捷函数
def create_constraint_enforcer(evaluator: EthicsEvaluator = None) -> ConstraintEnforcer:
    """创建约束执行器"""
    if evaluator is None:
        from core.ethics import create_ethics_evaluator

        evaluator = create_ethics_evaluator()

    constraint = EthicalConstraint(evaluator)
    return ConstraintEnforcer(constraint)
