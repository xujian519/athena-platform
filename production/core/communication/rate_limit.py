#!/usr/bin/env python3
"""
Athena通信系统 - 速率限制器
Rate Limiter for Communication System

实现速率限制功能,防止DoS攻击。

主要功能:
1. 滑动窗口算法
2. 多级别限制
3. IP级别限制
4. 用户级别限制
5. 限制规则配置

作者: Athena平台团队
创建时间: 2026-01-16
版本: v1.0.0
"""

from __future__ import annotations
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RateLimitRule:
    """速率限制规则"""

    max_requests: int
    window: int  # 时间窗口(秒)
    burst: int = 0  # 突发限制

    def __post_init__(self):
        if self.burst == 0:
            self.burst = self.max_requests // 10


@dataclass
class RateLimitInfo:
    """速率限制信息"""

    allowed: bool
    remaining: int
    reset_time: float
    retry_after: float | None = None


class RateLimiter:
    """
    速率限制器

    使用滑动窗口算法实现速率限制。
    """

    def __init__(self, default_rule: RateLimitRule | None = None):
        """
        初始化速率限制器

        Args:
            default_rule: 默认限制规则
        """
        self.default_rule = default_rule or RateLimitRule(max_requests=100, window=60)

        # 存储每个客户端的请求记录
        self._requests: dict[str, deque] = defaultdict(deque)

        # 存储每个客户端的自定义规则
        self._rules: dict[str, RateLimitRule] = {}

        logger.info(
            f"速率限制器初始化: 默认限制={self.default_rule.max_requests}/{self.default_rule.window}秒"
        )

    def set_rule(self, client_id: str, rule: RateLimitRule) -> None:
        """
        为特定客户端设置限制规则

        Args:
            client_id: 客户端ID
            rule: 限制规则
        """
        self._rules[client_id] = rule
        logger.info(f"为客户端 {client_id} 设置限制规则: {rule.max_requests}/{rule.window}秒")

    def remove_rule(self, client_id: str) -> None:
        """
        移除客户端的自定义规则

        Args:
            client_id: 客户端ID
        """
        if client_id in self._rules:
            del self._rules[client_id]
            logger.info(f"移除客户端 {client_id} 的自定义限制规则")

    def get_rule(self, client_id: str) -> RateLimitRule:
        """
        获取客户端的限制规则

        Args:
            client_id: 客户端ID

        Returns:
            限制规则
        """
        return self._rules.get(client_id, self.default_rule)

    def is_allowed(self, client_id: str) -> bool:
        """
        检查是否允许请求

        Args:
            client_id: 客户端ID

        Returns:
            是否允许
        """
        return self.check_limit(client_id).allowed

    def check_limit(self, client_id: str) -> RateLimitInfo:
        """
        检查并更新速率限制

        Args:
            client_id: 客户端ID

        Returns:
            限制信息
        """
        rule = self.get_rule(client_id)
        now = time.time()

        # 获取或创建请求队列
        requests = self._requests[client_id]

        # 清理过期的请求记录
        cutoff_time = now - rule.window
        while requests and requests[0] < cutoff_time:
            requests.popleft()

        # 检查是否超过限制
        current_count = len(requests)
        allowed = current_count < rule.max_requests

        if allowed:
            # 记录本次请求
            requests.append(now)
            remaining = rule.max_requests - current_count - 1
        else:
            remaining = 0

        # 计算重置时间
        if requests:
            oldest_request = requests[0]
            reset_time = oldest_request + rule.window
        else:
            reset_time = now + rule.window

        # 计算重试时间
        retry_after = None
        if not allowed:
            retry_after = reset_time - now

        return RateLimitInfo(
            allowed=allowed,
            remaining=max(0, remaining),
            reset_time=reset_time,
            retry_after=retry_after,
        )

    def get_remaining(self, client_id: str) -> int:
        """
        获取剩余请求数

        Args:
            client_id: 客户端ID

        Returns:
            剩余请求数
        """
        info = self.check_limit(client_id)
        return info.remaining

    def reset(self, client_id: str) -> Any:
        """
        重置客户端的请求计数

        Args:
            client_id: 客户端ID
        """
        if client_id in self._requests:
            del self._requests[client_id]
            logger.info(f"重置客户端 {client_id} 的请求计数")

    def cleanup(self, max_age: int = 3600) -> Any:
        """
        清理长期未使用的客户端记录

        Args:
            max_age: 最大保留时间(秒)
        """
        now = time.time()
        to_remove = []

        for client_id, requests in self._requests.items():
            if not requests:
                continue

            # 检查最后一次请求时间
            last_request = requests[-1]
            if now - last_request > max_age:
                to_remove.append(client_id)

        for client_id in to_remove:
            del self._requests[client_id]

        if to_remove:
            logger.debug(f"清理了 {len(to_remove)} 个客户端的速率限制记录")

    def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        total_clients = len(self._requests)
        active_clients = sum(1 for requests in self._requests.values() if requests)

        # 计算总请求数
        total_requests = sum(len(requests) for requests in self._requests.values())

        return {
            "total_clients": total_clients,
            "active_clients": active_clients,
            "total_requests": total_requests,
            "default_rule": {
                "max_requests": self.default_rule.max_requests,
                "window": self.default_rule.window,
                "burst": self.default_rule.burst,
            },
        }


