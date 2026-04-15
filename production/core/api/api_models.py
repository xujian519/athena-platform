#!/usr/bin/env python3
"""
API请求/响应模型

定义所有API使用的请求和响应模型
"""

from __future__ import annotations
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# 通用模型
# =============================================================================


class ErrorDetail(BaseModel):
    """错误详情"""

    field: str = Field(..., description="错误字段")
    message: str = Field(..., description="错误消息")
    type: str = Field(..., description="错误类型")

    class Config:
        json_schema_extra = {
            "example": {
                "field": "message",
                "message": "字段不能为空",
                "type": "value_error.missing",
            }
        }


class ErrorResponse(BaseModel):
    """标准错误响应"""

    success: bool = Field(False, description="请求是否成功")
    message: str = Field(..., description="错误消息")
    error_code: str = Field(..., description="错误代码")
    details: dict[str, Any] | None = Field(None, description="错误详情")
    timestamp: str = Field(..., description="时间戳")
    path: str | None = Field(None, description="请求路径")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "请求验证失败",
                "error_code": "VALIDATION_ERROR",
                "timestamp": "2025-12-30T12:00:00",
                "path": "/chat",
            }
        }


class SuccessResponse(BaseModel):
    """标准成功响应"""

    success: bool = Field(True, description="请求是否成功")
    message: str = Field(..., description="成功消息")
    data: Any | None = Field(None, description="响应数据")
    timestamp: str = Field(..., description="时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {},
                "timestamp": "2025-12-30T12:00:00",
            }
        }


# =============================================================================
# Phase 2扩展模型
# =============================================================================


class ResponseDetailEnum(str, Enum):
    """响应详细程度枚举"""

    BRIEF = "brief"
    MEDIUM = "medium"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class TechnicalDepthEnum(str, Enum):
    """技术深度枚举"""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LanguageStyleEnum(str, Enum):
    """语言风格枚举"""

    CASUAL = "casual"
    PROFESSIONAL = "professional"
    FORMAL = "formal"
    FRIENDLY = "friendly"


class OutputFormatEnum(str, Enum):
    """输出格式枚举"""

    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    BULLET_POINTS = "bullet_points"
    TABLE = "table"


class UserPreferenceRequest(BaseModel):
    """用户偏好设置请求"""

    response_detail: ResponseDetailEnum = Field(
        ResponseDetailEnum.MEDIUM, description="响应详细程度"
    )
    technical_depth: TechnicalDepthEnum = Field(
        TechnicalDepthEnum.INTERMEDIATE, description="技术深度"
    )
    language_style: LanguageStyleEnum = Field(
        LanguageStyleEnum.PROFESSIONAL, description="语言风格"
    )
    output_format: OutputFormatEnum = Field(OutputFormatEnum.TEXT, description="输出格式")
    preferred_agent: str | None = Field(None, description="首选智能体")
    avoid_topics: list[str] | None = Field(None, description="避免的话题")

    class Config:
        json_schema_extra = {
            "example": {
                "response_detail": "detailed",
                "technical_depth": "advanced",
                "language_style": "professional",
                "output_format": "markdown",
            }
        }


