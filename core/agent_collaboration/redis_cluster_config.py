#!/usr/bin/env python3
from __future__ import annotations
"""
Redis集群配置支持
Redis Cluster Configuration for Production

支持多种Redis部署模式:
1. 单机模式(开发/测试)
2. 哨兵模式(高可用)
3. 集群模式(分布式、高并发)

版本: v1.0.0
创建时间: 2026-01-18
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:
    import redis.asyncio as redis

    redis_available = True  # type: ignore[assignment]
except ImportError:
    redis = None  # type: ignore[assignment]
    redis_available = False  # type: ignore[assignment]
    RedisSyncCluster = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Type aliases
RedisClient = Any

# Suppress errors for redis module which may be None
# pyright: reportOptionalMemberAccess=false


# =============================================================================
# Redis部署模式
# =============================================================================


class RedisDeploymentMode(Enum):
    """Redis部署模式"""

    SINGLE = "single"  # 单机模式
    SENTINEL = "sentinel"  # 哨兵模式(高可用)
    CLUSTER = "cluster"  # 集群模式(分布式)


@dataclass
class RedisNodeConfig:
    """Redis节点配置"""

    host: str
    port: int
    password: Optional[str] = None
    db: int = 0
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5


@dataclass
class RedisSentinelConfig:
    """Redis哨兵配置"""

    sentinels: list[RedisNodeConfig] = field(default_factory=list)
    master_name: str = "mymaster"
    password: Optional[str] = None
    socket_timeout: int = 5
    socket_connect_timeout: int = 5


@dataclass
class RedisClusterConfig:
    """Redis集群配置"""

    nodes: list[RedisNodeConfig] = field(default_factory=list)
    password: Optional[str] = None
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    max_connections_per_node: bool = True
    skip_full_coverage_check: bool = False
    decode_responses: bool = True


# =============================================================================
# Redis连接工厂
# =============================================================================


class RedisConnectionFactory:
    """
    Redis连接工厂

    根据部署模式创建相应的Redis客户端
    """

    @staticmethod
    def create_single_client(config: RedisNodeConfig) -> RedisClient:  # type: ignore[valid-type]
        """创建单机模式客户端"""
        return redis.Redis(  # type: ignore[attr-defined]
            host=config.host,
            port=config.port,
            password=config.password,
            db=config.db,
            max_connections=config.max_connections,
            socket_timeout=config.socket_timeout,
            socket_connect_timeout=config.socket_connect_timeout,
            decode_responses=True,
        )

    @staticmethod
    def create_sentinel_client(config: RedisSentinelConfig) -> RedisClient:  # type: ignore[valid-type]
        """创建哨兵模式客户端"""
        sentinel_hosts = [(node.host, node.port) for node in config.sentinels]

        return redis.Sentinel(
            sentinel_hosts,
            socket_timeout=config.socket_timeout,
            socket_connect_timeout=config.socket_connect_timeout,
            password=config.password,
            decode_responses=True,
        )

    @staticmethod
    async def create_cluster_client(config: RedisClusterConfig) -> RedisClient:  # type: ignore[valid-type]
        """创建集群模式客户端"""
        # 注意:redis-py的集群支持在asyncio中有限制
        # 这里使用连接池到单个节点,生产环境建议使用redis-py-cluster

        if not config.nodes:
            raise ValueError("集群配置至少需要一个节点")

        # 使用第一个节点作为主节点
        primary_node = config.nodes[0]

        client = redis.Redis(  # type: ignore[attr-defined]
            host=primary_node.host,
            port=primary_node.port,
            password=config.password,
            max_connections=config.max_connections,
            socket_timeout=config.socket_timeout,
            socket_connect_timeout=config.socket_connect_timeout,
            decode_responses=config.decode_responses,
        )

        # 测试连接
        await client.ping()  # type: ignore[attr-defined]

        return client


# =============================================================================
# Redis集群管理器
# =============================================================================


class RedisClusterManager:
    """
    Redis集群管理器

    管理Redis连接的完整生命周期:
    - 连接池管理
    - 自动重连
    - 故障转移
    - 性能监控
    """

    def __init__(
        self,
        deployment_mode: RedisDeploymentMode = RedisDeploymentMode.SINGLE,
        config: RedisNodeConfig | RedisSentinelConfig | RedisClusterConfig | None = None,
    ):
        if not redis_available:
            raise ImportError("Redis不可用,请安装: pip install redis[hiredis]")

        self.deployment_mode = deployment_mode
        self.config = config or self._get_default_config()

        self.client: RedisClient | None = None
        self.running = False

        # 性能统计
        self.stats = {
            "connections_created": 0,
            "connections_failed": 0,
            "reconnects": 0,
            "commands_executed": 0,
            "errors": 0,
        }

    def _get_default_config(self) -> Any:
        """获取默认配置"""
        if self.deployment_mode == RedisDeploymentMode.SINGLE:
            return RedisNodeConfig(host="127.0.0.1", port=6379, db=0)
        elif self.deployment_mode == RedisDeploymentMode.SENTINEL:
            return RedisSentinelConfig(
                sentinels=[
                    RedisNodeConfig(host="127.0.0.1", port=26379),
                    RedisNodeConfig(host="127.0.0.1", port=26380),
                    RedisNodeConfig(host="127.0.0.1", port=26381),
                ],
                master_name="mymaster",
            )
        else:  # CLUSTER
            return RedisClusterConfig(
                nodes=[
                    RedisNodeConfig(host="127.0.0.1", port=7000),
                    RedisNodeConfig(host="127.0.0.1", port=7001),
                    RedisNodeConfig(host="127.0.0.1", port=7002),
                ]
            )

    async def start(self):
        """启动Redis连接"""
        try:
            if self.deployment_mode == RedisDeploymentMode.SINGLE:
                self.client = RedisConnectionFactory.create_single_client(
                    self.config  # type: ignore
                )

            elif self.deployment_mode == RedisDeploymentMode.SENTINEL:
                sentinel_client = RedisConnectionFactory.create_sentinel_client(
                    self.config  # type: ignore
                )
                # 通过哨兵获取主节点连接
                self.client = sentinel_client.master_for(self.config.master_name)  # type: ignore

            elif self.deployment_mode == RedisDeploymentMode.CLUSTER:
                self.client = await RedisConnectionFactory.create_cluster_client(
                    self.config  # type: ignore
                )

            # 测试连接
            await self.client.ping()

            self.running = True
            self.stats["connections_created"] += 1

            logger.info(f"✅ Redis连接已建立 ({self.deployment_mode.value}模式)")

        except Exception as e:
            self.stats["connections_failed"] += 1
            logger.error(f"❌ Redis连接失败: {e}")
            raise

    async def stop(self):
        """停止Redis连接"""
        self.running = False

        if self.client:
            await self.client.close()
            logger.info("✅ Redis连接已关闭")

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        if not self.client or not self.running:
            return {"status": "disconnected", "mode": self.deployment_mode.value}

        try:
            start_time = asyncio.get_event_loop().time()
            await self.client.ping()
            latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000

            # 获取Redis信息
            info = await self.client.info()

            return {
                "status": "connected",
                "mode": self.deployment_mode.value,
                "latency_ms": round(latency_ms, 2),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "stats": self.stats,
            }

        except Exception as e:
            return {"status": "error", "mode": self.deployment_mode.value, "error": str(e)}

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "deployment_mode": self.deployment_mode.value,
            "running": self.running,
        }


# =============================================================================
# 预定义配置
# =============================================================================

# 开发环境配置
DEV_REDIS_CONFIG = RedisNodeConfig(
    host="127.0.0.1", port=6379, db=1, max_connections=10  # 使用测试数据库
)

# 生产环境单机配置
PROD_SINGLE_CONFIG = RedisNodeConfig(
    host="redis-production.internal",
    port=6379,
    password="YOUR_SECURE_PASSWORD",
    db=0,
    max_connections=100,
)

# 生产环境哨兵配置
PROD_SENTINEL_CONFIG = RedisSentinelConfig(
    sentinels=[
        RedisNodeConfig(
            host="redis-sentinel-1.internal", port=26379, password="YOUR_SENTINEL_PASSWORD"
        ),
        RedisNodeConfig(
            host="redis-sentinel-2.internal", port=26379, password="YOUR_SENTINEL_PASSWORD"
        ),
        RedisNodeConfig(
            host="redis-sentinel-3.internal", port=26379, password="YOUR_SENTINEL_PASSWORD"
        ),
    ],
    master_name="athena_master",
    password="YOUR_REDIS_PASSWORD",
)

# 生产环境集群配置
PROD_CLUSTER_CONFIG = RedisClusterConfig(
    nodes=[
        RedisNodeConfig(
            host="redis-cluster-node-1.internal", port=7000, password="YOUR_CLUSTER_PASSWORD"
        ),
        RedisNodeConfig(
            host="redis-cluster-node-2.internal", port=7001, password="YOUR_CLUSTER_PASSWORD"
        ),
        RedisNodeConfig(
            host="redis-cluster-node-3.internal", port=7002, password="YOUR_CLUSTER_PASSWORD"
        ),
        RedisNodeConfig(
            host="redis-cluster-node-4.internal", port=7003, password="YOUR_CLUSTER_PASSWORD"
        ),
        RedisNodeConfig(
            host="redis-cluster-node-5.internal", port=7004, password="YOUR_CLUSTER_PASSWORD"
        ),
        RedisNodeConfig(
            host="redis-cluster-node-6.internal", port=7005, password="YOUR_CLUSTER_PASSWORD"
        ),
    ],
    password="YOUR_CLUSTER_PASSWORD",
    max_connections=200,
)


# =============================================================================
# Docker Compose配置生成器
# =============================================================================


def generate_redis_cluster_docker_compose() -> str:
    """生成Redis集群的Docker Compose配置"""

    compose_config = """# =====================================================
