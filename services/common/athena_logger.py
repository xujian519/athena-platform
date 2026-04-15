"""
Athena统一日志客户端
Athena Unified Logger Client
提供统一的日志记录接口
"""

import asyncio
import logging
import traceback
from datetime import datetime, timezone
from functools import wraps
from typing import Any

import httpx

# 日志级别映射
LOG_LEVEL_MAP = {
    logging.DEBUG: "DEBUG",
    logging.INFO: "INFO",
    logging.WARNING: "WARNING",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "CRITICAL"
}

class AthenaLogger:
    """Athena统一日志记录器"""

    def __init__(self, service_name: str, service_host: str = "http://localhost:8010"):
        self.service_name = service_name
        self.service_host = service_host
        self.client: httpx.AsyncClient | None = None
        self._buffer = []
        self.buffer_size = 100
        self.flush_interval = 10  # 秒
        self._last_flush = datetime.now()
        self._task: asyncio.Task | None = None

    async def initialize(self):
        """初始化日志客户端"""
        self.client = httpx.AsyncClient(timeout=10.0)
        # 启动后台刷新任务
        self._task = asyncio.create_task(self._auto_flush())

    async def close(self):
        """关闭日志客户端"""
        if self._task:
            self._task.cancel()
        await self.flush()
        if self.client:
            await self.client.aclose()

    async def _auto_flush(self):
        """自动刷新缓冲区"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"自动刷新日志失败: {e}")

    def debug(self, message: str, **kwargs) -> Any:
        """记录调试日志"""
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs) -> Any:
        """记录信息日志"""
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs) -> Any:
        """记录警告日志"""
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, exception: Exception | None = None, **kwargs) -> Any:
        """记录错误日志"""
        if exception:
            kwargs['exception'] = {
                'type': exception.__class__.__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, exception: Exception | None = None, **kwargs) -> Any:
        """记录严重错误日志"""
        if exception:
            kwargs['exception'] = {
                'type': exception.__class__.__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
        self._log("CRITICAL", message, **kwargs)

    def _log(self, level: str, message: str, **kwargs) -> Any:
        """内部日志记录方法"""
        log_entry = {
            "level": level,
            "service": self.service_name,
            "message": message,
            "source": "application",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": kwargs
        }

        # 添加到缓冲区
        self._buffer.append(log_entry)

        # 如果是错误级别或缓冲区满了，立即刷新
        if level in ["ERROR", "CRITICAL"] or len(self._buffer) >= self.buffer_size:
            asyncio.create_task(self.flush())

    async def flush(self):
        """刷新缓冲区到日志服务"""
        if not self._buffer or not self.client:
            return

        try:
            # 批量发送日志
            logs = self._buffer.copy()
            self._buffer.clear()

            response = await self.client.post(
                f"{self.service_host}/api/v1/logs/batch",
                json=logs
            )

            if response.status_code != 200:
                print(f"发送日志失败: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"刷新日志失败: {e}")

# 全局日志记录器实例
_loggers: dict[str, AthenaLogger] = {}

def get_logger(service_name: str) -> AthenaLogger:
    """获取服务日志记录器"""
    if service_name not in _loggers:
        _loggers[service_name] = AthenaLogger(service_name)
        # 注意：需要在应用启动时调用 initialize()
    return _loggers[service_name]

# 装饰器：自动记录函数调用
def log_function_call(level: str = "INFO", include_args: bool = False, include_result: bool = False) -> Any:
    """函数调用日志装饰器"""
    def decorator(func) -> None:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            function_name = f"{func.__module__}.{func.__name__}"

            # 记录函数开始
            log_data = {
                "event": "function_start",
                "function": function_name
            }

            if include_args:
                log_data["args"] = str(args)
                log_data["kwargs"] = str(kwargs)

            logger._log(level, f"开始执行: {function_name}", **log_data)

            # 执行函数
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # 记录函数完成
                log_data = {
                    "event": "function_end",
                    "function": function_name,
                    "success": True
                }

                if include_result:
                    log_data["result"] = str(result)[:500]  # 限制长度

                logger._log(level, f"执行完成: {function_name}", **log_data)
                return result

            except Exception as e:
                # 记录函数异常
                logger.error(
                    f"执行失败: {function_name}",
                    exception=e,
                    event="function_error",
                    function=function_name
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            logger = get_logger(func.__module__)
            function_name = f"{func.__module__}.{func.__name__}"

            # 记录函数开始
            log_data = {
                "event": "function_start",
                "function": function_name
            }

            if include_args:
                log_data["args"] = str(args)
                log_data["kwargs"] = str(kwargs)

            logger._log(level, f"开始执行: {function_name}", **log_data)

            # 执行函数
            try:
                result = func(*args, **kwargs)

                # 记录函数完成
                log_data = {
                    "event": "function_end",
                    "function": function_name,
                    "success": True
                }

                if include_result:
                    log_data["result"] = str(result)[:500]

                logger._log(level, f"执行完成: {function_name}", **log_data)
                return result

            except Exception as e:
                # 记录函数异常
                logger.error(
                    f"执行失败: {function_name}",
                    exception=e,
                    event="function_error",
                    function=function_name
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# 装饰器：记录API请求
def log_api_request(include_response: bool = False) -> Any:
    """API请求日志装饰器"""
    def decorator(func) -> None:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger = get_logger("api")

            # 提取请求信息
            request = None
            for arg in args:
                if hasattr(arg, 'method') and hasattr(arg, 'url'):
                    request = arg
                    break

            if not request:
                return await func(*args, **kwargs)

            # 记录请求开始
            logger.info(
                f"API请求: {request.method} {request.url.path}",
                event="api_request_start",
                method=request.method,
                path=request.url.path,
                query_params=str(request.query_params),
                headers=dict(request.headers)
            )

            # 执行请求
            try:
                response = await func(*args, **kwargs)

                # 记录响应
                log_data = {
                    "event": "api_response",
                    "status_code": response.status_code,
                    "success": 200 <= response.status_code < 400
                }

                if include_response:
                    log_data["response_size"] = len(str(response.body)) if hasattr(response, 'body') else 0

                logger.info(
                    f"API响应: {response.status_code}",
                    **log_data
                )

                return response

            except Exception as e:
                logger.error(
                    f"API请求失败: {request.method} {request.url.path}",
                    exception=e,
                    event="api_error",
                    method=request.method,
                    path=request.url.path
                )
                raise

        return wrapper
    return decorator

# 上下文管理器：跟踪操作
class LogContext:
    """日志上下文管理器"""

    def __init__(self, logger: AthenaLogger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = datetime.now()

    async def __aenter__(self):
        self.logger.info(
            f"开始操作: {self.operation}",
            event="operation_start",
            operation=self.operation,
            **self.context
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type:
            self.logger.error(
                f"操作失败: {self.operation}",
                exception=exc_val,
                event="operation_error",
                operation=self.operation,
                duration=duration,
                **self.context
            )
        else:
            self.logger.info(
                f"操作完成: {self.operation}",
                event="operation_end",
                operation=self.operation,
                duration=duration,
                **self.context
            )

        return False  # 不抑制异常

# 便捷函数
async def initialize_logging(service_name: str):
    """初始化服务的日志记录"""
    logger = get_logger(service_name)
    await logger.initialize()

async def cleanup_logging():
    """清理所有日志记录器"""
    for logger in _loggers.values():
        await logger.close()
    _loggers.clear()

# 使用示例
"""
# 在服务中初始化
await initialize_logging("my-service")

# 使用日志记录器
logger = get_logger("my-service")
logger.info("服务启动")
logger.error("发生错误", exception=e)

# 使用装饰器
@log_function_call(level="DEBUG", include_args=True)
async def process_data(data):
    # 函数实现
    return result

# 使用上下文管理器
async with LogContext(logger, "data_processing", batch_id=123) as ctx:
    # 执行操作
    process_batch()

# 在应用关闭时清理
await cleanup_logging()
"""
