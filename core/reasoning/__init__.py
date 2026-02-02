from typing import Optional
#!/usr/bin/env python3
"""
推理引擎模块 - 统一架构版本
Reasoning Engines Module - Unified Architecture

包含Athena工作平台的所有推理引擎,采用统一编排架构。

核心创新:
- 统一推理引擎编排器 (UnifiedReasoningOrchestrator)
- 自动识别任务类型
- 智能选择最优引擎
- 专业任务直接调用专业能力(绕过超级推理)

核心框架:
- 六步推理框架 (Six-Step Reasoning)
- 七步推理框架 (Seven-Step Reasoning / Athena Super Reasoning)

32模式超级推理:
- Athena增强推理引擎 (32种推理模式)

统一与高级推理:
- 统一推理引擎
- 双系统推理 (系统1+2)
- 高级推理 (贝叶斯/模糊/模态/反事实)  # TODO: 确保除数不为零

多模式推理系统:
- Athena多模式推理系统 (Think Hard / Think Harder / Super Thinking)

专利/法律推理:
- 语义推理引擎 v1/v4
- 法律推理引擎
- 小娜超级推理引擎 (法律专家版)
- 增强法律推理引擎
- AI推理引擎 (无效宣告)
- 合规判断引擎
- 专家规则引擎
- 专利规则链引擎
- 现有技术分析器
- 路线图生成器
- LLM增强判断引擎

清理状态:
- ✅ 已删除重复文件 (athena_super_reasoning_original.py)
- ✅ 已删除重复文件 (xiaonuo_super_reasoning_original.py)
- ✅ 新增统一编排器 (unified_reasoning_orchestrator.py)

作者: 小诺·双鱼座 v4.0.0
创建: 2025-12-31
版本: v4.0.0 (统一架构版)
"""

# 版本信息
__version__ = "4.0.0"
__author__ = "小诺·双鱼公主 v4.0.0"


# =============================================================================
# === 核心推理框架 ===
# =============================================================================


from .athena_super_reasoning import (
    AthenaSuperReasoningEngine,
    ConfidenceLevel,
    ReasoningState,
    RecursiveThinkingEngine,
    ThinkingPhase,
)

# LLM增强版本 (V2)
# try:
#     from .athena_super_reasoning_v2 import (
#         LLMEnhancedHypothesisManager,
#         LLMEnhancedSuperReasoningEngine,
#     )
# except Exception as e:
#     LLMEnhancedHypothesisManager = None

LLMEnhancedHypothesisManager = None  # 暂时禁用，文件有语法错误

from .xiaonuo_reasoning_bridge import (
    ReasoningRequest,
    ReasoningResponse,
    XiaonuoReasoningBridge,
    get_reasoning_bridge,
    reason,
)
from .xiaonuo_six_step_reasoning import ReasoningMode, SixStepPhase, XiaonuoSixStepReasoningEngine

# =============================================================================
# === 32模式超级推理 ===
# =============================================================================

try:
    from .athena_enhanced_reasoning_32modes import (
        AthenaReasoningEngine as Athena32ModesReasoningEngine,
    )
    from .athena_enhanced_reasoning_32modes import (
        ReasoningCapability,
        ReasoningCategory,
        ReasoningPerformanceMonitor,
        ReasoningStrategySelector,
    )
    from .athena_enhanced_reasoning_32modes import (
        ReasoningComplexity as ReasoningComplexity32,
    )
    from .athena_enhanced_reasoning_32modes import (
        ReasoningResult as ReasoningResult32,
    )
    from .athena_enhanced_reasoning_32modes import (
        ReasoningTask as ReasoningTask32,
    )
    from .athena_enhanced_reasoning_32modes import (
        ReasoningType as ReasoningType32,
    )
except Exception as e:
    ReasoningCategory = None
    ReasoningType32 = None
    ReasoningComplexity32 = None
    ReasoningTask32 = None
    ReasoningResult32 = None
    ReasoningCapability = None
    ReasoningStrategySelector = None
    ReasoningPerformanceMonitor = None


