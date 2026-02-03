#!/usr/bin/env python3
"""
常量定义 - Athena平台全局常量
Constants - Athena Platform Global Constants

定义所有魔法数字和配置常量,提供统一的常量管理

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

from enum import IntEnum
from typing import Final

# ============================================================================
# 文件大小常量
# ============================================================================


class FileSize(IntEnum):
    """文件大小常量(字节)"""

    B = 1
    KB = 1024
    MB = 1024 * 1024
    GB = 1024 * 1024 * 1024
    TB = 1024 * 1024 * 1024 * 1024


# 文件大小限制
MAX_UPLOAD_SIZE: Final[int] = 100 * FileSize.MB  # 100MB
MAX_CONTENT_ANALYSIS_SIZE: Final[int] = 10 * FileSize.MB  # 10MB
MAX_FILENAME_LENGTH: Final[int] = 255
MIN_FILENAME_LENGTH: Final[int] = 1
MAX_FILE_SIZE_PREVIEW: Final[int] = 5 * FileSize.MB  # 5MB(预览限制)
CHUNK_SIZE: Final[int] = 64 * FileSize.KB  # 64KB(读写块大小)


# ============================================================================
# 超时配置
# ============================================================================


class Timeout(IntEnum):
    """超时常量(秒)"""

    MINUTE = 60
    HOUR = 3600
    DAY = 86400


DEFAULT_TIMEOUT: Final[int] = 30  # 默认超时(秒)
LONG_RUNNING_TIMEOUT: Final[int] = 5 * Timeout.MINUTE  # 5分钟
UPLOAD_TIMEOUT: Final[int] = 5 * Timeout.MINUTE  # 上传超时
DOWNLOAD_TIMEOUT: Final[int] = 3 * Timeout.MINUTE  # 下载超时
PROCESSING_TIMEOUT: Final[int] = 10 * Timeout.MINUTE  # 处理超时
CACHE_TIMEOUT: Final[int] = 1 * Timeout.HOUR  # 缓存超时


# ============================================================================
# 分页配置
# ============================================================================

DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100
MIN_PAGE_SIZE: Final[int] = 1
DEFAULT_PAGE_NUMBER: Final[int] = 1


# ============================================================================
# 缓存配置
# ============================================================================

CACHE_TTL: Final[int] = 3600  # 缓存生存时间(1小时)
CACHE_DIR: Final[str] = "/tmp/athena_cache"
CACHE_MAX_SIZE: Final[int] = 1024 * FileSize.MB  # 缓存最大1GB
CACHE_CLEANUP_INTERVAL: Final[int] = 300  # 缓存清理间隔(5分钟)
LRU_EVICT_COUNT: Final[int] = 100  # LRU淘汰数量


# ============================================================================
# 数据库配置
# ============================================================================

DEFAULT_MIN_CONNECTIONS: Final[int] = 5
DEFAULT_MAX_CONNECTIONS: Final[int] = 20
CONNECTION_TIMEOUT: Final[int] = 10
QUERY_TIMEOUT: Final[int] = 30
POOL_RECYCLE: Final[int] = 3600  # 连接回收时间(1小时)
MAX_OVERFLOW: Final[int] = 10  # 最大溢出连接数


# ============================================================================
# 向量配置
# ============================================================================

VECTOR_DIMENSIONS: Final[int] = 1024  # 向量维度
SIMILARITY_THRESHOLD: Final[float] = 0.7  # 相似度阈值
MIN_SIMILARITY_THRESHOLD: Final[float] = 0.5  # 最低相似度
MAX_RESULTS: Final[int] = 100  # 最大返回结果数


# ============================================================================
# HTTP配置
# ============================================================================

MAX_REQUEST_SIZE: Final[int] = 10 * FileSize.MB  # 最大请求大小
MAX_HEADERS_SIZE: Final[int] = 8192  # 最大头部大小
MAX_URL_LENGTH: Final[int] = 2048  # 最大URL长度


# ============================================================================
# 并发配置
# ============================================================================

MAX_CONCURRENT_REQUESTS: Final[int] = 100
MAX_CONCURRENT_UPLOADS: Final[int] = 10
MAX_CONCURRENT_DOWNLOADS: Final[int] = 20
SEMAPHORE_TIMEOUT: Final[int] = 5  # 信号量超时


# ============================================================================
# 重试配置
# ============================================================================

MAX_RETRY_ATTEMPTS: Final[int] = 3
RETRY_BACKOFF_BASE: Final[float] = 1.0  # 退避基数(秒)
RETRY_BACKOFF_MAX: Final[float] = 10.0  # 最大退避时间(秒)
RETRY_STATUS_CODES: Final[set] = {408, 429, 500, 502, 503, 504}  # 可重试状态码


# ============================================================================
# 日志配置
# ============================================================================

LOG_LEVELS: Final[set] = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
DEFAULT_LOG_LEVEL: Final[str] = "INFO"
LOG_MAX_BYTES: Final[int] = 10 * FileSize.MB  # 日志文件最大10MB
LOG_BACKUP_COUNT: Final[int] = 5  # 日志备份数量


# ============================================================================
# 安全配置
# ============================================================================

MIN_PASSWORD_LENGTH: Final[int] = 8
MAX_PASSWORD_LENGTH: Final[int] = 128
PASSWORD_MIN_COMPLEXITY: Final[int] = 3  # 密码最小复杂度
SESSION_TIMEOUT: Final[int] = 24 * Timeout.HOUR  # 会话超时(24小时)
TOKEN_EXPIRE_HOURS: Final[int] = 24  # Token过期时间
SECRET_KEY_MIN_LENGTH: Final[int] = 32  # 密钥最小长度


# ============================================================================
# 文件类型配置
# ============================================================================

# 支持的图像类型
SUPPORTED_IMAGE_TYPES: Final[list] = [
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".svg",
    ".ico",
    ".tiff",
]

# 支持的文档类型
SUPPORTED_DOCUMENT_TYPES: Final[list] = [
    ".pdf",
    ".doc",
    ".docx",
    ".txt",
    ".md",
    ".rtf",
    ".odt",
    ".pages",
    ".epub",
]

# 支持的音频类型
SUPPORTED_AUDIO_TYPES: Final[list] = [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"]

# 支持的视频类型
SUPPORTED_VIDEO_TYPES: Final[list] = [
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
]

# 支持的数据类型
SUPPORTED_DATA_TYPES: Final[list] = [
    ".json",
    ".xml",
    ".csv",
    ".xlsx",
    ".xls",
    ".yaml",
    ".yml",
    ".sql",
    ".db",
    ".sqlite",
]

# 危险的文件扩展名黑名单
DANGEROUS_EXTENSIONS: Final[set] = {
    ".exe",
    ".bat",
    ".cmd",
    ".com",
    ".scr",
    ".pif",
    ".vbs",
    ".js",
    ".jar",
    ".sh",
    ".ps1",
    ".vb",
    ".wsf",
    ".deb",
    ".rpm",
    ".dmg",
    ".pkg",
    ".app",
}

# 允许的MIME类型白名单
ALLOWED_MIME_TYPES: Final[set] = {
    # 图像
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/bmp",
    "image/webp",
    "image/tiff",
    "image/svg+xml",
    # 文档
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/markdown",
    "text/csv",
    # 音频
    "audio/mpeg",
    "audio/wav",
    "audio/flac",
    "audio/aac",
    "audio/ogg",
    # 视频
    "video/mp4",
    "video/avi",
    "video/quicktime",
    "video/x-matroska",
    "video/webm",
    # 数据
    "application/json",
    "application/xml",
    "text/xml",
    # 压缩
    "application/zip",
    "application/x-rar-compressed",
    "application/x-7z-compressed",
    "application/x-tar",
    "application/gzip",
    "application/x-gzip",
}


# ============================================================================
# 性能配置
# ============================================================================

PROCESSING_QUEUE_SIZE: Final[int] = 1000  # 处理队列大小
BATCH_PROCESSING_SIZE: Final[int] = 32  # 批处理大小
WORKER_COUNT: Final[int] = 4  # 工作进程数
ASYNCIO_TASK_TIMEOUT: Final[int] = 300  # 异步任务超时


# ============================================================================
# 监控配置
# ============================================================================

HEALTH_CHECK_INTERVAL: Final[int] = 30  # 健康检查间隔(秒)
METRICS_COLLECTION_INTERVAL: Final[int] = 60  # 指标收集间隔(秒)
STATS_RETENTION_DAYS: Final[int] = 30  # 统计数据保留天数


# ============================================================================
# 响应代码
# ============================================================================


class ResponseCode:
    """响应代码常量"""

    # 成功
    SUCCESS = "SUCCESS"
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED"

    # 客户端错误
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    CONFLICT = "CONFLICT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"

    # 服务器错误
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    GATEWAY_TIMEOUT = "GATEWAY_TIMEOUT"


# ============================================================================
# 日期时间格式
# ============================================================================

DATETIME_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT: Final[str] = "%Y-%m-%d"
TIME_FORMAT: Final[str] = "%H:%M:%S"
ISO_DATETIME_FORMAT: Final[str] = "%Y-%m-%d_t%H:%M:%S"
ISO_DATETIME_FORMAT_WITH_TZ: Final[str] = "%Y-%m-%d_t%H:%M:%S%z"


# ============================================================================
# 文件编码
# ============================================================================

DEFAULT_ENCODING: Final[str] = "utf-8"
FALLBACK_ENCODING: Final[str] = "latin-1"
BOM_ENCODINGS: Final[list] = ["utf-8-sig", "utf-16", "utf-32"]


# ============================================================================
# 正则表达式模式
# ============================================================================

import re

EMAIL_PATTERN: Final[re.Pattern] = re.compile(
    r"^[a-z_a-Z0-9._%+-]+@[a-z_a-Z0-9.-]+\.[a-z_a-Z]{2,}$"
)
PHONE_PATTERN: Final[re.Pattern] = re.compile(r"^\+?[\d\s\-()]+$")
URL_PATTERN: Final[re.Pattern] = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")
FILENAME_PATTERN: Final[re.Pattern] = re.compile(r"^[\w\-\.\u4e00-\u9fff]+$")
SAFE_STRING_PATTERN: Final[re.Pattern] = re.compile(r"^[a-zA-Z0-9_-]+$")


# ============================================================================
# API相关
# ============================================================================

API_VERSION: Final[str] = "v1"
API_PREFIX: Final[str] = f"/api/{API_VERSION}"
API_TITLE: Final[str] = "Athena工作平台 API"
API_DESCRIPTION: Final[str] = "智能专利分析与检索系统"
DEFAULT_LIMIT: Final[int] = 20
MAX_LIMIT: Final[int] = 100


# ============================================================================
# 导出限制
# ============================================================================

MAX_EXPORT_ROWS: Final[int] = 100000  # 最大导出行数
EXPORT_CHUNK_SIZE: Final[int] = 1000  # 导出块大小


# ============================================================================
# 通知配置
# ============================================================================

NOTIFICATION_TYPES: Final[set] = {"email", "sms", "webhook", "websocket"}
MAX_NOTIFICATION_RETRIES: Final[int] = 3
NOTIFICATION_TIMEOUT: Final[int] = 30


# ============================================================================
# 任务配置
# ============================================================================

TASK_PRIORITY_HIGH: Final[int] = 1
TASK_PRIORITY_NORMAL: Final[int] = 2
TASK_PRIORITY_LOW: Final[int] = 3

TASK_STATUS_PENDING: Final[str] = "pending"
TASK_STATUS_RUNNING: Final[str] = "running"
TASK_STATUS_COMPLETED: Final[str] = "completed"
TASK_STATUS_FAILED: Final[str] = "failed"
TASK_STATUS_CANCELLED: Final[str] = "cancelled"


# ============================================================================
# 文本处理常量
# ============================================================================

MAX_TEXT_LENGTH: Final[int] = 10000  # 最大文本长度
MIN_TEXT_LENGTH: Final[int] = 1
DEFAULT_LANGUAGE: Final[str] = "zh"
SUPPORTED_LANGUAGES: Final[set] = {"zh", "en", "ja", "ko", "fr", "de", "es", "ru"}


# ============================================================================
# 路径常量
# ============================================================================

TEMP_DIR: Final[str] = "/tmp/athena_temp"
LOG_DIR: Final[str] = "logs"
UPLOAD_DIR: Final[str] = "uploads"
DOWNLOAD_DIR: Final[str] = "downloads"
BACKUP_DIR: Final[str] = "backups"


# ============================================================================
# 版本信息
# ============================================================================

VERSION: Final[str] = "2.0.0"
BUILD_DATE: Final[str] = "2026-01-16"
API_COMPATIBILITY_VERSION: Final[str] = "1.0.0"


# ============================================================================
# 辅助函数
# ============================================================================


def format_bytes(size: int) -> str:
    """
    格式化字节数为可读字符串

    Args:
        size: 字节数

    Returns:
        格式化后的字符串(如 "1.5MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}PB"


def format_duration(seconds: int) -> str:
    """
    格式化秒数为可读字符串

    Args:
        seconds: 秒数

    Returns:
        格式化后的字符串(如 "5m30s")
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m{secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h{minutes}m"
