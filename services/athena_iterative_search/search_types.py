#!/usr/bin/env python3
"""
Athena迭代式搜索系统数据类型定义
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

class SearchEngineType(Enum):
    """搜索引擎类型"""
    ELASTICSEARCH = 'elasticsearch'
    VECTOR_SEARCH = 'vector_search'
    EXTERNAL_SEARCH = 'external_search'
    KNOWLEDGE_GRAPH = 'knowledge_graph'
    CACHE_SEARCH = 'cache_search'

class PatentType(Enum):
    """专利类型"""
    INVENTION = '发明'
    UTILITY_MODEL = '实用新型'
    DESIGN = '外观设计'

class SearchStatus(Enum):
    """搜索状态"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class ResultRelevance(Enum):
    """结果相关性等级"""
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    UNKNOWN = 'unknown'

@dataclass
class PatentMetadata:
    """专利元数据"""
    patent_id: str
    patent_name: str
    patent_type: PatentType | None = None
    applicant: str | None = None
    inventor: str | None = None
    application_number: str | None = None
    application_date: datetime | None = None
    publication_number: str | None = None
    publication_date: datetime | None = None
    authorization_number: str | None = None
    authorization_date: datetime | None = None
    ipc_code: str | None = None
    ipc_main_class: str | None = None
    abstract: str | None = None
    claims_content: str | None = None
    current_assignee: str | None = None
    assignee_address: str | None = None
    source_year: int | None = None
    source_file: str | None = None

@dataclass
class SearchResult:
    """搜索结果基础类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ''
    content: str = ''
    url: str | None = None
    score: float = 0.0
    relevance: ResultRelevance = ResultRelevance.UNKNOWN
    engine_type: SearchEngineType = SearchEngineType.ELASTICSEARCH
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class PatentSearchResult(SearchResult):
    """专利搜索结果"""
    patent_metadata: PatentMetadata | None = None
    ipc_matches: List[str] = field(default_factory=list)
    applicant_matches: List[str] = field(default_factory=list)
    keyword_matches: List[str] = field(default_factory=list)
    similarity_score: float = 0.0  # 语义相似度分数
    text_match_score: float = 0.0   # 文本匹配分数
    combined_score: float = 0.0     # 综合分数

    def __post_init__(self):
        """初始化后处理"""
        if self.patent_metadata:
            self.title = self.patent_metadata.patent_name
            self.content = self.patent_metadata.abstract or ''
        # 计算综合分数
        self.combined_score = (
            self.text_match_score * 0.6 +
            self.similarity_score * 0.3 +
            self.score * 0.1
        )

@dataclass
class ExternalSearchResult(SearchResult):
    """外部搜索引擎结果"""
    source_engine: str = ''
    snippet: str = ''
    display_url: str | None = None
    last_updated: datetime | None = None

@dataclass
class SearchQuery:
    """搜索查询"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ''
    original_text: str = ''
    query_type: str = 'text'  # text, ipc, applicant, etc.
    filters: Dict[str, Any] = field(default_factory=dict)
    expansion_terms: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    similarity_to_previous: float = 1.0

@dataclass
class SearchIteration:
    """搜索迭代记录"""
    iteration_number: int
    query: SearchQuery
    results: List[PatentSearchResult]
    search_time: float
    total_results: int
    quality_score: float
    insights: List[str] = field(default_factory=list)
    next_query_suggestion: str | None = None

@dataclass
class ResearchSummary:
    """研究摘要"""
    topic: str = ''
    key_findings: List[str] = field(default_factory=list)
    main_patents: List[str] = field(default_factory=list)
    technological_trends: List[str] = field(default_factory=list)
    competing_applicants: List[str] = field(default_factory=list)
    innovation_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence_level: float = 0.0
    completeness_score: float = 0.0

@dataclass
class SearchSession:
    """搜索会话"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ''
    initial_query: str = ''
    strategy: str = 'hybrid'
    max_iterations: int = 3
    current_iteration: int = 0
    iterations: List[SearchIteration] = field(default_factory=list)
    research_summary: ResearchSummary | None = None
    status: SearchStatus = SearchStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    total_patents_found: int = 0
    unique_patents: int = 0
    search_config: Dict[str, Any] = field(default_factory=dict)

    def update_status(self, status: SearchStatus) -> None:
        """更新搜索状态"""
        self.status = status
        self.updated_at = datetime.now()

    def add_iteration(self, iteration: SearchIteration) -> None:
        """添加搜索迭代"""
        self.iterations.append(iteration)
        self.current_iteration = iteration.iteration_number
        self.updated_at = datetime.now()

@dataclass
class SearchStatistics:
    """搜索统计信息"""
    total_searches: int = 0
    successful_searches: int = 0
    failed_searches: int = 0
    average_response_time: float = 0.0
    average_results_per_search: float = 0.0
    most_common_queries: List[str] = field(default_factory=list)
    engine_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    patent_type_distribution: Dict[str, int] = field(default_factory=dict)
    ipc_distribution: Dict[str, int] = field(default_factory=dict)
    applicant_distribution: Dict[str, int] = field(default_factory=dict)

@dataclass
class SearchCache:
    """搜索缓存项"""
    query_hash: str
    results: List[PatentSearchResult]
    search_time: float
    total_results: int
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None
    hit_count: int = 0

@dataclass
class QueryExpansion:
    """查询扩展"""
    original_query: str
    expanded_terms: List[str]
    synonyms: List[str]
    related_concepts: List[str]
    ipc_suggestions: List[str]
    applicant_suggestions: List[str]
    expansion_method: str  # llm, thesaurus, embedding, etc.
    confidence: float = 0.0

@dataclass
class SearchFilter:
    """搜索过滤器"""
    field_name: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, contains, etc.
    value: Any
    case_sensitive: bool = False

@dataclass
class SearchError:
    """搜索错误信息"""
    error_code: str
    error_message: str
    engine_type: SearchEngineType | None = None
    query: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    stack_trace: str | None = None

# 类型别名
PatentResults = List[PatentSearchResult]
SearchResults = List[SearchResult]
ExternalResults = List[ExternalSearchResult]
SearchQueries = List[SearchQuery]
SearchFilters = List[SearchFilter]
SearchErrors = List[SearchError]

# 回调函数类型
from typing import Callable

SearchCallback = Callable[[SearchSession], None]
ProgressCallback = Callable[[int, int, str], None]  # current, total, message
ErrorCallback = Callable[[SearchError], None]

# 配置类型
EngineConfig = Dict[str, Any]
SearchConfig = Dict[str, Any]
FilterConfig = Dict[str, Any]