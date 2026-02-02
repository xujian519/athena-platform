#!/usr/bin/env python3
"""
专利分析模块
Patent Analysis Module

提供完整的专利分析、评估和重写能力
基于Athena专利系统的核心功能

作者: Athena AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""

from .analyzer import PatentAnalyzer
from .evaluator import PatentEvaluator
from .knowledge_graph import PatentKnowledgeGraph
from .rewriter import PatentRewriter

# 版本信息
__version__ = "3.0.0"
__author__ = "Athena AI System"
__description__ = "专利分析和评估系统"

# 导出的主要类
__all__ = [
    "PatentAnalysisSystem",
    "PatentAnalyzer",
    "PatentEvaluator",
    "PatentKnowledgeGraph",
    "PatentRewriter",
]

# 配置日志
import logging

logger = logging.getLogger(__name__)


async def initialize_patent_analysis():
    """初始化专利分析系统"""
    logger.info("🚀 初始化专利分析系统...")

    try:
        # 初始化各组件
        await PatentAnalyzer.initialize()
        await PatentEvaluator.initialize()
        await PatentRewriter.initialize()
        await PatentKnowledgeGraph.initialize()

        logger.info("✅ 专利分析系统初始化完成")

    except Exception as e:
        logger.error(f"❌ 专利分析系统初始化失败: {e}")
        raise


async def shutdown_patent_analysis():
    """关闭专利分析系统"""
    logger.info("🔄 关闭专利分析系统...")

    try:
        # 关闭各组件
        await PatentAnalyzer.shutdown()
        await PatentEvaluator.shutdown()
        await PatentRewriter.shutdown()
        await PatentKnowledgeGraph.shutdown()

        logger.info("✅ 专利分析系统已关闭")

    except Exception as e:
        logger.error(f"❌ 专利分析系统关闭失败: {e}")
