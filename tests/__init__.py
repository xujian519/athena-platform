#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体设计模式测试框架
Agentic Design Patterns Test Framework

提供完整的测试基础设施，包括单元测试、集成测试和性能测试
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 测试配置
TEST_CONFIG = {
    'test_data_dir': project_root / 'tests' / 'data',
    'test_reports_dir': project_root / 'tests' / 'reports',
    'mock_services': True,
    'performance_baseline': True,
    'coverage_analysis': True
}

__version__ = "1.0.0"
__author__ = "Athena Platform Team"