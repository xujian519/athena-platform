#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Athena工作平台核心服务状态
"""

import json
import logging
import subprocess
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

def check_service(name, url, expected_status=200):
    """检查HTTP服务状态"""
    try:
        response = requests.get(url, timeout=5)
        status = '✅ 运行正常' if response.status_code == expected_status else f"❌ 状态码: {response.status_code}"
        return {
            'name': name,
            'url': url,
            'status': status,
            'response_time': response.elapsed.total_seconds()
        }
    except Exception as e:
        return {
            'name': name,
            'url': url,
            'status': f"❌ 连接失败: {str(e)}",
            'response_time': None
        }

def check_database_service(name, command):
    """检查数据库服务"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return {'name': name, 'status': '✅ 运行正常', 'details': result.stdout.strip()}
        else:
            return {'name': name, 'status': f"❌ 错误: {result.stderr.strip()}', 'details": None}
    except Exception as e:
        return {'name': name, 'status': f"❌ 检查失败: {str(e)}', 'details": None}

def main():
    """主函数"""
    logger.info(str('=' * 60))
    logger.info('Athena工作平台核心服务状态检查')
    logger.info(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(str('=' * 60))

    services = []

    # 1. 检查Neo4j
    logger.info("\n🔍 检查Neo4j服务...")
    neo4j_http = check_service('Neo4j HTTP', 'http://localhost:7474')
    neo4j_db = check_database_service('Neo4j 数据库', 'curl -s http://localhost:7474/db/data/')
    services.extend([neo4j_http, neo4j_db])

    # 2. 检查PostgreSQL
    logger.info("\n🔍 检查PostgreSQL服务...")
    pg_status = check_database_service('PostgreSQL', 'pg_isready -h localhost -p 5432')
    services.append(pg_status)

    # 3. 检查Redis
    logger.info("\n🔍 检查Redis服务...")
    redis_status = check_database_service('Redis', 'redis-cli ping')
    services.append(redis_status)

    # 4. 检查Qdrant
    logger.info("\n🔍 检查Qdrant向量数据库...")
    qdrant_health = check_service('Qdrant Health', 'http://localhost:6333/health')
    qdrant_collections = check_service('Qdrant Collections', 'http://localhost:6333/collections')
    services.extend([qdrant_health, qdrant_collections])

    # 5. 检查知识图谱API
    logger.info("\n🔍 检查知识图谱API服务...")
    kg_api = check_service('知识图谱API', 'http://localhost:8001/docs', expected_status=200)
    services.append(kg_api)

    # 6. 检查向量知识服务
    logger.info("\n🔍 检查向量知识服务...")
    vector_api = check_service('向量知识API', 'http://localhost:8002/docs', expected_status=200)
    services.append(vector_api)

    # 7. 检查Docker容器状态
    logger.info("\n🔍 检查Docker容器...")
    try:
        result = subprocess.run("docker ps --format 'table {{.Names}}\t{{.Status}}'",
                               shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("\n📦 Docker容器状态:")
            logger.info(str(result.stdout))
    except Exception as e:
        logger.info(f"\n❌ Docker检查失败: {e}")

    # 生成报告
    logger.info(str("\n" + '=' * 60))
    logger.info('服务状态汇总:')
    logger.info(str('=' * 60))

    running = 0
    total = len(services)

    for service in services:
        status_icon = '✅' if '运行正常' in service['status'] else '❌'
        logger.info(f"{status_icon} {service['name']:<20} - {service['status']}")
        if '运行正常' in service['status']:
            running += 1

    logger.info(str("\n" + '-' * 60))
    logger.info(f"总计: {running}/{total} 服务正常运行")

    # 保存报告
    report = {
        'check_time': datetime.now().isoformat(),
        'services': services,
        'summary': {
            'total': total,
            'running': running,
            'failed': total - running
        }
    }

    report_file = 'logs/core_services_status.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"\n📄 详细报告已保存到: {report_file}")

    if running == total:
        logger.info("\n🎉 所有核心服务运行正常！")
    else:
        logger.info(f"\n⚠️  {total - running} 个服务需要关注")

if __name__ == '__main__':
    main()