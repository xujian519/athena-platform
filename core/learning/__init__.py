#!/usr/bin/env python3
"""
学习与适应模块 - 统一导出接口
Learning & Adaptation Module - Unified Export Interface

提供完整的学习功能，包括:
- 基础学习引擎
- 增强学习引擎
- 自主学习系统
- 在线学习
- 强化学习
- 元学习
- 知识蒸馏
- 迁移学习
- 不确定性量化

作者: Athena AI系统
版本: v2.0.0
更新时间: 2026-01-30
"""

import logging

logger = logging.getLogger(__name__)

# =============================================================================
# === 基础学习引擎 ===
# =============================================================================

class LearningEngine:
    """基础学习引擎"""

    def __init__(self, agent_id: str, config: dict | None = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False
        self._callbacks: dict = {}  # 初始化回调字典

    async def initialize(self):
        logger.info(f"📚 启动学习引擎: {self.agent_id}")
        self.initialized = True

    async def learn(self, data):
        return {"status": "learned"}

    def register_callback(self, event_type: str, callback) -> None:
        """注册回调函数"""
        if not hasattr(self, "_callbacks"):
            self._callbacks = {}
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    async def shutdown(self):
        logger.info(f"🔄 关闭学习引擎: {self.agent_id}")
        self.initialized = False

    @classmethod
    async def initialize_global(cls):
        if not hasattr(cls, "global_instance"):
            cls.global_instance = cls("global", {})
            await cls.global_instance.initialize()
        return cls.global_instance

    @classmethod
    async def shutdown_global(cls):
        if hasattr(cls, "global_instance") and cls.global_instance:
            await cls.global_instance.shutdown()
            del cls.global_instance


# =============================================================================
# === 学习引擎 (模块化版本) ===
# =============================================================================

try:
    from .learning_engine import (
        AdaptiveOptimizer,
        ExperienceStore,
        KnowledgeGraphUpdater,
        LearningEngine as ModularLearningEngine,
        PatternRecognizer,
    )

    MODULAR_LEARNING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"模块化学习引擎导入失败: {e}")
    MODULAR_LEARNING_AVAILABLE = False
    ModularLearningEngine = None
    AdaptiveOptimizer = None
    ExperienceStore = None
    KnowledgeGraphUpdater = None
    PatternRecognizer = None


# =============================================================================
# === 增强学习引擎 ===
# =============================================================================

try:
    from .enhanced_learning_engine import (
        EnhancedLearningEngine,
        LearningConfig,
        LearningStrategy,
        LearningTask,
    )

    ENHANCED_LEARNING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"增强学习引擎导入失败: {e}")
    ENHANCED_LEARNING_AVAILABLE = False
    EnhancedLearningEngine = None
    LearningConfig = None
    LearningStrategy = None
    LearningTask = None


# =============================================================================
# === 增强学习引擎 v4 ===
# =============================================================================

try:
    from .enhanced_learning_engine import (
        LearningEngineV4,
        get_learning_engine_v4,
    )

    LEARNING_V4_AVAILABLE = True
except ImportError as e:
    logger.warning(f"学习引擎v4导入失败: {e}")
    LEARNING_V4_AVAILABLE = False
    LearningEngineV4 = None


# =============================================================================
# === 自主学习系统 ===
# =============================================================================

try:
    from .autonomous_learning_system import (
        AutonomousLearningSystem,
        LearningAutonomy,
        SelfImprovementCycle,
    )

    AUTONOMOUS_LEARNING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"自主学习系统导入失败: {e}")
    AUTONOMOUS_LEARNING_AVAILABLE = False
    AutonomousLearningSystem = None
    LearningAutonomy = None
    SelfImprovementCycle = None


# =============================================================================
# === 在线学习 ===
# =============================================================================

try:
    from .online_learning import OnlineLearningSystem
    from .online_learning_engine import OnlineLearningEngine
    from .online_learning_system import IncrementalLearner

    ONLINE_LEARNING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"在线学习模块导入失败: {e}")
    ONLINE_LEARNING_AVAILABLE = False
    OnlineLearningSystem = None
    OnlineLearningEngine = None
    IncrementalLearner = None


# =============================================================================
# === 强化学习 ===
# =============================================================================

try:
    from .reinforcement_learning_agent import (
        ReinforcementLearningAgent,
        RLPolicy,
        RLTrainer,
    )
    from .production_rl_integration import (
        ProductionRLIntegration,
        RLProductionConfig,
    )

    RL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"强化学习模块导入失败: {e}")
    RL_AVAILABLE = False
    ReinforcementLearningAgent = None
    RLPolicy = None
    RLTrainer = None
    ProductionRLIntegration = None
    RLProductionConfig = None


# =============================================================================
# === 元学习 ===
# =============================================================================

