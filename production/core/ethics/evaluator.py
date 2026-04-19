"""
伦理评估器 - 评估AI行动是否符合宪法
Ethics Evaluator - Evaluate AI Actions Against Constitution

核心功能:
1. 评估行动是否符合所有启用原则
2. 生成详细评估报告
3. 提供违规处理建议
4. 记录评估日志
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .constitution import AthenaConstitution, EthicalPrinciple, PrinciplePriority
from .wittgenstein_guard import WittgensteinGuard

# 导入配置加载器(可选,如果配置文件存在则使用)
try:
    from .config import get_harmful_keywords, get_prohibited_claims, load_ethics_config

    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

logger = __import__("logging").get_logger(__name__)


class ComplianceStatus(Enum):
    """合规状态"""

    COMPLIANT = "compliant"  # 完全合规
    NON_COMPLIANT = "non_compliant"  # 不合规
    PARTIAL = "partial"  # 部分合规
    UNCERTAIN = "uncertain"  # 不确定


class ActionSeverity(Enum):
    """行动严重程度"""

    CRITICAL = 4  # 关键:可能造成严重伤害
    HIGH = 3  # 高:可能造成伤害
    MEDIUM = 2  # 中:可能造成轻微影响
    LOW = 1  # 低:影响很小


@dataclass
class PrincipleEvaluation:
    """单个原则的评估结果"""

    principle_id: str
    principle_name: str
    principle_priority: int
    compliant: bool
    confidence: float
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """综合评估结果"""

    agent_id: str
    action: str
    context: dict[str, Any]
    status: ComplianceStatus
    overall_score: float  # 0-1
    principle_evaluations: list[PrincipleEvaluation] = field(default_factory=list)
    violations: list[PrincipleEvaluation] = field(default_factory=list)
    recommended_action: str = "proceed"
    severity: ActionSeverity = ActionSeverity.LOW
    explanation: str = ""
    evaluated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "action": self.action,
            "context": self.context,
            "status": self.status.value,
            "overall_score": self.overall_score,
            "principle_evaluations": [
                {
                    "principle_id": pe.principle_id,
                    "principle_name": pe.principle_name,
                    "priority": pe.principle_priority,
                    "compliant": pe.compliant,
                    "confidence": pe.confidence,
                    "reason": pe.reason,
                }
                for pe in self.principle_evaluations
            ],
            "violations": [
                {
                    "principle_id": v.principle_id,
                    "principle_name": v.principle_name,
                    "priority": v.principle_priority,
                    "reason": v.reason,
                }
                for v in self.violations
            ],
            "recommended_action": self.recommended_action,
            "severity": self.severity.value,
            "explanation": self.explanation,
            "evaluated_at": self.evaluated_at.isoformat(),
        }


@dataclass
class ViolationReport:
    """违规报告"""

    agent_id: str
    action: str
    violations: list[PrincipleEvaluation]
    severity: ActionSeverity
    reported_at: datetime = field(default_factory=datetime.now)
    suggested_remediation: str = ""


class EthicsEvaluator:
    """伦理评估器

    评估AI行动是否符合宪法原则
    """

    def __init__(
        self,
        constitution: AthenaConstitution | None = None,
        wittgenstein_guard: WittgensteinGuard | None = None,
        max_history_size: int = 1000,
    ):
        """初始化伦理评估器

        Args:
            constitution: 宪法实例
            wittgenstein_guard: 维特根斯坦守护实例
            max_history_size: 最大历史记录数量,防止内存无限增长
        """
        self.constitution = constitution or AthenaConstitution()
        self.wittgenstein_guard = wittgenstein_guard or WittgensteinGuard()
        self.evaluation_history: list[EvaluationResult] = []
        self.violation_reports: list[ViolationReport] = []
        self.max_history_size = max_history_size

    def evaluate_action(
        self, agent_id: str, action: str, context: dict[str, Any]
    ) -> EvaluationResult:
        """评估一个行动

        Args:
            agent_id: 智能体ID
            action: 拟执行的行动描述
            context: 上下文信息,可包括:
                - confidence: 置信度 (0-1)
                - language_game: 语言游戏ID
                - query: 用户查询
                - domain: 领域
                - capabilities: 可用能力列表

        Returns:
            EvaluationResult: 评估结果
        """
        principle_evaluations = []
        violations = []

        # 获取所有启用的原则
        principles = self.constitution.get_enabled_principles()

        for principle in principles:
            evaluation = self._evaluate_principle(action, principle, context)
            principle_evaluations.append(evaluation)

            if not evaluation.compliant:
                violations.append(evaluation)

        # 计算总体评分
        overall_score = self._calculate_overall_score(principle_evaluations)

        # 确定状态
        status = self._determine_status(principle_evaluations)

        # 确定严重程度
        severity = self._determine_severity(violations)

        # 推荐行动
        recommended_action = self._get_recommended_action(status, severity, violations)

        # 生成解释
        explanation = self._generate_explanation(
            status, severity, violations, principle_evaluations
        )

        # 创建结果
        result = EvaluationResult(
            agent_id=agent_id,
            action=action,
            context=context,
            status=status,
            overall_score=overall_score,
            principle_evaluations=principle_evaluations,
            violations=violations,
            recommended_action=recommended_action,
            severity=severity,
            explanation=explanation,
        )

        # 记录历史(带大小限制)
        self.evaluation_history.append(result)
        if len(self.evaluation_history) > self.max_history_size:
            # 保留最近的历史记录
            self.evaluation_history = self.evaluation_history[-self.max_history_size :]

        # 如果有违规,创建报告
        if violations:
            self._create_violation_report(result)

        return result

    def _evaluate_principle(
        self, action: str, principle: EthicalPrinciple, context: dict[str, Any]
    ) -> PrincipleEvaluation:
        """评估单个原则"""

        # 认识论诚实原则
        if principle.id == "epistemic_honesty":
            confidence = context.get("confidence", 0.0)
            threshold = principle.metadata.get("default_threshold", 0.7)

            if confidence < threshold:
                return PrincipleEvaluation(
                    principle_id=principle.id,
                    principle_name=principle.name,
                    principle_priority=principle.priority.value,
                    compliant=False,
                    confidence=confidence,
                    reason=f"置信度{confidence:.2f}低于阈值{threshold:.2f}",
                )

        # 语言游戏边界原则
        elif principle.id == "language_game_boundaries":
            query = context.get("query", "")
            game_id = context.get("language_game")

            if self.wittgenstein_guard:
                evaluation = self.wittgenstein_guard.evaluate_query(query, game_id)

                if not evaluation.get("in_scope", False):
                    return PrincipleEvaluation(
                        principle_id=principle.id,
                        principle_name=principle.name,
                        principle_priority=principle.priority.value,
                        compliant=False,
                        confidence=evaluation.get("confidence", 0.0),
                        reason=evaluation.get("reason", "超出语言游戏边界"),
                    )

        # AI身份诚实原则
        elif principle.id == "ai_identity_honesty":
            # 检查是否声称是人类或有身体
            # 优先从配置文件加载,否则使用默认值
            if CONFIG_AVAILABLE:
                try:
                    prohibited_claims = get_prohibited_claims()
                except Exception:
                    prohibited_claims = [
                        "我是人类",
                        "我有身体",
                        "我能感觉到",
                        "我有感情",
                        "I am human",
                        "I have a body",
                        "I can feel",
                    ]
            else:
                prohibited_claims = [
                    "我是人类",
                    "我有身体",
                    "我能感觉到",
                    "我有感情",
                    "I am human",
                    "I have a body",
                    "I can feel",
                ]

            action_lower = action.lower()
            for claim in prohibited_claims:
                if claim.lower() in action_lower:
                    return PrincipleEvaluation(
                        principle_id=principle.id,
                        principle_name=principle.name,
                        principle_priority=principle.priority.value,
                        compliant=False,
                        confidence=1.0,
                        reason=f"禁止声称:{claim}",
                    )

        # 有害内容检查
        elif principle.id == "harmless":
            # 优先从配置文件加载,否则使用默认值
            if CONFIG_AVAILABLE:
                try:
                    harmful_patterns = get_harmful_keywords()
                except Exception:
                    harmful_patterns = [
                        "如何制造",
                        "如何攻击",
                        "如何入侵",
                        "how to hack",
                        "how to make bomb",
                        "how to steal",
                    ]
            else:
                harmful_patterns = [
                    "如何制造",
                    "如何攻击",
                    "如何入侵",
                    "how to hack",
                    "how to make bomb",
                    "how to steal",
                ]

            for pattern in harmful_patterns:
                if pattern in action.lower():
                    return PrincipleEvaluation(
                        principle_id=principle.id,
                        principle_name=principle.name,
                        principle_priority=principle.priority.value,
                        compliant=False,
                        confidence=0.9,
                        reason=f"可能包含有害内容模式:{pattern}",
                    )

        # 默认:合规
        return PrincipleEvaluation(
            principle_id=principle.id,
            principle_name=principle.name,
            principle_priority=principle.priority.value,
            compliant=True,
            confidence=1.0,
            reason="符合原则要求",
        )

    def _calculate_overall_score(self, evaluations: list[PrincipleEvaluation]) -> float:
        """计算总体评分"""
        if not evaluations:
            return 1.0

        # 加权平均,优先级越高权重越大
        total_weight = 0.0
        weighted_sum = 0.0

        for eval in evaluations:
            weight = eval.principle_priority
            total_weight += weight
            weighted_sum += weight * (1.0 if eval.compliant else 0.0)

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _determine_status(self, evaluations: list[PrincipleEvaluation]) -> ComplianceStatus:
        """确定合规状态"""
        if not evaluations:
            return ComplianceStatus.UNCERTAIN

        # 检查关键原则
        critical_evaluations = [
            e for e in evaluations if e.principle_priority >= PrinciplePriority.CRITICAL.value
        ]

        critical_violations = [e for e in critical_evaluations if not e.compliant]

        if critical_violations:
            return ComplianceStatus.NON_COMPLIANT

        # 检查高优先级原则
        high_evaluations = [
            e for e in evaluations if e.principle_priority >= PrinciplePriority.HIGH.value
        ]

        high_violations = [e for e in high_evaluations if not e.compliant]

        if high_violations:
            return ComplianceStatus.PARTIAL

        # 计算合规比例
        compliant_count = sum(1 for e in evaluations if e.compliant)
        compliance_ratio = compliant_count / len(evaluations)

        if compliance_ratio >= 0.9:
            return ComplianceStatus.COMPLIANT
        elif compliance_ratio >= 0.7:
            return ComplianceStatus.PARTIAL
        else:
            return ComplianceStatus.NON_COMPLIANT

    def _determine_severity(self, violations: list[PrincipleEvaluation]) -> ActionSeverity:
        """确定严重程度"""
        if not violations:
            return ActionSeverity.LOW

        max_priority = max(v.principle_priority for v in violations)

        if max_priority >= 10:
            return ActionSeverity.CRITICAL
        elif max_priority >= 8:
            return ActionSeverity.HIGH
        elif max_priority >= 6:
            return ActionSeverity.MEDIUM
        else:
            return ActionSeverity.LOW

    def _get_recommended_action(
        self,
        status: ComplianceStatus,
        severity: ActionSeverity,
        violations: list[PrincipleEvaluation],
    ) -> str:
        """获取推荐行动"""
        if status == ComplianceStatus.COMPLIANT:
            return "proceed"

        if severity == ActionSeverity.CRITICAL:
            return "block"

        if severity == ActionSeverity.HIGH:
            return "escalate"

        # 检查是否是认识论问题
        epistemic_violations = [
            v
            for v in violations
            if v.principle_id in ["epistemic_honesty", "language_game_boundaries"]
        ]

        if epistemic_violations:
            return "negotiate"

        return "proceed_with_caution"

    def _generate_explanation(
        self,
        status: ComplianceStatus,
        severity: ActionSeverity,
        violations: list[PrincipleEvaluation],
        all_evaluations: list[PrincipleEvaluation],
    ) -> str:
        """生成解释"""
        if status == ComplianceStatus.COMPLIANT:
            return "该行动符合所有启用的伦理原则。"

        if not violations:
            return "无法确定合规性。"

        # 按优先级排序违规
        sorted_violations = sorted(violations, key=lambda v: v.principle_priority, reverse=True)

        explanation = f"该行动违反了 {len(violations)} 项原则:\n"

        for v in sorted_violations[:3]:  # 只显示前3个
            explanation += f"- {v.principle_name}: {v.reason}\n"

        if len(violations) > 3:
            explanation += f"...还有 {len(violations) - 3} 项违规。\n"

        return explanation

    def _create_violation_report(self, result: EvaluationResult) -> Any:
        """创建违规报告"""
        if not result.violations:
            return

        report = ViolationReport(
            agent_id=result.agent_id,
            action=result.action,
            violations=result.violations,
            severity=result.severity,
            suggested_remediation=self._suggest_remediation(result),
        )

        self.violation_reports.append(report)

    def _suggest_remediation(self, result: EvaluationResult) -> str:
        """建议补救措施"""
        if result.severity == ActionSeverity.CRITICAL:
            return "立即阻止此行动,升级给人类审查。"

        if result.recommended_action == "negotiate":
            return "与用户协商,澄清需求。"

        if result.recommended_action == "escalate":
            return "升级给专家处理。"

        return "谨慎执行,持续监控。"

    def get_statistics(self) -> dict[str, Any]:
        """获取评估统计"""
        total = len(self.evaluation_history)

        if total == 0:
            return {"total_evaluations": 0, "compliance_rate": 0.0, "violation_count": 0}

        compliant = sum(
            1 for e in self.evaluation_history if e.status == ComplianceStatus.COMPLIANT
        )

        return {
            "total_evaluations": total,
            "compliance_rate": compliant / total,
            "violation_count": len(self.violation_reports),
            "status_distribution": {
                "compliant": sum(
                    1 for e in self.evaluation_history if e.status == ComplianceStatus.COMPLIANT
                ),
                "partial": sum(
                    1 for e in self.evaluation_history if e.status == ComplianceStatus.PARTIAL
                ),
                "non_compliant": sum(
                    1 for e in self.evaluation_history if e.status == ComplianceStatus.NON_COMPLIANT
                ),
            },
        }


# 便捷函数
def create_ethics_evaluator(constitution: AthenaConstitution = None) -> EthicsEvaluator:
    """创建伦理评估器"""
    return EthicsEvaluator(constitution)
