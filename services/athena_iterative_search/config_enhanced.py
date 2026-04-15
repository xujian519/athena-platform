#!/usr/bin/env python3
"""
Athena迭代式搜索系统增强配置文件
包含Qwen LLM集成和完整的外部搜索引擎配置
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .config import (
    AthenaSearchConfig,
    IterativeSearchConfig,
    PerformanceConfig,
    SearchDepth,
    SearchStrategy,
    logger,
)


class LLMProvider(Enum):
    """LLM提供商"""
    QWEN = 'qwen'
    MOCK = 'mock'

@dataclass
class LLMConfig:
    """LLM配置"""
    provider: LLMProvider = LLMProvider.QWEN
    api_key: str | None = None          # API密钥，从环境变量获取
    base_url: str = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    model_name: str = 'qwen-turbo'        # 模型名称
    timeout: int = 60                      # 超时时间（秒）
    max_tokens: int = 2000                 # 最大token数
    temperature: float = 0.7               # 温度参数
    cache_ttl: int = 3600                  # 缓存时间（秒）

    def __post_init__(self):
        """初始化后处理"""
        if self.api_key is None:
            # 从环境变量获取API密钥
            self.api_key = os.getenv('QWEN_API_KEY') or os.getenv('DASHSCOPE_API_KEY')

@dataclass
class ExternalEnginesConfig:
    """外部搜索引擎配置"""
    # 百度搜索配置
    baidu: dict[str, Any] = field(default_factory=lambda: {
        'enabled': False,
        'api_key': os.getenv('BAIDU_API_KEY', ''),
        'api_secret': os.getenv('BAIDU_API_SECRET', ''),
        'rate_limit': 5,
        'base_url': 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/plugin'
    })

    # Bing搜索配置
    bing: dict[str, Any] = field(default_factory=lambda: {
        'enabled': False,
        'api_key': os.getenv('BING_API_KEY', ''),
        'rate_limit': 10,
        'base_url': 'https://api.bing.microsoft.com/v7.0/search'
    })

    # 搜狗搜索配置
    sogou: dict[str, Any] = field(default_factory=lambda: {
        'enabled': False,
        'api_key': os.getenv('SOGOU_API_KEY', ''),
        'rate_limit': 5,
        'base_url': 'https://api.sogou.com/sss'
    })

    # Google专利搜索配置（无需API密钥）
    google_patents: dict[str, Any] = field(default_factory=lambda: {
        'enabled': True,
        'rate_limit': 2,
        'base_url': 'https://patents.google.com'
    })

    def get_enabled_engines(self) -> list[str]:
        """获取启用的搜索引擎列表"""
        enabled = []
        if self.google_patents.get('enabled', False):
            enabled.append('google_patents')
        if self.baidu.get('enabled', False) and self.baidu.get('api_key'):
            enabled.append('baidu')
        if self.bing.get('enabled', False) and self.bing.get('api_key'):
            enabled.append('bing')
        if self.sogou.get('enabled', False) and self.sogou.get('api_key'):
            enabled.append('sogou')
        return enabled

@dataclass
class VectorSearchConfig:
    """向量搜索配置"""
    # 向量模型配置
    model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
    embedding_dim: int = 384                 # 向量维度
    batch_size: int = 32                     # 批处理大小
    max_length: int = 512                    # 最大序列长度

    # 相似度搜索配置
    similarity_threshold: float = 0.7        # 相似度阈值
    max_candidates: int = 100                # 最大候选数
    rerank_top_k: int = 20                   # 重排数量

    # 向量存储配置
    index_type: str = 'ivf_flat'             # 索引类型
    nlist: int = 100                         # IVF索引聚类数
    nprobe: int = 10                         # 搜索时的聚类数

@dataclass
class CacheConfig:
    """增强缓存配置"""
    # 查询缓存
    query_cache_ttl: int = 7200              # 查询缓存2小时
    query_cache_size: int = 5000             # 查询缓存大小

    # 结果缓存
    result_cache_ttl: int = 3600             # 结果缓存1小时
    result_cache_size: int = 10000           # 结果缓存大小

    # LLM缓存
    llm_cache_ttl: int = 86400               # LLM缓存24小时
    llm_cache_size: int = 1000               # LLM缓存大小

    # 向量缓存
    vector_cache_ttl: int = 604800           # 向量缓存7天
    vector_cache_size: int = 50000           # 向量缓存大小

@dataclass
class EnhancedPerformanceConfig:
    """增强性能配置"""
    # 基础性能配置
    base_config: PerformanceConfig = field(default_factory=PerformanceConfig)

    # 并发配置
    max_concurrent_llm_requests: int = 3     # 最大并发LLM请求数
    max_concurrent_external_searches: int = 2  # 最大并发外部搜索

    # 连接池配置
    http_connections: int = 20               # HTTP连接池大小
    redis_connections: int = 10              # Redis连接池大小

    # 队列配置
    search_queue_size: int = 100             # 搜索队列大小
    result_queue_size: int = 200             # 结果队列大小

@dataclass
class AthenaEnhancedSearchConfig(AthenaSearchConfig):
    """Athena增强搜索配置"""
    # 增强配置
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    external_engines: ExternalEnginesConfig = field(default_factory=ExternalEnginesConfig)
    vector_config: VectorSearchConfig = field(default_factory=VectorSearchConfig)
    cache_config: CacheConfig = field(default_factory=CacheConfig)
    enhanced_performance: EnhancedPerformanceConfig = field(default_factory=EnhancedPerformanceConfig)

    def __post_init__(self):
        """配置验证和初始化"""
        super().__post_init__()
        self._validate_enhanced_config()

    def _validate_enhanced_config(self):
        """验证增强配置"""
        # 验证LLM配置
        if self.llm_config.provider == LLMProvider.QWEN and not self.llm_config.api_key:
            logger.info('⚠️  Qwen API密钥未配置，将使用Mock模式')
            self.llm_config.provider = LLMProvider.MOCK

        # 验证向量配置
        if self.vector_config.embedding_dim <= 0:
            raise ValueError('向量维度必须大于0')

        # 验证缓存配置
        if self.cache_config.query_cache_size <= 0:
            raise ValueError('查询缓存大小必须大于0')

        # 验证性能配置
        if self.enhanced_performance.max_concurrent_llm_requests <= 0:
            raise ValueError('最大并发LLM请求数必须大于0')

    def get_external_engines_config(self) -> dict[str, Any]:
        """获取外部搜索引擎配置"""
        return {
            'external_engines': {
                'baidu': self.external_engines.baidu,
                'bing': self.external_engines.bing,
                'sogou': self.external_engines.sogou,
                'google_patents': self.external_engines.google_patents
            }
        }

    def get_llm_config(self) -> dict[str, Any]:
        """获取LLM配置"""
        return {
            'provider': self.llm_config.provider.value,
            'api_key': self.llm_config.api_key,
            'base_url': self.llm_config.base_url,
            'model_name': self.llm_config.model_name,
            'timeout': self.llm_config.timeout,
            'max_tokens': self.llm_config.max_tokens,
            'temperature': self.llm_config.temperature,
            'cache_ttl': self.llm_config.cache_ttl
        }

# 环境检测
def detect_environment() -> str:
    """检测运行环境"""
    if os.getenv('ATHENA_ENV') == 'production':
        return 'production'
    elif os.getenv('ATHENA_ENV') == 'development':
        return 'development'
    else:
        return 'default'

# 预定义增强配置模板

# 默认配置（使用Mock LLM）
ENHANCED_DEFAULT_CONFIG = AthenaEnhancedSearchConfig(
    llm_config=LLMConfig(provider=LLMProvider.MOCK),
    external_engines=ExternalEnginesConfig(
        google_patents={'enabled': True}
    )
)

# 开发环境配置
DEVELOPMENT_CONFIG = AthenaEnhancedSearchConfig(
    default_strategy=SearchStrategy.HYBRID,
    default_depth=SearchDepth.STANDARD,
    llm_config=LLMConfig(
        provider=LLMProvider.QWEN,
        model_name='qwen-turbo',
        temperature=0.8
    ),
    external_engines=ExternalEnginesConfig(
        google_patents={'enabled': True},
        baidu={'enabled': False},
        bing={'enabled': False},
        sogou={'enabled': False}
    ),
    vector_config=VectorSearchConfig(
        similarity_threshold=0.6,
        max_candidates=50
    ),
    enhanced_performance=EnhancedPerformanceConfig(
        max_concurrent_llm_requests=2,
        max_concurrent_external_searches=1
    )
)

# 生产环境配置
PRODUCTION_CONFIG = AthenaEnhancedSearchConfig(
    default_strategy=SearchStrategy.HYBRID,
    default_depth=SearchDepth.DEEP,
    llm_config=LLMConfig(
        provider=LLMProvider.QWEN,
        model_name='qwen-plus',
        temperature=0.5,
        max_tokens=3000,
        cache_ttl=7200
    ),
    external_engines=ExternalEnginesConfig(
        google_patents={'enabled': True, 'rate_limit': 5},
        baidu={'enabled': True, 'rate_limit': 3},
        bing={'enabled': True, 'rate_limit': 8},
        sogou={'enabled': False}
    ),
    vector_config=VectorSearchConfig(
        model_name='sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
        embedding_dim=768,
        similarity_threshold=0.75,
        max_candidates=200
    ),
    cache_config=CacheConfig(
        query_cache_ttl=14400,    # 4小时
        result_cache_ttl=7200,    # 2小时
        llm_cache_ttl=86400,      # 24小时
        vector_cache_ttl=1209600  # 2周
    ),
    enhanced_performance=EnhancedPerformanceConfig(
        max_concurrent_llm_requests=5,
        max_concurrent_external_searches=3,
        http_connections=50,
        redis_connections=20
    )
)

# 高性能配置
HIGH_PERFORMANCE_ENHANCED_CONFIG = AthenaEnhancedSearchConfig(
    default_strategy=SearchStrategy.HYBRID,
    default_depth=SearchDepth.STANDARD,
    iterative_config=IterativeSearchConfig(
        max_iterations=2,
        top_k_per_iteration=15,
        enable_result_clustering=False
    ),
    llm_config=LLMConfig(
        provider=LLMProvider.QWEN,
        model_name='qwen-turbo',
        temperature=0.3,
        timeout=30
    ),
    vector_config=VectorSearchConfig(
        similarity_threshold=0.8,
        max_candidates=50,
        batch_size=64
    ),
    cache_config=CacheConfig(
        query_cache_ttl=3600,
        result_cache_ttl=1800,
        query_cache_size=10000,
        result_cache_size=20000
    ),
    enhanced_performance=EnhancedPerformanceConfig(
        base_config=PerformanceConfig(
            max_concurrent_searches=10,
            search_timeout=15,
            batch_size=200
        ),
        max_concurrent_llm_requests=8,
        max_concurrent_external_searches=4,
        http_connections=100
    )
)

# 综合分析配置
COMPREHENSIVE_ANALYSIS_CONFIG = AthenaEnhancedSearchConfig(
    default_strategy=SearchStrategy.HYBRID,
    default_depth=SearchDepth.COMPREHENSIVE,
    iterative_config=IterativeSearchConfig(
        max_iterations=7,
        top_k_per_iteration=10,
        query_similarity_threshold=0.6,
        research_summary_length=1000
    ),
    llm_config=LLMConfig(
        provider=LLMProvider.QWEN,
        model_name='qwen-plus',
        temperature=0.6,
        max_tokens=4000,
        cache_ttl=7200
    ),
    external_engines=ExternalEnginesConfig(
        google_patents={'enabled': True, 'rate_limit': 3},
        baidu={'enabled': True, 'rate_limit': 2},
        bing={'enabled': True, 'rate_limit': 5}
    ),
    vector_config=VectorSearchConfig(
        embedding_dim=768,
        similarity_threshold=0.65,
        max_candidates=150,
        rerank_top_k=50
    )
)

def get_config_by_environment(env: str | None = None) -> AthenaEnhancedSearchConfig:
    """根据环境获取配置"""
    if env is None:
        env = detect_environment()

    config_map = {
        'development': DEVELOPMENT_CONFIG,
        'production': PRODUCTION_CONFIG,
        'default': ENHANCED_DEFAULT_CONFIG
    }

    return config_map.get(env, ENHANCED_DEFAULT_CONFIG)

def create_custom_config(
    llm_provider: str = 'mock',
    enable_external_search: bool = False,
    enable_vector_search: bool = True,
    **kwargs
) -> AthenaEnhancedSearchConfig:
    """创建自定义配置"""
    llm_config = LLMConfig(
        provider=LLMProvider(llm_provider.lower())
    )

    external_engines = ExternalEnginesConfig()
    if enable_external_search:
        external_engines.google_patents['enabled'] = True

    vector_config = VectorSearchConfig() if enable_vector_search else None

    return AthenaEnhancedSearchConfig(
        llm_config=llm_config,
        external_engines=external_engines,
        vector_config=vector_config,
        **kwargs
    )

# 导出所有配置
__all__ = [
    'LLMProvider', 'LLMConfig', 'ExternalEnginesConfig', 'VectorSearchConfig',
    'CacheConfig', 'EnhancedPerformanceConfig', 'AthenaEnhancedSearchConfig',
    'ENHANCED_DEFAULT_CONFIG', 'DEVELOPMENT_CONFIG', 'PRODUCTION_CONFIG',
    'HIGH_PERFORMANCE_ENHANCED_CONFIG', 'COMPREHENSIVE_ANALYSIS_CONFIG',
    'get_config_by_environment', 'create_custom_config'
]
