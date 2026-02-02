#!/usr/bin/env python3
"""
Athena智能搜索选择器 - 类型定义
Athena Search Selector - Type Definitions

作者: Athena AI系统
创建时间: 2025-12-05
重构时间: 2026-01-27
版本: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from ...standards.base_search_tool import QueryComplexity


class QueryIntent(Enum):
    """查询意图枚举"""
    INFORMATIONAL = 'informational'     # 信息查询
    NAVIGATIONAL = 'navigational'       # 导航查询
    TRANSACTIONAL = 'transactional'     # 事务查询
    COMMERCIAL = 'commercial'           # 商业查询
    RESEARCH = 'research'               # 研究查询
    COMPARISON = 'comparison'           # 比较查询
    ANALYSIS = 'analysis'               # 分析查询
    VERIFICATION = 'verification'       # 验证查询
    PATENT = 'patent'                   # 专利查询


class DomainType(Enum):
    """领域类型枚举"""
    PATENT = 'patent'                   # 专利领域
    ACADEMIC = 'academic'               # 学术领域
    BUSINESS = 'business'               # 商业领域
    TECHNOLOGY = 'technology'           # 技术领域
    LEGAL = 'legal'                     # 法律领域
    MEDICAL = 'medical'                 # 医疗领域
    GENERAL = 'general'                 # 通用领域


@dataclass
class QueryAnalysis:
    """查询分析结果"""
    # 基本分析
    original_text: str
    normalized_text: str
    language: str
    complexity: QueryComplexity

    # 意图分析
    primary_intent: QueryIntent
    secondary_intents: list[QueryIntent]
    confidence: float

    # 领域识别
    primary_domain: DomainType
    secondary_domains: list[DomainType]
    domain_confidence: float

    # 关键词提取
    keywords: list[str]
    entities: list[str]
    technical_terms: list[str]

    # 时间信息
    temporal_indicators: list[str]
    time_sensitivity: bool

    # 地理信息
    geographic_indicators: list[str]
    geographic_scope: str

    # 质量要求
    precision_requirement: float  # 精度要求 0-1
    freshness_requirement: float  # 新鲜度要求 0-1
    completeness_requirement: float  # 完整性要求 0-1

    # 元数据
    analysis_time: datetime = field(default_factory=datetime.now)


@dataclass
class ToolRecommendation:
    """工具推荐结果"""
    tool_name: str
    match_score: float
    confidence: float
    reasoning: list[str]

    # 性能预测
    expected_response_time: float
    expected_success_rate: float
    expected_quality_score: float

    # 推荐策略
    recommendation_type: str  # primary, fallback, complementary
    priority: int  # 1-5, 5最高


@dataclass
class SelectionStrategy:
    """选择策略"""
    name: str
    description: str

    # 权重配置
    domain_match_weight: float = 0.3
    intent_match_weight: float = 0.25
    performance_weight: float = 0.2
    capability_weight: float = 0.15
    availability_weight: float = 0.1

    # 选择规则
    max_tools_per_query: int = 3
    min_confidence_threshold: float = 0.6
    require_fallback: bool = True
