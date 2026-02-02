#!/usr/bin/env python3
"""
评估与反思模块 - 统一导出接口
Evaluation & Reflection Module - Unified Export Interface

提供完整的评估功能，包括:
- 基础评估引擎
- 增强评估模块
- 质量评估器
- 反思系统
- 专利检索指标

作者: Athena AI系统
版本: v2.0.0
更新时间: 2026-01-30
"""

import logging

logger = logging.getLogger(__name__)

# =============================================================================
# === 基础评估引擎 ===
# =============================================================================

class EvaluationEngine:
    """基础评估引擎"""

    def __init__(self, agent_id: str, config: dict | None = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False

    async def initialize(self):
        logger.info(f"📊 启动评估引擎: {self.agent_id}")
        self.initialized = True

    async def evaluate(self, data):
        return {"score": 0.8, "feedback": "good"}

    def register_callback(self, event_type: str, callback) -> None:
        """注册回调函数"""
        if not hasattr(self, "_callbacks"):
            self._callbacks = {}
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    async def shutdown(self):
        logger.info(f"🔄 关闭评估引擎: {self.agent_id}")
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
# === 增强评估模块 ===
# =============================================================================

try:
    from .enhanced_evaluation_module import (
        EnhancedEvaluationModule,
        EvaluationTask,
        EvaluationTaskResult,
    )

    ENHANCED_EVALUATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"增强评估模块导入失败: {e}")
    ENHANCED_EVALUATION_AVAILABLE = False
    EnhancedEvaluationModule = None
    EvaluationTask = None
    EvaluationTaskResult = None


# =============================================================================
# === 增强质量评估器 ===
# =============================================================================

try:
    from .enhanced_quality_assessor import (
        AssessmentCriteria,
        AssessmentDimension,
        AssessmentResult,
        EnhancedQualityAssessor,
        QualityMetrics,
        QualityReport,
    )

    QUALITY_ASSESSOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"增强质量评估器导入失败: {e}")
    QUALITY_ASSESSOR_AVAILABLE = False
    EnhancedQualityAssessor = None
    AssessmentCriteria = None
    AssessmentDimension = None
    AssessmentResult = None
    QualityMetrics = None
    QualityReport = None


# =============================================================================
# === 评估引擎 (完整版) ===
# =============================================================================

try:
    from .evaluation_engine import (
        EvaluationCriteria,
        EvaluationEngine as FullEvaluationEngine,
        EvaluationLevel,
        EvaluationResult,
        EvaluationType,
    )

    FULL_ENGINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"完整评估引擎导入失败: {e}")
    FULL_ENGINE_AVAILABLE = False
    FullEvaluationEngine = None
    EvaluationCriteria = None
    EvaluationLevel = None
    EvaluationResult = None
    EvaluationType = None


# =============================================================================
# === 评估引擎子模块 ===
# =============================================================================

try:
    from .evaluation_engine.engine import (
        BatchEvaluator,
        EvaluationContext,
        SequentialEvaluator,
    )
    from .evaluation_engine.metrics import (
        EvaluationMetrics,
        MetricsCalculator,
    )
    from .evaluation_engine.qa_checker import (
        QAChecker,
        QACheckResult,
    )
    from .evaluation_engine.reflection import (
        ReflectionRecord,
        ReflectionType,
    )
    from .evaluation_engine.types import (
        AssessmentType,
        EvaluationScope,
    )

    ENGINE_SUBMODULES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"评估引擎子模块导入失败: {e}")
    ENGINE_SUBMODULES_AVAILABLE = False
    BatchEvaluator = None
    EvaluationContext = None
    SequentialEvaluator = None
    EvaluationMetrics = None
    MetricsCalculator = None
    QAChecker = None
    QACheckResult = None
    ReflectionRecord = None
    ReflectionType = None
    AssessmentType = None
    EvaluationScope = None


# =============================================================================
# === 轻量级评估引擎 ===
# =============================================================================

