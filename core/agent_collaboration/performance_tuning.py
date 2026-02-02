#!/usr/bin/env python3
"""
Agent通信系统性能调优配置
Performance Tuning Configuration for Agent Communication System

提供完整的性能调优方案:
1. Redis连接池优化
2. 消息批处理优化
3. 并发控制优化
4. 内存使用优化
5. 网络传输优化

版本: v1.0.0
创建时间: 2026-01-18
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# =============================================================================
# 性能配置文件
# =============================================================================


class PerformanceProfile(Enum):
    """性能配置文件"""

    LOW_LATENCY = "low_latency"  # 低延迟优先
    HIGH_THROUGHPUT = "high_throughput"  # 高吞吐量优先
    BALANCED = "balanced"  # 平衡配置
    MEMORY_OPTIMIZED = "memory_optimized"  # 内存优化


@dataclass
class RedisConnectionPoolConfig:
    """Redis连接池配置"""

    # 基础配置
    max_connections: int = 50
    min_idle_connections: int = 5
    max_idle_connections: int = 20

    # 超时配置
    socket_timeout: int = 5  # Socket超时(秒)
    socket_connect_timeout: int = 5  # 连接超时(秒)
    socket_keepalive: bool = True  # 保持连接

    # 连接回收
    idle_check_interval: int = 30  # 空闲连接检查间隔(秒)
    idle_timeout: int = 300  # 空闲连接超时(秒)

    # 性能优化
    retry_on_timeout: bool = True  # 超时重试
    max_connections_per_node: bool = True  # 每节点最大连接

    # 高级配置
    health_check_interval: int = 30  # 健康检查间隔(秒)
    connection_pool_name: str = "agent_communication_pool"


@dataclass
class MessageQueueOptimizationConfig:
    """消息队列优化配置"""

    # 批处理配置
    enable_batching: bool = True
    batch_size: int = 100  # 批处理大小
    batch_timeout_ms: int = 50  # 批处理超时(毫秒)

    # 管道配置
    pipeline_enabled: bool = True  # 启用Redis Pipeline
    pipeline_size: int = 100  # Pipeline大小

    # 压缩配置
    enable_compression: bool = True
    compression_threshold: int = 1024  # 压缩阈值(字节)
    compression_level: int = 6  # 压缩级别 (1-9)

    # 序列化优化
    serialization_format: str = "json"  # json, msgpack, pickle
    use_orjson: bool = True  # 使用orjson加速

    # 内存优化
    max_message_size: int = 10 * 1024 * 1024  # 最大消息大小
    queue_memory_limit: int = 100 * 1024 * 1024  # 队列内存限制


@dataclass
class ConcurrencyControlConfig:
    """并发控制配置"""

    # 工作线程配置
    max_workers: int = 10  # 最大工作线程数
    min_workers: int = 2  # 最小工作线程数

    # 任务队列配置
    max_queue_size: int = 1000  # 最大任务队列大小
    queue_timeout: float = 1.0  # 队列超时(秒)

    # 限流配置
    rate_limit_enabled: bool = True
    rate_limit_per_second: int = 1000  # 每秒请求限制

    # 退避配置
    enable_backpressure: bool = True  # 启用背压
    backpressure_threshold: float = 0.8  # 背压阈值 (0-1)

    # 超时配置
    task_timeout: float = 30.0  # 任务超时(秒)
    graceful_shutdown_timeout: float = 30.0  # 优雅关闭超时


@dataclass
class MemoryOptimizationConfig:
    """内存优化配置"""

    # 缓冲区配置
    read_buffer_size: int = 64 * 1024  # 读缓冲区大小(64KB)
    write_buffer_size: int = 64 * 1024  # 写缓冲区大小

    # 消息历史限制
    max_message_history: int = 10000  # 最大消息历史数

    # 垃圾回收优化
    gc_threshold: int = 1000  # GC阈值
    gc_generation: int = 2  # GC代数

    # 流水线优化
    max_pipeline_commands: int = 100  # 最大Pipeline命令数

    # 连接复用
    reuse_connections: bool = True  # 复用连接
    connection_ttl: int = 3600  # 连接TTL(秒)


@dataclass
class NetworkOptimizationConfig:
    """网络优化配置"""

    # TCP配置
    tcp_nodelay: bool = True  # 禁用Nagle算法
    tcp_keepalive: bool = True  # 启用TCP keepalive

    # 传输优化
    enable_multiplexing: bool = True  # 启用多路复用
    multiplexing_pool_size: int = 20  # 多路复用池大小

    # 重试配置
    max_retries: int = 3  # 最大重试次数
    retry_backoff: bool = True  # 指数退避
    retry_backoff_max_ms: int = 2000  # 最大退避时间

    # 超时配置
    connect_timeout: int = 5  # 连接超时(秒)
    read_timeout: int = 5  # 读超时(秒)
    write_timeout: int = 5  # 写超时(秒)


@dataclass
class PerformanceTuningConfig:
    """性能调优总配置"""

    profile: PerformanceProfile = PerformanceProfile.BALANCED

    # 各组件配置
    redis_pool: RedisConnectionPoolConfig = field(default_factory=RedisConnectionPoolConfig)
    message_queue: MessageQueueOptimizationConfig = field(
        default_factory=MessageQueueOptimizationConfig
    )
    concurrency: ConcurrencyControlConfig = field(default_factory=ConcurrencyControlConfig)
    memory: MemoryOptimizationConfig = field(default_factory=MemoryOptimizationConfig)
    network: NetworkOptimizationConfig = field(default_factory=NetworkOptimizationConfig)

    def get_redis_url(self, base_url: str = "redis://127.0.0.1:6379/0") -> str:
        """获取优化的Redis URL"""
        params = []

        if self.network.tcp_nodelay:
            params.append("tcp_nodelay=true")

        if self.network.tcp_keepalive:
            params.append("tcp_keepalive=true")

        if self.redis_pool.socket_timeout:
            params.append(f"socket_timeout={self.redis_pool.socket_timeout}")

        if params:
            separator = "&" if "?" in base_url else "?"
            return base_url + separator + "&".join(params)

        return base_url


# =============================================================================
# 预定义性能配置文件
# =============================================================================

# 低延迟配置(适用于实时通信场景)
LOW_LATENCY_CONFIG = PerformanceTuningConfig(
    profile=PerformanceProfile.LOW_LATENCY,
    redis_pool=RedisConnectionPoolConfig(
        max_connections=100, min_idle_connections=20, socket_timeout=2, socket_connect_timeout=2
    ),
    message_queue=MessageQueueOptimizationConfig(
        enable_batching=False,  # 禁用批处理以降低延迟
        pipeline_enabled=True,
        pipeline_size=10,
        use_orjson=True,
    ),
    concurrency=ConcurrencyControlConfig(max_workers=20, task_timeout=10.0),
)

# 高吞吐量配置(适用于批量处理场景)
HIGH_THROUGHPUT_CONFIG = PerformanceTuningConfig(
    profile=PerformanceProfile.HIGH_THROUGHPUT,
    redis_pool=RedisConnectionPoolConfig(
        max_connections=200, min_idle_connections=50, socket_timeout=10
    ),
    message_queue=MessageQueueOptimizationConfig(
        enable_batching=True,
        batch_size=500,
        batch_timeout_ms=100,
        pipeline_enabled=True,
        pipeline_size=200,
        enable_compression=True,
    ),
    concurrency=ConcurrencyControlConfig(max_workers=50, max_queue_size=5000),
)

# 平衡配置(推荐用于大多数场景)
BALANCED_CONFIG = PerformanceTuningConfig(
    profile=PerformanceProfile.BALANCED,
    redis_pool=RedisConnectionPoolConfig(
        max_connections=50, min_idle_connections=10, socket_timeout=5
    ),
    message_queue=MessageQueueOptimizationConfig(
        enable_batching=True, batch_size=100, pipeline_enabled=True, use_orjson=True
    ),
    concurrency=ConcurrencyControlConfig(max_workers=10, max_queue_size=1000),
)

# 内存优化配置(适用于内存受限环境)
MEMORY_OPTIMIZED_CONFIG = PerformanceTuningConfig(
    profile=PerformanceProfile.MEMORY_OPTIMIZED,
    redis_pool=RedisConnectionPoolConfig(
        max_connections=20, min_idle_connections=2, socket_timeout=10
    ),
    message_queue=MessageQueueOptimizationConfig(
        enable_batching=True, batch_size=50, enable_compression=True, compression_level=9
    ),
    memory=MemoryOptimizationConfig(
        read_buffer_size=16 * 1024, write_buffer_size=16 * 1024, max_message_history=1000
    ),
)


# =============================================================================
# 性能测试和基准测试工具
# =============================================================================


class PerformanceBenchmark:
    """性能基准测试工具"""

    @staticmethod
    def get_benchmark_scenarios() -> dict[str, dict[str, Any]]:
        """
        获取性能测试场景

        Returns:
            Dict: 测试场景配置
        """
        return {
            "throughput_test": {
                "name": "吞吐量测试",
                "description": "测试系统最大吞吐量",
                "concurrent_users": [10, 50, 100, 200],
                "requests_per_user": [100, 500, 1000],
                "metrics": [
                    "messages_per_second",
                    "avg_latency_ms",
                    "p95_latency_ms",
                    "p99_latency_ms",
                ],
            },
            "latency_test": {
                "name": "延迟测试",
                "description": "测试系统端到端延迟",
                "message_sizes": [1024, 10240, 102400, 1024000],  # 1KB, 10KB, 100KB, 1MB
                "metrics": ["send_latency_ms", "process_latency_ms", "receive_latency_ms"],
            },
            "reliability_test": {
                "name": "可靠性测试",
                "description": "测试系统稳定性和错误恢复",
                "duration_hours": [1, 6, 24],
                "failure_injection": True,
                "metrics": ["success_rate", "error_rate", "recovery_time_s"],
            },
            "scalability_test": {
                "name": "扩展性测试",
                "description": "测试系统水平扩展能力",
                "node_counts": [1, 2, 4, 8],
                "metrics": ["throughput_scaling", "latency_increase"],
            },
            "stress_test": {
                "name": "压力测试",
                "description": "测试系统极限性能",
                "ramp_up_time_minutes": 10,
                "max_load_duration_minutes": 30,
                "metrics": ["max_throughput", "breaking_point"],
            },
        }

    @staticmethod
    def get_performance_thresholds() -> dict[str, dict[str, Any]]:
        """
        获取性能阈值标准

        Returns:
            Dict: 性能阈值
        """
        return {
            "latency": {
                "excellent": {"p50": 10, "p95": 50, "p99": 100},  # ms
                "good": {"p50": 50, "p95": 100, "p99": 200},
                "acceptable": {"p50": 100, "p95": 200, "p99": 500},
                "poor": {"p50": 200, "p95": 500, "p99": 1000},
            },
            "throughput": {
                "low": {"max": 1000},  # 消息/秒
                "medium": {"max": 5000},
                "high": {"max": 10000},
                "ultra": {"max": 50000},
            },
            "reliability": {
                "excellent": {"success_rate": 0.999, "mtbf_hours": 8760},  # 99.9%, 1年
                "good": {"success_rate": 0.995, "mtbf_hours": 720},
                "acceptable": {"success_rate": 0.99, "mtbf_hours": 168},
                "poor": {"success_rate": 0.95, "mtbf_hours": 24},
            },
            "resource_usage": {
                "memory": {
                    "excellent": {"usage_percent": 50},
                    "good": {"usage_percent": 70},
                    "warning": {"usage_percent": 85},
                    "critical": {"usage_percent": 95},
                },
                "cpu": {
                    "excellent": {"usage_percent": 50},
                    "good": {"usage_percent": 70},
                    "warning": {"usage_percent": 85},
                    "critical": {"usage_percent": 95},
                },
                "connections": {
                    "excellent": {"usage_percent": 50},
                    "good": {"usage_percent": 70},
                    "warning": {"usage_percent": 85},
                    "critical": {"usage_percent": 95},
                },
            },
        }


# =============================================================================
# 配置验证器
# =============================================================================


class ConfigValidator:
    """配置验证器"""

    @staticmethod
    def validate_performance_config(config: PerformanceTuningConfig) -> dict[str, Any]:
        """
        验证性能配置

        Args:
            config: 性能配置

        Returns:
            Dict: 验证结果
        """
        issues = []
        warnings = []

        # 验证连接池配置
        if config.redis_pool.max_connections < config.redis_pool.min_idle_connections:
            issues.append("max_connections不能小于min_idle_connections")

        if config.redis_pool.max_connections > 1000:
            warnings.append("max_connections过大可能导致资源耗尽")

        # 验证批处理配置
        if config.message_queue.batch_size > 1000:
            warnings.append("batch_size过大可能导致内存压力")

        if config.message_queue.batch_timeout_ms > 1000:
            warnings.append("batch_timeout_ms过长会增加延迟")

        # 验证并发配置
        if config.concurrency.max_workers > 100:
            warnings.append("max_workers过多可能导致上下文切换开销")

        # 验证内存配置
        if config.message_queue.max_message_size > 100 * 1024 * 1024:  # 100MB
            issues.append("max_message_size过大,建议小于100MB")

        # 验证网络配置
        if config.network.read_timeout < 1 or config.network.read_timeout > 60:
            warnings.append("read_timeout建议在1-60秒之间")

        return {"valid": len(issues) == 0, "issues": issues, "warnings": warnings}

    @staticmethod
    def suggest_optimizations(current_performance: dict[str, Any]) -> list[str]:
        """
        根据当前性能指标建议优化方案

        Args:
            current_performance: 当前性能指标

        Returns:
            list[str]: 优化建议列表
        """
        suggestions = []

        # 根据延迟建议
        avg_latency = current_performance.get("avg_latency_ms", 0)
        if avg_latency > 200:
            suggestions.append("⚡ 启用LOW_LATENCY配置文件以降低延迟")
            suggestions.append("⚡ 减小批处理大小(batch_size)")
            suggestions.append("⚡ 禁用消息压缩以减少CPU开销")

        # 根据吞吐量建议
        throughput = current_performance.get("throughput_per_second", 0)
        if throughput < 1000:
            suggestions.append("🚀 启用HIGH_THROUGHPUT配置文件以提升吞吐量")
            suggestions.append("🚀 增加批处理大小(batch_size)")
            suggestions.append("🚀 启用Redis Pipeline")

        # 根据内存使用建议
        memory_usage = current_performance.get("memory_usage_percent", 0)
        if memory_usage > 85:
            suggestions.append("💾 启用MEMORY_OPTIMIZED配置文件")
            suggestions.append("💾 减小消息历史缓存(max_message_history)")
            suggestions.append("💾 增加消息压缩级别(compression_level)")

        # 根据错误率建议
        error_rate = current_performance.get("error_rate", 0)
        if error_rate > 0.05:  # 5%
            suggestions.append("🛡️ 检查网络连接稳定性")
            suggestions.append("🛡️ 增加重试次数(max_retries)")
            suggestions.append("🛡️ 启用健康检查和故障转移")

        return suggestions


# =============================================================================
# 配置导出工具
# =============================================================================


def export_performance_config(
    config: PerformanceTuningConfig,
    filepath: str = "/Users/xujian/Athena工作平台/config/communication_performance.json",
):
    """
    导出性能配置到文件

    Args:
        config: 性能配置
        filepath: 导出文件路径
    """
    import json
    from pathlib import Path

    # 创建目录
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    # 转换为可序列化的字典
    config_dict = {
        "profile": config.profile.value,
        "redis_pool": {
            "max_connections": config.redis_pool.max_connections,
            "min_idle_connections": config.redis_pool.min_idle_connections,
            "socket_timeout": config.redis_pool.socket_timeout,
        },
        "message_queue": {
            "enable_batching": config.message_queue.enable_batching,
            "batch_size": config.message_queue.batch_size,
            "pipeline_enabled": config.message_queue.pipeline_enabled,
        },
        "concurrency": {
            "max_workers": config.concurrency.max_workers,
            "max_queue_size": config.concurrency.max_queue_size,
        },
    }

    # 写入文件
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)

    print(f"✅ 性能配置已导出: {filepath}")


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Agent通信系统性能调优配置")
    print("=" * 70)
    print()

    # 验证配置
    validator = ConfigValidator()
    result = validator.validate_performance_config(BALANCED_CONFIG)

    print("📋 配置验证:")
    print(f"  有效: {result['valid']}")
    if result["issues"]:
        print(f"  问题: {result['issues']}")
    if result["warnings"]:
        print(f"  警告: {result['warnings']}")
    print()

    # 性能建议
    current_performance = {
        "avg_latency_ms": 250,
        "throughput_per_second": 800,
        "memory_usage_percent": 75,
        "error_rate": 0.03,
    }

    suggestions = validator.suggest_optimizations(current_performance)
    print("💡 优化建议:")
    for suggestion in suggestions:
        print(f"  {suggestion}")
    print()

    # 导出配置
    export_performance_config(BALANCED_CONFIG)

    print("=" * 70)
    print("📚 预定义配置文件:")
    print("  1. LOW_LATENCY_CONFIG - 低延迟优先")
    print("  2. HIGH_THROUGHPUT_CONFIG - 高吞吐量优先")
    print("  3. BALANCED_CONFIG - 平衡配置(推荐)")
    print("  4. MEMORY_OPTIMIZED_CONFIG - 内存优化")
    print("=" * 70)
