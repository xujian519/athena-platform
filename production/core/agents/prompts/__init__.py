#!/usr/bin/env python3
"""
智能体提示词系统
Agent Prompts System

版本: v2.0
更新: 2026-02-03

新增:
- 写作风格参考系统（徐健风格）
- 小诺写作风格提示词
- 小宸写作风格提示词
"""

from __future__ import annotations
from .writing_style_reference import XujianWritingStyleManager
from .xiaochen_prompts import XiaochenPrompts
from .xiaona_prompts import XiaonaPrompts
from .xiaonuo_prompts import XiaonuoPrompts

__all__ = [
    "XiaonaPrompts",
    "XiaonuoPrompts",
    "XiaochenPrompts",
    "XujianWritingStyleManager",
]
