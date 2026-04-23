from __future__ import annotations

"""
Athena专利权利要求质量改进系统

基于三篇AI专利论文的综合实现：
1. 论文1: LLM Patent Classification - 专利分类
2. 论文2: Patentformer - 权利要求生成
3. 论文3: LLM High-Quality Claims - 质量评估

本模块实现：
- 六维质量评估框架
- 交互式改进建议
- 多轮迭代优化
- 质量追踪与学习

作者: Athena平台开发组
版本: v1.0.0
日期: 2026-02-12
"""

from .claim_generator import PatentClaimGenerator
from .interactive_improver import ImprovementSession, InteractiveQualityImprover
from .knowledge_base import CPCKnowledgeBase
from .quality_assessor import ClaimQualityAssessor, QualityAssessment
from .term_normalizer import TechnicalTermNormalizer

__all__ = [
    'ClaimQualityAssessor',
    'QualityAssessment',
    'InteractiveQualityImprover',
    'ImprovementSession',
    'PatentClaimGenerator',
    'TechnicalTermNormalizer',
    'CPCKnowledgeBase',
]
