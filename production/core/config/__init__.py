from __future__ import annotations
"""
配置模块
提供系统配置、环境变量管理和加载功能
"""

from .system_prompt import get_agent_prompt, get_system_prompt

__all__ = ['get_system_prompt', 'get_agent_prompt']
