#!/usr/bin/env python3
"""
健康检查器
定期检查服务的健康状态
"""

import time
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from core.config import config
from utils.logger import ScriptLogger


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    service_name: str
    status: str  # healthy, unhealthy, unknown
    response_time: float
    message: str
    timestamp: datetime
    details: Dict = None


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.logger = ScriptLogger("HealthChecker")
        self.checks: Dict[str, Dict] = {}
        self.results: Dict[str, HealthCheckResult] = {}
        self.callbacks: List[Callable] = []
        self.running = False

    def register_check(self, service_name: str, check_config: Dict):
        """注册健康检查"""
        self.checks[service_name] = {
            'url': check_config.get('url'),
            'method': check_config.get('method', 'GET'),
            'headers': check_config.get('headers', {}),
            'expected_status': check_config.get('expected_status', 200),
            'timeout': check_config.get('timeout', 10),
            'interval': check_config.get('interval', 60),
            'retries': check_config.get('retries', 3),
            'custom_check': check_config.get('custom_check')  # 自定义检查函数
        }
        self.logger.info(f"注册健康检查: {service_name}")

    def unregister_check(self, service_name: str):
        """取消注册健康检查"""
        if service_name in self.checks:
            del self.checks[service_name]
            if service_name in self.results:
                del self.results[service_name]
            self.logger.info(f"取消健康检查: {service_name}")

    def add_callback(self, callback: Callable):
        """添加状态变化回调"""
        self.callbacks.append(callback)

    async def check_service(self, service_name: str) -> HealthCheckResult:
        """检查单个服务"""
        if service_name not in self.checks:
            return HealthCheckResult(
                service_name=service_name,
                status='unknown',
                response_time=0,
                message='未注册检查',
                timestamp=datetime.now()
            )

        check_config = self.checks[service_name]
        start_time = time.time()

        # 如果有自定义检查函数，优先使用
        if check_config.get('custom_check'):
            try:
                result = await check_config['custom_check']()
                response_time = time.time() - start_time
                return HealthCheckResult(
                    service_name=service_name,
                    status='healthy' if result else 'unhealthy',
                    response_time=response_time,
                    message='自定义检查通过' if result else '自定义检查失败',
                    timestamp=datetime.now()
                )
            except Exception as e:
                response_time = time.time() - start_time
                return HealthCheckResult(
                    service_name=service_name,
                    status='unhealthy',
                    response_time=response_time,
                    message=f'自定义检查异常: {e}',
                    timestamp=datetime.now()
                )

        # HTTP健康检查
        url = check_config['url']
        if not url:
            return HealthCheckResult(
                service_name=service_name,
                status='unknown',
                response_time=0,
                message='未配置检查URL',
                timestamp=datetime.now()
            )

        async with aiohttp.ClientSession() as session:
            for attempt in range(check_config['retries']):
                try:
                    async with session.request(
                        check_config['method'],
                        url,
                        headers=check_config['headers'],
                        timeout=aiohttp.ClientTimeout(total=check_config['timeout'])
                    ) as response:
                        response_time = time.time() - start_time

                        if response.status == check_config['expected_status']:
                            status = 'healthy'
                            message = '检查通过'
                        else:
                            status = 'unhealthy'
                            message = f'状态码错误: {response.status}'

                        return HealthCheckResult(
                            service_name=service_name,
                            status=status,
                            response_time=response_time,
                            message=message,
                            timestamp=datetime.now(),
                            details={
                                'status_code': response.status,
                                'headers': dict(response.headers),
                                'attempt': attempt + 1
                            }
                        )

                except asyncio.TimeoutError:
                    if attempt == check_config['retries'] - 1:
                        response_time = time.time() - start_time
                        return HealthCheckResult(
                            service_name=service_name,
                            status='unhealthy',
                            response_time=response_time,
                            message='请求超时',
                            timestamp=datetime.now()
                        )
                    await asyncio.sleep(1)

                except Exception as e:
                    if attempt == check_config['retries'] - 1:
                        response_time = time.time() - start_time
                        return HealthCheckResult(
                            service_name=service_name,
                            status='unhealthy',
                            response_time=response_time,
                            message=f'检查失败: {e}',
                            timestamp=datetime.now()
                        )
                    await asyncio.sleep(1)

    async def check_all_services(self) -> Dict[str, HealthCheckResult]:
        """检查所有服务"""
        tasks = []
        for service_name in self.checks.keys():
            task = asyncio.create_task(self.check_service(service_name))
            tasks.append((service_name, task))

        results = {}
        for service_name, task in tasks:
            try:
                result = await task
                results[service_name] = result

                # 检查状态是否有变化
                if service_name in self.results:
                    old_result = self.results[service_name]
                    if old_result.status != result.status:
                        self.logger.warning(
                            f"服务 {service_name} 状态变化: {old_result.status} -> {result.status}"
                        )
                        # 调用回调函数
                        for callback in self.callbacks:
                            try:
                                await callback(old_result, result)
                            except Exception as e:
                                self.logger.error(f"回调函数执行失败: {e}")

            except Exception as e:
                self.logger.error(f"检查服务 {service_name} 失败: {e}")
                results[service_name] = HealthCheckResult(
                    service_name=service_name,
                    status='unknown',
                    response_time=0,
                    message=f'检查异常: {e}',
                    timestamp=datetime.now()
                )

        self.results = results
        return results

    async def start_monitoring(self):
        """开始监控"""
        self.running = True
        self.logger.info("开始健康监控...")

        while self.running:
            try:
                await self.check_all_services()

                # 计算下次检查时间
                intervals = [cfg.get('interval', 60) for cfg in self.checks.values()]
                next_check = min(intervals) if intervals else 60

                await asyncio.sleep(next_check)

            except Exception as e:
                self.logger.error(f"监控循环出错: {e}")
                await asyncio.sleep(10)

    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        self.logger.info("停止健康监控")

    def get_service_health(self, service_name: str) -> HealthCheckResult | None:
        """获取服务健康状态"""
        return self.results.get(service_name)

    def get_all_health(self) -> Dict[str, HealthCheckResult]:
        """获取所有服务健康状态"""
        return self.results.copy()

    def get_unhealthy_services(self) -> List[str]:
        """获取不健康的服务列表"""
        return [
            name for name, result in self.results.items()
            if result.status == 'unhealthy'
        ]

    def get_health_summary(self) -> Dict:
        """获取健康状态汇总"""
        total = len(self.results)
        healthy = sum(1 for r in self.results.values() if r.status == 'healthy')
        unhealthy = sum(1 for r in self.results.values() if r.status == 'unhealthy')
        unknown = sum(1 for r in self.results.values() if r.status == 'unknown')

        return {
            'total': total,
            'healthy': healthy,
            'unhealthy': unhealthy,
            'unknown': unknown,
            'health_rate': (healthy / total * 100) if total > 0 else 0,
            'last_check': max(
                (r.timestamp for r in self.results.values()),
                default=datetime.now()
            ).isoformat()
        }

    def generate_report(self) -> str:
        """生成健康检查报告"""
        summary = self.get_health_summary()

        report = [
            "=" * 60,
            "🏥 健康检查报告",
            "=" * 60,
            f"总服务数: {summary['total']}",
            f"健康服务: {summary['healthy']} ✅",
            f"不健康服务: {summary['unhealthy']} ❌",
            f"未知状态: {summary['unknown']} ❓",
            f"健康率: {summary['health_rate']:.1f}%",
            f"检查时间: {summary['last_check']}",
            "",
            "📋 详细状态:",
            "-" * 40
        ]

        for name, result in self.results.items():
            icon = {
                'healthy': '✅',
                'unhealthy': '❌',
                'unknown': '❓'
            }.get(result.status, '❓')

            report.append(
                f"{icon} {name:20} "
                f"{result.status:10} "
                f"{result.response_time:.3f}s "
                f"{result.message}"
            )

        return "\n".join(report)


# 全局实例
health_checker = HealthChecker()