try:
    from .meta_learning_engine import MetaLearningEngine
    from .enhanced_meta_learning import EnhancedMetaLearning
    from .enhanced_meta_learning_impl import MetaLearningImplementation

    META_LEARNING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"元学习模块导入失败: {e}")
    META_LEARNING_AVAILABLE = False
    MetaLearningEngine = None
    EnhancedMetaLearning = None
    MetaLearningImplementation = None


# =============================================================================
# === 知识蒸馏 ===
# =============================================================================

try:
    from .knowledge_distillation import (
        DistillationConfig,
        KnowledgeDistillation,
        TeacherStudentModel,
    )

    DISTILLATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"知识蒸馏模块导入失败: {e}")
    DISTILLATION_AVAILABLE = False
    DistillationConfig = None
    KnowledgeDistillation = None
    TeacherStudentModel = None


# =============================================================================
# === 迁移学习 ===
# =============================================================================

try:
    from .transfer_learning_framework import (
        TransferLearningFramework,
        TransferStrategy,
        DomainAdaptation,
    )

    TRANSFER_LEARNING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"迁移学习模块导入失败: {e}")
    TRANSFER_LEARNING_AVAILABLE = False
    TransferLearningFramework = None
    TransferStrategy = None
    DomainAdaptation = None


# =============================================================================
# === 不确定性量化 ===
# =============================================================================

try:
    from .uncertainty_quantifier import (
        UncertaintyQuantifier,
        UncertaintyEstimate,
    )

    UNCERTAINTY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"不确定性量化模块导入失败: {e}")
    UNCERTAINTY_AVAILABLE = False
    UncertaintyQuantifier = None
    UncertaintyEstimate = None


# =============================================================================
# === 不确定性量化 v4 ===
# =============================================================================

try:
    from .v4.uncertainty_quantifier import (
        UncertaintyQuantifierV4,
        get_uncertainty_quantifier_v4,
    )

    UNCERTAINTY_V4_AVAILABLE = True
except ImportError as e:
    logger.warning(f"不确定性量化v4导入失败: {e}")
    UNCERTAINTY_V4_AVAILABLE = False
    UncertaintyQuantifierV4 = None


# =============================================================================
# === 快速学习 ===
# =============================================================================

try:
    from .rapid_learning import (
        RapidLearningEngine,
        RapidLearner,
    )
    from .rapid_learning.engine import RapidLearningEngine as RapidLearningEngineV2

    RAPID_LEARNING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"快速学习模块导入失败: {e}")
    RAPID_LEARNING_AVAILABLE = False
    RapidLearningEngine = None
    RapidLearner = None
    RapidLearningEngineV2 = None


# =============================================================================
# === 深度学习引擎 ===
# =============================================================================

try:
    from .deep_learning_engine import (
        DeepLearningEngine,
        NeuralNetworkArchitecture,
    )

    DEEP_LEARNING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"深度学习引擎导入失败: {e}")
    DEEP_LEARNING_AVAILABLE = False
    DeepLearningEngine = None
    NeuralNetworkArchitecture = None


# =============================================================================
# === 端到端模型 ===
# =============================================================================

try:
    from .end_to_end_model import (
        EndToEndModel,
        EndToEndTrainer,
    )

    END_TO_END_AVAILABLE = True
except ImportError as e:
    logger.warning(f"端到端模型导入失败: {e}")
    END_TO_END_AVAILABLE = False
    EndToEndModel = None
    EndToEndTrainer = None


# =============================================================================
# === 个性化学习 ===
# =============================================================================

try:
    from .xiaonuo_personalized_learning import (
        PersonalizedLearningSystem,
        UserProfile,
        LearningPath,
    )

    PERSONALIZED_LEARNING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"个性化学习模块导入失败: {e}")
    PERSONALIZED_LEARNING_AVAILABLE = False
    PersonalizedLearningSystem = None
    UserProfile = None
    LearningPath = None


# =============================================================================
# === 记忆巩固系统 ===
# =============================================================================

try:
    from .memory_consolidation_system import (
        MemoryConsolidationSystem,
        ConsolidationStrategy,
    )

    MEMORY_CONSOLIDATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"记忆巩固系统导入失败: {e}")
    MEMORY_CONSOLIDATION_AVAILABLE = False
    MemoryConsolidationSystem = None
    ConsolidationStrategy = None


# =============================================================================
# === RL监控 ===
# =============================================================================

try:
    from .rl_monitoring import (
        RLMonitor,
        RLTrainingMetrics,
    )

    RL_MONITORING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"RL监控模块导入失败: {e}")
    RL_MONITORING_AVAILABLE = False
    RLMonitor = None
    RLTrainingMetrics = None


# =============================================================================
# === 其他组件 ===
# =============================================================================

try:
    from .learning_config import LearningModuleConfig
    from .learning_evaluator import LearningEvaluator
    from .benchmarks import LearningBenchmarks
    from .concurrency_control import ConcurrencyController
    from .error_handling import LearningErrorHandler
    from .exceptions import LearningException
    from .input_validator import InputValidator
    from .persistence_manager import LearningPersistenceManager
    from .base_interface import BaseLearningInterface