# =============================================================================
# === 统一与高级推理 ===
# =============================================================================

try:
    from .unified_reasoning_engine import (
        BaseReasoner as UnifiedBaseReasoner,
    )
    from .unified_reasoning_engine import (
        BayesianReasoner as UnifiedBayesianReasoner,
    )
    from .unified_reasoning_engine import (
        DualSystemReasoner as UnifiedDualSystemReasoner,
    )
    from .unified_reasoning_engine import (
        NeuroSymbolicReasoner,
        UnifiedReasoningEngine,
    )
    from .unified_reasoning_engine import (
        ReasoningChain as UnifiedReasoningChain,
    )
    from .unified_reasoning_engine import (
        ReasoningComplexity as UnifiedReasoningComplexity,
    )
    from .unified_reasoning_engine import (
        ReasoningContext as UnifiedReasoningContext,
    )
    from .unified_reasoning_engine import (
        ReasoningResult as UnifiedReasoningResult,
    )
    from .unified_reasoning_engine import (
        ReasoningStep as UnifiedReasoningStep,
    )
    from .unified_reasoning_engine import (
        ReasoningType as UnifiedReasoningType,
    )
    from .unified_reasoning_engine import (
        System1Reasoner as UnifiedSystem1Reasoner,
    )
    from .unified_reasoning_engine import (
        System2Reasoner as UnifiedSystem2Reasoner,
    )
except Exception as e:
    UnifiedSystem1Reasoner = None
    UnifiedSystem2Reasoner = None
    UnifiedBayesianReasoner = None
    NeuroSymbolicReasoner = None
    UnifiedDualSystemReasoner = None
    UnifiedBaseReasoner = None
    UnifiedReasoningType = None
    UnifiedReasoningContext = None
    UnifiedReasoningStep = None
    UnifiedReasoningChain = None
    UnifiedReasoningResult = None
    UnifiedReasoningComplexity = None

try:
    from .dual_system_reasoning import (
        DualSystemInteraction,
        System1Profile,
        System2Profile,
    )
    from .dual_system_reasoning import (
        DualSystemReasoning as DualSystemReasoningEngine,
    )
    from .dual_system_reasoning import (
        System1Reasoner as DualSystemSystem1Reasoner,
    )
    from .dual_system_reasoning import (
        System2Reasoner as DualSystemSystem2Reasoner,
    )
except Exception as e:
    DualSystemSystem1Reasoner = None
    DualSystemSystem2Reasoner = None
    System1Profile = None
    System2Profile = None
    DualSystemInteraction = None

try:
    from .advanced_reasoning_lingxi import (
        BayesianReasoner as AdvancedBayesianReasoner,
    )
    from .advanced_reasoning_lingxi import (
        CounterfactualReasoner,
        FuzzyReasoner,
        ModalReasoner,
    )
except Exception as e:
    FuzzyReasoner = None
    ModalReasoner = None
    CounterfactualReasoner = None


# =============================================================================
# === 多模式推理系统 ===
# =============================================================================

try:
    from .athena_multimodal_reasoning_system import (
        AgentRole,
        AIAgent,
        AITeamCoordinator,
        AthenaMultimodalReasoningEngine,
        ThinkingComplexity,
        ThinkingStep,
        ThinkingTask,
    )
    from .athena_multimodal_reasoning_system import (
        ReasoningMode as MultimodalReasoningMode,
    )
except Exception as e:
    MultimodalReasoningMode = None
    ThinkingComplexity = None
    AgentRole = None
    ThinkingTask = None
    ThinkingStep = None
    AIAgent = None
    AITeamCoordinator = None


# =============================================================================
# === 专利/法律推理引擎 ===
# =============================================================================

# 语义推理引擎
try:
    from .semantic_reasoning_engine import (
        ReasoningResult as SemanticReasoningResult,
    )
    from .semantic_reasoning_engine import (
        ReasoningRule as SemanticReasoningRule,
    )
    from .semantic_reasoning_engine import (
        ReasoningType as SemanticReasoningType,
    )
    from .semantic_reasoning_engine import (
        SemanticReasoningEngine,
    )
