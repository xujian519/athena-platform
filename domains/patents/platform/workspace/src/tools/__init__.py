#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块
Tools Module

提供专利分析、数据处理、报告生成等功能
Provides patent analysis, data processing, report generation and other functions

作者: Athena AI系统
创建时间: 2025-12-06
版本: 1.0.0
"""

# 导入各个工具子模块
try:
import logging

from .patent_tools import *

logger = logging.getLogger(__name__)

    PATENT_TOOLS_AVAILABLE = True
except ImportError:
    PATENT_TOOLS_AVAILABLE = False

try:
    from .data_tools import *
    DATA_TOOLS_AVAILABLE = True
except ImportError:
    DATA_TOOLS_AVAILABLE = False

try:
    from .analysis_tools import *
    ANALYSIS_TOOLS_AVAILABLE = True
except ImportError:
    ANALYSIS_TOOLS_AVAILABLE = False

try:
    from .report_tools import *
    REPORT_TOOLS_AVAILABLE = True
except ImportError:
    REPORT_TOOLS_AVAILABLE = False

__version__ = '1.0.0'
__author__ = 'Athena AI系统'

# 工具模块状态
MODULE_STATUS = {
    'patent_tools': PATENT_TOOLS_AVAILABLE,
    'data_tools': DATA_TOOLS_AVAILABLE,
    'analysis_tools': ANALYSIS_TOOLS_AVAILABLE,
    'report_tools': REPORT_TOOLS_AVAILABLE
}

def get_available_modules():
    """获取可用的工具模块列表"""
    return [module for module, available in MODULE_STATUS.items() if available]

def get_module_status():
    """获取模块状态信息"""
    return MODULE_STATUS.copy()

if __name__ == '__main__':
    logger.info('🔧 工具模块集合')
    logger.info(f"版本: {__version__}")
    logger.info(f"作者: {__author__}")
    logger.info(f"可用模块: {get_available_modules()}")
    logger.info(f"模块状态: {get_module_status()}")