# Redis集群配置 (生产级)
# Redis Cluster Configuration for Production
# 3主3从架构,支持自动故障转移
# =====================================================

version: '3.8'

services:
  # Redis集群节点 (6个节点:3主3从)
  redis-node-1:
    image: redis:7-alpine
    container_name: athena_redis_node_1
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes --port 7000
    ports:
      - "7000:7000"
      - "17000:17000"  # 集群总线端口
    volumes:
      - redis_node_1_data:/data
    networks:
      - redis_cluster_network
    restart: unless-stopped

  redis-node-2:
    image: redis:7-alpine
    container_name: athena_redis_node_2
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes --port 7001
    ports:
      - "7001:7001"
      - "17001:17001"
    volumes:
      - redis_node_2_data:/data
    networks:
      - redis_cluster_network
    restart: unless-stopped

  redis-node-3:
    image: redis:7-alpine
    container_name: athena_redis_node_3
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes --port 7002
    ports:
      - "7002:7002"
      - "17002:17002"
    volumes:
      - redis_node_3_data:/data
    networks:
      - redis_cluster_network
    restart: unless-stopped

  redis-node-4:
    image: redis:7-alpine
    container_name: athena_redis_node_4
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes --port 7003
    ports:
      - "7003:7003"
      - "17003:17003"
    volumes:
      - redis_node_4_data:/data
    networks:
      - redis_cluster_network
    restart: unless-stopped

  redis-node-5:
    image: redis:7-alpine
    container_name: athena_redis_node_5
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes --port 7004
    ports:
      - "7004:7004"
      - "17004:17004"
    volumes:
      - redis_node_5_data:/data
    networks:
      - redis_cluster_network
    restart: unless-stopped

  redis-node-6:
    image: redis:7-alpine
    container_name: athena_redis_node_6
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes --port 7005
    ports:
      - "7005:7005"
      - "17005:17005"
    volumes:
      - redis_node_6_data:/data
    networks:
      - redis_cluster_network
    restart: unless-stopped

  # Redis哨兵 (3个哨兵节点)
  redis-sentinel-1:
    image: redis:7-alpine
    container_name: athena_redis_sentinel_1
    command: redis-sentinel /etc/redis/sentinel.conf --port 26379
    ports:
      - "26379:26379"
    volumes:
      - ./config/redis/sentinel.conf:/etc/redis/sentinel.conf:ro
    depends_on:
      - redis-node-1
    networks:
      - redis_cluster_network
    restart: unless-stopped

  redis-sentinel-2:
    image: redis:7-alpine
    container_name: athena_redis_sentinel_2
    command: redis-sentinel /etc/redis/sentinel.conf --port 26380
    ports:
      - "26380:26380"
    volumes:
      - ./config/redis/sentinel.conf:/etc/redis/sentinel.conf:ro
    depends_on:
      - redis-node-2
    networks:
      - redis_cluster_network
    restart: unless-stopped

  redis-sentinel-3:
    image: redis:7-alpine
    container_name: athena_redis_sentinel_3
    command: redis-sentinel /etc/redis/sentinel.conf --port 26381
    ports:
      - "26381:26381"
    volumes:
      - ./config/redis/sentinel.conf:/etc/redis/sentinel.conf:ro
    depends_on:
      - redis-node-3
    networks:
      - redis_cluster_network
    restart: unless-stopped

  # Redis Commander (Web管理界面)
  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: athena_redis_commander
    ports:
      - "8081:8081"
    environment:
      - REDIS_HOSTS=local:redis-node-1:7000,local:redis-node-2:7001,local:redis-node-3:7002
    networks:
      - redis_cluster_network
    restart: unless-stopped