class UserPreferenceResponse(BaseModel):
    """用户偏好响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    user_id: str = Field(..., description="用户ID")
    preference: UserPreferenceRequest = Field(..., description="用户偏好")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "用户偏好已保存",
                "user_id": "user_001",
                "preference": {"response_detail": "detailed", "technical_depth": "advanced"},
            }
        }


class WorkflowTaskDefinition(BaseModel):
    """工作流任务定义"""

    name: str = Field(..., description="任务名称")
    capability: str = Field(..., description="使用的能力")
    input: dict[str, Any] = Field(default_factory=dict, description="任务输入")
    depends_on: list[str] = Field(default_factory=list, description="依赖的任务ID列表")
    timeout: float | None = Field(None, description="超时时间(秒)")
    retry: int = Field(0, description="重试次数")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "专利检索",
                "capability": "patent_search",
                "input": {"query": "人工智能"},
                "depends_on": [],
                "timeout": 30.0,
                "retry": 2,
            }
        }


class WorkflowRequest(BaseModel):
    """工作流执行请求"""

    name: str = Field(..., description="工作流名称")
    description: str = Field(..., description="工作流描述")
    tasks: list[WorkflowTaskDefinition] = Field(..., description="任务列表")
    stop_on_failure: bool = Field(True, description="失败时是否停止")
    timeout: float | None = Field(None, description="总超时时间(秒)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "专利分析工作流",
                "description": "检索并分析专利",
                "tasks": [
                    {"name": "专利检索", "capability": "patent_search", "input": {"query": "AI"}},
                    {
                        "name": "专利分析",
                        "capability": "patent_analysis",
                        "depends_on": ["专利检索"],
                    },
                ],
            }
        }


class TaskResult(BaseModel):
    """任务结果"""

    task_id: str = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    status: str = Field(..., description="任务状态: pending/running/success/failed")
    result: Any | None = Field(None, description="任务结果")
    error: str | None = Field(None, description="错误信息")
    start_time: float = Field(..., description="开始时间")
    end_time: float | None = Field(None, description="结束时间")
    duration: float | None = Field(None, description="执行时长(秒)")


class WorkflowResponse(BaseModel):
    """工作流执行响应"""

    success: bool = Field(..., description="是否成功")
    workflow_id: str = Field(..., description="工作流ID")
    workflow_name: str = Field(..., description="工作流名称")
    status: str = Field(..., description="工作流状态")
    results: list[TaskResult] = Field(..., description="任务结果列表")
    total_duration: float = Field(..., description="总执行时长(秒)")
    error: str | None = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "workflow_id": "wf_001",
                "workflow_name": "专利分析",
                "status": "completed",
                "results": [],
                "total_duration": 5.2,
            }
        }


class EntityTypeEnum(str, Enum):
    """实体类型枚举"""

    PATENT = "patent"
    CONCEPT = "concept"
    COMPANY = "company"
    INVENTOR = "inventor"
    TECHNOLOGY = "technology"


class RelationDirectionEnum(str, Enum):
    """关系方向枚举"""

    IN = "in"
    OUT = "out"
    BOTH = "both"


class KnowledgeSearchRequest(BaseModel):
    """知识图谱搜索请求"""

    query: str = Field(..., description="搜索关键词")
    entity_type: EntityTypeEnum | None = Field(None, description="实体类型过滤")
    limit: int = Field(10, ge=1, le=100, description="返回数量限制")
    include_relations: bool = Field(True, description="是否包含关系")
    relation_direction: RelationDirectionEnum = Field(
        RelationDirectionEnum.BOTH, description="关系方向"
    )
    max_depth: int = Field(2, ge=1, le=5, description="最大搜索深度")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "BERT",
                "entity_type": "concept",
                "limit": 10,
                "include_relations": True,
                "max_depth": 2,
            }
        }


class Entity(BaseModel):
    """实体"""

    id: str = Field(..., description="实体ID")
    name: str = Field(..., description="实体名称")
    type: EntityTypeEnum = Field(..., description="实体类型")
    properties: dict[str, Any] = Field(default_factory=dict, description="实体属性")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "entity_001",
                "name": "BERT",
                "type": "concept",
                "properties": {"year": 2018, "authors": ["Devlin et al."]},
            }
        }


class Relation(BaseModel):
    """关系"""

    id: str = Field(..., description="关系ID")
    source: str = Field(..., description="源实体ID")
    target: str = Field(..., description="目标实体ID")
    relation_type: str = Field(..., description="关系类型")
    properties: dict[str, Any] = Field(default_factory=dict, description="关系属性")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "rel_001",
                "source": "entity_001",
                "target": "entity_002",
                "relation_type": "based_on",
                "properties": {"strength": 0.9},
            }
        }


class KnowledgeSearchResponse(BaseModel):
    """知识图谱搜索响应"""

    success: bool = Field(..., description="是否成功")
    query: str = Field(..., description="搜索查询")
    entities: list[Entity] = Field(..., description="找到的实体")
    relations: list[Relation] = Field(default_factory=list, description="实体间关系")
    total_entities: int = Field(..., description="实体总数")
    total_relations: int = Field(0, description="关系总数")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "query": "BERT",
                "entities": [],
                "relations": [],
                "total_entities": 10,
                "total_relations": 15,
            }
        }


# =============================================================================
# 告警模型
# =============================================================================


class AlertSeverityEnum(str, Enum):
    """告警严重级别枚举"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannelEnum(str, Enum):
    """告警渠道枚举"""

    LOG = "log"
    CONSOLE = "console"
    EMAIL = "email"
    WEBHOOK = "webhook"


