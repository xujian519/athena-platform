"""
视频元信息提取服务 - 主模型定义
基于BiliNote架构，支持多平台视频元信息提取
"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VideoPlatform(str, Enum):
    """支持的视频平台"""
    BILIBILI = 'bilibili'
    YOUTUBE = 'youtube'
    DOUYIN = 'douyin'
    KUAISHOU = 'kuaishou'
    LOCAL = 'local'
    UNKNOWN = 'unknown'


class ExtractionStatus(str, Enum):
    """提取状态"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    SUCCESS = 'success'
    FAILED = 'failed'
    TIMEOUT = 'timeout'


class VideoQuality(str, Enum):
    """视频质量选项"""
    AUTO = 'auto'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


class VideoMetadata(BaseModel):
    """视频元信息模型"""
    video_id: str = Field(..., description='视频唯一标识')
    title: str = Field(..., description='视频标题')
    description: str | None = Field(None, description='视频描述')
    duration: int | None = Field(None, description='视频时长（秒）')
    platform: VideoPlatform = Field(..., description='视频平台')
    author: str | None = Field(None, description='作者/UP主')
    author_id: str | None = Field(None, description='作者ID')
    publish_date: datetime | None = Field(None, description='发布时间')
    view_count: int | None = Field(None, description='播放量')
    like_count: int | None = Field(None, description='点赞数')
    cover_url: str | None = Field(None, description='封面图片URL')
    tags: list[str] = Field(default_factory=list, description='视频标签')
    category: str | None = Field(None, description='视频分类')
    language: str | None = Field(None, description='视频语言')
    resolution: str | None = Field(None, description='视频分辨率')
    file_size: int | None = Field(None, description='文件大小（字节）')
    format: str | None = Field(None, description='视频格式')
    raw_data: dict[str, Any] = Field(default_factory=dict, description='原始数据')
    extracted_at: datetime = Field(default_factory=datetime.now, description='提取时间')


class ExtractionRequest(BaseModel):
    """提取请求模型"""
    url: str = Field(..., description='视频URL')
    platform: VideoPlatform | None = Field(None, description='指定平台，不指定则自动检测')
    quality: VideoQuality = Field(VideoQuality.AUTO, description='提取质量')
    include_raw_data: bool = Field(False, description='是否包含原始数据')
    timeout: int = Field(30, description='超时时间（秒）')
    force_refresh: bool = Field(False, description='是否强制刷新缓存')


class ExtractionResult(BaseModel):
    """提取结果模型"""
    request_id: str = Field(..., description='请求ID')
    status: ExtractionStatus = Field(..., description='提取状态')
    platform: VideoPlatform = Field(..., description='识别的平台')
    metadata: VideoMetadata | None = Field(None, description='视频元信息')
    error_message: str | None = Field(None, description='错误信息')
    extraction_time: float = Field(..., description='提取耗时（秒）')
    cached: bool = Field(False, description='是否来自缓存')
    created_at: datetime = Field(default_factory=datetime.now, description='创建时间')


class CookieInfo(BaseModel):
    """Cookie信息模型"""
    domain: str = Field(..., description='域名')
    name: str = Field(..., description='Cookie名称')
    value: str = Field(..., description='Cookie值')
    expires: datetime | None = Field(None, description='过期时间')
    secure: bool = Field(False, description='是否安全传输')
    http_only: bool = Field(False, description='是否仅HTTP传输')


class PlatformConfig(BaseModel):
    """平台配置模型"""
    platform: VideoPlatform = Field(..., description='平台')
    enabled: bool = Field(True, description='是否启用')
    requires_cookie: bool = Field(False, description='是否需要Cookie')
    cookie_domains: list[str] = Field(default_factory=list, description='Cookie域名列表')
    rate_limit: int = Field(10, description='请求频率限制（每分钟）')
    timeout: int = Field(30, description='默认超时时间')
    retry_count: int = Field(3, description='重试次数')


class ExtractionStats(BaseModel):
    """提取统计模型"""
    total_requests: int = Field(0, description='总请求数')
    successful_extractions: int = Field(0, description='成功提取数')
    failed_extractions: int = Field(0, description='失败提取数')
    cache_hits: int = Field(0, description='缓存命中数')
    average_extraction_time: float = Field(0.0, description='平均提取时间')
    platform_stats: dict[VideoPlatform, int] = Field(default_factory=dict, description='平台统计')
    last_updated: datetime = Field(default_factory=datetime.now, description='最后更新时间')


# 响应模型
class APIResponse(BaseModel):
    """API响应模型"""
    success: bool = Field(..., description='是否成功')
    message: str = Field(..., description='响应消息')
    data: Any | None = Field(None, description='响应数据')
    timestamp: datetime = Field(default_factory=datetime.now, description='响应时间')


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description='服务状态')
    version: str = Field(..., description='服务版本')
    uptime: float = Field(..., description='运行时间（秒）')
    platform_status: dict[VideoPlatform, bool] = Field(default_factory=dict, description='平台状态')
    cache_status: dict[str, Any] = Field(default_factory=dict, description='缓存状态')
    timestamp: datetime = Field(default_factory=datetime.now, description='检查时间')
