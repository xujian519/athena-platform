#!/usr/bin/env python3
"""
优化系统配置常量
Optimization System Configuration Constants

作者: 小诺·双鱼公主
版本: v1.0.0

将硬编码的魔法数字提取为命名常量
"""

from typing import Final

# ==================== 延迟相关常量 ====================


class LatencyConfig:
    """延迟相关配置"""

    # 延迟阈值(毫秒)
    MAX_ACCEPTABLE_LATENCY_MS: Final[int] = 1000
    TARGET_P99_LATENCY_MS: Final[int] = 175
    TARGET_P95_LATENCY_MS: Final[int] = 150
    TARGET_AVG_LATENCY_MS: Final[int] = 100

    # 缓存相关
    CACHE_EXPIRE_SECONDS: Final[int] = 300  # 5分钟
    FAST_PATH_CACHE_TTL_SECONDS: Final[int] = 600  # 10分钟

    # 批处理
    BATCH_SIZE_THRESHOLD: Final[int] = 10
    BATCH_FLUSH_TIMEOUT_SECONDS: Final[int] = 10

    # 超时
    DEFAULT_TIMEOUT_MS: Final[int] = 5000
    FAST_TIMEOUT_MS: Final[int] = 1000


# ==================== 恢复相关常量 ====================


class RecoveryConfig:
    """恢复相关配置"""

    # 重试
    MAX_RETRIES: Final[int] = 3
    BASE_RETRY_DELAY_MS: Final[int] = 1000
    EXPONENTIAL_BACKOFF_BASE: Final[int] = 2
    MAX_RETRY_DELAY_MS: Final[int] = 30000  # 30秒

    # 超时
    TIMEOUT_THRESHOLD_SECONDS: Final[int] = 30

    # 恢复策略
    RECOVERY_CACHE_SIZE: Final[int] = 1000

    # 阈值
    PERFORMANCE_DROP_THRESHOLD: Final[float] = 0.05  # 5%
    ADAPTATION_THRESHOLD: Final[float] = 0.05


# ==================== 强化学习相关常量 ====================


class RLConfig:
    """强化学习相关配置"""

    # 学习率
    LEARNING_RATE: Final[float] = 0.1
    DISCOUNT_FACTOR: Final[float] = 0.95
    EXPLORE_RATE: Final[float] = 0.1
    EXPLORE_DECAY: Final[float] = 0.995
    MIN_EXPLORE_RATE: Final[float] = 0.01

    # 经验回放
    EXPERIENCE_BUFFER_SIZE: Final[int] = 10000
    BATCH_SIZE: Final[int] = 32
    MIN_REPLAY_SIZE: Final[int] = 100

    # Q表
    DEFAULT_Q_VALUE: Final[float] = 0.0


# ==================== 工具路由相关常量 ====================


class ToolRouterConfig:
    """工具路由相关配置"""

    # 评分权重
    CAPABILITY_WEIGHT: Final[float] = 0.40
    CONFIDENCE_WEIGHT: Final[float] = 0.25
    SPEED_WEIGHT: Final[float] = 0.20
    COST_WEIGHT: Final[float] = 0.15

    # 相似度
    SIMILARITY_THRESHOLD: Final[float] = 0.8
    SIMILARITY_PENALTY_FACTOR: Final[float] = 0.2

    # 选择
    MAX_TOOLS: Final[int] = 3
    MIN_CAPABILITY_SCORE: Final[float] = 0.3


# ==================== 上下文相关常量 ====================


class ContextConfig:
    """上下文相关配置"""

    # Token限制
    MAX_TOKENS: Final[int] = 8000
    TARGET_TOKENS: Final[int] = int(MAX_TOKENS * 0.8)

    # 压缩
    COMPRESSION_RATIO: Final[float] = 0.7

    # 缓存
    CONTEXT_CACHE_SIZE: Final[int] = 1000

    # 对话历史
    MAX_CONVERSATION_TURNS: Final[int] = 10
    RECENT_HISTORY_ROUNDS: Final[int] = 5

    # Token估算(简化版:2字符≈1token)
    CHARS_PER_TOKEN: Final[int] = 2


# ==================== 联邦学习相关常量 ====================


