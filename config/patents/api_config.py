
#!/usr/bin/env python3
"""
专利检索API配置
Patent Search API Configuration
"""

API_CONFIG = {
    'host': '0.0.0.0',
    'port': 8017,
    'debug': False,
    'reload': False,
    'log_level': 'info',
    'access_log': True,
    'workers': 1
}

DATABASE_CONFIG = {
    'results_db_path': 'data/patents/results/patents.db',
    'tasks_db_path': 'data/patents/tasks/tasks.db',
    'cache_db_path': 'data/patents/cache/cache.db'
}

SECURITY_CONFIG = {
    'cors_origins': ['*'],
    'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE'],
    'rate_limiting': {
        'enabled': True,
        'requests_per_minute': 60,
        'burst_size': 10
    }
}