except ImportError as e:
    logger.warning(f"其他组件导入失败: {e}")
    LearningModuleConfig = None
    LearningEvaluator = None
    LearningBenchmarks = None
    ConcurrencyController = None
    LearningErrorHandler = None
    LearningException = None
    InputValidator = None
    LearningPersistenceManager = None
    BaseLearningInterface = None


# =============================================================================
# === API ===
# =============================================================================

try:
    from .api import LearningAPI, get_learning_api
except ImportError as e:
    logger.warning(f"学习API导入失败: {e}")
    LearningAPI = None


# =============================================================================
# === 统一导出列表 ===
# =============================================================================

__all__ = [
    # === 基础学习引擎 ===
    "LearningEngine",
    # === 模块化学习引擎 ===
    "ModularLearningEngine",
    "AdaptiveOptimizer",
    "ExperienceStore",
    "KnowledgeGraphUpdater",
    "PatternRecognizer",
    # === 增强学习引擎 ===
    "EnhancedLearningEngine",
    "LearningConfig",
    "LearningStrategy",
    "LearningTask",
    # === 学习引擎 v4 ===
    "LearningEngineV4",
    # === 自主学习系统 ===
    "AutonomousLearningSystem",
    "LearningAutonomy",
    "SelfImprovementCycle",
    # === 在线学习 ===
    "OnlineLearningSystem",
    "OnlineLearningEngine",
    "IncrementalLearner",
    # === 强化学习 ===
    "ReinforcementLearningAgent",
    "RLPolicy",
    "RLTrainer",
    "ProductionRLIntegration",
    "RLProductionConfig",
    # === 元学习 ===
    "MetaLearningEngine",
    "EnhancedMetaLearning",
    "MetaLearningImplementation",
    # === 知识蒸馏 ===
    "DistillationConfig",
    "KnowledgeDistillation",
    "TeacherStudentModel",
    # === 迁移学习 ===
    "TransferLearningFramework",
    "TransferStrategy",
    "DomainAdaptation",
    # === 不确定性量化 ===
    "UncertaintyQuantifier",
    "UncertaintyEstimate",
    # === 不确定性量化 v4 ===
    "UncertaintyQuantifierV4",
    # === 快速学习 ===
    "RapidLearningEngine",
    "RapidLearner",
    # === 深度学习 ===
    "DeepLearningEngine",
    "NeuralNetworkArchitecture",
    # === 端到端模型 ===
    "EndToEndModel",
    "EndToEndTrainer",
    # === 个性化学习 ===
    "PersonalizedLearningSystem",
    "UserProfile",
    "LearningPath",
    # === 记忆巩固 ===
    "MemoryConsolidationSystem",
    "ConsolidationStrategy",
    # === RL监控 ===
    "RLMonitor",
    "RLTrainingMetrics",
    # === 其他组件 ===
    "LearningModuleConfig",
    "LearningEvaluator",
    "LearningBenchmarks",
    "ConcurrencyController",
    "LearningErrorHandler",
    "LearningException",
    "InputValidator",
    "LearningPersistenceManager",
    "BaseLearningInterface",
    # === API ===
    "LearningAPI",
    # === 便捷函数 ===
    "get_learning_api",
    "get_learning_engine_v4",
    "get_uncertainty_quantifier_v4",
]


# =============================================================================
# === 模块可用性检查 ===
# =============================================================================

def get_module_capabilities() -> dict:
    """获取学习模块可用能力"""
    return {
        "modular_learning": MODULAR_LEARNING_AVAILABLE,
        "enhanced_learning": ENHANCED_LEARNING_AVAILABLE,
        "learning_v4": LEARNING_V4_AVAILABLE,
        "autonomous_learning": AUTONOMOUS_LEARNING_AVAILABLE,
        "online_learning": ONLINE_LEARNING_AVAILABLE,
        "reinforcement_learning": RL_AVAILABLE,
        "meta_learning": META_LEARNING_AVAILABLE,
        "knowledge_distillation": DISTILLATION_AVAILABLE,
        "transfer_learning": TRANSFER_LEARNING_AVAILABLE,
        "uncertainty_quantification": UNCERTAINTY_AVAILABLE,
        "uncertainty_v4": UNCERTAINTY_V4_AVAILABLE,
        "rapid_learning": RAPID_LEARNING_AVAILABLE,
        "deep_learning": DEEP_LEARNING_AVAILABLE,
        "end_to_end": END_TO_END_AVAILABLE,
        "personalized_learning": PERSONALIZED_LEARNING_AVAILABLE,
        "memory_consolidation": MEMORY_CONSOLIDATION_AVAILABLE,
        "rl_monitoring": RL_MONITORING_AVAILABLE,
    }


def get_available_features() -> list:
    """获取可用功能列表"""
    capabilities = get_module_capabilities()
    return [name for name, available in capabilities.items() if available]
