#!/usr/bin/env python3
"""
⚠️  警告：Phase 3 开发中
⚠️  WARNING: Phase 3 Under Development

此模块处于开发中，请勿用于生产环境！
This module is under development, do NOT use in production!

请使用 Phase 2 系统：
Please use Phase 2 system:
    cd /Users/xujian/Athena工作平台/production/dev/scripts/patent_full_text
    python3 vectorize_with_local_bge.py

文档：Documentation:
    - Phase 2: ../PRODUCTION_USER_GUIDE.md
    - Phase 3: ./DEVELOPMENT_WARNING.md
"""

from __future__ import annotations
__version__ = "3.0.0-dev"
__status__ = "DEVELOPMENT"  # 开发中
__production_ready__ = False  # 不适用于生产环境

# ========== Schema定义 ==========
# ========== 核心处理模块 ==========
from .claim_parser_v2 import ClaimData, ClaimParserV2, ClaimType, ParsedClaims, parse_claims
from .content_chunker import (
    ChunkedContent,
    ContentChunk,
    ContentChunker,
    ContentSection,
    chunk_content,
)

# ========== 数据库集成 (Phase 4) ==========
from .db_integration import (
    ConnectionInfo,
    ConnectionStatus,
    DatabaseIntegration,
    DBIntegrationConfig,
    DBType,
    HealthCheckResult,
    NebulaManager,
    QdrantManager,
    create_db_integration,
)

# ========== 部署管理 (Phase 6) ==========
from .deployment_manager import (
    DeploymentEnvironment,
    DeploymentManager,
    DeploymentResult,
    ServiceInfo,
    ServiceStatus,
    create_deployment_manager,
    deploy_service,
)
from .kg_builder_v2 import (
    InsertResult,
    InsertStatus,
    KGBuildResult,
    PatentKGBuilderV2,
    build_patent_kg,
)

# ========== 模型加载 ==========
from .model_loader import (
    ModelInfo,
    ModelLoader,
    get_model_loader,
    load_embedding_model,
    load_sequence_tagger,
    unload_all_models,
)
from .nebula_schema import (
    FeatureCategory,
    FeatureRelation,
    NebulaSchemaDefinitions,
    NebulaSchemaManager,
    ProblemType,
    RelationType,
    TechnicalEffect,
    TechnicalFeature,
    TechnicalProblem,
    Triple,
    TripleExtractionResult,
)
from .pipeline_v2 import (
    PatentFullTextPipelineV2,
    PipelineInput,
    PipelineResult,
    create_pipeline_input,
    process_patent,
)

# ========== 生产配置 (Phase 6) ==========
from .production_config import (
    APIServerConfig,
    CacheConfig,
    KnowledgeGraphConfig,
    LoggingConfig,
    LogLevel,
    ModelConfig,
    MonitoringConfig,
    NebulaConfig,
    ProcessingConfig,
    ProductionConfig,
    QdrantConfig,
    RedisConfig,
    TripleExtractionConfig,
    VectorizationConfig,
    get_development_config,
    get_staging_config,
    load_production_config,
)
from .qdrant_schema import (
    ClaimType,
    ContentSection,
    QdrantCollectionConfig,
    QdrantSchemaManager,
    VectorInfo,
    VectorizationResultV2,
    VectorPayload,
    VectorType,
    create_payload_from_patent,
    get_default_config,
    get_schema_manager,
)
from .rule_extractor import (
    FeatureCategory,
    FeatureRelation,
    ProblemType,
    RelationType,
    RuleExtractor,
    TechnicalEffect,
    TechnicalFeature,
    TechnicalProblem,
    Triple,
    TripleExtractionResult,
    extract_triples,
)

# ========== 系统优化 (Phase 5) ==========
from .system_optimization import (
    BatchProcessor,
    BatchResult,
    CacheEntry,
    CacheLevel,
    CacheManager,
    MemoryCache,
    PerformanceMonitor,
    RetryHandler,
    cached,
    create_batch_processor,
    create_cache_manager,
    create_retry_handler,
    get_performance_monitor,
    monitor_performance,
)
from .vector_processor_v2 import (
    PatentDataV2,
    VectorProcessorV2,
    create_patent_data,
    vectorize_patent,
)

__all__ = [
    # Schema
    "VectorType",
    "ClaimType",
    "ContentSection",
    "QdrantCollectionConfig",
    "VectorPayload",
    "VectorInfo",
    "VectorizationResultV2",
    "QdrantSchemaManager",
    "get_default_config",
    "get_schema_manager",
    "create_payload_from_patent",

    # NebulaGraph Schema
    "ProblemType",
    "FeatureCategory",
    "RelationType",
    "NebulaSchemaDefinitions",
    "NebulaSchemaManager",
    "TechnicalProblem",
    "TechnicalFeature",
    "TechnicalEffect",
    "Triple",
    "FeatureRelation",
    "TripleExtractionResult",

    # Core Processing
    "ClaimData",
    "ParsedClaims",
    "ClaimParserV2",
    "parse_claims",

    "ContentChunk",
    "ChunkedContent",
    "ContentChunker",
    "chunk_content",

    "PatentDataV2",
    "VectorProcessorV2",
    "create_patent_data",
    "vectorize_patent",

    "RuleExtractor",
    "extract_triples",

    "KGBuildResult",
    "PatentKGBuilderV2",
    "build_patent_kg",

    "PipelineInput",
    "PipelineResult",
    "PatentFullTextPipelineV2",
    "create_pipeline_input",
    "process_patent",

    # Model Loader
    "ModelLoader",
    "ModelInfo",
    "get_model_loader",
    "load_embedding_model",
    "load_sequence_tagger",
    "unload_all_models",

    # Database Integration (Phase 4)
    "DBType",
    "ConnectionStatus",
    "ConnectionInfo",
    "HealthCheckResult",
    "QdrantManager",
    "NebulaManager",
    "DBIntegrationConfig",
    "DatabaseIntegration",
    "create_db_integration",

    # System Optimization (Phase 5)
    "CacheLevel",
    "CacheEntry",
    "MemoryCache",
    "CacheManager",
    "cached",
    "BatchResult",
    "BatchProcessor",
    "RetryHandler",
    "PerformanceMonitor",
    "get_performance_monitor",
    "monitor_performance",
    "create_cache_manager",
    "create_batch_processor",
    "create_retry_handler",

    # Deployment Management (Phase 6)
    "DeploymentEnvironment",
    "ServiceStatus",
    "ServiceInfo",
    "DeploymentResult",
    "DeploymentManager",
    "create_deployment_manager",
    "deploy_service",

    # Production Configuration (Phase 6)
    "LogLevel",
    "QdrantConfig",
    "NebulaConfig",
    "RedisConfig",
    "ModelConfig",
    "CacheConfig",
    "ProcessingConfig",
    "VectorizationConfig",
    "TripleExtractionConfig",
    "KnowledgeGraphConfig",
    "LoggingConfig",
    "MonitoringConfig",
    "APIServerConfig",
    "ProductionConfig",
    "load_production_config",
    "get_development_config",
    "get_staging_config",
]
