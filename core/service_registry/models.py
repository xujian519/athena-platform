"""
服务注册数据模型
Service Registry Data Models
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Literal
import json


class ServiceStatus(Enum):
    """服务状态"""
    HEALTHY = "healthy"       # 健康
    UNHEALTHY = "unhealthy"   # 不健康
    DRAINING = "draining"     # 流量排空（优雅下线）
    TERMINATED = "terminated" # 已终止


class LoadBalanceStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"       # 轮询
    RANDOM = "random"                 # 随机
    LEAST_CONNECTION = "least_connection"  # 最少连接
    CONSISTENT_HASH = "consistent_hash"    # 一致性哈希


@dataclass
class ServiceInstance:
    """服务实例"""
    instance_id: str          # 实例ID
    service_name: str         # 服务名称
    host: str                 # 主机地址
    port: int                 # 端口
    status: ServiceStatus     # 服务状态
    last_heartbeat: datetime  # 最后心跳时间
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    updated_at: datetime = field(default_factory=datetime.now)  # 更新时间

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换枚举为字符串
        data['status'] = self.status.value
        # 转换datetime为ISO格式字符串
        if isinstance(data['last_heartbeat'], datetime):
            data['last_heartbeat'] = data['last_heartbeat'].isoformat()
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()
        if isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].isoformat()
        return data

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceInstance":
        """从字典创建"""
        # 转换状态字符串为枚举
        if isinstance(data.get('status'), str):
            data['status'] = ServiceStatus(data['status'])

        # 转换ISO格式字符串为datetime
        if isinstance(data.get('last_heartbeat'), str):
            data['last_heartbeat'] = datetime.fromisoformat(data['last_heartbeat'])
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])

        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "ServiceInstance":
        """从JSON字符串创建"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @property
    def address(self) -> str:
        """获取服务地址"""
        return f"{self.host}:{self.port}"

    def is_healthy(self) -> bool:
        """判断服务是否健康"""
        return self.status == ServiceStatus.HEALTHY

    def is_expired(self, timeout_seconds: int = 300) -> bool:
        """判断服务是否超时（心跳超时）"""
        now = datetime.now()
        delta = (now - self.last_heartbeat).total_seconds()
        return delta > timeout_seconds

    def touch(self):
        """更新心跳时间"""
        self.last_heartbeat = datetime.now()
        self.updated_at = datetime.now()


@dataclass
class HealthCheckConfig:
    """健康检查配置"""
    check_type: Literal["http", "tcp", "heartbeat"] = "heartbeat"
    check_interval: int = 30      # 检查间隔（秒）
    check_timeout: int = 5        # 检查超时（秒）
    unhealthy_threshold: int = 3  # 不健康阈值
    healthy_threshold: int = 2    # 健康阈值

    # HTTP检查配置
    http_path: str = "/health"
    http_expected_status: int = 200
    http_method: str = "GET"

    # TCP检查配置
    tcp_port: Optional[int] = None

    # 心跳检查配置
    heartbeat_timeout: int = 300  # 心跳超时（秒）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HealthCheckConfig":
        """从字典创建"""
        return cls(**data)


@dataclass
class ServiceRegistration:
    """服务注册请求"""
    service_name: str                    # 服务名称
    instance_id: str                     # 实例ID
    host: str                            # 主机地址
    port: int                            # 端口
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    health_check_config: Optional[HealthCheckConfig] = None  # 健康检查配置

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if self.health_check_config:
            data['health_check_config'] = self.health_check_config.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceRegistration":
        """从字典创建"""
        if data.get('health_check_config'):
            data['health_check_config'] = HealthCheckConfig.from_dict(
                data['health_check_config']
            )
        return cls(**data)

    def to_service_instance(self) -> ServiceInstance:
        """转换为服务实例"""
        return ServiceInstance(
            instance_id=self.instance_id,
            service_name=self.service_name,
            host=self.host,
            port=self.port,
            status=ServiceStatus.HEALTHY,
            last_heartbeat=datetime.now(),
            metadata=self.metadata
        )
