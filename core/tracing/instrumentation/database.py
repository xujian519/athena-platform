"""
数据库自动埋点模块

提供数据库操作的自动追踪装饰器和工具。
支持PostgreSQL, Redis, Neo4j等多种数据库。
"""

from functools import wraps
from typing import Callable, Optional, Any
from contextlib import contextmanager
from opentelemetry import trace, Status, StatusCode

from ..tracer import AthenaTracer
from ..attributes import DatabaseAttributes


class DatabaseTracer:
    """
    数据库调用追踪器（增强版）

    提供完整的数据库操作追踪，包括：
    - 操作类型追踪
    - 影响行数记录
    - 查询性能统计
    - 异常捕获

    Example:
        >>> tracer = DatabaseTracer("postgresql", "athena_db")
        >>> with tracer.trace_query("SELECT", "patents"):
        ...     results = await db.fetch("SELECT * FROM patents")
        ...     tracer.add_result_info(len(results))
    """

    def __init__(self, db_system: str = "postgresql", db_name: str = "default"):
        """
        初始化数据库追踪器

        Args:
            db_system: 数据库系统（postgresql, redis, neo4j等）
            db_name: 数据库名称
        """
        self.db_system = db_system
        self.db_name = db_name
        self._tracer = trace.get_tracer(f"db.{db_system}")
        self._current_span: Optional[trace.Span] = None

    @contextmanager
    def trace_query(
        self,
        operation: str,
        table: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs
    ):
        """
        数据库查询追踪上下文管理器

        Args:
            operation: 操作类型（SELECT, INSERT, UPDATE, DELETE）
            table: 表名
            query: 查询语句（可选）
            **kwargs: 额外属性

        Yields:
            DatabaseSpanContext对象

        Example:
            >>> with tracer.trace_query("SELECT", "patents") as ctx:
            ...     results = await db.fetch("SELECT * FROM patents")
            ...     ctx.add_result_info(rows_affected=len(results))
        """
        attributes = {
            "db.system": self.db_system,
            "db.name": self.db_name,
            "db.operation": operation,
            **kwargs
        }

        if table:
            attributes["db.table"] = table
        if query:
            attributes["db.statement"] = query

        with self._tracer.start_as_current_span(
            name=f"{operation.lower()}.{table or 'query'}",
            kind=trace.SpanKind.CLIENT,
            attributes=attributes
        ) as span:
            self._current_span = span
            ctx = DatabaseSpanContext(span)
            try:
                yield ctx
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                ctx.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
            finally:
                self._current_span = None


class DatabaseSpanContext:
    """
    数据库Span上下文管理器

    提供便捷的方法来添加数据库操作相关属性。
    """

    def __init__(self, span: trace.Span):
        """
        初始化Span上下文

        Args:
            span: OpenTelemetry Span对象
        """
        self.span = span

    def add_result_info(
        self,
        rows_affected: int = 0,
        rows_returned: int = 0,
        execution_time_ms: float = 0.0
    ):
        """
        添加结果信息

        Args:
            rows_affected: 影响行数
            rows_returned: 返回行数
            execution_time_ms: 执行时间
        """
        if rows_affected > 0:
            self.span.set_attribute("db.rows_affected", rows_affected)
        if rows_returned > 0:
            self.span.set_attribute("db.rows_returned", rows_returned)
        if execution_time_ms > 0:
            self.span.set_attribute("db.execution_time_ms", execution_time_ms)

    def record_error(self, error: Exception):
        """
        记录错误到Span

        Args:
            error: 异常对象
        """
        self.span.record_exception(error)
        self.span.set_attribute("db.error.type", type(error).__name__)
        self.span.set_attribute("db.error.message", str(error))

    def add_connection_info(
        self,
        connection_id: Optional[str] = None,
        pool_name: Optional[str] = None
    ):
        """
        添加连接信息

        Args:
            connection_id: 连接ID
            pool_name: 连接池名称
        """
        if connection_id:
            self.span.set_attribute("db.connection_id", connection_id)
        if pool_name:
            self.span.set_attribute("db.pool_name", pool_name)