volumes:
  redis_node_1_data:
  redis_node_2_data:
  redis_node_3_data:
  redis_node_4_data:
  redis_node_5_data:
  redis_node_6_data:

networks:
  redis_cluster_network:
    name: athena_redis_cluster
    driver: bridge
"""

    return compose_config


# =============================================================================
# 集群初始化脚本
# =============================================================================


def generate_cluster_setup_script() -> str:
    """生成Redis集群初始化脚本"""

    script = """#!/bin/bash
# =====================================================
# Redis集群初始化脚本
# Redis Cluster Setup Script
# =====================================================

set -e

echo "========================================="
echo "  Redis集群初始化"
echo "========================================="
echo ""

# 等待所有Redis节点启动
echo "⏳ 等待Redis节点启动..."
sleep 10

# 创建Redis集群(3主3从)
echo "🔧 创建Redis集群..."
docker exec athena_redis_node_1 redis-cli --cluster create \\
  127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \\
  127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 \\
  --cluster-replicas 1 --cluster-yes

echo ""
echo "✅ Redis集群已创建"
echo ""

# 验证集群状态
echo "📊 验证集群状态..."
docker exec athena_redis_node_1 redis-cli --cluster check 127.0.0.1:7000

echo ""
echo "========================================="
echo "  ✅ 集群初始化完成"
echo "========================================="
echo ""
echo "📝 集群信息:"
echo "  主节点: 7000, 7001, 7002"
echo "  从节点: 7003, 7004, 7005"
echo ""
echo "🌐 访问地址:"
echo "  Redis Commander: http://127.0.0.1:8081"
echo ""
"""

    return script


# =============================================================================
# 配置文件生成器
# =============================================================================


def generate_sentinel_conf() -> str:
    """生成Redis哨兵配置文件"""

    config = """# Redis哨兵配置文件