except Exception as e:
    SemanticReasoningType = None
    SemanticReasoningResult = None
    SemanticReasoningRule = None

try:
    from .semantic_reasoning_engine_v4 import (
        ReasoningResultV4,
        SemanticReasoningEngineV4,
    )
    from .semantic_reasoning_engine_v4 import (
        ReasoningRule as SemanticReasoningRuleV4,
    )
except Exception as e:
    import logging

    logging.getLogger(__name__).warning(f"semantic_reasoning_engine_v4 导入失败: {e}")
    SemanticReasoningEngineV4 = None
    ReasoningResultV4 = None
    SemanticReasoningRuleV4 = None

# 法律推理引擎
try:
    from .xiaona_super_reasoning_engine import (
        LegalReasoningMode,
        LegalReasoningNode,
        XiaonaSuperReasoningEngine,
    )
except Exception as e:
    LegalReasoningMode = None
    LegalReasoningNode = None

try:
    from .enhanced_legal_reasoning_engine import (
        EnhancedLegalReasoningEngine,
        InventivenessAnalysisResult,
        InventivenessConclusion,
        NoveltyAnalysisResult,
        NoveltyConclusion,
        PriorArtReference,
        TechnicalFeature,
    )
except Exception as e:
    NoveltyConclusion = None
    InventivenessConclusion = None
    TechnicalFeature = None
    PriorArtReference = None
    NoveltyAnalysisResult = None
    InventivenessAnalysisResult = None

# AI推理引擎 (无效宣告) - 暂时禁用(语法错误)
try:
    from .ai_reasoning_engine_invalidity import (
        AIReasoningEngine,
        QueryResult,
    )
    from .ai_reasoning_engine_invalidity import (
        ReasoningTask as AIReasoningTask,
    )
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"ai_reasoning_engine_invalidity 导入失败: {e}")
    QueryResult = None
    AIReasoningTask = None

# 其他专业引擎
try:
    from .compliance_judge import ComplianceJudge
except Exception as e:
    pass

try:
    from .expert_rule_engine import (
        ExpertRuleEngine,
    )
    from .expert_rule_engine import (
        ReasoningChain as ExpertReasoningChain,
    )
    from .expert_rule_engine import (
        ReasoningRule as ExpertReasoningRule,
    )
except Exception as e:
    ExpertReasoningRule = None
    ExpertReasoningChain = None

try:
    from .patent_rule_chain import PatentRuleChainEngine
except Exception as e:
    pass

try:
    from .prior_art_analyzer import PriorArtAnalyzer
except Exception as e:
    pass

try:
    from .roadmap_generator import RoadmapGenerator
except Exception as e:
    pass

try:
    from .llm_enhanced_judgment import LLMEnhancedJudgment
except Exception as e:
    pass


# =============================================================================
# === 统一推理引擎编排器 ===
# =============================================================================

try:
    from .unified_reasoning_orchestrator import (
        EngineRecommendation as OrchestratorEngineRecommendation,
    )
    from .unified_reasoning_orchestrator import (
        TaskComplexity as OrchestratorTaskComplexity,
    )
    from .unified_reasoning_orchestrator import (
        TaskDomain as OrchestratorTaskDomain,
    )
    from .unified_reasoning_orchestrator import (
        TaskProfile as OrchestratorTaskProfile,
    )
    from .unified_reasoning_orchestrator import (
        TaskType as OrchestratorTaskType,
    )
    from .unified_reasoning_orchestrator import (
        UnifiedReasoningOrchestrator,
        get_orchestrator,
    )
    from .unified_reasoning_orchestrator import (
        execute_reasoning as orchestrated_execute_reasoning,
    )
except Exception as e:
    OrchestratorTaskDomain = None
    OrchestratorTaskComplexity = None
    OrchestratorTaskType = None
    OrchestratorTaskProfile = None
    OrchestratorEngineRecommendation = None
    get_orchestrator = None
    orchestrated_execute_reasoning = None

