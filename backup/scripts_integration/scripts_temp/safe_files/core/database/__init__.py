"""
数据库管理模块
提供统一的数据库访问接口
"""

from .db import DatabaseManager, db_manager

__all__ = ['DatabaseManager', 'db_manager']