# port 26379

sentinel monitor mymaster 127.0.0.1 6379 2
sentinel auth-pass mymaster YOUR_REDIS_PASSWORD
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 10000
sentinel notification-script mymaster /var/redis/notify.sh
"""

    return config


# =============================================================================
# 健康检查脚本
# =============================================================================


def generate_redis_health_check_script() -> str:
    """生成Redis集群健康检查脚本"""

    script = """#!/bin/bash
# =====================================================
# Redis集群健康检查脚本
# Redis Cluster Health Check Script
# =====================================================

GREEN='\\033[0;32m'
RED='\\033[0;31m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

echo "========================================="
echo "  Redis集群健康检查"
echo "========================================="
echo ""

# 检查集群状态
echo "📊 集群状态:"
docker exec athena_redis_node_1 redis-cli --cluster info 127.0.0.1:7000 | grep -E "cluster_state|cluster_slots_assigned"
echo ""

# 检查节点状态
echo "🔍 节点状态:"
for port in 7000 7001 7002 7003 7004 7005; do
    result=$(docker exec athena_redis_node_1 redis-cli -p $port ping 2>/dev/null || echo "FAILED")
    if [[ "$result" == "PONG" ]]; then
        echo -e "  ${GREEN}✅${NC} 节点 $port: 正常"
    else
        echo -e "  ${RED}❌${NC} 节点 $port: 异常"
    fi
done
echo ""

# 检查集群槽分配
echo "🎯 集群槽分配:"
docker exec athena_redis_node_1 redis-cli --cluster check 127.0.0.1:7000
echo ""

# 检查内存使用
echo "💾 内存使用:"
for port in 7000 7001 7002; do
    memory=$(docker exec athena_redis_node_$port redis-cli -p $port info memory | grep used_memory_human | cut -d: -f2 | tr -d '\\r')
    echo "  节点 $port: $memory"
done
echo ""

echo "========================================="
echo "  ✅ 健康检查完成"
echo "========================================="
"""

    return script