# === 增强版统一推理引擎编排器 v2.0 (带缓存和性能监控) ===
try:
    from .unified_reasoning_orchestrator_v2 import (
        EngineRecommendation as OrchestratorV2EngineRecommendation,
    )
    from .unified_reasoning_orchestrator_v2 import (
        ReasoningCache,
    )
    from .unified_reasoning_orchestrator_v2 import (
        TaskComplexity as OrchestratorV2TaskComplexity,
    )
    from .unified_reasoning_orchestrator_v2 import (
        TaskDomain as OrchestratorV2TaskDomain,
    )
    from .unified_reasoning_orchestrator_v2 import (
        TaskProfile as OrchestratorV2TaskProfile,
    )
    from .unified_reasoning_orchestrator_v2 import (
        TaskType as OrchestratorV2TaskType,
    )
    from .unified_reasoning_orchestrator_v2 import (
        UnifiedReasoningOrchestratorV2,
        get_orchestrator_v2,
    )
    from .unified_reasoning_orchestrator_v2 import (
        execute_reasoning_v2,
    )
except Exception as e:
    OrchestratorV2TaskDomain = None
    OrchestratorV2TaskComplexity = None
    OrchestratorV2TaskType = None
    OrchestratorV2TaskProfile = None
    OrchestratorV2EngineRecommendation = None
    UnifiedReasoningOrchestratorV2 = None
    ReasoningCache = None
    get_orchestrator_v2 = None
    execute_reasoning_v2 = None

# === 并行推理引擎和结果融合 ===
try:
    from .parallel_reasoning_engine import (
        ConflictReport,
        ConflictType,
        FusionResult,
        FusionStrategy,
        ParallelReasoningEngine,
        ReasoningResult as ParallelReasoningResult,
        ResultFusionEngine,
    )
except Exception as e:
    ParallelReasoningEngine = None
    ResultFusionEngine = None
    FusionStrategy = None
    FusionResult = None
    ConflictType = None
    ConflictReport = None
    ParallelReasoningResult = None

# === 性能监控系统 ===
try:
    from .performance_monitor import (
        AlertSeverity,
        EnginePerformanceReport,
        MetricData,
        MetricType,
        PerformanceAlert,
        PerformanceMonitor,
        get_performance_monitor,
        record_engine_performance,
    )
except Exception as e:
    PerformanceMonitor = None
    MetricType = None
    MetricData = None
    PerformanceAlert = None
    AlertSeverity = None
    EnginePerformanceReport = None
    get_performance_monitor = None
    record_engine_performance = None

# === 推理历史分析和增量学习系统 ===
try:
    from .reasoning_learning_system import (
        EnginePerformanceStats,
        FeedbackType,
        IncrementalLearningSystem,
        ReasoningHistoryAnalyzer,
        ReasoningRecord,
        RoutingOptimizer,
        RoutingRule,
    )
    from .reasoning_learning_system import (
        get_history_analyzer,
        get_learning_system,
        record_reasoning as learning_record_reasoning,
    )
except Exception as e:
    ReasoningRecord = None
    FeedbackType = None
    EnginePerformanceStats = None
    RoutingRule = None
    ReasoningHistoryAnalyzer = None
    IncrementalLearningSystem = None
    RoutingOptimizer = None
    get_history_analyzer = None
    get_learning_system = None
    learning_record_reasoning = None

# === 推理结果可解释性增强系统 ===
try:
    from .reasoning_explainability import (
        ExplainabilityLevel,
        InteractiveReasoningEditor,
        ReasoningAdjustment,
        ReasoningChain,
        ReasoningExplainer,
        ReasoningQualityAssessor,
        ReasoningStep,
        VisualizationFormat,
    )
    from .reasoning_explainability import (
        explain_reasoning as explain_reasoning_func,
    )
    from .reasoning_explainability import (
        get_assessor,
        get_editor,
        get_explainer,
    )
except Exception as e:
    ExplainabilityLevel = None
    VisualizationFormat = None
    ReasoningStep = None
    ReasoningChain = None
    ReasoningAdjustment = None
    ReasoningExplainer = None
    InteractiveReasoningEditor = None
    ReasoningQualityAssessor = None
    get_explainer = None
    get_editor = None
    get_assessor = None
    explain_reasoning_func = None


