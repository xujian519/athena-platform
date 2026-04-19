#!/usr/bin/env python3
from __future__ import annotations
"""
提示词系统统一入口
Unified Prompt System Entry

提供简化的API接口：
- get_prompt(task_type) - 获取完整提示词
- get_minimal_prompt() - 获取最小上下文
- evaluate_prompt(file) - 评估提示词质量

作者: 小诺·双鱼公主
版本: v1.0
"""

from pathlib import Path
from typing import Optional

from .progressive_loader import (
    ComplexityLevel,
    ProgressivePromptLoader,
    PromptContext,
    TaskType,
)
from .quality_evaluator import (
    PromptQualityEvaluator,
    QualityReport,
    evaluate_prompt_file,
)

# 默认配置
DEFAULT_PROMPTS_DIR = "/Users/xujian/Athena工作平台/prompts"
DEFAULT_CACHE_DIR = "/tmp/prompt_cache"
DEFAULT_COMPRESSION_RATIO = 0.4


# 全局加载器实例
_loader: ProgressivePromptLoader | None = None
_evaluator: PromptQualityEvaluator | None = None


def get_loader(
    prompts_dir: str = DEFAULT_PROMPTS_DIR,
    compression_ratio: float = DEFAULT_COMPRESSION_RATIO,
) -> ProgressivePromptLoader:
    """获取或创建加载器实例"""
    global _loader
    if _loader is None:
        _loader = ProgressivePromptLoader(
            prompts_dir=prompts_dir,
            compression_ratio=compression_ratio,
        )
    return _loader


def get_evaluator() -> PromptQualityEvaluator:
    """获取或创建评估器实例"""
    global _evaluator
    if _evaluator is None:
        _evaluator = PromptQualityEvaluator()
    return _evaluator


def get_prompt(
    task_type: str = "general",
    complexity: str = "medium",
    domain: str = "general",
    include_data_layer: bool = False,
) -> str:
    """
    获取完整提示词

    Args:
        task_type: 任务类型 (general, patent_writing, office_action, etc.)
        complexity: 复杂度 (simple, medium, complex)
        domain: 领域
        include_data_layer: 是否包含数据层

    Returns:
        完整提示词文本

    Token消耗估算:
        - general: ~5K tokens
        - patent_writing (simple): ~15K tokens
        - patent_writing (complex): ~25K tokens
        - office_action (complex): ~30K tokens
    """
    loader = get_loader()

    context = PromptContext(
        task_type=TaskType(task_type),
        complexity=ComplexityLevel(complexity),
        domain=domain,
    )

    loaded = loader.build_prompt(context, include_data_layer)
    return '\n\n---\n\n'.join(s.content for s in loaded.segments)


def get_minimal_prompt() -> str:
    """
    获取最小上下文提示词

    约 5K tokens，包含：
    - 基础身份和角色
    - HITL核心协议
    - 任务路由信息
    """
    loader = get_loader()
    return loader.get_minimal_context()


def get_capability_prompt(capabilities: list[str]) -> str:
    """
    获取能力层提示词

    Args:
        capabilities: 能力列表 ["retrieval", "analysis", "writing", ...]

    Returns:
        能力层提示词
    """
    loader = get_loader()
    return loader.get_capability_context(capabilities)


def get_business_prompt(task_type: str) -> str:
    """
    获取业务层提示词

    Args:
        task_type: 任务类型

    Returns:
        业务层提示词
    """
    loader = get_loader()
    return loader.get_business_context(TaskType(task_type))


def evaluate_prompt(prompt: str) -> QualityReport:
    """
    评估提示词质量

    Args:
        prompt: 提示词内容

    Returns:
        质量报告
    """
    evaluator = get_evaluator()
    return evaluator.evaluate(prompt)


def evaluate_prompt_file(file_path: str) -> QualityReport:
    """
    评估提示词文件

    Args:
        file_path: 文件路径

    Returns:
        质量报告
    """
    return evaluate_prompt_file(Path(file_path))


def get_system_stats() -> dict:
    """获取系统统计信息"""
    loader = get_loader()
    return loader.get_stats()


# 便捷常量
TASK_TYPES = [t.value for t in TaskType]
COMPLEXITY_LEVELS = [c.value for c in ComplexityLevel]


# 导出
__all__ = [
    # 核心类
    "ProgressivePromptLoader",
    "PromptContext",
    "TaskType",
    "ComplexityLevel",
    "PromptQualityEvaluator",
    "QualityReport",

    # 便捷函数
    "get_prompt",
    "get_minimal_prompt",
    "get_capability_prompt",
    "get_business_prompt",
    "evaluate_prompt",
    "evaluate_prompt_file",
    "get_system_stats",

    # 常量
    "TASK_TYPES",
    "COMPLEXITY_LEVELS",
]
