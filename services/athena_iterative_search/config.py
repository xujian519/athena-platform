#!/usr/bin/env python3
"""
Athena迭代式搜索系统配置文件
基于XiaoXi搜索架构，针对专利搜索优化
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SearchStrategy(Enum):
    """搜索策略枚举"""
    HYBRID = 'hybrid'           # 混合搜索（全文+向量+语义）
    FULLTEXT = 'fulltext'       # 全文搜索
    SEMANTIC = 'semantic'       # 语义搜索
    ITERATIVE = 'iterative'     # 迭代搜索
    EXTERNAL = 'external'       # 外部搜索引擎

class SearchDepth(Enum):
    """搜索深度级别"""
    BASIC = 'basic'             # 基础搜索（1轮）
    STANDARD = 'standard'       # 标准搜索（2-3轮）
    DEEP = 'deep'              # 深度搜索（3-5轮）
    COMPREHENSIVE = 'comprehensive'  # 全面搜索（5-7轮）

@dataclass
class EngineWeights:
    """搜索引擎权重配置"""
    elasticsearch_weight: float = 0.4    # Elasticsearch全文搜索
    vector_weight: float = 0.3           # 向量搜索
    external_weight: float = 0.3         # 外部搜索引擎

    def validate(self) -> Any:
        """验证权重总和为1"""
        total = self.elasticsearch_weight + self.vector_weight + self.external_weight
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"权重总和必须为1.0，当前为{total}")

@dataclass
class IterativeSearchConfig:
    """迭代搜索配置"""
    max_iterations: int = 3               # 最大迭代轮数
    top_k_per_iteration: int = 5          # 每轮返回结果数
    query_similarity_threshold: float = 0.7  # 查询相似度阈值
    result_diversity_weight: float = 0.3   # 结果多样性权重
    research_summary_length: int = 500     # 研究摘要长度
    enable_query_expansion: bool = True    # 启用查询扩展
    enable_result_clustering: bool = True  # 启用结果聚类

@dataclass
class PatentSearchConfig:
    """专利特定搜索配置"""
    # 专利字段权重
    title_weight: float = 0.3              # 专利标题权重
    abstract_weight: float = 0.25          # 摘要权重
    claims_weight: float = 0.2            # 权利要求权重
    ipc_weight: float = 0.15              # IPC分类号权重
    applicant_weight: float = 0.1         # 申请人权重

    # 专利搜索策略
    enable_ipc_search: bool = True         # 启用IPC分类搜索
    enable_applicant_filter: bool = True   # 启用申请人过滤
    enable_date_range_filter: bool = True  # 启用日期范围过滤
    enable_patent_type_filter: bool = True # 启用专利类型过滤

    # 中文分词配置
    use_jieba_segmentation: bool = True    # 使用jieba分词
    patent_dict_path: str | None = None # 专利词典路径
    enable_ipc_recognition: bool = True    # 启用IPC识别

@dataclass
class ExternalEnginesConfig:
    """外部搜索引擎配置"""
    enable_baidu: bool = True              # 启用百度搜索
    enable_bing: bool = True               # 启用Bing搜索
    enable_google: bool = False            # 启用Google搜索（需要代理）
    enable_sogou: bool = True              # 启用搜狗搜索

    # 请求限制
    max_requests_per_minute: int = 30      # 每分钟最大请求数
    request_timeout: int = 10              # 请求超时时间（秒）
    retry_attempts: int = 3                # 重试次数

    # 结果处理
    max_external_results: int = 20         # 外部搜索最大结果数
    external_result_threshold: float = 0.5 # 外部结果相关性阈值

@dataclass
class PerformanceConfig:
    """性能优化配置"""
    # 缓存配置
    enable_cache: bool = True              # 启用缓存
    cache_ttl: int = 3600                  # 缓存过期时间（秒）
    max_cache_size: int = 10000            # 最大缓存条目数

    # 并发配置
    max_concurrent_searches: int = 5       # 最大并发搜索数
    search_timeout: int = 30               # 搜索超时时间（秒）

    # 批处理配置
    batch_size: int = 100                  # 批处理大小
    enable_parallel_processing: bool = True # 启用并行处理

@dataclass
class AthenaSearchConfig:
    """Athena搜索系统主配置"""
    # 基础配置
    default_strategy: SearchStrategy = SearchStrategy.HYBRID
    default_depth: SearchDepth = SearchDepth.STANDARD

    # 子配置
    engine_weights: EngineWeights = field(default_factory=EngineWeights)
    iterative_config: IterativeSearchConfig = field(default_factory=IterativeSearchConfig)
    patent_config: PatentSearchConfig = field(default_factory=PatentSearchConfig)
    external_config: ExternalEnginesConfig = field(default_factory=ExternalEnginesConfig)
    performance_config: PerformanceConfig = field(default_factory=PerformanceConfig)

    # 调试配置
    enable_logging: bool = True
    log_level: str = 'INFO'
    debug_mode: bool = False

    def __post_init__(self):
        """配置验证和初始化"""
        self.engine_weights.validate()
        self._validate_config()

    def _validate_config(self) -> Any:
        """验证配置的合理性"""
        if self.iterative_config.max_iterations < 1:
            raise ValueError('最大迭代轮数必须大于0')

        if self.iterative_config.top_k_per_iteration < 1:
            raise ValueError('每轮结果数必须大于0')

        if self.performance_config.search_timeout < 1:
            raise ValueError('搜索超时时间必须大于0')

# 预定义配置模板
DEFAULT_CONFIG = AthenaSearchConfig()

HIGH_PERFORMANCE_CONFIG = AthenaSearchConfig(
    default_strategy=SearchStrategy.HYBRID,
    iterative_config=IterativeSearchConfig(
        max_iterations=2,
        top_k_per_iteration=10,
        enable_result_clustering=False
    ),
    performance_config=PerformanceConfig(
        max_concurrent_searches=10,
        search_timeout=15,
        batch_size=200
    )
)

COMPREHENSIVE_SEARCH_CONFIG = AthenaSearchConfig(
    default_strategy=SearchStrategy.ITERATIVE,
    default_depth=SearchDepth.DEEP,
    iterative_config=IterativeSearchConfig(
        max_iterations=5,
        top_k_per_iteration=8,
        query_similarity_threshold=0.8,
        result_diversity_weight=0.4
    ),
    patent_config=PatentSearchConfig(
        enable_ipc_search=True,
        enable_applicant_filter=True,
        enable_date_range_filter=True,
        enable_patent_type_filter=True
    )
)

PATENT_ANALYSIS_CONFIG = AthenaSearchConfig(
    default_strategy=SearchStrategy.ITERATIVE,
    default_depth=SearchDepth.COMPREHENSIVE,
    iterative_config=IterativeSearchConfig(
        max_iterations=7,
        top_k_per_iteration=5,
        research_summary_length=800,
        enable_query_expansion=True,
        enable_result_clustering=True
    ),
    patent_config=PatentSearchConfig(
        title_weight=0.25,
        abstract_weight=0.35,
        claims_weight=0.25,
        ipc_weight=0.1,
        applicant_weight=0.05
    ),
    external_config=ExternalEnginesConfig(
        max_external_results=50,
        external_result_threshold=0.6
    )
)