# =============================================================================
# === 基础模块 ===
# =============================================================================

try:
    from .enhanced_reasoning_base import (
        BaseReasoner,
        MetacognitiveMonitor,
        MetacognitiveState,
        ThinkingMode,
        create_reasoning_context,
        create_reasoning_step,
    )
    from .enhanced_reasoning_base import (
        ReasoningChain as BaseReasoningChain,
    )
    from .enhanced_reasoning_base import (
        ReasoningComplexity as BaseReasoningComplexity,
    )
    from .enhanced_reasoning_base import (
        ReasoningContext as BaseReasoningContext,
    )
    from .enhanced_reasoning_base import (
        ReasoningResult as BaseReasoningResult,
    )
    from .enhanced_reasoning_base import (
        ReasoningStep as BaseReasoningStep,
    )
    from .enhanced_reasoning_base import (
        ReasoningStrategySelector as BaseStrategySelector,
    )
    from .enhanced_reasoning_base import (
        ReasoningType as BaseReasoningType,
    )
except Exception as e:
    ThinkingMode = None
    BaseReasoningComplexity = None
    MetacognitiveState = None
    BaseReasoningStep = None
    BaseReasoningContext = None
    BaseReasoningResult = None
    BaseReasoningChain = None
    BaseReasoner = None
    MetacognitiveMonitor = None
    BaseStrategySelector = None
    create_reasoning_step = None
    create_reasoning_context = None


# =============================================================================
# === 推理引擎选择器 ===
# =============================================================================

try:
    from .engine_selector import (
        EngineRecommendation,
        ReasoningEngineSelector,
        TaskComplexity,
        TaskDomain,
        TaskProfile,
        TaskType,
        UrgencyLevel,
        get_selector,
        select_reasoning_engine,
    )
except Exception as e:
    TaskComplexity = None
    TaskType = None
    UrgencyLevel = None
    TaskProfile = None
    EngineRecommendation = None
    ReasoningEngineSelector = None
    get_selector = None
    select_reasoning_engine = None


# =============================================================================
# === 统一接口 ===
# =============================================================================


def get_reasoning_engine(mode: str = "auto", task_description: str | None = None, **kwargs):
    """获取推理引擎实例(支持自动选择)

    Args:
        mode: 推理模式,设置为 'auto' 时自动选择最合适的引擎
        task_description: 任务描述(仅在 mode='auto' 时使用)
        **kwargs: 额外参数(用于自动选择)

    Returns:
        推理引擎实例

    Available modes:
        - auto: 自动选择(推荐,需要 task_description)
        - six_step: 六步推理
        - seven_step: 七步推理
        - 32modes: 32模式超级推理
        - multimodal: 多模式推理系统
        - unified: 统一推理引擎
        - dual_system: 双系统推理
        - semantic: 语义推理
        - semantic_v4: 语义推理 v4
        - legal: 法律推理
        - enhanced_legal: 增强法律推理
        - ai_invalidity: AI推理(无效宣告)
        - compliance: 合规判断
        - expert_rule: 专家规则
        - patent_rule: 专利规则链
        - prior_art: 现有技术分析
        - roadmap: 路线图生成
        - llm_judgment: LLM增强判断
    """
    # 自动选择模式
    if mode == "auto":
        if select_reasoning_engine is not None and task_description:
            mode = select_reasoning_engine(task_description, **kwargs)
        else:
            mode = "seven_step"  # 默认使用七步推理

    engine_map = {
        # 核心框架
        "six_step": XiaonuoSixStepReasoningEngine,
        "seven_step": AthenaSuperReasoningEngine,
        # 32模式超级推理
        "32modes": Athena32ModesReasoningEngine,
        # 统一与高级推理
        "unified": UnifiedReasoningEngine,
        "dual_system": DualSystemReasoningEngine,
        # 多模式推理系统
        "multimodal": AthenaMultimodalReasoningEngine,
        # 专利/法律推理
        "semantic": SemanticReasoningEngine,
        "semantic_v4": SemanticReasoningEngineV4,
        "legal": XiaonaSuperReasoningEngine,
        "enhanced_legal": EnhancedLegalReasoningEngine,
        "ai_invalidity": AIReasoningEngine,
        "compliance": ComplianceJudge,
        "expert_rule": ExpertRuleEngine,
        "patent_rule": PatentRuleChainEngine,
        "prior_art": PriorArtAnalyzer,
        "roadmap": RoadmapGenerator,
        "llm_judgment": LLMEnhancedJudgment,
    }

    engine_class = engine_map.get(mode)
    if engine_class is None:
        available_modes = [k for k, v in engine_map.items() if v is not None]
        raise ValueError(f"未知的推理模式: {mode},可用模式: {available_modes}")

    return engine_class()


