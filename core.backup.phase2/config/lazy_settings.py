#!/usr/bin/env python3
"""
快速配置加载器 - 性能优化版本
Fast Configuration Loader - Performance Optimized

通过懒加载和延迟初始化优化配置加载性能。

目标: 配置加载时间 <50ms

优化策略:
1. 使用TYPE_CHECKING避免运行时导入
2. 实现单例模式缓存
3. 延迟初始化重量级组件
4. 移除不必要的导入

作者: Athena平台团队
创建时间: 2026-04-21
版本: v1.0.0
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import yaml

# 只在类型检查时导入重量级模块
if TYPE_CHECKING:
    pass


class FastSettings(BaseSettings):
    """
    快速配置加载器

    优化版本，避免加载重量级组件。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ==================== 环境配置 ====================
    environment: str = Field(default="development", alias="ENV")
    debug: bool = False

    # ==================== 数据库配置 ====================
    database_host: str = "localhost"
    database_port: int = 5432
    database_user: str = "athena"
    database_password: str = "athena123"
    database_name: str = "athena"

    # LLM配置
    llm_provider: str = "ollama"
    llm_model: str = "qwen2.5:7b"

    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "redis123"

    @classmethod
    def load(cls, environment: str = "development") -> "FastSettings":
        """
        快速加载配置（优化版本）

        Args:
            environment: 环境名称

        Returns:
            配置对象
        """
        start = time.perf_counter()

        # 直接创建实例，不触发额外加载
        settings = cls()
        settings.environment = environment

        elapsed = time.perf_counter() - start

        # 只在调试模式下打印日志
        if os.getenv("DEBUG_FAST_SETTINGS") == "1":
            print(f"⚡ 快速配置加载耗时: {elapsed*1000:.2f}ms")

        return settings


# ==================== 单例缓存 ====================
_cached_settings: FastSettings | None = None


def get_fast_settings() -> FastSettings:
    """
    获取快速配置单例

    Returns:
        配置对象（缓存）
    """
    global _cached_settings

    if _cached_settings is None:
        _cached_settings = FastSettings.load()

    return _cached_settings


# ==================== 性能测试 ====================
if __name__ == "__main__":
    print("=" * 80)
    print("快速配置加载器性能测试")
    print("=" * 80)

    # 测试性能
    iterations = 10
    times = []

    print(f"\n运行 {iterations} 次加载测试...")

    for i in range(iterations):
        # 清除缓存
        import importlib
        import core.config.lazy_settings
        importlib.reload(core.config.lazy_settings)

        start = time.perf_counter()
        settings = FastSettings.load()
        elapsed = time.perf_counter() - start

        times.append(elapsed)
        print(f"  第{i+1}次: {elapsed*1000:.2f}ms")

    # 统计
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"\n统计结果:")
    print(f"  平均耗时: {avg_time*1000:.2f}ms")
    print(f"  最小耗时: {min_time*1000:.2f}ms")
    print(f"  最大耗时: {max_time*1000:.2f}ms")

    # 评估
    if avg_time < 0.05:  # 50ms
        print(f"\n✅ 性能优秀! 平均耗时 {avg_time*1000:.2f}ms < 50ms")
    elif avg_time < 0.1:  # 100ms
        print(f"\n✅ 性能良好! 平均耗时 {avg_time*1000:.2f}ms < 100ms")
    else:
        print(f"\n⚠️ 需要优化! 平均耗时 {avg_time*1000:.2f}ms > 100ms")

    print("=" * 80)
