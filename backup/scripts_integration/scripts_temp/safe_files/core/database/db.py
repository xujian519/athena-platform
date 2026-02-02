#!/usr/bin/env python3
"""
统一数据库管理器
提供数据库连接池、操作和事务管理
"""

import os
import psycopg2
import psycopg2.extras
from typing import Optional, Dict, Any, List, Union
from contextlib import contextmanager
import logging
import time
from datetime import datetime

from ..config import config


class DatabaseManager:
    """数据库管理器"""

    _instance = None
    _connection_pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger('DatabaseManager')
            self.config = config.get_database_config()
            self._initialize_pool()
            self._initialized = True

    def _initialize_pool(self):
        """初始化连接池"""
        try:
            # 这里简化实现，实际项目中可以使用连接池库如psycopg2.pool
            self.logger.info("数据库连接初始化完成")
        except Exception as e:
            self.logger.error(f"数据库连接初始化失败: {e}")

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            yield conn
        except Exception as e:
            self.logger.error(f"数据库连接错误: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_cursor(self, dict_cursor=False):
        """获取数据库游标"""
        with self.get_connection() as conn:
            cursor_factory = psycopg2.extras.RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()

    def execute_query(self, query: str, params: tuple = None,
                      fetch_one: bool = False,
                      dict_cursor: bool = False) -> Union[Dict, List[Dict | None]]:
        """执行查询"""
        with self.get_cursor(dict_cursor=dict_cursor) as cursor:
            try:
                cursor.execute(query, params or ())

                if fetch_one:
                    result = cursor.fetchone()
                    if result and dict_cursor:
                        result = dict(result)
                else:
                    results = cursor.fetchall()
                    if dict_cursor:
                        results = [dict(r) for r in results]
                    result = results

                return result
            except Exception as e:
                self.logger.error(f"查询执行失败: {query} - {e}")
                raise

    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新（INSERT, UPDATE, DELETE）"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params or ())
                affected_rows = cursor.rowcount
                conn.commit()
                return affected_rows
            except Exception as e:
                conn.rollback()
                self.logger.error(f"更新执行失败: {query} - {e}")
                raise
            finally:
                cursor.close()

    def execute_batch(self, query: str, params_list: List[tuple]) -> int:
        """批量执行"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(query, params_list)
                affected_rows = cursor.rowcount
                conn.commit()
                return affected_rows
            except Exception as e:
                conn.rollback()
                self.logger.error(f"批量执行失败: {query} - {e}")
                raise
            finally:
                cursor.close()

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise

    def close_all_connections(self):
        """关闭所有连接"""
        if self._connection_pool:
            self._connection_pool.closeall()
            self.logger.info("所有数据库连接已关闭")


# 创建全局实例
db_manager = DatabaseManager()