class AlertTestRequest(BaseModel):
    """告警测试请求"""

    severity: AlertSeverityEnum = Field(AlertSeverityEnum.WARNING, description="告警严重级别")
    channels: list[AlertChannelEnum] = Field(
        default_factory=lambda: [AlertChannelEnum.CONSOLE], description="通知渠道"
    )
    message: str = Field("这是一条测试告警", description="告警消息")

    class Config:
        json_schema_extra = {
            "example": {
                "severity": "warning",
                "channels": ["console", "log"],
                "message": "测试告警",
            }
        }


class AlertTestResponse(BaseModel):
    """告警测试响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    alert_id: str = Field(..., description="告警ID")
    severity: AlertSeverityEnum = Field(..., description="告警级别")
    channels_sent: list[str] = Field(..., description="已发送的渠道")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "测试告警已发送",
                "alert_id": "alert_001",
                "severity": "warning",
                "channels_sent": ["console", "log"],
            }
        }


# =============================================================================
# 能力相关模型
# =============================================================================


class CapabilityInfo(BaseModel):
    """能力信息"""

    id: str = Field(..., description="能力ID")
    name: str = Field(..., description="能力名称")
    description: str = Field(..., description="能力描述")
    category: str = Field(..., description="能力分类")
    enabled: bool = Field(True, description="是否启用")
    usage_count: int = Field(0, description="使用次数")
    avg_response_time: float = Field(0.0, description="平均响应时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "xiaona",
                "name": "小娜能力",
                "description": "专利法律专业服务",
                "category": "legal",
                "enabled": True,
                "usage_count": 1234,
                "avg_response_time": 0.5,
            }
        }


class CapabilitiesListResponse(BaseModel):
    """能力列表响应"""

    success: bool = Field(..., description="是否成功")
    total: int = Field(..., description="总能力数")
    enabled: int = Field(..., description="已启用数量")
    capabilities: list[CapabilityInfo] = Field(..., description="能力列表")

    class Config:
        json_schema_extra = {
            "example": {"success": True, "total": 17, "enabled": 17, "capabilities": []}
        }


# =============================================================================
# 导出所有模型
# =============================================================================

__all__ = [
    "AlertChannelEnum",
    # 告警模型
    "AlertSeverityEnum",
    "AlertTestRequest",
    "AlertTestResponse",
    "CapabilitiesListResponse",
    # 能力相关模型
    "CapabilityInfo",
    "Entity",
    "EntityTypeEnum",
    # 通用模型
    "ErrorDetail",
    "ErrorResponse",
    "KnowledgeSearchRequest",
    "KnowledgeSearchResponse",
    "LanguageStyleEnum",
    "OutputFormatEnum",
    "Relation",
    "RelationDirectionEnum",
    # Phase 2扩展模型
    "ResponseDetailEnum",
    "SuccessResponse",
    "TaskResult",
    "TechnicalDepthEnum",
    "UserPreferenceRequest",
    "UserPreferenceResponse",
    "WorkflowRequest",
    "WorkflowResponse",
    "WorkflowTaskDefinition",
]