def trace_database_query(
    db_system: str = "postgresql",
    operation: Optional[str] = None,
    table_arg: Optional[str] = None
):
    """
    数据库查询装饰器（增强版）

    自动为数据库操作方法添加追踪。

    Args:
        db_system: 数据库系统
        operation: 操作类型（默认从方法名推断）
        table_arg: 包含表名的参数名

    Example:
        >>> @trace_database_query(db_system="postgresql", operation="SELECT")
        ... async def get_patent(self, patent_id: str):
        ...     return await self.db.fetch_one(...)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # 推断操作类型
            actual_operation = operation
            if actual_operation is None:
                func_name = func.__name__.upper()
                for op in ["SELECT", "INSERT", "UPDATE", "DELETE"]:
                    if op in func_name:
                        actual_operation = op
                        break
                if actual_operation is None:
                    actual_operation = "QUERY"

            # 尝试获取表名
            table = None
            if table_arg and table_arg in kwargs:
                table = kwargs[table_arg]

            # 获取或创建追踪器
            tracer = getattr(self, '_tracer', None) or getattr(self, 'tracer', None)
            if tracer is None:
                tracer = DatabaseTracer(db_system)

            with tracer.trace_query(actual_operation, table):
                return await func(self, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            actual_operation = operation
            if actual_operation is None:
                func_name = func.__name__.upper()
                for op in ["SELECT", "INSERT", "UPDATE", "DELETE"]:
                    if op in func_name:
                        actual_operation = op
                        break
                if actual_operation is None:
                    actual_operation = "QUERY"

            table = None
            if table_arg and table_arg in kwargs:
                table = kwargs[table_arg]

            tracer = getattr(self, '_tracer', None) or getattr(self, 'tracer', None)
            if tracer is None:
                tracer = DatabaseTracer(db_system)

            with tracer.trace_query(actual_operation, table):
                return func(self, *args, **kwargs)

        # 检测是否为协程函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@contextmanager
def trace_database_operation(
    tracer: AthenaTracer,
    db_system: str,
    operation: str,
    table: Optional[str] = None,
    **kwargs
):
    """
    数据库操作追踪上下文管理器

    Args:
        tracer: 追踪器实例
        db_system: 数据库系统（postgresql, redis, neo4j）
        operation: 操作类型（SELECT, INSERT, UPDATE, DELETE）
        table: 表名
        **kwargs: 额外属性

    Yields:
        Span对象

    Example:
        >>> with trace_database_operation(tracer, "postgresql", "SELECT", "patents"):
        ...     results = await db.fetch("SELECT * FROM patents")
    """
    with tracer.start_database_span(
        db_system=db_system,
        operation=operation,
        table=table,
        **kwargs
    ) as span:
        yield span


def trace_db_method(
    db_system: str = "postgresql",
    operation: Optional[str] = None,
    table_arg: Optional[str] = None
):
    """
    数据库方法装饰器

    自动为数据库操作方法添加追踪。

    Args:
        db_system: 数据库系统
        operation: 操作类型（默认从方法名推断）
        table_arg: 包含表名的参数名

    Example:
        >>> @trace_db_method(db_system="postgresql", operation="SELECT")
        ... async def get_patent(self, patent_id: str):
        ...     return await self.db.fetch_one(...)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            tracer = getattr(self, '_tracer', None) or getattr(self, 'tracer', None)
            if tracer is None:
                return await func(self, *args, **kwargs)

            # 推断操作类型
            actual_operation = operation
            if actual_operation is None:
                func_name = func.__name__.upper()
                for op in ["SELECT", "INSERT", "UPDATE", "DELETE"]:
                    if op in func_name:
                        actual_operation = op
                        break
                if actual_operation is None:
                    actual_operation = "QUERY"

            # 尝试获取表名
            table = None
            if table_arg and table_arg in kwargs:
                table = kwargs[table_arg]

            with trace_database_operation(
                tracer=tracer,
                db_system=db_system,
                operation=actual_operation,
                table=table
            ):
                return await func(self, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            tracer = getattr(self, '_tracer', None) or getattr(self, 'tracer', None)
            if tracer is None:
                return func(self, *args, **kwargs)

            actual_operation = operation
            if actual_operation is None:
                func_name = func.__name__.upper()
                for op in ["SELECT", "INSERT", "UPDATE", "DELETE"]:
                    if op in func_name:
                        actual_operation = op
                        break
                if actual_operation is None:
                    actual_operation = "QUERY"

            table = None
            if table_arg and table_arg in kwargs:
                table = kwargs[table_arg]

            with trace_database_operation(
                tracer=tracer,
                db_system=db_system,
                operation=actual_operation,
                table=table
            ):
                return func(self, *args, **kwargs)

        # 检测是否为协程函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class DatabaseTracerMixin:
    """
    数据库追踪混入类

    为数据库客户端类提供追踪功能。

    Example:
        >>> class MyDatabase(DatabaseTracerMixin):
        ...     def __init__(self, db_type: str):
        ...         super().__init__()
        ...         self.setup_db_tracer(db_type)
    """

    _db_tracer: Optional[AthenaTracer] = None
    _db_system: str = "postgresql"

    def setup_db_tracer(
        self,
        db_system: str,
        tracer: Optional[AthenaTracer] = None
    ) -> None:
        """
        设置数据库追踪器

        Args:
            db_system: 数据库系统
            tracer: 自定义追踪器
        """
        self._db_system = db_system
        self._db_tracer = tracer or AthenaTracer(f"db.{db_system}")

    @contextmanager
    def trace_db_operation(
        self,
        operation: str,
        table: Optional[str] = None
    ):
        """
        数据库操作追踪上下文管理器

        Args:
            operation: 操作类型
            table: 表名

        Yields:
            Span对象
        """
        if self._db_tracer:
            with trace_database_operation(
                self._db_tracer,
                self._db_system,
                operation,
                table
            ) as span:
                yield span
        else:
            from contextlib import nullcontext
            yield nullcontext()


# 数据库系统常量
class DatabaseSystem:
    """数据库系统常量"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    REDIS = "redis"
    MONGODB = "mongodb"
    NEO4J = "neo4j"
    ARANGODB = "arangodb"


# 操作类型常量
class DatabaseOperation:
    """数据库操作类型常量"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    ALTER = "ALTER"
    BEGIN = "BEGIN"
    COMMIT = "COMMIT"
    ROLLBACK = "ROLLBACK"
