#!/usr/bin/env python3
"""
专利应用标准化API接口规范
Patent Application Standardized API Interface Specification

定义统一的查询、响应、错误处理和日志记录标准，确保模块间通信一致性。

Created by Athena + AI团队
Date: 2025-12-05
"""

import json
import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

# 设置日志
logger = logging.getLogger(__name__)

class ModuleName(Enum):
    """模块名称枚举"""
    MEMORY_SYSTEM = 'memory_system'
    LEARNING_SYSTEM = 'learning_system'
    COMMUNICATION_SYSTEM = 'communication_system'
    EVALUATION_SYSTEM = 'evaluation_system'
    KNOWLEDGE_SYSTEM = 'knowledge_system'
    AI_CONFIG = 'ai_config'

class KnowledgeType(Enum):
    """知识类型枚举"""
    PATENT_RULE = 'patent_rule'
    CASE_LAW = 'case_law'
    TECHNICAL_STANDARD = 'technical_standard'
    EXAMINATION_GUIDE = 'examination_guide'
    LEGAL_REGULATION = 'legal_regulation'

class EvaluationType(Enum):
    """评估类型枚举"""
    PATENT_QUALITY = 'patent_quality'
    NOVELTY_ASSESSMENT = 'novelty_assessment'
    INVENTIVENESS_EVALUATION = 'inventiveness_evaluation'
    COMMERCIAL_VALUE = 'commercial_value'
    LEGAL_RISK = 'legal_risk'

class CommunicationType(Enum):
    """通信类型枚举"""
    INTERNAL = 'internal'
    EXTERNAL = 'external'
    AI_FAMILY = 'ai_family'
    SYSTEM = 'system'

