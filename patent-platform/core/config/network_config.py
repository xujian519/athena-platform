import logging

logger = logging.getLogger(__name__)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利检索网络配置
Patent Search Network Configuration

网络访问配置和优化参数

作者: 小诺 (Athena AI助手)
创建时间: 2025-12-08
"""

# 基础网络配置
NETWORK_CONFIG = {
    'base_urls': {
        'google_patents': 'https://patents.google.com',
        'google_patents_search': 'https://patents.google.com/xhr/query',
        'google_patents_suggest': 'https://patents.google.com/xhr/suggest',

        # 备用数据源
        'uspto': 'https://patft.uspto.gov',
        'epo': 'https://worldwide.espacenet.com',
        'wipo': 'https://patentscope.wipo.int'
    },

    # 请求延迟配置（秒）
    'delays': {
        'conservative': {'min': 5.0, 'max': 10.0, 'base': 7.0},  # 保守模式
        'standard': {'min': 2.0, 'max': 5.0, 'base': 3.0},       # 标准模式
        'aggressive': {'min': 1.0, 'max': 3.0, 'base': 2.0}     # 激进模式
    },

    # 重试配置
    'retry': {
        'max_attempts': 3,
        'backoff_factor': 2,
        'retry_on_status': [400, 429, 500, 502, 503, 504],
        'max_wait_time': 60
    },

    # 超时配置
    'timeout': {
        'connect': 10,
        'read': 30,
        'total': 60
    },

    # User-Agent池
    'user_agents': [
        # 最新版Chrome (Mac)
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',

        # 最新版Chrome (Windows)
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',

        # Firefox (Mac)
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',

        # Safari (Mac)
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',

        # Edge (Windows)
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
    ],

    # 请求头模板
    'request_headers': {
        'chrome': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        },
        'firefox': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    }
}

# 数据源配置
DATA_SOURCES = {
    'google_patents': {
        'enabled': True,
        'priority': 1,
        'weight': 0.6,
        'url_pattern': 'https://patents.google.com/?q={query}&oq={query}',
        'api_endpoint': 'https://patents.google.com/xhr/query',
        'rate_limit': 3.0,  # 每秒最多请求数
        'selector_config': {
            'result_items': ['div.search-result-item', "a[href*='/patent/']"],
            'title': ['h3', 'h2', 'a.search-result-title'],
            'number': ['span.search-result-number', 'span.application-number'],
            'abstract': ['div.abstract', 'p.search-result-abstract'],
            'date': ['span.search-result-date', 'time']
        }
    },

    'google_patents_api': {
        'enabled': True,
        'priority': 2,
        'weight': 0.4,
        'endpoint': 'https://patents.google.com/xhr/query',
        'method': 'GET',
        'rate_limit': 2.0,
        'parameters': {
            'text': '{query}',
            'num': '{limit}',
            'type': 'PATENT',
            'country': 'US'
        }
    }
}

# 缓存配置
CACHE_CONFIG = {
    'enabled': True,
    'ttl': 3600,  # 1小时
    'max_size': 1000,
    'storage_type': 'memory'  # memory, redis, file
}

# 代理配置（如果需要）
PROXY_CONFIG = {
    'enabled': False,
    'proxies': [
        # {"http": "http://proxy1:port", "https": "https://proxy1:port"},
        # {"http": "http://proxy2:port", "https": "https://proxy2:port"}
    ],
    'rotation': 'round_robin'  # round_robin, random, weighted
}

# 搜索优化配置
SEARCH_OPTIMIZATION = {
    'max_results_per_source': 20,
    'max_total_results': 50,
    'similarity_threshold': 0.7,
    'result_merging': {
        'strategy': 'score_based',  # score_based, source_priority, time_based
        'boost_recent': True,
        'boost_source': {'google_patents_api': 1.2, 'google_patents': 1.0}
    }
}

# 日志配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_handler': {
        'enabled': False,
        'filename': 'patent_search.log',
        'max_bytes': 10 * 1024 * 1024,  # 10MB
        'backup_count': 3
    }
}

def get_config(mode: str = 'standard') -> dict:
    """
    根据模式获取配置

    Args:
        mode: 运行模式 (conservative, standard, aggressive)

    Returns:
        配置字典
    """
    config = {
        'network': NETWORK_CONFIG.copy(),
        'data_sources': DATA_SOURCES.copy(),
        'cache': CACHE_CONFIG.copy(),
        'proxy': PROXY_CONFIG.copy(),
        'search': SEARCH_OPTIMIZATION.copy(),
        'logging': LOGGING_CONFIG.copy()
    }

    # 根据模式调整延迟设置
    if mode in NETWORK_CONFIG['delays']:
        config['network']['delays'] = NETWORK_CONFIG['delays'][mode]

    return config

# 使用示例
if __name__ == '__main__':
    # 获取标准配置
    standard_config = get_config('standard')
    logger.info('标准配置:')
    logger.info(f"延迟设置: {standard_config['network']['delays']}")

    # 获取保守配置
    conservative_config = get_config('conservative')
    logger.info("\\n保守配置:")
    logger.info(f"延迟设置: {conservative_config['network']['delays']}")
