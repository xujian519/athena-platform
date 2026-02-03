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

from .xiaona_prompts import XiaonaPrompts
from .xiaonuo_prompts import XiaonuoPrompts
from .xiaochen_prompts import XiaochenPrompts
from .writing_style_reference import XujianWritingStyleManager


__all__ = [
    "XiaonaPrompts",
    "XiaonuoPrompts",
    "XiaochenPrompts",
    "XujianWritingStyleManager",
]
