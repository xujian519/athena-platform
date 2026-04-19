from __future__ import annotations
"""
伦理框架接口抽象层
Ethics Framework Interface Abstraction Layer

定义伦理框架的核心接口,提供抽象基类(ABC)用于扩展和实现

接口定义:
- IPrincipleEvaluator: 原则评估器接口
- ILanguageGame: 语言游戏接口
- IConstraintEnforcer: 约束执行器接口
- IEthicsMonitor: 监控器接口
- ISensitiveDataFilter: 敏感信息过滤器接口
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol

# ============================================================================
# 数据结构接口
# ============================================================================


class ComplianceStatus(Protocol):
    """合规状态协议"""

    value: str
    name: str


class EvaluationResult(Protocol):
    """评估结果协议"""

    status: ComplianceStatus
    overall_score: float
    principle_evaluations: list[Any]
    violations: list[Any]
    recommended_action: str
    severity: Any
    explanation: str


# ============================================================================
# 核心接口定义
# ============================================================================


class IPrincipleEvaluator(ABC):
    """原则评估器接口

    定义如何评估单个伦理原则
    """

    @abstractmethod
    def evaluate_principle(self, action: str, principle: Any, context: dict[str, Any]) -> Any:
        """评估单个原则

        Args:
            action: 拟执行的行动
            principle: 伦理原则对象
            context: 上下文信息

        Returns:
            原则评估结果
        """
        pass

    @abstractmethod
    def get_statistics(self) -> dict[str, Any]:
        """获取评估统计信息

        Returns:
            统计信息字典,包含:
            - total_evaluations: 总评估次数
            - compliant_count: 合规次数
            - violation_count: 违规次数
            - compliance_rate: 合规率
        """
        pass


class ILanguageGame(ABC):
    """语言游戏接口

    基于维特根斯坦《哲学研究》的语言游戏概念
    """

    @property
    @abstractmethod
    def game_id(self) -> str:
        """获取游戏ID"""
        pass

    @property
    @abstractmethod
    def domain(self) -> str:
        """获取领域"""
        pass

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """是否启用"""
        pass

    @abstractmethod
    def evaluate_query(self, query: str) -> dict[str, Any]:
        """评估查询是否在游戏范围内

        Args:
            query: 用户查询

        Returns:
            评估结果字典,包含:
            - in_scope: 是否在范围内
            - confidence: 置信度 (0-1)
            - threshold: 阈值
            - action: 推荐行动
            - reason: 原因说明
        """
        pass

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """获取游戏状态

        Returns:
            状态信息字典
        """
        pass


class IConstraintEnforcer(ABC):
    """约束执行器接口

    定义如何执行伦理约束
    """

    @abstractmethod
    def enforce(self, agent_id: str, action: str, context: dict[str, Any]) -> Any:
        """执行约束

        Args:
            agent_id: 智能体ID
            action: 拟执行的行动
            context: 上下文信息

        Returns:
            约束执行结果
        """
        pass

    @abstractmethod
    def get_enforcement_statistics(self) -> dict[str, Any]:
        """获取执行统计信息

        Returns:
            统计信息字典,包含:
            - total: 总执行次数
            - allowed: 允许次数
            - blocked: 阻止次数
            - allow_rate: 允许率
        """
        pass


class IEthicsMonitor(ABC):
    """监控器接口

    定义监控伦理合规性的接口
    """

    @abstractmethod
    def record_evaluation(self, result: Any) -> None:
        """记录评估结果

        Args:
            result: 评估结果
        """
        pass

    @abstractmethod
    def get_current_metrics(self) -> Any:
        """获取当前指标

        Returns:
            当前指标对象
        """
        pass

    @abstractmethod
    def generate_dashboard_data(self) -> dict[str, Any]:
        """生成仪表板数据

        Returns:
            仪表板数据字典
        """
        pass


class ISensitiveDataFilter(ABC):
    """敏感信息过滤器接口

    定义过滤敏感信息的接口
    """

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """是否启用过滤"""
        pass

    @abstractmethod
    def filter_dict(self, data: dict[str, Any], max_depth: int = 10) -> dict[str, Any]:
        """过滤字典中的敏感数据

        Args:
            data: 输入字典
            max_depth: 最大递归深度

        Returns:
            过滤后的字典
        """
        pass

    @abstractmethod
    def filter_string(self, text: str) -> str:
        """过滤字符串中的敏感模式

        Args:
            text: 输入文本

        Returns:
            过滤后的文本
        """
        pass

    @abstractmethod
    def filter_log_message(self, message: str, context: dict[str, Any] | None = None) -> str:
        """过滤日志消息

        Args:
            message: 日志消息
            context: 上下文字典

        Returns:
            过滤后的日志消息
        """
        pass

    @abstractmethod
    def add_sensitive_field(self, field_name: str) -> None:
        """添加敏感字段

        Args:
            field_name: 字段名
        """
        pass

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """获取过滤器统计信息

        Returns:
            统计信息字典
        """
        pass


# ============================================================================
# 复合接口
# ============================================================================


class IEthicsFramework(ABC):
    """伦理框架完整接口

    整合所有核心接口的完整框架接口
    """

    @abstractmethod
    def get_constitution(self) -> Any:
        """获取宪法"""
        pass

    @abstractmethod
    def get_evaluator(self) -> IPrincipleEvaluator:
        """获取评估器"""
        pass

    @abstractmethod
    def get_constraint_enforcer(self) -> IConstraintEnforcer:
        """获取约束执行器"""
        pass

    @abstractmethod
    def get_monitor(self) -> IEthicsMonitor:
        """获取监控器"""
        pass

    @abstractmethod
    def get_sensitive_filter(self) -> ISensitiveDataFilter:
        """获取敏感信息过滤器"""
        pass

    @abstractmethod
    def evaluate_action(
        self, agent_id: str, action: str, context: dict[str, Any]
    ) -> EvaluationResult:
        """评估行动(完整流程)

        Args:
            agent_id: 智能体ID
            action: 拟执行的行动
            context: 上下文信息

        Returns:
            评估结果
        """
        pass

    @abstractmethod
    def get_framework_status(self) -> dict[str, Any]:
        """获取框架状态

        Returns:
            框架状态字典
        """
        pass


# ============================================================================
# 插件接口
# ============================================================================


class IPrinciplePlugin(ABC):
    """原则插件接口

    允许扩展自定义的伦理原则
    """

    @property
    @abstractmethod
    def principle_id(self) -> str:
        """获取原则ID"""
        pass

    @abstractmethod
    def evaluate(self, action: str, context: dict[str, Any]) -> Any:
        """评估原则

        Args:
            action: 行动描述
            context: 上下文

        Returns:
            评估结果
        """
        pass

    @abstractmethod
    def get_priority(self) -> int:
        """获取原则优先级 (0-10)"""
        pass


class IConstraintPlugin(ABC):
    """约束插件接口

    允许扩展自定义的约束策略
    """

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """获取插件ID"""
        pass

    @abstractmethod
    def should_block(self, evaluation: Any) -> bool:
        """判断是否应该阻止

        Args:
            evaluation: 评估结果

        Returns:
            是否应该阻止
        """
        pass

    @abstractmethod
    def get_negotiation_message(self, evaluation: Any) -> str:
        """获取协商消息

        Args:
            evaluation: 评估结果

        Returns:
            协商消息
        """
        pass


# ============================================================================
# 工厂接口
# ============================================================================


class IEthicsComponentFactory(ABC):
    """伦理组件工厂接口

    定义创建伦理框架组件的工厂方法
    """

    @abstractmethod
    def create_constitution(self) -> Any:
        """创建宪法"""
        pass

    @abstractmethod
    def create_evaluator(self, constitution: Any) -> IPrincipleEvaluator:
        """创建评估器"""
        pass

    @abstractmethod
    def create_constraint_enforcer(self, evaluator: IPrincipleEvaluator) -> IConstraintEnforcer:
        """创建约束执行器"""
        pass

    @abstractmethod
    def create_monitor(self, evaluator: IPrincipleEvaluator) -> IEthicsMonitor:
        """创建监控器"""
        pass

    @abstractmethod
    def create_sensitive_filter(self) -> ISensitiveDataFilter:
        """创建敏感信息过滤器"""
        pass


# ============================================================================
# 便捷函数
# ============================================================================


def is_compatible_evaluator(obj: Any) -> bool:
    """检查对象是否兼容评估器接口

    Args:
        obj: 待检查对象

    Returns:
        是否兼容
    """
    return isinstance(obj, IPrincipleEvaluator)


def is_compatible_monitor(obj: Any) -> bool:
    """检查对象是否兼容监控器接口

    Args:
        obj: 待检查对象

    Returns:
        是否兼容
    """
    return isinstance(obj, IEthicsMonitor)


def is_compatible_filter(obj: Any) -> bool:
    """检查对象是否兼容过滤器接口

    Args:
        obj: 待检查对象

    Returns:
        是否兼容
    """
    return isinstance(obj, ISensitiveDataFilter)


# ============================================================================
# 导出列表
# ============================================================================

__all__ = [
    "IConstraintEnforcer",
    "IConstraintPlugin",
    # 工厂接口
    "IEthicsComponentFactory",
    # 复合接口
    "IEthicsFramework",
    "IEthicsMonitor",
    "ILanguageGame",
    # 核心接口
    "IPrincipleEvaluator",
    # 插件接口
    "IPrinciplePlugin",
    "ISensitiveDataFilter",
    # 便捷函数
    "is_compatible_evaluator",
    "is_compatible_filter",
    "is_compatible_monitor",
]
