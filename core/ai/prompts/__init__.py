#!/usr/bin/env python3
from __future__ import annotations

"""
提示词系统统一入口
Unified Prompt System Entry

提供简化的API接口：
- evaluate_prompt(file) - 评估提示词质量

作者: 小诺·双鱼公主
版本: v1.0
"""

from pathlib import Path
from typing import Optional

from .quality_evaluator import (
    PromptQualityEvaluator,
    QualityReport,
)

# 默认配置
DEFAULT_PROMPTS_DIR = "/Users/xujian/Athena工作平台/prompts"
DEFAULT_CACHE_DIR = "/tmp/prompt_cache"
DEFAULT_COMPRESSION_RATIO = 0.4


# 全局评估器实例
_evaluator: Optional[PromptQualityEvaluator] = None


def get_evaluator() -> PromptQualityEvaluator:
    """获取或创建评估器实例"""
    global _evaluator
    if _evaluator is None:
        _evaluator = PromptQualityEvaluator()
    return _evaluator


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
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")
    return evaluate_prompt(content)


# 导出
__all__ = [
    # 核心类
    "PromptQualityEvaluator",
    "QualityReport",

    # 便捷函数
    "evaluate_prompt",
    "evaluate_prompt_file",
]
