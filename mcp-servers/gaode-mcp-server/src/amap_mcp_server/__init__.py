"""
高德地图MCP服务器
Gaode Maps MCP Server

为AI模型提供地理空间智能服务的MCP服务器
"""

__version__ = '1.0.0'
__author__ = 'Xiao Nuo'
__email__ = 'xujian519@gmail.com'
__description__ = '高德地图MCP服务器 - 为AI模型提供地理空间智能服务'

import logging

from .server import AmapMcpServer

__all__ = [
    'AmapMcpServer',
    '__version__',
    '__author__',
    '__description__'
]