try:
    from .lightweight_evaluation_engine import (
        LightweightEvaluationEngine,
        get_lightweight_evaluator,
    )

    LIGHTWEIGHT_ENGINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"轻量级评估引擎导入失败: {e}")
    LIGHTWEIGHT_ENGINE_AVAILABLE = False
    LightweightEvaluationEngine = None


# =============================================================================
# === 专利检索指标 ===
# =============================================================================

try:
    from .patent_retrieval_metrics import (
        PatentRetrievalMetrics,
        RetrievalQualityAssessor,
    )

    PATENT_METRICS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"专利检索指标模块导入失败: {e}")
    PATENT_METRICS_AVAILABLE = False
    PatentRetrievalMetrics = None
    RetrievalQualityAssessor = None


# =============================================================================
# === 反馈系统 ===
# =============================================================================

try:
    from .xiaonuo_feedback_system import (
        FeedbackCollector,
        FeedbackProcessor,
        XiaonuoFeedbackSystem,
    )

    FEEDBACK_SYSTEM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"反馈系统导入失败: {e}")
    FEEDBACK_SYSTEM_AVAILABLE = False
    FeedbackCollector = None
    FeedbackProcessor = None
    XiaonuoFeedbackSystem = None


# =============================================================================
# === 其他组件 ===
# =============================================================================

try:
    from .evaluation_config import EvaluationConfig
    from .async_file_ops import AsyncFileOperations
except ImportError as e:
    logger.warning(f"其他组件导入失败: {e}")
    EvaluationConfig = None
    AsyncFileOperations = None


# =============================================================================
# === 统一导出列表 ===
# =============================================================================

__all__ = [
    # === 基础评估引擎 ===
    "EvaluationEngine",
    # === 增强评估模块 ===
    "EnhancedEvaluationModule",
    "EvaluationTask",
    "EvaluationTaskResult",
    # === 增强质量评估器 ===
    "EnhancedQualityAssessor",
    "AssessmentCriteria",
    "AssessmentDimension",
    "AssessmentResult",
    "QualityMetrics",
    "QualityReport",
    # === 完整评估引擎 ===
    "FullEvaluationEngine",
    "EvaluationCriteria",
    "EvaluationLevel",
    "EvaluationResult",
    "EvaluationType",
    # === 评估引擎子模块 ===
    "BatchEvaluator",
    "EvaluationContext",
    "SequentialEvaluator",
    "EvaluationMetrics",
    "MetricsCalculator",
    "QAChecker",
    "QACheckResult",
    "ReflectionRecord",
    "ReflectionType",
    "AssessmentType",
    "EvaluationScope",
    # === 轻量级评估引擎 ===
    "LightweightEvaluationEngine",
    # === 专利检索指标 ===
    "PatentRetrievalMetrics",
    "RetrievalQualityAssessor",
    # === 反馈系统 ===
    "XiaonuoFeedbackSystem",
    "FeedbackCollector",
    "FeedbackProcessor",
    # === 其他组件 ===
    "EvaluationConfig",
    "AsyncFileOperations",
    # === 便捷函数 ===
    "get_lightweight_evaluator",
]


# =============================================================================
# === 模块可用性检查 ===
# =============================================================================

def get_module_capabilities() -> dict:
    """获取评估模块可用能力"""
    return {
        "enhanced_evaluation": ENHANCED_EVALUATION_AVAILABLE,
        "quality_assessor": QUALITY_ASSESSOR_AVAILABLE,
        "full_engine": FULL_ENGINE_AVAILABLE,
        "engine_submodules": ENGINE_SUBMODULES_AVAILABLE,
        "lightweight_engine": LIGHTWEIGHT_ENGINE_AVAILABLE,
        "patent_metrics": PATENT_METRICS_AVAILABLE,
        "feedback_system": FEEDBACK_SYSTEM_AVAILABLE,
    }


def get_available_features() -> list:
    """获取可用功能列表"""
    capabilities = get_module_capabilities()
    return [name for name, available in capabilities.items() if available]
