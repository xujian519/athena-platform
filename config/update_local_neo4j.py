#!/usr/bin/env python3
"""
更新配置以使用本地Neo4j
"""

import json
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

def update_configs() -> None:
    """更新配置文件以使用本地Neo4j"""
    project_root = Path('/Users/xujian/Athena工作平台')
    config_dir = project_root / 'config'

    # Neo4j本地配置
    neo4j_config = {
        'neo4j': {
            'type': 'graph_db',
            'uri': 'bolt://localhost:7687',
            'user': 'neo4j',
            'password': 'neo4j',
            'database': 'neo4j',
            'connection_type': 'local',  # 标记为本地连接
            'host': 'localhost',
            'http_port': 7474,
            'bolt_port': 7687
        }
    }

    # 更新统一数据库配置
    unified_config_path = config_dir / 'database_unified.yaml'
    if unified_config_path.exists():
        with open(unified_config_path, encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 更新Neo4j配置
        if 'databases' in config:
            config['databases']['neo4j'] = neo4j_config['neo4j']

        # 更新环境变量
        if 'environment_variables' in config:
            config['environment_variables'].update({
                'NEO4J_URI': 'bolt://localhost:7687',
                'NEO4J_USER': 'neo4j',
                'NEO4J_PASSWORD': 'neo4j',
                'NEO4J_HTTP_PORT': '7474',
                'NEO4J_BOLT_PORT': '7687'
            })

        # 保存配置
        with open(unified_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        logger.info('✅ 已更新 database_unified.yaml')

    # 创建Neo4j专用配置文件
    neo4j_config_path = config_dir / 'neo4j_local.yaml'
    neo4j_full_config = {
        'connection': neo4j_config['neo4j'],
        'settings': {
            'auto_index': True,
            'default_constraints': True,
            'keep_logical_logs': '1000 MB',
            'max_concurrent_queries': 1000,
            'query_timeout': '60s'
        },
        'backup': {
            'enabled': True,
            'path': '/Users/xujian/Athena工作平台/data/neo4j/backup',
            'schedule': '0 2 * * *'
        },
        'scripts': {
            'init_path': '/Users/xujian/Athena工作平台/database/neo4j/init',
            'migrations_path': '/Users/xujian/Athena工作平台/database/neo4j/migrations'
        }
    }

    with open(neo4j_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(neo4j_full_config, f, default_flow_style=False, allow_unicode=True)

    logger.info('✅ 已创建 neo4j_local.yaml')

    # 创建服务发现配置
    service_discovery = {
        'services': {
            'neo4j': {
                'type': 'local',
                'host': 'localhost',
                'ports': {
                    'http': 7474,
                    'bolt': 7687
                },
                'health_check': {
                    'url': 'http://localhost:7474',
                    'method': 'GET'
                },
                'management': {
                    'command': 'neo4j',
                    'start': 'neo4j start',
                    'stop': 'neo4j stop',
                    'restart': 'neo4j restart',
                    'status': 'neo4j status'
                }
            },
            'docker_services': {
                'postgres': {
                    'type': 'docker',
                    'container': 'athena_postgres',
                    'host': 'localhost',
                    'port': 5432
                },
                'redis': {
                    'type': 'docker',
                    'container': 'athena_redis',
                    'host': 'localhost',
                    'port': 6379
                },
                'qdrant': {
                    'type': 'docker',
                    'container': 'athena_qdrant',
                    'host': 'localhost',
                    'port': 6333
                }
            }
        }
    }

    service_discovery_path = config_dir / 'service_discovery.json'
    with open(service_discovery_path, 'w', encoding='utf-8') as f:
        json.dump(service_discovery, f, indent=2, ensure_ascii=False)

    logger.info('✅ 已创建 service_discovery.json')

    # 更新环境变量文件
    env_file = project_root / '.env'
    if env_file.exists():
        # 读取现有环境变量
        env_vars = {}
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key] = value

        # 添加或更新Neo4j配置
        env_vars.update({
            'NEO4J_URI': 'bolt://localhost:7687',
            'NEO4J_USER': 'neo4j',
            'NEO4J_PASSWORD': 'neo4j',
            'NEO4J_HTTP_PORT': '7474',
            'NEO4J_BOLT_PORT': '7687'
        })

        # 写回文件
        with open(env_file, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

        logger.info('✅ 已更新 .env 文件')

    logger.info("\n🎉 配置更新完成！")
    logger.info("\n📝 配置说明：")
    logger.info('  - Neo4j 使用本地安装版本（brew）')
    logger.info('  - 其他服务（PostgreSQL、Redis、Qdrant）使用Docker')
    logger.info('  - 所有配置已同步更新')

if __name__ == '__main__':
    update_configs()
