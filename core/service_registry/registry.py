"""
服务注册表

> 版本: v1.0
> 更新: 2026-04-21
"""

from typing import Dict, List, Optional
from datetime import datetime
import threading
from .models import ServiceInfo, ServiceHealth, ServiceRegistry as ServiceRegistryModel


class ServiceRegistry:
    """
    服务注册表
    
    职责:
    - 存储服务信息
    - 管理服务生命周期
    - 提供服务查询接口
    """
    
    def __init__(self):
        """初始化服务注册表"""
        self._registry = ServiceRegistryModel()
        self._lock = threading.RLock()
    
    def register(self, service: ServiceInfo) -> bool:
        """
        注册服务
        
        参数:
            service: 服务信息
            
        返回:
            是否注册成功
        """
        with self._lock:
            try:
                # 设置初始健康状态
                if service.health.status == ServiceStatus.STARTING:
                    service.health.last_check = datetime.now()
                
                # 添加到注册表
                self._registry.services[service.id] = service
                self._registry.last_updated = datetime.now()
                
                print(f"✅ 服务已注册: {service.name} ({service.id})")
                return True
                
            except Exception as e:
                print(f"❌ 注册服务失败: {e}")
                return False
    
    def deregister(self, service_id: str) -> bool:
        """
        注销服务
        
        参数:
            service_id: 服务ID
            
        返回:
            是否注销成功
        """
        with self._lock:
            if service_id in self._registry.services:
                service = self._registry.services[service_id]
                del self._registry.services[service_id]
                self._registry.last_updated = datetime.now()
                
                print(f"✅ 服务已注销: {service.name} ({service_id})")
                return True
            return False
    
    def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        """
        获取服务
        
        参数:
            service_id: 服务ID
            
        返回:
            服务信息，如果不存在返回None
        """
        with self._lock:
            return self._registry.services.get(service_id)
    
    def find_services(
        self,
        name: str = None,
        service_type: str = None,
        tags: List[str] = None,
        healthy_only: bool = True
    ) -> List[ServiceInfo]:
        """
        查找服务
        
        参数:
            name: 服务名称（可选）
            service_type: 服务类型（可选）
            tags: 标签列表（可选）
            healthy_only: 是否只返回健康服务
            
        返回:
            服务列表
        """
        with self._lock:
            services = list(self._registry.services.values())
        
        # 过滤条件
        if name:
            services = [s for s in services if s.name == name]
        
        if service_type:
            services = [s for s in services if s.type == service_type]
        
        if tags:
            services = [
                s for s in services
                if any(tag in s.tags for tag in tags)
            ]
        
        if healthy_only:
            services = [s for s in services if s.is_healthy]
        
        return services
    
    def update_health(
        self,
        service_id: str,
        health: ServiceHealth
    ) -> bool:
        """
        更新健康状态
        
        参数:
            service_id: 服务ID
            health: 健康状态
            
        返回:
            是否更新成功
        """
        with self._lock:
            if service_id in self._registry.services:
                self._registry.services[service_id].health = health
                self._registry.last_updated = datetime.now()
                return True
            return False
    
    def get_all_services(self) -> List[ServiceInfo]:
        """
        获取所有服务
        
        返回:
            所有服务列表
        """
        with self._lock:
            return list(self._registry.services.values())
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        返回:
            统计信息字典
        """
        with self._lock:
            services = list(self._registry.services.values())
            
            return {
                "total_services": len(services),
                "healthy_services": sum(1 for s in services if s.is_healthy),
                "unhealthy_services": sum(1 for s in services if not s.is_healthy),
                "services_by_type": self._count_by_type(services),
                "services_by_status": self._count_by_status(services),
                "last_updated": self._registry.last_updated.isoformat()
            }
    
    def _count_by_type(self, services: List[ServiceInfo]) -> Dict[str, int]:
        """按类型统计服务"""
        counts = {}
        for service in services:
            counts[service.type] = counts.get(service.type, 0) + 1
        return counts
    
    def _count_by_status(self, services: List[ServiceInfo]) -> Dict[str, int]:
        """按状态统计服务"""
        counts = {}
        for service in services:
            status = service.health.status.value
            counts[status] = counts.get(status, 0) + 1
        return counts


# 全局服务注册表实例
_registry_instance: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """
    获取全局服务注册表实例
    
    返回:
        服务注册表实例（单例）
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ServiceRegistry()
    return _registry_instance


__all__ = [
    "ServiceRegistry",
    "get_service_registry",
]
