from __future__ import annotations
"""
意图识别服务 - API数据模型

定义所有API请求和响应的Pydantic模型。

Author: Xiaonuo
Created: 2025-01-17
Version: 1.0.0
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

# ========================================================================
# 请求模型
# ========================================================================


class IntentRecognitionRequest(BaseModel):
    """意图识别请求"""

    text: str = Field(..., description="待识别的文本", min_length=1, max_length=10000)
    context: dict[str, Any] | None = Field(default=None, description="上下文信息")
    engine: str | None = Field(default="keyword", description="引擎类型")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v) -> str:
        """验证文本不为空且仅包含空白字符"""
        if not v or not v.strip():
            raise ValueError("文本不能为空")
        return v.strip()


class BatchIntentRecognitionRequest(BaseModel):
    """批量意图识别请求"""

    texts: list[str] = Field(..., description="待识别的文本列表", min_items=1, max_items=100)
    engine: str | None = Field(default="keyword", description="引擎类型")

    @field_validator("texts")
    @classmethod
    def validate_texts(cls, v) -> list[str]:
        """验证文本列表"""
        if not v:
            raise ValueError("文本列表不能为空")
        # 验证每个文本
        validated = []
        for text in v:
            if not text or not text.strip():
                raise ValueError("文本列表不能包含空文本")
            validated.append(text.strip())
        return validated


class ModelLoadRequest(BaseModel):
    """模型加载请求"""

    device: str | None = Field(default="auto", description="设备类型")


# ========================================================================
# 响应模型
# ========================================================================


class IntentRecognitionResponse(BaseModel):
    """意图识别响应"""

    intent: str = Field(description="识别出的意图类型")
    confidence: float = Field(description="置信度", ge=0.0, le=1.0)
    category: str = Field(description="意图类别")
    entities: list[str] = Field(default_factory=list, description="提取的实体")
    processing_time_ms: float = Field(description="处理时间(毫秒)")
    model_version: str = Field(description="模型版本")


class BatchIntentRecognitionResponse(BaseModel):
    """批量意图识别响应"""

    results: list[IntentRecognitionResponse] = Field(description="识别结果列表")
    total_count: int = Field(description="总数量")
    successful_count: int = Field(description="成功数量")
    failed_count: int = Field(description="失败数量")
    total_processing_time_ms: float = Field(description="总处理时间(毫秒)")


class EngineInfo(BaseModel):
    """引擎信息"""

    name: str = Field(description="引擎名称")
    version: str = Field(description="引擎版本")
    description: str = Field(description="引擎描述")
    supported_intents: list[str] = Field(description="支持的意图类型")
    is_active: bool = Field(description="是否激活")


class EnginesListResponse(BaseModel):
    """引擎列表响应"""

    engines: list[EngineInfo] = Field(description="引擎列表")
    total_count: int = Field(description="总数量")


class EngineStatsResponse(BaseModel):
    """引擎统计响应"""

    name: str = Field(description="引擎名称")
    version: str = Field(description="引擎版本")
    stats: dict[str, Any] = Field(description="统计信息")


class ModelInfo(BaseModel):
    """模型信息"""

    name: str = Field(description="模型名称")
    type: str = Field(description="模型类型")
    status: str = Field(description="模型状态")
    device: str | None = Field(description="设备类型")
    load_time: datetime | None = Field(description="加载时间")
    last_access: datetime | None = Field(description="最后访问时间")
    access_count: int = Field(description="访问次数")
    memory_usage_mb: float | None = Field(description="内存使用(MB)")


class ModelsListResponse(BaseModel):
    """模型列表响应"""

    models: list[ModelInfo] = Field(description="模型列表")
    total_count: int = Field(description="总数量")
    loaded_count: int = Field(description="已加载数量")


class ModelLoadResponse(BaseModel):
    """模型加载响应"""

    message: str = Field(description="响应消息")
    model_name: str = Field(description="模型名称")
    load_time: datetime | None = Field(description="加载时间")
    duration_ms: float = Field(description="加载耗时(毫秒)")


class ModelUnloadResponse(BaseModel):
    """模型卸载响应"""

    message: str = Field(description="响应消息")
    model_name: str = Field(description="模型名称")
    memory_freed_mb: float | None = Field(description="释放的内存(MB)")


# ========================================================================
# 通用响应模型
# ========================================================================


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(description="服务状态: healthy, unhealthy")
    version: str = Field(description="服务版本")
    uptime_seconds: float = Field(description="运行时长(秒)")
    timestamp: datetime = Field(description="检查时间")


class ReadinessResponse(BaseModel):
    """就绪检查响应"""

    ready: bool = Field(description="是否就绪")
    checks: dict[str, str] = Field(description="各项检查结果")


class ErrorResponse(BaseModel):
    """错误响应"""

    error: str = Field(description="错误类型")
    message: str = Field(description="错误消息")
    details: dict[str, Any] | None = Field(default=None, description="错误详情")
    timestamp: datetime = Field(description="错误时间")


class StatsResponse(BaseModel):
    """统计信息响应"""

    service: dict[str, Any] = Field(description="服务信息")
    engines: dict[str, Any] = Field(description="引擎信息")
    models: dict[str, Any] = Field(description="模型信息")
    performance: dict[str, Any] = Field(description="性能信息")
    errors: dict[str, Any] = Field(description="错误信息")


# ========================================================================
# 认证模型
# ========================================================================


class TokenResponse(BaseModel):
    """令牌响应"""

    access_token: str = Field(description="访问令牌")
    token_type: str = Field(description="令牌类型")
    expires_in: int = Field(description="过期时间(秒)")


class LoginRequest(BaseModel):
    """登录请求"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class APIKeyResponse(BaseModel):
    """API密钥响应"""

    api_key: str = Field(description="API密钥")
    created_at: datetime = Field(description="创建时间")
    expires_at: datetime | None = Field(description="过期时间")


# ========================================================================
# 导出
# ========================================================================

__all__ = [
    "APIKeyResponse",
    "BatchIntentRecognitionRequest",
    "BatchIntentRecognitionResponse",
    "EngineInfo",
    "EngineStatsResponse",
    "EnginesListResponse",
    "ErrorResponse",
    # 通用响应
    "HealthResponse",
    # 请求模型
    "IntentRecognitionRequest",
    # 响应模型
    "IntentRecognitionResponse",
    "LoginRequest",
    "ModelInfo",
    "ModelLoadRequest",
    "ModelLoadResponse",
    "ModelUnloadResponse",
    "ModelsListResponse",
    "ReadinessResponse",
    "StatsResponse",
    # 认证模型
    "TokenResponse",
]