async def execute_reasoning(problem: str, mode: str = "seven_step", context: Optional[dict] | None = None):
    """执行推理的便捷函数

    Args:
        problem: 待解决的问题
        mode: 推理模式
        context: 上下文信息

    Returns:
        推理结果
    """
    engine = get_reasoning_engine(mode)

    # 根据不同引擎调用不同的方法
    if mode == "multimodal" and hasattr(engine, "execute_reasoning"):
        return await engine.execute_reasoning(problem, context or {})
    elif mode == "32modes" and hasattr(engine, "execute_reasoning"):
        if ReasoningTask32 is not None:
            from .athena_enhanced_reasoning_32modes import ReasoningComplexity, ReasoningTask

            task = ReasoningTask(
                query=problem,
                domain="general",
                complexity=ReasoningComplexity.MEDIUM,
                context=context or {},
            )
            return await engine.execute_reasoning(task)
        else:
            return await engine.execute_super_reasoning(problem, context or {})
    else:
        # 默认调用 execute_super_reasoning 或 execute_reasoning
        if hasattr(engine, "execute_super_reasoning"):
            return await engine.execute_super_reasoning(problem, context or {})
        elif hasattr(engine, "execute_reasoning"):
            return await engine.execute_reasoning(problem, context or {})
        else:
            raise AttributeError(f"引擎 {mode} 没有可执行的推理方法")


def get_all_reasoning_engines() -> dict:
    """获取所有可用的推理引擎

    Returns:
        引擎名称到引擎类的映射
    """
    engines = {
        # 核心框架
        "six_step": XiaonuoSixStepReasoningEngine,
        "seven_step": AthenaSuperReasoningEngine,
        # 32模式超级推理
        "32modes": Athena32ModesReasoningEngine,
        # 统一与高级推理
        "unified": UnifiedReasoningEngine,
        "dual_system": DualSystemReasoningEngine,
        # 多模式推理系统
        "multimodal": AthenaMultimodalReasoningEngine,
        # 专利/法律推理
        "semantic": SemanticReasoningEngine,
        "semantic_v4": SemanticReasoningEngineV4,
        "legal": XiaonaSuperReasoningEngine,
        "enhanced_legal": EnhancedLegalReasoningEngine,
        "ai_invalidity": AIReasoningEngine,
        "compliance": ComplianceJudge,
        "expert_rule": ExpertRuleEngine,
        "patent_rule": PatentRuleChainEngine,
        "prior_art": PriorArtAnalyzer,
        "roadmap": RoadmapGenerator,
        "llm_judgment": LLMEnhancedJudgment,
        # 统一编排器
        "orchestrator": UnifiedReasoningOrchestrator,
    }

    # 过滤掉None值
    return {k: v for k, v in engines.items() if v is not None}


def list_available_engines() -> list:
    """列出所有可用的推理引擎

    Returns:
        可用引擎的名称列表
    """
    engines = get_all_reasoning_engines()
    return list(engines.keys())


