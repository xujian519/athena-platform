#!/usr/bin/env python3
from __future__ import annotations
"""
学习与适应模块配置常量
Learning and Adaptation Module Configuration Constants

集中管理所有硬编码的配置值,提高可维护性

v2.0: 添加机器学习模型配置 (TF-IDF, KMeans等)
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class PerformanceThresholds:
    """性能阈值配置"""

    # 性能下降阈值(触发恢复策略)
    PERFORMANCE_DECLINE_THRESHOLD: float = -0.1
    # 性能提升阈值(触发增强策略)
    PERFORMANCE_IMPROVE_THRESHOLD: float = 0.1
    # 异常检测阈值(性能下降超过此值视为异常)
    ANOMALY_THRESHOLD: float = -0.2
    # 高严重性异常阈值
    HIGH_SEVERITY_ANOMALY_THRESHOLD: float = -0.4


@dataclass
class BatchConfig:
    """批处理配置"""

    # 批量更新模型的反馈数量
    MODEL_UPDATE_BATCH_SIZE: int = 100
    # 性能分析样本数量
    PERFORMANCE_ANALYSIS_SAMPLES: int = 10
    # 趋势分析样本数量
    TREND_ANALYSIS_RECENT_SAMPLES: int = 50
    # 模型更新所需的最小样本数
    MIN_SAMPLES_FOR_UPDATE: int = 10
    # 性能提升阈值(触发模型更新)
    PERFORMANCE_IMPROVEMENT_THRESHOLD: float = 1.05  # 5%提升


@dataclass
class CacheConfig:
    """缓存配置"""

    # 热记忆缓存大小(每个智能体)
    HOT_CACHE_SIZE: int = 100
    # 经验存储最大数量
    MAX_EXPERIENCES: int = 10000
    # 模式缓存大小
    PATTERN_CACHE_SIZE: int = 1000
    # 性能历史最大长度
    PERFORMANCE_HISTORY_MAXLEN: int = 1000
    # 学习历史最大长度
    LEARNING_HISTORY_MAXLEN: int = 100


@dataclass
class AIThresholds:
    """AI参数阈值配置"""

    # 推理深度最小值
    MIN_REASONING_DEPTH: int = 3
    # 推理深度最大值
    MAX_REASONING_DEPTH: int = 10
    # 温度参数最小值
    MIN_TEMPERATURE: float = 0.1
    # 温度参数最大值
    MAX_TEMPERATURE: float = 1.0
    # 学习率最大值
    MAX_LEARNING_RATE: float = 1.0
    # 创造力参数最大值
    MAX_CREATIVITY: float = 1.0
    # 默认推理深度
    DEFAULT_REASONING_DEPTH: int = 5
    # 默认温度
    DEFAULT_TEMPERATURE: float = 0.7
    # 默认学习率
    DEFAULT_LEARNING_RATE: float = 0.1
    # 默认批次大小
    DEFAULT_BATCH_SIZE: int = 32
    # 默认创造力
    DEFAULT_CREATIVITY: float = 0.5


@dataclass
class OptimizationStrategy:
    """优化策略配置"""

    # 保守推理策略参数
    CONSERVATIVE_DEPTH_ADJUST: int = -1
    CONSERVATIVE_TEMP_ADJUST: float = -0.2

    # 深度推理策略参数
    DEEP_DEPTH_ADJUST: int = 2
    DEEP_TEMP_ADJUST: float = 0.1

    # 快速学习策略参数
    RAPID_LEARNING_RATE_INCREASE: float = 0.4
    RAPID_BATCH_SIZE_MULTIPLIER: int = 2

    # 增强学习策略参数
    ENHANCED_LEARNING_RATE_INCREASE: float = 0.2


@dataclass
class TimeoutConfig:
    """超时配置"""

    # 连接超时(秒)
    CONNECTION_TIMEOUT: int = 30
    # 查询超时(秒)
    QUERY_TIMEOUT: int = 30
    # 学习循环间隔(秒)
    LEARNING_LOOP_INTERVAL: int = 300  # 5分钟
    # 错误后等待时间(秒)
    ERROR_RETRY_WAIT: int = 60


@dataclass
class DatabaseConfig:
    """数据库配置"""

    # PostgreSQL连接池配置
    PG_POOL_MIN_SIZE: int = 5
    PG_POOL_MAX_SIZE: int = 30
    # 缓存清理阈值
    CACHE_PRUNE_THRESHOLD: float = 0.8
    # 搜索结果限制
    SEARCH_RESULT_LIMIT: int = 50
    # 嵌入批量大小
    EMBEDDING_BATCH_SIZE: int = 32
    # 向量维度(bge-m3模型)
    VECTOR_DIMENSION: int = 1024


@dataclass
class RewardConfig:
    """奖励函数配置"""

    # 成功奖励
    SUCCESS_REWARD: float = 1.0
    # 失败惩罚
    FAILURE_PENALTY: float = -0.5
    # 用户满意度权重
    USER_SATISFACTION_WEIGHT: float = 0.5
    # 效率奖励权重
    EFFICIENCY_REWARD_WEIGHT: float = 0.3
    # 效率基准时间(秒)
    EFFICIENCY_BENCHMARK_TIME: float = 10.0
    # 奖励范围
    REWARD_MIN: float = -1.0
    REWARD_MAX: float = 1.0


@dataclass
class ABTestConfig:
    """A/B测试配置"""

    # �置信度阈值
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.70
    # 最小样本数
    MIN_SAMPLE_SIZE: int = 100
    # 实验持续时间(秒)
    DEFAULT_TEST_DURATION: int = 3600  # 1小时
    # 最小成功改进百分比
    MIN_IMPROVEMENT_PERCENTAGE: float = 0.05


@dataclass
class MLModelConfig:
    """机器学习模型配置 (v2.0新增)"""

    # TF-IDF向量化器配置
    TFIDF_MAX_FEATURES: int = 1000
    TFIDF_STOP_WORDS: str = "english"
    TFIDF_NGRAM_RANGE: tuple[int, int] = (1, 2)

    # K-Means聚类配置
    KMEANS_N_CLUSTERS: int = 5
    KMEANS_RANDOM_STATE: int = 42
    KMEANS_MAX_CLUSTERS: int = 10
    KMEANS_MIN_CLUSTER_SIZE: int = 2

    # 模式识别配置
    TOP_K_KEYWORDS: int = 5
    MIN_PATTERN_CONFIDENCE: float = 0.1

    def validate(self) -> bool:
        """验证ML配置参数"""
        if self.TFIDF_MAX_FEATURES <= 0:
            raise ValueError(f"TFIDF_MAX_FEATURES必须大于0,当前为{self.TFIDF_MAX_FEATURES}")

        if self.KMEANS_N_CLUSTERS <= 0:
            raise ValueError(f"KMEANS_N_CLUSTERS必须大于0,当前为{self.KMEANS_N_CLUSTERS}")

        return True

    def get_dynamic_n_clusters(self, data_size: int) -> int:
        """根据数据大小动态计算聚类数量"""
        return min(self.KMEANS_N_CLUSTERS, max(self.KMEANS_MIN_CLUSTER_SIZE, data_size // 2))


# 导出所有配置类
__all__ = [
    "ABTestConfig",
    "AIThresholds",
    "BatchConfig",
    "CacheConfig",
    "DatabaseConfig",
    "LearningConfig",
    "LearningModuleConfig",  # 学习模块配置别名
    "MLModelConfig",  # v2.0新增
    "OptimizationStrategy",
    "PerformanceThresholds",
    "RewardConfig",
    "TimeoutConfig",
]


# 全局配置实例(单例模式)
class LearningConfig:
    """学习系统全局配置"""

    performance = PerformanceThresholds()
    batch = BatchConfig()
    cache = CacheConfig()
    ai_thresholds = AIThresholds()
    optimization = OptimizationStrategy()
    timeout = TimeoutConfig()
    database = DatabaseConfig()
    reward = RewardConfig()
    ab_test = ABTestConfig()
    ml_model = MLModelConfig()  # v2.0新增: 机器学习模型配置

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
            "performance": cls.performance.__dict__,
            "batch": cls.batch.__dict__,
            "cache": cls.cache.__dict__,
            "ai_thresholds": cls.ai_thresholds.__dict__,
            "optimization": cls.optimization.__dict__,
            "timeout": cls.timeout.__dict__,
            "database": cls.database.__dict__,
            "reward": cls.reward.__dict__,
            "ab_test": cls.ab_test.__dict__,
            "ml_model": cls.ml_model.__dict__,  # v2.0新增
        }


# 为保持兼容性，提供 LearningModuleConfig 作为 LearningConfig 的别名
LearningModuleConfig = LearningConfig
