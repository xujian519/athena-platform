"""
exploration - 主动探索模块

基于《Agentic Design Patterns》第21章:Exploration and Discovery

提供智能体的主动探索能力:
1. 知识图谱空白分析
2. 主动知识发现
3. 替代方案探索
4. 意外发现机制

作者: 小诺·双鱼座
版本: v1.0.0
"""

from .active_exploration_engine import (
    ActiveExplorationEngine,
    ExplorationResult,
    ExplorationStrategy,
    Hypothesis,
    KnowledgeGap,
    get_active_exploration_engine,
)

__all__ = [
    "ActiveExplorationEngine",
    "ExplorationResult",
    "ExplorationStrategy",
    "Hypothesis",
    "KnowledgeGap",
    "get_active_exploration_engine",
]

__version__ = "1.0.0"
__author__ = "小诺·双鱼座"