class MultiLevelRateLimiter:
    """
    多级速率限制器

    支持不同级别的限制(IP、用户、全局)。
    """

    def __init__(self):
        """初始化多级速率限制器"""
        self.ip_limiter = RateLimiter(RateLimitRule(200, 60))  # IP级别
        self.user_limiter = RateLimiter(RateLimitRule(100, 60))  # 用户级别
        self.global_limiter = RateLimiter(RateLimitRule(1000, 60))  # 全局级别

        logger.info("多级速率限制器初始化完成")

    def is_allowed(self, ip: str | None = None, user_id: str | None = None) -> bool:
        """
        检查是否允许请求

        Args:
            ip: 客户端IP地址
            user_id: 用户ID

        Returns:
            是否允许
        """
        # 检查全局限制
        if not self.global_limiter.is_allowed("global"):
            logger.warning("全局速率限制触发")
            return False

        # 检查IP限制
        if ip and not self.ip_limiter.is_allowed(ip):
            logger.warning(f"IP速率限制触发: {ip}")
            return False

        # 检查用户限制
        if user_id and not self.user_limiter.is_allowed(user_id):
            logger.warning(f"用户速率限制触发: {user_id}")
            return False

        return True

    def get_stats(self) -> dict[str, Any]:
        """获取所有级别的统计信息"""
        return {
            "ip_level": self.ip_limiter.get_stats(),
            "user_level": self.user_limiter.get_stats(),
            "global_level": self.global_limiter.get_stats(),
        }


# =============================================================================
# 便捷函数
# =============================================================================


def create_rate_limiter(max_requests: int = 100, window: int = 60) -> RateLimiter:
    """创建速率限制器实例"""
    return RateLimiter(RateLimitRule(max_requests, window))


def create_multi_level_limiter() -> MultiLevelRateLimiter:
    """创建多级速率限制器实例"""
    return MultiLevelRateLimiter()


# 默认实例
_default_limiter: RateLimiter | None = None
_multi_level_limiter: MultiLevelRateLimiter | None = None


def get_default_limiter() -> RateLimiter:
    """获取默认速率限制器"""
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = RateLimiter()
    return _default_limiter


def get_multi_level_limiter() -> MultiLevelRateLimiter:
    """获取多级速率限制器"""
    global _multi_level_limiter
    if _multi_level_limiter is None:
        _multi_level_limiter = MultiLevelRateLimiter()
    return _multi_level_limiter


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "MultiLevelRateLimiter",
    "RateLimitInfo",
    "RateLimitRule",
    "RateLimiter",
    "create_multi_level_limiter",
    "create_rate_limiter",
    "get_default_limiter",
    "get_multi_level_limiter",
]
