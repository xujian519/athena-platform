#!/usr/bin/env python3
"""
生产环境配置
Production Environment Configuration

配置说明：
1. 生产数据库连接（PostgreSQL + Qdrant + NebulaGraph）
2. Redis缓存配置
3. 性能优化参数
4. 监控配置

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Production"
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Any

import yaml

# 生产环境数据库配置
PRODUCTION_DATABASE_CONFIG = {
    "postgresql": {
        "host": os.getenv("PG_HOST", "localhost"),
        "port": int(os.getenv("PG_PORT", "5432")),
        "database": os.getenv("PG_DATABASE", "athena_production"),
        "user": os.getenv("PG_USER", "athena_user"),
        "password": os.getenv("PG_PASSWORD"),
        "min_connections": 5,
        "max_connections": 20,
        "options": "-c statement_timeout=30s"
    },
    "qdrant": {
        "url": os.getenv("QDRANT_URL", "http://localhost:6333"),
        "collection_name": "patent_rules_production",
        "vector_size": 768,
        "distance": "Cosine"
    },
    "nebulagraph": {
        "hosts": os.getenv("NEBULA_HOSTS", "127.0.0.1").split(","),
        "port": int(os.getenv("NEBULA_PORT", "9669")),
        "username": os.getenv("NEBULA_USERNAME", "root"),
        "password": os.getenv("NEBULA_PASSWORD", "nebula"),
        "space": os.getenv("NEBULA_SPACE", "patent_kg_production"),
        "pool_size": 10
    },
    "redis": {
        "enabled": True,
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "db": int(os.getenv("REDIS_DB", "0")),
        "password": os.getenv("REDIS_PASSWORD"),
        "max_connections": 50,
        "socket_timeout": 2,
        "socket_connect_timeout": 2,
        "decode_responses": True
    }
}

# 性能优化配置
PERFORMANCE_CONFIG = {
    "cache": {
        "l1_enabled": True,
        "l1_size": 10000,  # 生产环境更大的L1缓存
        "l2_enabled": True,   # 生产环境启用L2 Redis
        "l2_ttl": 7200,       # 2小时TTL
        "max_memory": "512mb",
        "policy": "allkeys-lru"
    },
    "query": {
        "batch_size": 20,           # 批处理大小
        "max_wait_time": 0.05,       # 最大等待时间50ms
        "parallel_queries": 10,      # 最大并行查询数
        "timeout": 30                # 查询超时30秒
    },
    "connection": {
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 3600
    }
}

# 监控配置
MONITORING_CONFIG = {
    "prometheus": {
        "enabled": True,
        "host": "localhost",
        "port": 9090,
        "metrics_path": "/metrics"
    },
    "grafana": {
        "enabled": True,
        "host": "localhost",
        "port": 3000,
        "dashboards": [
            "athena_overview",
            "query_performance",
            "cache_statistics",
            "database_health"
        ]
    },
    "logging": {
        "level": "INFO",
        "format": "json",
        "output": "/var/log/athena/production.log"
    }
}

# 生产环境向量索引配置
VECTOR_INDEX_CONFIG = {
    "pgvector": {
        "enabled": True,
        "index_type": "ivfflat",
        "lists": 100,  # IVFFlat列表数
        "probes": 10   # 搜索探针数
    },
    "qdrant": {
        "enabled": True,
        "payload_index": True,
        "optimizers_config": {
            "indexing_threshold": 20000
        }
    }
}

# 导出配置
__all__ = [
    'PRODUCTION_DATABASE_CONFIG',
    'PERFORMANCE_CONFIG',
    'MONITORING_CONFIG',
    'VECTOR_INDEX_CONFIG'
]


def save_production_config(output_dir: str = "config/production") -> None:
    """保存生产环境配置到文件"""
    config_dir = Path(output_dir)
    config_dir.mkdir(parents=True, exist_ok=True)

    # 保存为YAML
    config_file = config_dir / "production_config.yaml"
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump({
            'database': PRODUCTION_DATABASE_CONFIG,
            'performance': PERFORMANCE_CONFIG,
            'monitoring': MONITORING_CONFIG,
            'vector_index': VECTOR_INDEX_CONFIG
        }, f, allow_unicode=True, default_flow_style=False)

    print(f"✅ 生产环境配置已保存到: {config_file}")
    return config_file


def load_production_config(config_file: str = "config/production/production_config.yaml") -> dict[str, Any]:
    """从文件加载生产环境配置"""
    config_path = Path(config_file)

    if not config_path.exists():
        print("⚠️ 配置文件不存在，使用默认配置")
        return {
            'database': PRODUCTION_DATABASE_CONFIG,
            'performance': PERFORMANCE_CONFIG,
            'monitoring': MONITORING_CONFIG,
            'vector_index': VECTOR_INDEX_CONFIG
        }

    with open(config_path, encoding='utf-8') as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    print("🏭 生产环境配置")
    print("="*70)

    # 保存配置
    config_file = save_production_config()

    print("\n📋 配置摘要:")
    print(f"  PostgreSQL: {PRODUCTION_DATABASE_CONFIG['postgresql']['host']}:{PRODUCTION_DATABASE_CONFIG['postgresql']['port']}")
    print(f"  Qdrant: {PRODUCTION_DATABASE_CONFIG['qdrant']['url']}")
    print(f"  NebulaGraph: {PRODUCTION_DATABASE_CONFIG['nebulagraph']['hosts'][0]}:{PRODUCTION_DATABASE_CONFIG['nebulagraph']['port']}")
    print(f"  Redis: {PRODUCTION_DATABASE_CONFIG['redis']['host']}:{PRODUCTION_DATABASE_CONFIG['redis']['port']} (启用: {PRODUCTION_DATABASE_CONFIG['redis']['enabled']})")
    print(f"  L1缓存: {PERFORMANCE_CONFIG['cache']['l1_size']} 条目")
    print(f"  L2缓存: TTL {PERFORMANCE_CONFIG['cache']['l2_ttl']}秒 (启用: {PERFORMANCE_CONFIG['cache']['l2_enabled']})")

    print("\n💡 环境变量示例:")
    print("  export PG_HOST=localhost")
    print("  export PG_DATABASE=athena_production")
    print("  export PG_USER=athena_user")
    print("  export PG_PASSWORD=your_password")
    print("  export REDIS_HOST=localhost")
    print("  export REDIS_PORT=6379")
