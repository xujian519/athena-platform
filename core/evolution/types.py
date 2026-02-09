#!/usr/bin/env python3
"""
自动进化系统类型定义
Auto-Evolution System Type Definitions
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class EvolutionPhase(Enum):
    """进化阶段"""
    BASIC = "basic"           # 基础进化 - 参数自动调优
    INTELLIGENT = "intelligent"  # 智能进化 - 演化算法
    AUTONOMOUS = "autonomous"     # 自主进化 - 完全自主


class EvolutionStatus(Enum):
    """进化状态"""
    IDLE = "idle"               # 空闲
    ANALYZING = "analyzing"     # 分析中
    EVOLVING = "evolving"       # 进化中
    DEPLOYING = "deploying"     # 部署中
    ROLLING_BACK = "rolling_back"  # 回滚中
    COMPLETED = "completed"     # 完成
    FAILED = "failed"           # 失败


class MutationType(Enum):
    """突变类型"""
    PARAMETER_TUNING = "parameter_tuning"       # 参数调优
    CONFIG_UPDATE = "config_update"             # 配置更新
    MODEL_SELECTION = "model_selection"         # 模型选择
    STRUCTURE_CHANGE = "structure_change"       # 结构变更
    STRATEGY_CHANGE = "strategy_change"         # 策略变更


class EvolutionStrategy(Enum):
    """进化策略"""
    GRADIENT = "gradient"           # 梯度优化
    GENETIC = "genetic"             # 遗传算法
    REINFORCEMENT = "reinforcement"  # 强化学习
    BAYESIAN = "bayesian"           # 贝叶斯优化
    ENSEMBLE = "ensemble"           # 集成策略


@dataclass
class EvolutionConfig:
    """进化配置"""
    # 基础配置
    enabled: bool = True
    phase: EvolutionPhase = EvolutionPhase.BASIC
    auto_deploy: bool = False  # 自动部署（需要谨慎）

    # 触发条件
    performance_threshold: float = 0.7  # 性能阈值
    trigger_interval: int = 3600  # 触发间隔（秒）
    min_iterations: int = 10  # 最小迭代次数

    # 安全限制
    max_evolution_per_day: int = 10  # 每日最大进化次数
    rollback_on_degradation: bool = True  # 性能下降时回滚
    safety_margin: float = 0.05  # 安全裕度

    # 优化目标
    optimize_targets: list[str] = field(default_factory=lambda: [
        "accuracy", "efficiency", "cost"
    ])

    # 监控配置
    enable_monitoring: bool = True
    monitoring_interval: int = 60  # 监控间隔（秒）

    # 日志配置
    log_evolution_history: bool = True
    max_history_size: int = 1000


@dataclass
class EvolutionResult:
    """进化结果"""
    success: bool
    phase: EvolutionPhase
    strategy: EvolutionStrategy

    # 性能指标
    before_score: float
    after_score: float
    improvement: float

    # 变更详情
    mutations: list[dict[str, Any]]
    mutations_count: int = 0

    # 状态信息
    status: EvolutionStatus = EvolutionStatus.COMPLETED
    error: Optional[str] = None

    # 时间信息
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration: float = 0.0  # 秒

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    # 性能分数
    accuracy: float = 0.0
    efficiency: float = 0.0
    cost: float = 0.0
    overall: float = 0.0

    # 详细指标
    response_time: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0
    resource_usage: float = 0.0

    # 用户满意度
    user_satisfaction: float = 0.0

    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "accuracy": self.accuracy,
            "efficiency": self.efficiency,
            "cost": self.cost,
            "overall": self.overall,
            "response_time": self.response_time,
            "error_rate": self.error_rate,
            "throughput": self.throughput,
            "resource_usage": self.resource_usage,
            "user_satisfaction": self.user_satisfaction,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Mutation:
    """突变定义"""
    mutation_type: MutationType
    target: str  # 目标模块/参数
    before_value: Any
    after_value: Any
    expected_improvement: float = 0.0
    confidence: float = 0.5  # 信心度

    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "mutation_type": self.mutation_type.value,
            "target": self.target,
            "before_value": str(self.before_value),
            "after_value": str(self.after_value),
            "expected_improvement": self.expected_improvement,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat()
        }
