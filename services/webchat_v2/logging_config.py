#!/usr/bin/env python3
"""
日志配置模块
提供统一的日志配置和工具（支持日志轮转）

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.2
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


# 日志格式
class LogFormat:
    """日志格式定义"""

    # 详细格式（用于文件）
    DETAILED = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    )

    # 简洁格式（用于控制台）
    SIMPLE = "%(asctime)s | %(levelname)-8s | %(message)s"

    # JSON格式（用于结构化日志）
    JSON = "%(asctime)s %(levelname)s %(name)s %(message)s"


# 自定义异常类
class WebChatException(Exception):
    """WebChat基础异常"""

    def __init__(self, message: str, code: str = "WEBCHAT_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthenticationError(WebChatException):
    """认证错误"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(message, "AUTH_ERROR")


class ValidationError(WebChatException):
    """验证错误"""

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        msg = f"{field}: {message}" if field else message
        super().__init__(msg, "VALIDATION_ERROR")


class ModuleNotFoundError(WebChatException):
    """模块未找到错误"""

    def __init__(self, module: str):
        super().__init__(f"模块不存在: {module}", "MODULE_NOT_FOUND")


class PermissionDeniedError(WebChatException):
    """权限拒绝错误"""

    def __init__(self, user_id: str, resource: str):
        super().__init__(
            f"用户 {user_id} 无权限访问 {resource}",
            "PERMISSION_DENIED"
        )


class InvokeTimeoutError(WebChatException):
    """调用超时错误"""

    def __init__(self, module: str, action: str, timeout: int):
        super().__init__(
            f"模块调用超时: {module}.{action} (超过{timeout}秒)",
            "INVOKE_TIMEOUT"
        )


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    设置日志配置（支持日志轮转）

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件名（不含路径）
        log_dir: 日志目录
        max_bytes: 单个日志文件最大字节数（默认10MB）
        backup_count: 保留的备份文件数量（默认5个）
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 获取根日志记录器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # 清除现有处理器
    logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        LogFormat.SIMPLE,
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件处理器（带轮转）
    if log_file:
        file_path = log_path / log_file

        # 使用RotatingFileHandler实现日志轮转
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            LogFormat.DETAILED,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # 错误日志文件处理器（带轮转）
        error_file_path = log_path / f"{file_path.stem}_error{file_path.suffix}"
        error_handler = RotatingFileHandler(
            error_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称（通常使用__name__）

    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)


def log_exception(
    logger: logging.Logger,
    exception: Exception,
    context: Optional[dict] = None,
    level: int = logging.ERROR
) -> None:
    """
    记录异常及其上下文

    Args:
        logger: 日志记录器
        exception: 异常对象
        context: 上下文信息
        level: 日志级别
    """
    import traceback

    exc_type = type(exception).__name__
    exc_msg = str(exception)

    # 构建日志消息
    msg_parts = [f"[{exc_type}] {exc_msg}"]

    if context:
        ctx_str = " | ".join(f"{k}={v}" for k, v in context.items())
        msg_parts.append(f"Context: {ctx_str}")

    logger.log(level, " | ".join(msg_parts))

    # 在DEBUG级别记录完整堆栈跟踪
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Stack trace:\n{''.join(traceback.format_tb(exception.__traceback__))}")


class LoggingMixin:
    """日志混入类，为类提供便捷的日志方法"""

    @property
    def logger(self) -> logging.Logger:
        """获取该类的日志记录器"""
        return get_logger(self.__class__.__name__)

    def log_exception(
        self,
        exception: Exception,
        context: Optional[dict] = None,
        level: int = logging.ERROR
    ) -> None:
        """记录异常"""
        log_exception(self.logger, exception, context, level)

    def log_debug(self, msg: str, **kwargs) -> None:
        """记录DEBUG级别日志"""
        if kwargs:
            msg = f"{msg} | {kwargs}"
        self.logger.debug(msg)

    def log_info(self, msg: str, **kwargs) -> None:
        """记录INFO级别日志"""
        if kwargs:
            msg = f"{msg} | {kwargs}"
        self.logger.info(msg)

    def log_warning(self, msg: str, **kwargs) -> None:
        """记录WARNING级别日志"""
        if kwargs:
            msg = f"{msg} | {kwargs}"
        self.logger.warning(msg)

    def log_error(self, msg: str, **kwargs) -> None:
        """记录ERROR级别日志"""
        if kwargs:
            msg = f"{msg} | {kwargs}"
        self.logger.error(msg)


def format_request_info(
    method: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    **extra
) -> dict:
    """
    格式化请求信息用于日志

    Args:
        method: 请求方法
        user_id: 用户ID
        session_id: 会话ID
        **extra: 额外信息

    Returns:
        格式化的上下文字典
    """
    context = {}
    if method:
        context["method"] = method
    if user_id:
        context["user_id"] = user_id[:8] + "..."  # 脱敏
    if session_id:
        context["session_id"] = session_id[:8] + "..."  # 脱敏
    context.update(extra)
    return context


def generate_jwt_secret() -> str:
    """
    生成安全的JWT密钥

    Returns:
        随机生成的JWT密钥
    """
    import secrets

    return secrets.token_urlsafe(32)
