#!/usr/bin/env python3
"""
Athena迭代式深度搜索系统
基于XiaoXi工作平台的搜索架构，专为专利搜索优化

主要功能：
- 多轮迭代式深度搜索
- 智能查询生成和扩展
- 结果重排序和筛选
- 研究摘要自动生成
- 专利特定搜索策略
"""

__version__ = '1.0.0'
__author__ = 'Athena Patent Search Team'

import logging

from .agent import AthenaIterativeSearchAgent
from .config import AthenaSearchConfig, SearchDepth, SearchStrategy
from .core import AthenaIterativeSearchEngine
from .types import PatentSearchResult

__all__ = [
    'AthenaIterativeSearchEngine',
    'PatentSearchResult',
    'AthenaSearchConfig',
    'SearchStrategy',
    'SearchDepth',
    'AthenaIterativeSearchAgent'
]
