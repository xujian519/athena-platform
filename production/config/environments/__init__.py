"""
Athena配置环境模块
"""
from __future__ import annotations
from pathlib import Path

# 配置根目录
CONFIG_ROOT = Path(__file__).parent.parent

__all__ = ['CONFIG_ROOT']
