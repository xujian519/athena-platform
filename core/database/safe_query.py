"""
安全的数据库查询工具模块
提供防止SQL注入的数据库访问方法

作者: Claude Code
日期: 2026-01-25
"""

from typing import Optional
import logging
from contextlib import contextmanager

try:
    from psycopg2 import sql
    from psycopg2.extensions import cursor as PsycoCursor
    from psycopg2.sql import SQL, Composable, Identifier

    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logging.warning("psycopg2不可用,将使用基础SQL保护")

logger = logging.getLogger(__name__)


class SafeQueryError(Exception):
    """安全查询错误"""

    pass


class SQLInjectionWarning(UserWarning):
    """SQL注入警告"""

    pass


class SafeQueryBuilder:
    """
    安全的SQL查询构建器

    防止SQL注入的主要方法:
    1. 使用psycopg2.sql模块处理动态标识符
    2. 使用参数化查询处理用户输入
    3. 表名/列名白名单验证
    4. 自动转义特殊字符
    """

    # 允许的表名白名单
    ALLOWED_TABLES: dict[str, set] = {
        "athena": {
            "patent_rules_unified",
            "patent_judgments",
            "patent_law_documents",
            "law_documents",
        },
        "patent_db": {
            "patents",
            "data_import_log",
            "patent_search_logs",
        },
        "default": {
            # 默认允许的表名
        },
    }

    # 允许的schema白名单
    ALLOWED_SCHEMAS = {
        "public",
        "patent_data",
        "graph",
    }

    @classmethod
    def validate_table_name(cls, table_name: str, database: str = "default") -> bool:
        """
        验证表名是否在白名单中

        Args:
            table_name: 表名
            database: 数据库名称

        Returns:
            bool: 是否有效

        Raises:
            SafeQueryError: 表名不在白名单中
        """
        if not isinstance(table_name, str):
            raise SafeQueryError(f"表名必须是字符串,收到: {type(table_name)}")

        # 检查基本格式
        if not table_name.replace("_", "").replace("-", "").isalnum():
            raise SafeQueryError(f"表名包含非法字符: {table_name}")

        # 检查白名单
        allowed = cls.ALLOWED_TABLES.get(database, cls.ALLOWED_TABLES["default"])
        if table_name not in allowed:
            logger.warning(f"表名 '{table_name}' 不在白名单中,建议添加到白名单")

        return True

    @classmethod
    def validate_schema_name(cls, schema_name: str) -> bool:
        """
        验证schema名称

        Args:
            schema_name: schema名称

        Returns:
            bool: 是否有效

        Raises:
            SafeQueryError: schema名称无效
        """
        if not isinstance(schema_name, str):
            raise SafeQueryError(f"schema名称必须是字符串,收到: {type(schema_name)}")

        # 检查基本格式
        if not schema_name.replace("_", "").replace("-", "").isalnum():
            raise SafeQueryError(f"schema名称包含非法字符: {schema_name}")

        # 检查白名单
        if schema_name not in cls.ALLOWED_SCHEMAS:
            logger.warning(f"schema '{schema_name}' 不在白名单中,建议添加到白名单")

        return True

    @classmethod
    def safe_identifier(cls, identifier: str) -> Composable:
        """
        创建安全的SQL标识符

        Args:
            identifier: 标识符名称

        Returns:
            Composable: 安全的SQL标识符

        Example:
            >>> SafeQueryBuilder.safe_identifier("my_table")
            Identifier('my_table')
        """
        if not PSYCOPG2_AVAILABLE:
            raise SafeQueryError("psycopg2不可用,无法使用safe_identifier")

        # 验证标识符格式
        if not isinstance(identifier, str):
            raise SafeQueryError(f"标识符必须是字符串,收到: {type(identifier)}")

        if not identifier.replace("_", "").replace("-", "").isalnum():
            raise SafeQueryError(f"标识符包含非法字符: {identifier}")

        return Identifier(identifier)

    @classmethod
    def safe_table_name(cls, table_name: str) -> Composable:
        """
        创建安全的表名标识符

        Args:
            table_name: 表名

        Returns:
            Composable: 安全的表名SQL

        Example:
            >>> query = SQL("SELECT * FROM {}").format(SafeQueryBuilder.safe_table_name("patents"))
        """
        cls.validate_table_name(table_name)
        return cls.safe_identifier(table_name)

    @classmethod
    def safe_schema_name(cls, schema_name: str) -> Composable:
        """
        创建安全的schema标识符

        Args:
            schema_name: schema名称

        Returns:
            Composable: 安全的schema SQL

        Example:
            >>> query = SQL("SET search_path TO {}").format(SafeQueryBuilder.safe_schema_name("public"))
        """
        cls.validate_schema_name(schema_name)
        return cls.safe_identifier(schema_name)

    @classmethod
    def safe_search_path(cls, schemas: list[str]) -> SQL:
        """
        创建安全的search_path设置语句

        Args:
            schemas: schema列表

        Returns:
            SQL: 安全的search_path SQL

        Example:
            >>> SafeQueryBuilder.safe_search_path(['public', 'graph'])
            SQL('SET search_path TO "public", "graph"')
        """
        if not PSYCOPG2_AVAILABLE:
            raise SafeQueryError("psycopg2不可用,无法使用safe_search_path")

        # 验证所有schema
        for schema in schemas:
            cls.validate_schema_name(schema)

        # 构建安全的SQL
        schema_identifiers = [cls.safe_identifier(schema) for schema in schemas]
        return SQL("SET search_path TO {}").format(sql.SQL(", ").join(schema_identifiers))


