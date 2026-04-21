#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利工具模块
Patent Tools Module

提供专利分析、检索、无效性预测等功能
Provides patent analysis, retrieval, invalidity prediction and other functions

作者: Athena AI系统
创建时间: 2025-12-06
版本: 1.0.0
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入核心专利工具类
try:
    from patent-platform/workspace.src.patent_tools.patent_invalidator import (
        PatentInvalidator,
    )
    PATENT_INVALIDATOR_AVAILABLE = True
except ImportError as e:
    PATENT_INVALIDATOR_AVAILABLE = False
    PatentInvalidator = None

try:
    from patent-platform/workspace.src.patent_tools.invalidity_predictor import (
        InvalidityPredictor,
    )
    INVALIDITY_PREDICTOR_AVAILABLE = True
except ImportError as e:
    INVALIDITY_PREDICTOR_AVAILABLE = False
    InvalidityPredictor = None

try:
    from patent-platform/workspace.src.patent_tools.legal_knowledge_enhancer import (
        LegalKnowledgeEnhancer,
    )
    LEGAL_KNOWLEDGE_AVAILABLE = True
except ImportError as e:
    LEGAL_KNOWLEDGE_AVAILABLE = False
    LegalKnowledgeEnhancer = None

__all__ = [
    'PatentInvalidator',
    'InvalidityPredictor',
    'LegalKnowledgeEnhancer'
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'Athena AI系统'

# 工具可用性状态
TOOL_STATUS = {
    'patent_invalidator': PATENT_INVALIDATOR_AVAILABLE,
    'invalidity_predictor': INVALIDITY_PREDICTOR_AVAILABLE,
    'legal_knowledge_enhancer': LEGAL_KNOWLEDGE_AVAILABLE
}

def get_available_tools():
    """获取可用的工具列表"""
    return [tool for tool, available in TOOL_STATUS.items() if available]

def get_tool_status():
    """获取工具状态信息"""
    return TOOL_STATUS.copy()

def check_patent_tools():
    """检查专利工具可用性"""
    results = {}

    if PATENT_INVALIDATOR_AVAILABLE and PatentInvalidator:
        try:
            # 简单测试初始化
            invalidator = PatentInvalidator()
            results['patent_invalidator'] = '✅ 可用'
        except Exception as e:
            results['patent_invalidator'] = f'❌ 错误: {str(e)[:50]}...'
    else:
        results['patent_invalidator'] = '❌ 不可用'

    if INVALIDITY_PREDICTOR_AVAILABLE and InvalidityPredictor:
        try:
            predictor = InvalidityPredictor()
            results['invalidity_predictor'] = '✅ 可用'
        except Exception as e:
            results['invalidity_predictor'] = f'❌ 错误: {str(e)[:50]}...'
    else:
        results['invalidity_predictor'] = '❌ 不可用'

    if LEGAL_KNOWLEDGE_AVAILABLE and LegalKnowledgeEnhancer:
        try:
            enhancer = LegalKnowledgeEnhancer()
            results['legal_knowledge_enhancer'] = '✅ 可用'
        except Exception as e:
            results['legal_knowledge_enhancer'] = f'❌ 错误: {str(e)[:50]}...'
    else:
        results['legal_knowledge_enhancer'] = '❌ 不可用'

    return results

if __name__ == '__main__':
    logger.info('🔧 专利工具模块状态')
    logger.info(f"版本: {__version__}")
    logger.info(f"作者: {__author__}")
    logger.info(f"\n工具检查结果:")
    for tool, status in check_patent_tools().items():
        logger.info(f"  {tool}: {status}")