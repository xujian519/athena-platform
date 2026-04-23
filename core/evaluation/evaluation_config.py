#!/usr/bin/env python3
from __future__ import annotations
"""
评估与反思模块配置常量
Evaluation & Reflection Module Configuration Constants

集中管理所有硬编码的配置值,提高可维护性

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class EvaluationThresholds:
    """评估阈值配置"""

    # 等级阈值
    EXCELLENT: float = 90
    GOOD: float = 80
    SATISFACTORY: float = 70
    NEEDS_IMPROVEMENT: float = 60
    POOR: float = 0

    # 置信度阈值
    HIGH_CONFIDENCE: float = 0.7
    MEDIUM_CONFIDENCE: float = 0.5
    LOW_CONFIDENCE: float = 0.3

    # 证据相关
    MIN_EVIDENCE_PER_CRITERION: int = 2
    MAX_EVIDENCE_FOR_FULL_CONFIDENCE: int = 3

    # 趋势分析窗口
    TREND_WINDOW_SIZE: int = 5

    # 趋势斜率阈值
    RAPID_IMPROVEMENT_SLOPE: float = 2.0
    IMPROVEMENT_SLOPE: float = 0.5
    DECLINE_SLOPE: float = -0.5
    RAPID_DECLINE_SLOPE: float = -2.0


@dataclass
class ExecutionThresholds:
    """执行时间阈值配置"""

    # 执行时间阈值(秒)
    VERY_FAST: float = 1.0
    FAST: float = 3.0
    ACCEPTABLE: float = 5.0
    SLOW: float = 10.0

    # 效率评分
    VERY_FAST_SCORE: float = 1.0
    FAST_SCORE: float = 0.8
    ACCEPTABLE_SCORE: float = 0.6
    SLOW_SCORE: float = 0.4
    VERY_SLOW_SCORE: float = 0.2


@dataclass
class ReflectionThresholds:
    """反思阈值配置"""

    # 反思边界检查
    MIN_OUTPUT_LENGTH: int = 50
    MIN_OUTPUT_LENGTH_REASON: str = "输出内容过少,无法有效反思"

    # 反思次数限制
    MAX_REFINEMENT_ATTEMPTS: int = 3

    # 置信度阈值
    HIGH_CONFIDENCE_THRESHOLD: float = 0.8
    MEDIUM_CONFIDENCE_THRESHOLD: float = 0.5
    LOW_CONFIDENCE_THRESHOLD: float = 0.2

    # 反思历史
    REFLECTION_HISTORY_SIZE: int = 1000

    # 质量阈值
    MIN_QUALITY_SCORE: float = 0.7
    EXCELLENT_QUALITY_SCORE: float = 0.85

    # 不可反思关键词
    UNSAYABLE_KEYWORDS: Optional[list[str]] = None

    # 创意内容关键词
    CREATIVE_KEYWORDS: Optional[list[str]] = None

    def __post_init__(self):
        """初始化列表"""
        if self.UNSAYABLE_KEYWORDS is None:
            self.UNSAYABLE_KEYWORDS = [
                "情感体验",
                "主观感受",
                "生命意义",
                "价值判断",
                "道德决策",
                "美学品味",
            ]
        if self.CREATIVE_KEYWORDS is None:
            self.CREATIVE_KEYWORDS = ["创意", "艺术", "诗歌", "虚构"]


@dataclass
class QualityAssuranceConfig:
    """质量保证配置"""

    # QA检查项
    MIN_OVERALL_SCORE: float = 0.0
    MAX_OVERALL_SCORE: float = 100.0

    # 完整性检查扣分
    MISSING_CRITERIA_PENALTY: float = 50.0
    MISSING_STRENGTHS_PENALTY: float = 10.0
    MISSING_WEAKNESSES_PENALTY: float = 10.0
    MISSING_RECOMMENDATIONS_PENALTY: float = 20.0
    SCORE_OUT_OF_RANGE_PENALTY: float = 30.0

    # 一致性检查扣分
    LEVEL_MISMATCH_PENALTY: float = 30.0
    HIGH_STD_DEV_PENALTY: float = 20.0
    HIGH_STD_DEV_THRESHOLD: float = 30.0

    # 偏见检测扣分
    EXTREME_SCORES_RATIO: float = 0.3
    TOO_MANY_EXTREME_SCORES_PENALTY: float = 25.0
    MISSING_EVIDENCE_PENALTY: float = 20.0

    # 证据质量检查
    EVIDENCE_FORMAT_ERROR_PENALTY: float = 5.0
    INSUFFICIENT_EVIDENCE_PENALTY: float = 20.0

    # QA通过分数
    QA_PASS_SCORE: float = 70.0


@dataclass
class StorageConfig:
    """存储配置"""

    # 数据目录
    DATA_DIR: str = "data/evaluation"

    # 历史记录限制
    MAX_EVALUATION_RECORDS: int = 100
    EVALUATION_RECORD_KEEP: int = 50

    # 反思历史
    REFLECTION_DEQUE_MAXLEN: int = 1000

    # 文件编码
    FILE_ENCODING: str = "utf-8"

    # JSON格式化
    JSON_INDENT: int = 2
    JSON_ENSURE_ASCII: bool = False


@dataclass
class ScoreAdjustmentConfig:
    """分数调整配置"""

    # 执行反思调整
    BASE_ADJUSTMENT_FACTOR: float = 0.2
    SUCCESS_WEIGHT: float = 0.5
    QUALITY_WEIGHT: float = 0.3
    EFFICIENCY_WEIGHT: float = 0.2

    # 时间惩罚/奖励
    TIME_PENALTY_THRESHOLD: float = 10.0
    TIME_PENALTY_AMOUNT: float = 0.1
    TIME_REWARD_THRESHOLD: float = 1.0
    TIME_REWARD_AMOUNT: float = 0.05

    # 调整范围
    MAX_ADJUSTMENT: float = 0.2
    MIN_ADJUSTMENT: float = -0.2

    # 选择反思调整
    SELECTION_ADJUSTMENT_FACTOR: float = 0.1
    ALTERNATIVE_TOOL_REWARD: float = 0.05


# 导出所有配置类
__all__ = [
    "EvaluationThresholds",
    "ExecutionThresholds",
    "QualityAssuranceConfig",
    "ReflectionThresholds",
    "ScoreAdjustmentConfig",
    "StorageConfig",
]


# 全局配置实例
class EvaluationConfig:
    """评估系统全局配置"""

    thresholds = EvaluationThresholds()
    execution = ExecutionThresholds()
    reflection = ReflectionThresholds()
    qa = QualityAssuranceConfig()
    storage = StorageConfig()
    score_adjustment = ScoreAdjustmentConfig()

    @classmethod
    def update(cls, config_dict: dict[str, Any]) -> Any:
        """更新配置"""
        for section, values in config_dict.items():
            if hasattr(cls, section):
                section_obj = getattr(cls, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        """转换为字典"""
        return {
            "thresholds": cls.thresholds.__dict__,
            "execution": cls.execution.__dict__,
            "reflection": cls.reflection.__dict__,
            "qa": cls.qa.__dict__,
            "storage": cls.storage.__dict__,
            "score_adjustment": cls.score_adjustment.__dict__,
        }
