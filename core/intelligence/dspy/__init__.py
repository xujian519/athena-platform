"""
DSPy集成模块 - Athena平台
DSPy Integration Module for Athena Platform

本模块提供DSPy框架与Athena平台的集成能力,包括:
- DSPy配置管理
- LLM后端适配
- 向量检索适配
- 知识图谱检索适配
- 混合提示词生成器

版本: v1.0.0
创建时间: 2025-12-29
"""

from .llm_backend import (
    ATHENA_LLM_AVAILABLE,
    AthenaLLMDirect,
    AthenaLLMModule,
    create_athena_dspy_lm,
    create_athena_module,
    get_athena_llm_client,
)

__all__ = [
    "ATHENA_LLM_AVAILABLE",
    "AthenaGraphRetriever",
    "AthenaHybridRetriever",
    # LLM后端
    "AthenaLLMDirect",
    "AthenaLLMModule",
    # 检索器
    "AthenaVectorRetriever",
    # 配置
    "DSPyConfig",
    # 混合提示词生成器
    "DSPyHybridPromptGenerator",
    "HybridPromptConfig",
    "configure_dspy",
    "create_athena_dspy_lm",
    "create_athena_module",
    "create_hybrid_generator",
    "get_athena_llm_client",
    "get_config",
]

__version__ = "1.0.0"
