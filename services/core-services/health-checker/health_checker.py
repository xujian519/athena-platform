"""
Athena平台健康检查服务
统一监控所有服务的健康状态
"""

import asyncio
from core.async_main import async_main
import json
import logging
from core.logging_config import setup_logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class ServiceHealth:
    """服务健康状态"""

    def __init__(self, name: str, url: str, timeout: int = 5):
        self.name = name
        self.url = url
        self.timeout = timeout
        self.status = 'unknown'
        self.last_check = None
        self.response_time = None
        self.error = None
        self.consecutive_failures = 0
        self.consecutive_successes = 0

    async def check(self) -> Dict:
        """执行健康检查"""
        start_time = datetime.now()

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(self.url) as response:
                    response_time = (datetime.now() - start_time).total_seconds()

                    if response.status == 200:
                        self.status = 'healthy'
                        self.error = None
                        self.consecutive_successes += 1
                        self.consecutive_failures = 0
                    else:
                        self.status = 'unhealthy'
                        self.error = f"HTTP {response.status}"
                        self.consecutive_failures += 1
                        self.consecutive_successes = 0

                    self.response_time = response_time

        except asyncio.TimeoutError:
            self.status = 'timeout'
            self.error = f"Request timeout after {self.timeout}s"
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.response_time = self.timeout

        except Exception as e:
            self.status = 'error'
            self.error = str(e)
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.response_time = (datetime.now() - start_time).total_seconds()

        self.last_check = datetime.now()

        return {
            'name': self.name,
            'status': self.status,
            'url': self.url,
            'response_time': self.response_time,
            'error': self.error,
            'last_check': self.last_check.isoformat(),
            'consecutive_failures': self.consecutive_failures,
            'consecutive_successes': self.consecutive_successes
        }


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.services: Dict[str, ServiceHealth] = {}
        self.session: aiohttp.ClientSession | None = None

        # 默认服务配置
        self.default_services = {
            'api-gateway': ServiceHealth('API网关', 'http://localhost:8080/health'),
            'patent-service': ServiceHealth('专利服务', 'http://localhost:8001/health'),
            'user-service': ServiceHealth('用户服务', 'http://localhost:8002/health'),
            'search-service': ServiceHealth('搜索服务', 'http://localhost:8003/health'),
            'crawler-service': ServiceHealth('爬虫服务', 'http://localhost:8300/health'),
            'redis': ServiceHealth('Redis', 'http://localhost:6379', timeout=3),
            'postgres': ServiceHealth('PostgreSQL', 'http://localhost:5432', timeout=5),
            'qdrant': ServiceHealth('Qdrant', 'http://localhost:6333/health'),
            'neo4j': ServiceHealth('Neo4j', 'http://localhost:7474/', timeout=5),
            'elasticsearch': ServiceHealth('Elasticsearch', 'http://localhost:9200/_cluster/health'),
            'rabbitmq': ServiceHealth('RabbitMQ', 'http://localhost:15672/api/overview', timeout=5),
            'prometheus': ServiceHealth('Prometheus', 'http://localhost:9090/-/healthy'),
            'grafana': ServiceHealth('Grafana', 'http://localhost:3000/api/health'),
            'jaeger': ServiceHealth('Jaeger', 'http://localhost:16686/')
        }

        # 注册默认服务
        for name, service in self.default_services.items():
            self.services[name] = service

    async def start(self):
        """启动健康检查器"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        logger.info('健康检查器已启动')

    async def stop(self):
        """停止健康检查器"""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info('健康检查器已停止')

    def add_service(self, name: str, url: str, timeout: int = 5):
        """添加服务"""
        service = ServiceHealth(name, url, timeout)
        self.services[name] = service
        logger.info(f"已添加服务: {name} -> {url}")

    def remove_service(self, name: str):
        """移除服务"""
        if name in self.services:
            del self.services[name]
            logger.info(f"已移除服务: {name}")

    async def check_service(self, name: str) -> Dict:
        """检查单个服务"""
        if name not in self.services:
            return {'error': f"Service {name} not found"}

        return await self.services[name].check()

    async def check_all(self) -> Dict:
        """检查所有服务"""
        results = {}

        # 并行检查所有服务
        tasks = []
        for name in self.services:
            task = asyncio.create_task(self.services[name].check())
            tasks.append((name, task))

        # 等待所有检查完成
        for name, task in tasks:
            try:
                results[name] = await task
            except Exception as e:
                logger.error(f"检查服务 {name} 失败: {e}")
                results[name] = {
                    'name': name,
                    'status': 'error',
                    'error': str(e),
                    'last_check': datetime.now().isoformat()
                }

        return results

    async def get_healthy_services(self) -> List[str]:
        """获取健康的服务列表"""
        results = await self.check_all()
        return [name for name, result in results.items() if result.get('status') == 'healthy']

    async def get_unhealthy_services(self) -> List[str]:
        """获取不健康的服务列表"""
        results = await self.check_all()
        return [name for name, result in results.items() if result.get('status') != 'healthy']

    async def get_overall_status(self) -> Dict:
        """获取整体状态"""
        results = await self.check_all()

        total = len(results)
        healthy = sum(1 for r in results.values() if r.get('status') == 'healthy')
        unhealthy = total - healthy

        # 计算整体状态
        if healthy == total:
            overall_status = 'healthy'
        elif healthy > 0:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'

        return {
            'overall_status': overall_status,
            'total_services': total,
            'healthy_services': healthy,
            'unhealthy_services': unhealthy,
            'health_percentage': (healthy / total * 100) if total > 0 else 0,
            'last_check': datetime.now().isoformat(),
            'services': results
        }

    async def start_monitoring(self, interval: int = 30):
        """启动持续监控"""
        logger.info(f"开始持续监控，检查间隔: {interval}秒")

        while True:
            try:
                results = await self.check_all()

                # 记录状态变化
                for name, result in results.items():
                    service = self.services[name]
                    if service.consecutive_failures == 3:
                        logger.warning(f"服务 {name} 连续失败3次")
                    elif service.consecutive_failures == 5:
                        logger.error(f"服务 {name} 连续失败5次，可能需要关注")
                    elif service.consecutive_successes == 3 and service.consecutive_failures > 0:
                        logger.info(f"服务 {name} 已恢复正常")

                # 输出摘要
                healthy_count = sum(1 for r in results.values() if r.get('status') == 'healthy')
                logger.info(f"健康检查完成: {healthy_count}/{len(results)} 服务健康")

                # 保存检查结果到文件
                await self.save_results(results)

            except Exception as e:
                logger.error(f"健康检查失败: {e}: {exc_info=True}")

            await asyncio.sleep(interval)

    async def save_results(self, results: Dict):
        """保存检查结果"""
        try:
            # 创建检查结果目录
            import os
            os.makedirs('/tmp/athena_health', exist_ok=True)

            # 保存详细结果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"/tmp/athena_health/health_check_{timestamp}.json"

            with open(filename, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'results': results
                }, f, indent=2)

            # 只保留最近的100个结果文件
            files = sorted(os.listdir('/tmp/athena_health'))
            if len(files) > 100:
                for old_file in files[:-100]:
                    os.remove(f"/tmp/athena_health/{old_file}")

        except Exception as e:
            logger.error(f"保存健康检查结果失败: {e}")


# API接口
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title='Athena平台健康检查API', version='1.0.0')
health_checker = HealthChecker()


@app.on_event('startup')
async def startup_event():
    """启动事件"""
    await health_checker.start()

    # 启动后台监控任务
    asyncio.create_task(health_checker.start_monitoring())


@app.on_event('shutdown')
async def shutdown_event():
    """关闭事件"""
    await health_checker.stop()


@app.get('/')
async def root():
    """根路径"""
    return {
        'service': 'Athena Health Checker',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    }


@app.get('/health')
async def health():
    """健康检查端点"""
    return await health_checker.get_overall_status()


@app.get('/health/all')
async def check_all_services():
    """检查所有服务"""
    return await health_checker.check_all()


@app.get('/health/{service_name}')
async def check_service(service_name: str):
    """检查单个服务"""
    result = await health_checker.check_service(service_name)
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    return result


@app.get('/services')
async def get_services():
    """获取服务列表"""
    return {
        'services': [
            {
                'name': name,
                'url': service.url,
                'status': service.status,
                'last_check': service.last_check.isoformat() if service.last_check else None
            }
            for name, service in health_checker.services.items()
        ]
    }


@app.get('/services/healthy')
async def get_healthy_services():
    """获取健康的服务"""
    services = await health_checker.get_healthy_services()
    return {
        'healthy_services': services,
        'count': len(services)
    }


@app.get('/services/unhealthy')
async def get_unhealthy_services():
    """获取不健康的服务"""
    services = await health_checker.get_unhealthy_services()
    return {
        'unhealthy_services': services,
        'count': len(services)
    }


@app.post('/services/{service_name}')
async def add_service(service_name: str, url: str, timeout: int = 5):
    """添加服务"""
    health_checker.add_service(service_name, url, timeout)
    return {'message': f"Service {service_name} added successfully"}


@app.delete('/services/{service_name}')
async def remove_service(service_name: str):
    """移除服务"""
    health_checker.remove_service(service_name)
    return {'message': f"Service {service_name} removed successfully"}


if __name__ == '__main__':
    import uvicorn

    # 运行健康检查服务
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=9999,
        log_level='info'
    )