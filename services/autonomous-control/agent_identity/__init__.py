#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体身份系统
Agent Identity System

author: 小娜·天秤女神
created: 2024年12月15日
"""

from .core import (
    AgentIdentity,
    AgentType,
    AgentIdentityManager,
    identity_manager,
    get_agent_identity,
    display_agent_identity,
    register_agent_identity,
    format_identity_display,
    IDENTITY_DISPLAY_TEMPLATES
)

__all__ = [
    'AgentIdentity',
    'AgentType',
    'AgentIdentityManager',
    'identity_manager',
    'get_agent_identity',
    'display_agent_identity',
    'register_agent_identity',
    'format_identity_display',
    'IDENTITY_DISPLAY_TEMPLATES'
]