def get_engine_info(mode: str) -> dict:
    """获取推理引擎的详细信息

    Args:
        mode: 推理模式

    Returns:
        引擎信息字典
    """
    engine_map = {
        "six_step": {
            "name": "六步推理框架",
            "description": "问题分解→跨学科连接→抽象建模→递归分析→创新突破→综合验证",
            "category": "核心框架",
            "version": "1.0.0",
        },
        "seven_step": {
            "name": "七步推理框架",
            "description": "初始参与→问题分析→假设生成→自然发现→测试验证→错误修正→知识综合",
            "category": "核心框架",
            "version": "1.0.0",
        },
        "32modes": {
            "name": "Athena增强推理引擎",
            "description": "32种推理模式,8大推理分类",
            "category": "32模式超级推理",
            "version": "1.0.0",
        },
        "multimodal": {
            "name": "Athena多模式推理系统",
            "description": "Think Hard / Think Harder / Super Thinking 三层推理",
            "category": "多模式推理系统",
            "version": "3.0.0",
        },
        "unified": {
            "name": "统一推理引擎",
            "description": "统一整合多种推理引擎的接口",
            "category": "统一与高级推理",
            "version": "1.0.0",
        },
        "dual_system": {
            "name": "双系统推理引擎",
            "description": "系统1(快思考)和系统2(慢思考)的协同推理",
            "category": "统一与高级推理",
            "version": "1.0.0",
        },
        "semantic": {
            "name": "语义推理引擎",
            "description": "基于语义理解的推理",
            "category": "专利/法律推理",
            "version": "1.0.0",
        },
        "semantic_v4": {
            "name": "语义推理引擎 v4",
            "description": "增强版语义推理",
            "category": "专利/法律推理",
            "version": "4.0.0",
        },
        "legal": {
            "name": "小娜超级推理引擎",
            "description": "法律专家版推理引擎",
            "category": "专利/法律推理",
            "version": "3.0.0",
        },
        "enhanced_legal": {
            "name": "增强法律推理引擎",
            "description": "专业法律分析引擎",
            "category": "专利/法律推理",
            "version": "2.0.0",
        },
    }

    return engine_map.get(
        mode, {"name": mode, "description": "未知推理引擎", "category": "未知", "version": "未知"}
    )


# =============================================================================
# === __all__ 导出列表 ===
# =============================================================================