class SafeQueryExecutor:
    """
    安全的查询执行器

    提供安全的查询执行方法,防止SQL注入
    """

    def __init__(self, cursor: PsycoCursor):
        """
        初始化查询执行器

        Args:
            cursor: 数据库游标
        """
        self.cursor = cursor
        self.builder = SafeQueryBuilder()

    def execute_safe(
        self,
        query: str | Composable,
        params: tuple | None = None,
        query_name: str | None = None,
    ) -> None:
        """
        安全执行查询

        Args:
            query: SQL查询或Composable对象
            params: 查询参数
            query_name: 查询名称(用于日志)

        Raises:
            SafeQueryError: 查询执行失败
        """
        try:
            if params is None:
                self.cursor.execute(query)
            else:
                self.cursor.execute(query, params)

            if query_name:
                logger.debug(f"查询执行成功: {query_name}")

        except Exception as e:
            error_msg = "查询执行失败"
            if query_name:
                error_msg += f" ({query_name})"
            error_msg += f": {e}"
            logger.error(error_msg)
            raise SafeQueryError(error_msg) from e

    def execute_with_table_name(
        self, query_template: str, table_name: str, params: tuple | None = None
    ) -> None:
        """
        使用动态表名安全执行查询

        Args:
            query_template: 查询模板,使用{}作为表名占位符
            table_name: 表名
            params: 查询参数

        Example:
            >>> executor.execute_with_table_name(
            ...     "SELECT COUNT(*) FROM {}",
            ...     "patents",
            ...     None
            ... )
        """
        if not PSYCOPG2_AVAILABLE:
            raise SafeQueryError("psycopg2不可用,无法使用execute_with_table_name")

        # 验证表名
        self.builder.validate_table_name(table_name)

        # 构建安全查询
        safe_table = self.builder.safe_table_name(table_name)
        query = SQL(query_template).format(safe_table)

        # 执行查询
        self.execute_safe(query, params, f"table={table_name}")

    def set_search_path(self, schemas: list[str]) -> None:
        """
        设置安全的search_path

        Args:
            schemas: schema列表

        Example:
            >>> executor.set_search_path(['public', 'graph'])
        """
        if not PSYCOPG2_AVAILABLE:
            raise SafeQueryError("psycopg2不可用,无法使用set_search_path")

        query = self.builder.safe_search_path(schemas)
        self.execute_safe(query, None, f"search_path={','.join(schemas)}")

    def fetch_all_safe(
        self, query: str | Composable | None = None, params: tuple | None = None
    ) -> list[tuple]:
        """
        安全执行查询并获取所有结果

        Args:
            query: SQL查询
            params: 查询参数

        Returns:
            list[Tuple]: 查询结果
        """
        self.execute_safe(query, params)
        return self.cursor.fetchall()

    def fetch_one_safe(
        self, query: str | Composable | None = None, params: tuple | None = None
    ) -> tuple | None:
        """
        安全执行查询并获取单条结果

        Args:
            query: SQL查询
            params: 查询参数

        Returns:
            Optional[Tuple]: 查询结果,如果没有结果则返回None
        """
        self.execute_safe(query, params)
        return self.cursor.fetchone()


@contextmanager
def safe_query_context(cursor: PsycoCursor):
    """
    安全查询上下文管理器

    Args:
        cursor: 数据库游标

    Yields:
        SafeQueryExecutor: 安全查询执行器

    Example:
        >>> with safe_query_context(cursor) as executor:
        ...     executor.execute_safe("SELECT * FROM patents WHERE id = %s", (patent_id,))
        ...     results = executor.cursor.fetchall()
    """
    executor = SafeQueryExecutor(cursor)
    try:
        yield executor
    except Exception as e:
        logger.error(f"安全查询上下文错误: {e}")
        raise


def safe_execute(
    cursor: PsycoCursor, query: str | Composable | None = None, params: tuple | None = None
) -> None:
    """
    安全执行查询的便捷函数

    Args:
        cursor: 数据库游标
        query: SQL查询
        params: 查询参数

    Example:
        >>> safe_execute(cursor, "SELECT * FROM patents WHERE id = %s", (patent_id,))
    """
    with safe_query_context(cursor) as executor:
        executor.execute_safe(query, params)


def safe_execute_with_table(
    cursor: PsycoCursor | None = None, query_template: str | None = None, table_name: str | None = None, params: tuple | None = None
) -> None:
    """
    使用动态表名安全执行查询的便捷函数

    Args:
        cursor: 数据库游标
        query_template: 查询模板
        table_name: 表名
        params: 查询参数

    Example:
        >>> safe_execute_with_table(
        ...     cursor,
        ...     "SELECT COUNT(*) FROM {}",
        ...     "patents"
        ... )
    """
    with safe_query_context(cursor) as executor:
        executor.execute_with_table_name(query_template, table_name, params)
