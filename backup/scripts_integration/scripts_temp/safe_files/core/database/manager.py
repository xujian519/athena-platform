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
        self.logger = logging.getLogger(__name__)
        self.db_config = config.get_database_config()
        self._initialize_connection_pool()

    def _initialize_connection_pool(self):
        """初始化连接池"""
        try:
            # 使用pgbouncer作为连接池
            pool_config = {
                'host': self.db_config.get('host', 'localhost'),
                'port': self.db_config.get('port', 5432),
                'database': self.db_config.get('database', 'athena'),
                'user': self.db_config.get('user', 'postgres'),
                'password': self.db_config.get('password'),
                'minconn': self.db_config.get('min_connections', 5),
                'maxconn': self.db_config.get('max_connections', 20)
            }

            self.connection_string = (
                f"postgresql://{pool_config['user']}:{pool_config['password']}"
                f"@{pool_config['host']}:{pool_config['port']}/{pool_config['database']}"
            )

            self.logger.info("数据库连接池初始化成功")
        except Exception as e:
            self.logger.error(f"数据库连接池初始化失败: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = None
        try:
            conn = psycopg2.connect(self.connection_string)
            yield conn
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_cursor(self, dictionary=False):
        """获取数据库游标"""
        with self.get_connection() as conn:
            if dictionary:
                yield conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            else:
                yield conn.cursor()

    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> List | None:
        """执行查询"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)

                if fetch:
                    if cursor.description:
                        columns = [desc[0] for desc in cursor.description]
                        results = cursor.fetchall()
                        return [dict(zip(columns, row)) for row in results]
                    else:
                        return []
                else:
                    return []
        except Exception as e:
            self.logger.error(f"查询执行失败: {query}, 错误: {e}")
            raise

    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新操作"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount
        except Exception as e:
            self.logger.error(f"更新执行失败: {query}, 错误: {e}")
            raise

    @contextmanager
    def transaction(self):
        """事务管理"""
        conn = None
        try:
            conn = psycopg2.connect(self.connection_string)
            conn.autocommit = False
            with conn.cursor() as cursor:
                yield conn, cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"事务执行失败: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def batch_insert(self, table: str, data: List[Dict], batch_size: int = 1000) -> int:
        """批量插入"""
        if not data:
            return 0

        total_inserted = 0
        columns = list(data[0].keys())

        # 构建插入SQL
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))

        with self.transaction() as (conn, cursor):
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                values = [tuple(item[col] for col in columns) for item in batch]

                query = f"""
                    INSERT INTO {table} ({columns_str})
                    VALUES ({placeholders})
                """

                cursor.executemany(query, values)
                total_inserted += len(batch)

        self.logger.info(f"批量插入完成: {table}, {total_inserted} 条记录")
        return total_inserted

    def check_connection(self) -> bool:
        """检查数据库连接"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            self.logger.error(f"数据库连接检查失败: {e}")
            return False

    def get_table_info(self, table: str) -> Dict:
        """获取表信息"""
        query = """
            SELECT
                table_name,
                table_type,
                table_rows
            FROM information_schema.tables
            WHERE table_name = %s
        """

        result = self.execute_query(query, (table,))
        return result[0] if result else {}

    @classmethod
    def instance(cls):
        """获取单例实例"""
        if DatabaseManager._instance is None:
            DatabaseManager._instance = DatabaseManager()
        return DatabaseManager._instance

    @classmethod
    def execute_sql_file(cls, file_path: str):
        """执行SQL文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        statements = sql_content.split(';')
        db = cls.instance()

        for statement in statements:
            statement = statement.strip()
            if statement:
                try:
                    db.execute_query(statement)
                except Exception as e:
                    print(f"执行SQL失败: {e}")


# 全局实例
db_manager = DatabaseManager.instance()