__all__ = [
    "AIAgent",
    "AIReasoningEngine",
    "AIReasoningTask",
    "AITeamCoordinator",
    "AdvancedBayesianReasoner",
    "AgentRole",
    # === 32模式超级推理 ===
    "Athena32ModesReasoningEngine",
    # === 多模式推理系统 ===
    "AthenaMultimodalReasoningEngine",
    # === 核心框架 ===
    "AthenaSuperReasoningEngine",
    "BaseReasoner",
    "BaseReasoningChain",
    "BaseReasoningComplexity",
    "BaseReasoningContext",
    "BaseReasoningResult",
    "BaseReasoningStep",
    # === 基础模块 ===
    "BaseReasoningType",
    "BaseStrategySelector",
    "ComplianceJudge",
    "ConfidenceLevel",
    "CounterfactualReasoner",
    "DualSystemInteraction",
    "DualSystemReasoningEngine",
    "DualSystemSystem1Reasoner",
    "DualSystemSystem2Reasoner",
    "EngineRecommendation",
    "EnhancedLegalReasoningEngine",
    "EnginePerformanceStats",
    "ExplainabilityLevel",
    "ExpertReasoningChain",
    "ExpertReasoningRule",
    "ExpertRuleEngine",
    "FeedbackType",
    "FuzzyReasoner",
    "IncrementalLearningSystem",
    "InventivenessAnalysisResult",
    "InventivenessConclusion",
    "InteractiveReasoningEditor",
    "LLMEnhancedJudgment",
    "LegalReasoningMode",
    "LegalReasoningNode",
    "MetacognitiveMonitor",
    "MetacognitiveState",
    "ModalReasoner",
    "MultimodalReasoningMode",
    "NeuroSymbolicReasoner",
    "NoveltyAnalysisResult",
    "NoveltyConclusion",
    "OrchestratorEngineRecommendation",
    "OrchestratorTaskComplexity",
    "OrchestratorTaskDomain",
    "OrchestratorTaskProfile",
    "OrchestratorTaskType",
    "PatentRuleChainEngine",
    "PriorArtAnalyzer",
    "PriorArtReference",
    "QueryResult",
    "ReasoningAdjustment",
    "ReasoningCapability",
    "ReasoningCategory",
    "ReasoningChain",
    "ReasoningComplexity32",
    "ReasoningEngineSelector",
    "ReasoningHistoryAnalyzer",
    "ReasoningMode",
    "ReasoningPerformanceMonitor",
    "ReasoningQualityAssessor",
    "ReasoningRecord",
    "ReasoningRequest",
    "ReasoningResponse",
    "ReasoningResult32",
    "ReasoningResultV4",
    "ReasoningState",
    "ReasoningStep",
    "ReasoningStrategySelector",
    "ReasoningTask32",
    "ReasoningType32",
    "RecursiveThinkingEngine",
    "RoadmapGenerator",
    "RoutingOptimizer",
    "RoutingRule",
    # === 专利/法律推理 ===
    "SemanticReasoningEngine",
    "SemanticReasoningEngineV4",
    "SemanticReasoningResult",
    "SemanticReasoningRule",
    "SemanticReasoningRuleV4",
    "SemanticReasoningType",
    "SixStepPhase",
    "System1Profile",
    "System2Profile",
    "TaskComplexity",
    # === 推理引擎选择器 ===
    "TaskDomain",
    "TaskProfile",
    "TaskType",
    "TechnicalFeature",
    "ThinkingComplexity",
    "ThinkingMode",
    "ThinkingPhase",
    "ThinkingStep",
    "ThinkingTask",
    "UnifiedBaseReasoner",
    "UnifiedBayesianReasoner",
    "UnifiedDualSystemReasoner",
    "UnifiedReasoningChain",
    "UnifiedReasoningComplexity",
    "UnifiedReasoningContext",
    # === 统一与高级推理 ===
    "UnifiedReasoningEngine",
    # === 统一推理引擎编排器 ===
    "UnifiedReasoningOrchestrator",
    "UnifiedReasoningResult",
    "UnifiedReasoningStep",
    "UnifiedReasoningType",
    "UnifiedSystem1Reasoner",
    "UnifiedSystem2Reasoner",
    "UrgencyLevel",
    "VisualizationFormat",
    "AbductiveReasoner",
    "AnalogicalReasoner",
    "CausalReasoner",
    "CounterfactualReasoner",
    "DeductiveReasoner",
    "InductiveReasoner",
    "MetacognitiveReasoner",
    "XiaonaSuperReasoningEngine",
    "XiaonuoReasoningBridge",
    "XiaonuoSixStepReasoningEngine",
    "__author__",
    # 版本信息
    "__version__",
    "create_reasoning_context",
    "create_reasoning_step",
    "explain_reasoning_func",
    "execute_reasoning",
    "get_all_reasoning_engines",
    "get_assessor",
    "get_engine_info",
    "get_editor",
    "get_explainer",
    "get_history_analyzer",
    "get_learning_system",
    "get_orchestrator",
    "get_reasoning_bridge",
    # === 统一接口 ===
    "get_reasoning_engine",
    "get_selector",
    "learning_record_reasoning",
    "list_available_engines",
    "orchestrated_execute_reasoning",
    "reason",
    "select_reasoning_engine",
]

# =============================================================================
# === 新增推理模式模块 (2026-01-26) ===
# =============================================================================

try:
    from .enhanced_reasoning_modes import (
        AbductiveReasoner,
        AnalogicalReasoner,
        CausalReasoner,
        CounterfactualReasoner,
        DeductiveReasoner,
        InductiveReasoner,
        MetacognitiveReasoner,
    )
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"enhanced_reasoning_modes 导入失败: {e}")
    AbductiveReasoner = None
    AnalogicalReasoner = None
    CausalReasoner = None
    CounterfactualReasoner = None
    DeductiveReasoner = None
    InductiveReasoner = None
    MetacognitiveReasoner = None
