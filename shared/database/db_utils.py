"""
标准化的数据库操作工具
提供安全的SQL执行方法
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor, DictCursor
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    @contextmanager
    def get_cursor(self, dictionary: bool = False) -> Any | None:
        """获取数据库游标上下文管理器"""
        conn = None
        cursor = None
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor_type = RealDictCursor if dictionary else DictCursor
            cursor = conn.cursor(cursor_factory=cursor_type)
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def execute_query(
        self,
        query: str,
        params: Tuple | None = None,
        fetch_one: bool = False,
        fetch_all: bool = True,
        dictionary: bool = False
    ) -> Union[Dict, List[Dict], None]:
        """执行查询语句"""
        with self.get_cursor(dictionary=dictionary) as cursor:
            cursor.execute(query, params)

            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            return None

    def execute_update(
        self,
        query: str,
        params: Tuple | None = None
    ) -> int:
        """执行更新语句"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def execute_insert(
        self,
        query: str,
        params: Tuple | None = None,
        returning: str | None = None
    ) -> Any | None:
        """执行插入语句"""
        with self.get_cursor() as cursor:
            if returning:
                query += f" RETURNING {returning}"
            cursor.execute(query, params)
            if returning:
                result = cursor.fetchone()
                return result[0] if result else None
            return cursor.rowcount

    def execute_batch(
        self,
        query: str,
        params_list: List[Tuple]
    ) -> int:
        """批量执行语句"""
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount


def build_safe_query(table: str, columns: Optional[List[str] = None,
                     where_conditions: Dict[str, Any] = None,
                     order_by: str = None, limit: int = None) -> Tuple[str, Tuple]:
    """构建安全的SQL查询"""
    # 使用psycopg2.sql模块防止SQL注入
    query_parts = []
    params = []

    # SELECT部分
    if columns:
        query_parts.append(
            sql.SQL("SELECT {}").format(
                sql.SQL(', ').join(map(sql.Identifier, columns))
            )
        )
    else:
        query_parts.append(sql.SQL("SELECT *"))

    # FROM部分
    query_parts.append(sql.SQL("FROM {}").format(sql.Identifier(table)))

    # WHERE部分
    if where_conditions:
        where_clauses = []
        for column, value in where_conditions.items():
            where_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(column)))
            params.append(value)
        query_parts.append(sql.SQL("WHERE {}").format(
            sql.SQL(" AND ").join(where_clauses)
        ))

    # ORDER BY部分
    if order_by:
        query_parts.append(sql.SQL("ORDER BY {}").format(sql.SQL(order_by)))

    # LIMIT部分
    if limit:
        query_parts.append(sql.SQL("LIMIT %s"))
        params.append(limit)

    # 组合查询
    final_query = sql.SQL(" ").join(query_parts)

    # 返回查询字符串和参数
    return final_query.as_string(None), tuple(params)


# 使用示例
if __name__ == "__main__":
    # 初始化数据库管理器
    db = DatabaseManager("postgresql://user:password@localhost/db")

    # 安全查询示例
    query, params = build_safe_query(
        table="users",
        columns=["id", "name", "email"],
        where_conditions={"active": True},
        order_by="created_at DESC",
        limit=10
    )

    results = db.execute_query(query, params)
    print(results)
