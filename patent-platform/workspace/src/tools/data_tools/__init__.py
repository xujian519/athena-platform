#!/usr/bin/env python3
"""
数据处理工具模块
Data Processing Tools Module

提供数据处理、分析、清洗等功能
Provides data processing, analysis, cleaning and other functions

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

# 导入核心数据处理工具
try:
    import numpy as np
    import pandas as pd
    PANDAS_AVAILABLE = True
    NUMPY_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    NUMPY_AVAILABLE = False

try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import csv
    import json
    import re
    STANDARD_LIB_AVAILABLE = True
except ImportError:
    STANDARD_LIB_AVAILABLE = False

__all__ = [
    'DataProcessor',
    'DataAnalyzer',
    'DataCleaner'
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'Athena AI系统'

class DataProcessor:
    """数据处理器"""

    def __init__(self):
        self.pandas_available = PANDAS_AVAILABLE
        self.numpy_available = NUMPY_AVAILABLE
        self.sklearn_available = SKLEARN_AVAILABLE

    def load_data(self, file_path, file_type='auto'):
        """加载数据文件"""
        if not PANDAS_AVAILABLE:
            raise ImportError('Pandas not available for data processing')

        try:
            if file_type == 'auto':
                if file_path.endswith('.csv'):
                    return pd.read_csv(file_path)
                elif file_path.endswith('.xlsx'):
                    return pd.read_excel(file_path)
                elif file_path.endswith('.json'):
                    return pd.read_json(file_path)
                else:
                    raise ValueError(f"Unsupported file format: {file_path}")
            else:
                if file_type == 'csv':
                    return pd.read_csv(file_path)
                elif file_type == 'excel':
                    return pd.read_excel(file_path)
                elif file_type == 'json':
                    return pd.read_json(file_path)
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}") from e

    def basic_stats(self, data):
        """基本统计信息"""
        if not PANDAS_AVAILABLE:
            raise ImportError('Pandas not available')

        if isinstance(data, pd.DataFrame):
            return data.describe()
        else:
            return {'error': 'Data must be a pandas DataFrame'}

class DataAnalyzer:
    """数据分析器"""

    def __init__(self):
        self.pandas_available = PANDAS_AVAILABLE
        self.numpy_available = NUMPY_AVAILABLE

    def correlation_analysis(self, data):
        """相关性分析"""
        if not PANDAS_AVAILABLE:
            raise ImportError('Pandas not available')

        if isinstance(data, pd.DataFrame):
            return data.corr()
        else:
            return {'error': 'Data must be a pandas DataFrame'}

    def group_analysis(self, data, group_by, agg_func='mean'):
        """分组分析"""
        if not PANDAS_AVAILABLE:
            raise ImportError('Pandas not available')

        if isinstance(data, pd.DataFrame):
            return data.groupby(group_by).agg(agg_func)
        else:
            return {'error': 'Data must be a pandas DataFrame'}

class DataCleaner:
    """数据清洗器"""

    def __init__(self):
        self.pandas_available = PANDAS_AVAILABLE

    def remove_duplicates(self, data):
        """移除重复数据"""
        if not PANDAS_AVAILABLE:
            raise ImportError('Pandas not available')

        if isinstance(data, pd.DataFrame):
            return data.drop_duplicates()
        else:
            return {'error': 'Data must be a pandas DataFrame'}

    def handle_missing_values(self, data, method='drop'):
        """处理缺失值"""
        if not PANDAS_AVAILABLE:
            raise ImportError('Pandas not available')

        if isinstance(data, pd.DataFrame):
            if method == 'drop':
                return data.dropna()
            elif method == 'fill':
                return data.fillna(data.mean())
            else:
                return data.fillna(method)
        else:
            return {'error': 'Data must be a pandas DataFrame'}

# 工具可用性状态
TOOL_STATUS = {
    'data_processor': PANDAS_AVAILABLE and NUMPY_AVAILABLE,
    'data_analyzer': PANDAS_AVAILABLE and NUMPY_AVAILABLE,
    'data_cleaner': PANDAS_AVAILABLE,
    'sklearn_features': SKLEARN_AVAILABLE,
    'standard_lib': STANDARD_LIB_AVAILABLE
}

def get_available_tools():
    """获取可用的工具列表"""
    return [tool for tool, available in TOOL_STATUS.items() if available]

def get_tool_status():
    """获取工具状态信息"""
    return TOOL_STATUS.copy()

def check_dependencies():
    """检查依赖库状态"""
    deps = {
        'pandas': PANDAS_AVAILABLE,
        'numpy': NUMPY_AVAILABLE,
        'sklearn': SKLEARN_AVAILABLE,
        'standard_lib': STANDARD_LIB_AVAILABLE
    }
    return deps

if __name__ == '__main__':
    logger.info('🔧 数据处理工具模块状态')
    logger.info(f"版本: {__version__}")
    logger.info(f"作者: {__author__}")
    logger.info(f"\n可用工具: {get_available_tools()}")
    logger.info(f"依赖检查: {check_dependencies()}")

    # 简单功能测试
    try:
        processor = DataProcessor()
        logger.info("✅ DataProcessor 初始化成功")
    except Exception as e:
        logger.info(f"❌ DataProcessor 初始化失败: {e}")
