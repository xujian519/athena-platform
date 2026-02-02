#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL注入防护工具类
SQL Injection Prevention Utilities

提供安全的数据库查询方法和验证工具
"""

import re
import logging
from typing import Any, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class SQLInjectionPrevention:
    """SQL注入防护工具类"""

    # 允许的表名模式（仅限字母、数字、下划线）
    TABLE_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

    # 允许的列名模式
    COLUMN_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

    # SQL注入关键字检测
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT',
        'UPDATE', 'EXEC', 'EXECUTE', 'SCRIPT', 'JAVASCRIPT',
        '--', ';--', '/*', '*/', 'xp_', 'sp_', 'DECLARE'
    ]

    @classmethod
    def validate_table_name(cls, table_name: str) -> bool:
        """
        验证表名是否安全

        Args:
            table_name: 表名

        Returns:
            bool: 表名是否安全

        Raises:
            ValueError: 表名不安全时抛出异常
        """
        if not table_name:
            raise ValueError("表名不能为空")

        if not cls.TABLE_NAME_PATTERN.match(table_name):
            raise ValueError(f"无效的表名: {table_name}")

        # 检查是否包含危险关键字
        upper_table = table_name.upper()
        for keyword in cls.DANGEROUS_KEYWORDS:
            if keyword in upper_table:
                raise ValueError(f"表名包含危险关键字: {keyword}")

        return True

    @classmethod
    def validate_column_name(cls, column_name: str) -> bool:
        """
        验证列名是否安全

        Args:
            column_name: 列名

        Returns:
            bool: 列名是否安全

        Raises:
            ValueError: 列名不安全时抛出异常
        """
        if not column_name:
            raise ValueError("列名不能为空")

        if not cls.COLUMN_NAME_PATTERN.match(column_name):
            raise ValueError(f"无效的列名: {column_name}")

        return True

    @classmethod
    def validate_identifier_list(cls, identifiers: List[str], identifier_type: str = "identifier") -> bool:
        """
        验证标识符列表（表名或列名）

        Args:
            identifiers: 标识符列表
            identifier_type: 标识符类型（用于错误消息）

        Returns:
            bool: 所有标识符是否都安全

        Raises:
            ValueError: 包含不安全标识符时抛出异常
        """
        for identifier in identifiers:
            if identifier_type == "table":
                cls.validate_table_name(identifier)
            else:
                cls.validate_column_name(identifier)

        return True

    @classmethod
    def sanitize_sql_string(cls, value: str) -> str:
        """
        清理SQL字符串值（虽然优先使用参数化查询，但有时需要拼接）

        Args:
            value: 原始字符串值

        Returns:
            str: 清理后的字符串
        """
        if not isinstance(value, str):
            return str(value)

        # 转义单引号
        value = value.replace("'", "''")

        # 移除危险字符
        dangerous_chars = ['\x00', '\n', '\r', '\\', '\x1a']
        for char in dangerous_chars:
            value = value.replace(char, '')

        return value

    @classmethod
    def build_safe_table_query(
        cls,
        operation: str,
        table_name: str,
        where_clause: str | None = None,
        limit: int | None = None,
        offset: int | None = None
    ) -> Tuple[str, List[Any]]:
        """
        构建安全的表查询（使用已验证的表名）

        Args:
            operation: SQL操作类型（SELECT, COUNT等）
            table_name: 已验证的表名
            where_clause: WHERE子句（可选，应使用参数化）
            limit: 限制数量
            offset: 偏移量

        Returns:
            Tuple[str, List[Any]]: (SQL查询, 参数列表)
        """
        # 验证表名
        cls.validate_table_name(table_name)

        # 构建基础查询
        if operation.upper() == "COUNT":
            query = f"SELECT COUNT(*) FROM {table_name}"
        elif operation.upper() == "SELECT":
            query = f"SELECT * FROM {table_name}"
        else:
            raise ValueError(f"不支持的操作类型: {operation}")

        params = []

        # 添加WHERE子句（应该使用参数化）
        if where_clause:
            query += f" WHERE {where_clause}"

        # 添加LIMIT和OFFSET
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)

        return query, params

    @classmethod
    def check_sql_injection_attempts(cls, input_string: str) -> bool:
        """
        检查字符串中是否包含SQL注入尝试

        Args:
            input_string: 输入字符串

        Returns:
            bool: True表示检测到注入尝试
        """
        if not isinstance(input_string, str):
            return False

        upper_input = input_string.upper()

        # 检查常见的SQL注入模式
        injection_patterns = [
            r"'.*--",          # 注释攻击
            r"'.*;.*",         # 多语句攻击
            r"\bor\s+1\s*=\s*1",  # Boolean-based注入
            r"union.*select",  # UNION注入
            r"exec\s*\(",      # 执行命令
            r"waitfor\s+delay", # 时间延迟注入
            r"cast\s*\(",      # CAST注入
            r"convert\s*\(",   # CONVERT注入
        ]

        for pattern in injection_patterns:
            if re.search(pattern, upper_input, re.IGNORECASE):
                logger.warning(f"检测到SQL注入尝试: {pattern} in {input_string[:100]}")
                return True

        return False

    @classmethod
    def escape_like_wildcards(cls, value: str) -> str:
        """
        转义LIKE查询中的通配符

        Args:
            value: 原始值

        Returns:
            str: 转义后的值
        """
        if not isinstance(value, str):
            return str(value)

        # 转义LIKE通配符
        value = value.replace('\\', '\\\\')
        value = value.replace('%', '\\%')
        value = value.replace('_', '\\_')

        return value


class SafeQueryBuilder:
    """安全的SQL查询构建器"""

    def __init__(self, table_name: str):
        """
        初始化查询构建器

        Args:
            table_name: 表名（会自动验证）
        """
        SQLInjectionPrevention.validate_table_name(table_name)
        self.table_name = table_name
        self.select_columns = ["*"]
        self.where_conditions = []
        self.where_params = []
        self.order_by_column = None
        self.limit_value = None
        self.offset_value = None

    def select(self, columns: Union[str, List[str]]) -> 'SafeQueryBuilder':
        """
        设置SELECT列

        Args:
            columns: 列名或列名列表

        Returns:
            SafeQueryBuilder: 自身，支持链式调用
        """
        if isinstance(columns, str):
            columns = [columns]

        # 验证所有列名
        SQLInjectionPrevention.validate_identifier_list(columns, "column")
        self.select_columns = columns
        return self

    def where(self, condition: str, *params: Any) -> 'SafeQueryBuilder':
        """
        添加WHERE条件（参数化）

        Args:
            condition: WHERE条件（使用?作为占位符）
            *params: 参数值

        Returns:
            SafeQueryBuilder: 自身，支持链式调用
        """
        self.where_conditions.append(condition)
        self.where_params.extend(params)
        return self

    def order_by(self, column: str, ascending: bool = True) -> 'SafeQueryBuilder':
        """
        添加排序

        Args:
            column: 列名（会验证）
            ascending: 是否升序

        Returns:
            SafeQueryBuilder: 自身，支持链式调用
        """
        SQLInjectionPrevention.validate_column_name(column)
        direction = "ASC" if ascending else "DESC"
        self.order_by_column = f"{column} {direction}"
        return self

    def limit(self, value: int) -> 'SafeQueryBuilder':
        """
        设置LIMIT

        Args:
            value: 限制数量

        Returns:
            SafeQueryBuilder: 自身，支持链式调用
        """
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"无效的LIMIT值: {value}")
        self.limit_value = value
        return self

    def offset(self, value: int) -> 'SafeQueryBuilder':
        """
        设置OFFSET

        Args:
            value: 偏移量

        Returns:
            SafeQueryBuilder: 自身，支持链式调用
        """
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"无效的OFFSET值: {value}")
        self.offset_value = value
        return self

    def build(self) -> Tuple[str, List[Any]]:
        """
        构建最终的SQL查询

        Returns:
            Tuple[str, List[Any]]: (SQL查询, 参数列表)
        """
        # 构建SELECT部分
        columns_str = ", ".join(self.select_columns)
        query = f"SELECT {columns_str} FROM {self.table_name}"

        # 构建WHERE部分
        if self.where_conditions:
            query += " WHERE " + " AND ".join(self.where_conditions)

        # 构建ORDER BY部分
        if self.order_by_column:
            query += f" ORDER BY {self.order_by_column}"

        # 构建LIMIT和OFFSET
        params = self.where_params.copy()
        if self.limit_value is not None:
            query += " LIMIT ?"
            params.append(self.limit_value)

        if self.offset_value is not None:
            query += " OFFSET ?"
            params.append(self.offset_value)

        return query, params


def safe_execute(
    cursor,
    query_template: str,
    params: Optional[List[Any]] | None = None,
    operation: str = "SELECT"
) -> Any:
    """
    安全执行SQL查询（包装器）

    Args:
        cursor: 数据库游标对象
        query_template: 查询模板（使用?作为占位符）
        params: 参数列表
        operation: 操作类型（用于日志记录）

    Returns:
        Any: 查询结果

    Raises:
        ValueError: 检测到安全问题时抛出异常
    """
    # 检查SQL注入尝试
    if params:
        for param in params:
            if isinstance(param, str) and SQLInjectionPrevention.check_sql_injection_attempts(param):
                raise ValueError(f"检测到SQL注入尝试: {param}")

    # 执行查询
    try:
        if params:
            cursor.execute(query_template, params)
        else:
            cursor.execute(query_template)

        logger.debug(f"成功执行 {operation} 查询")
        return cursor

    except Exception as e:
        logger.error(f"SQL执行失败: {e}")
        raise


# 导出
__all__ = [
    'SQLInjectionPrevention',
    'SafeQueryBuilder',
    'safe_execute'
]
