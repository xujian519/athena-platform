"""
服务发现API

> 版本: v1.0
> 更新: 2026-04-21
"""

import asyncio
import random
from typing import List, Optional
from .models import ServiceInfo, ServiceStatus
from .registry import get_service_registry


class DiscoveryAPI:
    """
    服务发现API
    
    职责:
    - 提供服务查询接口
    - 负载均衡
    - 失败重试
    """
    
    def __init__(self):
        """初始化服务发现API"""
        self.registry = get_service_registry()
    
    async def discover(
        self,
        service_name: str,
        load_balance: str = "round_robin",
        healthy_only: bool = True
    ) -> Optional[ServiceInfo]:
        """
        发现服务（带负载均衡）
        
        参数:
            service_name: 服务名称
            load_balance: 负载均衡算法
            healthy_only: 是否只返回健康服务
            
        返回:
            服务信息，如果找不到返回None
        """
        services = self.registry.find_services(
            name=service_name,
            healthy_only=healthy_only
        )
        
        if not services:
            return None
        
        # 负载均衡
        if load_balance == "round_robin":
            return self._round_robin_select(services)
        elif load_balance == "response_time":
            return self._response_time_select(services)
        elif load_balance == "least_connections":
            return self._least_connections_select(services)
        elif load_balance == "random":
            return random.choice(services)
        else:
            return services[0]
    
    async def discover_all(
        self,
        service_name: str,
        healthy_only: bool = True
    ) -> List[ServiceInfo]:
        """
        发现所有服务实例
        
        参数:
            service_name: 服务名称
            healthy_only: 是否只返回健康服务
            
        返回:
            服务列表
        """
        return self.registry.find_services(
            name=service_name,
            healthy_only=healthy_only
        )
    
    async def discover_by_type(
        self,
        service_type: str,
        healthy_only: bool = True
    ) -> List[ServiceInfo]:
        """
        按类型发现服务
        
        参数:
            service_type: 服务类型
            healthy_only: 是否只返回健康服务
            
        返回:
            服务列表
        """
        return self.registry.find_services(
            service_type=service_type,
            healthy_only=healthy_only
        )
    
    async def discover_by_tags(
        self,
        tags: List[str],
        healthy_only: bool = True
    ) -> List[ServiceInfo]:
        """
        按标签发现服务
        
        参数:
            tags: 标签列表
            healthy_only: 是否只返回健康服务
            
        返回:
            服务列表
        """
        return self.registry.find_services(
            tags=tags,
            healthy_only=healthy_only
        )
    
    def _round_robin_select(self, services: List[ServiceInfo]) -> ServiceInfo:
        """轮询选择"""
        # 简化实现：随机选择
        # 生产环境应该维护一个索引
        return random.choice(services)
    
    def _response_time_select(self, services: List[ServiceInfo]) -> ServiceInfo:
        """响应时间加权选择"""
        # 选择响应时间最短的服务
        return min(services, key=lambda s: s.response_time)
    
    def _least_connections_select(self, services: List[ServiceInfo]) -> ServiceInfo:
        """最少连接选择"""
        # 选择活动连接数最少的服务
        return min(services, key=lambda s: s.active_connections)


# 全局服务发现API实例
_discovery_api_instance: Optional[DiscoveryAPI] = None


def get_discovery_api() -> DiscoveryAPI:
    """
    获取全局服务发现API实例
    
    返回:
        服务发现API实例（单例）
    """
    global _discovery_api_instance
    if _discovery_api_instance is None:
        _discovery_api_instance = DiscoveryAPI()
    return _discovery_api_instance


__all__ = [
    "DiscoveryAPI",
    "get_discovery_api",
]
