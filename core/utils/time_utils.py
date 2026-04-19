#!/usr/bin/env python3
from __future__ import annotations
"""
时间处理工具模块
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def now_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """获取当前时间的字符串表示"""
    return datetime.now().strftime(fmt)


def now_iso() -> str:
    """获取当前时间的ISO格式"""
    return datetime.now().isoformat()


def parse_time(time_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime | None:
    """解析时间字符串"""
    try:
        return datetime.strptime(time_str, fmt)
    except (ValueError, TypeError) as e:
        logger.debug(f"时间解析失败: {e}")
        return None


def add_seconds(seconds: int) -> datetime:
    """获取N秒后的时间"""
    return datetime.now() + timedelta(seconds=seconds)


def add_minutes(minutes: int) -> datetime:
    """获取N分钟后的时间"""
    return datetime.now() + timedelta(minutes=minutes)


def add_hours(hours: int) -> datetime:
    """获取N小时后的时间"""
    return datetime.now() + timedelta(hours=hours)


def add_days(days: int) -> datetime:
    """获取N天后的时间"""
    return datetime.now() + timedelta(days=days)


__all__ = [
    "add_days",
    "add_hours",
    "add_minutes",
    "add_seconds",
    "now_iso",
    "now_str",
    "parse_time",
]
