"""
健康检查器

> 版本: v1.0
> 更新: 2026-04-21
"""

import asyncio
import aiohttp
from typing import Dict, Optional
from datetime import datetime
from .models import ServiceInfo, ServiceHealth, ServiceStatus
from .registry import get_service_registry


class HealthChecker:
    """
    健康检查器
    
    职责:
    - 定期检查服务健康状态
    - 自动更新服务状态
    - 剔除不健康服务
    """
    
    def __init__(
        self,
        check_interval: int = 30,
        timeout: int = 5,
        failure_threshold: int = 3
    ):
        """
        初始化健康检查器
        
        参数:
            check_interval: 检查间隔（秒）
            timeout: 超时时间（秒）
            failure_threshold: 失败阈值（连续失败多少次剔除）
        """
        self.check_interval = check_interval
        self.timeout = timeout
        self.failure_threshold = failure_threshold
        self._failure_count: Dict[str, int] = {}
        self._running = False
        self._check_task: Optional[asyncio.Task] = None
    
    async def check_service(self, service: ServiceInfo) -> ServiceHealth:
        """
        检查单个服务
        
        参数:
            service: 服务信息
            
        返回:
            健康状态
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    service.health_check_url,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        return ServiceHealth(
                            status=ServiceStatus.RUNNING,
                            last_check=datetime.now(),
                            metrics={"response_time": 0.0}
                        )
                    else:
                        return ServiceHealth(
                            status=ServiceStatus.ERROR,
                            last_check=datetime.now(),
                            error_message=f"HTTP {response.status}"
                        )
        except asyncio.TimeoutError:
            return ServiceHealth(
                status=ServiceStatus.ERROR,
                last_check=datetime.now(),
                error_message="Timeout"
            )
        except Exception as e:
            return ServiceHealth(
                status=ServiceStatus.ERROR,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def check_all_services(self) -> Dict[str, ServiceHealth]:
        """
        检查所有服务
        
        返回:
            服务ID到健康状态的映射
        """
        registry = get_service_registry()
        services = registry.get_all_services()
        
        health_status = {}
        for service in services:
            health = await self.check_service(service)
            health_status[service.id] = health
            
            # 更新注册表
            registry.update_health(service.id, health)
            
            # 处理失败计数
            if health.status == ServiceStatus.ERROR:
                self._failure_count[service.id] = \
                    self._failure_count.get(service.id, 0) + 1
            else:
                self._failure_count[service.id] = 0
        
        return health_status
    
    async def start_background_check(self) -> None:
        """启动后台健康检查"""
        if self._running:
            return
        
        self._running = True
        self._check_task = asyncio.create_task(self._background_check_loop())
        print("✅ 健康检查器已启动")
    
    async def stop_background_check(self) -> None:
        """停止后台健康检查"""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        print("✅ 健康检查器已停止")
    
    async def _background_check_loop(self) -> None:
        """后台检查循环"""
        while self._running:
            try:
                # 检查所有服务
                health_status = await self.check_all_services()
                
                # 剔除连续失败的服务
                registry = get_service_registry()
                for service_id, count in self._failure_count.items():
                    if count >= self.failure_threshold:
                        service = registry.get_service(service_id)
                        if service:
                            print(f"⚠️ 剔除不健康服务: {service.name} ({service_id})")
                            # 可以在这里标记服务为不健康，但不自动注销
                
                # 等待下次检查
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                print(f"❌ 健康检查出错: {e}")
                await asyncio.sleep(self.check_interval)


# 全局健康检查器实例
_health_checker_instance: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """
    获取全局健康检查器实例
    
    返回:
        健康检查器实例（单例）
    """
    global _health_checker_instance
    if _health_checker_instance is None:
        _health_checker_instance = HealthChecker()
    return _health_checker_instance


__all__ = [
    "HealthChecker",
    "get_health_checker",
]
