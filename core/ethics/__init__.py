from __future__ import annotations
"""
Athena平台AI伦理框架
Athena Platform AI Ethics Framework

版本: 1.0.0
基于: Anthropic Constitutional AI + 维特根斯坦逻辑哲学 + 东方智慧

核心模块:
- constitution: 宪法原则定义
- wittgenstein_guard: 维特根斯坦防幻觉模块
- evaluator: 伦理评估器
- constraints: 约束执行器
- monitoring: 伦理监控系统
- sensitive_data_filter: 敏感信息过滤器

使用示例:
    from core.ethics import AthenaConstitution, EthicsEvaluator

    # 创建宪法
    constitution = AthenaConstitution()

    # 创建评估器
    evaluator = EthicsEvaluator(constitution)

    # 评估行动
    result = evaluator.evaluate_action(
        agent_id="xiaonuo",
        action="回答专利法律问题",
        context={"confidence": 0.85, "language_game": "patent_law"}
    )
"""

from .constitution import AthenaConstitution, EthicalPrinciple, PrinciplePriority, PrincipleSource
from .container import (
    EthicsContainer,
    IContainer,
    LifecycleType,
    ServiceDescriptor,
    get_container,
    reset_container,
)
from .container import (
    create_constraint_enforcer as container_create_constraint_enforcer,
)
from .container import (
    create_evaluator as container_create_evaluator,
)
from .container import (
    create_monitor as container_create_monitor,
)
from .evaluator import (
    ActionSeverity,
    ComplianceStatus,
    EthicsEvaluator,
    EvaluationResult,
    ViolationReport,
)
from .sensitive_data_filter import (
    SensitiveDataFilter,
    SensitivePattern,
    create_sensitive_data_filter,
    filter_log,
    filter_sensitive_data,
    get_sensitive_data_filter,
)
from .wittgenstein_guard import (
    ConfidenceLevel,
    GamePattern,
    LanguageGame,
    PatternType,
    WittgensteinGuard,
)

__version__ = "1.0.0"
__author__ = "Athena Platform Team"

# 导出主要类和函数
__all__ = [
    "ActionSeverity",
    "Alert",
    "AlertLevel",
    # 宪法相关
    "AthenaConstitution",
    "ComplianceStatus",
    "ConfidenceLevel",
    "ConstraintAction",
    "ConstraintEnforcer",
    "ConstraintResult",
    # 约束执行
    "EthicalConstraint",
    "EthicalPrinciple",
    # 依赖注入容器
    "EthicsContainer",
    # 评估器
    "EthicsEvaluator",
    "EthicsMetrics",
    # 监控系统
    "EthicsMonitor",
    "EvaluationResult",
    "GamePattern",
    "IContainer",
    "LanguageGame",
    "LifecycleType",
    "PatternType",
    "PrinciplePriority",
    "PrincipleSource",
    "PrometheusMonitor",
    # 敏感信息过滤
    "SensitiveDataFilter",
    "SensitivePattern",
    "ServiceDescriptor",
    "ViolationReport",
    # 维特根斯坦守护
    "WittgensteinGuard",
    "container_create_constraint_enforcer",
    "container_create_evaluator",
    "container_create_monitor",
    "create_sensitive_data_filter",
    "filter_log",
    "filter_sensitive_data",
    "get_container",
    "get_sensitive_data_filter",
    "reset_container",
    "setup_logging_alert_handler",
    "setup_prometheus_monitoring",
]

# 默认宪法实例
_default_constitution = None


def get_default_constitution() -> AthenaConstitution:
    """获取默认宪法实例(单例模式)"""
    global _default_constitution
    if _default_constitution is None:
        _default_constitution = AthenaConstitution()
    return _default_constitution


def create_ethics_evaluator(constitution: AthenaConstitution = None) -> EthicsEvaluator:
    """创建伦理评估器便捷函数"""
    if constitution is None:
        constitution = get_default_constitution()
    return EthicsEvaluator(constitution)
