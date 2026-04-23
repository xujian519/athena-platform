#!/usr/bin/env python3
"""
Athena平台健康检查脚本
Health Check Script for Athena Platform

功能:
- 检查所有核心服务状态
- 提供详细的诊断信息
- 生成健康报告
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Any

import requests

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.project_root = project_root
        self.results = {}

    async def check_all(self) -> dict[str, Any]:
        """执行所有健康检查"""
        logger.info("=" * 60)
        logger.info("🏥 Athena平台健康检查")
        logger.info("=" * 60)

        start_time = time.time()

        checks = {
            "Redis": self._check_redis,
            "PostgreSQL": self._check_postgresql,
            "Neo4j": self._check_neo4j,
            "Qdrant": self._check_qdrant,
            "Gateway": self._check_gateway,
            "Xiaonuo": self._check_xiaonuo,
        }

        results = {}
        healthy_count = 0

        for name, check_func in checks.items():
            logger.info(f"检查 {name}...")
            try:
                is_healthy = await check_func()
                results[name] = {
                    "status": "✅ 健康" if is_healthy else "❌ 异常",
                    "healthy": is_healthy
                }
                if is_healthy:
                    healthy_count += 1
            except Exception as e:
                logger.error(f"❌ {name}检查失败: {e}")
                results[name] = {
                    "status": f"❌ 错误: {str(e)[:50]}",
                    "healthy": False
                }

        end_time = time.time()

        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_time": round(end_time - start_time, 2),
            "healthy_count": healthy_count,
            "total_count": len(checks),
            "health_percentage": round(healthy_count / len(checks) * 100, 1),
            "details": results
        }

        self._print_report(report)

        return report

    async def _check_redis(self) -> bool:
        """检查Redis"""
        try:
            import redis
            # 使用docker-compose.yml中配置的密码
            client = redis.Redis(
                host='localhost',
                port=6379,
                password='redis123',  # docker-compose.yml中配置的默认密码
                decode_responses=True
            )
            result = client.ping()
            if result:
                logger.info("  ✅ Redis连接正常")
                return True
            return False
        except Exception as e:
            logger.error(f"  ❌ Redis检查失败: {e}")
            return False

    async def _check_postgresql(self) -> bool:
        """检查PostgreSQL"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="postgres",
                password="athena_dev_password_2024_secure",
                database="postgres",
                connect_timeout=5
            )
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            cur.close()
            conn.close()
            logger.info(f"  ✅ PostgreSQL连接正常 ({version.split(',')[0]})")
            return True
        except Exception as e:
            logger.error(f"  ❌ PostgreSQL检查失败: {e}")
            return False

    async def _check_neo4j(self) -> bool:
        """检查Neo4j"""
        try:
            response = requests.get("http://localhost:7474", timeout=5)
            if response.status_code == 200:
                logger.info("  ✅ Neo4j连接正常")
                return True
            logger.error(f"  ❌ Neo4j返回错误状态码: {response.status_code}")
            return False
        except Exception as e:
            logger.error(f"  ❌ Neo4j检查失败: {e}")
            return False

    async def _check_qdrant(self) -> bool:
        """检查Qdrant"""
        try:
            response = requests.get("http://localhost:6333", timeout=5)
            if response.status_code == 200:
                logger.info("  ✅ Qdrant连接正常")
                return True
            logger.error(f"  ❌ Qdrant返回错误状态码: {response.status_code}")
            return False
        except Exception as e:
            logger.error(f"  ❌ Qdrant检查失败: {e}")
            return False

    async def _check_gateway(self) -> bool:
        """检查Gateway"""
        try:
            response = requests.get("http://localhost:8005/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"  ✅ Gateway连接正常 (状态: {data.get('status', 'unknown')})")
                return True
            logger.error(f"  ❌ Gateway返回错误状态码: {response.status_code}")
            return False
        except Exception as e:
            logger.error(f"  ❌ Gateway检查失败: {e}")
            return False

    async def _check_xiaonuo(self) -> bool:
        """检查小诺智能体"""
        try:
            # 检查进程是否存在
            import subprocess
            result = subprocess.run(
                ["pgrep", "-f", "xiaonuo_main.py"],
                capture_output=True
            )
            if result.returncode == 0:
                logger.info("  ✅ 小诺智能体运行中")
                return True
            logger.error("  ❌ 小诺智能体未运行")
            return False
        except Exception as e:
            logger.error(f"  ❌ 小诺检查失败: {e}")
            return False

    def _print_report(self, report: dict[str, Any]):
        """打印健康报告"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 健康检查报告")
        logger.info("=" * 60)
        logger.info(f"⏱️ 检查时间: {report['timestamp']}")
        logger.info(f"⏱️ 总耗时: {report['total_time']}秒")
        logger.info(f"📊 健康度: {report['health_percentage']}% ({report['healthy_count']}/{report['total_count']})")
        logger.info("=" * 60)
        logger.info("📋 详细结果:")

        for service, info in report['details'].items():
            logger.info(f"  {service}: {info['status']}")

        logger.info("=" * 60)


async def main():
    """主函数"""
    checker = HealthChecker()
    report = await checker.check_all()

    # 根据健康度返回退出码
    if report['health_percentage'] >= 80:
        sys.exit(0)
    elif report['health_percentage'] >= 50:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
