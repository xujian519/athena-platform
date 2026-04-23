"""
服务注册中心数据模型

> 版本: v1.0
> 更新: 2026-04-21
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class ServiceStatus(str, Enum):
    """服务状态枚举"""
    STARTING = "starting"            # 启动中
    RUNNING = "running"              # 运行中
    DEGRADED = "degraded"            # 降级运行
    STOPPING = "stopping"            # 停止中
    STOPPED = "stopped"              # 已停止
    ERROR = "error"                  # 错误


class ServiceHealth(BaseModel):
    """服务健康状态"""
    
    status: ServiceStatus = Field(
        default=ServiceStatus.STARTING,
        description="服务状态"
    )
    last_check: datetime = Field(
        default_factory=datetime.now,
        description="最后检查时间"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="错误信息"
    )
    metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="性能指标"
    )


class ServiceInfo(BaseModel):
    """服务信息"""
    
    # 基本信息
    id: str = Field(..., description="服务ID（唯一）")
    name: str = Field(..., description="服务名称")
    type: str = Field(..., description="服务类型")
    version: str = Field(default="1.0.0", description="服务版本")
    
    # 网络信息
    host: str = Field(..., description="主机地址")
    port: int = Field(..., description="端口号")
    protocol: str = Field(default="http", description="协议（http/https/ws）")
    
    # 健康检查
    health_check_url: str = Field(..., description="健康检查URL")
    health_check_interval: int = Field(default=30, description="健康检查间隔（秒）")
    health: ServiceHealth = Field(
        default_factory=ServiceHealth,
        description="健康状态"
    )
    
    # 负载均衡
    weight: int = Field(default=1, description="权重")
    response_time: float = Field(default=0.0, description="响应时间（ms）")
    active_connections: int = Field(default=0, description="活动连接数")
    
    # 元数据
    tags: List[str] = Field(default_factory=list, description="标签")
    metadata: Dict[str, str] = Field(default_factory=dict, description="元数据")
    
    @property
    def base_url(self) -> str:
        """生成基础URL"""
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def is_healthy(self) -> bool:
        """判断服务是否健康"""
        return self.health.status in [
            ServiceStatus.RUNNING,
            ServiceStatus.DEGRADED
        ]


class ServiceRegistry(BaseModel):
    """服务注册表"""
    
    services: Dict[str, ServiceInfo] = Field(
        default_factory=dict,
        description="服务列表"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="最后更新时间"
    )
    
    def get_service_count(self) -> int:
        """获取服务数量"""
        return len(self.services)
    
    def get_healthy_service_count(self) -> int:
        """获取健康服务数量"""
        return sum(
            1 for service in self.services.values()
            if service.is_healthy
        )


__all__ = [
    "ServiceStatus",
    "ServiceHealth",
    "ServiceInfo",
    "ServiceRegistry",
]
