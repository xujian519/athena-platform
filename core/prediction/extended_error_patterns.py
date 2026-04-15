#!/usr/bin/env python3
from __future__ import annotations
"""
扩展错误模式库
Extended Error Pattern Library

提供15+种错误模式,增强错误预测和预防能力:
1. 原有7种基础模式
2. 新增10+种扩展模式
3. 详细的特征工程
4. 专门的预防策略

作者: Athena平台团队
创建时间: 2025-12-27
版本: v2.0.0
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ===== 基础风险等级 =====
class RiskLevel(Enum):
    """风险等级"""

    NONE = "none"  # 无风险
    LOW = "low"  # 低风险
    MEDIUM = "medium"  # 中风险
    HIGH = "high"  # 高风险
    CRITICAL = "critical"  # 严重风险


# ===== 基础错误模式(原有) =====
class BaseErrorPattern(Enum):
    """基础错误模式"""

    TIMEOUT = "timeout"  # 超时模式
    RATE_LIMIT = "rate_limit"  # 限流模式
    RESOURCE_EXHAUSTION = "resource"  # 资源耗尽
    DEPENDENCY_FAILURE = "dependency"  # 依赖失败
    INVALID_INPUT = "invalid_input"  # 无效输入
    CASCADE_FAILURE = "cascade"  # 级联失败
    PERFORMANCE_DEGRADATION = "performance"  # 性能下降


# ===== 扩展错误模式(新增) =====
class ExtendedErrorPattern(Enum):
    """扩展错误模式(新增)"""

    # AI模型相关
    MODEL_OVERLOAD = "model_overload"  # 模型过载
    TOKEN_LIMIT_EXCEEDED = "token_limit"  # Token超限
    EMBEDDING_FAILURE = "embedding_failure"  # 嵌入失败
    RESPONSE_QUALITY_DEGRADED = "quality_degraded"  # 响应质量下降

    # 数据相关
    DATA_CORRUPTION = "data_corruption"  # 数据损坏
    SCHEMA_MISMATCH = "schema_mismatch"  # 模式不匹配
    DATA_INCONSISTENCY = "data_inconsistency"  # 数据不一致

    # 网络相关
    NETWORK_PARTITION = "network_partition"  # 网络分区
    API_UNREACHABLE = "api_unreachable"  # API不可达
    DNS_RESOLUTION_FAILURE = "dns_failure"  # DNS解析失败

    # 安全相关
    AUTHENTICATION_FAILURE = "auth_failure"  # 认证失败
    AUTHORIZATION_ERROR = "authz_error"  # 授权错误
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"  # 限流超限

    # 工具相关
    TOOL_UNAVAILABLE = "tool_unavailable"  # 工具不可用
    TOOL_EXECUTION_FAILED = "tool_exec_failed"  # 工具执行失败
    TOOL_TIMEOUT = "tool_timeout"  # 工具超时

    # 并发相关
    DEADLOCK = "deadlock"  # 死锁
    RACE_CONDITION = "race_condition"  # 竞态条件
    CONCURRENCY_LIMIT = "concurrency_limit"  # 并发限制

    # 内存相关
    MEMORY_LEAK = "memory_leak"  # 内存泄漏
    OUT_OF_MEMORY = "out_of_memory"  # 内存不足
    GC_OVERHEAD = "gc_overhead"  # GC开销过大

    # 存储相关
    DISK_FULL = "disk_full"  # 磁盘满
    IO_TIMEOUT = "io_timeout"  # IO超时
    STORAGE_CORRUPTION = "storage_corruption"  # 存储损坏


# ===== 统一错误模式 =====
class ErrorPattern(Enum):
    """统一错误模式(包含所有基础和扩展模式)"""

    # === 基础模式 ===
    TIMEOUT = "timeout"  # 超时模式
    RATE_LIMIT = "rate_limit"  # 限流模式
    RESOURCE_EXHAUSTION = "resource"  # 资源耗尽
    DEPENDENCY_FAILURE = "dependency"  # 依赖失败
    INVALID_INPUT = "invalid_input"  # 无效输入
    CASCADE_FAILURE = "cascade"  # 级联失败
    PERFORMANCE_DEGRADATION = "performance"  # 性能下降

    # === AI模型相关 ===
    MODEL_OVERLOAD = "model_overload"  # 模型过载
    TOKEN_LIMIT_EXCEEDED = "token_limit"  # Token超限
    EMBEDDING_FAILURE = "embedding_failure"  # 嵌入失败
    RESPONSE_QUALITY_DEGRADED = "quality_degraded"  # 响应质量下降

    # === 数据相关 ===
    DATA_CORRUPTION = "data_corruption"  # 数据损坏
    SCHEMA_MISMATCH = "schema_mismatch"  # 模式不匹配
    DATA_INCONSISTENCY = "data_inconsistency"  # 数据不一致

    # === 网络相关 ===
    NETWORK_PARTITION = "network_partition"  # 网络分区
    API_UNREACHABLE = "api_unreachable"  # API不可达
    DNS_RESOLUTION_FAILURE = "dns_failure"  # DNS解析失败

    # === 安全相关 ===
    AUTHENTICATION_FAILURE = "auth_failure"  # 认证失败
    AUTHORIZATION_ERROR = "authz_error"  # 授权错误

    # === 工具相关 ===
    TOOL_UNAVAILABLE = "tool_unavailable"  # 工具不可用
    TOOL_EXECUTION_FAILED = "tool_exec_failed"  # 工具执行失败
    TOOL_TIMEOUT = "tool_timeout"  # 工具超时

    # === 并发相关 ===
    DEADLOCK = "deadlock"  # 死锁
    RACE_CONDITION = "race_condition"  # 竞态条件
    CONCURRENCY_LIMIT = "concurrency_limit"  # 并发限制

    # === 内存相关 ===
    MEMORY_LEAK = "memory_leak"  # 内存泄漏
    OUT_OF_MEMORY = "out_of_memory"  # 内存不足

    # === 存储相关 ===
    DISK_FULL = "disk_full"  # 磁盘满
    IO_TIMEOUT = "io_timeout"  # IO超时


# ===== 错误模式特征定义 =====
@dataclass
class ErrorPatternFeatures:
    """错误模式特征"""

    pattern: ErrorPattern
    category: str  # 类别
    severity: RiskLevel  # 严重程度
    frequency_weight: float  # 频率权重
    impact_weight: float  # 影响权重

    # 触发条件(特征阈值)
    trigger_conditions: dict[str, Any] = field(default_factory=dict)

    # 关键指标
    key_indicators: list[str] = field(default_factory=list)

    # 预防策略
    prevention_strategies: list[str] = field(default_factory=list)

    # 恢复策略
    recovery_strategies: list[str] = field(default_factory=list)


# ===== 错误模式特征库 =====
ERROR_PATTERN_FEATURES: dict[ErrorPattern, ErrorPatternFeatures] = {
    # === 基础模式 ===
    ErrorPattern.TIMEOUT: ErrorPatternFeatures(
        pattern=ErrorPattern.TIMEOUT,
        category="基础",
        severity=RiskLevel.MEDIUM,
        frequency_weight=0.8,
        impact_weight=0.7,
        trigger_conditions={"processing_time": 10.0, "queue_length": 100, "cpu_usage": 0.9},  # 秒
        key_indicators=["processing_time", "queue_length", "cpu_usage"],
        prevention_strategies=["增加超时时间", "实现请求超时控制", "添加队列监控", "实施熔断机制"],
        recovery_strategies=["重试请求", "降级处理", "使用缓存"],
    ),
    ErrorPattern.RATE_LIMIT: ErrorPatternFeatures(
        pattern=ErrorPattern.RATE_LIMIT,
        category="基础",
        severity=RiskLevel.MEDIUM,
        frequency_weight=0.9,
        impact_weight=0.6,
        trigger_conditions={
            "request_rate": 100,  # 请求/秒
            "rate_limit_errors": 10,  # 错误数/分钟
            "api_quota_usage": 0.9,  # 90%
        },
        key_indicators=["request_rate", "rate_limit_errors", "api_quota_usage"],
        prevention_strategies=["实施请求限流", "使用令牌桶算法", "添加退避策略", "监控API配额"],
        recovery_strategies=["等待配额重置", "切换到备用API", "使用缓存数据"],
    ),
    ErrorPattern.RESOURCE_EXHAUSTION: ErrorPatternFeatures(
        pattern=ErrorPattern.RESOURCE_EXHAUSTION,
        category="基础",
        severity=RiskLevel.HIGH,
        frequency_weight=0.6,
        impact_weight=0.9,
        trigger_conditions={
            "memory_usage": 0.95,  # 95%
            "cpu_usage": 0.95,
            "disk_usage": 0.95,
            "connection_count": 1000,
        },
        key_indicators=["memory_usage", "cpu_usage", "disk_usage"],
        prevention_strategies=["实施资源配额", "添加资源监控", "实现自动扩容", "优化资源使用"],
        recovery_strategies=["释放资源", "重启服务", "增加资源容量"],
    ),
    # === AI模型相关 ===
    ErrorPattern.MODEL_OVERLOAD: ErrorPatternFeatures(
        pattern=ErrorPattern.MODEL_OVERLOAD,
        category="AI模型",
        severity=RiskLevel.HIGH,
        frequency_weight=0.7,
        impact_weight=0.8,
        trigger_conditions={
            "concurrent_model_requests": 50,
            "model_queue_length": 100,
            "model_response_time": 5.0,  # 秒
        },
        key_indicators=["concurrent_model_requests", "model_queue_length", "model_response_time"],
        prevention_strategies=[
            "实施模型请求队列",
            "添加模型缓存",
            "使用模型负载均衡",
            "实现模型降级策略",
        ],
        recovery_strategies=["切换到备用模型", "使用本地模型", "减少并发请求"],
    ),
    ErrorPattern.TOKEN_LIMIT_EXCEEDED: ErrorPatternFeatures(
        pattern=ErrorPattern.TOKEN_LIMIT_EXCEEDED,
        category="AI模型",
        severity=RiskLevel.MEDIUM,
        frequency_weight=0.8,
        impact_weight=0.7,
        trigger_conditions={
            "token_usage_rate": 0.9,  # 90%
            "request_token_count": 8000,
            "response_token_count": 4000,
        },
        key_indicators=["token_usage_rate", "request_token_count"],
        prevention_strategies=[
            "监控token使用",
            "实施请求分块",
            "优化prompt长度",
            "使用更高效的模型",
        ],
        recovery_strategies=["缩短上下文", "切换到更大配额的模型", "使用摘要代替全文"],
    ),
    ErrorPattern.EMBEDDING_FAILURE: ErrorPatternFeatures(
        pattern=ErrorPattern.EMBEDDING_FAILURE,
        category="AI模型",
        severity=RiskLevel.MEDIUM,
        frequency_weight=0.5,
        impact_weight=0.6,
        trigger_conditions={
            "embedding_error_rate": 0.1,  # 10%
            "embedding_service_unavailable": True,
            "embedding_queue_length": 1000,
        },
        key_indicators=["embedding_error_rate", "embedding_service_unavailable"],
        prevention_strategies=[
            "使用多个嵌入服务",
            "添加嵌入缓存",
            "实施降级策略",
            "监控嵌入服务健康",
        ],
        recovery_strategies=["切换到备用嵌入服务", "使用简单hash嵌入", "跳过嵌入步骤"],
    ),
    ErrorPattern.RESPONSE_QUALITY_DEGRADED: ErrorPatternFeatures(
        pattern=ErrorPattern.RESPONSE_QUALITY_DEGRADED,
        category="AI模型",
        severity=RiskLevel.MEDIUM,
        frequency_weight=0.6,
        impact_weight=0.7,
        trigger_conditions={
            "user_satisfaction": 0.6,  # 60%
            "response_relevance": 0.5,  # 50%
            "hallucination_rate": 0.2,  # 20%
        },
        key_indicators=["user_satisfaction", "response_relevance"],
        prevention_strategies=["监控响应质量", "实施质量过滤", "使用更好的prompt", "添加人工审核"],
        recovery_strategies=["调整temperature", "切换模型", "重新生成响应"],
    ),
    # === 数据相关 ===
    ErrorPattern.DATA_CORRUPTION: ErrorPatternFeatures(
        pattern=ErrorPattern.DATA_CORRUPTION,
        category="数据",
        severity=RiskLevel.CRITICAL,
        frequency_weight=0.3,
        impact_weight=0.95,
        trigger_conditions={
            "data_checksum_failed": True,
            "parse_error_rate": 0.1,
            "null_value_rate": 0.3,
        },
        key_indicators=["data_checksum_failed", "parse_error_rate"],
        prevention_strategies=[
            "实施数据校验",
            "使用数据备份",
            "添加数据完整性检查",
            "监控数据质量",
        ],
        recovery_strategies=["从备份恢复", "修复损坏数据", "重新获取数据"],
    ),
    ErrorPattern.SCHEMA_MISMATCH: ErrorPatternFeatures(
        pattern=ErrorPattern.SCHEMA_MISMATCH,
        category="数据",
        severity=RiskLevel.MEDIUM,
        frequency_weight=0.5,
        impact_weight=0.6,
        trigger_conditions={
            "schema_validation_failed": True,
            "field_type_mismatch": True,
            "missing_required_fields": True,
        },
        key_indicators=["schema_validation_failed", "field_type_mismatch"],
        prevention_strategies=[
            "使用严格schema验证",
            "版本化schema",
            "实施数据转换层",
            "自动化schema迁移",
        ],
        recovery_strategies=["转换数据格式", "使用默认值", "更新schema定义"],
    ),
    # === 网络相关 ===
    ErrorPattern.NETWORK_PARTITION: ErrorPatternFeatures(
        pattern=ErrorPattern.NETWORK_PARTITION,
        category="网络",
        severity=RiskLevel.HIGH,
        frequency_weight=0.4,
        impact_weight=0.8,
        trigger_conditions={
            "network_unreachable": True,
            "connection_timeout": True,
            "packet_loss_rate": 0.5,  # 50%
        },
        key_indicators=["network_unreachable", "connection_timeout"],
        prevention_strategies=["实施网络监控", "使用多区域部署", "添加本地缓存", "实施断路器模式"],
        recovery_strategies=["重试连接", "切换到备用网络", "使用本地数据"],
    ),
    ErrorPattern.API_UNREACHABLE: ErrorPatternFeatures(
        pattern=ErrorPattern.API_UNREACHABLE,
        category="网络",
        severity=RiskLevel.HIGH,
        frequency_weight=0.6,
        impact_weight=0.7,
        trigger_conditions={
            "api_endpoint_unavailable": True,
            "dns_resolution_failed": True,
            "connection_refused": True,
        },
        key_indicators=["api_endpoint_unavailable", "dns_resolution_failed"],
        prevention_strategies=["使用多个API端点", "实施健康检查", "添加API缓存", "使用服务发现"],
        recovery_strategies=["切换到备用端点", "使用缓存数据", "重试请求"],
    ),
    # === 安全相关 ===
    ErrorPattern.AUTHENTICATION_FAILURE: ErrorPatternFeatures(
        pattern=ErrorPattern.AUTHENTICATION_FAILURE,
        category="安全",
        severity=RiskLevel.HIGH,
        frequency_weight=0.7,
        impact_weight=0.8,
        trigger_conditions={
            "auth_failure_rate": 0.1,  # 10%
            "invalid_token_count": 100,
            "account_locked": True,
        },
        key_indicators=["auth_failure_rate", "invalid_token_count"],
        prevention_strategies=["实施token刷新", "使用多因素认证", "监控认证失败", "实施速率限制"],
        recovery_strategies=["刷新token", "重新认证", "使用备用凭证"],
    ),
    ErrorPattern.AUTHORIZATION_ERROR: ErrorPatternFeatures(
        pattern=ErrorPattern.AUTHORIZATION_ERROR,
        category="安全",
        severity=RiskLevel.MEDIUM,
        frequency_weight=0.5,
        impact_weight=0.6,
        trigger_conditions={
            "permission_denied_count": 50,
            "role_mismatch": True,
            "resource_access_denied": True,
        },
        key_indicators=["permission_denied_count", "role_mismatch"],
        prevention_strategies=["实施RBAC", "定期审计权限", "使用最小权限原则", "监控授权失败"],
        recovery_strategies=["请求额外权限", "使用管理员账号", "调整资源ACL"],
    ),
    # === 工具相关 ===
    ErrorPattern.TOOL_UNAVAILABLE: ErrorPatternFeatures(
        pattern=ErrorPattern.TOOL_UNAVAILABLE,
        category="工具",
        severity=RiskLevel.MEDIUM,
        frequency_weight=0.6,
        impact_weight=0.7,
        trigger_conditions={
            "tool_health_check_failed": True,
            "tool_not_registered": True,
            "tool_disabled": True,
        },
        key_indicators=["tool_health_check_failed", "tool_not_registered"],
        prevention_strategies=["实施工具健康检查", "使用备用工具", "添加工具缓存", "监控工具状态"],
        recovery_strategies=["启用备用工具", "重新加载工具", "跳过该工具"],
    ),
    ErrorPattern.TOOL_EXECUTION_FAILED: ErrorPatternFeatures(
        pattern=ErrorPattern.TOOL_EXECUTION_FAILED,
        category="工具",
        severity=RiskLevel.MEDIUM,
        frequency_weight=0.5,
        impact_weight=0.6,
        trigger_conditions={
            "tool_error_rate": 0.15,  # 15%
            "tool_timeout": True,
            "tool_exception": True,
        },
        key_indicators=["tool_error_rate", "tool_timeout"],
        prevention_strategies=[
            "添加工具参数验证",
            "实施工具超时控制",
            "使用工具重试",
            "监控工具性能",
        ],
        recovery_strategies=["重试工具调用", "使用备用工具", "返回默认结果"],
    ),
    # === 并发相关 ===
    ErrorPattern.CONCURRENCY_LIMIT: ErrorPatternFeatures(
        pattern=ErrorPattern.CONCURRENCY_LIMIT,
        category="并发",
        severity=RiskLevel.MEDIUM,
        frequency_weight=0.7,
        impact_weight=0.6,
        trigger_conditions={
            "concurrent_requests": 500,
            "queue_length": 1000,
            "thread_pool_full": True,
        },
        key_indicators=["concurrent_requests", "queue_length"],
        prevention_strategies=["实施请求限流", "使用异步处理", "增加并发容量", "实施背压机制"],
        recovery_strategies=["等待队列空闲", "拒绝新请求", "扩容线程池"],
    ),
    # === 内存相关 ===
    ErrorPattern.MEMORY_LEAK: ErrorPatternFeatures(
        pattern=ErrorPattern.MEMORY_LEAK,
        category="内存",
        severity=RiskLevel.HIGH,
        frequency_weight=0.4,
        impact_weight=0.9,
        trigger_conditions={
            "memory_usage_trend": "increasing",
            "memory_growth_rate": 10.0,  # MB/分钟
            "gc_frequency": 10,  # 次/分钟
        },
        key_indicators=["memory_usage_trend", "memory_growth_rate"],
        prevention_strategies=[
            "实施内存监控",
            "定期重启服务",
            "使用内存分析工具",
            "优化对象生命周期",
        ],
        recovery_strategies=["重启服务", "触发GC", "释放缓存"],
    ),
    ErrorPattern.OUT_OF_MEMORY: ErrorPatternFeatures(
        pattern=ErrorPattern.OUT_OF_MEMORY,
        category="内存",
        severity=RiskLevel.CRITICAL,
        frequency_weight=0.3,
        impact_weight=1.0,
        trigger_conditions={
            "memory_usage": 0.98,  # 98%
            "swap_usage": 0.8,  # 80%
            "oom_killer_triggered": True,
        },
        key_indicators=["memory_usage", "swap_usage"],
        prevention_strategies=[
            "实施内存限制",
            "使用内存高效的数据结构",
            "优化缓存策略",
            "增加物理内存",
        ],
        recovery_strategies=["重启服务", "增加内存", "优化内存使用"],
    ),
    # === 存储相关 ===
    ErrorPattern.DISK_FULL: ErrorPatternFeatures(
        pattern=ErrorPattern.DISK_FULL,
        category="存储",
        severity=RiskLevel.CRITICAL,
        frequency_weight=0.4,
        impact_weight=0.9,
        trigger_conditions={
            "disk_usage": 0.95,  # 95%
            "inode_usage": 0.9,  # 90%
            "write_failed": True,
        },
        key_indicators=["disk_usage", "inode_usage"],
        prevention_strategies=["实施磁盘监控", "自动清理旧数据", "使用日志轮转", "实施数据归档"],
        recovery_strategies=["清理磁盘空间", "删除临时文件", "扩展存储容量"],
    ),
    ErrorPattern.IO_TIMEOUT: ErrorPatternFeatures(
        pattern=ErrorPattern.IO_TIMEOUT,
        category="存储",
        severity=RiskLevel.MEDIUM,
        frequency_weight=0.5,
        impact_weight=0.7,
        trigger_conditions={
            "io_operation_time": 5.0,  # 秒
            "io_wait_time": 1.0,  # 秒
            "disk_queue_length": 100,
        },
        key_indicators=["io_operation_time", "io_wait_time"],
        prevention_strategies=["使用异步IO", "优化IO操作", "增加IO缓存", "监控IO性能"],
        recovery_strategies=["重试IO操作", "使用缓存数据", "优化数据访问模式"],
    ),
}


# ===== 便捷函数 =====
def get_error_pattern_features(pattern: ErrorPattern) -> ErrorPatternFeatures | None:
    """获取错误模式特征"""
    return ERROR_PATTERN_FEATURES.get(pattern)


def get_error_patterns_by_category(category: str) -> list[ErrorPattern]:
    """按类别获取错误模式"""
    return [
        pattern
        for pattern, features in ERROR_PATTERN_FEATURES.items()
        if features.category == category
    ]


def get_high_severity_patterns() -> list[ErrorPattern]:
    """获取高严重性错误模式"""
    return [
        pattern
        for pattern, features in ERROR_PATTERN_FEATURES.items()
        if features.severity in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    ]


def get_prevention_strategies(pattern: ErrorPattern) -> list[str]:
    """获取预防策略"""
    features = ERROR_PATTERN_FEATURES.get(pattern)
    return features.prevention_strategies if features else []


def get_recovery_strategies(pattern: ErrorPattern) -> list[str]:
    """获取恢复策略"""
    features = ERROR_PATTERN_FEATURES.get(pattern)
    return features.recovery_strategies if features else []


# ===== 使用示例 =====
async def main():
    """主函数示例"""
    print("=" * 70)
    print("扩展错误模式库演示")
    print("=" * 70)

    # 统计信息
    total_patterns = len(ErrorPattern)
    categories = {}
    severity_count = {}

    for pattern, features in ERROR_PATTERN_FEATURES.items():
        # 统计类别
        if features.category not in categories:
            categories[features.category] = 0
        categories[features.category] += 1

        # 统计严重程度
        if features.severity not in severity_count:
            severity_count[features.severity] = 0
        severity_count[features.severity] += 1

    print("\n📊 错误模式统计:")
    print(f"   总数: {total_patterns} 种")

    print("\n📁 按类别:")
    for category, count in sorted(categories.items()):
        print(f"   {category}: {count} 种")

    print("\n⚠️  按严重程度:")
    for severity, count in sorted(severity_count.items(), key=lambda x: -x[1].value):
        print(f"   {severity.value}: {count} 种")

    # 示例:模型过载模式
    print("\n🔍 示例: 模型过载模式")
    features = ERROR_PATTERN_FEATURES[ErrorPattern.MODEL_OVERLOAD]
    print(f"   类别: {features.category}")
    print(f"   严重程度: {features.severity.value}")
    print(f"   触发条件: {features.trigger_conditions}")
    print(f"   关键指标: {', '.join(features.key_indicators)}")
    print("   预防策略:")
    for strategy in features.prevention_strategies:
        print(f"     - {strategy}")

    # 示例:获取高严重性模式
    print("\n🚨 高严重性错误模式:")
    high_severity = get_high_severity_patterns()
    for pattern in high_severity[:5]:
        print(f"   - {pattern.value}")

    print("\n✅ 演示完成")


# 入口点: @async_main装饰器已添加到main函数
