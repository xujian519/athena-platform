from __future__ import annotations
"""
专利AI服务模块
Patent AI Services Module

提供基于论文研究的专利智能服务:
- 专利分类
- 权利要求修订
- 无效性预测
- 质量评分
- 权利要求范围测量 (基于论文2023)
- 专利附图智能分析 (基于论文2025 PatentVision)
- 专利说明书自动撰写 (基于论文2025 AutoSpec)
- 知识激活诊断系统 (基于论文2025 Missing vs. Unused Knowledge)
- 专利任务分类系统 (基于专利NLP综述)
- 多模态检索增强系统 (基于多模态专利检索论文)
- 综合质量评估增强 (基于专利质量评估论文)
"""

from .autospec_drafter import (
    AutoSpecDrafter,
    DraftPhase,
    InventionType,
    InventionUnderstanding,
    QualityReport,
    SectionContent,
    SectionType,
    SpecificationDraft,
    TechnicalFeature,
    draft_patent_specification,
    format_specification,
)
from .claim_reviser import ClaimReviser, RevisionResult
from .claim_scope_analyzer import (
    AnalysisMode,
    ClaimScopeAnalyzer,
    ProbabilityEstimate,
    RiskLevel,
    ScopeAnalysisResult,
    ScopeComparison,
    ScopeScore,
    analyze_claim_scope,
    format_scope_report,
)
from .drawing_analyzer import (
    ComponentConnection,
    ComponentType,
    DrawingAnalysisResult,
    DrawingAnnotation,
    DrawingComponent,
    DrawingType,
    PatentDrawingAnalyzer,
    analyze_patent_drawing,
    format_figure_description,
    format_full_figure_description,
)
from .invalidity_predictor import InvalidityPrediction, InvalidityPredictor
from .knowledge_diagnosis import (
    ActivationSession,
    ActivationStrategy,
    ClarificationQuestion,
    DiagnosisResult,
    DiagnosisSeverity,
    ErrorType,
    KnowledgeActivationDiagnoser,
    OptimizationRecommendation,
    SelfAnsweringPrompt,
    activate_and_improve,
    diagnose_response,
    format_diagnosis_report,
)
from .multimodal_retrieval import (
    CrossModalRetriever,
    FusionStrategy,
    HybridFusion,
    HybridSearchResult,
    ImageSearchQuery,
    ImageType,
    ImageVector,
    ImageVectorizer,
    MultimodalRetrievalSystem,
    RelevanceLevel,
    RetrievalConfig,
    SearchMode,
    SearchResult,
    TextVector,
    format_search_result,
    hybrid_search,
    multimodal_search,
)
from .patent_classifier import ClassificationResult, PatentClassifier
from .patent_quality_scorer import ComprehensiveQualityReport, EnhancedPatentQualityScorer
from .quality_assessment_enhanced import (
    AssessmentType,
    BenchmarkComparison,
    DimensionEvaluator,
    DimensionScore,
    EnhancedQualityAssessment,
    EnhancedQualityAssessor,
    ImprovementGenerator,
    ImprovementPriority,
    ImprovementSuggestion,
    QualityDimension,
    QualityGrade,
    QualityRisk,
    RiskAnalyzer,
    assess_patent_quality,
    format_assessment_report,
)
from .quality_assessment_enhanced import RiskLevel as QualityRiskLevel
from .task_classifier import (
    ExecutionPriority,
    PatentTaskClassifier,
    PatentTaskType,
    SubTask,
    TaskClassificationResult,
    TaskComplexity,
    WorkflowStage,
    WorkflowStep,
    classify_patent_task,
    format_classification_report,
    get_workflow_for_task,
)

__all__ = [
    # 分类器
    "PatentClassifier",
    "ClassificationResult",
    # 修订器
    "ClaimReviser",
    "RevisionResult",
    # 无效性预测
    "InvalidityPredictor",
    "InvalidityPrediction",
    # 质量评分
    "EnhancedPatentQualityScorer",
    "ComprehensiveQualityReport",
    # 范围测量
    "ClaimScopeAnalyzer",
    "ScopeAnalysisResult",
    "ScopeScore",
    "ProbabilityEstimate",
    "RiskLevel",
    "AnalysisMode",
    "ScopeComparison",
    "analyze_claim_scope",
    "format_scope_report",
    # 附图分析
    "PatentDrawingAnalyzer",
    "DrawingAnalysisResult",
    "DrawingComponent",
    "ComponentConnection",
    "DrawingAnnotation",
    "DrawingType",
    "ComponentType",
    "analyze_patent_drawing",
    "format_figure_description",
    "format_full_figure_description",
    # 说明书撰写
    "AutoSpecDrafter",
    "SpecificationDraft",
    "InventionUnderstanding",
    "SectionContent",
    "TechnicalFeature",
    "QualityReport",
    "DraftPhase",
    "SectionType",
    "InventionType",
    "draft_patent_specification",
    "format_specification",
    # 知识激活诊断
    "KnowledgeActivationDiagnoser",
    "DiagnosisResult",
    "ClarificationQuestion",
    "SelfAnsweringPrompt",
    "OptimizationRecommendation",
    "ActivationSession",
    "ErrorType",
    "DiagnosisSeverity",
    "ActivationStrategy",
    "diagnose_response",
    "activate_and_improve",
    "format_diagnosis_report",
    # 任务分类
    "PatentTaskClassifier",
    "TaskClassificationResult",
    "SubTask",
    "WorkflowStep",
    "PatentTaskType",
    "TaskComplexity",
    "WorkflowStage",
    "ExecutionPriority",
    "classify_patent_task",
    "get_workflow_for_task",
    "format_classification_report",
    # 多模态检索
    "MultimodalRetrievalSystem",
    "ImageVectorizer",
    "CrossModalRetriever",
    "HybridFusion",
    "ImageVector",
    "TextVector",
    "SearchResult",
    "HybridSearchResult",
    "ImageSearchQuery",
    "RetrievalConfig",
    "SearchMode",
    "ImageType",
    "FusionStrategy",
    "RelevanceLevel",
    "hybrid_search",
    "multimodal_search",
    "format_search_result",
    # 综合质量评估
    "EnhancedQualityAssessor",
    "DimensionEvaluator",
    "RiskAnalyzer",
    "ImprovementGenerator",
    "DimensionScore",
    "QualityRisk",
    "ImprovementSuggestion",
    "BenchmarkComparison",
    "EnhancedQualityAssessment",
    "QualityDimension",
    "QualityGrade",
    "QualityRiskLevel",
    "ImprovementPriority",
    "AssessmentType",
    "assess_patent_quality",
    "format_assessment_report",
]

__version__ = "1.7.0"