class FederatedLearningConfig:
    """联邦学习相关配置"""

    # 训练
    NUM_ROUNDS: Final[int] = 100
    CLIENTS_PER_ROUND: Final[int] = 10
    LOCAL_EPOCHS: Final[int] = 5

    # 聚合
    MIN_PARTICIPATING_CLIENTS: Final[int] = 5

    # 差分隐私
    DP_NOISE_SCALE: Final[float] = 0.1
    DP_CLIP_NORM: Final[float] = 1.0

    # 通信
    MODEL_COMPRESSION_RATIO: Final[float] = 0.5


# ==================== 模型压缩相关常量 ====================


class ModelCompressionConfig:
    """模型压缩相关配置"""

    # 稀疏度
    TARGET_SPARSITY: Final[float] = 0.5
    PRUNE_ITERATIONS: Final[int] = 10

    # 量化
    QUANTIZATION_CALIBRATION_SAMPLES: Final[int] = 100

    # 秩
    TARGET_RANK: Final[int] = 32


# ==================== 元学习相关常量 ====================


class MetaLearningConfig:
    """元学习相关配置"""

    # MAML
    INNER_LR: Final[float] = 0.01
    OUTER_LR: Final[float] = 0.001
    NUM_INNER_STEPS: Final[int] = 5

    # 任务采样
    TASK_BATCH_SIZE: Final[int] = 10
    NUM_CLASSES: Final[int] = 5
    NUM_SHOTS: Final[int] = 5

    # 支持/查询集
    SUPPORT_SIZE_FACTOR: Final[int] = 1
    QUERY_SIZE_FACTOR: Final[int] = 1


# ==================== 对比学习相关常量 ====================


class ContrastiveLearningConfig:
    """对比学习相关配置"""

    # 温度
    TEMPERATURE: Final[float] = 0.07
    MOMENTUM: Final[float] = 0.999

    # 队列
    QUEUE_SIZE: Final[int] = 65536

    # 增强
    NUM_AUGMENTATIONS: Final[int] = 2

    # 投影
    PROJECTION_DIM: Final[int] = 64
    EMBEDDING_DIM: Final[int] = 128


# ==================== 提示工程相关常量 ====================


class PromptEngineeringConfig:
    """提示工程相关配置"""

    # A/B测试
    AB_TEST_SAMPLES: Final[int] = 10
    MIN_SAMPLES_FOR_SIGNIFICANCE: Final[int] = 30

    # 评估
    QUALITY_WEIGHT: Final[float] = 0.4
    RELEVANCE_WEIGHT: Final[float] = 0.3
    ACCURACY_WEIGHT: Final[float] = 0.3

    # 优化
    MAX_SUGGESTIONS: Final[int] = 10


# ==================== 学习率调度相关常量 ====================


class LearningRateConfig:
    """学习率调度相关配置"""

    # Warmup
    WARMUP_STEPS: Final[int] = 1000
    WARMUP_START_LR_RATIO: Final[float] = 0.1

    # 衰减
    STEP_SIZE: Final[int] = 10000
    STEP_GAMMA: Final[float] = 0.1

    # Cosine
    TOTAL_STEPS: Final[int] = 100000

    # Cyclical
    CYCLE_STEP_UP: Final[int] = 2000
    CYCLE_STEP_DOWN: Final[int] = 2000

    # 平台期
    PATIENCE: Final[int] = 10
    LR_DECAY_FACTOR: Final[float] = 0.5


# ==================== 日志相关常量 ====================


class LoggingConfig:
    """日志相关配置"""

    # 日志级别
    LOG_LEVEL: Final[str] = "INFO"

    # 格式
    LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 文件
    LOG_FILE_MAX_BYTES: Final[int] = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT: Final[int] = 5


# ==================== 性能监控相关常量 ====================


class MonitoringConfig:
    """性能监控相关配置"""

    # 采样
    SAMPLE_RATE: Final[float] = 0.1  # 10%采样

    # 窗口
    SLIDING_WINDOW_SIZE: Final[int] = 100
    METRIC_RETENTION_HOURS: Final[int] = 24

    # 告警
    ALERT_THRESHOLD_P95: Final[float] = 0.95
    ALERT_THRESHOLD_P99: Final[float] = 0.99