class PriorityLevel(Enum):
    """优先级枚举"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'

class StatusCode(Enum):
    """状态码枚举"""
    SUCCESS = 'success'
    ERROR = 'error'
    WARNING = 'warning'
    PENDING = 'pending'
    TIMEOUT = 'timeout'

@dataclass
class StandardQuery:
    """标准化查询基类"""
    query_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source_module: ModuleName = None
    target_module: ModuleName = None
    query_type: str = ''
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class KnowledgeQuery(StandardQuery):
    """知识库查询"""
    query_type: str = 'knowledge_search'
    query_text: str = ''
    knowledge_types: list[KnowledgeType] = field(default_factory=list)
    max_results: int = 10
    relevance_threshold: float = 0.5
    filters: dict[str, Any] = field(default_factory=dict)

@dataclass
class EvaluationQuery(StandardQuery):
    """评估查询"""
    query_type: str = 'evaluation'
    patent_id: str = ''
    evaluation_type: EvaluationType = None
    evaluation_scope: list[str] = field(default_factory=list)
    criteria_weights: dict[str, float] = field(default_factory=dict)

@dataclass
class LearningQuery(StandardQuery):
    """学习查询"""
    query_type: str = 'learning'
    ai_member: str = ''
    learning_focus: list[str] = field(default_factory=list)
    patent_case: dict[str, Any] = field(default_factory=dict)
    execution_result: dict[str, Any] = field(default_factory=dict)

@dataclass
class CommunicationQuery(StandardQuery):
    """通信查询"""
    query_type: str = 'communication'
    message_id: str = ''
    communication_type: CommunicationType = None
    sender: str = ''
    recipient: str = ''
    content: str = ''
    optimization_level: str = 'standard'

@dataclass
class StandardResponse:
    """标准化响应基类"""
    query_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source_module: ModuleName = None
    status: StatusCode = StatusCode.SUCCESS
    success: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    message: str = ''
    execution_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class KnowledgeResponse(StandardResponse):
    """知识库响应"""
    results: list[dict[str, Any] = field(default_factory=list)
    total_found: int = 0
    search_time: float = 0.0
    relevance_scores: list[float] = field(default_factory=list)

@dataclass
class EvaluationResponse(StandardResponse):
    """评估响应"""
    overall_score: float = 0.0
    confidence_score: float = 0.0
    detailed_scores: dict[str, float] = field(default_factory=dict)
    evaluation_criteria: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

@dataclass
class LearningResponse(StandardResponse):
    """学习响应"""
    learning_score: float = 0.0
    insights: list[dict[str, Any] = field(default_factory=list)
    improvement_areas: list[str] = field(default_factory=list)
    next_focus_areas: list[str] = field(default_factory=list)
    experience_gained: dict[str, Any] = field(default_factory=dict)

@dataclass
class CommunicationResponse(StandardResponse):
    """通信响应"""
    optimized_content: str = ''
    optimization_notes: list[str] = field(default_factory=list)
    professional_terms: list[str] = field(default_factory=list)
    clarity_score: float = 0.0
    appropriateness_score: float = 0.0

class StandardError:
    """标准化错误处理"""

    def __init__(self, error_code: str, error_message: str,
                 details: dict[str, Any] = None, module: ModuleName = None):
        self.error_code = error_code
        self.error_message = error_message
        self.details = details or {}
        self.module = module
        self.timestamp = datetime.now().isoformat()
        self.traceback = traceback.format_exc()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            'error_code': self.error_code,
            'error_message': self.error_message,
            'details': self.details,
            'module': self.module.value if self.module else None,
            'timestamp': self.timestamp,
            'traceback': self.traceback
        }

    def to_response(self, query_id: str, source_module: ModuleName = None) -> StandardResponse:
        """转换为错误响应"""
        return StandardResponse(
            query_id=query_id,
            source_module=source_module,
            status=StatusCode.ERROR,
            success=False,
            message=f"{self.error_code}: {self.error_message}",
            metadata={'error': self.to_dict()}
        )

class StandardLogger:
    """标准化日志记录"""

    @staticmethod
    def log_query_start(query: StandardQuery):
        """记录查询开始"""
        logger.info(f"[QUERY_START] {query.source_module.value} -> {query.target_module.value}: {query.query_type} (ID: {query.query_id})")
        logger.debug(f"Query details: {json.dumps(query.parameters, ensure_ascii=False, indent=2)}")

    @staticmethod
    def log_query_success(query: StandardQuery, response: StandardResponse):
        """记录查询成功"""
        execution_time = response.execution_time
        logger.info(f"[QUERY_SUCCESS] {query.query_type} completed in {execution_time:.3f}s (ID: {query.query_id})")
        if response.data:
            logger.debug(f"Response data: {json.dumps(response.data, ensure_ascii=False, indent=2)}")

    @staticmethod
    def log_query_error(query: StandardQuery, error: StandardError):
        """记录查询错误"""
        logger.error(f"[QUERY_ERROR] {query.query_type} failed (ID: {query.query_id}): {error.error_message}")
        logger.debug(f"Error details: {json.dumps(error.to_dict(), ensure_ascii=False, indent=2)}")

    @staticmethod
    def log_module_operation(module: ModuleName, operation: str, details: dict[str, Any] = None):
        """记录模块操作"""
        logger.info(f"[MODULE_OPERATION] {module.value}: {operation}")
        if details:
            logger.debug(f"Operation details: {json.dumps(details, ensure_ascii=False, indent=2)}")

    @staticmethod
    def log_inter_module_communication(source: ModuleName, target: ModuleName,
                                      message_type: str, status: str, details: dict[str, Any] = None):
        """记录模块间通信"""
        logger.info(f"[INTER_MODULE] {source.value} -> {target.value}: {message_type} ({status})")
        if details:
            logger.debug(f"Communication details: {json.dumps(details, ensure_ascii=False, indent=2)}")

class APIValidator:
    """API接口验证器"""

    @staticmethod
    def validate_query(query: StandardQuery) -> list[str]:
        """验证查询格式"""
        errors = []

        if not query.query_id:
            errors.append('query_id is required')

        if not query.source_module:
            errors.append('source_module is required')

        if not query.target_module:
            errors.append('target_module is required')

        if not query.query_type:
            errors.append('query_type is required')

        if query.timestamp and len(query.timestamp) < 10:
            errors.append('timestamp format is invalid')

        return errors

    @staticmethod
    def validate_response(response: StandardResponse) -> list[str]:
        """验证响应格式"""
        errors = []

        if not response.query_id:
            errors.append('query_id is required')

        if not response.source_module:
            errors.append('source_module is required')

        if response.execution_time < 0:
            errors.append('execution_time cannot be negative')

        return errors

    @staticmethod
    def validate_knowledge_query(query: KnowledgeQuery) -> list[str]:
        """验证知识查询格式"""
        errors = APIValidator.validate_query(query)

        if not query.query_text:
            errors.append('query_text is required for knowledge queries')

        if query.max_results <= 0:
            errors.append('max_results must be positive')

        if not (0 <= query.relevance_threshold <= 1):
            errors.append('relevance_threshold must be between 0 and 1')

        return errors

    @staticmethod
    def validate_evaluation_query(query: EvaluationQuery) -> list[str]:
        """验证评估查询格式"""
        errors = APIValidator.validate_query(query)

        if not query.patent_id:
            errors.append('patent_id is required for evaluation queries')

        if not query.evaluation_type:
            errors.append('evaluation_type is required for evaluation queries')

        return errors

class APIAdapter:
    """API适配器基类"""

    def __init__(self, module_name: ModuleName):
        self.module_name = module_name
        self.logger = StandardLogger()

    async def handle_query(self, query: StandardQuery) -> StandardResponse:
        """处理查询的通用方法"""
        start_time = datetime.now()

        try:
            # 验证查询格式
            validation_errors = self._validate_query(query)
            if validation_errors:
                error = StandardError(
                    error_code='VALIDATION_ERROR',
                    error_message='Query validation failed',
                    details={'errors': validation_errors},
                    module=self.module_name
                )
                self.logger.log_query_error(query, error)
                return error.to_response(query.query_id, self.module_name)

            # 记录查询开始
            self.logger.log_query_start(query)

            # 处理查询
            response = await self._process_query(query)

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            response.execution_time = execution_time

            # 记录查询成功
            self.logger.log_query_success(query, response)

            return response

        except Exception as e:
            # 处理异常
            execution_time = (datetime.now() - start_time).total_seconds()
            error = StandardError(
                error_code='PROCESSING_ERROR',
                error_message=str(e),
                module=self.module_name
            )
            self.logger.log_query_error(query, error)

            response = error.to_response(query.query_id, self.module_name)
            response.execution_time = execution_time
            return response

    def _validate_query(self, query: StandardQuery) -> list[str]:
        """子类重写此方法实现特定验证"""
        return APIValidator.validate_query(query)

    async def _process_query(self, query: StandardQuery) -> StandardResponse:
        """子类必须重写此方法实现具体处理逻辑"""
        raise NotImplementedError('Subclasses must implement _process_query method')

# 预定义的标准错误类型
class StandardErrors:
    """预定义的标准错误"""

    VALIDATION_ERROR = 'VALIDATION_ERROR'
    PROCESSING_ERROR = 'PROCESSING_ERROR'
    TIMEOUT_ERROR = 'TIMEOUT_ERROR'
    RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND'
    PERMISSION_DENIED = 'PERMISSION_DENIED'
    MODULE_UNAVAILABLE = 'MODULE_UNAVAILABLE'
    COMMUNICATION_FAILURE = 'COMMUNICATION_FAILURE'
    DATA_FORMAT_ERROR = 'DATA_FORMAT_ERROR'
    CAPACITY_EXCEEDED = 'CAPACITY_EXCEEDED'
    CONFIGURATION_ERROR = 'CONFIGURATION_ERROR'

# 标准配置
class StandardConfig:
    """标准配置常量"""

    # 查询配置
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_RELEVANCE_THRESHOLD = 0.5
    MAX_QUERY_TIMEOUT = 30.0  # 秒

    # 响应配置
    MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10MB
    DEFAULT_PAGE_SIZE = 20

    # 日志配置
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # 缓存配置
    DEFAULT_CACHE_TTL = 300  # 5分钟
    MAX_CACHE_SIZE = 1000

    # 重试配置
    DEFAULT_RETRY_COUNT = 3
    RETRY_DELAY = 1.0  # 秒
